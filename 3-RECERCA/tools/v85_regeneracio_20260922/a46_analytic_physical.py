"""Same analytical truth/injections, retaining accepted physical-domain samples.
Existing oracle and 0.9..1.1 gate retained; no new scientific PASS implied.
"""
from a20_analytic_boundary import namespace
from a13_filters import *
from a43_physical_boundary import install_physical

def scene(ns):
 # Execute literal scene/injection AST from the frozen original control.
 tree=ast.parse((R/'3-RECERCA/tools/v85_regeneracio_20260922/a20_analytic_boundary.py').read_text());body=next(n.body for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main');start=next(i for i,n in enumerate(body) if isinstance(n,ast.Assign) and ast.unparse(n.targets[0])=='angular_envelope');end=next(i for i,n in enumerate(body[start:],start) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='save');nodes=copy.deepcopy(body[start:end]);exec(compile(ast.Module(body=nodes,type_ignores=[]),'literal a20 scene/injection AST','exec'),ns);return ns['truth'],ns['injection'],hashlib.sha256(ast.dump(ast.Module(body=nodes,type_ignores=[]),include_attributes=False).encode()).hexdigest()

def main():
 out=O/'analytic_physical_R02';out.mkdir();ns=namespace(out);r,t=ns['coords']();physical=np.load(O/'d4_baseline/products/sources/support.npy');z=np.load(O/'current_lunar_support.npz');x0,y0,x1,y1=map(int,z['box']);sl=(slice(y0,y1),slice(x0,x1));roi=(slice(y0-700,y1+700),slice(x0-700,x1+700));truth,injection,astsha=scene(dict(np=np,r=r,t=t));baseprofile=json.loads((H/'v29_profiles_round1/cau/refined_detail_receipt.json').read_text())['profiles'];layer_sigmas={'01':(2,4,8,16,32),'04':(1,2,4,8,16),'05':(2,4,8,16,32,48),'06':(4,8,16,32,64)};sigmas=sorted({s for ss in layer_sigmas.values() for s in ss});rr=r[roi];ww=np.ones(rr.shape,np.float32);color_env=(1-np.exp(-(r/180.)**2))**6*np.exp(-((r-500)/130)**2);rows=[]
 save(out/'FROZEN_TEST.json',{'truth_and_injection_AST_sha256':astsha,'literal_from':'a20_analytic_boundary.py','E3_color':'same as a30 .04 smooth chromatic angular variation','change':'same D/T equations on complement of physical support; observed samples under final lunar photo retained','oracle':'existing analytic_boundary/analytic_biharmonic and analytic_local outputs; same full known truth inside finalMoon','no_change_to_old_thresholds':True,'E3_scope':'same pre-display d as prior local QA','products':'base/injected E3x4 and MGN ROI2800; WOW standard/bilateral fullcanvas','science_PASS':None})
 for injected in [False,True]:
  label='injected' if injected else 'base';folder=out/label;folder.mkdir();ens=namespace(folder);edir=folder/'E3boundary';edir.mkdir();install_physical(ens,edir,screened=True,validity=physical[sl]);channel_maps={k:[] for k in layer_sigmas}
  for ch in range(3):
   a=(np.log(truth)+.04*color_env*np.cos(3*t+ch*2*np.pi/3)+(injection if injected else 0)).astype(np.float32);ent,_=ens['farcit_perfil_ln_A'](a,physical,r);np.testing.assert_array_equal(ent[physical],a[physical]);xroi=np.array(ent[roi]);p=baseprofile[str(ch)];scale=np.interp(np.log(np.maximum(rr/440.60304883027544,1e-5)),p['lnr_centres'],p['robust_contrast']).astype(np.float32);acc={k:np.zeros(rr.shape,np.float32) for k in layer_sigmas}
   for sigma0 in sigmas:
    band=xroi-ens['normgauss'](xroi,ww,sigma0)
    for k,ss in layer_sigmas.items():
     if sigma0 in ss:acc[k]+=band/len(ss)
   for k in layer_sigmas:channel_maps[k].append(acc[k]/scale)
   del a,ent,acc,xroi,scale,band;gc.collect()
  for k in layer_sigmas:
   q=np.median(np.stack(channel_maps[k]),axis=0).astype(np.float32);np.save(folder/(k+'.npy'),q);rows.append({'case':label,'tag':k,'sha256':sha(folder/(k+'.npy'))})
  del ens,channel_maps;gc.collect();print('PHYSICAL_ANALYTIC_E3_DONE',label,flush=True)
  ens=namespace(folder);edir=folder/'E2boundary';edir.mkdir();install_physical(ens,edir,validity=physical[sl]);a=truth*np.exp(injection,dtype=np.float32) if injected else truth;ent,_=ens['farcit_perfil'](a,physical,r);np.testing.assert_array_equal(ent[physical],a[physical]);limits=[float(a[physical].min()),float(a[physical].max())]
  # Prior local oracle defines limits on domain, not physical. These numerical
  # extrema are checked equal before reusing that oracle; otherwise stop.
  domain=np.load(O/'domain_v1/sources/support.npy',mmap_mode='r');priorlimits=[float(a[domain].min()),float(a[domain].max())];assert limits==priorlimits,(limits,priorlimits)
  q=ens['mgn'](np.asarray(ent[roi]),ww.astype(bool),limits=limits);np.save(folder/'MGN.npy',q);rows.append({'case':label,'tag':'MGN','sha256':sha(folder/'MGN.npy')});del q,ent,domain;gc.collect();print('PHYSICAL_ANALYTIC_MGN_DONE',label,flush=True)
  ent,_=ens['farcit_perfil_A'](a,physical,r);np.testing.assert_array_equal(ent[physical],a[physical]);full=np.ones_like(physical)
  for bilateral,tag in [(False,'WOW'),(True,'WOW_bilateral')]:
   q=ens['wow'](ent,full,11,bilateral);np.save(folder/(tag+'.npy'),q);rows.append({'case':label,'tag':tag,'sha256':sha(folder/(tag+'.npy'))});del q;gc.collect();print('PHYSICAL_ANALYTIC_WOW_DONE',label,tag,flush=True)
  save(out/'PROGRESS.json',rows);del ent,ens,a;gc.collect()
 save(out/'COMPLETE.json',{'PASS':True,'products':rows,'meaning':'calculation integrity only; unchanged scientific gate evaluated separately'});print('ANALYTIC_PHYSICAL_COMPLETE',flush=True)
if __name__=='__main__':guard();main()
