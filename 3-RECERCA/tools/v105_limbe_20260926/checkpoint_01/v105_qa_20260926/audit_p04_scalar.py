"""Read-only independent audit. Outputs only to this QA scratch directory."""
from pathlib import Path
import json
import numpy as np
from scipy.ndimage import binary_erosion, map_coordinates

ROOT = Path('/Users/USUARI/Desktop/Eclipse 2026')
PILOT = Path('/private/tmp/v105_root_pilots_20260926')
OUT = Path('/private/tmp/v105_qa_20260926')
q = dict(np.load(PILOT/'P04/Q_OBSERVED.npz'))
p3 = np.load(PILOT/'P03/Q_OBSERVED.npz')
old = np.load(ROOT/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_franja_silueta.npz')
cfg = json.loads((PILOT/'P04/SCALAR.json').read_text())
meta = json.loads(Path('/private/tmp/v105_raw_pilot_20260926/no_floor_all67/METADATA.json').read_text())
y0,y1,x0,x1 = map(int,q['box']); yy,xx = np.mgrid[y0:y1,x0:x1]
cx,cy,r = q['centre']; d = np.hypot(xx-cx,yy-cy)-r
th = np.degrees(np.arctan2(-(yy-cy),xx-cx))%360
alpha = np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L258.npz')['c-1'][y0-3000:y1-3000,x0-4600:x1-4600].astype(float)/65535
E = q['E_observed']; L = (E[...,0]+2*E[...,1]+E[...,2])/4
good = q['observed']&np.isfinite(L)&(L>0)
t = np.clip((d-12)/13,0,1); w = (1-t*t*(3-2*t))*good
oldL = (old['F'][...,0]+2*old['F'][...,1]+old['F'][...,2])/4
targets = {'G':old['G'],'V':old['V'],'L_scalar':oldL}

def stat(x):
    x=np.asarray(x); x=x[np.isfinite(x)]
    return {'n':int(x.size),'p01_p16_p50_p84_p99':np.percentile(x,[1,16,50,84,99]).tolist() if x.size else None}

report = {'scope':'Independent read-only audit of scalar source selection, arithmetic, domain and join. Physical distance remains the frozen fitted silhouette, not external physical truth.',
 'coordinates':{'box_y0y1x0x1':q['box'].tolist(),'centre_x_y_r':q['centre'].tolist(),
 'cache_box_equal':bool(np.array_equal(q['box'],meta['box_y0y1x0x1'])),
 'old_box_equal':bool(np.array_equal(q['box'],old['box'])),
 'old_centre_equal':bool(np.array_equal(q['centre'],old['centre'])),
 'no_extra_registration_in_scalar_stage':True},
 'arithmetic':{},'support':{},'join_sectors':{},'radial_cuts':{}}
unchanged=['E_observed','observed','NF','DMIN','DREAL_MAX','NEFF','short_fraction','W','physical_ramp','domini_E']
report['P03_equal']={k:bool(np.array_equal(q[k],p3[k],equal_nan=True))for k in unchanged}
report['F_legacy_exact']=bool(np.array_equal(q['F'],old['F'],equal_nan=True))
report['scalar_observed_exact']=bool(np.array_equal(q['scalar_observed'],L,equal_nan=True))
report['scalar_valid_exact']=bool(np.array_equal(q['scalar_valid'],good))
domain_expected=np.where(d<25,q['domini_E']&good,old['domini'])
report['domain_exact']=bool(np.array_equal(q['domini'],domain_expected))
for k,a in targets.items():
    g=cfg['unit_scales'][k]
    expected=np.where(w>0,a*(1-w)+L*g*w,a).astype(np.float32)
    # Analytic contribution caused by changing blend weight, independently of gradients in either image.
    wp=np.where((d>12)&(d<25),-6*t*(1-t)/13,0)*good
    mix_slope=wp*(g*L-a)
    report['arithmetic'][k]={'formula_exact':bool(np.array_equal(q[k],expected,equal_nan=True)),
      'outside25_exact':bool(np.array_equal(q[k][d>=25],a[d>=25],equal_nan=True)),
      'inner12_vs_observed_scaled_max_abs':float(np.max(np.abs(q[k][good&(d<=12)]-(g*L)[good&(d<=12)]))),
      'nonfinite_inside_domain':int((~np.isfinite(q[k])&q['domini']).sum()),
      'nonpositive_inside_domain':int(((q[k]<=0)&q['domini']).sum()),
      'transition_blend_slope_percent_per_px':stat(100*mix_slope[q['domini']&(d>=12)&(d<25)]/q[k][q['domini']&(d>=12)&(d<25)])}
for lo in range(0,360,30):
    sec=(th>=lo)&(th<lo+30)
    rows={}
    for a,b in [(0,2),(2,5),(5,10),(10,12),(12,15),(15,20),(20,25),(25,30),(30,100)]:
        m=sec&(d>=a)&(d<b)&(alpha<=.05)
        n=int(m.sum()); dom=m&q['domini']; obs=m&q['observed']
        rows[f'{a}-{b}']={'n_exterior_alpha005':n,
          'observed':int(obs.sum()),'filter_domain':int(dom.sum()),
          'filter_domain_unobserved':int((dom&~good).sum()),
          'dreal_max_observed':stat(q['DREAL_MAX'][obs]),
          'NF_observed':stat(q['NF'][obs]),'NEFF_observed':stat(q['NEFF'][obs]),
          'nonpositive_L_observed':int((obs&(L<=0)).sum())}
    report['support'][str(lo)]=rows
    m=sec&q['domini']&(d>=12)&(d<25)
    report['join_sectors'][str(lo)]={}
    for k,a in targets.items():
        g=cfg['unit_scales'][k]; vals=q[k]
        wp=np.where((d>12)&(d<25),-6*t*(1-t)/13,0)*good
        report['join_sectors'][str(lo)][k]={
         'source_difference_percent':stat(100*(g*L[m]/a[m]-1)),
         'blend_only_gradient_percent_per_px':stat(100*wp[m]*(g*L[m]-a[m])/vals[m])}

ring=(d>=10)&(d<27)
report['support_summary']={
 'join10_27_unobserved':int((ring&~good).sum()),
 'join10_27_filter_excluded':int((ring&~q['domini']).sum()),
 'new_domain':int((q['domini']&~old['domini']).sum()),
 'lost_domain':int((~q['domini']&old['domini']).sum()),
 'observed_without_nominal_guard06':int((q['observed']&(q['DREAL_MAX']<=.6)).sum()),
 'observed_without_any_weight_channel':int((q['observed']&~np.all(q['W']>0,axis=-1)).sum()),
 'inner25_domain_NF_lt3':int((q['domini']&(d<25)&(q['NF']<3)).sum()),
 'inner25_domain_nonpositive_L':int((q['domini']&(d<25)&(L<=0)).sum())}
# Sample identical solar-coordinate rays without refitting or radial profile subtraction.
rad=np.arange(9.,28.0001,.125)
for deg in [60,75,90,105,120,135,150,165,180,195,210,225,240,255,270,300,330]:
    xy=np.array([cy-(r+rad)*np.sin(np.deg2rad(deg))-y0,cx+(r+rad)*np.cos(np.deg2rad(deg))-x0])
    def sample(a):return map_coordinates(a,xy,order=1,mode='constant',cval=np.nan,prefilter=False)
    report['radial_cuts'][str(deg)]={'d':rad.tolist(),'domain':sample(q['domini'].astype(float)).tolist(),
      **{k:{'old':sample(a).tolist(),'new':sample(q[k]).tolist(),'observed_scaled':sample(L*cfg['unit_scales'][k]).tolist()}for k,a in targets.items()}}
report['interpretation']=[
 'G and V in P04 are declared intensity surrogates derived from L, not measured green-channel replacements.',
 'L_scalar is the explicit input for scalar detail; F remains legacy RGB. A downstream consumer silently recomputing L from F bypasses this change.',
 'The smoothstep join is mathematically C1 where support is uninterrupted; this does not guarantee visually negligible curvature or filter response.',
 'E_observed is a weighted multi-epoch solar-registered observation selected outside each modeled Moon; it is not one photographic epoch and not deconvolved or free from PSF.',
 'Heldout constants compare strongly dependent products sharing source data. Their small differences validate unit continuity, not independent absolute radiometry.',
 'A base preserving V104 chroma is a declared presentation transform; it must not be labeled recovered physical color.'
]
(OUT/'P04_SCALAR_AUDIT.json').write_text(json.dumps(report,indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ['support','join_sectors','radial_cuts','interpretation']},indent=2))
