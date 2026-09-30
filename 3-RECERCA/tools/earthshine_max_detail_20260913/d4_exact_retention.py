"""Fixed independent source judge and photographic retention. No optimization."""
from common import *
from scipy.ndimage import map_coordinates,distance_transform_edt,label
claim();r,theta=geometry()
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

"""Photographic retained structure and gain; Sony is NOT independent here."""

from PIL import Image
import sys
tag='D0'
claim();raw={'V53':np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/D1_candidate_rgb.npy').mean(-1),'candidate':np.load(OUT/f'arrays/{tag}_candidate_rgb.npy').mean(-1),
 'Sony':np.load(ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'],'LROC':lroc()}
marks=np.load(ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz')['green'];lab,_=label(marks)
regions={f'green_{i}':map_coordinates((lab==i).astype(float),co,order=1)>.999 for i in range(1,lab.max()+1) if (lab==i).sum()>=100}
regions['upper_green']=map_coordinates((lab==lab[313,630]).astype(float),co,order=1)>.999
for a,b in [(100,300),(300,370),(370,435),(435,449)]:
    for parity in [0,1]:regions[f'{a}_{b}_'+('fit' if parity==0 else 'heldout')]=np.broadcast_to((rr[:,None]>=a)&(rr[:,None]<b),(len(rr),nt))&((np.arange(nt)[None,:]//120)%2==parity)
rows=[]
for mode in ['linear','log']:
    pol={k:polar(v,mode=='log') for k,v in raw.items()}
    for lo,hi in [(8,16),(16,24),(24,40),(40,64),(64,96)]:
        b={k:band(v[0],lo,hi) for k,v in pol.items()}
        for region,m0 in regions.items():
            m=m0&pol['Sony'][1]&pol['LROC'][1]&pol['V53'][1]&pol['candidate'][1]
            if m.sum()<50:continue
            sl=compare(b['Sony'],b['LROC'],m);old={j:compare(b['V53'],b[j],m) for j in ['Sony','LROC']};new={j:compare(b['candidate'],b[j],m) for j in ['Sony','LROC']}
            ob=old['Sony']['pass_null'] and old['LROC']['pass_null'] and sl['pass_null'];nb=new['Sony']['pass_null'] and new['LROC']['pass_null'] and sl['pass_null']
            vx=b['V53'][m];vy=b['candidate'][m];vx=vx-vx.mean();vy=vy-vy.mean()
            rows.append(dict(mode=mode,band=[lo,hi],region=region,old=old,new=new,old_triple=ob,new_triple=nb,relative_amplitude=float(vx@vy/max(vx@vx,1e-30)),same_structure=corr(b['V53'],b['candidate'],m)))
lost=[x for x in rows if x['old_triple'] and not x['new_triple']]
held=[x for x in rows if x['mode']=='linear' and 'heldout' in x['region']]
save('D4_exact_retention.json',dict(rows=rows,lost_triples=lost,old_triples=sum(x['old_triple'] for x in rows),new_triples=sum(x['new_triple'] for x in rows),
    mean_Sony_heldout_before=float(np.mean([x['old']['Sony']['r'] for x in held])),mean_Sony_heldout_after=float(np.mean([x['new']['Sony']['r'] for x in held])),
    limits=['Photographic retention only: base already contains Sony.','No new lunar feature or new spatial resolution claimed.','Data, parameters and null controls fixed before this comparison.']))
print('C3 triples lost',len(lost),'of',sum(x['old_triple'] for x in rows),flush=True)
for x in held:
    if x['band']==[40,64]:print(x['region'],'amplitude',x['relative_amplitude'],'structure',x['same_structure'],'Sony',x['old']['Sony']['r'],x['new']['Sony']['r'],flush=True)
