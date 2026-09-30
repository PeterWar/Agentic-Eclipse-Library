"""c3b (V106) · Ràster definitiu de la capa «Detall arran del limbe · V106» (a partir de $V106_OUT/CAPA_F.npy, c2b): gris R=G=B, 16 bits (neutre 32768, com la 302),
alfa 65535 només on la capa actua (g > 0, dilatat 2 px) i la Lluna de Pere (258) no és opaca (< 0,999); fora, alfa 0. Caixa: la caixa lunar."""
import sys, json, hashlib, numpy as np, cv2
from pathlib import Path
R0=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(R0/'3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat
import os; T=R0/os.environ['V106_OUT']; O=T
F=np.load(T/'CAPA_F.npy'); box=(4677,3077,6077,4477); bx0,by0,bx1,by1=box
S=Estat(R0/'4-RESULTATS/v105_limbe_20260926/claude/estat_v105')
a258=S.alfa_efectiva(258,box)          # alfa de la Lluna de Pere (amb opacitat 255 = 1)
actua=np.abs(F-0.5)>1e-6
act=cv2.dilate(actua.astype(np.uint8),np.ones((5,5),np.uint8))>0
alfa=act&(a258<0.999)
F=np.where(alfa,F,0.5)
v16=np.where(alfa,np.clip(np.rint(32768+(F-0.5)*65535),0,65535),32768).astype(np.uint16)
A16=np.where(alfa,65535,0).astype(np.uint16)
RGB16=np.repeat(v16[...,None],3,-1)
np.savez_compressed(O/'CAPA_V106.npz',RGB16=RGB16,A16=A16,box=np.array([by0,by1,bx0,bx1]))
h=hashlib.sha256(RGB16.tobytes()+A16.tobytes()).hexdigest()
Fm=np.where(alfa,(v16.astype(np.float64)-32768)/65535,np.nan)
rep=dict(pixels_actius=int(alfa.sum()),F_menys_05_rms=float(np.nanstd(Fm)),F_menys_05_min=float(np.nanmin(Fm)),F_menys_05_max=float(np.nanmax(Fm)),
         frac_fora_035_065=float(np.mean(np.abs(Fm[alfa])>0.15)),pixels_tapats_per_la_lluna_opaca=int((act&(a258>=0.999)).sum()),sha_pixels=h,caixa_x0y0x1y1=list(box))
(O/'CAPA_V106.json').write_text(json.dumps(rep,indent=1)); print(json.dumps(rep,indent=1))
