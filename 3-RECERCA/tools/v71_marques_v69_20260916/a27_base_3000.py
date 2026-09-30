"""A27: finestra 3000×3000 de la base (id 3) i del seu alfa/màscara centrada al centre lunar (per al model del vel amb la corona de pantalla des-tonificada, com a alternativa a l'HDR RAW)."""
import sys, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from psb69 import PSB
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
p=PSB('/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V69.psb')
cx,cy=4377+998.88,2777+998.41; x0,y0=int(round(cx))-1500,int(round(cy))-1500; box=(x0,y0,x0+3000,y0+3000)
d={}
for cid in (0,1,2,-1,-2): d['c%d'%cid]=p.channel_box(3,cid,box,fill=0)
np.savez_compressed(SP+'/base_3000.npz',**d,box=np.array(box)); print('base 3000² extreta; caixa',box,'centre lunar a la finestra',(cx-x0,cy-y0))
