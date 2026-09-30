"""fb10: contrast marca/entorn aparellat per anells (mateix radi), per a tots els camps i variants; i el perfil radial del contrast."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/e4f0fbff-bfdf-4da5-a1d0-1bbdf0423383/scratchpad')
from fb6_candidata import *
from scipy.ndimage import gaussian_filter
V=np.load(S4+'/fb6b_variants.npz'); candB=V['candB']; candBp=V['candBp']; Vlin=V['Vlin']; c0=float(V['c0'])
C6=np.load(S4+'/fb6_candidata.npz'); candA=C6['cand69']
f,finv,xc,yi=ajusta_f(RAWs,P); lin=finv(P); linp=lin-(Vlin-c0); fl=f(linp); fR=f(RAWs); rho=P-fR
disc=rr<430
def s6(A): m=disc.astype(float); return gaussian_filter(np.nan_to_num(A)*m,6)/np.maximum(gaussian_filter(m,6),1e-9)
rings=np.arange(170,412,4)
def contrast_anells(A,rel=True,mask_extra=None):
    a=s6(A); vals=[]
    for r0 in rings:
        ring=(rr>=r0)&(rr<r0+4); md=m6&ring; ed=e6&ring
        if mask_extra is not None: md&=mask_extra; ed&=mask_extra
        if md.sum()<20 or ed.sum()<20: continue
        vals.append(np.log(np.median(a[md])/np.median(a[ed])) if rel else np.median(a[md])-np.median(a[ed]))
    vals=np.array(vals); return float(np.median(vals)), vals
out={}
rows=[('RAW Vixen 10 s (lineal)',RAWs,True,None),('f⁻¹(P) (lineal)',lin,True,None),('Vlin−c0 model (additiu)',Vlin-c0,False,None),('RAW − (Vlin−c0)',RAWs-(Vlin-c0),True,None),('f⁻¹(P) − (Vlin−c0)',linp,True,None),
      ('f(RAW)',fR,True,None),('P (revelat Pere reconstruït)',P,True,None),('ρ = P − f(RAW) (additiu DN16)',rho,False,None),('W_S8 (additiu)',Wdq,False,None),('capa69 = P − W_S8',G69,True,None),('capa74 = capa69·F71',G74,True,None),('F71 (factor)',F71,True,None),
      ('LROC (capa 62)',L62,True,v62),('cand A (radial/sector per corba)',candA,True,None),('cand A · F71',candA*F71,True,None),('cand B (vel complet per corba)',candB,True,None),('cand B · F71',candB*F71,True,None),('cand B′ (azimutal per corba + S8)',candBp,True,None),('f(lin′) sense κ',fl,True,None)]
print(f"{'camp':36s} contrast marca/entorn aparellat per anells (mediana dels anells 170–410) | per terços de r: 170–250 / 250–330 / 330–410")
for nom,A,rel,mk in rows:
    c,vals=contrast_anells(A,rel,mk); n=len(vals); t=[float(np.median(vals[:n//3])),float(np.median(vals[n//3:2*n//3])),float(np.median(vals[2*n//3:]))]
    out[nom]=dict(contrast=c,tercos=t); print(f"{nom:36s} {c:+.4f}  | {t[0]:+.4f} / {t[1]:+.4f} / {t[2]:+.4f}")
json.dump(out,open(S4+'/fb10_anells.json','w'),indent=1,ensure_ascii=False); print('fet')
