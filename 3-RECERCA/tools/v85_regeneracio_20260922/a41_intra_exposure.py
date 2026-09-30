"""Read-only science inputs: same-sky same-exposure moving-limb residuals.
No fit, source correction or holdout evaluation. Six original holdouts excluded.
"""
from a11_limb_diagnostics import *

def main():
 src=O/'limb_frames';out=O/'intra_exposure_R02';out.mkdir();meta=json.loads((src/'METADATA.json').read_text());frames=meta['frames'];train=[i for i,f in enumerate(frames) if not f['holdout'] and np.isclose(f['exposure'],1/3200)];assert len(train)==19
 save(out/'FROZEN_DIAGNOSTIC.json',{'question':'Does distance-dependent residual persist with same-exposure references at the same sky pixels?','train':[frames[i]['name'] for i in train],'holdouts':'all original six excluded; no evaluation or fit','cuts_sensor_px':[15,20],'target_D_bins':[[-4,0],[0,2],[2,4],[4,8],[8,15],[15,25],[25,40]],'anchor_D':[25,40],'minimum_reference_frames':3,'pixel_step':2,'minimum_sector_bin_pixels':8,'sectors':24,'no_source_change':True,'distance_caveat':'D relative to modelled lunar radius, not apparent occultation; negative D not automatically invalid'})
 N=np.asarray(np.load(src/'numerator.npy',mmap_mode='r')[train,::2,::2,:],dtype=np.float32);W=np.asarray(np.load(src/'weight.npy',mmap_mode='r')[train,::2,::2,:],dtype=np.float32);D=np.asarray(np.load(src/'distance_model.npy',mmap_mode='r')[train,::2,::2],dtype=np.float32);tables=old_tables();ds,bs=tables['curts'];bias=np.interp(D,ds,bs,right=0).astype(np.float32);C=N*np.exp(-bias)[...,None];y0,y1,x0,x1=meta['box_y0y1x0x1'];yy,xx=np.mgrid[y0:y1:2,x0:x1:2];r=np.hypot(xx-5361.768111973117,yy-3775.747534140857);annulus=(r>410)&(r<560);sectors=(np.floor((np.arctan2(yy-3775.747534140857,xx-5361.768111973117)+np.pi)/(2*np.pi)*24).astype(int)%24);rows=[];offsets=[]
 bins=[(-4,0),(0,2),(2,4),(4,8),(8,15),(15,25),(25,40)]
 for cut in [15.,20.]:
  for channel in range(3):
   n=N[...,channel];w=W[...,channel];cn=C[...,channel];valid=(D>cut)&(w>0)&(n>0)&annulus;tn=np.sum(np.where(valid,cn,0),axis=0,dtype=np.float64);tw=np.sum(np.where(valid,w,0),axis=0,dtype=np.float64);tc=valid.sum(axis=0)
   for a,i in enumerate(train):
    rn=tn-np.where(valid[a],cn[a],0);rw=tw-np.where(valid[a],w[a],0);cnt=tc-valid[a];good=annulus&(n[a]>0)&(w[a]>0)&(rn>0)&(rw>0)&(cnt>=3)&(D[a]>-4)&(D[a]<40);res=np.log(np.maximum(cn[a],1e-30)/np.maximum(w[a],1e-30))-np.log(np.maximum(rn,1e-30)/np.maximum(rw,1e-30));anchor=good&(D[a]>=25)&(D[a]<40);offset=float(np.median(res[anchor])) if anchor.sum()>=100 else None;offsets.append({'cut':cut,'channel':channel,'frame':i,'name':frames[i]['name'],'anchor_n':int(anchor.sum()),'offset':offset})
    if offset is None:continue
    for lo,hi in bins:
     ring=good&(D[a]>=lo)&(D[a]<hi)
     for s in range(24):
      m=ring&(sectors==s);v=res[m]-offset
      if v.size<8:continue
      rows.append({'cut':cut,'channel':channel,'frame':i,'name':frames[i]['name'],'time':frames[i]['time'],'epoch':'early' if i<10 else 'late','D':[lo,hi],'sector':s,'n':int(v.size),'median':float(np.median(v)),'mad':float(np.median(abs(v-np.median(v)))),'reference_count_min':int(cnt[m].min()),'reference_count_median':float(np.median(cnt[m]))})
   print('SAME_EXPOSURE_DONE',cut,channel,flush=True)
 summary=[]
 for cut in [15.,20.]:
  for ch in range(3):
   for epoch in ['early','late','all']:
    for lo,hi in bins:
     cells=[v for v in rows if v['cut']==cut and v['channel']==ch and (epoch=='all' or v['epoch']==epoch) and v['D']==[lo,hi]];v=np.array([c['median'] for c in cells]);summary.append({'cut':cut,'channel':ch,'epoch':epoch,'D':[lo,hi],'cells':len(cells),'frames':len({c['frame'] for c in cells}),'pixels_summed':sum(c['n'] for c in cells),'median':float(np.median(v)) if len(v) else None,'p25':float(np.percentile(v,25)) if len(v) else None,'p75':float(np.percentile(v,75)) if len(v) else None})
 save(out/'FRAME_SECTOR_BINS.json',rows);save(out/'OFFSETS.json',offsets);save(out/'SUMMARY.json',summary);save(out/'COMPLETE.json',{'PASS':True,'meaning':'diagnostic calculation only, no causal correction validated','train_frames':19,'holdouts_used':False,'source_modified':False})
 for v in summary:
  if v['cut']==20 and v['channel']==1 and v['epoch']=='all':print(v,flush=True)
if __name__=='__main__':guard();main()
