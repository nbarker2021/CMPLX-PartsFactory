"""
Escrow merge (2026-05-19T00:00:31Z).
Source: ``CMPLX-history/staging/by-family/unclassified/partsfactory/atlas_o8.py``
Slot: ``slot-04-speedlight-worldline``
"""
import math
from typing import Dict, List

def extract_O8(block_meta: Dict) -> List[float]:
    version = float(block_meta.get("version", 0))
    chain_tight = float(block_meta.get("height", 0) % 2016)
    merkle_entropy = float(block_meta.get("txcount", 1))**0.5
    diff_ratio = 1.0
    weight = float(block_meta.get("weight", 1000000)) / 4_000_000.0
    script_mix = float(block_meta.get("sigops", 0)) / 20000.0
    coinbase_flags = float(len(block_meta.get("coinbaseaux",{}).get("flags","")) % 64) / 64.0
    prop_cadence = float(block_meta.get("template_age", 1.0))
    return [version, chain_tight, merkle_entropy, diff_ratio, weight, script_mix, coinbase_flags, prop_cadence]

def embed_E8(vec8: List[float]) -> List[float]:
    return [float(x) for x in vec8]

def curvature(points: List[List[float]]) -> float:
    if len(points) < 3: return 0.0
    def dot(a,b): return sum(x*y for x,y in zip(a,b))
    def norm(a): return math.sqrt(dot(a,a))+1e-12
    curv = 0.0; cnt=0
    for i in range(1, len(points)-1):
        a = [points[i][k]-points[i-1][k] for k in range(len(points[i]))]
        b = [points[i+1][k]-points[i][k] for k in range(len(points[i]))]
        cosang = max(-1.0, min(1.0, dot(a,b)/(norm(a)*norm(b))))
        curv += math.acos(cosang); cnt+=1
    return curv/max(1,cnt)
