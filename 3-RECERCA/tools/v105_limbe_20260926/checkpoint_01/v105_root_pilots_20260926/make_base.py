"""Photographic HDR pilot from the same observed hybrid used by filters."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
R=Path('/Users/USUARI/Desktop/Eclipse 2026');O=Path('/private/tmp/v105_root_pilots_20260926/P01')
sys.path.insert(0,'/private/tmp/v105_color_pilot_20260926')
from HEADROOM import render_headroom
from color_pilot import color_ratios
sys.path.insert(0,str(R/'3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat,comp
q=np.load(O/'Q_OBSERVED.npz');E=q['E'];y0,y1,x0,x1=map(int,q['box']);box=(x0,y0,x1,y1)
yy,xx=np.mgrid[y0:y1,x0:x1];cx,cy,r=q['centre'];d=np.hypot(xx-cx,yy-cy)-r
valid=q['observed']&np.all(np.isfinite(E),axis=-1)&np.all(E>0,axis=-1)
L,chrom=color_ratios(E,valid)
head=json.loads(Path('/private/tmp/v105_color_pilot_20260926/HEADROOM.json').read_text())['models']['0.14']['config']
out,inter=render_headroom(L,chrom,head['anchor'],.14,head['logRG'],head['logBG'],head['Lref'])
valid&=np.all(np.isfinite(out)&(out>=0)&(out<=1),-1)
S=Estat(R/'4-RESULTATS/v103_banda_20260926/E/estat_v103');P=S.pila(box=box);old=S.rgb(3,box)
moon=np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L258.npz')['c-1'][77:1477,77:1477]/65535
# Fully opaque lunar interior stays byte-exact. Native lunar layer/mask unchanged.
z=np.clip((d-50)/100,0,1);w=(1-z*z*(3-2*z))*valid*(moon<.95)
base=np.where(w[...,None]>0,(1-w[...,None])*old+w[...,None]*np.nan_to_num(out),old)
b16=np.rint(base*65535).clip(0,65535).astype(np.uint16)
np.savez_compressed(O/'BASE_ROI.npz',base_rgb_u16=b16,box_xyxy=np.array(box),replacement_weight=w.astype(np.float32),valid_observed=valid,configuration_json=np.array(json.dumps(head)))
oldc,_=comp([(m,f,a)for lid,m,f,a in P],1400,1400)
newc,_=comp([(m,base if lid==3 else f,a)for lid,m,f,a in P],1400,1400)
np.save(O/'old_comp.npy',oldc);np.save(O/'base_only_comp.npy',newc)
coords={'top':(640,205,860,300),'upper_left':(300,290,515,380),'lower_left':(300,960,515,1090),'left':(205,600,335,770)}
for name,(a,b,c,e)in coords.items():
    ims=[]
    for arr,label in [(old,'Old base'),(base,'Observed base'),(oldc,'Old composite'),(newc,'New base old filters')]:
        im=Image.fromarray(np.uint8(arr[b:e,a:c].clip(0,1)*255)).resize(((c-a)*3,(e-b)*3),Image.Resampling.NEAREST)
        can=Image.new('RGB',(im.width,im.height+28),'#222222');can.paste(im,(0,28));ImageDraw.Draw(can).text((6,8),label,fill='white');ims.append(can)
    full=Image.new('RGB',(sum(i.width for i in ims),ims[0].height));off=0
    for im in ims:full.paste(im,(off,0));off+=im.width
    full.save(O/f'base_{name}.png')
sel=w>0
rep={'pixels_replaced':int(sel.sum()),'RGB_u16_65535_new_counts':np.sum((b16==65535)&sel[...,None],axis=(0,1)).tolist(),'RGB_u16_65535_old_counts':np.sum((np.rint(old*65535)==65535)&sel[...,None],axis=(0,1)).tolist(),'outside150_maxDN':int(np.max(abs(b16[d>=150].astype(int)-np.rint(old[d>=150]*65535).astype(int)))),'lunar_alpha095_maxDN':int(np.max(abs(b16[moon>=.95].astype(int)-np.rint(old[moon>=.95]*65535).astype(int)))),'tone':head,'status':'PILOT; raw calibration and native clipping still under test'}
(O/'BASE.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
