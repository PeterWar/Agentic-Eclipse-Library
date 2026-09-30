from common import *
from scipy.ndimage import map_coordinates
def main():
 v=np.load(FIX/'vixen_corrected_G.npy',mmap_mode='r'); s=np.load(FIX/'sony_corrected_G.npy',mmap_mode='r')
 mv=np.load(OLD/'vixen_support.npy');ms=np.load(OLD/'sony_support.npy')
 gain=0.3411462604999542
 r,t=coords(); wv=(1-smooth(r/RS,2,2.65)).astype('float32')*mv
 wv=np.where(ms,wv,mv.astype('float32'));ws=(1-wv)*ms
 m=mv|ms; a=np.where(mv,v,0)*wv+np.where(ms,s,0)*ws*gain
 assert a.shape==(H,W) and np.isfinite(a[m]).all()
 assert np.array_equal(m,np.load(OLD/'fusion_support.npy'))
 a[~m]=0;np.save(C/'base_G.npy',a);np.save(C/'support.npy',m)
 np.save(C/'weight_vixen.npy',wv)
 iy,ix=np.where(m&(a<=0));savejson(D/'receipts/base_nonpositive.json',{'count':len(ix),'yx':np.stack([iy,ix],axis=1),'values':a[iy,ix],'radii_R':r[iy,ix]/RS,'treatment':'preserved in linear scientific base; only algorithms whose published definition clips nonpositive input do so, explicitly'})
 rep={'source':'corrected linear G radiance, one global inter-train gain; original physical blend weights','shape':[H,W],'gain_sony_to_vixen':gain,'sun':[CX,CY,RS],'observed_pixels':int(m.sum()),'nonpositive_observed':int((a[m]<=0).sum()),'source_files':{str(p):sha(p) for p in [FIX/'vixen_corrected_G.npy',FIX/'sony_corrected_G.npy',FIX/'offset_model.json',OLD/'vixen_support.npy',OLD/'sony_support.npy']},'base_sha256':sha(C/'base_G.npy'),'support_sha256':sha(C/'support.npy'),'FOV_resample_crop':'none','filter_input_channel':'G, monochrome; not asserted to be RGB luminance'}
 savejson(D/'receipts/base.json',rep);log('base saved')
if __name__=='__main__':main()
