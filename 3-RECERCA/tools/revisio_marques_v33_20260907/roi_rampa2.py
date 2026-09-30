"""Prova del remei a l'origen: ROI Vixen recomposta COM LA V32 (k, offsets c03, camps φ de B1) amb
tres finestres de sostre: actual (lineal 70→85 % sat), gradual (smoothstep 35→85 %) i gradual2
(smoothstep 25→85 %). Mesura: perfil de soroll fi (calaixos de 4 px) i AMPLADA del graó a l'entrada
dels 10 s (radi on el rms passa del 90 al 10 % del salt); fracció de pes dels 10 s en funció de r;
MGN de cada variant. Dos sectors."""
import os, sys, json
from pathlib import Path
os.environ['V29_FINAL_GRID'] = '1'
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026'); sys.path.insert(0, str(ROOT / 'research/tools/v32_arcs_20260907')); from comu32 import *
import f2
from b2_recomposicio import upsample
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont
OUT = ROOT / 'output/revisio_marques_v33_20260907'; VISd = OUT / 'lliurables/vistes'; REBd = OUT / '4-rebuts'
R0, R1 = 1.05, 2.5
def sm(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
RAMPES = {'actual_70_85': lambda f, alt: np.clip((alt - f) / (0.18 * alt), 0, 1), 'gradual_35_85': lambda f, alt: 1 - sm(f, 0.35 / 0.85 * alt, alt), 'gradual_25_85': lambda f, alt: 1 - sm(f, 0.25 / 0.85 * alt, alt)}


def finestra_factory(ramp):
    def finestra(f, t, sat, ped):
        alt = f2.SOSTRE * (sat - ped); w = np.clip((f - f2.TERRA_DN) / (3.0 * f2.TERRA_DN), 0.0, 1.0); w *= ramp(f, alt); return (w * t).astype(np.float32)
    return finestra


def ng_(a, m, s_):
    k = 2 * int(3 * s_ + .5) + 1; den_ = cv2.GaussianBlur(m.astype(np.float32), (k, k), s_, borderType=cv2.BORDER_REPLICATE)
    return cv2.GaussianBlur(np.where(m, a, 0).astype(np.float32), (k, k), s_, borderType=cv2.BORDER_REPLICATE) / np.maximum(den_, 1e-20)


def mgn(a, m, sigmas=(1.25, 2.5, 5, 10, 20, 40), k=.7, h=.7, gamma=3.2, limits=None):
    lo, hi = limits; detail = np.zeros_like(a, dtype='float32')
    for s_ in sigmas:
        mu = ng_(a, m, s_); d = a - mu; den_ = np.sqrt(ng_(d * d, m, s_)); z = np.divide(d, den_, out=np.zeros_like(d), where=den_ > 0); detail += np.arctan(k * z) / len(sigmas)
    return h * np.clip((a - lo) / (hi - lo), 0, 1) ** (1 / gamma) + (1 - h) * detail


def main():
    path = RUNS['vixen']; run = comu.Run.obre(str(path)); ctx = f2.Ctx(run); pos = json.loads((path / '4-rebuts/F1.3_registre.json').read_text())['fotogrames']; kq = json.loads((path / '4-rebuts/F2.2_coherencia.json').read_text())['k']
    meta = {m['name']: m for m in json.loads((CAU32 / 'vixen_meta.json').read_text())['frames']}; b1 = json.loads((ROOT / 'output/v32_arcs_20260907/4-rebuts/B1_camps_vixen.json').read_text())['frames']; phi = np.load(CAU32 / 'vixen_G_phi.npy', mmap_mode='r')
    inv = cv2.invertAffineTransform(COMMON_TO_FINAL); orig = f2.finestra; rep = {'rampes': list(RAMPES), 'sectors': {}}
    F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14)
    for AZ in (-50.0, 110.0):
        cx0 = CX + 1.75 * RS * np.cos(np.radians(AZ)); cy0 = CY + 1.75 * RS * np.sin(np.radians(AZ)); half = 640
        x0, x1, y0, y1 = int(cx0 - half), int(cx0 + half), int(cy0 - half), int(cy0 + half); hh, ww = y1 - y0, x1 - x0
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); qx = (inv[0, 0] * xx + inv[0, 1] * yy + inv[0, 2]).astype(np.float32); qy = (inv[1, 0] * xx + inv[1, 1] * yy + inv[1, 2]).astype(np.float32); dx = (qx - ctx.CX) * ctx.k; dy = (qy - ctx.CY) * ctx.k
        r = np.hypot(xx - CX, yy - CY); t = np.degrees(np.arctan2(yy - CY, xx - CX)); sect = (t >= AZ - 25) & (t <= AZ + 25)
        num = {k: np.zeros((hh, ww), np.float32) for k in RAMPES}; den = {k: np.zeros((hh, ww), np.float32) for k in RAMPES}; w10 = {k: np.zeros((hh, ww), np.float32) for k in RAMPES}
        for n in sorted(pos):
            v = pos[n]; k = kq.get(n, 1.0); rx = (ctx.ca * dx + ctx.sa * dy + v['sol_x']).astype(np.float32); ry = (-ctx.sa * dx + ctx.ca * dy + v['sol_y']).astype(np.float32); fl = f2.mascara_lluna(ctx, v, rx, ry)
            ph = upsample(np.asarray(phi[b1.index(n)]))[y0:y1, x0:x1] if n in b1 else 0.0; b = float(meta[n]['offset_RGB'][1])
            for key, ramp in RAMPES.items():
                f2.finestra = finestra_factory(ramp); plans = ctx.plans(n, v['exp'])
                for i, (pl, w) in plans.items():
                    if comu.IDX_CANAL[i] != 1:
                        continue
                    oy, ox = ctx.orig[i]; mx = ((rx - ox) * .5).astype(np.float32); my = ((ry - oy) * .5).astype(np.float32)
                    dd = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl; nn = cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) * fl
                    nn = (nn + b * dd) * np.exp(-ph); num[key] += nn; den[key] += dd
                    if v['exp'] >= 9:
                        w10[key] += dd
            f2.finestra = orig
        secrep = {}; panels = []
        for key in RAMPES:
            G = np.where(den[key] > 0, num[key] / np.maximum(den[key], 1e-20), np.nan); m = np.isfinite(G) & (G > 0) & (r > 1.02 * RS); L = np.where(m, np.log(np.maximum(G, 1e-9)), 0).astype(np.float32)
            fine = np.where(m, ng_(L, m, 1.5) - ng_(L, m, 3.0), 0); ri = np.floor((r - R0 * RS) / 4).astype(int); nb = int((R1 - R0) * RS / 4); kk = m & sect & (ri >= 0) & (ri < nb)
            cnt = np.bincount(ri[kk], minlength=nb); prof = np.where(cnt > 20, np.sqrt(np.bincount(ri[kk], weights=fine[kk] ** 2, minlength=nb) / np.maximum(cnt, 1)), np.nan); rr = R0 + (np.arange(nb) + .5) * 4 / RS
            f10 = np.where(cnt > 20, np.bincount(ri[kk], weights=(w10[key] / np.maximum(den[key], 1e-20))[kk], minlength=nb) / np.maximum(cnt, 1), np.nan)
            # amplada de l'entrada dels 10 s: r on f10 passa de 0,1 a 0,9 del seu màxim; i amplada del graó de soroll: r on el rms (suavitzat 3 calaixos) passa del 90 % al 10 % del salt entre els altiplans
            g = np.isfinite(f10); fm = np.nanmax(f10); r10 = rr[g & (f10 >= 0.1 * fm)]; r90 = rr[g & (f10 >= 0.9 * fm)]
            ent = (float(r10.min()), float(r90.min())) if r10.size and r90.size else (None, None)
            ps = np.convolve(np.nan_to_num(prof), np.ones(3) / 3, mode='same'); hi_ = np.nanmedian(ps[(rr > ent[0] - 0.25) & (rr < ent[0] - 0.05)]) if ent[0] else np.nan; lo_ = np.nanmedian(ps[(rr > ent[1] + 0.05) & (rr < ent[1] + 0.25)]) if ent[1] else np.nan
            wstep = None
            if np.isfinite(hi_) and np.isfinite(lo_) and hi_ > lo_:
                a90 = rr[(ps <= hi_ - 0.1 * (hi_ - lo_)) & (rr > ent[0] - 0.25)]; a10 = rr[(ps <= lo_ + 0.1 * (hi_ - lo_)) & (rr > ent[0] - 0.25)]
                wstep = float((a10.min() - a90.min()) * RS) if a90.size and a10.size else None
            secrep[key] = {'r': rr.tolist(), 'rms_fi_pct': (100 * np.nan_to_num(prof)).tolist(), 'f10': np.nan_to_num(f10).tolist(), 'entrada_10s_r10_r90': ent, 'amplada_entrada_px': (ent[1] - ent[0]) * RS if ent[0] else None, 'rms_abans_pct': 100 * float(hi_), 'rms_despres_pct': 100 * float(lo_), 'amplada_graó_soroll_px': wstep}
            gm = np.maximum(np.nan_to_num(G), 0); out = mgn(gm, m, limits=[float(gm[m].min()), float(gm[m].max())]); lo2, hi2 = np.percentile(out[m], [0.5, 99.5]); u = np.uint8(np.clip((out - lo2) / (hi2 - lo2), 0, 1) * 255); u[~m] = 0; panels.append((key, u))
            log(f"az {AZ} {key}: entrada 10 s {ent} ({secrep[key]['amplada_entrada_px'] and round(secrep[key]['amplada_entrada_px'])} px) · rms {100*hi_:.3f}→{100*lo_:.3f} % · amplada graó soroll {wstep and round(wstep)} px")
        rep['sectors'][str(AZ)] = secrep
        im = Image.new('L', (3 * ww + 40, hh + 30), 30); d = ImageDraw.Draw(im)
        for i, (key, u) in enumerate(panels):
            im.paste(Image.fromarray(u), (10 + i * (ww + 10), 28)); d.text((10 + i * (ww + 10), 6), f'MGN · Vixen ROI az {AZ}° amb k, offsets i φ (com V32) · rampa {key}', fill=255, font=F)
        im.save(VISd / f'ROI2_rampa_MGN_az{int(AZ)}.png')
    savejson(REBd / 'R33_roi_rampa2.json', rep); log('ROI2 fet')


if __name__ == '__main__':
    main()
