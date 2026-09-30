"""Four-frame calibrated camera RGB pilot, before colour mixing and display.
Signed RAW radiance; no coronal additive offsets or coronal phi fields. One
positive CFA interpolation per subplane, all contributing pixels physically
valid and below 85% range. Never uses the old brightness-floor weights.
"""
from common50 import *
import sys,time,gc
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from b1_native import f2,comu,RUNS,COMMON_TO_FINAL,CAU36,B,MC,rawpy,cv2
from scipy.ndimage import map_coordinates
ctx=f2.Ctx(comu.Run.obre(str(RUNS['vixen'])));pos=json.loads((RUNS['vixen']/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((RUNS['vixen']/'4-rebuts/F2.2_coherencia.json').read_text())['k'];frames=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'];meta={m['stem']:m for m in frames if m['tren']=='vixen'}
inv=cv2.invertAffineTransform(COMMON_TO_FINAL);yy,xx=np.mgrid[Y0:Y0+N,X0:X0+N].astype(np.float32);rows=[]
for stem in ['572A2975','572A2993','572A2978','572A2996']:
 start=time.time();nom=stem+'.CR3';v=pos[nom];sx,sy=meta[stem]['native']['shift'];xm=xx-sx;ym=yy-sy;qx=inv[0,0]*xm+inv[0,1]*ym+inv[0,2];qy=inv[1,0]*xm+inv[1,1]*ym+inv[1,2];dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
 qmx=inv[0,0]*MC[0]+inv[0,1]*MC[1]+inv[0,2];qmy=inv[1,0]*MC[0]+inv[1,1]*MC[1]+inv[1,2];dmx=(qmx-ctx.CX)*ctx.k;dmy=(qmy-ctx.CY)*ctx.k;offx=v['lluna_dx']-(ctx.ca*dmx+ctx.sa*dmy);offy=v['lluna_dy']-(-ctx.sa*dmx+ctx.ca*dmy)
 rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']+offx).astype(np.float32);ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']+offy).astype(np.float32)
 with rawpy.imread(str(ctx.ruta[nom])) as rf:raw=rf.raw_image.astype(np.float32);wb=np.array(rf.daylight_whitebalance);wb/=wb[1]
 plans=ctx.plans(nom,v['exp']);num=np.zeros((N,N,3));cnt=np.zeros_like(num);var=np.zeros_like(num);quality=np.ones_like(num)
 for i,(pl,_) in plans.items():
  c=comu.IDX_CANAL[i];oy,ox=ctx.orig[i];mx=((rx-ox)*.5).astype(float);my=((ry-oy)*.5).astype(float);ix=np.floor(mx).astype(int);iy=np.floor(my).astype(int);fx=mx-ix;fy=my-iy;rp=raw[oy::2,ox::2];inside=(ix>=0)&(iy>=0)&(ix+1<rp.shape[1])&(iy+1<rp.shape[0]);assert inside.all();rn=(rp-ctx.cfg['pedestal_dn'])/(ctx.cfg['saturacio_dn']-ctx.cfg['pedestal_dn']);vp=ctx.valid[oy::2,ox::2];bad=np.zeros((N,N),bool);highest=np.zeros((N,N));g=np.zeros((N,N));vv=np.zeros((N,N));k=kq.get(nom,1);read=1.05 if v['exp']>=1 else 2.72;scale=k*ctx.wb[c]/(np.maximum(ctx.flat[oy::2,ox::2],1e-12)*v['exp']);noise=(np.maximum(rp-ctx.cfg['pedestal_dn'],0)/5.08+2*read**2)*scale**2
  for jy,jx,w in [(0,0,(1-fy)*(1-fx)),(0,1,(1-fy)*fx),(1,0,fy*(1-fx)),(1,1,fy*fx)]:
   q=rn[iy+jy,ix+jx];bad|=(q>=.85)|(vp[iy+jy,ix+jx]<=0)|~np.isfinite(pl[iy+jy,ix+jx]);highest=np.maximum(highest,q);g+=w*pl[iy+jy,ix+jx]*k;vv+=w*w*noise[iy+jy,ix+jx]
  z=np.clip((highest-.35)/.5,0,1);quality[...,c]=np.minimum(quality[...,c],np.where(bad,0,1-z*z*(3-2*z)));num[...,c]+=g;var[...,c]+=vv;cnt[...,c]+=1
 camera=num/cnt;variance=var/cnt**2;camera[quality<=0]=np.nan;variance[quality<=0]=np.nan
 np.savez_compressed(OUT/f'M0_camera_{stem}.npz',camera=camera.astype(np.float32),variance=variance.astype(np.float32),quality=quality.astype(np.float32))
 row=dict(stem=stem,raw=str(ctx.ruta[nom]),exp=v['exp'],shift=[sx,sy],daylight_wb=wb.tolist(),valid_channels=[int(np.sum(quality[...,c]>0)) for c in range(3)],seconds=time.time()-start);rows.append(row);print(row,flush=True);del raw,plans,num,cnt,var,quality,camera,variance;gc.collect()
save('M0_camera_inputs.json',dict(method=__doc__,frames=rows,scope='exploratory spectral identifiability; no photographic output'))
