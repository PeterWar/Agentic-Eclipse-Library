"""Read-only audit of modeled per-frame limb versus unchanged display alpha.
Output only to /private/tmp/v105_qa_20260926. No product masks are created.
"""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import map_coordinates

ROOT = Path('/Users/USUARI/Desktop/Eclipse 2026')
OUT = Path('/private/tmp/v105_qa_20260926')
SRC = Path('/private/tmp/v105_base_sources_20260926')
LF = ROOT/'4-RESULTATS/v98_20260925/cadena_raw/limb_frames_comuna'
meta = json.loads((LF/'METADATA.json').read_text())
geo = json.loads((ROOT/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A2_GEOMETRIA.json').read_text())['lluna_presentacio']
y0,y1,x0,x1 = meta['box_y0y1x0x1']
alpha0 = np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L258.npz')['c-1']
alpha = alpha0[y0-3000:y1-3000,x0-4600:x1-4600].astype(float)/65535
yy,xx = np.mgrid[y0:y1,x0:x1]
dist = np.hypot(xx-geo['cx'],yy-geo['cy'])-geo['R']
theta = np.degrees(np.arctan2(-(yy-geo['cy']),xx-geo['cx']))%360
outside_display = alpha <= .95
roi = outside_display & (dist >= -5) & (dist < 15)
ry,rx = np.nonzero(roi)
pa = theta[roi]; dd=dist[roi]; aa=alpha[roi]
sectors=[('top',60,120),('upper_left',120,150),('prominence',150,180),
         ('left',180,210),('lower_left',210,240),('lower_left_exception',240,270),
         ('bottom',270,300),('right',300,60)]
def sector(a,lo,hi):
    return ((a>=lo)&(a<hi)) if lo<hi else ((a>=lo)|(a<hi))
def stat(a):
    a=np.asarray(a); a=a[np.isfinite(a)]
    return {'n':int(a.size),'p05_p50_p95':np.percentile(a,[5,50,95]).tolist() if a.size else None}
sources={}
thresholds=[0,.6,1,2,3]
for stem in ('572A2968','572A2969','572A2975','572A2993'):
    z=np.load(SRC/(stem+'.npz'))
    e=z['E']; v=z['valid_rgb'].astype(bool)&np.isfinite(e).all(-1)
    pos=v & (e>0).all(-1)
    sources[stem]={'distance':z['dreal'][roi], 'valid':v[roi], 'positive':pos[roi],
                   'dreal_array':z['dreal'], 'metadata':json.loads(str(z['metadata_json']))}
eref=np.load(SRC/'V104_E_reference.npz')
evalid=eref['valid_rgb'].astype(bool)[roi]

# Independent per-frame geometric model audit across all 67 exposures, sparse ring.
# This does not infer unoccluded support from the presentation alpha or E domain.
D=np.load(LF/'distance_model.npy',mmap_mode='r')
W=np.load(LF/'weight.npy',mmap_mode='r')
N=np.load(LF/'numerator.npy',mmap_mode='r')
sil=np.load(ROOT/'4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz')
matrix=np.asarray(meta['matrix']); gain=np.asarray(meta['gain'])
rm=float(meta['radius_model']); delta_radius=rm-geo['R']
groups={'all67':lambda f:True,'up_to_2969':lambda f:f['time']<=22.270001,
        'anchor_pm4s':lambda f:abs(f['time']-geo['instant_s'])<=4,
        'first8_short':lambda f:f['name']<='572A2966.CR3'}
unions={g:{str(t):np.zeros(len(ry),bool) for t in thresholds} for g in groups}
maxdist=np.full(len(ry),-np.inf); bestframe=np.full(len(ry),-1,int)
per_frame=[]
for j,f in enumerate(meta['frames']):
    dm=D[j]; iy,ix=(y1-y0)//2,x1-x0-100
    gy=(float(dm[iy+1,ix])-float(dm[iy-1,ix]))/2
    gx=(float(dm[iy,ix+1])-float(dm[iy,ix-1]))/2
    cx=ix+x0-(float(dm[iy,ix])+rm)*gx
    cy=iy+y0-(float(dm[iy,ix])+rm)*gy
    angle=np.degrees(np.arctan2(-(yy[roi]-cy),xx[roi]-cx))%360
    dr=np.asarray(dm[ry,rx],float)+delta_radius-np.interp(angle,sil['pa'],sil['e'],period=360)
    w=np.asarray(W[j,ry,rx,:]); n=np.asarray(N[j,ry,rx,:])
    valid=(w>0).all(-1)&np.isfinite(n).all(-1)&np.isfinite(w).all(-1)
    rgb=np.full_like(n,np.nan,dtype=float)
    np.divide(n,w,out=rgb,where=w>0)
    e=np.einsum('ij,...j->...i',matrix,rgb*gain)
    valid &= np.isfinite(e).all(-1)&(e>0).all(-1)
    better=valid&(dr>maxdist);maxdist[better]=dr[better];bestframe[better]=j
    for group,selected in groups.items():
        if selected(f):
            for t in thresholds: unions[group][str(t)] |= valid&(dr>=t)
    per_frame.append({'name':f['name'],'time':f['time'],'exposure':f['exposure'],
                      'model_center_xy':[cx,cy], 'outside_display_roi_supported_dreal_ge0':int((valid&(dr>=0)).sum())})

report={'scope':'Unchanged display alpha is only a presentation exclusion. Physical classification uses per-frame distance_model + shared measured D21 silhouette, uncertain near the limb.',
 'limitations':['dreal is a fitted silhouette estimate, not external absolute truth; show 0 and +0.6 px guards separately.',
 'dreal >=0 only means nominally outside the geometric silhouette, not free of PSF/cromosphere.',
 'All67 coverage refers to the frozen weighted CFA extraction, not proof of absence in every original RAW.',
 'No solar transform from approximate user 303 is assumed or applied.',
 'E domain indicates accepted processing support, not independent evidence of physical coronal validity.'],
 'box_y0y1x0x1':meta['box_y0y1x0x1'],'display_alpha_layer':258,'excluded_alpha_gt':.95,
 'roi_presentation_distance_px':[-5,15],'presentation':geo,'alpha_range':[float(alpha.min()),float(alpha.max())],
 'thresholds_per_frame_dreal_px':thresholds,'per_frame':per_frame,'sectors':{},'edge_displacements':{}}
for name,lo,hi in sectors:
    sec=sector(pa,lo,hi); rows=[]
    for a,b in [(-5,0),(0,1),(1,2),(2,3),(3,5),(5,8),(8,10),(10,15)]:
        z=sec&(dd>=a)&(dd<b); count=int(z.sum())
        def frac(m):return float(m[z].mean()) if count else None
        row={'d_presentation_px':[a,b],'pixels':count,'display_alpha':stat(aa[z]),'E_domain_fraction':frac(evalid),'sources':{},'union':{}}
        for stem,s in sources.items():
            row['sources'][stem]={'dreal':stat(s['distance'][z]),'all_channels_positive_fraction':frac(s['positive']),
                'supported_fraction_at_dreal_ge':{str(t):frac(s['positive']&(s['distance']>=t)) for t in thresholds}}
        row['union']={g:{t:frac(m) for t,m in td.items()} for g,td in unions.items()}
        rows.append(row)
    # Quantify gaps that 2969/2968 can supply where 2975 is occulted at each guard.
    inner=sec&(dd<10)
    coverage={}
    for t in thresholds:
        v75=sources['572A2975']['positive']&(sources['572A2975']['distance']>=t)
        v69=sources['572A2969']['positive']&(sources['572A2969']['distance']>=t)
        v68=sources['572A2968']['positive']&(sources['572A2968']['distance']>=t)
        missing=inner&~v75
        coverage[str(t)]={'visible_inner_pixels':int(inner.sum()),'2975_missing':int(missing.sum()),
            '2969_supplies':int((missing&v69).sum()),'2968_additional':int((missing&~v69&v68).sum()),
            'remaining_after_2975_2969_2968':int((inner&~v75&~v69&~v68).sum()),
            'remaining_all67':int((inner&~unions['all67'][str(t)]).sum()),
            'remaining_anchor_pm4s':int((inner&~unions['anchor_pm4s'][str(t)]).sum())}
    exterior={}
    for al in [.5,.05,0.0]:
        vis=inner&(aa<=al)
        exterior[str(al)]={}
        for t in thresholds:
            v75=sources['572A2975']['positive']&(sources['572A2975']['distance']>=t)
            v69=sources['572A2969']['positive']&(sources['572A2969']['distance']>=t)
            v68=sources['572A2968']['positive']&(sources['572A2968']['distance']>=t)
            missing=vis&~v75; allmissing=vis&~unions['all67'][str(t)]
            witnesses=np.flatnonzero(allmissing)[:12]
            exterior[str(al)][str(t)]={'visible_pixels':int(vis.sum()),'2975_missing':int(missing.sum()),
                '2969_supplies':int((missing&v69).sum()),'2968_additional':int((missing&~v69&v68).sum()),
                'remaining_after_three':int((vis&~v75&~v69&~v68).sum()),
                'remaining_all67':int(allmissing.sum()),'remaining_all67_no_positive_rgb':int((allmissing&~np.isfinite(maxdist)).sum()),
                'remaining_all67_max_dreal':stat(maxdist[allmissing]),
                'remaining_all67_d_presentation':stat(dd[allmissing]),
                'remaining_all67_alpha':stat(aa[allmissing]),
                'example_missing_global_xy':np.column_stack([rx[witnesses]+x0,ry[witnesses]+y0]).tolist()}
    report['sectors'][name]={'bands':rows,'inner_10px_gap_accounting':coverage,'inner_10px_by_display_alpha_le':exterior}

# Radius where each source's fitted silhouette crosses zero versus display alpha.
angles=np.arange(0,360,.25); radii=np.arange(geo['R']-12,geo['R']+18,.025)
th=np.deg2rad(angles)[None,:]; rr=radii[:,None]
coords=np.array([geo['cy']-rr*np.sin(th)-y0,geo['cx']+rr*np.cos(th)-x0])
ap=map_coordinates(alpha,coords,order=1,mode='constant',cval=1,prefilter=False)
edge_alpha={str(t):radii[np.argmin(abs(ap-t),axis=0)] for t in (.95,.5,.05)}
edges={}
for stem,s in sources.items():
    drp=map_coordinates(s['dreal_array'],coords,order=1,mode='constant',cval=np.nan,prefilter=False)
    edges[stem]=radii[np.nanargmin(abs(drp),axis=0)]
for name,lo,hi in sectors:
    z=sector(angles,lo,hi)
    report['edge_displacements'][name]={stem:{f'frame_zero_minus_display_alpha_{t}_px':stat((edge-edge_alpha[t])[z]) for t in edge_alpha} for stem,edge in edges.items()}

(OUT/'physical_support_2975_2969.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
np.savez_compressed(OUT/'physical_support_sparse_diagnostic.npz',global_x=rx+x0,global_y=ry+y0,
    d_presentation=dd,display_alpha=aa,angle_deg=pa,max_supported_dreal_all67=maxdist,best_frame_index=bestframe,
    dreal_2975=sources['572A2975']['distance'],positive_rgb_2975=sources['572A2975']['positive'],
    dreal_2969=sources['572A2969']['distance'],positive_rgb_2969=sources['572A2969']['positive'],
    dreal_2968=sources['572A2968']['distance'],positive_rgb_2968=sources['572A2968']['positive'])
lines=['# Per-frame support versus unchanged V104 display alpha','',
       'A positive edge displacement means the source lunar edge lies OUTSIDE the given display-alpha contour, leaving a gap if that source alone is used.',
       'Numbers below use alpha=0.05 (95% transparent), then support dreal>=0 / >=0.6. They are model-based, not PSF-free corona certification.','',
       '| Sector | 2975 edge minus alpha0.05 p05/median/p95 px | 2969 edge minus alpha0.05 px | Visible inner pixels | Missing2975 / supplied2969 / residual all67 (d>=0) | Same d>=0.6 |',
       '|---|---|---|---:|---|---|']
for name,lo,hi in sectors:
    ed=report['edge_displacements'][name]
    def ps(stem):return '/'.join(f'{x:.2f}' for x in ed[stem]['frame_zero_minus_display_alpha_0.05_px']['p05_p50_p95'])
    g=report['sectors'][name]['inner_10px_gap_accounting']
    def fmt(t):
        v=g[str(t)];return f"{v['2975_missing']} / {v['2969_supplies']} / {v['remaining_all67']}"
    lines.append(f"| {name} | {ps('572A2975')} | {ps('572A2969')} | {g['0']['visible_inner_pixels']} | {fmt(0)} | {fmt(.6)} |")
lines+=['','ROI: presentation-circle distance [-5,10) and display alpha <=0.95. Thus gap counts include partially covered edge pixels; see JSON alpha statistics and radial bands for the fully exterior portion.',
        'The all67 result includes later frames and early short exposures, with their calibration limitations. A zero nominal geometric gap does not warrant deconvolution or a claim that the signal is pure corona.']
lines+=['','## Fully exterior alpha <=0.05, d_presentation [-5,10)', '',
        '| Sector | Pixels | Missing2975 / supplied2969 / remaining all67 at dreal>=0 | Same dreal>=0.6 |',
        '|---|---:|---|---|']
for name,lo,hi in sectors:
    g=report['sectors'][name]['inner_10px_by_display_alpha_le']['0.05']
    def fmt_ext(t):
        v=g[str(t)];return f"{v['2975_missing']} / {v['2969_supplies']} / {v['remaining_all67']}"
    lines.append(f"| {name} | {g['0']['visible_pixels']} | {fmt_ext(0)} | {fmt_ext(.6)} |")
(OUT/'physical_support_summary.md').write_text('\n'.join(lines)+'\n')
print('\n'.join(lines))
