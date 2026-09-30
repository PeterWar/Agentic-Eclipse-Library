"""Numerical quadrature of the published ACHF precursor, and SWAP's off-limb recipe.
Polar sampling is internal to integration only. Native output coordinates/FOV are unchanged.
"""
from common import *
import gc
from scipy.ndimage import gaussian_filter1d, median_filter
from scipy.special import erf
def integrated_kernel(s):
 # Integrate the published +/-2sigma Gaussian over each quadrature cell.
 # A partially covered endpoint cell loses weight continuously as s changes,
 # instead of abruptly dropping a sample still weighted exp(-2).
 radius=int(np.ceil(2*s+.5));j=np.arange(-radius,radius+1,dtype='float64')
 lo=np.maximum(j-.5,-2*s);hi=np.minimum(j+.5,2*s)
 k=np.where(hi>lo,erf(hi/(np.sqrt(2)*s))-erf(lo/(np.sqrt(2)*s)),0).astype('float32')
 return k/k.sum()
def make_polar(a,m,nt=32760,dr=.5):
 r,_=coords();r0=max(0,float(np.floor(r[m].min()-64)));r1=float(np.ceil(r[m].max()+64));rv=np.arange(r0,r1+dr,dr);th=np.arange(nt,dtype='float64')*(2*np.pi/nt)
 f=np.lib.format.open_memmap(C/f'polar_{nt}_numerator.npy',mode='w+',dtype='float32',shape=(len(rv),nt))
 w=np.lib.format.open_memmap(C/f'polar_{nt}_support.npy',mode='w+',dtype='float32',shape=f.shape)
 af=np.where(m,a,0).astype('float32');mf=m.astype('float32')
 for i in range(0,len(rv),96):
  rr=rv[i:i+96,None];x=(CX+rr*np.cos(th)).astype('float32');y=(CY+rr*np.sin(th)).astype('float32')
  f[i:i+96]=cv2.remap(af,x,y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
  w[i:i+96]=cv2.remap(mf,x,y,cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT)
 f.flush();w.flush();log('polar quadrature prepared '+str(nt));return f,w,rv
def back(p,rv,shape=(H,W),origin=(0,0)):
 r,t=coords(shape,origin);nt=p.shape[1];out=np.empty(shape,np.float32)
 # Append periodic endpoint. OpenCV limits each source dimension to <32767.
 pp=np.empty((p.shape[0],nt+1),np.float32);pp[:,:nt]=p;pp[:,-1]=p[:,0]
 for y in range(0,shape[0],128):
  xm=(np.mod(t[y:y+128],2*np.pi)*nt/(2*np.pi)).astype('float32');ym=((r[y:y+128]-rv[0])/(rv[1]-rv[0])).astype('float32')
  out[y:y+128]=cv2.remap(pp,xm,ym,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
 return out
def precursor_mean(f,w,rv,sigma):
 nr,nt=f.shape;dr=rv[1]-rv[0];sd=sigma/dr
 kr=integrated_kernel(sd)
 a=np.lib.format.open_memmap(C/f'precursor_{nt}_{sigma}_polar.npy',mode='w+',dtype='float32',shape=f.shape)
 # Two separable Gaussian factors of eq5.1 with exactly the stated +/-2sigma support.
 n=np.empty(f.shape,np.float32);d=np.empty(w.shape,np.float32)
 for x in range(0,nt,1024):
  n[:,x:x+1024]=cv2.sepFilter2D(np.asarray(f[:,x:x+1024]),-1,np.array([1],np.float32),kr,borderType=cv2.BORDER_CONSTANT)
  d[:,x:x+1024]=cv2.sepFilter2D(np.asarray(w[:,x:x+1024]),-1,np.array([1],np.float32),kr,borderType=cv2.BORDER_CONSTANT)
 for y,r in enumerate(rv):
  st=sigma/(r*(2*np.pi/nt));kt=integrated_kernel(st);rad=len(kt)//2
  nn=np.pad(n[y],(rad,rad),mode='wrap')[None,:];dd=np.pad(d[y],(rad,rad),mode='wrap')[None,:]
  nn=cv2.filter2D(nn,-1,kt[None,:],borderType=cv2.BORDER_CONSTANT)[0,rad:rad+nt]
  dd=cv2.filter2D(dd,-1,kt[None,:],borderType=cv2.BORDER_CONSTANT)[0,rad:rad+nt]
  a[y]=nn/np.maximum(dd,1e-20)
 a.flush();del n,d;gc.collect();return a
def main():
 a,m=readbase();r,_=coords();rv=np.arange(max(0,float(np.floor(r[m].min()-64))),float(np.ceil(r[m].max()+64))+.5,.5)
 f=np.load(C/'polar_32760_numerator.npy',mmap_mode='r');w=np.load(C/'polar_32760_support.npy',mmap_mode='r')
 for sigma,tag in [(16,'P07_ACHF_precursor16'),(32,'P08_ACHF_precursor32')]:
  p=precursor_mean(f,w,rv,sigma);low=back(p,rv);out=a-low
  save_output(tag,out,m,{'source':'Druckmullerova thesis, section5.2 equations5.1-5.2','identity':'published ACHF precursor, not proprietary Corona ACHF','sigma_px':sigma,'radial_support':[-2*sigma,2*sigma],'tangential_arc_support':[-2*sigma,2*sigma],'input':'linear corrected G, no log/contrast/H1','quadrature':{'dr_px':.5,'angular_nodes':32760,'interpolation':'bilinear inside quadrature only; native output grid'},'boundary':'incomplete convolution normalized by observed support','notation':'coherent offsets u,v; fixes the absolute/offset notation conflict in printed eq5.2'})
  del low,out,p;gc.collect()
if __name__=='__main__':main()
