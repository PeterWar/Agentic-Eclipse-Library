import json, numpy as np, sys, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'.')
from common import SCALE
res=json.load(open("sweep.json"))
good=[r for r in res if r['resid']<0.03 and r['nsec']>=40 and 3<r['fwhm']<15]
print("mesures netes:",len(good))
import collections
by=collections.defaultdict(list)
for r in good:
    by[r['ch']].append(r['fwhm']); by['ALL'].append(r['fwhm'])
for k in ['R','G1','G2','B','ALL']:
    v=np.array(by[k]); 
    if len(v): print("  %-4s n=%2d  FWHM = %.2f +- %.2f (sd)  err_mitjana %.2f  [%.2f .. %.2f]"%(k,len(v),v.mean(),v.std(ddof=1),v.std(ddof=1)/np.sqrt(len(v)),v.min(),v.max()))
print()
fin=np.array([r['fin'] for r in good if np.isfinite(r['fin'])])
fout=np.array([r['fout'] for r in good if np.isfinite(r['fout'])])
print("caiguda cap a DINS  (2x d50->d10, esc. gaussiana): %.2f +- %.2f arcsec (n=%d)"%(fin.mean(),fin.std(ddof=1),len(fin)))
print("caiguda cap a FORA  (2x d50->d90, esc. gaussiana): %.2f +- %.2f arcsec (n=%d)"%(fout.mean(),fout.std(ddof=1),len(fout)))
print()
print("per exposicio:")
for tag in ['1/100','1/30','1/8','1/800']:
    v=[r['fwhm'] for r in good if r['tag'].startswith(tag)]
    if v: print("   %-6s n=%2d  %.2f +- %.2f"%(tag,len(v),np.mean(v),np.std(v,ddof=1) if len(v)>1 else 0))
print()
print("evolucio temporal (mitjana dels canals nets per fotograma):")
order=["DSC06975.ARW","DSC06978.ARW","DSC06981.ARW","DSC06983.ARW","DSC06986.ARW","DSC06992.ARW","DSC06995.ARW","DSC06998.ARW","DSC07002.ARW","DSC07005.ARW"]
tt={"DSC06975.ARW":-3.4,"DSC06978.ARW":-0.5,"DSC06981.ARW":2.5,"DSC06983.ARW":13.5,"DSC06986.ARW":25.5,
    "DSC06992.ARW":58.5,"DSC06995.ARW":77.5,"DSC06998.ARW":82.5,"DSC07002.ARW":100.5,"DSC07005.ARW":104.5}
for nm in order:
    v=[r['fwhm'] for r in good if r['frame']==nm]
    if v: print("   t(C2)=%+6.1f s  %-14s n=%d  FWHM=%.2f +- %.2f"%(tt[nm],nm,len(v),np.mean(v),np.std(v,ddof=1) if len(v)>1 else 0))
# MTF from the mean fitted kernel
from viaA3 import lsf_moffat
fw=np.mean(by['ALL'])
sig=fw/2*SCALE  # placeholder
# use gaussian equivalent in plane px
fw_pl=fw/(2*SCALE)   # FWHM in plane px
s=fw_pl/2.3548
print()
print("MTF (nucli gaussia equivalent FWHM=%.2f arcsec = %.3f px_pla) x obertura de fotosit:"%(fw,fw_pl))
for lam in [25.9,19.4,12.94,9.70,6.47]:
    f=2*SCALE/lam  # cycles per plane px
    M=np.exp(-2*np.pi**2*s**2*f**2)
    px=np.sinc(f*0.5)   # single photosite = 0.5 plane px
    print("   lambda=%6.2f\" (%.2f px_complet)  f=%.3f c/px_pla  MTF_psf=%.3f  x_px=%.3f  total=%.3f"%(
        lam,lam/SCALE,f,M,px,M*px))
