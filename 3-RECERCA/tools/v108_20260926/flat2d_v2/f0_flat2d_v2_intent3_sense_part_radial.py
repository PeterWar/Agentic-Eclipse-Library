"""[INTENT 3, DESCARTAT: la mitjana per anells treia els arcs fins del flat (T3, T5); vegeu f0_flat2d_v2.py] f0_flat2d_v2 (V108, flat 2D lliurable) · LA PART NO RADIAL DEL FLAT, corregida després del verificador de la ronda 1.

Què canvia respecte del pilot (marrons/f0_flat2d_v108.py), i per què:
  1. EL PERFIL RADIAL DE REFERÈNCIA. El pilot feia el perfil amb 260 calaixos i omplia els que tenen < 300 mostres (el calaix 0, r < 18,5 px
     del RAW) amb la MEDIANA de tot el perfil. Al centre del sensor això fabricava un disc a C: +48,8 % a la Sony, +2 % a la Vixen.
     Ara el perfil és fi (calaixos de 2 px del RAW, ≥ 40 mostres), els calaixos del centre s'omplen amb un ajust parabòlic en r² dels veïns
     (r < 200 px; el vinyetatge hi és ∝ r²) i el perfil es suavitza σ 4 px. Així C no té cap part radial: és només l'estructura fixa
     del sensor que un model radial no pot representar.
  2. C NO TÉ PART RADIAL. Després del pas banda (σ_fi − σ_gran, com el pilot), es treu la mitjana de C per anells (2 px, suavitzada σ 4 px):
     C conserva les línies, arcs, pols i textura de guany, però no toca el perfil radial de la cadena (ni els seus calaixos, ni el
     «ghost» del centre, que és el calaix 0 del FLAT_RADIAL de la cadena: vegeu el rebut). ÚNIC CANVI = la part no radial.
  3. VORES DEL SENSOR. C s'esvaeix (smoothstep) als 100 px del RAW de la vora de la zona visible: allà el flat de cel és el menys fiable.
  4. PÍXELS DEFECTUOSOS AÏLLATS (|q − mediana 3×3| > 8σ robustes de la resposta píxel a píxel): es deixen com a la cadena. Un píxel
     defectuós no és estructura del flat, i el suavitzat σ_fi n'escamparia la correcció als veïns. La resposta píxel a píxel normal del
     sensor (PRNU) sí que es conserva: és real (hi és també als flats invertits, amb el cos girat 173,5°).
  5. PORTES que aturen: mitjana per anells (suavitzada σ 4 px, 50 px ≤ r < radi inscrit) |<C − 1>| < 0,02 % i disc central |C − 1| < 0,5 %.
     Porta informativa: |C − 1| < 3 % a ≥ 100 px de la vora (se'n compten els píxels que la passen).
Recepta comuna amb F0.3: màster = mediana de TOTS els flats de l'exposició majoritària menys el dark del run, centre DECLARAT (alt/2, ample/2).
Sortida: <out>/<TREN>_flat2d_v2.npz (C, mosaic CFA a mida del RAW, float32; el flat 2D és FLAT_RADIAL · C) i <TREN>_flat2d_v2_REBUT.json,
amb el diagnòstic del calaix 0 del FLAT_RADIAL de la cadena (el disc del centre del sensor).
Ús: f0_flat2d_v2.py VIXEN|SONYTOT [--sigma-fi 1.0] [--sigma-gran 60] [--vora-px 100]"""
import sys, os, json, glob, argparse, subprocess, hashlib, time
from pathlib import Path
import numpy as np, cv2, rawpy
from astropy.io import fits
ARREL = Path(__file__).resolve().parents[4]
RI = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/raw_inputs'; CAL = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
ap = argparse.ArgumentParser(); ap.add_argument('tren', choices=['VIXEN', 'SONYTOT']); ap.add_argument('--sigma-fi', type=float, default=None)
ap.add_argument('--sigma-gran', type=float, default=60.0); ap.add_argument('--vora-px', type=float, default=100.0)
ap.add_argument('--out', default=str(ARREL / '4-RESULTATS/v108_20260926/flat2d_v2/flat2d'))
a = ap.parse_args(); OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True); t0 = time.time()
SFI = a.sigma_fi if a.sigma_fi is not None else (1.0 if a.tren == 'VIXEN' else 2.0)   # els del pilot (validats a M14/M15)
fdir = RI / a.tren / 'flats'
o = subprocess.run(['exiftool', '-q', '-n', '-T', '-FileName', '-ExposureTime', str(fdir)], capture_output=True, text=True).stdout
ex = {l.split('\t')[0]: float(l.split('\t')[1]) for l in o.splitlines() if len(l.split('\t')) >= 2}
grups = {}
for n, e in ex.items(): grups.setdefault(round(e, 8), []).append(n)
e_ref = max(grups, key=lambda k: (len(grups[k]), k)); noms = sorted(grups[e_ref])
dm = json.loads((CAL / f'calibration_{a.tren}/4-rebuts/F0.2_masters_dark.json').read_text())['masters']
kd = min(dm, key=lambda q: abs(float(q) - e_ref)); fdark = str(CAL / f'calibration_{a.tren}/0-calibracio/masters_dark' / dm[kd]['fitxer'])
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
print(a.tren, 'màster fet', len(noms), 'flats', f'{time.time()-t0:.0f}s', flush=True)
vis = np.zeros((h_, w_), bool); T_, L_ = sz.top_margin, sz.left_margin; B_, R_ = T_ + sz.height, L_ + sz.width; vis[T_:B_, L_:R_] = True
CY, CX = h_ / 2.0, w_ / 2.0; yy, xx = np.mgrid[0:h_, 0:w_].astype(np.float32); rad = np.hypot(yy - CY, xx - CX)
dvora = np.minimum(np.minimum(yy - T_, (B_ - 1) - yy), np.minimum(xx - L_, (R_ - 1) - xx)).astype(np.float32); del yy, xx   # px del RAW a la vora visible
FR = fits.getdata(CAL / f'calibration_{a.tren}/0-calibracio/FLAT_RADIAL.fits').astype(np.float32)   # només per al diagnòstic (no entra a C)
def smoothstep(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
TAPER = smoothstep(dvora / a.vora_px).astype(np.float32)
BIN = 2.0; nbin = int(rad[vis].max() / BIN) + 2; rc = (np.arange(nbin) + 0.5) * BIN
def perfil_fi(vals, rr, minim=40):
    ib = (rr / BIN).astype(np.int32); n = np.bincount(ib, None, nbin); s = np.bincount(ib, vals, nbin)
    p = np.where(n >= minim, s / np.maximum(n, 1), np.nan); return p, n
def gs1(p, s):
    ok = np.isfinite(p).astype(np.float64); q = np.where(ok > 0, p, 0.0)
    from scipy.ndimage import gaussian_filter1d
    return gaussian_filter1d(q, s, mode='nearest') / np.maximum(gaussian_filter1d(ok, s, mode='nearest'), 1e-9)
C = np.ones((h_, w_), np.float32)
rep = dict(tren=a.tren, exposicio_flat=e_ref, n_flats=len(noms), dark=Path(fdark).name, sigma_fi_subplans=SFI, sigma_gran_subplans=a.sigma_gran, vora_px_RAW=a.vora_px,
           perfil_radial=dict(calaix_px_RAW=BIN, mostres_minimes=40, centre='ajust a + b·r² + c·r⁴ als calaixos vàlids de r < 200 px', suavitzat_px=4.0),
           centre_yx=[CY, CX], canals={})
for oy in range(2):
    for ox in range(2):
        c = desc[pat[oy, ox]] + ('' if desc[pat[oy, ox]] != 'G' else ('1' if pat[oy, ox] == 1 else '2'))
        sl = (slice(oy, None, 2), slice(ox, None, 2)); m = M[sl]; v = vis[sl]; rr = rad[sl]
        p, n = perfil_fi(m[v], rr[v])
        # centre: calaixos buits o pobres de r < 200 px → ajust parabòlic en r² als veïns vàlids (pes n)
        k = np.isfinite(p) & (rc < 200)
        A_ = np.stack([np.ones(k.sum()), rc[k] ** 2, rc[k] ** 4], 1); wq = np.sqrt(n[k]); coef = np.linalg.lstsq(A_ * wq[:, None], p[k] * wq, rcond=None)[0]
        buits_centre = (~np.isfinite(p)) & (rc < 200); p = np.where(buits_centre, coef[0] + coef[1] * rc ** 2 + coef[2] * rc ** 4, p)
        # vores extremes (cantonades amb poques mostres): el valor vàlid més proper cap endins
        jv = np.where(np.isfinite(p))[0]; p[jv[-1] + 1:] = p[jv[-1]]
        ps = gs1(np.log(np.maximum(p, 1e-6)), 4.0 / BIN); prof = np.exp(np.interp(rr, rc, ps)).astype(np.float32)
        q = np.where(v, m / prof - 1, 0).astype(np.float32)
        # píxels defectuosos AÏLLATS (un sol píxel molt per sota o per sobre dels veïns: resposta del píxel, no estructura del flat):
        # es deixen com a la cadena (el valor del veïnat), perquè el suavitzat σ_fi no escampi la seva correcció als veïns
        d12 = np.where(v, (M1[sl] - M2[sl]) / np.maximum(m, 1e-6), 0).astype(np.float32); sig_px = float(0.5 * d12[v].std())
        # llindar sobre la dispersió REAL píxel a píxel (PRNU del sensor, ~1,7 % a la Vixen R: és resposta real i es conserva), no sobre el
        # soroll del màster: només els píxels a > 8σ robustes del seu veïnat 3×3 (defectes de debò)
        med3 = cv2.medianBlur(q, 3); dq = (q - med3)[v]; sig_prnu = float(1.4826 * np.median(np.abs(dq - np.median(dq))))
        aill = v & (np.abs(q - med3) > 8 * sig_prnu); q = np.where(aill, med3, q).astype(np.float32); del dq
        wv = v.astype(np.float32); ng = lambda x, sg: cv2.GaussianBlur(x * wv, (0, 0), sg) / np.maximum(cv2.GaussianBlur(wv, (0, 0), sg), 1e-6)
        rb = np.where(v, ng(q, SFI) - ng(q, a.sigma_gran), 0).astype(np.float32)
        # C sense part radial: fora la mitjana per anells (2 px, suavitzada σ 4 px), mesurada lluny de les vores (on C és sencera)
        lli0 = v & (dvora[sl] >= a.vora_px)
        pm, _ = perfil_fi(rb[lli0], rr[lli0], minim=20); pm = np.where(np.isfinite(pm), pm, 0.0); pms = gs1(pm, 4.0 / BIN)
        rins = float(min(CY - T_, B_ - 1 - CY, CX - L_, R_ - 1 - CX) - a.vora_px)
        treta = dict(max_abs_r_lt_inscrit=float(np.abs(pms[rc < rins]).max()), p99_abs_r_lt_inscrit=float(np.percentile(np.abs(pms[rc < rins]), 99)))
        rb_nr = np.where(v, rb - np.interp(rr, rc, pms).astype(np.float32), 0).astype(np.float32)
        Cc = (1 + rb_nr * TAPER[sl]).astype(np.float32); C[sl] = Cc
        # portes i xifres
        dv = dvora[sl]; lliure = v & (dv >= a.vora_px); zv = v & (dv < a.vora_px)
        pa, _ = perfil_fi((Cc - 1)[lliure], rr[lliure], minim=20); pa_s = gs1(np.where(np.isfinite(pa), pa, 0.0), 4.0 / BIN); zr = (rc >= 50) & (rc < rins)
        cen = v & (rr < 20); ane = v & (rr >= 20) & (rr < 60)
        d = d12; ds = ng(d, SFI)
        # el pilot (mateixa banda, perfil de 260 calaixos amb la mediana al calaix 0): per comparar el disc
        fr = FR[sl]
        rep['canals'][f'{c}@{oy}{ox}'] = dict(
            C_menys_1_p1_p50_p99=np.percentile(Cc[lliure] - 1, [1, 50, 99]).round(6).tolist(), C_rms=float((Cc[lliure] - 1).std()),
            max_abs_C_menys_1_fora_vores=float(np.abs(Cc[lliure] - 1).max()), on_max=[int(x) for x in np.unravel_index(np.argmax(np.where(lliure, np.abs(Cc - 1), 0)), Cc.shape)],
            frac_fora_vores_sobre_1pc=float((np.abs(Cc[lliure] - 1) > 0.01).mean()), frac_fora_vores_sobre_2pc=float((np.abs(Cc[lliure] - 1) > 0.02).mean()),
            max_abs_C_menys_1_zona_vora=float(np.abs(Cc[zv] - 1).max()) if zv.any() else None,
            mitjana_per_anells_max_abs=float(np.abs(pa_s[zr]).max()), mitjana_per_anells_calaix2px_p99=float(np.nanpercentile(np.abs(pa[zr]), 99)), r_inscrit_px=rins,
            part_radial_treta_de_la_banda=treta, pixels_aillats_deixats=int(aill.sum()), pixels_aillats_frac=float(aill[v].mean()), sigma_prnu_px=sig_prnu,
            n_px_fora_vores_sobre_3pc=int((np.abs(Cc[lliure] - 1) > 0.03).sum()), disc_central_r_lt_20px=float(Cc[cen].mean() - 1), anell_20_60px=float(Cc[ane].mean() - 1),
            centre_ajust_coef=coef.tolist(), calaixos_centre_omplerts=int(buits_centre.sum()),
            soroll_master_px=float(0.5 * d[v].std()), soroll_master_despres_sigma_fi=float(0.5 * ds[v].std()),
            FLAT_RADIAL_cadena=dict(disc_r_lt_17px=float(fr[v & (rr < 17)].mean()), anell_19_25px=float(fr[v & (rr >= 19) & (rr < 25)].mean()),
                                    exces_que_el_disc_posa_a_la_dada=float(fr[v & (rr >= 19) & (rr < 25)].mean() / fr[v & (rr < 17)].mean() - 1),
                                    master_disc_sobre_anell=float(m[v & (rr < 17)].mean() / m[v & (rr >= 19) & (rr < 25)].mean() - 1)))
        print(a.tren, c, json.dumps({k_: rep['canals'][f'{c}@{oy}{ox}'][k_] for k_ in ('C_menys_1_p1_p50_p99', 'max_abs_C_menys_1_fora_vores', 'on_max', 'mitjana_per_anells_max_abs', 'disc_central_r_lt_20px', 'FLAT_RADIAL_cadena')}), flush=True)
        del q, rb, rb_nr, d, ds
cs = rep['canals'].values()
rep['portes'] = dict(max_C_fora_vores_lt_3pc=all(x['max_abs_C_menys_1_fora_vores'] < 0.03 for x in cs), anells_lt_0_02pc=all(x['mitjana_per_anells_max_abs'] < 2e-4 for x in cs),
                     disc_central_lt_0_5pc=all(abs(x['disc_central_r_lt_20px']) < 0.005 for x in cs))
rep['portes']['PASSA'] = all(rep['portes'].values())
rep['portes']['nota'] = ('la porta del 3 % és informativa (la Vixen R té la resposta píxel a píxel del sensor, PRNU ~1,7 %, i el pas banda σ_fi = 1 en deixa '
                         'algun píxel just per sobre); les portes que aturen són el disc central i la mitjana per anells (C sense cap part radial)')
np.savez_compressed(OUT / f'{a.tren}_flat2d_v2.npz', C=C, patró=pat, centre_yx=np.array([CY, CX]), e_ref=e_ref)
rep['sortida'] = str((OUT / f'{a.tren}_flat2d_v2.npz').resolve().relative_to(ARREL)); rep['sha256'] = hashlib.sha256((OUT / f'{a.tren}_flat2d_v2.npz').read_bytes()).hexdigest()
rep['segons'] = time.time() - t0
(OUT / f'{a.tren}_flat2d_v2_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); print('FET', rep['sortida'], 'PORTES', rep['portes'], flush=True)
if not (rep['portes']['anells_lt_0_02pc'] and rep['portes']['disc_central_lt_0_5pc']): sys.exit(1)
