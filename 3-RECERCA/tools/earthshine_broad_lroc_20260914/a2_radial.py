from pathlib import Path
import numpy as np,json
from scipy.ndimage import gaussian_filter,gaussian_filter1d
from PIL import Image,ImageDraw
R=Path.cwd(); O=R/'output/earthshine_broad_lroc_20260914'
S={
 'V49_Pere':np.load(R/'output/earthshine_v49_pere_reveal_20260912/A0_Pere_moon_RGB16.npy').mean(-1),
 'V53':np.load(R/'research/tools/earthshine_v50_temporal_20260912/cau/lun_rgb_vel_u16.npy').mean(-1),
 'V68':np.load(R/'output/v68_artefactes_20260914/arrays/B10_photo_pilot.npz')['candidate'].mean(-1),
 'LROC':np.load(R/'output/v68_lroc_revisio_20260914/arrays/L62_exact_psb.npz')['rgb'].mean(-1),
 'preCR':np.load(R/'research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy').mean(-1),
 'Sony':np.load(R/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'],
 'Vixen':np.load(R/'output/earthshine_v56_three_routes_20260913/arrays/R5_sources.npz')['Gclean']}
y,x=np.mgrid[:1400,:1400];r=np.hypot(x-699.568111973117,y-699.6475341408573);theta=np.arctan2(y-699.6475341408573,x-699.568111973117)%(2*np.pi)
mark=(x>=550)&(x<723)&(y>=902)&(y<1048);guard=(x>=500)&(x<773)&(y>=852)&(y<1098)
valid=(r>100)&(r<400);fit=valid&~guard;local=(x>=462)&(x<792)&(y>=833)&(y<1103)&(r<400)
def radial(a):
 q=gaussian_filter(np.nan_to_num(a),8);bins=np.arange(0,500,4);bc=bins[:-1]+2
 p=np.array([np.median(q[(r>=lo)&(r<hi)&~guard]) for lo,hi in zip(bins[:-1],bins[1:])]);p=gaussian_filter1d(p,2)
 return q-np.interp(r,bc,p)
def corr(a,b,m):
 a=a[m]-a[m].mean();b=b[m]-b[m].mean();return float(np.sum(a*b)/np.sqrt(np.sum(a*a)*np.sum(b*b)))
D={k:radial(v) for k,v in S.items()}; rows=[]
for k,a in D.items():
 sd=np.std(a[fit]);rows.append(dict(name=k,matched_radial_mark_median=float(np.median(a[mark])),fit_sigma=float(sd),mark_standardized=float(np.median(a[mark])/sd),corr_sony_mark=corr(a,D['Sony'],mark),corr_vixen_mark=corr(a,D['Vixen'],mark),corr_sony_all=corr(a,D['Sony'],fit)))
pan=Image.new('RGB',(600*4,544*2),'#171717');dr=ImageDraw.Draw(pan)
for j,(k,a) in enumerate(D.items()):
 sd=np.std(a[fit]);z=np.clip(.5+a/(4*sd),0,1);im=Image.fromarray(np.uint8(z[833:1103,462:792]*255+.5)).convert('RGB');xx=j%4*600;yy=j//4*544;pan.paste(im.resize((600,490)),(xx,yy+44));dr.text((xx+8,yy+8),k+' | radial matched | +/-2 global sigma',fill='white')
pan.save(O/'vistes/A2_radial_matched.png');np.savez_compressed(O/'arrays/A2_radial.npz',**D)
(O/'A2_radial.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows,indent=2))
