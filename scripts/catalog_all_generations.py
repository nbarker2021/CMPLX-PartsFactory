#!/usr/bin/env python3
"""
Catalog All Generations — production-scale indexer for all 13,634 archive-staging UUID dirs.

Processes every UUID directory in Manny output/archive-staging:
- Project type classification
- Metadata extraction (file count, size, depth, readme, manifest)
- SQLite index with batched inserts
- Aggregate statistics

Usage:
    python scripts/catalog_all_generations.py --scan
    python scripts/catalog_all_generations.py --report
    python scripts/catalog_all_generations.py --best <project_type>
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path

ARCHIVE_ROOT = "D:/Manny Unification 2/output/archive-staging"
DB_PATH = "data/generation_master_catalog.sqlite"
BATCH_SIZE = 500

# Project type detectors
PROJECT_SIGNATURES = {
    "snapos": ["agent_center.py", "agent_mgmt.py", "snapos", "atomic.py", "build_all.py"],
    "lattice_system": ["lattice_system_base", "lattice_ai", "shelling.py", "hash_system.py", "safe_cube"],
    "agrm": ["agrm_core.py", "agrm/", "mdhg_hash.py", "hierarchy.py", "sweep.py", "beam_search"],
    "cqe": ["cqe_unified", "cqe_runtime", "cqe_complete", "cqe/", "cqe_governance", "cqe_math"],
    "morphonic": ["morphonic", "geo_ops_controller", "viewer24_probe", "morphonic_regression"],
    "speedlight": ["speedlight", "speedlight_controller", "speedlight_miner"],
    "mmdb": ["mmdb_ingest", "mmdb_embedding", "mmdb_client"],
    "e8_tools": ["unify_e8.py", "detect_version.py", "merge_versions.py", "rewrite_imports.py"],
    "snap_configs": [".json5", "SnapScratchBoot", "SnapDocTrail", "AGRM_SessionOrigin", "SnapTrust"],
    "ml_model": ["weights.th", "config.json", "vocabulary/tokens.txt", "model.ckpt"],
    "docker_build": ["Dockerfile", "docker-compose", "launch.sh", ".dockerignore"],
    "experiment_log": ["Experiment_Database", "conversation_transcript", "Brainstorming", "experiment"],
    "tsp_benchmark": [".tsp"],
    "test_harness": ["test_", "harness", "run_checks.py", "run_all.py"],
    "documentation": [".md", "README", "SPEC.md", "docs/"],
}


@dataclass
class GenerationRecord:
    uuid: str
    file_count: int
    total_size: int
    max_depth: int
    project_types: str
    has_readme: bool
    has_manifest: bool
    has_dockerfile: bool
    has_requirements: bool
    has_setup_py: bool
    top_level_dirs: str
    top_level_files: str
    readme_snippet: str


def detect_project_types(files: list[str]) -> list[str]:
    types = []
    file_str = " ".join(files).lower()
    for proj, sigs in PROJECT_SIGNATURES.items():
        if any(sig.lower() in file_str for sig in sigs):
            types.append(proj)
    return types if types else ["unknown"]


def harvest_readme(path: str, max_chars: int = 300) -> str:
    for name in ["README.md", "README.txt", "README", "readme.md"]:
        readme_path = os.path.join(path, name)
        if os.path.isfile(readme_path):
            try:
                with open(readme_path, "r", encoding="utf-8", errors="replace") as f:
                    return f.read(max_chars).replace("\n", " ")[:max_chars]
            except Exception:
                pass
    # Search one level deep
    for root, dirs, files in os.walk(path):
        if root != path and os.path.relpath(root, path).count(os.sep) > 1:
            break
        for name in files:
            if name.lower().startswith("readme"):
                try:
                    with open(os.path.join(root, name), "r", encoding="utf-8", errors="replace") as f:
                        return f.read(max_chars).replace("\n", " ")[:max_chars]
                except Exception:
                    pass
    return ""


def analyze_generation(uuid: str) -> GenerationRecord:
    path = os.path.join(ARCHIVE_ROOT, uuid)
    
    files = []
    total_size = 0
    max_depth = 0
    has_manifest = False
    has_dockerfile = False
    has_requirements = False
    has_setup_py = False
    top_dirs = []
    top_files = []
    
    try:
        for entry in os.listdir(path):
            full = os.path.join(path, entry)
            if os.path.isfile(full):
                top_files.append(entry)
            elif os.path.isdir(full) and entry != ".git":
                top_dirs.append(entry)
    except Exception:
        pass
    
    for dirpath, dirnames, filenames in os.walk(path):
        depth = os.path.relpath(dirpath, path).count(os.sep)
        max_depth = max(max_depth, depth)
        
        for f in filenames:
            rel = os.path.relpath(os.path.join(dirpath, f), path)
            files.append(rel)
            try:
                size = os.path.getsize(os.path.join(dirpath, f))
                total_size += size
            except (OSError, PermissionError):
                pass
            if "manifest" in f.lower():
                has_manifest = True
            if f.lower() == "dockerfile":
                has_dockerfile = True
            if f.lower() == "requirements.txt":
                has_requirements = True
            if f.lower() == "setup.py":
                has_setup_py = True
        
        # Speed limit: don't go deeper than 4 levels
        if depth >= 4:
            del dirnames[:]
    
    types = detect_project_types(files)
    readme = harvest_readme(path)
    
    return GenerationRecord(
        uuid=uuid,
        file_count=len(files),
        total_size=total_size,
        max_depth=max_depth,
        project_types=",".join(types),
        has_readme=bool(readme),
        has_manifest=has_manifest,
        has_dockerfile=has_dockerfile,
        has_requirements=has_requirements,
        has_setup_py=has_setup_py,
        top_level_dirs=",".join(top_dirs),
        top_level_files=",".join(top_files),
        readme_snippet=readme,
    )


def init_db() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS generations (
        uuid TEXT PRIMARY KEY,
        file_count INTEGER,
        total_size INTEGER,
        max_depth INTEGER,
        project_types TEXT,
        has_readme INTEGER,
        has_manifest INTEGER,
        has_dockerfile INTEGER,
        has_requirements INTEGER,
        has_setup_py INTEGER,
        top_level_dirs TEXT,
        top_level_files TEXT,
        readme_snippet TEXT
    )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_gen_type ON generations(project_types)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_gen_size ON generations(total_size)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_gen_files ON generations(file_count)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_gen_readme ON generations(has_readme)")
    conn.commit()
    return conn


def scan_all() -> None:
    print("=== Cataloging All Generations ===")
    if not Path(ARCHIVE_ROOT).exists():
        print(f"ERROR: {ARCHIVE_ROOT} does not exist")
        return
    
    entries = [e for e in os.listdir(ARCHIVE_ROOT) if os.path.isdir(os.path.join(ARCHIVE_ROOT, e))]
    total = len(entries)
    print(f"Found {total} UUID directories")
    print("Processing... (this will take several minutes)")
    
    conn = init_db()
    batch = []
    
    for i, uuid in enumerate(entries):
        rec = analyze_generation(uuid)
        batch.append((
            rec.uuid, rec.file_count, rec.total_size, rec.max_depth,
            rec.project_types, int(rec.has_readme), int(rec.has_manifest),
            int(rec.has_dockerfile), int(rec.has_requirements), int(rec.has_setup_py),
            rec.top_level_dirs, rec.top_level_files, rec.readme_snippet
        ))
        
        if len(batch) >= BATCH_SIZE:
            conn.executemany("""
                INSERT OR REPLACE INTO generations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
            """, batch)
            conn.commit()
            batch = []
        
        if (i + 1) % 1000 == 0:
            print(f"  ... {i+1}/{total} done ({(i+1)/total*100:.1f}%)")
    
    if batch:
        conn.executemany("""
            INSERT OR REPLACE INTO generations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, batch)
        conn.commit()
    
    conn.close()
    print(f"\nDone. Catalog saved to {DB_PATH}")


def print_report() -> None:
    if not Path(DB_PATH).exists():
        print(f"No catalog found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    cur = conn.execute("SELECT COUNT(*) as cnt FROM generations")
    total = cur.fetchone()["cnt"]
    
    print(f"\n=== GENERATION MASTER CATALOG ===")
    print(f"Total UUID dirs cataloged: {total}\n")
    
    # Project type distribution
    print("--- Project Type Distribution ---")
    type_counts = {}
    cur = conn.execute("SELECT project_types FROM generations")
    for row in cur:
        for t in row["project_types"].split(","):
            type_counts[t] = type_counts.get(t, 0) + 1
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {c:>5} dirs  {t}")
    
    # Size distribution
    print("\n--- Size Distribution ---")
    cur = conn.execute("""
        SELECT 
            CASE 
                WHEN total_size < 1024 THEN '<1 KB'
                WHEN total_size < 10240 THEN '1-10 KB'
                WHEN total_size < 102400 THEN '10-100 KB'
                WHEN total_size < 1048576 THEN '100 KB-1 MB'
                WHEN total_size < 10485760 THEN '1-10 MB'
                ELSE '>10 MB'
            END as size_bucket,
            COUNT(*) as cnt
        FROM generations
        GROUP BY size_bucket
        ORDER BY cnt DESC
    """)
    for row in cur:
        print(f"  {row['cnt']:>5} dirs  {row['size_bucket']}")
    
    # README availability
    print("\n--- README Availability ---")
    cur = conn.execute("SELECT has_readme, COUNT(*) as cnt FROM generations GROUP BY has_readme")
    for row in cur:
        status = "Has README" if row["has_readme"] else "No README"
        print(f"  {row['cnt']:>5} dirs  {status}")
    
    # Manifest availability
    print("\n--- Manifest Availability ---")
    cur = conn.execute("SELECT has_manifest, COUNT(*) as cnt FROM generations GROUP BY has_manifest")
    for row in cur:
        status = "Has manifest" if row["has_manifest"] else "No manifest"
        print(f"  {row['cnt']:>5} dirs  {status}")
    
    # Docker/build artifacts
    print("\n--- Build Artifacts ---")
    cur = conn.execute("SELECT has_dockerfile, COUNT(*) as cnt FROM generations GROUP BY has_dockerfile")
    docker = {0: 0, 1: 0}
    for row in cur:
        docker[row["has_dockerfile"]] = row["cnt"]
    print(f"  {docker[1]:>5} dirs  Has Dockerfile")
    
    cur = conn.execute("SELECT has_requirements, COUNT(*) as cnt FROM generations GROUP BY has_requirements")
    req = {0: 0, 1: 0}
    for row in cur:
        req[row["has_requirements"]] = row["cnt"]
    print(f"  {req[1]:>5} dirs  Has requirements.txt")
    
    cur = conn.execute("SELECT has_setup_py, COUNT(*) as cnt FROM generations GROUP BY has_setup_py")
    setup = {0: 0, 1: 0}
    for row in cur:
        setup[row["has_setup_py"]] = row["cnt"]
    print(f"  {setup[1]:>5} dirs  Has setup.py")
    
    # Largest generations by type
    print("\n--- Largest Generations by Type ---")
    for ptype in ["lattice_system", "agrm", "cqe", "snapos", "morphonic", "docker_build"]:
        cur = conn.execute("""
            SELECT uuid, file_count, total_size, has_readme
            FROM generations
            WHERE project_types LIKE ?
            ORDER BY total_size DESC
            LIMIT 3
        """, (f"%{ptype}%",))
        rows = cur.fetchall()
        if rows:
            print(f"\n  {ptype}:")
            for row in rows:
                size_mb = row["total_size"] / (1024 * 1024)
                readme = "[README]" if row["has_readme"] else ""
                print(f"    {size_mb:>6.1f} MB  {row['file_count']:>4} files  {row['uuid'][:20]}...  {readme}")
    
    conn.close()


def find_best_variants(project_type: str) -> None:
    if not Path(DB_PATH).exists():
        print(f"No catalog found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    print(f"\n=== BEST VARIANTS: {project_type} ===\n")
    
    # Best = largest with README and manifest
    cur = conn.execute("""
        SELECT uuid, file_count, total_size, has_readme, has_manifest, readme_snippet, top_level_files
        FROM generations
        WHERE project_types LIKE ?
        ORDER BY 
            (has_readme + has_manifest) DESC,
            total_size DESC
        LIMIT 10
    """, (f"%{project_type}%",))
    
    for row in cur:
        size_mb = row["total_size"] / (1024 * 1024)
        readme = "[README]" if row["has_readme"] else ""
        manifest = "[MANIFEST]" if row["has_manifest"] else ""
        print(f"  {size_mb:>6.1f} MB  {row['file_count']:>4} files  {readme} {manifest}")
        print(f"    UUID: {row['uuid']}")
        if row["readme_snippet"]:
            print(f"    {row['readme_snippet'][:150]}...")
        print()
    
    conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Catalog All Generations")
    parser.add_argument("--scan", action="store_true", help="Catalog all UUID dirs")
    parser.add_argument("--report", action="store_true", help="Print aggregate report")
    parser.add_argument("--best", help="Find best variants of a project type")
    args = parser.parse_args()
    
    if args.scan:
        scan_all()
    
    if args.report or args.scan:
        print_report()
    
    if args.best:
        find_best_variants(args.best)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
