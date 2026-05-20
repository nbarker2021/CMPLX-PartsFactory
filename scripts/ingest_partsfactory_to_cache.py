#!/usr/bin/env python3
"""
Ingest PartsFactory real files into cache postgres (unification_aggregator).

Populates:
- artifact.source (all real files)
- catalog.code_source (code files with AST metadata)
- ingest.queue (optional: queue for further processing)
"""
import sqlite3
import psycopg2
import uuid
import json
import os
import ast
from datetime import datetime, timezone

YARD_DB = "data/yard_inventory.sqlite"
CACHE_DSN = "postgresql://research:research_hub_dev@postgres-cache:5432/unification_aggregator"
SPACE_TAG = "partsfactory"


def detect_artifact_kind(extension, basename):
    """Map file extension to artifact_kind."""
    ext = (extension or '').lower()
    if ext in ('.zip', '.tar', '.gz', '.bz2', '.xz', '.7z', '.rar'):
        return 'archive'
    if ext in ('.sql', '.ddl'):
        return 'sql_text'
    if ext in ('.db', '.sqlite', '.sqlite3', '.mdb'):
        return 'database'
    if ext in ('.json', '.jsonl', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf'):
        return 'data_store_text'
    if ext in ('.txt', '.md', '.rst', '.csv', '.tsv', '.log'):
        return 'data_store_text'
    return 'other'


def detect_language(extension):
    """Map extension to programming language."""
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'jsx',
        '.tsx': 'tsx',
        '.sql': 'sql',
        '.sh': 'bash',
        '.ps1': 'powershell',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'scss',
    }
    return ext_map.get((extension or '').lower(), 'unknown')


def analyze_python_file(path):
    """Extract AST metadata from Python file."""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
        
        tree = ast.parse(source)
        
        funcs = []
        classes = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                funcs.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ''
                imports.append(mod)
        
        lines = source.count('\n') + (1 if source and not source.endswith('\n') else 0)
        return {
            'line_count': lines,
            'function_names': funcs,
            'class_names': classes,
            'imports': imports,
            'entry_points': [],
            'exports': []
        }
    except Exception as e:
        return {
            'line_count': 0,
            'function_names': [],
            'class_names': [],
            'imports': [],
            'entry_points': [],
            'exports': [],
            'error': str(e)
        }


def ingest_files(batch_size=500):
    """Main ingestion loop."""
    # Connect to SQLite
    sq = sqlite3.connect(YARD_DB)
    sq.row_factory = sqlite3.Row
    sq_cur = sq.cursor()
    
    # Connect to PostgreSQL
    pg = psycopg2.connect(CACHE_DSN)
    pg_cur = pg.cursor()
    
    # Get total count
    sq_cur.execute("""
        SELECT COUNT(*) 
        FROM file_inventory fi
        JOIN file_classification fc ON fi.file_id = fc.file_id
        WHERE fc.classification IN ('real', 'canonical')
    """)
    total = sq_cur.fetchone()[0]
    print(f"Ingesting {total:,} PartsFactory real files into cache postgres...")
    
    # Stream files
    sq_cur.execute("""
        SELECT 
            fi.file_id,
            fi.abs_path,
            fi.rel_path,
            fi.basename,
            fi.extension,
            fi.size_bytes,
            fi.mtime,
            fi.content_hash,
            fc.classification
        FROM file_inventory fi
        JOIN file_classification fc ON fi.file_id = fc.file_id
        WHERE fc.classification IN ('real', 'canonical')
        ORDER BY fi.extension, fi.basename
    """)
    
    artifact_batch = []
    code_batch = []
    processed = 0
    code_files = 0
    
    for row in sq_cur:
        file_id, abs_path, rel_path, basename, ext, size, mtime, content_hash, classification = row
        
        # Generate UUID
        file_uuid = str(uuid.uuid4())
        
        # Determine kind
        kind = detect_artifact_kind(ext, basename)
        lang = detect_language(ext)
        
        # Build source_uri
        source_uri = f"file://{SPACE_TAG}/{rel_path}"
        
        # Convert mtime to ISO if present
        mtime_iso = None
        if mtime:
            try:
                mtime_iso = datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
            except:
                pass
        
        artifact_batch.append((
            file_uuid,
            source_uri,
            SPACE_TAG,
            abs_path,
            None,  # container_path
            rel_path,
            None,  # parent_source_id
            kind,
            'filesystem',
            ext,
            size,
            mtime_iso,
            content_hash,
            'registered',
            '{}',
            'fact',
            0.8,
            datetime.now(timezone.utc).isoformat(),
            datetime.now(timezone.utc).isoformat()
        ))
        
        # If Python, analyze AST
        if lang == 'python' and os.path.exists(abs_path):
            meta = analyze_python_file(abs_path)
            code_files += 1
            
            code_batch.append((
                file_uuid,
                lang,
                SPACE_TAG,
                meta['line_count'],
                json.dumps(meta['function_names']),
                json.dumps(meta['class_names']),
                json.dumps(meta['imports']),
                json.dumps(meta['entry_points']),
                json.dumps(meta['exports']),
                '',  # capabilities_summary
                None,  # temporal_beacon_end
                None,  # temporal_context
                'evidence',
                'claim',
                None,  # skip_reason
                datetime.now(timezone.utc).isoformat()
            ))
        
        # Batch insert
        if len(artifact_batch) >= batch_size:
            pg_cur.executemany("""
                INSERT INTO artifact.source (
                    id, source_uri, root_label, host_path, container_path, relative_path,
                    parent_source_id, artifact_kind, storage_kind, extension, size_bytes,
                    mtime, sha256, discovery_state, metadata_json, label, confidence,
                    discovered_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, artifact_batch)
            
            if code_batch:
                pg_cur.executemany("""
                    INSERT INTO catalog.code_source (
                        source_id, language, system_of_origin, line_count,
                        function_names, class_names, imports, entry_points, exports,
                        capabilities_summary, temporal_beacon_end, temporal_context,
                        implement_status, confidence, skip_reason, profiled_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_id) DO NOTHING
                """, code_batch)
            
            pg.commit()
            processed += len(artifact_batch)
            artifact_batch = []
            code_batch = []
            
            if processed % 5000 == 0:
                print(f"  Processed {processed:,} / {total:,} ({code_files} code files analyzed)")
    
    # Final batch
    if artifact_batch:
        pg_cur.executemany("""
            INSERT INTO artifact.source (
                id, source_uri, root_label, host_path, container_path, relative_path,
                parent_source_id, artifact_kind, storage_kind, extension, size_bytes,
                mtime, sha256, discovery_state, metadata_json, label, confidence,
                discovered_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO NOTHING
        """, artifact_batch)
        
        if code_batch:
            pg_cur.executemany("""
                INSERT INTO catalog.code_source (
                    source_id, language, system_of_origin, line_count,
                    function_names, class_names, imports, entry_points, exports,
                    capabilities_summary, temporal_beacon_end, temporal_context,
                    implement_status, confidence, skip_reason, profiled_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (source_id) DO NOTHING
            """, code_batch)
        
        pg.commit()
        processed += len(artifact_batch)
    
    # Update statistics
    pg_cur.execute("""
        SELECT COUNT(*) FROM artifact.source WHERE root_label = %s
    """, (SPACE_TAG,))
    total_artifacts = pg_cur.fetchone()[0]
    
    pg_cur.execute("""
        SELECT COUNT(*) FROM catalog.code_source WHERE system_of_origin = %s
    """, (SPACE_TAG,))
    total_code = pg_cur.fetchone()[0]
    
    print(f"\nIngestion complete!")
    print(f"  artifact.source: {total_artifacts:,} rows")
    print(f"  catalog.code_source: {total_code:,} rows")
    print(f"  Code files analyzed with AST: {code_files:,}")
    
    sq_cur.close()
    sq.close()
    pg_cur.close()
    pg.close()


if __name__ == "__main__":
    ingest_files()
