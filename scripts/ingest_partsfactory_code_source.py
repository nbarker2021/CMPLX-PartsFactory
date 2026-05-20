#!/usr/bin/env python3
"""
Populate catalog.code_source for PartsFactory files already in artifact.source.

Translates Windows paths to container paths and extracts Python AST metadata.
"""
import psycopg2
import json
import os
import ast
from datetime import datetime, timezone

CACHE_DSN = "postgresql://research:research_hub_dev@postgres-cache:5432/unification_aggregator"
SPACE_TAG = "partsfactory"


def translate_path(host_path):
    """Convert Windows D:/ path to container /mnt/d/ path."""
    if not host_path:
        return None
    # Handle D:/path -> /mnt/d/path
    if host_path.startswith('D:/') or host_path.startswith('d:/'):
        return '/mnt/d/' + host_path[3:]
    if host_path.startswith('D:\\\\') or host_path.startswith('d:\\\\'):
        return '/mnt/d/' + host_path[3:].replace('\\\\', '/')
    return host_path


def detect_language(extension):
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
        
        lines = source.count('\n')
        if source and not source.endswith('\n'):
            lines += 1
        
        return {
            'line_count': lines,
            'function_names': funcs,
            'class_names': classes,
            'imports': imports,
            'entry_points': [],
            'exports': []
        }
    except Exception as e:
        # Still count lines even if AST fails
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
            lines = source.count('\n')
            if source and not source.endswith('\n'):
                lines += 1
        except:
            lines = 0
        
        return {
            'line_count': lines,
            'function_names': [],
            'class_names': [],
            'imports': [],
            'entry_points': [],
            'exports': [],
            'error': str(e)
        }


def ingest_code_source(batch_size=500):
    """Process PartsFactory artifacts and populate catalog.code_source."""
    pg = psycopg2.connect(CACHE_DSN)
    pg_cur = pg.cursor()
    
    # Get all partsfactory artifacts that are code files
    pg_cur.execute("""
        SELECT id, host_path, extension
        FROM artifact.source
        WHERE root_label = %s
          AND artifact_kind = 'other'
          AND extension IN ('.py', '.js', '.ts', '.jsx', '.tsx', '.sql', '.sh', '.ps1', '.html', '.css', '.scss')
        ORDER BY extension, host_path
    """, (SPACE_TAG,))
    
    artifacts = pg_cur.fetchall()
    total = len(artifacts)
    print(f"Found {total:,} code files in partsfactory artifact.source")
    
    code_batch = []
    processed = 0
    analyzed = 0
    failed_paths = 0
    
    for row in artifacts:
        file_uuid, host_path, ext = row
        container_path = translate_path(host_path)
        
        lang = detect_language(ext)
        line_count = 0
        funcs = []
        classes = []
        imports = []
        
        if container_path and os.path.exists(container_path):
            if lang == 'python':
                meta = analyze_python_file(container_path)
                line_count = meta['line_count']
                funcs = meta['function_names']
                classes = meta['class_names']
                imports = meta['imports']
                analyzed += 1
            else:
                # Non-Python: just count lines
                try:
                    with open(container_path, 'r', encoding='utf-8', errors='replace') as f:
                        source = f.read()
                    line_count = source.count('\n')
                    if source and not source.endswith('\n'):
                        line_count += 1
                except:
                    line_count = 0
                analyzed += 1
        else:
            failed_paths += 1
        
        code_batch.append((
            file_uuid,
            lang,
            SPACE_TAG,
            line_count,
            json.dumps(funcs),
            json.dumps(classes),
            json.dumps(imports),
            json.dumps([]),  # entry_points
            json.dumps([]),  # exports
            '',  # capabilities_summary
            None,  # temporal_beacon_end
            None,  # temporal_context
            'evidence',
            'claim',
            None,  # skip_reason
            datetime.now(timezone.utc).isoformat()
        ))
        
        if len(code_batch) >= batch_size:
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
            processed += len(code_batch)
            code_batch = []
            
            if processed % 5000 == 0:
                print(f"  Processed {processed:,} / {total:,} ({analyzed} analyzed, {failed_paths} path failures)")
    
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
        processed += len(code_batch)
    
    # Verify
    pg_cur.execute("""
        SELECT COUNT(*) FROM catalog.code_source WHERE system_of_origin = %s
    """, (SPACE_TAG,))
    total_code = pg_cur.fetchone()[0]
    
    print(f"\nCode source ingestion complete!")
    print(f"  catalog.code_source: {total_code:,} rows")
    print(f"  Files analyzed: {analyzed:,}")
    print(f"  Path failures: {failed_paths:,}")
    
    pg_cur.close()
    pg.close()


if __name__ == "__main__":
    ingest_code_source()
