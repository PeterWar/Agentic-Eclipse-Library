"""x2 (verificador adversari 3) · COLOR I LLUMINÀNCIA fora de 6 R☉: prova s amb DISTRIBUCIÓ NUL·LA i per REGIONS (no només per anells).
fusion_starless (cadena control / flat2d_v2 / flat2d_v3): ln R/G, ln B/G i ln G; bandes σ2–20, σ20–200, σ200–800.
s = (ΣY² − ΣX²)/ΣΔ² (X = control, Y = v, Δ = Y − X): −1 cura, +1 injecció. NUL: X desplaçat 12 vegades (200–900 px) → mitjana i σ de s_nul;
z = (s − ⟨s_nul⟩)/σ(s_nul). Regions (R > 6 R☉ i també 3–6 R☉):
  · «només Sony» (fora del camp de la Vixen) i «Vixen» (dins), segons el suport de vixen_starless del control;
  · distància a la vora del camp de la Sony (suport de sony_starless): 0–300, 300–1000, > 1000 px (les «bandes paral·leles a les vores»).
També rajoles de 512 px a R > 3 R☉: quantes tenen s > 0 amb |Δ| apreciable (possible injecció local amagada a la mitjana).
Sortida: 4-RESULTATS/v108_20260926/verifica3_flat2d/X2_COLOR_S.json"""
import json
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica3_flat2d'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603
CAD = A / '4-RESULTATS/v108_20260926/cadena'
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; del yy, xx
def sup(p):
    x = np.asarray(np.load(p, mmap_mode='r')[..., 1], np.float32); return (np.isfinite(x) & (x > 0))
VIX = sup(CAD / 'control/lineal/vixen_starless.npy'); SON = sup(CAD / 'control/lineal/sony_starless.npy')
DSON = cv2.distanceTransform(SON.astype(np.uint8), cv2.DIST_L2, 5); DVIX = cv2.distanceTransform(VIX.astype(np.uint8), cv2.DIST_L2, 5)
rng = np.random.default_rng(21); DESPL = []
while len(DESPL) < 12:
    r = rng.uniform(200, 900); t = rng.uniform(0, 2 * np.pi); DESPL.append((int(r * np.cos(t)), int(r * np.sin(t))))
def q(v, nom):
    f = np.load(CAD / v / 'lineal/fusion_starless.npy', mmap_mode='r'); G = np.asarray(f[..., 1], np.float32)
    x = G if nom == 'lnG' else np.asarray(f[..., 0 if nom == 'lnRG' else 2], np.float32) / np.maximum(G, 1e-20)
    ok = np.isfinite(x) & (x > 0) & (G > 0); return np.where(ok, np.log(np.maximum(x, 1e-20)), 0).astype(np.float32), ok
R = {}
for nom in ('lnRG', 'lnBG', 'lnG'):
    L = {}; ok = None
    for v in ('control', 'flat2d_v2', 'flat2d_v3'):
        L[v], o = q(v, nom); ok = o if ok is None else ok & o
    m = ok.astype(np.float32)
    ng = lambda l, s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    out = {}
    for s1, s2 in ((2, 20), (20, 200), (200, 800)):
        er = min(int(2 * s2) | 1, 801); okb = cv2.erode(m, np.ones((er, er), np.uint8)) > 0
        X = (ng(L['control'], s1) - ng(L['control'], s2)).astype(np.float32)
        REG = {'3-6_tot': (RS >= 3) & (RS < 6), '>6_tot': RS >= 6, '>6_nomes_sony': (RS >= 6) & ~VIX, '>6_vixen': (RS >= 6) & VIX & (DVIX > 300),
               '>6_vora_vixen_0-300': (RS >= 6) & VIX & (DVIX <= 300),
               '>6_vora_sony_0-300': (RS >= 6) & (DSON < 300), '>6_vora_sony_300-1000': (RS >= 6) & (DSON >= 300) & (DSON < 1000), '>6_vora_sony_>1000': (RS >= 6) & (DSON >= 1000)}
        ob = {}
        for v in ('flat2d_v2', 'flat2d_v3'):
            Y = (ng(L[v], s1) - ng(L[v], s2)).astype(np.float32); D = Y - X; o = {}
            for rn, rm in REG.items():
                k = okb & rm
                if k.sum() < 20000: continue
                x = X[k].astype(np.float64); d = D[k].astype(np.float64); ED = (d * d).sum(); EX = (x * x).sum()
                s = 1 + 2 * (x * d).sum() / ED; nul = []
                for dx, dy in DESPL:
                    Xs = np.roll(np.roll(X, dx, 1), dy, 0); ks = k & np.roll(np.roll(okb, dx, 1), dy, 0); ds = D[ks].astype(np.float64)
                    nul.append(1 + 2 * float((Xs[ks].astype(np.float64) * ds).sum() / (ds * ds).sum()))
                nul = np.array(nul)
                o[rn] = dict(s=round(float(s), 3), s_nul_mitjana=round(float(nul.mean()), 3), s_nul_sd=round(float(nul.std()), 3), z=round(float((s - nul.mean()) / nul.std()), 1),
                             dE_pc=round(100 * float(((x + d) ** 2).sum() / EX - 1), 2), rms_D_ppm=round(1e4 * float(np.sqrt(ED / k.sum())), 2), rms_X_ppm=round(1e4 * float(np.sqrt(EX / k.sum())), 2))
            # rajoles de 512 px a R > 3 R☉
            T = 512; ny, nx = H // T, W // T; kk = (okb & (RS >= 3))[:ny * T, :nx * T]
            xd = (X * D)[:ny * T, :nx * T]; dd = (D * D)[:ny * T, :nx * T]
            sx = np.where(kk, xd, 0).reshape(ny, T, nx, T).sum((1, 3)); sd_ = np.where(kk, dd, 0).reshape(ny, T, nx, T).sum((1, 3)); n = kk.reshape(ny, T, nx, T).sum((1, 3))
            val = n > 0.5 * T * T; st = 1 + 2 * sx / np.maximum(sd_, 1e-30); rmsd = 1e4 * np.sqrt(sd_ / np.maximum(n, 1))
            gran = val & (rmsd >= np.percentile(rmsd[val], 50))
            o['rajoles_512_R>3'] = {'n': int(val.sum()), 'n_s_positiu': int((val & (st > 0)).sum()), 'n_s_major_0.5': int((val & (st > 0.5)).sum()),
                                    'n_s_positiu_entre_les_de_Delta_gran': int((gran & (st > 0)).sum()), 'n_de_Delta_gran': int(gran.sum()),
                                    'pitjors':[dict(x=int((j + .5) * T), y=int((i + .5) * T), s=round(float(st[i, j]), 2), rms_D_ppm=round(float(rmsd[i, j]), 2)) for i, j in sorted(zip(*np.nonzero(val)), key=lambda ij: -st[ij])[:6]]}
            ob[v] = o; del Y, D
        out[f'{s1}-{s2}px'] = ob; print(nom, s1, s2, json.dumps(ob), flush=True); del X
    R[nom] = out; del L
    (OUT / 'X2_COLOR_S.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
