#!/usr/bin/env python3
"""Migrate canonicalization data from SQLite yard_inventory to PostgreSQL unification_hub."""
import sqlite3
import psycopg2
import json

SQLITE_PATH = "data/yard_inventory.sqlite"
PG_DSN = "postgresql://research:research_hub_dev@postgres:5432/unification_hub"


def migrate():
    sq = sqlite3.connect(SQLITE_PATH)
    sq.row_factory = sqlite3.Row

    pg = psycopg2.connect(PG_DSN)
    cur = pg.cursor()

    # Migrate clusters
    sq_cur = sq.cursor()
    sq_cur.execute("SELECT cluster_id, tool_name, ast_hash, status, notes, created_at FROM cluster")
    clusters = sq_cur.fetchall()
    print(f"Found {len(clusters)} clusters in SQLite")

    for row in clusters:
        cluster_id, tool_name, ast_hash, status, notes, created_at = row
        cur.execute(
            """INSERT INTO canonical_clusters (cluster_key, basename, description, created_at, updated_at)
               VALUES (%s, %s, %s, %s, %s)
               ON CONFLICT (cluster_key) DO UPDATE SET
                 description = EXCLUDED.description,
                 updated_at = NOW()
               RETURNING id""",
            (cluster_id, tool_name, notes or f"Cluster for {tool_name}", created_at, created_at)
        )
        pg_cluster_id = cur.fetchone()[0]
        print(f"  Cluster '{tool_name}' -> PG id {pg_cluster_id}")

        # Get cluster members
        sq_cur2 = sq.cursor()
        sq_cur2.execute(
            "SELECT artifact_id, rank, reason FROM cluster_member WHERE cluster_id = ?",
            (cluster_id,)
        )
        members = {m[0]: (m[1], m[2]) for m in sq_cur2.fetchall()}
        print(f"    Found {len(members)} cluster members")

        # Migrate artifacts for this cluster
        for artifact_id, (rank, reason) in members.items():
            sq_cur3 = sq.cursor()
            sq_cur3.execute(
                "SELECT artifact_id, rel_path, abs_path, basename, size_bytes, lines, content_hash, ast_hash, top_level, repo_tag, scan_batch FROM artifact WHERE artifact_id = ?",
                (artifact_id,)
            )
            art = sq_cur3.fetchone()
            if not art:
                print(f"    WARNING: artifact {artifact_id} not found")
                continue

            artifact_id, rel_path, abs_path, basename, size_bytes, lines, content_hash, art_ast_hash, top_level, repo_tag, scan_batch = art
            cur.execute(
                """INSERT INTO canonical_artifacts
                   (cluster_id, source_path, content_hash, file_size, line_count, language, system_name, variant_index, is_canonical, canonical_reason, created_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT DO NOTHING""",
                (pg_cluster_id, abs_path, content_hash, size_bytes, lines,
                 'python' if basename.endswith('.py') else 'unknown',
                 repo_tag or 'unknown', rank, False, reason or '', scan_batch)
            )

        # Mark canonical artifact
        sq_cur4 = sq.cursor()
        sq_cur4.execute(
            "SELECT tool_name, cluster_id, rel_path, content_hash, lines, created_at, derived_from FROM canonical_file WHERE cluster_id = ?",
            (cluster_id,)
        )
        canonical = sq_cur4.fetchone()
        if canonical:
            c_tool_name, c_cluster_id, c_rel_path, c_hash, c_lines, c_created, c_derived = canonical
            cur.execute(
                """UPDATE canonical_artifacts
                   SET is_canonical = TRUE,
                       canonical_reason = 'Canonical chosen from variants with full lineage'
                   WHERE cluster_id = %s AND content_hash = %s""",
                (pg_cluster_id, c_hash)
            )
            rows_updated = cur.rowcount
            print(f"    Marked canonical: {c_rel_path} (hash: {c_hash}, updated: {rows_updated})")

            # Log the canonicalization action
            cur.execute(
                """INSERT INTO canonicalization_log (cluster_key, action, details, created_at)
                   VALUES (%s, %s, %s, %s)""",
                (cluster_id, 'canonicalize', json.dumps({
                    'canonical_path': c_rel_path,
                    'content_hash': c_hash,
                    'lines': c_lines,
                    'derived_from_count': len(json.loads(c_derived)) if c_derived else 0
                }), c_created)
            )

    pg.commit()
    cur.close()
    pg.close()
    sq.close()
    print("\nMigration complete.")


if __name__ == "__main__":
    migrate()
