"""Measure native visibility-only comparisons, leaving source RGB/masks exact.
Do not attribute the empirical display-join mask to pure physical occultation.
"""
from joint_common import *
import tifffile
from PIL import Image
from scipy.ndimage import map_coordinates

paths=json.loads((OUT/'C0_composition_diagnostic.json').read_text())['exports'];imgs={};X0=4677;Y0=3077
for key,path in paths.items():
    with tifffile.TiffFile(path) as tf:
        a=tf.asarray();assert a.shape[:2]==(7506,10551) and a.dtype==np.uint16
        roi=a[Y0:Y0+N,X0:X0+N].copy();del a
        if roi.shape[2]==4:assert np.all(roi[:,:,3]==65535)
        imgs[key]=roi[:,:,:3].copy()
    print('READ',key,flush=True)
base=imgs['baseline'];expected=np.load(SRC/'C4_expected_moon.npy');err=int(np.max(abs(base.astype(int)-expected.astype(int))));assert err<=3,err
mask=np.load(SRC/'C4_inherited_mask_roi.npy').astype(float)/65535
with np.load(OUT/'A2_occlusion_polygon.npz') as z:P=z['P64']
alpha=mask[...,None];source=np.load(SRC/'C3_candidate_rgb.npy');calc=alpha*source+(1-alpha)*imgs['solar_background'];single=imgs['single_lunar_source'];recomp=int(np.max(abs(single.astype(float)-calc)));assert recomp<=4,recomp
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);marks=np.load(ROOT/'output/v46_detall_diagnostic_20260911/marks_masks.npz')
regions=[(str((lo,hi)),(r>=lo)&(r<hi)) for lo,hi in [(0,350),(350,435),(435,449),(449,454),(454,470)]]
regions += [('green_marks',marks['green'].astype(bool)),('purple_marks',marks['purple'].astype(bool)),('original_lunar_mask_zero',mask==0),('original_lunar_mask_one',mask==1)]
diffs=[]
for before,after in [('baseline','without_all_epochs'),('without_all_epochs','single_lunar_source'),('baseline','single_lunar_source')]:
    d=imgs[after].astype(int)-imgs[before].astype(int);rows=[]
    for label,good in regions:
        vals=d[good];rows.append(dict(region=label,pixels=int(good.sum()),changed_pixels=int(np.any(vals!=0,axis=1).sum()),max_abs_DN16=int(abs(vals).max()),mean_RGB_delta_DN16=np.mean(vals,axis=0).tolist()))
    diffs.append(dict(before=before,after=after,regions=rows))
# Exact source-data provenance of the inherited display mask.
join=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/join_coverage.npy')
join_err=int(np.max(abs(np.rint(join*65535).astype(int)-np.rint(mask*65535).astype(int))))
np.savez_compressed(OUT/'C1_native_composition_roi.npz',**imgs)
vis=OUT/'vistes';vis.mkdir(exist_ok=True)
labels=['baseline','without_all_epochs','single_lunar_source']
row=np.concatenate([imgs[k][200:1200,200:1200]>>8 for k in labels],axis=1).astype(np.uint8);Image.fromarray(row).save(vis/'C1_lunar_sources_comparison.png')
for name,box in [('top',(540,220,860,290)),('right',(1100,530,1180,860)),('bottom',(550,1110,860,1180))]:
    x1,y1,x2,y2=box;parts=[imgs[k][y1:y2,x1:x2]>>8 for k in labels];axis=1 if name=='right' else 0
    row=np.concatenate(parts,axis=axis).astype(np.uint8);im=Image.fromarray(row);im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).save(vis/f'C1_{name}_comparison_x3.png')
save('C1_composition_review.json',dict(method=__doc__,native_baseline_vs_V48_expected_max_DN16=err,single_source_normal_recomposition_max_DN16=recomp,differences=diffs,inherited_mask=dict(matches_stored_V44_display_join_max_DN16=join_err,area_pixels=float(mask.sum()),equivalent_area_radius=float(np.sqrt(mask.sum()/np.pi)),observed_geometric_area_pixels=float(P.sum()),observed_geometric_equivalent_radius=float(np.sqrt(P.sum()/np.pi)),source_code='v44/f5_render.py join_response fits sigma,gamma and angular phase to Pere09 display; v45/f7_fonts.py reuses join for source layers',scope='Stored empirical photographic join plus source validity; NOT solely a physical occultation mask'),status='Visibility-only native diagnostic; no published change or full-limb recovery claim',limits=['Removing the alternative lunar source and LROC changes their contribution where the top source is partly transparent','CameraRaw source RGB and all original layer pixels/masks remain untouched','A clean appearance does not establish additional measured lunar texture']))
print('BASELINE',err,'SINGLE RECOMPOSITION',recomp,'JOIN MATCH',join_err,flush=True)
for a in diffs:print(a['before'],a['after'],[(r['region'],r['changed_pixels'],r['max_abs_DN16']) for r in a['regions']],flush=True)
