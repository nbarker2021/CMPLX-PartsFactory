
let screens = [];
const grid = document.getElementById("grid");
const statusEl = document.getElementById("status");
let playing = false; let rafId = null;

async function api(path, method="GET", body=null){
  const opt = {method, headers:{}};
  if(body){ opt.headers["Content-Type"]="application/json"; opt.body = JSON.stringify(body); }
  const r = await fetch(path, opt);
  return await r.json();
}
function makeCanvasCell(label){
  const div = document.createElement("div"); div.className = "screen";
  const canvas = document.createElement("canvas"); canvas.width=320; canvas.height=180;
  const lab = document.createElement("div"); lab.className="label"; lab.textContent=label;
  const badge = document.createElement("div"); badge.className="badge"; badge.textContent="CA";
  div.appendChild(canvas); div.appendChild(lab); div.appendChild(badge);
  return {div, canvas};
}
async function buildGrid(){
  screens = (await api("/api/screens")).screens; grid.innerHTML="";
  for(const sc of screens){ const cell = makeCanvasCell(sc.label); grid.appendChild(cell.div); }
}
async function drawTile(index, canvas, alpha){
  const ctx = canvas.getContext("2d");
  const data = await api(`/api/ca/tile?index=${index}&alpha=${alpha}`);
  const w = data.w, h = data.h; const rgba = new Uint8ClampedArray(data.rgba);
  const img = new ImageData(rgba, w, h);
  const off = new OffscreenCanvas(w, h); const offctx = off.getContext("2d");
  offctx.putImageData(img, 0, 0); ctx.imageSmoothingEnabled = false;
  ctx.drawImage(off, 0, 0, canvas.width, canvas.height);
}
async function tick(){
  if(!playing) return;
  await api(`/api/ca/step?steps=1&kappa=0.08`);
  const alpha = parseInt(document.getElementById("alpha").value||"160");
  const cells = Array.from(document.querySelectorAll(".screen canvas"));
  await Promise.all(cells.map((c, i) => drawTile(i, c, alpha)));
  rafId = requestAnimationFrame(tick);
}
document.getElementById("load").onclick = async () => {
  try{
    const pts = JSON.parse(document.getElementById("points").value || "[]");
    const r = await api("/api/load", "POST", {points: pts, meta:{}});
    statusEl.textContent = `Loaded ${r.count} points.`;
  }catch(e){ alert("Bad JSON"); }
};
document.getElementById("caInit").onclick = async () => { await api(`/api/ca/init?n=64`); statusEl.textContent="CA initialized."; };
document.getElementById("caPlay").onclick = async () => { if(playing) return; playing=true; tick(); };
document.getElementById("caPause").onclick = () => { playing=false; if(rafId) cancelAnimationFrame(rafId); };
(async function init(){ await buildGrid(); await api(`/api/ca/init?n=64`); const cells = Array.from(document.querySelectorAll(".screen canvas")); const alpha = parseInt(document.getElementById("alpha").value||"160"); await Promise.all(cells.map((c, i) => drawTile(i, c, alpha))); })();
