"""Fixed-source photographic tone previews and numeric ablation summary.
These are source diagnostics, not a Photoshop composite or a delivery.
"""
from native_common import *
from scipy.ndimage import map_coordinates,gaussian_filter1d
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

z={v:np.load(OUT/f'B0_{v}_all.npz') for v in ['old','new']};tone=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F7_fonts.json').read_text())['tone']
def display(g):return tone['anchor']+tone['scale']*np.arcsinh((g-tone['mid'])/tone['soft'])
images={k:display(z[k]['candidate']) for k in z};out=OUT/'vistes';out.mkdir(exist_ok=True)
patches=[('Dalt',slice(205,350),slice(595,805)),('Dreta',slice(595,805),slice(1075,1220)),('Baix dreta',slice(935,1105),slice(935,1105))]
fig,axes=plt.subplots(3,3,figsize=(12,11))
for j,(label,ys,xs) in enumerate(patches):
    old,new=[images[k][ys,xs] for k in ['old','new']];lo,hi=np.percentile(np.r_[old.ravel(),new.ravel()],[2,98])
    for i,(name,v) in enumerate([('V48 font',old),('Graella verda conjunta',new)]):axes[j,i].imshow(v,cmap='gray',vmin=lo,vmax=hi,interpolation='nearest');axes[j,i].set_title(label+' · '+name,fontsize=10)
    d=new-old;lim=np.quantile(abs(d),.995);axes[j,2].imshow(d,cmap='RdBu_r',vmin=-lim,vmax=lim,interpolation='nearest');axes[j,2].set_title(f'Diferència ±{lim:.5f} (to de font)',fontsize=10)
    for a in axes[j]:a.axis('off')
fig.suptitle('Diagnòstic de font; mateixa corba tonal. Sense Camera Raw ni màscara.',fontsize=12);fig.tight_layout();fig.savefig(out/'B2_source_patches.png',dpi=180);plt.close(fig)
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');tangent=np.arange(-80.,80.);rad=np.arange(-14.,15.);rows=[]
raw={k:z[k]['candidate'] for k in z}
for stem in ['572A2976','572A2994']:
    a=np.load(OUT/f'A0_quincunx_{stem}.npz');raw[stem]=a['g']
valid={k:np.isfinite(g)&(g>0) for k,g in raw.items()}
for deg in range(0,360,15):
    th=np.deg2rad(deg);r=edge[deg*4];xx=CX+(r+rad[:,None])*np.cos(th)-tangent*np.sin(th);yy=CY+(r+rad[:,None])*np.sin(th)+tangent*np.cos(th);positions={};support={}
    for k,g in raw.items():
        p=map_coordinates(np.nan_to_num(g),[yy,xx],order=1,mode='nearest');ok=map_coordinates(valid[k].astype(float),[yy,xx],order=1,mode='constant',cval=0)>.999
        d=np.diff(np.log(np.maximum(p,1e-9)),axis=0);j=np.argmax(d,axis=0);cc=np.arange(len(tangent));a=d[np.maximum(j-1,0),cc];b=d[j,cc];c=d[np.minimum(j+1,len(d)-1),cc];sub=np.clip(.5*(a-c)/np.minimum(a-2*b+c,-1e-30),-.5,.5)
        positions[k]=rad[j]+.5+sub;support[k]=np.all(ok,axis=0)&(j>1)&(j<len(d)-2)&(b>.1)
    common=support['old']&support['new'];ref='572A2976' if (common&support['572A2976']).sum()>=100 else '572A2994';common&=support[ref];row=dict(angle=deg,reference=ref,n=int(common.sum()),metrics={})
    for k,p in positions.items():
        w=common&support[k];hp=p-gaussian_filter1d(p,5);row['metrics'][k]=dict(roughness_rms=float(np.std(hp[w])) if w.sum() else None,offset_vs_reference=float(np.median((p-positions[ref])[w])) if w.sum() else None)
    rows.append(row)
yy,xx=np.mgrid[:N,:N];r=np.hypot(xx-CX,yy-CY);change=[]
for lo,hi in [(0,350),(350,420),(420,435),(435,449),(449,454)]:
    w=(r>=lo)&(r<hi);d=z['new']['candidate'][w]-z['old']['candidate'][w];change.append(dict(radius=[lo,hi],pixels=int(w.sum()),median_delta_G=float(np.median(d)),rms_delta_G=float(np.sqrt(np.mean(d*d))),median_fractional_delta=float(np.median(d/z['old']['candidate'][w]))))
save('B2_source_review.json',dict(method=__doc__,tone=tone,radial_change=change,limb=rows,limits=['Apparent edge position is a resampled diagnostic, not terrain truth','Sharper edge and source differences do not prove new texture','No edited Photoshop or hand-painted mask']))
print(json.dumps(change),flush=True)
