"""
data-intel-api — data intelligence capsule for the Manny manifold.
Handles CSV, Parquet, Excel, SQLite, DuckDB profiling and analytics.
Registers with manny-manifold on startup.
"""
import asyncio
import json
import logging
import os
import traceback
from pathlib import Path
from typing import Any

import duckdb
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Security: API-key auth for all endpoints
_DATA_INTEL_API_KEY = os.environ.get("DATA_INTEL_API_KEY", "")

def _require_api_key(x_api_key: str = Header(default="")):
    if not _DATA_INTEL_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="DATA_INTEL_API_KEY environment variable is not set. Configure it to enable this endpoint."
        )
    if x_api_key != _DATA_INTEL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("data-intel")

PORT = int(os.getenv("DATA_INTEL_PORT", "8832"))
MANIFOLD_URL = os.getenv("MANIFOLD_URL", "http://host.docker.internal:8840")
SELF_URL = os.getenv("SELF_URL", f"http://data-intel-api:{PORT}")

app = FastAPI(title="data-intel-api", version="1.0.0")


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------
MANIFEST = {
    "capsule_name": "data-intel",
    "field": "data-intel",
    "version": "1.0.0",
    "base_url": SELF_URL,
    "description": "Tabular data profiling and analytics for CSV, Parquet, Excel, SQLite/DuckDB via DuckDB federation.",
    "accepts": ["csv", "parquet", "xlsx", "xls", "sqlite", "db", "duckdb"],
    "produces": ["application/json"],
    "publishes": ["manny.data.profiled"],
    "subscribes": [],
    "endpoints": {
        "health": "GET /health",
        "manifest": "GET /manifest",
        "run": "POST /run",
        "profile": "POST /profile",
        "query": "POST /query",
        "schema": "GET /schema",
    },
}


# ---------------------------------------------------------------------------
# DuckDB helpers
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Security helpers
# ---------------------------------------------------------------------------

import re

_ALLOWED_EXTENSIONS = {".csv", ".parquet", ".xlsx", ".xls", ".db", ".sqlite", ".duckdb"}
_DANGEROUS_SQL = re.compile(
    r"\b(ATTACH|COPY|CREATE|DROP|INSERT|UPDATE|DELETE|PRAGMA|LOAD|INSTALL|"
    r"IMPORT|EXPORT|EXECUTE|CALL|ALTER|TRUNCATE|VACUUM|CHECKPOINT)\b",
    re.IGNORECASE,
)


def _sanitize_path(path: str) -> str:
    """Resolve path, validate it is a file with an allowed suffix, and escape for SQL."""
    p = Path(path).resolve()
    if not p.exists():
        raise ValueError(f"Path does not exist: {path}")
    if not p.is_file():
        raise ValueError(f"Path is not a file: {path}")
    if p.suffix.lower() not in _ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {p.suffix}")
    # Escape single quotes for safe SQL literal use
    return str(p).replace("'", "''")


def _validate_query_sql(sql: str) -> None:
    """Ensure user-supplied SQL is read-only SELECT."""
    stripped = sql.strip()
    if not stripped.upper().startswith("SELECT"):
        raise ValueError("Only SELECT queries are allowed")
    if _DANGEROUS_SQL.search(stripped):
        raise ValueError("SQL contains forbidden keywords")


def _get_conn() -> duckdb.DuckDBPyConnection:
    return duckdb.connect(":memory:")


def profile_csv(path: str, sample: int = 1000) -> dict[str, Any]:
    safe_path = _sanitize_path(path)
    con = _get_conn()
    rel = con.read_csv(path)
    cols = rel.columns
    dtypes = [str(t) for t in rel.dtypes]
    row_count = con.execute(f"SELECT COUNT(*) FROM read_csv_auto('{safe_path}')").fetchone()[0]
    sample_rows = con.execute(
        f"SELECT * FROM read_csv_auto('{safe_path}') LIMIT {sample}"
    ).fetchdf().to_dict(orient="records")
    return {
        "format": "csv",
        "row_count": row_count,
        "column_count": len(cols),
        "columns": [{"name": c, "dtype": d} for c, d in zip(cols, dtypes)],
        "sample": sample_rows[:10],
    }


def profile_parquet(path: str) -> dict[str, Any]:
    safe_path = _sanitize_path(path)
    con = _get_conn()
    info = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{safe_path}')").fetchdf()
    row_count = con.execute(f"SELECT COUNT(*) FROM read_parquet('{safe_path}')").fetchone()[0]
    return {
        "format": "parquet",
        "row_count": row_count,
        "column_count": len(info),
        "columns": info[["column_name", "column_type"]].rename(
            columns={"column_name": "name", "column_type": "dtype"}
        ).to_dict(orient="records"),
        "sample": con.execute(f"SELECT * FROM read_parquet('{safe_path}') LIMIT 10").fetchdf().to_dict(orient="records"),
    }


def profile_excel(path: str) -> dict[str, Any]:
    safe_path = _sanitize_path(path)
    import pandas as pd
    xf = pd.ExcelFile(safe_path)
    sheets = {}
    for sheet in xf.sheet_names:
        df = pd.read_excel(safe_path, sheet_name=sheet, nrows=5)
        sheets[sheet] = {
            "columns": list(df.columns),
            "sample_rows": df.to_dict(orient="records"),
        }
    return {"format": "excel", "sheets": list(xf.sheet_names), "sheet_details": sheets}


def profile_sqlite(path: str) -> dict[str, Any]:
    safe_path = _sanitize_path(path)
    con = _get_conn()
    try:
        con.execute(f"ATTACH '{safe_path}' AS src (TYPE SQLITE, READ_ONLY)")
    except Exception:
        con.execute(f"ATTACH '{safe_path}' AS src")
    tables = con.execute("SELECT name FROM src.sqlite_master WHERE type='table'").fetchall()
    result: dict[str, Any] = {"format": "sqlite", "tables": []}
    for (tname,) in tables:
        try:
            schema = con.execute(f"DESCRIBE SELECT * FROM src.{tname}").fetchdf()
            count = con.execute(f"SELECT COUNT(*) FROM src.{tname}").fetchone()[0]
            sample = con.execute(f"SELECT * FROM src.{tname} LIMIT 5").fetchdf().to_dict(orient="records")
            result["tables"].append({
                "name": tname,
                "row_count": count,
                "columns": schema[["column_name", "column_type"]].rename(
                    columns={"column_name": "name", "column_type": "dtype"}
                ).to_dict(orient="records"),
                "sample": sample,
            })
        except Exception as e:
            result["tables"].append({"name": tname, "error": str(e)})
    return result


def run_query(sql: str, paths: list[str] | None = None) -> list[dict]:
    _validate_query_sql(sql)
    con = _get_conn()
    if paths:
        for i, p in enumerate(paths):
            safe_path = _sanitize_path(p)
            ext = Path(p).suffix.lower()
            alias = f"src{i}"
            if ext in (".db", ".sqlite"):
                try:
                    con.execute(f"ATTACH '{safe_path}' AS {alias} (TYPE SQLITE, READ_ONLY)")
                except Exception:
                    con.execute(f"ATTACH '{safe_path}' AS {alias}")
            elif ext == ".parquet":
                con.execute(f"CREATE VIEW {alias} AS SELECT * FROM read_parquet('{safe_path}')")
            elif ext == ".csv":
                con.execute(f"CREATE VIEW {alias} AS SELECT * FROM read_csv_auto('{safe_path}')")
    return con.execute(sql).fetchdf().to_dict(orient="records")


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class ProfileRequest(BaseModel):
    path: str
    sample: int = 1000


class QueryRequest(BaseModel):
    sql: str
    paths: list[str] | None = None


class RunRequest(BaseModel):
    kind: str = "profile"
    input: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "capsule": "data-intel", "version": "1.0.0"}


@app.get("/manifest")
async def manifest(_=Depends(_require_api_key)):
    return MANIFEST


@app.post("/profile")
async def profile(req: ProfileRequest, _=Depends(_require_api_key)):
    p = Path(req.path)
    if not p.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {req.path}")
    ext = p.suffix.lower().lstrip(".")
    try:
        if ext == "csv":
            return profile_csv(req.path, req.sample)
        if ext == "parquet":
            return profile_parquet(req.path)
        if ext in ("xlsx", "xls"):
            return profile_excel(req.path)
        if ext in ("db", "sqlite", "duckdb"):
            return profile_sqlite(req.path)
        raise HTTPException(status_code=400, detail=f"Unsupported extension: {ext}")
    except HTTPException:
        raise
    except Exception as e:
        traceback_str = traceback.format_exc()
        # Log full traceback server-side; never leak it to the client
        import logging
        logging.getLogger("data-intel").error("Profile error: %s\n%s", e, traceback_str)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/query")
async def query(req: QueryRequest, _=Depends(_require_api_key)):
    try:
        rows = run_query(req.sql, req.paths)
        return {"row_count": len(rows), "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query error: {e}")


@app.post("/run")
async def run(req: RunRequest, _=Depends(_require_api_key)):
    if req.kind == "profile":
        return await profile(ProfileRequest(**req.input))
    if req.kind == "query":
        return await query(QueryRequest(**req.input))
    raise HTTPException(status_code=400, detail=f"Unknown kind: {req.kind}")


@app.get("/manifest-map")
async def manifest_map(_=Depends(_require_api_key)):
    return {
        "GET /health": "Health check",
        "GET /manifest": "Capsule manifest",
        "POST /profile": "Profile a tabular data file (CSV/Parquet/Excel/SQLite)",
        "POST /query": "Execute DuckDB SQL against one or more files",
        "POST /run": "Generic run wrapper (kind=profile|query)",
    }


# ---------------------------------------------------------------------------
# Startup: register with manifold
# ---------------------------------------------------------------------------

async def register_with_manifold():
    await asyncio.sleep(3)
    for attempt in range(6):
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(f"{MANIFOLD_URL}/include", json=MANIFEST)
                if r.status_code in (200, 201):
                    log.info("Registered with manifold: %s", r.json())
                    return
                log.warning("Manifold include returned %s: %s", r.status_code, r.text)
        except Exception as e:
            log.warning("Manifold register attempt %d failed: %s", attempt + 1, e)
        await asyncio.sleep(10 * (attempt + 1))
    log.warning("Could not register with manifold after 6 attempts — continuing anyway")


@app.on_event("startup")
async def startup():
    asyncio.create_task(register_with_manifold())


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=PORT, log_level="info")
