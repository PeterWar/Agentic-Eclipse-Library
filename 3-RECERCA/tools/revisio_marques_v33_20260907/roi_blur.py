"""Prova de la causa (B): els fotogrames llargs són més BORROSOS (moguda de la muntura dins de
l'exposició: 0,61″/s ≈ 0,28 px/s → 2,9 px als 10,3 s, 0,6 px als 2 s). Transferència relativa entre
un fotograma llarg i un de curt, per bandes de Fourier, T(λ) = Re<F_l·F_c*>/<|F_c|²>, sobre la zona
on tots dos són a l'altiplà (finestra = 1): independent del soroll (no correlat entre fotogrames).
Sector sud (az 110°), on els 10 s entren a 1,6 R☉. També la nitidesa del compost V32 dins/fora de
l'entrada dels 10 s (energia fina 3–6 px / mitjana 12–24 px)."""
import os, sys, json
from pathlib import Path
os.environ['V29_FINAL_GRID'] = '1'
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026'); sys.path.insert(0, str(ROOT / 'research/tools/v32_arcs_20260907')); from comu32 import *
import f2
OUT = ROOT / 'output/revisio_marques_v33_20260907'; VISd = OUT / 'lliurables/vistes'; REBd = OUT / '4-rebuts'
AZ = 110.0; PAIRS = [('572A2982.CR3', '572A2979.CR3'), ('572A2983.CR3', '572A2980.CR3'), ('572A2979.CR3', '572A2996.CR3'), ('572A2996.CR3', '572A3002.CR3'), ('572A2982.CR3', '572A2983.CR3'), ('572A2979.CR3', '572A2980.CR3')]
BANDS = [(3, 4), (4, 6), (6, 8), (8, 12), (12, 16), (16, 24), (24, 48), (48, 96)]


def main():
    cx0 = CX + 1.9 * RS * np.cos(np.radians(AZ)); cy0 = CY + 1.9 * RS * np.sin(np.radians(AZ)); half = 512
    x0, x1, y0, y1 = int(cx0 - half), int(cx0 + half), int(cy0 - half), int(cy0 + half); hh, ww = y1 - y0, x1 - x0
    inv = cv2.invertAffineTransform(COMMON_TO_FINAL); yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    qx = (inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]).astype(np.float32); qy = (inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]).astype(np.float32)
    path = RUNS['vixen']; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run); pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']
    dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
    need = sorted({n for p in PAIRS for n in p}); fr = {}
    for n in need:
        v = pos[n]; rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32)
        plans = ctx.plans(n, v['exp'])
        for i, (pl, w) in plans.items():
            if comu.IDX_CANAL[i] != 1:
                continue
            oy, ox = ctx.orig[i]; mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
            P = cv2.remap(pl, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); Wg = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
            fr[n] = (P, Wg >= 0.999 * v['exp'], v['exp']); break
        log(f'{n} {v["exp"]} s')
    fy = np.fft.fftfreq(hh)[:, None]; fx = np.fft.rfftfreq(ww)[None, :]; f = np.hypot(fy, fx); win = np.outer(np.hanning(hh), np.hanning(ww))
    rep = {'roi': [x0, y0, x1, y1], 'az': AZ, 'bands_px': BANDS, 'pairs': {}}
    for a, b in PAIRS:
        Pa, ma, ea = fr[a]; Pb, mb, eb = fr[b]; m = ma & mb & (Pa > 0) & (Pb > 0)
        if m.mean() < 0.25:
            rep['pairs'][f'{a[:-4]}({ea:g}s)/{b[:-4]}({eb:g}s)'] = {'frac_altipla_comu': float(m.mean()), 'nota': 'poc solapament'}; continue
        la = np.where(m, np.log(np.maximum(Pa, 1e-9)), 0); lb = np.where(m, np.log(np.maximum(Pb, 1e-9)), 0)
        wgt = m.astype(np.float32) * win; la = (la - np.mean(la[m])) * wgt; lb = (lb - np.mean(lb[m])) * wgt
        Fa = np.fft.rfft2(la); Fb = np.fft.rfft2(lb); T = []; coh = []
        for lo, hi in BANDS:
            k = (f >= 1 / hi) & (f < 1 / lo); cross = np.real(np.vdot(Fb[k], Fa[k])); pb = np.sum(np.abs(Fb[k]) ** 2); pa = np.sum(np.abs(Fa[k]) ** 2)
            T.append(float(cross / max(pb, 1e-30))); coh.append(float(cross / max(np.sqrt(pa * pb), 1e-30)))
        key = f'{a[:-4]}({ea:g}s)/{b[:-4]}({eb:g}s)'; rep['pairs'][key] = {'frac_altipla_comu': float(m.mean()), 'T_per_banda': T, 'coherencia_per_banda': coh}
        print(key, 'altiplà comú %.2f' % m.mean(), 'T:', [round(t, 2) for t in T], 'coh:', [round(c, 2) for c in coh])
    # nitidesa del compost V32 dins/fora de l'entrada dels 10 s (sector 90–130°)
    V = np.load(CAU32 / 'vixen_total_v32.npy', mmap_mode='r'); G = np.asarray(V[y0:y1, x0:x1, 1]); mm = np.isfinite(G) & (G > 0); L = np.where(mm, np.log(np.maximum(G, 1e-9)), 0)
    r = np.hypot(xx - CX, yy - CY) / RS; from scipy.ndimage import gaussian_filter
    def band(s1, s2):
        w = mm.astype(np.float32); return np.where(mm, gaussian_filter(L * w, s1) / np.maximum(gaussian_filter(w, s1), 1e-6) - gaussian_filter(L * w, s2) / np.maximum(gaussian_filter(w, s2), 1e-6), 0)
    fine = band(1.5, 3); mid = band(6, 12); rows = []
    for ra, rb in [(1.3, 1.45), (1.45, 1.58), (1.58, 1.68), (1.68, 1.8), (1.8, 1.95), (1.95, 2.1), (2.1, 2.3)]:
        k = mm & (r >= ra) & (r < rb); rows.append({'r': [ra, rb], 'rms_fi_pct': float(100 * np.sqrt(np.mean(fine[k] ** 2))), 'rms_mig_pct': float(100 * np.sqrt(np.mean(mid[k] ** 2))), 'fi_sobre_mig': float(np.sqrt(np.mean(fine[k] ** 2) / np.mean(mid[k] ** 2)))})
    rep['compost_v32_sector'] = rows; print('compost V32 sector: ', [(z['r'], round(z['fi_sobre_mig'], 3)) for z in rows])
    savejson(REBd / 'R33_roi_blur.json', rep); log('blur fet')


if __name__ == '__main__':
    main()
