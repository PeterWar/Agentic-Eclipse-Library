"""Frozen independent last-limb judge; measured source, no sector background.
Reproduces the read-only review. Not a radial-resolution or absence-of-signal test.
"""
from comu45 import *
from scipy.ndimage import map_coordinates,distance_transform_edt

def main():
    claim45();Y,X=np.mgrid[:N,:N];radius=np.hypot(X-CXT,Y-CYT);x=(X-CXT)/500;y=(Y-CYT)/500
    rr=np.arange(435.,449.,.5);nt=1440;th=np.arange(nt)*2*np.pi/nt
    coords=[CYT+rr[:,None]*np.sin(th),CXT+rr[:,None]*np.cos(th)]
    lrfile=ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy';lr=np.load(lrfile)
    bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];L=np.zeros((N,N));oy,ox=bb[1]-Y0,bb[0]-X0
    L[oy:oy+lr.shape[0],ox:ox+lr.shape[1]]=lr[...,:3].mean(-1);raw={'L':L}
    paths={'V45V':(CAU45/'vixen_reference.npy',None),'V45S':(CAU45/'sony_reference.npy',None),'V45C':(CAU45/'combined_reference.npy',None),'V44V':(CAU44/'surface_vixen_rgb.npy',1),'V44S':(CAU44/'surface_sonyA_rgb.npy',1),'V44C':(CAU44/'surface_clean_rgb.npy',1),'V44display':(CAU44/'earthshine_natural_disc.npy',1)}
    report={'inputs':{'L':dict(path=str(lrfile),sha256=sha(lrfile))},'results':{},'scope':'fixed435–449 annulus, full angularFFT, cosine weights at correlation only, oneCartesianplane, fixedLROC,11rotatednulls; no radial filtering'}
    for name,(p,ch) in paths.items():
        a=np.load(p);raw[name]=(a if ch is None else a[...,ch]).astype(float);report['inputs'][name]=dict(path=str(p),sha256=sha(p))
    valids={k:np.isfinite(a)&(a>0) for k,a in raw.items()};pgood={k:map_coordinates(v.astype(float),coords,order=1,mode='constant',cval=0)>.999 for k,v in valids.items()}
    common=np.logical_and.reduce(list(pgood.values()));report['support']=dict(valid=int(common.sum()),total=common.size,LROC_bbox=bb)
    freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*rr[:,None])
    def pearw(a,b,w):
        sel=(w>0)&np.isfinite(a)&np.isfinite(b);ww=w[sel];a=a[sel];b=b[sel];s=ww.sum();aa=a-(a@ww)/s;bb=b-(b@ww)/s
        return float((aa*bb)@ww/max(np.sqrt((aa*aa)@ww)*np.sqrt((bb*bb)@ww),1e-30))
    weights={'ring':common.astype(float)}
    for j in range(8):
        dt=(th-(j+.5)*np.pi/4+np.pi)%(2*np.pi)-np.pi;w=np.where(abs(dt)<np.pi/8,.5+.5*np.cos(dt*8),0);weights['sector'+str(j)]=common*w[None,:]
    pairs=[('V45VS','V45V','V45S'),('V45VL','V45V','L'),('V45SL','V45S','L'),('V45CL','V45C','L'),('V44VS','V44V','V44S'),('V44VL','V44V','L'),('V44SL','V44S','L'),('V44CL','V44C','L'),('V44displayL','V44display','L')]
    for mode in ['log','linear']:
        pol={};mode_result={};passed=0
        for name,g in raw.items():
            valid=valids[name];ix=distance_transform_edt(~valid,return_distances=False,return_indices=True);a=g[tuple(ix)]
            if mode=='log':a=np.log(np.maximum(a,1e-30))
            m=valid&(radius<449);A=np.stack([np.ones(int(m.sum())),x[m],y[m]],1);co=np.linalg.lstsq(A,a[m],rcond=None)[0]
            resid=a-(co[0]+co[1]*x+co[2]*y);pol[name]=map_coordinates(resid,coords,order=3,mode='nearest')
        for lo,hi in [(16,24),(24,40),(40,64)]:
            mask=(freq>=1/hi)&(freq<=1/lo);bf={k:np.fft.irfft(np.fft.rfft(a,axis=1)*mask,n=nt,axis=1) for k,a in pol.items()};result={}
            for pn,a,b in pairs:
                rows={}
                for reg,w in weights.items():
                    r=pearw(bf[a],bf[b],w);null=[pearw(bf[a],np.roll(bf[b],nt*k//12,axis=1),w) for k in range(1,12)];n=max(map(abs,null))
                    rows[reg]={'r':r,'null':n,'pass':r>n}
                result[pn]=rows
            for j in range(8):passed+=all(result[p]['sector'+str(j)]['pass'] for p in ['V45VS','V45VL','V45SL'])
            mode_result[str(lo)+'_'+str(hi)]=result
        report['results'][mode]=dict(bands=mode_result,triple_pass_sectors=int(passed),total=24)
        print(mode,passed,'/24',flush=True)
    report['F2_sha256']=sha(REB45/'F2_temporal.json');report['conclusion']='NO_CORROBORATED_NEW_RECOVERY_OF_ALL_LAST_LIMB'
    savejson(REB45/'F9_fixed_last_limb_judge.json',report)
if __name__=='__main__':main()
