"""Same24 sector check, original texture registration; late Vixen2994 is the independent temporal reference only where2976 lacks complete valid profiles. Selection by physical coverage only."""
"""Fixed C5 diagnostic on24 tangent sectors; observed short frames as controls.
An entire radial profile must be valid before finding its optical transition.
No maximum at a censored saturation boundary, no radius or image edits.
"""
from validation_common import *
from scipy.ndimage import map_coordinates,gaussian_filter1d
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
z=np.load(OUT/'C0_temporal_ensemble.npz');raw={'V45':np.load(CAU45/'vixen_reference.npy'),'sum67':z['base'],'C5':z['candidate']}
new=np.load(OUT/'full_epoch2_original_geometry/source_arrays.npz');raw['Vshort']=new['572A2976_g']
late=np.load(CAU45/'native_vixen_572A2994.npz');raw['Vlate']=late['g']
valid={k:np.isfinite(v)&(v>0) for k,v in raw.items()};valid['Vlate']&=late['q']>0;valid['Vshort']&=new['572A2976_q']>0
for key,stem in [('Searly','DSC06983'),('Slate','DSC06995')]:
    zz=np.load(CAU45/f'native_sony_{stem}.npz');raw[key]=zz['g'];valid[key]=np.isfinite(zz['g'])&(zz['g']>0)&(zz['q']>0)
edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
t=np.arange(-80.,80.);r=np.arange(-14.,15.);rows=[];curves={}
for angle in np.arange(0,360,15):
    th=np.deg2rad(angle);rr=float(edge[angle*4]);xx=CX+(rr+r[:,None])*np.cos(th)-t*np.sin(th);yy=CY+(rr+r[:,None])*np.sin(th)+t*np.cos(th)
    pos={};support={};drops={}
    for key,g in raw.items():
        p=map_coordinates(np.nan_to_num(g),[yy,xx],order=1,mode='nearest');safe=map_coordinates(valid[key].astype(float),[yy,xx],order=1,mode='constant',cval=0)>.999
        dg=np.diff(np.log(np.maximum(p,1e-9)),axis=0);j=np.argmax(dg,axis=0);c=np.arange(len(t));a=dg[np.maximum(j-1,0),c];b=dg[j,c];d=dg[np.minimum(j+1,len(dg)-1),c]
        sub=np.clip(.5*(a-d)/np.minimum(a-2*b+d,-1e-30),-.5,.5);p0=r[j]+.5+sub
        good=np.all(safe,axis=0)&(j>1)&(j<len(dg)-2)&(b>.1)
        pos[key]=p0;support[key]=good;drops[key]=1-np.exp(-b)
    summary={}
    # Pairwise Vixen reference comparison retains more sectors if Sony profile
    # has insufficient valid radial extent; report the distinction explicitly.
    fixed=support['V45']&support['sum67']&support['C5'];refkey='Vshort' if (fixed&support['Vshort']).sum()>=100 else 'Vlate';vm=fixed&support[refkey];common=vm&support['Searly']&support['Slate']
    for key,p0 in pos.items():
        m=common if key.startswith('S') else vm&support[key]
        hp=p0-gaussian_filter1d(p0,5);summary[key]=dict(n=int(m.sum()),roughness_rms=float(np.std(hp[m])) if m.sum() else None,offset_vs_Vshort_median=float(np.median((p0-pos[refkey])[m])) if m.sum() else None,max_fractional_drop_median=float(np.median(drops[key][m])) if m.sum() else None)
        curves[f'{angle}_{key}']=p0;curves[f'{angle}_{key}_valid']=support[key]
    rows.append(dict(angle=int(angle),reference_used=refkey,common_with_both_sony=int(common.sum()),vixen_common=int(vm.sum()),sources=summary))
save('C2_temporal_ensemble_limb.json',dict(method=__doc__,rows=rows,limits=['Tangent diagnostic resampling only; native PSF and unequal Sony resolution not removed','Roughness alone is not terrain truth or a scientific PASS','No full-canvas Photoshop change yet']))
np.savez_compressed(OUT/'C2_temporal_ensemble_limb_curves.npz',tangent=t,**curves)
(OUT/'vistes').mkdir(exist_ok=True)
fig,axs=plt.subplots(2,1,figsize=(12,7),layout='constrained')
for key in ['V45','sum67','C5','Vshort']:
    axs[0].plot([r['angle'] for r in rows],[r['sources'][key]['roughness_rms'] if r['vixen_common']>=100 else np.nan for r in rows],'.-',label=key)
    axs[1].plot([r['angle'] for r in rows],[r['sources'][key]['offset_vs_Vshort_median'] if r['vixen_common']>=100 else np.nan for r in rows],'.-',label=key)
axs[0].set(ylabel='Irregularitat (px)',title='Vora per sectors: només perfils complets vàlids');axs[0].legend();axs[1].set(xlabel='Angle,0°dreta;90°baix',ylabel='Posició respecte de presa curta (px)')
for ax in axs:ax.grid(alpha=.25)
fig.savefig(OUT/'vistes/C2_temporal_ensemble_limb.png',dpi=140)
print([(r['angle'],r['vixen_common'],round(r['sources']['C5']['roughness_rms'] or 0,3),round(r['sources']['V45']['roughness_rms'] or 0,3)) for r in rows],flush=True)
