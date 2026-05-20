#!/usr/bin/env python3
"""
Extract unique capability signatures from massive monolithic files.

Maps function/class names from monoliths to canonical capability domains.
"""
import psycopg2
import json
import os
import ast
from collections import defaultdict

CACHE_DSN = "postgresql://research:research_hub_dev@postgres-cache:5432/unification_aggregator"


def translate_path(host_path):
    if not host_path:
        return None
    path = host_path.replace('\\\\', '/')
    if path.startswith('D:/PartsFactory/'):
        return '/mnt/d/' + path[3:]
    if path.startswith('D:/OC build/'):
        return '/workspace/OCbuild/' + path[12:]
    if path.startswith('D:/Manny Unification 2/'):
        return '/workspace/MannyUnification2/' + path[23:]
    if path.startswith('d:/PartsFactory/'):
        return '/mnt/d/' + path[3:]
    if path.startswith('d:/OC build/'):
        return '/workspace/OCbuild/' + path[12:]
    if path.startswith('d:/Manny Unification 2/'):
        return '/workspace/MannyUnification2/' + path[23:]
    return path


def categorize_function(name):
    """Map function name to capability domain."""
    name_lower = name.lower()
    
    if any(x in name_lower for x in ['lattice', 'e8', 'root', 'weyl', 'leech', 'dynkin', 'cartan']):
        return 'geometry_lattice'
    if any(x in name_lower for x in ['snap', 'agrm', 'govern', 'policy', 'rule', 'vote', 'consensus']):
        return 'governance_snap'
    if any(x in name_lower for x in ['mmdb', 'crystal', 'memory', 'recall', 'store']):
        return 'mmdb_memory'
    if any(x in name_lower for x in ['morph', 'field', 'state', 'transition']):
        return 'morphonic'
    if any(x in name_lower for x in ['mdhg', 'hierarchy', 'tree', 'node', 'depth']):
        return 'mdhg_hierarchy'
    if any(x in name_lower for x in ['speedlight', 'receipt', 'cache', 'lineage']):
        return 'speedlight'
    if any(x in name_lower for x in ['wallet', 'identity', 'auth', 'credential']):
        return 'identity_wallet'
    if any(x in name_lower for x in ['server', 'app', 'run', 'listen', 'handle']):
        return 'server_runtime'
    if any(x in name_lower for x in ['registry', 'engine', 'pipeline', 'thinktank', 'orchestr']):
        return 'core_engine'
    if any(x in name_lower for x in ['hash', 'crypto', 'sign', 'verify']):
        return 'cryptography'
    if any(x in name_lower for x in ['metric', 'log', 'trace', 'monitor']):
        return 'observability'
    if any(x in name_lower for x in ['config', 'setting', 'param']):
        return 'configuration'
    if name.startswith('_') or name.startswith('test_'):
        return 'internal'
    return 'other'


def extract_signatures_from_file(path):
    """Extract all top-level function and class names from a Python file."""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        functions = []
        classes = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append({
                    'name': node.name,
                    'line': node.lineno,
                    'args': len(node.args.args),
                    'category': categorize_function(node.name)
                })
            elif isinstance(node, ast.ClassDef):
                methods = []
                for child in ast.iter_child_nodes(node):
                    if isinstance(child, ast.FunctionDef):
                        methods.append(child.name)
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'methods': methods,
                    'method_count': len(methods),
                    'category': categorize_function(node.name)
                })
        
        return functions, classes
    except Exception as e:
        return [], []


def analyze_monoliths():
    pg = psycopg2.connect(CACHE_DSN)
    pg_cur = pg.cursor()
    
    print("Extracting signatures from monolithic files...\n")
    
    # Get monoliths
    pg_cur.execute("""
        SELECT 
            cs.source_id,
            s.host_path,
            s.relative_path,
            cs.line_count,
            jsonb_array_length(cs.function_names) as func_count,
            jsonb_array_length(cs.class_names) as class_count
        FROM catalog.code_source cs
        JOIN artifact.source s ON cs.source_id = s.id
        WHERE cs.line_count > 100000
        ORDER BY cs.line_count DESC
    """)
    
    monoliths = pg_cur.fetchall()
    
    all_functions = defaultdict(list)
    all_classes = defaultdict(list)
    domain_counts = defaultdict(int)
    
    for row in monoliths:
        source_id, host_path, rel_path, lines, func_count, class_count = row
        container_path = translate_path(host_path)
        
        basename = rel_path.split('/')[-1] if rel_path else 'unknown'
        print(f"\nAnalyzing: {basename} ({lines:,} lines, {func_count} funcs, {class_count} classes)")
        
        if not container_path or not os.path.exists(container_path):
            print(f"  ⚠️  File not accessible: {host_path}")
            continue
        
        funcs, classes = extract_signatures_from_file(container_path)
        
        print(f"  Extracted {len(funcs)} top-level functions, {len(classes)} top-level classes")
        
        # Categorize
        file_domains = defaultdict(int)
        for f in funcs:
            all_functions[f['category']].append({
                'name': f['name'],
                'file': basename,
                'line': f['line'],
                'args': f['args']
            })
            file_domains[f['category']] += 1
            domain_counts[f['category']] += 1
        
        for c in classes:
            all_classes[c['category']].append({
                'name': c['name'],
                'file': basename,
                'line': c['line'],
                'methods': c['method_count']
            })
            file_domains[c['category']] += 1
            domain_counts[c['category']] += 1
        
        print(f"  Domain distribution:")
        for domain, count in sorted(file_domains.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {domain}: {count}")
    
    # Summary
    print("\n\n=== CAPABILITY SIGNATURE SUMMARY ===\n")
    
    print("Functions by domain:")
    for domain, funcs in sorted(all_functions.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n  {domain}: {len(funcs)} functions")
        # Show unique names
        unique_names = sorted(set(f['name'] for f in funcs))
        print(f"    Unique names: {len(unique_names)}")
        for name in unique_names[:10]:
            print(f"      {name}")
        if len(unique_names) > 10:
            print(f"      ... and {len(unique_names) - 10} more")
    
    print("\n\nClasses by domain:")
    for domain, classes in sorted(all_classes.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"\n  {domain}: {len(classes)} classes")
        unique_names = sorted(set(c['name'] for c in classes))
        print(f"    Unique names: {len(unique_names)}")
        for name in unique_names[:10]:
            print(f"      {name}")
        if len(unique_names) > 10:
            print(f"      ... and {len(unique_names) - 10} more")
    
    print("\n\n=== OVERALL DOMAIN COUNTS ===")
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {domain}: {count}")
    
    pg_cur.close()
    pg.close()


if __name__ == "__main__":
    analyze_monoliths()
