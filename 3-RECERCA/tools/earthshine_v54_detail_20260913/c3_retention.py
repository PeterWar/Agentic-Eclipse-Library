"""Photographic retained structure and gain; Sony is NOT independent here."""
from b2_judge import *
from PIL import Image
import sys
tag='D1' if len(sys.argv)>1 and sys.argv[1]=='D1' else 'C2'
claim();raw={'V53':np.load(OUT/'arrays/V53_moon_rgb.npy').mean(-1),'candidate':np.load(OUT/f'arrays/{tag}_candidate_rgb.npy').mean(-1),
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
            x=b['V53'][m];y=b['candidate'][m];x=x-x.mean();y=y-y.mean()
            rows.append(dict(mode=mode,band=[lo,hi],region=region,old=old,new=new,old_triple=ob,new_triple=nb,relative_amplitude=float(x@y/max(x@x,1e-30)),same_structure=corr(b['V53'],b['candidate'],m)))
lost=[x for x in rows if x['old_triple'] and not x['new_triple']]
held=[x for x in rows if x['mode']=='linear' and 'heldout' in x['region']]
save('D2_retention.json' if tag=='D1' else 'C3_retention.json',dict(rows=rows,lost_triples=lost,old_triples=sum(x['old_triple'] for x in rows),new_triples=sum(x['new_triple'] for x in rows),
    mean_Sony_heldout_before=float(np.mean([x['old']['Sony']['r'] for x in held])),mean_Sony_heldout_after=float(np.mean([x['new']['Sony']['r'] for x in held])),
    limits=['Photographic retention only: base already contains Sony.','No new lunar feature or new spatial resolution claimed.','Data, parameters and null controls fixed before this comparison.']))
print('C3 triples lost',len(lost),'of',sum(x['old_triple'] for x in rows),flush=True)
for x in held:
    if x['band']==[40,64]:print(x['region'],'amplitude',x['relative_amplitude'],'structure',x['same_structure'],'Sony',x['old']['Sony']['r'],x['new']['Sony']['r'],flush=True)
