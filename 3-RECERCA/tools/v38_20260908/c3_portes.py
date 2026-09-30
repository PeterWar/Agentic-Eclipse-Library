"""C3 (V38) · Portes de la V38 contra la V37 (i la V32 per a les azimutals): (1) CONTROL NUL de la correcció de la vora lunar: la fusió V38
ha de ser idèntica a la V36 lluny de tota vora lunar (> 35 px); (2) rivet per sector (24) a la vora del forat per capa, V37 → V38;
(3) el judici P01 vs P01_extrap: rivet per azimut a la vora del forat: si el rivet clar apareix NOMÉS on els primers anells són cromosfera
(W az −180…−160, SE az +25…+45) és senyal; si apareix a tot el contorn és artefacte; (4) vista polar del limbe V37 | V38 per capa;
(5) retalls 1:1 al limbe W amb el disc de la Lluna a l'INICI dibuixat. Només lectura."""
from comu38 import *
from scipy.ndimage import gaussian_filter
from PIL import Image, ImageDraw, ImageFont
PC37 = HERE37 / 'purs/cau'; PC38 = HERE38 / 'purs/cau'; CAU32 = ROOT / 'research/tools/v32_arcs_20260907/cau'
LAYERS = {'01': (CAU37 / '01_v37_u16.npy', CAU38 / '01_v38_u16.npy'), '02': (CAU37 / '02_v37_u16.npy', CAU38 / '02_v38_u16.npy'), '04': (CAU37 / '04_v37_u16.npy', CAU38 / '04_v38_u16.npy'),
          '05': (CAU37 / '05_v37_u16.npy', CAU38 / '05_v38_u16.npy'), '06': (CAU37 / '06_v37_u16.npy', CAU38 / '06_v38_u16.npy'),
          'P01': (PC37 / 'P01_NRGF_u16.npy', PC38 / 'P01_NRGF_u16.npy'), 'P01x': (PC37 / 'P01_NRGF_u16.npy', PC38 / 'P01_NRGF_extrap_u16.npy'), 'P02': (PC37 / 'P02_RHEF_u16.npy', PC38 / 'P02_RHEF_u16.npy'),
          'P03': (PC37 / 'P03_MGN_u16.npy', PC38 / 'P03_MGN_u16.npy'), 'P04': (PC37 / 'P04_WOW_u16.npy', PC38 / 'P04_WOW_u16.npy'), 'P05': (PC37 / 'P05_WOW_bilateral_u16.npy', PC38 / 'P05_WOW_bilateral_u16.npy'),
          '03r4': (CAU32 / '03v30_v32_u16.npy', CAU38 / '03v30_v38_u16.npy'), '03r0': (CAU32 / '03_v32_u16.npy', CAU38 / '03_v38_u16.npy'), '07': (CAU32 / '07_v32_u16.npy', CAU38 / '07_v38_u16.npy')}
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'; NB = 24; NT = 2400
LLUNA_INICI = (14.8, 0.9); RL_PX = 455.5018


def font(n):
    return ImageFont.truetype(FONT, n)


def main():
    r, t = coords(); m37 = np.load(CAU36 / 'support_v36.npy'); m38 = np.load(CAU38 / 'support_v38.npy')
    Y0, Y1, X0, X1 = int(CY - 1.4 * RS), int(CY + 1.4 * RS), int(CX - 1.4 * RS), int(CX + 1.4 * RS); rr = r[Y0:Y1, X0:X1] / RS; tt = np.degrees(t[Y0:Y1, X0:X1])
    rep = {}
    # (1) control nul de la fusió: lluny de tota vora lunar (r > 1,12 R☉ ja és > 35 px de qualsevol vora: forat màx 1,046 + 28,5 px) → idèntica a la V36
    f36 = np.load(CAU36 / 'fusion_total_v36.npy', mmap_mode='r'); f38 = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r'); sl = (slice(0, H, 5), slice(0, W, 5))
    a, b = np.asarray(f36[sl][..., 1]), np.asarray(f38[sl][..., 1]); rq = r[sl] / RS; s = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
    far = s & (rq > 1.12); near = s & (rq < 1.06); d = np.abs(b / a - 1)
    rep['control_nul_fusio'] = {'px_lluny': int(far.sum()), 'rel_max_lluny_r>1.12': float(d[far].max()), 'rel_p50_prop_r<1.06': float(np.median(d[near])), 'rel_p99_prop': float(np.percentile(d[near], 99)), 'suport_identic': bool(np.array_equal(m37, m38))}
    log(f"control nul: lluny (r>1,12) rel màx {d[far].max():.2e} · prop (r<1,06) mediana {np.median(d[near]):.4f} p99 {np.percentile(d[near], 99):.4f} · suport idèntic {np.array_equal(m37, m38)}")
    # (2) rivet per sector i (3) rivet per azimut fi (72) per a P01/P01x
    mm37 = m37[Y0:Y1, X0:X1]; mm38 = m38[Y0:Y1, X0:X1]; sec = np.floor((tt + 180) / 360 * NB).astype(int) % NB; sec72 = np.floor((tt + 180) / 360 * 72).astype(int) % 72
    def rivet(v, mm, nb, secmap):
        dist = cv2.distanceTransform(mm.astype(np.uint8), cv2.DIST_L2, 5); sd = float(np.nanstd(v[mm & (rr > 1.05) & (rr < 1.6)])); out = []
        for bb in range(nb):
            nearb = mm & (secmap == bb) & (dist > 0) & (dist <= 8) & (rr < 1.15); farb = mm & (secmap == bb) & (dist > 20) & (dist <= 40) & (rr < 1.2)
            out.append(float((np.nanmean(v[nearb]) - np.nanmean(v[farb])) / sd) if nearb.sum() > 20 and farb.sum() > 20 else np.nan)
        return out
    rep['rivet_per_sector'] = {}; rep['rivet_72_P01'] = {}
    for k, (p37, p38) in LAYERS.items():
        if not p38.exists() or not p37.exists():
            log(f'{k}: falta {p38 if not p38.exists() else p37}'); continue
        v37 = np.asarray(np.load(p37, mmap_mode='r')[Y0:Y1, X0:X1], np.float32) / 65535; v38 = np.asarray(np.load(p38, mmap_mode='r')[Y0:Y1, X0:X1], np.float32) / 65535
        r37 = rivet(v37, mm37, NB, sec); r38 = rivet(v38, mm38, NB, sec); a37 = np.array([x for x in r37 if np.isfinite(x)]); a38 = np.array([x for x in r38 if np.isfinite(x)])
        rep['rivet_per_sector'][k] = {'V37_max': float(np.max(np.abs(a37))), 'V37_med': float(np.median(np.abs(a37))), 'V38_max': float(np.max(np.abs(a38))), 'V38_med': float(np.median(np.abs(a38))), 'V37': r37, 'V38': r38}
        log(f"{k}: rivet |màx|/|mediana| {'V32' if k in ('03r4','03r0','07') else 'V37'} {np.max(np.abs(a37)):.2f}/{np.median(np.abs(a37)):.2f} → V38 {np.max(np.abs(a38)):.2f}/{np.median(np.abs(a38)):.2f}")
        if k in ('P01', 'P01x'):
            r72 = rivet(v38, mm38, 72, sec72); rep['rivet_72_P01'][k] = r72
            crom = [i for i in range(72) if (-180 + (i + .5) * 5) <= -160 or (-180 + (i + .5) * 5) >= 175 or 25 <= (-180 + (i + .5) * 5) <= 45]; altres = [i for i in range(72) if i not in crom]
            rc = np.array([r72[i] for i in crom if np.isfinite(r72[i])]); ra = np.array([r72[i] for i in altres if np.isfinite(r72[i])])
            rep['rivet_72_P01'][k + '_resum'] = {'cromosfera_W_SE_mediana': float(np.median(rc)), 'cromosfera_max': float(rc.max()), 'resta_mediana': float(np.median(ra)), 'resta_p95': float(np.percentile(ra, 95)), 'resta_max_abs': float(np.max(np.abs(ra)))}
            log(f"  {k} rivet per azimut (72): on hi ha cromosfera (W/SE) mediana {np.median(rc):+.2f} màx {rc.max():+.2f} σ · a la resta del contorn mediana {np.median(ra):+.2f} p95 {np.percentile(ra,95):+.2f} |màx| {np.max(np.abs(ra)):.2f} σ")
    savejson(REB38 / 'C3_portes.json', rep)
    # (4) vista polar del limbe V37 | V38 (0,98–1,30) per a 01, 03r4, P01, P01x, P02, P03, P04, P05
    keys = [k for k in ('01', '03r4', 'P01', 'P01x', 'P02', 'P03', 'P04', 'P05') if LAYERS[k][1].exists() and LAYERS[k][0].exists()]
    rv_ = np.arange(0.98 * RS, 1.30 * RS, 0.5, dtype=np.float32); th = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32); X = (CX + rv_[:, None] * np.cos(th)[None, :]).astype(np.float32); Y = (CY + rv_[:, None] * np.sin(th)[None, :]).astype(np.float32); nr = len(rv_)
    sheet = Image.new('L', (NT + 60, len(keys) * 2 * (nr + 20) + 10), 30); d = ImageDraw.Draw(sheet); j = 0
    for k in keys:
        for lab, p, mm in ((('V32' if k == '03r4' else 'V37'), LAYERS[k][0], mm37), ('V38', LAYERS[k][1], mm38)):
            v = np.asarray(np.load(p, mmap_mode='r')[Y0:Y1, X0:X1], np.float32) / 65535; ww = mm.astype(np.float32); hp = np.where(mm, v - gaussian_filter(v * ww, 6) / np.maximum(gaussian_filter(ww, 6), 1e-6), np.nan)
            pol = cv2.remap(np.nan_to_num(hp), X - X0, Y - Y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); pm = cv2.remap(np.isfinite(hp).astype(np.float32), X - X0, Y - Y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.99
            z = pol[pm]; sc = float(np.percentile(np.abs(z), 98)) if z.size else 1; u8 = np.uint8(np.clip(0.5 + pol / (2 * sc), 0, 1) * 255); u8[~pm] = 40
            sheet.paste(Image.fromarray(u8), (60, j * (nr + 20) + 20)); d.text((64, j * (nr + 20) + 3), f'{k} {lab} · passa-alt σ6 · ±{sc:.4f} u · r 0,98–1,30 R☉ · azimut −180…180°', fill=255, font=font(13)); j += 1
    sheet.save(VIS38 / 'C3_polar_limbe_V37_V38.png')
    # (5) retalls 1:1 (×3) al limbe W amb el disc de la Lluna a l'INICI
    cxl, cyl = CX + LLUNA_INICI[0], CY + LLUNA_INICI[1]
    for k in ('P01', 'P01x', 'P03', 'P04', '01', '03r4'):
        if not LAYERS[k][1].exists() or not LAYERS[k][0].exists(): continue
        for tag, (x0, x1, y0, y1) in (('oest', (4700, 5000, 3630, 3930)), ('sudoest', (4880, 5180, 3930, 4230)), ('nordoest', (4880, 5180, 3320, 3620))):
            sheetk = Image.new('L', (2 * (x1 - x0) * 3 + 30, (y1 - y0) * 3 + 30), 30); dk = ImageDraw.Draw(sheetk)
            for jj, (lab, p) in enumerate(((('V32' if k == '03r4' else 'V37'), LAYERS[k][0]), ('V38', LAYERS[k][1]))):
                a = (np.asarray(np.load(p, mmap_mode='r')[y0:y1, x0:x1]) // 257).astype(np.uint8); im = Image.fromarray(a).resize(((x1 - x0) * 3, (y1 - y0) * 3), Image.NEAREST).convert('RGB'); di = ImageDraw.Draw(im)
                cx_, cy_ = (cxl - x0) * 3, (cyl - y0) * 3; di.ellipse([cx_ - 3 * RL_PX, cy_ - 3 * RL_PX, cx_ + 3 * RL_PX, cy_ + 3 * RL_PX], outline=(60, 220, 60), width=2)
                sheetk.paste(im, (jj * ((x1 - x0) * 3 + 10), 26)); dk.text((jj * ((x1 - x0) * 3 + 10) + 4, 6), f'{k} · {lab} · limbe {tag} · x {x0}-{x1} y {y0}-{y1} (×3) · verd: Lluna a l\'INICI (R 455,5)', fill=255, font=font(13))
            sheetk.save(VIS38 / f'C3_retall_limbe_{tag}_{k}_V37_V38.png')
    log('C3 fet')


if __name__ == '__main__':
    main()
