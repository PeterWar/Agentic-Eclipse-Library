"""Fixed normal-to-trace contrasts on actual mark246, with rotated controls.
No recentering on a candidate minimum; raw-raster metric is not proof of cure.
"""
from a16_build_psb import *
from scipy.ndimage import label,map_coordinates
from scipy.spatial import cKDTree
import tifffile as tf

def main():
 out=O/'marks246_T_R02';out.mkdir();marks=np.load(O/'ROI_L246.npz');alpha=marks['c-1'].astype(np.float64)/65535;yy,xx=np.where(alpha>0);pts=np.column_stack([xx+4600,yy+3000]).astype(float);weights=alpha[yy,xx];labels,n=label(alpha>0);components=labels[yy,xx];tree=cKDTree(pts);normals=np.full(pts.shape,np.nan);quality=np.zeros(len(pts))
 for j,p in enumerate(pts):
  ids=np.asarray(tree.query_ball_point(p,17));ids=ids[components[ids]==components[j]]
  if len(ids)<5:continue
  w=weights[ids];z=pts[ids]-np.average(pts[ids],axis=0,weights=w);cov=(z*w[:,None]).T@z/w.sum();ev,evec=np.linalg.eigh(cov);quality[j]=ev[1]/max(ev[0],1e-12)
  if quality[j]>=4:normals[j]=evec[:,0]
 z=np.load(O/'current_lunar_support.npz');x0,y0,x1,y1=map(int,z['box']);M=np.zeros(alpha.shape,bool);M[y0-3000:y1-3000,x0-4600:x1-4600]=z['support'];physical=np.asarray(np.load(O/'d4_baseline/products/sources/support.npy',mmap_mode='r')[3000:4550,4600:6150]);valid=physical&~M;usable=np.isfinite(normals).all(axis=1)
 save(out/'FROZEN_GEOMETRY.json',{'mark_source':'ROI_L246.npz c-1 > 0','alpha_max':float(alpha.max()),'pixels':len(pts),'components':n,'normal_method':'alpha-weighted local PCA radius17px within same connected component; >=5 neighbors and eigenratio>=4; no image intensity used','usable_normals':int(usable.sum()),'h_px':[2,4,8],'rotation_degrees':[0,45,90,135,180,225,270,315],'rotation_center':[5361.768111973117,3775.747534140857],'minimum_samples':10,'validity':'all three bilinear sample footprints fully within physical support and outside final Moon; raw raster values, not layer contribution','no_automatic_acceptance_threshold':True,'scope':'diagnostic evidence for signed trace contrast; real coronal detail can contribute'})
 np.savez(out/'GEOMETRY.npz',points=pts,normals=normals,weights=weights,component=components,usable=usable)
 rows=[];p=PSB(str(O/'V84_Pere_input.psb'));center=np.array([5361.768111973117,3775.747534140857]);sampling={}
 for angle in [0,45,90,135,180,225,270,315]:
  theta=np.deg2rad(angle);rot=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]]);points=(pts-center)@rot.T+center;normal=normals@rot.T
  for h in [2,4,8]:
   pp=[points,points+h*normal,points-h*normal];coordinates=[np.array([q[:,1]-3000,q[:,0]-4600]) for q in pp];good=usable.copy()
   for coords in coordinates:good&=map_coordinates(valid.astype(float),np.nan_to_num(coords,nan=-1000),order=1,mode='constant',cval=0)>.999
   sampling[(angle,h)]=(coordinates,good)
 def measure(name,variant,a):
  for (angle,h),(coordinates,good) in sampling.items():
   if good.sum()<10:continue
   v=[map_coordinates(a,coords[:,good],order=1,mode='constant',cval=np.nan) for coords in coordinates];c=v[0]-.5*(v[1]+v[2]);w=weights[good];ids=components[good];finite=np.isfinite(c)
   for component in [0,*sorted(set(ids))]:
    keep=finite if component==0 else finite&(ids==component)
    if keep.sum()<10:continue
    value=c[keep];weight=w[keep];order=np.argsort(value);median=float(value[order][np.searchsorted(np.cumsum(weight[order]),weight.sum()/2)]);rows.append({'operator':name,'variant':variant,'rotation_deg':angle,'h_px':h,'component':int(component),'samples':int(keep.sum()),'weighted_median_C':median,'weighted_mean_C':float(np.average(value,weights=weight)),'weighted_mean_abs_C':float(np.average(abs(value),weights=weight)),'rms_C':float(np.sqrt(np.average(value*value,weights=weight))),'positive_weight_fraction':float(weight[value>0].sum()/weight.sum())})
 for lid,tag in MAP.items():
  if lid==250:continue
  cached=O/f'ROI_L{lid}.npz';a=np.load(cached)['c1'] if cached.exists() else p.channel_box(lid,1,(4600,3000,6150,4550));measure(tag,'actual_V84',a.astype(float)/65535)
  for variant,folder in [('regenerated_baseline',O/'filters_baseline/products/filters'),('delivered_V85',O/'filters_selected')]:
   a=np.load(folder/(tag+'_u16.npy'),mmap_mode='r')[3000:4550,4600:6150];measure(tag,variant,a.astype(float)/65535)
  pf=O/('filters_physical_E3' if tag in ['01','04','05','06'] else 'filters_physical_T_E2')/'products/filters'/(tag+'_u16.npy')
  if pf.exists():a=np.load(pf,mmap_mode='r')[3000:4550,4600:6150];measure(tag,'physical_T_R02',a.astype(float)/65535)
  print('MARK_OPERATOR_DONE',tag,flush=True)
 a=np.load(O/'d4_baseline/products/sources/base_G.npy',mmap_mode='r')[3000:4550,4600:6150];measure('source_log_G','unchanged',np.log(np.maximum(a,1e-30)).astype(float))
 for variant,file in [('actual_V84','A_current_roi.tif'),('delivered_V85','Q_final_preserved_roi.tif')]:measure('native_composite_G',variant,tf.imread(O/file)[...,1].astype(float)/65535)
 save(out/'METRICS.json',{'rows':rows,'interpretation':'raw signed second normal difference; not automatic artifact classification or acceptance','units':'filter/composite encodedG normalized0..1; physical source logG','physical_inputs_unchanged':True});save(out/'COMPLETE.json',{'PASS':True,'rows':len(rows),'scope':'diagnostic calculation integrity only'});print('MARKS246_COMPLETE',len(rows))
if __name__=='__main__':guard();main()
