import sys,json
from pathlib import Path
import numpy as np
ROOT=Path('/Users/USUARI/Desktop/Eclipse 2026');OUT=Path('/private/tmp/v105_color_pilot_20260926')
sys.path.insert(0,str(ROOT/'3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat,comp
sys.path.insert(0,str(OUT));from color_pilot import make_panel
S=Estat(ROOT/'4-RESULTATS/v103_banda_20260926/E/estat_v103');P=S.pila(box=(4677,3077,6077,4477))
old=next(f for lid,m,f,a in P if lid==3);C,_=comp([(m,f,a) for lid,m,f,a in P],1400,1400)
for name in ['572A2969','572A2975']:
 q=np.load(OUT/f'{name}_reference_curve_ready.npz');d=q['d_presentation_circle'];t=np.clip((d-50)/100,0,1);w=q['maskwhereupdate']*(1-t*t*(3-2*t))
 base=(1-w[...,None])*old+w[...,None]*q['RGB'];new,_=comp([(m,base if lid==3 else f,a) for lid,m,f,a in P],1400,1400)
 np.savez_compressed(OUT/f'{name}_reference_curve_EMULATED.npz',RGB=new,base_RGB=base,box=q['box'],provisional_weight=w)
 for key,(x0,x1,y0,y1) in {'top':(650,860,210,295),'upper_left':(310,520,275,360),'left':(210,330,600,750)}.items():
  sl=np.s_[y0:y1,x0:x1];v=np.ones(d[sl].shape,bool)
  make_panel([('Current old-filter composite',C[sl],v),('Reference-tone carrier + old filters',new[sl],v)],
   OUT/f'{name}_{key}_REFERENCE_EMULATED.png','DIAGNOSTIC: original reference tone, old filters; no adjustment layers; provisional 50-150 px transition',zoom=True)
print('DONE')
