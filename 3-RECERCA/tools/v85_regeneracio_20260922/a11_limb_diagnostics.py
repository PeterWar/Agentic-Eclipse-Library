"""Training-only moving-edge residuals against independent same-sky contributions.
No candidate selection on held-out frames; no pixels of the product are changed.
"""
from a4_sources import *
from scipy.ndimage import gaussian_filter1d

def old_tables():
 table=json.loads((H/'v38_limb_round1/cau/correccio_vora_lunar.json').read_text())['taula']
 a1=json.loads((H/'v38_limb_round1/receipts/A1_franja_font.json').read_text())['perfil_biaix_vs_distancia_vora']
 cls={'curts':'curts (≤1/800)','mitjans':'mitjans (1/800–1/50)','llargs':'llargs (>1/50)'}
 out={}
 for c,t in table.items():
  p=a1[cls[c]]['perfil'];d=np.array([v['d'] for v in p]);b=np.array([v['mediana_ln'] for v in p]);lo=d<t['d_px'][0]
  out[c]=(np.r_[d[lo],t['d_px']].astype(np.float32),np.r_[b[lo],t['B_ln']].astype(np.float32))
 return out

def classe(e):return 'curts' if e<=1/800 else ('mitjans' if e<=1/50 else 'llargs')

def diagnostic():
 src=O/'limb_frames';assert json.loads((src/'COMPLETE.json').read_text())['PASS'];out=O/'limb_diagnostic_train';out.mkdir()
 meta=json.loads((src/'METADATA.json').read_text());frames=meta['frames'];train=[i for i,f in enumerate(frames) if not f['holdout']];tables=old_tables()
 # A regular two-pixel diagnostic grid, independent of user marks.
 N=np.asarray(np.load(src/'numerator.npy',mmap_mode='r')[:,::2,::2,1]);Wg=np.asarray(np.load(src/'weight.npy',mmap_mode='r')[:,::2,::2,1]);D=np.asarray(np.load(src/'distance_model.npy',mmap_mode='r')[:,::2,::2]);y0,y1,x0,x1=meta['box_y0y1x0x1']
 yy,xx=np.mgrid[y0:y1:2,x0:x1:2];rr=np.hypot(xx-5361.768111973117,yy-3775.747534140857);sector=np.floor((np.arctan2(yy-3775.747534140857,xx-5361.768111973117)+np.pi)/(2*np.pi)*24).astype(int)%24
 annulus=(rr>410)&(rr<560);cuts=[15.,20.];centers=np.arange(-3.75,40,.5);rows=[];summary={}
 for cut in cuts:
  totalN=np.zeros(D.shape[1:],np.float64);totalW=totalN.copy();count=np.zeros(D.shape[1:],np.int16)
  for j in train:
   ds,bs=tables[classe(frames[j]['exposure'])];co=np.exp(-np.interp(D[j],ds,bs,right=0)).astype(np.float32);valid=(D[j]>cut)&(Wg[j]>0)&(N[j]>0)&annulus
   totalN+=np.where(valid,N[j]*co,0);totalW+=np.where(valid,Wg[j],0);count+=valid
  for j in train:
   ds,bs=tables[classe(frames[j]['exposure'])];b=np.interp(D[j],ds,bs,right=0).astype(np.float32);valid=(D[j]>cut)&(Wg[j]>0)&(N[j]>0)&annulus
   wn=totalW-np.where(valid,Wg[j],0);nn=totalN-np.where(valid,N[j]*np.exp(-b),0);cnt=count-valid
   good=annulus&(Wg[j]>0)&(N[j]>0)&(wn>0)&(nn>0)&(cnt>=3)&(D[j]>-4)&(D[j]<40)
   raw=np.log(np.maximum(N[j],1e-30)/np.maximum(Wg[j],1e-30))-np.log(np.maximum(nn,1e-30)/np.maximum(wn,1e-30));res=raw-b
   anchor=good&(D[j]>=25)&(D[j]<40);offset=float(np.median(res[anchor])) if anchor.sum()>=100 else np.nan
   for k,d in enumerate(centers):
    ring=good&(D[j]>=d-.25)&(D[j]<d+.25)
    for s in range(24):
     sel=ring&(sector==s);n=int(sel.sum())
     if n<8:continue
     z=res[sel]-offset
     rows.append(dict(cut=cut,frame=j,name=frames[j]['name'],cls=classe(frames[j]['exposure']),sector=s,d=float(d),n=n,offset=offset,raw=float(np.median(raw[sel])),residual=float(np.median(z)),mad=float(np.median(np.abs(z-np.median(z))))))
   print('TRAIN_RESIDUAL',cut,j+1,len(frames),flush=True)
  per={}
  for c in tables:
   rc=[r for r in rows if r['cut']==cut and r['cls']==c];med=[];spread=[];counts=[]
   for d in centers:
    q=np.array([r['residual'] for r in rc if r['d']==d and np.isfinite(r['residual'])]);med.append(float(np.median(q)) if q.size else None);spread.append(float(np.percentile(q,75)-np.percentile(q,25)) if q.size else None);counts.append(int(q.size))
   per[c]=dict(d=centers.tolist(),median=med,iqr=spread,frame_sector_cells=counts)
  summary[str(cut)]=per
 save(out/'FRAME_SECTOR_BINS.json',rows);save(out/'TRAIN_SUMMARY.json',summary);save(out/'COMPLETE.json',{'PASS':True,'cut_sensor_px':cuts,'frames':len(train),'holdouts_read_for_shapes_only':True,'pixel_step':2,'sectors':24,'min_pixels_per_cell':8,'reference_min_other_frames':3,'source_sha256':sha(src/'COMPLETE.json'),'scope':'conditional residual diagnosis, no fitted correction promoted'})

if __name__=='__main__':guard();diagnostic()
