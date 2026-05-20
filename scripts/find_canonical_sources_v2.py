#!/usr/bin/env python3
"""
Find clean canonical sources — refined to exclude third-party libraries.

Strategy:
1. Exclude scipy, numpy, numba, apsw, etc.
2. Focus on CMPLX-native files (not hashed-named dumps)
3. Search for actual CMPLX function/class names
"""
import psycopg2
import json
from collections import defaultdict

CACHE_DSN = "postgresql://research:research_hub_dev@postgres-cache:5432/unification_aggregator"

# Third-party patterns to exclude
EXCLUDE_PATTERNS = [
    'scipy_', 'numpy_', 'numba_', 'apsw_', 'f2py_', 'stats_',
    'signal_', 'special_', 'optimize_', 'linalg_', 'interpolate_',
    'spatial_', 'ndimage_', 'ma_tests_', 'core_tests_',
    'versioneer', 'typing_extensions', 'crackfortran',
    'test_', '_tests_', 'tests__',
    '1bad6ab', 'b90eb64', 'f386e78', '4477aad', '9dfe247',
    'f50c9d1', '7516055', '61e0e32', '52b920f', '0169bca',
    '92d7fc6', 'ed79266', 'a994122', 'ccce0f3', '8077216',
    'a64ec07', 'af21ccd', '0a7d2cc', 'd119859', 'f5b3ac4',
    '2fbf6f9', 'c782b80', '02598e7', '4b84c3a', 'd6ee042',
    '7aaa595', '2d0e435', '9ef921b', 'bcb1687', 'e2cf98c',
    '46ec64f', 'adf575a', 'bcc3c6b',
]

# Domain-specific basenames (known CMPLX files)
DOMAIN_FILES = {
    'geometry_lattice': ['e8_lattice.py', 'lattice.py', 'root_system.py', 'weyl.py', 'leech.py'],
    'governance_snap': ['snap.py', 'agrm.py', 'agrm_runtime.py', 'agrm_core.py', 'governance.py', 'policy_engine.py'],
    'mmdb_memory': ['mmdb.py', 'crystal.py', 'memory.py', 'store.py'],
    'morphonic': ['morphonic.py', 'morph.py', 'field.py', 'state.py'],
    'mdhg_hierarchy': ['mdhg.py', 'hierarchy.py', 'tree.py', 'mdhg_tree.py'],
    'speedlight': ['speedlight.py', 'receipt.py', 'cache.py'],
    'identity_wallet': ['wallet.py', 'identity.py', 'auth.py'],
    'server_runtime': ['server.py', 'app.py', 'main.py', 'run.py'],
    'core_engine': ['registry.py', 'engine.py', 'pipeline.py', 'thinktank.py', 'think_tank.py'],
    'observability': ['metrics.py', 'monitor.py', 'trace.py', 'logger.py'],
    'cryptography': ['hash.py', 'crypto.py', 'sign.py'],
}


def is_third_party(path):
    """Check if path is a third-party library file."""
    path_lower = path.lower()
    for pattern in EXCLUDE_PATTERNS:
        if pattern.lower() in path_lower:
            return True
    return False


def find_canonical_by_basename():
    """Find canonical sources by matching known CMPLX basenames."""
    pg = psycopg2.connect(CACHE_DSN)
    pg_cur = pg.cursor()
    
    print("=== FINDING CANONICAL SOURCES (Refined) ===\n")
    
    for domain, basenames in DOMAIN_FILES.items():
        print(f"\n--- Domain: {domain} ---")
        
        # Search for files with matching basenames
        placeholders = ','.join(['%s'] * len(basenames))
        pg_cur.execute(f"""
            SELECT 
                cs.source_id,
                s.relative_path,
                s.root_label,
                cs.line_count,
                cs.language,
                jsonb_array_length(cs.function_names) as func_count,
                jsonb_array_length(cs.class_names) as class_count,
                s.sha256,
                s.size_bytes
            FROM catalog.code_source cs
            JOIN artifact.source s ON cs.source_id = s.id
            WHERE split_part(s.relative_path, '/', -1) IN ({placeholders})
              AND cs.line_count BETWEEN 10 AND 10000
              AND cs.line_count IS NOT NULL
            ORDER BY 
                CASE WHEN s.root_label = 'partsfactory' THEN 0 ELSE 1 END,
                cs.line_count DESC
        """, basenames)
        
        candidates = pg_cur.fetchall()
        
        # Filter out third-party
        clean = []
        for row in candidates:
            source_id, rel_path, root_label, lines, lang, funcs, classes, sha256, size = row
            if is_third_party(rel_path):
                continue
            clean.append(row)
        
        if not clean:
            print(f"  No clean candidates found for: {basenames}")
            # Fallback: search by function names containing domain keywords
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
                    s.size_bytes
                FROM catalog.code_source cs
                JOIN artifact.source s ON cs.source_id = s.id
                WHERE cs.line_count BETWEEN 10 AND 5000
                  AND cs.line_count IS NOT NULL
                  AND s.root_label = 'partsfactory'
                ORDER BY cs.line_count DESC
                LIMIT 20
            """)
            fallback = pg_cur.fetchall()
            for row in fallback:
                source_id, rel_path, root_label, lines, lang, funcs, classes, sha256, size = row
                if not is_third_party(rel_path):
                    basename = rel_path.split('/')[-1] if rel_path else 'unknown'
                    print(f"  Fallback: {basename} ({lines}L, {funcs}F, {classes}C) | {rel_path[:60]}")
                    break
            continue
        
        print(f"  Found {len(clean)} clean candidates:")
        for i, row in enumerate(clean[:5]):
            source_id, rel_path, root_label, lines, lang, funcs, classes, sha256, size = row
            basename = rel_path.split('/')[-1] if rel_path else 'unknown'
            hash_str = sha256[:8] if sha256 else 'no-hash'
            print(f"  {i+1}. {basename:<35} | {lines:>5}L | {funcs:>3}F {classes:>3}C | {root_label:<12} | {hash_str}")
    
    pg_cur.close()
    pg.close()


if __name__ == "__main__":
    find_canonical_by_basename()
