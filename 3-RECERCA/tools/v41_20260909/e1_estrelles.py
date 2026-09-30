"""E1 (V41) · Les estrelles: com són (PSF mesurada a la base lineal, per tren) i què els fan els filtres (V38 = els de la V41).
Entrada: posicions de la capa `Estrelles` (catàleg HIP/Tycho, llum mesurada; research/125) exportades a JSON.
Per estrella: fons local (mediana d'un anell 12–20 px), pic sobre fons, S/N, moments de segon ordre → σ major/menor, elongació, angle; per a la fusió, la Vixen i la Sony.
Per filtre (u16 V38: 01/04/05/06 ACHF, P03 MGN, P04 WOW, P05 bilateral, P01 NRGF, P02 RHEF): excés al centre i mínim de l'anell 3–10 px respecte del nivell local (0,5 = neutre als Superposar), en σ del fons local del filtre.
Sortides: REB41/E1_estrelles.json, VIS41/E1_galeria_estrelles.png (24 més brillants, 1:1, mateixa escala per columna), VIS41/E1_mapa_estrelles_quart.png (llenç sencer)."""
from comu41 import *
import cv2
from scipy.ndimage import median_filter
SONY36 = ROOT / 'research/tools/v36_20260908/cau/sony_corrected_total_v36.npy'; PC38 = ROOT / 'research/tools/v38_20260908/purs/cau'
STARS = Path('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/bb2a9ec7-d793-44f1-a277-703c16855cd4/scratchpad/estrelles_v39.json')
FILTRES = {'01 ACHF fi 2-32': CAU38 / '01_v38_u16.npy', '04 ACHF micro 1-16': CAU38 / '04_v38_u16.npy', '05 ACHF fi 2-48': CAU38 / '05_v38_u16.npy', '06 ACHF estructura 4-64': CAU38 / '06_v38_u16.npy',
           'P03 MGN': PC38 / 'P03_MGN_u16.npy', 'P04 WOW': PC38 / 'P04_WOW_u16.npy', 'P05 WOW bilateral': PC38 / 'P05_WOW_bilateral_u16.npy', 'P01 NRGF': PC38 / 'P01_NRGF_u16.npy', 'P02 RHEF': PC38 / 'P02_RHEF_u16.npy'}
R = 20


def stamp(arr, x, y, c=None):
    y0, y1, x0, x1 = y - R, y + R + 1, x - R, x + R + 1
    if y0 < 0 or x0 < 0 or y1 > H or x1 > W: return None
    s = arr[y0:y1, x0:x1]; s = s[..., c] if (c is not None and s.ndim == 3) else s; return np.asarray(s, np.float64)


def psf(s):
    """fons = mediana anell 12–20; pic; S/N; moments dins de r ≤ 6 amb pesos positius"""
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; rr = np.hypot(xx, yy); an = (rr >= 12) & (rr <= 20); bg = np.median(s[an]); sd = 1.4826 * np.median(np.abs(s[an] - bg)); d = s - bg
    iy, ix = np.unravel_index(np.argmax(np.where(rr <= 4, d, -np.inf)), d.shape); pic = d[iy, ix]; snr = pic / sd if sd > 0 else np.nan
    w = np.where((np.hypot(xx - (ix - R), yy - (iy - R)) <= 6) & (d > 0), d, 0); W_ = w.sum()
    if W_ <= 0: return dict(fons=bg, pic=pic, snr=snr)
    mx, my = (w * xx).sum() / W_, (w * yy).sum() / W_; cxx = (w * (xx - mx) ** 2).sum() / W_; cyy = (w * (yy - my) ** 2).sum() / W_; cxy = (w * (xx - mx) * (yy - my)).sum() / W_
    tr, det = cxx + cyy, cxx * cyy - cxy ** 2; l1 = tr / 2 + np.sqrt(max(tr * tr / 4 - det, 0)); l2 = tr / 2 - np.sqrt(max(tr * tr / 4 - det, 0)); ang = 0.5 * np.degrees(np.arctan2(2 * cxy, cxx - cyy))
    return dict(fons=float(bg), pic=float(pic), snr=float(snr), sigma_major=float(np.sqrt(max(l1, 0))), sigma_menor=float(np.sqrt(max(l2, 0))), fwhm_major=float(2.355 * np.sqrt(max(l1, 0))), fwhm_menor=float(2.355 * np.sqrt(max(l2, 0))), elongacio=float(np.sqrt(l1 / l2)) if l2 > 0 else np.nan, angle_deg=float(ang), flux6=float(W_))


def resposta_filtre(s):
    """excés al centre i mínim de l'anell 3–10 px respecte del nivell local (mediana anell 12–20), en σ del fons"""
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; rr = np.hypot(xx, yy); an = (rr >= 12) & (rr <= 20); bg = np.median(s[an]); sd = 1.4826 * np.median(np.abs(s[an] - bg)) + 1e-9
    return dict(nivell=float(bg), sigma_fons=float(sd), exces_centre=float((s[rr <= 2].max() - bg)), exces_centre_sig=float((s[rr <= 2].max() - bg) / sd), minim_anell=float(s[(rr >= 3) & (rr <= 10)].min() - bg), minim_anell_sig=float((s[(rr >= 3) & (rr <= 10)].min() - bg) / sd))


def main():
    stars = json.loads(STARS.read_text()); r, t = coords()
    F = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r'); V = np.load(CAU38 / 'vixen_total_v38.npy', mmap_mode='r'); S = np.load(SONY36, mmap_mode='r'); WV = np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r')
    filt = {k: np.load(p, mmap_mode='r') for k, p in FILTRES.items() if p.exists()}; log('filtres: ' + ', '.join(filt))
    out = []
    for st in stars:
        x, y = int(round(st['cx'])), int(round(st['cy'])); d = dict(x=x, y=y, r_R=float(r[y, x] / RS), az=float(np.degrees(t[y, x])), pes_vixen=float(np.nan_to_num(WV[y, x])), pic_capa=st['pic'])
        for nom, arr in (('fusio', F), ('vixen', V), ('sony', S)):
            s = stamp(arr, x, y, 1)
            if s is None or not np.isfinite(s).all() or (s <= 0).mean() > 0.2: d[nom] = None; continue
            d[nom] = psf(s)
        d['filtres'] = {}
        for k, arr in filt.items():
            s = stamp(arr, x, y)
            if s is None: continue
            d['filtres'][k] = resposta_filtre(s / 65535.0)
        out.append(d)
    ok = [d for d in out if d.get('fusio') and np.isfinite(d['fusio'].get('elongacio', np.nan))]
    def med(key, tren='fusio', sel=None):
        v = [d[tren][key] for d in (sel or ok) if d.get(tren) and key in d[tren] and np.isfinite(d[tren][key])]; return (float(np.median(v)), len(v)) if v else (np.nan, 0)
    rep = dict(n_estrelles=len(out), n_mesurables=len(ok))
    bright = [d for d in ok if d['fusio']['snr'] > 10]; rep['n_snr_gt_10'] = len(bright)
    for tren in ('fusio', 'vixen', 'sony'):
        sel = [d for d in bright if d.get(tren) and np.isfinite(d[tren].get('elongacio', np.nan)) and d[tren]['snr'] > 5]
        rep[tren] = dict(n=len(sel), fwhm_major_px=med('fwhm_major', tren, sel)[0], fwhm_menor_px=med('fwhm_menor', tren, sel)[0], elongacio=med('elongacio', tren, sel)[0], angle_deg=med('angle_deg', tren, sel)[0], snr=med('snr', tren, sel)[0])
        log(f"{tren}: {len(sel)} estrelles S/N>5 (i S/N fusió>10): FWHM major {rep[tren]['fwhm_major_px']:.1f} px, menor {rep[tren]['fwhm_menor_px']:.1f} px, elongació {rep[tren]['elongacio']:.2f}, angle {rep[tren]['angle_deg']:+.0f}°, S/N mediana {rep[tren]['snr']:.1f}")
    # angle de la traça per tren: histograma d'angles (les traces de deriva tenen un angle comú; el soroll no)
    for tren in ('vixen', 'sony'):
        sel = [d for d in bright if d.get(tren) and d[tren].get('elongacio', 0) > 1.3 and d[tren]['snr'] > 8]
        if sel: angs = np.array([d[tren]['angle_deg'] for d in sel]); c = np.mean(np.exp(2j * np.deg2rad(angs))); rep[tren]['angle_comu_deg'] = float(np.degrees(np.angle(c)) / 2); rep[tren]['coherencia_angle'] = float(abs(c)); rep[tren]['n_elongades'] = len(sel)
        else: rep[tren]['n_elongades'] = 0
        log(f"{tren}: {rep[tren]['n_elongades']} estrelles elongades > 1,3 · angle comú {rep[tren].get('angle_comu_deg', float('nan')):+.0f}° (coherència {rep[tren].get('coherencia_angle', float('nan')):.2f})")
    rep['filtres'] = {}
    for k in filt:
        ex = [d['filtres'][k]['exces_centre_sig'] for d in bright if k in d['filtres']]; mn = [d['filtres'][k]['minim_anell_sig'] for d in bright if k in d['filtres']]; ex2 = [d['filtres'][k]['exces_centre'] for d in bright if k in d['filtres']]; mn2 = [d['filtres'][k]['minim_anell'] for d in bright if k in d['filtres']]
        rep['filtres'][k] = dict(n=len(ex), exces_centre_sig=float(np.median(ex)), minim_anell_sig=float(np.median(mn)), exces_centre=float(np.median(ex2)), minim_anell=float(np.median(mn2)), frac_anell_fosc_gt_3sig=float(np.mean(np.array(mn) < -3)))
        log(f"{k:24s}: al centre +{np.median(ex):.1f} σ ({np.median(ex2):+.3f}), anell fosc {np.median(mn):+.1f} σ ({np.median(mn2):+.3f}); {100 * np.mean(np.array(mn) < -3):.0f} % de les estrelles amb anell < −3 σ")
    rep['estrelles'] = out; savejson(REB41 / 'E1_estrelles.json', rep)
    # galeria 1:1: 24 més brillants; columnes: fusió (log), Vixen, Sony, i cada filtre; escala fixa per columna
    g = sorted(bright, key=lambda d: -d['fusio']['snr'])[:24]; cols = [('fusio', F, 1), ('vixen', V, 1), ('sony', S, 1)] + [(k, arr, None) for k, arr in filt.items()]
    T = 2 * R + 1; sc = 3; canvas = np.full((len(g) * (T * sc + 4) + 40, len(cols) * (T * sc + 4) + 120, 3), 30, np.uint8)
    for j, (k, arr, c) in enumerate(cols): cv2.putText(canvas, k[:14], (120 + j * (T * sc + 4), 26), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    for i, d in enumerate(g):
        cv2.putText(canvas, f"{d['r_R']:.1f}R S/N{d['fusio']['snr']:.0f} e{d['fusio']['elongacio']:.1f}", (4, 40 + i * (T * sc + 4) + T * sc // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 255, 200), 1)
        for j, (k, arr, c) in enumerate(cols):
            s = stamp(arr, d['x'], d['y'], c)
            if s is None: continue
            if c is not None:
                bg = np.median(s); s = np.log10(np.maximum(s - bg + 1e-9, 1e-9) / max(d['fusio']['pic'], 1e-9)); img = np.clip((s + 2.5) / 2.5, 0, 1)   # 2,5 dècades sota el pic
            else:
                s = s / 65535.0; img = np.clip((s - 0.5) / 0.3 + 0.5, 0, 1)   # ±0,15 al voltant del neutre 0,5
            tile = cv2.resize((img * 255).astype(np.uint8), (T * sc, T * sc), interpolation=cv2.INTER_NEAREST); y0, x0 = 40 + i * (T * sc + 4), 120 + j * (T * sc + 4); canvas[y0:y0 + T * sc, x0:x0 + T * sc] = tile[..., None]
    cv2.imwrite(str(VIS41 / 'E1_galeria_estrelles.png'), canvas)
    # mapa al llenç sencer (1/4): base en log + cercles a les estrelles mesurables (verd S/N>10, groc la resta)
    base = np.asarray(F[::4, ::4, 1], np.float32); lg = np.log10(np.maximum(base, 1e-9)); lo, hi = np.percentile(lg[np.isfinite(lg) & (base > 0)], [1, 99.7]); img = cv2.cvtColor((np.clip((lg - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
    for d in ok: cv2.circle(img, (d['x'] // 4, d['y'] // 4), 9, (0, 255, 0) if d['fusio']['snr'] > 10 else (0, 200, 255), 1)
    cv2.imwrite(str(VIS41 / 'E1_mapa_estrelles_quart.png'), img); log('E1 fet')


if __name__ == '__main__':
    main()
