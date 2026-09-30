"""f0_flat2d_v3 (V108, flat 2D LLIURABLE) · La C de la v2 sense el que no és a la dada de l'eclipsi, i amb porta per estructura.
Parteix EXACTAMENT de la v2 (f0_flat2d_v2.py: mateix màster, mateixa REF = el flat que aplica la cadena, mateix disc central, mateixa banda
σ_fi … σ_gran, mateixos píxels aïllats, mateix esvaïment de 100 px a les vores). Control: amb --recepta v2 surt la C de la v2 bit a bit.
Els canvis de la v3 són TRES, cadascun provat a la dada abans d'entrar-hi (d2_prova_AB, d3_prova_VS, g1_porta_estructures):
  1 · COLOR. ln C_c = ℓ + κ_c (ℓ = part comuna als quatre canals CFA; κ_c = part cromàtica). A la Sony, la prova dels dos apuntaments (A − B,
      on el cel s'anul·la) diu que de κ només n'hi ha un 20–45 % a la dada (R/G) i que els ANELLS cromàtics (centrats a 195 px de l'eix òptic,
      a (2832, 4092) px RAW: són de la llum dels flats) no hi són gens (β = 0,00 ± 0,04). La part comuna sí que hi és sencera (β ≈ −1).
      --croma cap: C comuna als canals (el color de la imatge no canvia).  --croma sencera: la κ de la v2.  --croma-vixen: el mateix per a la Vixen.
  2 · ANELLS DEL FLAT (--anells y,x): la mitjana per anells d'1 subplà de ℓ al voltant del centre dels anells (fora de les vores) es treu de ℓ.
  3 · PORTA PER ESTRUCTURA (--porta <json de g1>): les estructures de ℓ (taques de pols i línies: z ≥ 4,5 a les escales 3, 6 o 12 subplans,
      amb histèresi a 2,5) només es corregeixen a l'apuntament on l'apilat sense corregir hi té el defecte (validat amb nuls per g1). Sense
      --porta, s'escriuen els components (ℓ, κ, estructures) per a g1 i una C «sense porta» (totes les estructures aplicades) per diagnosi.
Sortida (4-RESULTATS/v108_20260926/flat2d_v3/flat2d/): <TREN>_components_v3.npz + ESTRUCTURES_<TREN>.json; amb --porta, una C per GRUP
(VIXEN_flat2d_v3.npz; SONYTOT_A_flat2d_v3.npz i SONYTOT_B_flat2d_v3.npz: cada apuntament la seva porta) amb el mateix format que la v2, i el rebut.
Ús: f0_flat2d_v3.py VIXEN|SONYTOT [--recepta v3|v2] [--croma cap|sencera] [--anells y,x|cap] [--porta <json>] [--sense-porta-sortida]"""
import sys, os, json, glob, argparse, subprocess, hashlib, time, types
from pathlib import Path
import numpy as np, cv2, rawpy
from astropy.io import fits
from scipy.ndimage import gaussian_filter1d, binary_dilation, label as nd_label
ARREL = Path(__file__).resolve().parents[4]
CRT = ARREL / '3-RECERCA/tools/v97_refundacio_20260924/cadena_raw'; sys.path.insert(0, str(CRT))
import a4_sources as A4                      # només per al codi congelat (frozen_map, definition, comu); no escriu res
RI = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/raw_inputs'; CAL = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
V2 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v2/flat2d'
ap = argparse.ArgumentParser(); ap.add_argument('tren', choices=['VIXEN', 'SONYTOT']); ap.add_argument('--recepta', choices=['v3', 'v2'], default='v3')
ap.add_argument('--croma', choices=['cap', 'sencera'], default=None); ap.add_argument('--anells', default=None)
ap.add_argument('--porta', default=None); ap.add_argument('--z-llavor', type=float, default=4.5); ap.add_argument('--z-histeresi', type=float, default=2.5)
ap.add_argument('--out', default=str(ARREL / '4-RESULTATS/v108_20260926/flat2d_v3/flat2d'))
a = ap.parse_args(); OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True); t0 = time.time()
SONY = a.tren == 'SONYTOT'; SFI = 2.0 if SONY else 1.0; SGRAN = 60.0; VORA = 100.0; REXT = 180.0 if SONY else 20.0
DEF = dict(SONYTOT=dict(croma='cap', anells='2832.5,4092.5'), VIXEN=dict(croma=None, anells='cap'))[a.tren]   # la croma de la Vixen la decideix d3 (vegeu l'INFORME)
CROMA = a.croma or DEF['croma']; ANELLS = a.anells or DEF['anells']
if a.recepta == 'v3' and CROMA is None: sys.exit('ATURAT: cal --croma per a la Vixen (la decideix d3_prova_VS)')
# =====================================================================================================================================
# 1 · LA RECEPTA DE LA v2 (còpia literal de f0_flat2d_v2.py fins a rb, sense l'esvaïment; l'esvaïment s'aplica al final, igual)
# =====================================================================================================================================
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
M = np.empty((h_, w_), np.float32)
for y0 in range(0, h_, 256): M[y0:y0 + 256] = np.median(pila[:, y0:y0 + 256].astype(np.float32), axis=0)
M -= dark; del pila
print(a.tren, 'màster fet', len(noms), 'flats', f'{time.time()-t0:.0f}s', flush=True)
FR = fits.getdata(CAL / f'calibration_{a.tren}/0-calibracio/FLAT_RADIAL.fits').astype(np.float32); assert FR.shape == (h_, w_)
comu = A4.comu
with rawpy.imread(str(sorted((RI / a.tren / 'totalitat').glob('*'))[0])) as r:
    g = comu.geometria(r); mc = comu.mapa_colors(r)
orig = {i: tuple(int(v.min()) for v in np.where(mc == i)) for i in range(4)}
valid = np.zeros((g.alt, g.ample), np.float32); valid[g.marge_dalt + 2:g.alt - g.marge_baix - 2, g.marge_esq + 2:g.ample - g.marge_dreta - 2] = 1.0
RIP = {}; rip_sha = None; DITH = None
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
TAPER = smoothstep(dvora / VORA).astype(np.float32)
RB = {}; VV = {}; CANAL = {}
for oy in range(2):
    for ox in range(2):
        c = desc[pat[oy, ox]] + ('' if desc[pat[oy, ox]] != 'G' else ('1' if pat[oy, ox] == 1 else '2')); CANAL[(oy, ox)] = c
        sl = (slice(oy, None, 2), slice(ox, None, 2)); m = M[sl]; v = vis[sl]; rr = rad[sl]
        i_cfa = next(i for i in range(4) if orig[i] == (oy, ox))
        ref = (FR[sl] / RIP[i_cfa]).astype(np.float32) if SONY else FR[sl].copy()
        if SONY:
            cn = comu.nom_canal(i_cfa, g.desc); r1 = np.arange(int(rr.max()) + 2, dtype=np.float64)
            lnD = gaussian_filter1d(np.interp(r1, DITH['r_sensor_px'], DITH['lnF'][cn]), 32.0, mode='nearest')
            ref = (ref / np.exp(np.interp(rr, r1, lnD))).astype(np.float32)
        ib = rr.astype(np.int32); nb1 = int(rr.max()) + 2; n1 = np.bincount(ib[v], None, nb1); s1 = np.bincount(ib[v], m[v].astype(np.float64), nb1)
        pm_ = np.where(n1 >= 8, s1 / np.maximum(n1, 1), np.nan); rc1 = np.arange(nb1) + 0.5
        kfit = np.isfinite(pm_) & (rc1 >= 5) & (rc1 < 60); cq = np.polyfit(rc1[kfit] ** 2, pm_[kfit], 1, w=np.sqrt(n1[kfit])); pm_ = np.where(np.isfinite(pm_) & (rc1 >= 5), pm_, np.polyval(cq, rc1 ** 2))
        pm_ = np.exp(gaussian_filter1d(np.log(np.maximum(pm_, 1e-6)), 4.0, mode='nearest')); Mp = np.interp(rr, rc1, pm_).astype(np.float32)
        kk = v & (rr >= REXT) & (rr < REXT + 40); kcst = float(np.median(ref[kk] / Mp[kk]))
        dins = v & (rr < REXT); ref = np.where(dins, (kcst * Mp).astype(np.float32), ref).astype(np.float32)
        wv = v.astype(np.float32); ng = lambda x, sg: cv2.GaussianBlur(x * wv, (0, 0), sg) / np.maximum(cv2.GaussianBlur(wv, (0, 0), sg), 1e-6)
        q0 = np.where(v, m / ref, 0).astype(np.float32); q = np.where(v, q0 / np.maximum(ng(q0, SGRAN), 1e-12) - 1, 0).astype(np.float32); del q0
        med3 = cv2.medianBlur(q, 3); dq = (q - med3)[v]; sig_prnu = float(1.4826 * np.median(np.abs(dq - np.median(dq))))
        aill = v & (np.abs(q - med3) > 8 * sig_prnu); q = np.where(aill, med3, q).astype(np.float32); del dq
        RB[(oy, ox)] = np.where(v, ng(q, SFI) - ng(q, SGRAN), 0).astype(np.float32); VV[(oy, ox)] = v
        del q, ref, med3
print(a.tren, 'recepta v2 refeta fins a rb', f'{time.time()-t0:.0f}s', flush=True)
def munta(lnc):
    """lnc: {(oy,ox): ln C sense esvaïment} → C a mida del RAW, amb l'esvaïment de la v2 (C = 1 + esv·(e^lnC − 1), idèntic a la v2 si lnC = ln(1 + rb))."""
    C = np.ones((h_, w_), np.float32)
    for (oy, ox), l in lnc.items():
        sl = (slice(oy, None, 2), slice(ox, None, 2)); C[sl] = (1 + np.expm1(l) * TAPER[sl]).astype(np.float32) if l is not None else (1 + RB[(oy, ox)] * TAPER[sl]).astype(np.float32)
    return C
rep = dict(tren=a.tren, recepta=a.recepta, sigma_fi=SFI, sigma_gran=SGRAN, vora_px_RAW=VORA, r_ext=REXT, n_flats=len(noms), exposicio_flat=e_ref, ondulacio_sha256=rip_sha)
# control: la recepta v2 ha de donar la C de la v2 bit a bit
C2 = munta({k: None for k in RB}); Cv2 = np.load(V2 / f'{a.tren}_flat2d_v2.npz')['C']
rep['control_v2'] = dict(igual_bit_a_bit=bool(np.array_equal(C2, Cv2)), max_abs_dif=float(np.abs(C2 - Cv2).max()))
print(a.tren, 'CONTROL: la recepta v2 refeta = C de la v2 bit a bit:', rep['control_v2'], flush=True)
if not rep['control_v2']['igual_bit_a_bit']: sys.exit('ATURAT: la recepta v2 refeta no dona la v2')
del Cv2
if a.recepta == 'v2':
    np.savez_compressed(OUT / f'{a.tren}_flat2d_v2_refeta.npz', C=C2, patró=pat); (OUT / f'{a.tren}_flat2d_v2_refeta_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); sys.exit(0)
del C2
# =====================================================================================================================================
# 2 · v3: anells del flat fora (a tots els canals), estructures (taques i línies) de cada canal, i C de cada grup amb la porta per canal
# =====================================================================================================================================
hs = min(v.shape[0] for v in RB.values()); ws = min(v.shape[1] for v in RB.values())
LN = {k: np.log1p(v[:hs, :ws]).astype(np.float32) for k, v in RB.items()}
V = np.logical_and.reduce([v[:hs, :ws] for v in VV.values()])
TS = np.minimum.reduce([TAPER[oy::2, ox::2][:hs, :ws] for oy in range(2) for ox in range(2)])       # esvaïment al subplà
inter = V & (TS >= 1.0)                                                                              # fora de la zona d'esvaïment
rep['v3'] = dict(croma=CROMA, anells=ANELLS)
KCAM = {'R': [k for k in LN if CANAL[k] == 'R'], 'G': [k for k in LN if CANAL[k].startswith('G')], 'B': [k for k in LN if CANAL[k] == 'B']}   # canals de càmera → CFA
# 2a · anells del flat: la mitjana per anells d'1 subplà al voltant del seu centre, a CADA canal CFA (fora de la zona d'esvaïment)
if ANELLS != 'cap':
    cyA, cxA = (float(v) for v in ANELLS.split(','))
    gy, gx = np.mgrid[0:hs, 0:ws].astype(np.float32); ra = np.hypot(2 * gy + 0.5 - cyA, 2 * gx + 0.5 - cxA) / 2.0; del gy, gx
    ib = ra.astype(np.int32); nb = int(ib.max()) + 1; n = np.bincount(ib[inter], None, nb); ANELL = {}; pr_max = {}
    for k, v in LN.items():
        sm = np.bincount(ib[inter], v[inter].astype(np.float64), nb); prof = np.where(n >= 30, sm / np.maximum(n, 1), 0.0)
        ANELL[k] = np.where(V, prof[ib], 0).astype(np.float32); pr_max[CANAL[k]] = round(1e4 * float(np.abs(prof[n >= 30]).max()), 2)
    LNp = {k: (v - ANELL[k]).astype(np.float32) for k, v in LN.items()}
    rep['v3']['anells_rms_ppm'] = {CANAL[k]: round(1e4 * float(a_[inter].std()), 3) for k, a_ in ANELL.items()}; rep['v3']['anells_perfil_max_abs_ppm'] = pr_max; del ra, ib
else:
    LNp = LN
ellp = (sum(LNp.values()) / 4.0).astype(np.float32)
CAM = {c: (sum(LNp[k] for k in ks) / len(ks)).astype(np.float32) for c, ks in KCAM.items()}          # ln C de cada canal de càmera (sense anells)
# 2b · estructures: TAQUES (z multiescala isòtrop, 3/6/12 subplans) i LÍNIES (filtre orientat: σ 25 al llarg, DoG 1–5 de través, cada 3°),
#      a ℓ' i a cada canal de càmera; llavor ≥ z_llavor (línies ≥ 6), histèresi ≥ z_histeresi
wI = inter.astype(np.float32)
ngI = lambda x, s: cv2.GaussianBlur(x * wI, (0, 0), s) / np.maximum(cv2.GaussianBlur(wI, (0, 0), s), 1e-6)
def robust(z):
    med = float(np.median(z[inter])); sg = float(1.4826 * np.median(np.abs(z[inter] - med))); return med, sg
def taques(img):
    zmx = np.zeros((hs, ws), np.float32); m = np.zeros((hs, ws), bool)
    for s in (3, 6, 12):
        d = (ngI(img, s) - ngI(img, 6 * s)) * wI; med, sg = robust(d); z = np.where(inter, (d - med) / sg, 0).astype(np.float32)
        lab, _ = nd_label(np.abs(z) >= a.z_histeresi); ll = np.unique(lab[(np.abs(z) >= a.z_llavor) & (lab > 0)]); m |= np.isin(lab, ll) & (lab > 0)
        zmx = np.where(np.abs(z) > np.abs(zmx), z, zmx); del d, z, lab
    return m, zmx
def linies(img, sL=25.0, s1=1.0, s2=5.0, pas=3, llavor=6.0):
    zmx = np.zeros((hs, ws), np.float32); cen = (ws / 2.0, hs / 2.0)
    for th in range(0, 180, pas):
        Mr = cv2.getRotationMatrix2D(cen, float(th), 1.0); Mi = cv2.invertAffineTransform(Mr)
        ri = cv2.warpAffine(img * wI, Mr, (ws, hs), flags=cv2.INTER_LINEAR, borderValue=0); rw = cv2.warpAffine(wI, Mr, (ws, hs), flags=cv2.INTER_LINEAR, borderValue=0)
        al = lambda x: cv2.GaussianBlur(x, (0, 0), sigmaX=sL, sigmaY=0.01)
        ti = lambda x, s: cv2.GaussianBlur(x, (0, 0), sigmaX=0.01, sigmaY=s)
        num = al(ri); den = al(rw); a1 = ti(num, s1) / np.maximum(ti(den, s1), 1e-6); a2 = ti(num, s2) / np.maximum(ti(den, s2), 1e-6)
        r = cv2.warpAffine((a1 - a2) * (rw > 0.99), Mi, (ws, hs), flags=cv2.INTER_LINEAR, borderValue=0) * wI; med, sg = robust(r)
        z = np.where(inter, (r - med) / sg, 0).astype(np.float32); zmx = np.where(np.abs(z) > np.abs(zmx), z, zmx); del ri, rw, num, den, a1, a2, r, z
    lab, _ = nd_label(np.abs(zmx) >= a.z_histeresi); ll = np.unique(lab[(np.abs(zmx) >= llavor) & (lab > 0)])
    return np.isin(lab, ll) & (lab > 0), zmx
peu_t = np.zeros((hs, ws), bool); peu_l = np.zeros((hs, ws), bool); ZT = {}; ZL = {}
for nm, img in [('comuna', ellp)] + list(CAM.items()):
    mt, zt = taques(img); ml, zl = linies(img); peu_t |= mt; peu_l |= ml; ZT[nm] = zt; ZL[nm] = zl
    print(a.tren, 'detecció', nm, 'taques px', int(mt.sum()), 'línies px', int(ml.sum()), f'{time.time()-t0:.0f}s', flush=True)
peu = binary_dilation(peu_t | peu_l, np.ones((7, 7), bool)) & V
LAB, NE = nd_label(peu); LAB = LAB.astype(np.int32)
# pes suau de cada petjada (gaussiana σ 2 subplans de la petjada binària); la cua de 2–4 subplans enfora s'assigna a l'etiqueta veïna
W = cv2.GaussianBlur(peu.astype(np.float32), (0, 0), 2.0); LABx = cv2.dilate(LAB.astype(np.float32), np.ones((9, 9), np.uint8)).astype(np.int32); LABx = np.where(LAB > 0, LAB, LABx)
W = np.where(LABx > 0, W, 0).astype(np.float32)
llista = []
for k in range(1, NE + 1):
    mk = LAB == k; ys, xs = np.nonzero(mk)
    if len(ys) == 0: continue
    fl = float((peu_l & mk).sum()) / float(mk.sum())
    zt = {nm: round(float(z[mk][np.argmax(np.abs(z[mk]))]), 2) for nm, z in ZT.items()}; zl = {nm: round(float(z[mk][np.argmax(np.abs(z[mk]))]), 2) for nm, z in ZL.items()}
    llista.append(dict(id=k, tipus='línia' if fl >= 0.5 else 'taca', frac_linia=round(fl, 3), centre_subpla_xy=[float(xs.mean()), float(ys.mean())], centre_RAW_xy=[float(2 * xs.mean() + 0.5), float(2 * ys.mean() + 0.5)],
                       caixa_subpla=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1], area_subpla=int(mk.sum()), z_taca=zt, z_linia=zl,
                       llargada_px=round(float(np.hypot(xs.max() - xs.min(), ys.max() - ys.min())), 1)))
rep['v3']['estructures'] = dict(n=len(llista), n_linies=sum(1 for e in llista if e['tipus'] == 'línia'), z_llavor_taques=a.z_llavor, z_llavor_linies=6.0, z_histeresi=a.z_histeresi,
                                area_total_subpla=int(peu.sum()), frac_sensor=round(float(peu.mean()), 6))
(OUT / f'ESTRUCTURES_{a.tren}.json').write_text(json.dumps(dict(tren=a.tren, n=len(llista), estructures=llista), ensure_ascii=False, indent=1) + '\n')
np.savez_compressed(OUT / f'{a.tren}_components_v3.npz', ellp=ellp, lab=LABx, W=W, V=V, inter=inter, **{f'cam_{c}': v for c, v in CAM.items()},
                    **{f'lnp_{CANAL[k]}': v for k, v in LNp.items()}, **{f'zt_{n}': v for n, v in ZT.items()}, **{f'zl_{n}': v for n, v in ZL.items()}, patró=pat, hs=hs, ws=ws)
print(a.tren, 'estructures', len(llista), 'de les quals línies', rep['v3']['estructures']['n_linies'], f'{time.time()-t0:.0f}s', flush=True)
# 2c · la C de cada grup: FONS = ℓ' a tots els canals (--croma cap) o ln C' per canal (--croma sencera); dins de cada estructura k,
#      lnC_c = (1 − W_k)·FONS_c + W_k·(ln C'_c si la porta ha validat el canal de càmera de c a aquest grup; 0 si no)
def lnC_grup(dec):
    out = {}
    for k_cfa in RB:
        fons = LNp[k_cfa] if CROMA == 'sencera' else ellp; cam = next(c for c, ks in KCAM.items() if k_cfa in ks)
        if dec is None: l = fons                                   # sense porta: totes les estructures aplicades (només diagnosi)
        else:
            ok_ids = np.array(sorted(int(k) for k, d in dec.items() if d.get('aplica_canals', {}).get(cam)), np.int32)
            dins = LABx > 0; val = np.isin(LABx, ok_ids)
            l = np.where(dins, (1 - W) * fons + W * np.where(val, LNp[k_cfa], 0), fons).astype(np.float32)
        full = np.zeros(RB[k_cfa].shape, np.float32); full[:hs, :ws] = l; out[k_cfa] = full
    return out
grups_t = ['A', 'B'] if SONY else ['V']
porta = json.loads(Path(a.porta).read_text()) if a.porta else None
rep['grups'] = {}
for gp in grups_t:
    if porta is None: dec = None; etiq = f'{a.tren}{"_" + gp if SONY else ""}_flat2d_v3_sense_porta'
    else: dec = porta['grups'][{'A': 'sony_A', 'B': 'sony_B', 'V': 'vixen'}[gp]]['decisions']; etiq = f'{a.tren}{"_" + gp if SONY else ""}_flat2d_v3'
    C = munta(lnC_grup(dec)); p = OUT / f'{etiq}.npz'
    np.savez_compressed(p, C=C, patró=pat, centre_yx=np.array([CY, CX]), e_ref=e_ref)
    lliure = vis & (dvora >= VORA)
    rep['grups'][gp] = dict(fitxer=str(p.relative_to(ARREL)), sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                            aplicades={c: sorted(int(k) for k, d in (dec or {}).items() if d.get('aplica_canals', {}).get(c)) for c in ('R', 'G', 'B')},
                            C_menys_1_p1_p99=np.percentile(C[lliure] - 1, [1, 99]).round(6).tolist(), max_abs_C_menys_1=float(np.abs(C[lliure] - 1).max()))
    print(a.tren, gp, rep['grups'][gp], flush=True); del C
rep['segons'] = time.time() - t0
(OUT / f'{a.tren}_flat2d_v3{"" if porta else "_sense_porta"}_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float) + '\n')
print('FET', f'{time.time()-t0:.0f}s')
