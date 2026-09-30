"""Separa la corona real dels artefactes de remostreig.

Tres proves independents:

A) ESCALAT ANGULAR AMB EL RADI. Una estructura REAL de corona té una amplada
   ANGULAR fixa: la seva freqüència azimutal m no depèn del radi. Un artefacte
   de remostreig té una amplada en PÍXELS fixa: la seva m creix proporcional a
   r. Es mesura l'espectre de potència azimutal a diversos radis i es mira on
   cau el centroide.

B) TRAMA FINA. Espectre 2-D d'un tros de fons: un patró de remostreig hi deixa
   pics discrets (Nyquist, període 2, batecs de la reixa de drizzle).

C) COSTURES EN FALCA. El mapa de cobertura i el nombre de fotogrames que
   contribueixen a cada píxel, en polars.
"""
import os
import sys
import json
import math

import numpy as np
import cv2
from scipy.ndimage import uniform_filter, gaussian_filter

sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
os.environ.setdefault("SENSE_PRNU", "0")
import hdr_corona_vixen as M  # noqa: E402

OUT = M.OUT
NA = 4096          # mostres azimutals


def polar(img, cy, cx, nr):
    return cv2.warpPolar(np.nan_to_num(img, nan=0.0).astype(np.float32),
                         (nr, NA), (cx, cy), float(nr),
                         cv2.INTER_LINEAR + cv2.WARP_POLAR_LINEAR)


def espectre_azimutal(pol, rr, r0, r1, valid_pol=None):
    """Potència per freqüència azimutal m, mitjanada sobre l'anell r0..r1."""
    sel = (rr > r0) & (rr < r1)
    if sel.sum() < 4:
        return None
    b = pol[:, sel].astype(np.float64)
    if valid_pol is not None:
        v = valid_pol[:, sel]
        if v.mean() < 0.98:
            return None
    # cada radi es normalitza per la seva pròpia mitjana → contrast relatiu
    mu = b.mean(0, keepdims=True)
    b = b / np.maximum(mu, 1e-12) - 1.0
    F = np.fft.rfft(b * np.hanning(NA)[:, None], axis=0)
    P = (np.abs(F) ** 2).mean(1)
    return P


def centroide(P, m0, m1):
    m = np.arange(len(P))
    s = (m >= m0) & (m <= m1)
    w = P[s]
    return float((m[s] * w).sum() / max(w.sum(), 1e-30))


def main():
    hdr = np.load(OUT / "hdr_vixen_countss.npy")
    cob = np.load(OUT / "hdr_vixen_cobertura.npy")
    H, W, _ = hdr.shape
    cy, cx = H / 2.0, W / 2.0
    print(f"compost {W}×{H}, R☉ = {M.R_SOL_PX:.1f} px, "
          f"cercle inscrit = {min(H,W)/2/M.R_SOL_PX:.2f} R☉")

    L = hdr[..., 1]                      # verd: el més net
    valid = np.all(np.isfinite(hdr), axis=2)
    r = M.anells(H, W, cy, cx)
    base, _perf = M.perfil_azimutal(np.where(valid, L, np.nan), r, min(H, W) / 2.0)
    norm = np.where(valid, L / np.maximum(base, 1e-9), np.nan)

    nr = int(min(H, W) / 2)
    pol = polar(norm, cy, cx, nr)
    polv = polar(valid.astype(np.float32), cy, cx, nr)
    rr = np.arange(nr) / M.R_SOL_PX

    print("\n=== A) escalat angular amb el radi ===")
    print("Si el centroide de m creix com r → amplada FIXA EN PÍXELS = artefacte.")
    print("Si es queda constant → amplada ANGULAR fixa = corona.\n")
    print(f"{'anell (R☉)':>12} {'m centr.':>9} {'m/r':>8} {'ampl (°)':>9} "
          f"{'ampl (px)':>10} {'contrast':>9}")
    files = []
    for r0, r1 in [(1.15, 1.35), (1.35, 1.65), (1.65, 2.05), (2.05, 2.55),
                   (2.55, 3.15), (3.15, 3.85), (3.85, 4.65)]:
        P = espectre_azimutal(pol, rr, r0, r1, polv)
        if P is None:
            continue
        # banda d'interès: de m=20 (18°) a m=1200 (0,3°)
        cm = centroide(P, 20, 1200)
        rm = 0.5 * (r0 + r1)
        ampl_deg = 360.0 / cm
        ampl_px = math.radians(ampl_deg) * rm * M.R_SOL_PX
        con = math.sqrt(P[20:1200].sum() * 2 / NA)
        files.append((rm, cm, ampl_deg, ampl_px, con))
        print(f"{r0:5.2f}–{r1:4.2f} {cm:9.1f} {cm/rm:8.1f} {ampl_deg:9.3f} "
              f"{ampl_px:10.1f} {con:9.4f}")

    if len(files) >= 3:
        rms = np.array([f[0] for f in files])
        cms = np.array([f[1] for f in files])
        p = np.polyfit(np.log(rms), np.log(cms), 1)[0]
        print(f"\n  pendent d(log m)/d(log r) = {p:+.3f}")
        print("   0,0 = corona pura (angular)   ·   +1,0 = artefacte de reixa (píxels)")

    print("\n=== A bis) espectre azimutal detallat a 2,05–2,55 R☉ ===")
    P = espectre_azimutal(pol, rr, 2.05, 2.55, polv)
    tot = P[5:2000].sum()
    for lo, hi in [(5, 20), (20, 60), (60, 180), (180, 400), (400, 900),
                   (900, 2000)]:
        print(f"  m {lo:4d}–{hi:4d}  ({360/hi:6.2f}°–{360/lo:6.2f}°) : "
              f"{100*P[lo:hi].sum()/tot:5.1f} %")
    # pics discrets?
    m = np.arange(len(P))
    s = (m > 30) & (m < 2000)
    sm = uniform_filter(P, 41)
    exc = P[s] / np.maximum(sm[s], 1e-30)
    top = np.argsort(exc)[-8:][::-1]
    print("  pics per damunt del continu (m, excés):")
    for i in top:
        print(f"     m={m[s][i]:5d}  ×{exc[i]:.2f}   ({360/m[s][i]:.3f}°)")

    print("\n=== B) trama fina: espectre 2-D del fons ===")
    for nom, y0, x0 in [("fons NE", int(cy - 1900), int(cx + 1400)),
                        ("fons SW", int(cy + 1400), int(cx - 1900))]:
        pt = norm[y0:y0 + 512, x0:x0 + 512]
        if not np.isfinite(pt).all():
            print(f"  {nom}: fora de dades")
            continue
        pt = pt - gaussian_filter(pt, 8)
        F = np.fft.fftshift(np.abs(np.fft.fft2(pt * np.outer(np.hanning(512),
                                                             np.hanning(512))))**2)
        c = 256
        fy, fx = np.mgrid[-c:c, -c:c]
        fr = np.hypot(fy, fx)
        anell = np.array([F[(fr >= k) & (fr < k + 1)].mean() for k in range(1, 250)])
        pic = int(np.argmax(anell / np.maximum(uniform_filter(anell, 31), 1e-30))) + 1
        print(f"  {nom}: pic radial a f={pic}/512 → període {512/pic:.2f} px, "
              f"excés ×{anell[pic-1]/uniform_filter(anell,31)[pic-1]:.2f}")
        # Nyquist exacte (període 2 px) i període 4
        for per in (2.0, 2.828, 4.0):
            k = int(round(512 / per))
            if 1 <= k < 250:
                print(f"     període {per:.3f} px (k={k}): "
                      f"×{anell[k-1]/uniform_filter(anell,31)[k-1]:.2f} del continu")

    print("\n=== C) costures: nombre de fotogrames per píxel, en polars ===")
    cb = polar(cob[..., 1].astype(np.float32), cy, cx, nr)
    for r0, r1 in [(1.15, 1.35), (1.65, 2.05), (2.55, 3.15), (3.85, 4.65)]:
        sel = (rr > r0) & (rr < r1)
        v = cb[:, sel].mean(1)
        print(f"  {r0:4.2f}–{r1:4.2f} R☉: cobertura {v.mean():6.2f} "
              f"± {v.std():5.3f}  (min {v.min():.2f} max {v.max():.2f}, "
              f"variació azimutal {100*v.std()/max(v.mean(),1e-9):.2f} %)")

    np.save("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/"
            "8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/pol_norm.npy",
            pol[:, :int(5.0 * M.R_SOL_PX)])
    print("\n(polar guardat)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
