"""Native V48 versus native V49 readback: unchanged context and solar structure."""
from full_delta_common import *
import tifffile
b=tifffile.imread(SRC/'C4_Photoshop_RGBA.tif');a=tifffile.imread(OUT/'E0_Photoshop_RGBA.tif');m=np.load(OUT/'E0_inherited_mask_roi.npy');ar=a[Y0:Y0+N,X0:X0+N,:3].astype(int);br=b[Y0:Y0+N,X0:X0+N,:3].astype(int);chroma=(ar-ar[...,1,None])-(br-br[...,1,None]);prom=(br[...,0]-br[...,1])>1000
outside=True;outside_max=0
for aa,bb in [(a[:Y0],b[:Y0]),(a[Y0+N:],b[Y0+N:]),(a[Y0:Y0+N,:X0],b[Y0:Y0+N,:X0]),(a[Y0:Y0+N,X0+N:],b[Y0:Y0+N,X0+N:])]:
    outside &= np.array_equal(aa,bb)
    if not np.array_equal(aa,bb):outside_max=max(outside_max,int(np.max(abs(aa.astype(int)-bb.astype(int)))))
rr=np.hypot(*np.mgrid[:N,:N].astype(float)-np.array([CY,CX])[:,None,None]);solar=prom&(rr>454);d=ar-br
report=dict(outside_source_rectangle_exact=bool(outside),outside_max_DN16=outside_max,alpha_exact=bool(np.array_equal(a[...,3],b[...,3])),prominence_pixels=int(prom.sum()),prominence_chroma_max_change_DN16=int(abs(chroma[prom]).max()),all_source_chroma_max_change_DN16=int(abs(chroma).max()),source_mask_zero_rgb_max_change_DN16=int(abs(d[m==0]).max()),solar_prominence_luminance_delta_percentiles_DN16=np.percentile(d[solar],[0,1,50,99,100]).tolist(),comparison='Native Photoshop V49 versus native saved V48; all original layers and empirical join unchanged')
report['PASS']=report['outside_source_rectangle_exact'] and report['alpha_exact'] and report['prominence_chroma_max_change_DN16']<=6 and report['source_mask_zero_rgb_max_change_DN16']<=6
save('E2_actual_protection.json',report);assert report['PASS'],report;print(report,flush=True)
