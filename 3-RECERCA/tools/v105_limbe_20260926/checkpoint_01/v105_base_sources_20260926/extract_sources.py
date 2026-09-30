"""Read-only extraction from frozen per-frame intermediates; outputs only beside this script."""
from pathlib import Path
import json, hashlib, datetime
import numpy as np
from scipy.ndimage import gaussian_filter
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path('/Users/USUARI/Desktop/Eclipse 2026')
OUT = Path('/private/tmp/v105_base_sources_20260926')
LF = ROOT / '4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'
VAR = ROOT / '4-RESULTATS/v103_banda_20260926/E'
META = json.loads((LF / 'METADATA.json').read_text())
GEO = json.loads((VAR / 'lineal_v103_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']
SIL_PATH = ROOT / '4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'
SIL = np.load(SIL_PATH)
N = np.load(LF/'numerator.npy', mmap_mode='r')
W = np.load(LF/'weight.npy', mmap_mode='r')
D = np.load(LF/'distance_model.npy', mmap_mode='r')
Q = np.load(VAR/'lineal_v103_franja/A3C_franja_silueta.npz')
by0,by1,bx0,bx1 = META['box_y0y1x0x1']
h,w=by1-by0,bx1-bx0
yy,xx=np.mgrid[by0:by1,bx0:bx1]
d=np.hypot(xx-GEO['cx'],yy-GEO['cy'])-GEO['R']
theta=np.degrees(np.arctan2(-(yy-GEO['cy']),xx-GEO['cx']))%360
M=np.asarray(META['matrix'],np.float32)
gain=np.asarray(META['gain'],np.float32)

def sha(path):
    with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def savejson(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def dreal(j):
    # Literal distance conversion used by a3d; no new validity guard is imposed.
    dj=np.asarray(D[j],np.float64);gy,gx=np.gradient(dj)
    iy,ix=h//2,w-100
    cx=ix+bx0-(dj[iy,ix]+META['radius_model'])*gx[iy,ix]
    cy=iy+by0-(dj[iy,ix]+META['radius_model'])*gy[iy,ix]
    pa=np.degrees(np.arctan2(-(yy-cy),xx-cx))%360
    dr=dj+(META['radius_model']-GEO['R'])-np.interp(pa.ravel(),SIL['pa'],SIL['e'],period=360).reshape(h,w)
    return dr.astype(np.float32),[float(cx),float(cy)]
def stats(a,mask):
    z=np.asarray(a)[mask];z=z[np.isfinite(z)]
    return {'n':int(z.size),'p16_p50_p84':np.percentile(z,[16,50,84]).tolist() if z.size else None}
def normalized_gauss(x,valid,sigma):
    return gaussian_filter(np.where(valid,x,0),sigma)/np.maximum(gaussian_filter(valid.astype(float),sigma),1e-30)
def detail(g,valid):
    x=np.log(np.maximum(g,1e-30))
    return normalized_gauss(x,valid,2)-normalized_gauss(x,valid,8)

sources={}
rows=[]
for stem in ['572A2968','572A2969','572A2975','572A2993']:
    j=next(i for i,f in enumerate(META['frames']) if f['name']==stem+'.CR3')
    num=np.array(N[j]);weight=np.array(W[j]);valid_channel=(weight>0)&np.isfinite(num)&np.isfinite(weight)
    camera=np.full(num.shape,np.nan,np.float32)
    np.divide(num,weight,out=camera,where=valid_channel)
    valid=np.all(valid_channel,axis=-1)
    E=np.einsum('ij,hwj->hwi',M,camera*gain).astype(np.float32)
    E[~valid]=np.nan
    dr,center=dreal(j)
    row={**META['frames'][j],'array_index':j,'box_y0y1x0x1':META['box_y0y1x0x1'],
         'model_center_final_xy':center,'matrix':META['matrix'],'gain':META['gain'],
         'all_channels_observed_pixels':int(valid.sum()),'all_channels_positive_postmatrix_pixels':int((valid&np.all(E>0,axis=-1)).sum()),
         'saturation_map_available':False,'saturation_note':'Weight already combines saturation rolloff, low-signal floor and sensor validity; zero weight is not a unique saturation flag.',
         'no_extra_lunar_guard':True,'T_correction_applied':False,'extra_blur_applied':False,'demosaic_fill_applied':False}
    path=OUT/(stem+'.npz')
    assert not path.exists(),path
    np.savez_compressed(path,E=E,camera_rgb=camera,numerator=num,weight=weight,valid_channel=valid_channel,valid_rgb=valid,
                        dreal=dr,dmodel=np.asarray(D[j]),d_presentation_circle=d.astype(np.float32),box=np.asarray(META['box_y0y1x0x1']),metadata_json=np.asarray(json.dumps(row)))
    row['output']={'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size};rows.append(row)
    vg=valid&np.isfinite(E[...,1])&(E[...,1]>0)
    sources[stem]={'E':E,'valid':vg,'dreal':dr,'detail':detail(E[...,1],vg)}
    print('EXTRACTED',stem,flush=True)

eref=np.asarray(Q['E'],np.float32)
validE=np.asarray(Q['domini_E'],bool)&np.all(np.isfinite(eref),axis=-1)&np.all(eref>0,axis=-1)
sources['V104_E']={'E':eref,'valid':validE,'dreal':d.astype(np.float32),'detail':detail(eref[...,1],validE)}
np.savez_compressed(OUT/'V104_E_reference.npz',E=eref,valid_rgb=validE,domini_E=Q['domini_E'],box=Q['box'],
                    d_presentation_circle=d.astype(np.float32),F=Q['F'],G=Q['G'],beta=Q['beta'])

diagnostics={'scope':'No gain, tone, geometry or T fit applied. Ratios and fine structure comparisons only on common observed support.',
             'distance_bins_reference':'Distances to V104 presentation circle. Per-frame dreal > 10 px required for clean-support diagnostics only, never used to modify extracted source.',
             'detail_metric':'Difference of normalized Gaussian smoothings (sigma 2 and 8 px) of log postmatrix G; descriptive, not independent physical resolution validation.',
             'per_source_vs_V104_E':{},'pairwise':{}}
fig,axes=plt.subplots(3,1,figsize=(11,9),sharex=True)
rbins=[(10,20),(20,30),(30,40),(40,60),(60,80),(80,100)]
for name in ['572A2968','572A2969','572A2975','572A2993']:
    a=sources[name];common=a['valid']&validE&(a['dreal']>10)
    drs={}
    for lo,hi in rbins:
        mask=common&(d>=lo)&(d<hi)
        drs[f'{lo}..{hi}']={c:stats(np.log(np.maximum(a['E'][...,k],1e-30)/np.maximum(eref[...,k],1e-30)),mask&(a['E'][...,k]>0)) for k,c in enumerate('RGB')}
    diagnostics['per_source_vs_V104_E'][name]=drs
    for k,c in enumerate('RGB'):
        vals=[drs[f'{lo}..{hi}'][c]['p16_p50_p84'] for lo,hi in rbins]
        axes[k].plot([(lo+hi)/2 for lo,hi in rbins],[100*np.expm1(v[1]) if v else np.nan for v in vals],'-o',label=name)
        axes[k].set_ylabel(c+' ratio to E (%)');axes[k].grid(alpha=.2);axes[k].axhline(0,color='k',lw=.5)
for first,second in [('572A2975','572A2969'),('572A2975','572A2993'),('572A2975','572A2968')]:
    a,b=sources[first],sources[second];out={}
    for lo,hi in [(10,30),(30,60),(60,100)]:
        for sector,lth,hth in [('all',0,360),('top',60,120),('left',150,210),('bottom',240,300),('right',0,60)]:
            m=a['valid']&b['valid']&(a['dreal']>10)&(b['dreal']>10)&(d>=lo)&(d<hi)&(theta>=lth)&(theta<hth)
            x=a['detail'][m];y=b['detail'][m]
            out[f'{lo}..{hi}_{sector}']={'n':int(m.sum()),'correlation':float(np.corrcoef(x,y)[0,1]) if len(x)>20 else None,
                                       'std_logG_a_b':[float(np.std(x)),float(np.std(y))],
                                       'median_log_G_ratio':float(np.median(np.log(a['E'][...,1][m]/b['E'][...,1][m]))) if m.any() else None}
    diagnostics['pairwise'][first+'_vs_'+second]=out
axes[0].legend(ncol=4);axes[2].set_xlabel('Distance from presentation circle (px)')
fig.suptitle('Uncorrected calibrated individual frames vs V104 E; observed clean overlap only')
fig.tight_layout();fig.savefig(OUT/'profiles_vs_E.png',dpi=150);plt.close(fig)
savejson('DIAGNOSTICS.json',diagnostics)
manifest={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'originals_untouched':True,
          'sources':{'metadata':str(LF/'METADATA.json'),'metadata_sha256':sha(LF/'METADATA.json'),
                     'arrays_checksums_frozen_receipt':json.loads((LF/'COMPLETE.json').read_text()),
                     'note':'Large input arrays were mapped read-only; frozen checksums copied from producer receipt, not recomputed.',
                     'silueta':str(SIL_PATH),'silueta_sha256':sha(SIL_PATH),
                     'E_reference':str(VAR/'lineal_v103_franja/A3C_franja_silueta.npz')},
          'producer_audit':{'path':str(ROOT/'3-RECERCA/tools/v98_20260925/a9b_limb_frames_comuna.py'),
                            'no_lunar_mask_in_this_extractor':True,'no_Gaussian_blur_of_radiance_in_this_extractor':True,
                            'prior_operations':['per-Bayer-cell common saturation and floor weighting','dark/flat calibration','fixed k and offsets','fixed phi field','bilinear remapping of CFA planes into common final canvas'],
                            'caveat':'Valid RGB is computational channel support only, not physical corona validity; lunar signal remains present and must be classified with dreal.'},
          'frames':rows,'extraction_script_sha256':sha(Path(__file__))}
savejson('MANIFEST.json',manifest)
print('DONE',str(OUT),flush=True)
