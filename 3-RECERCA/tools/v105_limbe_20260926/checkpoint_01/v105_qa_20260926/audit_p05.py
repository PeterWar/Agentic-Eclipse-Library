"""Read-only P05 scalar/green separation and AdobeRGB base audit."""
from pathlib import Path
import json,sys,hashlib,struct
import numpy as np
R=Path('/Users/USUARI/Desktop/Eclipse 2026');P=Path('/private/tmp/v105_root_pilots_20260926');OUT=Path('/private/tmp/v105_qa_20260926')
sys.path.insert(0,str(R/'3-RECERCA/tools/v97_refundacio_20260924'))
from jutge_comu import Estat
q=dict(np.load(P/'P05/Q_OBSERVED.npz'));p3=np.load(P/'P03/Q_OBSERVED.npz');p4=np.load(P/'P04/Q_OBSERVED.npz')
old=np.load(R/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_franja_silueta.npz')
sc=json.loads((R/'4-RESULTATS/v103_banda_20260926/E/lineal_v103_franja/A3C_FRANJA_SILUETA.json').read_text())['escales']
b=np.load(P/'P05/BASE_ROI.npz');bcfg=json.loads(str(b['configuration_json']))
y0,y1,x0,x1=map(int,q['box']);yy,xx=np.mgrid[y0:y1,x0:x1];cx,cy,r=q['centre'];d=np.hypot(xx-cx,yy-cy)-r
theta=np.degrees(np.arctan2(-(yy-cy),xx-cx))%360
t=np.clip((d-12)/13,0,1);w=1-t*t*(3-2*t);wp=np.where((d>12)&(d<25),-6*t*(1-t)/13,0)
def st(a):
 a=np.asarray(a);a=a[np.isfinite(a)]
 return {'n':int(a.size),'p01_p16_p50_p84_p99':np.percentile(a,[1,16,50,84,99]).tolist()if a.size else None,'max_abs':float(abs(a).max())if a.size else None}
rep={'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in [P/'make_base_scalar_adobergb.py',P/'P05/BASE_ROI.npz',P/'P05/Q_OBSERVED.npz']},
 'P03_equal':{k:bool(np.array_equal(q[k],p3[k],equal_nan=True))for k in ['G','V','domini','E_observed','NF','DMIN','DREAL_MAX','NEFF','W','observed']},
 'P04_equal':{k:bool(np.array_equal(q[k],p4[k],equal_nan=True))for k in ['L_scalar','scalar_observed','scalar_valid']},
 'L_domain_exact_P04_domini':bool(np.array_equal(q['L_domain'],p4['domini'])),
 'green_join':{},'base':{'config':bcfg}}
for deg in range(0,360,30):
 sec=(theta>=deg)&(theta<deg+30);m=sec&(d>=12)&(d<25)&q['domini']
 row={}
 for k in ['G','V']:
  scale=sc['c_'+k][0];newg=q['E_observed'][...,1]*scale;oldg=old['E'][...,1]*scale
  row[k]={'new_vs_old_green_percent':st(100*(newg[m]/old[k][m]-1)),
    'blend_only_gradient_percent_per_px':st(100*wp[m]*(newg[m]-oldg[m])/q[k][m]),
    'oldscaled_vs_actual_legacy_within_join_percent':st(100*(oldg[m]/old[k][m]-1))}
 rep['green_join'][str(deg)]=row
rep['green_join_masks']={'unobserved12_25':int(((d>=12)&(d<25)&~q['observed']).sum()),
 'excluded12_25':int(((d>=12)&(d<25)&~q['domini']).sum()),
 'G_outside25_exact':bool(np.array_equal(q['G'][d>=25],old['G'][d>=25],equal_nan=True)),
 'V_outside25_exact':bool(np.array_equal(q['V'][d>=25],old['V'][d>=25],equal_nan=True))}
from scipy.ndimage import map_coordinates
pa=np.arange(0,360,.25);xy=np.array([cy-(r+25)*np.sin(np.deg2rad(pa))-y0,cx+(r+25)*np.cos(np.deg2rad(pa))-x0])
eg=old['E'][...,1]*sc['c_G'][0];og=old['G'];endpoint_scaled=map_coordinates(eg,xy,order=1);endpoint_old=map_coordinates(og,xy,order=1)
endpoint_delta=100*(endpoint_scaled/endpoint_old-1)
holes=(d>=24)&(d<25)&~q['domini']
rep['green_endpoint25']={'old_E_G_scaled_vs_legacy_G_percent':st(endpoint_delta),
 'rays_difference_over1pct':pa[abs(endpoint_delta)>1].tolist(),
 'hole_pixels24_25_global_x_y_d_theta_G_oldG':np.column_stack([xx[holes],yy[holes],d[holes],theta[holes],q['G'][holes],og[holes]]).tolist(),
 'oldscaled_differs_legacy_G_join12_25_count':int(((d>=12)&(d<25)&(abs(eg-og)>.01)).sum()),
 'oldscaled_differs_legacy_G_25_26_count':int(((d>=25)&(d<26)&(abs(eg-og)>.01)).sum()),
 'remedy':'Blend the actual legacy scalar G/V endpoint directly against scaled new observed green; scalar_old*(1-w)+scalar_new*w. Do not assume E_old_green*constant equals legacy scalar inside the join.'}
oldbase=Estat(R/'4-RESULTATS/v103_banda_20260926/E/estat_v103').rgb(3,(x0,y0,x1,y1));new16=b['base_rgb_u16'];new=new16.astype(float)/65535
alpha=np.load('/private/tmp/eclipse_v104_diagnosi_20260926/L258.npz')['c-1'][77:1477,77:1477]/65535
mask=b['replacement_weight']>0
icc=Path('/private/tmp/v105_base_sources_20260926/V104_embedded.icc').read_bytes();gammas={}
for j in range(struct.unpack_from('>I',icc,128)[0]):
 tag,off,ln=struct.unpack_from('>4sII',icc,132+12*j)
 if tag in [b'rTRC',b'gTRC',b'bTRC']:
  assert icc[off:off+4]==b'curv' and struct.unpack_from('>I',icc,off+8)[0]==1
  gammas[tag.decode()]=struct.unpack_from('>H',icc,off+12)[0]/256
rep['base']['ICC_gammas']=gammas;gamma=gammas['rTRC']
oldlin=oldbase.astype(float)**gamma;newlin=new**gamma
ch=lambda a:a/np.maximum(a.sum(-1,keepdims=True),1e-30)
delta_ch=ch(newlin)-ch(oldlin)
scale=np.sum(new*oldbase,axis=-1)/np.maximum(np.sum(oldbase**2,axis=-1),1e-30)
collinear_resid=(new-oldbase*scale[...,None])*65535
rep['base']['collinearity_quantization_residual_DN16']=st(collinear_resid[mask])
rep['base']['chromaticity_delta']=st(delta_ch[mask])
rep['base']['new_65535_counts']=[int(((new16[...,i]==65535)&(oldbase[...,i]<1)&mask).sum())for i in range(3)]
rep['base']['outside150_max_DN16']=int(abs(new16[d>=150].astype(int)-np.rint(oldbase[d>=150]*65535).astype(int)).max())
rep['base']['opaque_moon_max_DN16']=int(abs(new16[alpha>=.95].astype(int)-np.rint(oldbase[alpha>=.95]*65535).astype(int)).max())
rep['base']['replacement_without_scalar_support']=int((mask&~q['scalar_valid']).sum())
L=q['scalar_observed'];chrom=oldlin/np.maximum((oldlin[...,0]+2*oldlin[...,1]+oldlin[...,2])[...,None]/4,1e-30)
anchor=bcfg['anchor'];slope=bcfg['slope_log10'];Lref=bcfg['Lref'];knee=bcfg['shoulder_encoded_knee']**gamma;head=bcfg['shoulder_encoded_head']**gamma
def render(delta):
 tone=np.maximum(anchor+slope*np.log10(np.maximum(L*np.exp(delta),1e-20)/Lref),.001)
 rgb=tone[...,None]**gamma*chrom;mx=rgb.max(-1);u=np.maximum(mx-knee,0)
 comp=np.where(mx>knee,knee+(head-knee)*u/(head-knee+u),mx)
 return (rgb*(comp/np.maximum(mx,1e-20))[...,None])**(1/gamma),tone,mx,comp
out,tone,mx,compressed=render(0);J=(render(1e-4)[0]-render(-1e-4)[0])/2e-4
idealJ=slope/np.log(10)*chrom**(1/gamma)
rep['base']['bands']={}
for a,c in [(0,3),(3,10),(10,25),(25,50),(50,150)]:
 m=mask&(d>=a)&(d<c)
 rep['base']['bands'][f'{a}-{c}']={'shoulder_fraction':float(np.mean(mx[m]>knee)),
 'nonpositive_J':int((J[m]<=0).sum()),'J_per_lnL':{ch:st(J[...,i][m])for i,ch in enumerate('RGB')},
 'relative_J_after_shoulder':st((J/np.maximum(idealJ,1e-30))[m]),
 'shoulder_scalar_compression':st((compressed/np.maximum(mx,1e-30))[m])}
rep['limits']=['P05 retains old per-pixel chromaticity by design, not newly measured spectral color.',
 'A positive pointwise Jacobian does not prove useful spatial contrast after filters or native Photoshop adjustments.',
 'Shoulder compression depends on inherited chromaticity and can modulate rendered intensity; it must remain declared and its attenuation reported.',
 'G join smoothstep removes arithmetic jumps only if scaled old E green equals legacy G at the endpoint. Audit quantifies that discrepancy separately.',
 'Native clip, nonlocal adjustments and reopened pixel preservation are independent required checks, not completed by this input-array audit.']
(OUT/'P05_SCALAR_COLOR_AUDIT.json').write_text(json.dumps(rep,indent=2))
print(json.dumps({k:v for k,v in rep.items()if k not in ['green_join','base']},indent=2))
print(json.dumps({k:v for k,v in rep['base'].items()if k!='bands'},indent=2))
print('green180',json.dumps(rep['green_join']['180']))
print('base0_3',json.dumps(rep['base']['bands']['0-3']))
