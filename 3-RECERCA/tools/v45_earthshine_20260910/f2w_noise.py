"""Fixed empirical8–64px scalar weights; not a physical variance estimate."""
from comu45 import *
from scipy.ndimage import gaussian_filter as gf

def main():
    claim45();manifest=REB45/'B1_inputs.json';frames=json.loads(manifest.read_text())['frames']
    from f2_temporal import GAIN,ALPHA,component
    names=list(ALPHA);sl=np.s_[300:1100,300:1100];y,x=np.mgrid[300:1100,300:1100]
    xx,yy=x-CXT,y-CYT;r=np.hypot(xx,yy);ghost=np.hypot(x+X0-5367,y+Y0-3545)
    acc={k:[np.zeros((800,800)) for _ in range(3)] for k in names}
    for m in frames:
        k=component(m);d=np.load(m['native']['file']);a=GAIN[m['grup']]
        g=d['g'][sl].astype(float)*a;q=d['q'][sl];v=d['variance'][sl].astype(float)*a*a
        ok=np.isfinite(g)&np.isfinite(v)&(v>0)&(q>0);support=gf(ok.astype(float),4)
        vs=gf(np.nan_to_num(v)*ok,4)/np.maximum(support,1e-30);w=np.where(ok,q/np.maximum(vs,1e-12),0)
        if k=='sony_B':t=np.clip((ghost-140)/40,0,1);w*=t*t*(3-2*t)
        acc[k][0]+=np.nan_to_num(g)*w;acc[k][1]+=w;acc[k][2]+=np.nan_to_num(v)*w*w
    def smooth(t):
        t=np.clip(t,0,1);return t**3*(10+t*(-15+6*t))
    win=smooth((.7*455.50181897230107-r)/64)*smooth((ghost-180)/48);w2=win**2;mask=win>0
    basis=np.array([np.ones_like(xx),xx/320,yy/320,(xx/320)**2,xx*yy/320**2,(yy/320)**2]);A=basis[:,mask].T*win[mask,None]
    fts=[];variances=[];precisions=[]
    for k in names:
        num,den,vn=acc[k];g=num/np.maximum(den,1e-30);v=vn/np.maximum(den**2,1e-30)
        co=np.linalg.lstsq(A,g[mask]*win[mask],rcond=None)[0]
        residual=(g-np.einsum('i,iyx->yx',co,basis))*win;fts.append(np.fft.fft2(residual));variances.append(v);precisions.append(float((den*w2).sum()))
    f=np.fft.fftfreq(800);rho=np.hypot(f[:,None],f[None,:]);H=(rho>=1/64)&(rho<1/8);band=np.fft.ifft2(np.array(fts)*H).real
    quarters=[('all',np.ones_like(mask)),('exclude_Q1',~((xx>=0)&(yy>=0))),('exclude_Q2',~((xx<0)&(yy>=0))),('exclude_Q3',~((xx<0)&(yy<0))),('exclude_Q4',~((xx>=0)&(yy<0)))]
    rows=[]
    for label,region in quarters:
        norm=w2[region].sum();b=band[:,region];cov=b@b.T/norm;signal=np.median(cov[:2,3:]);noise=np.diag(cov)-signal
        pred=np.array([(v*w2*region).sum()/norm*H.mean() for v in variances]);alpha=noise/pred
        row=dict(region=label,covariance_DN2=cov.tolist(),common_signal_DN2=float(signal),conditional_power_DN2=pred.tolist(),effective_alpha=alpha.tolist())
        if label=='all':
            before=np.array(precisions)/sum(precisions);after=before/alpha;after/=after.sum()
            row.update(weight_fraction_before=before.tolist(),weight_fraction_after=after.tolist())
            assert np.allclose(alpha,list(ALPHA.values()),rtol=1e-4),(alpha,ALPHA)
        rows.append(row)
    savejson(REB45/'F2w_empirical_weights.json',dict(B1_sha256=sha(manifest),components=names,rows=rows,scope='fixed inner aperture, FFT8–64, leave-one-quadrant sensitivity not confidence interval; effective weights include MTF ambiguity and incoherentFPN; covariance not eliminated; noLROC',applied_alpha=ALPHA,variance_output='conditional variance unchanged; alpha affects weights only'))
    print('REPRODUCED',rows[0],flush=True)
if __name__=='__main__':main()
