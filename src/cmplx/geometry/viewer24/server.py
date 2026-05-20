"""
Viewer24 slot-09 (2026-05-19T01:17:22Z).
Source: Downloads/Viewer24_Controller_v2_CA_Residue.zip
"""

import json, os
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server
from .niemeier_specs import NIEMEIER_SPECS
from .transforms import world_to_screen
from .dihedral_ca import DihedralCA
from .inverse_residue import ResidueAnalyzer

SESSION = {"points": [], "meta": {}}
TILES_X, TILES_Y = 6, 4
N = 64
CA = DihedralCA(tiles_x=TILES_X, tiles_y=TILES_Y, n=N, seed=1337)
CA.seed_from_specs(NIEMEIER_SPECS + ["LEECH"])
INV = ResidueAnalyzer(CA)

def read_json(environ):
    try: length = int(environ.get('CONTENT_LENGTH','0'))
    except (ValueError): length = 0
    body = environ['wsgi.input'].read(length) if length>0 else b'{}'
    return json.loads(body.decode('utf-8') or "{}")

def respond(start_response, status, obj, ctype="application/json"):
    data = json.dumps(obj).encode("utf-8")
    start_response(status, [('Content-Type', ctype), ('Content-Length', str(len(data)))])
    return [data]

def app(environ, start_response):
    path = environ.get('PATH_INFO','/'); method = environ.get('REQUEST_METHOD','GET')

    if path == "/api/load" and method == "POST":
        payload = read_json(environ); SESSION["points"]=payload.get("points") or []; SESSION["meta"]=payload.get("meta") or {}
        return respond(start_response,'200 OK',{"ok":True,"count":len(SESSION["points"])})
    if path == "/api/screens":
        labs = NIEMEIER_SPECS + ["LEECH"]
        return respond(start_response,'200 OK',{"screens":[{"index":i,"label":lab} for i,lab in enumerate(labs)]})
    if path == "/api/frame":
        q = parse_qs(environ.get('QUERY_STRING','')); w=int(q.get('w',['320'])[0]); h=int(q.get('h',['180'])[0])
        s,tx,ty = world_to_screen(SESSION.get("points") or [], w, h, padding=0.08)
        return respond(start_response,'200 OK',{"s":s,"tx":tx,"ty":ty})
    # CA controls
    if path == "/api/ca/init":
        q = parse_qs(environ.get('QUERY_STRING','')); n=int(q.get('n',['64'])[0])
        global CA,N,INV; N=n; CA=DihedralCA(tiles_x=TILES_X, tiles_y=TILES_Y, n=N, seed=1337); CA.seed_from_specs(NIEMEIER_SPECS+["LEECH"]); INV = ResidueAnalyzer(CA)
        return respond(start_response,'200 OK',{"ok":True,"n":N})
    if path == "/api/ca/step":
        q = parse_qs(environ.get('QUERY_STRING','')); steps=int(q.get('steps',['1'])[0]); kappa=float(q.get('kappa',['0.08'])[0])
        for _ in range(steps): CA.step(kappa=kappa, dual=True)
        return respond(start_response,'200 OK',{"ok":True,"step":CA.step_id})
    if path == "/api/ca/tile":
        q = parse_qs(environ.get('QUERY_STRING','')); idx=int(q.get('index',['0'])[0]); alpha=int(q.get('alpha',['160'])[0])
        tile = CA.tile_pixels_em(idx, alpha=alpha); return respond(start_response,'200 OK',tile)
    # Inverse/residue endpoints
    if path == "/api/inverse/baseline":
        INV.capture_baseline(); return respond(start_response,'200 OK',{"ok":True})
    if path == "/api/inverse/tile":
        q = parse_qs(environ.get('QUERY_STRING','')); idx=int(q.get('index',['0'])[0])
        tile = INV.residue_tile(idx)
        return respond(start_response,'200 OK',tile)
    # Static
    if path == "/":
        with open("./static/index.html","rb") as f: data=f.read()
        start_response('200 OK',[('Content-Type','text/html')]); return [data]
    if path == "/inverse":
        with open("./static/inverse.html","rb") as f: data=f.read()
        start_response('200 OK',[('Content-Type','text/html')]); return [data]
    if path.startswith("/static/"):
        p = "."+path
        if not os.path.exists(p): start_response('404 NOT FOUND',[('Content-Type','text/plain')]); return [b'not found']
        ctype="text/plain"
        if p.endswith(".html"): ctype="text/html"
        if p.endswith(".js"): ctype="text/javascript"
        if p.endswith(".css"): ctype="text/css"
        with open(p,"rb") as f: data=f.read()
        start_response('200 OK',[('Content-Type',ctype)]); return [data]
    start_response('404 NOT FOUND',[('Content-Type','application/json')]); return [b'{}']

def serve(host="127.0.0.1", port=9091):
    httpd = make_server(host, port, app)
    print(f"Viewer24 v2 + CA + Inverse on http://{host}:{port}")
    httpd.serve_forever()

if __name__ == "__main__":
    serve()
