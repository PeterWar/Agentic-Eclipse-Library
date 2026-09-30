"""Same V53 comparison after frozen-response source transport.
Extract the exact existing diagnostic function with AST: no campaign top-level
code or native CR action is run. This guarantees the same detector definition.
"""
from common import *
from psd_tools import PSDImage
from scipy.ndimage import gaussian_filter1d,map_coordinates
from PIL import Image,ImageDraw
import ast
claim();r,theta,d=geometry();dd=np.arange(-299.,9.,2.);sectors=(theta*12/(2*np.pi)).astype(int)
src=ast.parse((HERE/'c2_appearance_gates.py').read_text());fn=next(x for x in src.body if isinstance(x,ast.FunctionDef) and x.name=='profiles')
exec(compile(ast.Module(body=[fn],type_ignores=[]),str(HERE/'c2_appearance_gates.py'),'exec'))
old=np.load(OUT/'arrays/V53_moon_rgb.npy').astype('int32');new=np.load(OUT/'arrays/D1_candidate_rgb.npy').astype('int32');delta=new-old
cb=np.load(OUT/'arrays/C2_baseline_composite.npy');a=np.load(OUT/'arrays/V53_lunar_alpha.npy').astype(float)/65535*np.load(OUT/'arrays/V53_lunar_mask.npy')/65535.
# Lunar layer is last visible Normal; full ROI is opaque. Exact replacement
# delta on premultiplied cached mathematical baseline, quantisation <=1DN16.
cn=np.rint(cb.astype(float)+a[...,None]*delta).astype('uint16')
np.save(OUT/'arrays/D2_candidate_composite.npy',cn)
pb=profiles(old,cb);pn=profiles(new,cn)
stats=[]
for b,n in zip(pb['rows'],pn['rows']):
    pp=np.array(n['lunar_profile'])-np.array(b['lunar_profile']);cp=np.array(n['composite_profile'])-np.array(b['composite_profile'])
    stats.append(dict(sector=n['sector'],max_profile_delta_DN16=float(abs(pp[dd<-2]).max()),max_limb_composite_delta_DN16=float(abs(cp).max()),outside_ratio_delta=n['outside_ratio']-b['outside_ratio']))
save('D2_profiles.json',dict(baseline=pb,candidate=pn,delta=stats,
    literal_handoff_gate=dict(lunar_2pct_baseline=all(q['max_step_inside']<=.02 for q in pb['rows']),lunar_2pct_candidate=all(q['max_step_inside']<=.02 for q in pn['rows']),monotonic_baseline=all(q['monotonic'] for q in pb['rows']),monotonic_candidate=all(q['monotonic'] for q in pn['rows']),ratio90pct_baseline=all(q['outside_ratio']>=.9 for q in pb['rows']),ratio90pct_candidate=all(q['outside_ratio']>=.9 for q in pn['rows'])),
    interpretation='Literal detectors in the handoff do not pass the accepted V53 itself: ordinary lunar detail exceeds2pct bin steps and d0 lies inside the inherited alpha transition, so minimum d0..8 is below90pct. No threshold, radius, alpha or baseline was changed to force a PASS; report absolute values and candidate-minus-V53. This delivery preserves accepted limb appearance, does not claim to solve those inconsistent absolute criteria.',
    inherited_masks_exact=True,new_mask=False,new_chroma=False,hidden_pixels_unchanged=bool(np.array_equal(old[a==0],new[a==0]))))
for name,img in [('V53',cb),('V54',cn)]:
    Image.fromarray((img>>8).astype('uint8')).save(OUT/f'vistes/D2_{name}_moon.png')
    Image.fromarray(np.clip(img.astype(float)*2/256,0,255).astype('uint8')).save(OUT/f'vistes/D2_{name}_moon_x2.png')
# Native-size side-by-side comparison, presentation-only scale identical.
panel=Image.new('RGB',(2800,1450),'#182124');panel.paste(Image.open(OUT/'vistes/D2_V53_moon_x2.png'),(0,50));panel.paste(Image.open(OUT/'vistes/D2_V54_moon_x2.png'),(1400,50));draw=ImageDraw.Draw(panel);draw.text((30,18),'V53 | mateixa llum x2',fill='white');draw.text((1430,18),'V54 | mateixa llum x2',fill='white');panel.save(OUT/'vistes/D2_comparacio_1a1.png')
print('D2 profiles arcs',pb['arc_rms_DN16'],pn['arc_rms_DN16'],'limbmax',max(x['max_limb_composite_delta_DN16'] for x in stats),flush=True)
