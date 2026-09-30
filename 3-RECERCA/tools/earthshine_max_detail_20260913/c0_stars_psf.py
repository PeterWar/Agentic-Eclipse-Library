"""Secondary route: actual RAW stars constrain only their own field PSF.
No kernel inferred at lunar position from remote stars without a spatial model.
"""
from common import *
import sys,math
import rawpy,cv2
from scipy.optimize import least_squares
sys.path.insert(0,str(ROOT/'research/tools/eclipse_determinista'))
import comu,f2
claim()
class ReadOnlyRun(comu.Run):
    def fase(self,n,*parts):
        p=Path(self.dir)/comu.FASES[n]
        for x in parts:p=p/x
        assert p.exists();return str(p)
    def desa_rebut(self,*args):raise RuntimeError('read only')
ctx=f2.Ctx(ReadOnlyRun.obre(str(RUNS['vixen'])));pos=json.loads((RUNS['vixen']/'4-rebuts/F1.3_registre.json').read_text())['fotogrames']
cat=json.loads((ROOT/'research/tools/v42_20260910/cau/estrelles_v42.json').read_text())['estrelles'];stars=sorted([s for s in cat if s['r_R']<9.1],key=lambda s:-s['snr'])[:6]
M=np.array(json.loads((ROOT/'research/tools/v25_lineal/cau_v25/geometria_v27.json').read_text())['M_llenc_a_v23']);inv=cv2.invertAffineTransform(M)
save('C0_stars_design.json',dict(method=__doc__,stars=stars,frames=['572A2982.CR3','572A2983.CR3','572A2984.CR3'],fitting='Elliptic Gaussian plus plane, joint native G1/G2 samples in 64px patch, measured conditional photon/read weights; no resampling',gate='Positive amplitude SNR>10, centroid not on bound, axes1-15nativepx, residual assessment and field/epoch stability. Passing is local to star position; no lunar extrapolation claim.'))
rows=[]
for nom in ['572A2982.CR3','572A2983.CR3','572A2984.CR3']:
    v=pos[nom]
    with rawpy.imread(ctx.ruta[nom]) as raw:rr=raw.raw_image.astype(np.float32)
    dark=ctx.dark(v['exp'])
    for st in stars:
        q=inv@np.array([st['x'],st['y'],1]);dx=(q[0]-ctx.CX)*ctx.k;dy=(q[1]-ctx.CY)*ctx.k
        px=ctx.ca*dx+ctx.sa*dy+v['sol_x'];py=-ctx.sa*dx+ctx.ca*dy+v['sol_y'];ix=int(round(px));iy=int(round(py));h,w=rr.shape
        if ix<35 or iy<35 or ix>w-36 or iy>h-36:rows.append(dict(frame=nom,star=st,status='OUTSIDE_VIXEN'));continue
        xx=[];yy=[];data=[];var=[]
        for i in [1,3]:
            oy,ox=ctx.orig[i];xa=(ix-32-ox)//2;ya=(iy-32-oy)//2;sl=np.s_[ya:ya+33,xa:xa+33]
            r=rr[oy::2,ox::2][sl];d=dark[oy::2,ox::2][sl];flat=ctx.flat[oy::2,ox::2][sl];Y,X=np.mgrid[:33,:33]
            good=((r-ctx.cfg['pedestal_dn'])/(ctx.cfg['saturacio_dn']-ctx.cfg['pedestal_dn'])<.85)&(ctx.valid[oy::2,ox::2][sl]>0)
            xx.extend((2*(xa+X)+ox-px)[good]);yy.extend((2*(ya+Y)+oy-py)[good]);data.extend(((r-d)/flat/v['exp'])[good]);var.extend(((np.maximum(r-512,0)/5.08+2*1.05**2)/(flat*v['exp'])**2)[good])
        x=np.array(xx);y=np.array(yy);z=np.array(data);sd=np.sqrt(np.array(var));bg=np.median(z);amp=max(np.max(z)-bg,1e-6)
        def model(p):
            a,cx,cy,sx,sy,ang,b,bx,by=p;dx=x-cx;dy=y-cy;u=np.cos(ang)*dx+np.sin(ang)*dy;vv=-np.sin(ang)*dx+np.cos(ang)*dy
            return a*np.exp(-.5*((u/sx)**2+(vv/sy)**2))+b+bx*x+by*y
        p0=[amp,0,0,3,3,0,bg,0,0];lo=[0,-12,-12,1,1,-np.pi,-np.inf,-np.inf,-np.inf];hi=[np.inf,12,12,15,15,np.pi,np.inf,np.inf,np.inf]
        fit=least_squares(lambda p:(model(p)-z)/sd,p0,bounds=(lo,hi),max_nfev=200);a,cx,cy,sx,sy,ang,b,bx,by=fit.x;chi=np.mean(((model(fit.x)-z)/sd)**2);sig=np.sqrt(np.diag(np.linalg.pinv(fit.jac.T@fit.jac))*chi);snr=a/max(sig[0],1e-30)
        ok=fit.success and snr>10 and max(abs(cx),abs(cy))<11 and 1.01<min(sx,sy) and max(sx,sy)<14.9
        row=dict(frame=nom,star=st,pred_native=[px,py],fit_parameters=fit.x,amplitude_snr=snr,chi2_reduced=chi,fwhm_native_px=sorted([2.35482*sx,2.35482*sy],reverse=True),status='LOCAL_STAR_FIT' if ok else 'NOT_QUALIFIED');rows.append(row);print(nom,st['r_R'],row['status'],row['fwhm_native_px'],'snr',round(snr,2),'chi',round(chi,2),flush=True)
good=[q for q in rows if q['status']=='LOCAL_STAR_FIT'];save('C0_stars_psf.json',dict(rows=rows,qualified_local=len(good),nearest_catalog_radius_R=min(s['r_R'] for s in cat),decision='No lunar PSF promoted: identified stars are at least6.16solar radii away; no simultaneous near-Moon star measurement or validated spatial PSF model. Keep as measured bounds for later study.',method=__doc__))
