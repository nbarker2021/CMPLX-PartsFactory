"""
Viewer24 slot-09 (2026-05-19T01:17:22Z).
Source: Downloads/Viewer24_Controller_v2_CA_Residue.zip
"""

import math, random
from typing import List, Tuple, Dict
class DihedralCA:
    def __init__(self, tiles_x=6, tiles_y=4, n=64, seed=1337):
        self.tiles_x = tiles_x; self.tiles_y = tiles_y; self.n = n
        self.W = tiles_x*n; self.H = tiles_y*n
        self.zr = [0.0]*(self.W*self.H); self.zi = [0.0]*(self.W*self.H)
        self.cr = [0.0]*(self.W*self.H); self.ci = [0.0]*(self.W*self.H)
        self.wr = [0.0]*(self.W*self.H); self.wi = [0.0]*(self.W*self.H)
        self.step_id = 0; self.rnd = random.Random(seed)
    def idx(self, x,y): x%=self.W; y%=self.H; return y*self.W + x
    def seed_from_specs(self, specs: List[str]):
        def ph(spec):
            h=0
            for ch in spec: h=(h*131+ord(ch))&0xffffffff
            return (h%360)*math.pi/180.0
        amp=0.7885
        for ty in range(self.tiles_y):
            for tx in range(self.tiles_x):
                tile=ty*self.tiles_x+tx
                phi=ph(specs[tile] if tile<len(specs) else "LEECH")
                cr=amp*math.cos(phi); ci=amp*math.sin(phi)
                for j in range(self.n):
                    for i in range(self.n):
                        x=tx*self.n+i; y=ty*self.n+j; k=self.idx(x,y)
                        self.cr[k]=cr; self.ci[k]=ci
                        self.zr[k]=0.001*math.cos((i+j)*0.1)
                        self.zi[k]=0.001*math.sin((i-j)*0.1)
                        self.wr[k]=self.zr[k]; self.wi[k]=self.zi[k]
    def neighbor_sum(self,x,y):
        s1=s2=0.0
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            k=self.idx(x+dx,y+dy); s1+=self.zr[k]; s2+=self.zi[k]
        return s1,s2
    def step(self,kappa=0.08,dual=True):
        out_zr=[0.0]*len(self.zr); out_zi=[0.0]*len(self.zi)
        out_wr=[0.0]*len(self.wr); out_wi=[0.0]*len(self.wi)
        for y in range(self.H):
            for x in range(self.W):
                k=self.idx(x,y); zr=self.zr[k]; zi=self.zi[k]; cr=self.cr[k]; ci=self.ci[k]
                nsr,nsi=self.neighbor_sum(x,y); lr=nsr-4.0*zr; li=nsi-4.0*zi
                zr2=zr*zr-zi*zi+cr+kappa*lr; zi2=2*zr*zi+ci+kappa*li
                out_zr[k]=zr2; out_zi[k]=zi2
                if dual:
                    ar=zr-cr; ai=zi-ci; r=max(0.0, (ar*ar+ai*ai))**0.5; th=math.atan2(ai,ar)
                    sr=math.sqrt(r); th2=0.5*th
                    out_wr[k]=sr*math.cos(th2); out_wi[k]=sr*math.sin(th2)
                else:
                    out_wr[k]=self.wr[k]; out_wi[k]=self.wi[k]
        self.zr,self.zi=out_zr,out_zi; self.wr,self.wi=out_wr,out_wi; self.step_id+=1
    def wavelength(self,k):
        r1=(self.zr[k]*self.zr[k]+self.zi[k]*self.zi[k])**0.5
        return 380.0+400.0*(math.tanh(0.5*r1))
    def tile_pixels_em(self,tile_index:int,alpha:int=160)->Dict:
        tx=tile_index%self.tiles_x; ty=tile_index//self.tiles_x
        w=self.n; h=self.n; data=[]; hexes=[]
        for j in range(h):
            for i in range(w):
                x=tx*self.n+i; y=ty*self.n+j; k=self.idx(x,y)
                wl=self.wavelength(k)
                R,G,B=wavelength_to_rgb(wl)
                data.extend([R,G,B,alpha])
                hexes.append(rgb_to_hex(R,G,B))
        return {"w":w,"h":h,"rgba":data,"hex":hexes}
def wavelength_to_rgb(wl: float):
    if wl<380: wl=380
    if wl>780: wl=780
    def clamp(x): return 0 if x<0 else (1 if x>1 else x)
    if wl<440: t=(wl-380)/(440-380); R,G,B=(clamp(1.0-t),0.0,1.0)
    elif wl<490: t=(wl-440)/(490-440); R,G,B=(0.0,clamp(t),1.0)
    elif wl<510: t=(wl-490)/(510-490); R,G,B=(0.0,1.0,clamp(1.0-t))
    elif wl<580: t=(wl-510)/(580-510); R,G,B=(clamp(t),1.0,0.0)
    elif wl<645: t=(wl-580)/(645-580); R,G,B=(1.0,clamp(1.0-t),0.0)
    else: t=(wl-645)/(780-645); R,G,B=(1.0,0.0,clamp(0.3*(1.0-t)))
    if wl<420: f=0.3+0.7*(wl-380)/(420-380)
    elif wl>700: f=0.3+0.7*(780-wl)/(780-700)
    else: f=1.0
    return (int(255*R*f), int(255*G*f), int(255*B*f))
def rgb_to_hex(R,G,B):
    return "#{:02X}{:02X}{:02X}".format(max(0,min(255,R)), max(0,min(255,G)), max(0,min(255,B)))
