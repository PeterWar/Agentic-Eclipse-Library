"""La prova de control: si dividim per s_corona, que QUEDA?

Si la normalitzacio esborra tot el color, es que estem esborrant fisica.
Si les protuberancies continuen VERMELLES (Halfa) i el continu queda neutre,
es que hem tret l'instrument i hem deixat la fisica. Aquest es l'unic
control honest que te aquesta operacio.
"""
import json
import numpy as np
from astropy.io import fits

R = (__import__("glob").glob(os.path.expanduser("/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/*20260826T112542Z*")) + [""])[0] + "/"
g = json.load(open(R + "4-rebuts/F1.2_sol_llenc.json"))["llenc"]
W, H, Rsol = g["W"], g["H"], g["R_sol_px"]
cy, cx = H / 2.0, W / 2.0

cub = np.stack([fits.getdata(R + f"2-ldic/CORONA_{c}.fits").astype(np.float32) for c in "RGB"], -1)
yy, xx = np.mgrid[0:H, 0:W]
r = (np.hypot(yy - cy, xx - cx) / Rsol).astype(np.float32)
th = np.degrees(np.arctan2(-(yy - cy), xx - cx)) % 360.0
del yy, xx

S = np.array([1.765, 1.000, 0.497])            # el vector mesurat de la corona
u = cub / S                                     # normalitzat

print("=== A. EL CONTINU QUEDA NEUTRE? (anells sencers, mediana per anell) ===")
print(f"{'r':>6} {'u_R/u_G':>9} {'u_B/u_G':>9}   (1,000 = neutre perfecte)")
vores = np.geomspace(1.06, 6.0, 16)
for a, b in zip(vores[:-1], vores[1:]):
    m = (r >= a) & (r < b) & np.isfinite(cub).all(-1)
    if m.sum() < 5000:
        continue
    v = u[m]
    L = v @ np.array([0.2126, 0.7152, 0.0722])
    k = L > np.percentile(L, 50)
    print(f"{np.sqrt(a*b):6.2f} {np.median(v[k,0]/v[k,1]):9.3f} {np.median(v[k,2]/v[k,1]):9.3f}")

print()
print("=== B. LES PROTUBERANCIES CONTINUEN VERMELLES? (anell 1,00-1,06 R_sol) ===")
anell = (r >= 1.00) & (r < 1.06) & np.isfinite(cub).all(-1)
v = u[anell]; t = th[anell]
rg = v[:, 0] / np.maximum(v[:, 1], 1e-6)
print(f"  pixels de l'anell: {anell.sum()}")
print(f"  u_R/u_G  mediana {np.median(rg):.3f}   p90 {np.percentile(rg,90):.3f}   "
      f"p99 {np.percentile(rg,99):.3f}   p99,9 {np.percentile(rg,99.9):.3f}   max {rg.max():.2f}")
forts = rg > 1.5
print(f"  px amb u_R/u_G > 1,5: {forts.sum()} ({forts.mean()*100:.2f} %)")
if forts.sum():
    h, _ = np.histogram(t[forts], bins=36, range=(0, 360))
    top = np.argsort(h)[::-1][:4]
    print("  azimuts (0=E, antihorari) amb mes vermell: " +
          ", ".join(f"{k*10}-{k*10+10} deg ({h[k]} px)" for k in sorted(top) if h[k] > 20))

print()
print("=== C. QUANT DE CROMA QUEDA, I VAL LA PENA? (desviacio de la neutralitat) ===")
for a, b in [(1.06, 1.3), (1.3, 2.0), (2.0, 3.0), (3.0, 4.5)]:
    m = (r >= a) & (r < b) & np.isfinite(cub).all(-1)
    v = u[m]
    L = v @ np.array([0.2126, 0.7152, 0.0722])
    k = L > np.percentile(L, 60)
    v = v[k]; L = L[k]
    q = v / L[:, None]
    d = np.hypot(q[:, 0] - 1, q[:, 2] - 1)
    print(f"  {a:.2f}-{b:.2f} R_sol: croma residual mediana {np.median(d)*100:5.2f} %   "
          f"p90 {np.percentile(d,90)*100:5.2f} %   -> saturacio x{1/max(np.median(d),1e-9)*0.30:.0f} per veure'l al 30 %")

print()
print("=== D. HI HA SENYAL DE Fe XIV (corona E, verd) a 1,1-1,6 R_sol? ===")
for a, b in [(1.06, 1.2), (1.2, 1.4), (1.4, 1.6), (1.6, 2.0), (2.0, 3.0), (3.0, 4.5)]:
    m = (r >= a) & (r < b) & np.isfinite(cub).all(-1)
    v = u[m]
    L = v @ np.array([0.2126, 0.7152, 0.0722])
    k = L > np.percentile(L, 60)
    v = v[k]
    exces_G = np.median(v[:, 1] / (0.5 * (v[:, 0] + v[:, 2])))
    print(f"  {a:.2f}-{b:.2f} R_sol: G / mitjana(R,B) = {exces_G:.4f}  "
          f"({(exces_G-1)*100:+.2f} % d'exces verd)")
