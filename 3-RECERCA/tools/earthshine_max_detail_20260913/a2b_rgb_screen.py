"""Valid support-aware replacement for A2 angular diagnostic, with 2D check.
A2 stacks/poses are valid; its cubic spline was contaminated by non-finite
exterior samples. A2 correlation zeros/NaN slopes are INVALID and not evidence.
"""
from common import *
from spectral import *
claim();plan=json.loads((OUT/'PLAN.json').read_text());z=np.load(OUT/'arrays/A2_color_stacks.npz');st={k:z[k] for k in z.files if not k.startswith('weight_')}
P={k:polar(v) for k,v in st.items()};rows=[];coeffs={}
for band in plan['judge']['bands_px']:
    B={k:angular_band(p[0],*band) for k,p in P.items()}
    for rlo,rhi in plan['judge']['radii']:
        for parity in [0,1]:
            mask=sector_mask(rlo,rhi,parity)
            for c in ['R','G1','G2','B']:
                good=mask&P['all_'+c][1]&P['all_G'][1]&P['fit_'+c][1]&P['test_'+c][1]&P['test_G'][1]
                rows.append(dict(band=band,radius=[rlo,rhi],parity=parity,channel=c,valid=int(good.sum()),r_same_G=corr(B['all_'+c],B['all_G'],good),r_temporal=corr(B['fit_'+c],B['test_'+c],good),r_temporal_G=corr(B['fit_'+c],B['test_G'],good),rms=float(np.std(B['all_'+c][good])),rms_G=float(np.std(B['all_G'][good]))))
    if band==[64,96]:
        mask=sector_mask(60,350,0);g1=B['fit_G1'][mask];g2=B['fit_G2'][mask];g=.5*(g1+g2);signal=np.mean(g1*g2)
        for c in ['R','B']:coeffs[c]=float(np.mean(B['fit_'+c][mask]*g)/signal)
tile_list=tiles();tile_stats=[]
for ti,t in enumerate(tile_list):
    ff={k:tile_fft(v,t) for k,v in st.items()}
    for band in plan['judge']['bands_px']:
        for c in ['R','G1','G2','B']:
            rt,aa,bb,ab=fft_stats(ff['fit_'+c],ff['test_'+c],band);rg=fft_stats(ff['fit_'+c],ff['test_G'],band)[0];rs=fft_stats(ff['all_'+c],ff['all_G'],band)[0]
            tile_stats.append(dict(tile=ti,band=band,channel=c,r_temporal=rt,r_temporal_G=rg,r_same_G=rs))
save('A2b_rgb_training_screen.json',dict(method=__doc__,rows=rows,tile_list=tile_list,tiles=tile_stats,color_texture_slopes_relative_G=coeffs,rule='64-96 tangential; training/even/r<350; G1xG2 auto noise debiasing only, common systematics remain.',supersedes='A2_rgb_training_screen.json INVALID due to global NaN spline contamination; inputs/stacks/diversity unaffected'))
for b in plan['judge']['bands_px']:
    for c in ['R','G1','G2','B']:
        a=[r for r in rows if r['band']==b and r['channel']==c and r['radius'][1]<=410 and r['parity']==1];ts=[r for r in tile_stats if r['band']==b and r['channel']==c]
        print('RGB',b,c,'r temporal G',round(np.mean([r['r_temporal_G'] for r in a]),4),'r temporal same',round(np.mean([r['r_temporal'] for r in a]),4),'r allG',round(np.mean([r['r_same_G'] for r in a]),4),'2D temporal G',round(np.mean([r['r_temporal_G'] for r in ts]),4),flush=True)
print('TEXTURE SLOPES',coeffs,flush=True)
