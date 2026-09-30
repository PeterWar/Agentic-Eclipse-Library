from pathlib import Path
import json,numpy as np
from scipy.ndimage import gaussian_filter
O=Path('/private/tmp/v105_base_sources_20260926');A={s:np.load(O/f'detail_audit_hp_sigma{s}.npz') for s in [1,2,4,8]};Q=np.load(O/'572A2975.npz');dr=Q['dreal'];by,ey,bx,ex=Q['box'];rows=[]
def corr(a,b):return float(np.corrcoef(a,b)[0,1]) if len(a)>30 else None
def phase_metric(a,b,s):
 # Windowed cross-spectrum phase agreement at declared wavelengths.
 n,m=a.shape;win=np.outer(np.hanning(n),np.hanning(m));fa=np.fft.fft2((a-a.mean())*win);fb=np.fft.fft2((b-b.mean())*win);freq=np.hypot(np.fft.fftfreq(n)[:,None],np.fft.fftfreq(m)[None,:]);z=(freq>=1/(12*s))&(freq<=1/(3*s));c=fa*np.conj(fb);amp=np.abs(c);return {'frequency_bins':int(z.sum()),'amplitude_weighted_phase_cosine':float(np.real(c[z]).sum()/max(amp[z].sum(),1e-30)),'unweighted_phase_cosine':float(np.mean(np.real(c[z])/np.maximum(amp[z],1e-30))),'wavelength_px':[3*s,12*s]}
for theta in [45,105,165,225,285,345]:
 for dist,size in [(25,16),(40,24),(70,48),(120,64)]:
  cx=5375.7868+(452.9785+dist)*np.cos(np.deg2rad(theta));cy=3775.9775-(452.9785+dist)*np.sin(np.deg2rad(theta));x=int(round(cx-bx));y=int(round(cy-by));sl=(slice(y-size//2,y+size//2),slice(x-size//2,x+size//2));r={'center_canvas_xy':[x+int(bx),y+int(by)],'theta_deg':theta,'nominal_distance':dist,'size':size,'metrics':{}}
  for s in [1,2,4,8]:
   safe=A[s]['safe_09'][sl]&A[s]['safe_2969'][sl]&A[s]['safe_2975'][sl]&A[s]['safe_2993'][sl];rec={'safe_fraction':float(safe.mean()),'safe_n':int(safe.sum()),'rho_G':{}}
   for a,b in [('09','2969'),('2975','2969'),('09','2975'),('09','2993')]:rec['rho_G'][a+'_'+b]=corr(A[s][a][sl][safe],A[s][b][sl][safe])
   if safe.all():rec['phase_09_2969']=phase_metric(A[s]['09'][sl],A[s]['2969'][sl],s)
   r['metrics'][str(s)]=rec
  rows.append(r)
# Examples selected from predeclared held-out grid, using independent exposure2969, not presented as global rates.
good=[r for r in rows if r['metrics']['2']['safe_n']>100 and r['metrics']['2']['rho_G']['09_2969'] is not None]
best=max(good,key=lambda r:r['metrics']['2']['rho_G']['09_2969']);weak=min(good,key=lambda r:abs(r['metrics']['1']['rho_G']['09_2969']))
out={'selection':'descriptive examples from fixed held-out angular grid; best sigma2 independent correlation and near-zero sigma1 pair; not unbiased population estimates','candidate_grid':rows,'corroborated_example':best,'uncorroborated_microtexture_example':weak}
(O/'DETAIL_EXAMPLES_PHASE.json').write_text(json.dumps(out,indent=2));print('BEST',json.dumps(best),flush=True);print('WEAK',json.dumps(weak),flush=True)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axs=plt.subplots(4,4,figsize=(12,11));images=['09','2975','2969','2993'];labels=['09 original · Adobe RGB','RAW2975 · original member','RAW2969 · independent','RAW2993 · original member']
for j,(example,s,title) in enumerate([(best,1,'Best corroborated patch: fine band sigma1'),(best,2,'Same patch: sigma2'),(weak,1,'Weak microtexture corroboration: sigma1'),(weak,4,'Same patch: sigma4')]):
 x,y=np.array(example['center_canvas_xy'])-[bx,by];size=example['size'];sl=(slice(y-size//2,y+size//2),slice(x-size//2,x+size//2));limits=np.percentile(np.abs(np.concatenate([A[s][k][sl].ravel() for k in images])),97)
 for i,k in enumerate(images):
  v=A[s][k][sl];safe=A[s][f'safe_{k}'][sl];z=(v-np.median(v))/max(v.std(),1e-12);axs[j,i].imshow(np.ma.array(z,mask=~safe),cmap='gray',vmin=-2.5,vmax=2.5,interpolation='nearest');axs[j,i].set_xticks([]);axs[j,i].set_yticks([])
  if j==0:axs[j,i].set_title(labels[i],fontsize=10)
  if i==0:axs[j,i].set_ylabel(title+'\n'+str(example['center_canvas_xy']),fontsize=9)
fig.suptitle('Observed log-green spatial bands; each tile standardized for visibility\nMasked gray = filter support touches lunar or missing data; no output-image correction',fontsize=12);fig.tight_layout(rect=[0,0,1,.94]);fig.savefig(O/'DETAIL_EXAMPLES_PHASE.png',dpi=150);plt.close(fig)
