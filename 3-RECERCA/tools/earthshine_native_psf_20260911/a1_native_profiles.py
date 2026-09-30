"""Compare unbinned native green samples and two renderers in fixed sectors.
The same observed contour defines distance; no radiance resampling for fitting.
Descriptive widths include optical blur, terrain and calibration uncertainty.
"""
from native_common import *
from scipy.optimize import least_squares
from scipy.special import ndtr
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

edge=np.load(ROOT/'research/tools/v44_earthshine_20260910/cau/vixen_optical_edge.npy')
def coords(x,y):
    dx=x-CX;dy=y-CY;theta=np.arctan2(dy,dx);rad=np.interp(theta%(2*np.pi),np.linspace(0,2*np.pi,len(edge),endpoint=False),edge,period=2*np.pi)
    return theta,np.hypot(dx,dy)-rad

def fit(d,t,g):
    if len(d)<180 or np.sum(d<-10)<20 or np.sum(d>10)<20:return None
    b=np.median(g[d<-10]);amp=np.median(g[d>10])-b
    if amp<=0:return None
    yn=(g-b)/amp
    def model(p):
        bg,mi,A,dm,c,s,ti,td=p;x=d-c;F=ndtr(x/s);phi=np.exp(-.5*(x/s)**2)/np.sqrt(2*np.pi)
        return bg+mi*x+A*F+dm*(x*F+s*phi)+t*(ti+td*F)
    opt=least_squares(lambda p:(model(p)-yn)/.01,[0,0,1,0,0,1.4,0,0],bounds=([-1,-.2,.1,-.3,-8,.35,-.2,-.3],[1,.2,5,.3,8,12,.2,.3]),loss='soft_l1',f_scale=2,max_nfev=150)
    rms=float(np.sqrt(np.mean((model(opt.x)-yn)**2)))
    return dict(sigma=float(opt.x[5]),center=float(opt.x[4]),relative_rms=rms,qualified=bool(opt.success and rms<.03 and .36<opt.x[5]<11.9 and abs(opt.x[4])<7.9),n=len(d),parameters=opt.x.tolist())

yy,xx=np.mgrid[:N,:N];th,dd=coords(xx,yy);rows=[]
for m in json.loads((OUT/'A0_native_and_quincunx.json').read_text())['frames']:
    stem=m['stem'];native=np.load(m['native_samples']);nt,nd=coords(native['x'],native['y']);new=np.load(m['output']);old=np.load(SRC/f'native/vixen_{stem}.npz')
    common=(old['q']>.2)&(new['q']>.2)&np.isfinite(old['g'])&np.isfinite(new['g']);natok=(native['q']>.2)&np.isfinite(native['g'])
    for deg in np.arange(0,360,7.5):
        angle=np.deg2rad(deg);t=((th-angle+np.pi)%(2*np.pi)-np.pi)*453.5;tn=((nt-angle+np.pi)%(2*np.pi)-np.pi)*453.5
        mask=(abs(dd)<18)&(abs(t)<15)&common;nm=(abs(nd)<18)&(abs(tn)<15)&natok
        # Reject sectors without complete radial support in both renderers.
        whole=(abs(dd)<18)&(abs(t)<15)
        if mask.sum()<.99*whole.sum():continue
        ff={key:fit(dd[mask],t[mask],z['g'][mask]) for key,z in [('old',old),('new',new)]}
        ff['native']=fit(nd[nm],tn[nm],native['g'][nm])
        for plane in [1,3]:
            mm=nm&(native['green_plane']==plane);ff[f'G{plane}']=fit(nd[mm],tn[mm],native['g'][mm])
        rows.append(dict(stem=stem,exp=m['exp'],angle=float(deg),fits=ff))
    print(stem,'fit sectors',sum(r['stem']==stem for r in rows),flush=True)

summary=[]
for stem in [m['stem'] for m in json.loads((OUT/'A0_native_and_quincunx.json').read_text())['frames']]:
    good=[r for r in rows if r['stem']==stem and all(r['fits'][k] and r['fits'][k]['qualified'] for k in ['old','new','native'])]
    summary.append(dict(stem=stem,common_qualified=len(good),median_sigma={k:float(np.median([r['fits'][k]['sigma'] for r in good])) if good else None for k in ['old','new','native']},median_width_reduction=float(np.median([1-r['fits']['new']['sigma']/r['fits']['old']['sigma'] for r in good])) if good else None))
save('A1_native_profiles.json',dict(method=__doc__,summary=summary,sectors=rows,limits=['Conditional descriptive fits, not unique PSF or recovered texture','Same grid-pixel support for old/new; irregular native samples have different locations','No formal confidence intervals; conditional noise and terrain nuisance not fully modelled']))
out=OUT/'vistes';out.mkdir(exist_ok=True)
fig,ax=plt.subplots(1,2,figsize=(11,4))
for i,stem in enumerate(['572A2973','572A2976']):
    sel=[r for r in rows if r['stem']==stem and all(r['fits'][k] and r['fits'][k]['qualified'] for k in ['old','new','native'])]
    for k,label in [('old','V48: dos verds interpolats'),('new','Graella verda conjunta'),('native','Mostres natives sense remapat')]:ax[i].plot([r['angle'] for r in sel],[r['fits'][k]['sigma'] for r in sel],'.-',label=label,lw=.8)
    ax[i].set(title=stem,xlabel='Angle del llimb (graus)',ylabel='Amplada descriptiva sigma (px)');ax[i].grid(alpha=.2)
ax[0].legend(fontsize=8);fig.tight_layout();fig.savefig(out/'A1_native_profile_widths.png',dpi=160);plt.close(fig)
print(json.dumps(summary),flush=True)
