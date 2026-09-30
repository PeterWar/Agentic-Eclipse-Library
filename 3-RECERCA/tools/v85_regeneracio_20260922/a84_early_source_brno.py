"""Fixed inner-reference comparison of early/matching/mixed source logG."""
from a16_build_psb import *
from scipy.ndimage import map_coordinates,gaussian_filter,binary_erosion

def main():
 src=O/'early_epoch_R03';assert json.loads((src/'COMPLETE.json').read_text())['PASS'];out=src/'brno';out.mkdir();meta=json.loads((R/'4-RESULTATS/v82_capes_brno_20260918/registre_v82.json').read_text());caps=json.loads((R/'4-RESULTATS/v82_capes_brno_20260918/capes_v82.json').read_text());geo=json.loads((R/'3-RECERCA/tools/estudi_druckmuller/geometria.json').read_text());name='TSE2026_Trigaza_800mm.png';m=meta['imatges'][name];reg=m[caps[name]['tria']];sigma=.45*reg['escala'];assert int(3*sigma+.5)==4
 geom=np.load(O/'marks246_R02/GEOMETRY.npz');pts=geom['points'];norm=geom['normals'];comp=geom['component'];aw=geom['weights'];points=np.stack([pts,pts+4*norm,pts-4*norm]);safe=np.nan_to_num(points,nan=-1000);y0,y1,x0,x1=json.loads((O/'limb_frames/METADATA.json').read_text())['box_y0y1x0x1'];coords=np.stack([safe[...,1]-y0,safe[...,0]-x0]);A=np.vstack([reg['A_png_a_v'],[0,0,1]]);uv=np.linalg.inv(A)@np.stack([safe[...,0].ravel(),safe[...,1].ravel(),np.ones(safe.shape[0]*safe.shape[1])]);u,v=uv[:2].reshape(2,*safe.shape[:2]);g=geo[name];f0,f1,c0,c1=g['marc'];refvalid=(u>c0+1)&(u<c1-1)&(v>f0+1)&(v<f1-m['peu_files']-1)&(np.hypot(u-(g['cx']+c0),v-(g['cy']+f0))>g['R_lluna_px']+4)
 names=['early6','same19','mixed61'];valid={k:np.load(src/(k+'_valid.npy')) for k in names};common=np.logical_and.reduce(list(valid.values()));eroded=binary_erosion(common,structure=np.ones((9,9),bool));ok=geom['usable']&refvalid.all(axis=0)
 for c in coords.transpose(1,0,2):ok&=map_coordinates(eroded.astype(float),c,order=1,mode='constant',cval=0)>=1-1e-12
 save(out/'METHOD.json',{'fixed_reference':233,'same_h4_original_normals':True,'components':[2,3],'sigma':sigma,'kernel_radius':4,'support':'common valid positiveG; full smoothing and bilinear footprints','minimum_samples':10,'controls':'same selected points without smoothing','metrics':'weighted Pearson normal C of source logG vs published encodedG, descriptive only','scope':'source diagnostic, not full-canvas filter validation; reference rendering is not photometric truth','primary':'early6 vs same19','secondary':'mixed61'})
 def contrast(a):
  z=map_coordinates(a,coords,order=1,mode='constant',cval=np.nan);return z[0]-.5*(z[1]+z[2])
 ref=PSB(str(O/'V84_Pere_input.psb')).channel_box(233,1,(x0,y0,x1,y1)).astype(float)/65535;rc=contrast(ref);values={k:np.log(np.where(valid[k],np.load(src/(k+'_G.npy')),1)).astype(float) for k in names};rows=[]
 for smooth in ['nominal','none_control']:
  cs={k:contrast(gaussian_filter(a,sigma,truncate=3,mode='constant',cval=0) if smooth=='nominal' else a) for k,a in values.items()}
  for component in [2,3]:
   sel=ok&(comp==component)&np.isfinite(rc)
   for a in cs.values():sel&=np.isfinite(a)
   row={'component':component,'smoothing':smooth,'n':int(sel.sum()),'groups':{}}
   if sel.sum()>=10:
    w=aw[sel];r=rc[sel]-np.average(rc[sel],weights=w)
    for k,a in cs.items():
     z=a[sel];zc=z-np.average(z,weights=w);den=np.sqrt(np.sum(w*r*r)*np.sum(w*zc*zc));row['groups'][k]={'Pearson':float(np.sum(w*zc*r)/den) if den>0 else None,'mean_C':float(np.average(z,weights=w)),'rms_C':float(np.sqrt(np.average(z*z,weights=w)))}
   rows.append(row)
 save(out/'QA.json',{'rows':rows,'scientific_PASS':None,'no_reference_fit':True});print('EARLY_BRNO_SOURCE',rows,flush=True)

if __name__=='__main__':guard();main()
