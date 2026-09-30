#!/usr/bin/env python3
"""ÉS CORONA? El guardrail del 28-08, demanat per Pere.

⛔ **L'error que aquest instrument fa impossible de repetir**: declarar «corona
real» una estructura perquè LA VEUEN ELS DOS TRENS. Els dos trens comparteixen
el cel del lloc: el seu acord només demostra que la cosa és a la llum que
arribava a León. El 28-08 això va estar a punt de beneir com a corona una
franja de cirrus; la va aturar Pere («si fos real, Druckmüller la contemplaria
també») i l'arbitratge de Brno (`research/116` §15.1).

**La regla, ara mecanitzada**: un veredicte «és corona» exigeix TRES columnes,
i la tercera és OBLIGATÒRIA:
  1. els dos trens la veuen (Vixen i Sony, mateix lloc del cel, mateix signe);
  2. amb significància contra un NUL honest;
  3. **un observador d'UN ALTRE LLOC la veu** (els composts de Brno, via el
     registre del `research/114`).

**El nul honest**: el mateix segment, girat a N azimuts aleatoris del mateix
radi, a la MATEIXA imatge. Això calibra cada imatge amb ella mateixa —cap
factor d'amplificació extern, cap comparació de processats diferents— i dona
una z per imatge que sí que es pot comparar entre imatges.

**Veredictes**:
  CORONA REAL      z consistents i del mateix signe als dos trens I a Brno
  NO ÉS CORONA     significativa als nostres trens, |z| < 1,5 de mediana a Brno
                   (amb poder: prou nuls vàlids) → llum del NOSTRE lloc
  INDECÍS          qualsevol altra cosa (i es diu per què)

Ús:
    python3 es_corona.py --seg H 5507 3440 3850 --seg H 4653 2180 2630
    python3 es_corona.py --prova          # autotest amb línia sintètica

⛔ Un segment ha de quedar DINS de la cobertura de Brno (r ≲ 8 R☉ pels DHS).
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
from astropy.io import fits

import nucli as N

sys.path.insert(0, os.path.join(N.AQUI, "..", "eclipse_determinista"))
import comu  # noqa: E402

W, H, RS = 8096, 8960, 440.60304883027544
N_NULS = 36
GUARDA_DEG = 12.0          # els nuls no s'acosten tant al segment
FLANC_PX = 30.0


def punts_segment(seg):
    """(r, θ) de la línia i dels dos flancs, en coordenades del llenç comú."""
    ori, a, b, c = seg
    n = 48
    if ori == "H":
        xs = np.linspace(b, c, n); ys = np.full(n, float(a))
        fl = ((0.0, -FLANC_PX), (0.0, +FLANC_PX))
    else:
        ys = np.linspace(b, c, n); xs = np.full(n, float(a))
        fl = ((-FLANC_PX, 0.0), (+FLANC_PX, 0.0))
    out = []
    for dx, dy in ((0.0, 0.0),) + fl:
        r = np.hypot(xs + dx - W/2, ys + dy - H/2) / RS
        th = np.arctan2(ys + dy - H/2, xs + dx - W/2)
        out.append((r, th))
    return out


def mostra(img, cy, cx, Rpx, gir_rad, r, th):
    yy = cy + r * Rpx * np.sin(th + gir_rad)
    xx = cx + r * Rpx * np.cos(th + gir_rad)
    ny, nx = img.shape
    y0 = np.floor(yy).astype(int); x0 = np.floor(xx).astype(int)
    ok = (y0 >= 0) & (x0 >= 0) & (y0 < ny-1) & (x0 < nx-1)
    y0c = np.clip(y0, 0, ny-2); x0c = np.clip(x0, 0, nx-2)
    fy = yy - y0; fx = xx - x0
    v = (img[y0c,x0c]*(1-fy)*(1-fx) + img[y0c+1,x0c]*fy*(1-fx)
         + img[y0c,x0c+1]*(1-fy)*fx + img[y0c+1,x0c+1]*fy*fx)
    return np.where(ok, v, np.nan)


def contrast(img, geo, punts, dth=0.0):
    """(línia − mitjana dels flancs) / flancs, mediana sobre el segment."""
    cy, cx, Rpx, gir = geo
    vs = [mostra(img, cy, cx, Rpx, gir, r, th + dth) for r, th in punts]
    fons = 0.5 * (vs[1] + vs[2])
    k = np.isfinite(vs[0]) & np.isfinite(fons) & (fons > 0)
    if k.sum() < 24:
        return np.nan, int(k.sum())
    return float(np.median((vs[0][k] - fons[k]) / fons[k])), int(k.sum())


def z_amb_nul(img, geo, punts, rng):
    """z del segment contra N girs aleatoris del MATEIX segment al mateix radi."""
    c0, n0 = contrast(img, geo, punts)
    if not np.isfinite(c0):
        return np.nan, np.nan, 0
    nuls = []
    for _ in range(N_NULS * 3):
        if len(nuls) >= N_NULS:
            break
        dth = rng.uniform(np.deg2rad(GUARDA_DEG), 2*np.pi - np.deg2rad(GUARDA_DEG))
        c, n = contrast(img, geo, punts, dth)
        if np.isfinite(c):
            nuls.append(c)
    if len(nuls) < 15:
        return c0, np.nan, len(nuls)
    nuls = np.array(nuls)
    esc = 1.4826 * np.median(np.abs(nuls - np.median(nuls)))
    return c0, float((c0 - np.median(nuls)) / max(esc, 1e-12)), len(nuls)


def lum_de(tren):
    d = comu.darrer_run(tren)
    out = None
    for c, w in (("R", 1.0), ("G", 2.0), ("B", 1.0)):
        a = fits.getdata(os.path.join(d, "2-ldic", f"LDIC_{c}.fits")).astype(np.float64)
        out = a * (w/4) if out is None else out + a * (w/4)
    return out, os.path.basename(d)


def jutja(seg, imatges, rng):
    punts = punts_segment(seg)
    et = f"{seg[0]} {'y' if seg[0]=='H' else 'x'}={seg[1]} {seg[2]}-{seg[3]}"
    r_mig = float(np.mean(punts[0][0]))
    print(f"\n■ segment {et} · r mitjà {r_mig:.2f} R☉")
    print(f"  {'imatge':>28s} {'contrast':>9s} {'z':>7s} {'nuls':>5s}")
    zs = {}
    for nom, (img, geo) in imatges.items():
        c, z, nn = z_amb_nul(img, geo, punts, rng)
        zs[nom] = z
        print(f"  {nom:>28s} {100*c:+8.2f}% {z:7.1f} {nn:5d}"
              if np.isfinite(c) else f"  {nom:>28s}    (sense cobertura)")
    zv, zs_ = zs.get("VIXEN", np.nan), zs.get("SONYTOT", np.nan)
    zb = [v for k, v in zs.items() if k.startswith("Brno") and np.isfinite(v)]
    # ⏭️ els dos trens es COMBINEN (Stouffer): un senyal feble però coherent als
    #    dos val més que el mateix senyal en un de sol. Exigeix el mateix signe.
    zc = (zv + zs_) / np.sqrt(2.0) if np.isfinite(zv) and np.isfinite(zs_) else np.nan
    nostres = (np.isfinite(zc) and np.sign(zv) == np.sign(zs_)
               and abs(zv) > 1.2 and abs(zs_) > 1.2 and abs(zc) >= 2.5)
    if not zb:
        v = "INDECÍS — Brno sense cobertura o sense poder: NO es pot declarar corona"
    elif nostres and np.median(np.abs(zb)) >= 3 and \
            np.sign(np.median(zb)) == np.sign(zv):
        v = "⏭️ CORONA REAL (els dos trens i Brno, mateix signe)"
    elif nostres and np.median(np.abs(zb)) < 1.5:
        v = ("⛔ NO ÉS CORONA — els dos trens la comparteixen però Brno no la té: "
             "llum del NOSTRE lloc (atmosfera local) o del que compartim")
    else:
        v = "INDECÍS — les columnes no es posen d'acord; mira-ho a mà"
    print(f"  VEREDICTE: {v}")
    return v


def carrega_tot():
    imatges = {}
    for tren in ("VIXEN", "SONYTOT"):
        img, nom = lum_de(tren)
        imatges[tren] = (img, (H/2, W/2, RS, 0.0))
        print(f"  {tren}: {nom}")
    reg = json.load(open(os.path.join(N.AQUI, N.REGISTRE)))
    for nom in reg:
        try:
            br, _, _, _ = N.carrega_brno(nom)
        except Exception:
            continue
        g = reg[nom]
        imatges[f"Brno {nom.split('_')[2].replace('.png','')}"] = \
            (br, (g["cy"], g["cx"], g["R_sol_px"], np.deg2rad(g["gir_deg"])))
    return imatges


def prova():
    """Autotest: una línia sintètica NOMÉS als nostres trens ha de sortir
    «NO ÉS CORONA»; un lloc buit, INDECÍS o res; i el nul no s'autoenganya."""
    rng = np.random.default_rng(7)
    print("PROVA amb línia sintètica del −3 % injectada NOMÉS als dos trens:")
    imatges = carrega_tot()
    seg = ("H", 6200, 4600, 5000)
    for tren in ("VIXEN", "SONYTOT"):
        img, geo = imatges[tren]
        img = img.copy()
        img[6194:6207, 4600:5000] *= 0.97
        imatges[tren] = (img, geo)
    v = jutja(seg, imatges, rng)
    assert "NO ÉS CORONA" in v, f"la prova havia de dir NO ÉS CORONA i diu: {v}"
    print("\nPROVA en un lloc sense res (no pot sortir cap veredicte fort):")
    v2 = jutja(("H", 6600, 5200, 5600), imatges, rng)
    assert "CORONA REAL" not in v2 and "NO ÉS CORONA" not in v2, v2
    print("\n✓ autotest passat")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--seg", nargs=4, action="append", metavar=("ORI", "A", "B", "C"),
                    help="H y x0 x1  ·  V x y0 y1")
    ap.add_argument("--prova", action="store_true")
    args = ap.parse_args()
    if args.prova:
        prova()
        sys.exit(0)
    if not args.seg:
        ap.error("cal --seg o --prova")
    rng = np.random.default_rng(7)
    imatges = carrega_tot()
    for s in args.seg:
        jutja((s[0].upper(), int(s[1]), int(s[2]), int(s[3])), imatges, rng)
