"""V21 · earthshine dels DOS TRENS: apilat lineal registrat a la LLUNA.

Ús:  v21_lluna_tren.py sony|vixen

Cada tren es compon en un procés propi (els dos runs porten mòduls `comu`
i `f2` amb el mateix nom). Tots dos aterren al MATEIX marc lunar: l'origen
és el centre de la Lluna al llenç V16 (6465,40 · 6752,63), que és on cau la
Lluna del fotograma base de la Sony (DSC06993) al muntatge de Pere.

Geometria, per tren:
  · SONY  canvas → v15 → comu → raw Sony (àncora solar de la base) →
          desplaçament respecte de la Lluna de la base → R(−θ_n) →
          + Lluna del fotograma n.   [θ_n = rotació de camp del salt]
  · VIXEN canvas → v15 → coordenades del sensor Vixen (el llenç hi és 1:1 i
          amb la seva orientació: escala 2,1495″/px als dos) → desplaçament
          respecte de la Lluna base → + Lluna del fotograma n.

⛔ Res del disc no es fabrica: el que se'n treu és la mitjana ponderada LDIC
   dels RAW, amb els pesos de saturació/validesa de cada fotograma.
"""
from __future__ import annotations

import json, math, os, sys, time

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
import fes_v15 as F15
import fes_v17 as F17

# el marc lunar comú (V16)
MB_CANVAS = (6465.398680355321, 6752.632845814709)
RL_CANVAS = 455.5018189723177
GUARDA_PX = 8.0        # canvas px per dins del limbe (fora corona/protub.)
VORA_PX = 6.0
MARGE = 40
T0 = time.time()


def marca(t):
    print(f"[{time.time()-T0:7.1f}s] {t}", flush=True)


def main(tren, subconjunt=None, sufix=""):
    sv = F17.SV16()
    geo15 = F15.Geo(padx=3387.0, pady=5109.0)
    RUN = F15.RUN_SONY if tren == "sony" else F15.RUN_VIXEN
    sys.path.insert(0, os.path.join(RUN, "codi"))
    import comu, f2
    run = comu.Run.obre(RUN)
    ctx = f2.Ctx(run)
    S13 = run.llegeix_rebut("F1.3_registre.json")["fotogrames"]
    K = run.llegeix_rebut("F2.2_coherencia.json")["k"]
    print(f"tren {tren}: k(llenç→sensor)={ctx.k:.4f} · RL sensor={ctx.RL:.2f} px "
          f"· pa_north={ctx.LL['pa_north_deg']:.3f}°", flush=True)

    if tren == "sony":
        from v21_apilats import carrega_fits, FRAMES, BASE
        noms = [n for n in FRAMES if subconjunt is None or n.split(".")[0] in subconjunt]
        fits = carrega_fits()
        vb = S13[BASE]
        solb = np.array([vb["sol_x"], vb["sol_y"]])
        Mb = np.array([vb["sol_x"] + vb["lluna_dx"],
                       vb["sol_y"] + vb["lluna_dy"]])
    else:
        # per defecte els >9 s; amb subconjunt explícit, el que demanin
        if subconjunt is None:
            noms = sorted(n for n, v in S13.items() if float(v["exp"]) > 9.0)
        else:
            noms = sorted(n for n in S13 if n.split(".")[0] in subconjunt)
        fits = {n: (0.0, np.zeros(2)) for n in noms}
    print(f"fotogrames: {noms}", flush=True)
    print("  " + " · ".join(f"{n} {float(S13[n]['exp']):g}s t={S13[n].get('t',0):.1f}"
                            for n in noms), flush=True)

    # finestra de treball al llenç
    x0 = int(MB_CANVAS[0] - RL_CANVAS - MARGE); x1 = int(MB_CANVAS[0] + RL_CANVAS + MARGE)
    y0 = int(MB_CANVAS[1] - RL_CANVAS - MARGE); y1 = int(MB_CANVAS[1] + RL_CANVAS + MARGE)
    Wc, Hc = x1 - x0, y1 - y0
    Xv, Yv = np.meshgrid(np.arange(x0, x1, dtype=np.float32),
                         np.arange(y0, y1, dtype=np.float32))
    x15, y15 = sv.enrere(Xv, Yv)
    del Xv, Yv
    # el punt del llenç, expressat com a desplaçament respecte de la Lluna base
    m15 = sv.enrere(np.float32(MB_CANVAS[0]), np.float32(MB_CANVAS[1]))
    if tren == "sony":
        dX, dY = geo15.v15_a_comu(x15, y15)
        rbx, rby = geo15.comu_a_raw_sony(dX, dY, solb)
        del dX, dY
        ux, uy = rbx - Mb[0], rby - Mb[1]
        del rbx, rby
    else:
        # el llenç V15 JA és el sensor Vixen (1:1, mateixa orientació)
        pvx = x15 - geo15.padx - F15.SENSOR_A_V13[0]
        pvy = y15 - geo15.pady - F15.SENSOR_A_V13[1]
        mbx = m15[0] - geo15.padx - F15.SENSOR_A_V13[0]
        mby = m15[1] - geo15.pady - F15.SENSOR_A_V13[1]
        ux, uy = pvx - mbx, pvy - mby
        del pvx, pvy
    del x15, y15

    num = {c: np.zeros((Hc, Wc), np.float32) for c in comu.CANALS}
    den = {c: np.zeros((Hc, Wc), np.float32) for c in comu.CANALS}
    nfr = np.zeros((Hc, Wc), np.float32)
    for n in noms:
        v = S13[n]
        Mn = np.array([v["sol_x"] + v["lluna_dx"], v["sol_y"] + v["lluna_dy"]])
        th, _ = fits[n]
        ca, sa = math.cos(th), math.sin(th)
        rx = (ca * ux + sa * uy + Mn[0]).astype(np.float32)
        ry = (-sa * ux + ca * uy + Mn[1]).astype(np.float32)
        dl = np.hypot(rx - Mn[0], ry - Mn[1])
        # guarda EN PÍXELS DEL SENSOR d'aquest tren
        fll = np.clip(((ctx.RL - GUARDA_PX * ctx.k) - dl) / (VORA_PX * ctx.k),
                      0.0, 1.0).astype(np.float32)
        del dl
        k = K.get(n, 1.0)
        plans = ctx.plans(n, v["exp"])
        for i, (pl, w) in plans.items():
            oy, ox = ctx.orig[i]
            mx = ((rx - ox) * 0.5).astype(np.float32)
            my = ((ry - oy) * 0.5).astype(np.float32)
            c = comu.CANALS[comu.IDX_CANAL[i]]
            num[c] += cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR,
                                borderValue=0.0) * fll
            den[c] += cv2.remap(w, mx, my, cv2.INTER_LINEAR,
                                borderValue=0.0) * fll
            del mx, my
        nfr += (fll > 0).astype(np.float32)
        del rx, ry, fll
        marca(f"  {n} ({v['exp']:g} s) compost")
    C = np.dstack([np.where(den[c] > 0, num[c] / np.maximum(den[c], 1e-20), np.nan)
                   for c in comu.CANALS]).astype(np.float32)
    tres = np.all(np.isfinite(C), axis=2) & (nfr >= len(noms) - 0.5)
    np.save(os.path.join(CAU, f"lluna_{tren}{sufix}_lineal.npy"), C)
    np.save(os.path.join(CAU, f"lluna_{tren}{sufix}_tres.npy"), tres)
    md = np.median(C[tres], axis=0) if tres.any() else [np.nan] * 3
    json.dump({"tren": tren, "fotogrames": noms,
               "exp": {n: float(S13[n]["exp"]) for n in noms},
               "t": {n: float(S13[n].get("t", 0)) for n in noms},
               "lluna_per_fotograma": {n: [S13[n]["sol_x"] + S13[n]["lluna_dx"],
                                           S13[n]["sol_y"] + S13[n]["lluna_dy"]]
                                       for n in noms},
               "bbox_canvas": [x0, y0, x1, y1], "k_llenc_sensor": float(ctx.k),
               "RL_sensor": float(ctx.RL), "canals": list(comu.CANALS),
               "mediana_lineal_RGB": [float(z) for z in md],
               "px_tres": int(tres.sum()),
               "integracio_s": float(sum(float(S13[n]["exp"]) for n in noms))},
              open(os.path.join(CAU, f"lluna_{tren}{sufix}_meta.json"), "w"),
              indent=1, ensure_ascii=False)
    print(f"\n{tren}: {C.shape} · px complets {int(tres.sum())} · "
          f"mediana lineal RGB {md} · integració "
          f"{sum(float(S13[n]['exp']) for n in noms):g} s", flush=True)


if __name__ == "__main__":
    sub = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    main(sys.argv[1], sub, sys.argv[3] if len(sys.argv) > 3 else "")
