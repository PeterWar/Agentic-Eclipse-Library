"""PROVA (no es cap lliurable ni cap mesura): renderitza el nostre llenc a la
manera de Brno, per veure que compra.

Recepta:
  u   = (CORONA + CEL) / s_corona     -> la corona queda NEUTRA i el cel es
                                          queda el seu blau VERITABLE relatiu
  L   = (u_R + 2 u_G + u_B) / 4        -> lluminancia (Brno: el detall i la
                                          corba SEMPRE sobre una brillantor)
  q   = suau(u) / suau(L)              -> color de BAIXA FREQUENCIA (Brno)
  y   = corba declarada sobre L        -> corba ESCALAR, un sol canal
  RGB = y * (1 + sat*(q-1))

⛔ El cel NO es resta: aixi el terra no es negre sino cel, com a Brno. El
producte cientific continua essent els FITS lineals amb el cel restat.
"""
import json, os, sys
import numpy as np
from astropy.io import fits
from scipy.ndimage import gaussian_filter
from PIL import Image

sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/eclipse_determinista")
from comu import corba_to

RUN = (__import__("glob").glob(os.path.expanduser("/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/*20260826T112542Z*")) + [""])[0] + "/"
OUT = "/Users/USUARI/Desktop/Eclipse determinista/2-OUTPUT/ESTUDI_DRUCKMULLER"
os.makedirs(OUT, exist_ok=True)
SIGMA_COLOR = 24.0        # px; "color de baixa frequencia"
SATURACIO = 1.0

cel_r = json.load(open(RUN + "4-rebuts/F2.4_cel.json"))
S = np.asarray(cel_r["s_corona"], dtype=np.float32)
g = json.load(open(RUN + "4-rebuts/F1.2_sol_llenc.json"))["llenc"]
W, H, Rsol = g["W"], g["H"], g["R_sol_px"]
print(f"s_corona = {S}   llenc {W}x{H}  R_sol {Rsol:.1f}")

u = np.empty((H, W, 3), np.float32)
for i, c in enumerate("RGB"):
    u[:, :, i] = (fits.getdata(RUN + f"2-ldic/CORONA_{c}.fits").astype(np.float32)
                  + fits.getdata(RUN + f"2-ldic/CEL_{c}.fits").astype(np.float32)) / S[i]
val = np.isfinite(u).all(axis=2)
print(f"pixels amb dada: {val.sum()/val.size*100:.1f} %")

L = (u[:, :, 0] + 2.0 * u[:, :, 1] + u[:, :, 2]) / 4.0

# color de baixa frequencia, ignorant els forats
mk = val.astype(np.float32)
den = gaussian_filter(mk, SIGMA_COLOR)
uS = np.empty_like(u)
for i in range(3):
    uS[:, :, i] = gaussian_filter(np.where(val, u[:, :, i], 0.0), SIGMA_COLOR) / np.maximum(den, 1e-6)
LS = gaussian_filter(np.where(val, L, 0.0), SIGMA_COLOR) / np.maximum(den, 1e-6)

yy, xx = np.mgrid[0:H, 0:W]
r = (np.hypot(yy - H / 2.0, xx - W / 2.0) / Rsol).astype(np.float32)
del yy, xx
anc = float(np.nanmedian(np.where(val & (r >= 1.05) & (r <= 1.15), L, np.nan)))
print(f"ancora L a 1,05-1,15 R_sol = {anc:.4g}")

y = corba_to(L, val, anc)                       # corba ESCALAR sobre la lluminancia
q = uS / np.maximum(LS, 1e-9)[:, :, None]
rgb = y[:, :, None] * (1.0 + SATURACIO * (q - 1.0))
rgb = np.clip(np.where(val[:, :, None], rgb, 0.0), 0.0, 1.0)

# mesures del resultat, amb la mateixa vara que Brno
def anells(img, lbl):
    print(f"  -- {lbl} --")
    lum = img.mean(axis=2)
    for a, b in zip(np.geomspace(1.06, 9.0, 12)[:-1], np.geomspace(1.06, 9.0, 12)[1:]):
        m = (r >= a) & (r < b) & val
        if m.sum() < 5000:
            continue
        v = img[m]
        print(f"     {np.sqrt(a*b):5.2f} R_sol  nivell {np.median(lum[m]):.3f}   "
              f"R/G {np.median(v[:,0]/np.maximum(v[:,1],1e-6)):.3f}   "
              f"B/G {np.median(v[:,2]/np.maximum(v[:,1],1e-6)):.3f}")
anells(rgb, "PROVA a la manera de Brno")

np.save(os.path.join(OUT, "PROVA_BRNO_rgb.npy"), rgb)
im = (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
Image.fromarray(im).resize((W // 8, H // 8), Image.LANCZOS).save(os.path.join(OUT, "PROVA_BRNO_x8.png"))
print("desat", os.path.join(OUT, "PROVA_BRNO_x8.png"))
