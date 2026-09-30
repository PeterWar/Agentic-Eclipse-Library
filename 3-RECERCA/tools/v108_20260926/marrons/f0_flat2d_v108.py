"""f0_flat2d (V108, marrons) · LA PART NO RADIAL DEL FLAT, que el F0.3 de la cadena (flat RADIAL, `f0.flat_radial`) no pot representar.
Causa trobada (M12–M15): el flat radial deixa a cada fotograma l'estructura fixa del sensor i de l'òptica que no és un cercle al voltant
del centre del sensor (línies i arcs de vinyetatge, pols, textura de guany); passa a l'apilat perquè el registre només la desplaça uns
píxels (Vixen 18 px en 100 s; Sony 0–8 px dins de cada apuntament), i les WOW la fan visible. Correlació residu del flat ↔ apilat
(banda σ 2–30 px, camp exterior): Vixen 0,59 (pendent 0,65), Sony A 0,32 (0,46); nul desplaçat 150 px: 0,00.
Recepta (mateixa que F0.3 excepte el model): màster = mediana de TOTS els flats de l'exposició majoritària menys el dark del run;
per a cada canal CFA, residu r = màster / (el seu perfil radial, mateix centre declarat i 260 calaixos) − 1; es desa NOMÉS la banda
validada: r_b = G(r, σ_fi) − G(r, σ_gran) (convolució normalitzada a la zona visible, a la graella de cada subpla), amb σ_fi = 1 subpla
(treu el soroll de fotó del màster) i σ_gran = 60 subplans (les escales grans del flat de cel no es toquen: el nivell el porten el B1 i la fusió).
Sortida: <out>/<TREN>_flat2d.npz amb C = 1 + r_b (mosaic CFA a mida del RAW, float32; el flat 2D és FLAT_RADIAL · C) i el rebut JSON.
Ús: f0_flat2d_v108.py VIXEN|SONYTOT [--sigma-fi 1.0] [--sigma-gran 60]"""
import sys, os, json, glob, argparse, subprocess, hashlib
from pathlib import Path
import numpy as np, cv2, rawpy
from astropy.io import fits
ARREL = Path(__file__).resolve().parents[4]
RI = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/raw_inputs'; CAL = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
ap = argparse.ArgumentParser(); ap.add_argument('tren', choices=['VIXEN', 'SONYTOT']); ap.add_argument('--sigma-fi', type=float, default=1.0); ap.add_argument('--sigma-gran', type=float, default=60.0)
ap.add_argument('--out', default=str(ARREL / '4-RESULTATS/v108_20260926/marrons/flat2d'))
a = ap.parse_args(); OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
fdir = RI / a.tren / 'flats'
o = subprocess.run(['exiftool', '-q', '-n', '-T', '-FileName', '-ExposureTime', str(fdir)], capture_output=True, text=True).stdout
ex = {l.split('\t')[0]: float(l.split('\t')[1]) for l in o.splitlines() if len(l.split('\t')) >= 2}
grups = {}
for n, e in ex.items(): grups.setdefault(round(e, 8), []).append(n)
e_ref = max(grups, key=lambda k: (len(grups[k]), k)); noms = sorted(grups[e_ref])
# dark del run (F0.2), el més proper a l'exposició del flat, com f0.dark_de
dm = json.loads((CAL / f'calibration_{a.tren}/4-rebuts/F0.2_masters_dark.json').read_text())['masters'] if (CAL / f'calibration_{a.tren}/4-rebuts/F0.2_masters_dark.json').exists() else None
if dm is None:
    fitxers = sorted(glob.glob(str(CAL / f'calibration_{a.tren}/0-calibracio/masters_dark/MD_E*.fits')))
    ed = {float(Path(f).stem.split('MD_E')[1].rstrip('s')): f for f in fitxers}; kd = min(ed, key=lambda q: abs(q - e_ref)); fdark = ed[kd]
else:
    kd = min(dm, key=lambda q: abs(float(q) - e_ref)); fdark = str(CAL / f'calibration_{a.tren}/0-calibracio/masters_dark' / dm[kd]['fitxer'])
dark = fits.getdata(fdark).astype(np.float32)
with rawpy.imread(str(fdir / noms[0])) as r:
    h_, w_ = r.raw_image.shape; sz = r.sizes; pat = r.raw_pattern.copy(); desc = r.color_desc.decode()
pila = np.empty((len(noms), h_, w_), np.uint16)
for i, n in enumerate(noms):
    with rawpy.imread(str(fdir / n)) as r: pila[i] = r.raw_image
# màster (mediana) i dues meitats (per al soroll del màster)
def mediana(ix):
    med = np.empty((h_, w_), np.float32)
    for y0 in range(0, h_, 256): med[y0:y0 + 256] = np.median(pila[ix, y0:y0 + 256].astype(np.float32), axis=0)
    return med - dark
M = mediana(np.arange(len(noms))); M1 = mediana(np.arange(0, len(noms), 2)); M2 = mediana(np.arange(1, len(noms), 2)); del pila
# zona visible i centre declarat (com f0.flat_radial: CY, CX = alt/2, ample/2 del RAW)
vis = np.zeros((h_, w_), bool); vis[sz.top_margin:sz.top_margin + sz.height, sz.left_margin:sz.left_margin + sz.width] = True
CY, CX = h_ / 2.0, w_ / 2.0; yy, xx = np.mgrid[0:h_, 0:w_].astype(np.float32); rad = np.hypot(yy - CY, xx - CX); del yy, xx
RMAX = float(rad[vis].max()); nb = 260; idx = np.clip((rad / RMAX * nb).astype(np.int32), 0, nb - 1)
C = np.ones((h_, w_), np.float32); rep = dict(tren=a.tren, exposicio_flat=e_ref, n_flats=len(noms), dark=Path(fdark).name, sigma_fi=a.sigma_fi, sigma_gran=a.sigma_gran, canals={})
for oy in range(2):
    for ox in range(2):
        c = desc[pat[oy, ox]] + ('' if desc[pat[oy, ox]] != 'G' else ('1' if pat[oy, ox] == 1 else '2'))
        sl = (slice(oy, None, 2), slice(ox, None, 2)); m = M[sl]; v = vis[sl]; ii = idx[sl]
        s = np.bincount(ii[v], m[v], nb); n_ = np.bincount(ii[v], None, nb); prof = np.where(n_ > 300, s / np.maximum(n_, 1), np.nan)
        prof = np.where(np.isfinite(prof), prof, np.nanmedian(prof)); r = np.where(v, m / prof[ii] - 1, 0).astype(np.float32)
        wv = v.astype(np.float32); ng = lambda x, sg: cv2.GaussianBlur(x * wv, (0, 0), sg) / np.maximum(cv2.GaussianBlur(wv, (0, 0), sg), 1e-6)
        rb = np.where(v, ng(r, a.sigma_fi) - ng(r, a.sigma_gran), 0).astype(np.float32)
        C[sl] = 1 + rb
        # soroll del màster que s'injectaria: meitats → σ(M1−M2)/2 relatiu, i després del suavitzat σ_fi
        d = np.where(v, (M1[sl] - M2[sl]) / np.maximum(m, 1e-6), 0).astype(np.float32); ds = ng(d, a.sigma_fi)
        rep['canals'][f'{c}@{oy}{ox}'] = dict(rb_p1_p50_p99=np.percentile(rb[v], [1, 50, 99]).round(6).tolist(), rb_rms=float(rb[v].std()),
                                           soroll_master_px=float(0.5 * d[v].std()), soroll_master_despres_sigma_fi=float(0.5 * ds[v].std()))
        print(a.tren, c, rep['canals'][f'{c}@{oy}{ox}'], flush=True)
np.savez_compressed(OUT / f'{a.tren}_flat2d.npz', C=C, patró=pat, centre_yx=np.array([CY, CX]), e_ref=e_ref)
rep['sortida'] = str((OUT / f'{a.tren}_flat2d.npz').resolve().relative_to(ARREL)); rep['sha256'] = hashlib.sha256((OUT / f'{a.tren}_flat2d.npz').read_bytes()).hexdigest()
(OUT / f'{a.tren}_flat2d_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); print('FET', rep['sortida'])
