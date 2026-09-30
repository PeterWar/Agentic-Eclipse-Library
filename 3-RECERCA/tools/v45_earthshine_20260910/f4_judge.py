"""Frozen LROC registration, unique angular nulls, whole limb + new marks.
LROC never enters a source, fit, weight, pixel, or render.
"""
from comu45 import *
from f3_global import detail,fill
from scipy.ndimage import gaussian_filter,map_coordinates,gaussian_filter1d
sys.path.insert(0,str(HERE44))
from f6_qa import load_lroc
NA=1440;RR=np.arange(365.,455.,.5);TH=np.arange(NA)*2*np.pi/NA
MX=(CXT+RR[:,None]*np.cos(TH)).astype(np.float32);MY=(CYT+RR[:,None]*np.sin(TH)).astype(np.float32)

def pol(a):return cv2.remap(np.nan_to_num(a).astype(np.float32),MX,MY,cv2.INTER_LINEAR)
def regions():
    cyan=cv2.remap(np.load(CAU45/'blau_clar_mask.npy').astype(np.uint8),MX,MY,cv2.INTER_NEAREST)>0
    lilasec=(TH>=np.radians(180))&(TH<=np.radians(195))
    r=RR[:,None];rs={'cyan400_428':cyan&(r>=400)&(r<428)}
    for name,a,b in [('ring400_428',400,428),('ring428_440',428,440),('ring440_449',440,449),('ring449_454',449,454)]:rs[name]=np.broadcast_to((r>=a)&(r<b),(len(RR),NA))
    for name,a,b in [('lila420_440',420,440),('lila440_449',440,449),('lila449_454',449,454)]:rs[name]=((r>=a)&(r<b))&lilasec[None,:]
    for j in range(8):rs['sector'+str(j)+'_435_450']=((r>=435)&(r<450))&((TH>=j*np.pi/4)&(TH<(j+1)*np.pi/4))[None,:]
    return rs

def score(a,b):
    good=np.isfinite(a)&np.isfinite(b);a=a[good].astype(float);b=b[good].astype(float);a-=a.mean();b-=b.mean()
    return float(a@b/max(np.linalg.norm(a)*np.linalg.norm(b),1e-30))

def judge(z):
    p=pol(z);lp=pol(load_lroc());rs=regions();freq=np.fft.rfftfreq(NA)[None,:]*NA/(2*np.pi*RR[:,None]);out={}
    for lo,hi in [(8,12),(16,24),(24,40),(40,64)]:
        h=(freq>=1/hi)&(freq<=1/lo)
        f=lambda q:np.fft.irfft(np.fft.rfft(q,axis=1)*h,n=NA,axis=1)
        a=f(p);b=f(lp);rows={}
        for name,m in rs.items():
            r=score(a[m],b[m]);nulls=[score(a[m],np.roll(b,NA*k//12,axis=1)[m]) for k in range(1,12)]
            rows[name]=dict(r=r,max_abs_null=max(map(abs,nulls)),passes=r>max(map(abs,nulls)),n=int(m.sum()))
        out[str(lo)+'_'+str(hi)]=rows
    return out

def main():
    claim45();rep={}
    names=[x.stem for x in CAU45.glob('*_logdetail.npy')]
    data={name:np.load(CAU45/(name+'.npy')) for name in names}
    data['V44_final']=np.log(np.maximum(np.load(CAU44/'earthshine_natural_disc.npy')[...,1],1e-4))
    for name,z in data.items():
        rep[name]=judge(z)
        print(name,{band:{k:(round(v['r'],3),round(v['max_abs_null'],3),v['passes']) for k,v in rr.items() if k in ['cyan400_428','ring440_449','lila440_449']} for band,rr in rep[name].items()},flush=True)
    savejson(REB45/'F4_judge.json',rep)
if __name__=='__main__':main()
