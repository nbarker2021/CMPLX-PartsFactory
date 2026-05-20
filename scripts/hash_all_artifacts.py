#!/usr/bin/env python3
"""
Compute SHA-256 hashes for all artifacts in artifact.source that lack them.
"""
import psycopg2
import hashlib
import os
from datetime import datetime, timezone

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


def compute_sha256(path):
    try:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None


def hash_batch(batch_size=2000):
    pg = psycopg2.connect(CACHE_DSN)
    
    count_cur = pg.cursor()
    count_cur.execute("SELECT COUNT(*) FROM artifact.source WHERE sha256 IS NULL OR sha256 = ''")
    total_missing = count_cur.fetchone()[0]
    count_cur.close()
    print(f"Computing hashes for {total_missing:,} artifacts...")
    
    # Use regular cursor with fetchmany
    stream_cur = pg.cursor()
    stream_cur.execute("""
        SELECT id, host_path, root_label
        FROM artifact.source
        WHERE sha256 IS NULL OR sha256 = ''
        ORDER BY root_label, id
    """)
    
    update_cur = pg.cursor()
    processed = 0
    hashed = 0
    failed = 0
    skipped = 0
    
    while True:
        rows = stream_cur.fetchmany(batch_size)
        if not rows:
            break
        
        for row in rows:
            file_id, host_path, root_label = row
            container_path = translate_path(host_path)
            
            if not container_path or not os.path.exists(container_path):
                skipped += 1
                update_cur.execute("""
                    UPDATE artifact.source SET sha256 = NULL, updated_at = %s WHERE id = %s
                """, (datetime.now(timezone.utc).isoformat(), file_id))
            else:
                file_hash = compute_sha256(container_path)
                if file_hash:
                    hashed += 1
                    update_cur.execute("""
                        UPDATE artifact.source SET sha256 = %s, updated_at = %s WHERE id = %s
                    """, (file_hash, datetime.now(timezone.utc).isoformat(), file_id))
                else:
                    failed += 1
                    update_cur.execute("""
                        UPDATE artifact.source SET sha256 = NULL, updated_at = %s WHERE id = %s
                    """, (datetime.now(timezone.utc).isoformat(), file_id))
            
            processed += 1
        
        pg.commit()
        
        if processed % 10000 == 0:
            pct = processed / total_missing * 100
            print(f"  {processed:,} / {total_missing:,} ({pct:.1f}%) | Hashed: {hashed:,} | Failed: {failed:,} | Skipped: {skipped:,}")
    
    stream_cur.close()
    update_cur.close()
    
    stats_cur = pg.cursor()
    stats_cur.execute("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN sha256 IS NOT NULL AND sha256 != '' THEN 1 ELSE 0 END) as hashed
        FROM artifact.source
    """)
    row = stats_cur.fetchone()
    print(f"\nComplete!")
    print(f"  Total artifacts: {row[0]:,}")
    print(f"  With SHA-256: {row[1]:,} ({row[1]/row[0]*100:.1f}%)")
    print(f"  Processed this run: {processed:,}")
    print(f"  Successfully hashed: {hashed:,}")
    print(f"  Failed to hash: {failed:,}")
    print(f"  Skipped (not found): {skipped:,}")
    stats_cur.close()
    pg.close()


if __name__ == "__main__":
    hash_batch()
