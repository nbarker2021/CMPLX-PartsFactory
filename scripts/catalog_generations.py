#!/usr/bin/env python3
"""
Catalog Generations — extract the architectural fossil record from archive-staging.

Samples UUID directories, identifies project types, harvests READMEs/manifests,
and builds a capability catalog.

Usage:
    python scripts/catalog_generations.py --sample 50
    python scripts/catalog_generations.py --catalog
    python scripts/catalog_generations.py --reports
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

ARCHIVE_ROOT = "D:/Manny Unification 2/output/archive-staging"
REPORTS_ROOT = "D:/Manny Unification 2/output/reports"

# Project type detectors based on filenames and directory names
PROJECT_SIGNATURES = {
    "snapos": ["agent_center.py", "agent_mgmt.py", "snapos", "atomic.py", "build_all.py"],
    "lattice_system": ["lattice_system_base", "lattice_ai", "shelling.py", "hash_system.py"],
    "agrm": ["agrm_core.py", "agrm/", "mdhg_hash.py", "hierarchy.py"],
    "cqe": ["cqe_unified", "cqe_runtime", "cqe_complete", "cqe/"],
    "morphonic": ["morphonic", "geo_ops_controller", "viewer24_probe"],
    "speedlight": ["speedlight", "speedlight_controller"],
    "mmdb": ["mmdb_ingest", "mmdb_embedding"],
    "e8_tools": ["unify_e8.py", "detect_version.py", "merge_versions.py"],
    "snap_configs": [".json5", "SnapScratchBoot", "SnapDocTrail", "AGRM_SessionOrigin"],
    "ml_model": ["weights.th", "config.json", "vocabulary/tokens.txt"],
    "docker_build": ["Dockerfile", "docker-compose", "launch.sh"],
    "experiment_log": ["Experiment_Database", "conversation_transcript", "Brainstorming"],
    "tsp_benchmark": [".tsp"],
}


@dataclass
class GenerationRecord:
    uuid: str
    file_count: int
    total_size: int
    project_types: list[str]
    has_readme: bool
    has_manifest: bool
    readme_snippet: str
    top_files: list[str]
    depth: int


def detect_project_types(files: list[str]) -> list[str]:
    types = []
    file_str = " ".join(files).lower()
    for proj, sigs in PROJECT_SIGNATURES.items():
        if any(sig.lower() in file_str for sig in sigs):
            types.append(proj)
    return types if types else ["unknown"]


def harvest_readme(path: str, max_chars: int = 500) -> str:
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


def analyze_generation(uuid: str) -> GenerationRecord | None:
    path = os.path.join(ARCHIVE_ROOT, uuid)
    if not os.path.isdir(path):
        return None
    
    files = []
    total_size = 0
    max_depth = 0
    has_manifest = False
    
    for root, dirs, filenames in os.walk(path):
        depth = os.path.relpath(root, path).count(os.sep)
        max_depth = max(max_depth, depth)
        for f in filenames:
            rel = os.path.relpath(os.path.join(root, f), path)
            files.append(rel)
            try:
                total_size += os.path.getsize(os.path.join(root, f))
            except Exception:
                pass
            if "manifest" in f.lower():
                has_manifest = True
    
    types = detect_project_types(files)
    readme = harvest_readme(path)
    has_readme = bool(readme)
    
    return GenerationRecord(
        uuid=uuid,
        file_count=len(files),
        total_size=total_size,
        project_types=types,
        has_readme=has_readme,
        has_manifest=has_manifest,
        readme_snippet=readme,
        top_files=files[:10],
        depth=max_depth,
    )


def sample_generations(count: int = 50) -> list[GenerationRecord]:
    import random
    entries = [e for e in os.listdir(ARCHIVE_ROOT) if os.path.isdir(os.path.join(ARCHIVE_ROOT, e))]
    random.seed(2026)
    # Stratified: some from start, middle, end, and random
    sample = entries[:count//4] + entries[len(entries)//2:len(entries)//2+count//4]
    sample += entries[-count//4:] + random.sample(entries, count//4)
    sample = list(dict.fromkeys(sample))[:count]  # dedupe and limit
    
    results = []
    for i, uuid in enumerate(sample):
        rec = analyze_generation(uuid)
        if rec:
            results.append(rec)
        if (i + 1) % 10 == 0:
            print(f"  ... analyzed {i+1}/{len(sample)}")
    return results


def print_catalog(records: list[GenerationRecord]) -> str:
    import io
    buf = io.StringIO()
    
    buf.write(f"\n=== GENERATION CATALOG ({len(records)} sampled) ===\n\n")
    
    # Project type distribution
    type_counts = {}
    for rec in records:
        for t in rec.project_types:
            type_counts[t] = type_counts.get(t, 0) + 1
    
    buf.write("--- Project Type Distribution ---\n")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        buf.write(f"  {c:>3}x  {t}\n")
    
    # README harvests
    buf.write("\n--- READMEs Harvested ---\n")
    for rec in records:
        if rec.has_readme:
            buf.write(f"\n[{rec.uuid}] types={','.join(rec.project_types)} files={rec.file_count}\n")
            snippet = rec.readme_snippet[:200].encode('ascii', 'replace').decode('ascii')
            buf.write(f"  {snippet}...\n")
    
    # Largest generations
    buf.write("\n--- Largest Generations ---\n")
    for rec in sorted(records, key=lambda x: -x.total_size)[:10]:
        buf.write(f"  {rec.total_size:>10,} bytes  {rec.file_count:>4} files  {','.join(rec.project_types):20s}  {rec.uuid}\n")
    
    # Deepest generations
    buf.write("\n--- Deepest Generations ---\n")
    for rec in sorted(records, key=lambda x: -x.depth)[:10]:
        buf.write(f"  depth={rec.depth:>2}  {rec.file_count:>4} files  {','.join(rec.project_types):20s}  {rec.uuid}\n")
    
    return buf.getvalue()


def analyze_reports() -> None:
    print(f"\n=== REPORTS DIRECTORY ===")
    if not os.path.isdir(REPORTS_ROOT):
        print("Reports directory not found")
        return
    
    for root, dirs, files in os.walk(REPORTS_ROOT):
        depth = os.path.relpath(root, REPORTS_ROOT).count(os.sep)
        if depth > 2:
            dirs[:] = []  # don't go deeper
            continue
        rel = os.path.relpath(root, REPORTS_ROOT)
        if files:
            print(f"\n[{rel}]")
            for f in sorted(files)[:15]:
                size = os.path.getsize(os.path.join(root, f))
                print(f"  {size:>10,} bytes  {f}")
            if len(files) > 15:
                print(f"  ... ({len(files)-15} more)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Catalog Generations")
    parser.add_argument("--sample", type=int, default=50, help="Number of UUID dirs to sample")
    parser.add_argument("--catalog", action="store_true", help="Print catalog from existing sample")
    parser.add_argument("--reports", action="store_true", help="Analyze reports directory")
    args = parser.parse_args()
    
    if args.reports:
        analyze_reports()
        return 0
    
    print(f"Sampling {args.sample} generations from archive-staging...")
    records = sample_generations(args.sample)
    catalog_text = print_catalog(records)
    
    # Write catalog to file
    catalog_path = Path("docs/GENERATION_CATALOG.md")
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    with open(catalog_path, "w", encoding="utf-8") as f:
        f.write(catalog_text)
    print(catalog_text)
    
    # Save to JSON for later analysis
    out_path = Path("data/generation_catalog_sample.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in records], f, indent=2, default=str)
    print(f"\nSaved catalog to {catalog_path}")
    print(f"Saved JSON to {out_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
