"""Measure correction to all88 native sources by fixed radial diagnostic regions.
No radial image edits: these regions summarize observed values only.
"""
from detail_common import *
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);frames=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'];rows=[]
for m in frames:
 z=np.load(OUT/'native'/(m['tren']+'_'+m['stem']+'.npz'));o=np.load(m['native']['file']);valid=(z['q']>0)&(o['q']>0)&np.isfinite(z['g'])&np.isfinite(o['g']);regs=[]
 for lo,hi in [(0,350),(350,420),(420,435),(435,449),(449,454)]:
  mask=valid&(r>=lo)&(r<hi);n=int(mask.sum())
  if not n:continue
  d=z['g'][mask].astype(float)-o['g'][mask];regs.append(dict(radius=[lo,hi],pixels=n,old_mean=float(np.mean(o['g'][mask])),mean_change=float(d.mean()),rms_change=float(np.sqrt(np.mean(d*d))),max_abs_change=float(abs(d).max())))
 rows.append(dict(stem=m['stem'],tren=m['tren'],exp=m['exp'],regions=regs))
save('B3_native_change.json',dict(method=__doc__,frames=rows))
for tag in ['vixen','sony']:
 print(tag,[(r['stem'],[(g['radius'],round(g['rms_change'],3)) for g in r['regions'][-2:]]) for r in rows if r['tren']==tag and r['exp']>=1],flush=True)
