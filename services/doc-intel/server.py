"""
doc-intel-api — document intelligence capsule for the Manny manifold.
Handles text extraction from DOCX, PDF, MD, TXT and schema/template files.
Registers with manny-manifold on startup.
"""
import asyncio
import io
import json
import logging
import os
import re
import traceback
from pathlib import Path
from typing import Any

import chardet
import httpx
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Security: API-key auth for all endpoints
_DOC_INTEL_API_KEY = os.environ.get("DOC_INTEL_API_KEY", "")

def _require_api_key(x_api_key: str = Header(default="")):
    if not _DOC_INTEL_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="DOC_INTEL_API_KEY environment variable is not set. Configure it to enable this endpoint."
        )
    if x_api_key != _DOC_INTEL_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("doc-intel")

PORT = int(os.getenv("DOC_INTEL_PORT", "8830"))
MANIFOLD_URL = os.getenv("MANIFOLD_URL", "http://host.docker.internal:8840")
SELF_URL = os.getenv("SELF_URL", f"http://doc-intel-api:{PORT}")

app = FastAPI(title="doc-intel-api", version="1.0.0")


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------
MANIFEST = {
    "capsule_name": "doc-intel",
    "field": "doc-intel",
    "version": "1.0.0",
    "base_url": SELF_URL,
    "description": "Text extraction and structure analysis for DOCX, PDF, MD, TXT, schema and template files.",
    "accepts": ["docx", "pdf", "md", "txt", "rst", "yaml", "json", "sql", "xml", "html"],
    "produces": ["text/plain", "application/json"],
    "publishes": ["manny.doc.extracted"],
    "subscribes": [],
    "endpoints": {
        "health": "GET /health",
        "manifest": "GET /manifest",
        "run": "POST /run",
        "extract": "POST /extract",
    },
}


# ---------------------------------------------------------------------------
# Extraction helpers
# ---------------------------------------------------------------------------

def _detect_encoding(raw: bytes) -> str:
    result = chardet.detect(raw[:8192])
    return result.get("encoding") or "utf-8"


def extract_docx(raw: bytes) -> str:
    try:
        import mammoth
        result = mammoth.extract_raw_text(io.BytesIO(raw))
        return result.value
    except Exception:
        try:
            import docx
            doc = docx.Document(io.BytesIO(raw))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception as e:
            return f"[docx extraction failed: {e}]"


def extract_pdf(raw: bytes) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(raw))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except Exception as e:
        return f"[pdf extraction failed: {e}]"


def extract_text(raw: bytes, ext: str) -> str:
    enc = _detect_encoding(raw)
    try:
        return raw.decode(enc, errors="replace")
    except Exception:
        return raw.decode("utf-8", errors="replace")


def extract_content(raw: bytes, ext: str) -> str:
    ext = ext.lower().lstrip(".")
    if ext in ("docx",):
        return extract_docx(raw)
    if ext == "pdf":
        return extract_pdf(raw)
    return extract_text(raw, ext)


def analyze_structure(text: str, ext: str) -> dict[str, Any]:
    lines = text.splitlines()
    word_count = len(text.split())
    headings = [l.lstrip("#").strip() for l in lines if re.match(r"^#{1,6}\s", l)]
    sql_tables = re.findall(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?([\w.]+)", text, re.IGNORECASE)
    top_keys: list[str] = []
    if ext in ("json",):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                top_keys = list(parsed.keys())[:20]
        except Exception:
            pass

    return {
        "line_count": len(lines),
        "word_count": word_count,
        "char_count": len(text),
        "headings": headings[:30],
        "sql_tables_detected": sql_tables[:30],
        "top_json_keys": top_keys,
        "has_code_blocks": "```" in text or "~~~" in text,
    }


def sanitize(text: str) -> str:
    return text.replace("\x00", "")


# ---------------------------------------------------------------------------
# Request/Response models
# ---------------------------------------------------------------------------

class ExtractRequest(BaseModel):
    path: str | None = None
    content_b64: str | None = None
    ext: str = "txt"
    max_chars: int = 200_000


class RunRequest(BaseModel):
    kind: str = "extract"
    input: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "capsule": "doc-intel", "version": "1.0.0"}


@app.get("/manifest")
async def manifest(_=Depends(_require_api_key)):
    return MANIFEST


# Base directory for path-based extraction (configurable via env)
_DOC_INTEL_BASE_DIR = Path(os.environ.get("DOC_INTEL_BASE_DIR", "/tmp/doc-intel-safe")).resolve()
_DOC_INTEL_BASE_DIR.mkdir(parents=True, exist_ok=True)


def _safe_doc_path(req_path: str) -> Path:
    """Prevent path traversal: reject absolute paths and paths escaping base dir."""
    p = Path(req_path)
    if p.is_absolute():
        raise HTTPException(status_code=400, detail="Absolute paths not allowed")
    target = (_DOC_INTEL_BASE_DIR / p).resolve()
    if not str(target).startswith(str(_DOC_INTEL_BASE_DIR)):
        raise HTTPException(status_code=400, detail="Path escapes allowed directory")
    return target


@app.post("/extract")
async def extract(req: ExtractRequest, _=Depends(_require_api_key)):
    raw: bytes
    if req.path:
        p = _safe_doc_path(req.path)
        if not p.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {req.path}")
        raw = p.read_bytes()
        ext = req.ext or p.suffix.lstrip(".")
    elif req.content_b64:
        import base64
        raw = base64.b64decode(req.content_b64)
        ext = req.ext
    else:
        raise HTTPException(status_code=400, detail="Provide 'path' or 'content_b64'")

    text = sanitize(extract_content(raw, ext))
    if req.max_chars and len(text) > req.max_chars:
        text = text[: req.max_chars]

    structure = analyze_structure(text, ext)
    return {
        "ext": ext,
        "text": text,
        "structure": structure,
        "truncated": len(text) >= req.max_chars,
    }


@app.post("/run")
async def run(req: RunRequest, _=Depends(_require_api_key)):
    if req.kind == "extract":
        extract_req = ExtractRequest(**req.input)
        return await extract(extract_req)
    raise HTTPException(status_code=400, detail=f"Unknown kind: {req.kind}")


@app.get("/manifest-map")
async def manifest_map(_=Depends(_require_api_key)):
    return {
        "GET /health": "Health check",
        "GET /manifest": "Capsule manifest",
        "POST /extract": "Extract text + structure from a document file",
        "POST /run": "Generic run wrapper (kind=extract)",
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
