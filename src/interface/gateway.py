"""
Unified HTTP API Gateway for CMPLX-PartsFactory.
Single entrypoint for ALL external access.
Routes: opencode agent API, service mesh, Docker services, MCP SSE.
"""

from __future__ import annotations

import json
import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Optional

import httpx
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from mcp.server.fastmcp import FastMCP

from .auth import verify_auth
from .config import settings

logger = logging.getLogger("cmplx.gateway")

_start_time = time.time()
_client: Optional[httpx.AsyncClient] = None
_mesh_health: dict[str, Any] = {}

SERVICES_HEALTH_ENDPOINTS = {
    name: f"{url.rstrip('/')}/health"
    for name, url in settings.known_services.items()
}


def _auth_header() -> str:
    import base64
    raw = f"{settings.opencode_username}:{settings.opencode_password}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            base_url=settings.opencode_api_url,
            headers={"Authorization": _auth_header()},
            timeout=httpx.Timeout(120.0, connect=10.0),
        )
    return _client


async def check_services_health() -> dict[str, Any]:
    results: dict[str, Any] = {}
    async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=3.0)) as c:
        for name, url in SERVICES_HEALTH_ENDPOINTS.items():
            try:
                r = await c.get(url)
                results[name] = {
                    "healthy": r.status_code == 200,
                    "status_code": r.status_code,
                }
                if r.status_code == 200:
                    try:
                        results[name]["body"] = r.json()
                    except Exception:
                        results[name]["body"] = r.text[:200]
            except Exception as e:
                results[name] = {"healthy": False, "error": str(e)[:100]}
    return results


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _mesh_health
    get_client()
    try:
        from mesh.health_monitor import HealthMonitor
        hm = HealthMonitor(check_interval=30.0)
        for name in settings.known_services:
            url = settings.known_services[name]
            hm.register(name, lambda u=url: _check_url(u))
        hm.start()
        app.state.health_monitor = hm
        logger.info("Mesh health monitor registered")
    except ImportError:
        logger.info("Mesh module not available — running standalone")
        app.state.health_monitor = None
    _mesh_health = await check_services_health()
    yield
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
    if hasattr(app.state, "health_monitor") and app.state.health_monitor:
        app.state.health_monitor.stop()


def _check_url(url: str) -> bool:
    try:
        import requests
        r = requests.get(f"{url.rstrip('/')}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


app = FastAPI(
    title="CMPLX Unified Interface Gateway",
    description="Single entrypoint for ALL external access to CMPLX-PartsFactory",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

mcp = FastMCP(
    "cmplx-gateway",
    instructions=(
        "CMPLX Unified Interface Gateway: tools call the opencode agent API. "
        "Use opencode_health() to check agent status, opencode_send_message() to interact."
    ),
)


async def _oc_request(method: str, path: str, body: Any = None) -> httpx.Response:
    c = get_client()
    if method == "GET":
        return await c.get(path)
    return await c.post(path, json=body or {})


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "CMPLX Unified Interface Gateway", "version": "1.0.0", "dashboard": "/dashboard"}


@app.get("/api/health")
async def api_health(user: str = Depends(verify_auth)):
    uptime = time.time() - _start_time
    oc_ok = False
    oc_latency = None
    try:
        t0 = time.time()
        r = await get_client().get("/global/health")
        oc_latency = round((time.time() - t0) * 1000, 1)
        oc_ok = r.status_code == 200
    except Exception:
        pass
    return {
        "ok": True,
        "uptime_seconds": round(uptime, 1),
        "opencode_reachable": oc_ok,
        "opencode_latency_ms": oc_latency,
        "services_count": len(settings.known_services),
        "authenticated": user,
    }


@app.get("/api/services")
async def list_services(user: str = Depends(verify_auth)):
    global _mesh_health
    _mesh_health = await check_services_health()
    healthy_count = sum(1 for v in _mesh_health.values() if v.get("healthy"))
    return {
        "services": _mesh_health,
        "healthy": healthy_count,
        "total": len(_mesh_health),
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/api/services/{name}")
async def service_detail(name: str, user: str = Depends(verify_auth)):
    global _mesh_health
    if name not in settings.known_services:
        raise HTTPException(404, f"Unknown service '{name}'. Known: {', '.join(sorted(settings.known_services))}")
    _mesh_health = await check_services_health()
    return {
        "name": name,
        "url": settings.known_services[name],
        "health": _mesh_health.get(name, {"healthy": False, "error": "not checked"}),
    }


@app.api_route("/api/opencode/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_opencode(path: str, request: Request, user: str = Depends(verify_auth)):
    c = get_client()
    body = None
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.json()
        except Exception:
            body = None
    try:
        r = await c.request(request.method, f"/{path}", json=body)
        content_type = r.headers.get("content-type", "")
        if "application/json" in content_type:
            return JSONResponse(content=r.json(), status_code=r.status_code)
        return JSONResponse(content={"ok": r.status_code < 400, "status_code": r.status_code, "body": r.text[:10000]})
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, detail=e.response.text[:1000])
    except httpx.RequestError as e:
        raise HTTPException(502, detail=f"opencode agent unreachable: {e}")


@app.get("/api/sessions")
async def list_sessions(user: str = Depends(verify_auth)):
    try:
        r = await get_client().get("/session")
        r.raise_for_status()
        return JSONResponse(content=r.json())
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, detail=e.response.text[:1000])
    except httpx.RequestError as e:
        raise HTTPException(502, detail=f"opencode agent unreachable: {e}")


@app.post("/api/sessions")
async def create_session(payload: dict[str, Any] | None = None, user: str = Depends(verify_auth)):
    try:
        r = await get_client().post("/session", json=payload or {})
        r.raise_for_status()
        return JSONResponse(content=r.json())
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, detail=e.response.text[:1000])
    except httpx.RequestError as e:
        raise HTTPException(502, detail=f"opencode agent unreachable: {e}")


@app.post("/api/sessions/{session_id}/message")
async def send_message(session_id: str, request: Request, user: str = Depends(verify_auth)):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Request body must be valid JSON")
    if "parts" not in body and "message" in body:
        msg = body.pop("message")
        body["parts"] = [{"type": "text", "text": msg}]
    try:
        r = await get_client().post(f"/session/{session_id}/message", json=body)
        r.raise_for_status()
        if r.content:
            try:
                return JSONResponse(content=r.json())
            except ValueError:
                return JSONResponse(content={"ok": True, "session_id": session_id, "raw": r.text[:5000]})
        return JSONResponse(content={"ok": True, "session_id": session_id})
    except httpx.HTTPStatusError as e:
        raise HTTPException(e.response.status_code, detail=e.response.text[:1000])
    except httpx.RequestError as e:
        raise HTTPException(502, detail=f"opencode agent unreachable: {e}")


@app.get("/api/gateway/stats")
async def gateway_stats(user: str = Depends(verify_auth)):
    uptime = time.time() - _start_time
    return {
        "uptime_seconds": round(uptime, 1),
        "services_known": len(settings.known_services),
        "auth_disabled": settings.auth_disabled,
        "opencode_url": settings.opencode_api_url,
    }


@mcp.tool()
async def opencode_health() -> str:
    """GET /global/health on the opencode agent (JSON text)."""
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
async def opencode_send_message(session_id: str, message: str) -> str:
    """POST /session/:id/message with a text message."""
    payload = {"parts": [{"type": "text", "text": message}]}
    r = await get_client().post(f"/session/{session_id}/message", json=payload)
    r.raise_for_status()
    return r.text


@mcp.tool()
async def gateway_list_services() -> str:
    """List all known services and their health status."""
    health = await check_services_health()
    return json.dumps(health, indent=2)


DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CMPLX Unified Interface Gateway</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0d1117; color: #c9d1d9; min-height: 100vh; }
  .container { max-width: 1200px; margin: 0 auto; padding: 2rem; }
  header { margin-bottom: 2rem; }
  h1 { font-size: 1.8rem; color: #58a6ff; font-weight: 600; }
  .subtitle { color: #8b949e; margin-top: 0.25rem; font-size: 0.9rem; }
  .stats { display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap; }
  .stat-card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 1rem 1.5rem; flex: 1; min-width: 140px; }
  .stat-card .value { font-size: 1.5rem; font-weight: 600; color: #f0f6fc; }
  .stat-card .label { font-size: 0.8rem; color: #8b949e; margin-top: 0.25rem; text-transform: uppercase; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 0.75rem; margin-top: 1rem; }
  .service-card { background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 1rem; }
  .service-card .name { font-weight: 600; font-size: 0.95rem; }
  .service-card .url { color: #8b949e; font-size: 0.75rem; margin-top: 0.25rem; word-break: break-all; }
  .service-card .status { margin-top: 0.5rem; font-size: 0.85rem; }
  .healthy { color: #3fb950; }
  .unhealthy { color: #f85149; }
  .unknown { color: #8b949e; }
  .badge { display: inline-block; padding: 0.15rem 0.5rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; text-transform: uppercase; }
  .badge-ok { background: #1b3626; color: #3fb950; border: 1px solid #3fb95040; }
  .badge-fail { background: #36212b; color: #f85149; border: 1px solid #f8514940; }
  .api-links { margin-top: 2rem; }
  .api-links h2 { font-size: 1.2rem; color: #58a6ff; margin-bottom: 0.75rem; }
  .api-links a { color: #58a6ff; text-decoration: none; display: block; padding: 0.3rem 0; font-size: 0.85rem; font-family: monospace; }
  .api-links a:hover { text-decoration: underline; }
  footer { margin-top: 3rem; padding-top: 1rem; border-top: 1px solid #30363d; color: #8b949e; font-size: 0.8rem; }
</style>
</head>
<body>
<div class="container">
<header>
  <h1>CMPLX Unified Interface Gateway</h1>
  <div class="subtitle">Single entrypoint for all external access to CMPLX-PartsFactory</div>
</header>
<div class="stats">
  <div class="stat-card"><div class="value" id="uptime">--</div><div class="label">Uptime</div></div>
  <div class="stat-card"><div class="value" id="services-total">0</div><div class="label">Services</div></div>
  <div class="stat-card"><div class="value" id="services-healthy">0</div><div class="label">Healthy</div></div>
  <div class="stat-card"><div class="value" id="oc-status">--</div><div class="label">Agent</div></div>
</div>
<h2 style="font-size:1.1rem;color:#f0f6fc;">Service Mesh</h2>
<div class="grid" id="service-grid"></div>
<div class="api-links">
  <h2>Endpoints</h2>
  <a href="/api/health">/api/health — Gateway health</a>
  <a href="/api/services">/api/services — All services health</a>
  <a href="/api/sessions">/api/sessions — Active sessions</a>
  <a href="/api/gateway/stats">/api/gateway/stats — Gateway statistics</a>
  <a href="/mcp">/mcp — MCP SSE endpoint</a>
</div>
<footer>CMPLX-PartsFactory &middot; Unified Interface Layer</footer>
</div>
<script>
async function load() { try {
  const h = await fetch('/api/health'); const hd = await h.json();
  document.getElementById('uptime').textContent = Math.floor(hd.uptime_seconds/3600)+'h'+Math.floor((hd.uptime_seconds%3600)/60)+'m';
  document.getElementById('oc-status').textContent = hd.opencode_reachable ? 'Online' : 'Offline';
  document.getElementById('oc-status').className = hd.opencode_reachable ? 'healthy' : 'unhealthy';
  const s = await fetch('/api/services'); const sd = await s.json();
  document.getElementById('services-total').textContent = sd.total;
  document.getElementById('services-healthy').textContent = sd.healthy;
  const grid = document.getElementById('service-grid');
  for (const [name, info] of Object.entries(sd.services)) {
    const card = document.createElement('div'); card.className = 'service-card';
    const ok = info.healthy;
    card.innerHTML = '<div class="name">'+name+' <span class="badge '+(ok?'badge-ok':'badge-fail')+'">'+(ok?'OK':'DOWN')+'</span></div>' +
      '<div class="url">'+info.status_code+'</div>' +
      '<div class="status '+(ok?'healthy':'unhealthy')+'">'+(ok?'Online':'Unreachable')+'</div>';
    grid.appendChild(card);
  }
} catch(e) { console.error(e); } }
load();
setInterval(load, 15000);
</script>
</body>
</html>"""


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return HTMLResponse(content=DASHBOARD_HTML)


app.mount("/mcp", mcp.sse_app())


def main():
    import uvicorn
    uvicorn.run(
        "interface.gateway:app",
        host=settings.host,
        port=settings.gateway_port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
