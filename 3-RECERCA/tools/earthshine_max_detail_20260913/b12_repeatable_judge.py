"""Fixed source-only external judge; all candidates retained, no model edits.
Sony green alone is independent from Vixen candidates. LROC reference is a
second, historical pattern check; no external pixels in producer.
"""
from common import *
from spectral import *
import sys
claim();cand=np.load(OUT/'arrays/A3_rgb_candidates.npz');raw={k[4:]:cand[k] for k in cand.files if k.startswith('all_')}
fpn='--fpn' in sys.argv
fpn67='--fpn67' in sys.argv
hetero='--hetero' in sys.argv
rgbfpn='--rgb-fpn' in sys.argv
fullsafe='--full-safe' in sys.argv
photo='--photo' in sys.argv
if fpn:
    a=np.load(OUT/'arrays/B3_G_all.npz');b=np.load(OUT/'arrays/B3_G_train.npz')
    raw={'G_baseline':a['raw_baseline'],'FPN_all':a['source'],'FPN_train':b['source']}
if fpn67:
    a=np.load(OUT/'arrays/B3_G67_all.npz');b=np.load(OUT/'arrays/B3_G67_robust_all.npz');c=np.load(OUT/'arrays/B3_G67_robust_train.npz')
    raw={'G_baseline67':a['raw_baseline'],'FPN67':a['source'],'FPN67_covariance':b['source'],'FPN67_covariance_train':c['source']}
if hetero:
    a=np.load(OUT/'arrays/B3_G67_robust_all.npz');b=np.load(OUT/'arrays/B3_G67_robust_hetero_all.npz');c=np.load(OUT/'arrays/B3_G67_robust_hetero_train.npz')
    raw={'G_baseline67':a['raw_baseline'],'FPN_covariance':a['source'],'FPN_frame_error':b['source'],'FPN_frame_error_train':c['source']}
if rgbfpn:
    zz=np.load(OUT/'arrays/A5_color_after_fpn.npz');raw={k:zz[k] for k in zz.files}
if fullsafe:
    a=np.load(OUT/'arrays/B3_G67_robust_all.npz');b=np.load(OUT/'arrays/B3_G67_robust_hetero_all.npz');c=np.load(OUT/'arrays/B3_G67_robust_hetero_full_safe_all.npz')
    raw={'G_baseline67':a['raw_baseline'],'FPN_low_error':b['source'],'FPN_total_error':c['source']}
if photo:
    raw={'V54':np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/D1_candidate_rgb.npy').mean(-1),'D0_photo':np.load(OUT/'arrays/D0_candidate_rgb.npy').mean(-1)}
if '--repeatable' in sys.argv:
    q=np.load(OUT/'arrays/B11_repeatable_all.npz');raw={'baseline':q['raw_baseline'],'repeatable':q['source']}
raw['G67']=np.load(ROOT/'output/earthshine_v54_detail_20260913/arrays/B1_stacks.npz')['all']
raw['Sony']=np.load(ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference']
l=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];lr=np.full((N,N),np.nan);oy,ox=bb[1]-Y0,bb[0]-X0;lr[oy:oy+l.shape[0],ox:ox+l.shape[1]]=l[...,:3].mean(-1);raw['LROC']=lr
plan=json.loads((OUT/'PLAN.json').read_text());rows=[];tile_rows=[];P={k:polar(a) for k,a in raw.items()}
def compare(a,b,m):
    val=corr(a,b,m);null=[corr(a,np.roll(b,NT*j//12,axis=1),m) for j in range(1,12)]
    return dict(r=val,null_max=float(np.nanmax(np.abs(null))),pass_null=val>np.nanmax(np.abs(null)))
for band in plan['judge']['bands_px']:
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
    for band in plan['judge']['bands_px']:
        sl=fft_stats(F['Sony'],F['LROC'],band)[0]
        for c in raw:
            if c in ['Sony','LROC']:continue
            vs=fft_stats(F[c],F['Sony'],band)[0];vl=fft_stats(F[c],F['LROC'],band)[0]
            # Rotate in image coordinates, with detrending/window applied identically.
            n=tile['size'];y0=tile['y0'];x0=tile['x0'];sn=raw['Sony'][y0:y0+n,x0:x0+n];ln=raw['LROC'][y0:y0+n,x0:x0+n]
            tt=dict(size=n,x0=0,y0=0);vn=[fft_stats(F[c],tile_fft(np.rot90(sn,j),tt),band)[0] for j in [1,2,3]];nl=[fft_stats(F[c],tile_fft(np.rot90(ln,j),tt),band)[0] for j in [1,2,3]]
            tile_rows.append(dict(tile=i,band=band,candidate=c,Sony=vs,LROC=vl,SL=sl,null_Sony_max=max(map(abs,vn)),null_LROC_max=max(map(abs,nl)),pass_null=vs>max(map(abs,vn)) and vl>max(map(abs,nl))))
save('B12_repeatable_external.json' if '--repeatable' in sys.argv else 'D1_photo_retention.json' if photo else 'B9_total_error_external.json' if fullsafe else 'A6_RGB_FPN_external.json' if rgbfpn else 'B8_frame_error_external.json' if hetero else 'B6_fpn67_external.json' if fpn67 else 'B4_fpn_full_external.json' if fpn else 'A4_external_judge.json',dict(rows=rows,tiles=tile_rows,tile_list=ts,method=__doc__,limits=['Previous common geometry/calibration globally fitted','Overlapping tiles not independent samples','2D square support excludes outer limb; angular test covers edge','No selection based on this judge','Photographic comparison is retention: original wide lunar base already includes Sony pixels']))
for band in plan['judge']['bands_px']:
    for c in raw:
        if c in ['Sony','LROC']:continue
        a=[q for q in rows if q['band']==band and q['candidate']==c and q['parity']==1 and q['radius'][1]<=435];b=[q for q in tile_rows if q['band']==band and q['candidate']==c]
        print(band,c,'polarS',round(np.mean([q['Sony']['r'] for q in a]),4),'polarL',round(np.mean([q['LROC']['r'] for q in a]),4),'triples',sum(q['triple'] for q in a),'2DS',round(np.mean([q['Sony'] for q in b]),4),'2DL',round(np.mean([q['LROC'] for q in b]),4),'2Dnullpass',sum(q['pass_null'] for q in b),'/',len(b),flush=True)
