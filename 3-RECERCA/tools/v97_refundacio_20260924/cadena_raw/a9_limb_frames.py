"""Collect per-frame calibrated native camera RGB numerators on fixed lunar ROI.
No bias correction, presentation mask or astronomical source is fabricated here.
"""
from a4_sources import *

def collect():
 ns,fr=context();O2=O/'limb_frames';O2.mkdir()
 ns.update(FLAT_CENTRE_YX={'sony':(2660.,4000.)},FLAT_SIGMA_PX=32.)
 definition(fr['sources']['common32']['copy'],'flat_ripple_correction',ns);definition(H/'s4_v51_core_comu38.py','upsample',ns)
 path=f12dirs['vixen'];run=comu.Run.obre(str(path));ctx=f2.Ctx(run);pos=json.loads((path/'4-rebuts/F1.3_registre.json').read_text())['fotogrames'];kq=json.loads((path/'4-rebuts/F2.2_coherencia.json').read_text())['k'];meta=json.loads((O/'sources_v36/cau/vixen_meta.json').read_text())['frames'];names=[m['name'] for m in meta]
 hold=json.loads((O/'QA_FROZEN.json').read_text())['development_validation']['new_holdout'];assert set(hold)<=set(names),set(hold)-set(names)
 box=[3077,4477,4677,6077];y0,y1,x0,x1=box;h,w=y1-y0,x1-x0;nF=len(names)
 shape=(nF,h,w,3);N=np.lib.format.open_memmap(O2/'numerator.npy',mode='w+',dtype='float32',shape=shape);Wg=np.lib.format.open_memmap(O2/'weight.npy',mode='w+',dtype='float32',shape=shape);Ds=np.lib.format.open_memmap(O2/'distance_model.npy',mode='w+',dtype='float32',shape=(nF,h,w))
 phis={c:np.load(O/'sources_v36/cau'/f'vixen_{c}_phi.npy',mmap_mode='r') for c in ['R','G','B']};fcorr,_=ns['flat_ripple_correction'](ctx,'vixen')
 inv=cv2.invertAffineTransform(ns['COMMON_TO_FINAL']);yy,xx=np.mgrid[y0:y1,x0:x1].astype(np.float32);qx=inv[0,0]*xx+inv[0,1]*yy+inv[0,2];qy=inv[1,0]*xx+inv[1,1]*yy+inv[1,2];dx=(qx-ctx.CX)*ctx.k;dy=(qy-ctx.CY)*ctx.k
 info=[];t0=time.monotonic()
 for j,n in enumerate(names):
  v=pos[n];k=kq.get(n,1.);m=meta[j];rx=(ctx.ca*dx+ctx.sa*dy+v['sol_x']).astype(np.float32);ry=(-ctx.sa*dx+ctx.ca*dy+v['sol_y']).astype(np.float32);mlx=v['sol_x']+float(v['lluna_dx']);mly=v['sol_y']+float(v['lluna_dy']);Ds[j]=(np.hypot(rx-mlx,ry-mly)-ctx.RL).astype(np.float32)
  N[j]=0;Wg[j]=0;plans=ctx.plans(n,v['exp']);pmap={c:ns['upsample'](phis[c][j])[y0:y1,x0:x1] for c in phis}
  for i,(pl,wgt) in plans.items():
   c=comu.IDX_CANAL[i];oy,ox=ctx.orig[i]
   if fcorr is not None:pl=pl*fcorr[i]
   mx=((rx-ox)*.5).astype(np.float32);my=((ry-oy)*.5).astype(np.float32);dd=cv2.remap(wgt,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);nn=cv2.remap(pl*wgt*k,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);b=float(m['offset_RGB'][c])
   if b!=0:nn=nn+b*dd
   nn=nn*np.exp(-pmap[{0:'R',1:'G',2:'B'}[c]]);N[j,...,c]+=nn;Wg[j,...,c]+=dd
  info.append({'name':n,'time':m['t'],'exposure':v['exp'],'holdout':n in hold,'lluna_dx':v['lluna_dx'],'lluna_dy':v['lluna_dy'],'k':k})
  del plans,pmap,rx,ry
  if j%10==0 or j==nF-1:print('LIMB_FRAME',j+1,nF,round(time.monotonic()-t0,1),flush=True)
 for a in [N,Wg,Ds]:a.flush()
 save(O2/'METADATA.json',{'box_y0y1x0x1':box,'shape':list(shape),'frames':info,'matrix':run.matriu,'gain':run.color['guany'],'radius_model':ctx.RL,'common_to_final':ns['COMMON_TO_FINAL'],'distances':'relative to modelled radius, not a binary apparent-limb validity','stage':'per-frame native balanced CFA RGB, after frozen offsets/phi, before lunar bias correction','holdout_limitation':'Conditional on historical calibration/registration/phi, not independent of entire pipeline','QA_sha256':sha(O/'QA_FROZEN.json')})
 rows=[{'name':name,'sha256':sha(O2/name)} for name in ['numerator.npy','weight.npy','distance_model.npy','METADATA.json']];save(O2/'COMPLETE.json',{'PASS':True,'files':rows,'seconds':time.monotonic()-t0});print('LIMB_COMPLETE',flush=True)

if __name__=='__main__':guard();collect()
