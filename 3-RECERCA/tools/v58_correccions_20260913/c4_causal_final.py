from filters58 import *
from rhef_native58 import rhef_native_cdf
claim();y,x=np.mgrid[:1200,:1200];r=np.hypot(x-600,y-600);t=np.arctan2(y-600,x-600);m=(r>220)&(r<540);a=(np.exp(-(r-300)/44)*np.exp(.2*np.sin(3*t)+.07*np.cos(7*t)+.015*np.cos(17*t))).astype('float32');rr=np.arange(260,501,.25);tt=np.linspace(0,2*np.pi,1440,endpoint=False);sy=600+rr[:,None]*np.sin(tt);sx=600+rr[:,None]*np.cos(tt);rep={}
for deg in [60.,30.]:
 q=rhef_native_cdf(a,m,r,t,deg,deg/4,nt=8192,cx=600,cy=600,quiet=True);p=map_coordinates(q,[sy,sx],order=1);res=p-p.mean(axis=0,keepdims=True);v=res.mean(axis=1);fr=np.fft.rfftfreq(len(rr),.25);ps=np.abs(np.fft.rfft(v-v.mean()))**2;sel=np.abs(fr-1/8)<.01;old=json.loads((O/'C0_rhef_cause.json').read_text())['variants'][f'DR8_S{deg:g}'];rep[str(deg)]=dict(radial_leak_rms=float(np.sqrt(np.mean(res**2))),period8_power=float(ps[sel].sum()),old=old,period8_reduction_fraction=1-float(ps[sel].sum())/old['period8_power']);print(deg,rep[str(deg)],flush=True)
 from PIL import Image
 Image.fromarray(np.uint8(np.clip(np.nan_to_num(q),0,1)*255)).save(O/'vistes'/f'C4_analytic_{deg:g}.png')
save('C4_final_causal_rings.json',rep)
