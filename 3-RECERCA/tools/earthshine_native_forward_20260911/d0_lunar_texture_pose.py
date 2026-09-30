"""Cross-sensor lunar texture registration diagnostic, independent of bright rim.
Full-field linear radiance DoG6-24; target-only aperture r<0.70R.
Three distinct Sony A exposures, angular halves and imposed-shift control.
"""
from native_forward_common import *
from scipy.ndimage import gaussian_filter,distance_transform_edt,shift
from scipy.signal import fftconvolve
import time
stems=[f'572A{n}' for n in [2968,2969,2970,2973,2974,2975,2976,2977,2978,2983,2991,2992,2993,2994,2995,2996]]
refs=['DSC06987','DSC06984','DSC06985'];size=768;lo=316;rg=5;yy,xx=np.mgrid[lo:lo+size,lo:lo+size];R=np.hypot(xx-CX,yy-CY);phi=np.arctan2(yy-CY,xx-CX);mask=R<.7*455.5018;sector=(np.floor((phi%(2*np.pi))/(np.pi/4)).astype(int)%2)==0
save('D0_texture_plan.json',dict(method=__doc__,vixen_stems=stems,sony_references=refs,filter_sigma=[6,24],aperture_radius=.7*455.5018,search_radius=rg,sign='NCC reports correction to apply to moving Vixen field to align with target Sony',qualification='Diagnostic only: correlations>=0.10 in all three refs, no search boundary, relative reference disagreement<=0.30px, angular half gap<=0.50px, imposed-shift equivariance<=0.10px. Absolute Sony reference bias removed using existing Vixen2983 anchor.',limits=['Three Sony exposures share sensor/calibration; are not three independent telescopes','Linear high-pass texture supports registration only, not new lunar detail','No source shift applied; same historical lunar/coronal calibration inherited']))
def hp(g,q):
    valid=np.isfinite(g)&(q>0)
    if not valid.all():g=g[tuple(distance_transform_edt(~valid,return_distances=False,return_indices=True))]
    return (gaussian_filter(g.astype(float),6)-gaussian_filter(g.astype(float),24))[lo:lo+size,lo:lo+size]
def ncc(z,target,m):
    m=m.astype(float);n=m.sum();v=(target-target[m>0].mean())*m;vv=np.sum(v*v)
    def cor(a,b):
        c=fftconvolve(a,b[::-1,::-1],mode='full');return c[size-1-rg:size+rg,size-1-rg:size+rg]
    sm=cor(m,z);sq=cor(m,z*z);cs=cor(v,z)/np.sqrt(np.maximum(vv*(sq-sm*sm/n),1e-30));j,i=np.unravel_index(np.argmax(cs),cs.shape);dx=float(i-rg);dy=float(j-rg)
    def sub(a,b,c):return float(np.clip(.5*(a-c)/(a-2*b+c),-.5,.5)) if a-2*b+c < -1e-10 else 0.
    if 0<i<2*rg:dx+=sub(*cs[j,i-1:i+2])
    if 0<j<2*rg:dy+=sub(*cs[j-1:j+2,i])
    return dict(correction=[dx,dy],r=float(cs[j,i]),boundary=bool(i in [0,2*rg] or j in [0,2*rg]))
targets={}
for s in refs:
    z=np.load(ROOT/'output/earthshine_detail_20260911/native'/f'sony_{s}.npz');targets[s]=hp(z['g'],z['q'])
anchor=np.load(SRC/'A0_quincunx_572A2983.npz');anchorhp=hp(anchor['g'],anchor['q']);anchors={s:ncc(anchorhp,t,mask) for s,t in targets.items()}
rows=[]
for stem in stems:
    start=time.time();z=np.load(SRC/f'A0_quincunx_{stem}.npz');moving=hp(z['g'],z['q']);fits={s:ncc(moving,t,mask) for s,t in targets.items()};halves=[ncc(moving,targets[refs[0]],mask&a) for a in [sector,~sector]];null=ncc(moving,np.rot90(targets[refs[0]]),mask);relative={s:(np.array(fits[s]['correction'])-np.array(anchors[s]['correction'])).tolist() for s in refs};vec=np.array(list(relative.values()));reference_gap=float(max(np.linalg.norm(a-b) for a in vec for b in vec));half_gap=float(np.linalg.norm(np.array(halves[0]['correction'])-halves[1]['correction']));eligible=bool(all(v['r']>=.1 and not v['boundary'] for v in fits.values()) and reference_gap<=.3 and half_gap<=.5)
    r=dict(stem=stem,fits=fits,correction_relative_2983=relative,reference_gap_px=reference_gap,angular_halves=halves,half_gap_px=half_gap,null_90deg=null,diagnostic_eligible=eligible,seconds=time.time()-start);rows.append(r);save('D0_texture_registration_partial.json',dict(rows=rows,anchors=anchors));print(stem,'r',round(fits[refs[0]]['r'],4),'d',fits[refs[0]]['correction'],'refgap',round(reference_gap,3),'halfgap',round(half_gap,3),'eligible',eligible,flush=True)
# Controls on a long and intermediate exposure; translates only diagnostic data.
controls=[]
for stem in ['572A2983','572A2977']:
    z=np.load(SRC/f'A0_quincunx_{stem}.npz');g=z['g'].astype(float);q=z['q'];imposed=np.array([1.3,-.7]);original=ncc(hp(g,q),targets[refs[0]],mask);changed=ncc(hp(shift(g,(imposed[1],imposed[0]),order=1,cval=np.nan,prefilter=False),shift(q,(imposed[1],imposed[0]),order=1,cval=0,prefilter=False)),targets[refs[0]],mask);delta=np.array(changed['correction'])-original['correction'];controls.append(dict(stem=stem,imposed=imposed.tolist(),recovered=delta.tolist(),expected=(-imposed).tolist(),error=float(np.linalg.norm(delta+imposed)),boundary=original['boundary'] or changed['boundary']))
control_pass=all(r['error']<=.1 and not r['boundary'] for r in controls)
save('D0_lunar_texture_pose.json',dict(method=__doc__,anchors=anchors,rows=rows,controls=controls,control_PASS=control_pass,limits=['No new photographic registration promoted','Reference disagreements and spatial halves are required in addition to shift equivariance','All textures measured inside0.70R, independently from bright-limb profile fits']))
print('CONTROLS',json.dumps(controls),flush=True)
