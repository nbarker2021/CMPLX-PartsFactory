"""
Automation hub — primary workforce UI + MCP SSE → OpenCode workforce HTTP API.

Env: see README in parent `automation-hubs/`. Hub identity for multi-hub ops:
  AUTOMATION_HUB_ID           default cmplx-workforce
  AUTOMATION_HUB_PUBLIC_TITLE default CMPLX Workforce Hub
  FASTMCP_INSTANCE            default cmplx-workforce-primary (MCP server name)
"""
from __future__ import annotations

import base64
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from mcp.server.fastmcp import FastMCP

HUB_ID = os.environ.get("AUTOMATION_HUB_ID", "cmplx-workforce")
HUB_TITLE = os.environ.get("AUTOMATION_HUB_PUBLIC_TITLE", "CMPLX Workforce Hub")
MCP_NAME = os.environ.get("FASTMCP_INSTANCE", "cmplx-workforce-primary")
DEFAULT_PROVIDER_ID = os.environ.get("WORKFORCE_DEFAULT_PROVIDER_ID", "opencode")
DEFAULT_MODEL_ID = os.environ.get("WORKFORCE_DEFAULT_MODEL_ID", "deepseek-v4-flash-free")

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"

OPENCODE_BASE = os.environ.get("OPENCODE_WORKFORCE_URL", "http://opencode-session:4096").rstrip("/")
OC_USER = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")

# Lazy password lookup to avoid KeyError at import time
def _oc_pass() -> str:
    password = os.environ.get("OPENCODE_SERVER_PASSWORD")
    if not password:
        raise RuntimeError("OPENCODE_SERVER_PASSWORD environment variable is not set")
    return password

_client: httpx.AsyncClient | None = None


def _auth_header() -> str:
    raw = f"{OC_USER}:{_oc_pass()}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=OPENCODE_BASE,
            headers={"Authorization": _auth_header()},
            timeout=httpx.Timeout(120.0, connect=10.0),
        )
    return _client


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_client()
    yield
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


app = FastAPI(
    title=HUB_TITLE,
    description=f"Automation hub `{HUB_ID}` — web + REST + MCP SSE → OpenCode.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("WORKFORCE_HUB_CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp = FastMCP(
    MCP_NAME,
    instructions=(
        f"Hub `{HUB_ID}`: tools call OpenCode workforce HTTP API. "
        "Project instructions live under OpenCode /workspace and /suite mounts."
    ),
)


@mcp.tool()
async def opencode_health() -> str:
    """GET /global/health on OpenCode workforce (JSON text)."""
    r = await get_client().get("/global/health")
    r.raise_for_status()
    return r.text


@mcp.tool()
async def opencode_list_sessions() -> str:
    """GET /session (JSON text)."""
    r = await get_client().get("/session")
    r.raise_for_status()
    return r.text


@mcp.tool()
async def opencode_create_session(title: str | None = None) -> str:
    """POST /session — optional title."""
    body: dict[str, Any] = {}
    if title:
        body["title"] = title
    r = await get_client().post("/session", json=body or {})
    r.raise_for_status()
    return r.text


@mcp.tool()
async def opencode_send_message(
    session_id: str,
    message: str,
    model: str | None = None,
) -> str:
    """POST /session/:id/message."""
    payload: dict[str, Any] = {"parts": [{"type": "text", "text": message}]}
    if model:
        if "/" in model:
            provider_id, model_id = model.split("/", 1)
        else:
            provider_id, model_id = DEFAULT_PROVIDER_ID, model
        payload["model"] = {"providerID": provider_id, "modelID": model_id}
    else:
        payload["model"] = {"providerID": DEFAULT_PROVIDER_ID, "modelID": DEFAULT_MODEL_ID}
    r = await get_client().post(f"/session/{session_id}/message", json=payload)
    r.raise_for_status()
    return r.text


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = STATIC / "index.html"
    if not index_path.is_file():
        return HTMLResponse(f"<h1>{HUB_TITLE}</h1><p>Missing static/index.html</p>", status_code=500)
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/api/health")
async def api_health():
    hub = {"hub_id": HUB_ID, "title": HUB_TITLE, "ok": True}
    oc: dict[str, Any] = {"reachable": False}
    try:
        r = await get_client().get("/global/health")
        oc["reachable"] = r.status_code == 200
        oc["status_code"] = r.status_code
        try:
            oc["body"] = r.json()
        except Exception:
            oc["body"] = r.text
    except Exception as e:
        oc["error"] = str(e)
    return {"hub": hub, "opencode": oc, "opencode_base": OPENCODE_BASE}


@app.get("/api/sessions")
async def api_list_sessions():
    try:
        r = await get_client().get("/session")
        r.raise_for_status()
        return JSONResponse(content=r.json())
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, detail=e.response.text) from e


@app.post("/api/sessions")
async def api_create_session(payload: dict[str, Any] | None = None):
    try:
        r = await get_client().post("/session", json=payload or {})
        r.raise_for_status()
        return JSONResponse(content=r.json())
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, detail=e.response.text) from e


@app.post("/api/sessions/{session_id}/message")
async def api_send_message(session_id: str, request: Request):
    body = await request.json()
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="request body must be a JSON object")

    if "parts" not in body and "message" in body:
        message = body.pop("message")
        if not isinstance(message, str):
            raise HTTPException(status_code=400, detail="message must be a string")
        body["parts"] = [{"type": "text", "text": message}]

    if "parts" not in body:
        raise HTTPException(
            status_code=400,
            detail="request body must include `parts` or shorthand `message`",
        )

    model = body.get("model")
    if model is None:
        body["model"] = {"providerID": DEFAULT_PROVIDER_ID, "modelID": DEFAULT_MODEL_ID}
    elif isinstance(model, str):
        if "/" in model:
            provider_id, model_id = model.split("/", 1)
        else:
            provider_id, model_id = DEFAULT_PROVIDER_ID, model
        body["model"] = {"providerID": provider_id, "modelID": model_id}
    elif not isinstance(model, dict):
        raise HTTPException(status_code=400, detail="model must be an object or string")

    try:
        r = await get_client().post(f"/session/{session_id}/message", json=body)
        r.raise_for_status()
        if r.content:
            try:
                return JSONResponse(content=r.json())
            except ValueError:
                return JSONResponse(
                    content={
                        "ok": True,
                        "session_id": session_id,
                        "status_code": r.status_code,
                        "raw": r.text,
                    },
                    status_code=r.status_code,
                )
        return JSONResponse(
            content={
                "ok": True,
                "session_id": session_id,
                "status_code": r.status_code,
                "note": "No response body returned by opencode.",
            },
            status_code=r.status_code,
        )
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, detail=e.response.text) from e


@app.get("/api/opencode/doc")
async def proxy_openapi():
    try:
        r = await get_client().get("/doc")
        r.raise_for_status()
        return HTMLResponse(content=r.text)
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, detail=e.response.text) from e


app.mount("/mcp", mcp.sse_app())

if STATIC.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")


def main():
    import uvicorn

    port = int(os.environ.get("WORKFORCE_HUB_PORT", "8775"))
    uvicorn.run("server:app", host="0.0.0.0", port=port, factory=False)


if __name__ == "__main__":
    main()
