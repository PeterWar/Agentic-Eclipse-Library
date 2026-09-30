# -*- coding: utf-8 -*-
"""Pas 4c: nucli DEFINITIU en log-polar, amb correcció del solapament de Hann,
soroll de la dispersió entre sectors, i graella de centres.
Zona fiable: 3,5-6,05 Rs (fora de corona i dins del camp d'estrelles del V18).
"""
import numpy as np, cv2, json, os, sys

BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
OUT = os.path.join(BASE, "geometria_fable")
SCR = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/dfcda07d-fe88-40c0-8251-cd1d860283ac/scratchpad/desenfoc"
geo = json.load(open(os.path.join(BASE, "geometria.json")))
xc, yc = geo["sol_crop"]; rs = geo["rs"]

hp1 = np.ascontiguousarray(np.load(os.path.join(SCR, "hp1.npy"), mmap_mode="r"))
hp2 = np.ascontiguousarray(np.load(os.path.join(SCR, "hp2.npy"), mmap_mode="r"))
M2 = np.load(os.path.join(BASE, "capa2_mask16.npy"), mmap_mode="r")
mval = (np.asarray(M2, np.float32) >= 60000).astype(np.float32)

NU, NTH, RMAX = 16384, 2880, 5150.0
DU = np.log(RMAX) / NU
VMAX = 0.32
nv = int(VMAX / DU)

def nucli(cx, cy, bandes):
    lp1 = cv2.warpPolar(hp1, (NU, NTH), (cx, cy), RMAX, cv2.INTER_LINEAR | cv2.WARP_POLAR_LOG)
    lp2 = cv2.warpPolar(hp2, (NU, NTH), (cx, cy), RMAX, cv2.INTER_LINEAR | cv2.WARP_POLAR_LOG)
    lpm = cv2.warpPolar(mval, (NU, NTH), (cx, cy), RMAX, cv2.INTER_LINEAR | cv2.WARP_POLAR_LOG)
    res = {}
    for (lo, hi) in bandes:
        u_lo = int(np.log(lo * rs) / DU); u_hi = int(np.log(hi * rs) / DU)
        L = u_hi - u_lo
        Lf = int(2 ** np.ceil(np.log2(L + 2 * nv + 8)))
        hann = np.hanning(L).astype(np.float64)
        # solapament exacte de la Hann amb ella mateixa per cada retard
        ov_full = np.correlate(hann * hann, hann * hann, mode="full")
        ov_full /= ov_full.max()
        centre = L - 1
        lags = np.arange(-nv, nv + 1)
        ov = np.array([ov_full[centre + l] if 0 <= centre + l < len(ov_full) else 0.0 for l in lags])
        n_sect = 24; fs = NTH // n_sect
        sK = []
        for s0 in range(0, NTH, fs):
            acc = np.zeros(Lf); npar = 0
            for j in range(s0, s0 + fs):
                if lpm[j, u_lo:u_hi].mean() < 0.98:
                    continue
                x1 = lp1[j, u_lo:u_hi].astype(np.float64)
                x2 = lp2[j, u_lo:u_hi].astype(np.float64)
                x1 -= x1.mean(); x2 -= x2.mean()
                x1 *= hann; x2 *= hann
                F1 = np.fft.rfft(x1, Lf); F2 = np.fft.rfft(x2, Lf)
                acc += np.fft.irfft(F2 * np.conj(F1), Lf)
                npar += 1
            if npar >= fs // 4:
                sK.append(np.concatenate([acc[-nv:], acc[:nv + 1]]) / npar)
        if not sK:
            continue
        sK = np.array(sK)
        K = np.median(sK, axis=0)
        err = 1.2533 * sK.std(axis=0) / np.sqrt(len(sK))
        vv = lags * DU
        usable = ov > 0.12
        Kc = np.where(usable, K / np.maximum(ov, 0.12), 0.0)
        ec = np.where(usable, err / np.maximum(ov, 0.12), np.inf)
        # fons: mediana de la part usable amb |v| gran
        cuau = usable & (np.abs(vv) > 0.8 * vv[usable].max())
        if cuau.sum() > 10:
            Kc = Kc - np.median(Kc[cuau])
        res[f"{lo}-{hi}"] = {"v": vv, "K": Kc, "err": ec, "usable": usable,
                             "n_sectors": len(sK)}
    return res

BANDES = [(3.5, 4.6), (4.6, 6.05), (3.5, 6.05)]
mode = sys.argv[1] if len(sys.argv) > 1 else "nucli"

if mode == "nucli":
    res = nucli(xc, yc, BANDES)
    sortida = {}
    for k, d in res.items():
        vv, K, err, us = d["v"], d["K"], d["err"], d["usable"]
        pic = K[us].max(); ip = int(np.nonzero(us)[0][np.argmax(K[us])])
        err_pic = float(np.median(err[np.abs(vv) < 0.03]))
        lo_b, hi_b = (float(x) for x in k.split("-"))
        r_mig = 0.5 * (lo_b + hi_b) * rs
        fites = {}
        for f in (0.5, 0.2, 0.05):
            llind = max(f * pic, 3 * err_pic)
            dins = np.nonzero((K > llind) & us)[0]
            fites[str(f)] = [float(vv[dins[0]]), float(vv[dins[-1]])] if len(dins) else None
        Kp = np.where(us, K, 0).clip(0)
        cs = np.cumsum(Kp); cs /= cs[-1]
        quant = {str(q): float(vv[np.searchsorted(cs, q)]) for q in (0.05, 0.25, 0.5, 0.75, 0.95)}
        m_in = Kp[vv < -0.003].sum(); m_out = Kp[vv > 0.003].sum()
        sortida[k] = {"n_sectors": d["n_sectors"], "pic_sobre_err": float(pic / err_pic),
                      "v_pic": float(vv[ip]), "r_mig_px": r_mig,
                      "fites_v": fites, "quantils_massa_v": quant,
                      "frac_massa_endins": float(m_in / (m_in + m_out)),
                      "perfil_v": vv[us][::4].tolist(),
                      "perfil_K_norm": (K[us][::4] / pic).tolist()}
        print("== banda", k, "n_sect", d["n_sectors"], "pic/err %.1f" % (pic / err_pic))
        print("   fites:", {kk: ["%+.4f" % x for x in v] if v else None for kk, v in fites.items()})
        print("   quantils massa:", {kk: "%+.4f" % v for kk, v in quant.items()},
              " frac endins %.2f" % (m_in / (m_in + m_out)))
        print("   perfil K/pic:", "  ".join("%+.3f:%.2f" % (vv[j], K[j] / pic)
              for j in range(0, len(vv), 24) if us[j]))
    json.dump(sortida, open(os.path.join(OUT, "nucli_final.json"), "w"), indent=1)
elif mode == "graella":
    passos = [-150, -75, 0, 75, 150]
    taula = []
    for dy in passos:
        fila = []
        for dx in passos:
            r = nucli(xc + dx, yc + dy, [(4.0, 6.0)])
            d = r["4.0-6.0"]
            vv, K, err = d["v"], d["K"], d["err"]
            err_pic = float(np.median(err[np.abs(vv) < 0.03]))
            p = float(K[np.abs(vv) < 0.05].max() / err_pic)
            fila.append(p)
            print("dx %+4d dy %+4d  pic/err %8.1f" % (dx, dy, p))
        taula.append(fila)
    json.dump({"passos_px": passos, "pic_sobre_err": taula},
              open(os.path.join(OUT, "nucli_graella_centres.json"), "w"), indent=1)
