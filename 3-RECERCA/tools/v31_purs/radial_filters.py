"""Published radial operators; no external high-pass or ring correction."""
from common import *
from scipy.stats import rankdata
import gc
def radial(a,m,r):
 ri=np.floor(r).astype('int32');nr=int(ri.max())+1
 ids=ri[m];v=a[m].astype('float64')
 count=np.bincount(ids,minlength=nr);s=np.bincount(ids,weights=v,minlength=nr);s2=np.bincount(ids,weights=v*v,minlength=nr)
 mean=np.divide(s,count,out=np.zeros(nr),where=count>0)
 std=np.sqrt(np.maximum(0,np.divide(s2,count,out=np.zeros(nr),where=count>0)-mean*mean))
 # Evaluate the continuous profiles between the centers of 1-pixel measurement annuli.
 nodes=np.arange(nr)+.5;good=count>0
 mu=np.interp(r,nodes[good],mean[good]).astype('float32')
 sd=np.interp(r,nodes[good],std[good]).astype('float32')
 nrgf=np.divide(a-mu,sd,out=np.zeros_like(a),where=sd>0)
 del mu,sd,v,ids,s,s2;gc.collect()
 # RHEF's rank operation is performed within each explicit annulus, with equal ties.
 flat=np.flatnonzero(m);order=np.argsort(ri.ravel()[flat],kind='stable');flat=flat[order]
 counts=np.bincount(ri.ravel()[flat],minlength=nr);cuts=np.r_[0,np.cumsum(counts)]
 rhef=np.zeros_like(a).ravel();af=a.ravel()
 for i in range(nr):
  ix=flat[cuts[i]:cuts[i+1]]
  if len(ix):rhef[ix]=rankdata(af[ix],method='average')/len(ix)
 return nrgf,rhef.reshape(a.shape),{'annulus_width_px':1,'NRGF_profile_evaluation':'linear interpolation between annulus centers; no post-filter correction','RHEF_rank':'average ranks for ties / population; upsilon=None','count_min':int(count[good].min()),'count_max':int(count.max())}
def main():
 a,m=readbase();a=np.array(a);r,_=coords();n,h,rep=radial(a,m,r)
 save_output('P01_NRGF',n,m,{**rep,'paper':'Morgan, Habbal & Woo 2006','equation':'(B-mean_theta(r))/std_theta(r)','coverage':'statistics of actual observed pixels; no zero-filled missing sky'})
 save_output('P02_RHEF',h,m,{**rep,'paper':'Gilly & Cranmer 2025','vignette':None,'coverage':'rank only actual observed pixels'},display=[0,1])
if __name__=='__main__':main()
