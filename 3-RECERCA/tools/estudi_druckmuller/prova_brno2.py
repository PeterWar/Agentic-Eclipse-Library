"""PROVA 2 (no es lliurable): color a la Brno + detall en OVERLAY, i dues
corbes de to. Llenc SENCER, cap retall."""
import json, os, sys
import numpy as np
from astropy.io import fits
from scipy.ndimage import gaussian_filter
from PIL import Image
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/eclipse_determinista")
from comu import corba_to

RUN = (__import__("glob").glob(os.path.expanduser("/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/*20260826T112542Z*")) + [""])[0] + "/"
OUT = "/Users/USUARI/Desktop/Eclipse determinista/2-OUTPUT/ESTUDI_DRUCKMULLER"
S = np.asarray(json.load(open(RUN + "4-rebuts/F2.4_cel.json"))["s_corona"], np.float32)
g = json.load(open(RUN + "4-rebuts/F1.2_sol_llenc.json"))["llenc"]
W, H, Rsol = g["W"], g["H"], g["R_sol_px"]

u = np.empty((H, W, 3), np.float32)
for i, c in enumerate("RGB"):
    u[:, :, i] = (fits.getdata(RUN + f"2-ldic/CORONA_{c}.fits").astype(np.float32)
                  + fits.getdata(RUN + f"2-ldic/CEL_{c}.fits").astype(np.float32)) / S[i]
val = np.isfinite(u).all(axis=2)
L = (u[:, :, 0] + 2.0 * u[:, :, 1] + u[:, :, 2]) / 4.0
mk = val.astype(np.float32); den = np.maximum(gaussian_filter(mk, 24.0), 1e-6)
q = np.empty_like(u)
LS = gaussian_filter(np.where(val, L, 0.0), 24.0) / den
for i in range(3):
    q[:, :, i] = (gaussian_filter(np.where(val, u[:, :, i], 0.0), 24.0) / den) / np.maximum(LS, 1e-9)
del u, LS, mk, den

yy, xx = np.mgrid[0:H, 0:W]
r = (np.hypot(yy - H/2.0, xx - W/2.0) / Rsol).astype(np.float32); del yy, xx
anc_v = float(np.nanmedian(np.where(val & (r >= 1.05) & (r <= 1.15), L, np.nan)))

det = np.load(RUN + "3-filtres/DETALL_PASSA_ALT.npy").astype(np.float32)
if det.ndim == 3:
    det = det.mean(axis=2)


def a_lineal(c):
    return np.where(c <= 0.04045, c/12.92, ((c+0.055)/1.055)**2.4)


def a_srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return np.where(c <= 0.0031308, 12.92*c, 1.055*c**(1/2.4) - 0.055)


def overlay(a, b):
    return np.where(a < 0.5, 2*a*b, 1.0 - 2.0*(1.0-a)*(1.0-b))


def fes(pend, anc, sat, etiq):
    y = corba_to(L, val, anc_v, pend=pend, anc=anc, terra=0.045)
    y = overlay(y, det)
    # el croma s'aplica en LINEAL i es torna a codificar: aplicar-lo sobre el
    # valor de pantalla sobresatura (el cel sortia B/R 3,06 quan Brno en fa 1,87)
    ylin = a_lineal(y)
    rgb = a_srgb(ylin[:, :, None] * (1.0 + sat*(q - 1.0)))
    rgb = np.where(val[:, :, None], rgb, 0.0)
    lum = rgb.mean(axis=2)
    fil = []
    for a, b in zip(np.geomspace(1.06, 9.0, 10)[:-1], np.geomspace(1.06, 9.0, 10)[1:]):
        m = (r >= a) & (r < b) & val
        if m.sum() > 5000:
            fil.append((float(np.sqrt(a*b)), float(np.median(lum[m]))))
    print(f"  {etiq}: " + "  ".join(f"{a:.1f}->{b:.3f}" for a, b in fil))
    Image.fromarray((rgb*255+0.5).astype(np.uint8)).resize((W//8, H//8), Image.LANCZOS)\
        .save(os.path.join(OUT, f"PROVA_BRNO_{etiq}_x8.png"))
    return rgb


print("nivell mostrat per radi:")
fes(0.17, 0.68, 1.0, "declarada")
fes(0.24, 0.75, 1.0, "brno")
fes(0.24, 0.75, 0.7, "brno_sat70")
print("Brno 400mm de referencia:  1.2->0.655  1.6->0.470  2.2->0.333  3.0->0.281  3.7->0.257  5.3->0.228")
