"""A4: recompon la ROI amb compo.py i la compara amb el compost desat de V69 (sense la capa de marques)."""
import sys, numpy as np, json
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
C=np.load(SP+'/roi_compost.npz')['C'].astype(np.float32)/65535
m=np.load(SP+'/marques_218.npz'); A=np.zeros((2000,2000),np.float32); mx,my=int(m['x0'])-4377,int(m['y0'])-2777; A[my:my+m['A'].shape[0],mx:mx+m['A'].shape[1]]=m['A']/65535
Cr,ar=recompon()
sense=(A==0)
d=np.abs(Cr-C[...,:3])*65535; da=np.abs(ar-C[...,3])*65535
print('píxels sense marca:',int(sense.sum()))
print('RGB  |dif| DN16: max %.1f  p99,9 %.2f  p99 %.2f  mediana %.2f'%(d[sense].max(),np.percentile(d[sense],99.9),np.percentile(d[sense],99),np.median(d[sense])))
print('alfa |dif| DN16: max %.1f  p99,9 %.2f'%(da[sense].max(),np.percentile(da[sense],99.9)))
# on són les diferències grans?
yy,xx=np.nonzero((d.max(-1)>200)&sense); print('n>200 DN16:',len(xx)); 
if len(xx): print(' x rang',xx.min()+4377,xx.max()+4377,'y rang',yy.min()+2777,yy.max()+2777)
np.savez_compressed(SP+'/roi_recomp.npz',C=(np.clip(Cr,0,1)*65535+.5).astype(np.uint16),a=(np.clip(ar,0,1)*65535+.5).astype(np.uint16))
