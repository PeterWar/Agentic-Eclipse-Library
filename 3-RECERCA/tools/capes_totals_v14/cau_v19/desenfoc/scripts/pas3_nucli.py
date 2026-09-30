# -*- coding: utf-8 -*-
"""Pas 3: nucli del desenfoc mesurat per correlació creuada finestra a finestra.
- hp suau (resta gaussiana sigma=24), Hann, C = ifft(F2 conj F1) normalitzada per Ac1(0)
- angle de la cresta per moments -> centre de convergència per mínims quadrats
- apilat de C i de l'autocorrelació de capa2 girats al marc radial, per calaixos de radi
"""
import numpy as np, cv2, json, os

BASE = "/Users/USUARI/Downloads/Eclipse 2026/research/tools/capes_totals_v14/cau_v19/desenfoc"
OUT = os.path.join(BASE, "geometria_fable")
SCR = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/dfcda07d-fe88-40c0-8251-cd1d860283ac/scratchpad/desenfoc"
geo = json.load(open(os.path.join(BASE, "geometria.json")))
xc, yc = geo["sol_crop"]; rs = geo["rs"]

res1 = np.load(os.path.join(SCR, "residu_capa1_G.npy"), mmap_mode="r")
res2 = np.load(os.path.join(SCR, "residu_capa2_G.npy"), mmap_mode="r")
M2 = np.load(os.path.join(BASE, "capa2_mask16.npy"), mmap_mode="r")
H, W = res1.shape

N = 768; h = N // 2; PAS = 384
HANN = (np.hanning(N)[:, None] * np.hanning(N)[None, :]).astype(np.float32)

def prepara(a):
    a = np.array(a, np.float32)
    a = a - cv2.GaussianBlur(a, (0, 0), 24)
    a -= a.mean()
    return a * HANN

finestres = []
for Y in range(h, H - h + 1, PAS):
    for X in range(h, W - h + 1, PAS):
        r = float(np.hypot(X - xc, Y - yc))
        if r < 2.6 * rs:
            continue
        mm = np.asarray(M2[Y - h:Y + h:8, X - h:X + h:8], np.float32).mean() / 65535.0
        if mm < 0.97:
            continue
        finestres.append((X, Y, r))
print("finestres:", len(finestres))

RB = [(2.6, 3.5), (3.5, 4.5), (4.5, 5.5), (5.5, 6.5), (6.5, 8.0), (8.0, 11.0)]
stC = {i: np.zeros((N, N), np.float64) for i in range(len(RB))}
stA2 = {i: np.zeros((N, N), np.float64) for i in range(len(RB))}
stA1 = {i: np.zeros((N, N), np.float64) for i in range(len(RB))}
nst = {i: 0 for i in range(len(RB))}
angles = []

for (X, Y, r) in finestres:
    a1 = prepara(res1[Y - h:Y + h, X - h:X + h])
    a2 = prepara(res2[Y - h:Y + h, X - h:X + h])
    F1 = np.fft.rfft2(a1); F2 = np.fft.rfft2(a2)
    e1 = float((a1 * a1).sum()); e2 = float((a2 * a2).sum())
    if e1 <= 0 or e2 <= 0 or e2 / e1 < 1e-5:
        continue
    C = np.fft.fftshift(np.fft.irfft2(F2 * np.conj(F1), s=(N, N))) / e1
    A2 = np.fft.fftshift(np.fft.irfft2(F2 * np.conj(F2), s=(N, N))) / e2
    A1 = np.fft.fftshift(np.fft.irfft2(F1 * np.conj(F1), s=(N, N))) / e1
    ang = np.degrees(np.arctan2(Y - yc, X - xc))
    # gir perquè +x sigui el radial cap enfora
    Mrot = cv2.getRotationMatrix2D((h, h), ang, 1.0)
    Cr = cv2.warpAffine(C.astype(np.float32), Mrot, (N, N), flags=cv2.INTER_LINEAR)
    A2r = cv2.warpAffine(A2.astype(np.float32), Mrot, (N, N), flags=cv2.INTER_LINEAR)
    A1r = cv2.warpAffine(A1.astype(np.float32), Mrot, (N, N), flags=cv2.INTER_LINEAR)
    for i, (lo, hi) in enumerate(RB):
        if lo <= r / rs < hi:
            stC[i] += Cr; stA2[i] += A2r; stA1[i] += A1r; nst[i] += 1
    # angle de la cresta per moments de C (finestra |d|<250, només valors positius alts)
    yy, xx = np.mgrid[-h:h, -h:h]
    dd = np.hypot(xx, yy)
    sel = (dd < 250) & (dd > 3)
    v = C[sel]
    llin = np.percentile(v, 99.0)
    m = sel & (C > llin)
    wgt = C[m] - llin
    ux = xx[m].astype(np.float64); uy = yy[m].astype(np.float64)
    Wt = wgt.sum()
    if Wt <= 0:
        continue
    c20 = (ux * ux * wgt).sum() / Wt; c02 = (uy * uy * wgt).sum() / Wt
    c11 = (ux * uy * wgt).sum() / Wt
    th = 0.5 * np.arctan2(2 * c11, c20 - c02)
    tr = c20 + c02; disc = np.sqrt(max((c20 - c02) ** 2 / 4 + c11 ** 2, 0))
    elong = np.sqrt((tr / 2 + disc) / max(tr / 2 - disc, 1e-9))
    angles.append({"X": X, "Y": Y, "r_px": r, "r_rs": r / rs,
                   "ang_radial": ang % 180.0, "ang_cresta": float(np.degrees(th) % 180.0),
                   "elong": float(elong), "pes": float(Wt),
                   "e2_sobre_e1": e2 / e1})

print("finestres amb cresta:", len(angles))
np.savez(os.path.join(SCR, "nuclis_apilats.npz"),
         **{f"C_{i}": (stC[i] / max(nst[i], 1)).astype(np.float32) for i in range(len(RB))},
         **{f"A2_{i}": (stA2[i] / max(nst[i], 1)).astype(np.float32) for i in range(len(RB))},
         **{f"A1_{i}": (stA1[i] / max(nst[i], 1)).astype(np.float32) for i in range(len(RB))},
         n=np.array([nst[i] for i in range(len(RB))]),
         bins=np.array(RB))

# centre de convergència: recta de cada finestra (pel seu centre, direcció de la cresta)
def ajusta_centre(sel_angles):
    A = np.zeros((2, 2)); b = np.zeros(2)
    for a in sel_angles:
        th = np.radians(a["ang_cresta"])
        nx, ny = -np.sin(th), np.cos(th)
        w = a["pes"] * min(a["elong"], 10.0)
        nn = w * np.outer([nx, ny], [nx, ny])
        A += nn; b += nn @ np.array([a["X"], a["Y"]])
    return np.linalg.solve(A, b)

def rms_perp(sel_angles, cx_, cy_):
    d = []
    for a in sel_angles:
        th = np.radians(a["ang_cresta"])
        nx, ny = -np.sin(th), np.cos(th)
        d.append((nx * (cx_ - a["X"]) + ny * (cy_ - a["Y"])) ** 2)
    return float(np.sqrt(np.mean(d)))

bons = [a for a in angles if a["elong"] > 1.8]
C0 = ajusta_centre(bons)
geoC = (8156 / 2.0, 5422 / 2.0)
resum = {
    "n_finestres": len(finestres), "n_crestes": len(angles), "n_bones": len(bons),
    "centre_ajustat": [float(C0[0]), float(C0[1])],
    "sol": [xc, yc], "centre_geometric": list(geoC),
    "dist_a_sol_px": float(np.hypot(C0[0] - xc, C0[1] - yc)),
    "dist_a_geometric_px": float(np.hypot(C0[0] - geoC[0], C0[1] - geoC[1])),
    "rms_perp_px": {"ajustat": rms_perp(bons, *C0), "sol": rms_perp(bons, xc, yc),
                    "geometric": rms_perp(bons, *geoC)},
    "dang_cresta_vs_radial_deg": {},
    "n_per_bin": {str(RB[i]): nst[i] for i in range(len(RB))},
}
d = [((a["ang_cresta"] - a["ang_radial"] + 90) % 180) - 90 for a in bons]
resum["dang_cresta_vs_radial_deg"] = {"mediana": float(np.median(d)),
                                      "p16": float(np.percentile(d, 16)),
                                      "p84": float(np.percentile(d, 84)), "n": len(d)}
json.dump({"resum": resum, "finestres": angles},
          open(os.path.join(OUT, "nucli_finestres.json"), "w"), indent=1)
print(json.dumps(resum, indent=1))
