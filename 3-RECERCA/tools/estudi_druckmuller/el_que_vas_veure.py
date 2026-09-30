"""PROVA: el llenc renderitzat TAL COM PERE HO VA VEURE.

Diferencia amb prova_brno2: NO es divideix per s_corona. El groc es queda,
perque es l'atmosfera (extincio a X=6,12 predita 1,758/0,498 contra 1,755/0,498
mesurat). El que SI que s'arregla es la DERIVA: amb la corba per canal el R/G
mostrat anava d'1,06 a 1,35 amb el radi quan la dada el te PLA a 1,76.

  L   = (u_R + 2u_G + u_B)/4      una sola lluminancia
  q   = suau(u)/suau(L)           color de baixa frequencia
  y   = corba ESCALAR sobre L
  RGB = srgb( lineal(y) * (1 + w(q-1)) )   amb w limitat per no sortir de gamut
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
g = json.load(open(RUN + "4-rebuts/F1.2_sol_llenc.json"))["llenc"]
W, H, Rsol = g["W"], g["H"], g["R_sol_px"]

a_lin = lambda c: np.where(c <= 0.04045, c/12.92, ((c+0.055)/1.055)**2.4)
a_srgb = lambda c: np.where(c <= 0.0031308, 12.92*np.clip(c,0,1), 1.055*np.clip(c,0,1)**(1/2.4) - 0.055)
overlay = lambda a, b: np.where(a < 0.5, 2*a*b, 1.0 - 2.0*(1.0-a)*(1.0-b))

u = np.empty((H, W, 3), np.float32)
for i, c in enumerate("RGB"):
    u[:, :, i] = (fits.getdata(RUN + f"2-ldic/CORONA_{c}.fits").astype(np.float32)
                  + fits.getdata(RUN + f"2-ldic/CEL_{c}.fits").astype(np.float32))
# MATRIU DE COLOR de la R6 III: els multiplicadors sols no son colorimetria.
# Sense ella la corona surt 1,89x massa blava (B/G 0,498 en lloc de 0,264).
# convencio dcraw (files de la matriu ENDAVANT normalitzades, i despres
# invertida). Amb l'altra convencio el cel sortia verdos.
MCOL = np.array([[ 1.5596, -0.5903,  0.0307],
                 [-0.1770,  1.6855, -0.5084],
                 [-0.0250, -0.4963,  1.5213]], np.float32)
u = np.einsum("ij,hwj->hwi", MCOL, u)
val = np.isfinite(u).all(axis=2)
L = (u[:, :, 0] + 2.0*u[:, :, 1] + u[:, :, 2]) / 4.0
mk = val.astype(np.float32); den = np.maximum(gaussian_filter(mk, 24.0), 1e-6)
LS = gaussian_filter(np.where(val, L, 0.0), 24.0) / den
q = np.empty_like(u)
for i in range(3):
    q[:, :, i] = (gaussian_filter(np.where(val, u[:, :, i], 0.0), 24.0)/den) / np.maximum(LS, 1e-9)
del u, LS, mk, den

yy, xx = np.mgrid[0:H, 0:W]
r = (np.hypot(yy-H/2.0, xx-W/2.0)/Rsol).astype(np.float32); del yy, xx
anc_v = float(np.nanmedian(np.where(val & (r >= 1.05) & (r <= 1.15), L, np.nan)))
det = np.load(RUN + "3-filtres/DETALL_PASSA_ALT.npy").astype(np.float32)
if det.ndim == 3:
    det = det.mean(axis=2)


def fes(pend, anc, etiq):
    y = overlay(corba_to(L, val, anc_v, pend=pend, anc=anc, terra=0.045), det)
    ylin = a_lin(y)
    # guarda de gamut: acota w perque cap canal no passi d'1. MAI retallar
    # per canal, que aixo canvia el color (avis de Codex).
    qmax = q.max(axis=2)
    with np.errstate(divide="ignore", invalid="ignore"):
        wmax = np.where(qmax > 1.0, (1.0/np.maximum(ylin, 1e-9) - 1.0)/(qmax - 1.0), np.inf)
    w = np.clip(np.nan_to_num(wmax, nan=0.0, posinf=1.0), 0.0, 1.0).astype(np.float32)
    rgb = a_srgb(ylin[:, :, None] * (1.0 + w[:, :, None]*(q - 1.0)))
    rgb = np.where(val[:, :, None], rgb, 0.0).astype(np.float32)
    print(f"  {etiq}: w<1 al {(w < 0.999).mean()*100:.2f} % dels pixels amb dada")
    print(f"  {'r':>6} {'nivell':>7} {'R/G':>7} {'B/G':>7}")
    for a, b in zip(np.geomspace(1.06, 9.0, 11)[:-1], np.geomspace(1.06, 9.0, 11)[1:]):
        m = (r >= a) & (r < b) & val
        if m.sum() < 5000:
            continue
        v = rgb[m]
        print(f"  {np.sqrt(a*b):6.2f} {np.median(v.mean(1)):7.3f} "
              f"{np.median(v[:,0]/np.maximum(v[:,1],1e-6)):7.3f} {np.median(v[:,2]/np.maximum(v[:,1],1e-6)):7.3f}")
    Image.fromarray((np.clip(rgb,0,1)*255+0.5).astype(np.uint8))\
        .resize((W//8, H//8), Image.LANCZOS).save(os.path.join(OUT, f"EL_QUE_VAS_VEURE_{etiq}_x8.png"))
    return rgb


print("EL QUE VAS VEURE (groc conservat, deriva arreglada, MATRIU DE COLOR):")
fes(0.22, 0.74, "v3")
