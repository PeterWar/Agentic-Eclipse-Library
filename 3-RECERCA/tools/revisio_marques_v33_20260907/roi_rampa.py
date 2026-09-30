"""Prova de la causa (A): recomposició d'un sector de la Vixen (ROI a la graella final) amb la rampa
de sostre actual (70→85 % sat, entrada dels fotogrames en 16–48 px) i amb una rampa AMPLA (45→85 %),
mateix registre, mateixos flats, mateixa màscara lunar, mateixos guanys k. Mesura: perfil radial del
soroll fi (DoG 1,5/3 en ln G) per calaixos de 4 px; MGN (codi v31_purs) sobre les dues ROI; vista.
Hipòtesi: el graó de soroll a l'entrada de cada fotograma és la costura que MGN/WOW dibuixen."""
import os, sys, json
from pathlib import Path
os.environ['V29_FINAL_GRID'] = '1'
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026')
sys.path.insert(0, str(ROOT / 'research/tools/v32_arcs_20260907')); from comu32 import *
import f2
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont
OUT = ROOT / 'output/revisio_marques_v33_20260907'; VISd = OUT / 'lliurables/vistes'; REBd = OUT / '4-rebuts'
AZ, R0, R1 = -50.0, 1.05, 2.4      # sector de les marques L08-M04 / L09-M10 / L09-M08 (az −80…−20)
RAMPES = {'actual_70_85': 0.18, 'ampla_45_85': 0.47}   # fracció d'alt sobre la qual cau la rampa: alt·(1−x)…alt


def finestra_factory(frac):
    def finestra(f, t, sat, ped):
        alt = f2.SOSTRE * (sat - ped)
        w = np.clip((f - f2.TERRA_DN) / (3.0 * f2.TERRA_DN), 0.0, 1.0)
        w *= np.clip((alt - f) / (frac * alt), 0.0, 1.0)
        return (w * t).astype(np.float32)
    return finestra


def main():
    cx0 = CX + 1.7 * RS * np.cos(np.radians(AZ)); cy0 = CY + 1.7 * RS * np.sin(np.radians(AZ)); half = 620
    x0, x1, y0, y1 = int(cx0 - half), int(cx0 + half), int(cy0 - half), int(cy0 + half); hh, ww = y1 - y0, x1 - x0
    inv = cv2.invertAffineTransform(COMMON_TO_FINAL); yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    qx = (inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]).astype(np.float32); qy = (inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]).astype(np.float32)
    path = RUNS['vixen']; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run)
    pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
    dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
    num = {k: np.zeros((hh, ww), np.float32) for k in RAMPES}; den = {k: np.zeros((hh, ww), np.float32) for k in RAMPES}
    names = sorted(pos); orig_finestra = f2.finestra
    for j, n in enumerate(names):
        v = pos[n]; k = kq.get(n, 1.0)
        rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32)
        fl = f2.mascara_lluna(ctx, v, rx, ry)
        for key, frac in RAMPES.items():
            f2.finestra = finestra_factory(frac)
            plans = ctx.plans(n, v['exp'])
            for i, (pl, w) in plans.items():
                if comu.IDX_CANAL[i] != 1:
                    continue
                oy, ox = ctx.orig[i]; mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
                dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl; nn = cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
                num[key] += nn; den[key] += dd
        f2.finestra = orig_finestra
        if j % 10 == 0:
            log(f'{j + 1}/{len(names)} {n}')
    r = np.hypot(xx - CX, yy - CY); t = np.degrees(np.arctan2(yy - CY, xx - CX)); sect = (t >= AZ - 28) & (t <= AZ + 28)
    rep = {'roi': [x0, y0, x1, y1], 'az': AZ, 'rampes': RAMPES, 'perfils': {}}
    def ng_(a, m, s_):
        k = 2 * int(3 * s_ + .5) + 1; den_ = cv2.GaussianBlur(m.astype(np.float32), (k, k), s_, borderType=cv2.BORDER_REPLICATE)
        return cv2.GaussianBlur(np.where(m, a, 0).astype(np.float32), (k, k), s_, borderType=cv2.BORDER_REPLICATE) / np.maximum(den_, 1e-20)
    def mgn(a, m, sigmas=(1.25, 2.5, 5, 10, 20, 40), k=.7, h=.7, gamma=3.2, limits=None):   # còpia literal de v31_purs/local_filters.mgn
        lo, hi = limits; detail = np.zeros_like(a, dtype='float32')
        for s_ in sigmas:
            mu = ng_(a, m, s_); d = a - mu; d[np.abs(d) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(a), np.abs(mu))] = 0
            den_ = np.sqrt(ng_(d * d, m, s_)); z = np.divide(d, den_, out=np.zeros_like(d), where=den_ > 0); detail += np.arctan(k * z) / len(sigmas)
        return h * np.clip((a - lo) / (hi - lo), 0, 1) ** (1 / gamma) + (1 - h) * detail
    panels = []
    for key in RAMPES:
        G = np.where(den[key] > 0, num[key] / np.maximum(den[key], 1e-20), np.nan); m = np.isfinite(G) & (G > 0) & (r > 1.02 * RS)
        L = np.where(m, np.log(np.maximum(G, 1e-9)), 0).astype(np.float32); w = m.astype(np.float32)
        fine = np.where(m, gaussian_filter(L * w, 1.5) / np.maximum(gaussian_filter(w, 1.5), 1e-6) - gaussian_filter(L * w, 3) / np.maximum(gaussian_filter(w, 3), 1e-6), 0)
        ri = np.floor((r - R0 * RS) / 4).astype(int); nb = int((R1 - R0) * RS / 4); k = m & sect & (ri >= 0) & (ri < nb)
        cnt = np.bincount(ri[k], minlength=nb); s2 = np.bincount(ri[k], weights=fine[k] ** 2, minlength=nb); prof = np.where(cnt > 20, np.sqrt(s2 / np.maximum(cnt, 1)), np.nan); rr = R0 + (np.arange(nb) + .5) * 4 / RS
        # graó màxim en 12 px i suma de |Δ log rms| (rugositat del perfil)
        g = np.isfinite(prof); lp = np.log(prof[g]); jumps = np.abs(lp[3:] - lp[:-3]); rough = float(np.nansum(np.abs(np.diff(lp))))
        rep['perfils'][key] = {'r': rr[g].tolist(), 'rms_fi_pct': (100 * prof[g]).tolist(), 'graó_max_12px': float(np.exp(jumps.max())), 'r_graó_max': float(rr[g][3 + int(jumps.argmax())]), 'rugositat_sum_abs_dlog': rough, 'n_frames_median': None}
        gm = np.maximum(np.nan_to_num(G), 0); out = mgn(gm, m, limits=[float(gm[m].min()), float(gm[m].max())]); np.save(REBd / f'roi_mgn_{key}.npy', out.astype(np.float32)); np.save(REBd / f'roi_G_{key}.npy', G.astype(np.float32))
        lo_, hi_ = np.percentile(out[m], [0.5, 99.5]); u = np.uint8(np.clip((out - lo_) / (hi_ - lo_), 0, 1) * 255); u[~m] = 0; panels.append((key, u))
        log(f"{key}: graó màx 12 px {rep['perfils'][key]['graó_max_12px']:.2f} a {rep['perfils'][key]['r_graó_max']:.2f} R · rugositat {rough:.2f}")
    F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14); im = Image.new('L', (2 * ww + 30, hh + 30), 30); d = ImageDraw.Draw(im)
    for i, (key, u) in enumerate(panels):
        im.paste(Image.fromarray(u), (10 + i * (ww + 10), 28)); d.text((10 + i * (ww + 10), 6), f'MGN sobre la ROI Vixen · rampa {key} · az {AZ}° · r {R0}–{R1}', fill=255, font=F)
    im.save(VISd / 'ROI_rampa_MGN_actual_vs_ampla.png')
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(9, 3.5))
    for key in RAMPES:
        ax.plot(rep['perfils'][key]['r'], rep['perfils'][key]['rms_fi_pct'], lw=.9, label=f"rampa {key}")
    for r_ in (1.21, 1.33, 1.47, 1.96):
        ax.axvline(r_, color='.5', lw=.5, ls='--')
    ax.set_xlabel('r [R☉]'); ax.set_ylabel('gra fi rms [%]'); ax.set_yscale('log'); ax.legend(fontsize=8); ax.set_title(f'Soroll fi del compost Vixen al sector az {AZ}°: rampa actual (70→85 % sat) contra ampla (45→85 %)', fontsize=9)
    fig.tight_layout(); fig.savefig(VISd / 'ROI_rampa_perfil_soroll.png', dpi=120)
    savejson(REBd / 'R33_roi_rampa.json', rep); log('ROI fet')


if __name__ == '__main__':
    main()
