"""Independent inner-mark morphology at frozen registration and resolution.

Specified before viewing pre-S4 mark/Brno results. No fitting or PASS threshold.
"""
from a16_build_psb import *
from scipy.ndimage import map_coordinates,gaussian_filter,binary_erosion

def main():
 assert json.loads((O/'filters_pres4_WOW_R02/COMPLETE.json').read_text())['PASS']
 out=O/'inner_brno_pres4_R02';out.mkdir();meta=json.loads((R/'4-RESULTATS/v82_capes_brno_20260918/registre_v82.json').read_text());caps=json.loads((R/'4-RESULTATS/v82_capes_brno_20260918/capes_v82.json').read_text());geo=json.loads((R/'3-RECERCA/tools/estudi_druckmuller/geometria.json').read_text());geom=np.load(O/'marks246_R02/GEOMETRY.npz');pts=geom['points'];normals=geom['normals'];usable=geom['usable'];comp=geom['component'];weights=geom['weights'];points=np.stack([pts,pts+4*normals,pts-4*normals]);safe=np.nan_to_num(points,nan=-1000);box=(4600,3000,6150,4550);x0,y0,x1,y1=box;sl=(slice(y0,y1),slice(x0,x1));coords=np.stack([safe[...,1]-y0,safe[...,0]-x0]);support=np.load(O/'domain_v1/sources/support.npy',mmap_mode='r')[sl];base_valid=map_coordinates(support,coords,order=1,output=np.float32,mode='constant',cval=0)>.999;source_triplet=usable&base_valid.all(axis=0);coverage=[];ref_masks={}
 for lid,name in [(230,'TSE_2026_200mm_DHS.png'),(231,'TSE_2026_400mm_DHS.png'),(232,'TSE_2026_530mm_DHS.png'),(233,'TSE2026_Trigaza_800mm.png')]:
  m=meta['imatges'][name];reg=m[caps[name]['tria']];A=np.vstack([reg['A_png_a_v'],[0,0,1]]);uv=np.linalg.inv(A)@np.stack([safe[...,0].ravel(),safe[...,1].ravel(),np.ones(safe.shape[0]*safe.shape[1])]);u,v=uv[:2].reshape(2,*safe.shape[:2]);g=geo[name];f0,f1,c0,c1=g['marc'];frame=(u>c0+1)&(u<c1-1)&(v>f0+1)&(v<f1-m['peu_files']-1);d=np.hypot(u-(g['cx']+c0),v-(g['cy']+f0));refvalid=frame&(d>g['R_lluna_px']+4);ref_masks[lid]=refvalid;rows=[]
  for k in [0,*map(int,np.unique(comp))]:
   q=np.ones(len(comp),bool) if k==0 else comp==k;rows.append({'component':k,'both_center_valid':int((q&base_valid[0]&refvalid[0]).sum()),'both_triplet_valid':int((q&source_triplet&refvalid.all(axis=0)).sum())})
  coverage.append({'reference':lid,'name':name,'scale':reg['escala'],'rows':rows})
 assert [r['rows'][0]['both_triplet_valid'] for r in coverage]==[0,44,0,428];save(out/'GEOMETRIC_COVERAGE.json',{'source_triplets':int(source_triplet.sum()),'references':coverage,'scope':'geometry only; no intensity judgement'})
 oldG=np.load(O/'d4_baseline/products/sources/base_G.npy',mmap_mode='r')[sl];newG=np.load(O/'domain_pres4_R02/sources/base_G.npy',mmap_mode='r')[sl];newS=np.load(O/'domain_pres4_R02/sources/support.npy',mmap_mode='r')[sl];v0=support&np.isfinite(oldG)&(oldG>0);v1=newS&np.isfinite(newG)&(newG>0);common=v0&v1;eroded=binary_erosion(common,structure=np.ones((9,9),bool));strict=usable&ref_masks[233].all(axis=0)
 for c in coords.transpose(1,0,2):
  # Weight1 exactly means every positive bilinear corner belongs to erosion.
  strict&=map_coordinates(eroded.astype(float),c,order=1,mode='constant',cval=0)>=1-1e-12
 sigma=.45*next(r['scale'] for r in coverage if r['reference']==233);assert int(3*sigma+.5)==4
 save(out/'METHOD.json',{'fixed_before_results':True,'ref':233,'components':[2,3],'h':4,'sigma_canvas_px':sigma,'truncate':3,'radius':4,'support':'full9x9 Gaussian footprint and positive-weight bilinear corners within common finite positive source support','minimum_samples':10,'same_sample_unblurred_control':True,'metrics':['weighted Pearson of normal C vsBrno','mean signedC','RMS and new/old ratio'],'limitations':['nominal sampling equalization, not measured PSF','fixed published composite is not physical radiance truth','component1 has no usable external reference','no automatic scientific PASS']})
 p=PSB(str(O/'V84_Pere_input.psb'));ref=np.asarray(p.channel_box(233,1,box),float)/65535
 def C(a):
  v=map_coordinates(a,coords,order=1,mode='constant',cval=np.nan);return v[0]-.5*(v[1]+v[2])
 rc=C(ref);result=[]
 for op in ['P04_WOW','P05_WOW_bilateral']:
  values={k:np.asarray(np.load(folder/(op+'_u16.npy'),mmap_mode='r')[sl],float)/65535 for k,folder in [('R01',O/'filters_selected'),('preS4',O/'filters_pres4_WOW_R02/products/filters')]}
  for smoothing in ['nominal','none_control']:
   contrasts={k:C(gaussian_filter(a,sigma,truncate=3,mode='constant',cval=0) if smoothing=='nominal' else a) for k,a in values.items()}
   for k in [2,3]:
    ok=strict&(comp==k)&np.isfinite(rc)
    for q in contrasts.values():ok&=np.isfinite(q)
    row={'operator':op,'smoothing':smoothing,'component':k,'samples':int(ok.sum()),'candidates':{}}
    if ok.sum()>=10:
     w=weights[ok];r=rc[ok];rz=r-np.average(r,weights=w)
     for variant,c in contrasts.items():
      q=c[ok];qz=q-np.average(q,weights=w);den=np.sqrt(np.sum(w*qz*qz)*np.sum(w*rz*rz));row['candidates'][variant]={'weighted_Pearson':float(np.sum(w*qz*rz)/den) if den>0 else None,'mean_C':float(np.average(q,weights=w)),'rms_C':float(np.sqrt(np.average(q*q,weights=w)))}
     r0=row['candidates']['R01'];r1=row['candidates']['preS4'];row['delta_Pearson']=r1['weighted_Pearson']-r0['weighted_Pearson'] if r0['weighted_Pearson'] is not None and r1['weighted_Pearson'] is not None else None;row['rms_ratio_new_old']=r1['rms_C']/r0['rms_C'] if r0['rms_C']>0 else None
    result.append(row)
 save(out/'QA.json',{'rows':result,'scope':'fixed partial inner-mark morphology only; no PSB promotion','scientific_PASS':None});print('INNER_BRNO_DONE',[(r['operator'],r['component'],r['smoothing'],r['samples'],r.get('delta_Pearson')) for r in result],flush=True)

if __name__=='__main__':guard();main()
