"""Apply the paired moving-limb operator delta, preserving frozen stellar subtraction.
The source candidate is provisional until independent/held-out and filter QA.
"""
from a15_lunar_domain import *
from scipy.ndimage import binary_dilation,distance_transform_edt,gaussian_filter

def main():
 z=np.load(O/'limb_confidence_q16/STACKS.npz');out=O/'domain_q16';out.mkdir();(out/'sources').mkdir();base=O/'d4_baseline/products/sources';y0,y1,x0,x1=z['box'];sl=(slice(y0,y1),slice(x0,x1));oldb2=np.array(np.load(O/'b2_vixen/cau/vixen_total_v38.npy',mmap_mode='r')[sl]);oldphoto=oldb2.copy();s4=np.load(O/'s4_baseline/cau/s4_recomposicio_box.npz');sy0,sy1,sx0,sx1=s4['box'];ss=(slice(sy0-y0,sy1-y0),slice(sx0-x0,sx1-x0));oldm=np.load(O/'b3_baseline/cau/support_v42.npy',mmap_mode='r')[sy0:sy1,sx0:sx1];s4m=np.load(O/'s4_baseline/cau/s4_support_new_box.npy');use=s4m&((~oldm)|(s4['Dmin']<6));oldphoto[ss][use]=s4['totN'][use]
 q=z['q16'];oldcalc=z['old'];validold=np.all(np.isfinite(oldb2)&(oldb2>0)&np.isfinite(oldcalc)&(oldcalc>0),-1);newphoto=oldb2.copy();newphoto[validold]=oldb2[validold]+(q[validold]-oldcalc[validold]);newonly=~validold&np.all(np.isfinite(q)&(q>0),-1);newphoto[newonly]=q[newonly];affected=z['affected'];newphoto[~affected]=oldphoto[~affected];physical=np.load(base/'support.npy')[sl];moon=np.load(O/'current_lunar_support.npz')['support'];visible=physical&~moon
 delta=np.where((physical&affected)[...,None],newphoto-oldphoto,0).astype(np.float32);assert np.isfinite(delta[physical]).all();wv=np.array(np.load(O/'b3_baseline/cau/weight_vixen_v42.npy',mmap_mode='r')[sl]);wv[ss][use]=1.;assert np.all(wv[physical&affected]==1),'Correction intersects a live Sony blend after accounting for historical S4 replacement';assert np.all(np.isfinite(newphoto[visible])&(newphoto[visible]>0)),'nonpositive visible source'
 rows={};changed=np.any(delta!=0,-1);report={'source_delta_rule':'new_photo = exactB2 + (new_q16_same_coordinates - old_B2_same_coordinates), new-only directly from measured q16; delta = new_photo - exactoldD4_photo; add delta to starless arrays without scaling stellar subtraction','box':[int(x0),int(y0),int(x1),int(y1)],'visible_changed':int((changed&visible).sum()),'all_changed':int(changed.sum()),'min_blend_weight_vixen':float(wv[physical&affected].min()),'physical_support_unchanged':True,'beta':0,'scope':'provisional source-confidence candidate'}
 for name in ['fusion_starless.npy','vixen_starless.npy','sony_starless.npy','base_G.npy']:
  clone(base/name,out/'sources'/name)
  if name in ['fusion_starless.npy','vixen_starless.npy']:
   a=np.load(out/'sources'/name,mmap_mode='r+');roi=np.array(a[sl]);roi[physical&affected]+=delta[physical&affected];a[sl]=roi;a.flush();assert np.all(np.isfinite(roi[visible])&(roi[visible]>0))
  elif name=='base_G.npy':
   a=np.load(out/'sources'/name,mmap_mode='r+');f=np.load(out/'sources/fusion_starless.npy',mmap_mode='r');a[sl]=np.where(physical,f[sl][...,1],0);a.flush()
  rows[name]={'sha256':sha(out/'sources'/name),'source_photometry_changed':name!='sony_starless.npy'}
 # Copy the separately declared computational masks, not reinterpret physical support.
 clone(O/'domain_v1/sources/support.npy',out/'sources/support.npy');(out/'train_supports').mkdir();(out/'s4').mkdir()
 for name in ['vixen_support.npy','sony_support.npy']:clone(O/'domain_v1/train_supports'/name,out/'train_supports'/name)
 for name in ['s4_recomposicio_box.npz','s4_support_new_box.npy']:clone(O/'domain_v1/s4'/name,out/'s4'/name)
 dom=json.loads((O/'domain_v1/MANIFEST.json').read_text());dom.update(physical_radiance_arrays_unchanged=False,physical_support_unchanged=True,source_correction=report,status='q16 confidence candidate; not promoted');dom['sources'].update(rows);save(out/'MANIFEST.json',dom)
 L0=oldphoto[...,1];L1=newphoto[...,1];eps=1e-30;lr=np.log(np.maximum(L1,eps)/np.maximum(L0,eps));good=visible&affected;report['visible_log_ratio_quantiles']=np.percentile(lr[good],[0,1,25,50,75,99,100]).tolist();report['weight_neff_ratio_quantiles']=np.percentile(z['neff_q16'][...,1][good]/np.maximum(z['neff_full'][...,1][good],1e-30),[0,1,50,99,100]).tolist();report['positive_support_diff_vs_full']=int(np.count_nonzero(np.all(z['q16']>0,-1)^np.all(z['full']>0,-1)));report['den_support_diff_vs_full']=int(np.count_nonzero(np.all(z['den_q16']>0,-1)^np.all(z['den_full']>0,-1)))
 np.savez(out/'SOURCE_DELTA.npz',delta=delta,oldphoto=oldphoto,newphoto=newphoto,visible=visible,affected=affected,box=z['box']);save(out/'SOURCE_QA.json',report);save(out/'COMPLETE.json',{'PASS':True,'meaning':'source construction integrity only; scientific QA pending','report':report});print(json.dumps(report),flush=True)

if __name__=='__main__':guard();main()
