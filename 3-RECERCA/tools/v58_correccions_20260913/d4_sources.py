from common58 import *
import ast,time
from scipy.optimize import nnls
claim();tree=ast.parse((T/'d3_empirical_stars.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='extract_empirical');rad=32;yy,xx=np.mgrid[-rad:rad+1,-rad:rad+1];rr=np.hypot(xx,yy);X=np.stack([np.ones_like(xx),xx/rad,yy/rad,(xx/rad)**2,xx*yy/rad**2,(yy/rad)**2],axis=-1);ann=(rr>=16)&(rr<30);valid=rr<22;nodes=np.arange(-6,7,3);G=np.stack([np.exp(-((xx-a)**2+(yy-b)**2)/8.) for a in nodes for b in nodes],axis=-1);D=G[valid];exec(compile(ast.Module(body=[fn],type_ignores=[]),'empirical','exec'))
rows=json.loads((O/'D3_empirical_pilot.json').read_text());sel=[r for r in rows if r['repeat_AB'] or r['star']['independent_two_trains'] or (r['star']['Vmag']<9 and np.hypot(r['star']['x']-r['star']['pred'][0],r['star']['y']-r['star']['pred'][1])<6)];print('SELECTED',len(sel),flush=True)
# Preserve every existing 21 confirmed star, using its native location even if local background makes catalogue threshold fail.
for s in json.loads((V42/'cau/estrelles_v42.json').read_text())['estrelles']:
 if all(np.hypot(s['x']-r['star']['x'],s['y']-r['star']['y'])>10 for r in sel):sel.append(dict(star=s,prior_confirmed_V42=True))
C=O/'sources';C.mkdir(exist_ok=True);mask=np.zeros((7506,10551),bool);rep=dict(selected=sel,outputs={},method='Subtract nonnegative empirical stellar light fitted to 25 Gaussian basis functions and independent quadratic local background. No cloned pixels or noise. Footprint r<22 reserved as removed stellar signal; no claim of coronal detail underneath stars. Raw/photographic bases untouched.')
for tag,path in [('fusion',V42/'cau/fusion_total_v42.npy'),('vixen',R/'research/tools/v38_20260908/cau/vixen_total_v38.npy'),('sony',V42/'cau/sony_corrected_total_v42.npy')]:
 src=np.load(path,mmap_mode='r');out=np.lib.format.open_memmap(C/f'{tag}_starless.npy',mode='w+',dtype=src.dtype,shape=src.shape);out[:]=src;rrs=[]
 for i,row in enumerate(sel):
  s=row['star'];x,y=int(s['x']),int(s['y']);q=np.array(src[y-32:y+33,x-32:x+33],float)
  if q.shape!=(65,65,3) or not np.isfinite(q).all() or (q<=0).any():continue
  model=[];r=None
  for ch in range(3):
   comp,r=extract_empirical(q[...,ch]);comp[rr>=22]=0;out[y-32:y+33,x-32:x+33,ch]=(q[...,ch]-comp).astype(src.dtype);model.append(comp)
  np.savez_compressed(C/f'{tag}_star_{i:03d}.npz',component=np.stack(model,axis=-1).astype('float32'),xy=np.array([x,y]));rrs.append(dict(index=i,xy=[x,y],diagnostic=r));mask[y-32:y+33,x-32:x+33]|=rr<22
 out.flush();rep['outputs'][tag]=dict(source=str(path),output=str(C/f'{tag}_starless.npy'),stars=len(rrs),measurements=rrs);del src,out;print(tag,len(rrs),'written',flush=True)
# Physical limb source accepted in V51/V53, recomposed from per-frame optical support.
P=R/'research/tools/earthshine_v50_temporal_20260912/cau';z=np.load(P/'s4_recomposicio_box.npz');y0,y1,x0,x1=z['box'].astype(int);supN=np.load(P/'s4_support_new_box.npy');Dmin=z['Dmin'];m=np.load(V42/'cau/support_v42.npy');old=m[y0:y1,x0:x1].copy();use=supN&((~old)|(Dmin<6));m[y0:y1,x0:x1]|=supN
for tag in ['fusion','vixen']:
 a=np.load(C/f'{tag}_starless.npy',mmap_mode='r+');sub=np.array(a[y0:y1,x0:x1]);sub[use]=z['totN'][use];a[y0:y1,x0:x1]=sub;a.flush()
np.save(C/'support.npy',m);np.save(C/'star_footprints.npy',mask);rep['limb_source']=dict(file=str(P/'s4_recomposicio_box.npz'),box=[int(x0),int(y0),int(x1),int(y1)],pixels=int(use.sum()),support_added=int((supN&~old).sum()),criterion='same accepted S5 locus: new physical source where old missing or Dmin<6, not a new radial mask')
for tag in ['fusion','vixen','sony']:rep['outputs'][tag]['sha256']=sha(C/f'{tag}_starless.npy')
np.save(C/'base_G.npy',np.where(m,np.load(C/'fusion_starless.npy',mmap_mode='r')[...,1],0).astype('float32'));save('D4_sources.json',rep);print('SOURCE COMPLETE',len(sel),flush=True)
