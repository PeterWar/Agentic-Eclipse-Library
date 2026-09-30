from common import *
import ctypes, importlib.util
spec=importlib.util.spec_from_file_location('nafe_published',D/'sources/nafe_published.py');ref=importlib.util.module_from_spec(spec);spec.loader.exec_module(ref)
lib=ctypes.CDLL(str(D/'nafe_native.dylib'))
P=ctypes.c_void_p;I=ctypes.c_int;F=ctypes.c_double
lib.nafe_points.argtypes=[P,P,I,I,I,P,F,P,P,I,P];lib.nafe_points.restype=None
lib.nafe_full.argtypes=[P,P,I,I,I,P,F,I,P];lib.nafe_full.restype=None
def points(a,m,n,sigma,y,x):
 a=np.ascontiguousarray(a,np.float32);m=np.ascontiguousarray(m,np.uint8);k=np.ascontiguousarray(ref.membership_function(n),np.float64)
 y=np.ascontiguousarray(y,np.int32);x=np.ascontiguousarray(x,np.int32);out=np.zeros(len(y),np.float64)
 lib.nafe_points(a.ctypes.data,m.ctypes.data,*a.shape,n,k.ctypes.data,sigma,y.ctypes.data,x.ctypes.data,len(y),out.ctypes.data);return out
def test():
 rng=np.random.default_rng(193);rows=[]
 for scale in [1,10,100,10000]:
  a=(rng.lognormal(1,.8,(160,160))*scale).astype('float32');m=np.ones_like(a,bool);n=65;sigma=5
  ys=rng.integers(0,160,100);xs=rng.integers(0,160,100);our=points(a,m,n,sigma,ys,xs);r=ref.Im(a,n,sigma);expected=np.array([r.y1((int(y),int(x))) for y,x in zip(ys,xs)])
  err=float(np.max(np.abs(our-expected)));rows.append({'input_scale':scale,'n':n,'max_abs_error':err});assert err<2e-6,(scale,err)
 # Constant-image case tests histogram auto-range and broad Gaussian tails.
 a=np.ones((80,80),np.float32)*400;m=np.ones_like(a,bool);o=points(a,m,65,5,[0,40],[0,40]);r=ref.Im(a,65,5);e=np.array([r.y1((0,0)),r.y1((40,40))]);err=float(np.max(np.abs(o-e)));assert err<2e-6,err
 savejson(D/'receipts/NAFE_reference_validation.json',{'PASS':True,'reference_sha256':sha(D/'sources/nafe_published.py'),'max_tolerance':2e-6,'rows':rows,'constant_max_error':err,'samples':402});log('NAFE reference checks passed')
def main():
 test();a,m=readbase();a=np.maximum(a,0);limits=[0,float(a[m].max())];n=65;sigma=5.;k=np.ascontiguousarray(ref.membership_function(n),np.float64);mask=m.astype('uint8')
 det=np.lib.format.open_memmap(C/'NAFE_detail.npy',mode='w+',dtype='float32',shape=a.shape)
 log('NAFE native n65 start');lib.nafe_full(a.ctypes.data,mask.ctypes.data,*a.shape,n,k.ctypes.data,sigma,6,det.ctypes.data);det.flush()
 out=.2*(a/limits[1])**(1/2.4)+.8*det
 save_output('P06_NAFE',out,m,{'paper':'Druckmuller2013; public implementation ebuchlin/medocimage','n':n,'ngauss':12,'local_histogram_bins':500,'sigma_intensity':sigma,'sigma_meaning':'declared additive-noise suppression parameter in base G units; not claimed calibrated sensor sigma','a':limits,'gamma':2.4,'gamma_weight':.2,'detail_weight':.8,'boundary':'only actual observed neighbors contribute; no zero-valued missing sky','native_reference_tolerance':2e-6})
if __name__=='__main__':
 import sys
 test() if '--test' in sys.argv else main()
