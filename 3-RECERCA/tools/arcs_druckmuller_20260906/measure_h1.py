"""Fixed radial sampling independent of H1's 200 diagnostic bins.

Measures the direct stored H1 contribution, not scientific artifact purity.
Radial bands use an explicit Butterworth response; no DoG band estimates.
"""
from pathlib import Path
import json, hashlib
import numpy as np
from scipy.ndimage import map_coordinates
from scipy.signal import butter, sosfiltfilt

ROOT=Path(__file__).resolve().parents[3]
D=Path(__file__).parent
C=ROOT/'research/tools/v29/cau_final'
CX,CY,RS=5361.768111973117,3775.747534140857,440.60304883027544
r=np.arange(np.floor(1.5*RS),np.ceil(5.5*RS)+1)
t=np.arange(1440)*2*np.pi/1440
yx=np.stack(np.broadcast_arrays(CY+r[:,None]*np.sin(t),CX+r[:,None]*np.cos(t)))
def sample(path):
    a=np.load(path,mmap_mode='r')
    return map_coordinates(a,yx,order=1,prefilter=False,mode='constant',cval=np.nan,output=np.float64)
mask=sample(C/'fusion_support.npy')
assert np.all(mask>.999999)
def bp(a,lo,hi):
    sos=butter(4,[1/hi,1/lo],btype='bandpass',fs=1,output='sos')
    return sosfiltfilt(sos,a,axis=0)
def rms(a):return float(np.sqrt(np.mean(np.square(a))))
out={'status':'DIAGNOSTIC_ONLY','solar_geometry':[CX,CY,RS],
     'sampling':'1 radial pixel,1440 angles,eight45deg sectors; float64 bilinear samples;1.5-5.5R;all physical support valid',
     'bandpass':'Butterworth order4, zero-phase sosfiltfilt along radius; evaluation2.5-4.5R avoids boundaries',
     'definitions':'F=u16/65535-.5;S=smoothed beforeH1;C=F-S including clipping/quantization;Cmedian=median over angles;sector residual=meanF over45deg;common=mean over all angles',
     'layers':{}}
for tag,name in [('01','achf'),('02','passalt24')]:
    S=sample(C/f'{name}_smoothed.npy');F=sample(C/f'{name}_u16.npy')/65535-.5;delta=F-S
    cm=np.median(delta,axis=1)
    sectors=np.stack([np.mean(F[:,i*180:(i+1)*180],axis=1) for i in range(8)],axis=1)
    q={}
    for lo,hi in [(4,32),(32,128)]:
        cb=bp(cm,lo,hi); fb=bp(sectors,lo,hi)
        sb=bp(np.mean(S,axis=1),lo,hi); fcommon=bp(np.mean(F,axis=1),lo,hi)
        for a,b in [(2.5,3.5),(3.5,4.5),(2.5,4.5)]:
            k=(r>=a*RS)&(r<b*RS); cr=rms(cb[k]); fr=np.array([rms(fb[k,j]) for j in range(8)])
            q[f'{a}-{b}R_{lo}-{hi}px']={'H1_median_RMS':cr,'sector_RMS_median':float(np.median(fr)),
                'H1_to_sector_RMS_median':float(np.median(cr/fr)),
                'common_preH1_RMS':rms(sb[k]),'common_postH1_RMS':rms(fcommon[k])}
    out['layers'][tag]=q
out['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
(D/'h1_measurements.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:{b:q for b,q in v.items() if b.startswith('2.5-4.5')} for k,v in out['layers'].items()},indent=2))
