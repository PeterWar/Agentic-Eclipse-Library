"""C3 (V37fc) · Comparació V37 (franja conservada) | V37fc (forat circular): vista polar del limbe 0,98–1,30 de 01/02/06/P01/P02/P03/P04/P05,
retalls 1:1 al limbe oest (az 178°) i al limbe sud-oest (az 150°) per a P01, P03 i 01, i el rivet/biaix d'anell per capa."""
from comu37fc import *
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont
PC37 = HERE37 / 'purs/cau'; PC = HERE37FC / 'purs/cau'; NT = 2400; NB = 24
LAYERS = {'01': (CAU37 / '01_v37_u16.npy', CAU37FC / '01_v37fc_u16.npy'), '02': (CAU37 / '02_v37_u16.npy', CAU37FC / '02_v37fc_u16.npy'), '06': (CAU37 / '06_v37_u16.npy', CAU37FC / '06_v37fc_u16.npy'),
          'P01': (PC37 / 'P01_NRGF_u16.npy', PC / 'P01_NRGF_u16.npy'), 'P02': (PC37 / 'P02_RHEF_u16.npy', PC / 'P02_RHEF_u16.npy'), 'P03': (PC37 / 'P03_MGN_u16.npy', PC / 'P03_MGN_u16.npy'), 'P04': (PC37 / 'P04_WOW_u16.npy', PC / 'P04_WOW_u16.npy'), 'P05': (PC37 / 'P05_WOW_bilateral_u16.npy', PC / 'P05_WOW_bilateral_u16.npy')}
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'


def font(n):
    return ImageFont.truetype(FONT, n)


def main():
    r, t = coords(); m37 = np.load(CAU36 / 'support_v36.npy'); mfc = np.load(CAU37FC / 'support_v37fc.npy')
    Y0, Y1, X0, X1 = int(CY - 1.4 * RS), int(CY + 1.4 * RS), int(CX - 1.4 * RS), int(CX + 1.4 * RS); rr = r[Y0:Y1, X0:X1] / RS; tt = np.degrees(t[Y0:Y1, X0:X1])
    rv_ = np.arange(0.98 * RS, 1.30 * RS, 0.5, dtype=np.float32); th = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32); X = (CX + rv_[:, None] * np.cos(th)[None, :]).astype(np.float32); Y = (CY + rv_[:, None] * np.sin(th)[None, :]).astype(np.float32); nr = len(rv_)
    sheet = Image.new('L', (NT + 60, len(LAYERS) * 2 * (nr + 20) + 10), 30); d = ImageDraw.Draw(sheet); j = 0; rep = {}
    for k, (p37, pfc) in LAYERS.items():
        row = {}
        for lab, p, m in (('V37 franja', p37, m37), ('V37fc forat circular', pfc, mfc)):
            mm = m[Y0:Y1, X0:X1]; v = np.asarray(np.load(p, mmap_mode='r')[Y0:Y1, X0:X1], np.float32) / 65535; ww = mm.astype(np.float32); hp = np.where(mm, v - gaussian_filter(v * ww, 6) / np.maximum(gaussian_filter(ww, 6), 1e-6), np.nan)
            pol = cv2.remap(np.nan_to_num(hp), X - X0, Y - Y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); pm = cv2.remap(np.isfinite(hp).astype(np.float32), X - X0, Y - Y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.99
            z = pol[pm]; sc = float(np.percentile(np.abs(z), 98)) if z.size else 1; u8 = np.uint8(np.clip(0.5 + pol / (2 * sc), 0, 1) * 255); u8[~pm] = 40
            sheet.paste(Image.fromarray(u8), (60, j * (nr + 20) + 20)); d.text((64, j * (nr + 20) + 3), f'{k} {lab} · passa-alt σ6 · ±{sc:.4f} u · r 0,98–1,30 R☉ · azimut −180…180°', fill=255, font=font(13)); j += 1
            dist = cv2.distanceTransform(mm.astype(np.uint8), cv2.DIST_L2, 5); sec = np.floor((tt + 180) / 360 * NB).astype(int) % NB; sd = float(np.nanstd(v[mm & (rr > 1.05) & (rr < 1.6)])); riv = []
            for b in range(NB):
                near = mm & (sec == b) & (dist > 0) & (dist <= 8) & (rr < 1.15); far = mm & (sec == b) & (dist > 20) & (dist <= 40) & (rr < 1.2); riv.append(float((np.nanmean(v[near]) - np.nanmean(v[far])) / sd) if near.sum() > 20 and far.sum() > 20 else np.nan)
            rv = np.array([x for x in riv if np.isfinite(x)]); row[lab] = {'rivet_max_abs': float(np.max(np.abs(rv))), 'rivet_mediana_abs': float(np.median(np.abs(rv)))}
        rep[k] = row; log(f"{k}: rivet màx/mediana V37 {row['V37 franja']['rivet_max_abs']:.2f}/{row['V37 franja']['rivet_mediana_abs']:.2f} → V37fc {row['V37fc forat circular']['rivet_max_abs']:.2f}/{row['V37fc forat circular']['rivet_mediana_abs']:.2f}")
    sheet.save(VIS37FC / 'C3_polar_limbe_V37_V37fc.png'); savejson(REB37FC / 'C3_compara.json', rep)
    # retalls 1:1 al limbe oest (az 178°, x 4700–5000, y 3640–3920) i sud-oest (az 150°) per a P01, P03, 01, P05
    for k in ('P01', 'P03', '01', 'P05'):
        for tag, (x0, x1, y0, y1) in (('oest', (4700, 5000, 3630, 3930)), ('sudoest', (4880, 5180, 3930, 4230))):
            sheetk = Image.new('L', (2 * (x1 - x0) * 3 + 30, (y1 - y0) * 3 + 30), 30); dk = ImageDraw.Draw(sheetk)
            for jj, (lab, p) in enumerate((('V37 franja', LAYERS[k][0]), ('V37fc forat circular', LAYERS[k][1]))):
                a = (np.asarray(np.load(p, mmap_mode='r')[y0:y1, x0:x1]) // 257).astype(np.uint8); sheetk.paste(Image.fromarray(a).resize(((x1 - x0) * 3, (y1 - y0) * 3), Image.NEAREST), (jj * ((x1 - x0) * 3 + 10), 26)); dk.text((jj * ((x1 - x0) * 3 + 10) + 4, 6), f'{k} · {lab} · limbe {tag} · x {x0}-{x1} y {y0}-{y1} (×3)', fill=255, font=font(13))
            sheetk.save(VIS37FC / f'C3_retall_limbe_{tag}_{k}_V37_V37fc.png')
    log('C3 fet')


if __name__ == '__main__':
    main()
