from filters58 import *
claim();C=O/'filters';C.mkdir(exist_ok=True);S=O/'sources';a=np.load(S/'base_G.npy');m=np.load(S/'support.npy')&np.isfinite(a)&(a>0);r,t=coords();rep={}
def output(tag,q,display):
 lo,hi=display;assert np.isfinite(q[m]).all();u=np.round(np.clip(np.nan_to_num((q-lo)/(hi-lo),nan=0),0,1)*65535).astype('uint16');np.save(C/f'{tag}_u16.npy',u);np.save(C/f'{tag}_float.npy',np.where(m,q,np.nan).astype('float32'));rep[tag]=dict(display=display,sha256=sha(C/f'{tag}_u16.npy'))
 from PIL import Image
 Image.fromarray((u[::4,::4]//257).astype('uint8')).save(O/'vistes'/f'E1_{tag}_full.png');log(tag+' DONE')
log('global radial start');n,h,n2,xinfo,info=radial_v36(a,m,r,t)
for tag,q in [('P01_NRGF',n),('P01_NRGF_extrap',n2)]:
 d=json.loads((V42/'purs/receipts'/f'{tag}.json').read_text())['display'];output(tag,q,[d['black'],d['white']])
output('P02_RHEF',h,[0,1]);output('P02b_RHEF_ups0.35',upsilon(np.clip(h,0,1)),[0,1]);del n,h,n2;gc.collect()
for deg,tag in [(60,'P02c_RHEF_local60'),(30,'P02d_RHEF_local30')]:
 log('DR1 local '+str(deg));q=rhef_local(a,m,r,t,deg,deg/4)
 # Insufficient angular population at actual partial outer coverage keeps undefined data excluded, not displayed as black.
 bad=m&~np.isfinite(q);print('undefined',tag,int(bad.sum()),flush=True);np.save(C/f'{tag}_support.npy',m&np.isfinite(q));mm=m;m=m&np.isfinite(q);output(tag,q,[0,1]);m=mm;del q;gc.collect()
rep['source_sha256']=sha(S/'base_G.npy');rep['global_info']=info;rep['new_local_DR']=1.;save('E1_radial_filters.json',rep)
