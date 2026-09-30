"""Causal source ablation: restore literal pre-S4 photometry for corona filters.

No new frame weighting or B(D) curve. Original star subtraction is retained;
the original S4 footprint must not overlap any subtracted star footprint.
"""
from a15_lunar_domain import *

def main():
 out=O/'domain_pres4_R02';out.mkdir();(out/'sources').mkdir();(out/'s4').mkdir();(out/'train_supports').mkdir()
 base=O/'d4_baseline/products/sources';z=np.load(O/'s4_baseline/cau/s4_recomposicio_box.npz');y0,y1,x0,x1=map(int,z['box']);sl=(slice(y0,y1),slice(x0,x1))
 b3=O/'b3_baseline/cau';oldmask=np.load(b3/'support_v42.npy');sup=np.load(O/'s4_baseline/cau/s4_support_new_box.npy');use=sup&((~oldmask[sl])|(z['Dmin']<6));stars=np.load(base/'star_footprints.npy',mmap_mode='r');assert not np.any(stars[sl]&use),'Need literal stellar reconstruction if any overlap'
 lunar=np.load(O/'current_lunar_support.npz');mx0,my0,mx1,my1=map(int,lunar['box']);msl=(slice(my0,my1),slice(mx0,mx1));moon=lunar['support'];newmask=oldmask.copy();newmask[msl]&=~moon
 current=np.load(O/'domain_v1/sources/support.npy');lost=current&~newmask;gained=newmask&~current;assert not gained.any()
 save(out/'FROZEN_ABLATION.json',{'status':'DECLARED_BEFORE_FILTER_EVALUATION','question':'Does S4 source substitution propagate moving-limb response into corona detail filters?',
  'change':'Restore B3 fusion and B2 Vixen pixels at exact historical S4 replacement footprint, retain original stellar subtraction elsewhere, disable S4 auxiliary support',
  'source_support':'Original support_v42; same final photographic Moon exclusion; no new distance threshold or radius',
  'base_photographic_PSB':'unchanged','frames_BD_weights':'historical B2/B3 unchanged; no fit',
  'lost_visible_support':int(lost.sum()),'gained_support':int(gained.sum()),'star_overlap':0,
  'filter_padding':'Same R01 residual biharmonic equation for scalar E2 with enlarged unknown mask determined solely by source validity',
  'acceptance':'Report lost observations separately. Disappearance due to missing support is not recovery; inspect common-domain marks and fixed Brno. No hidden-corona truth claim.',
  'reserved_radiance':'not read or used for tuning'})
 rows={}
 for tag,path in [('fusion',b3/'fusion_total_v42.npy'),('vixen',O/'b2_vixen/cau/vixen_total_v38.npy'),('sony',b3/'sony_corrected_total_v42.npy')]:
  name=tag+'_starless.npy';clone(base/name,out/'sources'/name)
  if tag!='sony':
   a=np.load(out/'sources'/name,mmap_mode='r+');q=np.array(a[sl]);original=np.load(path,mmap_mode='r')[sl];q[use]=original[use];a[sl]=q;a.flush();assert np.array_equal(q[use],original[use],equal_nan=True)
  rows[name]={'sha256':sha(out/'sources'/name),'restored_pre_S4':tag!='sony','source':str(path.relative_to(R))}
 fusion=np.load(out/'sources/fusion_starless.npy',mmap_mode='r');G=np.where(oldmask,fusion[...,1],0).astype(np.float32);np.save(out/'sources/base_G.npy',G);np.save(out/'sources/support.npy',newmask)
 valid=newmask&np.isfinite(G)&(G>0);invalid=newmask&~valid
 for name in ['vixen_support.npy','sony_support.npy']:clone(O/'domain_v1/train_supports'/name,out/'train_supports'/name)
 clone(O/'s4_baseline/cau/s4_recomposicio_box.npz',out/'s4/s4_recomposicio_box.npz');np.save(out/'s4/s4_support_new_box.npy',np.zeros_like(sup))
 np.save(out/'lost_output_support.npy',lost)
 save(out/'MANIFEST.json',{'purpose':'Pre-S4 filter-source ablation, unpromoted','sources':rows,'support_sha256':sha(out/'sources/support.npy'),'G_sha256':sha(out/'sources/base_G.npy'),'lost_visible_source_support':int(lost.sum()),'supported_nonpositive_or_invalid_G':int(invalid.sum()),'S4_disabled_in_auxiliary_support':True,'source_mask_is_not_claim_of_coronal_validity':True,'PSB_unchanged':True})
 save(out/'COMPLETE.json',{'PASS':True,'meaning':'construction integrity only','restored_S4_pixels':int(use.sum()),'lost_visible_support':int(lost.sum()),'invalid_G':int(invalid.sum())});print('PRES4_DOMAIN_COMPLETE',int(lost.sum()),int(invalid.sum()),flush=True)

if __name__=='__main__':guard();main()
