"""f0_flat2d_v2 (V108, flat 2D lliurable) · EL QUE EL FLAT DE LA CADENA NO REPRESENTA, sense el disc del centre del sensor.

Recepta (la del pilot marrons/f0_flat2d_v108.py, amb tres correccions):
  C = 1 + T_vora · [ G(q, σ_fi) − G(q, σ_gran) ],   q = (M / REF) / G(M / REF, σ_gran) − 1   (relativa al nivell de gran escala)
  · M: màster = mediana de TOTS els flats de l'exposició majoritària menys el dark del run (com F0.3).
  · REF = EL FLAT QUE LA CADENA APLICA DE DEBÒ (la referència que demanava el verificador): el FLAT_RADIAL.fits de la cadena (260 calaixos,
    centre declarat) i, a la Sony, dividit per la correcció d'ondulació que la cadena hi aplica (flat_ripple_correction, calculada aquí
    amb el mateix codi congelat i el mateix FLAT_RADIAL: el SHA ha de ser el que desen els apilats). Així C és exactament el que falta:
    l'estructura no radial (línies, pols, textura de guany) i els arcs i anells fins que el model de 260 calaixos no pot seguir.
    A la Sony, el FLAT_RADIAL porta també la TAULA DEL DITHER (correcció radial del flat de cel mesurada amb el salt de muntura de 749 px,
    flat_dither_SONY.json), que la cadena aplica suavitzada σ 32 px. El màster de flats no la porta: sense treure-la de REF, C en tindria la
    inversa en banda (anells a 150–400 px i a les cantonades; correlació 0,72) i desfaria una correcció validada. Per això REF_Sony es
    divideix per la taula del dither suavitzada igual (σ 32 px).
  · CORRECCIÓ 1 (el disc): el calaix 0 del FLAT_RADIAL de la cadena (r < 18,5 px del RAW) té un valor fals (la mediana de tot el perfil
    omple els calaixos amb < 300 mostres): 0,675 en lloc d'1,009 a la Sony (+49 % a la dada: és el «ghost de l'eix òptic» de l'agost)
    i −2 % a la Vixen. A la Sony, la correcció d'ondulació (σ 32 px) l'escampa fins a ~150 px. Dins de r_ext (Vixen 20 px, Sony 180 px)
    REF és la forma radial del màster mateix (mitjana per anells d'1 px, σ 4 px) enllaçada amb REF a r_ext … r_ext + 40 px (Sony r_ext = 180 px,
    més enllà dels 18,5 + 4·32 px on l'ondulació escampa el calaix 0): C hi queda sense cap part radial. C no toca el disc: el
    «ghost» queda com a la V107 (la fusió ja hi posa pes 0 a l'apuntament A). Curar-lo és un altre canvi (vegeu l'INFORME).
  · CORRECCIÓ 2 (vores del sensor): C s'esvaeix (smoothstep) als 100 px del RAW de la vora de la zona visible.
  · CORRECCIÓ 3 (píxels defectuosos aïllats: |q − mediana 3×3| > 8σ robustes de la resposta píxel a píxel): es deixen com a la cadena,
    perquè el suavitzat σ_fi no n'escampi la correcció als veïns. La resposta píxel a píxel normal (PRNU) es conserva.
  · Banda: σ_fi 1 subpla a la Vixen, 2 a la Sony; σ_gran 60 subplans (com el pilot, validat a M14/M15).
Portes: disc central |C − 1| < 0,5 % (atura); |C − 1| < 3 % a ≥ 100 px de la vora (informativa: se'n compten els píxels).
Sortida: <out>/<TREN>_flat2d_v2.npz (C, mosaic CFA a mida del RAW, float32; el flat 2D és FLAT_RADIAL · C) i <TREN>_flat2d_v2_REBUT.json.
Ús: f0_flat2d_v2.py VIXEN|SONYTOT [--sigma-fi …] [--sigma-gran 60] [--vora-px 100] [--r-ext …]"""
import sys, os, json, glob, argparse, subprocess, hashlib, time, types
from pathlib import Path
import numpy as np, cv2, rawpy
from astropy.io import fits
ARREL = Path(__file__).resolve().parents[4]
CRT = ARREL / '3-RECERCA/tools/v97_refundacio_20260924/cadena_raw'; sys.path.insert(0, str(CRT))
import a4_sources as A4                      # només per al codi congelat (frozen_map, definition, comu); no escriu res
RI = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/raw_inputs'; CAL = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
ap = argparse.ArgumentParser(); ap.add_argument('tren', choices=['VIXEN', 'SONYTOT']); ap.add_argument('--sigma-fi', type=float, default=None)
ap.add_argument('--sigma-gran', type=float, default=60.0); ap.add_argument('--vora-px', type=float, default=100.0); ap.add_argument('--r-ext', type=float, default=None)
ap.add_argument('--out', default=str(ARREL / '4-RESULTATS/v108_20260926/flat2d_v2/flat2d'))
a = ap.parse_args(); OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True); t0 = time.time()
SONY = a.tren == 'SONYTOT'; SFI = a.sigma_fi if a.sigma_fi is not None else (2.0 if SONY else 1.0); REXT = a.r_ext if a.r_ext is not None else (180.0 if SONY else 20.0)
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
# ---- el flat que aplica la cadena: FLAT_RADIAL (i, a la Sony, la correcció d'ondulació amb el codi congelat i la validesa de f2.Ctx)
FR = fits.getdata(CAL / f'calibration_{a.tren}/0-calibracio/FLAT_RADIAL.fits').astype(np.float32); assert FR.shape == (h_, w_)
comu = A4.comu
with rawpy.imread(str(sorted((RI / a.tren / 'totalitat').glob('*'))[0])) as r:
    g = comu.geometria(r); mc = comu.mapa_colors(r)
orig = {i: tuple(int(v.min()) for v in np.where(mc == i)) for i in range(4)}
valid = np.zeros((g.alt, g.ample), np.float32); valid[g.marge_dalt + 2:g.alt - g.marge_baix - 2, g.marge_esq + 2:g.ample - g.marge_dreta - 2] = 1.0
RIP = {}; rip_sha = None; DITH = None
from scipy.ndimage import gaussian_filter1d
if SONY:
    fr_ = A4.frozen_map('V36_RGB_FROZEN.json'); ns = dict(np=np, FLAT_CENTRE_YX={'sony': (2660., 4000.)}, FLAT_SIGMA_PX=32.)
    A4.definition(fr_['sources']['common32']['copy'], 'flat_ripple_correction', ns)
    RIP, _ = ns['flat_ripple_correction'](types.SimpleNamespace(flat=FR, orig=orig, valid=valid), 'sony')
    hh = hashlib.sha256()
    for i in sorted(RIP): hh.update(np.ascontiguousarray(RIP[i]).tobytes())
    rip_sha = hh.hexdigest()
    DITH = json.loads((ARREL / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/frozen_code' / comu.TRENS['SONYTOT']['flat_dither']).read_text())
    DITH = dict(r_sensor_px=np.asarray(DITH['r_sensor_px'], np.float64), lnF={k: np.asarray(v, np.float64) for k, v in DITH['lnF'].items()}, font=DITH.get('font'))
vis = np.zeros((h_, w_), bool); T_, L_ = sz.top_margin, sz.left_margin; B_, R_ = T_ + sz.height, L_ + sz.width; vis[T_:B_, L_:R_] = True
CY, CX = h_ / 2.0, w_ / 2.0; yy, xx = np.mgrid[0:h_, 0:w_].astype(np.float32); rad = np.hypot(yy - CY, xx - CX)
dvora = np.minimum(np.minimum(yy - T_, (B_ - 1) - yy), np.minimum(xx - L_, (R_ - 1) - xx)).astype(np.float32); del yy, xx
def smoothstep(x): x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)
TAPER = smoothstep(dvora / a.vora_px).astype(np.float32)
C = np.ones((h_, w_), np.float32)
rep = dict(tren=a.tren, exposicio_flat=e_ref, n_flats=len(noms), dark=Path(fdark).name, sigma_fi_subplans=SFI, sigma_gran_subplans=a.sigma_gran, vora_px_RAW=a.vora_px,
           referencia='FLAT_RADIAL de la cadena' + (' ÷ correcció d\'ondulació de la cadena (flat_ripple_correction, σ 32 px)' if SONY else ''),
           ondulacio_sha256=rip_sha, r_ext_px_RAW=REXT, extrapolacio='dins de r_ext: la forma radial del màster (anells d\'1 px, σ 4 px) enllaçada amb REF a r_ext … r_ext + 40 px', centre_yx=[CY, CX], canals={})
for oy in range(2):
    for ox in range(2):
        c = desc[pat[oy, ox]] + ('' if desc[pat[oy, ox]] != 'G' else ('1' if pat[oy, ox] == 1 else '2'))
        sl = (slice(oy, None, 2), slice(ox, None, 2)); m = M[sl]; v = vis[sl]; rr = rad[sl]
        i_cfa = next(i for i in range(4) if orig[i] == (oy, ox))
        ref = (FR[sl] / RIP[i_cfa]).astype(np.float32) if SONY else FR[sl].copy()
        if SONY:   # fora la taula del dither (correcció RADIAL validada pel salt de muntura; la cadena l'aplica suavitzada per l'ondulació, σ 32 px)
            cn = comu.nom_canal(i_cfa, g.desc); r1 = np.arange(int(rr.max()) + 2, dtype=np.float64)
            lnD = gaussian_filter1d(np.interp(r1, DITH['r_sensor_px'], DITH['lnF'][cn]), 32.0, mode='nearest')
            ref = (ref / np.exp(np.interp(rr, r1, lnD))).astype(np.float32)
        # el disc (i, a la Sony, l'halo de l'ondulació): dins de r_ext, REF = la FORMA radial del màster mateix (mitjana per anells d'1 px,
        # suavitzada σ 4 px; la fracció central sense prou mostres, ajust a + b·r² als 5–60 px) × la constant que l'enllaça amb REF a r_ext … r_ext + 40
        ib = rr.astype(np.int32); nb1 = int(rr.max()) + 2; n1 = np.bincount(ib[v], None, nb1); s1 = np.bincount(ib[v], m[v].astype(np.float64), nb1)
        pm_ = np.where(n1 >= 8, s1 / np.maximum(n1, 1), np.nan); rc1 = np.arange(nb1) + 0.5
        kfit = np.isfinite(pm_) & (rc1 >= 5) & (rc1 < 60); cq = np.polyfit(rc1[kfit] ** 2, pm_[kfit], 1, w=np.sqrt(n1[kfit])); pm_ = np.where(np.isfinite(pm_) & (rc1 >= 5), pm_, np.polyval(cq, rc1 ** 2))
        pm_ = np.exp(gaussian_filter1d(np.log(np.maximum(pm_, 1e-6)), 4.0, mode='nearest')); Mp = np.interp(rr, rc1, pm_).astype(np.float32)
        kk = v & (rr >= REXT) & (rr < REXT + 40); kcst = float(np.median(ref[kk] / Mp[kk])); coef = [kcst] + [float(x) for x in cq]
        dins = v & (rr < REXT); ref_ext = (kcst * Mp).astype(np.float32)
        disc_vell = float(np.mean(ref[v & (rr < 17)])); ref = np.where(dins, ref_ext, ref).astype(np.float32)
        wv = v.astype(np.float32); ng = lambda x, sg: cv2.GaussianBlur(x * wv, (0, 0), sg) / np.maximum(cv2.GaussianBlur(wv, (0, 0), sg), 1e-6)
        # M (DN) i REF (normalitzat) tenen escales diferents: q relativa al seu propi nivell de gran escala (σ_gran), com el pilot (m/perfil − 1)
        q0 = np.where(v, m / ref, 0).astype(np.float32); q = np.where(v, q0 / np.maximum(ng(q0, a.sigma_gran), 1e-12) - 1, 0).astype(np.float32); del q0
        d12 = np.where(v, (M1[sl] - M2[sl]) / np.maximum(m, 1e-6), 0).astype(np.float32)
        med3 = cv2.medianBlur(q, 3); dq = (q - med3)[v]; sig_prnu = float(1.4826 * np.median(np.abs(dq - np.median(dq))))
        aill = v & (np.abs(q - med3) > 8 * sig_prnu); q = np.where(aill, med3, q).astype(np.float32); del dq
        rb = np.where(v, ng(q, SFI) - ng(q, a.sigma_gran), 0).astype(np.float32)
        Cc = (1 + rb * TAPER[sl]).astype(np.float32); C[sl] = Cc
        dv = dvora[sl]; lliure = v & (dv >= a.vora_px); zv = v & (dv < a.vora_px); cen = v & (rr < 20); ane = v & (rr >= 20) & (rr < 60)
        # contingut radial de C (arcs i anells fins que el model de 260 calaixos no segueix): mitjana per anells de 2 px, fora de les vores
        ib2 = (rr / 2).astype(np.int32); n2 = np.bincount(ib2[lliure], None); s2 = np.bincount(ib2[lliure], (Cc - 1)[lliure].astype(np.float64)); pr2 = np.where(n2 >= 40, s2 / np.maximum(n2, 1), np.nan)
        ds = ng(d12, SFI)
        rep['canals'][f'{c}@{oy}{ox}'] = dict(
            C_menys_1_p1_p50_p99=np.percentile(Cc[lliure] - 1, [1, 50, 99]).round(6).tolist(), C_rms=float((Cc[lliure] - 1).std()),
            max_abs_C_menys_1_fora_vores=float(np.abs(Cc[lliure] - 1).max()), on_max_subpla=[int(x) for x in np.unravel_index(np.argmax(np.where(lliure, np.abs(Cc - 1), 0)), Cc.shape)],
            n_px_fora_vores_sobre_3pc=int((np.abs(Cc[lliure] - 1) > 0.03).sum()), frac_fora_vores_sobre_2pc=float((np.abs(Cc[lliure] - 1) > 0.02).mean()),
            max_abs_C_menys_1_zona_vora=float(np.abs(Cc[zv] - 1).max()) if zv.any() else None,
            disc_central_r_lt_20px=float(Cc[cen].mean() - 1), anell_20_60px=float(Cc[ane].mean() - 1),
            REF_disc_cadena_r_lt_17px=disc_vell, REF_extrapolada_r_lt_17px=float(np.mean(ref[v & (rr < 17)])), REF_anell_130_150px=float(np.mean(ref[v & (rr >= 130) & (rr < 150)])),
            contingut_radial_de_C=dict(max_abs=float(np.nanmax(np.abs(pr2))), rms=float(np.sqrt(np.nanmean(pr2 ** 2))),
                                       corr_amb_la_banda_del_dither=(None if not SONY else float((lambda x, y, k: np.corrcoef(x[k], y[k])[0, 1])(
                                           np.nan_to_num(pr2), -(gaussian_filter1d(np.interp((np.arange(len(pr2)) + 0.5) * 2, DITH['r_sensor_px'], DITH['lnF'][comu.nom_canal(i_cfa, g.desc)]), SFI) -
                                                                 gaussian_filter1d(np.interp((np.arange(len(pr2)) + 0.5) * 2, DITH['r_sensor_px'], DITH['lnF'][comu.nom_canal(i_cfa, g.desc)]), a.sigma_gran)), np.isfinite(pr2))))),
            pixels_aillats_deixats=int(aill.sum()), sigma_prnu_px=sig_prnu,
            soroll_master_px=float(0.5 * d12[v].std()), soroll_master_despres_sigma_fi=float(0.5 * ds[v].std()))
        print(a.tren, c, json.dumps({k_: rep['canals'][f'{c}@{oy}{ox}'][k_] for k_ in ('C_menys_1_p1_p50_p99', 'max_abs_C_menys_1_fora_vores', 'n_px_fora_vores_sobre_3pc', 'disc_central_r_lt_20px', 'REF_disc_cadena_r_lt_17px', 'REF_extrapolada_r_lt_17px', 'contingut_radial_de_C')}), flush=True)
        del q, rb, d12, ds, ref, ref_ext
cs = rep['canals'].values()
rep['portes'] = dict(disc_central_lt_0_5pc=all(abs(x['disc_central_r_lt_20px']) < 0.005 for x in cs),
                     max_C_fora_vores_lt_3pc=all(x['max_abs_C_menys_1_fora_vores'] < 0.03 for x in cs), px_fora_vores_sobre_3pc=int(sum(x['n_px_fora_vores_sobre_3pc'] for x in cs)),
                     nota='atura només el disc central; la del 3 % és informativa (la Vixen té resposta píxel a píxel real, PRNU ~1,2–1,4 %, present també als flats invertits)')
np.savez_compressed(OUT / f'{a.tren}_flat2d_v2.npz', C=C, patró=pat, centre_yx=np.array([CY, CX]), e_ref=e_ref)
rep['sortida'] = str((OUT / f'{a.tren}_flat2d_v2.npz').resolve().relative_to(ARREL)); rep['sha256'] = hashlib.sha256((OUT / f'{a.tren}_flat2d_v2.npz').read_bytes()).hexdigest(); rep['segons'] = time.time() - t0
(OUT / f'{a.tren}_flat2d_v2_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); print('FET', rep['sortida'], 'PORTES', rep['portes'], 'ondulació', rip_sha, flush=True)
if not rep['portes']['disc_central_lt_0_5pc']: sys.exit(1)
