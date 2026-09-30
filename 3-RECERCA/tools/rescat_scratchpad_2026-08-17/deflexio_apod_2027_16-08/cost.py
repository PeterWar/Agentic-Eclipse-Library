import numpy as np, sys
sys.path.insert(0,'.')
from model import *
from final2 import budget, VSD

CAL = dict(extcal=True, dS=5e-7)
TH  = 0.0092*0.24      # bracketed thermal scale drift
def T(b): return np.sqrt(b['tot']**2 + TH**2 + 0.001**2 + 0.0005**2)

rows = [
 ('A  R6 III as flown, no filter, linear fit, no cal fields', 0,
  dict(**VSD, pix=5.17, eta=ETA_BAYER, fwhm=4.13, aext=0.20, csys=0.070, order=1,
       distres_mas=800, coronares_mas=60)),
 ('B  R6 III + red long-pass + 3rd order + cal fields', 400,
  dict(**VSD, pix=5.17, eta=ETA_BAYER, fwhm=3.90, aext=0.14, csys=0.035, order=3,
       distres_mas=150, coronares_mas=10, **CAL)),
 ('C  A7R IIIA + red long-pass + 3rd order + cal fields', 400,
  dict(F=494, D=89.8, sw=35.9, sh=23.9, pix=4.51, eta=ETA_BAYER, fwhm=3.90, aext=0.14,
       csys=0.033, order=3, distres_mas=150, coronares_mas=10, **CAL)),
 ('D  ASI2600MM (APS-C mono) + r\' + cal fields', 2800,
  dict(F=494, D=89.8, sw=23.5, sh=15.7, pix=3.76, eta=ETA_MONO_R, fwhm=3.50, aext=0.12,
       csys=0.020, order=3, distres_mas=25, coronares_mas=8, **CAL)),
 ('E  ASI6200MM (full-frame mono) + r\' + cal fields  <-- PICK', 5500,
  dict(**VSD, pix=3.76, eta=ETA_MONO_R, fwhm=3.50, aext=0.12, csys=0.020, order=3,
       distres_mas=40, coronares_mas=8, **CAL)),
 ('F  E, but no cal fields (in-frame scale) - the fallback', 5500,
  dict(**VSD, pix=3.76, eta=ETA_MONO_R, fwhm=3.50, aext=0.12, csys=0.020, order=3,
       distres_mas=40, coronares_mas=8)),
 ('G  E + buy NP101is/FSQ-106 as a matched second train', 16000,
  dict(F=540, D=101, sw=36, sh=24, pix=3.76, eta=ETA_MONO_R, fwhm=3.30, aext=0.12,
       csys=0.020, order=3, distres_mas=25, coronares_mas=8, **CAL)),
 ('H  second train: Sony 300 @f/4 + ASI2600MM + r\'', 2800,
  dict(F=300, D=75, sw=23.5, sh=15.7, pix=3.76, eta=ETA_MONO_R, fwhm=5.50, aext=0.12,
       csys=0.035, order=3, distres_mas=250, coronares_mas=20)),
 ('I  second train: Sony 300 + A7R IIIA + red filter', 400,
  dict(F=300, D=107, sw=35.9, sh=23.9, pix=4.51, eta=ETA_BAYER, fwhm=5.80, aext=0.14,
       csys=0.045, order=3, distres_mas=400, coronares_mas=25)),
]
print(f"{'option':56s} {'N*':>5s} {'sigma(eps)':>11s} {'GR':>5s} {'E-N':>5s} {'EUR':>6s} {'EUR per % gained':>17s}")
print('-'*112)
B={}
base=None
for nm,c,kw in rows:
    b=budget(**kw); t=T(b); B[nm[0]]=(b,t)
    if base is None: base=t
    gain = (base-t)*100
    per = f"{c/gain:,.0f}" if gain>0.05 else "-"
    print(f"{nm:56s} {b['N']:5d} {t*100:10.2f}% {1/t:5.0f} {0.5/t:5.1f} {c:6d} {per:>17s}")

print("\nTWO TRAINS (primary = E):")
def comb(a,b,rho):
    sa,sb=a[1],b[1]
    ca=np.sqrt(a[0]['bd']**2+a[0]['bc']**2+a[0]['bs']**2+TH**2)
    cb=np.sqrt(b[0]['bd']**2+b[0]['bc']**2+b[0]['bs']**2+TH**2)
    cov=rho*ca*cb
    return np.sqrt((sa**2*sb**2-cov**2)/(sa**2+sb**2-2*cov))
for k,nm,rho in (('H','+ Sony 300 @f/4 + ASI2600MM (indep. optics)',0.3),
                 ('I','+ Sony 300 + A7R IIIA + red filter',0.3),
                 ('C','+ A7R IIIA on a 2nd 494 mm scope',0.5),
                 ('G','+ a matched NP101is/FSQ mono train',0.3)):
    print(f"   {nm:46s} {comb(B['E'],B[k],rho)*100:6.2f}%   (E alone {B['E'][1]*100:.2f}%)")
