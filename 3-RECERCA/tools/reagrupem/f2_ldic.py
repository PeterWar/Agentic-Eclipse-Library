#!/usr/bin/env python3
"""FASE 2 · Composició LDIC — UNA SOLA suma ponderada al llenç comú.

    g = Sum_i  w(f_i) * ( k_i * f_i + q_i )   /   Sum_i w(f_i)

⛔ Aquí dins NO hi ha cap fusió entre exposicions: no hi ha fronteres i per
tant no hi pot haver cap graó de fusió. Tots els fotogrames entren a la
mateixa suma, amb pes continu.

- `w` depèn del VALOR del píxel: 0 per damunt del 85 % del rang (on es perd la
  linealitat) i 0 al terra de soroll, amb transicions contínues.
- `k_i` (guany) i `q_i` (pedestal) per fotograma surten de la coherència
  contra el compost, amb gauge mediana(ln k) = 0: **l'escala absoluta no es
  toca**.
- ⛔ Tot per canal. La imatge final és en color.
"""

from __future__ import annotations

import glob, json, math, os, sys, time
import numpy as np, cv2, rawpy
from astropy.io import fits

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu  # noqa: E402

PEDESTAL_NOM = 512.0
SAT = 16382.0
SOSTRE = 0.85          # research/101: es queda a 0,85 (baixar-lo costa S/N)
TERRA_DN = 12.0        # ~4 sigma de soroll de lectura
CANALS = ("R", "G", "B")


def finestra(f: np.ndarray, t: float) -> np.ndarray:
    """Pes continu: 0 al terra de soroll, 0 al sostre de linealitat."""
    alt = SOSTRE * (SAT - PEDESTAL_NOM)
    w = np.clip((f - TERRA_DN) / (3.0 * TERRA_DN), 0.0, 1.0)
    w *= np.clip((alt - f) / (0.18 * alt), 0.0, 1.0)
    return (w * t).astype(np.float32)


class Llenc:
    def __init__(s, W, H):
        s.W, s.H = W, H
        s.num = {c: np.zeros((H, W), np.float32) for c in CANALS}
        s.den = {c: np.zeros((H, W), np.float32) for c in CANALS}

    def afegeix(s, canal, sub, num, den):
        y0, y1, x0, x1 = sub
        s.num[canal][y0:y1, x0:x1] += num
        s.den[canal][y0:y1, x0:x1] += den

    def compost(s):
        out = {}
        for c in CANALS:
            d = s.den[c]
            out[c] = np.where(d > 0, s.num[c] / np.maximum(d, 1e-20), np.nan).astype(np.float32)
        return out


def main():
    t0 = time.time()
    S = json.load(open(os.path.join(comu.REBUTS, "F1_sol_llenc.json")))
    LL = S["llenc"]; W, H = LL["vixen"]["W"], LL["vixen"]["H"]
    CXc, CYc = W/2.0, H/2.0
    PA = math.radians(-LL["pa_north_deg_origen"])
    ca, sa = math.cos(PA), math.sin(PA)
    frames = {n: v for n, v in S["fotogrames"].items() if v["coronal"]}
    print(f"llenç {W}x{H} · {len(frames)} fotogrames coronals", flush=True)

    with rawpy.imread(comu.llista(comu.VIXEN, ".CR3")[0]) as r:
        g = comu.geometria(r); mc = comu.mapa_colors(r)
    FLAT = fits.getdata(os.path.join(comu.F0, "flat", "FLAT_RADIAL_R6III.fits")).astype(np.float32)
    darks = {}
    for p in glob.glob(os.path.join(comu.F0, "masters_dark", "*.fits")):
        darks[round(float(p.split("_E")[1].rstrip("s.fits")), 8)] = p
    # origen de cada subpla CFA
    orig = {}
    for i in range(4):
        ys, xs = np.where(mc == i); orig[i] = (int(ys.min()), int(xs.min()))
    col = {0: "R", 1: "G", 2: "B", 3: "G"}

    def dark_de(e):
        k = min(darks, key=lambda q: abs(q - e))
        return fits.getdata(darks[k]).astype(np.float32)

    _dk = {}
    llenc = Llenc(W, H)
    kq = {n: (1.0, 0.0) for n in frames}

    def passada(kq, etiqueta):
        L = Llenc(W, H)
        for j, (n, v) in enumerate(sorted(frames.items()), 1):
            e = v["exp"]
            if e not in _dk: _dk[e] = dark_de(e)
            with rawpy.imread(os.path.join(comu.VIXEN, n)) as r:
                raw = r.raw_image.astype(np.float32)
            cal = (raw - _dk[e]) / FLAT
            sx, sy = v["sol_x"], v["sol_y"]
            # caixa del fotograma al llenç
            cs = []
            for (yy, xx) in ((0,0),(0,g.ample),(g.alt,0),(g.alt,g.ample)):
                dx, dy = xx - sx, yy - sy
                cs.append((CXc + ca*dx - sa*dy, CYc + sa*dx + ca*dy))
            cs = np.array(cs)
            x0 = max(0, int(np.floor(cs[:,0].min()))-2); x1 = min(W, int(np.ceil(cs[:,0].max()))+2)
            y0 = max(0, int(np.floor(cs[:,1].min()))-2); y1 = min(H, int(np.ceil(cs[:,1].max()))+2)
            XX, YY = np.meshgrid(np.arange(x0, x1, dtype=np.float32),
                                 np.arange(y0, y1, dtype=np.float32))
            dX = XX - CXc; dY = YY - CYc
            rawx = ( ca*dX + sa*dY) + sx           # rotació inversa
            rawy = (-sa*dX + ca*dY) + sy
            k_i, q_i = kq[n]
            for i in range(4):
                oy, ox = orig[i]
                pl = cal[oy::2, ox::2]
                wpl = finestra(raw[oy::2, ox::2] - PEDESTAL_NOM, e)
                mx = ((rawx - ox) * 0.5).astype(np.float32)
                my = ((rawy - oy) * 0.5).astype(np.float32)
                val = (k_i * pl / e + q_i).astype(np.float32)
                a = cv2.remap(val*wpl, mx, my, cv2.INTER_LINEAR, borderValue=0.0,
                              borderMode=cv2.BORDER_CONSTANT)
                b = cv2.remap(wpl, mx, my, cv2.INTER_LINEAR, borderValue=0.0,
                              borderMode=cv2.BORDER_CONSTANT)
                L.afegeix(col[i], (y0, y1, x0, x1), a, b)
            if j % 10 == 0 or j == len(frames):
                print(f"  [{etiqueta}] {j}/{len(frames)}  ({time.time()-t0:.0f}s)", flush=True)
        return L

    # ---- passada 1: guany nominal (1/t)
    L1 = passada(kq, "1")
    C1 = L1.compost()

    # ---- coherència: NOMÉS el guany k_i, per mediana píxel a píxel.
    # ⛔ Ajustar k i q alhora és DEGENERAT quan el perfil és pla: mesurat el
    # 26-08, els fotogrames d'1 s demanaven k=2,5 amb q=-1.700, cosa que no és
    # transparència sinó la degeneració. El terme additiu del cel es treu UNA
    # vegada al final del compost, no per fotograma.
    def coherencia(Cref, etiqueta):
        cg = Cref["G"]
        vora = np.isfinite(cg)
        llind = 5.0 * float(np.nanmedian(cg[vora])) if vora.any() else 0.0
        out = {}; lnk = []
        for j, (n, v) in enumerate(sorted(frames.items()), 1):
            e = v["exp"]
            if e not in _dk: _dk[e] = dark_de(e)
            with rawpy.imread(os.path.join(comu.VIXEN, n)) as r:
                raw = r.raw_image.astype(np.float32)
            cal = (raw - _dk[e]) / FLAT
            sx, sy = v["sol_x"], v["sol_y"]
            cs = []
            for (yy_, xx_) in ((0,0),(0,g.ample),(g.alt,0),(g.alt,g.ample)):
                dx, dy = xx_ - sx, yy_ - sy
                cs.append((CXc + ca*dx - sa*dy, CYc + sa*dx + ca*dy))
            cs = np.array(cs)
            x0 = max(0, int(np.floor(cs[:,0].min()))-2); x1 = min(W, int(np.ceil(cs[:,0].max()))+2)
            y0 = max(0, int(np.floor(cs[:,1].min()))-2); y1 = min(H, int(np.ceil(cs[:,1].max()))+2)
            XX, YY = np.meshgrid(np.arange(x0, x1, dtype=np.float32),
                                 np.arange(y0, y1, dtype=np.float32))
            dX = XX - CXc; dY = YY - CYc
            rawx = ( ca*dX + sa*dY) + sx; rawy = (-sa*dX + ca*dY) + sy
            oy, ox = orig[1]
            pl = (cal[oy::2, ox::2] / e).astype(np.float32)
            wpl = finestra(raw[oy::2, ox::2] - PEDESTAL_NOM, e)
            mx = ((rawx - ox)*0.5).astype(np.float32); my = ((rawy - oy)*0.5).astype(np.float32)
            a = cv2.remap(pl, mx, my, cv2.INTER_LINEAR, borderValue=0.0,
                          borderMode=cv2.BORDER_CONSTANT)
            b = cv2.remap(wpl, mx, my, cv2.INTER_LINEAR, borderValue=0.0,
                          borderMode=cv2.BORDER_CONSTANT)
            ref = cg[y0:y1, x0:x1]
            bo = (b > 0.35*float(wpl.max())) & np.isfinite(ref) & (ref > llind) & (a > 0)
            if bo.sum() < 5000:
                out[n] = (1.0, 0.0); continue
            k_ = float(np.median(ref[bo] / a[bo]))
            if not np.isfinite(k_) or k_ <= 0: k_ = 1.0
            out[n] = (k_, 0.0); lnk.append(math.log(k_))
            if j % 15 == 0: print(f"    [{etiqueta}] {j}/{len(frames)} ({time.time()-t0:.0f}s)", flush=True)
        med = float(np.median(lnk)) if lnk else 0.0
        for n in out: out[n] = (out[n][0]/math.exp(med), 0.0)
        ks = np.array([out[n][0] for n in sorted(frames)])
        print(f"  [{etiqueta}] k: mediana {np.median(ks):.4f}  "
              f"p5–p95 {np.percentile(ks,5):.4f}–{np.percentile(ks,95):.4f}  "
              f"dispersió {100*ks.std():.2f} %   (gauge mediana(ln k)=0)", flush=True)
        return out

    print("\nCoherència (guany per fotograma):", flush=True)
    kq2 = coherencia(C1, "c1")
    L2 = passada(kq2, "2"); C2 = L2.compost()
    kq3 = coherencia(C2, "c2")
    L3 = passada(kq3, "3"); C3 = L3.compost()

    # ---- BALANÇ DE BLANCS de llum de dia (l'escena ÉS el Sol)
    with rawpy.imread(os.path.join(comu.VIXEN, sorted(frames)[0])) as r:
        wb = list(r.daylight_whitebalance)
    mult = {"R": wb[0]/wb[1], "G": 1.0, "B": wb[2]/wb[1]}
    print(f"\nbalanç de blancs (llum de dia, normalitzat a G): "
          + "  ".join(f"{c} x{mult[c]:.4f}" for c in CANALS))
    for c in CANALS: C3[c] = (C3[c] * mult[c]).astype(np.float32)

    os.makedirs(comu.F2, exist_ok=True)
    for c in CANALS:
        fits.PrimaryHDU(C3[c]).writeto(os.path.join(comu.F2, f"LDIC_{c}.fits"), overwrite=True)
        fits.PrimaryHDU(L3.den[c]).writeto(os.path.join(comu.F2, f"LDIC_pes_{c}.fits"), overwrite=True)
    json.dump({"kq": {n: list(kq3[n]) for n in kq3}, "sostre": SOSTRE,
               "terra_dn": TERRA_DN, "gauge": "mediana(ln k) = 0",
               "balanc_blancs_daylight": mult,
               "n_fotogrames": len(frames), "llenc": [W, H]},
              open(os.path.join(comu.REBUTS, "F2_ldic.json"), "w"), indent=1)
    print(f"\nfet en {time.time()-t0:.0f} s -> {comu.F2}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
