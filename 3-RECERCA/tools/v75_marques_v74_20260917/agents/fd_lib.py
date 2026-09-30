"""Verificador D (escèptic): utilitats pròpies (no reutilitza fa_lib/fc/fb més enllà de compo74/compo71)."""
import numpy as np, json, sys, importlib.util
S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'
OLD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
CX,CY,RS=998.88,998.41,456.0
Y,X=np.mgrid[0:2000,0:2000]; RR=np.hypot(X-CX,Y-CY); AZ=(np.degrees(np.arctan2(-(Y-CY),X-CX)))%360
M=np.array([[0.5767,0.1856,0.1882],[0.2974,0.6273,0.0753],[0.0270,0.0707,0.9911]],np.float64)
WN=np.array([0.9505,1.0,1.089],np.float64)
def lab(C):
    lin=np.clip(C.astype(np.float64),0,1)**2.2; XYZ=lin@M.T; t=XYZ/WN
    f=np.where(t>(6/29)**3,np.cbrt(t),t/(3*(6/29)**2)+4/29)
    return 116*f[...,1]-16, 500*(f[...,0]-f[...,1]), 200*(f[...,1]-f[...,2])
def Lstar(C): return lab(C)[0].astype(np.float32)
def modul(nom,ruta):
    sp=importlib.util.spec_from_file_location(nom,ruta); m=importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def compo74(): return modul('compo74',S4+'/compo74.py')
def compo71(): return modul('compo71',NEW+'/compo71.py')
_mk=None
def mask(k):
    global _mk
    if _mk is None: _mk=np.load(S4+'/marques74_masks.npz')
    return _mk[k]
def sector(a0,a1):
    if a0<=a1: return (AZ>=a0)&(AZ<a1)
    return (AZ>=a0)|(AZ<a1)
def anell(r0,r1): return (RR>=r0)&(RR<r1)
def dump(nom,obj):
    json.dump(obj,open(S4+f'/{nom}.json','w'),indent=1,ensure_ascii=False,default=lambda o: float(o) if isinstance(o,(np.floating,)) else (int(o) if isinstance(o,np.integer) else (o.tolist() if isinstance(o,np.ndarray) else str(o))))
    print('escrit',S4+f'/{nom}.json')
def compost_ps():
    d=np.load(S4+'/roi74p_compost.npz'); C=d['C']
    C=C.astype(np.float32)/(65535 if C.dtype==np.uint16 else 255)
    return C[...,:3]
def retall(C,y0,y1,x0,x1,Z=3,lo=0,hi=1):
    from PIL import Image
    A=np.clip((C[y0:y1,x0:x1]-lo)/(hi-lo),0,1)
    if A.ndim==2: A=np.dstack([A]*3)
    return Image.fromarray((A*255).astype(np.uint8)).resize(((x1-x0)*Z,(y1-y0)*Z),Image.NEAREST)
def fila(imgs,noms=None,sep=6):
    from PIL import Image, ImageDraw
    w=sum(i.width for i in imgs)+sep*(len(imgs)-1); h=max(i.height for i in imgs)
    out=Image.new('RGB',(w,h),(40,40,40)); x=0
    for k,i in enumerate(imgs):
        out.paste(i,(x,0))
        if noms: ImageDraw.Draw(out).text((x+3,3),noms[k],fill=(255,255,0))
        x+=i.width+sep
    return out
