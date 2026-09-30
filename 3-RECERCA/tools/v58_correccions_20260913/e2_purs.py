from filters58 import *
claim();C=O/'filters';C.mkdir(exist_ok=True);S=O/'sources';a=np.load(S/'base_G.npy');m=np.load(S/'support.npy')&np.isfinite(a)&(a>0);r,t=coords();full=np.ones_like(m);del t;rep={};ent,fr=farcit_perfil(a,m,r)
for tag in ['P03_MGN','P04_WOW','P05_WOW_bilateral']:
 log(tag+' start')
 if tag=='P03_MGN':q=mgn(np.maximum(ent,0),full,limits=[float(a[m].min()),float(a[m].max())])
 elif tag=='P04_WOW':q=wow(ent,full,11,False)
 else:
  entA,frA=farcit_perfil_A(a,m,r);q=wow(entA,full,11,True);del entA
 d=json.loads((V42/'purs/receipts'/f'{tag}.json').read_text())['display'];lo,hi=d['black'],d['white'];assert np.isfinite(q[m]).all();u=np.round(np.clip(np.where(m,(q-lo)/(hi-lo),0),0,1)*65535).astype('uint16');np.save(C/f'{tag}_u16.npy',u);np.save(C/f'{tag}_float.npy',np.where(m,q,np.nan).astype('float32'));rep[tag]=dict(display=[lo,hi],sha256=sha(C/f'{tag}_u16.npy'))
 from PIL import Image
 Image.fromarray((u[::4,::4]//257).astype('uint8')).save(O/'vistes'/f'E2_{tag}_full.png');log(tag+' DONE');del q,u;gc.collect()
rep['fill_B']=fr;rep['fill_A']=frA;save('E2_purs_filters.json',rep)
