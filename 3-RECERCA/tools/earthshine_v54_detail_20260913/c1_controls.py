"""Same-version native Camera Raw identity and blind injected paired controls."""
from c0_photoshop import *
from scipy.ndimage import map_coordinates
claim();assert RESULT.exists()
def write_source(rgb,dst):
    assert not dst.exists();s=PSDImage.open(PRE);l=next(l for l in s if l.name==NAME)
    for info,ch in zip(l._record.channel_info,l._channels):
        if int(info.id) in [0,1,2]:
            ch.set_data(np.ascontiguousarray(rgb[...,int(info.id)].astype('>u2')).tobytes(),N,N,16,s.version);info.length=len(ch.data)+2
    finalize_lr16(s);s._updated=False
    with dst.open('xb') as f:s.save(f)
def replay(name,source):
    dst=OUT/f'staging/C1_{name}.psd';assert not dst.exists()
    js=(OUT/'receipts/C1_replay.jsx').read_text()
    js=js.replace(str(DST),str(source)).replace(str(RESULT),str(dst))
    for suffix in ['input_descriptor.bin','returned_descriptor.bin']:js=js.replace('C1_'+suffix,'C1_'+name+'_'+suffix)
    before=inventory();result=jsx(js);after=inventory();assert before==after
    save(f'C1_{name}.json',dict(result=result,source=str(source),source_sha256=sha(source),output=str(dst),sha256=sha(dst),inventory=after,preserved=True))
    print(name,'DONE',flush=True)
replay('baseline',PRE)
# Freeze a real 2D plane-wave injection with non-radial orientations, 40-64px.
# Reproduce the B3 producer explicitly without importing its writing script.
orig=np.load(SRC/'full_sampler_delta/C0_pre_camera_raw_rgb.npy').astype(float)
gain=np.load(OUT/'arrays/B3_confidence_polar.npy');nt=2880;rr=np.arange(0.,456.,.5);th=np.arange(nt)*2*np.pi/nt
r,theta,d=geometry();yy,xx=np.mgrid[:N,:N];rng=np.random.default_rng(540915);field=np.zeros((N,N))
for k in range(8):
    angle=rng.uniform(0,2*np.pi);phase=rng.uniform(0,2*np.pi);wave=rng.uniform(42,60)
    field+=np.sin(2*np.pi*((xx-CX)*np.cos(angle)+(yy-CY)*np.sin(angle))/wave+phase)
mask=np.load(OUT/'arrays/V53_lunar_mask.npy')/65535.;field*=mask;field*=40/np.std(field[r<430])
base=np.rint(orig+field[...,None]).astype('uint16')
co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)];p=map_coordinates(base.mean(-1),co,order=3,mode='nearest')
freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*np.maximum(rr[:,None],.25))
u=np.clip((freq-1/80)/(1/64-1/80),0,1);v=np.clip((freq-1/40)/(1/32-1/40),0,1);H=(.5-.5*np.cos(np.pi*u))*(.5+.5*np.cos(np.pi*v))
b=np.fft.irfft(np.fft.rfft(p,axis=1)*H,n=nt,axis=1);pm=map_coordinates(mask,co,order=3,mode='nearest')
dp=.08*gain*b*np.clip(pm,0,1);pad=np.concatenate([dp[:,-2:],dp,dp[:,:2]],1)
dc=map_coordinates(pad,[np.minimum(r/.5,len(rr)-1),theta*nt/(2*np.pi)+2],order=3,mode='nearest');dc[mask==0]=0
cand=np.rint(base.astype(float)+dc[...,None]).astype('uint16')
np.save(OUT/'arrays/C1_blind_field.npy',field);np.save(OUT/'arrays/C1_blind_base.npy',base);np.save(OUT/'arrays/C1_blind_candidate.npy',cand)
save('C1_injection_design.json',dict(seed=540915,orientation='8 randomly oriented plane waves, wavelengths42-60px;40DN16 RMS; physical inherited lunar support',fit=False,confidence_frozen=True))
for name,a in [('injected_baseline',base),('injected_candidate',cand)]:
    src=OUT/f'staging/C0_{name}.psd';write_source(a,src);replay(name,src)
