"""Brno contra el nostre lliurament, mesurats amb la MATEIXA vara.

Correccio: el marc de Brno porta una linia blanca d'1 px que es menjava la
comptabilitat de saturacio. S'erosiona 3 px la vora del contingut.
"""
import json, os
import numpy as np
from PIL import Image
from geometria import CARPETA, carrega, retalla_marc, srgb_a_lineal, centre_i_radi

AQUI = os.path.dirname(os.path.abspath(__file__))
# ⏭️ la carpeta de sortida porta el numero del run al davant: es busca
#    l'ultima del tren en lloc d'escriure-la a ma (que ja havia quedat
#    desfasada: apuntava a `2-OUTPUT/VIXEN/`, que no existeix).
import glob as _g
NOSTRE = sorted(_g.glob(os.path.expanduser(
    "~/Desktop/Eclipse determinista/2-OUTPUT/*_VIXEN_CIENCIA/vistes/LLIURAMENT_x8.png")))[-1]
RATIO = 1.0335
ordre = ["TSE2026_Trigaza_800mm.png", "TSE_2026_530mm_DHS.png",
         "TSE_2026_400mm_DHS.png", "TSE_2026_200mm_DHS.png"]


def analitza(sub, cy, cx, Rsol, etiq):
    lin = srgb_a_lineal(sub)
    lum = sub.mean(axis=2)
    ny, nx = lum.shape
    yy, xx = np.mgrid[0:ny, 0:nx]
    r = np.hypot(yy - cy, xx - cx) / Rsol
    fora = r > 1.00
    n99 = int((lum[fora] >= 0.99).sum())
    rq = r[fora & (lum >= 0.99)]
    r_ple = min(cy, cx, ny - cy, nx - cx) / Rsol

    files = []
    for a, b in zip(np.geomspace(1.05, r.max(), 60)[:-1], np.geomspace(1.05, r.max(), 60)[1:]):
        m = (r >= a) & (r < b)
        if m.sum() < 300:
            continue
        th = np.arctan2((yy - cy)[m], (xx - cx)[m])
        cob = np.unique(((th + np.pi) / (2*np.pi) * 360).astype(int)).size / 360.0
        v = lin[m]
        lv = v @ np.array([0.2126, 0.7152, 0.0722])
        e = v[lv >= np.percentile(lv, 85)].mean(0) - v[lv <= np.percentile(lv, 35)].mean(0)
        files.append((float(np.sqrt(a*b)), cob, float(np.median(lum[m])),
                      float(e[0]/e[1]) if e[1] > 1e-7 else np.nan,
                      float(e[2]/e[1]) if e[1] > 1e-7 else np.nan))
    f = [x for x in files if x[1] > 0.999]
    R = np.array([x[0] for x in f]); N = np.array([x[2] for x in f])
    rg = np.array([x[3] for x in f]); bg = np.array([x[4] for x in f])
    dins = (R < 5.0) & np.isfinite(rg) & np.isfinite(bg)
    disc = lum[r < 0.90]
    return dict(etiq=etiq, n99=n99,
                r99=(float(rq.min()), float(rq.max())) if rq.size else None,
                pic=float(N.max()), r_pic=float(R[np.argmax(N)]), cel=float(N[-3:].mean()),
                r_ple=float(r_ple),
                rg=float(np.median(rg[dins])), bg=float(np.median(bg[dins])),
                rg_sp=(float(np.percentile(rg[dins],10)), float(np.percentile(rg[dins],90))),
                bg_sp=(float(np.percentile(bg[dins],10)), float(np.percentile(bg[dins],90))),
                lluna=float(np.median(disc)), lluna_c=float(np.percentile(disc,95)-np.percentile(disc,5)),
                perfil=[(x[0], x[2]) for x in f])


res = []
P = json.load(open(os.path.join(AQUI, "perfils.json")))
for nom in ordre:
    rgb = carrega(nom); f0,f1,c0,c1 = retalla_marc(rgb)
    sub = rgb[f0+3:f1-3, c0+3:c1-3]          # fora la linia blanca del marc
    g = P[nom]
    res.append(analitza(sub, g["centre"][1]-3, g["centre"][0]-3, g["Rsol_px"],
                        nom.replace("TSE_2026_","").replace("TSE2026_","").replace(".png","")))

im = np.asarray(Image.open(NOSTRE).convert("RGB"), dtype=np.float64)/255.0
lum = im.mean(axis=2)
cy, cx, Rll, _ = centre_i_radi(lum)
res.append(analitza(im, cy, cx, Rll/RATIO, "NOSTRE lliurament 26-08"))
print(f"(el nostre: centre ({cx:.1f},{cy:.1f}), R_lluna {Rll:.1f} px -> R_sol {Rll/RATIO:.1f} px)\n")

h = f"{'':26s} {'crema':>7} {'pic':>6} {'a r':>5} {'cel':>6} {'recorr':>7} {'EST R/G':>9} {'EST B/G':>9} {'Lluna':>7} {'relleu':>7}"
print(h); print("-"*len(h))
for d in res:
    print(f"{d['etiq']:26s} {d['n99']:7d} {d['pic']:6.3f} {d['r_pic']:5.2f} {d['cel']:6.3f} "
          f"{d['pic']-d['cel']:7.3f} {d['rg']:9.3f} {d['bg']:9.3f} {d['lluna']:7.4f} {d['lluna_c']:7.4f}")
    if d['r99']:
        print(f"{'':26s}   (crema de {d['r99'][0]:.2f} a {d['r99'][1]:.2f} R_sol)")
print()
print("Marge del color de l'estructura (p10-p90):")
for d in res:
    print(f"  {d['etiq']:26s} R/G {d['rg_sp'][0]:.3f}-{d['rg_sp'][1]:.3f}   B/G {d['bg_sp'][0]:.3f}-{d['bg_sp'][1]:.3f}")
json.dump(res, open(os.path.join(AQUI,"cara_a_cara.json"),"w"), indent=1)
