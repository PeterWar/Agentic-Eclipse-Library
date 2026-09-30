"""Frozen early-epoch ablation of temporal mixing, on source ROI only.

Primary: six early versus nineteen same-exposure train frames. Mixed61 is
secondary. No new B(D), calibration, geometry, source splice or PSB changes.
"""
from a14_limb_recompose import *
from scipy.ndimage import map_coordinates

def main():
 out=O/'early_epoch_R03';out.mkdir();src=O/'limb_frames';meta=json.loads((src/'METADATA.json').read_text());frames=meta['frames'];train=[i for i,f in enumerate(frames) if not f['holdout']];same=[i for i in train if np.isclose(frames[i]['exposure'],1/3200)];early=[i for i in same if i<10];assert len(train)==61 and len(same)==19 and len(early)==6
 assert [frames[i]['name'] for i in early]==['572A2960.CR3','572A2961.CR3','572A2962.CR3','572A2964.CR3','572A2965.CR3','572A2966.CR3']
 groups={'early6':early,'same19':same,'mixed61':train,'early_odd':early[::2],'early_even':early[1::2]};shape=tuple(meta['shape'][1:]);y0,y1,x0,x1=meta['box_y0y1x0x1'];assert shape==(y1-y0,x1-x0,3)
 save(out/'FROZEN_TEST.json',{'question':'Does narrow-epoch composition reduce source contrast associated with moving-limb population changes?',
  'groups':{k:[frames[i]['name'] for i in v] for k,v in groups.items()},'primary_comparison':'early6 vs same19 (same1/3200 exposure)','secondary':'mixed61 full train reference',
  'early_time_span':[frames[early[0]]['time'],frames[early[-1]]['time']],'early_moon_displacement_sensor_px':float(np.hypot(frames[early[-1]]['lluna_dx']-frames[early[0]]['lluna_dx'],frames[early[-1]]['lluna_dy']-frames[early[0]]['lluna_dy'])),
  'frozen':'existing N/W/D, B2 factors and S4tiers, separate old/tierfloat32 sums, matrix and gain, mark geometry/h2,4,8',
  'holdout_N_excluded':6,'no_new_parameter_fit':True,'source_only_ROI':'Not a full-canvas WOW test. No hybrid source or PSB constructed.',
  'split_control':'alternating3+3 early frames; logdifference is noise plus residual temporal/registration/calibration effects, not pure read noise',
  'acceptance':'diagnostic only; retain lost-support counts and signed contrasts; no automatic acceptance or revised thresholds'})
 N=np.load(src/'numerator.npy',mmap_mode='r');W=np.load(src/'weight.npy',mmap_mode='r');D=np.load(src/'distance_model.npy',mmap_mode='r');b2=json.loads((H/'v38_limb_round1/cau/correccio_vora_lunar.json').read_text())['taula'];tables=old_tables();acc={k:[np.zeros(shape,np.float32) for _ in range(5)] for k in groups}
 for j in train:
  f=frames[j];c=classe(f['exposure']);d=np.asarray(D[j]);n=np.asarray(N[j]);w=np.asarray(W[j]);tb=b2[c];co=np.exp(-np.interp(d,np.asarray(tb['d_px'],np.float32),np.asarray(tb['B_ln'],np.float32),left=tb['B_ln'][0],right=0).astype(np.float32),dtype=np.float32);ds,bs=tables[c];cn=np.exp(-np.interp(d,ds,bs,right=0).astype(np.float32),dtype=np.float32);fl=np.clip((d-2)/2,0,1).astype(np.float32);we=np.zeros_like(d)
  for tier,g in zip(TIERS,GT):
   d0=tier[c]
   if d0 is not None:we+=g*np.clip(d-d0,0,1)/np.maximum(cn,1e-6)**2
  no=n*(fl*co)[...,None];nt=n*(we*cn)[...,None];do=w*fl[...,None];dt=w*we[...,None];w2=(do+dt)**2
  for k,idx in groups.items():
   if j in idx:
    for dest,add in zip(acc[k],[no,nt,do,dt,w2]):dest+=add
  if j%10==0:print('EARLY_RECOMPOSE',j,flush=True)
 matrix=np.asarray(meta['matrix'],np.float32);gain=np.asarray(meta['gain'],np.float32);data={};valid={};physical=np.load(O/'domain_v1/sources/support.npy',mmap_mode='r')[y0:y1,x0:x1]
 for k,(no,nt,do,dt,w2) in acc.items():
  den=do+dt;cam=np.where(den>0,(no+nt)/np.maximum(den,1e-20),np.nan).astype(np.float32);rgb=(np.einsum('ij,hwj->hwi',matrix,cam)*gain).astype(np.float32);data[k]=rgb[...,1];valid[k]=physical&np.all(den>0,axis=-1)&np.isfinite(rgb[...,1])&(rgb[...,1]>0);np.save(out/(k+'_G.npy'),rgb[...,1]);np.save(out/(k+'_valid.npy'),valid[k]);np.save(out/(k+'_neff_G.npy'),den[...,1]**2/np.maximum(w2[...,1],1e-30));del rgb,cam
 del acc;geom=np.load(O/'marks246_R02/GEOMETRY.npz');pts=geom['points'];norm=geom['normals'];ids=geom['component'];aw=geom['weights'];usable=geom['usable'];rows=[];coverage=[];logs={k:np.log(np.where(valid[k],a,1)).astype(float) for k,a in data.items()};split=[]
 for h in [2,4,8]:
  coords=np.stack([np.stack([p[:,1]-y0,p[:,0]-x0]) for p in [pts,pts+h*norm,pts-h*norm]],axis=1);g={k:usable&(map_coordinates(v.astype(float),coords,order=1,mode='constant',cval=0)>.999).all(axis=0) for k,v in valid.items()};sample={k:map_coordinates(a,coords,order=1,mode='constant',cval=np.nan) for k,a in logs.items()};C={k:s[0]-.5*(s[1]+s[2]) for k,s in sample.items()}
  common=g['early6']&g['same19']&g['mixed61'];split_common=common&g['early_odd']&g['early_even']
  for component in [0,*sorted(set(ids))]:
   select=np.ones(len(ids),bool) if component==0 else ids==component;ok=common&select;coverage.append({'h':h,'component':int(component),'group_counts':{k:int((q&select).sum()) for k,q in g.items()},'common':int(ok.sum())})
   if ok.sum()>=10:
    for k in ['early6','same19','mixed61']:
     q=C[k][ok];w=aw[ok];rows.append({'h':h,'component':int(component),'group':k,'n':int(ok.sum()),'mean_C':float(np.average(q,weights=w)),'mean_abs_C':float(np.average(abs(q),weights=w)),'rms_C':float(np.sqrt(np.average(q*q,weights=w)))})
   sp=split_common&select
   if sp.sum()>=10:
    w=aw[sp];dc=(C['early_odd']-C['early_even'])[sp];delta=(C['early6']-C['same19'])[sp];split.append({'h':h,'component':int(component),'n':int(sp.sum()),'split_C_difference_rms':float(np.sqrt(np.average(dc*dc,weights=w))),'early_minus_same19_C_rms':float(np.sqrt(np.average(delta*delta,weights=w))),'scope':'different temporal/spatial noise; no universal SNR claim'})
 save(out/'METRICS.json',{'rows':rows,'coverage':coverage,'split_control':split,'scope':'fixed source logG contrast only; common effective domain; no new filtered or native output'})
 save(out/'COMPLETE.json',{'PASS':True,'scientific_acceptance':None,'source_arrays':{k:{'sha256':sha(out/(k+'_G.npy')),'valid_pixels':int(valid[k].sum())} for k in data},'no_reserved_N_read':True})
 print('EARLY_SOURCE_COMPLETE',[(r['group'],r['component'],r['mean_C'],r['rms_C']) for r in rows if r['h']==4],flush=True)

if __name__=='__main__':guard();main()
