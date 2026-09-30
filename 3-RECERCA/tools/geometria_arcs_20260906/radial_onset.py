"""Follow-up to Pere's inner-corona observation; descriptive, no artifact classifier."""
from geometry import *
from scipy.ndimage import distance_transform_cdt
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw

s=Samples(radial=(1.2*RS,4.5*RS),step=4,nsectors=24,margin_deg=2)
pad=20;x0=int(s.x.min())-pad;y0=int(s.y.min())-pad
x1=int(s.x.max())+pad+1;y1=int(s.y.max())+pad+1
sl=np.s_[y0:y1,x0:x1];x=s.x-x0;y=s.y-y0
support=np.load(ROOT/'research/tools/v29/cau_final/fusion_support.npy',mmap_mode='r')[sl]
dist=distance_transform_cdt(np.pad(support,1),metric='chessboard')[1:-1,1:-1]
valid=dist[y,x]>10
rad=np.hypot(s.x-CX,s.y-CY)/RS;theta=np.arctan2(s.y-CY,s.x-CX)
rows=[];edges=np.r_[1.2,np.arange(1.5,4.51,.25)]
fig,ax=plt.subplots(figsize=(10,5))
for tag in ['01','02']:
    source=ROOT/f'research/tools/v31/cau/{tag}_final_u16.npy'
    native=np.load(source,mmap_mode='r');a=np.asarray(native[sl],np.float32)/65535-.5
    b=gauss(a,3);z=b[y,x]
    xx=b[y,x+1]-2*z+b[y,x-1];yy=b[y+1,x]-2*z+b[y-1,x]
    xy=(b[y+1,x+1]-b[y+1,x-1]-b[y-1,x+1]+b[y-1,x-1])/4
    delta=np.hypot(xx-yy,2*xy);p=(xx+yy+delta)/2;q=(xx+yy-delta)/2
    angle=.5*np.arctan2(2*xy,xx-yy)+np.where(np.abs(q)>np.abs(p),np.pi/2,0)
    strong=np.maximum(abs(p),abs(q));weak=np.minimum(abs(p),abs(q))
    aniso=(strong-weak)/np.maximum(strong+weak,1e-30);weight=aniso**2
    align=np.cos(2*(angle-theta))
    np.savez(D/f'{tag}_radial_onset.npz',x=s.x,y=s.y,radius_R=rad,sector=s.sector,valid=valid,
        alignment=align,anisotropy=aniso,curvature=strong)
    localrows=[]
    for lo,hi in zip(edges[:-1],edges[1:]):
        band=valid&(rad>=lo)&(rad<hi);fold=[];sect=[]
        for parity in [0,1]:
            train=band&(s.sector%2==parity);thr=float(np.median(strong[train]))
            test=band&(s.sector%2!=parity)&(aniso>.6)&(strong>thr)
            score=float(np.average(align[test],weights=weight[test]))
            fold.append({'parity':parity,'score':score,'selected':int(test.sum()),'threshold':thr})
            for k in np.unique(s.sector[test]):
                good=test&(s.sector==k)
                sect.append({'sector':int(k),'score':float(np.average(align[good],weights=weight[good]))})
        row={'layer':tag,'r_min_R':float(lo),'r_max_R':float(hi),'folds':fold,'sectors':sect,
            'positive_sectors':sum(v['score']>0 for v in sect),
            'valid_pixels':int(band.sum()),'curvature_median':float(np.median(strong[band]))}
        localrows.append(row);rows.append(row)
    ax.plot([(r['r_min_R']+r['r_max_R'])/2 for r in localrows],
        [np.mean([f['score'] for f in r['folds']]) for r in localrows],'-o',label='Capa '+tag)
ax.axhline(0,color='black',lw=.7);ax.axvspan(2,2.65,color='orange',alpha=.16,label='Transició de pes Vixen/Sony al codi')
ax.set_xlabel('Distància al centre solar [radis solars]');ax.set_ylabel('Orientació: + tangencial / − radial')
ax.set_title('Descripció per radi; no identifica per si sola cercles ni artefactes');ax.legend()
fig.tight_layout();fig.savefig(RUN.vista('05_orientacio_per_radi.png'),dpi=150);plt.close(fig)
plate=Image.new('RGB',(1024,1152),(20,20,20));draw=ImageDraw.Draw(plate)
for i,(tag,side,th) in enumerate([('01','Nord',-np.pi/2),('01','Sud',np.pi/2),('02','Nord',-np.pi/2),('02','Sud',np.pi/2)]):
    a=np.load(ROOT/f'research/tools/v31/cau/{tag}_final_u16.npy',mmap_mode='r')
    for j,rr in enumerate([1.5,2.,2.5,3.5]):
        xx=int(round(CX+rr*RS*np.cos(th)));yy=int(round(CY+rr*RS*np.sin(th)))
        z=np.asarray(a[yy-128:yy+128,xx-128:xx+128],float)/65535
        im=Image.fromarray(np.uint8(np.clip((z-.3)/.4,0,1)*255)).convert('RGB')
        plate.paste(im,(256*j,288*i+32));draw.text((256*j+5,288*i+8),f'{tag} {side} | {rr:g} R centre | 1:1',fill='white')
plate.save(RUN.vista('06_finestres_per_radi.png'))
save('radial_onset',{'observation':'Pere: no gramophone rings until about one solar radius outside limb; interpretation r~2R from center',
    'scope':'Descriptive Hessian orientation at sigma3 on unchanged 01/02; fixed center; radial bins; no onset fit or artifact segmentation',
    'selection':'anisotropy>0.6; curvature>training median in each radial band; 24 sectors with 2deg margins; valid square support>10px',
    'limitation':'Band-specific curvature thresholds and true coronal structure affect scores; no statistical significance or exact onset radius claimed',
    'rows':rows})
for r in rows:print(r['layer'],r['r_min_R'],r['r_max_R'],[round(f['score'],4) for f in r['folds']],r['positive_sectors'],flush=True)
