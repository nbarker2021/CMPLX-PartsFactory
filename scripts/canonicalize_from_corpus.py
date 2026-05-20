#!/usr/bin/env python3
"""
Canonicalize using best corpus candidates.
"""
import os
import hashlib
from datetime import datetime, timezone
import psycopg2
import json

HUB_DSN = os.environ.get("HUB_DSN") or os.environ.get("PG_HUB_DSN")
EXTRACT_DIR = "corpus_extracted"

# Only canonicalize clearly superior corpus versions
CORPUS_BEST = {
    # Better than snap.py (103L)
    'governance_snap': ('governance_snap/snap-corpus/01-active-implementation/Working Prototyping/services/snap-unified/snap_engine.py', 'snap_engine.py'),
    
    # Better than state.py (172L)
    'morphonic': ('morphonic/morphon-corpus/03-historical-builds/historical builds/CMPLX-TMN1/retooling/src/retooling/morphon/morphon.py', 'morphon.py'),
    
    # Better than dump (6725L rejected)
    'mmdb_memory': ('mmdb_memory/mmdb-corpus/03-historical-builds/historical builds/CMPLX-main (1)/CMPLX-main/mcp-server/servers/vector_mmdb_tools.py', 'vector_mmdb_tools.py'),
    
    # Better than logger.py (27L stub)
    'observability': ('observability/aletheia-corpus/03-historical-builds/historical builds/CMPLX-TMN1/tmn1-v2/shared/geometry/aletheia_port.py', 'aletheia_port.py'),
}


def normalize_and_hash(source_path, dest_path):
    with open(source_path, 'rb') as f:
        data = f.read()
    data = data.replace(b'\r\n', b'\n')
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, 'wb') as f:
        f.write(data)
    h = hashlib.sha256(data).hexdigest()
    return h, len(data)


def canonicalize_from_corpus():
    hub_pg = psycopg2.connect(HUB_DSN)
    hub_cur = hub_pg.cursor()
    
    print("=== CANONICALIZING FROM CORPUS (Curated) ===\n")
    
    for domain, (corpus_rel, canon_name) in CORPUS_BEST.items():
        corpus_path = os.path.join(EXTRACT_DIR, corpus_rel)
        canon_dir = f"src/canon/{domain}"
        canon_path = f"{canon_dir}/{canon_name}"
        
        if not os.path.exists(corpus_path):
            print(f"\n{domain}: Corpus file not found: {corpus_path}")
            continue
        
        print(f"\n{domain}:")
        print(f"  Source: {corpus_rel}")
        print(f"  Canonical: {canon_path}")
        
        canon_hash, size = normalize_and_hash(corpus_path, canon_path)
        
        with open(canon_path, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.read().count('\n') + 1
        
        print(f"  Written: {lines} lines, {size} bytes, hash {canon_hash[:16]}...")
        
        cluster_key = f"{domain}:{canon_name}"
        
        hub_cur.execute("""
            INSERT INTO canonical_clusters (cluster_key, basename, description)
            VALUES (%s, %s, %s)
            ON CONFLICT (cluster_key) DO UPDATE SET
                description = EXCLUDED.description,
                updated_at = NOW()
            RETURNING id
        """, (cluster_key, canon_name, f"Canonical {domain} from corpus: {corpus_rel}"))
        
        cluster_id = hub_cur.fetchone()[0]
        
        hub_cur.execute("""
            INSERT INTO canonical_artifacts 
            (cluster_id, source_path, content_hash, file_size, line_count, language, system_name, is_canonical, canonical_reason, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT DO NOTHING
        """, (cluster_id, canon_path, canon_hash, size, lines, 'python', 'corpus', True, f"Canonical from corpus zip for {domain}", datetime.now(timezone.utc).isoformat()))
        
        hub_pg.commit()
    
    hub_cur.close()
    hub_pg.close()
    
    print("\n\n=== CORPUS CANONICALIZATION COMPLETE ===")
    print("\nCanonical files now in src/canon/:")
    for root, dirs, files in os.walk("src/canon"):
        for f in sorted(files):
            if f.endswith('.py'):
                path = os.path.join(root, f)
                size = os.path.getsize(path)
                with open(path, 'r') as fh:
                    lines = fh.read().count('\n') + 1
                rel = path.replace('src/canon/', '')
                print(f"  {rel:<50} | {lines:>5}L | {size:>7} bytes")


if __name__ == "__main__":
    canonicalize_from_corpus()
