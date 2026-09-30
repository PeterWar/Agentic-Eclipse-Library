"""Fixed independent-reference check of the two temporal inverse-core pilots.
Compare baseline/inverse on identical valid pixels of each reference. All nine
green marks and the last435..449 fringe remain separate. Fourier/rotated-null
statistics are exploratory; no parameter is chosen from these outcomes.
"""
from optics_common import *
from scipy.ndimage import map_coordinates,distance_transform_edt,label
from PIL import Image
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

raw={}
for key,epoch in [('early','vixen_2'),('late','vixen_5')]:
    z=np.load(OUT/f'B0_{epoch}_inverse.npz');raw[key+'_base']=z['baseline'];raw[key+'_inverse']=z['inverse']
raw['Sony']=np.load(SRC/'B2_sony_reference.npz')['reference']
lr=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];L=np.zeros((N,N));oy,ox=bb[1]-3077,bb[0]-4677;L[oy:oy+lr.shape[0],ox:ox+lr.shape[1]]=lr[...,:3].mean(-1);raw['LROC']=L
rr=np.arange(300.,454.,.5);nt=1440;th=np.arange(nt)*2*np.pi/nt;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)]
freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*rr[:,None]);valid={k:np.isfinite(a) for k,a in raw.items()};valid['LROC']&=raw['LROC']>0
pv={k:map_coordinates(v.astype(float),co,order=1,mode='constant',cval=0)>.999 for k,v in valid.items()}
mask=np.load(ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz')['green'];lab,nlab=label(mask);regions={}
for i in range(1,nlab+1):
    if (lab==i).sum()>=100:regions['green_'+str(i)]=map_coordinates((lab==i).astype(float),co,order=1,mode='constant',cval=0)>.999
for sector in range(12):regions['last_'+str(sector)]=(rr[:,None]>=435)&(rr[:,None]<449)&(np.arange(nt)[None,:]//120==sector)
def corr(a,b,w):
    a=a[w];b=b[w];a=a-a.mean();b=b-b.mean();return float(np.dot(a,b)/max(np.linalg.norm(a)*np.linalg.norm(b),1e-30))
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);xx=(x-CX)/500;yy=(y-CY)/500;results={};changes=[]
for mode in ['linear','asinh20']:
    pol={}
    for k,a in raw.items():
        ix=distance_transform_edt(~valid[k],return_distances=False,return_indices=True);g=a[tuple(ix)]
        if mode=='asinh20':g=np.arcsinh(g/20)
        m=valid[k]&(r<435);A=np.stack([np.ones(m.sum()),xx[m],yy[m]],1);f=np.linalg.lstsq(A,g[m],rcond=None)[0];pol[k]=map_coordinates(g-f[0]-f[1]*xx-f[2]*yy,co,order=3,mode='nearest')
    results[mode]={}
    for lo,hi in [(8,16),(16,24),(24,40),(40,64)]:
        h=(freq>=1/hi)&(freq<=1/lo);band={k:np.fft.irfft(np.fft.rfft(p,axis=1)*h,n=nt,axis=1) for k,p in pol.items()};rows=[]
        for key in ['early','late']:
            base=key+'_base';inv=key+'_inverse';support=pv[base]&pv[inv]&pv['Sony']&pv['LROC']
            for name,reg in regions.items():
                w=support&reg
                if w.sum()<100:continue
                pairs={}
                for a,b in [(base,'Sony'),(inv,'Sony'),(base,'LROC'),(inv,'LROC'),('Sony','LROC')]:
                    rho=corr(band[a],band[b],w);null=[corr(band[a],np.roll(band[b],120*j,axis=1),w) for j in range(1,12)];mx=max(map(abs,null));pairs[a+'_'+b]=dict(r=rho,null_max_abs=mx,pass_null=bool(rho>mx))
                triple={a:all(pairs[k]['pass_null'] for k in [a+'_Sony',a+'_LROC','Sony_LROC']) for a in [base,inv]}
                rows.append(dict(epoch=key,region=name,samples=int(w.sum()),pairs=pairs,triple=triple))
                if triple[base]!=triple[inv]:changes.append(dict(mode=mode,band=[lo,hi],epoch=key,region=name,change='gain' if triple[inv] else 'loss'))
        results[mode][f'{lo}_{hi}']=rows
save('B1_inverse_judge.json',dict(method=__doc__,results=results,changes=changes,limits=['Temporal captures and Sony supply no inverse pixels except inherited calibration parameters','No complete independent RAW injection or PSF identification','A smoother/darker limb alone is not evidence of lunar detail']))
print('CHANGES',changes,flush=True)
# Diagnostic radiance figures; no edited photographic product.
fig,axs=plt.subplots(2,2,figsize=(12,10),layout='constrained')
for ax,(key,title) in zip(axs.ravel(),[(k,k) for k in ['early_base','early_inverse','late_base','late_inverse']]):
    im=ax.imshow(np.arcsinh(raw[key]/20),origin='upper',cmap='gray',vmin=3.5,vmax=6.5);ax.set(title=title,xlim=(200,1200),ylim=(1200,200));ax.axis('off')
fig.savefig(OUT/'vistes/B1_inverse_sources.png',dpi=120)
fig,axs=plt.subplots(2,2,figsize=(12,8),layout='constrained')
for ax,angle in zip(axs.ravel(),[0,90,180,270]):
    rad=np.arange(410.,470.,.25);t=np.arange(-15.,16.,1.);theta=np.deg2rad(angle);co=[CY+rad[:,None]*np.sin(theta)+t*np.cos(theta),CX+rad[:,None]*np.cos(theta)-t*np.sin(theta)]
    for k in ['early_base','early_inverse','late_base','late_inverse']:ax.plot(rad,np.median(map_coordinates(raw[k],co,order=1),axis=1),label=k)
    ax.axhline(0,color='k',lw=.7);ax.set_yscale('symlog',linthresh=100);ax.set(title=f'{angle}°',xlabel='Radi lunar (px)',ylabel='Radiància G calibrada');ax.grid(alpha=.2);ax.legend(fontsize=7)
fig.savefig(OUT/'vistes/B1_inverse_profiles.png',dpi=140)
