from common58 import *
from scipy.ndimage import gaussian_filter1d
import cv2,time

def rhef_native_cdf(a,m,r,t,S_deg,step_deg,dr=.5,nt=16384,cx=CX,cy=CY,quiet=False):
 # CDFs use samples on fixed radii; evaluate them at the original pixel's value.
 # An additive radial log normalizer transports queries between neighboring radii,
 # and is rank-invariant at each exact radius. It does not alter output ring levels.
 idx=np.flatnonzero(m);rv=r.ravel()[idx];ri=np.floor(rv).astype(int);lv=np.log(a.ravel()[idx]);n=np.bincount(ri);mu=np.bincount(ri,weights=lv)/np.maximum(n,1);nodes=np.arange(len(n));ok=n>0;mu=np.interp(nodes,nodes[ok],mu[ok]);mu=gaussian_filter1d(mu,16,mode='nearest');norm=np.zeros(a.shape,np.float32);norm.ravel()[idx]=lv-np.interp(rv,nodes+.5,mu);r0=max(0,int(np.floor(rv.min()))-1);nr=int(np.ceil((rv.max()-r0)/dr))+2;b=np.floor((rv-r0)/dr).astype('int32');fr=((rv-r0)/dr-b).astype('float32');ang=np.degrees(t.ravel()[idx])%360;K=int(round(360/step_deg));k0=(ang/step_deg).astype('int32')%K;wk=(ang/step_deg-k0).astype('float32');query=norm.ravel()[idx];order=np.argsort(b,kind='stable');cuts=np.searchsorted(b[order],np.arange(nr+1));theta=np.arange(nt,dtype='float32')*2*np.pi/nt;half=int(round(nt*S_deg/720));centers=np.round(np.arange(K)*step_deg*nt/360).astype(int);sectors=[(np.arange(-half,half+1)+c)%nt for c in centers];out=np.zeros(len(idx),np.float32);denout=np.zeros(len(idx),np.float32);mf=m.astype('float32');cache={};t0=time.time()
 def cells(i):
  rad=np.float32(r0+i*dr);mx=(cx+rad*np.cos(theta))[None,:].astype('float32');my=(cy+rad*np.sin(theta))[None,:].astype('float32');wm=cv2.remap(mf,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)[0];p=cv2.remap(norm,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)[0]/np.maximum(wm,1e-8);good=wm>.999
  return [np.sort(p[ix][good[ix]]) for ix in sectors]
 for i in range(nr):
  ii=order[cuts[i]:cuts[i+1]]
  if not len(ii):continue
  for j in [i,i+1]:
   if j not in cache:cache[j]=cells(j)
  for j,wr in [(i,1-fr[ii]),(i+1,fr[ii])]:
   for kk,ww in [(k0[ii],1-wk[ii]),((k0[ii]+1)%K,wk[ii])]:
    for k in np.unique(kk):
     vals=cache[j][k]
     if len(vals)<50:continue
     use=kk==k;ix=ii[use];weight=wr[use]*ww[use];rank=(np.searchsorted(vals,query[ix],side='left')+np.searchsorted(vals,query[ix],side='right'))/(2*len(vals));out[ix]+=weight*rank;denout[ix]+=weight
  for j in list(cache):
   if j<i:del cache[j]
  if not quiet and i%1000==0:print('nativeCDF',S_deg,i,nr,round(time.time()-t0,1),flush=True)
 result=np.full(a.shape,np.nan,np.float32);result.ravel()[idx]=np.where(denout>0,out/np.maximum(denout,1e-9),np.nan);return result
