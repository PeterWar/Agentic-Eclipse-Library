"""Native differential CameraRaw transfer, frozen E2, V53 appearance preserved."""
from common import *
from psd_tools import PSDImage
from scipy.interpolate import PchipInterpolator
from scipy.ndimage import gaussian_filter1d,map_coordinates
from PIL import Image
claim();r,theta,d=geometry();s=PSDImage.open(V53)
def roi(l,c):
    a=channel(l,c)
    if c==-2:md=l._record.mask_data;left,top=md.left,md.top
    else:left,top=l.left,l.top
    if a.shape==(N,N) and (left,top)==(X0,Y0):return a
    return a[Y0-top:Y0-top+N,X0-left:X0-left+N]
def cr(path):
    p=PSDImage.open(path);l=next(l for l in p if l.name=='V45 font G · dos trens · preferència temporal · vel present')
    a=[]
    for c in range(3):
        i=[int(v.id) for v in l._record.channel_info].index(c)
        a.append(np.frombuffer(l._channels[i].get_data(N,N,16,p.version),dtype='>u2').reshape(N,N).astype(float))
    return np.mean(a,axis=0)
E=json.loads((ROOT/'output/earthshine_v50_limb_20260912/E2_appearance.json').read_text());kn=np.array(E['knots'])
F=PchipInterpolator(np.r_[0,kn[:,0],65535],np.r_[0,E['isotonic_output'],65535])
old=cr(OUT/'staging/C1_baseline.psd');new=cr(OUT/'staging/C1_camera_raw.psd');historical=cr(SRC/'full_sampler_delta/C1_camera_raw.psd')
base=np.load(OUT/'arrays/V53_moon_rgb.npy').astype('int32');delta=np.rint(F(new)-F(old)).astype('int32')
# Native local operators have a footprint beyond the physical lunar mask.
# Preserve the inherited invisible RGB there; no new support or new mask.
inherited_mask=np.load(OUT/'arrays/V53_lunar_mask.npy');delta[inherited_mask==0]=0
newrgb=base+delta[...,None]
assert newrgb.min()>=0 and newrgb.max()<=65535;assert np.max(np.ptp(newrgb-base,axis=-1))==0
newrgb=newrgb.astype('uint16');np.save(OUT/'arrays/C2_candidate_rgb.npy',newrgb)
Ba=roi(s[1],-1).astype(float)/65535*roi(s[1],-2)/65535;B=np.stack([roi(s[1],c) for c in range(3)],-1)/65535.
Sa=roi(s[7],-1)/65535.;S=np.stack([roi(s[7],c) for c in range(3)],-1)/65535.
La=roi(s[25],-1)/65535.*roi(s[25],-2)/65535.
Cc=B*Ba[...,None];Ca=Ba;Cb=np.where(Ca[...,None]>0,Cc/np.maximum(Ca[...,None],1e-9),0)
mix=(1-Ca[...,None])*S+Ca[...,None]*np.maximum(S,Cb);Cc=Sa[...,None]*mix+(1-Sa[...,None])*Cc;Ca=Sa+Ca-Sa*Ca
def compose(l):
    a=La+Ca-La*Ca;c=La[...,None]*l/65535+(1-La[...,None])*Cc
    return np.rint(np.where(a[...,None]>0,c/np.maximum(a[...,None],1e-9),0)*65535).astype('uint16')
cb=compose(base);cn=compose(newrgb);np.save(OUT/'arrays/C2_baseline_composite.npy',cb);np.save(OUT/'arrays/C2_candidate_composite.npy',cn)
native53=np.load(ROOT/'research/tools/earthshine_v50_temporal_20260912/cau/after_photoshop53_roi_u16.npy');err=abs(cb.astype(int)-native53.astype(int));assert err.max()<=3
# Full paired native injection: sensitivity ratio of the candidate and baseline
# to the same unseen 2D plane-wave field; not normalized to a claimed gain.
ib=F(cr(OUT/'staging/C1_injected_baseline.psd'))-F(old);ic=F(cr(OUT/'staging/C1_injected_candidate.psd'))-F(new)
injection=[]
for a,b in [(100,300),(300,370),(370,435),(435,449)]:
    for sec in range(12):
        m=(r>=a)&(r<b)&(theta>=sec*np.pi/6)&(theta<(sec+1)*np.pi/6);x=ib[m];y=ic[m]
        gain=float(x@y/max(x@x,1e-30));rho=corr(ib,ic,m)
        injection.append(dict(radius=[a,b],sector=sec,transfer=gain,r=rho,pass_gate=.9<=gain<=1.1))
# Exact inherited handoff detectors, applied equally to V53 and candidate.
dd=np.arange(-299.,9.,2.);sectors=(theta*12/(2*np.pi)).astype(int)
def profiles(layer,comp):
    a=layer[...,1];c=comp[...,1];rows=[]
    for sec in range(12):
        p=np.array([np.median(a[(sectors==sec)&(d>=v-1)&(d<v+1)]) for v in dd])
        steps=abs(np.diff(p))/np.maximum(.5*(p[1:]+p[:-1]),1)
        pp=np.array([np.median(c[(sectors==sec)&(d>=v-.5)&(d<v+.5)]) for v in range(-3,9)])
        outside=np.median(c[(sectors==sec)&(d>=8)&(d<14)])
        ratio=float(np.min(pp[3:])/outside)
        rows.append(dict(sector=sec,lunar_profile=p.tolist(),max_step_inside=float(steps[dd[1:]<-2].max()),composite_profile=pp.tolist(),monotonic=bool(np.all(np.diff(pp)>=0)),outside_ratio=ratio))
    ds=np.arange(-300.,-2.,.5);nt=1440;t=np.arange(nt)*2*np.pi/nt
    edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy');edge=gaussian_filter1d(edge,3.,mode='wrap');edge=np.interp(t,np.linspace(0,2*np.pi,len(edge),endpoint=False),edge,period=2*np.pi)
    rad=edge[None,:]+ds[:,None];pol=map_coordinates(a.astype(float),[CY+rad*np.sin(t),CX+rad*np.cos(t)],order=1)
    sm=gaussian_filter1d(pol,40,axis=1,mode='wrap');hp=sm-gaussian_filter1d(sm,24,axis=0,mode='nearest')
    return dict(rows=rows,arc_rms_DN16=float(np.sqrt(np.mean(hp*hp))),arc_max_radial_rms=float(np.max(np.sqrt(np.mean(hp*hp,axis=1)))),radius_bins_d=dd.tolist())
pb,pn=profiles(base,cb),profiles(newrgb,cn)
save('C2_appearance_gates.json',dict(native_identity_DN16=dict(max=float(abs(old-historical).max()),p95=float(np.percentile(abs(old-historical)[r<450],95))),
    transfer='V53 + frozen E2(current native candidate) - frozen E2(current native baseline); saved chroma exact',E2_historical_p95_DN16=E['heldout_error_DN16'][1],
    delta_DN16=dict(p50=float(np.percentile(abs(delta)[r<450],50)),p95=float(np.percentile(abs(delta)[r<450],95)),max=int(abs(delta).max())),
    zero_clip=True,chroma_exact=True,recompose_baseline_max_DN16=int(err.max()),native_injection=injection,baseline=pb,candidate=pn))
for name,a in [('V53',cb),('candidate',cn)]:
    Image.fromarray((a>>8).astype('uint8')).save(OUT/f'vistes/C2_{name}_moon.png')
    # Identical presentation-only exposure lift, no change to source/PSB.
    q=np.clip(a.astype(float)*2,0,65535).astype('uint16');Image.fromarray((q>>8).astype('uint8')).save(OUT/f'vistes/C2_{name}_moon_x2.png')
Image.fromarray(np.clip((cn.astype(float)-cb)*4/256+128,0,255).astype('uint8')).save(OUT/'vistes/C2_delta_x4.png')
print('C2 native injection',min(x['transfer'] for x in injection),max(x['transfer'] for x in injection),'arcs',pb['arc_rms_DN16'],pn['arc_rms_DN16'],'delta',np.percentile(abs(delta)[r<450],[50,95,100]),flush=True)
