"""Auchere et al. 2023 WOW, streaming B3 a-trous, with physical-support boundaries.
No denoising, gamma component, scale synthesis weights, H1, or radial normalizer.
Fully supported inputs are checked against the author's watroo implementation.
"""
from common import *
import numexpr as ne
import gc
import ctypes
K=np.array([1,4,6,4,1],np.float32)/16
lib=ctypes.CDLL(str(D/'sparse_conv.dylib'))
lib.sparse_b3.argtypes=[ctypes.c_void_p]*3+[ctypes.c_int]*4
lib.sparse_b3.restype=None
def conv(a,s):
 # Sparse separable stencil is mathematically the author's filter2D dilated B3 kernel.
 # Chunked gathering prevents padding an enormous array at the coarsest scales.
 a=np.ascontiguousarray(a,np.float32);h,w=a.shape
 out=np.empty_like(a);tmp=np.empty_like(a)
 lib.sparse_b3(a.ctypes.data,tmp.ctypes.data,out.ctypes.data,h,w,2**s,4)
 return out
def nconv(a,m,s):
 den=conv(m.astype('float32'),s)
 return conv(np.where(m,a,0),s)/np.maximum(den,1e-20)
def bilateral_conv(a,m,s):
 # Same 25-point B3 kernel, range Gaussian from equation18; no radius approximation.
 h,w=a.shape;d=2**s;out=np.zeros_like(a);den=np.zeros_like(a)
 # Work in row blocks to keep temporaries bounded. Reflect only the rectangular edge.
 for y0 in range(0,h,192):
  y1=min(h,y0+192);center=a[y0:y1];moment=np.zeros_like(center);moment2=np.zeros_like(center);mass=np.zeros_like(center)
  for dy,ky in zip(range(-2,3),K):
   iy=np.mod(np.arange(y0,y1)+dy*d,2*h);iy=np.where(iy<h,iy,2*h-1-iy)
   for dx,kx in zip(range(-2,3),K):
    ix=np.mod(np.arange(w)+dx*d,2*w);ix=np.where(ix<w,ix,2*w-1-ix)
    valid=m[iy[:,None],ix];delta=np.where(valid,a[iy[:,None],ix]-center,0);k=float(ky*kx)
    moment+=k*delta;moment2+=k*delta*delta;mass+=k*valid
  mean=moment/np.maximum(mass,1e-20)
  vv=np.maximum(moment2/np.maximum(mass,1e-20)-mean*mean,1e-20)
  num=np.zeros_like(center);norm=np.zeros_like(center)
  for dy,ky in zip(range(-2,3),K):
   iy=np.mod(np.arange(y0,y1)+dy*d,2*h);iy=np.where(iy<h,iy,2*h-1-iy)
   for dx,kx in zip(range(-2,3),K):
    ix=np.mod(np.arange(w)+dx*d,2*w);ix=np.where(ix<w,ix,2*w-1-ix)
    valid=m[iy[:,None],ix];v=np.where(valid,a[iy[:,None],ix],0);k=float(ky*kx)
    weight=ne.evaluate('k*exp(-0.5*(center-v)**2/vv)')*valid
    num+=(v-center)*weight;norm+=weight
  out[y0:y1]=center+num/np.maximum(norm,1e-20)
 return out
def wow(a,m,n_scales=10,bilateral=False,progress=True):
 c=np.where(m,a,0).astype('float32');out=np.zeros_like(c)
 for s in range(n_scales):
  nxt=bilateral_conv(c,m,s) if bilateral else nconv(c,m,s)
  wave=c-nxt
  wave[np.abs(wave)<=8*np.finfo('float32').eps*np.maximum(np.abs(c),np.abs(nxt))]=0
  power=nconv(wave*wave,m,s);amp=np.sqrt(np.maximum(power,1e-20))
  out+=wave/amp;c=np.where(m,nxt,0)
  if progress:log(('WOW bilateral ' if bilateral else 'WOW ')+'scale '+str(s))
  del wave,power,amp;gc.collect()
 # Coarsest plane normalized by its global standard deviation, matching author code.
 sd=float(np.std(c[m],dtype='float64'))
 if sd>16*np.finfo('float32').eps*float(np.max(np.abs(c[m]))):out+=c/sd
 return out
def main():
 a,m=readbase();a=np.array(a);scales=int(np.round(np.log2(min(a.shape))-np.log2(5)))
 for bilateral,tag in [(False,'P04_WOW'),(True,'P05_WOW_bilateral')]:
  if (D/'receipts'/(tag+'.json')).exists():continue
  out=wow(a,m,scales,bilateral)
  save_output(tag,out,m,{'paper':'Auchere et al. 2023 A&A670 A66 equations4-9,16-18','author_reference':'watroo','scales':scales,'B3_kernel_1d':K.tolist(),'weights':'all1','h':0,'denoise':False,'reason_no_denoise':'no validated full-canvas HDR noise sigma','bilateral':1 if bilateral else None,'boundary':'mirror at rectangle; incomplete normalized convolution at actual missing support'})
  del out;gc.collect()
if __name__=='__main__':main()
