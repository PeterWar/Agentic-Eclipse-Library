"""m19 · La prova de la WOW: la P04 WOW del projecte (operador V95, wow_v95, paràmetres de l'etapa E2 de f3_filtres_v98: centra_rad,
iso 0,25–0,75, llindar 0,6–0,995, 8 escales, K = 0,03709) aplicada a la base_G d'ABANS (linealitzada E, la de la V104–V107) i a la del PILOT
(flat 2D), en dos retalls de càlcul amb ≥ 600 px de marge al voltant dels traços (la WOW és local: < 500 px d'abast). Les constants de
centratge per escala es mesuren a l'ABANS i es fan servir per a totes dues. Es desen els dos ràsters (retall) i se'n fa la mesura dels traços
com m17 (marca de Pere, ±60 px/±1,5°, nul de 120 segments del mateix retall a l'abans). Sortida: M19_WOW.json i wow_<retall>_{abans,despres}.npy.
Ús: m19_wow_retalls.py <base_abans.npy> <support_abans.npy> <base_despres.npy> <support_despres.npy>"""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v95_20260924')); from wow_v95 import wow_v95
fa, sa, fd, sd = sys.argv[1:5]
RETALLS = {'esquerra_dalt_T1_T2': ((0, 0, 6400, 3000), [1, 2]), 'dreta_T3_T6': ((6300, 500, 10551, 6800), [3, 4, 5, 6])}
SIG = lambda s: min(150.0, max(32.0, 4.0 * 2 ** s)); K = 0.03709
P = dict(centra_rad=True, iso=(0.25, 0.75), sig_rad=SIG, llindar=lambda s: (0.6, 0.995))
out = {}; PD = OUT / 'pilot'
for nomr, (box, trs) in RETALLS.items():
    x0, y0, x1, y1 = box; res = {}
    ws = {}
    mus = None
    for et, (fb, fs) in (('abans', (fa, sa)), ('despres', (fd, sd))):
        a = np.asarray(np.load(fb, mmap_mode='r')[y0:y1, x0:x1], np.float32); m = np.asarray(np.load(fs, mmap_mode='r')[y0:y1, x0:x1]) & np.isfinite(a) & (a > 0)
        a = np.nan_to_num(a); dmap = np.full(a.shape, 1e4, np.float32); t0 = time.time()
        q, _, mus_ = wow_v95(a, m, dmap, 8, False, log=lambda s: None, mus=mus, **P)
        if mus is None: mus = mus_
        disp = np.where(m, 0.5 + K * np.nan_to_num(q), np.nan).astype(np.float32); ws[et] = disp
        np.save(PD / f'wow_{nomr}_{et}.npy', disp); print(nomr, et, f'{time.time()-t0:.0f}s', flush=True)
    # mesura dels traços (com m17) sobre els ràsters de la WOW del retall
    def mapa_r(img):
        mm = np.isfinite(img); w = mm.astype(np.float32); img = np.where(mm, img, 0)
        ng = lambda x, s: cv2.GaussianBlur(x * w, (0, 0), s) / np.maximum(cv2.GaussianBlur(w, (0, 0), s), 1e-6)
        ok = cv2.erode(w, np.ones((81, 81), np.uint8)) > 0
        return np.where(ok, ng(img, 4) / np.maximum(ng(img, 40), 1e-12) - 1, np.nan).astype(np.float32)
    R = {et: mapa_r(ws[et]) for et in ws}
    TH = np.arange(-1.5, 1.501, 0.25); TT = np.arange(-60, 61, 2.0)
    def cerca(r, c, d, L):
        best = np.inf
        for dth in TH:
            aa = np.radians(dth); dd = np.array([d[0] * np.cos(aa) - d[1] * np.sin(aa), d[0] * np.sin(aa) + d[1] * np.cos(aa)]); nn = np.array([-dd[1], dd[0]])
            s = np.arange(-L / 2, L / 2 + 1e-6, 3.0)
            X = (c[0] + s[:, None] * dd[0] + TT[None, :] * nn[0]).astype(np.float32); Y = (c[1] + s[:, None] * dd[1] + TT[None, :] * nn[1]).astype(np.float32)
            Pp = mostreja(r, X, Y, (x0, y0)); cov = np.isfinite(Pp).mean(0)
            with np.errstate(all='ignore'): v = np.where(cov > 0.8, np.nanmean(Pp, 0), np.inf)
            best = min(best, float(np.min(v)))
        return best
    rng = np.random.default_rng(7)
    for tr in [t for t in TRACOS if t['k'] in trs]:
        c0, d0, L = tr['centre'], tr['d'], tr['llarg']; nuls = []
        while len(nuls) < 120:
            c = np.array([rng.uniform(x0 + 700, x1 - 700), rng.uniform(y0 + 700, y1 - 700)]); an = rng.uniform(0, np.pi); d = np.array([np.cos(an), np.sin(an)])
            if np.hypot(c[0] - SOL[0], c[1] - SOL[1]) < 5 * RSOL or np.hypot(*(c - c0)) < 300 + L / 2: continue
            nuls.append((c, d))
        va = cerca(R['abans'], c0, d0, L); vd = cerca(R['despres'], c0, d0, L)
        vn = np.array([cerca(R['abans'], c, d, L) for c, d in nuls]); vn = vn[np.isfinite(vn)]; med = float(np.median(vn)); mad = float(1.4826 * np.median(np.abs(vn - med)))
        pa = float((np.sum(vn <= va) + 1) / (len(vn) + 1)); pd = float((np.sum(vn <= vd) + 1) / (len(vn) + 1))
        res[tr['k']] = dict(solc_abans=va, solc_despres=vd, z_abans=(va - med) / mad, z_despres=(vd - med) / mad, p_abans=pa, p_despres=pd, nul_mediana=med, nul_mad=mad)
        print(f"WOW {nomr} T{tr['k']}: abans {va*1e4:+.0f}‱ (z {(va-med)/mad:+.1f}, p {pa:.3f}) → després {vd*1e4:+.0f}‱ (z {(vd-med)/mad:+.1f}, p {pd:.3f})", flush=True)
    # canvi global del ràster de la WOW (control): diferència absoluta mediana i al 99 %, fora dels traços
    dif = np.abs(ws['despres'] - ws['abans']); k = np.isfinite(dif)
    res['dif_WOW_p50_p99'] = np.percentile(dif[k], [50, 99]).tolist(); res['rms_WOW_abans_despres'] = [float(np.nanstd(ws['abans'])), float(np.nanstd(ws['despres']))]
    out[nomr] = dict(caixa=box, mesures=res); print(nomr, 'dif WOW p50/p99', res['dif_WOW_p50_p99'], 'rms', res['rms_WOW_abans_despres'], flush=True)
desa(OUT / 'M19_WOW.json', out)
