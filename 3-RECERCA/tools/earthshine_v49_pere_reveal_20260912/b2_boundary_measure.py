"""Measure causal influence of invisible input pixels; never publish the probe."""
from reveal_common import *
from psd_tools import PSDImage
from scipy.interpolate import PchipInterpolator
from PIL import Image
import gc
BASE=ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta'
name='V45 font G · dos trens · preferència temporal · vel present'
def source_pixels(path):
    s=PSDImage.open(path);l=next(l for l in s if l.name==name);a=np.stack([channel(l,c) for c in range(3)],-1);del s;gc.collect();return a
ref=source_pixels(BASE/'C1_camera_raw.psd');base=source_pixels(OUT/'B1_baseline_camera_raw.psd');aux=source_pixels(OUT/'B1_auxiliary_camera_raw.psd');err=int(np.max(abs(base.astype(int)-ref.astype(int))));np.save(OUT/'B2_baseline_CR_RGB16.npy',base);np.save(OUT/'B2_auxiliary_CR_RGB16.npy',aux)
curves=json.loads((ROOT/'output/earthshine_validation_20260911/B1_global_tone_diagnostic.json').read_text())['curves'];mapped=[]
for a in [base,aux]:
    rgb=np.empty_like(a,dtype=float)
    for c,curve in enumerate(curves):
        f=PchipInterpolator([0.]+curve['input_DN16']+[65535.],[0.]+curve['output_DN16']+[65535.],extrapolate=False);rgb[...,c]=f(a[...,c])
    mapped.append(rgb)
delta=mapped[1].mean(-1)-mapped[0].mean(-1);np.save(OUT/'B2_historical_display_delta_DN16.npy',delta)
before=np.load(OUT/'A0_previous_moon_RGB16.npy').astype(float);mask=np.load(OUT/'A0_inherited_mask_roi.npy').astype(float)/65535
probe=before+delta[...,None];inrange=bool(probe.min()>=0 and probe.max()<=65535)
np.save(OUT/'B2_probe_previous_style_RGB16.npy',np.rint(np.clip(probe,0,65535)).astype('uint16'))
Image.fromarray((np.rint(np.clip(probe,0,65535)).astype('uint16')>>8).astype('uint8')).save(OUT/'B2_probe_source_previous_style.png')
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);ang=np.arctan2(y-CY,x-CX)%(2*np.pi);edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');d=r-np.interp(ang,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi);rows=[]
for label,use in [('face_r350',r<350),('inner_30_80',(d>=-80)&(d<-30)),('limb_6_25',(d>=-25)&(d<-6)),('last_3_inside',(d>=-3)&(d<0)),('outside_0_3',(d>=0)&(d<3))]:
    rows.append(dict(region=label,median_delta_DN16=float(np.median(delta[use])),percentiles_delta_DN16=np.percentile(delta[use],[0,1,50,99,100]).tolist(),median_relative_to_old_source=float(np.median(delta[use]/np.maximum(before.mean(-1)[use],1))),visible_weighted_delta_percentiles=np.percentile((delta*mask)[use],[1,50,99]).tolist()))
save('B2_boundary_result.json',dict(method=__doc__,historical_replay_max_DN16=err,historical_replay_qualified=err<=4,visible_input_pixels_changed=0,probe_in_range=inrange,regions=rows,maximum_visible_output_change_DN16=float(np.max(abs(delta*mask))),scope='Changes are measured after the historical CR and existing global tone curve, before the newer user reveal. Not proof of improved limb, recovered texture or preservation under newest CR.',publication='NONE; nearest continuation is an auxiliary perturbation only. Original source, mask and saved V49 untouched.'))
print('REPLAY ERROR',err,'RANGE',inrange,flush=True);print(rows,flush=True)
