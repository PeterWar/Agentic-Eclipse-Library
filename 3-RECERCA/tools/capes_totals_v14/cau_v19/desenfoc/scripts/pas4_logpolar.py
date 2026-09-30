# -*- coding: utf-8 -*-
"""Pas 4: nucli del zoom en LOG-POLAR. Si capa2 = zoom-blur(capa1) amb centre C,
en (theta, u=ln r) la relació és una convolució 1D al llarg d'u amb nucli w(v) fix.
Mesura: correlació creuada 1D per fila theta i banda d'u; MEDIANA sobre 24 sectors.
Es fa per diversos centres candidats per decidir el centre real.
"""
import numpy as np, cv2, json, os, sys

BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
OUT = os.path.join(BASE, "geometria_fable")
SCR = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/dfcda07d-fe88-40c0-8251-cd1d860283ac/scratchpad/desenfoc"
geo = json.load(open(os.path.join(BASE, "geometria.json")))
xc, yc = geo["sol_crop"]; rs = geo["rs"]

res1 = np.load(os.path.join(SCR, "residu_capa1_G.npy"), mmap_mode="r")
res2 = np.load(os.path.join(SCR, "residu_capa2_G.npy"), mmap_mode="r")
M2 = np.load(os.path.join(BASE, "capa2_mask16.npy"), mmap_mode="r")

# passa-alt cartesià suau (una vegada)
hp1_path = os.path.join(SCR, "hp1.npy"); hp2_path = os.path.join(SCR, "hp2.npy")
if not os.path.exists(hp1_path):
    a = np.array(res1, np.float32)
    np.save(hp1_path, a - cv2.GaussianBlur(a, (0, 0), 8)); del a
    a = np.array(res2, np.float32)
    np.save(hp2_path, a - cv2.GaussianBlur(a, (0, 0), 8)); del a
hp1 = np.load(hp1_path, mmap_mode="r")
hp2 = np.load(hp2_path, mmap_mode="r")
mval = (np.asarray(M2, np.float32) >= 60000).astype(np.float32)

NU = 8192      # mostres en u
NTH = 2880     # files en theta (0,125 graus)
RMAX = 5150.0
DU = np.log(RMAX) / NU     # pas en u per columna

A1 = np.ascontiguousarray(hp1)
A2 = np.ascontiguousarray(hp2)

def logpolar(img, centre):
    return cv2.warpPolar(img, (NU, NTH), centre, RMAX,
                         cv2.INTER_LINEAR | cv2.WARP_POLAR_LOG)

# bandes de radi (Rs) -> u
BANDES = [(3.2, 4.5), (4.5, 6.0), (6.0, 8.0), (8.0, 10.8)]
VMAX = 0.45    # abast del nucli en v = ln s
nv = int(VMAX / DU)

def nucli_per_centre(cx, cy, desa_prefix=None):
    lp1 = logpolar(A1, (cx, cy))
    lp2 = logpolar(A2, (cx, cy))
    lpm = logpolar(mval, (cx, cy))
    sortida = {}
    for (lo, hi) in BANDES:
        u_lo = int(np.log(lo * rs) / DU); u_hi = int(np.log(hi * rs) / DU)
        L = u_hi - u_lo
        Lf = int(2 ** np.ceil(np.log2(L + 2 * nv)))
        hann = np.hanning(L).astype(np.float32)
        sect = []
        n_sect = 24; files_sect = NTH // n_sect
        for s0 in range(0, NTH, files_sect):
            acc = np.zeros(Lf); npar = 0
            for j in range(s0, s0 + files_sect, 2):   # 1 de cada 2 files
                m = lpm[j, u_lo:u_hi]
                if m.mean() < 0.98:
                    continue
                x1 = lp1[j, u_lo:u_hi].astype(np.float64)
                x2 = lp2[j, u_lo:u_hi].astype(np.float64)
                x1 -= x1.mean(); x2 -= x2.mean()
                x1 *= hann; x2 *= hann
                F1 = np.fft.rfft(x1, Lf); F2 = np.fft.rfft(x2, Lf)
                acc += np.fft.irfft(F2 * np.conj(F1), Lf)
                npar += 1
            if npar >= files_sect // 4:
                e = acc / npar
                sect.append(np.concatenate([e[-nv:], e[:nv + 1]]))   # v de -nv..+nv
        sect = np.array(sect)
        if len(sect) == 0:
            continue
        K = np.median(sect, axis=0)
        # fons i soroll: mediana i MAD de les cues |v|>0.35
        vv = (np.arange(-nv, nv + 1)) * DU
        cua = K[np.abs(vv) > 0.35]
        fons = np.median(cua); soroll = 1.4826 * np.median(np.abs(cua - fons)) + 1e-30
        sortida[f"{lo}-{hi}"] = {
            "v": vv, "K": K - fons, "soroll": soroll, "n_sectors": len(sect),
            "pic": float((K - fons).max() / soroll),
        }
        if desa_prefix:
            np.save(os.path.join(SCR, f"{desa_prefix}_K_{lo}-{hi}.npy"),
                    np.stack([vv, K - fons]))
    return sortida

def resum(nom, srt):
    print("== centre", nom)
    for k, d in srt.items():
        K = d["K"]; vv = d["v"]; s = d["soroll"]
        i0 = np.argmax(K)
        print(" banda %s Rs: pic %.0f std a v=%+.4f (n_sect %d)" % (k, K[i0] / s, vv[i0], d["n_sectors"]))
        for f in (0.5, 0.1, 0.02):
            dins = np.nonzero(K > f * K[i0])[0]
            if len(dins):
                print("   >%2.0f%% del pic: v de %+.4f a %+.4f  (Δr/r %+.3f .. %+.3f)"
                      % (100 * f, vv[dins[0]], vv[dins[-1]],
                         np.expm1(vv[dins[0]]), np.expm1(vv[dins[-1]])))
    return {k: {"pic_sobre_soroll": float(d["K"].max() / d["soroll"]),
                "v_pic": float(d["v"][np.argmax(d["K"])])} for k, d in srt.items()}

candidats = {"sol": (xc, yc), "geometric": (8156 / 2.0, 5422 / 2.0)}
mode = sys.argv[1] if len(sys.argv) > 1 else "base"
resultats = {}
if mode == "base":
    for nom, (cx, cy) in candidats.items():
        srt = nucli_per_centre(cx, cy, desa_prefix=f"lp_{nom}")
        resultats[nom] = resum(nom, srt)
    json.dump(resultats, open(os.path.join(OUT, "nucli_logpolar_centres.json"), "w"), indent=1)
elif mode == "graella":
    # graella de centres al voltant del Sol per afinar el centre: pic de la banda 4.5-6
    passos = [-120, -60, 0, 60, 120]
    taula = []
    for dy in passos:
        fila = []
        for dx in passos:
            srt = nucli_per_centre(xc + dx, yc + dy)
            p = srt.get("4.5-6.0", {}).get("pic", 0.0)
            fila.append(p)
            print("dx %+4d dy %+4d pic %.0f" % (dx, dy, p))
        taula.append(fila)
    json.dump({"passos": passos, "pic_4p5_6": taula},
              open(os.path.join(OUT, "nucli_logpolar_graella.json"), "w"), indent=1)
