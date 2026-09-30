"""Physical-domain E2/E3 unit-tension control, paired normalization and old gates."""
from a46_analytic_physical import *

def main():
 out=O/'analytic_physical_T_R02';out.mkdir();ns=namespace(out);r,t=ns['coords']();physical=np.load(O/'d4_baseline/products/sources/support.npy');domain=np.load(O/'domain_v1/sources/support.npy');z=np.load(O/'current_lunar_support.npz');x0,y0,x1,y1=map(int,z['box']);sl=(slice(y0,y1),slice(x0,x1));roi=(slice(y0-700,y1+700),slice(x0-700,x1+700));truth,injection,astsha=scene(dict(np=np,r=r,t=t));baseprofile=json.loads((H/'v29_profiles_round1/cau/refined_detail_receipt.json').read_text())['profiles'];layer_sigmas={'01':(2,4,8,16,32),'04':(1,2,4,8,16),'05':(2,4,8,16,32,48),'06':(4,8,16,32,64)};sigmas=sorted({s for ss in layer_sigmas.values() for s in ss});rr=r[roi];ww=np.ones(rr.shape,np.float32);color_env=(1-np.exp(-(r/180.)**2))**6*np.exp(-((r-500)/130)**2);rows=[];limits_rows=[]
 save(out/'FROZEN_TEST.json',{'truth_and_injection_AST_sha256':astsha,'literal_scene_from':'a20_analytic_boundary.py','E3':'physical support; exact same screened unit-tension as a46; base arrays reused by hash','E2':'physical support; fixed unit-tension same as E3, no parameter fitting','MGN_normalization':'actual physical min/max separately for base/injected; fresh oracle with identical physical limits','old_MGN_compare':'QA may add .7 times gamma physical-minus-domain at judged observed pixels only, per exact operator decomposition; old tests retained','WOW_oracle':'existing a20 profileA full known truth','thresholds':'same prior0.9..1.1; new test does not invalidate prior failures','claims':'calculation integrity only; scientific assessment separate'})
 for injected in [False,True]:
  label='injected' if injected else 'base';folder=out/label;folder.mkdir()
  if not injected:
   for k in layer_sigmas:
    src=O/'analytic_physical_R02/base'/(k+'.npy');dst=folder/(k+'.npy');assert src.is_file();os.link(src,dst);rows.append({'case':label,'tag':k,'sha256':sha(dst),'reused_exact_from':str(src.relative_to(R))})
  else:
   ens=namespace(folder);edir=folder/'E3boundary';edir.mkdir();install_physical(ens,edir,screened=True,validity=physical[sl]);channel_maps={k:[] for k in layer_sigmas}
   for ch in range(3):
    a=(np.log(truth)+.04*color_env*np.cos(3*t+ch*2*np.pi/3)+injection).astype(np.float32);ent,_=ens['farcit_perfil_ln_A'](a,physical,r);np.testing.assert_array_equal(ent[physical],a[physical]);xroi=np.array(ent[roi]);p=baseprofile[str(ch)];scale=np.interp(np.log(np.maximum(rr/440.60304883027544,1e-5)),p['lnr_centres'],p['robust_contrast']).astype(np.float32);acc={k:np.zeros(rr.shape,np.float32) for k in layer_sigmas}
    for sigma0 in sigmas:
     band=xroi-ens['normgauss'](xroi,ww,sigma0)
     for k,ss in layer_sigmas.items():
      if sigma0 in ss:acc[k]+=band/len(ss)
    for k in layer_sigmas:channel_maps[k].append(acc[k]/scale)
    del a,ent,acc,xroi,scale,band;gc.collect()
   for k in layer_sigmas:
    q=np.median(np.stack(channel_maps[k]),axis=0).astype(np.float32);np.save(folder/(k+'.npy'),q);rows.append({'case':label,'tag':k,'sha256':sha(folder/(k+'.npy'))})
   del ens,channel_maps;gc.collect()
  print('PHYSICAL_T_ANALYTIC_E3_DONE',label,flush=True)
  a=truth*np.exp(injection,dtype=np.float32) if injected else truth;limits=[float(a[physical].min()),float(a[physical].max())];oldlimits=[float(a[domain].min()),float(a[domain].max())];limits_rows.append({'case':label,'physical':limits,'old_domain':oldlimits});save(out/'LIMITS.json',limits_rows)
  # Fresh paired oracle: literal historical padding outside the lunar box,
  # true analytical radiance throughout the lunar support, same current limits.
  ons=namespace(folder);oracle_ent,_=ons['farcit_perfil'](a,physical,r);oracle_ent[sl][z['support']]=a[sl][z['support']];np.testing.assert_array_equal(oracle_ent[physical],a[physical]);q=ons['mgn'](np.asarray(oracle_ent[roi]),ww.astype(bool),limits=limits);np.save(folder/'MGN_oracle.npy',q);rows.append({'case':label,'tag':'MGN_oracle','sha256':sha(folder/'MGN_oracle.npy')});del q,oracle_ent,ons;gc.collect()
  ens=namespace(folder);edir=folder/'E2boundary';edir.mkdir();install_physical(ens,edir,screened=True,validity=physical[sl]);ent,_=ens['farcit_perfil'](a,physical,r);np.testing.assert_array_equal(ent[physical],a[physical]);q=ens['mgn'](np.asarray(ent[roi]),ww.astype(bool),limits=limits);np.save(folder/'MGN.npy',q);rows.append({'case':label,'tag':'MGN','sha256':sha(folder/'MGN.npy')});del q,ent;gc.collect();print('PHYSICAL_T_ANALYTIC_MGN_DONE',label,flush=True)
  ent,_=ens['farcit_perfil_A'](a,physical,r);np.testing.assert_array_equal(ent[physical],a[physical]);full=np.ones_like(physical)
  for bilateral,tag in [(False,'WOW'),(True,'WOW_bilateral')]:
   q=ens['wow'](ent,full,11,bilateral);np.save(folder/(tag+'.npy'),q);rows.append({'case':label,'tag':tag,'sha256':sha(folder/(tag+'.npy'))});del q;gc.collect();print('PHYSICAL_T_ANALYTIC_WOW_DONE',label,tag,flush=True)
  save(out/'PROGRESS.json',rows);del ent,ens,a;gc.collect()
 save(out/'COMPLETE.json',{'PASS':True,'products':rows,'meaning':'calculation integrity only; unchanged scientific gate evaluated separately'});print('ANALYTIC_PHYSICAL_T_COMPLETE',flush=True)
if __name__=='__main__':guard();main()
