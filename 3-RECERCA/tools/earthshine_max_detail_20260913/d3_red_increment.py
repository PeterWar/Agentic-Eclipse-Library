"""Bounded test of additional red information in the saved photographic base.
Photo = beta*Gclean + gamma*Gdetector + mu*(Rclean/scaled-Gclean).
Target red fraction is A3's frozen GR photon fraction; add only a missing
positive red contribution. No increased red contribution if already present.
"""
from common import *
from spectral import *
from scipy.ndimage import map_coordinates
claim();model=json.loads((OUT/'A5_color_model.json').read_text());wr=model['weights']['R']/(model['weights']['R']+model['weights']['G'])
g=np.load(OUT/'arrays/B3_G67_robust_hetero_full_safe_all.npz');red=np.load(OUT/'arrays/B3_R67_robust_hetero_full_safe_all.npz')['source']/model['slopes']['R']+model['offsets']['R'];contrast=red-g['source'];old=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/D1_candidate_rgb.npy').astype(np.int32)
S,V=polar(g['source']);D,_=polar(g['correction']);R,_=polar(contrast);P,_=polar(old.mean(-1));a,b,c,q=[angular_band(z,16,64) for z in [S,D,R,P]];fit=sector_mask(60,350,0)&V;hold=sector_mask(60,350,1)&V
save('D3_protocol.json',dict(method=__doc__,fraction_red=wr,training='even sectors r60-350, same fixed16-64 band; no Sony fit',rule='beta,gamma,mu by unconstrained scalar regression; if beta*wr-mu<=0, no extra red signal is called missing. If positive, bounded candidate adds exactly that amount plus detector correction from fit, then passes unchanged photographic gates. No tuning to heldout.'))
X=np.stack([a[fit],b[fit],c[fit]],1);beta,gamma,mu=np.linalg.lstsq(X,q[fit],rcond=None)[0];extra=beta*wr-mu;rows=[]
for band in [[16,24],[24,40],[40,64]]:
    aa,bb,cc,qq=[angular_band(z,*band) for z in [S,D,R,P]];xx=np.stack([aa[fit],bb[fit],cc[fit]],1);cf=np.linalg.lstsq(xx,qq[fit],rcond=None)[0];rows.append(dict(band=band,beta=float(cf[0]),gamma=float(cf[1]),mu=float(cf[2]),extra_red=float(cf[0]*wr-cf[2])))
rep=dict(beta=float(beta),gamma=float(gamma),mu=float(mu),target_red_fraction=wr,extra_red=float(extra),condition=float(np.linalg.cond(X)),heldout_residual_rms=float(np.std((q-beta*a-gamma*b-mu*c)[hold])),per_band=rows,missing_positive_red=bool(extra>0),claim='Empirical component fit, not provenance proof or native CameraRaw slider reconstruction')
save('D3_red_fit.json',rep);print('RED PHOTO',rep,flush=True)
if extra>0:
    rr=np.arange(0,456.,.5);nt=2880;th=np.arange(nt)*2*np.pi/nt;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)];f=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*np.maximum(rr[:,None],.25))
    u=np.clip((f-1/96)/(1/64-1/96),0,1);v=np.clip((f-1/16)/(1/12-1/16),0,1);H=(.5-.5*np.cos(np.pi*u))*(.5+.5*np.cos(np.pi*v))
    pol=map_coordinates(contrast,co,order=3,mode='nearest');pb=np.fft.irfft(np.fft.rfft(pol,axis=1)*H,n=nt,axis=1);rad,theta=geometry();pad=np.c_[pb[:,-2:],pb,pb[:,:2]];cr=map_coordinates(pad,[np.minimum(rad/.5,len(rr)-1),theta*nt/(2*np.pi)+2],order=3,mode='nearest')
    delta=np.rint(-gamma*g['correction']+extra*cr).astype(np.int32);mask=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/V53_lunar_mask.npy');alpha=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/V53_lunar_alpha.npy');delta[(mask==0)|(alpha==0)]=0;new=old+delta[...,None]
    assert new.min()>=0 and new.max()<=65535,'Clipping: no red candidate'
    np.save(OUT/'arrays/D3_candidate_rgb.npy',new.astype(np.uint16));np.save(OUT/'arrays/D3_delta.npy',delta)
