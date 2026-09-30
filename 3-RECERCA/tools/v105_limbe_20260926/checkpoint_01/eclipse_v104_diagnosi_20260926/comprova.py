from pathlib import Path
import json,numpy as np,cv2
from scipy.ndimage import gaussian_filter1d
R=Path('/Users/USUARI/Desktop/Eclipse 2026');O=Path('/private/tmp/eclipse_v104_diagnosi_20260926');E=R/'4-RESULTATS/v103_banda_20260926/E/estat_v103'
meta=json.loads((E/'CAPES_V98.json').read_text())['capes'];idx={l['id']:l for l in json.loads((O/'index.json').read_text())};box=(4600,3000,6150,4550)
rep={}
for lid in (3,258,76,96,41,42,51,55,56):
    d=np.load(O/f'L{lid}.npz');m=meta[str(lid)];res={}
    for key in d.files:
        c=int(key[1:]);suffix='alfa' if c==-1 else 'mascara' if c==-2 else 'G' if m['canals']=='G' else 'RGB'
        a=np.load(E/f'L{lid}_{suffix}.npy',mmap_mode='r')
        if a.ndim==3:a=a[:,:,c]
        xa,ya,xb,yb=m['caixa_desada'];h,w=a.shape
        if c==-2 and a.shape==(7506,10551):xa,ya=0,0
        if c==-2 and a.shape==(7506,10552):xa,ya=0,0
        # saved arrays generally expanded to full canvas or layer bbox
        if a.shape[0]>=7506 and a.shape[1]>=10551:xa,ya=0,0
        aa=np.full(d[key].shape,idx[lid]['mask']['background']*257 if c==-2 else 0,np.uint16)
        x0,y0,x1,y1=box;xx0,yy0=max(xa,x0),max(ya,y0);xx1,yy1=min(xa+w,x1),min(ya+h,y1)
        if xx1>xx0 and yy1>yy0:aa[yy0-y0:yy1-y0,xx0-x0:xx1-x0]=a[yy0-ya:yy1-ya,xx0-xa:xx1-xa]
        dif=np.abs(d[key].astype(np.int32)-aa.astype(np.int32));res[key]={'max':int(dif.max()),'pct_gt2':round(float(np.mean(dif>2))*100,4)}
    rep[lid]=res
print(json.dumps(rep,indent=1));(O/'comparison_current_vs_delivery_state.json').write_text(json.dumps(rep,indent=1))
# Apparent edges: diagnostic only, not a new scientific alignment.
ref=np.load(O/'L303.npz')['c1'].astype(np.float32)/65535;a=np.load(O/'L258.npz')['c-1'].astype(np.float32)/65535
ang=np.arange(0,360,.25);rr=np.arange(430,480,.1);tt=np.deg2rad(ang)
px=(5375.786804312011+rr[:,None]*np.cos(tt)[None,:]-4600).astype(np.float32);py=(3775.9774911631-rr[:,None]*np.sin(tt)[None,:]-3000).astype(np.float32)
p=cv2.remap(ref,px,py,cv2.INTER_LINEAR);p=gaussian_filter1d(p,.7/.1,axis=0)
g=np.gradient(p,.1,axis=0);edge09=rr[np.argmax(g,axis=0)]
pa=cv2.remap(a,px,py,cv2.INTER_LINEAR);edge258=rr[np.argmin(np.abs(pa-.5),axis=0)]
for name,lo,hi in [('dalt',60,120),('dalt_esq',120,150),('esq',170,195),('baix_esq',210,240),('dreta',-15,15)]:
    z=(ang>=lo)&(ang<hi) if lo>=0 else ((ang>=345)|(ang<15));delta=edge258[z]-edge09[z]
    print(name,'edge09 R',np.median(edge09[z]),'alpha258 R',np.median(edge258[z]),'delta_alpha_minus09 p10/50/90',np.round(np.percentile(delta,[10,50,90]),2))
