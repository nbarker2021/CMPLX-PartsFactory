#!/usr/bin/env python3
"""
Find clean canonical source files for each capability domain.

Scans catalog.code_source for non-monolithic implementations of functions/classes
extracted from monoliths. Ranks by cleanliness and completeness.
"""
import psycopg2
import json
from collections import defaultdict

CACHE_DSN = "postgresql://research:research_hub_dev@postgres-cache:5432/unification_aggregator"


def get_domain_keywords():
    """Return keyword patterns for each capability domain."""
    return {
        'geometry_lattice': ['lattice', 'e8', 'root', 'weyl', 'leech', 'dynkin', 'cartan', 'root_system'],
        'governance_snap': ['snap', 'agrm', 'govern', 'policy', 'rule', 'vote', 'consensus', 'acceptance'],
        'mmdb_memory': ['mmdb', 'crystal', 'memory', 'recall', 'store', 'embedding'],
        'morphonic': ['morph', 'field', 'state', 'transition', 'curvature'],
        'mdhg_hierarchy': ['mdhg', 'hierarchy', 'tree', 'node', 'depth', 'personal_node'],
        'speedlight': ['speedlight', 'receipt', 'cache', 'lineage', 'braid'],
        'identity_wallet': ['wallet', 'identity', 'auth', 'credential', 'merit'],
        'server_runtime': ['server', 'app', 'runtime', 'listen', 'handle', 'route'],
        'core_engine': ['registry', 'engine', 'pipeline', 'thinktank', 'orchestr'],
        'observability': ['metric', 'log', 'trace', 'monitor', 'tracer'],
        'cryptography': ['hash', 'crypto', 'sign', 'verify', 'audit'],
    }


def find_candidates():
    pg = psycopg2.connect(CACHE_DSN)
    pg_cur = pg.cursor()
    
    domains = get_domain_keywords()
    
    print("=== FINDING CLEAN CANONICAL SOURCES ===\n")
    
    for domain, keywords in domains.items():
        print(f"\n--- Domain: {domain} ---")
        
        # Build pattern query
        patterns = ' | '.join(keywords)
        
        # Find files that contain domain-relevant function/class names
        # Exclude monoliths (>10K lines) and tiny files (<10 lines)
        pg_cur.execute("""
            SELECT 
                cs.source_id,
                s.relative_path,
                s.root_label,
                cs.line_count,
                cs.language,
                jsonb_array_length(cs.function_names) as func_count,
                jsonb_array_length(cs.class_names) as class_count,
                s.sha256,
                cs.function_names,
                cs.class_names
            FROM catalog.code_source cs
            JOIN artifact.source s ON cs.source_id = s.id
            WHERE cs.line_count BETWEEN 10 AND 10000
              AND cs.line_count IS NOT NULL
              AND (
        """ + ' OR '.join(["cs.function_names::text ILIKE %s OR cs.class_names::text ILIKE %s" for _ in keywords]) + """
              )
            ORDER BY 
                CASE WHEN s.root_label = 'partsfactory' THEN 0 ELSE 1 END,
                cs.line_count DESC
            LIMIT 50
        """, [f'%"%{kw}%"%' for kw in keywords for _ in (0, 1)])
        
        candidates = pg_cur.fetchall()
        
        if not candidates:
            print(f"  No candidates found")
            continue
        
        # Score candidates
        scored = []
        for row in candidates:
            source_id, rel_path, root_label, lines, lang, funcs, classes, sha256, fnames, cnames = row
            
            # Score components:
            # - Completeness: line_count / 100 (more lines = more complete, up to 500)
            completeness = min(lines / 100, 5) if lines else 0
            
            # - Focus: fewer total functions = more focused on this domain
            total_items = (funcs or 0) + (classes or 0)
            focus = max(0, 5 - (total_items / 10))
            
            # - Purity: PartsFactory preferred over manny pipeline dumps
            purity = 2 if root_label == 'partsfactory' else 0
            
            # - Has hash: indicates file was accessible and hashed
            hashed = 1 if sha256 else 0
            
            score = completeness + focus + purity + hashed
            
            scored.append((score, source_id, rel_path, root_label, lines, funcs, classes, sha256))
        
        scored.sort(reverse=True)
        
        print(f"  Found {len(scored)} candidates, top 10:")
        for i, (score, source_id, rel_path, root_label, lines, funcs, classes, sha256) in enumerate(scored[:10]):
            basename = rel_path.split('/')[-1] if rel_path else 'unknown'
            hash_str = sha256[:8] if sha256 else 'no-hash'
            print(f"  {i+1}. [{score:.1f}] {basename:<35} | {lines:>5}L | {funcs:>3}F {classes:>3}C | {root_label:<18} | {hash_str}")
        
        # Show best candidate details
        if scored:
            best = scored[0]
            print(f"\n  BEST CANDIDATE:")
            print(f"    Path: {best[2]}")
            print(f"    Space: {best[3]}")
            print(f"    Lines: {best[4]}")
            print(f"    Score: {best[0]:.1f}")
    
    pg_cur.close()
    pg.close()


if __name__ == "__main__":
    find_candidates()
