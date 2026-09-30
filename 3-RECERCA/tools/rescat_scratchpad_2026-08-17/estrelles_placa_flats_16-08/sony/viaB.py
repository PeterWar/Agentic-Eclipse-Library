import numpy as np, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
from common import planes, SCALE
from esf import limb_circle
from skimage.registration import phase_cross_correlation
from scipy.ndimage import fourier_shift
SAT=(16383.0-512.0)*0.97

def auto_c0(P):
    g=P['G1']; h,w=g.shape
    d=g[:h//8*8,:w//8*8].reshape(h//8,8,w//8,8).mean(axis=(1,3))
    thr=np.percentile(d,99.9)*0.05
    ys,xs=np.nonzero(d>thr); return (np.average(xs,weights=d[ys,xs])*8,np.average(ys,weights=d[ys,xs])*8)

def crop(img,cx,cy,n):
    x0=int(round(cx))-n//2; y0=int(round(cy))-n//2
    return img[y0:y0+n, x0:x0+n].copy(), x0, y0

def fshift(a,s):
    return np.real(np.fft.ifft2(fourier_shift(np.fft.fft2(a),s)))

def radial_power(img):
    n=img.shape[0]
    w=np.hanning(n); W=np.outer(w,w)
    F=np.fft.fftshift(np.fft.fft2((img-img.mean())*W))
    P=np.abs(F)**2/ (W**2).sum()
    fy=np.fft.fftshift(np.fft.fftfreq(n)); fx=fy
    FX,FY=np.meshgrid(fx,fy); FR=np.hypot(FX,FY)
    bins=np.arange(0,0.5001,1.0/n)
    idx=np.digitize(FR.ravel(),bins)-1
    out=np.zeros(len(bins)-1); cnt=np.zeros(len(bins)-1)
    np.add.at(out,idx[(idx>=0)&(idx<len(out))],P.ravel()[(idx>=0)&(idx<len(out))])
    np.add.at(cnt,idx[(idx>=0)&(idx<len(out))],1)
    f=0.5*(bins[:-1]+bins[1:])
    return f, np.where(cnt>0,out/np.maximum(cnt,1),np.nan), cnt

def pair_analysis(f1,f2,ch,center,n=96,regbox=192,label="",scale_match=True):
    P1=planes(f1); P2=planes(f2)
    A=P1[ch]; B=P2[ch]
    c1=auto_c0(P1); c2=auto_c0(P2)
    cx1,cy1,R1,_,_=limb_circle(P1['G1'],'G1',c1,135,172)
    cx2,cy2,R2,_,_=limb_circle(P2['G1'],'G1',c2,135,172)
    # target position given as (radius_frac_of_R, azimuth_deg) relative to limb
    rr,adeg=center
    ax=np.radians(adeg)
    px1=cx1+rr*R1*np.cos(ax); py1=cy1+rr*R1*np.sin(ax)
    px2=cx2+rr*R2*np.cos(ax); py2=cy2+rr*R2*np.sin(ax)
    a0,_,_=crop(A,px1,py1,regbox); b0,_,_=crop(B,px2,py2,regbox)
    if a0.shape!=b0.shape or a0.size==0: return None
    sat = (a0.max()>=SAT) or (b0.max()>=SAT)
    # scale match (handles different exposure times)
    k=np.sum(a0*b0)/np.sum(b0*b0)
    b0s=b0*k
    sh,err,_=phase_cross_correlation(a0-a0.mean(), b0s-b0s.mean(), upsample_factor=200, normalization=None)
    b0r=fshift(b0s,sh)
    m=n//2; c=regbox//2
    a=a0[c-m:c+m,c-m:c+m]; b=b0r[c-m:c+m,c-m:c+m]
    k2=np.sum(a*b)/np.sum(b*b); b=b*k2
    S=a+b; D=a-b
    f,Ps,_=radial_power(S); _,Pd,_=radial_power(D)
    Psig=(Ps-Pd)/4.0
    Pn=Pd/2.0
    return dict(f=f,Ps=Ps,Pd=Pd,Psig=Psig,Pn=Pn,shift=sh,k=k*k2,sat=sat,
                mean=a.mean(),label=label,R1=R1,R2=R2,pos=(px1,py1))

def report(r,name):
    if r is None: print(name,"-> None"); return
    f=r['f']; sig=r['Psig']; noi=r['Pn']
    ratio=sig/np.maximum(noi,1e-30)
    print("== %s  (shift=%.2f,%.2f px, k=%.3f, sat=%s, mean=%.0f ADU)"%(name,r['shift'][0],r['shift'][1],r['k'],r['sat'],r['mean']))
    hdr="  f[cyc/plane-px]  lambda[arcsec]   P_sig      P_noise    S/N_power"
    print(hdr)
    for i in range(len(f)):
        if f[i]<=0: continue
        if i%2 and f[i]<0.3: continue
        lam=2*SCALE/f[i]   # full-res px scale: 1 plane px = 2 fullres px
        print("   %8.4f      %8.2f   %10.3e %10.3e  %8.2f"%(f[i],lam,sig[i],noi[i],ratio[i]))
    # crossing
    good=np.isfinite(ratio)&(f>0.05)
    ff=f[good]; rr=ratio[good]
    cross=np.nan
    for i in range(len(ff)-1):
        if rr[i]>=1 and rr[i+1]<1:
            cross=ff[i]+(1-rr[i])*(ff[i+1]-ff[i])/(rr[i+1]-rr[i]); break
    if np.isnan(cross):
        print("   -> signal power still above noise power at Nyquist (f=0.5 cyc/plane-px); ratio at Nyq=%.2f"%rr[-1])
    else:
        print("   -> crossing f=%.4f cyc/plane-px  => resolution 1/(2f)=%.2f plane px = %.2f arcsec"%(
            cross,1/(2*cross),1/(2*cross)*2*SCALE))
    return cross

if __name__=="__main__":
    cases=[
      ("DSC06983.ARW","DSC06995.ARW",'G1',(1.35,285),"corona 1/30 dither"),
      ("DSC07000.ARW","DSC07002.ARW",'G1',(1.35,285),"corona bracket 1/800+1/100"),
      ("DSC07000.ARW","DSC07002.ARW",'G1',(1.05,70),"prominence bracket"),
      ("DSC07000.ARW","DSC07002.ARW",'G1',(0.55,0),"CONTROL inside moon"),
    ]
    for a,b,ch,pos,lab in cases:
        r=pair_analysis(a,b,ch,pos,label=lab)
        report(r,lab)
        print()
