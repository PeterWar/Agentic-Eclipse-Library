"""Separate Sony reference with all21 ordinary-CFA renders and frozen V45 temporal
preference. Never injected into the Vixen reconstruction. Store G1/G2 conditional
splits as controls, not independent sensors or independent preference estimates.
"""
from detail_common import *
import sys
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from f2_temporal import ng,GAIN,ALPHA,component,epoch
fr=[m for m in json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'] if m['tren']=='sony'];keys=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F2_temporal.json').read_text())['groups']['sony']['keys'];pref=np.load(CAU45/'sony_epoch_preference.npy');yy,xx=np.mgrid[:N,:N];dist=np.hypot(xx+4677-5367,yy+3077-3545);t=np.clip((dist-140)/40,0,1);ghost=t*t*(3-2*t)
arrays={};rows=[]
for split in ['', '1','2']:
 num=np.zeros((N,N));den=num.copy();pn=num.copy();pd=num.copy();vn=num.copy()
 for m in fr:
  receipt=OUT/'native'/('sony_'+m['stem']+'.json');assert receipt.exists();z=np.load(receipt.with_suffix('.npz'));gain=GAIN[m['grup']];g=z['g'+split].astype(float)*gain;q=z['q'+split].astype(float);v=z['variance'+split].astype(float)*gain**2;valid=np.isfinite(g)&np.isfinite(v)&(q>0)&(v>0);vs,_=ng(v,valid,4);w=np.where(valid,q/np.maximum(vs*ALPHA[component(m)],1e-12),0)
  if m['grup']=='sony_B':w*=ghost
  p=pref[keys.index(epoch(m))];num+=w*np.nan_to_num(g);den+=w;pn+=w*p*np.nan_to_num(g);pd+=w*p;vn+=(w*p)**2*np.nan_to_num(v)
  if not split:rows.append(dict(stem=m['stem'],gain=gain,epoch=epoch(m)))
 arrays['all'+split]=np.where(den>0,num/np.maximum(den,1e-30),np.nan);arrays['reference'+split]=np.where(pd>0,pn/np.maximum(pd,1e-30),np.nan);arrays['weight'+split]=pd;arrays['variance'+split]=np.where(pd>0,vn/np.maximum(pd**2,1e-30),np.nan)
 print('Sony split',split or 'combined','complete',flush=True)
np.savez_compressed(OUT/'B2_sony_reference.npz',**arrays);save('B2_sony_reference.json',dict(method=__doc__,frames=rows,complete21=len(rows)==21,old_temporal_preferences=True,old_ghost_exclusion=True,geometry='Original V45 including SonyB+8.10arcmin star correction and lunar shift'))
