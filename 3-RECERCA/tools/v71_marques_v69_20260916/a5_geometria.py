"""A5: les vores al limbe amb UN detector (50 % del trànsit, 1440 azimuts, cercle robust): alfa earthshine, màscara/alfa base, interiors 76, perles 96/204/206, i el compost."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import map_coordinates
C=np.load(SP+'/roi_compost_net.npz')['U'].astype(np.float32)/65535
CX0,CY0=5377.0-4377,3777.0-2777   # centre lunar inicial (ROI)
TH=np.deg2rad(np.arange(0,360,0.25)); RR=np.arange(380,540,0.25)
def perfils(img):
    xs=CX0+RR[None,:]*np.cos(TH[:,None]); ys=CY0-RR[None,:]*np.sin(TH[:,None])   # azimut antihorari des de l'est (+x), y cap avall
    return map_coordinates(img,[ys.ravel(),xs.ravel()],order=1,mode='nearest').reshape(len(TH),len(RR))
def vora_50(P,dins_alt=True):
    """radi on el perfil creua el 50 % entre el nivell interior (r 400–430) i l'exterior (r 480–510), per azimut."""
    lo=np.median(P[:,(RR>=400)&(RR<=430)],1); hi=np.median(P[:,(RR>=480)&(RR<=510)],1); mid=(lo+hi)/2
    out=np.full(len(TH),np.nan)
    for i in range(len(TH)):
        p=P[i]; s=np.sign(p-mid[i]); j=np.nonzero(np.diff(s)!=0)[0]
        if len(j): k=j[0]; out[i]=RR[k]+(mid[i]-p[k])/(p[k+1]-p[k]+1e-12)*(RR[k+1]-RR[k])
    return out
def cercle(r):
    ok=np.isfinite(r); A=np.stack([np.ones(ok.sum()),np.cos(TH[ok]),np.sin(TH[ok])],1); b=r[ok]
    for _ in range(5):
        x,*_=np.linalg.lstsq(A,b,rcond=None); res=b-A@x; s=1.4826*np.median(np.abs(res)); w=np.abs(res)<3*max(s,0.3); A,b=A[w],b[w]
    return dict(R=round(float(x[0]),2),dx=round(float(x[1]),2),dy=round(float(-x[2]),2),n=int(len(b)),rms=round(float(np.std(b-A@x)),2))
res={}; perf={}
# 1) alfa efectiva de cada capa (alfa × màscara), 2) lluminància del compost
for lid,nom in [(30,'earthshine alfa×màsc'),(3,'base alfa×màsc (forat)'),(76,'interiors 06–12 alfa×màsc'),(96,'perles 96 alfa×màsc'),(204,'perles 204 alfa×màsc'),(206,'perles 206 alfa×màsc')]:
    rgb,a=carrega(lid); P=perfils(a/ (LAYERS[lid]['opacity']/255.0)); r=vora_50(P); res[nom]=cercle(r); perf[nom]=r
    print(f"{nom:28s} {res[nom]}")
# les fotos: la silueta lunar dins de les capes de perles/interiors (lluminància del RGB on alfa>0)
for lid,nom in [(76,'interiors 76 RGB (silueta)'),(96,'perles 96 RGB (silueta)'),(204,'perles 204 RGB (silueta)'),(206,'perles 206 RGB (silueta)')]:
    rgb,a=carrega(lid); L=rgb.mean(-1); P=perfils(L); r=vora_50(P); res[nom]=cercle(r); perf[nom]=r; print(f"{nom:28s} {res[nom]}")
L=C.mean(-1); P=perfils(L); r=vora_50(P); res['compost net (lluminància)']=cercle(r); perf['compost net (lluminància)']=r; print('compost net',res['compost net (lluminància)'])
json.dump(res,open(SP+'/a5_vores.json','w'),indent=1); np.savez_compressed(SP+'/a5_perfils.npz',TH=TH,RR=RR,**{k.replace(' ','_'):v for k,v in perf.items()})
