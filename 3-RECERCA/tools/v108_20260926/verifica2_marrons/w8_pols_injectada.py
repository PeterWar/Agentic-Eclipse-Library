"""w8 (verificador adversari 2) · POLS DELS FLATS: la cura treu una ombra que hi era, o n'afegeix la inversa on no n'hi havia?
1. Troba els discos compactes del canvi a l'apilat de la Vixen (ln després/abans suavitzat σ10 menys σ60; màxims locals |x| > 0,15 %, separats 150 px).
2. Per a cada disc: E = mitjana r < 35 px − anell 70–110 px, a l'apilat ABANS (E_abans) i al CANVI (Δ). Si la pols era a les llums, E_abans ≈ −Δ
   (la cura la treu); si no hi era, E_abans ≈ 0 i després queda un disc +Δ (injecció). Nul: la mateixa E_abans a 60 posicions a l'atzar
   a la mateixa distància del Sol (±10 %), a la mateixa imatge. Fracció curada f = −E_abans/Δ (1 = cura, 0 = injecció).
3. El mateix a la base (on el disc de la Vixen hi arriba segons el pes de la fusió).
Sortida: W8_POLS_INJECTADA.json"""
import json
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica2_marrons'
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; CAD = A / '4-RESULTATS/v108_20260926/cadena'; CR = A / '4-RESULTATS/v97_refundacio_20260924'
W, H = 10551, 7506; SOL = np.array([5361.768, 3775.748]); RSOL = 440.603
def ld(p, ch):
    a = np.load(p, mmap_mode='r'); return np.asarray(a if ch is None else a[..., ch], np.float32)
def lnm(x):
    m = (np.isfinite(x) & (x > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(x, 1e-12)), 0).astype(np.float32), m
def ng(l, m, s): return cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
va, ma = lnm(ld(CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', 1)); vb, mb = lnm(ld(F2 / 'apilats/vixen_total.npy', 1)); m = ma * mb
d = np.where(m > 0, vb - va, 0).astype(np.float32); dd = ng(d, m, 10) - ng(d, m, 60)
ok = cv2.erode(m, np.ones((251, 251), np.uint8)) > 0
yy, xx = np.mgrid[0:H, 0:W]; rs = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; ok &= rs > 1.6; del yy, xx
mx = cv2.dilate(np.abs(dd), np.ones((151, 151), np.uint8)); pk = ok & (np.abs(dd) == mx) & (np.abs(dd) > 0.0015)
ys, xs = np.nonzero(pk); print('discos candidats', len(ys), flush=True)
ba, mba = lnm(ld(CAD / 'control/lineal/base_G.npy', None)); bb, mbb = lnm(ld(CAD / 'flat2d_v2/lineal/base_G.npy', None))
yy, xx = np.mgrid[-120:121, -120:121]; rr = np.hypot(yy, xx); DISC = rr < 35; ANELL = (rr >= 70) & (rr < 110)
def E(l, mk, x, y):
    t = l[y - 120:y + 121, x - 120:x + 121]; k = mk[y - 120:y + 121, x - 120:x + 121] > 0
    if t.shape != rr.shape or (k & DISC).sum() < 0.9 * DISC.sum() or (k & ANELL).sum() < 0.9 * ANELL.sum(): return np.nan
    return float(1e4 * (t[k & DISC].mean() - t[k & ANELL].mean()))
rng = np.random.default_rng(7); R = []
for y, x in zip(ys, xs):
    r0 = np.hypot(x - SOL[0], y - SOL[1]); nul = []
    for _ in range(400):
        if len(nul) >= 60: break
        ang = rng.uniform(0, 2 * np.pi); rr_ = r0 * rng.uniform(0.9, 1.1); cx, cy = int(SOL[0] + rr_ * np.cos(ang)), int(SOL[1] + rr_ * np.sin(ang))
        if 130 < cx < W - 130 and 130 < cy < H - 130 and ok[cy, cx]:
            v = E(va, m, cx, cy)
            if np.isfinite(v): nul.append(v)
    ea = E(va, m, x, y); eb = E(vb, m, x, y); de = eb - ea; nul = np.array(nul)
    bea = E(ba, mba * mbb, x, y); beb = E(bb, mba * mbb, x, y)
    o = dict(x=int(x), y=int(y), R_sol=round(r0 / RSOL, 2), senyal_dd_pc=round(100 * float(dd[y, x]), 3), vixen_E_abans_ppm=round(ea, 1), vixen_E_despres_ppm=round(eb, 1), vixen_canvi_ppm=round(de, 1),
             fraccio_curada=(round(-ea / de, 2) if abs(de) > 1 else None), nul_E_abans_sd_ppm=round(float(nul.std()), 1), z_abans=round(float((ea - nul.mean()) / nul.std()), 2), z_despres=round(float((eb - nul.mean()) / nul.std()), 2),
             base_E_abans_ppm=round(bea, 1), base_E_despres_ppm=round(beb, 1))
    R.append(o); print(o, flush=True)
(OUT / 'W8_POLS_INJECTADA.json').write_text(json.dumps(R, ensure_ascii=False, indent=1))
