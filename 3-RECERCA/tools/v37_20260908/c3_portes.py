"""C3 (V37) · Portes V36 → V37 al limbe, mateixa vara: per capa ACHF (01/02/04/05/06) saturació de la tanh i estructura (std) per anell
1,00–1,20; per P03/P04/P05 el rivet a la vora del forat per sector (mitjana 0–8 px − 20–40 px, en σ) i el biaix d'anell 1,03–1,3;
H1 de la B4a; gra fi a 4 R☉ (no ha de canviar); vista polar del limbe de totes les capes V36|V37; retalls a les marques de Pere de la V36."""
from comu37 import *
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(ROOT / 'research/tools/revisio_marques_v32_20260907'))
from a4_color_i_rho import ring_profile
PC36 = HERE36 / 'purs/cau'; PC37 = HERE37 / 'purs/cau'; WIN36 = ROOT / 'research/tools/revisio_marques_v36_20260908/windows'
LAYERS = {'01': (CAU36 / '01_v36_u16.npy', CAU37 / '01_v37_u16.npy'), '02': (CAU36 / '02_v36_u16.npy', CAU37 / '02_v37_u16.npy'), '04': (CAU36 / '04_v36_u16.npy', CAU37 / '04_v37_u16.npy'),
          '05': (CAU36 / '05_v36_u16.npy', CAU37 / '05_v37_u16.npy'), '06': (CAU36 / '06_v36_u16.npy', CAU37 / '06_v37_u16.npy'),
          'P01': (PC36 / 'P01_NRGF_u16.npy', PC37 / 'P01_NRGF_u16.npy'), 'P02': (PC36 / 'P02_RHEF_u16.npy', PC37 / 'P02_RHEF_u16.npy'), 'P03': (PC36 / 'P03_MGN_u16.npy', PC37 / 'P03_MGN_u16.npy'),
          'P04': (PC36 / 'P04_WOW_u16.npy', PC37 / 'P04_WOW_u16.npy'), 'P05': (PC36 / 'P05_WOW_bilateral_u16.npy', PC37 / 'P05_WOW_bilateral_u16.npy')}
LAYER_OF = {'L01': '01', 'L02': '02', 'L03': '04', 'L04': '05', 'L05': '06', 'L06': 'P01', 'L07': 'P02', 'L08': 'P03', 'L09': 'P04', 'L10': 'P05'}
MARKS = ['L01-M01', 'L01-M03', 'L05-M01', 'L06-M02', 'L07-M02', 'L08-M01', 'L08-M02', 'L09-M02', 'L10-M02', 'L10-M03']
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'; NT = 2400; NB = 24


def font(n):
    return ImageFont.truetype(FONT, n)


def main():
    r, t = coords(); m = np.load(CAU36 / 'support_v36.npy'); w = m.astype(np.float32)
    Y0, Y1, X0, X1 = int(CY - 1.4 * RS), int(CY + 1.4 * RS), int(CX - 1.4 * RS), int(CX + 1.4 * RS); rr = r[Y0:Y1, X0:X1] / RS; tt = np.degrees(t[Y0:Y1, X0:X1]); mm = m[Y0:Y1, X0:X1]
    G = np.asarray(np.load(CAU36 / 'base_G_v36.npy', mmap_mode='r')[Y0:Y1, X0:X1]); mm = mm & (G > 0); dist = cv2.distanceTransform(mm.astype(np.uint8), cv2.DIST_L2, 5); sec = np.floor((tt + 180) / 360 * NB).astype(int) % NB
    rec = json.loads((CAUF / 'refined_detail_receipt.json').read_text()); fv = json.loads((ROOT / 'research/tools/v30/cau/fine_variants_receipt.json').read_text())
    scales = {'01': rec['filters']['achf']['scale_tanh'], '02': rec['filters']['passalt24']['scale_tanh'], '04': fv['variants']['micro1_16']['scale_tanh'], '05': fv['variants']['fi2_48']['scale_tanh'], '06': fv['variants']['estructura4_64']['scale_tanh']}
    rs = np.arange(1.0, 1.2, 0.01); rep = {'limbe_cadena': {}, 'rivet_purs': {}, 'gra_4R': {}, 'H1': {}}
    b4_36 = json.loads((REB36 / 'B4a_capes_cadena.json').read_text()); b4_37 = json.loads((REB37 / 'B4a_capes_cadena.json').read_text())
    for k in ('01', '02', '04', '05', '06'):
        row = {}
        for lab, C, suf in (('V36', CAU36, 'v36'), ('V37', CAU37, 'v37')):
            raw = np.asarray(np.load(C / f'{k}_{suf}_raw.npy', mmap_mode='r')[Y0:Y1, X0:X1]); u = np.asarray(np.load(C / f'{k}_{suf}_u16.npy', mmap_mode='r')[Y0:Y1, X0:X1], np.float32) / 65535; sc = scales[k]
            sat = []; std = []
            for a0 in rs:
                kk = mm & (rr >= a0) & (rr < a0 + 0.01) & np.isfinite(raw); sat.append(float(np.mean(np.abs(np.tanh(raw[kk] / sc)) > 0.95))); std.append(float(np.std(u[kk])))
            r50 = float(np.interp(0.5, np.array(sat)[::-1], rs[::-1])) if min(sat) < 0.5 else None
            row[lab] = {'r': rs.round(2).tolist(), 'saturacio': sat, 'std': std, 'r_on_saturacio_cau_a_0.5': r50, 'H1': (b4_36 if lab == 'V36' else b4_37)['capes'][k]['H1']['worst']}
        rep['limbe_cadena'][k] = row; rep['H1'][k] = {'V36': row['V36']['H1'], 'V37': row['V37']['H1']}
        log(f"{k}: saturació 50 % a r {row['V36']['r_on_saturacio_cau_a_0.5']} → {row['V37']['r_on_saturacio_cau_a_0.5']} · std a 1,03: {row['V36']['std'][3]:.3f} → {row['V37']['std'][3]:.3f} · H1 pitjor {row['V36']['H1']['error']:.4f}@{row['V36']['H1']['R']:.3f} → {row['V37']['H1']['error']:.4f}@{row['V37']['H1']['R']:.3f}")
    for k in ('P03', 'P04', 'P05', 'P01', 'P02'):
        row = {}
        for lab, P in (('V36', PC36), ('V37', PC37)):
            name = {'P03': 'P03_MGN', 'P04': 'P04_WOW', 'P05': 'P05_WOW_bilateral', 'P01': 'P01_NRGF', 'P02': 'P02_RHEF'}[k]; v = np.asarray(np.load(P / f'{name}_float.npy', mmap_mode='r')[Y0:Y1, X0:X1]); sd = float(np.nanstd(v[mm & (rr > 1.05) & (rr < 1.6)])); riv = []
            for b in range(NB):
                near = mm & (sec == b) & (dist > 0) & (dist <= 8) & (rr < 1.15); far = mm & (sec == b) & (dist > 20) & (dist <= 40) & (rr < 1.2); riv.append(float((np.nanmean(v[near]) - np.nanmean(v[far])) / sd) if near.sum() > 20 and far.sum() > 20 else None)
            rs2 = np.arange(0.98, 1.6, 0.01); med = [np.median(v[mm & (rr >= a0) & (rr < a0 + 0.01)]) / sd if (mm & (rr >= a0) & (rr < a0 + 0.01)).sum() > 50 else np.nan for a0 in rs2]; z = np.array(med); zz = z - np.nanmedian(z[rs2 > 1.3])
            rv = np.array([x for x in riv if x is not None]); row[lab] = {'rivet_per_sector': riv, 'rivet_max_abs': float(np.max(np.abs(rv))), 'rivet_mediana_abs': float(np.median(np.abs(rv))), 'biaix_anell_1.03_1.3': float(np.nanmax(np.abs(zz[(rs2 >= 1.03) & (rs2 < 1.3)])))}
        rep['rivet_purs'][k] = row; log(f"{k}: rivet màx {row['V36']['rivet_max_abs']:.2f} → {row['V37']['rivet_max_abs']:.2f} σ, mediana {row['V36']['rivet_mediana_abs']:.2f} → {row['V37']['rivet_mediana_abs']:.2f} · biaix anell {row['V36']['biaix_anell_1.03_1.3']:.2f} → {row['V37']['biaix_anell_1.03_1.3']:.2f}")
    for k, (p36, p37) in LAYERS.items():
        g = {}
        for lab, p in (('V36', p36), ('V37', p37)):
            v = np.asarray(np.load(p, mmap_mode='r'), np.float32) / 65535; fine = np.where(m, gaussian_filter(v * w, 1.5) / np.maximum(gaussian_filter(w, 1.5), 1e-6) - gaussian_filter(v * w, 3) / np.maximum(gaussian_filter(w, 3), 1e-6), 0)
            rr_, pf, _ = ring_profile(fine ** 2, m, r, 3.9, 4.1, step=0.1 * RS); g[lab] = float(np.sqrt(pf).mean()); del v, fine
        rep['gra_4R'][k] = g
    savejson(REB37 / 'C3_portes.json', rep); log('gra 4R: ' + ', '.join(f"{k} {g['V36']:.4f}→{g['V37']:.4f}" for k, g in rep['gra_4R'].items()))
    # vista polar del limbe V36 | V37 (passa-alt σ6, 0,98–1,30) per a 01, 02, 06, P03, P04, P05
    rv_ = np.arange(0.98 * RS, 1.30 * RS, 0.5, dtype=np.float32); th = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32); X = (CX + rv_[:, None] * np.cos(th)[None, :]).astype(np.float32); Y = (CY + rv_[:, None] * np.sin(th)[None, :]).astype(np.float32); nr = len(rv_)
    sel = [k for k in ('01', '02', '06', 'P03', 'P04', 'P05')]; sheet = Image.new('L', (NT + 60, len(sel) * 2 * (nr + 20) + 10), 30); d = ImageDraw.Draw(sheet); j = 0
    for k in sel:
        for lab, p in (('V36', LAYERS[k][0]), ('V37', LAYERS[k][1])):
            v = np.asarray(np.load(p, mmap_mode='r')[Y0:Y1, X0:X1], np.float32) / 65535; ww = mm.astype(np.float32); hp = np.where(mm, v - gaussian_filter(v * ww, 6) / np.maximum(gaussian_filter(ww, 6), 1e-6), np.nan)
            pol = cv2.remap(np.nan_to_num(hp), X - X0, Y - Y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); pm = cv2.remap(np.isfinite(hp).astype(np.float32), X - X0, Y - Y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.99
            z = pol[pm]; sc = float(np.percentile(np.abs(z), 98)) if z.size else 1; u8 = np.uint8(np.clip(0.5 + pol / (2 * sc), 0, 1) * 255); u8[~pm] = 40
            sheet.paste(Image.fromarray(u8), (60, j * (nr + 20) + 20)); d.text((64, j * (nr + 20) + 3), f'{k} {lab} · passa-alt σ6 · ±{sc:.4f} u · r 0,98–1,30 R☉ · azimut −180…180°', fill=255, font=font(13)); j += 1
    sheet.save(VIS37 / 'C3_polar_limbe_V36_V37.png')
    # retalls a les marques de Pere de la V36
    cat = {x['id']: x for x in json.loads((ROOT / 'output/revisio_marques_v36_20260908/4-rebuts/review_catalog.json').read_text())['marks']}
    for mid in MARKS:
        mk = cat[mid]; k = LAYER_OF[mid[:3]]; x0, y0, x1, y1 = mk['window_bbox']
        if (x1 - x0) * (y1 - y0) > 1400 * 1400 or (x1 - x0) < 300 or (y1 - y0) < 300:
            cx, cy = int(mk['center_xy'][0]), int(mk['center_xy'][1]); half = 700 if (x1 - x0) * (y1 - y0) > 1400 * 1400 else 250; x0, y0, x1, y1 = max(cx - half, 0), max(cy - half, 0), min(cx + half, W), min(cy + half, H)
        p36, p37 = LAYERS[k]; a36 = (np.load(p36, mmap_mode='r')[y0:y1, x0:x1] // 257).astype(np.uint8); a37 = (np.load(p37, mmap_mode='r')[y0:y1, x0:x1] // 257).astype(np.uint8)
        codes = np.load(WIN36 / (mid + '_codes.npy')); wx0, wy0, wx1, wy1 = mk['window_bbox']; pm = np.zeros(a36.shape, bool); ya, yb, xa, xb = max(wy0, y0), min(wy1, y1), max(wx0, x0), min(wx1, x1)
        if yb > ya and xb > xa:
            pm[ya - y0:yb - y0, xa - x0:xb - x0] = codes[ya - wy0:yb - wy0, xa - wx0:xb - wx0] > 0
        ed = cv2.morphologyEx(pm.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; panels = []
        for a, lab in ((a36, 'V36'), (a37, 'V37')):
            rgb = np.stack([a, a, a], -1); rgb[ed] = (200, 60, 255); im = Image.fromarray(rgb); im.thumbnail((1000, 1000), Image.Resampling.LANCZOS); panels.append((im, lab))
        wtot = sum(p.width for p, _ in panels) + 30; ht = max(p.height for p, _ in panels) + 30; sheet2 = Image.new('RGB', (wtot, ht), (24, 24, 24)); d2 = ImageDraw.Draw(sheet2); xx = 10
        for p, lab in panels:
            sheet2.paste(p, (xx, 26)); d2.text((xx, 6), f'{mid} · {k} · {lab} · {x1 - x0}×{y1 - y0} px', fill='white', font=font(13)); xx += p.width + 10
        sheet2.save(VIS37 / f'C3_retall_{mid}_{k}.png')
    log('C3 fet')


if __name__ == '__main__':
    main()
