"""Training-only RGB screen. No Sony pixels inspected for selecting producer.
Compare split temporal sets and colors at fixed Fourier bands. Independent
sensor qualification happens later after coefficients are frozen.
"""
from common import *
from scipy.ndimage import gaussian_filter,map_coordinates
from scipy.fft import rfft2
claim();plan=json.loads((OUT/'PLAN.json').read_text());fit=plan['pilot']['fit_vixen'];fr=[m for m in json.loads((OUT/'A0_freeze.json').read_text())['pilot_frames'] if m['tren']=='vixen']
channels=['R','G1','G2','B'];nums={};dens={};rows=[]
for part in ['all','fit','test','early','late']:
    for c in channels:nums[part+'_'+c]=np.zeros((N,N));dens[part+'_'+c]=np.zeros((N,N))
poses=[];rad,theta=geometry()
for m in fr:
    z=np.load(OUT/'native'/('vixen_'+m['stem']+'.npz'));poses.append(dict(stem=m['stem'],exp=m['exp'],time=m['t_mid_C2'],roi_to_native=z['roi_to_native']))
    alpha=35.54865158 if m['exp']>=10 else 32.94040478 if m['exp']>=2 else 14.82631372
    for c in channels:
        a=z[c].astype(float);v=z[c+'_var'].astype(float);q=z[c+'_q'].astype(float);good=np.isfinite(a)&np.isfinite(v)&(q>0)
        den=gaussian_filter(good.astype(float),4);vs=gaussian_filter(np.where(good,v,0),4)/np.maximum(den,1e-30);w=np.where(good,q/np.maximum(vs*alpha,1e-12),0)
        for part in ['all','fit' if m['stem'] in fit else 'test','early' if m['t_mid_C2']<40 else 'late']:
            key=part+'_'+c;nums[key]+=np.where(good,a,0)*w;dens[key]+=w
    print('STACK',m['stem'],flush=True)
st={k:np.where(dens[k]>0,nums[k]/np.maximum(dens[k],1e-30),np.nan) for k in nums}
for part in ['all','fit','test','early','late']:
    a,b=part+'_G1',part+'_G2';st[part+'_G']=(nums[a]+nums[b])/np.maximum(dens[a]+dens[b],1e-30)
np.savez_compressed(OUT/'arrays/A2_color_stacks.npz',**{k:v.astype(np.float32) for k,v in st.items()},**{'weight_'+k:v.astype(np.float32) for k,v in dens.items()})
# Absolute sensor displacement and diversity along both principal directions.
centres=np.array([np.array(p['roi_to_native'])@np.array([CX,CY,1]) for p in poses]);_,sv,V=np.linalg.svd(centres-centres.mean(0),full_matrices=False)
save('A2_detector_diversity.json',dict(poses=poses,centres=centres,range_xy=np.ptp(centres,axis=0),principal_RMS=sv/np.sqrt(len(centres)),directions=V,interpretation='Two-axis diversity measures identifiability potential, not a proof of successful self calibration. Exposure classes and times confounded.'))
rr=np.arange(60.,450.,.5);nt=1440;th=np.arange(nt)*2*np.pi/nt;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)];f=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*rr[:,None])
def polar(a):return map_coordinates(a,co,order=3,mode='nearest')
P={k:np.fft.rfft(polar(v),axis=1) for k,v in st.items()}
fitreg=np.broadcast_to(((np.arange(nt)//120)%2==0)[None,:],(len(rr),nt));coeffs={}
for band in plan['judge']['bands_px']:
    lo,hi=band;H=(f>=1/hi)&(f<=1/lo);B={k:np.fft.irfft(v*H,n=nt,axis=1) for k,v in P.items()}
    for rlo,rhi in plan['judge']['radii']:
        for parity in [0,1]:
            mask=(rr[:,None]>=rlo)&(rr[:,None]<rhi)&(fitreg if parity==0 else ~fitreg)
            for c in ['R','G1','G2','B']:
                rows.append(dict(band=band,radius=[rlo,rhi],parity=parity,channel=c,r_same_G=corr(B['all_'+c],B['all_G'],mask),r_temporal=corr(B['fit_'+c],B['test_'+c],mask),r_temporal_G=corr(B['fit_'+c],B['test_G'],mask),rms=float(np.std(B['all_'+c][mask])),rms_G=float(np.std(B['all_G'][mask]))))
    # Coherent large-scale slope uses cross-G1/G2 within training captures,
    # avoiding same-G auto-power. CFA planes still share systematics.
    if band==[64,96]:
        mask=(rr[:,None]<350)&fitreg
        g1=B['fit_G1'][mask];g2=B['fit_G2'][mask];g=.5*(g1+g2);signal=np.mean(g1*g2)
        for c in ['R','B']:
            coeffs[c]=float(np.mean(B['fit_'+c][mask]*g)/signal)
save('A2_rgb_training_screen.json',dict(rows=rows,color_texture_slopes_relative_G=coeffs,rule='64-96 px tangential cross-CFA spectrum, training frames/even sectors/r<350 only. Estimate recorded before external comparison.',limits=['Each sensor color shares photon scene but may carry spectral albedo and chromatic PSF differences','Empirical exposure alpha inherited from G for provisional time stacking, not claimed calibrated for R/B','Common detector artifacts can inflate within-sensor covariance']))
for b in plan['judge']['bands_px']:
    for c in ['R','G1','G2','B']:
        a=[r for r in rows if r['band']==b and r['channel']==c and r['radius'][1]<=410 and r['parity']==1]
        print('RGB',b,c,'r temporal G',round(np.mean([r['r_temporal_G'] for r in a]),4),'r temporal same',round(np.mean([r['r_temporal'] for r in a]),4),'r allG',round(np.mean([r['r_same_G'] for r in a]),4),flush=True)
print('TEXTURE SLOPES',coeffs,'SENSOR RANGE',np.ptp(centres,axis=0),'RMS',sv/np.sqrt(len(centres)),flush=True)
