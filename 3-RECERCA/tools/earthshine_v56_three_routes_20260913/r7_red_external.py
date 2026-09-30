"""Fixed source-only external judge; all candidates retained, no model edits.
Sony green alone is independent from Vixen candidates. LROC reference is a
second, historical pattern check; no external pixels in producer.
"""
from common import *
from spectral import *
import sys
claim();q=np.load(OUT/'arrays/R5_sources.npz');raw={k:q[k] for k in q.files}
raw['Sony']=np.load(ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference']
l=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];lr=np.full((N,N),np.nan);oy,ox=bb[1]-Y0,bb[0]-X0;lr[oy:oy+l.shape[0],ox:ox+l.shape[1]]=l[...,:3].mean(-1);raw['LROC']=lr
plan=json.loads((OUT/'PLAN.json').read_text());rows=[];tile_rows=[];P={k:polar(a) for k,a in raw.items()}
def compare(a,b,m):
    val=corr(a,b,m);null=[corr(a,np.roll(b,NT*j//12,axis=1),m) for j in range(1,12)]
    return dict(r=val,null_max=float(np.nanmax(np.abs(null))),pass_null=val>np.nanmax(np.abs(null)))
for band in plan['judge']['bands']:
    B={k:angular_band(p[0],*band) for k,p in P.items()}
    for rlo,rhi in plan['judge']['radii']:
        for parity in [0,1]:
            mask=sector_mask(rlo,rhi,parity)&P['Sony'][1]&P['LROC'][1];sl=compare(B['Sony'],B['LROC'],mask)
            for c in raw:
                if c in ['Sony','LROC']:continue
                good=mask&P[c][1];vs=compare(B[c],B['Sony'],good);vl=compare(B[c],B['LROC'],good)
                rows.append(dict(band=band,radius=[rlo,rhi],parity=parity,candidate=c,valid=int(good.sum()),Sony=vs,LROC=vl,SL=sl,triple=vs['pass_null'] and vl['pass_null'] and sl['pass_null']))
ts=tiles()
for i,tile in enumerate(ts):
    F={k:tile_fft(a,tile) for k,a in raw.items()}
    for band in plan['judge']['bands']:
        sl=fft_stats(F['Sony'],F['LROC'],band)[0]
        for c in raw:
            if c in ['Sony','LROC']:continue
            vs=fft_stats(F[c],F['Sony'],band)[0];vl=fft_stats(F[c],F['LROC'],band)[0]
            # Rotate in image coordinates, with detrending/window applied identically.
            n=tile['size'];y0=tile['y0'];x0=tile['x0'];sn=raw['Sony'][y0:y0+n,x0:x0+n];ln=raw['LROC'][y0:y0+n,x0:x0+n]
            tt=dict(size=n,x0=0,y0=0);vn=[fft_stats(F[c],tile_fft(np.rot90(sn,j),tt),band)[0] for j in [1,2,3]];nl=[fft_stats(F[c],tile_fft(np.rot90(ln,j),tt),band)[0] for j in [1,2,3]]
            tile_rows.append(dict(tile=i,band=band,candidate=c,Sony=vs,LROC=vl,SL=sl,null_Sony_max=max(map(abs,vn)),null_LROC_max=max(map(abs,nl)),pass_null=vs>max(map(abs,vn)) and vl>max(map(abs,nl))))
save('R7_red_external.json',dict(rows=rows,tiles=tile_rows,tile_list=ts,method=__doc__,limits=['Previous common geometry/calibration globally fitted','Overlapping tiles not independent samples','2D square support excludes outer limb; angular test covers edge','No selection based on this judge','Photographic comparison is retention: original wide lunar base already includes Sony pixels']))
for band in plan['judge']['bands']:
    for c in raw:
        if c in ['Sony','LROC']:continue
        a=[q for q in rows if q['band']==band and q['candidate']==c and q['parity']==1 and q['radius'][1]<=435];b=[q for q in tile_rows if q['band']==band and q['candidate']==c]
        print(band,c,'polarS',round(np.mean([q['Sony']['r'] for q in a]),4),'polarL',round(np.mean([q['LROC']['r'] for q in a]),4),'triples',sum(q['triple'] for q in a),'2DS',round(np.mean([q['Sony'] for q in b]),4),'2DL',round(np.mean([q['LROC'] for q in b]),4),'2Dnullpass',sum(q['pass_null'] for q in b),'/',len(b),flush=True)
