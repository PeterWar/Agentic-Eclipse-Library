"""V21, pas 3: els dos apilats nous al llenç de la V19 (geometria V16).

A) APILAT REGISTRAT A LES ESTRELLES (base DSC06993, el 8 s amb la Lluna
   centrada): canvas → raw_base (àncora solar de la base) → raw_n per la
   cadena d'ajustos d'estrelles  raw_n = R(−θ_n)·(raw_base − sol_base − t_n)
   + sol_n. La Lluna de cada fotograma, exclosa (es mou). D'aquí surt la
   CAPA D'ESTRELLES (excés sobre el fons local, dins discos, additiva).

B) APILAT REGISTRAT A LA LLUNA: raw_n = R(−θ_n)·(raw_base − M_base) + M_n
   amb M = centre lunar mesurat per fotograma (la rotació de camp del salt
   d'apuntament també gira el disc: es compensa amb la mateixa θ). Només el
   disc (guarda dins del limbe). D'aquí surt la CAPA D'EARTHSHINE.

Render: el mateix sistema tonal que la capa Sony de la V19 (WB i àncora del
rebut de la V17). Alineació verificada contra la capa 12 de la V19.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
CAU17 = os.path.join(AQUI, "cau_v17")
CAU19 = os.path.join(AQUI, "cau_v19")
sys.path.insert(0, AQUI)
import fes_v15 as F15
import fes_v17 as F17

BASE = "DSC06993.ARW"
FRAMES = ["DSC06984.ARW", "DSC06996.ARW", "DSC06999.ARW",
          "DSC06987.ARW", "DSC06993.ARW"]
RS = 455.5
GUARDA_LIMBE_PX = 6.0     # px RAW per dins del limbe (fora corona/protub.)
VORA_DISC_PX = 6.0
T0 = time.time()


def marca(txt):
    print(f"[{time.time()-T0:7.1f}s] {txt}", flush=True)


def carrega_fits():
    ff = json.load(open(os.path.join(CAU, "fits_finestres.json")))["fits"]
    f87 = json.load(open(os.path.join(CAU, "fit_06987_final.json")))
    fits = {BASE: (0.0, np.zeros(2))}
    fits["DSC06996.ARW"] = (math.radians(ff["DSC06996.ARW"]["theta_deg"]),
                            np.array(ff["DSC06996.ARW"]["t_px"]))
    fits["DSC06999.ARW"] = (math.radians(ff["DSC06999.ARW"]["theta_deg"]),
                            np.array(ff["DSC06999.ARW"]["t_px"]))
    th2 = math.radians(f87["theta_deg"])
    t2 = np.array(f87["t_px"])
    fits["DSC06987.ARW"] = (th2, t2)
    th1 = math.radians(ff["DSC06984.ARW"]["theta_deg"])
    t1 = np.array(ff["DSC06984.ARW"]["t_px"])
    ca, sa = math.cos(th2), math.sin(th2)
    tc = np.array([ca * t1[0] - sa * t1[1], sa * t1[0] + ca * t1[1]]) + t2
    fits["DSC06984.ARW"] = (th1 + th2, tc)
    return fits


def compon(sv, geo15, comu, f2, ctx, S13, K, fits, mode,
           y0y1=None, correccio=(0.0, 0.0), banda=1024):
    """Compost LDIC al llenç V16 amb àncora per estrelles o per Lluna."""
    W, H = sv.W16, sv.H16
    ya, yb = (0, H) if y0y1 is None else y0y1
    num = {c: np.zeros((yb - ya, W), np.float32) for c in comu.CANALS}
    den = {c: np.zeros((yb - ya, W), np.float32) for c in comu.CANALS}
    vb = S13[BASE]
    solb = np.array([vb["sol_x"] + correccio[0], vb["sol_y"] + correccio[1]])
    Mb = np.array([vb["sol_x"] + vb["lluna_dx"] + correccio[0],
                   vb["sol_y"] + vb["lluna_dy"] + correccio[1]])
    for n in FRAMES:
        v = S13[n]
        soln = np.array([v["sol_x"], v["sol_y"]])
        Mn = np.array([v["sol_x"] + v["lluna_dx"], v["sol_y"] + v["lluna_dy"]])
        th, t = fits[n]
        ca, sa = math.cos(th), math.sin(th)
        k = K.get(n, 1.0)
        plans = ctx.plans(n, v["exp"])
        for y0 in range(ya, yb, banda):
            y1 = min(yb, y0 + banda)
            Xv, Yv = np.meshgrid(np.arange(W, dtype=np.float32),
                                 np.arange(y0, y1, dtype=np.float32))
            x15, y15 = sv.enrere(Xv, Yv)
            del Xv, Yv
            dX, dY = geo15.v15_a_comu(x15, y15)
            del x15, y15
            rbx, rby = geo15.comu_a_raw_sony(dX, dY, solb)
            del dX, dY
            if mode == "estrelles":
                ux = rbx - solb[0] - t[0]
                uy = rby - solb[1] - t[1]
                rx = ca * ux + sa * uy + soln[0]
                ry = -sa * ux + ca * uy + soln[1]
            else:                     # lluna
                ux = rbx - Mb[0]
                uy = rby - Mb[1]
                rx = ca * ux + sa * uy + Mn[0]
                ry = -sa * ux + ca * uy + Mn[1]
            del rbx, rby, ux, uy
            dl = np.hypot(rx - Mn[0], ry - Mn[1])
            if mode == "estrelles":
                fll = np.clip((dl - (ctx.RL + f2.GUARDA_LLUNA_PX))
                              / f2.VORA_LLUNA_PX, 0.0, 1.0).astype(np.float32)
            else:
                fll = np.clip(((ctx.RL - GUARDA_LIMBE_PX) - dl)
                              / VORA_DISC_PX, 0.0, 1.0).astype(np.float32)
            del dl
            for i, (pl, w) in plans.items():
                oy, ox = ctx.orig[i]
                mx = ((rx - ox) * 0.5).astype(np.float32)
                my = ((ry - oy) * 0.5).astype(np.float32)
                c = comu.CANALS[comu.IDX_CANAL[i]]
                num[c][y0 - ya:y1 - ya] += cv2.remap(
                    pl * w * k, mx, my, cv2.INTER_LINEAR, borderValue=0.0) * fll
                den[c][y0 - ya:y1 - ya] += cv2.remap(
                    w, mx, my, cv2.INTER_LINEAR, borderValue=0.0) * fll
                del mx, my
            del rx, ry, fll
        marca(f"  {n} ({v['exp']:g} s) compost [{mode}]")
    C = {c: np.where(den[c] > 0, num[c] / np.maximum(den[c], 1e-20),
                     np.nan).astype(np.float32) for c in comu.CANALS}
    del num
    return C, den


def renderitza(C, den, comu, run, reb17):
    tres = np.ones(C["G"].shape, bool)
    for c in comu.CANALS:
        tres &= (den[c] > 0) & np.isfinite(C[c])
    g = reb17["wb_guanys_lineals_RGB"]
    va = reb17["valor_ancora_final"]
    Cg = {c: C[c] * g[j] for j, c in enumerate(comu.CANALS)}
    rgb, ren = comu.render_visual(np.dstack([Cg[c] for c in comu.CANALS]),
                                  tres, va, run.matriu, run.color["guany"])
    return np.clip(rgb, 0.0, 1.0), tres


def main():
    os.makedirs(CAU, exist_ok=True)
    sv = F17.SV16()
    geo15 = F15.Geo(padx=3387.0, pady=5109.0)
    comu, f2, run, ctx, S13, K, va = F15.carrega_sony()
    reb17 = json.load(open(os.path.join(CAU17, "rebut_v17.json")))
    if "valor_ancora_final" not in reb17:
        reb17["valor_ancora_final"] = va * reb17["ancora_factor"]
    fits = carrega_fits()
    for n in FRAMES:
        th, t = fits[n]
        print(f"  {n}: θ={math.degrees(th)*60:+.2f}′ t=({t[0]:+.2f},{t[1]:+.2f})")
    W, H = sv.W16, sv.H16

    # ---------- A) apilat registrat a les estrelles ----------
    marca("[A] apilat registrat a les ESTRELLES")
    C, den = compon(sv, geo15, comu, f2, ctx, S13, K, fits, "estrelles")

    # alineació contra la capa Sony de la V19 (passa-alt del log G, anell on
    # tots dos tenen dada; la capa 12 està registrada al SOL de cada fotograma
    # i el nostre apilat al SOL DE LA BASE: l'estructura de corona coincideix)
    S12 = np.load(os.path.join(CAU19, "sony_v18_rgb16.npy"), mmap_mode="r")
    sol16 = sv.endavant(7410.63, 7844.42)
    g12 = np.asarray(S12[..., 1], np.float32) / 65535.0
    gl = np.where(np.isfinite(C["G"]) & (C["G"] > 0),
                  np.log10(np.maximum(np.nan_to_num(C["G"]), 1e-9)), 0.0
                  ).astype(np.float32)
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    rad = np.hypot(xx - sol16[0], yy - sol16[1])
    zona = ((rad > 2.2 * RS) & (rad < 3.2 * RS) & (g12 > 0.02) & (gl != 0)
            ).astype(np.float32)
    a = (g12 - cv2.GaussianBlur(g12, (0, 0), 12)) * zona
    b = (gl - cv2.GaussianBlur(gl, (0, 0), 12)) * zona
    m_ = int(3.2 * RS) + 40
    x0 = max(0, int(sol16[0]) - m_); x1 = min(W, int(sol16[0]) + m_)
    y0 = max(0, int(sol16[1]) - m_); y1 = min(H, int(sol16[1]) + m_)
    (dx, dy), resp = cv2.phaseCorrelate(a[y0:y1, x0:x1].astype(np.float64),
                                        b[y0:y1, x0:x1].astype(np.float64))
    print(f"    alineació vs capa 12: ({dx:+.2f}, {dy:+.2f}) px · resp {resp:.3f}")
    del a, b, gl
    if resp >= 0.03 and 0.35 < math.hypot(dx, dy) < 12.0:
        vx = sv.ca * dx - sv.sa * dy
        vy = sv.sa * dx + sv.ca * dy
        ddX = geo15.cav * vx - geo15.sav * vy
        ddY = geo15.sav * vx + geo15.cav * vy
        rx = geo15.cas * (ddX * geo15.ks) + geo15.sas * (ddY * geo15.ks)
        ry = -geo15.sas * (ddX * geo15.ks) + geo15.cas * (ddY * geo15.ks)
        print(f"    correcció al RAW: ({rx:+.2f}, {ry:+.2f}) — es recompon")
        C, den = compon(sv, geo15, comu, f2, ctx, S13, K, fits, "estrelles",
                        correccio=(rx, ry))
        gl = np.where(np.isfinite(C["G"]) & (C["G"] > 0),
                      np.log10(np.maximum(np.nan_to_num(C["G"]), 1e-9)), 0.0
                      ).astype(np.float32)
        b = (gl - cv2.GaussianBlur(gl, (0, 0), 12)) * zona
        a = (g12 - cv2.GaussianBlur(g12, (0, 0), 12)) * zona
        (dx2, dy2), resp2 = cv2.phaseCorrelate(a[y0:y1, x0:x1].astype(np.float64),
                                               b[y0:y1, x0:x1].astype(np.float64))
        print(f"    residual: ({dx2:+.2f}, {dy2:+.2f}) px · resp {resp2:.3f}")
        del a, b, gl
    del g12, zona
    rgbE, tresE = renderitza(C, den, comu, run, reb17)
    np.save(os.path.join(CAU, "apilat_estrelles_rgb.npy"),
            np.clip(np.rint(rgbE * 65535), 0, 65535).astype(np.uint16))
    np.save(os.path.join(CAU, "apilat_estrelles_tres.npy"), tresE)
    del C, den
    marca("[A] apilat d'estrelles renderitzat i desat")

    # ---------- B) apilat registrat a la LLUNA (només el disc) ----------
    marca("[B] apilat registrat a la LLUNA (earthshine)")
    vb = S13[BASE]
    Mb_raw = (vb["sol_x"] + vb["lluna_dx"], vb["sol_y"] + vb["lluna_dy"])
    xv15, yv15 = geo15.raw_sony_a_v15(np.array([Mb_raw[0]]),
                                      np.array([Mb_raw[1]]),
                                      (vb["sol_x"], vb["sol_y"]))
    mx16, my16 = sv.endavant(float(xv15[0]), float(yv15[0]))
    print(f"    Lluna de la base al llenç: ({mx16:.1f}, {my16:.1f})")
    Rl_canvas = ctx.RL / geo15.ks
    marge = int(Rl_canvas + 60)
    ya = max(0, int(my16) - marge); yb_ = min(H, int(my16) + marge)
    C2, den2 = compon(sv, geo15, comu, f2, ctx, S13, K, fits, "lluna",
                      y0y1=(ya, yb_))
    rgbL, tresL = renderitza(C2, den2, comu, run, reb17)
    np.save(os.path.join(CAU, "apilat_lluna_rgb.npy"),
            np.clip(np.rint(rgbL * 65535), 0, 65535).astype(np.uint16))
    np.save(os.path.join(CAU, "apilat_lluna_tres.npy"), tresL)
    json.dump({"fits_deg_t": {n: [math.degrees(fits[n][0]),
                                  list(map(float, fits[n][1]))] for n in FRAMES},
               "lluna_base_canvas": [float(mx16), float(my16)],
               "rl_canvas": float(Rl_canvas), "banda_lluna": [int(ya), int(yb_)],
               "sol16": [float(sol16[0]), float(sol16[1])]},
              open(os.path.join(CAU, "apilats_meta.json"), "w"), indent=1)
    del C2, den2
    marca("[B] apilat de la Lluna renderitzat i desat")

    # estadística ràpida del disc (earthshine)
    hL = rgbL.shape[0]
    yyL = np.arange(hL, dtype=np.float32)[:, None] + ya
    xxL = np.arange(W, dtype=np.float32)[None, :]
    dl = np.hypot(xxL - mx16, yyL - my16)
    disc = (dl < Rl_canvas - 20) & tresL
    if disc.sum() > 1000:
        print("    earthshine (disc, mediana RGB):",
              [round(float(np.median(rgbL[..., j][disc])), 4) for j in range(3)],
              f"· px {int(disc.sum())}")
    marca("fet")


if __name__ == "__main__":
    main()
