# -*- coding: utf-8 -*-
"""Pas 4b: nucli log-polar afinat.
- NU=16384 (Δu = 5,22e-4), totes les files, soroll = dispersió entre sectors
- autocorrelació de capa1 (rho) per separar la component delta (còpia sense moure)
- 6 bandes fines pel test d'escala-invariància
- mode 'graella': afina el centre amb el pic de correlació
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
BANDES = [(3.3, 4.0), (4.0, 5.0), (5.0, 6.0), (6.0, 7.2), (7.2, 8.6), (8.6, 10.5)]
VMAX = 0.30
nv = int(VMAX / DU)

def analitza(cx, cy, bandes, amb_rho=False):
    lp1 = cv2.warpPolar(hp1, (NU, NTH), (cx, cy), RMAX, cv2.INTER_LINEAR | cv2.WARP_POLAR_LOG)
    lp2 = cv2.warpPolar(hp2, (NU, NTH), (cx, cy), RMAX, cv2.INTER_LINEAR | cv2.WARP_POLAR_LOG)
    lpm = cv2.warpPolar(mval, (NU, NTH), (cx, cy), RMAX, cv2.INTER_LINEAR | cv2.WARP_POLAR_LOG)
    res = {}
    for (lo, hi) in bandes:
        u_lo = int(np.log(lo * rs) / DU); u_hi = int(np.log(hi * rs) / DU)
        L = u_hi - u_lo
        Lf = int(2 ** np.ceil(np.log2(L + 2 * nv + 8)))
        hann = np.hanning(L).astype(np.float64)
        n_sect = 24; fs = NTH // n_sect
        sK, sR = [], []
        for s0 in range(0, NTH, fs):
            accK = np.zeros(Lf); accR = np.zeros(Lf); npar = 0
            for j in range(s0, s0 + fs):
                if lpm[j, u_lo:u_hi].mean() < 0.98:
                    continue
                x1 = lp1[j, u_lo:u_hi].astype(np.float64)
                x2 = lp2[j, u_lo:u_hi].astype(np.float64)
                x1 -= x1.mean(); x2 -= x2.mean()
                x1 *= hann; x2 *= hann
                F1 = np.fft.rfft(x1, Lf); F2 = np.fft.rfft(x2, Lf)
                accK += np.fft.irfft(F2 * np.conj(F1), Lf)
                if amb_rho:
                    accR += np.fft.irfft(F1 * np.conj(F1), Lf)
                npar += 1
            if npar >= fs // 4:
                sK.append(np.concatenate([accK[-nv:], accK[:nv + 1]]) / npar)
                if amb_rho:
                    sR.append(np.concatenate([accR[-nv:], accR[:nv + 1]]) / npar)
        if not sK:
            continue
        sK = np.array(sK)
        K = np.median(sK, axis=0)
        err = 1.2533 * sK.std(axis=0) / np.sqrt(len(sK))     # error de la mediana
        vv = np.arange(-nv, nv + 1) * DU
        # fons: mediana de les cues
        cua = np.abs(vv) > 0.25
        K = K - np.median(K[cua])
        d = {"v": vv, "K": K, "err": err, "n_sectors": len(sK),
             "pic": float(K.max() / np.median(err[cua]))}
        if amb_rho:
            R = np.median(np.array(sR), axis=0)
            R = R - np.median(R[cua])
            d["rho"] = R
        res[f"{lo}-{hi}"] = d
    return res

mode = sys.argv[1] if len(sys.argv) > 1 else "fi"
if mode == "fi":
    res = analitza(xc, yc, BANDES, amb_rho=True)
    sortida = {}
    for k, d in res.items():
        vv, K, err = d["v"], d["K"], d["err"]
        i0 = int(np.argmax(K)); Kmax = K[i0]
        lo_b = float(k.split("-")[0]); hi_b = float(k.split("-")[1])
        r_mig = 0.5 * (lo_b + hi_b) * rs
        # component delta: ajusta a*rho al voltant de |v|<0.004 i resta
        R = d["rho"]; iC = len(vv) // 2
        w = slice(iC - 6, iC + 7)
        aa = float((K[w] * R[w]).sum() / (R[w] * R[w]).sum())
        Ksm = K - aa * R
        # àrees (aprox. de w0): tot en unitats d'àrea de rho
        area_rho = float(R.sum()); area_K = float(K.sum())
        w0 = aa * area_rho / area_K if area_K > 0 else np.nan
        fites = {}
        for f in (0.5, 0.1, 0.02):
            dins = np.nonzero(K > f * Kmax)[0]
            fites[f] = [float(vv[dins[0]]), float(vv[dins[-1]])] if len(dins) else None
        # el gruix del smear sol (sense delta), fites del 20% del seu màxim
        j0 = int(np.argmax(Ksm)); f2 = {}
        for f in (0.5, 0.2):
            dins = np.nonzero(Ksm > f * Ksm[j0])[0]
            f2[f] = [float(vv[dins[0]]), float(vv[dins[-1]])] if len(dins) else None
        # masses endins/enfora del smear
        m_in = float(Ksm[vv < -0.004].clip(0).sum()); m_out = float(Ksm[vv > 0.004].clip(0).sum())
        sortida[k] = {"pic_sobre_err": d["pic"], "n_sectors": d["n_sectors"],
                      "v_pic": float(vv[i0]), "w0_frac_copia": w0,
                      "fites_K": {str(f): v for f, v in fites.items()},
                      "fites_smear_sense_delta": {str(f): v for f, v in f2.items()},
                      "v_pic_smear": float(vv[j0]),
                      "massa_endins_frac": m_in / (m_in + m_out) if m_in + m_out > 0 else np.nan,
                      "r_mig_px": r_mig,
                      "L_smear_px_al_20pc": [f2[0.2][0] * r_mig, f2[0.2][1] * r_mig] if f2[0.2] else None}
        np.save(os.path.join(SCR, f"lpfi_K_{k}.npy"), np.stack([vv, K, Ksm, err]))
    json.dump(sortida, open(os.path.join(OUT, "nucli_logpolar_fi.json"), "w"), indent=1)
    print(json.dumps(sortida, indent=1))
elif mode == "graella":
    passos = [-150, -75, 0, 75, 150]
    b = [(4.0, 6.0)]
    taula = []
    for dy in passos:
        fila = []
        for dx in passos:
            r = analitza(xc + dx, yc + dy, b)
            p = r.get("4.0-6.0", {"pic": 0})["pic"]
            fila.append(float(p))
            print("dx %+4d dy %+4d  pic/err %8.1f" % (dx, dy, p))
        taula.append(fila)
    json.dump({"passos_px": passos, "pic_sobre_err": taula},
              open(os.path.join(OUT, "nucli_logpolar_graella.json"), "w"), indent=1)
