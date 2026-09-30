"""Sparse train-only B(D) numerator ablation at fixed marked normals."""
from a4_sources import *

def main():
 src=O/'limb_frames';meta=json.loads((src/'METADATA.json').read_text());frames=meta['frames'];train=[i for i,f in enumerate(frames) if not f['holdout']];geom=np.load(O/'marks246_R02/GEOMETRY.npz');pts=geom['points'];norm=geom['normals'];aw=geom['weights'];comp=geom['component'];usable=geom['usable'];samples=np.stack([pts,pts+4*norm,pts-4*norm]);flo=np.floor(samples).astype(int);frac=samples-flo;corners=flo[...,None,:]+np.array([[0,0],[1,0],[0,1],[1,1]]);coeff=np.stack([(1-frac[...,0])*(1-frac[...,1]),frac[...,0]*(1-frac[...,1]),(1-frac[...,0])*frac[...,1],frac[...,0]*frac[...,1]],axis=-1);pix,inv=np.unique(corners.reshape(-1,2),axis=0,return_inverse=True);y0,y1,x0,x1=meta['box_y0y1x0x1'];ix=pix[:,0]-x0;iy=pix[:,1]-y0;assert (ix>=0).all() and (iy>=0).all() and (ix<x1-x0).all() and (iy<y1-y0).all();N=np.load(src/'numerator.npy',mmap_mode='r');W=np.load(src/'weight.npy',mmap_mode='r');D=np.load(src/'distance_model.npy',mmap_mode='r');b2=json.loads((H/'v38_limb_round1/cau/correccio_vora_lunar.json').read_text())['taula'];a1=json.loads((H/'v38_limb_round1/receipts/A1_franja_font.json').read_text())['perfil_biaix_vs_distancia_vora'];clabel={'curts':'curts (≤1/800)','mitjans':'mitjans (1/800–1/50)','llargs':'llargs (>1/50)'};tables={}
 for c,t in b2.items():
  p=a1[clabel[c]]['perfil'];ds=np.array([v['d'] for v in p]);bs=np.array([v['mediana_ln'] for v in p]);lo=ds<t['d_px'][0];tables[c]=(np.r_[ds[lo],t['d_px']].astype(np.float32),np.r_[bs[lo],t['B_ln']].astype(np.float32))
 tiers=[dict(curts=0.,mitjans=.5,llargs=1.5),dict(curts=-2.,mitjans=-.5,llargs=None),dict(curts=-4.,mitjans=None,llargs=None)];GT=[.02,4e-4,8e-6];ncO=np.zeros((len(pix),3),np.float32);nuO=ncO.copy();deO=ncO.copy();ncT=ncO.copy();nuT=ncO.copy();deT=ncO.copy()
 parts={c+'_'+b:np.zeros((len(pix),3),np.float64) for c in tables for b in ['old','tiers']};weight_parts={k:np.zeros(len(pix),np.float64) for k in parts};DW=[];DD=[];MAXD=[]
 for j in train:
  f=frames[j];e=f['exposure'];c='curts' if e<=1/800 else ('mitjans' if e<=1/50 else 'llargs');d=np.asarray(D[j,iy,ix]);n=np.asarray(N[j,iy,ix,:]);w=np.asarray(W[j,iy,ix,:]);tb=b2[c];bo=np.interp(d,np.asarray(tb['d_px'],np.float32),np.asarray(tb['B_ln'],np.float32),left=tb['B_ln'][0],right=0).astype(np.float32);co=np.exp(-bo,dtype=np.float32);ds,bs=tables[c];bn=np.interp(d,ds,bs,right=0).astype(np.float32);cn=np.exp(-bn,dtype=np.float32);fl=np.clip((d-2)/2,0,1).astype(np.float32);we=np.zeros_like(d)
  for tier,g in zip(tiers,GT):
   d0=tier[c]
   if d0 is not None:we+=g*np.clip(d-d0,0,1)/np.maximum(cn,1e-6)**2
  ncO+=n*(fl*co)[:,None];nuO+=n*fl[:,None];deO+=w*fl[:,None];ncT+=n*(we*cn)[:,None];nuT+=n*we[:,None];deT+=w*we[:,None]
  parts[c+'_old']+=n*(fl*co)[:,None]-n*fl[:,None];parts[c+'_tiers']+=n*(we*cn)[:,None]-n*we[:,None];weight_parts[c+'_old']+=w[:,1]*fl;weight_parts[c+'_tiers']+=w[:,1]*we;DW.append(w[:,1]*(fl+we));DD.append(d);MAXD.append(np.where(w[:,1]>0,d,-np.inf))
 den=deO+deT;matrix=np.asarray(meta['matrix'],np.float32);gain=np.asarray(meta['gain'],np.float32)
 def rgb(n):
  cam=np.where(den>0,n/np.maximum(den,1e-20),np.nan).astype(np.float32);return (np.einsum('ij,nj->ni',matrix,cam)*gain).astype(np.float32)
 corrected=rgb(ncO+ncT);uncorrected=rgb(nuO+nuT);physical=np.load(O/'d4_baseline/products/sources/support.npy',mmap_mode='r')[pix[:,1],pix[:,0]];z=np.load(O/'current_lunar_support.npz');mx0,my0,mx1,my1=map(int,z['box']);inside=(pix[:,0]>=mx0)&(pix[:,0]<mx1)&(pix[:,1]>=my0)&(pix[:,1]<my1);moon=np.zeros(len(pix),bool);moon[inside]=z['support'][pix[inside,1]-my0,pix[inside,0]-mx0];valid=physical&~moon;finite=np.all(den>0,axis=1)&np.isfinite(corrected[:,1])&np.isfinite(uncorrected[:,1])&(corrected[:,1]>0)&(uncorrected[:,1]>0)
 def interp(a):return (a[inv].reshape(corners.shape[:-1])*coeff).sum(axis=-1)
 good=usable&(interp(valid.astype(float))>.999).all(axis=0)&(interp(finite.astype(float))>.999).all(axis=0);safe_c=np.where(finite,corrected[:,1],1);safe_u=np.where(finite,uncorrected[:,1],1);sc=interp(np.log(safe_c).astype(float));su=interp(np.log(safe_u).astype(float));cc=sc[0]-.5*(sc[1]+sc[2]);cu=su[0]-.5*(su[1]+su[2]);delta=cc-cu
 def stats(v,w):
  order=np.argsort(v);return dict(mean=float(np.average(v,weights=w)),median=float(v[order][np.searchsorted(np.cumsum(w[order]),w.sum()/2)]),mean_abs=float(np.average(abs(v),weights=w)),rms=float(np.sqrt(np.average(v*v,weights=w))),p05_p50_p95_unweighted=np.percentile(v,[5,50,95]).tolist(),positive_weight_fraction=float(w[v>0].sum()/w.sum()))
 rows=[]
 for k in [0,*sorted(set(comp))]:
  m=good if k==0 else good&(comp==k)
  if not m.sum():continue
  w=aw[m];rows.append(dict(component=int(k),n=int(m.sum()),corrected=stats(cc[m],w),uncorrected_same_weights=stats(cu[m],w),correction_delta=stats(delta[m],w)))
 s4=np.load(O/'s4_baseline/cau/s4_recomposicio_box.npz');sy0,sy1,sx0,sx1=map(int,s4['box']);sx=pix[:,0]-sx0;sy=pix[:,1]-sy0;sb=(sx>=0)&(sy>=0)&(sx<sx1-sx0)&(sy<sy1-sy0);use=np.zeros(len(pix),bool);sup=np.load(O/'s4_baseline/cau/s4_support_new_box.npy');olds=np.load(O/'b3_baseline/cau/support_v42.npy',mmap_mode='r');dmin=s4['Dmin'];use[sb]=sup[sy[sb],sx[sb]]&((~olds[pix[sb,1],pix[sb,0]])|(dmin[sy[sb],sx[sb]]<6));nuse=int((good&(interp(use.astype(float))>.999).all(axis=0)).sum());assert len(pix)==4047 and len(train)==61 and good.sum()==902 and nuse==831;assert abs(rows[1]['correction_delta']['mean']+.113701)<1e-6
 m=good&(comp==1);w=aw[m];report=dict(n=int(m.sum()),corrected_mean=float(np.average(cc[m],weights=w)),uncorrected_mean=float(np.average(cu[m],weights=w)),log_effect_at_center_plus_minus=[float(np.average((sc[k]-su[k])[m],weights=w)) for k in range(3)],full_S4_triplets=int((m&(interp(use.astype(float))>.999).all(axis=0)).sum()),parts={})
 for key,part in parts.items():
  v=rgb((ncO+ncT)-part.astype(np.float32));vg=v[:,1];assert (vg[finite]>0).all(),key;sample=interp(np.log(np.where(finite,vg,1)).astype(float));cv=sample[0]-.5*(sample[1]+sample[2]);fr=interp(weight_parts[key]/np.maximum(den[:,1],1e-30));report['parts'][key]=dict(mean_C_without_this_factor=float(np.average(cv[m],weights=w)),delta_from_full=float(np.average(cv[m]-cc[m],weights=w)),CFA_G_weight_fraction_center_plus_minus=[float(np.average(fr[k,m],weights=w)) for k in range(3)])
 dw=np.asarray(DW);dd=np.asarray(DD);report['D_weight_fractions']={}
 for key,sel in [('negative',dd<0),('zero_to_two',(dd>=0)&(dd<2)),('two_to_four',(dd>=2)&(dd<4)),('four_or_more',dd>=4)]:
  f=interp(np.sum(np.where(sel,dw,0),axis=0,dtype=np.float64)/np.maximum(den[:,1],1e-30));report['D_weight_fractions'][key]=[float(np.average(f[k,m],weights=w)) for k in range(3)]
 md=np.max(np.asarray(MAXD),axis=0);inner_indices=inv.reshape(corners.shape[:-1])[2,m];inner_coeff=coeff[2,m];max_corner=np.max(np.where(inner_coeff>0,md[inner_indices],-np.inf),axis=1);assert not (max_corner>4).any()
 sample_s4=interp(use.astype(float));coords=[]
 for i in np.flatnonzero(m):
  coords.append({'geometry_index':int(i),'alpha_weight':float(aw[i]),'normal_xy':norm[i].tolist(),'samples':[{'label':label,'xy':samples[k,i].tolist(),'solar_radius_px':float(np.hypot(samples[k,i,0]-5361.768111973117,samples[k,i,1]-3775.747534140857)),'S4_bilinear_fraction':float(sample_s4[k,i])} for k,label in enumerate(['center','plus4','minus4'])]})
 report.update(train_frames=len(train),heldout_N_excluded=6,inner_maxD_corner_quantiles=np.percentile(max_corner,[0,50,100]).tolist(),inner_triplets_any_train_D_gt4=int((max_corner>4).sum()),coordinates=coords,limits=['same a71 train full-S4 counterfactual, not actual D4 splice','weights CFA-G, color transform has mixed channel coefficients','factor-removal log contrasts not additive','validity uses a45 bilinear threshold>.999','no independent photometric correctness established'])
 assert report['n']==80 and report['full_S4_triplets']==9;assert abs(report['log_effect_at_center_plus_minus'][2]-.293000)<1e-6
 out=O/'bias_component_R02/DECOMPOSITION.json';assert not out.exists();save(out,report);print('COMPONENT_DECOMPOSITION_REPRODUCED',report['log_effect_at_center_plus_minus'],report['inner_maxD_corner_quantiles'])

if __name__=='__main__':guard();main()
