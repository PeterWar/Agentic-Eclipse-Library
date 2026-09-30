"""Apply the fixed global monotone tone calibration to native CameraRaw output.
No spatially variable colour/tone correction, no marked masks. Curves frozen
from B1 (disjoint-sector validation), with physical endpoints 0 and 65535.
"""
from validation_common import *
from scipy.interpolate import PchipInterpolator
from PIL import Image
import sys
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from c5_fonts_psb import C,PSDImage
p=OUT/'E1_direct_camera_raw_candidate.psd';s=PSDImage.open(p);l=next(l for l in s if l.name=='V45 font G · dos trens · preferència temporal · vel present');a=np.stack([C.channel(l,c) for c in range(3)],-1).astype(float)
curves=json.loads((OUT/'B1_global_tone_diagnostic.json').read_text())['curves'];result=np.empty_like(a);baseline=np.empty_like(a);old_replay=np.load(OUT/'B0_replay_rgb.npy');target=np.load(PREV/'A0_live_layer21_rgb.npy');report=[]
for c,curve in enumerate(curves):
 x=np.array([0.]+curve['input_DN16']+[65535.]);y=np.array([0.]+curve['output_DN16']+[65535.]);assert np.all(np.diff(y)>=0)
 f=PchipInterpolator(x,y,extrapolate=False);result[...,c]=f(a[...,c]);baseline[...,c]=f(old_replay[...,c]);report.append(dict(channel=c,candidate_outside_training=int(((a[...,c]<x[1])|(a[...,c]>x[-2])).sum()),baseline_outside_training=int(((old_replay[...,c]<x[1])|(old_replay[...,c]>x[-2])).sum())))
new=np.rint(np.clip(result,0,65535)).astype(np.uint16);np.save(OUT/'E2_candidate_rgb.npy',new);np.save(OUT/'E2_baseline_calibrated_rgb.npy',np.rint(baseline).astype(np.uint16))
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);err=abs(baseline-target);diff=result-target
save('E2_render_calibrate.json',dict(method=__doc__,channel_domain=report,baseline_error_inner_quantiles=np.percentile(err[r<440],[50,95,99,100]).tolist(),baseline_error_all_quantiles=np.percentile(err,[50,95,99,100]).tolist(),candidate_minus_user_inner_quantiles=np.percentile(diff[r<430],[0,5,50,95,100]).tolist(),exact_historical_sliders=False,spatial_masks_used=False))
vis=OUT/'vistes';vis.mkdir(exist_ok=True)
Image.fromarray((new>>8).astype(np.uint8)).save(vis/'E2_candidate_lunar_layer.png')
print('CALIBRATED',json.loads((OUT/'E2_render_calibrate.json').read_text()),flush=True)
