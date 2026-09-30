"""Known-truth MGN and RGB ACHF pre-display checks on full-scene padding.
Local convolution ROI has >400 px halo beyond the last judged distance512;
maximum E3 kernel radius256 and nested MGN radius240 cannot reach its edge.
"""
from a20_analytic_boundary import namespace
from a13_filters import *
from a18_boundary_extension import install as harmonic_install
from a24_biharmonic_boundary import install as biharmonic_install
from a29_screened_boundary import install as screened_install

def main():
 out=O/'analytic_local';out.mkdir();ns=namespace(out);r,t=ns['coords']();physical=np.load(O/'d4_baseline/products/sources/support.npy');domain=np.load(O/'domain_v1/sources/support.npy');lunar=np.load(O/'current_lunar_support.npz');moon=lunar['support'];x0,y0,x1,y1=lunar['box'];sl=(slice(y0,y1),slice(x0,x1));full=np.ones_like(domain)
 # Positive, smooth, non-harmonic known corona. The field remains finite at centre.
 angular_envelope=(1-np.exp(-(r/180.)**2))**6
 logtruth=(16.-5*np.log1p((r/140.)**2)+angular_envelope*(.18*np.cos(5*t)*np.exp(-((r-540)/500)**2)*(1+.35*np.sin((r-456)/27))+.035*np.cos(11*t+.04*r)*np.exp(-((r-500)/120)**2))).astype(np.float32);del angular_envelope
 truth=np.exp(logtruth,dtype=np.float32);del logtruth
 y,x=np.ogrid[:7506,:10551];injection=np.zeros(r.shape,np.float32);bands=[[2,8],[8,32],[32,128]];wavelengths=[5.,18.,70.];signal_rows=[]
 for i,lam in enumerate(wavelengths):
  for j,orient in enumerate(['radial','tangential','oblique']):
   angle=-np.pi+(i*3+j+.5)*2*np.pi/9;da=np.arctan2(np.sin(t-angle),np.cos(t-angle));window=np.exp(-(da/.13)**8)*np.exp(-((r-490)/90)**8);phase=r if j==0 else (440.60304883027544*t if j==1 else (.7*(x-5361.768111973117)+.714*(y-3775.747534140857)));injection+=.003*window*np.sin(2*np.pi*phase/lam);signal_rows.append({'band':bands[i],'orientation':orient,'angular_center':float(angle),'wavelength':lam})
 save(out/'FROZEN_TEST.json',{'scene':'smooth radial profile plus angular streamers with radial-varying amplitude and oblique phase; nonharmonic','shape':[7506,10551],'WOW_scales':11,'source_sha256':sha(O/'current_lunar_support.npz'),'injection_stage':'analytical radiance BEFORE re-estimating profile and boundary','injection_log_amplitude':.003,'components':signal_rows,'cases':['base_A','base_B','base_C','base_oracle','injected_C','injected_oracle'],'status':'outputs for separate QA; no automatic scientific pass'})
 rows=[];roi=(slice(y0-700,y1+700),slice(x0-700,x1+700));rr=r[roi];ww=np.ones(rr.shape,np.float32);baseprofile=json.loads((H/'v29_profiles_round1/cau/refined_detail_receipt.json').read_text())['profiles'];layer_sigmas={'01':(2,4,8,16,32),'04':(1,2,4,8,16),'05':(2,4,8,16,32,48),'06':(4,8,16,32,64)};sigmas=sorted({s for ss in layer_sigmas.values() for s in ss});color_env=(1-np.exp(-(r/180.)**2))**6*np.exp(-((r-500)/130)**2)
 save(out/'SCOPE.json',{'ROI_y0y1x0x1':[y0-700,y1+700,x0-700,x1+700],'E3':'same full-scene logarithmic boundary and fixed original RGB contrast profiles; compare pre-display median normalized detail d before tanh/SN/H1','MGN':'exact operator on padded ROI, fixed domain min/max limits, interior metric protected by >400px halo','scene':'same common truth/injections as WOW plus small smooth chromatic angular variation for E3','variants_E3':['A','C','T','oracle'],'variants_MGN':['A','D','oracle'],'T':'unit grid-scale tension; not fitted','holdouts_used_for_tuning':False})
 for injected,case in [(False,c) for c in ['A','C','T','oracle']]+[(True,c) for c in ['C','T','oracle']]:
  label=('injected_' if injected else 'base_')+case;folder=out/label;folder.mkdir();ns=namespace(folder)
  if case=='C':harmonic_install(ns,folder)
  if case=='T':screened_install(ns,folder)
  channel_maps={k:[] for k in layer_sigmas}
  for ch in range(3):
   a=(np.log(truth)+.04*color_env*np.cos(3*t+ch*2*np.pi/3)+(injection if injected else 0)).astype(np.float32);mask=physical if case in ['A','oracle'] else domain;ent,_=ns['farcit_perfil_ln_A'](a,mask,r)
   if case=='oracle':ent[sl][moon]=a[sl][moon]
   np.testing.assert_array_equal(ent[domain],a[domain]);xroi=np.array(ent[roi]);p=baseprofile[str(ch)];scale=np.interp(np.log(np.maximum(rr/440.60304883027544,1e-5)),p['lnr_centres'],p['robust_contrast']).astype(np.float32);acc={k:np.zeros(rr.shape,np.float32) for k in layer_sigmas}
   for sigma in sigmas:
    band=xroi-ns['normgauss'](xroi,ww,sigma)
    for k,ss in layer_sigmas.items():
     if sigma in ss:acc[k]+=band/len(ss)
   for k in layer_sigmas:channel_maps[k].append(acc[k]/scale)
   del a,ent,acc,xroi,scale,band;gc.collect()
  for k in layer_sigmas:
   q=np.median(np.stack(channel_maps[k]),axis=0).astype(np.float32);np.save(folder/(k+'.npy'),q);rows.append({'case':label,'tag':k,'sha256':sha(folder/(k+'.npy'))})
  del channel_maps,ns;gc.collect();print('LOCAL_E3_DONE',label,flush=True);save(out/'PROGRESS.json',rows)
 for injected,case in [(False,'A'),(False,'D'),(False,'oracle'),(True,'D'),(True,'oracle')]:
  label=('injected_' if injected else 'base_')+case;folder=out/label;folder.mkdir(exist_ok=True);ns=namespace(folder)
  if case=='D':biharmonic_install(ns,folder)
  a=truth*np.exp(injection,dtype=np.float32) if injected else truth;mask=physical if case in ['A','oracle'] else domain;ent,_=ns['farcit_perfil'](a,mask,r)
  if case=='oracle':ent[sl][moon]=a[sl][moon]
  np.testing.assert_array_equal(ent[domain],a[domain]);limits=[float(a[domain].min()),float(a[domain].max())];q=ns['mgn'](np.asarray(ent[roi]),ww.astype(bool),limits=limits);np.save(folder/'MGN.npy',q);rows.append({'case':label,'tag':'MGN','sha256':sha(folder/'MGN.npy')});save(out/'PROGRESS.json',rows);print('LOCAL_MGN_DONE',label,flush=True);del q,ent,ns
  if injected:del a
  gc.collect()
 save(out/'COMPLETE.json',{'PASS':True,'products':rows,'shape':[2800,2800],'meaning':'calculation integrity only; scientific QA separate'})

if __name__=='__main__':guard();main()
