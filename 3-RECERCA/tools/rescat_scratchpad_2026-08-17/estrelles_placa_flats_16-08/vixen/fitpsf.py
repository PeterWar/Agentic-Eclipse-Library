import numpy as np
from scipy.optimize import least_squares
cand=np.load('cand.npy')
FL=np.load('g_long_flux.npy'); DL=np.load('g_long_den.npy')
FS=np.load('g_short_flux.npy'); DS=np.load('g_short_den.npy')
def fit(F,D,x,y,box=9,free_angle=True):
    x0,y0=int(round(x)),int(round(y))
    sub=F[y0-box:y0+box+1,x0-box:x0+box+1].astype(np.float64)
    sig=1.0/np.sqrt(np.maximum(D[y0-box:y0+box+1,x0-box:x0+box+1],1e-12))
    yy,xx=np.mgrid[-box:box+1,-box:box+1].astype(float)
    def model(p):
        A,cx,cy,sa,sb,th,B=p
        c,s=np.cos(th),np.sin(th)
        u=(xx-cx)*c+(yy-cy)*s; v=-(xx-cx)*s+(yy-cy)*c
        return A*np.exp(-0.5*((u/sa)**2+(v/sb)**2))+B
    p0=[sub.max(),0,0,1.7,1.5,-np.pi/4,0.0]
    lo=[0,-4,-4,0.4,0.4,-np.pi,-abs(sub).max()]
    hi=[np.inf,4,4,8,8,np.pi,abs(sub).max()]
    if not free_angle:
        lo[5]=-np.pi/4-1e-6; hi[5]=-np.pi/4+1e-6
    r=least_squares(lambda p:((model(p)-sub)/sig).ravel(),p0,bounds=(lo,hi))
    A,cx,cy,sa,sb,th,B=r.x
    if sb>sa: sa,sb=sb,sa; th=th+np.pi/2
    th=(np.degrees(th)+90)%180-90
    return dict(A=A,x=x0+cx,y=y0+cy,sa=sa,sb=sb,th=th,B=B)
print('drift PA in array coords = -45.0 deg (dx>0, dy<0)')
print('%4s %8s %8s %7s | sig_maj sig_min  ratio  PA_deg | trail L px  L arcsec  v arcsec/s'%('id','x','y','snr'))
Ls=[];PAs=[]
for i in range(12):
    x,y,pk,sa_,sb_=cand[i]
    g=fit(FL,DL,x,y)
    d=g['sa']**2-g['sb']**2
    L=np.sqrt(12*d) if d>0 else float('nan')
    print('%4d %8.2f %8.2f %7.1f |  %5.2f  %5.2f  %5.3f  %+6.1f | %7.2f %8.2f %9.3f'%(
        i,g['x'],g['y'],pk,g['sa'],g['sb'],g['sa']/g['sb'],g['th'],L,L*2.158,L*2.158/10.3))
    if pk>15 and L==L: Ls.append(L); PAs.append(g['th'])
Ls=np.array(Ls);PAs=np.array(PAs)
print()
print('bright (snr>15) n=%d: trail L = %.2f +- %.2f px = %.2f +- %.2f arcsec  -> v = %.3f +- %.3f arcsec/s'%(
    len(Ls),Ls.mean(),Ls.std(ddof=1)/np.sqrt(len(Ls)),Ls.mean()*2.158,Ls.std(ddof=1)/np.sqrt(len(Ls))*2.158,
    Ls.mean()*2.158/10.3,Ls.std(ddof=1)/np.sqrt(len(Ls))*2.158/10.3))
print('   PA = %.1f +- %.1f deg (expected -45.0)'%(PAs.mean(),PAs.std(ddof=1)/np.sqrt(len(PAs))))
print()
print('--- same fit on the SHORT stack (trail <0.6 px): gives the PSF alone')
S=[]
for i in range(8):
    x,y,pk,_,_=cand[i]
    g=fit(FS,DS,x,y)
    print('%4d sig_maj %5.2f sig_min %5.2f ratio %5.3f PA %+6.1f  FWHM_geo %5.2f px = %5.2f arcsec'%(
        i,g['sa'],g['sb'],g['sa']/g['sb'],g['th'],2.355*np.sqrt(g['sa']*g['sb']),2.355*np.sqrt(g['sa']*g['sb'])*2.158))
    if pk>15: S.append(2.355*np.sqrt(g['sa']*g['sb']))
print('PSF FWHM (short stack, bright) = %.2f +- %.2f px = %.2f arcsec'%(np.mean(S),np.std(S,ddof=1)/np.sqrt(len(S)),np.mean(S)*2.158))
