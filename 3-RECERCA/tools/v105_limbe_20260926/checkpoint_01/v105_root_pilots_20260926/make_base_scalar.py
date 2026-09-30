"""P04 photographic base: measured intensity, existing presentation chromaticity.
No source RGB colour splice, extrapolation or texture transplantation.
Global tone parameters explicit; common shoulder is strictly monotonic.
"""
from pathlib import Path
import numpy as np,json,sys
from scipy.optimize import least_squares
from PIL import Image,ImageDraw
R=Path('/Users/USUARI/Desktop/Eclipse 2026');O=Path('/private/tmp/v105_root_pilots_20260926/P04')
sys.path.insert(0,'/private/tmp/v105_color_pilot_20260926');from color_pilot import decode,encode_unclipped
sys.path.insert(0,str(R/'3-RECERCA/tools/v97_refundacio_20260924'));from jutge_comu import Estat,comp
q=np.load(O/'Q_OBSERVED.npz');L=q['scalar_observed'];valid=q['scalar_valid'];y0,y1,x0,x1=map(int,q['box']);box=(x0,y0,x1,y1)
yy,xx=np.mgrid[y0:y1,x0:x1];cx,cy,r=q['centre'];d=np.hypot(xx-cx,yy-cy)-r
S=Estat(R/'4-RESULTATS/v103_banda_20260926/E/estat_v103');P=S.pila(box=box);old=S.rgb(3,box)
lin=decode(old);oldL=(lin[...,0]+2*lin[...,1]+lin[...,2])/4;chrom=lin/np.maximum(oldL[...,None],1e-20)
fit=valid&(d>=25)&(d<100)&(oldL>0)
Lref=float(np.median(L[fit]));slope=.14;knee=float(decode(.94));head=float(decode(.98))
def render(anchor,delta=0):
    tone=np.maximum(anchor+slope*np.log10(np.maximum(L*np.exp(delta),1e-20)/Lref),.001)
    rgb=decode(tone)[...,None]*chrom;mx=rgb.max(-1);u=np.maximum(mx-knee,0)
    compressed=np.where(mx>knee,knee+(head-knee)*u/(head-knee+u),mx)
    return encode_unclipped(rgb*(compressed/np.maximum(mx,1e-20))[...,None])
iy,ix=np.nonzero(fit);take=np.arange(0,len(iy),max(1,len(iy)//16000));iy,ix=iy[take],ix[take]
res=least_squares(lambda a:(render(a[0])[iy,ix]-old[iy,ix]).ravel(),[.66],bounds=([.1],[1]),loss='soft_l1',f_scale=.01)
anchor=float(res.x[0]);out=render(anchor)
valid=valid&np.all(np.isfinite(out)&(out>=0)&(out<=1),-1)
moon=np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L258.npz')['c-1'][77:1477,77:1477]/65535
z=np.clip((d-50)/100,0,1);w=(1-z*z*(3-2*z))*valid*(moon<.95)
base=np.where(w[...,None]>0,(1-w[...,None])*old+w[...,None]*np.nan_to_num(out),old)
b16=np.rint(base*65535).clip(0,65535).astype(np.uint16)
config={'anchor':anchor,'slope_log10':slope,'Lref':Lref,'shoulder_encoded_knee':.94,'shoulder_encoded_head':.98,'colour':'V104 base pixel chromaticity in linear AdobeRGB; common RGB scalar only','intensity':'observed L=(R+2G+B)/4, P02 nofloor undoPhi camera gains','replacement':'full to50px smoothstep50–150; no opaque lunar pixel changed','reason_shoulder':'P01 native produced714 newR-clipped pixels; head.98 excludes quantization to65535 before native adjustment','limitations':['Photographic presentation only; no new spectral colour calibration','Photoshop adjustments may have nonlocal response; native QA mandatory']}
np.savez_compressed(O/'BASE_ROI.npz',base_rgb_u16=b16,box_xyxy=np.array(box),replacement_weight=w.astype(np.float32),valid_observed=valid,configuration_json=np.array(json.dumps(config)))
oldc,_=comp([(m,f,a)for lid,m,f,a in P],1400,1400);newc,_=comp([(m,base if lid==3 else f,a)for lid,m,f,a in P],1400,1400)
np.save(O/'old_comp.npy',oldc);np.save(O/'base_only_comp.npy',newc)
J=(render(anchor,1e-4)-render(anchor,-1e-4))/2e-4
rep={'config':config,'pixels_replaced':int((w>0).sum()),'new_clip_counts':np.sum((b16==65535)&(w>0)[...,None],axis=(0,1)).tolist(),'outside150_maxDN':int(np.max(abs(b16[d>=150].astype(int)-np.rint(old[d>=150]*65535).astype(int)))),'lunar_alpha095_maxDN':int(np.max(abs(b16[moon>=.95].astype(int)-np.rint(old[moon>=.95]*65535).astype(int)))),'bands':{}}
for lo,hi in [(0,3),(3,10),(10,25),(25,100)]:
    sel=valid&(d>=lo)&(d<hi);rep['bands'][f'{lo}-{hi}']={'median_J_per_lnL':np.median(J[sel],axis=0).tolist(),'medianRGB':np.median(out[sel],axis=0).tolist(),'nonpositive_J':np.mean(J[sel]<=0,axis=0).tolist()}
(O/'BASE.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep,indent=2))
for name,(a,b,c,e)in {'top':(640,205,860,300),'upper_left':(300,290,515,380),'lower_left':(300,960,515,1090),'left':(205,600,335,770)}.items():
    ims=[]
    for arr,label in [(old,'Old base'),(base,'Measured L / V104 colour'),(oldc,'Old composite'),(newc,'New base old filters')]:
        im=Image.fromarray(np.uint8(arr[b:e,a:c].clip(0,1)*255)).resize(((c-a)*3,(e-b)*3),Image.Resampling.NEAREST);can=Image.new('RGB',(im.width,im.height+28),'#222222');can.paste(im,(0,28));ImageDraw.Draw(can).text((6,8),label,fill='white');ims.append(can)
    full=Image.new('RGB',(sum(i.width for i in ims),ims[0].height));off=0
    for im in ims:full.paste(im,(off,0));off+=im.width
    full.save(O/f'base_{name}.png')
