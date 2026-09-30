#!/usr/bin/env python3
"""FASE 4 bis — les CAPES LDIC, una per esglaó d'exposició, amb el seu pes.

El contracte de fases ho declara **requisit dur**: «la supervisió capa a capa
de Pere és ORTODOXA... es lliura una capa per fotograma o per grup + la seva
màscara de pes». Brno pinta els mapes de pes a mà, un per fotograma.

⛔⛔ **AQUESTES CAPES NO REPRODUEIXEN EL COMPOST SI LES APILES A PHOTOSHOP.**
Photoshop fa composició alfa, que depèn de l'ordre; el compost és
`Σ(w·I)/Σw`, que no. Són per **mirar-les i jutjar-les d'una en una**, que és
per a què el contracte les demana. El compost bo és l'altre fitxer.

Cada capa porta:
- la imatge d'aquell esglaó sol, amb la MATEIXA corba de to que la base;
- la seva **màscara = el pes normalitzat** d'aquell esglaó (on mana i on no).
"""

from __future__ import annotations

import glob, json, math, os, sys, time
import numpy as np, cv2, rawpy
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/encaix_sony")
import comu  # noqa: E402
import f2_ldic as L2  # noqa: E402
import f3_filtres as F3  # noqa: E402

RS = 440.60


def main():
    t0 = time.time()
    S = json.load(open(os.path.join(comu.REBUTS, "F1_sol_llenc.json")))
    K = json.load(open(os.path.join(comu.REBUTS, "F2_ldic.json")))
    LL = S["llenc"]; W, H = LL["vixen"]["W"], LL["vixen"]["H"]
    CXc, CYc = W/2.0, H/2.0
    PA = math.radians(-LL["pa_north_deg_origen"]); ca, sa = math.cos(PA), math.sin(PA)
    frames = {n: v for n, v in S["fotogrames"].items() if v["coronal"]}
    grups = {}
    for n, v in frames.items(): grups.setdefault(round(v["exp"], 8), []).append(n)
    print(f"{len(grups)} esglaons: " + " ".join(f"{e:g}s×{len(v)}" for e, v in sorted(grups.items())),
          flush=True)

    with rawpy.imread(comu.llista(comu.VIXEN, ".CR3")[0]) as r:
        g = comu.geometria(r); mc = comu.mapa_colors(r)
    FLAT = fits.getdata(os.path.join(comu.F0, "flat", "FLAT_RADIAL_R6III.fits")).astype(np.float32)
    darks = {round(float(p.split("_E")[1].rstrip("s.fits")), 8): p
             for p in glob.glob(os.path.join(comu.F0, "masters_dark", "*.fits"))}
    orig = {}
    for i in range(4):
        ys, xs = np.where(mc == i); orig[i] = (int(ys.min()), int(xs.min()))
    col = {0: "R", 1: "G", 2: "B", 3: "G"}
    mfull = np.load(os.path.join(comu.F3, "MASCARA.npy"))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy-H/2.0, xx-W/2.0); del yy, xx
    bcel = json.load(open(os.path.join(comu.REBUTS, "F2_cel_color.json")))["b_cel"]
    Scel = fits.getdata(os.path.join(comu.F2, "COLOR_CEL_S.fits")).astype(np.float32)
    F3j = json.load(open(os.path.join(comu.REBUTS, "F3_filtres.json")))
    anc = F3j["corba_to"]["valor_ancora"]
    mult = {c: anc["G"]/anc[c] for c in ("R", "G", "B")}

    from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16
    from psd_tools.constants import BlendMode
    psd = new_psb(W, H)
    rebut = {"nota": "capes de SUPERVISIO; apilades a Photoshop NO reprodueixen el compost",
             "esglaons": {}}

    for e in sorted(grups):
        num = {c: np.zeros((H, W), np.float32) for c in ("R", "G", "B")}
        den = {c: np.zeros((H, W), np.float32) for c in ("R", "G", "B")}
        dk = fits.getdata(darks[min(darks, key=lambda q: abs(q-e))]).astype(np.float32)
        for n in sorted(grups[e]):
            v = frames[n]; k_i = K["kq"][n][0]
            with rawpy.imread(os.path.join(comu.VIXEN, n)) as r:
                raw = r.raw_image.astype(np.float32)
            cal = (raw - dk)/FLAT
            sx, sy = v["sol_x"], v["sol_y"]
            cs = []
            for (yy_, xx_) in ((0,0),(0,g.ample),(g.alt,0),(g.alt,g.ample)):
                dx, dy = xx_-sx, yy_-sy
                cs.append((CXc+ca*dx-sa*dy, CYc+sa*dx+ca*dy))
            cs = np.array(cs)
            x0 = max(0, int(cs[:,0].min())-2); x1 = min(W, int(cs[:,0].max())+2)
            y0 = max(0, int(cs[:,1].min())-2); y1 = min(H, int(cs[:,1].max())+2)
            XX, YY = np.meshgrid(np.arange(x0,x1,dtype=np.float32), np.arange(y0,y1,dtype=np.float32))
            dX = XX-CXc; dY = YY-CYc
            rawx = (ca*dX+sa*dY)+sx; rawy = (-sa*dX+ca*dY)+sy
            for i in range(4):
                oy, ox = orig[i]
                pl = cal[oy::2, ox::2]
                wpl = L2.finestra(raw[oy::2, ox::2]-L2.PEDESTAL_NOM, e)
                mx = ((rawx-ox)*0.5).astype(np.float32); my = ((rawy-oy)*0.5).astype(np.float32)
                val = (k_i*pl/e).astype(np.float32)
                num[col[i]][y0:y1, x0:x1] += cv2.remap(val*wpl, mx, my, cv2.INTER_LINEAR,
                                                       borderValue=0.0, borderMode=cv2.BORDER_CONSTANT)
                den[col[i]][y0:y1, x0:x1] += cv2.remap(wpl, mx, my, cv2.INTER_LINEAR,
                                                       borderValue=0.0, borderMode=cv2.BORDER_CONSTANT)
        dg = den["G"]
        hi = dg > 0
        rgb = np.zeros((H, W, 3), np.float32)
        for i, c in enumerate(("R", "G", "B")):
            I = np.where(den[c] > 0, num[c]/np.maximum(den[c], 1e-20), np.nan)
            rgb[..., i], _ = F3.corba_to((I - Scel*bcel[i])*mult[c], rad, hi & mfull)
        msk = np.clip(dg/max(float(np.nanmax(dg)), 1e-9), 0, 1)
        nom = f"LDIC {e:g}s  ({len(grups[e])} fotogrames)"
        add_pixel_layer(psd, np.clip(np.rint(rgb*65535), 0, 65535).astype(np.uint16),
                        nom, mask8=(msk*255).astype(np.uint8),
                        blend=BlendMode.NORMAL, visible=(e == 0.5))
        rebut["esglaons"][f"{e:g}"] = {"n": len(grups[e]),
                                       "cobertura_pct": float(100*hi.mean()),
                                       "pes_max": float(np.nanmax(dg))}
        print(f"  capa {nom:32s} cobertura {100*hi.mean():5.1f} %   [{time.time()-t0:.0f}s]",
              flush=True)
        del num, den

    finalize_lr16(psd)
    base = np.load(os.path.join(comu.F3, "BASE_rgb.npy"))
    set_merged(psd, np.clip(np.rint(base*65535), 0, 65535).astype(np.uint16))
    if getattr(psd, "_updated", False): psd._updated = False
    dst = comu.lliurable("Eclipsi_2026_VIXEN_capes_LDIC.psb")
    psd.save(dst)
    print(f"\nPSB: {dst}\n     {os.path.getsize(dst)/1e9:.2f} GB · {len(grups)} capes "
          f"({time.time()-t0:.0f}s)")
    rebut["fitxer"] = dst; rebut["bytes"] = os.path.getsize(dst)
    json.dump(rebut, open(os.path.join(comu.REBUTS, "F4_capes_ldic.json"), "w"), indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
