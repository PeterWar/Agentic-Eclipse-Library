"""Single frozen positive per-frame lunar-distance confidence ablation.
Heuristic confidence, not a calibrated noise variance or a recovered PSF.
"""
from a14_limb_recompose import *

def main():
 src=O/'limb_frames';out=O/'limb_confidence_q16';out.mkdir();meta=json.loads((src/'METADATA.json').read_text());N=np.load(src/'numerator.npy',mmap_mode='r');Wg=np.load(src/'weight.npy',mmap_mode='r');Ds=np.load(src/'distance_model.npy',mmap_mode='r');tables=old_tables();b2=json.loads((H/'v38_limb_round1/cau/correccio_vora_lunar.json').read_text())['taula'];shape=N.shape[1:]
 save(out/'FROZEN_CANDIDATE.json',{'q':'0.05 + 0.95*smoothstep(D;4,16)','q_applied_to':'each existing B2 and auxiliary S4 numerator and denominator contribution','tier_taper':'smooth1atD2 to0atD8, as separate continuous S4 ablation','parameter_selection':'one physically motivated predeclared candidate;4 is original full lunar gate and16 approximates historical clean-reference distance15','B0':'unchanged; beta0','support':'all weights remain positive where formerly eligible','holdouts':json.loads((O/'QA_FROZEN.json').read_text())['development_validation']['new_holdout'],'limits':'Heuristic confidence, can increase noise gradients; no claim of complete deconvolution or correction where no cleaner observation exists'})
 sums={k:[np.zeros(shape,np.float32) for _ in range(3)] for k in ['old','full','q16','train_old','train_full','train_q16']};affected=np.zeros(shape[:2],bool);all_low=np.ones(shape[:2],bool)
 for j,f in enumerate(meta['frames']):
  d=Ds[j];c=classe(f['exposure']);tb=b2[c];bo=np.interp(d,np.asarray(tb['d_px'],np.float32),np.asarray(tb['B_ln'],np.float32),left=tb['B_ln'][0],right=0).astype(np.float32);co=np.exp(-bo,dtype=np.float32);dd,bb=tables[c];cn=np.exp(-np.interp(d,dd,bb,right=0).astype(np.float32),dtype=np.float32);fl=np.clip((d-2)/2,0,1).astype(np.float32);wextra=np.zeros_like(d)
  for tier,g in zip(TIERS,GT):
   d0=tier[c]
   if d0 is not None:wextra+=g*np.clip(d-d0,0,1)/np.maximum(cn,1e-6)**2
  u=np.clip((d-2)/6,0,1);tap=1-u*u*(3-2*u);u=np.clip((d-4)/12,0,1);q=.05+.95*u*u*(3-2*u)
  coeff={'old':(fl*co,fl),'full':(fl*co+wextra*cn,fl+wextra),'q16':((fl*co+wextra*tap*cn)*q,(fl+wextra*tap)*q)}
  contributes=np.any(Wg[j]>0,-1)&((fl+wextra)>0);affected|=contributes&(d<16);all_low&=~contributes|(d<=4)
  for k,(ncoef,wcoef) in coeff.items():
   nn=N[j]*ncoef[...,None];ww=Wg[j]*wcoef[...,None]
   for key in [k]+([] if f['holdout'] else ['train_'+k]):sums[key][0]+=nn;sums[key][1]+=ww;sums[key][2]+=ww**2
  if j%10==0:print('CONFIDENCE',j+1,len(meta['frames']),flush=True)
 arrays={'affected':affected,'all_low':all_low,'box':np.array(meta['box_y0y1x0x1'])}
 for k,(num,den,w2) in sums.items():
  cam=np.where(den>0,num/np.maximum(den,1e-20),np.nan);_,v=comu.lluminancia(cam,np.asarray(meta['matrix'],np.float32),meta['gain']);arrays[k]=v.astype(np.float32);arrays['den_'+k]=den;arrays['neff_'+k]=den**2/np.maximum(w2,1e-30)
 np.savez(out/'STACKS.npz',**arrays);save(out/'COMPLETE.json',{'PASS':True,'sha256':sha(out/'STACKS.npz'),'stage':'candidate only, not scientific acceptance'});print('CONFIDENCE_COMPLETE',flush=True)

if __name__=='__main__':guard();main()
