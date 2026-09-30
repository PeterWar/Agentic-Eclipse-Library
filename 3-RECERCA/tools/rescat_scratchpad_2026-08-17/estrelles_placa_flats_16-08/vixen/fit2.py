import numpy as np
from scipy.optimize import least_squares
cand=np.load('cand.npy')
FL=np.load('g_long_flux.npy'); DL=np.load('g_long_den.npy')
FS=np.load('g_short_flux.npy'); DS=np.load('g_short_den.npy')
TH=np.radians(-45.05)   # drift direction, array coords
c,s=np.cos(TH),np.sin(TH)
def fitfix(F,D,x,y,box=9):
    x0,y0=int(round(x)),int(round(y))
    sub=F[y0-box:y0+box+1,x0-box:x0+box+1].astype(np.float64)
    sig=1.0/np.sqrt(np.maximum(D[y0-box:y0+box+1,x0-box:x0+box+1],1e-12))
    yy,xx=np.mgrid[-box:box+1,-box:box+1].astype(float)
    def model(p):
        A,cx,cy,sp,sq,B=p
        u=(xx-cx)*c+(yy-cy)*s; v=-(xx-cx)*s+(yy-cy)*c
        return A*np.exp(-0.5*((u/sp)**2+(v/sq)**2))+B
    p0=[max(sub.max(),1e-6),0,0,1.6,1.4,0.0]
    r=least_squares(lambda p:((model(p)-sub)/sig).ravel(),p0,
                    bounds=([0,-4,-4,0.4,0.4,-abs(sub).max()],[np.inf,4,4,6,6,abs(sub).max()]))
    return r.x   # A,cx,cy,sigma_parallel,sigma_perp,B
print('%4s %6s | LONG sp    sq   | SHORT sp    sq   | dsp2   trail L px  arcsec   v"/s | dsq2(ctrl)'%('id','snr'))
Ls=[]
for i in range(12):
    x,y,pk,_,_=cand[i]
    a=fitfix(FL,DL,x,y); b=fitfix(FS,DS,x,y)
    d=a[3]**2-b[3]**2; dq=a[4]**2-b[4]**2
    L=np.sqrt(12*d) if d>0 else float('nan')
    print('%4d %6.1f |   %5.3f %5.3f  |   %5.3f %5.3f  | %+6.3f  %6.2f %7.2f %7.3f | %+6.3f'%(
        i,pk,a[3],a[4],b[3],b[4],d,L,L*2.158,L*2.158/10.3,dq))
    if pk>15 and L==L: Ls.append(L)
Ls=np.array(Ls)
if len(Ls):
    m=Ls.mean(); e=Ls.std(ddof=1)/np.sqrt(len(Ls))
    print('\nbright n=%d: L = %.2f +- %.2f px = %.2f +- %.2f arcsec -> v = %.3f +- %.3f arcsec/s'%(
        len(Ls),m,e,m*2.158,e*2.158,m*2.158/10.3,e*2.158/10.3))
