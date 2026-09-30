"""Les portes de la V14. Mesura, no impressió.

⛔ Cap d'aquestes portes no es pot passar pintant: totes surten de la dada del
run i de les màscares del fitxer que s'acaba d'escriure.

- **A · el transformat.** El limbe lunar mesurat a cada capa de la V13,
  portat al llenç comú, contra on la cadena diu que és la Lluna d'aquell
  fotograma. Llindar: 3 px.
- **B · cap màscara demana el que no hi ha.** Per a cada capa, píxels amb
  màscara > 0,01 on la capa no té dada. Llindar: 0.
- **C · el disc lunar és net.** Nivell mostrat dins de la intersecció dels
  discos lunars al compost. La V13 hi té 0,137 i la V13_Pere 0,024.
- **D · el perfil és monòton.** La V13 no ho és: puja del limbe (0,518) fins a
  un màxim a **2,0 R☉** (0,731) — és el vel de la capa de 10,3 s. Es mesura on
  cau el màxim del perfil i si baixa d'allà cap enfora.
  ⛔ La monotonia es demana **des d'1,07 R☉**, i el número no és triat: per
  sota, la cobertura és PARCIAL (46-99 % entre 1,013 i 1,05 R☉, mesurat al
  `research/112`) i la vora suau de la màscara cau sobre negre. Aquell tram és
  la vora de la dada, no corona.
- **F · la Lluna és RODONA.** Es camina cada raig des del centre declarat i es
  mira on deixa de ser negre: `r(θ)`. Un cercle té dispersió zero. ⛔ La
  primera V14 no ho era —la silueta era la intersecció dels discos, amb corona
  sobresortint per un costat i **23 px de mossegada** per l'altre—, i és el que
  Pere va veure. Llindar: **±3 px** de desviació màxima (la vora suau en val 2).
- **E · cap halo a les vores interiors.** A cada radi on una capa deixa d'estar
  saturada, el perfil del compost no hi pot fer cap bony.
  ⏭️ El llistó **no és inventat aquí**: `research/100` va mesurar que els
  esglaons veïns d'aquesta escala discrepen **1,1-1,3 %** amb el signe alternat
  (dues mitges escales de 2 EV que són dos instants diferents, amb la
  transparència caient un 8 % durant la totalitat). Aquell és el terra físic de
  QUALSEVOL muntatge per capes d'aquesta escala —el compost LDIC de la cadena
  se n'escapa perquè no té fronteres— i la porta demana que el muntatge **no
  l'amplifiqui**: l'ondulació ha de quedar per sota de l'1,1 %.
  ⛔ Es mesura el residu contra la **interpolació dels veïns** (±6 calaixos en
  log r), se'n treu la **tendència** amb una mediana mòbil de 25 calaixos i el
  que queda es normalitza amb la seva pròpia dispersió. Els dos passos són
  necessaris: una segona derivada amb σ global dona z de milers al tram
  interior, que és un penya-segat; i sense treure la tendència, la curvatura
  natural del perfil —convex en log r— ja dona z de 6 sense que hi hagi cap
  bony.
"""

from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import geo_v13


def perfil(v, rad, RS, m, nb=260, r0=1.0, r1=9.0):
    """Mediana per calaix de log r."""
    lr = np.log10(np.clip(rad / RS, 1e-6, None))
    lo, hi = math.log10(r0), math.log10(r1)
    idx = np.clip(((lr - lo) / (hi - lo) * nb).astype(np.int32), -1, nb)
    ok = m & (idx >= 0) & (idx < nb) & np.isfinite(v)
    out = np.full(nb, np.nan)
    ii = idx[ok]; vv = v[ok]
    o = np.argsort(ii, kind="stable"); ii, vv = ii[o], vv[o]
    n = np.bincount(ii, None, nb); off = np.concatenate([[0], np.cumsum(n)])
    for k in np.flatnonzero(n > 100):
        out[k] = np.median(vv[off[k]:off[k + 1]])
    r = 10 ** (lo + (np.arange(nb) + 0.5) / nb * (hi - lo))
    return r, out


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--v14", default=("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/"
                                      "1-Unint Capes/Capes Totals/CapesTotalsV14.psd"))
    ap.add_argument("--run", default=None)
    a = ap.parse_args()
    vistes = os.path.join(os.path.dirname(a.v14), "CapesTotalsV14_vistes")
    reb = json.load(open(os.path.join(vistes, "REBUT_V14.json")))
    ARREL = os.path.expanduser("~/Desktop/Eclipse determinista")
    run_dir = a.run or os.path.join(ARREL, "1-RUNS", reb["run"])
    sys.path.insert(0, os.path.join(run_dir, "codi"))
    import comu                                              # noqa: E402
    run = comu.Run.obre(run_dir)
    F12 = run.llegeix_rebut("F1.2_sol_llenc.json")
    LL = F12["llenc"]; W, H = LL["W"], LL["H"]; RS = LL["R_sol_px"]
    RL = F12["contactes"]["R_lluna_px"]
    S = F12["fotogrames"]
    res = {"portes": {}}

    # ---------------- A · el transformat ----------------
    lim = json.load(open(os.path.join(AQUI, "limbe_v13.json"))) if os.path.exists(
        os.path.join(AQUI, "limbe_v13.json")) else {}
    dif = []
    for capa, d in lim.items():
        dif.append(math.hypot(d["dx"], d["dy"]))
    res["portes"]["A_transformat"] = {
        "n_capes_mesurades": len(dif),
        "residu_max_px": max(dif) if dif else None,
        "residu_mediana_px": float(np.median(dif)) if dif else None,
        "llindar_px": 3.0,
        "veredicte": "PASSA" if dif and max(dif) <= 3.0 else ("SENSE MESURA" if not dif else "FALLA")}

    # ---------------- B · cap màscara sobre zona sense dada ----------------
    fora = {c["num"]: c["px_mascara_sobre_zona_sense_dada"] for c in reb["capes"]}
    res["portes"]["B_mascara_sense_dada"] = {
        "per_capa": fora, "total": int(sum(fora.values())),
        "veredicte": "PASSA" if sum(fora.values()) == 0 else "FALLA"}

    # ---------------- C, D, E · sobre el compost ----------------
    from psd_tools import PSDImage
    psd = PSDImage.open(a.v14)
    comp = np.asarray(psd.numpy())[..., :3].astype(np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - H / 2.0, xx - W / 2.0); del yy, xx
    L = comp.mean(axis=2)
    hi = comp.max(axis=2) > 0
    # C · el disc lunar: la INTERSECCIÓ dels discos, que és el que mai té dada
    ts = [v for v in S.values() if v["coronal"]]
    cx = np.array([v["lluna_dx"] for v in ts]); cy = np.array([v["lluna_dy"] for v in ts])
    th = math.radians(-LL["pa_north_deg"]); ca, sa = math.cos(th), math.sin(th)
    X = W / 2.0 + (ca * cx - sa * cy); Y = H / 2.0 + (sa * cx + ca * cy)
    dins = np.ones((H, W), bool)
    for k in range(len(X)):
        dins &= np.hypot(np.arange(W)[None, :] - X[k],
                         np.arange(H)[:, None] - Y[k]) < RL
    res["portes"]["C_disc_lunar"] = {
        "px_interseccio": int(dins.sum()),
        "nivell_mitja": float(L[dins].mean()), "nivell_p99": float(np.percentile(L[dins], 99)),
        "nivell_max": float(L[dins].max()),
        "referencia_V13": 0.137, "referencia_V13_Pere": 0.024,
        "veredicte": "PASSA" if float(np.percentile(L[dins], 99)) <= 0.005 else "MIRA-HO"}

    # D · monotonia del perfil
    r, p = perfil(L, rad, RS, hi & ~dins)
    tot = np.isfinite(p) & (r >= 1.015) & (r <= 8.0)
    R_COMPLETA = 1.07
    bo = tot & (r >= R_COMPLETA)
    rr, pp = r[bo], p[bo]
    rt, pt = r[tot], p[tot]
    d = np.diff(pp)
    res["portes"]["D_monotonia"] = {
        "r_cobertura_completa_Rsol": R_COMPLETA,
        "n_calaixos": int(bo.sum()),
        "maxim_del_perfil": float(pt.max()),
        "r_del_maxim_Rsol": float(rt[int(np.argmax(pt))]),
        "pujades": int((d > 0).sum()),
        "pujada_maxima": float(d.max()),
        "r_de_la_pujada_maxima_Rsol": float(rr[int(np.argmax(d))]),
        "nivell_a_1.1_Rsol": float(np.interp(1.1, rr, pp)),
        "nivell_a_2_Rsol": float(np.interp(2.0, rr, pp)),
        "nivell_a_4_Rsol": float(np.interp(4.0, rr, pp)),
        "referencia_V13": {"r_del_maxim": 2.0, "1.09": 0.518, "2.15": 0.719, "3.74": 0.484},
        "llindar_pujada": 0.001,
        "veredicte": "PASSA" if (d <= 0.001).all() and rt[int(np.argmax(pt))] < 1.2 else "MIRA-HO"}

    # E · cap bony a les vores interiors de les capes
    K = 6
    res_loc = pp[K:-K] - 0.5 * (pp[:-2 * K] + pp[2 * K:])
    from scipy.ndimage import median_filter
    tend = median_filter(res_loc, size=25, mode="nearest")
    exc = res_loc - tend
    sg = 1.4826 * np.median(np.abs(exc - np.median(exc)))
    bonys = []
    for c in reb["capes"]:
        rv = c["rang_validesa_Rsol"][0]
        if rv is None or not (rr[K] < rv < rr[-K - 1]):
            bonys.append({"capa": c["num"], "r_Rsol": rv, "z": None,
                          "nota": "la vora interior cau fora del tram mesurat"})
            continue
        k = int(np.argmin(np.abs(rr[K:-K] - rv)))
        z = float((exc[k] - np.median(exc)) / max(sg, 1e-12))
        amp = float(100.0 * (exc[k] - np.median(exc)) / max(float(np.interp(rv, rr, pp)), 1e-9))
        bonys.append({"capa": c["num"], "r_Rsol": rv, "z": z, "amplitud_pct_del_nivell": amp})
    pitjor = max((abs(b["z"]) for b in bonys if b["z"] is not None), default=0.0)
    amp_max = max((abs(b.get("amplitud_pct_del_nivell", 0.0)) for b in bonys), default=0.0)
    res["portes"]["E_halos"] = {
        "finestra_calaixos": K, "finestra_tendencia": 25, "sigma_excedent": float(sg),
        "per_capa": bonys, "z_pitjor": pitjor,
        "amplitud_maxima_pct": amp_max,
        "llindar_pct": 1.1,
        "llindar_d_on_ve": ("research/100: els esglaons veïns d'aquesta escala discrepen "
                            "1,1-1,3 % amb el signe alternat. És el terra físic d'un "
                            "muntatge per capes; la porta demana no amplificar-lo."),
        "veredicte": "PASSA" if amp_max <= 1.1 else "MIRA-HO"}
    res["perfil"] = {"r_Rsol": [float(x) for x in rt], "nivell": [float(x) for x in pt]}

    # ---------------- F · la Lluna és rodona ----------------
    lld = reb.get("lluna_declarada")
    if lld:
        cx, cy = lld["centre_px"]; RLd = lld["R_lluna_px"]
        naz = 720
        az = np.linspace(0, 2 * np.pi, naz, endpoint=False)
        rs = np.arange(0.0, RLd * 1.25, 0.5)
        ys = (cy + rs[None, :] * np.cos(az)[:, None]).astype(np.float32)
        xs = (cx + rs[None, :] * np.sin(az)[:, None]).astype(np.float32)
        prof = cv2.remap(L, xs, ys, cv2.INTER_LINEAR, borderValue=1.0)
        rr = np.full(naz, np.nan)
        for k in range(naz):
            fo = np.flatnonzero(prof[k] > 0.004)
            if fo.size:
                rr[k] = rs[fo[0]]
        bo = np.isfinite(rr)
        med = float(np.median(rr[bo]))
        dev = float(np.max(np.abs(rr[bo] - med)))
        res["portes"]["F_lluna_rodona"] = {
            "centre_declarat_px": [cx, cy], "R_declarat_px": RLd,
            "n_azimuts": int(bo.sum()),
            "r_mediana_px": med, "r_min_px": float(np.nanmin(rr)),
            "r_max_px": float(np.nanmax(rr)),
            "desviacio_maxima_px": dev,
            "rms_px": float(np.std(rr[bo])),
            "llindar_px": 3.0,
            "veredicte": "PASSA" if dev <= 3.0 else "MIRA-HO"}

    json.dump(res, open(os.path.join(vistes, "PORTES_V14.json"), "w"), indent=1, ensure_ascii=False)
    for k, v in res["portes"].items():
        print(f"  {k:26s} {v['veredicte']}")
    print(f"\n  C · disc lunar: mitjana {res['portes']['C_disc_lunar']['nivell_mitja']:.4f} "
          f"p99 {res['portes']['C_disc_lunar']['nivell_p99']:.4f} "
          f"(V13 0,137 · V13_Pere 0,024)")
    d = res["portes"]["D_monotonia"]
    print(f"  D · màxim {d['maxim_del_perfil']:.3f} a {d['r_del_maxim_Rsol']:.3f} R☉ "
          f"(V13: a 2,0) · nivell 1,1 {d['nivell_a_1.1_Rsol']:.3f} · 2 R☉ "
          f"{d['nivell_a_2_Rsol']:.3f} · 4 R☉ {d['nivell_a_4_Rsol']:.3f} · "
          f"pujades {d['pujades']} (màx {d['pujada_maxima']:+.5f})")
    trossos = []
    for b in bonys:
        z = "—" if b["z"] is None else f"{b['z']:+.1f}"
        am = ("—" if b.get("amplitud_pct_del_nivell") is None
              else f"{b['amplitud_pct_del_nivell']:+.3f} %")
        rv = "—" if b["r_Rsol"] is None else f"{b['r_Rsol']:.2f}"
        trossos.append(f"{b['capa']}({rv} R☉, {am}, z={z})")
    if "F_lluna_rodona" in res["portes"]:
        f_ = res["portes"]["F_lluna_rodona"]
        print(f"  F · Lluna: r mediana {f_['r_mediana_px']:.1f} px (declarat "
              f"{f_['R_declarat_px']:.1f}) · min {f_['r_min_px']:.1f} màx {f_['r_max_px']:.1f} "
              f"· desviació {f_['desviacio_maxima_px']:.1f} px · rms {f_['rms_px']:.2f}")
    print(f"  E · ondulació màxima {amp_max:.3f} % del nivell (llistó 1,1 % de research/100) · "
          f"z pitjor {pitjor:.2f}")
    print("      " + (", ".join(trossos) or "—"))
    return res


if __name__ == "__main__":
    main()
