"""C3 (V36) · Portes V35 → V36, mateixa vara:
  · gra fi de la base per radi (V35/V36) i per capa; PERFIL DEL GRA contra la distància amb signe al contorn de mig pes dels 8 s de la Sony (la vora quadrada);
  · graó APARELLAT al contorn dels 8 s (mitjana local σ24 a ±150 px al llarg de la normal, ÷ rms banda 6–12; nul = contorn desplaçat 600 px) per capa;
  · biaix d'anell al limbe 1,03–1,3 per capa; salt de la NRGF al primer anell sencer (mediana per anell 1,00–1,10 a 0,005); bandes de la RHEF prop de l'eix −x (rms del passa-alt de la mediana per fila);
  · retalls 1:1 a les marques de Pere de la V35 (V35 | V36) i polars."""
from comu36 import *
from scipy.ndimage import gaussian_filter, map_coordinates
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(ROOT / 'research/tools/revisio_marques_v32_20260907'))
from a4_color_i_rho import ring_profile
PC35 = HERE35 / 'purs/cau'; PC36 = HERE36 / 'purs/cau'; WIN35 = ROOT / 'research/tools/revisio_marques_v35_20260908/windows'
LAYERS = {'01': (CAU35 / '01_v35_u16.npy', CAU36 / '01_v36_u16.npy'), '02': (CAU35 / '02_v35_u16.npy', CAU36 / '02_v36_u16.npy'), '04': (CAU35 / '04_v35_u16.npy', CAU36 / '04_v36_u16.npy'),
          '05': (CAU35 / '05_v35_u16.npy', CAU36 / '05_v36_u16.npy'), '06': (CAU35 / '06_v35_u16.npy', CAU36 / '06_v36_u16.npy'),
          'P01': (PC35 / 'P01_NRGF_u16.npy', PC36 / 'P01_NRGF_u16.npy'), 'P02': (PC35 / 'P02_RHEF_u16.npy', PC36 / 'P02_RHEF_u16.npy'), 'P03': (PC35 / 'P03_MGN_u16.npy', PC36 / 'P03_MGN_u16.npy'),
          'P04': (PC35 / 'P04_WOW_u16.npy', PC36 / 'P04_WOW_u16.npy'), 'P05': (PC35 / 'P05_WOW_bilateral_u16.npy', PC36 / 'P05_WOW_bilateral_u16.npy')}
LAYER_OF = {'L01': '01', 'L02': '02', 'L03': '04', 'L04': '05', 'L05': '06', 'L06': 'P01', 'L07': 'P02', 'L08': 'P03', 'L09': 'P04', 'L10': 'P05'}
MARKS = ['L05-M01', 'L06-M01', 'L07-M01', 'L07-M03', 'L08-M01', 'L08-M03', 'L09-M01', 'L10-M02', 'L10-M04', 'L10-M06', 'L10-M10']
FONT = '/System/Library/Fonts/Supplemental/Arial.ttf'; NT = 2400; D = 150.0


def font(n):
    return ImageFont.truetype(FONT, n)


def ng(a, w, s):
    return gaussian_filter(a * w, s) / np.maximum(gaussian_filter(w, s), 1e-6)


def contour_8s():
    """Distància amb signe al contorn de mig pes dels 8 s de la Sony (+ dins, on els 8 s NO hi són = més a prop del Sol)."""
    w = np.load(CAU34 / 'sony_w.npy', mmap_mode='r'); meta = json.loads((CAU34 / 'sony_meta.json').read_text())['frames']
    idx = [i for i, f in enumerate(meta) if f['name'] in ('DSC06987.ARW', 'DSC06993.ARW')]; w8 = sum(np.asarray(w[i]) for i in idx)
    plateau = float(np.percentile(w8[w8 > 0], 90)); inside = cv2.resize((w8 < 0.5 * plateau).astype(np.uint8), (W, H), interpolation=cv2.INTER_NEAREST) > 0
    sd = np.where(inside, cv2.distanceTransform(inside.astype(np.uint8), cv2.DIST_L2, 5), -cv2.distanceTransform((~inside).astype(np.uint8), cv2.DIST_L2, 5)).astype(np.float32)
    return sd, inside


def edge_samples(sd, zone, offset=0.0, step=20):
    band = zone & (np.abs(sd - offset) < 1.5); ys, xs = np.nonzero(band); ys, xs = ys[::step], xs[::step]
    gy, gx = np.gradient(gaussian_filter(sd, 4)); nx, ny = gx[ys, xs], gy[ys, xs]; n = np.hypot(nx, ny); ok = n > 1e-3
    return ys[ok].astype(np.float32), xs[ok].astype(np.float32), nx[ok] / n[ok], ny[ok] / n[ok]


def paired(lo, ys, xs, nx, ny, m):
    vin = map_coordinates(lo, [ys + D * ny, xs + D * nx], order=1, mode='nearest'); vout = map_coordinates(lo, [ys - D * ny, xs - D * nx], order=1, mode='nearest')
    ok = (map_coordinates(m.astype(np.float32), [ys + D * ny, xs + D * nx], order=1) > 0.99) & (map_coordinates(m.astype(np.float32), [ys - D * ny, xs - D * nx], order=1) > 0.99)
    d = vin[ok] - vout[ok]; return (float(np.median(d)) if ok.any() else float('nan')), int(ok.sum())


def ring_bias(v, m, r):
    sd = float(np.nanstd(v[m & (r > 1.05 * RS) & (r < 1.6 * RS)])); rs = np.arange(0.98, 1.6, 0.01); med = []
    for a0 in rs:
        k = m & (r >= a0 * RS) & (r < (a0 + 0.01) * RS); med.append(float(np.median(v[k])) / max(sd, 1e-12) if k.sum() > 50 else np.nan)
    z = np.array(med); zz = z - np.nanmedian(z[rs > 1.3]); return float(np.nanmax(np.abs(zz[(rs >= 1.03) & (rs < 1.3)])))


def nrgf_first_ring_jump(v, m, r):
    rs = np.arange(1.0, 1.1, 0.005); med = np.array([np.median(v[m & (r >= a * RS) & (r < (a + 0.005) * RS)]) if (m & (r >= a * RS) & (r < (a + 0.005) * RS)).sum() > 50 else np.nan for a in rs])
    sd = float(np.nanstd(v[m & (r > 1.05 * RS) & (r < 1.6 * RS)])); d = np.abs(np.diff(med)) / max(sd, 1e-12); return {'max_salt_entre_anells_0.005_sigma': float(np.nanmax(d)), 'r_salt': float(rs[int(np.nanargmax(d))])}


def rhef_axis_bands(v, m):
    """rms del passa-alt (σ6 en y) de la mediana per fila, a x ∈ [CX−700, CX−300] (prop de l'eix −x) contra el mateix a 45° (control)."""
    def band(x0, x1, y0, y1):
        c = v[y0:y1, x0:x1]; mm = m[y0:y1, x0:x1]; prof = np.array([np.median(c[i][mm[i]]) if mm[i].sum() > 50 else np.nan for i in range(c.shape[0])]); prof = np.nan_to_num(prof, nan=np.nanmedian(prof)); hp = prof - gaussian_filter(prof, 6); return float(np.std(hp))
    ax = band(int(CX - 700), int(CX - 300), int(CY - 120), int(CY + 120)); ctl = band(int(CX - 520), int(CX - 280), int(CY - 520), int(CY - 280)); return {'eix_x_rms': ax, 'control_45_rms': ctl, 'quocient': ax / max(ctl, 1e-12)}


def polar_u8(u, m, r0, r1, sigma):
    v = np.asarray(u, np.float32) / 65535; w = m.astype(np.float32); hp = np.where(m, v - ng(v, w, sigma), np.nan)
    rv = np.arange(r0 * RS, r1 * RS, 1.0, dtype=np.float32); th = np.linspace(-np.pi, np.pi, NT, endpoint=False, dtype=np.float32)
    X = (CX + rv[:, None] * np.cos(th)[None, :]).astype(np.float32); Y = (CY + rv[:, None] * np.sin(th)[None, :]).astype(np.float32)
    pol = cv2.remap(np.nan_to_num(hp), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); pm = cv2.remap(np.isfinite(hp).astype(np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT) > 0.99
    z = pol[pm]; sc = float(np.percentile(np.abs(z), 98)) if z.size else 1; u8 = np.uint8(np.clip(0.5 + pol / (2 * sc), 0, 1) * 255); u8[~pm] = 40; return u8, sc


def main():
    r, t = coords(); m = np.load(CAU36 / 'support_v36.npy'); w = m.astype(np.float32); sd8, inside8 = contour_8s()
    y, x = np.ogrid[:H, :W]; dist = np.hypot(x - GHOST_XY[0], y - GHOST_XY[1]); zone8 = m & (r > 2.2 * RS) & (r < 6 * RS) & (dist > 320)
    S8 = [edge_samples(sd8, zone8, 0.0), edge_samples(sd8, zone8, 600.0)]
    rep = {'gra': {}, 'vora_8s': {'capes': {}, 'perfil_gra_base': {}}, 'limbe_biaix_anell_sigma': {}, 'nrgf_salt_primer_anell': {}, 'rhef_bandes_eix': {}, 'retalls': []}
    bins = list(range(-800, 800, 50))
    for nm, pth in (('base_V35', CAU35 / 'base_G_v35.npy'), ('base_V36', CAU36 / 'base_G_v36.npy')):
        G = np.asarray(np.load(pth, mmap_mode='r')); mm = m & np.isfinite(G) & (G > 0); L = np.where(mm, np.log(np.maximum(G, 1e-9)), 0).astype(np.float32); ww = mm.astype(np.float32)
        fine = np.where(mm, ng(L, ww, 1.5) - ng(L, ww, 3), 0); rr, pf, _ = ring_profile(fine ** 2, mm, r, 1.05, 9.0, step=0.02 * RS); rep['gra'][nm] = {'r': rr.tolist(), 'fi_pct': (100 * np.sqrt(pf)).tolist()}
        lf = np.sqrt(np.maximum(ng(fine * fine, ww, 24), 0)); prof = []
        for b0 in bins:
            k = zone8 & mm & (sd8 >= b0) & (sd8 < b0 + 50); prof.append(float(100 * np.median(lf[k])) if k.sum() > 300 else None)
        lg = np.log(np.maximum(lf, 1e-12)); gr_, _ = paired(lg, *S8[0], mm); gn_, _ = paired(lg, *S8[1], mm)
        rep['vora_8s']['perfil_gra_base'][nm] = {'bins_px': bins, 'gra_fi_pct': prof, 'grao_GRA_ln_dins_fora_150px': gr_, 'nul_GRA_ln': gn_}; del G, L, fine, lf
        log(nm + f' gra contra la vora 8 s (graó GRA ln dins/fora {gr_:+.3f}, nul {gn_:+.3f}): ' + ' '.join('–' if p is None else f'{p:.3f}' for p in prof))
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, axs = plt.subplots(5, 2, figsize=(12, 15), sharex=True); axs = axs.ravel()
    for i, (k, (p35, p36)) in enumerate(LAYERS.items()):
        row = {}
        for lab, p in (('V35', p35), ('V36', p36)):
            v = np.asarray(np.load(p, mmap_mode='r'), np.float32) / 65535; lo = ng(v, w, 24); mid = np.where(m, ng(v, w, 6) - ng(v, w, 12), 0); fine = np.where(m, ng(v, w, 1.5) - ng(v, w, 3), 0)
            rr, pf, _ = ring_profile(fine ** 2, m, r, 1.05, 12.0, step=0.05 * RS); _, pm_, _ = ring_profile(mid ** 2, m, r, 1.05, 12.0, step=0.05 * RS); rep['gra'].setdefault(k, {})[lab] = {'r': rr.tolist(), 'fi': np.sqrt(pf).tolist(), 'mig': np.sqrt(pm_).tolist()}
            rms = float(np.sqrt(np.mean(mid[zone8] ** 2))); sr, n1 = paired(lo, *S8[0], m); sn, n2 = paired(lo, *S8[1], m)
            lg = np.log(np.maximum(np.sqrt(np.maximum(ng(fine * fine, w, 24), 0)), 1e-12)); gr_, _ = paired(lg, *S8[0], m); gn_, _ = paired(lg, *S8[1], m)
            row[lab] = {'grao_sobre_rms': sr / max(rms, 1e-9), 'nul_sobre_rms': sn / max(rms, 1e-9), 'n': n1, 'grao_GRA_ln_dins_fora': gr_, 'nul_GRA_ln': gn_}
            rep['limbe_biaix_anell_sigma'].setdefault(k, {})[lab] = ring_bias(v, m, r)
            if k == 'P01':
                rep['nrgf_salt_primer_anell'][lab] = nrgf_first_ring_jump(v, m, r)
            if k == 'P02':
                rep['rhef_bandes_eix'][lab] = rhef_axis_bands(v, m)
            ax = axs[i]; ax.semilogy(rr, np.sqrt(pf), 'r' if lab == 'V35' else 'r--', lw=.8, label=f'fi {lab}'); ax.semilogy(rr, np.sqrt(pm_), 'b' if lab == 'V35' else 'b--', lw=.8, label=f'mig {lab}'); ax.set_title(k, fontsize=9); ax.legend(fontsize=7)
            del v, lo, mid, fine
        rep['vora_8s']['capes'][k] = row
        log(f"{k}: graó nivell al contorn 8 s {row['V35']['grao_sobre_rms']:+.2f} (nul {row['V35']['nul_sobre_rms']:+.2f}) → {row['V36']['grao_sobre_rms']:+.2f} (nul {row['V36']['nul_sobre_rms']:+.2f}) · graó GRA ln(dins/fora) {row['V35']['grao_GRA_ln_dins_fora']:+.3f} (nul {row['V35']['nul_GRA_ln']:+.3f}) → {row['V36']['grao_GRA_ln_dins_fora']:+.3f} (nul {row['V36']['nul_GRA_ln']:+.3f}) · limbe {rep['limbe_biaix_anell_sigma'][k]['V35']:.2f}→{rep['limbe_biaix_anell_sigma'][k]['V36']:.2f} σ")
    fig.tight_layout(); fig.savefig(VIS36 / 'C3_gra_per_radi_V35_V36.png', dpi=110); plt.close(fig)
    log(f"NRGF salt primer anell: {rep['nrgf_salt_primer_anell']} · RHEF bandes eix: {rep['rhef_bandes_eix']}")
    savejson(REB36 / 'C3_portes.json', rep)
    for k, (p35, p36) in LAYERS.items():
        u35 = np.load(p35, mmap_mode='r'); u36 = np.load(p36, mmap_mode='r')
        for tram, (r0, r1), sg in [('interior', (1.0, 3.0), 12), ('intermedi', (3.0, 6.0), 24)]:
            a35, s35 = polar_u8(u35, m, r0, r1, sg); a36, s36 = polar_u8(u36, m, r0, r1, sg); nr = a35.shape[0]; im = Image.new('L', (NT + 60, 2 * (nr + 24)), 30); d = ImageDraw.Draw(im)
            for j, (a, s, lab) in enumerate([(a35, s35, 'V35'), (a36, s36, 'V36')]):
                im.paste(Image.fromarray(a), (60, j * (nr + 24) + 24)); d.text((64, j * (nr + 24) + 4), f'{k} {lab} · passa-alt σ{sg} · ±{s:.4f} u · r {r0}–{r1} R☉ · azimut −180…180°', fill=255, font=font(13))
                for rr_ in np.arange(np.ceil(r0 * 2) / 2, r1, 0.5):
                    d.text((2, j * (nr + 24) + 24 + int((rr_ - r0) * RS) - 6), f'{rr_:.1f}', fill=200, font=font(11))
            im.save(VIS36 / f'C3_polar_{k}_{tram}.png')
    cat = {x['id']: x for x in json.loads((ROOT / 'output/revisio_marques_v35_20260908/4-rebuts/review_catalog.json').read_text())['marks']}
    edge8 = cv2.morphologyEx(inside8.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0
    for mid in MARKS:
        mk = cat[mid]; k = LAYER_OF[mid[:3]]; x0, y0, x1, y1 = mk['window_bbox']
        if (x1 - x0) * (y1 - y0) > 1400 * 1400 or (x1 - x0) < 300 or (y1 - y0) < 300:
            cx, cy = int(mk['center_xy'][0]), int(mk['center_xy'][1]); half = 700 if (x1 - x0) * (y1 - y0) > 1400 * 1400 else 250; x0, y0, x1, y1 = max(cx - half, 0), max(cy - half, 0), min(cx + half, W), min(cy + half, H)
        p35, p36 = LAYERS[k]; a35 = (np.load(p35, mmap_mode='r')[y0:y1, x0:x1] // 257).astype(np.uint8); a36 = (np.load(p36, mmap_mode='r')[y0:y1, x0:x1] // 257).astype(np.uint8)
        codes = np.load(WIN35 / (mid + '_codes.npy')); wx0, wy0, wx1, wy1 = mk['window_bbox']; pm = np.zeros(a35.shape, bool); ya, yb, xa, xb = max(wy0, y0), min(wy1, y1), max(wx0, x0), min(wx1, x1)
        if yb > ya and xb > xa:
            pm[ya - y0:yb - y0, xa - x0:xb - x0] = codes[ya - wy0:yb - wy0, xa - wx0:xb - wx0] > 0
        ed = cv2.morphologyEx(pm.astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8)) > 0; e8 = edge8[y0:y1, x0:x1]
        panels = []
        for a, lab in ((a35, 'V35'), (a36, 'V36')):
            rgb = np.stack([a, a, a], -1); rgb[e8] = (60, 200, 255); rgb[ed] = (200, 60, 255); im = Image.fromarray(rgb); im.thumbnail((1000, 1000), Image.Resampling.LANCZOS); panels.append((im, lab))
        wtot = sum(p.width for p, _ in panels) + 30; ht = max(p.height for p, _ in panels) + 30; sheet = Image.new('RGB', (wtot, ht), (24, 24, 24)); d = ImageDraw.Draw(sheet); xx = 10
        for p, lab in panels:
            sheet.paste(p, (xx, 26)); d.text((xx, 6), f'{mid} · {k} · {lab} · {x1 - x0}×{y1 - y0} px · lila = traç de Pere, blau = contorn de mig pes dels 8 s', fill='white', font=font(13)); xx += p.width + 10
        sheet.save(VIS36 / f'C3_retall_{mid}_{k}.png'); rep['retalls'].append({'id': mid, 'layer': k, 'box': [x0, y0, x1, y1]})
    savejson(REB36 / 'C3_portes.json', rep); log('C3 fet')


if __name__ == '__main__':
    main()
