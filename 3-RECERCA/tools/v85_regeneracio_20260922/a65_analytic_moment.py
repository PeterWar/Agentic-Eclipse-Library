"""E3 quadratic-moment boundary against unchanged known-truth benchmark."""
from a62_moment_operator import *
from a46_analytic_physical import namespace,scene

def main():
 out=O/'analytic_moment_R02';out.mkdir();assert json.loads((O/'moment_E3_R02/NULL_QA.json').read_text())['PASS'];engine=MomentGaussian();roi=engine.roi;ns=namespace(out);r,t=ns['coords']();truth,injection,astsha=scene(dict(np=np,r=r,t=t));rr=r[roi];pold=json.loads((H/'v29_profiles_round1/cau/refined_detail_receipt.json').read_text())['profiles'];layers={'01':[2,4,8,16,32],'04':[1,2,4,8,16],'05':[2,4,8,16,32,48],'06':[4,8,16,32,64]};color_env=(1-np.exp(-(r/180.)**2))**6*np.exp(-((r-500)/130)**2);rows=[]
 save(out/'FROZEN_TEST.json',{'scene_AST_sha256':astsha,'scene':'same a20/a30 known-truth field, color term and injections','operator':'quadratic moment Gaussian mean on exactly domain_v1 observed exterior; same 4scale recipes and fixed RGB contrast profiles','oracle':'existing analytic_local base_oracle/injected_oracle; no altered gates','invalid_output':'zero only at nonobserved pixels, excluded from all QA','full_ordinary_stencil':'original OpenCV Gaussian is unchanged','scope':'pre-display d only, no PSB promotion or sciencePASS'})
 for injected in [False,True]:
  label='injected' if injected else 'base';folder=out/label;folder.mkdir();channels={k:[] for k in layers}
  for ch in range(3):
   a=(np.log(truth)+.04*color_env*np.cos(3*t+ch*2*np.pi/3)+(injection if injected else 0)).astype(np.float32)[roi];p=pold[str(ch)];scale=np.interp(np.log(np.maximum(rr/440.60304883027544,1e-5)),p['lnr_centres'],p['robust_contrast']).astype(np.float32);acc={k:np.zeros(rr.shape,np.float32) for k in layers}
   for s in SIGMAS:
    smooth=engine.smooth_roi(a,s).astype(np.float32);band=a-smooth
    for k,ss in layers.items():
     if s in ss:acc[k]+=band/len(ss)
   for k in layers:channels[k].append(acc[k]/scale)
   del a,acc,smooth,band,scale;gc.collect();print('MOMENT_ANALYTIC_CHANNEL',label,ch,flush=True)
  for k in layers:
   q=np.median(np.stack(channels[k]),axis=0).astype(np.float32);q[~engine.m]=0;np.save(folder/(k+'.npy'),q);rows.append({'case':label,'tag':k,'sha256':sha(folder/(k+'.npy'))})
  save(out/'PROGRESS.json',rows);del channels;gc.collect()
 save(out/'COMPLETE.json',{'PASS':True,'products':rows,'meaning':'calculation integrity only; scientific gate separate'});print('ANALYTIC_MOMENT_COMPLETE',flush=True)
if __name__=='__main__':guard();main()
