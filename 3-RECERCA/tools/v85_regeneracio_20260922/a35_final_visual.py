from a16_build_psb import *
import tifffile as tf
from PIL import Image,ImageCms
import io

def main():
 z=np.load(O/'current_lunar_support.npz');x0,y0,x1,y1=map(int,z['box']);moon=z['support'];roi_m=np.zeros((1550,1550),bool);roi_m[y0-3000:y1-3000,x0-4600:x1-4600]=moon
 a=tf.imread(O/'A_current_roi.tif');q=tf.imread(O/'Q_final_preserved_roi.tif');pre=tf.imread(O/'Q_final_preplate_roi.tif');u=tf.imread(O/'Q_final_unfiltered_roi.tif');c=tf.imread(O/'C_unfiltered_roi.tif')
 plate=np.zeros_like(roi_m);plate[493:867,308:436]=tf.imread(O/'Moon_V84_preserved.tif')[:,:,3]>0
 mark=np.load(O/'ROI_L251.npz')['c-1']>1000;y,x=np.mgrid[3000:4550,4600:6150];mark&=np.hypot(y-3775.747534140857,x-5361.768111973117)>480
 assert mark.sum()==22857
 assert np.array_equal(q[roi_m],a[roi_m]);assert np.array_equal(q[~plate],pre[~plate]);assert not np.any(q[:,:,0][mark]>.999*65535)
 record={'scope':'native composite integrity and marked-area clipping; no universal artifact-free claim','moon_pixels':int(roi_m.sum()),'moon_changed':int(np.any(a!=q,axis=2)[roi_m].sum()),'moon_max_DN16':int(np.abs(a.astype(np.int32)-q)[roi_m].max()),'outside_plate_changed':int(np.any(q!=pre,axis=2)[~plate].sum()),'marked_pixels':int(mark.sum()),'red_clip_threshold':.999,'original_unfiltered_red_clip_percent':float(np.mean(c[:,:,0][mark]>.999*65535)*100),'final_red_clip_percent':float(np.mean(q[:,:,0][mark]>.999*65535)*100),'final_unfiltered_red_clip_percent':float(np.mean(u[:,:,0][mark]>.999*65535)*100)}
 save(O/'FINAL_NATIVE_VISUAL_QA.json',record)
 for name in ['Q_final_preplate','Q_final_preserved','Q_final_unfiltered']:
  for size in ['roi','full']:
   p=O/(name+'_'+size+'.tif');arr=tf.imread(p)
   with tf.TiffFile(p) as f:icc=f.pages[0].tags[34675].value
   im=Image.fromarray(np.uint8(arr/257));im=ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),outputMode='RGB');im.save(p.with_suffix('.png'))
 print(json.dumps(record,indent=2))
if __name__=='__main__':guard();main()
