"""Assembled SOURCE diagnostic for the boundary-trained empirical transfer.
Only the 21 completely observed native fields participate; no long-frame
donor completion or transfer assumption. This does NOT produce V50 or a PSB.
The closest edge is displayed explicitly but remains outside qualification.
"""
from common50 import *
from scipy.ndimage import gaussian_filter,map_coordinates
from PIL import Image,ImageDraw
import gc,time
SRC=ROOT/'output/earthshine_native_psf_20260911';fit=json.loads((OUT/'I1_fit.json').read_text());p=np.array(fit['models']['real']['p']);sig=np.array(fit['plan']['sigmas']);stems=fit['plan']['training']+fit['plan']['reserved']
frames=[m for m in json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/B1_inputs.json').read_text())['frames'] if m['tren']=='vixen'];idx={m['stem']:i for i,m in enumerate(frames)}
G=np.load(SRC/'compositor_cache/G.npy',mmap_mode='r');W=np.load(SRC/'compositor_cache/W.npy',mmap_mode='r');edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
yy,xx=np.mgrid[:N,:N];den=np.zeros((N,N));num=den.copy();scnum=den.copy();reports=[]
for stem in stems:
 t=time.time();z=np.load(NATIVE/f'D0_native_field_{stem}.npz');g=z['g'].astype(float);assert np.all(z['valid']);vv,uu=np.mgrid[:g.shape[0],:g.shape[1]];u=uu+int(z['u0']);v=vv+int(z['v0']);nx=1+u+v;ny=u-v;J=z['native_to_world'];origin=z['world_origin'];x=origin[0]+J[0,0]*nx+J[0,1]*ny;y=origin[1]+J[1,0]*nx+J[1,1]*ny;r=np.hypot(x-CX,y-CY);a=np.arctan2(y-CY,x-CX)%(2*np.pi);d=r-np.interp(a,np.arange(len(edge))*2*np.pi/len(edge),edge,period=2*np.pi)
 b=np.load(OUT/f'G0_features_{stem}.npz')['deep_plane'];contrast=g-b[0]-b[1]*(x-CX)/455-b[2]*(y-CY)/455;tt=np.clip(d+.5,0,1);donor=contrast*tt*tt*(3-2*tt);parity=nx%2;scatter=np.zeros_like(g)
 for par in [0,1]:
  donorhalf=2*np.where(parity!=par,donor,0);pred=np.zeros_like(g)
  for c,s in zip(p,sig):
   if c:pred+=c*gaussian_filter(donorhalf,s/np.sqrt(2),mode='reflect',truncate=6)
  scatter[parity==par]=pred[parity==par]
 # Reproduce actual I1 cell means to guard parity/field construction.
 use=(r>=260)&(r<458)&(x>=0)&(x<N)&(y>=0)&(y<N);cell=np.floor(y[use]/STEP).astype(int)*NC+np.floor(x[use]/STEP).astype(int);ids=2*cell+parity[use];unique,index,count=np.unique(ids,return_inverse=True,return_counts=True);red=np.bincount(index,weights=scatter[use])/count;target=np.load(OUT/f'I1_real_{stem}.npz')['scatter'];err=float(np.max(abs(red[count>=3]-target)));assert err<1e-8,err
 native=np.stack([xx-origin[0],yy-origin[1]],-1)@np.linalg.inv(J).T;ru=(native[...,0]+native[...,1]-1)/2-int(z['u0']);rv=(native[...,0]-native[...,1]-1)/2-int(z['v0']);assert min(ru.min(),rv.min())>=0
 reg=map_coordinates(scatter,[rv,ru],order=1,mode='nearest');i=idx[stem];w=W[i].astype(float);num+=w*G[i];scnum+=w*reg;den+=w
 np.savez_compressed(OUT/f'I4_registered_{stem}.npz',scatter=reg.astype(np.float32))
 last=(d>=-6)&(d<-.5);strict=(d>=-6)&(d<-2);corrected=g-scatter
 reports.append(dict(stem=stem,cell_reproduction_max=err,last_G=np.percentile(corrected[last],[5,50,95]).tolist(),last_negative_fraction=float(np.mean(corrected[last]<0)),strict_G=np.percentile(corrected[strict],[5,50,95]).tolist()));print(stem,'DONE',round(time.time()-t,2),flush=True);del z,g,scatter;gc.collect()
old=num/np.maximum(den,1e-30);sc=scnum/np.maximum(den,1e-30);new=old-sc;rr=np.hypot(xx-CX,yy-CY);gauge=float(np.median(sc[rr<350]));new_display=new+gauge
np.savez_compressed(OUT/'I4_short_source.npz',baseline=old,scatter=sc,corrected=new,denominator=den,display_gauge=gauge)
def picture(g):
 v=.2+.045*np.arcsinh((g-528.312744140625)/20);return Image.fromarray(np.rint(np.clip(v,0,1)*255).astype(np.uint8)).convert('RGB')
before=picture(old);after=picture(new_display);canvas=Image.new('RGB',(1600,835));canvas.paste(before.resize((800,800)),(0,35));canvas.paste(after.resize((800,800)),(800,35));draw=ImageDraw.Draw(canvas);draw.text((12,10),'Observed short-source stack',fill='white');draw.text((812,10),'Empirical solar-transfer subtraction (DIAGNOSTIC)',fill='white');canvas.save(OUT/'I4_source_comparison.png')
for label,box in {'top':(450,170,950,390),'right':(1030,400,1260,1000),'bottom':(430,1010,960,1260)}.items():
 a=before.crop(box);b=after.crop(box);c=Image.new('RGB',(a.width*2,a.height));c.paste(a,(0,0));c.paste(b,(a.width,0));c.save(OUT/f'I4_{label}.png')
save('I4_native_preview.json',dict(method=__doc__,frames=reports,display_gauge=gauge,regions={f'{lo}_{hi}':dict(before=np.percentile(old[(rr>=lo)&(rr<hi)],[5,50,95]).tolist(),after=np.percentile(new_display[(rr>=lo)&(rr<hi)],[5,50,95]).tolist(),negative_fraction=float(np.mean(new[(rr>=lo)&(rr<hi)]<0))) for lo,hi in [(0,350),(415,435),(435,449),(449,454),(454,460)]},status='Source diagnostic only; no photographic preservation or full-limb qualification'))
