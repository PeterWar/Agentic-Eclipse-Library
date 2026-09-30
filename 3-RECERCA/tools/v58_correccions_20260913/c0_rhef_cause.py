from common58 import *
import ast,time
from scipy.ndimage import map_coordinates
from PIL import Image
claim();src=V42/'b4f_rhef_variants_v42.py';tree=ast.parse(src.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='rhef_local');env={'np':np,'time':time,'log':lambda t:None,'DR':8.};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(src),'exec'),env)
y,x=np.mgrid[:1200,:1200];r=np.hypot(x-600,y-600);t=np.arctan2(y-600,x-600);m=(r>220)&(r<540);a=(np.exp(-(r-300)/44)*np.exp(.2*np.sin(3*t)+.07*np.cos(7*t)+.015*np.cos(17*t))).astype('float32')
rr=np.arange(260,501,.25);tt=np.linspace(0,2*np.pi,1440,endpoint=False);sy=600+rr[:,None]*np.sin(tt);sx=600+rr[:,None]*np.cos(tt)
rep={'source_code_sha256':sha(src),'source':'analytic separable exp(-r/44) x angular structure; contains no concentric rings','variants':{}}
for dr in [8.,1.]:
 env['DR']=dr
 for deg in [60.,30.]:
  q=env['rhef_local'](a,m,r,t,deg,deg/4);p=map_coordinates(np.nan_to_num(q),[sy,sx],order=1,prefilter=False);res=p-p.mean(axis=0,keepdims=True);v=res.mean(axis=1);fr=np.fft.rfftfreq(len(rr),.25);ps=np.abs(np.fft.rfft(v-v.mean()))**2;sel=np.abs(fr-1/8)<.01
  z=dict(radial_leak_rms=float(np.sqrt(np.mean(res**2))),period8_power=float(ps[sel].sum()),phase_profile=[float(np.mean(res[(np.mod(rr,8)>=i)&(np.mod(rr,8)<i+1)])) for i in range(8)])
  rep['variants'][f'DR{dr:g}_S{deg:g}']=z;np.save(O/'arrays'/f'C0_DR{dr:g}_S{deg:g}.npy',q)
  Image.fromarray(np.uint8(np.clip(np.nan_to_num(q),0,1)*255)).save(O/'vistes'/f'C0_DR{dr:g}_S{deg:g}_full.png');print(dr,deg,z,flush=True)
save('C0_rhef_cause.json',rep)
