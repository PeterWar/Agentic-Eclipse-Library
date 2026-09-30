"""Diagnostic independent Sony temporal subsets with exact V5 total-stack control. No product edit."""
from pathlib import Path
import sys,json,os,time,math,gc
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R/'3-RECERCA/tools/v97_refundacio_20260924/cadena_raw'))
import a4_sources as a4
a4.CID='CODEX_V112_ESTRELLES_I_ARTEFACTES_20260928'
from a4_sources import *
guard(); ns,fr=context();ns.update(FLAT_CENTRE_YX={'sony':(2660.,4000.)},FLAT_SIGMA_PX=32.)
definition(fr['sources']['common32']['copy'],'flat_ripple_correction',ns);definition(H/'s4_v51_core_comu38.py','upsample',ns)
OUT=R/'4-RESULTATS/v112_20260928/noise_v5';OUT.mkdir(exist_ok=True)
box=(3072,0,8192,3072);x0,y0,x1,y1=box;sl=(slice(y0,y1),slice(x0,x1));hh,ww=y1-y0,x1-x0
path=f12dirs['sony'];run=comu.Run.obre(str(path));pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((path/'4-rebuts/F2.2_coherencia.json').read_text())['k'];meta=json.loads((O/'sources_v36/cau/sony_meta.json').read_text())['frames'];byname={m['name']:m for m in meta}
corrB=json.loads((H/'b2_v42_correccions_B.json').read_text());report=dict(box=list(box),purpose='Diagnostic noise and repeatability only',groups={},matriu=np.asarray(run.matriu).tolist(),guany=np.asarray(run.color['guany']).tolist(),source_producer=sha(R/'3-RECERCA/tools/v108_20260926/flat2d_v2/b2_flat2d_v2.py'))
for group in ('sony_A','sony_B'):
 ctx=f2.Ctx(run); original=ctx.flat;fcorr,frep=ns['flat_ripple_correction'](ctx,'sony');flat=R/f'4-RESULTATS/v108_20260926/flat2d_v5/flat2d/SONYTOT_{group[-1]}_flat2d_v5.npz';C=np.load(flat)['C'];ctx.flat=(original*C).astype(np.float32);del original,C
 inv=cv2.invertAffineTransform(ns['COMMON_TO_FINAL']);yy,xx=np.ogrid[y0:y1,x0:x1]
 qx=(inv[0,0]*xx+inv[0,1]*yy+inv[0,2]).astype(np.float32);qy=(inv[1,0]*xx+inv[1,1]*yy+inv[1,2]).astype(np.float32)
 dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k;del qx,qy
 if group=='sony_B':
  rad=math.radians(8.10/60);co,si=math.cos(rad),math.sin(rad);dx,dy=(co*dx-si*dy).astype(np.float32),(si*dx+co*dy).astype(np.float32)
 nums=[np.zeros((hh,ww,3),np.float32) for _ in range(3)];dens=[np.zeros((hh,ww,3),np.float32) for _ in range(3)]
 names=[m['name'] for m in meta if m['group']==group];phis={c:np.load(O/'sources_v36/cau'/f'{group}_{c}_phi.npy',mmap_mode='r') for c in ('R','G','B')};frames=[]
 for j,name in enumerate(names):
  m=byname[name];tt=m['t'];cut=18 if group=='sony_A' else 70;lo=28 if group=='sony_A' else 80;h=1 if tt<=cut else 2;assert h==1 or tt>=lo
  v=pos[name];k=kq.get(name,1.0);cx_,cy_=corrB.get(name,(0.,0.)) if group=='sony_B' else (0.,0.)
  rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']+cx_).astype(np.float32);ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']+cy_).astype(np.float32)
  vv=dict(v);vv['sol_x']+=cx_;vv['sol_y']+=cy_;fl=f2.mascara_lluna(ctx,vv,rx,ry);plans=ctx.plans(name,v['exp'])
  for i,(pl,w) in plans.items():
   c=comu.IDX_CANAL[i];oy,ox=ctx.orig[i]
   if fcorr is not None:pl=pl*fcorr[i]
   mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32)
   dd=cv2.remap(w,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*fl;nn=cv2.remap(pl*w*k,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*fl
   b=float(m['offset_RGB'][c])
   if b!=0:nn+=b*dd
   phi=ns['upsample'](phis[('R','G','B')[c]][j]);nn*=np.exp(-phi[sl]);del phi
   nums[0][...,c]+=nn;dens[0][...,c]+=dd;nums[h][...,c]+=nn;dens[h][...,c]+=dd
   del nn,dd,mx,my,pl,w
  frames.append(dict(name=name,half=h,t=tt,exp=v['exp'],sha256=sha(ctx.ruta[name])));del plans,rx,ry,fl
  ctx._dk.clear();gc.collect();print(group,j+1,len(names),name,flush=True)
 cam=np.where(dens[0]>0,nums[0]/np.maximum(dens[0],1e-20),np.nan);_,total=comu.lluminancia(cam,run.matriu,run.color['guany']);total=total.astype(np.float32);del cam
 refp=R/('4-RESULTATS/v108_20260926/flat2d_v5/apilats/sony_A_total.npy' if group=='sony_A' else '4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_total_v42.npy');ref=np.load(refp,mmap_mode='r')[sl];ok=np.isfinite(ref)&np.isfinite(total);exact=bool(np.array_equal(total,ref,equal_nan=True))
 info=dict(flat_sha256=sha(flat),frames=frames,total_exact=exact,max_abs_difference=float(np.max(abs(total[ok]-ref[ok]))),relative_p99=float(np.percentile(abs(total[ok]/ref[ok]-1),99)),reference=str(refp),ripple=frep)
 # Strict control first. Preserve a failed receipt; never estimate from a mismatched reconstruction.
 report['groups'][group]=info;save(OUT/'CONTROL.json',report);assert exact,info
 del total,ref,ok,nums[0],dens[0]
 for h in (0,1):
  cam=np.where(dens[h]>0,nums[h]/np.maximum(dens[h],1e-20),np.nan).astype(np.float32);_,total=comu.lluminancia(cam,run.matriu,run.color['guany']);dest=OUT/f'{group}_{h+1}';dest.mkdir(exist_ok=False)
  np.save(dest/'cam_rgb.npy',cam);np.save(dest/'den_rgb.npy',dens[h]);np.save(dest/'G.npy',total[...,1].astype(np.float32));del cam,total
 del ctx,nums,dens,fcorr,dx,dy;gc.collect()
report['complete']=True;save(OUT/'COMPLETE.json',report);print('COMPLETE',flush=True)
