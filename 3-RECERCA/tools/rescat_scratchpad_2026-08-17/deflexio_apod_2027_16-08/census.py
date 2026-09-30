from skyfield.api import load
from skyfield.data import hipparcos
import numpy as np, sys
try:
    with load.open(hipparcos.URL) as f:
        df = hipparcos.load_dataframe(f)
except Exception as e:
    print("FETCH FAIL", e); sys.exit(1)
df = df[df['magnitude'].notnull()]
ra = df['ra_degrees'].values; dec = df['dec_degrees'].values; mag = df['magnitude'].values
sra, sdec = 131.9672, 17.8642
r1,d1,r2,d2 = np.radians(sra), np.radians(sdec), np.radians(ra), np.radians(dec)
cs = np.sin(d1)*np.sin(d2)+np.cos(d1)*np.cos(d2)*np.cos(r1-r2)
sep = np.degrees(np.arccos(np.clip(cs,-1,1)))
Rsun_deg = 945.6/3600.
rsr = sep/Rsun_deg
for lim in (6,7,8,9,10):
    for rmax in (4,8,14,20):
        m = (mag<=lim)&(rsr<=rmax)&(rsr>=1.1)
        print(f"  V<={lim}  r<{rmax:2d} Rsun : {m.sum():4d}")
    print()
m = (mag<=9)&(rsr<=16)&(rsr>=1.1)
idx = np.argsort(rsr[m])
print("closest 30 Hipparcos stars V<=9 (2027 field):")
print(" r[Rsun]   V     defl(as)   RA        Dec")
for i in np.argsort(rsr)[:400]:
    if mag[i]<=9.2 and rsr[i]>=1.05 and rsr[i]<16:
        print(f" {rsr[i]:6.2f}  {mag[i]:5.2f}   {1.7516/rsr[i]:6.3f}   {ra[i]:8.3f} {dec[i]:8.3f}")
