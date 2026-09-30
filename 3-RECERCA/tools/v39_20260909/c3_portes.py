"""C3 (V39) · Portes: (1) soroll per anell (rms de capa−0,5) V38 → V39 per capa; (2) JUTGE EXTERN fix (com v31_purs/qa_science.external_judge:
la Vixen ORIGINAL sense correccions, quatre finestres de 3,5/4 R☉ on la base és Sony, correlació per bandes 2–8/8–32/32–64 px) per a P03/P04/P05
i per a les bandes crues de l'ACHF (01/04/06), V38 i V39; (3) resum de l'A3 (meitats i injecció ±); (4) mapa de guany a llenç sencer d'una escala
(MGN σ5) i vistes: polar del limbe i retalls a 3,7 i 5,5 R☉ V38 | V39. Només lectura."""
from comu39 import *
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont
PC39 = HERE39 / 'purs/cau'; FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'; OLD = ROOT / 'research/tools/v29/cau_final'
LAYERS = {'01': (CAU38 / '01_v38_u16.npy', CAU39 / '01_v39_u16.npy'), '04': (CAU38 / '04_v38_u16.npy', CAU39 / '04_v39_u16.npy'), '05': (CAU38 / '05_v38_u16.npy', CAU39 / '05_v39_u16.npy'), '06': (CAU38 / '06_v38_u16.npy', CAU39 / '06_v39_u16.npy'),
          'P01': (PC38 / 'P01_NRGF_u16.npy', PC39 / 'P01_NRGF_u16.npy'), 'P01b': (PC38 / 'P01_NRGF_extrap_u16.npy', PC39 / 'P01_NRGF_extrap_u16.npy'), 'P02': (PC38 / 'P02_RHEF_u16.npy', PC39 / 'P02_RHEF_u16.npy'),
          'P03': (PC38 / 'P03_MGN_u16.npy', PC39 / 'P03_MGN_u16.npy'), 'P04': (PC38 / 'P04_WOW_u16.npy', PC39 / 'P04_WOW_u16.npy'), 'P05': (PC38 / 'P05_WOW_bilateral_u16.npy', PC39 / 'P05_WOW_bilateral_u16.npy')}
FLOATS = {'P03': ('P03_MGN_float.npy', 'P03_MGN_float.npy'), 'P04': ('P04_WOW_float.npy', 'P04_WOW_float.npy'), 'P05': ('P05_WOW_bilateral_float.npy', 'P05_WOW_bilateral_float.npy')}
WINS = [(5890, 2326), (5089, 5294), (5965, 2120), (5056, 5511)]; BANDS = [(2, 8), (8, 32), (32, 64)]


def font(n):
    return ImageFont.truetype(FONT, n)


def judge(arr_fn, fixed, mv, a, m):
    rows = []
    for x, y in WINS:
        sl = (slice(y - 384, y + 384), slice(x - 384, x + 384)); good = m[sl] & mv[sl]; assert good.all(); b = np.asarray(fixed[sl]); cand = np.nan_to_num(np.asarray(arr_fn(sl), np.float32)); src = np.asarray(a[sl]); core = np.s_[256:512, 256:512]
        for s1, s2 in BANDS:
            def band(z):
                return (gaussian_filter(z, s1) - gaussian_filter(z, s2))[core].ravel()
            j = band(b); z = band(cand); s = band(src); rows.append({'xy': [x, y], 'band': [s1, s2], 'corr_capa_vs_Vixen_original': float(np.corrcoef(j, z)[0, 1]), 'corr_base_vs_Vixen_original': float(np.corrcoef(j, s)[0, 1])})
    return rows


def main():
    r, t = coords(); m = np.load(CAU38 / 'support_v38.npy'); rq = r / RS; sl4 = (slice(0, H, 3), slice(0, W, 3)); rq4 = rq[sl4]; m4 = m[sl4]
    rep = {'soroll_per_anell': {}, 'jutge_extern': {}, 'a3': None}
    bands_r = [(1.1, 1.5), (1.5, 2.0), (2.0, 2.65), (2.65, 3.5), (3.5, 5.0), (5.0, 7.0)]
    for k, (p38, p39) in LAYERS.items():
        if not p39.exists(): log(f'{k}: falta {p39}'); continue
        row = {}
        for lab, p in (('V38', p38), ('V39', p39)):
            v = np.asarray(np.load(p, mmap_mode='r')[sl4], np.float32) / 65535 - 0.5; row[lab] = [float(np.sqrt(np.mean(v[m4 & (rq4 > a) & (rq4 < b)] ** 2))) for a, b in bands_r]
        rep['soroll_per_anell'][k] = row; log(f"{k}: rms per anell V38 " + ' '.join(f'{x:.3f}' for x in row['V38']) + ' → V39 ' + ' '.join(f'{x:.3f}' for x in row['V39']))
    # jutge extern
    fixed = np.load(OLD / 'vixen_total.npy', mmap_mode='r')[..., 1]; mv = np.load(OLD / 'vixen_support.npy'); a = np.load(CAU38 / 'base_G_v38.npy', mmap_mode='r')
    for k, (f38, f39) in FLOATS.items():
        for lab, d in (('V38', PC38), ('V39', PC39)):
            p = d / (f38 if lab == 'V38' else f39)
            if not p.exists(): continue
            arr = np.load(p, mmap_mode='r'); rows = judge(lambda sl: arr[sl], fixed, mv, a, m); rep['jutge_extern'][f'{k}_{lab}'] = rows
    for k in ('01', '04', '06'):
        for lab, d in (('V38', CAU38), ('V39', CAU39)):
            p = d / f'{k}_{"v38" if lab == "V38" else "v39"}_raw.npy'
            if not p.exists(): continue
            arr = np.load(p, mmap_mode='r'); rows = judge(lambda sl: arr[sl], fixed, mv, a, m); rep['jutge_extern'][f'{k}_{lab}'] = rows
    for k in ('P03', 'P04', 'P05', '01', '04', '06'):
        if f'{k}_V38' in rep['jutge_extern'] and f'{k}_V39' in rep['jutge_extern']:
            for i, (s1, s2) in enumerate(BANDS):
                c38 = np.mean([rw['corr_capa_vs_Vixen_original'] for rw in rep['jutge_extern'][f'{k}_V38'][i::3]]); c39 = np.mean([rw['corr_capa_vs_Vixen_original'] for rw in rep['jutge_extern'][f'{k}_V39'][i::3]]); cb = np.mean([rw['corr_base_vs_Vixen_original'] for rw in rep['jutge_extern'][f'{k}_V38'][i::3]])
                log(f'jutge {k} banda {s1}-{s2}: correlació amb la Vixen original V38 {c38:+.3f} → V39 {c39:+.3f} (base {cb:+.3f})')
    if (REB39 / 'A3_prova_operadors.json').exists(): rep['a3'] = json.loads((REB39 / 'A3_prova_operadors.json').read_text())
    savejson(REB39 / 'C3_portes.json', rep)
    # vistes: retalls V38|V39 a 3,7 R☉ (finestra del jutge) i a 5,5 R☉, i polar del limbe
    for k in ('P03', 'P04', 'P05', '01', '04', '06'):
        if not LAYERS[k][1].exists(): continue
        for tag, (cx, cy) in (('3.7R', (5089, 5294)), ('5.5R', (CX - 5.5 * RS, CY + 0.6 * RS)), ('1.6R', (CX + 1.6 * RS * np.cos(np.radians(-135)), CY + 1.6 * RS * np.sin(np.radians(-135))))):
            x0, y0 = int(cx) - 256, int(cy) - 256; sheet = Image.new('L', (2 * 512 * 2 + 20, 512 * 2 + 28), 30); d = ImageDraw.Draw(sheet)
            for jj, (lab, p) in enumerate((('V38', LAYERS[k][0]), ('V39', LAYERS[k][1]))):
                u = (np.asarray(np.load(p, mmap_mode='r')[y0:y0 + 512, x0:x0 + 512]) // 257).astype(np.uint8); sheet.paste(Image.fromarray(u).resize((1024, 1024), Image.NEAREST), (jj * 1044, 26)); d.text((jj * 1044 + 4, 6), f'{k} · {lab} · {tag} · x {x0}-{x0+512} y {y0}-{y0+512} (×2)', fill=255, font=font(13))
            sheet.save(VIS39 / f'C3_retall_{tag}_{k}_V38_V39.png')
    keys = [k for k in ('01', '04', '06', 'P03', 'P04', 'P05') if LAYERS[k][1].exists()]; Y0, Y1, X0, X1 = int(CY - 1.4 * RS), int(CY + 1.4 * RS), int(CX - 1.4 * RS), int(CX + 1.4 * RS)
    NT = 2400; rv_ = np.arange(0.98 * RS, 1.30 * RS, 0.5, dtype=np.float32); th = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32); X = (CX + rv_[:, None] * np.cos(th)[None, :]).astype(np.float32); Y = (CY + rv_[:, None] * np.sin(th)[None, :]).astype(np.float32); nr = len(rv_)
    sheet = Image.new('L', (NT + 60, len(keys) * 2 * (nr + 20) + 10), 30); d = ImageDraw.Draw(sheet); j = 0; mm = m[Y0:Y1, X0:X1]; ww = mm.astype(np.float32)
    for k in keys:
        for lab, p in (('V38', LAYERS[k][0]), ('V39', LAYERS[k][1])):
            v = np.asarray(np.load(p, mmap_mode='r')[Y0:Y1, X0:X1], np.float32) / 65535; hp = np.where(mm, v - gaussian_filter(v * ww, 6) / np.maximum(gaussian_filter(ww, 6), 1e-6), np.nan)
            pol = cv2.remap(np.nan_to_num(hp), X - X0, Y - Y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); pm = cv2.remap(np.isfinite(hp).astype(np.float32), X - X0, Y - Y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.99
            z = pol[pm]; sc = float(np.percentile(np.abs(z), 98)) if z.size else 1; u8 = np.uint8(np.clip(0.5 + pol / (2 * sc), 0, 1) * 255); u8[~pm] = 40
            sheet.paste(Image.fromarray(u8), (60, j * (nr + 20) + 20)); d.text((64, j * (nr + 20) + 3), f'{k} {lab} · passa-alt σ6 · ±{sc:.4f} u · r 0,98–1,30 R☉', fill=255, font=font(13)); j += 1
    sheet.save(VIS39 / 'C3_polar_limbe_V38_V39.png'); log('C3 fet')


if __name__ == '__main__':
    main()
