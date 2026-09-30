"""Global tone ablation excludes orange+guard and reserves alternating sectors."""
from pathlib import Path
import numpy as np,json
from scipy.ndimage import gaussian_filter
from scipy.optimize import isotonic_regression
R=Path.cwd();O=R/'output/earthshine_broad_lroc_20260914';C=R/'output/earthshine_v49_pere_reveal_20260912'
S={'preCR':np.load(R/'research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy').mean(-1),'previous':np.load(C/'A0_previous_moon_RGB16.npy').mean(-1),'Pere':np.load(C/'A0_Pere_moon_RGB16.npy').mean(-1)}
y,x=np.mgrid[:1400:2,:1400:2];r=np.hypot(x-699.568111973117,y-699.6475341408573);ang=np.arctan2(y-699.6475341408573,x-699.568111973117)%(2*np.pi)
mark=(x>=550)&(x<723)&(y>=902)&(y<1048);guard=(x>=500)&(x<773)&(y>=852)&(y<1098);valid=(r>40)&(r<390)
fit=valid&~guard&((ang/(np.pi/6)).astype(int)%2==0);hold=valid&~guard&~fit;rows=[]
for source,target,sigma in [('previous','Pere',0),('preCR','Pere',16),('preCR','previous',16)]:
 a=S[source] if not sigma else gaussian_filter(S[source],sigma);b=S[target] if not sigma else gaussian_filter(S[target],sigma);a=a[::2,::2];b=b[::2,::2]
 bins=np.unique(np.quantile(a[fit],np.linspace(0,1,257)));ix=np.digitize(a[fit],bins[1:-1]);xf=a[fit];yf=b[fit];xx=[];yy=[];ww=[]
 for i in range(len(bins)-1):
  m=ix==i
  if m.sum():xx.append(np.median(xf[m]));yy.append(np.median(yf[m]));ww.append(m.sum())
 yy=isotonic_regression(np.array(yy),weights=np.array(ww)).x;prediction=np.interp(a,xx,yy);err=b-prediction
 row=dict(source=source,target=target,sigma=sigma,holdout_RMS=float(np.sqrt(np.mean(err[hold]**2))),mark_residual_median=float(np.median(err[mark])),mark_RMS=float(np.sqrt(np.mean(err[mark]**2))),mark_correlation=float(np.corrcoef(prediction[mark],b[mark])[0,1]),mark_outside_fit_range=int(np.sum((a[mark]<xx[0])|(a[mark]>xx[-1]))),knots_input=list(map(float,xx)),knots_output=list(map(float,yy)))
 rows.append(row);print({k:v for k,v in row.items() if not k.startswith('knots')},flush=True)
(O/'A5_global_tone.json').write_text(json.dumps(rows,indent=2)+'\n')
