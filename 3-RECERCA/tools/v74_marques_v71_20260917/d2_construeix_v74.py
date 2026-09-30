"""D2 (V74) · Construeix les capes canviades de la V74 a partir dels retalls de la V71 de Pere, recompon, mesura i escriu els paràmetres de b11.
Canvis (tots dins de r ≤ 458 px del centre lunar, ROI (4377,2777)–(6377,4777); cap màscara ni alfa tocada):
  · capa 3 (base): dins la silueta fotografiada (R 456,0; vora erf σ 1 px) el farcit agregat clar (R 0,98) passa a un gris fosc al nivell de la
    vora de la capa 30 (mitjana per sector de 5° a r 444–450, suavitzada) → la vora de la màscara a mà ja no deixa veure cap franja clara.
  · capa 57 (POWAAAH3, hard light): neutre (0,5) més enllà de r 447 (vora del seu HDR; la seva ploma clara 447–452 i el blanc de fora no són contingut).
  · filtres 41, 42, 45, 46 (multiplicar) → 1,0 i 47, 49, 51, 53, 55, 56 (superposar) → 0,5 dins la silueta (erf a 455,5, σ 1): cap filtre té
    corona dins la Lluna; el que hi tenien era la resposta al forat (biaix, V35).
Mètriques de porta: L* a 452–456 per sector; índex de dentat (std del pas alt σ 1° del radi del 50 % per sector de 10°); cap canvi a r>462 ni a r<430; transparència igual a V71."""
import sys, os, json, numpy as np
from scipy.ndimage import gaussian_filter1d, map_coordinates
from scipy.special import erf
from PIL import Image
NEW='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/6346f583-afd0-49da-9c17-95128c31820e/scratchpad'; S4='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad'
sys.path.insert(0,NEW); os.chdir(NEW); import compo71 as c
CX,CY,RS=998.88,998.41,456.0; Y,X=np.mgrid[0:2000,0:2000]; rr=np.hypot(X-CX,Y-CY); az=(np.degrees(np.arctan2(-(Y-CY),X-CX)))%360
def w_in(r0,s=1.0): return 0.5*(1-erf((rr-r0)/(np.sqrt(2)*s)))
def desa(lid,arr3,src):
    d=np.load(src); out={k:d[k] for k in d.files if k not in('c0','c1','c2')}
    for i,k in enumerate(('c0','c1','c2')): out[k]=np.uint16(np.round(np.clip(arr3[...,i],0,1)*65535))
    np.savez_compressed(S4+'/roi74_L%d.npz'%lid,**out)
d30=np.load('roi71_L30.npz'); L30=np.dstack([d30['c0'],d30['c1'],d30['c2']]).astype(np.float64).mean(-1)/65535
niv=np.array([L30[(az>=a0)&(az<a0+5)&(rr>=444)&(rr<450)].mean() for a0 in range(0,360,5)]); nivmap=np.interp(az,np.arange(0,360,5)+2.5,gaussian_filter1d(niv,2,mode='wrap'),period=360)
b3=np.load('roi71_L3.npz'); B=np.dstack([b3['c0'],b3['c1'],b3['c2']]).astype(np.float64)/65535; w=w_in(RS)[...,None]; desa(3,B*(1-w)+nivmap[...,None]*w,'roi71_L3.npz')
d57=np.load('roi71_L57.npz'); R=np.dstack([d57['c0'],d57['c1'],d57['c2']]).astype(np.float64)/65535; w=w_in(447.0)[...,None]; desa(57,R*w+0.5*(1-w),'roi71_L57.npz')
for lid in (41,42,45,46,47,49,51,53,55,56):
    d=np.load('roi71_L%d.npz'%lid); R=np.dstack([d['c0'],d['c1'],d['c2']]).astype(np.float64)/65535; neu=1.0 if c.LAYERS[lid]['blend']=='MULTIPLY' else 0.5; w=w_in(455.5)[...,None]; desa(lid,R*(1-w)+neu*w,'roi71_L%d.npz'%lid)
lids=[3,57,41,42,45,46,47,49,51,53,55,56]; c.OVERRIDE.update({lid:S4+'/roi74_L%d.npz'%lid for lid in lids})
C0,a0=c.recompon(exclou=(218,219,220)); c.OVERRIDE.clear()   # V74
C1,a1=c.recompon(exclou=(218,219,220))                       # V71 (referència, sense marques)
c.OVERRIDE.update({lid:S4+'/roi74_L%d.npz'%lid for lid in lids})
np.savez_compressed(S4+'/roi74_compost.npz',C=np.uint16(np.round(np.clip(C0,0,1)*65535)),a=np.uint16(np.round(np.clip(a0,0,1)*65535)))
def lab(C):
    lin=np.clip(C,0,1)**2.2; M=np.array([[0.5767,0.1856,0.1882],[0.2974,0.6273,0.0753],[0.0270,0.0707,0.9911]]); XYZ=lin@M.T; wn=np.array([0.9505,1.0,1.089]); f=lambda t: np.where(t>0.008856,np.cbrt(t),7.787*t+16/116); fx,fy,fz=f(XYZ[...,0]/wn[0]),f(XYZ[...,1]/wn[1]),f(XYZ[...,2]/wn[2]); return 116*fy-16,500*(fx-fy),200*(fy-fz)
def dentat(C):
    Lm=C.mean(-1); r50=[]
    for a in np.arange(0,360,1.0):
        s=(az>=a)&(az<a+1)&(rr>=440)&(rr<470); rs=rr[s]; ls=Lm[s]; o=np.argsort(rs); rs,ls=rs[o],ls[o]; lo=np.median(ls[rs<446]); hi=np.median(ls[rs>464]); mid=(lo+hi)/2; r50.append(rs[np.argmax(ls>mid) if hi>lo else 0])
    r50=np.array(r50); hp=r50-gaussian_filter1d(r50,1.0,mode='wrap'); return r50,np.array([hp[i:i+10].std() for i in range(0,360,10)])
L1,_,B1=lab(C1); L0,_,B0=lab(C0); r1,d1=dentat(C1); r0,d0=dentat(C0)
rep={'limbe_452_456_Lstar_per_sector_30':{str(a):[float(L1[(az>=a)&(az<a+30)&(rr>=452)&(rr<456)].mean()),float(L0[(az>=a)&(az<a+30)&(rr>=452)&(rr<456)].mean())] for a in range(0,360,30)},
     'dentat_V71':[float(d1.mean()),float(d1.max())],'dentat_V74':[float(d0.mean()),float(d0.max())],'radi50_std_graus_V71_V74':[float(r1.std()),float(r0.std())],
     'max_dLstar_fora_r462':float(np.abs(L0-L1)[rr>462].max()),'max_dLstar_disc_r430':float(np.abs(L0-L1)[rr<430].max()),'alfa_min_V71_V74':[float(a1.min()),float(a0.min())],'px_alfa_lt_0998_V71_V74':[int((a1<0.998).sum()),int((a0<0.998).sum())]}
json.dump(rep,open(S4+'/d2_metriques_v74.json','w'),indent=1); print(json.dumps(rep,indent=1))
def polar(C):
    A=np.linspace(0,360,1441)[:-1]; Rr=np.arange(430,480,0.5); AA,RR=np.meshgrid(np.radians(A),Rr); xs=CX+RR*np.cos(AA); ys=CY-RR*np.sin(AA); return np.dstack([map_coordinates(C[...,k],[ys,xs],order=1) for k in range(3)])
P1,P0=polar(C1),polar(C0); lo,hi=np.percentile(P1,[0.5,99.5]); st=lambda v: np.uint8(np.clip((v-lo)/(hi-lo),0,1)*255)
Image.fromarray(np.vstack([st(P1),np.full((4,P1.shape[1],3),255,np.uint8),st(P0)])).save(S4+'/v_D12_tira_polar_limbe_V71_V74.png')
noms={3:'V74 disc fosc dins la silueta',57:'V74 neutre fora del seu HDR'}; noms.update({l:'V74 neutre dins la silueta' for l in (41,42,45,46,47,49,51,53,55,56)})
P={"src":"/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V71.psb","dst":"/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V74.psb","rebut":S4+"/b11_escriptura_v74.json","compost":S4+"/roi74_compost.npz","canvis":{str(l):["c0","c1","c2"] for l in lids},"fonts":{str(l):S4+"/roi74_L%d.npz"%l for l in lids},"noms":{str(k):v for k,v in noms.items()},"ocultes":[219,220],"roi":[4377,2777,6377,4777]}
json.dump(P,open(S4+'/v74_params.json','w'),indent=1,ensure_ascii=False); print('paràmetres per a b11_escriu_psb.py:',S4+'/v74_params.json')
