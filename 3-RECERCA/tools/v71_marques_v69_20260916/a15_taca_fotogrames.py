"""A15: la taca ampla fotograma a fotograma (Vixen): rotació RAW↔capa lunar per correlació, profunditat i posició de la taca (coordenades lunars i de sensor)."""
import sys, json, numpy as np, time
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/02e7086d-a9f1-455c-bd2d-9633948752b7/scratchpad')
from compo import *
from scipy.ndimage import map_coordinates, gaussian_filter, binary_fill_holes, label, rotate, zoom
import rawpy
exec(open(SP+'/a10_lluna_raw.py').read().split('res=[]')[0].split('# 2) fotogrames RAW')[1])   # llegeix(), troba_lluna(), ROOT
# patró de referència: capa lunar (id 30) passa-alt σ40 dins r<0,9R, al marc del compost (centre físic 998.88,998.41; R 456)
rgb,a=carrega(30); L30=rgb.mean(-1); CXp,CYp=998.88,998.41; yy,xx=np.mgrid[0:2000,0:2000]; rp=np.hypot(xx-CXp,yy-CYp)
hp=lambda im,s: im-gaussian_filter(im,s)
REF=hp(gaussian_filter(L30,6),40); REF[rp>0.9*456]=0
S=460; ref=REF[int(CYp)-S:int(CYp)+S,int(CXp)-S:int(CXp)+S]; refm=rp[int(CYp)-S:int(CYp)+S,int(CXp)-S:int(CXp)+S]<0.88*456
def correla(disc,cx,cy,R,angles):
    # disc: imatge normalitzada (half); remostreja a l'escala del compost (R→456) i centra
    esc=456.0/R; sub=zoom(disc[int(cy-R*1.05):int(cy+R*1.05),int(cx-R*1.05):int(cx+R*1.05)],esc,order=1)
    c=np.array(sub.shape)/2; h=S; sub=sub[int(c[0]-h):int(c[0]+h),int(c[1]-h):int(c[1]+h)]
    if sub.shape!=(2*S,2*S): return None
    d=hp(gaussian_filter(sub,6),40); out=[]
    for ang in angles:
        dr=rotate(d,ang,reshape=False,order=1); k=refm&(np.hypot(*np.mgrid[-S:S,-S:S][::-1])<0.88*456)
        out.append(float(np.corrcoef(dr[k],ref[k])[0,1]))
    return np.array(out)
frames=sys.argv[1:]
res=[]
for f in frames:
    t=time.time(); img=llegeix(f); Lum=img.mean(-1); cx,cy,R,rms=troba_lluna(Lum)
    yy2,xx2=np.mgrid[0:Lum.shape[0],0:Lum.shape[1]]; rr=np.hypot(xx2-cx,yy2-cy)
    prof=np.array([np.median(Lum[(rr>=k)&(rr<k+3)]) for k in range(0,int(R*0.98),3)]); rad=np.interp(rr,np.arange(0,int(R*0.98),3)+1.5,prof)
    norm=np.where(rr<R*0.97,Lum/np.maximum(rad,1e-6),1.0)
    cc=correla(norm,cx,cy,R,np.arange(0,360,5)); 
    if cc is None: print(f,'fora del marc'); continue
    a0=np.arange(0,360,5)[cc.argmax()]; fine=np.arange(a0-6,a0+6.5,1); cf=correla(norm,cx,cy,R,fine); ang=float(fine[cf.argmax()]); cmax=float(cf.max())
    # posició de la taca al RAW: gira l'offset (−44,5, +234,5)·esc per l'angle trobat (el compost gira `ang` respecte del RAW → invertim)
    esc=R/456.0; th=np.deg2rad(-ang); ox,oy=-44.5*esc,234.5*esc; bx=cx+ox*np.cos(th)-oy*np.sin(th); by=cy+ox*np.sin(th)+oy*np.cos(th)
    dins=np.hypot(xx2-bx,yy2-by)<45*esc; rt=np.hypot(bx-cx,by-cy); azt=np.rad2deg(np.arctan2(-(by-cy),bx-cx))%360; az=np.rad2deg(np.arctan2(-(yy2-cy),xx2-cx))%360
    an=(np.abs(rr-rt)<45*esc)&(np.abs(((az-azt+180)%360)-180)>35)&(rr<R*0.93)
    ns=gaussian_filter(norm,12*esc); win=(np.hypot(xx2-bx,yy2-by)<90*esc)&(rr<R*0.9); iy,ix=np.unravel_index(np.argmin(np.where(win,ns,9)),ns.shape)
    d=dict(frame=f,R_half=round(float(R),2),centre_half=[round(float(cx),2),round(float(cy),2)],rot_deg=ang,corr=round(cmax,3),corr_0=round(float(cc[0]),3),
           taca_esperada_half=[round(float(bx),1),round(float(by),1)],profunditat_pct=round(100*(1-norm[dins].mean()),2),std_anell_pct=round(100*norm[an].std(),2),
           minim_local_half=[int(ix),int(iy)],minim_local_rel_lluna=[round(float((ix-cx)/esc),1),round(float((iy-cy)/esc),1)],minim_local_val_pct=round(100*(1-ns[iy,ix]),2),
           minim_local_sensor_full=[int(2*ix),int(2*iy)])
    res.append(d); print(json.dumps(d),flush=True)
    # vista del disc normalitzat girat al marc del compost, amb la taca esperada
    esc2=456.0/R; sub=zoom(norm[int(cy-R*1.05):int(cy+R*1.05),int(cx-R*1.05):int(cx+R*1.05)],esc2,order=1); sub=rotate(sub,ang,reshape=False,order=1)
    from PIL import Image, ImageDraw
    im=Image.fromarray(np.uint8(np.clip((gaussian_filter(sub,3)-0.94)/0.12,0,1)*255)).convert('RGB'); dr=ImageDraw.Draw(im); c=np.array(sub.shape)/2
    dr.ellipse([c[1]-44.5-45,c[0]+234.5-45,c[1]-44.5+45,c[0]+234.5+45],outline=(0,255,255),width=2); im.save(SP+f'/v_A15_{f[:-4]}_disc_compost.png')
json.dump(res,open(SP+'/a15_taca_fotogrames.json','w'),indent=1)
