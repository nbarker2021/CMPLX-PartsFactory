#!/usr/bin/env python3
"""
Phase 3-4: Cross-reference PartsFactory with cache evidence, aggregate capabilities.

1. Read PartsFactory real files from yard_inventory.sqlite
2. Cross-reference with evidence_dedupe.sqlite (cache postgres data)
3. Find "remaining" files not represented in cache
4. Aggregate all unique capabilities across both spaces
5. Build capability taxonomy
"""
import sqlite3
import json
from collections import defaultdict

EVIDENCE_DB = "data/evidence_dedupe.sqlite"
YARD_DB = "data/yard_inventory.sqlite"

def cross_reference():
    ev = sqlite3.connect(EVIDENCE_DB)
    ev.row_factory = sqlite3.Row
    yd = sqlite3.connect(YARD_DB)
    yd.row_factory = sqlite3.Row
    
    print("=== PHASE 3: Cross-Reference PartsFactory with Cache Evidence ===\n")
    
    # Get all PartsFactory real files (not noise, not template)
    yd_cur = yd.cursor()
    yd_cur.execute("""
        SELECT abs_path, rel_path, basename, size_bytes, content_hash, classification, space_tag
        FROM file_inventory fi
        JOIN file_classification fc ON fi.file_id = fc.file_id
        WHERE classification IN ('real', 'canonical')
          AND (extension IS NULL OR extension NOT IN ('.pyc', '.pyo'))
        ORDER BY basename, size_bytes
    """)
    
    pf_files = []
    pf_basenames = defaultdict(list)
    for row in yd_cur.fetchall():
        pf_files.append(dict(row))
        pf_basenames[row['basename']].append(dict(row))
    
    print(f"PartsFactory real/canonical files: {len(pf_files):,}")
    print(f"Unique basenames in PartsFactory: {len(pf_basenames):,}")
    
    # Get all cache evidence basenames
    ev_cur = ev.cursor()
    ev_cur.execute("SELECT DISTINCT basename FROM evidence_file")
    cache_basenames = {r[0] for r in ev_cur.fetchall() if r[0]}
    
    print(f"Unique basenames in cache evidence: {len(cache_basenames):,}")
    
    # Find overlap
    overlap = set(pf_basenames.keys()) & cache_basenames
    pf_only = set(pf_basenames.keys()) - cache_basenames
    cache_only = cache_basenames - set(pf_basenames.keys())
    
    print(f"\nOverlap (in both): {len(overlap):,} basenames")
    print(f"PartsFactory only: {len(pf_only):,} basenames")
    print(f"Cache only: {len(cache_only):,} basenames")
    
    # Show top overlapping basenames
    print("\nTop overlapping basenames (duplicated across spaces):")
    overlap_counts = []
    for bn in sorted(overlap):
        pf_count = len(pf_basenames[bn])
        ev_cur.execute("SELECT COUNT(*) FROM evidence_file WHERE basename = ?", (bn,))
        cache_count = ev_cur.fetchone()[0]
        overlap_counts.append((bn, pf_count, cache_count, pf_count + cache_count))
    
    overlap_counts.sort(key=lambda x: x[3], reverse=True)
    for bn, pfc, cc, total in overlap_counts[:30]:
        print(f"  {bn:<40} | PF: {pfc:>3} | Cache: {cc:>5} | Total: {total:>5}")
    
    # Show PartsFactory-only basenames (unique to PartsFactory, not in cache)
    print("\nPartsFactory-only basenames (not in cache evidence):")
    pf_only_list = sorted(pf_only)
    # Group by file type
    by_ext = defaultdict(list)
    for bn in pf_only_list:
        ext = bn.split('.')[-1] if '.' in bn else 'no_ext'
        by_ext[ext].append(bn)
    
    for ext in sorted(by_ext.keys(), key=lambda e: len(by_ext[e]), reverse=True)[:10]:
        print(f"  .{ext}: {len(by_ext[ext]):>4} files")
        for bn in by_ext[ext][:5]:
            print(f"    {bn}")
    
    # Show cache-only basenames (in cache but not in PartsFactory)
    print("\nCache-only basenames (in Manny but not PartsFactory) — top 30:")
    cache_only_counts = []
    for bn in sorted(cache_only):
        ev_cur.execute("SELECT COUNT(*) FROM evidence_file WHERE basename = ?", (bn,))
        cache_count = ev_cur.fetchone()[0]
        cache_only_counts.append((bn, cache_count))
    
    cache_only_counts.sort(key=lambda x: x[1], reverse=True)
    for bn, cc in cache_only_counts[:30]:
        print(f"  {bn:<40} | {cc:>5} copies in cache")
    
    # Phase 4: Aggregate capabilities
    print("\n\n=== PHASE 4: Capability Aggregation ===\n")
    
    # Aggregate by basename + size pattern across BOTH datasets
    all_clusters = defaultdict(lambda: {
        'pf_files': [],
        'cache_files': [],
        'pf_systems': set(),
        'cache_systems': set(),
        'total_count': 0
    })
    
    # Add PartsFactory files
    for f in pf_files:
        bn = f['basename']
        size = f['size_bytes'] or 0
        key = f"{bn}:{size}"
        all_clusters[key]['pf_files'].append(f)
        all_clusters[key]['pf_systems'].add(f['space_tag'] or 'partsfactory')
        all_clusters[key]['total_count'] += 1
    
    # Add cache files
    ev_cur.execute("""
        SELECT basename, size_bytes, system_of_origin, relative_path, line_count
        FROM evidence_file
        WHERE basename IS NOT NULL
    """)
    for row in ev_cur.fetchall():
        bn, size, system, path, lines = row
        size = size or 0
        key = f"{bn}:{size}"
        all_clusters[key]['cache_files'].append({
            'basename': bn, 'size': size, 'system': system, 'path': path, 'lines': lines
        })
        all_clusters[key]['cache_systems'].add(system or 'unknown')
        all_clusters[key]['total_count'] += 1
    
    # Find clusters that appear in BOTH spaces (cross-space duplicates)
    cross_space = []
    for key, data in all_clusters.items():
        if data['pf_files'] and data['cache_files']:
            cross_space.append((
                key, 
                len(data['pf_files']), 
                len(data['cache_files']),
                data['total_count'],
                sorted(data['pf_systems']),
                sorted(data['cache_systems'])
            ))
    
    cross_space.sort(key=lambda x: x[3], reverse=True)
    print(f"Exact size+name duplicates across PartsFactory and Manny: {len(cross_space)}")
    print("\nTop 20 cross-space duplicates:")
    for key, pfc, cc, total, pfsys, csys in cross_space[:20]:
        print(f"  {key:<60} | PF: {pfc:>2} | Cache: {cc:>4} | PF systems: {', '.join(pfsys)} | Cache: {', '.join(csys[:3])}")
    
    # Build capability taxonomy from basenames
    print("\n\n=== CAPABILITY TAXONOMY ===\n")
    
    taxonomy = defaultdict(list)
    
    # Categorize by basename patterns
    for bn in set(list(pf_basenames.keys()) + list(cache_basenames)):
        if not bn:
            continue
        
        # Heuristic categorization
        if bn in ('server.py', 'app.py', 'main.py', 'run.py', 'start.py'):
            taxonomy['server_runtime'].append(bn)
        elif bn in ('registry.py', 'engine.py', 'thinktank.py', 'pipeline.py'):
            taxonomy['core_engine'].append(bn)
        elif 'lattice' in bn or 'e8' in bn:
            taxonomy['geometry_lattice'].append(bn)
        elif 'morph' in bn:
            taxonomy['morphonic'].append(bn)
        elif 'wallet' in bn or 'identity' in bn:
            taxonomy['identity_wallet'].append(bn)
        elif 'snap' in bn or 'agrm' in bn or 'governance' in bn:
            taxonomy['governance_snap'].append(bn)
        elif 'speedlight' in bn:
            taxonomy['speedlight'].append(bn)
        elif 'mmdb' in bn or 'crystal' in bn:
            taxonomy['mmdb_memory'].append(bn)
        elif 'mdhg' in bn:
            taxonomy['mdhg_hierarchy'].append(bn)
        elif 'policy' in bn:
            taxonomy['policy'].append(bn)
        elif 'config' in bn or 'settings' in bn:
            taxonomy['configuration'].append(bn)
        elif 'docker' in bn or 'dockerfile' in bn.lower():
            taxonomy['infrastructure'].append(bn)
        elif bn.endswith('.md') or bn.endswith('.rst') or bn.endswith('.txt'):
            taxonomy['documentation'].append(bn)
        elif bn.endswith('.yml') or bn.endswith('.yaml') or bn.endswith('.json'):
            taxonomy['configuration'].append(bn)
        elif bn.endswith('.sql'):
            taxonomy['database_schema'].append(bn)
        elif bn.endswith('.js') or bn.endswith('.ts') or bn.endswith('.jsx'):
            taxonomy['frontend'].append(bn)
        elif bn.endswith('.css') or bn.endswith('.scss'):
            taxonomy['frontend_style'].append(bn)
        elif bn.endswith('.html') or bn.endswith('.htm'):
            taxonomy['frontend_markup'].append(bn)
        elif bn == '__init__.py':
            taxonomy['python_package'].append(bn)
        elif bn.endswith('.py'):
            taxonomy['python_module'].append(bn)
        else:
            taxonomy['other'].append(bn)
    
    for category, basenames in sorted(taxonomy.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"{category:<25}: {len(basenames):>5} unique basenames")
    
    ev.close()
    yd.close()
    
    print("\n=== Phase 3-4 Complete ===")
    return len(cross_space), taxonomy


if __name__ == "__main__":
    cross_reference()
