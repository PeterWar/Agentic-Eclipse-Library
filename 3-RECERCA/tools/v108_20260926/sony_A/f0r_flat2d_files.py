"""f0r · LA REIXA DE FILES DEL SENSOR DE LA SONY, a l'origen (variant del flat 2D del pilot; no el substitueix).
Troballa (ronda 2, s11/s16): el sensor de l'A7R III té un patró de files amb període 12 files RAW (6 subplans), el de les files dels
píxels d'enfocament. És al flat (pic de l'espectre de files ×1.267 la mediana) i a les llums dels DOS apuntaments; el flat 2D del pilot
(σ_fi = 2 subplans) gairebé no el toca (és més fi que el seu tall). Al llenç és una reixa de línies paral·leles a les files, cada 17,9 px:
pic ×155 a l'apilat A, ×63 a la base i ×131 al compost de la cadena de la V107.
Cura: un factor de guany per FILA (fi en y, llis en x) mesurat al mateix màster de flats: g = part de files del residu que el pilot no
porta (r − banda del pilot), suavitzada NOMÉS al llarg de la fila (σx 200 subplans, convolució normalitzada a la zona visible) i passa-alt
en y (σy 8 files: només l'estructura de files). En mitjanar milers de píxels per fila, el soroll del màster hi és ~50 vegades menor que
al flat 2D. Pes de Wiener amb dues meitats del màster (parells/senars). C_nou = C_pilot · (1 + W·g), per canal CFA. Res més canvia.
Nul (--nul): g desplaçat 3 files de subplà (mitja reixa): ha d'EMPITJORAR la reixa de les llums.
Sortida: 4-RESULTATS/v108_20260926/sony_A/flat2d_files/SONYTOT_flat2d_files[_nul].npz (format del pilot) i el rebut."""
import sys, json, argparse, subprocess, hashlib
from pathlib import Path
import numpy as np, cv2, rawpy
from astropy.io import fits
ARREL = Path(__file__).resolve().parents[4]
RI = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/raw_inputs/SONYTOT'; CAL = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/calibration_SONYTOT'
PILOT = ARREL / '4-RESULTATS/v108_20260926/marrons/flat2d/SONYTOT_flat2d.npz'
OUT = ARREL / '4-RESULTATS/v108_20260926/sony_A/flat2d_files'; OUT.mkdir(parents=True, exist_ok=True)
ap = argparse.ArgumentParser(); ap.add_argument('--nul', action='store_true'); a = ap.parse_args()
fdir = RI / 'flats'
o = subprocess.run(['exiftool', '-q', '-n', '-T', '-FileName', '-ExposureTime', str(fdir)], capture_output=True, text=True).stdout
ex = {l.split('\t')[0]: float(l.split('\t')[1]) for l in o.splitlines() if len(l.split('\t')) >= 2}
grups = {}
for n, e in ex.items(): grups.setdefault(round(e, 8), []).append(n)
e_ref = max(grups, key=lambda k: (len(grups[k]), k)); noms = sorted(grups[e_ref])
dm = json.loads((CAL / '4-rebuts/F0.2_masters_dark.json').read_text())['masters']
kd = min(dm, key=lambda q: abs(float(q) - e_ref)); fdark = str(CAL / '0-calibracio/masters_dark' / dm[kd]['fitxer']); dark = fits.getdata(fdark).astype(np.float32)
with rawpy.imread(str(fdir / noms[0])) as r:
    h_, w_ = r.raw_image.shape; sz = r.sizes; pat = r.raw_pattern.copy(); desc = r.color_desc.decode()
pila = np.empty((len(noms), h_, w_), np.uint16)
for i, n in enumerate(noms):
    with rawpy.imread(str(fdir / n)) as r: pila[i] = r.raw_image
def mediana(ix):
    med = np.empty((h_, w_), np.float32)
    for y0 in range(0, h_, 256): med[y0:y0 + 256] = np.median(pila[ix, y0:y0 + 256].astype(np.float32), axis=0)
    return med - dark
M = mediana(np.arange(len(noms))); M1 = mediana(np.arange(0, len(noms), 2)); M2 = mediana(np.arange(1, len(noms), 2)); del pila
vis = np.zeros((h_, w_), bool); vis[sz.top_margin:sz.top_margin + sz.height, sz.left_margin:sz.left_margin + sz.width] = True
CY, CX = h_ / 2.0, w_ / 2.0; yy, xx = np.mgrid[0:h_, 0:w_].astype(np.float32); rad = np.hypot(yy - CY, xx - CX); del yy, xx
RMAX = float(rad[vis].max()); nb = 260; idx = np.clip((rad / RMAX * nb).astype(np.int32), 0, nb - 1)
Cp = np.load(PILOT)['C'].astype(np.float32); C = Cp.copy()
rep = dict(tren='SONYTOT', n_flats=len(noms), base='C del pilot (marrons/flat2d/SONYTOT_flat2d.npz)', sigma_x=200, sigma_y_passaalt=8, nul=a.nul, canals={})
def residu(m, v, ii):
    s = np.bincount(ii[v], m[v], nb); n_ = np.bincount(ii[v], None, nb); ok = n_ > 300; cen = np.arange(nb)
    prof = np.interp(cen, cen[ok], (s / np.maximum(n_, 1))[ok]); return np.where(v, m / prof[ii] - 1, 0).astype(np.float32)
def g_files(r, v):
    wv = v.astype(np.float32)
    ngx = lambda x: cv2.GaussianBlur(x * wv, (0, 0), sigmaX=200, sigmaY=0.3) / np.maximum(cv2.GaussianBlur(wv, (0, 0), sigmaX=200, sigmaY=0.3), 1e-6)
    ngp = lambda x, s: cv2.GaussianBlur(x * wv, (0, 0), s) / np.maximum(cv2.GaussianBlur(wv, (0, 0), s), 1e-6)
    band = r - (ngp(r, 2.0) - ngp(r, 60.0))                 # el que el pilot NO porta
    sx = ngx(band); lowy = cv2.GaussianBlur(sx, (0, 0), sigmaX=0.3, sigmaY=8)
    return np.where(v, sx - lowy, 0).astype(np.float32)
for oy in range(2):
    for ox in range(2):
        c = desc[pat[oy, ox]] + ('' if desc[pat[oy, ox]] != 'G' else ('1' if pat[oy, ox] == 1 else '2'))
        sl = (slice(oy, None, 2), slice(ox, None, 2)); v = vis[sl]; ii = idx[sl]
        g, g1, g2 = (g_files(residu(m_[sl], v, ii), v) for m_ in (M, M1, M2))
        vv = cv2.erode(v.astype(np.uint8), np.ones((61, 61), np.uint8)).astype(bool)
        S = float(np.mean(g1[vv] * g2[vv])); P = 0.5 * float(np.mean(g1[vv] ** 2) + np.mean(g2[vv] ** 2)); N = max(P - S, 0.0) / 2.0; Wb = S / (S + N) if S > 0 else 0.0
        gg = Wb * g
        if a.nul: gg = np.roll(gg, 3, axis=0)
        C[sl] = Cp[sl] * (1 + gg)
        # espectre de files del g (període 6 subplans)
        rows = g[200:-200, :][:, v[0]].mean(1); F = np.abs(np.fft.rfft(rows * np.hanning(len(rows)))) ** 2; f = np.fft.rfftfreq(len(rows)); k6 = np.argmin(np.abs(f - 1 / 6))
        rep['canals'][f'{c}@{oy}{ox}'] = dict(g_rms=float(g[vv].std()), senyal_rms=float(np.sqrt(max(S, 0))), soroll_master_rms=float(np.sqrt(N)), W=Wb, pic_periode_6_sobre_mediana=float(F[k6 - 1:k6 + 2].max() / np.median(F[5:])))
        print(c, {k: round(v_, 6) if isinstance(v_, float) else v_ for k, v_ in rep['canals'][f'{c}@{oy}{ox}'].items()}, flush=True)
nom = 'SONYTOT_flat2d_files' + ('_nul' if a.nul else '')
np.savez_compressed(OUT / f'{nom}.npz', C=C, patró=pat, centre_yx=np.array([CY, CX]), e_ref=e_ref)
rep['sortida'] = str((OUT / f'{nom}.npz').relative_to(ARREL)); rep['sha256'] = hashlib.sha256((OUT / f'{nom}.npz').read_bytes()).hexdigest()
(OUT / f'{nom}_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); print('FET', rep['sortida'])
