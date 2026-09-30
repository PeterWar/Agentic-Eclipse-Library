"""Existing V54 limb diagnostics, unchanged definitions and native geometry."""
from common import *
from psb_support import *
from psd_tools import PSDImage
from scipy.ndimage import gaussian_filter1d,map_coordinates
from PIL import Image,ImageDraw
import ast
claim();assert sha(V54)==V54_SHA;s=PSDImage.open(V54);old=np.stack([channel(s[25],c) for c in range(3)],-1);assert np.array_equal(old,np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/D1_candidate_rgb.npy'))
new=np.load(OUT/'arrays/D10_candidate_rgb.npy');cb=recomposition(s,old);cn=recomposition(s,new)
native=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/E3_native_moon.npy');err=abs(cb.astype(int)-native.astype(int));assert err.max()<=3
np.save(OUT/'arrays/D12_baseline_composite.npy',cb);np.save(OUT/'arrays/D12_candidate_composite.npy',cn)
r,theta=geometry();edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');edge=gaussian_filter1d(edge,3,mode='wrap');er=np.interp(theta,np.linspace(0,2*np.pi,len(edge),endpoint=False),edge,period=2*np.pi);d=r-er;dd=np.arange(-299.,9.,2.);sectors=(theta*12/(2*np.pi)).astype(int)
path=ROOT/'research/tools/earthshine_v54_detail_20260913/c2_appearance_gates.py';tree=ast.parse(path.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='profiles');exec(compile(ast.Module(body=[fn],type_ignores=[]),str(path),'exec'))
pb,pn=profiles(old,cb),profiles(new,cn);stats=[]
for a,b in zip(pb['rows'],pn['rows']):
    p=np.array(b['lunar_profile'])-a['lunar_profile'];c=np.array(b['composite_profile'])-a['composite_profile'];stats.append(dict(sector=a['sector'],max_lunar_profile_delta_DN16=float(abs(p[dd<-2]).max()),max_limb_composite_delta_DN16=float(abs(c).max()),outside_ratio_delta=b['outside_ratio']-a['outside_ratio'],step_before=a['max_step_inside'],step_after=b['max_step_inside']))
save('D12_profiles.json',dict(baseline=pb,candidate=pn,delta=stats,baseline_native_max_error=int(err.max()),masks_geometry_exact=True,interpretation='Same detector as V54. Literal absolute monotonic/2percent handoff limits already failed accepted V53/V54; not redefined to force a pass. Report baseline/candidate/delta. No new claim of limb texture recovery.'))
for name,a in [('V54',cb),('pilot',cn)]:
    Image.fromarray((a>>8).astype('uint8')).save(OUT/f'vistes/D12_{name}_composite.png');Image.fromarray(np.clip(a.astype(float)*2/256,0,255).astype('uint8')).save(OUT/f'vistes/D12_{name}_composite_x2.png')
panel=Image.new('RGB',(2800,1450),'#182124');panel.paste(Image.open(OUT/'vistes/D12_V54_composite_x2.png'),(0,50));panel.paste(Image.open(OUT/'vistes/D12_pilot_composite_x2.png'),(1400,50));dr=ImageDraw.Draw(panel);dr.text((25,18),'V54 | mateixa llum x2',fill='white');dr.text((1425,18),'Pilot FPN | mateixa llum x2',fill='white');panel.save(OUT/'vistes/D12_comparison_composite_1a1.png')
# Full original canvas, substituting only the mathematically recomposed lunar ROI.
raw=s._record.image_data.get_data(s._record.header);full=np.stack([np.frombuffer(raw[c],dtype='>u2').reshape(7506,10551) for c in range(3)],-1).copy();full[Y0:Y0+N,X0:X0+N]=cn
Image.fromarray((full[::4,::4]>>8).astype('uint8')).save(OUT/'vistes/D12_pilot_full.png')
print('PROFILES arcs',pb['arc_rms_DN16'],pn['arc_rms_DN16'],'max_limb_delta',max(q['max_limb_composite_delta_DN16'] for q in stats),'max_lunar_profile',max(q['max_lunar_profile_delta_DN16'] for q in stats),flush=True)
