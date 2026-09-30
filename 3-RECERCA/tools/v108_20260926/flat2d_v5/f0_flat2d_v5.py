"""f0_flat2d_v5 (V108, flat 2D, variant flat2d_v5) · La C de la v4 amb UN sol afinament que va demanar el verificador 4: la POLS MOGUDA de la Vixen.
Parteix EXACTAMENT de la v4 (f0_flat2d_v4.py copiat: mateixa recepta, mateixa porta, mateix encongiment H1_ENCONGIDA de la v4).
CONTROLS (s'atura si no): (1) la recepta v2 refeta = la C de la v2 bit a bit; (2) amb la regla de la v3 = la C de la v3 bit a bit; (3) amb la
regla de la v4 = la C de la v4 bit a bit (VIXEN_, SONYTOT_A_, SONYTOT_B_flat2d_v4.npz). L'únic canvi de la v5 és el que es diu aquí sota.
El canvi de la v5 (només a les 5 estructures de la Vixen que diu l'encàrrec; a la Sony, cap: la C de la v5 hi és la de la v4):
  POLS MOGUDA (â ≈ 0). A les estructures de la Vixen on la dada diu que la taca ja no hi és — les 4 amb â = 0 (5860, 5354), (2864, 2088),
  (3898, 2503), (6408, 4793) i la (6149, 4386), amb â = 0,14 i el canvi de la v4 com el nul a la prova s del verificador 4 —, la v4 hi aplicava
  la textura i el fons de la petjada (tot el que no és la banda de la taca) i, a σ4–40 px del llenç, hi passava de llarg (s +0,05, nul
  +1,09 ± 0,18: la meitat del que posava era patró girat). La textura fina (σ < 4 px del llenç) sí que hi és cura (s −1,74).
  Regla v5, dins de la petjada d'aquestes 5:  ln C_c = FONS_c − W_k·G_σt(FONS_c),  σt = 4 px del llenç = 2,0 subplans
  (escala subplà → llenç 1,9995, mesurada amb els centres de les 91 estructures amb centre al llenç; G = la gaussiana normalitzada a
  l'interior, ngI, la mateixa de les bandes de detecció). És a dir: la textura més fina que 4 px s'hi aplica sencera i res del fons de
  4–60 px (ni la part de taca: la â 0,14 de la (6149, 4386) tampoc). Fora de la petjada (W = 0), la C és la de la v4 byte a byte.
  Les altres 4 estructures de la Vixen amb 0 < â ≤ 0,15 (ids 31, 43, 44 i 82: petjades de ~200 subplans on la prova s no decideix,
  nul ± 0,7 … 2,8) queden com a la v4: l'encàrrec diu «res més».
Sortida (4-RESULTATS/v108_20260926/flat2d_v5/flat2d/): VIXEN_flat2d_v5.npz, SONYTOT_A_flat2d_v5.npz, SONYTOT_B_flat2d_v5.npz (format de la v2)
i <TREN>_flat2d_v5_REBUT.json (controls, llista de pols moguda, on i quant canvia respecte de la v4).
Ús: f0_flat2d_v5.py VIXEN|SONYTOT   (l'encongiment és el de la v4: flat2d_v4/flat2d/H1_ENCONGIDA_<TREN>.json)
─── Text de la v4 (la recepta de sota és la mateixa) ───
f0_flat2d_v4 (V108, flat 2D, variant flat2d_v4) · La C de la v3 amb els DOS afinaments que va demanar el verificador 3 a la porta de la pols.
Parteix EXACTAMENT de la v3 (f0_flat2d_v3.py copiat: mateixa recepta, mateixos anells fora, mateixa part cromàtica, mateixes estructures).
CONTROLS (s'atura si no): (1) la recepta v2 refeta = la C de la v2 bit a bit; (2) amb la porta de la v3 i la regla de la v3, la C de cada grup =
la C de la v3 bit a bit (VIXEN_, SONYTOT_A_, SONYTOT_B_flat2d_v3.npz). Així l'únic canvi de la v4 és el que es diu aquí sota.
Els dos canvis de la v4 (i només a les estructures que la porta de la v3 NO aplica):
  1 · PORTA PER GRUP: cada estructura rebutjada s'aplica amb la seva a ENCONGIDA cap a la població del seu grup (h1_encongiment.py: bayesià
      jeràrquic amb l'error de cada a, limitada a [0, 1,2]), mesurada amb la plantilla de la PART D'ESCALA DE TACA (g1_porta_v4.py).
  2 · DINS DE LA PETJADA: ja no es posa C = 1 (FONS·(1 − W)): només es treu la part d'escala de taca que la dada no sosté,
      ln C_c = FONS_c − (1 − â_k)·W_k·P_k,c, amb P_k,c = DoG del FONS_c a l'escala on es va detectar l'estructura (G_s − G_6s, s = 3, 6 o 12
      subplans; la mateixa banda de la detecció). La textura més fina que s (la comuna validada) i el fons més ample que 6s s'hi queden sencers.
  Les estructures «fora del llenç» del grup (no afecten cap fotograma del grup) segueixen amb la regla de la v3.
Sortida (4-RESULTATS/v108_20260926/flat2d_v4/flat2d/): <TREN>_components_v4.npz (per a g1_porta_v4: petjades, pesos, plantilla sencera i de
taca), i amb --encongida, una C per grup (VIXEN_flat2d_v4.npz; SONYTOT_A_flat2d_v4.npz i SONYTOT_B_flat2d_v4.npz), format de la v2, i el rebut.
Ús: f0_flat2d_v4.py VIXEN|SONYTOT [--encongida <H1_ENCONGIDA json> [--etiqueta a0]]   (la porta de la v3 es llegeix de flat2d_v3/flat2d/G1_PORTA_<TREN>.json)
─── Text de la v3 (la recepta de sota és la mateixa) ───
f0_flat2d_v3 (V108, flat 2D LLIURABLE) · La C de la v2 sense el que NO és a la dada de l'eclipsi, i amb porta per estructura.
Parteix EXACTAMENT de la v2 (f0_flat2d_v2.py: mateix màster, mateixa REF = el flat que aplica la cadena, mateix disc central, mateixa banda
σ_fi … σ_gran, mateixos píxels aïllats, mateix esvaïment de 100 px a les vores). CONTROL: la recepta v2 refeta ha de donar la C de la v2 bit a
bit (si no, s'atura); amb --recepta v2 només fa això.
Els canvis de la v3 són TRES, i cadascun s'ha provat a la dada abans d'entrar-hi (diag/: d2_prova_AB amb els dos apuntaments de la Sony, on
el cel s'anul·la; d3_prova_VS amb la Sony com a cel de referència de la Vixen; g1_porta_estructures per a cada taca):
  1 · ANELLS DEL FLAT FORA (--anells y,x; Sony: 2832,5, 4092,5 px RAW, a 195 px de l'eix òptic): la mitjana per anells d'1 subplà al voltant
      del seu centre es treu de cada canal. Són de la llum dels flats: a la dada, β = 0,00 ± 0,04 (no hi són gens).
  2 · NOMÉS LA PART CROMÀTICA QUE LA DADA SOSTÉ. ln C_c = ℓ + κ_c (ℓ comuna als quatre canals CFA; κ_c cromàtica).
      --croma sencera (Vixen): κ sencera (d3: β −0,5 … −1,2 a totes les bandes i colors).
      --croma files (Sony): només la κ que va AL LLARG DE LES FILES del sensor (mitjana en x, σ 100 subplans) i fina de través (≤ 6 subplans):
        β −1,0 … −2,6 a R/G i B/G. La resta de κ (textura cromàtica dels píxels, franges gruixudes, restes d'anells) fa β −0,2 … −0,4: hi és
        menys de la meitat, i aplicar-la injectava color (les bandes i els arcs de la v2 fora de 6 R☉).
      --croma cap: C comuna (el color no canvia).
  3 · PORTA PER ESTRUCTURA: les taques de ℓ' (z ≥ 4,0 a les escales 3, 6 o 12 subplans, histèresi 2,5; amb 4,5 s'escapava una pols moguda de la Vixen) només es corregeixen a l'apuntament
      on l'apilat sense corregir hi té el defecte (g1, validat amb nuls). Les que no passen: FONS_c·(1 − W_k) dins de la seva petjada.
      Sense --porta s'escriuen els components per a g1 i una C «sense porta» (totes aplicades), només per diagnosi.
Sortida (4-RESULTATS/v108_20260926/flat2d_v3/flat2d/): <TREN>_components_v3.npz, ESTRUCTURES_<TREN>.json; amb --porta, una C per grup
(VIXEN_flat2d_v3.npz; SONYTOT_A_flat2d_v3.npz i SONYTOT_B_flat2d_v3.npz, cada apuntament amb la seva porta), format de la v2, i el rebut.
Ús: f0_flat2d_v3.py VIXEN|SONYTOT [--recepta v3|v2] [--croma cap|files|sencera] [--anells y,x|cap] [--porta <G1_PORTA json>]
(Els intents descartats són f0_flat2d_v3_intent1_comuna.py i f0_flat2d_v3_intent2_linies_per_canal.py; vegeu l'INFORME.)"""
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
ap.add_argument('--croma', choices=['cap', 'files', 'sencera'], default=None); ap.add_argument('--anells', default=None)
ap.add_argument('--porta', default=None); ap.add_argument('--z-llavor', type=float, default=4.0); ap.add_argument('--z-histeresi', type=float, default=2.5)
ap.add_argument('--out', default=str(ARREL / '4-RESULTATS/v108_20260926/flat2d_v5/flat2d')); ap.add_argument('--encongida', default=None); ap.add_argument('--etiqueta', default='')
ap.add_argument('--sigma-textura-llenc', type=float, default=4.0); ap.add_argument('--escala-llenc', type=float, default=2.0)   # v5: σt = 4 px del llenç; 1 subplà = 2,0 px del llenç
a = ap.parse_args(); OUT = Path(a.out).resolve(); OUT.mkdir(parents=True, exist_ok=True); t0 = time.time()
V3 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v3/flat2d'                      # la v3: porta (G1_PORTA_<TREN>.json) i C de control
V4 = ARREL / '4-RESULTATS/v108_20260926/flat2d_v4/flat2d'                      # la v4: encongiment (H1_ENCONGIDA_<TREN>.json) i C de control
a.encongida = a.encongida or str(V4 / f'H1_ENCONGIDA_{a.tren}.json')
# v5 · POLS MOGUDA: les 5 estructures de l'encàrrec (centre al llenç, px), i la σ de la textura fina en subplans
POLS_MOGUDA_LLENC = dict(VIXEN=[(5860, 5354), (2864, 2088), (3898, 2503), (6408, 4793), (6149, 4386)], SONYTOT=[])[a.tren]
SIG_TEX = a.sigma_textura_llenc / a.escala_llenc
a.porta = a.porta or str(V3 / f'G1_PORTA_{a.tren}.json')
SONY = a.tren == 'SONYTOT'; SFI = 2.0 if SONY else 1.0; SGRAN = 60.0; VORA = 100.0; REXT = 180.0 if SONY else 20.0
DEF = dict(SONYTOT=dict(croma='files', anells='2832.5,4092.5'), VIXEN=dict(croma='sencera', anells='cap'))[a.tren]   # decidides a la dada: d2_prova_AB (Sony) i d3_prova_VS (Vixen)
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
# 2 · v3: anells del flat fora (a tots els canals), la part cromàtica que la dada sosté, i les taques amb porta per apuntament
# =====================================================================================================================================
hs = min(v.shape[0] for v in RB.values()); ws = min(v.shape[1] for v in RB.values())
LN = {k: np.log1p(v[:hs, :ws]).astype(np.float32) for k, v in RB.items()}
V = np.logical_and.reduce([v[:hs, :ws] for v in VV.values()])
TS = np.minimum.reduce([TAPER[oy::2, ox::2][:hs, :ws] for oy in range(2) for ox in range(2)])       # esvaïment al subplà
inter = V & (TS >= 1.0)                                                                              # fora de la zona d'esvaïment
rep['v3'] = dict(croma=CROMA, anells=ANELLS)
wI = inter.astype(np.float32)
ngI = lambda x, s: cv2.GaussianBlur(x * wI, (0, 0), s) / np.maximum(cv2.GaussianBlur(wI, (0, 0), s), 1e-6)
# 2a · anells del flat: la mitjana per anells d'1 subplà al voltant del seu centre, a CADA canal CFA (fora de la zona d'esvaïment)
if ANELLS != 'cap':
    cyA, cxA = (float(v) for v in ANELLS.split(','))
    gy, gx = np.mgrid[0:hs, 0:ws].astype(np.float32); ra = np.hypot(2 * gy + 0.5 - cyA, 2 * gx + 0.5 - cxA) / 2.0; del gy, gx
    ib = ra.astype(np.int32); nb = int(ib.max()) + 1; n = np.bincount(ib[inter], None, nb); ANELL = {}; pr_max = {}
    for k, v in LN.items():
        sm = np.bincount(ib[inter], v[inter].astype(np.float64), nb); prof = np.where(n >= 30, sm / np.maximum(n, 1), 0.0)
        ANELL[k] = np.where(V, prof[ib], 0).astype(np.float32); pr_max[CANAL[k]] = round(1e4 * float(np.abs(prof[n >= 30]).max()), 2)
    LNp = {k: (v - ANELL[k]).astype(np.float32) for k, v in LN.items()}
    rep['v3']['anells_rms_ppm'] = {CANAL[k]: round(1e4 * float(a_[inter].std()), 3) for k, a_ in ANELL.items()}; rep['v3']['anells_perfil_max_abs_ppm'] = pr_max; del ra, ib, ANELL
else:
    LNp = LN
ellp = (sum(LNp.values()) / 4.0).astype(np.float32)
# 2b · el FONS de C per canal: ℓ' (la part comuna) més la part cromàtica que la dada sosté
#      · --croma sencera (Vixen: d3, β −0,5 … −1,2 a totes les bandes): κ' sencera;
#      · --croma files (Sony: d2_prova_AB, β −1,0 … −2,6 a R/G i B/G fins a 18 px): només κ' AL LLARG DE LES FILES del sensor (mitjana en x amb
#        σ 100 subplans) i fina de través (menys el seu fons de σ 6 subplans en y): hi van les línies quasi paral·leles a les files (T2);
#        la resta de κ' (textura cromàtica dels píxels, franges gruixudes, restes d'anells: β −0,2 … −0,4) NO hi és a la dada i no hi entra;
#      · --croma cap: només ℓ'.
def nga(x, sx, sy): return cv2.GaussianBlur(x * wI, (0, 0), sigmaX=sx, sigmaY=sy) / np.maximum(cv2.GaussianBlur(wI, (0, 0), sigmaX=sx, sigmaY=sy), 1e-6)
def fila(x, sx=100.0, sy=6.0):
    f = nga(x, sx, 0.01); return ((f - nga(f, 0.01, sy)) * wI).astype(np.float32)
FONS = {}
for k, v in LNp.items():
    if CROMA == 'sencera': FONS[k] = v
    elif CROMA == 'files': FONS[k] = (ellp + fila(v - ellp)).astype(np.float32)
    else: FONS[k] = ellp
rep['v3']['croma_rms_ppm'] = {CANAL[k]: round(1e4 * float((f - ellp)[inter].std()), 3) for k, f in FONS.items()}
# 2c · ESTRUCTURES de ℓ' (taques de pols): z multiescala (3, 6, 12 subplans), llavor ≥ z_llavor i histèresi ≥ z_histeresi a la mateixa escala
peu = np.zeros((hs, ws), bool); zmax = np.zeros((hs, ws), np.float32); escala = np.zeros((hs, ws), np.uint8); sig_esc = {}
for s in (3, 6, 12):
    d = (ngI(ellp, s) - ngI(ellp, 6 * s)) * wI; med = float(np.median(d[inter])); sg = float(1.4826 * np.median(np.abs(d[inter] - med))); sig_esc[s] = sg
    z = np.where(inter, (d - med) / sg, 0).astype(np.float32)
    lab, nl = nd_label(np.abs(z) >= a.z_histeresi); ll = np.unique(lab[(np.abs(z) >= a.z_llavor) & (lab > 0)])
    m = np.isin(lab, ll) & (lab > 0); peu |= m
    upd = np.abs(z) > np.abs(zmax); zmax = np.where(upd, z, zmax); escala = np.where(upd & m, s, escala).astype(np.uint8); del d, z, lab
peu = binary_dilation(peu, np.ones((7, 7), bool)) & V
LAB, NE = nd_label(peu); LAB = LAB.astype(np.int32)
# pes suau de cada petjada (gaussiana σ 2 subplans de la petjada binària); la cua de 2–4 subplans enfora s'assigna a l'etiqueta veïna
W = cv2.GaussianBlur(peu.astype(np.float32), (0, 0), 2.0); LABx = cv2.dilate(LAB.astype(np.float32), np.ones((9, 9), np.uint8)).astype(np.int32); LABx = np.where(LAB > 0, LAB, LABx)
W = np.where(LABx > 0, W, 0).astype(np.float32)
cont = ellp       # contingut comú d'una estructura (la plantilla de g1): ℓ' dins de la seva petjada
llista = []
for k in range(1, NE + 1):
    mk = LAB == k; ys, xs = np.nonzero(mk)
    if len(ys) == 0: continue
    zk = zmax[mk]; ip = int(np.argmax(np.abs(zk)))
    llista.append(dict(id=k, centre_subpla_xy=[float(xs.mean()), float(ys.mean())], centre_RAW_xy=[float(2 * xs.mean() + 0.5), float(2 * ys.mean() + 0.5)],
                       caixa_subpla=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1], area_subpla=int(mk.sum()),
                       z_pic=round(float(zk[ip]), 2), escala_subpla=int(escala[mk][ip]) if escala[mk][ip] else None,
                       amplitud_pic_ppm=round(1e4 * float(ellp[mk][np.argmax(np.abs(ellp[mk]))]), 2), llargada_px=round(float(np.hypot(xs.max() - xs.min(), ys.max() - ys.min())), 1)))
rep['v3']['estructures'] = dict(n=len(llista), sigma_textura_ppm={str(s): round(1e4 * v, 3) for s, v in sig_esc.items()}, z_llavor=a.z_llavor, z_histeresi=a.z_histeresi,
                                area_total_subpla=int(peu.sum()), frac_sensor=round(float(peu.mean()), 6))
(OUT / f'ESTRUCTURES_{a.tren}.json').write_text(json.dumps(dict(tren=a.tren, n=len(llista), estructures=llista), ensure_ascii=False, indent=1) + '\n')
# v4 · control: les estructures han de ser les de la v3, idèntiques (mateixes etiquetes i petjades)
E3 = json.loads((V3 / f'ESTRUCTURES_{a.tren}.json').read_text())['estructures']
rep['v4_control_estructures'] = dict(iguals_a_la_v3=bool(E3 == json.loads(json.dumps(llista))), n_v3=len(E3), n_v4=len(llista))
print(a.tren, 'CONTROL: estructures iguals a la v3:', rep['v4_control_estructures'], flush=True)
if not rep['v4_control_estructures']['iguals_a_la_v3']: sys.exit('ATURAT: les estructures no són les de la v3')
# =====================================================================================================================================
# 3 · v4: LA PART D'ESCALA DE TACA de cada estructura (la banda de la seva detecció: G_s − G_6s, s = escala del pic de z, en subplans)
# =====================================================================================================================================
ESC = np.zeros(NE + 1, np.int32)
for e in llista: ESC[e['id']] = e['escala_subpla'] or 3                                  # (cap estructura sense escala; per si de cas, la més fina)
SMAP = ESC[LABx]                                                                           # escala de l'etiqueta de cada subplà (0 = fora de tota petjada)
def banda_s(x, s): return ((ngI(x, s) - ngI(x, 6 * s)) * wI).astype(np.float32)
def per_escala(x):
    out = np.zeros((hs, ws), np.float32)
    for s in (3, 6, 12):
        k = SMAP == s
        if k.any(): out[k] = banda_s(x, s)[k]
    return out
TACA = {k_cfa: per_escala(FONS[k_cfa]) for k_cfa in FONS}                                   # P_c: la part d'escala de taca del FONS de cada canal
cont_taca = per_escala(ellp)                                                               # la plantilla de taca de g1 (part comuna)
dins = LABx > 0
rep['v4'] = dict(escales_estructures={str(s): int((ESC[1:] == s).sum()) for s in (3, 6, 12)},
                 taca_rms_dins_petjades_ppm={CANAL[k]: round(1e4 * float((W * t)[dins].std()), 3) for k, t in TACA.items()},
                 textura_rms_dins_petjades_ppm={CANAL[k]: round(1e4 * float((W * (FONS[k] - t))[dins].std()), 3) for k, t in TACA.items()})
# (v5: els components de la v4 no es tornen a escriure: són els de flat2d_v4/flat2d/<TREN>_components_v4.npz, idèntics per construcció)
print(a.tren, 'estructures', len(llista), 'σ textura', {s: round(1e4 * v, 2) for s, v in sig_esc.items()}, 'croma', rep['v3']['croma_rms_ppm'], 'v4', rep['v4'], f'{time.time()-t0:.0f}s', flush=True)
# =====================================================================================================================================
# 4 · la C de cada grup
# =====================================================================================================================================
def lnC_v3(treure):
    """la regla de la v3, literal: dins de cada estructura que la porta NO aplica, FONS_c·(1 − W_k)."""
    mk = np.isin(LABx, np.array(sorted(treure), np.int32)) if treure else np.zeros((hs, ws), bool)
    out = {}
    for k_cfa in RB:
        l = np.where(mk, FONS[k_cfa] * (1 - W), FONS[k_cfa]).astype(np.float32)
        full = np.zeros(RB[k_cfa].shape, np.float32); full[:hs, :ws] = l; out[k_cfa] = full
    return out
def lnC_v4(regla_v3, ahat):
    """v4: les «fora del llenç», regla de la v3; les rebutjades provades (i les sense referència), FONS_c − (1 − â_k)·W_k·P_k,c; les aplicades, FONS_c."""
    AH = np.ones(NE + 1, np.float32); FORA = np.zeros(NE + 1, bool)
    for k in regla_v3: FORA[int(k)] = True
    for k, v in ahat.items(): AH[int(k)] = float(v)
    AHM = AH[LABx]; FM = FORA[LABx] & (LABx > 0); out = {}
    for k_cfa in RB:
        l = FONS[k_cfa] - (1 - AHM) * W * TACA[k_cfa]
        l = np.where(FM, FONS[k_cfa] * (1 - W), l).astype(np.float32)
        full = np.zeros(RB[k_cfa].shape, np.float32); full[:hs, :ws] = l; out[k_cfa] = full
    return out
GT = {}
def lnC_v5(regla_v3, ahat, pols):
    """v5: la v4 literal (mateixes operacions, mateix ordre: fora de la pols moguda, byte a byte) i, a la petjada de les estructures de POLS
    MOGUDA, només la textura més fina que σt: FONS_c − W_k·G_σt(FONS_c)."""
    AH = np.ones(NE + 1, np.float32); FORA = np.zeros(NE + 1, bool); PM = np.zeros(NE + 1, bool)
    for k in regla_v3: FORA[int(k)] = True
    for k, v in ahat.items(): AH[int(k)] = float(v)
    for k in pols: PM[int(k)] = True
    AHM = AH[LABx]; FM = FORA[LABx] & (LABx > 0); PMM = PM[LABx] & (LABx > 0); out = {}
    for k_cfa in RB:
        l = FONS[k_cfa] - (1 - AHM) * W * TACA[k_cfa]
        l = np.where(FM, FONS[k_cfa] * (1 - W), l).astype(np.float32)
        if PMM.any():
            if k_cfa not in GT: GT[k_cfa] = ngI(FONS[k_cfa], SIG_TEX).astype(np.float32)
            l = np.where(PMM, FONS[k_cfa] - W * GT[k_cfa], l).astype(np.float32)
        full = np.zeros(RB[k_cfa].shape, np.float32); full[:hs, :ws] = l; out[k_cfa] = full
    return out
grups_t = ['A', 'B'] if SONY else ['V']; NOMG = {'A': 'sony_A', 'B': 'sony_B', 'V': 'vixen'}
porta = json.loads(Path(a.porta).read_text()); enc = json.loads(Path(a.encongida).read_text()) if a.encongida else None
rep['porta_v3'] = str(Path(a.porta).relative_to(ARREL)); rep['encongida'] = str(Path(a.encongida).resolve().relative_to(ARREL)) if enc else None
rep['grups'] = {}; lliure = vis & (dvora >= VORA)
for gp in grups_t:
    dec = porta['grups'][NOMG[gp]]['decisions']; treure = [int(k) for k, d in dec.items() if not d['aplica']]
    # CONTROL: amb la porta i la regla de la v3, la C de la v3 bit a bit
    C3 = munta(lnC_v3(treure)); Cv3 = np.load(V3 / f'{a.tren}{"_" + gp if SONY else ""}_flat2d_v3.npz')['C']
    ctl = dict(igual_bit_a_bit=bool(np.array_equal(C3, Cv3)), max_abs_dif=float(np.abs(C3 - Cv3).max())); del Cv3
    print(a.tren, gp, 'CONTROL: la regla de la v3 refeta = C de la v3 bit a bit:', ctl, flush=True)
    if not ctl['igual_bit_a_bit']: sys.exit('ATURAT: la regla de la v3 refeta no dona la C de la v3')
    rg = dict(control_v3=ctl)
    if enc is not None:
        E_ = enc['grups'][NOMG[gp]]; fora = [int(k) for k, d in E_['estructures'].items() if d['regla'] == 'v3_fora_del_llenc']
        ah = {int(k): d['a_encongida'] for k, d in E_['estructures'].items() if d['regla'] in ('encongida', 'encongida_sense_dada')}
        assert set(ah) | set(fora) == set(treure), 'l’encongiment no cobreix exactament les rebutjades de la v3'
        # CONTROL v4: amb la regla de la v4, la C de la v4 bit a bit
        C4 = munta(lnC_v4(fora, ah)); Cv4 = np.load(V4 / f'{a.tren}{"_" + gp if SONY else ""}_flat2d_v4.npz')['C']
        ctl4 = dict(igual_bit_a_bit=bool(np.array_equal(C4, Cv4)), max_abs_dif=float(np.abs(C4 - Cv4).max())); del Cv4
        print(a.tren, gp, 'CONTROL: la regla de la v4 refeta = C de la v4 bit a bit:', ctl4, flush=True)
        if not ctl4['igual_bit_a_bit']: sys.exit('ATURAT: la regla de la v4 refeta no dona la C de la v4')
        rg['control_v4'] = ctl4
        # v5 · les estructures de pols moguda: la més propera (≤ 10 px) de cada centre de l'encàrrec, amb â ≤ 0,15 a l'encongiment de la v4
        pols = []; rg['pols_moguda'] = []
        for cx_, cy_ in POLS_MOGUDA_LLENC:
            cand = [(float(np.hypot(d['centre_llenc'][0] - cx_, d['centre_llenc'][1] - cy_)), int(k), d) for k, d in E_['estructures'].items() if d.get('centre_llenc')]
            dist, k, d = min(cand); assert dist <= 10, f'cap estructura a ≤ 10 px de ({cx_}, {cy_}) (la més propera, {k}, a {dist:.1f} px)'
            assert k in ah and ah[k] <= 0.15, f'l’estructura {k} no és una rebutjada amb â ≤ 0,15 ({ah.get(k)})'
            pols.append(k); rg['pols_moguda'].append(dict(id=k, centre_encarrec=[cx_, cy_], centre_llenc=d['centre_llenc'], dist_px=round(dist, 1), a_encongida_v4=ah[k],
                                                          regla_v4=d['regla'], escala_subpla=d.get('escala_subpla'), R_sol=d.get('R_sol')))
        altres = sorted((int(k), v) for k, v in ah.items() if v <= 0.15 and int(k) not in pols)
        rg['altres_a_menor_o_igual_0_15_sense_canvi'] = [dict(id=k, a_encongida_v4=v, centre_llenc=E_['estructures'][str(k)].get('centre_llenc')) for k, v in altres]
        C = munta(lnC_v5(fora, ah, pols)); p = OUT / f'{a.tren}{"_" + gp if SONY else ""}_flat2d_v5{"_" + a.etiqueta if a.etiqueta else ""}.npz'
        np.savez_compressed(p, C=C, patró=pat, centre_yx=np.array([CY, CX]), e_ref=e_ref)
        # on canvia la v5 respecte de la v4: TOTS els píxels canviats han de caure a la petjada (LABx) d'una estructura de pols moguda
        canv = C != C4; PMx = np.zeros((h_, w_), bool)
        for oy in range(2):
            for ox in range(2): PMx[oy::2, ox::2][:hs, :ws] = np.isin(LABx, np.array(pols if pols else [-1], np.int32))
        d54 = (np.log(C) - np.log(C4)); dd = d54[lliure]
        rg.update(fitxer=str(p.relative_to(ARREL)), sha256=hashlib.sha256(p.read_bytes()).hexdigest(), n_encongides=len(ah), n_fora_regla_v3=len(fora),
                  C_menys_1_p1_p99=np.percentile(C[lliure] - 1, [1, 99]).round(6).tolist(), max_abs_C_menys_1=float(np.abs(C[lliure] - 1).max()),
                  v5_igual_a_v4_bit_a_bit=bool(not canv.any()), n_px_RAW_canviats_v5_v4=int(canv.sum()), n_px_canviats_fora_de_la_pols_moguda=int((canv & ~PMx).sum()),
                  canvi_v5_menys_v4_1e4=dict(rms_lliure=round(1e4 * float(np.sqrt(np.mean(dd.astype(np.float64) ** 2))), 4), max_abs=round(1e4 * float(np.abs(d54).max()), 2),
                                             frac_px_canviats=round(float(canv[lliure].mean()), 6)))
        if (canv & ~PMx).any(): sys.exit('ATURAT: la v5 canvia la C fora de la petjada de les estructures de pols moguda')
        # per estructura: què treu la v5 (en ln C, dins de la petjada, a cada canal), i quanta textura fina hi queda
        for e in rg['pols_moguda']:
            mk = LABx == e['id']; e['area_subpla_petjada'] = int(mk.sum()); e['canal'] = {}
            for k_cfa in RB:
                l4 = np.log(C4[k_cfa[0]::2, k_cfa[1]::2][:hs, :ws][mk].astype(np.float64)); l5 = np.log(C[k_cfa[0]::2, k_cfa[1]::2][:hs, :ws][mk].astype(np.float64))
                fi = (W * (FONS[k_cfa] - GT[k_cfa]))[mk] if k_cfa in GT else None
                e['canal'][CANAL[k_cfa]] = dict(rms_lnC_v4_1e4=round(1e4 * float(np.sqrt(np.mean(l4 ** 2))), 3), rms_lnC_v5_1e4=round(1e4 * float(np.sqrt(np.mean(l5 ** 2))), 3),
                                                rms_v5_menys_v4_1e4=round(1e4 * float(np.sqrt(np.mean((l5 - l4) ** 2))), 3),
                                                rms_textura_fina_aplicada_1e4=round(1e4 * float(np.sqrt(np.mean(fi.astype(np.float64) ** 2))), 3) if fi is not None else None)
        print(a.tren, gp, {k: v for k, v in rg.items() if k not in ('control_v3', 'control_v4', 'pols_moguda')}, flush=True)
        for e in rg['pols_moguda']: print('  pols moguda', e['id'], e['centre_llenc'], 'â v4', e['a_encongida_v4'], {c: (v['rms_v5_menys_v4_1e4'], v['rms_textura_fina_aplicada_1e4']) for c, v in e['canal'].items()}, flush=True)
        del C, C4, d54, canv, PMx
    rep['grups'][gp] = rg; del C3
rep['segons'] = time.time() - t0; rep['v5'] = dict(sigma_textura_llenc_px=a.sigma_textura_llenc, escala_llenc_px_per_subpla=a.escala_llenc, sigma_textura_subpla=SIG_TEX)
(OUT / f'{a.tren}_flat2d_v5{("_" + a.etiqueta if a.etiqueta else "") if enc else "_components"}_REBUT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float) + '\n')
print('FET', f'{time.time()-t0:.0f}s')
