"""w3 (verificador adversari 2) · CURA O INJECCIÓ? per bandes d'escala i anells, amb control nul.
Per a cada parell (abans X, després Y = X + Δ) al ln i per a cada banda (DoG 0–1, 1–2, 2–4, 4–8, 8–16, 16–32 px) i anell (R☉):
  s = (ΣY² − ΣX²) / ΣΔ²  →  −1 si Δ treu una part que JA HI ERA a X (cura), +1 si Δ és independent de X (injecció, soroll afegit),
  s_nul = el mateix amb X desplaçat (53, −37) px (Δ col·locat on no toca): ha de sortir ≈ +1.
  També E_Y/E_X − 1 (el canvi d'energia de la banda) i rms(Δ) en ‱.
Si Δ fos cosmètic (suavitzat de la imatge) també donaria s ≈ −1: per això es mira també Brno (w4) i que Δ ve només del flat (codi).
Ús: w3_injeccio_per_bandes.py [parells]   Sortida: 4-RESULTATS/v108_20260926/verifica2_marrons/W3_INJECCIO.json"""
import json, sys
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica2_marrons'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; CAD = A / '4-RESULTATS/v108_20260926/cadena'; CR = A / '4-RESULTATS/v97_refundacio_20260924'
PARELLS = {
    'vixen_G': (CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', F2 / 'apilats/vixen_total.npy', 1),
    'sonyA_G': (CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', F2 / 'apilats/sony_A_total.npy', 1),
    'sonyB_G': (CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy', F2 / 'apilats/cau/sony_B_total_v42.npy', 1),
    'base_G': (CAD / 'control/lineal/base_G.npy', CAD / 'flat2d_v2/lineal/base_G.npy', None),
    'compost': (F2 / 'compost_control.npy', F2 / 'compost_flat2d_v2.npy', None),
    'L56_WOW': (CAD / 'control/estat_v108/L56_G.npy', CAD / 'flat2d_v2/estat_v108/L56_G.npy', None),
    'L54_MGN': (CAD / 'control/estat_v108/L54_G.npy', CAD / 'flat2d_v2/estat_v108/L54_G.npy', None),
}
quins = sys.argv[1:] or list(PARELLS)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
ANELLS = [(1.05, 1.5), (1.5, 2.5), (2.5, 4), (4, 6), (6, 10), (10, 30)]
SIG = [0, 1, 2, 4, 8, 16, 32]
def carrega(p, ch):
    a = np.load(p, mmap_mode='r'); img = np.asarray(a if ch is None else a[..., ch], np.float32)
    m = np.isfinite(img) & (img > 0); return np.where(m, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
fp = OUT / 'W3_INJECCIO.json'; R = json.loads(fp.read_text()) if fp.exists() else {}
for nom in quins:
    pa, pd, ch = PARELLS[nom]
    X, mx = carrega(pa, ch); Y, my = carrega(pd, ch)
    m = (mx & my & (DL > 12)).astype(np.float32); ok = cv2.erode(m, np.ones((131, 131), np.uint8)) > 0
    msh = np.roll(np.roll(ok, 53, 1), -37, 0) & ok
    g = lambda l, s: (l if s == 0 else cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6))
    res = {}; gx0 = g(X, 0); gy0 = g(Y, 0)
    for i in range(len(SIG) - 1):
        gx1 = g(X, SIG[i + 1]); gy1 = g(Y, SIG[i + 1])
        bx = (gx0 - gx1).astype(np.float32); by = (gy0 - gy1).astype(np.float32); d = by - bx
        bxs = np.roll(np.roll(bx, 53, 1), -37, 0)
        banda = f'{SIG[i]}-{SIG[i + 1]}px'; res[banda] = {}
        for r0, r1 in ANELLS:
            k = ok & (RS >= r0) & (RS < r1); ks = msh & (RS >= r0) & (RS < r1)
            if k.sum() < 5000: continue
            EX = float((bx[k].astype(np.float64) ** 2).sum()); EY = float((by[k].astype(np.float64) ** 2).sum()); ED = float((d[k].astype(np.float64) ** 2).sum())
            EXs = float((bxs[ks].astype(np.float64) ** 2).sum()); EYs = float(((bxs[ks] + d[ks]).astype(np.float64) ** 2).sum()); EDs = float((d[ks].astype(np.float64) ** 2).sum())
            res[banda][f'{r0}-{r1}'] = dict(s=round((EY - EX) / ED, 3) if ED > 0 else None, s_nul=round((EYs - EXs) / EDs, 3) if EDs > 0 else None,
                                            dE_pc=round(100 * (EY / EX - 1), 2), rms_delta_ppm=round(1e4 * np.sqrt(ED / k.sum()), 2), rms_X_ppm=round(1e4 * np.sqrt(EX / k.sum()), 2))
        gx0, gy0 = gx1, gy1; del bx, by, d, bxs
    R[nom] = res; print(nom, json.dumps(res), flush=True); fp.write_text(json.dumps(R, ensure_ascii=False, indent=1))
    del X, Y, gx0, gy0, m, ok, msh
