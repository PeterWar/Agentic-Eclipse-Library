import sys,json
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw
R=Path('/Users/USUARI/Desktop/Eclipse 2026');O=Path('/private/tmp/v105_root_pilots_20260926');O.mkdir(exist_ok=True)
sys.path.insert(0,str(R/'3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat,comp,dist_limbe
E=R/'4-RESULTATS/v103_banda_20260926/E';S=Estat(E/'estat_v103');box=(4600,3000,6150,4550);x0,y0,x1,y1=box;d=dist_limbe(box)
old=S.rgb(3,box);new=np.asarray(np.load(E/'base_v103/base_v103_u16.npy',mmap_mode='r')[y0:y1,x0:x1],np.float32)/65535
support=np.load(E/'lineal_v103_franja/A3C_franja_silueta.npz')['domini_E']
q=np.load(E/'lineal_v103_franja/A3C_franja_silueta.npz');print('Q box',q['box'],'shapes',new.shape, q['F'].shape)
P=S.pila(box=box);cur,al=comp([(m,f,a) for _,m,f,a in P],y1-y0,x1-x0)
# Original pipeline unguarded before f2c, diagnostic-only. No product modifications.
new_comp,_=comp([(m,new if lid==3 else f,a) for lid,m,f,a in P],y1-y0,x1-x0)
np.save(O/'base_old.npy',old);np.save(O/'base_f2b.npy',new);np.save(O/'comp_old.npy',cur);np.save(O/'comp_f2b.npy',new_comp)
coords={'dalt':(646,283,906,413),'dalt_esquerra':(386,386,526,526),'baix_esquerra':(386,1026,526,1166)}
for name,(ax,ay,bx,by) in coords.items():
    ims=[]
    for a,title in ((old,'base V104'),(new,'base f2b'),(cur,'compost V104 emulat'),(new_comp,'compost f2b emulat')):
        im=Image.fromarray((a[ay:by,ax:bx]*255).clip(0,255).astype(np.uint8)).resize(((bx-ax)*3,(by-ay)*3),Image.Resampling.NEAREST)
        can=Image.new('RGB',(im.width,im.height+30),'#202020');can.paste(im,(0,30));ImageDraw.Draw(can).text((6,6),title,fill='white');ims.append(can)
    out=Image.new('RGB',(sum(i.width for i in ims)+6*(len(ims)-1),ims[0].height),'white');off=0
    for im in ims:out.paste(im,(off,0));off+=im.width+6
    out.save(O/f'pilot_f2b_{name}.png')
for lo,hi in [(0,3),(3,8),(8,15),(15,30),(30,60),(60,120),(150,250)]:
    z=(d>=lo)&(d<hi);print(lo,hi,'old',np.median(old[z],axis=0),'new',np.median(new[z],axis=0))
print('DONE')
