"""Rang útil de cada exposició de la totalitat (Vixen + Canon R6 III), i fins on
es poden agrupar exposicions diferents sense afegir soroll ni dades saturades.

Contesta, amb mesura sobre els CR3 crus i sense desbayerar:

1. quines imatges són DINS la totalitat (els contactes surten de la pròpia dada,
   per la fracció de píxels saturats dels fotogrames de 1/3200);
2. quin tram de brillantor cobreix cada exposició —del sostre de linealitat al
   senyal amb SNR = 3— i a quins radis cau aquest tram;
3. quin pes aporta cada esglaó a cada radi en una suma ponderada per inversa de
   variància, que és el que fa la fase 2, i què s'hi guanya agrupant-los.

Constants de la fase 0 d'aquesta mateixa cadena (pedestal mesurat 512,00 DN,
pou 16382, sostre del pes al 85 % del rang, soroll de lectura per canal). El
guany en e⁻/DN ve de `research/75`. El factor absolut a B/B☉ també.

⛔ Cap retall: els perfils es fan sobre el fotograma sencer amb marges exclosos
només per la màscara del sensor, i les vistes són diagrames, no imatges
retallades del llenç.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor

import numpy as np
import rawpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import comu

# ----------------------------------------------------------------- constants
PEDESTAL = 512.0          # fase 0, mediana als quatre canals CFA
POU = 16382.0             # fase 0: els cremats s'amunteguen aquí, no a 16383
SOSTRE = PEDESTAL + 0.85 * (POU - PEDESTAL)      # 14.001,5 DN — el sostre del pes de la fase 2
GUANY = 5.08              # e⁻/DN a R i G (research/75)
SREAD = {True: 1.05, False: 2.72}                # DN; True = exposicions >= 1 s
RSUN_PX = 440.4           # radi solar al RAW nadiu (research/71, manifest del pilot)
RSUN = RSUN_PX / 2.0      # en superpíxels 2x2
BFACT = 2.772e-11         # B/B☉ per DN/s i píxel verd (research/75 §5.2, ±10 %)
LLAVOR = (1787.5, 1130.0) # llavor de centre, en superpíxels

# fracció corona/total del compost, mètode del color de la fase 2. Serveix per
# no dir «SNR» d'un senyal que a fora és cel: a 5 R☉ el cel n'és el 93 %.
FRAC_R = np.array([1.05, 1.10, 2.00, 3.00, 5.00, 9.00])
FRAC_V = np.array([0.995, 0.9905, 0.684, 0.300, 0.068, 0.020])

EDGES = np.concatenate([np.linspace(0.0, 1.0, 21)[:-1], np.geomspace(1.0, 9.0, 80)])
RC = 0.5 * (EDGES[1:] + EDGES[:-1])
NB = len(RC)
FRAC = np.clip(np.interp(np.log(RC), np.log(FRAC_R), FRAC_V), 0.01, 1.0)

sread = lambda t: SREAD[t >= 1.0]
nom = lambda t: f"1/{1/t:.0f}" if t < 1 else f"{t:g} s"


def carpeta_totalitat() -> str:
    for c in (comu.VIXEN,
              os.path.expanduser("~/Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat"),
              os.path.join(comu.VIXEN, "Vixen Fase totalitat")):
        if os.path.isdir(c) and any(n.upper().endswith(".CR3") for n in os.listdir(c)):
            return c
    raise SystemExit("no trobo els CR3 de la totalitat")


# ------------------------------------------------------------------- mesura
def plans(path):
    with rawpy.imread(path) as r:
        v = r.raw_image_visible.astype(np.float32)
    h, w = (v.shape[0] // 2) * 2, (v.shape[1] // 2) * 2
    v = v[:h, :w]
    return {"R": v[0::2, 0::2], "G1": v[0::2, 1::2], "G2": v[1::2, 0::2], "B": v[1::2, 1::2]}


def _polar(G, cx, cy, r0, r1, dr=0.25, na=360):
    a = np.linspace(0, 2 * np.pi, na, endpoint=False)[:, None]
    rs = np.arange(r0, r1, dr)[None, :]
    ys, xs = cy + np.sin(a) * rs, cx + np.cos(a) * rs
    y0 = np.clip(np.floor(ys).astype(int), 0, G.shape[0] - 2)
    x0 = np.clip(np.floor(xs).astype(int), 0, G.shape[1] - 2)
    fy, fx = ys - y0, xs - x0
    val = (G[y0, x0] * (1 - fy) * (1 - fx) + G[y0 + 1, x0] * fy * (1 - fx)
           + G[y0, x0 + 1] * (1 - fy) * fx + G[y0 + 1, x0 + 1] * fy * fx)
    return val, rs[0]


def limbe(G):
    """Centre i radi del limbe lunar pel MÀXIM DE GRADIENT radial.

    ⛔ No per llindar: un creuament al 50 % el subestima un 3 % (mesurat: 443 px
    contra 453) perquè les ales de la PSF de la corona pugen el nivell dins del
    disc. El màxim de gradient no en depèn.
    """
    cx, cy = LLAVOR
    R = RSUN * 1.031
    for it in range(6):
        pol, rs = _polar(G, cx, cy, max(R * 0.86, 8), R * 1.14)
        k = 9 if it < 2 else 5
        pol = np.apply_along_axis(lambda v: np.convolve(v, np.ones(3) / 3, "same"), 1, pol)
        pol = np.vstack([np.convolve(np.r_[pol[-k:, j], pol[:, j], pol[:k, j]],
                                     np.ones(k) / k, "same")[k:-k] for j in range(pol.shape[1])]).T
        g = np.gradient(pol, axis=1)
        j = np.argmax(g[:, 2:-2], axis=1) + 2
        n = np.arange(len(j))
        g0, g1, g2 = g[n, j - 1], g[n, j], g[n, j + 1]
        den = g0 - 2 * g1 + g2
        off = np.where(np.abs(den) > 1e-9, 0.5 * (g0 - g2) / np.where(den == 0, 1, den), 0)
        rad = rs[j] + np.clip(off, -1, 1) * (rs[1] - rs[0])
        a = np.linspace(0, 2 * np.pi, len(rad), endpoint=False)
        y, x = cy + np.sin(a) * rad, cx + np.cos(a) * rad
        for _ in range(2):
            A = np.c_[2 * x, 2 * y, np.ones(len(x))]
            sol, *_ = np.linalg.lstsq(A, x ** 2 + y ** 2, rcond=None)
            cx, cy = float(sol[0]), float(sol[1])
            R = float(np.sqrt(sol[2] + cx * cx + cy * cy))
            res = np.hypot(y - cy, x - cx) - R
            keep = np.abs(res) < 2.5 * max(np.std(res), 0.05)
            if keep.sum() > len(res) * 0.5:
                x, y = x[keep], y[keep]
    return cx, cy, R, float(np.std(np.hypot(y - cy, x - cx) - R))


def mesura(arg):
    path, texp = arg
    P = plans(path)
    G = 0.5 * (P["G1"] + P["G2"])
    sat = (P["R"] >= SOSTRE) | (P["G1"] >= SOSTRE) | (P["G2"] >= SOSTRE) | (P["B"] >= SOSTRE)
    cx, cy, Rl, resl = limbe(G)
    yy, xx = np.mgrid[0:G.shape[0], 0:G.shape[1]].astype(np.float32)
    rr = np.hypot(yy - cy, xx - cx) / RSUN
    idx = np.digitize(rr.ravel(), EDGES) - 1
    ok = (idx >= 0) & (idx < NB)
    io = idx[ok]
    n = np.bincount(io, minlength=NB).astype(float)
    out = {"file": os.path.basename(path), "texp": texp, "centre": [cx, cy],
           "R_limbe_sp": Rl, "limbe_residu_sp": resl,
           "frac_sat_global": float(sat.mean()), "n": n.tolist(),
           "fsat": (np.bincount(io[sat.ravel()[ok]], minlength=NB) / np.maximum(n, 1)).tolist()}
    for ch, a in (("R", P["R"]), ("G", G), ("B", P["B"])):
        v = a.ravel()[ok] - PEDESTAL
        good = a.ravel()[ok] < SOSTRE
        ng = np.bincount(io[good], minlength=NB).astype(float)
        sm = np.bincount(io[good], weights=v[good], minlength=NB)
        with np.errstate(invalid="ignore", divide="ignore"):
            mean = sm / np.where(ng > 0, ng, np.nan)
        out[f"mean_{ch}"] = np.where(np.isfinite(mean), mean, np.nan).tolist()
    d = (G[:, 1:] - G[:, :-1]) / np.sqrt(2.0)
    m = (G[:, 1:] < SOSTRE) & (G[:, :-1] < SOSTRE)
    ii = np.digitize(rr[:, :-1][m].ravel(), EDGES) - 1
    dv = d[m].ravel()
    o2 = (ii >= 0) & (ii < NB)
    nd = np.bincount(ii[o2], minlength=NB).astype(float)
    s2 = np.bincount(ii[o2], weights=dv[o2] ** 2, minlength=NB)
    with np.errstate(invalid="ignore", divide="ignore"):
        sg = np.sqrt(s2 / np.where(nd > 0, nd, np.nan))
    out["sigma_hf_G"] = np.where(np.isfinite(sg), sg, np.nan).tolist()
    return out


def exif(carpeta):
    cmd = ["exiftool", "-n", "-csv", "-FileName", "-SubSecDateTimeOriginal",
           "-ExposureTime", "-ISO", "-CameraTemperature", "-SerialNumber", carpeta]
    txt = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    rows = [r for r in csv.DictReader(txt.splitlines()) if r["FileName"].upper().endswith(".CR3")]
    t = lambda r: dt.datetime.fromisoformat(r["SubSecDateTimeOriginal"].replace(":", "-", 2))
    t0 = min(t(r) for r in rows)
    for r in rows:
        r["t"] = (t(r) - t0).total_seconds()
        r["texp"] = float(r["ExposureTime"])
    return sorted(rows, key=lambda r: r["t"])


def cel_ajustat(g):
    """Nivell de cel per fotograma: constant que fa que 3,2-5 R☉ sigui una potència."""
    m = (RC > 3.2) & (RC < 5.0) & np.isfinite(g)
    if m.sum() < 8:
        return 0.0
    x, y = np.log(RC[m]), g[m]
    millor = (np.inf, 0.0)
    for c in np.linspace(0, float(np.nanmin(y)), 300):
        z = y - c
        if (z <= 0).any():
            continue
        A = np.polyfit(x, np.log(z), 1)
        r = float(np.sum((np.log(z) - np.polyval(A, x)) ** 2))
        if r < millor[0]:
            millor = (r, float(c))
    return millor[1]


# ------------------------------------------------------------------ anàlisi
def contactes(rows, mes):
    """C2 i C3 de la pròpia dada: on la fotosfera deixa i torna a saturar a 1/3200."""
    curt = min(r["texp"] for r in rows)
    c = [(r["t"], mes[r["FileName"]]["frac_sat_global"]) for r in rows if abs(r["texp"] - curt) < 1e-9]
    c.sort()
    mig = 0.5 * (c[0][0] + c[-1][0])
    pre = [x for x in c if x[0] < mig]
    post = [x for x in c if x[0] > mig]
    c2 = 0.5 * ([x[0] for x in pre if x[1] > 0][-1] + [x[0] for x in pre if x[1] == 0][0])
    c3 = 0.5 * ([x[0] for x in post if x[1] == 0][-1] + [x[0] for x in post if x[1] > 0][0])
    return c2, c3


def taula(mes, rows, c2, c3):
    """Per fotograma: geometria, saturació, rang útil i color del mosaic."""
    T = []
    for r in rows:
        m = mes[r["FileName"]]
        t = r["texp"]
        g = np.array(m["mean_G"], float)
        fs = np.array(m["fsat"], float)
        cel = cel_ajustat(g) if t >= 0.01 else 0.0
        sc = g - cel
        sig = np.sqrt(np.maximum(g, 0) / GUANY + sread(t) ** 2)
        snr = sc / sig * np.sqrt(FRAC)
        fora = RC > 1.0292
        prim = lambda y, thr: next((RC[i] for i in range(NB) if fora[i] and y[i] < thr), np.nan)
        rsat = prim(fs, 1e-3)
        r3, r1 = prim(snr, 3.0), prim(snr, 1.0)
        rg = bg = rcol = np.nan
        for r0 in RC[fora]:
            k = (RC >= r0) & (RC < r0 * 1.15) & (fs < 1e-5)
            if k.sum() >= 4 and (fs[k] < 1e-5).all():
                R_ = np.array(m["mean_R"], float)[k]
                B_ = np.array(m["mean_B"], float)[k]
                G_ = g[k]
                rg, bg, rcol = float(np.nanmean(R_ / G_)), float(np.nanmean(B_ / G_)), float(r0)
                break
        # terra per píxel: arrel de S^2 = 9*((S + cel)/guany + soroll_lectura^2)
        a = 1.0 / GUANY
        s3 = float(np.roots([1, -9 * a, -9 * (cel / GUANY + sread(t) ** 2)])[0])
        T.append(dict(fitxer=r["FileName"][:-4], t=r["t"], dt_c2=r["t"] - c2, texp=t,
                      dins=bool(c2 < r["t"] < c3), iso=r["ISO"], temp=r["CameraTemperature"],
                      centre_x=m["centre"][0] * 2, centre_y=m["centre"][1] * 2,
                      R_limbe_px=m["R_limbe_sp"] * 2, limbe_res_px=m["limbe_residu_sp"] * 2,
                      frac_sat=m["frac_sat_global"], cel_DN=cel, cel_DN_s=cel / t,
                      r_sat=rsat, r_snr3=r3, r_snr1=r1,
                      B_max=(SOSTRE - PEDESTAL) / t * BFACT, B_min=s3 / t * BFACT,
                      EV=float(np.log2((SOSTRE - PEDESTAL) / s3)),
                      RG=rg, BG=bg, r_color=rcol))
    return T


def pesos(mes, rows, c2, c3):
    """Pes inversa-variància per esglaó i anell, i el que se'n deriva."""
    G = defaultdict(list)
    for r in rows:
        if c2 < r["t"] < c3:
            G[round(r["texp"], 9)].append(mes[r["FileName"]])
    EX = sorted(G)
    W = {}
    S = {}
    for t in EX:
        w = np.zeros(NB)
        s = []
        for m in G[t]:
            g = np.array(m["mean_G"], float)
            fs = np.array(m["fsat"], float)
            cel = cel_ajustat(g) if t >= 0.01 else 0.0
            val = (fs < 1e-3) & (RC > 1.0292) & np.isfinite(g)
            w += np.where(val, t ** 2 / (np.maximum(g, 0) / GUANY + sread(t) ** 2), 0.0)
            s.append(np.where(val, g - cel, np.nan) / t)
        W[t] = w
        S[t] = np.nanmean(s, axis=0)
    return EX, W, S, {t: len(G[t]) for t in EX}


# -------------------------------------------------------------------- vistes
def vistes(T, EX, W, S, NF, c2, c3):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    fora = RC > 1.0292
    Wt = sum(W[t] for t in EX)
    dom = [EX[int(np.argmax([W[t][i] for t in EX]))] if Wt[i] > 0 else np.nan for i in range(NB)]
    per_exp = {t: [x for x in T if abs(x["texp"] - t) < 1e-9 and x["dins"]] for t in EX}

    # ---- 1. mapa: on serveix cada esglaó
    fig, ax = plt.subplots(figsize=(15, 8.5))
    for k, t in enumerate(EX):
        rs = np.nanmedian([x["r_sat"] for x in per_exp[t]])
        r3 = np.nanmedian([x["r_snr3"] for x in per_exp[t]])
        r1 = np.nanmedian([x["r_snr1"] for x in per_exp[t]])
        ax.barh(k, rs - 1.0292, left=1.0292, height=0.66, color="#c0392b", zorder=3)
        ax.barh(k, r3 - rs, left=rs, height=0.66, color="#27ae60", zorder=3)
        ax.barh(k, r1 - r3, left=r3, height=0.66, color="#f0c419", zorder=3)
        ax.barh(k, 9.0 - r1, left=r1, height=0.66, color="#d8d8d8", zorder=2)
        ax.text(1.005, k, f"{nom(t)}  ", ha="right", va="center", fontsize=10.5)
        ax.text(9.15, k, f"{NF[t]}", ha="left", va="center", fontsize=9, color="#555")
        etiq = "no satura" if rs <= 1.05 else f"{rs:.2f}"
        ax.text(rs * 1.015, k - 0.31, etiq, ha="left", va="bottom", fontsize=8.5,
                color="#1d4b2c" if rs <= 1.05 else "w", zorder=7)
    md = np.array([EX.index(d) if d in EX else np.nan for d in dom], float)
    ax.step(RC[fora], md[fora], where="mid", color="k", lw=2.4, zorder=6, label="esglaó que mana el pes")
    ax.set_xscale("log")
    ax.set_xlim(1.0, 9.6)
    ax.set_ylim(-0.9, len(EX) - 0.2)
    ax.set_yticks([])
    ax.set_xticks([1.03, 1.2, 1.5, 2, 3, 4, 5, 6, 8])
    ax.set_xticklabels(["1,03\n(limbe)", "1,2", "1,5", "2", "3", "4", "5", "6", "8"])
    ax.set_xlabel("radi solar  r / R☉   (centre = Sol; el limbe lunar és a 1,029)", fontsize=11)
    ax.set_title("Rang útil de cada exposició de la totalitat — Vixen VSD90SS + Canon R6 III\n"
                 "roig: saturat (>85 % del rang)   ·   verd: útil (SNR corona > 3)   ·   "
                 "groc: marginal (3 > SNR > 1)   ·   gris: sota el soroll", fontsize=12.5)
    ax.legend(handles=[Patch(color="#c0392b", label="saturat (>85 % del rang)"),
                       Patch(color="#27ae60", label="útil (SNR corona > 3)"),
                       Patch(color="#f0c419", label="marginal (3 > SNR > 1)"),
                       Patch(color="#d8d8d8", label="sota el soroll"),
                       plt.Line2D([], [], color="k", lw=2.4, label="esglaó que mana el pes")],
              loc="upper center", bbox_to_anchor=(0.5, -0.105), ncol=5, fontsize=10, frameon=False)
    ax.text(9.15, len(EX) - 0.45, "fotogr.", fontsize=8.5, color="#555", ha="left")
    ax.grid(axis="x", alpha=0.25, zorder=0)
    fig.tight_layout()
    fig.savefig(comu.vista("RANG_UTIL_mapa.png"), dpi=145)
    plt.close(fig)

    # ---- 2. pesos i guany
    fig, axs = plt.subplots(2, 1, figsize=(15, 9), sharex=True,
                            gridspec_kw=dict(height_ratios=[2.1, 1]))
    frac = np.array([np.where(Wt > 0, W[t] / np.maximum(Wt, 1e-30), 0) for t in EX])
    cols = plt.cm.viridis(np.linspace(0.05, 0.95, len(EX)))
    axs[0].stackplot(RC[fora], frac[:, fora], colors=cols, labels=[nom(t) for t in EX])
    for k, t in enumerate(EX):
        zona = np.where(fora & (frac[k] > 0.09) & (RC > 1.045) & (RC < 7.5))[0]
        if len(zona) == 0:
            continue
        i = int(zona[len(zona) // 2])
        axs[0].text(RC[i], float(frac[:k, i].sum() + frac[k, i] / 2), nom(t),
                    ha="center", va="center", fontsize=10, color="w", weight="bold")
    axs[0].set_ylim(0, 1)
    axs[0].set_ylabel("fracció del pes total\n(inversa de variància)", fontsize=11)
    axs[0].set_title("Quant aporta cada exposició a cada radi, i què s'hi guanya agrupant-les", fontsize=13)
    gu = np.array([np.sqrt(Wt[i] / max([W[t][i] for t in EX])) if Wt[i] > 0 else np.nan for i in range(NB)])
    ev3 = []
    for i in range(NB):
        if Wt[i] <= 0:
            ev3.append(np.nan); continue
        per = {t: W[t][i] for t in EX if W[t][i] > 0}
        tb = max(per, key=per.get)
        s = sum(w for t, w in per.items() if np.log2(tb / t) <= 3 + 1e-6)
        ev3.append(np.sqrt(s / per[tb]))
    axs[1].plot(RC[fora], gu[fora], color="#2c3e50", lw=2.5, label="agrupant tots els esglaons")
    axs[1].plot(RC[fora], np.array(ev3)[fora], color="#e67e22", lw=2.2, ls="--",
                label="agrupant només fins a 3 EV per sota del dominant")
    axs[1].axhline(1, color="k", lw=0.8, alpha=0.5)
    axs[1].set_ylim(0.98, 2.0)
    axs[1].set_ylabel("guany en senyal/soroll\ncontra el millor esglaó sol", fontsize=11)
    axs[1].set_xlabel("radi solar  r / R☉", fontsize=11)
    axs[1].legend(fontsize=10, loc="upper right")
    axs[1].text(1.035, 1.02, "les dents surten de l'escala entrellaçada: els esglaons de la mitja escala B\n"
                "només tenen 2 fotogrames i els de l'A en tenen 4, i el guany es mesura contra\n"
                "el millor esglaó SOL amb tots els seus fotogrames", fontsize=9, color="#555", va="bottom")
    axs[1].grid(alpha=0.25)
    axs[0].grid(alpha=0.2)
    axs[0].set_xscale("log")
    axs[0].set_xlim(1.029, 9.0)
    axs[0].set_xticks([1.03, 1.2, 1.5, 2, 3, 4, 5, 6, 8])
    axs[0].set_xticklabels(["1,03", "1,2", "1,5", "2", "3", "4", "5", "6", "8"])
    fig.tight_layout()
    fig.savefig(comu.vista("RANG_UTIL_pesos.png"), dpi=145)
    plt.close(fig)

    # ---- 3. l'escala al llarg de la totalitat, i el cel que va canviar
    fig, axs = plt.subplots(2, 1, figsize=(15, 8), sharex=True,
                            gridspec_kw=dict(height_ratios=[1.6, 1]))
    for x in T:
        c = "#27ae60" if x["dins"] else "#aab0b7"
        axs[0].plot(x["dt_c2"], x["texp"], "o", ms=6.5, color=c, zorder=3)
    for k in (c2, c3):
        for a in axs:
            a.axvline(k - c2, color="#c0392b", lw=1.6, ls="--", zorder=2)
    axs[0].text(0, 13, " C2", color="#c0392b", fontsize=11, va="top")
    axs[0].text(c3 - c2, 13, " C3", color="#c0392b", fontsize=11, va="top")
    axs[0].set_yscale("log")
    axs[0].set_ylabel("temps d'exposició (s)", fontsize=11)
    axs[0].set_yticks([1 / 3200, 1 / 500, 1 / 60, 1 / 8, 1, 10])
    axs[0].set_yticklabels(["1/3200", "1/500", "1/60", "1/8", "1 s", "10 s"])
    axs[0].set_title("Les 124 captures de la finestra, i el cel que va canviar per sota\n"
                     f"verd: dins la totalitat ({sum(x['dins'] for x in T)} imatges)  ·  gris: fora", fontsize=13)
    axs[0].grid(alpha=0.25)
    d = [x for x in T if x["cel_DN_s"] > 0 and x["dins"]]
    axs[1].plot([x["dt_c2"] for x in d], [x["cel_DN_s"] for x in d], "o-", color="#2980b9", ms=6)
    axs[1].set_ylabel("cel de fons mesurat\n(DN/s, píxel verd)", fontsize=11)
    axs[1].set_xlabel("segons des de C2", fontsize=11)
    axs[1].grid(alpha=0.25)
    v = [x["cel_DN_s"] for x in d]
    axs[1].text(0.99, 0.06, f"recorregut {100*(max(v)-min(v))/np.mean(v):.0f} % en 85 s — "
                "és la mateixa V que research/76 va mesurar per una altra via",
                transform=axs[1].transAxes, ha="right", fontsize=10, color="#2980b9")
    fig.tight_layout()
    fig.savefig(comu.vista("RANG_UTIL_escala_i_cel.png"), dpi=145)
    plt.close(fig)


# ---------------------------------------------------------------------- main
def main():
    carp = carpeta_totalitat()
    rows = exif(carp)
    cau = os.path.join(comu.F0, "rang_util_mesures.json")
    os.makedirs(comu.F0, exist_ok=True)
    if os.path.exists(cau) and "--refes" not in sys.argv:
        mes = json.load(open(cau))
    else:
        jobs = [(os.path.join(carp, r["FileName"]), r["texp"]) for r in rows]
        with ProcessPoolExecutor(min(10, os.cpu_count() or 4)) as ex:
            mes = {m["file"]: m for m in ex.map(mesura, jobs)}
        json.dump(mes, open(cau, "w"))
    print(f"{len(rows)} CR3 de {carp}")

    c2, c3 = contactes(rows, mes)
    print(f"C2 = t {c2:.2f} s · C3 = t {c3:.2f} s · totalitat {c3-c2:.1f} s (de la pròpia dada)")
    T = taula(mes, rows, c2, c3)
    EX, W, S, NF = pesos(mes, rows, c2, c3)

    buits = ("r_sat", "r_snr3", "r_snr1", "B_min", "EV", "RG", "BG", "r_color")
    for x in T:            # fora de la totalitat hi ha fotosfera: aquestes columnes no volen dir res
        if not x["dins"]:
            for k in buits:
                x[k] = ""
    cols = ["fitxer", "t", "dt_c2", "texp", "dins", "iso", "temp", "centre_x", "centre_y",
            "R_limbe_px", "limbe_res_px", "frac_sat", "cel_DN", "cel_DN_s", "r_sat",
            "r_snr3", "r_snr1", "B_max", "B_min", "EV", "RG", "BG", "r_color"]
    with open(comu.lliurable("rang_util_imatges.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, cols)
        w.writeheader()
        for x in T:
            w.writerow({k: (f"{v:.6g}" if isinstance(v, float) else v) for k, v in x.items()})
    vistes(T, EX, W, S, NF, c2, c3)

    lim = [x["R_limbe_px"] for x in T if x["limbe_res_px"] < 2.4 and x["texp"] <= 0.5]
    print(f"limbe lunar: {np.median(lim):.2f} px = {np.median(lim)/RSUN_PX:.4f} R☉ "
          f"(sd {np.std(lim):.2f} px, {len(lim)} fotogrames)")
    print(f"dins la totalitat: {sum(x['dins'] for x in T)} imatges, {len(EX)} exposicions")
    print("vistes i CSV a", comu.OUT_CANON)
    return T, EX, W, S, NF, c2, c3


if __name__ == "__main__":
    main()
