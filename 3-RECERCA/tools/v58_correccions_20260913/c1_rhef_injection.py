from filters58 import *
claim();# Analytic reference has continuous radius; fixed sector centers/interpolation identical to tested algorithm.
H0=1200;yy,xx=np.mgrid[:H0,:H0];rr=np.hypot(xx-600,yy-600);tt=np.arctan2(yy-600,xx-600);m=(rr>220)&(rr<540)
def field(r,t,lam=None,phase=0):
 z=.2*np.sin(3*t)+.07*np.cos(7*t)+.015*np.cos(17*t)
 if lam:z=z+.004*np.cos(2*np.pi*r/lam+phase)*np.sin(19*t+.3)
 return np.exp(-(r-300)/44+z)
a=field(rr,tt).astype('float32');rads=np.arange(300,481,2.13);theta=np.arange(0,360,2.3);rtest=rads[:,None];ttest=np.deg2rad(theta[None,:]);mx=600+rtest*np.cos(ttest);my=600+rtest*np.sin(ttest);rep={}
for deg in [60.,30.]:
 step=deg/4;K=int(360/step);k0=np.floor(theta/step).astype(int);w=theta/step-k0;base=rhef_local(a,m,rr,tt,deg,step);basep=map_coordinates(base,[my,mx],order=1);ref0=None
 def exact(lam=None,phase=0):
  out=np.zeros((len(rads),len(theta)));v=field(rtest,ttest,lam,phase)
  for k in range(K):
   at=np.deg2rad(np.linspace(k*step-deg/2,k*step+deg/2,4096));val=np.sort(field(rtest,at[None,:],lam,phase),axis=1)
   for kk,wt in [(k0,1-w),((k0+1)%K,w)]:
    inds=np.flatnonzero(kk==k)
    for row in range(len(rads)):
     out[row,inds]+=wt[inds]*np.searchsorted(val[row],v[row,inds])/4096
  return out
 ref0=exact();rs=[]
 for lam in [24.,40.,64.,96.]:
  for phase in [0.,np.pi/2]:
   q=rhef_local(field(rr,tt,lam,phase).astype('float32'),m,rr,tt,deg,step);delta=map_coordinates(q,[my,mx],order=1)-basep;expected=exact(lam,phase)-ref0;gain=float(np.sum(delta*expected)/np.sum(expected**2));rms=float(np.sqrt(np.mean((delta-expected)**2)));rs.append(dict(wavelength=lam,phase=phase,gain=gain,rmse=rms,PASS=.9<=gain<=1.1));print(deg,lam,phase,gain,flush=True)
 rep[str(deg)]=rs
save('C1_rhef_injections.json',rep)
