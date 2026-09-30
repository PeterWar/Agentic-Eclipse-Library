"""Fixed independent source judge and photographic retention. No optimization."""
from common import *
from scipy.ndimage import map_coordinates,distance_transform_edt,label
claim();r,theta,d=geometry()
rr=np.arange(100.,450.,.5);nt=1440;th=np.arange(nt)*2*np.pi/nt
co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)]
f=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*rr[:,None])
y,x=np.mgrid[:N,:N];x=(x-CX)/500;y=(y-CY)/500
def polar(a,log=False):
    valid=np.isfinite(a)&(a>0)
    ix=distance_transform_edt(~valid,return_distances=False,return_indices=True)
    a=a[tuple(ix)].astype(float)
    if log:a=np.log(a)
    m=valid&(r<435);A=np.stack([np.ones(m.sum()),x[m],y[m]],1)
    b=np.linalg.lstsq(A,a[m],rcond=None)[0]
    p=map_coordinates(a-b[0]-b[1]*x-b[2]*y,co,order=3,mode='nearest')
    v=map_coordinates(valid.astype(float),co,order=1,mode='constant')>.999
    return p,v
def band(p,lo,hi):return np.fft.irfft(np.fft.rfft(p,axis=1)*((f>=1/hi)&(f<=1/lo)),n=nt,axis=1)
def compare(a,b,m):
    if m.sum()<50:return dict(r=None,null_max=None,pass_null=False,rms=None,valid_pixels=int(m.sum()),reason='insufficient valid support')
    c=corr(a,b,m);null=[corr(a,np.roll(b,nt*j//12,axis=1),m) for j in range(1,12)]
    return dict(r=c,null_max=max(map(abs,null)),pass_null=c>max(map(abs,null)),rms=float(np.std(a[m])),valid_pixels=int(m.sum()))
def lroc():
    a=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy')
    bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox']
    q=np.zeros((N,N));oy,ox=bb[1]-Y0,bb[0]-X0;q[oy:oy+a.shape[0],ox:ox+a.shape[1]]=a[...,:3].mean(-1)
    return q
if __name__=='__main__':
    z=np.load(OUT/'arrays/B1_stacks.npz')
    raw={k:z[k] for k in ['all','temporal','half0','half1','early','late']}
    raw['noise']=np.load(OUT/'arrays/B1_noise_candidate.npy')
    raw['V49_source']=np.load(SRC/'B0_new_all.npz')['candidate']
    raw['Sony']=np.load(ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference']
    raw['LROC']=lroc()
    raw['V53']=np.load(OUT/'arrays/V53_moon_rgb.npy').mean(-1)
    raw['preCR']=np.load(SRC/'full_sampler_delta/C0_pre_camera_raw_rgb.npy').mean(-1)
    for stem in ['572A2982','572A2983','572A2984']:
        ix=next(i for i,m in enumerate([f for f in frame_list() if f['tren']=='vixen']) if m['stem']==stem)
        raw[stem]=np.load(SRC/'compositor_cache/G.npy',mmap_mode='r')[ix].copy()
    marks=np.load(ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz')['green'];lab,_=label(marks)
    upper=map_coordinates((lab==lab[313,630]).astype(float),co,order=1)>.999
    regions={'upper_green':upper&(rr[:,None]>=370)&(rr[:,None]<435)}
    for lo,hi in [(100,300),(300,370),(370,435),(435,449)]:
        for parity in [0,1]:regions[f'{lo}_{hi}_'+('fit' if parity==0 else 'heldout')]=np.broadcast_to((rr[:,None]>=lo)&(rr[:,None]<hi),(len(rr),nt))&((np.arange(nt)[None,:]//120)%2==parity)
    rows=[]
    for mode in ['linear','log']:
        pol={k:polar(v,mode=='log') for k,v in raw.items()}
        for lo,hi in [(8,16),(16,24),(24,40),(40,64),(64,96)]:
            b={k:band(p[0],lo,hi) for k,p in pol.items()}
            for reg,m0 in regions.items():
                m=m0&pol['Sony'][1]&pol['LROC'][1]
                sl=compare(b['Sony'],b['LROC'],m)
                for name in raw:
                    if name in ['Sony','LROC']:continue
                    mm=m&pol[name][1];vs=compare(b[name],b['Sony'],mm);vl=compare(b[name],b['LROC'],mm)
                    rows.append(dict(mode=mode,band=[lo,hi],region=reg,source=name,Sony=vs,LROC=vl,SL=sl['r'],triple=vs['pass_null'] and vl['pass_null'] and sl['pass_null']))
            print(mode,lo,hi,'done',flush=True)
    save('B2_judge.json',dict(rows=rows,limits=['V53/preCR comparisons are retention: Sony already in their broad base.', 'Source Vixen producer excludes Sony/LROC; geometry and calibration jointly determined previously.', 'Rotated null is exploratory, not a formal multiple-comparison probability.']))
    for name in ['all','temporal','noise','V49_source','V53','preCR']:
        a=[v for v in rows if v['source']==name and v['mode']=='linear' and 'heldout' in v['region']]
        print(name,'triples',sum(v['triple'] for v in a),'of',len(a),'rSony',np.mean([v['Sony']['r'] for v in a]),flush=True)
