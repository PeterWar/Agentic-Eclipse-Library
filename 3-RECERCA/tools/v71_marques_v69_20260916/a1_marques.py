"""A1: extreu la capa «Artefactes Pere» (id 218) de V69.psb: components, colors, posició."""
import sys, json, numpy as np
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from psb69 import PSB
from scipy.ndimage import label, find_objects, binary_dilation
SP='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad'
p=PSB('/Users/USUARI/Desktop/Eclipse 2026/1-PHOTOSHOP/V69.psb')
json.dump(dict(width=p.width,height=p.height,channels=p.channels,image_data_offset=p.image_data_offset,layers=p.layers),open(SP+'/v69_index.json','w'),indent=1,ensure_ascii=False,default=str)
for l in p.layers: print(f"{l['i']:2d} id={l['id']:>3} vis={'V' if l['visible'] else '-'} op={l['opacity']:3d} {l['blend']:12s} [{l['left']},{l['top']} {l['right']-l['left']}x{l['bottom']-l['top']}] {l['name']}")
L=p.layer(218); x0,y0=L['left'],L['top']
A,_=p.channel(218,-1); R,_=p.channel(218,0); G,_=p.channel(218,1); B,_=p.channel(218,2)
print('marques: forma',A.shape,'alfa>0:',int((A>0).sum()),'alfa==65535:',int((A==65535).sum()),'alfa valors únics:',len(np.unique(A)))
np.savez_compressed(SP+'/marques_218.npz',A=A,R=R,G=G,B=B,x0=x0,y0=y0)
sel=A>0; lab,n=label(binary_dilation(sel,iterations=3)); rows=[]
for j,sl in enumerate(find_objects(lab),1):
    k=(lab[sl]==j)&sel[sl]
    if k.sum()<4: continue
    yy,xx=np.nonzero(k); yy=yy+sl[0].start; xx=xx+sl[1].start
    rgb=np.stack([R[yy,xx],G[yy,xx],B[yy,xx]],1).astype(float); a=A[yy,xx].astype(float)/65535
    med=np.median(rgb,0); 
    rows.append(dict(id=len(rows)+1,n=int(len(xx)),alfa_mitjana=round(float(a.mean()),3),bbox=[int(xx.min()+x0),int(yy.min()+y0),int(xx.max()+x0+1),int(yy.max()+y0+1)],
        centre=[round(float(xx.mean()+x0),1),round(float(yy.mean()+y0),1)],rgb_mediana=[int(v) for v in med],rgb8=[int(v/257) for v in med]))
json.dump(rows,open(SP+'/a1_marques.json','w'),indent=1)
for r in rows: print(r)
