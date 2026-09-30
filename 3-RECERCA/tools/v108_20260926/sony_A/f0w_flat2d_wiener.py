"""f0w · FLAT 2D DE LA SONY AMB PES DE WIENER PER ESCALA (variant de marrons/f0_flat2d_v108.py; no el substitueix).
Per què: la ronda 2 (s10, s11) troba que, després del flat 2D del pilot, als dos apuntaments de la Sony queda un patró FIX AL SENSOR a
les escales fines (el mateix a A i a B: correlació al sensor A×B 0,15 a la banda σ 0,5–2 subplans; i present al flat: A×flat 0,26,
B×flat 0,30). El pilot talla el flat a σ_fi = 2 subplans per no injectar el soroll de fotó del màster, i per això el deixa.
Recepta: per a cada canal CFA, el residu no radial del màster (r = M / perfil radial − 1, el mateix model i centre que la cadena) es
descompon en bandes (diferències de gaussianes normalitzades a la zona visible, σ 0 · 0,5 · 1 · 2 · 4 · 8 · 16 · 32 · 60 subplans).
A cada banda, el SENYAL del flat es mesura amb dues meitats independents del màster (flats parells i senars): S = ⟨r1·r2⟩ (el soroll no
hi correlaciona); el soroll del màster sencer, N = (⟨r1²⟩ + ⟨r2²⟩)/2 − S, dividit per 2. Pes de Wiener W = S / (S + N) (l'estimador
de mínim error: on el flat és sobretot soroll, W → 0 i no s'injecta res). C = 1 + Σ W_b · r_b (fins a σ 60, com el pilot).
Correcció inclosa: el perfil radial als calaixos amb poques mostres (el centre del sensor) s'interpola dels veïns en lloc d'omplir-lo
amb la mediana de tot el perfil (l'error que el verificador va trobar al pilot: un disc de +48,8 % al centre de la Sony).
Nul: --nul desplaça C (x +58, y +84 píxels RAW, fase CFA intacta): un flat desplaçat NO ha de treure el patró de les llums.
Sortida: 4-RESULTATS/v108_20260926/sony_A/flat2d_wiener/SONYTOT_flat2d_wiener[_nul].npz (mateix format que el pilot: C a mida del RAW)
i el rebut JSON. Ús: f0w_flat2d_wiener.py [--nul]"""
import sys, json, glob, argparse, subprocess, hashlib
from pathlib import Path
import numpy as np, cv2, rawpy
from astropy.io import fits
ARREL = Path(__file__).resolve().parents[4]
RI = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/raw_inputs/SONYTOT'; CAL = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/calibration_SONYTOT'
OUT = ARREL / '4-RESULTATS/v108_20260926/sony_A/flat2d_wiener'; OUT.mkdir(parents=True, exist_ok=True)
ap = argparse.ArgumentParser(); ap.add_argument('--nul', action='store_true'); a = ap.parse_args()
fdir = RI / 'flats'
o = subprocess.run(['exiftool', '-q', '-n', '-T', '-FileName', '-ExposureTime', str(fdir)], capture_output=True, text=True).stdout
ex = {l.split('\t')[0]: float(l.split('\t')[1]) for l in o.splitlines() if len(l.split('\t')) >= 2}
grups = {}
for n, e in ex.items(): grups.setdefault(round(e, 8), []).append(n)
e_ref = max(grups, key=lambda k: (len(grups[k]), k)); noms = sorted(grups[e_ref])
dm = json.loads((CAL / '4-rebuts/F0.2_masters_dark.json').read_text())['masters']
kd = min(dm, key=lambda q: abs(float(q) - e_ref)); fdark = str(CAL / '0-calibracio/masters_dark' / dm[kd]['fitxer'])
dark = fits.getdata(fdark).astype(np.float32)
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
SIG = [0.0, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 60.0]
C = np.ones((h_, w_), np.float32); Cvell = np.ones((h_, w_), np.float32)
rep = dict(tren='SONYTOT', exposicio_flat=e_ref, n_flats=len(noms), dark=Path(fdark).name, bandes_sigma_subpla=SIG, nul=a.nul, canals={})
def residu(m, v, ii):
    s = np.bincount(ii[v], m[v], nb); n_ = np.bincount(ii[v], None, nb); ok = n_ > 300; cen = np.arange(nb)
    prof = np.interp(cen, cen[ok], (s / np.maximum(n_, 1))[ok])   # calaixos sense prou mostres: interpolats dels veïns (no la mediana global)
    return np.where(v, m / prof[ii] - 1, 0).astype(np.float32)
for oy in range(2):
    for ox in range(2):
        c = desc[pat[oy, ox]] + ('' if desc[pat[oy, ox]] != 'G' else ('1' if pat[oy, ox] == 1 else '2'))
        sl = (slice(oy, None, 2), slice(ox, None, 2)); v = vis[sl]; ii = idx[sl]
        r, r1, r2 = residu(M[sl], v, ii), residu(M1[sl], v, ii), residu(M2[sl], v, ii)
        wv = v.astype(np.float32); ng = lambda x, sg: x if sg == 0 else cv2.GaussianBlur(x * wv, (0, 0), sg) / np.maximum(cv2.GaussianBlur(wv, (0, 0), sg), 1e-6)
        # zona de mesura del S/N: visible, lluny de la vora (60 subplans) i del centre (on hi havia el disc)
        vv = cv2.erode(v.astype(np.uint8), np.ones((121, 121), np.uint8)).astype(bool)
        hh, ww = v.shape; yy, xx = np.mgrid[0:hh, 0:ww]; vv &= np.hypot(yy - hh / 2, xx - ww / 2) > 60
        rb = np.zeros_like(r); bandes = []
        G = [ng(r, s) for s in SIG]; G1 = [ng(r1, s) for s in SIG]; G2 = [ng(r2, s) for s in SIG]
        for k in range(len(SIG) - 1):
            b, b1, b2 = G[k] - G[k + 1], G1[k] - G1[k + 1], G2[k] - G2[k + 1]
            S = float(np.mean(b1[vv] * b2[vv])); P = 0.5 * float(np.mean(b1[vv] ** 2) + np.mean(b2[vv] ** 2)); Nh = max(P - S, 0.0); N = Nh / 2.0
            Wb = S / (S + N) if S > 0 else 0.0
            rb += np.float32(Wb) * b
            bandes.append(dict(sigma=[SIG[k], SIG[k + 1]], senyal_rms=float(np.sqrt(max(S, 0))), soroll_master_rms=float(np.sqrt(N)), W=Wb))
        vell = np.where(v, ng(r, 2.0) - ng(r, 60.0), 0).astype(np.float32)   # el del pilot (σ_fi 2), però amb el perfil corregit
        rb = np.where(v, rb, 0).astype(np.float32)
        if a.nul: rb = np.roll(rb, (42, 29), axis=(0, 1))   # 84 × 58 píxels RAW: mateixa fase CFA
        C[sl] = 1 + rb; Cvell[sl] = 1 + vell
        rep['canals'][f'{c}@{oy}{ox}'] = dict(bandes=bandes, rb_rms=float(rb[vv].std()), rb_pilot_rms=float(vell[vv].std()), diferencia_rms=float((rb - vell)[vv].std()),
                                               soroll_injectat_rms=float(np.sqrt(sum(bb['W'] ** 2 * bb['soroll_master_rms'] ** 2 for bb in bandes))))
        print(c, ' · '.join(f"σ{bb['sigma'][0]:g}–{bb['sigma'][1]:g}: S {bb['senyal_rms']*1e4:.1f}‱ N {bb['soroll_master_rms']*1e4:.1f}‱ W {bb['W']:.2f}" for bb in bandes), flush=True)
        print(f"   rms C−1: Wiener {rep['canals'][f'{c}@{oy}{ox}']['rb_rms']*1e4:.1f}‱ · pilot {rep['canals'][f'{c}@{oy}{ox}']['rb_pilot_rms']*1e4:.1f}‱ · soroll injectat {rep['canals'][f'{c}@{oy}{ox}']['soroll_injectat_rms']*1e4:.1f}‱", flush=True)
nom = 'SONYTOT_flat2d_wiener' + ('_nul' if a.nul else '')
np.savez_compressed(OUT / f'{nom}.npz', C=C, patró=pat, centre_yx=np.array([CY, CX]), e_ref=e_ref)
rep['sortida'] = str((OUT / f'{nom}.npz').relative_to(ARREL)); rep['sha256'] = hashlib.sha256((OUT / f'{nom}.npz').read_bytes()).hexdigest()
(OUT / f'{nom}_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); print('FET', rep['sortida'])
