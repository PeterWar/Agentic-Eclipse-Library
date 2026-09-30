"""Paired red source and smooth photographic-response pilot.
Both colours share captures and weights. Six nonnegative coefficients fit the
saved V55 photo against green and paired red-minus-green, even sectors only.
Missing red fraction is the positive part in Bernstein coefficient space;
the globally smooth response has no mark/sector masks or painted transition.
"""
from common import *
from spectral import *
from scipy.optimize import nnls
claim();z=np.load(OUT/'arrays/R0_paired_red.npz');base=np.load(OLD/'arrays/B11_repeatable_all.npz')['source'];contrast=z['contrast'];fraction=float(z['fraction']);old=np.load(OLD/'arrays/D10_candidate_rgb.npy').astype(np.int32);r,t=geometry();alpha=np.load(OLD54/'arrays/V53_lunar_alpha.npy');mask=np.load(OLD54/'arrays/V53_lunar_mask.npy');visible=(alpha>0)&(mask>0);domain=float(r[visible].max())
save('R1_protocol.json',dict(method=__doc__,domain=domain,fraction=fraction,fit='NNLS beta(r)G + mu(r)(Rpaired-Gpaired), degree2 Bernstein of(r/domain)^2; fixed16-64, even sectors r60-435, no Sony or marked regions.',increment='Bernstein coefficients max(beta*fraction-mu,0), applied to measured angular16-64 with12-96 skirts; same increment RGB; hidden pixels exact.',decision='Save evidence even if clipping; reject any clipping, negative response, inherited claim loss or new contour failure. R0 detector is not independently qualified yet. No PSB.',limits='Source red difference may retain scattered solar light; common captures/weights address temporal colour mixing only. No absolute CameraRaw response claim.'))
G,V=polar(base);C,W=polar(contrast);P,_=polar(old.mean(-1));a,c,p=[angular_band(q,16,64) for q in [G,C,P]];u=(RR[:,None]/domain)**2;bb=np.broadcast_to(np.stack([(1-u)**2,2*u*(1-u),u*u],-1),(*a.shape,3));train=sector_mask(60,435,0)&V&W;hold=sector_mask(60,435,1)&V&W;X=np.concatenate([a[...,None]*bb,c[...,None]*bb],-1);cf,res=nnls(X[train],p[train]);extra=np.maximum(cf[:3]*fraction-cf[3:],0);v=(r/domain)**2;b2=np.stack([(1-v)**2,2*v*(1-v),v*v],-1);gain=b2@extra
# Fill unavailable input values only for operator support, carry validity apart.
valid=np.isfinite(contrast);ix=distance_transform_edt(~valid,return_distances=False,return_indices=True);cc=contrast[tuple(ix)];rr=np.arange(0,domain+2,.5);nt=2880;th=np.arange(nt)*2*np.pi/nt;co=[CY+rr[:,None]*np.sin(th),CX+rr[:,None]*np.cos(th)];freq=np.fft.rfftfreq(nt)[None,:]*nt/(2*np.pi*np.maximum(rr[:,None],.25));u=np.clip((freq-1/96)/(1/64-1/96),0,1);v=np.clip((freq-1/16)/(1/12-1/16),0,1);H=(.5-.5*np.cos(np.pi*u))*(.5+.5*np.cos(np.pi*v));pol=map_coordinates(cc,co,order=3,mode='nearest');filtered=np.fft.irfft(np.fft.rfft(pol,axis=1)*H,n=nt,axis=1);pad=np.c_[filtered[:,-2:],filtered,filtered[:,:2]];delta0=map_coordinates(pad,[np.minimum(r/.5,len(rr)-1),t*nt/(2*np.pi)+2],order=3,mode='nearest');delta=np.rint(gain*delta0).astype(np.int32);delta[~visible]=0;new=old+delta[...,None];clip=(new.min(-1)<0)|(new.max(-1)>65535);fitrep=dict(coefficients=cf,extra_coefficients=extra,condition=float(np.linalg.cond(X[train])),heldout_r=corr((X*cf).sum(-1),p,hold),minmax=[int(new.min()),int(new.max())],clipped_pixels=int(clip.sum()),clipped_radii=[float(r[clip].min()),float(r[clip].max())] if clip.any() else None,hidden_exact=bool(np.array_equal(new[~visible],old[~visible])))
np.savez_compressed(OUT/'arrays/R1_red_source.npz',baseline=base,paired_GR=base+fraction*contrast,red=z['red'],paired_green=z['green']);np.savez_compressed(OUT/'arrays/R1_photo_pilot_unclipped.npz',candidate=new,delta=delta,gain=gain,filtered=delta0)
if not clip.any():np.save(OUT/'arrays/R1_candidate_rgb.npy',new.astype(np.uint16))
save('R1_red_photo_fit.json',fitrep);print('RED PHOTO',fitrep,flush=True)
# Producer completed before any external reference is loaded.
sony=np.load(ROOT/'output/earthshine_detail_20260911/B2_sony_reference.npz')['reference'];lc=np.load(ROOT/'research/tools/v42_20260910/cau/lroc_capa_v39_rgba.npy');bb=json.loads((ROOT/'output/v42_20260910/4-rebuts/P2b_rotacio.json').read_text())['lroc_bbox'];lr=np.full((N,N),np.nan);oy,ox=bb[1]-Y0,bb[0]-X0;lr[oy:oy+lc.shape[0],ox:ox+lc.shape[1]]=lc[...,:3].mean(-1);raw=dict(V55source=base,paired_GR=base+fraction*contrast,red=z['red'],Sony=sony,LROC=lr);pol={k:polar(a) for k,a in raw.items()};rows=[]
for band in [(8,16),(16,24),(24,40),(40,64),(64,96)]:
 B={k:angular_band(p[0],*band) for k,p in pol.items()}
 for lo,hi in [(60,250),(250,350),(350,410),(410,435),(435,449)]:
  m=sector_mask(lo,hi,1)&pol['Sony'][1]&pol['LROC'][1]
  for k in ['V55source','paired_GR','red']:
   ok=m&pol[k][1];row=dict(band=band,radius=[lo,hi],candidate=k,Sony=corr(B[k],B['Sony'],ok),LROC=corr(B[k],B['LROC'],ok));rows.append(row)
 for k in ['V55source','paired_GR','red']:
  v=[a for a in rows if a['band']==band and a['candidate']==k and a['radius'][1]<=435];print('RED SOURCE',band,k,'Sony',np.mean([a['Sony'] for a in v]),'LROC',np.mean([a['LROC'] for a in v]),flush=True)
save('R1_red_source_judge.json',dict(rows=rows,limits=['Independent Sony source, previous use acknowledged; no external fit','Angular support crosses training/heldout sectors','No new resolution or formal significance']))
