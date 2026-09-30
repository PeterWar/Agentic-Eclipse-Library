"""C3 · Portes i vistes de la V33 contra la V32, mateixa vara:
  · gra per radi (rms del passa-alt fi 1,5/3 px i mitjà 6/12 px de cada capa u16) V32 vs V33;
  · anisotropia tangencial de NRGF/RHEF a l'anell de la vora del llenç (8,3–8,8 R☉) σ16/σ32;
  · vistes polars (interior 1–3, intermedi 3–6, exterior 6–10) V32 | V33 amb els traços de Pere;
  · retalls 1:1 a les finestres de marques representatives (V32 | V33).
Només lectura sobre les capes; escriu rebut i vistes."""
from comu33 import *
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(ROOT / 'research/tools/revisio_marques_v32_20260907'))
from a4_color_i_rho import ring_profile
PC32 = ROOT / 'research/tools/v32_arcs_20260907/purs/cau'; PC33 = HERE33 / 'purs/cau'; WIN = ROOT / 'research/tools/revisio_marques_v32_20260907/windows'
LAYERS = {'01': (CAU32 / '01_v32_u16.npy', CAU33 / '01_v33_u16.npy'), '02': (CAU32 / '02_v32_u16.npy', CAU33 / '02_v33_u16.npy'), '04': (CAU32 / '04_v32_u16.npy', CAU33 / '04_v33_u16.npy'),
          '05': (CAU32 / '05_v32_u16.npy', CAU33 / '05_v33_u16.npy'), '06': (CAU32 / '06_v32_u16.npy', CAU33 / '06_v33_u16.npy'),
          'P01': (PC32 / 'P01_NRGF_u16.npy', PC33 / 'P01_NRGF_u16.npy'), 'P02': (PC32 / 'P02_RHEF_u16.npy', PC33 / 'P02_RHEF_u16.npy'), 'P03': (PC32 / 'P03_MGN_u16.npy', PC33 / 'P03_MGN_u16.npy'),
          'P04': (PC32 / 'P04_WOW_u16.npy', PC33 / 'P04_WOW_u16.npy'), 'P05': (PC32 / 'P05_WOW_bilateral_u16.npy', PC33 / 'P05_WOW_bilateral_u16.npy')}
MARKS = ['L08-M01', 'L09-M03', 'L07-M02', 'L14-M05', 'L12-M01', 'L13-M02', 'L15-M08', 'L16-M01']
LAYER_OF = {'L05': '01', 'L06': '02', 'L07': '04', 'L08': '05', 'L09': '06', 'L12': 'P01', 'L13': 'P02', 'L14': 'P03', 'L15': 'P04', 'L16': 'P05'}
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'; NT = 2400


def font(n):
    return ImageFont.truetype(FONT, n)


def grain(u, m, r):
    v = np.asarray(u, np.float32) / 65535; w = m.astype(np.float32)
    def ng(a, s):
        return gaussian_filter(a * w, s) / np.maximum(gaussian_filter(w, s), 1e-6)
    fine = np.where(m, ng(v, 1.5) - ng(v, 3), 0); mid = np.where(m, ng(v, 6) - ng(v, 12), 0)
    rr, pf, _ = ring_profile(fine ** 2, m, r, 1.05, 12.0, step=0.05 * RS); _, pm, _ = ring_profile(mid ** 2, m, r, 1.05, 12.0, step=0.05 * RS)
    return rr, np.sqrt(pf), np.sqrt(pm)


def tangential(u, m, r, t, sig, a, b):
    v = np.asarray(u, np.float32) / 65535; w = m.astype(np.float32)
    def ng(x, s):
        return gaussian_filter(x * w, s) / np.maximum(gaussian_filter(w, s), 1e-6)
    band = np.where(m, ng(v, sig) - ng(v, 2 * sig), 0); gy, gx = np.gradient(band); s2 = 1.5 * sig
    Jxx = gaussian_filter(gx * gx, s2); Jyy = gaussian_filter(gy * gy, s2); Jxy = gaussian_filter(gx * gy, s2)
    proj = (Jxx - Jyy) * np.cos(2 * t) + 2 * Jxy * np.sin(2 * t); E = Jxx + Jyy; k = m & (r >= a * RS) & (r < b * RS)
    return float(np.sum(proj[k]) / max(np.sum(E[k]), 1e-20))


def polar_u8(u, m, r0, r1, sigma):
    v = np.asarray(u, np.float32) / 65535; w = m.astype(np.float32); hp = np.where(m, v - gaussian_filter(v * w, sigma) / np.maximum(gaussian_filter(w, sigma), 1e-6), np.nan)
    rv = np.arange(r0 * RS, r1 * RS, 1.0, dtype=np.float32); th = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32)
    X = (CX + rv[:, None] * np.cos(th)[None, :]).astype(np.float32); Y = (CY + rv[:, None] * np.sin(th)[None, :]).astype(np.float32)
    pol = cv2.remap(np.nan_to_num(hp), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); pm = cv2.remap(np.isfinite(hp).astype(np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.99
    z = pol[pm]; sc = float(np.percentile(np.abs(z), 98)) if z.size else 1
    u8 = np.uint8(np.clip(0.5 + pol / (2 * sc), 0, 1) * 255); u8[~pm] = 40
    return u8, sc


def main():
    r, t = coords(); m = np.load(CAU32 / 'support_v32.npy')
    cat = {x['id']: x for x in json.loads((ROOT / 'output/revisio_marques_v32_20260907/4-rebuts/review_catalog.json').read_text())['marks']}
    rep = {'gra': {}, 'tangencial_vora_llenc': {}, 'retalls': []}
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(5, 2, figsize=(12, 15), sharex=True); axs = axs.ravel()
    for i, (k, (p32, p33)) in enumerate(LAYERS.items()):
        u32 = np.load(p32, mmap_mode='r'); u33 = np.load(p33, mmap_mode='r')
        rr, f32, m32 = grain(u32, m, r); _, f33, m33 = grain(u33, m, r)
        rep['gra'][k] = {'r': rr.tolist(), 'fi_v32': f32.tolist(), 'fi_v33': f33.tolist(), 'mig_v32': m32.tolist(), 'mig_v33': m33.tolist()}
        ax = axs[i]; ax.semilogy(rr, f32, 'r', lw=.8, label='fi V32'); ax.semilogy(rr, f33, 'r--', lw=.8, label='fi V33'); ax.semilogy(rr, m32, 'b', lw=.8, label='mig V32'); ax.semilogy(rr, m33, 'b--', lw=.8, label='mig V33'); ax.set_title(k, fontsize=9); ax.legend(fontsize=7)
        if k in ('P01', 'P02'):
            rep['tangencial_vora_llenc'][k] = {f'σ{s}': {'V32': tangential(u32, m, r, t, s, 8.3, 8.8), 'V33': tangential(u33, m, r, t, s, 8.3, 8.8)} for s in (16, 32)}
        log(f'gra {k}: fi a 4 R V32 {np.interp(4, rr, f32):.4f} → V33 {np.interp(4, rr, f33):.4f}; mig {np.interp(4, rr, m32):.4f} → {np.interp(4, rr, m33):.4f}')
    fig.tight_layout(); fig.savefig(VIS33 / 'C3_gra_per_radi_V32_V33.png', dpi=110); plt.close(fig)
    # polars V32 | V33 per capa (tres trams)
    for k, (p32, p33) in LAYERS.items():
        u32 = np.load(p32, mmap_mode='r'); u33 = np.load(p33, mmap_mode='r')
        for tram, (r0, r1), sg in [('interior', (1.0, 3.0), 12), ('intermedi', (3.0, 6.0), 24), ('exterior', (6.0, 10.0), 32)]:
            a32, s32 = polar_u8(u32, m, r0, r1, sg); a33, s33 = polar_u8(u33, m, r0, r1, sg)
            nr = a32.shape[0]; im = Image.new('L', (NT + 60, 2 * (nr + 24)), 30); d = ImageDraw.Draw(im)
            for j, (a, s, lab) in enumerate([(a32, s32, 'V32'), (a33, s33, 'V33')]):
                im.paste(Image.fromarray(a), (60, j * (nr + 24) + 24)); d.text((64, j * (nr + 24) + 4), f'{k} {lab} · passa-alt σ{sg} · ±{s:.4f} u · r {r0}–{r1} R☉ amunt→avall · azimut −180…180°', fill=255, font=font(13))
                for rr_ in np.arange(np.ceil(r0 * 2) / 2, r1, 0.5):
                    yy = int((rr_ - r0) * RS); d.text((2, j * (nr + 24) + 24 + yy - 6), f'{rr_:.1f}', fill=200, font=font(11))
            im.save(VIS33 / f'C3_polar_{k}_{tram}.png')
        log(f'polar {k}')
    # retalls 1:1 a marques
    for mid in MARKS:
        mk = cat[mid]; k = LAYER_OF[mid[:3]]; x0, y0, x1, y1 = mk['window_bbox']
        if (x1 - x0) * (y1 - y0) > 1800 * 1800:
            cx, cy = int(mk['center_xy'][0]), int(mk['center_xy'][1]); x0, y0, x1, y1 = max(cx - 700, 0), max(cy - 700, 0), min(cx + 700, W), min(cy + 700, H)
        p32, p33 = LAYERS[k]; a32 = (np.load(p32, mmap_mode='r')[y0:y1, x0:x1] // 257).astype(np.uint8); a33 = (np.load(p33, mmap_mode='r')[y0:y1, x0:x1] // 257).astype(np.uint8)
        codes = np.load(WIN / (mid + '_codes.npy')); wx0, wy0, wx1, wy1 = mk['window_bbox']; pm = np.zeros(a32.shape, bool)
        ya, yb, xa, xb = max(wy0, y0), min(wy1, y1), max(wx0, x0), min(wx1, x1); pm[ya - y0:yb - y0, xa - x0:xb - x0] = codes[ya - wy0:yb - wy0, xa - wx0:xb - wx0] > 0
        edge = cv2.morphologyEx(pm.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
        panels = []
        for a, lab in ((a32, 'V32'), (a33, 'V33')):
            rgb = np.stack([a, a, a], -1); rgb[edge] = (200, 60, 255); im = Image.fromarray(rgb); im.thumbnail((1000, 1000), Image.Resampling.LANCZOS); panels.append((im, lab))
        wtot = sum(p.width for p, _ in panels) + 30; ht = max(p.height for p, _ in panels) + 30; sheet = Image.new('RGB', (wtot, ht), (24, 24, 24)); d = ImageDraw.Draw(sheet); xx = 10
        for p, lab in panels:
            sheet.paste(p, (xx, 26)); d.text((xx, 6), f'{mid} · {mk["layer"][:28]} · {lab} · {x1 - x0}×{y1 - y0} px', fill='white', font=font(14)); xx += p.width + 10
        sheet.save(VIS33 / f'C3_retall_{mid}_{k}.png'); rep['retalls'].append({'id': mid, 'layer': k, 'box': [x0, y0, x1, y1]})
    savejson(REB33 / 'C3_portes.json', rep); log('C3 fet')


if __name__ == '__main__':
    main()
