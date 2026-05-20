#!/usr/bin/env python3
"""
Phase 1-2: Extract evidence from cache postgres, build deduplication clusters.

Strategy:
1. Stream catalog.code_source (438K rows)
2. Cluster by basename + line_count_bucket (practical dedup for reimplemented files)
3. Cross-reference with artifact.source for paths and SHA-256
4. Store clusters in SQLite for analysis
"""
import sqlite3
import psycopg2
import json
import hashlib
from collections import defaultdict
import os

# Database connections
CACHE_DSN = "postgresql://research:research_hub_dev@postgres-cache:5432/unification_aggregator"
STAGING_DB = "data/evidence_dedupe.sqlite"

def ensure_staging_db():
    """Create SQLite staging database for deduplication analysis."""
    conn = sqlite3.connect(STAGING_DB)
    cur = conn.cursor()
    
    cur.executescript("""
        DROP TABLE IF EXISTS capability_cluster;
        DROP TABLE IF EXISTS evidence_file;
        
        CREATE TABLE evidence_file (
            file_id TEXT PRIMARY KEY,
            cluster_id TEXT,
            source_uri TEXT,
            host_path TEXT,
            relative_path TEXT,
            basename TEXT,
            system_of_origin TEXT,
            language TEXT,
            line_count INTEGER,
            size_bytes INTEGER,
            sha256 TEXT,
            function_names TEXT,
            class_names TEXT,
            imports TEXT,
            capabilities_summary TEXT,
            implement_status TEXT DEFAULT 'evidence',
            is_canonical_candidate INTEGER DEFAULT 0,
            dedupe_reason TEXT
        );
        
        CREATE TABLE capability_cluster (
            cluster_id TEXT PRIMARY KEY,
            basename TEXT NOT NULL,
            line_count_bucket TEXT,
            file_count INTEGER DEFAULT 0,
            systems TEXT,
            languages TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX idx_evidence_cluster ON evidence_file(cluster_id);
        CREATE INDEX idx_evidence_system ON evidence_file(system_of_origin);
        CREATE INDEX idx_evidence_sha256 ON evidence_file(sha256);
        CREATE INDEX idx_evidence_path ON evidence_file(relative_path);
        CREATE INDEX idx_evidence_basename ON evidence_file(basename);
    """)
    conn.commit()
    conn.close()
    print("Staging database created.")


def line_bucket(lc):
    """Bucket line counts into coarse ranges."""
    if lc is None:
        return 'unknown'
    if lc <= 10:
        return 'tiny'
    if lc <= 50:
        return 'small'
    if lc <= 150:
        return 'medium'
    if lc <= 500:
        return 'large'
    if lc <= 1500:
        return 'xlarge'
    return 'huge'


def cluster_key(basename, line_bucket_val):
    """Create cluster key from basename and line count bucket."""
    # Normalize basename
    base = basename or 'unknown'
    return f"{base}:{line_bucket_val}"


def extract_evidence(batch_size=20000):
    """Extract all code evidence from cache postgres into SQLite."""
    pg = psycopg2.connect(CACHE_DSN)
    pg_cur = pg.cursor()
    
    sq = sqlite3.connect(STAGING_DB)
    sq_cur = sq.cursor()
    
    # Count total
    pg_cur.execute("SELECT COUNT(*) FROM catalog.code_source")
    total = pg_cur.fetchone()[0]
    print(f"Extracting {total:,} code sources...")
    
    # Stream in batches
    pg_cur.execute("""
        SELECT 
            cs.source_id,
            s.source_uri,
            s.host_path,
            s.relative_path,
            split_part(s.relative_path, '/', -1) as basename,
            cs.system_of_origin,
            cs.language,
            cs.line_count,
            s.size_bytes,
            s.sha256,
            cs.function_names,
            cs.class_names,
            cs.imports,
            cs.capabilities_summary,
            cs.implement_status
        FROM catalog.code_source cs
        LEFT JOIN artifact.source s ON cs.source_id = s.id
        ORDER BY basename, cs.line_count DESC
    """)
    
    batch = []
    clusters = defaultdict(lambda: {
        'count': 0,
        'systems': set(),
        'languages': set(),
        'basename': '',
        'line_bucket': ''
    })
    
    processed = 0
    for row in pg_cur:
        (source_id, source_uri, host_path, rel_path, basename,
         system, language, line_count, size_bytes, sha256,
         funcs, classes, imports, capabilities, status) = row
        
        lb = line_bucket(line_count)
        ck = cluster_key(basename, lb)
        
        # Track cluster stats
        clusters[ck]['count'] += 1
        clusters[ck]['systems'].add(system or 'unknown')
        clusters[ck]['languages'].add(language or 'unknown')
        clusters[ck]['basename'] = basename or 'unknown'
        clusters[ck]['line_bucket'] = lb
        
        batch.append((
            str(source_id), ck, source_uri, host_path, rel_path, basename,
            system, language, line_count, size_bytes, sha256,
            json.dumps(funcs) if isinstance(funcs, (list, dict)) else funcs,
            json.dumps(classes) if isinstance(classes, (list, dict)) else classes,
            json.dumps(imports) if isinstance(imports, (list, dict)) else imports,
            capabilities, status, 0, None
        ))
        
        if len(batch) >= batch_size:
            sq_cur.executemany("""
                INSERT INTO evidence_file 
                (file_id, cluster_id, source_uri, host_path, relative_path, basename,
                 system_of_origin, language, line_count, size_bytes, sha256,
                 function_names, class_names, imports, capabilities_summary,
                 implement_status, is_canonical_candidate, dedupe_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            sq.commit()
            batch = []
            processed += batch_size
            if processed % 50000 == 0:
                print(f"  Processed {processed:,} / {total:,}")
    
    if batch:
        sq_cur.executemany("""
            INSERT INTO evidence_file 
            (file_id, cluster_id, source_uri, host_path, relative_path, basename,
             system_of_origin, language, line_count, size_bytes, sha256,
             function_names, class_names, imports, capabilities_summary,
             implement_status, is_canonical_candidate, dedupe_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, batch)
        sq.commit()
    
    print(f"Inserted {total:,} evidence files.")
    
    # Now create clusters
    print(f"Building {len(clusters):,} capability clusters...")
    cluster_rows = []
    for ck, stats in clusters.items():
        cluster_rows.append((
            ck, stats['basename'], stats['line_bucket'], stats['count'],
            json.dumps(sorted(stats['systems'])),
            json.dumps(sorted(stats['languages'])),
            f"{stats['basename']} ({stats['line_bucket']}) — {stats['count']} files across {len(stats['systems'])} systems"
        ))
    
    sq_cur.executemany("""
        INSERT INTO capability_cluster 
        (cluster_id, basename, line_count_bucket, file_count, systems, languages, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, cluster_rows)
    sq.commit()
    
    pg_cur.close()
    pg.close()
    sq_cur.close()
    sq.close()
    
    print("Phase 1 complete.")
    return len(clusters)


def analyze_clusters():
    """Print cluster analysis."""
    sq = sqlite3.connect(STAGING_DB)
    sq.row_factory = sqlite3.Row
    cur = sq.cursor()
    
    print("\n=== CLUSTER ANALYSIS ===")
    
    # Largest clusters
    print("\nTop 30 largest clusters (most duplicated files):")
    cur.execute("""
        SELECT cluster_id, basename, line_count_bucket, file_count, systems, description
        FROM capability_cluster
        ORDER BY file_count DESC
        LIMIT 30
    """)
    for row in cur.fetchall():
        systems = json.loads(row['systems'])
        print(f"  {row['file_count']:>5} | {row['basename']:<40} | {row['line_count_bucket']:<8} | {len(systems)} systems")
    
    # Files with identical SHA-256
    print("\nExact SHA-256 duplicates (where hash exists):")
    cur.execute("""
        SELECT sha256, COUNT(*) as c, 
               GROUP_CONCAT(DISTINCT system_of_origin) as systems,
               MIN(basename) as basename
        FROM evidence_file
        WHERE sha256 IS NOT NULL AND sha256 != ''
        GROUP BY sha256
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC
        LIMIT 15
    """)
    for row in cur.fetchall():
        print(f"  {row['c']:>3} copies | {row['basename']:<40} | {row['systems']}")
    
    # By system
    print("\nFiles per system:")
    cur.execute("""
        SELECT system_of_origin, COUNT(*) as c, 
               COUNT(DISTINCT basename) as unique_basenames,
               SUM(CASE WHEN sha256 IS NOT NULL THEN 1 ELSE 0 END) as hashed
        FROM evidence_file
        GROUP BY system_of_origin
        ORDER BY COUNT(*) DESC
    """)
    for row in cur.fetchall():
        pct = row['hashed'] / row['c'] * 100 if row['c'] > 0 else 0
        print(f"  {row['system_of_origin'] or 'unknown':>20}: {row['c']:>7} files | {row['unique_basenames']:>5} unique names | {pct:.1f}% hashed")
    
    # By line count bucket
    print("\nFiles by size bucket:")
    cur.execute("""
        SELECT 
            CASE 
                WHEN line_count IS NULL THEN 'unknown'
                WHEN line_count <= 10 THEN 'tiny'
                WHEN line_count <= 50 THEN 'small'
                WHEN line_count <= 150 THEN 'medium'
                WHEN line_count <= 500 THEN 'large'
                WHEN line_count <= 1500 THEN 'xlarge'
                ELSE 'huge'
            END as bucket,
            COUNT(*) as c, 
            COUNT(DISTINCT basename) as unique_names
        FROM evidence_file
        GROUP BY bucket
        ORDER BY c DESC
    """)
    for row in cur.fetchall():
        print(f"  {row['bucket']:<8}: {row['c']:>7} files | {row['unique_names']:>5} unique basenames")
    
    # Total clusters
    cur.execute("SELECT COUNT(*) FROM capability_cluster")
    total_clusters = cur.fetchone()[0]
    
    cur.execute("SELECT COUNT(*) FROM evidence_file WHERE sha256 IS NOT NULL AND sha256 != ''")
    total_hashed = cur.fetchone()[0]
    
    print(f"\nSummary: {total_clusters:,} clusters | {total_hashed:,} files with SHA-256")
    
    sq.close()


if __name__ == "__main__":
    ensure_staging_db()
    n_clusters = extract_evidence()
    analyze_clusters()
    print(f"\nDone. {n_clusters:,} clusters created from evidence.")
