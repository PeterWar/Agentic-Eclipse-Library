"""Simulacio directa: escena coneguda -> mateixa canonada -> es recupera el FWHM?
Es fa als dos trens amb la MATEIXA escena en arcsec i el MATEIX FWHM en arcsec."""
import sys, numpy as np, math
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/cmp')
from esfcmp import sector_fits, stack_esf, fit_esf
from scipy.ndimage import gaussian_filter

rng=np.random.default_rng(11)

def corona(u_as):
    """perfil radial real mesurat (Vixen 572A2987), normalitzat a 1 al pic"""
    us=np.array([-1e4,0,5,10,15,20,25,30,40,50,60,80,200,1e4])
    vs=np.array([1.0,1.0,1.0,0.99,0.95,0.90,0.85,0.79,0.72,0.66,0.60,0.52,0.30,0.20])
    return np.interp(u_as,us,vs)

def make(scale, R_as, fwhm_as, c0, pedestal_out, sigma_read, topo_rms_as, ss=4, seed=1):
    r=rng
    R=R_as/scale
    n=int(2*R+120)
    n=n+ (n%2)
    # graella supermostrejada
    N=n*ss
    ax=(np.arange(N)+0.5)/ss - n/2.0
    X,Y=np.meshgrid(ax,ax)
    rr=np.hypot(X,Y)
    th=np.arctan2(Y,X)
    # topografia lunar: suma d'harmonics fins m=40, rms fixat
    m=np.arange(3,41)
    ph=r.uniform(0,2*np.pi,m.size); am=r.normal(0,1,m.size)/m**0.5
    dR=np.zeros_like(th)
    for k,mm in enumerate(m): dR+=am[k]*np.cos(mm*th+ph[k])
    dR*= (topo_rms_as/scale)/np.std(dR)
    u=(rr-(R+dR))*scale          # arcsec des del limbe
    img=np.where(u>0, c0*corona(u), 0.0)
    # PSF gaussiana en arcsec -> px supermostrejats
    sig=fwhm_as/2.3548/scale*ss
    img=gaussian_filter(img,sig,mode='nearest')
    # caixa del fotosit: mitjana ss x ss
    img=img.reshape(n,ss,n,ss).mean(axis=(1,3))+pedestal_out
    img=img+r.normal(0,sigma_read,img.shape)+r.normal(0,1,img.shape)*np.sqrt(np.clip(img,0,None)*0.0)
    # mascara Bayer RGGB
    c=np.zeros(img.shape,np.uint8)
    c[0::2,0::2]=0; c[0::2,1::2]=1; c[1::2,0::2]=3; c[1::2,1::2]=2
    return img,c,R,n/2.0

def run(train,scale,fwhm_as,c0,sigma_read,topo=3.0,xlim_as=20.0,win_as=30.0,nsec=240):
    img,c,R,cen=make(scale,977.0,fwhm_as,c0,0.0,sigma_read,topo)
    mm=(c==1)|(c==3)
    ys,xs=np.nonzero(mm)
    val=img[ys,xs]
    fits=sector_fits(xs.astype(float),ys.astype(float),val,cen-0.5,cen-0.5,R,win_as/scale,nsec,1e9)
    xc,ym,e,cnt=stack_esf(fits,align=True,xlim=xlim_as/scale,bw=0.05)
    f=fit_esf(xc,ym,e,boxw=1.0)
    snr=float(np.median([q['snr'] for q in fits]))
    # FWHM real esperat: PSF (x) caixa d'1 px
    from esfcmp import fwhm_of
    s=fwhm_as/2.3548/scale
    esp=fwhm_of(1.0,s,s,1.0)*scale
    return dict(train=train,inp=fwhm_as,esperat_tot=esp,mesurat_tot=f['fwhm_tot']*scale,
                mesurat_int=f['fwhm_int']*scale,nok=len(fits),snr=snr)

print('  tren   FWHM_in  esperat_tot  mesurat_tot  mesurat_int  nsec  S/N')
for train,scale,c0,sr in [('vixen',2.158,830.0,3.0),('sony',3.234,2600.0,8.0)]:
    for fw in (4.0,5.5,7.0,8.3,10.0):
        r=run(train,scale,fw,c0,sr)
        print(f"  {r['train']:5s}  {r['inp']:5.2f}    {r['esperat_tot']:6.2f}      {r['mesurat_tot']:6.2f}"
              f"       {r['mesurat_int']:6.2f}     {r['nok']:3d}  {r['snr']:.0f}",flush=True)
