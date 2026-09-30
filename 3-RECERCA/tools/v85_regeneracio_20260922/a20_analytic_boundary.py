"""Full-canvas analytical oracle and paired pre-boundary injection for WOW.
No parameters are selected from user marks. All branches share exterior padding.
"""
from a13_filters import *
from a18_boundary_extension import install

def namespace(out):
 fr,deps,h,codes,ev=setup_programs();ns=dict(__name__='v85_analytic_control',np=np,cv2=cv2,ne=ne,Path=Path,json=json,hashlib=hashlib,ast=ast,time=time,gc=gc,ctypes=ctypes,sys=sys,gaussian_filter=gaussian_filter,map_coordinates=map_coordinates,gaussian_filter1d=gaussian_filter1d,R=R,O=out,T=deps,DEPS=deps,V42=out,CAU=O/'fixed_inputs',DISPLAY_DIR=deps/'display',VARIANTS_INPUT=deps/'fine_variants_receipt.json',DYLIB_INPUT=deps/'sparse_conv.dylib');exec(codes['common'],ns);exec(codes['filters'],ns);return ns

def main():
 out=O/'analytic_boundary';out.mkdir();ns=namespace(out);r,t=ns['coords']();physical=np.load(O/'d4_baseline/products/sources/support.npy');domain=np.load(O/'domain_v1/sources/support.npy');lunar=np.load(O/'current_lunar_support.npz');moon=lunar['support'];x0,y0,x1,y1=lunar['box'];sl=(slice(y0,y1),slice(x0,x1));full=np.ones_like(domain)
 # Positive, smooth, non-harmonic known corona. The field remains finite at centre.
 angular_envelope=(1-np.exp(-(r/180.)**2))**6
 logtruth=(16.-5*np.log1p((r/140.)**2)+angular_envelope*(.18*np.cos(5*t)*np.exp(-((r-540)/500)**2)*(1+.35*np.sin((r-456)/27))+.035*np.cos(11*t+.04*r)*np.exp(-((r-500)/120)**2))).astype(np.float32);del angular_envelope
 truth=np.exp(logtruth,dtype=np.float32);del logtruth
 y,x=np.ogrid[:7506,:10551];injection=np.zeros(r.shape,np.float32);bands=[[2,8],[8,32],[32,128]];wavelengths=[5.,18.,70.];signal_rows=[]
 for i,lam in enumerate(wavelengths):
  for j,orient in enumerate(['radial','tangential','oblique']):
   angle=-np.pi+(i*3+j+.5)*2*np.pi/9;da=np.arctan2(np.sin(t-angle),np.cos(t-angle));window=np.exp(-(da/.13)**8)*np.exp(-((r-490)/90)**8);phase=r if j==0 else (440.60304883027544*t if j==1 else (.7*(x-5361.768111973117)+.714*(y-3775.747534140857)));injection+=.003*window*np.sin(2*np.pi*phase/lam);signal_rows.append({'band':bands[i],'orientation':orient,'angular_center':float(angle),'wavelength':lam})
 save(out/'FROZEN_TEST.json',{'scene':'smooth radial profile plus angular streamers with radial-varying amplitude and oblique phase; nonharmonic','shape':[7506,10551],'WOW_scales':11,'source_sha256':sha(O/'current_lunar_support.npz'),'injection_stage':'analytical radiance BEFORE re-estimating profile and boundary','injection_log_amplitude':.003,'components':signal_rows,'cases':['base_A','base_B','base_C','base_oracle','injected_C','injected_oracle'],'status':'outputs for separate QA; no automatic scientific pass'})
 rows=[]
 for injected,case in [(False,'A'),(False,'B'),(False,'C'),(False,'oracle'),(True,'C'),(True,'oracle')]:
  label=('injected_' if injected else 'base_')+case;folder=out/label;folder.mkdir();a=truth*np.exp(injection,dtype=np.float32) if injected else truth;ns=namespace(folder);common,_=ns['farcit_perfil_A'](a,physical,r)
  if case=='A':ent=common
  elif case=='oracle':ent=common;block=ent[sl];block[moon]=a[sl][moon]
  else:
   if case=='C':extension=install(ns,folder)
   ent,_=ns['farcit_perfil_A'](a,domain,r)
   # Freeze all padding exterior to the lunar diagnostic box across cases.
   ent[:y0]=common[:y0];ent[y1:]=common[y1:];ent[y0:y1,:x0]=common[y0:y1,:x0];ent[y0:y1,x1:]=common[y0:y1,x1:];del common
  for bilateral,tag in [(False,'WOW'),(True,'WOW_bilateral')]:
   start=time.monotonic();print('ANALYTIC_START',label,tag,flush=True);q=ns['wow'](ent,full,11,bilateral);np.save(folder/(tag+'.npy'),q);rows.append({'case':label,'filter':tag,'seconds':time.monotonic()-start,'sha256':sha(folder/(tag+'.npy'))});save(out/'PROGRESS.json',rows);print('ANALYTIC_DONE',label,tag,flush=True);del q;gc.collect()
  del ent,ns
  if injected:del a
  gc.collect()
 save(out/'COMPLETE.json',{'PASS':True,'products':rows,'meaning':'numerical runs complete; quality acceptance is separate'})

if __name__=='__main__':guard();main()
