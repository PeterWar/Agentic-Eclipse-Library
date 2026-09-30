"""Prova d'injeccio i d'obertures buides sobre els fotogrames Sony reals,
amb EXACTAMENT el mateix phot_stamp del pipeline original."""
import numpy as np, rawpy, pandas as pd, pickle, sys, json
from scipy import ndimage as ndi
sys.path.insert(0,'/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/xmatch')
from phot2 import phot_stamp
SD='/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/sony_stars/'
D='/Users/USUARI/Desktop/Eclipse 2026/300mm/'
sol=json.load(open('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/xmatch/final_solution.json'))['sony_radial']
off=pickle.load(open(SD+'offsets6.pkl','rb'))['off']
MD={e:np.load(SD+f'masterdark_{int(e)}s.npy') for e in (8.,)}
tab=pd.read_csv('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/xmatch/final_match_sony.csv')
name,e='DSC06993',8.0
with rawpy.imread(D+name+'.ARW') as r:
    raw=r.raw_image_visible.astype(np.float32); col=r.raw_colors_visible
bkg=np.load(SD+f'bkg_{name}.npy')
res=raw-MD[e]-bkg
green=(col==1)|(col==3)
valid=green&(raw<15600)&(~ndi.binary_dilation(raw>=15600,iterations=6))
H,W=res.shape
dx,dy=off[name]
sx,sy=sol['sun_x']+dx,sol['sun_y']+dy
RSUN=947.07/sol['scale']
rng=np.random.default_rng(3)
# posicions reals de les estrelles per evitar-les
SXp=tab.x.values+dx; SYp=tab.y.values+dy

def band(rlo,rhi,n):
    out=[]
    while len(out)<n:
        th=rng.uniform(0,2*np.pi); rr=rng.uniform(rlo,rhi)*RSUN
        x,y=sx+rr*np.cos(th),sy+rr*np.sin(th)
        if not(50<x<W-50 and 50<y<H-50): continue
        if np.min(np.hypot(SXp-x,SYp-y))<60: continue
        out.append((x,y))
    return out

print(f'=== SONY {name}, {e}s.  Obertures BUIDES: biaix i soroll reals ===')
print(f'{"banda R/Rsol":>13s} {"n":>4s} {"F(r=6) mediana":>15s} {"desv":>9s} {"biaix/soroll":>13s} {"fons_local":>11s}')
BANDS=[(1.5,2.5),(2.5,4),(4,6),(6,9),(9,14)]
noise={}
for lo,hi in BANDS:
    pos=band(lo,hi,120); F=[];B=[]
    for x,y in pos:
        o=phot_stamp(res,valid,x,y,recenter=False)
        if o is None: continue
        F.append(o[0][5]*2.0/e); B.append(o[1])
    F=np.array(F); B=np.array(B)
    med=np.median(F); sd=1.4826*np.median(np.abs(F-med))
    noise[(lo,hi)]=sd
    print(f'{lo:5.1f}-{hi:5.1f} {len(F):9d} {med:15.1f} {sd:9.1f} {med/sd:13.2f} {np.median(B):11.0f}')

print(f'\n=== INJECCIO d\'estrelles sinteti-ques de flux CONEGUT (PSF gaussiana FWHM 3,74 px) ===')
print('   (flux injectat en ADU/s superficie verda, com el pipeline)')
print(f'{"banda":>13s} {"F_inj":>8s} {"n":>4s} {"F_rec/F_inj mediana":>21s} {"desv":>8s} {"perdua(mag)":>12s}')
sig=3.74/2.3548
for lo,hi in BANDS:
    for Finj in (400.,1200.):
        pos=band(lo,hi,60); rat=[]
        for x,y in pos:
            xi,yi=int(round(x)),int(round(y))
            P=50
            sub=res[yi-P:yi+P+1,xi-P:xi+P+1].copy()
            Y,Xg=np.mgrid[-P:P+1,-P:P+1]
            # flux ADU total al fotograma = Finj*e/2 sobre pixels verds
            amp=(Finj*e/2.0)/(2*np.pi*sig**2)
            psf=amp*np.exp(-((Xg-(x-xi))**2+(Y-(y-yi))**2)/(2*sig**2))
            # la PSF cau sobre TOTS els pixels; nomes els verds es sumen -> factor 2 al final
            res[yi-P:yi+P+1,xi-P:xi+P+1]=sub+psf
            o=phot_stamp(res,valid,x,y)
            res[yi-P:yi+P+1,xi-P:xi+P+1]=sub
            if o is None: continue
            cog=np.load('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/ea55df18-8190-4129-9f09-fd3063da460e/scratchpad/xmatch/cogf_sony.npz')
            corr=cog['ref'][5]/np.nanmedian(cog['ref'][13:18])
            rat.append((o[0][5]*2.0/e/corr)/Finj)
        rat=np.array(rat); md=np.median(rat)
        print(f'{lo:5.1f}-{hi:5.1f} {Finj:8.0f} {len(rat):4d} {md:21.3f} {1.4826*np.median(np.abs(rat-md)):8.3f} {-2.5*np.log10(md):+12.3f}')
