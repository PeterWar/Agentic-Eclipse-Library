"""Ordinary single-CFA radiance for all 88 sources, original texture geometry.
Confidence is separate from interpolation: no brightness-weighted radiance
interpolation. Retain negatives; admit only four valid unsaturated CFA samples.
Exact distance to invalid footprint squares is evaluated only near those squares.
Calibration, Sony LUT, field, clock/geometry and RGB-green convention inherited.
No rescaling/crop of final project, no RAW or previous cache overwrite.
"""
from pathlib import Path
import sys,json,math,hashlib,time
import numpy as np
from scipy.ndimage import maximum_filter
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from b1_native import *
from comu36 import lin_corr_sony
OUT=ROOT/'output/earthshine_detail_20260911';CACHE=OUT/'native';CACHE.mkdir(exist_ok=True)
assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']=='CODEX_EARTHSHINE_DETAIL_20260911'
fr=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'];checknames=[f'572A{n}' for n in range(2973,2979)]
if '--check-six' in sys.argv:fr=[m for m in fr if m['stem'] in checknames]
# Process each optical train independently; Sony supplies an external control.
fr.sort(key=lambda m:(m['tren']!='vixen',m['stem'] not in checknames,-m['exp'],m['stem']))
inv=cv2.invertAffineTransform(COMMON_TO_FINAL);yy,xx=np.mgrid[Y0:Y0+1400,X0:X0+1400].astype(np.float32)
lasttag=None;rows=[]
for count,m in enumerate(fr):
 tag=m['tren'];nom=m['nom'];fn=CACHE/(tag+'_'+m['stem']+'.npz');receipt=fn.with_suffix('.json')
 if fn.exists():
  row=json.loads(receipt.read_text());assert row['shift']==m['native']['shift'];assert row['source_native_sha256']==m['native']['sha256'];rows.append(row);continue
 if tag!=lasttag:
  ctx=f2.Ctx(comu.Run.obre(str(RUNS[tag])));pos=json.loads((RUNS[tag]/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((RUNS[tag]/'4-rebuts/F2.2_coherencia.json').read_text())['k'];meta=json.loads((CAU36/(tag+'_meta.json')).read_text())['frames'];fcorr,frep=B.flat_ripple_correction(ctx,tag);lasttag=tag
 group=m['grup'];gm=[mm for mm in meta if tag=='vixen' or mm['group']==group];j=next(i for i,mm in enumerate(gm) if mm['name']==nom);mm=gm[j];phis=np.load(CAU36/(group+'_G_phi.npy'),mmap_mode='r');phi_full=B.upsample(phis[j]);v=pos[nom];sx,sy=m['native']['shift'];xm=xx-sx;ym=yy-sy
 qx=inv[0,0]*xm+inv[0,1]*ym+inv[0,2];qy=inv[1,0]*xm+inv[1,1]*ym+inv[1,2];dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
 qmx=inv[0,0]*MC[0]+inv[0,1]*MC[1]+inv[0,2];qmy=inv[1,0]*MC[0]+inv[1,1]*MC[1]+inv[1,2];dmx=(qmx-ctx.CX)*ctx.k;dmy=(qmy-ctx.CY)*ctx.k;corrxy=(0.,0.)
 if group=='sony_B':
  delta=math.radians(8.10/60);ca,sa=math.cos(delta),math.sin(delta);dx,dy=ca*dx-sa*dy,sa*dx+ca*dy;dmx,dmy=ca*dmx-sa*dmy,sa*dmx+ca*dmy;corrxy=json.loads((HERE42/'cau/correccions_B.json').read_text()).get(nom,(0.,0.))
 offx=v['lluna_dx']-(ctx.ca*dmx+ctx.sa*dmy);offy=v['lluna_dy']-(-ctx.sa*dmx+ctx.ca*dmy)
 rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']+corrxy[0]+offx).astype(np.float32);ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']+corrxy[1]+offy).astype(np.float32)
 field=np.exp(-cv2.remap(phi_full,xm,ym,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE));del phi_full
 with rawpy.imread(ctx.ruta[nom]) as rr:raw=rr.raw_image.astype(np.float32)
 dark=ctx.dark(v['exp']);plans=ctx.plans(nom,v['exp']);num=np.zeros_like(xx);den=num.copy();vnum=num.copy();planes={};coverage=[]
 for i in range(4):
  if comu.IDX_CANAL[i]!=1:continue
  oy,ox=ctx.orig[i];rp=raw[oy::2,ox::2];flat=ctx.flat[oy::2,ox::2];pl=plans[i][0]
  if fcorr is not None:pl=pl*fcorr[i]
  mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32);span=ctx.cfg['saturacio_dn']-ctx.cfg['pedestal_dn'];rn=(rp-ctx.cfg['pedestal_dn'])/span;u=np.clip((rn-.35)/.5,0,1);quality=(1-u*u*(3-2*u)).astype(np.float32)
  ix=np.floor(mx).astype(int);iy=np.floor(my).astype(int);inside=(ix>=0)&(iy>=0)&(ix+1<rp.shape[1])&(iy+1<rp.shape[0]);safe_x=np.clip(ix,0,rp.shape[1]-2);safe_y=np.clip(iy,0,rp.shape[0]-2)
  bad=(rn>=.85)|(ctx.valid[oy::2,ox::2]<=0)|~np.isfinite(pl);invalid=bad[:-1,:-1]|bad[1:,:-1]|bad[:-1,1:]|bad[1:,1:];strict=inside&~invalid[safe_y,safe_x]
  near=maximum_filter(invalid,size=5,mode='constant',cval=1)[safe_y,safe_x]&strict;dist=np.ones_like(mx,dtype=float);d=np.ones(int(near.sum()));qx0=mx[near];qy0=my[near];ix0=ix[near];iy0=iy[near]
  for di in range(-2,3):
   for dj in range(-2,3):
    xi=ix0+dj;yi=iy0+di;ok=(xi>=0)&(yi>=0)&(xi<invalid.shape[1])&(yi<invalid.shape[0]);badcell=~ok|invalid[np.clip(yi,0,invalid.shape[0]-1),np.clip(xi,0,invalid.shape[1]-1)];ddx=np.maximum(np.maximum(xi-qx0,qx0-xi-1),0);ddy=np.maximum(np.maximum(yi-qy0,qy0-yi-1),0);d=np.minimum(d,np.where(badcell,np.hypot(ddx,ddy),1.))
  dist[near]=d;dist[~strict]=0;taper=dist*dist*(3-2*dist);q=cv2.remap(quality,mx,my,cv2.INTER_LINEAR)*strict*taper;assert not np.any((q>0)&~strict)
  g=(cv2.remap(pl*kq.get(nom,1),mx,my,cv2.INTER_LINEAR)+mm['offset_RGB'][1])*field
  read=(1.05 if v['exp']>=1 else 2.72) if tag=='vixen' else 1.22;rnvar=np.maximum(rp-ctx.cfg['pedestal_dn'],0)/(5.08 if tag=='vixen' else 3.41)+2*read**2
  if tag=='sony':
   ds=dark[oy::2,ox::2];derivative=(rp+.5-ds)*lin_corr_sony(rp+.5,ctx.cfg['pedestal_dn'],ctx.cfg['saturacio_dn'])-(rp-.5-ds)*lin_corr_sony(rp-.5,ctx.cfg['pedestal_dn'],ctx.cfg['saturacio_dn']);rnvar*=derivative**2
  scale=kq.get(nom,1)/(np.maximum(flat,1e-12)*v['exp'])
  if fcorr is not None:scale*=fcorr[i]
  rnvar*=scale**2;qx1=np.rint(mx*32)/32;qy1=np.rint(my*32)/32;vx=np.clip(np.floor(qx1).astype(int),0,rp.shape[1]-2);vy=np.clip(np.floor(qy1).astype(int),0,rp.shape[0]-2);fx=qx1-vx;fy=qy1-vy;var=np.zeros_like(xx,dtype=float)
  for di,dj,b in [(0,0,(1-fy)*(1-fx)),(0,1,(1-fy)*fx),(1,0,fy*(1-fx)),(1,1,fy*fx)]:var+=b*b*rnvar[vy+di,vx+dj]
  var*=field**2;num+=g*q;den+=q;vnum+=var*q*q;key=str(len(coverage)+1);planes['g'+key]=np.where(q>0,g,np.nan);planes['q'+key]=q.astype(np.float32);planes['variance'+key]=np.where(q>0,var,np.nan).astype(np.float32);coverage.append(dict(plane=i,valid=int((q>0).sum()),near_invalid=int(near.sum()),saturated_admitted=0))
  del pl,rnvar,var
 arr=dict(g=np.where(den>0,num/np.maximum(den,1e-30),np.nan),q=den/2,variance=np.where(den>0,vnum/np.maximum(den**2,1e-30),np.nan),**planes);np.savez_compressed(fn,**arr)
 row=dict(stem=m['stem'],tren=tag,exp=v['exp'],shift=[sx,sy],source_native_sha256=m['native']['sha256'],file=str(fn),planes=coverage,raw_path=str(ctx.ruta[nom]),raw_sha256=hashlib.file_digest(open(ctx.ruta[nom],'rb'),'sha256').hexdigest(),method=__doc__,Sony_B_rotation_arcmin=8.10 if group=='sony_B' else 0,Sony_B_star_correction=corrxy,group=group)
 receipt.write_text(json.dumps(row,indent=2));rows.append(row);print(count+1,len(fr),tag,m['stem'],'valid',int((den>0).sum()),flush=True)
 if m['stem'] in checknames:
  zz=np.load(ROOT/'output/earthshine_validation_20260911/full_epoch2_original_geometry/source_arrays.npz');comp={}
  for key in ['g','q','variance']:
   ref=zz[m['stem']+'_'+key];cur=arr[key];assert np.array_equal(np.isfinite(cur),np.isfinite(ref));diff=abs(cur[np.isfinite(cur)]-ref[np.isfinite(ref)]);comp[key]=float(diff.max());assert diff.max()==0,(m['stem'],key,diff.max())
  (CACHE/(m['stem']+'_equivalence.json')).write_text(json.dumps(comp))
 print('elapsed source complete',flush=True)
(OUT/('B0_six_check.json' if '--check-six' in sys.argv else 'B0_all_native.json')).write_text(json.dumps(dict(method=__doc__,frames=rows,frame_count=len(rows),complete88=len(rows)==88,original_geometry_preserved=True),indent=2));print('COMPLETE',len(rows),flush=True)
