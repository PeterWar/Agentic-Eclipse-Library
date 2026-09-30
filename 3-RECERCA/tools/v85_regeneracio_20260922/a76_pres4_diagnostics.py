"""Fixed marks on common observed domain, with support loss reported separately."""
from a16_build_psb import *
from scipy.ndimage import map_coordinates
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
 assert json.loads((O/'filters_pres4_WOW_R02/COMPLETE.json').read_text())['PASS']
 out=O/'marks246_pres4_R02';out.mkdir();box=(4600,3000,6150,4550);x0,y0,x1,y1=box;sl=(slice(y0,y1),slice(x0,x1));geom=np.load(O/'marks246_R02/GEOMETRY.npz');pts=geom['points'];normals=geom['normals'];w=geom['weights'];ids=geom['component'];usable=geom['usable'];center=np.array([5361.768111973117,3775.747534140857])
 oldG=np.load(O/'d4_baseline/products/sources/base_G.npy',mmap_mode='r');newG=np.load(O/'domain_pres4_R02/sources/base_G.npy',mmap_mode='r');oldmask=np.load(O/'domain_v1/sources/support.npy',mmap_mode='r');newmask=np.load(O/'domain_pres4_R02/sources/support.npy',mmap_mode='r');v0=oldmask[sl]&np.isfinite(oldG[sl])&(oldG[sl]>0);v1=newmask[sl]&np.isfinite(newG[sl])&(newG[sl]>0);common=v0&v1;coverage=[];sampling={}
 for angle in [0,45,90,135,180,225,270,315]:
  a=np.deg2rad(angle);rot=np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]]);pp=(pts-center)@rot.T+center;nn=normals@rot.T
  for h in [2,4,8]:
   coords=[np.array([q[:,1]-y0,q[:,0]-x0]) for q in [pp,pp+h*nn,pp-h*nn]];g0=usable.copy();g1=usable.copy()
   for c in coords:
    g0&=map_coordinates(v0.astype(float),c,order=1,mode='constant',cval=0)>.999;g1&=map_coordinates(common.astype(float),c,order=1,mode='constant',cval=0)>.999
   sampling[(angle,h)]=(coords,g1)
   for k in [0,*sorted(set(ids))]:
    z=np.ones(len(ids),bool) if k==0 else ids==k
    coverage.append({'rotation_deg':angle,'h_px':h,'component':int(k),'old_triplets':int((g0&z).sum()),'common_triplets':int((g1&z).sum()),'lost_triplets':int((g0&~g1&z).sum()),'old_alpha_sum':float(w[g0&z].sum()),'common_alpha_sum':float(w[g1&z].sum())})
 rows=[]
 def measure(op,variant,a):
  for (angle,h),(coords,good) in sampling.items():
   sampled=[map_coordinates(a,c[:,good],order=1,mode='constant',cval=np.nan) for c in coords];d=sampled[0]-.5*(sampled[1]+sampled[2]);weights=w[good];components=ids[good]
   for k in [0,*sorted(set(ids))]:
    keep=np.isfinite(d)&(True if k==0 else components==k)
    if keep.sum()<10:continue
    q=d[keep];ww=weights[keep];rows.append({'operator':op,'variant':variant,'rotation_deg':angle,'h_px':h,'component':int(k),'samples':int(keep.sum()),'weighted_mean_C':float(np.average(q,weights=ww)),'weighted_mean_abs_C':float(np.average(abs(q),weights=ww)),'rms_C':float(np.sqrt(np.average(q*q,weights=ww)))})
 tags=['P04_WOW','P05_WOW_bilateral'];p=PSB(str(O/'V84_Pere_input.psb'))
 for tag in tags:
  lid=next(i for i,v in MAP.items() if v==tag);a=np.load(O/f'ROI_L{lid}.npz')['c1'];measure(tag,'actual_V84',a.astype(float)/65535)
  for variant,folder in [('R01',O/'filters_selected'),('preS4',O/'filters_pres4_WOW_R02/products/filters')]:measure(tag,variant,np.asarray(np.load(folder/(tag+'_u16.npy'),mmap_mode='r')[sl],float)/65535)
 measure('source_log_G','R01',np.log(np.maximum(oldG[sl],1e-30)).astype(float));measure('source_log_G','preS4',np.log(np.maximum(newG[sl],1e-30)).astype(float))
 loss={'ROI':list(box),'old_valid':int(v0.sum()),'new_valid':int(v1.sum()),'lost_effective':int((v0&~v1).sum()),'gained':int((v1&~v0).sum()),'lost_support_only':int((oldmask[sl]&~newmask[sl]).sum()),'coverage':coverage};assert loss['lost_effective']==2880 and loss['lost_support_only']==2862 and loss['gained']==0
 save(out/'SUPPORT_LOSS.json',loss);save(out/'METRICS.json',{'rows':rows,'domain':'same common observed domain for both variants; frozen original normal geometry; bilinear validity>.999','limits':['lost samples excluded from BOTH variants','reduced contrast not classification of artifact','invalid output requires explicit layer-mask exclusion before any native candidate','preS4 experimental only']})
 bx=(4830,3300,5240,4030);a,b,c,d=bx;ss=(slice(b-y0,d-y0),slice(a-x0,c-x0));marks=np.load(O/'ROI_L246.npz')['c-1'][ss]>0;extent=[a,c,d,b]
 fig,axes=plt.subplots(2,3,figsize=(11,13),squeeze=False)
 for i,tag in enumerate(tags):
  lid=next(j for j,v in MAP.items() if v==tag);arr0=p.channel_box(lid,1,bx);vals=[arr0,np.load(O/'filters_selected'/(tag+'_u16.npy'),mmap_mode='r')[b:d,a:c],np.load(O/'filters_pres4_WOW_R02/products/filters'/(tag+'_u16.npy'),mmap_mode='r')[b:d,a:c]];lo,hi=np.percentile(arr0[v0[ss]],[1,99])
  for j,(label,value) in enumerate(zip(['V84 Pere','V85 R01','Pre-S4 candidate'],vals)):
   ax=axes[i,j];valid=v1[ss] if j==2 else v0[ss];ax.imshow(np.ma.array(value,mask=~valid),cmap='gray',vmin=lo,vmax=hi,extent=extent,interpolation='nearest');ax.contour(marks,levels=[.5],colors='#ff6c6c',linewidths=.4,extent=extent,origin='upper');ax.set_title(tag+'\n'+label);ax.set_xticks([]);ax.set_yticks([])
 fig.suptitle('Same limits per row; unsupported source is white, not recovered corona.');fig.tight_layout(rect=[0,0,1,.98]);fig.savefig(out/'WOW_comparison.png',dpi=150);plt.close(fig)
 save(out/'COMPLETE.json',{'PASS':True,'scope':'diagnostic integrity','rows':len(rows)});print('PRES4_MARKS_COMPLETE',len(rows),flush=True)

if __name__=='__main__':guard();main()
