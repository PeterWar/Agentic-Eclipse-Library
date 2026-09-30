"""Mesura GraduantColor.tif: quin color va veure Pere, amb numeros.

El fitxer es Display P3 amb transferencia sRGB. Es passa a lineal i despues a
primaries sRGB, que es l'espai on hem mesurat Brno. Sense aixo els quocients
R/G i B/G de P3 i de sRGB no son comparables (P3 te el vermell i el verd mes
saturats: el mateix objecte hi dona R/G mes BAIX).
"""
import os
import numpy as np
import tifffile

F = "/Users/USUARI/Downloads/GraduantColor.tif"
OUT = "/Users/USUARI/Desktop/Eclipse determinista/2-OUTPUT/ESTUDI_DRUCKMULLER"

# P3-D65 -> XYZ -> sRGB (Bradford ja no cal: mateix blanc D65)
P3_XYZ = np.array([[0.48657095, 0.26566769, 0.19821728],
                   [0.22897456, 0.69173852, 0.07928691],
                   [0.00000000, 0.04511338, 1.04394437]])
XYZ_SRGB = np.array([[ 3.24096994, -1.53738318, -0.49861076],
                     [-0.96924364,  1.87596750,  0.04155506],
                     [ 0.05563008, -0.20397696,  1.05697151]])
M = XYZ_SRGB @ P3_XYZ


def a_lineal(c):
    return np.where(c <= 0.04045, c/12.92, ((c+0.055)/1.055)**2.4)


a = tifffile.imread(F)
print("forma", a.shape, a.dtype)
v = (a[:, :, :3].astype(np.float32) / 65535.0)
del a
lin_p3 = a_lineal(v).astype(np.float32)
del v
lin = np.einsum("ij,hwj->hwi", M.astype(np.float32), lin_p3)   # a primaries sRGB
del lin_p3
H, W = lin.shape[:2]
lum = lin @ np.array([0.2126, 0.7152, 0.0722], np.float32)

# centre i radi lunars: el disc es el minim de brillantor envoltat del cim
llind = np.percentile(lum, 99.9)
ys, xs = np.nonzero(lum >= llind)
cy, cx = float(ys.mean()), float(xs.mean())
for _ in range(8):
    th = np.linspace(0, 2*np.pi, 720, endpoint=False)
    rs = np.arange(5.0, min(cy, cx, H-cy, W-cx), 2.0)
    rad = []
    for t in th:
        yy = np.clip((cy+rs*np.sin(t)).astype(int), 0, H-1)
        xx = np.clip((cx+rs*np.cos(t)).astype(int), 0, W-1)
        s = lum[yy, xx]; kp = int(np.argmax(s)); g = np.gradient(s)
        rad.append(rs[int(np.argmax(g[:max(kp, 3)]))])
    rad = np.asarray(rad); med = np.median(rad); bo = np.abs(rad-med) < 0.06*med
    A = np.column_stack([np.cos(th[bo]), np.sin(th[bo]), np.ones(bo.sum())])
    dx, dy, R = np.linalg.lstsq(A, rad[bo], rcond=None)[0]
    cx += dx; cy += dy
    if abs(dx) < 0.05 and abs(dy) < 0.05:
        break
Rsol = R / 1.0335
print(f"centre ({cx:.1f},{cy:.1f})  R_lluna {R:.1f} px  R_sol {Rsol:.1f} px  "
      f"bons {bo.mean()*100:.0f} %   -> camp ±{min(cx,W-cx)/Rsol:.1f} x ±{min(cy,H-cy)/Rsol:.1f} R_sol")

yy, xx = np.mgrid[0:H, 0:W]
r = (np.hypot(yy-cy, xx-cx)/Rsol).astype(np.float32); del yy, xx

print()
print("QUIN COLOR VA VEURE PERE (primaries sRGB, lineal)")
print(f"{'r':>6} {'cob':>5} {'sat':>6} | {'TOT R/G':>8} {'TOT B/G':>8} | {'EST R/G':>8} {'EST B/G':>8}")
vores = np.geomspace(1.04, float(r.max()), 26)
fil = []
for a0, b0 in zip(vores[:-1], vores[1:]):
    m = (r >= a0) & (r < b0)
    if m.sum() < 3000:
        continue
    th = np.arctan2.__call__(0, 1)  # placeholder
    q = lin[m]; L = lum[m]
    ang = np.unique(((np.degrees(np.arctan2(*(np.nonzero(m)[0]-cy, ), )) if False else 0),))
    sat = float((L >= 0.985).mean())
    t = q.mean(0)
    alt = L >= np.percentile(L, 85); baix = L <= np.percentile(L, 35)
    e = q[alt].mean(0) - q[baix].mean(0)
    rc = float(np.sqrt(a0*b0))
    cob = m.sum() / (np.pi*(b0**2-a0**2)*Rsol**2)
    fil.append((rc, cob, sat, t[0]/t[1], t[2]/t[1], e[0]/e[1], e[2]/e[1]))
    print(f"{rc:6.2f} {min(cob,1)*100:4.0f}% {sat*100:5.1f}% | {t[0]/t[1]:8.3f} {t[2]/t[1]:8.3f} "
          f"| {e[0]/e[1]:8.3f} {e[2]/e[1]:8.3f}")
np.save(os.path.join(OUT, "pere_perfil.npy"), np.array(fil))
