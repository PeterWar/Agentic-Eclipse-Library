"""Independent Sony A/B coronal ROI using only CFA samples >15 sensor px from Moon.
No Vixen-derived inter-train fit or lunar correction; no product pixels written.
"""
from a4_sources import *
import math

def main():
 ns,fr=context();out=O/'sony_clean_judge';out.mkdir();ns.update(FLAT_CENTRE_YX={'sony':(2660.,4000.)},FLAT_SIGMA_PX=32.)
 definition(fr['sources']['common32']['copy'],'flat_ripple_correction',ns);definition(H/'s4_v51_core_comu38.py','upsample',ns)
 path=f12dirs['sony'];run=comu.Run.obre(str(path));ctx=f2.Ctx(run);pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((path/'4-rebuts/F2.2_coherencia.json').read_text())['k'];meta=json.loads((O/'sources_v36/cau/sony_meta.json').read_text())['frames'];corr=json.loads((H/'b2_v42_correccions_B.json').read_text());fcorr,_=ns['flat_ripple_correction'](ctx,'sony')
 box=[3077,4477,4677,6077];y0,y1,x0,x1=box;h,w=y1-y0,x1-x0;inv=cv2.invertAffineTransform(ns['COMMON_TO_FINAL']);yy,xx=np.ogrid[y0:y1,x0:x1];qx=(inv[0,0]*xx+inv[0,1]*yy+inv[0,2]).astype(np.float32);qy=(inv[1,0]*xx+inv[1,1]*yy+inv[1,2]).astype(np.float32);dx0=(qx-ctx.CX)*ctx.k;dy0=(qy-ctx.CY)*ctx.k
 reports={}
 for group in ['sony_A','sony_B']:
  frames=[m for m in meta if m['group']==group];phis={c:np.load(O/'sources_v36/cau'/f'{group}_{c}_phi.npy',mmap_mode='r') for c in ['R','G','B']};num=np.zeros((h,w,3),np.float32);den=num.copy();w2=num.copy();count=np.zeros((h,w),np.uint8)
  delta=0. if group=='sony_A' else math.radians(8.10/60);ca,sa=math.cos(delta),math.sin(delta);dx=(ca*dx0-sa*dy0).astype(np.float32);dy=(sa*dx0+ca*dy0).astype(np.float32)
  for j,m in enumerate(frames):
   n=m['name'];v=pos[n];cx,cy=corr.get(n,(0.,0.)) if group=='sony_B' else (0.,0.);rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']+cx).astype(np.float32);ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']+cy).astype(np.float32);mlx=v['sol_x']+cx+v['lluna_dx'];mly=v['sol_y']+cy+v['lluna_dy'];clean=(np.hypot(rx-mlx,ry-mly)-ctx.RL)>15;frameW=np.zeros_like(num);plans=ctx.plans(n,v['exp']);pmap={c:ns['upsample'](phis[c][j])[y0:y1,x0:x1] for c in phis}
   for i,(pl,wgt) in plans.items():
    c=comu.IDX_CANAL[i];oy,ox=ctx.orig[i]
    if fcorr is not None:pl=pl*fcorr[i]
    sy,sx=np.ogrid[:wgt.shape[0],:wgt.shape[1]];nativeclean=(np.hypot(2*sx+ox-mlx,2*sy+oy-mly)-ctx.RL)>15;wgt=wgt*nativeclean
    mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32);dd=cv2.remap(wgt,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*clean;nn=cv2.remap(pl*wgt*kq.get(n,1.),mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)*clean;nn+=m['offset_RGB'][c]*dd;nn*=np.exp(-pmap[{0:'R',1:'G',2:'B'}[c]]);num[...,c]+=nn;den[...,c]+=dd;frameW[...,c]+=dd
   w2+=frameW**2;count+=np.all(frameW>0,axis=-1);del plans,pmap;print('SONY_JUDGE',group,j+1,len(frames),flush=True)
  cam=np.where(den>0,num/np.maximum(den,1e-30),np.nan);_,rgb=comu.lluminancia(cam,run.matriu,run.color['guany']);valid=np.all((den>0)&np.isfinite(rgb)&(rgb>0),-1);np.savez(out/(group+'.npz'),rgb=rgb.astype(np.float32),den=den,neff=den**2/np.maximum(w2,1e-30),count=count,valid=valid,box=np.array(box));reports[group]={'names':[m['name'] for m in frames],'valid_pixels':int(valid.sum()),'min_samples':int(count[valid].min()) if valid.any() else 0,'sha256':sha(out/(group+'.npz'))}
 save(out/'COMPLETE.json',{'PASS':True,'groups':reports,'guard_sensor_px':15,'native_CFA_and_output_gate':True,'scope':'independent of new Vixen correction conditional on frozen geometry/calibration/offset/phi; no B3 train fit','limit':'No possible clean coverage through1.05R; partial azimuth1.06-1.09R; missing coverage cannot validate innermost limb'})

if __name__=='__main__':guard();main()
