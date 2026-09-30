import numpy as np, json
from scipy import ndimage as ndi
from PIL import Image, ImageDraw
import fa_lib as F
C=np.load(F.S4+'/roi74p_C_sensemarques.npy'); L=F.Lstar(C)
Cps=np.load(F.S4+'/roi74p_compost.npz')['C'][...,:3].astype(np.float32)/65535
med=ndi.median_filter(L,21); d=L-med
band=(F.RR>=457)&(F.RR<=486)
out={}
for k in F.MARKS:
    m=F.mask(k); az=F.AZ[m]; a0,a1=az.min()-8,az.max()+8
    sel=band&(F.AZ>=a0)&(F.AZ<=a1)
    vals=d[sel]
    out[k]=dict(sector=[float(a0),float(a1)],n=int(sel.sum()),p0_1=float(np.percentile(vals,0.1)),p1=float(np.percentile(vals,1)),min=float(vals.min()),
                n_lt_m5=int((vals<-5).sum()),n_lt_m8=int((vals<-8).sum()),n_lt_m12=int((vals<-12).sum()),
                marca_min=float(d[m].min()),marca_n_lt_m5=int((d[m]<-5).sum()))
    # on són els < −8 ?
    ys,xs=np.nonzero(sel&(d<-8)); out[k]['pos_lt_m8']=[dict(y=int(y),x=int(x),r=float(F.RR[y,x]),az=float(F.AZ[y,x]),dL=float(d[y,x]),L=float(L[y,x])) for y,x in list(zip(ys,xs))[:40]]
    print(k,{a:b for a,b in out[k].items() if a!='pos_lt_m8'})
    for p in out[k]['pos_lt_m8'][:12]: print('    ',p)
json.dump(out,open(F.S4+'/fa_c_negres.json','w'),indent=1)
# vistes 1:1 i 3:1 del compost PS (amb traços de Pere) per a m2+m3, m4+m5, m7
grups={'m2m3':(F.mask('m2')|F.mask('m3')),'m4m5':(F.mask('m4')|F.mask('m5')),'m7':F.mask('m7')}
for g,mm in grups.items():
    y0,y1,x0,x1=F.bbox(mm,pad=70)
    for Z in (1,3):
        im=Image.fromarray((np.clip(Cps[y0:y1,x0:x1],0,1)*255).astype(np.uint8)).resize(((x1-x0)*Z,(y1-y0)*Z),Image.NEAREST)
        im.save(F.S4+f'/v_fa_ps_{g}_x{Z}.png'); print(g,Z,im.size)
