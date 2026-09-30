"""Read-only geometric audit of the existing V112 Brno windows; never changes QA windows or thresholds.
Astronomical rectangle excludes the frame and caption in the original PNG.
The two-original-pixel inward guard covers cv2 INTER_CUBIC interpolation support.
This is support only, not SNR, radiometric calibration, or registration accuracy.
"""
from pathlib import Path
import hashlib,json
import numpy as np
CATALOG={
 '200':('TSE_2026_200mm_DHS.png','optim3',(40,40,1470,932)),
 '400':('TSE_2026_400mm_DHS.png','optim3',(40,40,1501,995)),
 '530':('TSE_2026_530mm_DHS.png','optim',(40,40,1516,1020)),
}
PINNED={'4-RESULTATS/v82_capes_brno_20260918/registre_v82.json': 'ade1bc469fc3fa82e0dac9b14730203e8d82680eb689867e731a24543810a044', '3-RECERCA/druckmuller_fotos_finals/TSE_2026_200mm_DHS.png': '2b3e8afc40ec5c4a6e0c0dd9e1377bec6a93c4eb816b4c5f8932bc967648f10f', '3-RECERCA/druckmuller_fotos_finals/TSE_2026_400mm_DHS.png': '39260ba08f410daa1797e41b08470d0ef5191560ea39b9613b3804ed205ef59e', '3-RECERCA/druckmuller_fotos_finals/TSE_2026_530mm_DHS.png': 'c9db808d71223f7915351fbd8cdd57712bbc1cda99465607d99fa60f5ee6d6a7'}
def digest(path):
 with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def window_support(inverse_affine,box,astro_bounds,halo=32,interpolation_guard=2):
 x0,y0,x1,y1=map(int,box);loX,loY,hiX,hiY=map(float,astro_bounds)
 loX+=interpolation_guard;loY+=interpolation_guard;hiX-=interpolation_guard;hiY-=interpolation_guard
 yy,xx=np.ogrid[y0-halo:y1+halo,x0-halo:x1+halo]
 iv=np.asarray(inverse_affine,dtype=float)
 px=iv[0,0]*xx+iv[0,1]*yy+iv[0,2];py=iv[1,0]*xx+iv[1,1]*yy+iv[1,2]
 valid=(px>=loX)&(px<=hiX)&(py>=loY)&(py<=hiY)
 return dict(pixels=int(valid.size),valid=int(valid.sum()),invalid=int((~valid).sum()),complete=bool(valid.all()),fraction=float(valid.mean()),png_x_range=[float(px.min()),float(px.max())],png_y_range=[float(py.min()),float(py.max())])
def check(root,windows):
 root=Path(root);files={str(root/k):v for k,v in PINNED.items()}
 identity_failures=[dict(check='frozen_reference_footprint',path=p) for p,h in files.items() if not Path(p).is_file() or digest(p)!=h]
 out=dict(status='FAIL',gate_sha256=digest(Path(__file__)),meaning='Physical astronomical footprint only; no QA redefinition or scientific-quality approval',failures=identity_failures,rows=[])
 if identity_failures:return out
 reg=json.loads((root/'4-RESULTATS/v82_capes_brno_20260918/registre_v82.json').read_text())
 for ref,(name,variant,bounds) in CATALOG.items():
  mat=np.vstack([reg['imatges'][name][variant]['A_png_a_v'],[0,0,1]]);iv=np.linalg.inv(mat)[:2]
  for window,box in windows.items():
   used=not(ref=='530' and window=='NE') # Exact pre-existing qa_brno.py exclusion; do not add exclusions here.
   row=dict(reference=ref,window=window,used_by_frozen_QA=used,box=box,astronomical_rectangle_inclusive=bounds,interpolation_guard_native_px=2)
   row['window']=window;row['core']=window_support(iv,box,bounds,halo=0);row['margin32']=window_support(iv,box,bounds,halo=32)
   out['rows'].append(row)
   if used and not row['margin32']['complete']:out['failures'].append(dict(check='reference_astronomical_support',reference=ref,window=window,invalid=row['margin32']['invalid'],pixels=row['margin32']['pixels']))
 if not out['failures']:out['status']='SUPPORT_PASS'
 return out
