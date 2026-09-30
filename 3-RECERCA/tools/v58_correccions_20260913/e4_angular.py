from filters58 import *
claim();C=O/'filters';S=O/'sources';r,t=coords();old=json.loads((CAUF/'gran_azimuthal_receipt.json').read_text());profiles=old['post_contrast_profiles'];mv=np.load(CAUF/'vixen_support.npy');ms=np.load(CAUF/'sony_support.npy');P=R/'research/tools/earthshine_v50_temporal_20260912/cau';z=np.load(P/'s4_recomposicio_box.npz');y0,y1,x0,x1=z['box'].astype(int);mv[y0:y1,x0:x1]|=np.load(P/'s4_support_new_box.npy');V=np.load(S/'vixen_starless.npy',mmap_mode='r')[...,1];SS=np.load(S/'sony_starless.npy',mmap_mode='r')[...,1];masks={'vixen':mv&np.isfinite(V)&(V>0),'sony':ms&np.isfinite(SS)&(SS>0)};m=masks['vixen']|masks['sony'];wv=np.load(V42/'cau/weight_vixen_v42.npy');wv=np.where(masks['sony'],wv,masks['vixen'].astype('float32'))*masks['vixen'];ws=(1-wv)*masks['sony'];sigmamap=np.load(CAUF/'resolution_sigma.npy',mmap_mode='r');bands={};keys={'03':0.,'03v30':4.,'07':8.}
for tag,a,mask in [('vixen',V,masks['vixen']),('sony',SS,masks['sony'])]:
 log('polar '+tag);p,valid,r0,nt=angular_polar(np.log(np.maximum(np.asarray(a),1e-8)),mask,r,t)
 for key,sr in keys.items():
  q=p if sr==0 else gaussian_filter1d(p*valid,sr,axis=0,mode='constant',cval=0)/np.maximum(gaussian_filter1d(valid,sr,axis=0,mode='constant',cval=0),1e-8);bands[tag,key]=back(q,mask,r,t,r0,nt).astype('float32');log(tag+' '+key)
 del p,valid,q;gc.collect()
scale=np.zeros((H,W),np.float32)
for tag,w in [('vixen',wv),('sony',ws)]:
 pr=profiles[tag];scale+=w*np.interp(np.log(np.maximum(r/RS,1e-5)),pr['lnr_centres'],pr['robust_contrast']).astype('float32')
ctx=h1_setup(r,m);rep={}
for key,sr in keys.items():
 d=wv*bands['vixen',key]+ws*bands['sony',key];d=np.where(m,d/np.maximum(scale,.002),0).astype('float32');mapped=(.5*np.tanh(d/old['scale_tanh'])).astype('float32');sm,_=sn_smooth(mapped,m,sigma=sigmamap);centered,hist=centre_rings(sm,m,r);a=np.clip(.5+centered,0,1);a[~m]=.5;u=np.round(a*65535).astype('uint16');u[~m]=32768;np.save(C/f'{key}_u16.npy',u);np.save(C/f'{key}_float.npy',d);rep[key]=dict(sigma_radial=sr,H1=h1(a,m,ctx),H1_history=hist,sha256=sha(C/f'{key}_u16.npy'));from PIL import Image;Image.fromarray((u[::4,::4]//257).astype('uint8')).save(O/'vistes'/f'E4_{key}_full.png');log(key+' DONE');del d,mapped,sm,centered,a,u;gc.collect()
np.save(C/'angular_support.npy',m);save('E4_angular_filters.json',rep)
