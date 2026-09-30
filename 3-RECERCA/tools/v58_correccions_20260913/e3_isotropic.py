from filters58 import *
claim();C=O/'filters';S=O/'sources';m=np.load(S/'support.npy');total=np.load(S/'fusion_starless.npy',mmap_mode='r');r,t=coords();del t
layers={'01':((2,4,8,16,32),'refined:achf',3.),'04':((1,2,4,8,16),'variants:micro1_16',1.5),'05':((2,4,8,16,32,48),'variants:fi2_48',3.),'06':((4,8,16,32,64),'variants:estructura4_64',3.)};old=json.loads((CAUF/'refined_detail_receipt.json').read_text());profiles=old['profiles'];var=json.loads((R/'research/tools/v30/cau/fine_variants_receipt.json').read_text())['variants'];sigmamap=np.load(CAUF/'resolution_sigma.npy',mmap_mode='r');all_sigmas=sorted(set(s for v in layers.values() for s in v[0]));rep={}
for ch in range(3):
 good=m&(total[...,ch]>0);x=np.log(np.maximum(total[...,ch],1e-8));x,frep=farcit_perfil_ln_A(x,good,r);w=np.ones((H,W),np.float32);p=profiles[str(ch)];scale=np.interp(np.log(np.maximum(r/RS,1e-5)),p['lnr_centres'],p['robust_contrast']).astype('float32');acc={k:np.zeros((H,W),np.float32) for k in layers}
 for sig in all_sigmas:
  band=x-normgauss(x,w,sig)
  for k,v in layers.items():
   if sig in v[0]:acc[k]+=band/len(v[0])
  log(f'channel{ch} sigma{sig}')
 for k in layers:np.save(C/f'iso_{k}_{ch}_tmp.npy',np.where(good,acc[k]/scale,np.nan).astype('float32'))
 del acc,x,good,w,band,scale;gc.collect()
wsup=m.astype('float32');ctx=h1_setup(r,m)
for k,(sigmas,ts,se) in layers.items():
 reals=[np.load(C/f'iso_{k}_{ch}_tmp.npy',mmap_mode='r') for ch in range(3)];d=np.zeros((H,W),np.float32)
 for y0 in range(0,H,256):d[y0:y0+256]=np.nan_to_num(np.nanmedian(np.stack([q[y0:y0+256] for q in reals]),axis=0),nan=0)
 kind,key=ts.split(':');sc=old['filters'][key]['scale_tanh'] if kind=='refined' else var[key]['scale_tanh'];mapped=(.5*np.tanh(d/max(sc,1e-6))).astype('float32');sm,_=sn_smooth(mapped,m,sigma=sigmamap);centered,hist=centre_rings(sm,m,r);a=np.clip(.5+centered,0,1);a[~m]=.5;den=gauss(wsup,se);b=.5+gauss((a-.5)*wsup,se)/np.maximum(den,1e-8);b[~m]=.5;u=np.round(np.clip(b,0,1)*65535).astype('uint16');np.save(C/f'{k}_u16.npy',u);np.save(C/f'{k}_float.npy',d);rep[k]=dict(sigmas=sigmas,scale_tanh=sc,external_sigma=se,H1=h1(b,m,ctx),H1_history=hist,sha256=sha(C/f'{k}_u16.npy'))
 from PIL import Image
 Image.fromarray((u[::4,::4]//257).astype('uint8')).save(O/'vistes'/f'E3_{k}_full.png');log(k+' DONE');del reals,d,mapped,sm,centered,a,b,u;gc.collect()
 # Only this run's temporary intermediates removed after durable final output.
 for ch in range(3):(C/f'iso_{k}_{ch}_tmp.npy').unlink()
save('E3_isotropic_filters.json',rep)
