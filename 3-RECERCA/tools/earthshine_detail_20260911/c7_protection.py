from detail_common import *
import tifffile
b=tifffile.imread(PREV/'D3_baseline_no_manual_grade_RGBA.tif');a=tifffile.imread(OUT/'C4_Photoshop_RGBA.tif');m=np.load(OUT/'C4_inherited_mask_roi.npy');ar=a[3077:4477,4677:6077,:3].astype(int);br=b[3077:4477,4677:6077,:3].astype(int);chroma=(ar-ar[...,1,None])-(br-br[...,1,None]);prom=(br[...,0]-br[...,1])>1000
# Region outside the source rectangle is literally unchanged in actual exports.
outside=True
for lo,hi in [(0,3077),(4477,7506)]:outside &= np.array_equal(a[lo:hi],b[lo:hi])
for lo,hi in [(0,4677),(6077,10551)]:outside &= np.array_equal(a[3077:4477,lo:hi],b[3077:4477,lo:hi])
report=dict(outside_source_rectangle_exact=bool(outside),alpha_exact=bool(np.array_equal(a[...,3],b[...,3])),prominence_pixels=int(prom.sum()),prominence_chroma_max_change_DN16=int(abs(chroma[prom]).max()),all_source_chroma_max_change_DN16=int(abs(chroma).max()),source_mask_zero_rgb_max_change_DN16=int(abs(ar-br)[m==0].max()),comparison='Native Photoshop candidate versus native no-manual-grade baseline; original grade intentionally not active in V48')
report['PASS']=report['outside_source_rectangle_exact'] and report['alpha_exact'] and report['prominence_chroma_max_change_DN16']<=6 and report['source_mask_zero_rgb_max_change_DN16']<=6
save('C7_actual_protection.json',report);assert report['PASS'],report;print(report,flush=True)
