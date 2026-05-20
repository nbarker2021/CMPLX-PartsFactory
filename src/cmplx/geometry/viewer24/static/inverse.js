
let screens = [];
const grid = document.getElementById("grid");
const statusEl = document.getElementById("status");

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
  const badge = document.createElement("div"); badge.className="badge"; badge.textContent="Residue";
  div.appendChild(canvas); div.appendChild(lab); div.appendChild(badge);
  return {div, canvas};
}
async function buildGrid(){
  screens = (await api("/api/screens")).screens; grid.innerHTML="";
  for(const sc of screens){ const cell = makeCanvasCell(sc.label); grid.appendChild(cell.div); }
}
async function drawResidue(index, canvas){
  const ctx = canvas.getContext("2d");
  const data = await api(`/api/inverse/tile?index=${index}`);
  const w = data.w, h = data.h;
  // Draw residue (grayscale)
  let rgba = new Uint8ClampedArray(data.residue_rgba);
  let img = new ImageData(rgba, w, h);
  const off = new OffscreenCanvas(w, h); const offctx = off.getContext("2d");
  offctx.putImageData(img, 0, 0);
  ctx.imageSmoothingEnabled = false; ctx.drawImage(off, 0, 0, canvas.width, canvas.height);
  // Overlay wrap mask (red)
  rgba = new Uint8ClampedArray(data.wrap_rgba);
  img = new ImageData(rgba, w, h);
  const off2 = new OffscreenCanvas(w, h); const offctx2 = off2.getContext("2d");
  offctx2.putImageData(img, 0, 0);
  ctx.globalCompositeOperation = "lighter";
  ctx.drawImage(off2, 0, 0, canvas.width, canvas.height);
  ctx.globalCompositeOperation = "source-over";
}
document.getElementById("baseline").onclick = async () => {
  await api("/api/inverse/baseline");
  statusEl.textContent = "Baseline captured.";
};
document.getElementById("step").onclick = async () => {
  await api(`/api/ca/step?steps=1&kappa=0.08`);
  const cells = Array.from(document.querySelectorAll(".screen canvas"));
  await Promise.all(cells.map((c, i) => drawResidue(i, c)));
};
(async function init(){
  await buildGrid();
  await api("/api/inverse/baseline");
  const cells = Array.from(document.querySelectorAll(".screen canvas"));
  await Promise.all(cells.map((c, i) => drawResidue(i, c)));
})();
