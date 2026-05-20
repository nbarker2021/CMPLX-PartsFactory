"""
Viewer24 slot-09 (2026-05-19T01:17:22Z).
Source: Downloads/Viewer24_Controller_v2_CA_Residue.zip
"""

# Inverse/residue analysis on EM-hex gradient shifts.
# Baseline capture + delta-hex histograms + residue vs wrap heuristic.
import math
from typing import Dict, List, Tuple
from .dihedral_ca import DihedralCA, wavelength_to_rgb, rgb_to_hex

class ResidueAnalyzer:
    def __init__(self, ca: DihedralCA):
        self.ca = ca
        self.baseline_hex = None  # list of hex strings (per pixel of global grid)

    def capture_baseline(self):
        # render entire global grid as hex map
        W,H = self.ca.W, self.ca.H
        out = ["#000000"]*(W*H)
        for y in range(H):
            for x in range(W):
                k = self.ca.idx(x,y)
                wl = self.ca.wavelength(k)
                R,G,B = wavelength_to_rgb(wl)
                out[k] = rgb_to_hex(R,G,B)
        self.baseline_hex = out

    def _hex_to_rgb(self, h: str) -> Tuple[int,int,int]:
        return int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)

    def _nibble_hist(self, hexes: List[str]) -> Dict[str, List[int]]:
        # 16-bin hist for each channel nibble high (R_hi,G_hi,B_hi)
        R=[0]*16; G=[0]*16; B=[0]*16
        for h in hexes:
            r,g,b = self._hex_to_rgb(h)
            R[r>>4]+=1; G[g>>4]+=1; B[b>>4]+=1
        return {"R":R,"G":G,"B":B}

    def residue_tile(self, tile_index: int, thresh_wrap=12) -> Dict:
        # Return per-pixel residue likelihood based on hex delta from baseline and seam-consistency test.
        if self.baseline_hex is None:
            self.capture_baseline()
        tx=tile_index%self.ca.tiles_x; ty=tile_index//self.ca.tiles_x
        w=self.ca.n; h=self.ca.n
        res_data=[]; wrap_data=[]
        # compute current hex map for tile
        curr_hex = []
        for j in range(h):
            for i in range(w):
                x=tx*w+i; y=ty*h+j; k=self.ca.idx(x,y)
                wl=self.ca.wavelength(k); R,G,B = wavelength_to_rgb(wl)
                curr_hex.append(rgb_to_hex(R,G,B))
        # residue vs wrap: measure delta from baseline and compare to neighbor across the nearest seam
        # simple heuristic: if delta to baseline is big but local difference across seam is small => wrap (continuing wave)
        # else large delta with local stationary gradient => residue.
        def l1_rgb(a,b):
            ra,ga,ba = self._hex_to_rgb(a); rb,gb,bb = self._hex_to_rgb(b)
            return abs(ra-rb)+abs(ga-gb)+abs(ba-bb)
        for j in range(h):
            for i in range(w):
                x=tx*w+i; y=ty*h+j; k=self.ca.idx(x,y)
                base = self.baseline_hex[k]; cur = curr_hex[j*w+i]
                d_hex = l1_rgb(base, cur)
                # neighbor across right seam (wrapping)
                k_right = self.ca.idx(x+1,y); base_r = self.baseline_hex[k_right]
                d_seam = l1_rgb(base_r, rgb_to_hex(*wavelength_to_rgb(self.ca.wavelength(k_right))))
                wrap_like = 1 if d_seam < thresh_wrap else 0
                # residue score: high when big change not explained by seam continuation
                score = max(0, d_hex - d_seam)
                score = 255 if score>255 else score
                res_data.extend([score,score,score,160])  # grayscale alpha
                wrap_data.extend([wrap_like*255,0,0,120]) # red marks likely wrap awaiting closure
        # nibble hist "fingerprint"
        hist = self._nibble_hist(curr_hex)
        return {"w":w,"h":h,"residue_rgba":res_data,"wrap_rgba":wrap_data,"hist":hist}
