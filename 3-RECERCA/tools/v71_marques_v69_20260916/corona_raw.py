"""Descodificació lineal a mà dels CR3 Vixen (R6 III): mateix agrupament 2×2 que libraw half_size (R, mitjana dels dos G, B), negre 512 a tots els canals
(mesurat als marges òptics; libraw llegeix [0,34,101,67] i user_black=512 l'hi SUMA), escala 65535/(16383−512) = 4,1297 DN16 per DN14, sense retall a 0.
Retorna (img float32 (H/2,W/2,3) en DN16, sat bool: alguna de les 4 fotocèl·lules del grup ≥ 15041 DN14 (= 60000 DN16))."""
import numpy as np, rawpy
ROOT='/Users/USUARI/Desktop/Eclipse 2026/0-RAW/Vixen R6III/Vixen Fase totalitat/'
NEGRE=512.0; BLANC=16383.0; ESCALA=65535.0/(BLANC-NEGRE); SAT14=NEGRE+60000.0/ESCALA   # 15041
def llegeix_ma(f):
    raw=rawpy.imread(ROOT+f); s=raw.sizes
    assert raw.color_desc==b'RGBG' and raw.raw_pattern.tolist()==[[0,1],[3,2]], (raw.color_desc,raw.raw_pattern)
    a=raw.raw_image[s.top_margin:s.top_margin+s.crop_height, s.left_margin:s.left_margin+s.crop_width].astype(np.float32)
    R=a[0::2,0::2]; G=(a[0::2,1::2]+a[1::2,0::2])*0.5; B=a[1::2,1::2]
    sat=np.maximum(np.maximum(a[0::2,0::2],a[0::2,1::2]),np.maximum(a[1::2,0::2],a[1::2,1::2]))>=SAT14
    img=np.dstack([R,G,B]); img=(img-NEGRE)*ESCALA
    return img.astype(np.float32), sat
