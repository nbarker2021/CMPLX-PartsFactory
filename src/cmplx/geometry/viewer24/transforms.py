"""
Viewer24 slot-09 (2026-05-19T01:17:22Z).
Source: Downloads/Viewer24_Controller_v2_CA_Residue.zip
"""

from typing import List, Tuple
def bbox(points: List[Tuple[float,float]]):
    if not points: return (0.0,0.0,1.0,1.0)
    xs = [p[0] for p in points]; ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))
def world_to_screen(points: List[Tuple[float,float]], width: int, height: int, padding: float=0.08):
    xmin,ymin,xmax,ymax = bbox(points)
    dx = xmax - xmin; dy = ymax - ymin
    if dx == 0: dx = 1.0
    if dy == 0: dy = 1.0
    sx = (1.0 - 2*padding) * width / dx
    sy = (1.0 - 2*padding) * height / dy
    s = sx if sx<sy else sy
    cx = (xmin + xmax)/2.0; cy = (ymin + ymax)/2.0
    tx = width*0.5 - s*cx
    ty = height*0.5 - s*cy
    return (s, tx, ty)
