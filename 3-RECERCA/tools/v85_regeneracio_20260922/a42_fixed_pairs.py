"""Fixed early/late 1/3200 pairs at the same sky coordinate; no fitted cure."""
from a11_limb_diagnostics import *

def main():
 src=O/'limb_frames';out=O/'fixed_pairs_R02';out.mkdir();meta=json.loads((src/'METADATA.json').read_text());frames=meta['frames'];train=[i for i,f in enumerate(frames) if not f['holdout'] and np.isclose(f['exposure'],1/3200)];early=[i for i in train if i<10];late=[i for i in train if i>40];assert len(early)==6 and len(late)==13
 save(out/'FROZEN_DIAGNOSTIC.json',{'hypothesis':'Old B(D) leaves limb-distance residual within same exposure after removing fixed pair offset. Alternative: exposure/time/signal calibration and reference composition.','pairs':78,'early':[frames[i]['name'] for i in early],'late':[frames[i]['name'] for i in late],'holdouts_used':False,'reference_cuts':[15,20],'anchor':'same fixed pair, both D in25..40, outside marks; no changing reference population','pixel_step':2,'sectors':24,'target_bins':[[-4,0],[0,2],[2,4],[4,8],[8,15],[15,25],[25,40]],'signal_bins':'quartiles of each channel camera irradiance from train reference pixels with D>20 and r410..560, fixed before pair residuals','minimum_anchor_pixels':100,'minimum_summary_pixels':20,'outputs':'raw and anchored log ratio, all linear ratio including target N<=0, selection fractions; separate marked pixels','no_source_modification':True,'no_PASS_threshold_redefinition':True})
 y0,y1,x0,x1=meta['box_y0y1x0x1'];yy,xx=np.mgrid[y0:y1:2,x0:x1:2];rr=np.hypot(xx-5361.768111973117,yy-3775.747534140857);region=(rr>410)&(rr<560);mark=np.load(O/'ROI_L246.npz')['c-1'][y0-3000:y1-3000:2,x0-4600:x1-4600:2]>0
 N=np.asarray(np.load(src/'numerator.npy',mmap_mode='r')[train,::2,::2,:]);W=np.asarray(np.load(src/'weight.npy',mmap_mode='r')[train,::2,::2,:]);D=np.asarray(np.load(src/'distance_model.npy',mmap_mode='r')[train,::2,::2]);ds,bs=old_tables()['curts'];b=np.interp(D,ds,bs,right=0);I=np.divide(N,W,out=np.full_like(N,np.nan),where=W>0)*np.exp(-b)[...,None];index={i:j for j,i in enumerate(train)};rows=[];pairs=[];bins=[(-4,0),(0,2),(2,4),(4,8),(8,15),(15,25),(25,40)];signal_edges=[]
 for ch in range(3):
  valid=(D>20)&region&(W[...,ch]>0)&(I[...,ch]>0);v=I[...,ch][valid];signal_edges.append(np.r_[-np.inf,np.percentile(v,[25,50,75]),np.inf])
 for ei in early:
  for li in late:
   e,l=index[ei],index[li]
   for ch in range(3):
    valid=region&(W[e,...,ch]>0)&(W[l,...,ch]>0)&np.isfinite(I[e,...,ch])&np.isfinite(I[l,...,ch]);positive=valid&(I[e,...,ch]>0)&(I[l,...,ch]>0);anchor=positive&(D[e]>=25)&(D[e]<40)&(D[l]>=25)&(D[l]<40)&~mark;offset=float(np.median(np.log(I[l,...,ch][anchor]/I[e,...,ch][anchor]))) if anchor.sum()>=100 else None;pairs.append({'early':frames[ei]['name'],'late':frames[li]['name'],'channel':ch,'anchor_n':int(anchor.sum()),'offset_late_over_early':offset})
    if offset is None:continue
    for target,ref,sign,epoch in [(l,e,1,'late'),(e,l,-1,'early')]:
     ratio=np.divide(I[target,...,ch],I[ref,...,ch],out=np.full(region.shape,np.nan),where=I[ref,...,ch]>0);logratio=np.log(np.maximum(ratio,1e-30));anchored=logratio-sign*offset
     for cut in [15,20]:
      for lo,hi in bins:
       candidate=region&(W[target,...,ch]>0)&(W[ref,...,ch]>0)&(I[ref,...,ch]>0)&np.isfinite(ratio)&(D[ref]>cut)&(D[target]>=lo)&(D[target]<hi);pos=candidate&(I[target,...,ch]>0)
       groups=[('all',np.ones(region.shape,bool)),('marks246',mark)]
       for si in range(4):groups.append(('signalQ'+str(si+1),(I[ref,...,ch]>=signal_edges[ch][si])&(I[ref,...,ch]<signal_edges[ch][si+1])))
       for group,g in groups:
        m=candidate&g;p=pos&g
        if m.sum()<20:continue
        rows.append({'early':ei,'late':li,'target_epoch':epoch,'channel':ch,'cut':cut,'D':[lo,hi],'group':group,'n_linear':int(m.sum()),'n_positive_log':int(p.sum()),'n_nonpositive_target':int((m&~pos).sum()),'raw_log_median':float(np.median(logratio[p])) if p.any() else None,'anchored_log_median':float(np.median(anchored[p])) if p.any() else None,'linear_ratio_median':float(np.median(ratio[m])),'anchored_linear_ratio_median':float(np.median(ratio[m]*np.exp(-sign*offset))),'pair_offset_late_over_early':offset})
  print('FIXED_PAIRS_EARLY_DONE',ei,flush=True)
 summary=[]
 for ch in range(3):
  for cut in [15,20]:
   for epoch in ['early','late','both']:
    for lo,hi in bins:
     for group in ['all','marks246','signalQ1','signalQ2','signalQ3','signalQ4']:
      q=[v for v in rows if v['channel']==ch and v['cut']==cut and (epoch=='both' or v['target_epoch']==epoch) and v['D']==[lo,hi] and v['group']==group];valid=[v for v in q if v['anchored_log_median'] is not None]
      if not q:continue
      summary.append({'channel':ch,'cut':cut,'epoch':epoch,'D':[lo,hi],'group':group,'pair_cells':len(q),'raw_log_median':float(np.median([v['raw_log_median'] for v in valid])) if valid else None,'anchored_log_median':float(np.median([v['anchored_log_median'] for v in valid])) if valid else None,'anchored_log_iqr':np.percentile([v['anchored_log_median'] for v in valid],[25,75]).tolist() if valid else None,'linear_ratio_median':float(np.median([v['linear_ratio_median'] for v in q])),'anchored_linear_ratio_median':float(np.median([v['anchored_linear_ratio_median'] for v in q]))})
 save(out/'PAIR_OFFSETS.json',pairs);save(out/'PAIR_BINS.json',rows);save(out/'SUMMARY.json',summary);save(out/'COMPLETE.json',{'PASS':True,'meaning':'calculation integrity only; no curve fitted or correction promoted','holdouts_used':False,'source_modified':False})
 for v in summary:
  if v['channel']==1 and v['cut']==20 and v['epoch']=='both' and v['group']=='all':print(v,flush=True)
if __name__=='__main__':guard();main()
