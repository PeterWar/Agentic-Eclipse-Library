"""E1f (V41) · Què fan els filtres V38 a les estrelles, mesurat AL PIC REAL (no a la posició de la capa `Estrelles`, que és 25 px enllà: l'E1b hi apilava cel buit).
Per a cada estrella diferent amb pic > 5 σ a la fusió: retall 49 px al pic real, fons i σ de l'anell 14–24, perfil radial en σ; apilat i CONTROL NUL (+40 px).
Per filtre: excés al centre, r½ (radi on el perfil cau a la meitat del centre) contra el de la base, mínim de l'anell 5–16 px (anell fosc) i el seu radi."""
from comu41 import *
from scipy.ndimage import shift as ndshift
PC38 = ROOT / 'research/tools/v38_20260908/purs/cau'; SONY36 = ROOT / 'research/tools/v36_20260908/cau/sony_corrected_total_v36.npy'
FIL = {'base fusió': CAU38 / 'fusion_total_v38.npy', '01 ACHF fi 2-32': CAU38 / '01_v38_u16.npy', '04 ACHF micro 1-16': CAU38 / '04_v38_u16.npy', '05 ACHF fi 2-48': CAU38 / '05_v38_u16.npy', '06 ACHF estructura 4-64': CAU38 / '06_v38_u16.npy',
       'P03 MGN': PC38 / 'P03_MGN_u16.npy', 'P04 WOW': PC38 / 'P04_WOW_u16.npy', 'P05 WOW bilateral': PC38 / 'P05_WOW_bilateral_u16.npy', 'P01 NRGF': PC38 / 'P01_NRGF_u16.npy', 'P02 RHEF': PC38 / 'P02_RHEF_u16.npy', 'P02b RHEF υ 0,35': CAU39 / 'P02b_RHEF_ups0.35_u16.npy'}
R = 24; NUL = (40, 0)


def retall(arr, x, y, dx=0, dy=0):
    x, y = x + dx, y + dy
    if y - R < 0 or x - R < 0 or y + R + 1 > H or x + R + 1 > W: return None
    s = arr[y - R:y + R + 1, x - R:x + R + 1]; s = s[..., 1] if s.ndim == 3 else s; s = np.asarray(s, np.float64); return s if np.isfinite(s).all() else None


def perfil(s):
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]; rr = np.hypot(xx, yy); an = (rr >= 14) & (rr <= 24); bg = np.median(s[an]); sd = 1.4826 * np.median(np.abs(s[an] - bg)) + 1e-12; z = (s - bg) / sd
    prof = np.array([z[(rr >= a) & (rr < a + 1)].mean() for a in range(0, 17)]); return z, prof


def r_mig(prof):
    c = prof[0]
    if c <= 0: return float('nan')
    for a in range(1, len(prof)):
        if prof[a] <= c / 2: return float(a - 1 + (prof[a - 1] - c / 2) / max(prof[a - 1] - prof[a], 1e-9))
    return float(len(prof))


def main():
    rows = json.loads((REB41 / 'E1d_estrelles_dobles.json').read_text())['files']; ok = [r for r in rows if r['fusio'] and r['fusio'][0]['snr'] > 5]
    pos = []
    for r in sorted(ok, key=lambda r: -r['fusio'][0]['snr']):
        p = (r['cat_x'] + r['fusio'][0]['dx'], r['cat_y'] + r['fusio'][0]['dy'], r['r_R'])
        if all(np.hypot(p[0] - q[0], p[1] - q[1]) >= 8 for q in pos): pos.append(p)
    log(f'{len(pos)} estrelles diferents amb pic > 5 σ a la fusió (pic real)'); rep = dict(n=len(pos), estrelles=[dict(x=p[0], y=p[1], r_R=p[2]) for p in pos], filtres={})
    for nom, path in FIL.items():
        arr = np.load(path, mmap_mode='r'); esc = 1.0 if nom.startswith('base') else 65535.0; profs, profn, cen = [], [], []
        for x, y, _ in pos:
            s = retall(arr, x, y); n_ = retall(arr, x, y, *NUL)
            if s is None or n_ is None: continue
            z, p = perfil(s / esc); zn, pn = perfil(n_ / esc); profs.append(p); profn.append(pn); cen.append(p[0])
        P_, Pn = np.mean(profs, 0), np.mean(profn, 0); d = dict(n=len(profs), centre_sigma=float(P_[0]), centre_nul_sigma=float(Pn[0]), r_mig_px=r_mig(P_), anell_min_sigma=float(P_[5:17].min()), anell_min_r_px=int(5 + np.argmin(P_[5:17])), anell_nul_min_sigma=float(Pn[5:17].min()), centre_per_estrella_sigma=[float(c) for c in cen], perfil_sigma=[float(v) for v in P_])
        rep['filtres'][nom] = d; log(f"{nom:24s}: centre {d['centre_sigma']:+6.1f} σ (nul {d['centre_nul_sigma']:+.1f}) · r½ {d['r_mig_px']:4.1f} px · anell mín {d['anell_min_sigma']:+.2f} σ a r={d['anell_min_r_px']} px (nul {d['anell_nul_min_sigma']:+.2f}) · centre per estrella: " + ' '.join(f'{c:+.0f}' for c in cen[:8]))
    b = rep['filtres']['base fusió']['r_mig_px']
    for nom, d in rep['filtres'].items(): d['eixamplament_vs_base'] = float(d['r_mig_px'] / b) if np.isfinite(d['r_mig_px']) and b > 0 else float('nan')
    savejson(REB41 / 'E1f_filtres_al_pic_real.json', rep); log('E1f fet')


if __name__ == '__main__':
    main()
