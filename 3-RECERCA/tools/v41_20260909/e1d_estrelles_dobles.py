"""E1d (V41) · On són DE VERITAT les estrelles a la base, i per què no tenen una PSF neta. La galeria E1b ensenya que les taques brillants NO són al centre del
retall (posició de la capa `Estrelles`) sinó desplaçades desenes de píxels, i sovint DOBLES. Aquí, per a cada estrella del catàleg: (1) el pic real a la fusió dins
de ±60 px (suavitzat σ=2, > 4 σ); (2) el pic a cada apuntament de la Sony (A i B, mitjana de les seves meitats pA/pB) i a la Vixen; (3) la separació A–B
(= residu de registre entre apuntaments a la posició de l'estrella) i l'elongació de cada component. Galeria 1:1 ×4 centrada al pic REAL: fusió, Sony A, Sony B,
Vixen, i P03/P04/01 (filtres V38)."""
from comu41 import *
import cv2
from scipy.ndimage import gaussian_filter, maximum_filter, label, center_of_mass
SONY36 = ROOT / 'research/tools/v36_20260908/cau/sony_corrected_total_v36.npy'; PC38 = ROOT / 'research/tools/v38_20260908/purs/cau'
STARS = Path('/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/bb2a9ec7-d793-44f1-a277-703c16855cd4/scratchpad/estrelles_v39.json'); R = 60


def crop(arr, x, y, c=None):
    if y - R < 0 or x - R < 0 or y + R + 1 > H or x + R + 1 > W: return None
    s = arr[y - R:y + R + 1, x - R:x + R + 1]; s = s[..., c] if (c is not None and s.ndim == 3) else s; s = np.asarray(s, np.float64); return s if np.isfinite(s).all() and (s > 0).mean() > 0.9 else None


def pics(s, k=2.0, thr=4.0, nmax=3):
    """pics del retall suavitzat, en σ del fons (MAD), dins de r ≤ 50; retorna [(dx, dy, snr, fwhm_major, fwhm_menor, angle)]"""
    g = gaussian_filter(s, k); bg = np.median(g); sd = 1.4826 * np.median(np.abs(g - bg)) + 1e-12; z = (g - bg) / sd; yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; rr = np.hypot(xx, yy)
    pk = (z == maximum_filter(z, 11)) & (z > thr) & (rr <= 50); ys, xs = np.where(pk); o = np.argsort(z[ys, xs])[::-1][:nmax]; out = []
    for i in o:
        y, x = ys[i], xs[i]; w = np.where((np.hypot(xx - (x - R), yy - (y - R)) <= 7) & (z > 0.5), z, 0); W_ = w.sum()
        mx, my = (w * xx).sum() / W_, (w * yy).sum() / W_; cxx = (w * (xx - mx) ** 2).sum() / W_; cyy = (w * (yy - my) ** 2).sum() / W_; cxy = (w * (xx - mx) * (yy - my)).sum() / W_
        tr, det = cxx + cyy, cxx * cyy - cxy ** 2; q = np.sqrt(max(tr * tr / 4 - det, 0)); l1, l2 = tr / 2 + q, max(tr / 2 - q, 1e-9)
        out.append(dict(dx=int(x - R), dy=int(y - R), snr=float(z[y, x]), fwhm_major=float(2.355 * np.sqrt(l1)), fwhm_menor=float(2.355 * np.sqrt(l2)), elongacio=float(np.sqrt(l1 / l2)), angle_deg=float(0.5 * np.degrees(np.arctan2(2 * cxy, cxx - cyy)))))
    return out


def main():
    stars = json.loads(STARS.read_text()); r, t = coords()
    F = np.load(CAU38 / 'fusion_total_v38.npy', mmap_mode='r'); V = np.load(CAU38 / 'vixen_total_v38.npy', mmap_mode='r'); S = np.load(SONY36, mmap_mode='r'); WV = np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r')
    SA = [np.load(CAU39 / f'sony_A_total_v38_{h}.npy', mmap_mode='r') for h in ('pA', 'pB')]; SB = [np.load(CAU39 / f'sony_B_total_v38_{h}.npy', mmap_mode='r') for h in ('pA', 'pB')]
    FIL = {'01 ACHF': CAU38 / '01_v38_u16.npy', 'P03 MGN': PC38 / 'P03_MGN_u16.npy', 'P04 WOW': PC38 / 'P04_WOW_u16.npy'}; fil = {k: np.load(p, mmap_mode='r') for k, p in FIL.items()}
    rows = []
    for st in stars:
        x, y = int(round(st['cx'])), int(round(st['cy'])); rR = float(r[y, x] / RS)
        if rR < 2.2: continue
        sF = crop(F, x, y, 1)
        if sF is None: continue
        pF = pics(sF); d = dict(cat_x=x, cat_y=y, r_R=round(rR, 2), pes_vixen=float(np.nan_to_num(WV[y, x])), fusio=pF)
        for nom, arr in (('vixen', V), ('sony', S)):
            s = crop(arr, x, y, 1); d[nom] = pics(s) if s is not None else None
        for nom, pair in (('sonyA', SA), ('sonyB', SB)):
            a, b = crop(pair[0], x, y, 1), crop(pair[1], x, y, 1); d[nom] = pics((a + b) / 2) if (a is not None and b is not None) else None
        if d.get('sonyA') and d.get('sonyB'):
            a, b = d['sonyA'][0], d['sonyB'][0]; d['sep_AB_px'] = [b['dx'] - a['dx'], b['dy'] - a['dy']]; d['sep_AB'] = float(np.hypot(*d['sep_AB_px']))
        rows.append(d)
    ok = [d for d in rows if d['fusio']]
    log(f"{len(rows)} estrelles a r > 2,2 R☉ · {len(ok)} amb pic > 4 σ a la fusió (suavitzat σ=2) dins de ±60 px")
    off = np.array([[d['fusio'][0]['dx'], d['fusio'][0]['dy']] for d in ok]); log(f"desplaçament del pic real respecte de la capa Estrelles: mediana ({np.median(off[:, 0]):+.0f}, {np.median(off[:, 1]):+.0f}) px, |d| mediana {np.median(np.hypot(off[:, 0], off[:, 1])):.0f} px, rang {np.hypot(off[:, 0], off[:, 1]).min():.0f}–{np.hypot(off[:, 0], off[:, 1]).max():.0f}")
    dob = [d for d in ok if len(d['fusio']) >= 2 and d['fusio'][1]['snr'] > 4 and np.hypot(d['fusio'][1]['dx'] - d['fusio'][0]['dx'], d['fusio'][1]['dy'] - d['fusio'][0]['dy']) < 30]
    log(f"dobles a la fusió (segon pic > 4 σ a < 30 px): {len(dob)} de {len(ok)}; separació mediana {np.median([np.hypot(d['fusio'][1]['dx'] - d['fusio'][0]['dx'], d['fusio'][1]['dy'] - d['fusio'][0]['dy']) for d in dob]) if dob else float('nan'):.1f} px")
    ab = [d for d in ok if 'sep_AB' in d and d['sonyA'][0]['snr'] > 4 and d['sonyB'][0]['snr'] > 4]
    if ab: log(f"separació Sony A–B al mateix estel ({len(ab)} estrelles): mediana {np.median([d['sep_AB'] for d in ab]):.1f} px; vectors " + ', '.join(f"({d['sep_AB_px'][0]:+d},{d['sep_AB_px'][1]:+d}) a {d['r_R']:.1f}R" for d in ab[:10]))
    for nom in ('fusio', 'sonyA', 'sonyB', 'vixen'):
        el = [d[nom][0] for d in ok if d.get(nom) and d[nom][0]['snr'] > 5]
        if el: log(f"{nom}: {len(el)} components > 5 σ · FWHM major {np.median([e['fwhm_major'] for e in el]):.1f} px, menor {np.median([e['fwhm_menor'] for e in el]):.1f} px, elongació {np.median([e['elongacio'] for e in el]):.2f}, angle mediana {np.median([e['angle_deg'] for e in el]):+.0f}°")
    savejson(REB41 / 'E1d_estrelles_dobles.json', dict(files=rows))
    # galeria centrada al pic real (12 més fortes): fusió, Sony A, Sony B, Vixen, 01, P03, P04; ±5 σ-píxel a la base, ±0,15 als filtres; 1:1 ×4, 41 px
    g = sorted(ok, key=lambda d: -d['fusio'][0]['snr'])[:12]; RR = 20; Z = 4; T = 2 * RR + 1; cols = ['fusio', 'Sony A', 'Sony B', 'Vixen', '01 ACHF', 'P03 MGN', 'P04 WOW']
    canvas = np.full((len(g) * (T * Z + 6) + 30, len(cols) * (T * Z + 6) + 250, 3), 25, np.uint8)
    for j, h in enumerate(cols): cv2.putText(canvas, h, (250 + j * (T * Z + 6) + 2, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    def tile_base(arr, x, y, c=1):
        s = np.asarray(arr[y - RR:y + RR + 1, x - RR:x + RR + 1][..., c], np.float64); bg = np.median(s); sd = 1.4826 * np.median(np.abs(s - bg)) + 1e-12; return np.clip(((s - bg) / sd / 5 + 1) / 2, 0, 1)
    for i, d in enumerate(g):
        x, y = d['cat_x'] + d['fusio'][0]['dx'], d['cat_y'] + d['fusio'][0]['dy']
        srcs = [tile_base(F, x, y), tile_base((np.asarray(SA[0][y - RR:y + RR + 1, x - RR:x + RR + 1]) + np.asarray(SA[1][y - RR:y + RR + 1, x - RR:x + RR + 1])) / 2, RR, RR) if crop(SA[0], x, y, 1) is not None else None,
                tile_base((np.asarray(SB[0][y - RR:y + RR + 1, x - RR:x + RR + 1]) + np.asarray(SB[1][y - RR:y + RR + 1, x - RR:x + RR + 1])) / 2, RR, RR) if crop(SB[0], x, y, 1) is not None else None,
                tile_base(V, x, y) if crop(V, x, y, 1) is not None else None] + [np.clip((np.asarray(fil[k][y - RR:y + RR + 1, x - RR:x + RR + 1], np.float64) / 65535 - 0.5) / 0.3 + 0.5, 0, 1) for k in fil]
        for j, tl in enumerate(srcs):
            if tl is None: continue
            img = cv2.resize((tl * 255).astype(np.uint8), (T * Z, T * Z), interpolation=cv2.INTER_NEAREST); y0, x0 = 30 + i * (T * Z + 6), 250 + j * (T * Z + 6); canvas[y0:y0 + T * Z, x0:x0 + T * Z] = img[..., None]
        f0 = d['fusio'][0]; cv2.putText(canvas, f"({x},{y}) {d['r_R']:.1f}R {f0['snr']:.0f}s e{f0['elongacio']:.1f} {f0['angle_deg']:+.0f}deg" + (f" AB {d['sep_AB']:.0f}px" if 'sep_AB' in d else ''), (4, 30 + i * (T * Z + 6) + T * Z // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (200, 255, 200), 1)
    cv2.imwrite(str(VIS41 / 'E1d_galeria_pic_real.png'), canvas); log('E1d fet')


if __name__ == '__main__':
    main()
