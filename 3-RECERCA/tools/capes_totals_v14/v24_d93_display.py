"""V24d · el DSC06993 sencer al marc de la tessel·la V24, per a DISPLAY.

La composició LDIC exclou (amb raó) els píxels per damunt del sostre de
validesa: al limbe el glow de corona del 8 s hi és saturat, i per això cap
tessel·la científica porta el trànsit disc→corona. Per al DISPLAY el trànsit
és exactament el que es vol (és el que el PSB de Pere ensenya): aquí es
compon el fotograma SENCER — calibratge complet (dark, flat, WB, matriu de
canal), pes = només la zona activa del sensor — i els valors saturats queden
com el que són, llum cremada.

Un sol re-mostreig: raw → tessel·la V24 (991×991) via la cadena exacta
(invers del re-ancoratge ×0,9956 + llenç→raw de la base, θ=0).

Sortides: d93_disp_lineal.npy (991,991,3) · d93_contorn.json (limbe per
azimut, centre ajustat, amplada del trànsit).
"""
from __future__ import annotations
import json, math, os, sys, time

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
import fes_v15 as F15
from v24_d93_geometria import coords_raw, CXN, CYN

T0 = time.time()
NA = 720


def marca(t):
    print(f"[{time.time()-T0:7.1f}s] {t}", flush=True)


def compon():
    import rawpy
    sys.path.insert(0, os.path.join(F15.RUN_SONY, "codi"))
    import comu, f2
    run = comu.Run.obre(F15.RUN_SONY)
    ctx = f2.Ctx(run)
    rbx, rby = coords_raw()
    marca("cadena feta; component el fotograma sencer…")
    num = {c: np.zeros((991, 991), np.float32) for c in comu.CANALS}
    den = {c: np.zeros((991, 991), np.float32) for c in comu.CANALS}
    with rawpy.imread(ctx.ruta["DSC06993.ARW"]) as r:
        raw = r.raw_image.astype(np.float32)
    dk = ctx.dark(8.0)
    for i in range(4):
        oy, ox = ctx.orig[i]
        pl = comu.calibra_pla(raw[oy::2, ox::2], dk[oy::2, ox::2],
                              ctx.flat[oy::2, ox::2], 8.0, ctx.wb, ctx.mc, i)
        w = ctx.valid[oy::2, ox::2]          # NOMÉS la zona activa: display
        mx = ((rbx - ox) * 0.5).astype(np.float32)
        my = ((rby - oy) * 0.5).astype(np.float32)
        c = comu.CANALS[comu.IDX_CANAL[i]]
        num[c] += cv2.remap(pl * w, mx, my, cv2.INTER_LINEAR, borderValue=0)
        den[c] += cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderValue=0)
    C = np.dstack([np.where(den[c] > 0, num[c] / np.maximum(den[c], 1e-20),
                            np.nan) for c in comu.CANALS]).astype(np.float32)
    np.save(f"{CAU}/d93_disp_lineal.npy", C)
    marca(f"compost: mediana G {np.nanmedian(C[..., 1]):.1f}")
    return C


def perfil_limbe(G, cx, cy, r0=430.0, r1=478.0, na=NA):
    th = (np.arange(na) + 0.5) / na * 2 * np.pi - np.pi
    rs = np.arange(r0, r1, 0.25, dtype=np.float32)
    xs = (cx + rs[None, :] * np.cos(th)[:, None]).astype(np.float32)
    ys = (cy + rs[None, :] * np.sin(th)[:, None]).astype(np.float32)
    V = cv2.remap(G, xs, ys, cv2.INTER_LINEAR, borderValue=np.nan)
    K = np.array([1, 4, 6, 4, 1], np.float32); K /= K.sum()
    Vs = np.apply_along_axis(lambda v: np.convolve(v, K, "same"), 1, V)
    dV = np.gradient(Vs, 0.25, axis=1)
    rho = np.full(na, np.nan); wid = np.full(na, np.nan)
    for i in range(na):
        d = dV[i]
        if not np.any(np.isfinite(d)):
            continue
        j = int(np.nanargmax(d))
        if 1 <= j < len(rs) - 1 and np.isfinite(d[j - 1]) and np.isfinite(d[j + 1]):
            dd = d[j - 1] - 2 * d[j] + d[j + 1]
            off = 0.5 * (d[j - 1] - d[j + 1]) / dd if abs(dd) > 1e-12 else 0.0
            rho[i] = rs[j] + np.clip(off, -1, 1) * 0.25
        else:
            rho[i] = rs[j]
        j0, j1 = max(0, j - 40), min(len(rs), j + 40)
        seg = Vs[i, j0:j1]
        if np.all(np.isfinite(seg)):
            lo = np.nanpercentile(seg[: max(1, j - j0)], 10)
            hi = np.nanpercentile(seg[j - j0:], 90)
            if hi > lo:
                t20, t80 = lo + 0.2 * (hi - lo), lo + 0.8 * (hi - lo)
                i20 = int(np.argmax(seg >= t20)); i80 = int(np.argmax(seg >= t80))
                if i80 > i20:
                    wid[i] = (i80 - i20) * 0.25
    return th, rho, wid


def main():
    C = compon()
    G = np.nan_to_num(C[..., 1])
    cx, cy = CXN, CYN
    for _ in range(4):
        th, rho, wid = perfil_limbe(G, cx, cy)
        m = np.isfinite(rho)
        A = np.c_[np.cos(th[m]), np.sin(th[m]), np.ones(int(m.sum()))]
        dx, dy, R = np.linalg.lstsq(A, rho[m], rcond=None)[0]
        cx += dx; cy += dy
    th, rho, wid = perfil_limbe(G, cx, cy)
    m = np.isfinite(rho)
    A = np.c_[np.cos(th[m]), np.sin(th[m]), np.ones(int(m.sum()))]
    dx, dy, R = np.linalg.lstsq(A, rho[m], rcond=None)[0]
    res = rho[m] - (R + dx * np.cos(th[m]) + dy * np.sin(th[m]))
    marca(f"limbe D93 display: centre ({cx+dx:.3f},{cy+dy:.3f}) R={R:.3f} · "
          f"rms forma {res.std():.3f} px · amplada trànsit mediana "
          f"{np.nanmedian(wid):.2f} px")
    json.dump({"cx": float(cx + dx), "cy": float(cy + dy), "R": float(R),
               "rms_forma_px": float(res.std()),
               "amplada_transit_mediana_px": float(np.nanmedian(wid)),
               "na": NA}, open(f"{CAU}/d93_contorn.json", "w"), indent=1)
    np.save(f"{CAU}/d93_rho.npy", rho)
    np.save(f"{CAU}/d93_wid.npy", wid)
    np.save(f"{CAU}/d93_th.npy", th)


if __name__ == "__main__":
    main()
