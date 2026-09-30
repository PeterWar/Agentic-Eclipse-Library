from common58 import *
import cv2,time
# Fixed-radius polar CDF: radial bins no longer contain samples at different brightness radii.
def rhef_fixed_radius(a,m,r,t,S_deg,step_deg,dr=.5,nt=16384,cx=CX,cy=CY,quiet=False):
 h,w=a.shape;r0=max(0,int(np.floor(r[m].min()))-2);nr=int(np.ceil((r.max()-r0)/dr))+3;theta=np.arange(nt,dtype='float32')*2*np.pi/nt;logA=np.log(np.maximum(np.where(m,a,1e-12),1e-12)).astype('float32');mask=m.astype('float32');Q=np.zeros((nr,nt),np.float32);V=np.zeros_like(Q);K=int(round(360/step_deg));half=int(round(nt*S_deg/720));centers=np.round(np.arange(K)*step_deg*nt/360).astype(int);k0=np.floor(np.arange(nt)*360/nt/step_deg).astype(int)%K;k1=(k0+1)%K;wt=(np.arange(nt)*360/nt/step_deg-np.floor(np.arange(nt)*360/nt/step_deg)).astype('float32');tt0=time.time()
 for start in range(0,nr,64):
  rs=(r0+(np.arange(start,min(start+64,nr),dtype='float32'))*dr)[:,None];mx=cx+rs*np.cos(theta)[None,:];my=cy+rs*np.sin(theta)[None,:];valid=cv2.remap(mask,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);num=cv2.remap(logA*mask,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);p=num/np.maximum(valid,1e-8)
  for j in range(len(rs)):
   good=valid[j]>.999;v=p[j];acc=np.zeros(nt,np.float32);den=np.zeros(nt,np.float32)
   for k in range(K):
    ix=(np.arange(-half,half+1)+centers[k])%nt;vals=np.sort(v[ix][good[ix]])
    if len(vals)<max(50,int(.1*len(ix))):continue
    for kk,weight in [(k0,1-wt),(k1,wt)]:
     use=(kk==k)&good;rk=(np.searchsorted(vals,v[use],side='left')+np.searchsorted(vals,v[use],side='right'))/(2*len(vals));acc[use]+=rk*weight[use];den[use]+=weight[use]
   Q[start+j]=acc/np.maximum(den,1e-8);V[start+j]=(den>.99)&good
  if not quiet and start%1024==0:print('fixed-radius',S_deg,start,nr,round(time.time()-tt0,1),flush=True)
 # Periodic azimuth; validity-normalized interpolation back to the existing rectangular pixel grid.
 ext=np.concatenate([Q[:,-1:],Q,Q[:,:1]],axis=1);vm=np.concatenate([V[:,-1:],V,V[:,:1]],axis=1);mx=(np.mod(t,2*np.pi)*nt/(2*np.pi)+1).astype('float32');my=((r-r0)/dr).astype('float32');weight=cv2.remap(vm,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT);out=cv2.remap(ext*vm,mx,my,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)/np.maximum(weight,1e-8);return np.where(m&(weight>.99),out,np.nan).astype('float32')
