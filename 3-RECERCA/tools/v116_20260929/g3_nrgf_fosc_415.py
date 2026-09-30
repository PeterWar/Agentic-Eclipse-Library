"""g3 (V116 · Claude, 29-09-2026): CÒPIA de g2 on el genoll (_SUP) compta també la capa nova 415 «Detall radial coherent Sony A·B» (Superposar,
opacitat V116_OPAC_415, sense màscara; ràster <filtres-std>/AB_coherent_u16.npy), damunt de la 56. Així cap capa de Superposar, tampoc la nova,
no pot dur la corona per sota del cel. Sense el ràster 415, g3 = g2.
--- capçalera de g2 ---
g2 (V115 · Claude, 29-09-2026) · CÒPIA de v108_20260926/negres_v2/g1_nrgf_genoll.py (que no es toca: la V114 en surt bit a bit) amb UN sol
canvi a l'operador, el token _kNN (1r intent, retirat: aixecava tota la meitat de baix, que és z < 0 pel gradient del cel) i el _LkNN (2n intent: només
l'estructura fosca LOCAL, z − mitjana de 400 px, amb el nivell de gran escala conservat); el _kNN: el COSTAT FOSC de la NRGF comprimit, z' = k·z on z < 0 (k = NN/100), abans del mapatge de pantalla i del genoll.
Per què (4-RESULTATS/v114_artefactes_foscos_20260929/RESULTAT.md): la NRGF normalitza cada radi per la mitjana i la dispersió azimutals; on hi ha
raigs brillants, el buit entre raigs queda molt per sota de la mitjana (z < 0) i la capa en Multiplicar (41 al 99 %) l'enfonsa 1,6–3 vegades més
que el jutge (Brno 200 mm, en unitats de textura). El genoll només impedeix baixar del CEL; aquestes clotades són corona (w alt) i no hi arriben.
La compressió és global (tot el rectangle, cap porta radial ni de marca), no posa llum on no n'hi ha (z ≥ 0 no canvia) i k es tria contra Brno.
Sense _kNN, el resultat és bit a bit el de g1 (control).
--- Capçalera original de g1 ---
g1 (V108 · negres_v2) · GANXO de la cadena V108 per a les capes 41 (P01 NRGF) i 42 (P01b NRGF estès): la NRGF de sempre (etapa E1 de
f3_filtres_v98.py, reproduïda bit a bit: variant V107) amb el gradient del cel fora del numerador (CEL) i un GENOLL físic que impedeix que
les capes en Multiplicar enfosqueixin la corona per sota del cel. RECOMANADA (27-09): CEL_G_MAX_T_e30_W_H0.

PRINCIPI. La corona és llum que se suma al cel: a l'espai de pantalla on el Photoshop multiplica, la base és I = S + K, i la part coronal és
w = K/I = 1 − S/I. Les capes en Multiplicar (54, 41, 42, 45, 46) hi fan I·F, F = Π (1 − a_i·(1 − f_i)), a_i = opacitat·alfa·màscara (V107).
L'enfosquiment que el realç posa per sobre del que rep el cel (el cel que es veu també passa per la pila) és D = 1 − F/F_cel, i I·F ≥ S·F_cel
⟺ D ≤ w. (Amb la D absoluta, 1 − F, la 41 ja enfosqueix un 22 % el nivell z = 0 i a 3–4,5 R☉ w és un 4–11 %: el genoll hi esborraria la corona
sencera; el diagnòstic «D_absoluta_sobre_w_gt_1» del rebut ho mesura: > 99 % dels píxels a 3–4,5 R☉.)
GENOLL: D' = c·h(D/c), sostre c = w − ε; h a trossos (_T): h(x) = x fins a x = 0,5 i 0,5 + 0,5·g((x − 0,5)/0,5) a sobre, g(y) = y/(1 + yⁿ)^(1/n),
n = 6 (sense _T, h = g). On D ≤ 0 (plomalls), res; on c ≤ 0, D' = 0. S'aplica REESCALANT (1 − f) de la 41 i la 42 amb un mateix s ∈ [0, 1]:
(1 − s·A41)(1 − s·A42) = F_cel·(1 − D')/F_altres. El genoll MAI no posa llum: com a molt treu l'enfosquiment de la 41/42 (u → 1).
DUES ESCALES: D, w i s es calculen amb la part suau (gaussiana σ = 6 px normalitzada pel domini) i només s'aixeca el NIVELL suau,
u' = u + (1 − s)·(1 − u_suau): el detall fi de la NRGF hi queda (_PIX = píxel a píxel, per comparar).
CELS (de la BASE DE LA CADENA, V108_BASE; mai del PSB): SEC = mediana per sectors de 10° a 5,0–5,6 R☉ dins del marc final (el cel que es veu;
conté corona); HQ = polinomi HARMÒNIC de 2n grau (1, x, y, x² − y², xy; sense terme radial: no absorbeix la corona F ni la K) ajustat a
6,5–8,4 R☉ (el cel vertader); MAX = el més restrictiu dels dos a cada píxel. Pesos (_W_H0, la recomanada): el SEC actua on la base és més
clara que l'anell (pes smoothstep(w_SEC, 0, 1 %): a l'anell mateix no aixeca la meitat fosca); el HQ és terra a TOT arreu, sense pes.
NORMA DEL RECTANGLE: cap porta radial ni de contorn. El genoll només l'aturen la falta de dada i els 40 px del limbe (fosa fins a 80 px), on
el ràster és bit a bit el de la cadena; així els 2.258 px de dins del disc que el r3_estat fa a la V107 s'hi conserven (comprovat amb el r3).
  Variants antigues, NOMÉS per documentar: _R (porta radial 4,7–5,0 R☉) i el pes sobre c del HQ (sense _H0) deixen una VORA visible (arc
  fosc a ~5 R☉ al sud: halo); sense cap pes, el SEC aplana l'anell de 5–5,6 R☉.
CEL (tokens CEL, CELH): z = z0 − fosa_limbe·(c₁x + c₂y)/σ(r), el dipol d'un pla (CELH: harmònic de 2n grau) ajustat a la dada lineal a 6,5–8,4 R☉;
tots els termes tenen mitjana nul·la sobre l'anell sencer: cap canvi de mètode a r_edge.
VARIANTS (noms separats per comes; a la cadena, UNA sola): V107 (control bit a bit) · CEL · CELH · [CEL_|CELH_]G_{SEC|HQ|MAX} + sufixos:
  _T (h a trossos) · _eNN (ε = NN/1000 de pantalla) · _nN · _sNN (σ del suau, px) · _W (pes del SEC sobre w) · _H0 (HQ sense pes) · _gNN (amplada
  del pes, NN/1000; 10 per defecte) · _I (2a passada del SEC) · _bNN (sostre β·w) · _SUP / _SUPz (compta les de Superposar; fa baixar Brno) ·
  _PIX · _R (porta radial; prohibida per la norma).
ÚS A LA CADENA (llegeix V108_BASE, V97_FONTS, V98_FRANJA, V97_SORT i V108_R; els ràsters de 54/45/46 de <V108_R>/filtres_std/filtres; les màscares i
opacitats de 1-PHOTOSHOP/V107.psb, només lectura):
  V108_F41="3-RECERCA/tools/v108_20260926/negres_v2/g1_nrgf_genoll.py CEL_G_MAX_T_e30_W_H0" V108_F42=<el mateix> zsh cadena_v108.sh <variant>
  (~100 s, pic ~13,4 GB; sortida <V97_SORT>/CEL_G_MAX_T_e30_W_H0/P01_NRGF[_extrap][_alfa]_u16.npy, l'única subcarpeta que busca «troba»).
Sol (per defecte, entrades de la variant «control» de la cadena; sortida a 4-RESULTATS/v108_20260926/negres_v2/candidats):
  g1_nrgf_genoll.py V107,CEL_G_MAX_T_e30_W_H0     → rebut <V97_SORT>/G1_<variants>.json"""
import sys, os, json, time, argparse, subprocess
from pathlib import Path
R0 = Path(__file__).resolve().parents[3]   # (g1 era una carpeta més endins)
CTRL = R0 / '4-RESULTATS/v108_20260926/cadena/control'
for k, v in (('V97_FONTS', CTRL / 'lineal'), ('V98_FRANJA', CTRL / 'franja/A3C_franja_silueta.npz'), ('V108_BASE', CTRL / 'base/base_v108_final_u16.npy'),
             ('V108_R', CTRL), ('V97_SORT', R0 / '4-RESULTATS/v108_20260926/negres_v2/candidats')):
    os.environ.setdefault(k, str(v))
def ruta(p): p = Path(p); return p if p.is_absolute() else R0 / p
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v97_refundacio_20260924'))
from v97_comu import *   # noqa: F401,F403  (H, W, CX, CY, RS, FONTS, SORT, log, sha, coords, claim)
from v86_operadors import ring_stats, complete_from_partial, smoothstep, NB
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
from scipy.ndimage import gaussian_filter1d
import numpy as np, cv2
cv2.setNumThreads(6)
ap = argparse.ArgumentParser(); ap.add_argument('variants', nargs='?', default='CEL_G_MAX_T_e30_W_H0')
ap.add_argument('--psb', default=os.environ.get('V108_PSB_MASCARES', str(R0 / '1-PHOTOSHOP/V107.psb')), help='PSB de Pere: màscares i opacitats (només lectura)')
ap.add_argument('--filtres-std', default=os.environ.get('V108_FILTRES_STD', ''), help='ràsters de 54/45/46 (per defecte <V108_R>/filtres_std/filtres)')
A = ap.parse_args(); VARS = A.variants.split(','); claim(); T0 = time.time()
BASEP = ruta(os.environ['V108_BASE']); VR = ruta(os.environ['V108_R']); FSTD = ruta(A.filtres_std) if A.filtres_std else VR / 'filtres_std/filtres'
DISP = R0 / '2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/filters_v58_dependencies/display'
def display(tag): d = json.loads((DISP / f'{tag}.json').read_text())['display']; return float(d['black']), float(d['white'])
MARC = (1325, 1142, 9348, 6263)                                     # enquadrament final (jutge_comu)
TAGS = {415: 'AB_coherent', 41: 'P01_NRGF', 42: 'P01_NRGF_extrap', 54: 'P03_MGN', 45: 'P02c_RHEF_local60_native', 46: 'P02d_RHEF_local30_native',
        47: '03', 49: '07', 51: '04', 55: 'P04_WOW', 56: 'P05_WOW_bilateral'}
rep = dict(guio=str(Path(__file__).relative_to(R0)), variants_demanades=VARS, font=str(FONTS), franja=os.environ['V98_FRANJA'], base=str(BASEP),
           filtres_std=str(FSTD), psb=A.psb, variant_cadena=os.environ.get('V108_VARIANT'), capes=os.environ.get('V108_CAPES'), variants={})
# ---------- fonts i domini (idèntic a f3_filtres_v98.py, etapa E1) ----------
Q = np.load(os.environ['V98_FRANJA']); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]; BOXQ = (slice(qy0, qy1), slice(qx0, qx1))
cx, cy, R = [float(v) for v in Q['centre']]; DMIN = Q['DMIN']; NBZ = len(DMIN)
a = np.load(FONTS / 'base_G.npy').astype(np.float32); m_sup = np.load(FONTS / 'support.npy') & np.isfinite(a) & (a > 0)
a[BOXQ] = Q['G']; m = m_sup.copy(); m[BOXQ] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a); del m_sup
r, t = coords()
yy, xx = np.ogrid[:H, :W]; dL = (np.hypot(xx - cx, yy - cy) - R).astype(np.float32)
dLb = dL[BOXQ].copy(); thLb = ((np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360).astype(np.float32)[BOXQ].copy()
def nivell_buit(u01, mm, fosa=(0.0, 1.5)):
    """Còpia literal de f3_filtres_v98.nivell_buit (decisió B de Pere, 24-09)."""
    out = u01.copy(); d = dLb; th = thLb; dist = d - np.maximum(DMIN, 0)[(th / 360 * NBZ).astype(int) % NBZ]; mb = mm[BOXQ]; ub = out[BOXQ]
    NT = 3600; tb_ = (th / 360 * NT).astype(int) % NT; zona = mb & (dist >= 2) & (dist < 8)
    s = np.bincount(tb_[zona], weights=ub[zona], minlength=NT); n = np.bincount(tb_[zona], minlength=NT).astype(float); sig = 3.0 / (R * np.radians(360 / NT))
    L = (gaussian_filter1d(s, sig, mode='wrap') / np.maximum(gaussian_filter1d(n, sig, mode='wrap'), 1e-9))[tb_].astype(np.float32)
    buit = (~mb) & (d >= 0) & (d < 45); ub = np.where(buit, L, ub)
    zf = mb & (dist >= 0) & (dist < fosa[1]) & (d < 45)
    wfs = smoothstep(dist, fosa[0], fosa[1]); ub = np.where(zf, L + (ub - L) * wfs, ub)
    out[BOXQ] = ub; out[~mm & ~np.pad(np.ones_like(mb), ((qy0, H - qy1), (qx0, W - qx1)))] = 0.5
    return out, int(buit.sum())
def u_affine(q, lo, hi): return np.clip((q - lo) / (hi - lo), 0, 1).astype(np.float32)
ALFA = np.round(np.clip(dL, 0, 1) * 65535).astype(np.uint16)
# ---------- estadística d'anells (idèntica a l'E1) ----------
ri = np.floor(r).astype('int32'); nr = int(ri.max()) + 1; ids = ri[m]; tb = np.floor((t[m] + np.pi) / (2 * np.pi) * NB).astype('int32') % NB; del t, ri
nodes = np.arange(nr) + .5
v = a[m].astype('float64')
count, mean, std = ring_stats(v, ids, nr); good = count > 0
comp = count / (2 * np.pi * nodes); refc = np.median(comp[int(3 * RS):int(8 * RS)])
cand_out = np.flatnonzero((nodes > 3 * RS) & (comp < 0.98 * refc)); r_edge = int(cand_out[0]) if cand_out.size else nr
r_in = int(np.flatnonzero((comp >= 0.98 * refc) & (nodes > 0.9 * RS))[0])
inner = [i for i in range(r_in) if count[i] > 0]; outer = list(range(r_edge, nr))
mean_u, std_u, ok_o, _, _ = complete_from_partial(mean, std, ids, tb, v, outer, list(range(r_edge - 40, r_edge)))
mean_u, std_u2, ok_i, _, _ = complete_from_partial(mean_u, std_u, ids, tb, v, inner, list(range(r_in, r_in + 40)))
ok_ring = good & ok_o & ok_i; del v, tb
mu = np.interp(r, nodes[ok_ring], mean_u[ok_ring]).astype('float32'); sd0 = np.interp(r, nodes[ok_ring], std_u2[ok_ring]).astype('float32')
z0 = np.divide(a - mu, sd0, out=np.zeros_like(a), where=sd0 > 0).astype('float32'); del mu
rep.update(r_in=r_in, r_edge=r_edge, r_edge_Rsol=r_edge / RS); log(f'E1 · r_in {r_in} · r_edge {r_edge} ({r_edge / RS:.3f} R☉)')
X = ((np.arange(W, dtype=np.float32) - CX) / 4000)[None, :]; Y = ((np.arange(H, dtype=np.float32) - CY) / 4000)[:, None]
rr = (r / RS).astype(np.float32)
LIM40 = dL < 40
LIMBF = smoothstep(dL, 40.0, 80.0).astype(np.float32)             # fosa del limbe (40→80 px): a menys de 40 px, res no canvia
del r
# ---------- CEL: el gradient del cel fora del numerador (dada lineal, 6,5–8,4 R☉) ----------
def model_cel_lineal(tipus):
    sel = m & (rr > 6.5) & (rr < 8.4); sub = np.zeros_like(sel); sub[::4, ::4] = True; sel &= sub; del sub
    ys_, xs_ = np.nonzero(sel); x_ = (xs_ - CX) / 4000; y_ = (ys_ - CY) / 4000
    base = [np.ones_like(x_), x_, y_] + ([x_ * x_ - y_ * y_, x_ * y_] if tipus == 'harm' else [])
    Am = np.stack(base, 1); b = a[sel].astype(np.float64); okf = np.ones(len(b), bool)
    for _ in range(4):
        cf, *_ = np.linalg.lstsq(Am[okf], b[okf], rcond=None); res = b - Am @ cf; s_ = np.std(res[okf]); okf = np.abs(res) < 2.5 * s_
    # part azimutal: tots els termes menys el constant tenen mitjana nul·la sobre l'anell SENCER centrat al Sol → cap canvi de mètode a r_edge
    c = [float(x) for x in cf]; Saz = (c[1] * X + c[2] * Y).astype(np.float32)
    if tipus == 'harm': Saz += (c[3] * (X * X - Y * Y) + c[4] * (X * Y)).astype(np.float32)
    return Saz, dict(tipus=tipus, coef=[float(c) for c in cf], residu_rms=float(s_), punts=int(okf.sum()))
ZV = {'V107': z0}
need = {k.split('_')[0] for k in VARS}
for nomc, tip in (('CEL', 'pla'), ('CELH', 'harm')):
    if nomc in need:
        Saz, info = model_cel_lineal(tip); ZV[nomc] = np.where(m & (sd0 > 0), z0 - LIMBF * Saz / np.maximum(sd0, 1e-12), 0).astype(np.float32); del Saz
        rep['model_cel_lineal_' + nomc] = info; log(f'{nomc}: {info}')
del a, sd0
lo41, hi41 = display('P01_NRGF'); lo42, hi42 = display('P01_NRGF_extrap')
def rasters(z):
    out = {}
    for tag, lo, hi in (('P01_NRGF', lo41, hi41), ('P01_NRGF_extrap', lo42, hi42)):
        u = np.where(m, u_affine(z, lo, hi), 0.5); u, nb = nivell_buit(u, m); out[tag] = u
    return out
# ---------- el genoll: entrades comunes (només si alguna variant el porta) ----------
KNEE = any('G' in k.split('_') for k in VARS)
if KNEE:
    psb = PSB(str(ruta(A.psb))); CAPA = {}
    OPAC415 = float(os.environ.get('V116_OPAC_415', '0.40'))
    def efectiva(lid):
        """a = opacitat · alfa del ràster · màscara de Pere (V107), a tot el llenç (float32). La 415 (nova, V116) no és al PSB de Pere: opacitat OPAC415, sense màscara."""
        if lid == 415:
            al = np.load(FSTD / f'{TAGS[lid]}_alfa_u16.npy', mmap_mode='r'); e = np.asarray(al, np.float32) / 65535 * OPAC415
            CAPA[lid] = dict(nom='Detall radial coherent Sony A·B', mode='OVERLAY', opacitat=OPAC415); return e.astype(np.float32)
        l = psb.layer(lid); mk = l['mask']; o = l['opacity'] / 255.0
        mm_ = psb.channel_box(lid, -2, (0, 0, W, H), fill=65535 if (mk and mk['background'] == 255) else 0)
        al = np.load(FSTD / f'{TAGS[lid]}_alfa_u16.npy', mmap_mode='r') if lid not in (41, 42) else ALFA
        e = (np.asarray(al, np.float32) / 65535) * (np.ones((H, W), np.float32) if mm_ is None else mm_.astype(np.float32) / 65535) * o
        CAPA[lid] = dict(nom=l['name'], mode=l['blend'], opacitat=l['opacity'], visible=l['visible'], mascara_mitjana_1_5R=float(e[(rr > 1.3) & (rr < 5)].mean() / max(o, 1e-9)))
        return e.astype(np.float32)
    a41 = efectiva(41); a42 = efectiva(42)
    def llegeix(lid): return efectiva(lid), np.load(FSTD / f'{TAGS[lid]}_u16.npy').astype(np.float32) / 65535
    def factor_altres(sup, U=None):
        """Factor de la pila sense la 41 i la 42: 54, 45, 46 en Multiplicar i, amb sup, 47, 49, 51, 55, 56 en Superposar amb la fórmula del Photoshop
        sobre el compost que tenen a sota, b (base × les capes de sota, amb la 41/42 d'entrada): factor = 1 − a + a·ov(b, f)/b,
        ov = 2bf (b < 0,5) o 1 − 2(1 − b)(1 − f). Ordre de la pila: 54, 41, 42, 47, 49, 51, 45, 46, 55, 56."""
        e, u = llegeix(54); F = (1 - e * (1 - u)).astype(np.float32); del e, u
        if not sup:
            for lid in (45, 46): e, u = llegeix(lid); F *= 1 - e * (1 - u); del e, u
            return F, None
        Fov = np.ones((H, W), np.float32)
        b = B * F; b *= 1 - a41 * (1 - U['P01_NRGF']); b *= 1 - a42 * (1 - U['P01_NRGF_extrap'])
        for grup in ((47, 49, 51), (45, 46), (55, 56) + ((415,) if (FSTD / 'AB_coherent_u16.npy').exists() else ())):
            for lid in grup:
                e, u = llegeix(lid)
                if lid in (45, 46): fct = 1 - e * (1 - u)
                else:
                    bb = np.maximum(b, 1e-4); ov = np.where(bb < 0.5, 2 * bb * u, 1 - 2 * (1 - bb) * (1 - u)); fct = 1 - e + e * ov / bb; del ov, bb
                (F if lid in (45, 46) else Fov)[...] *= fct; b *= fct; del e, u, fct
        del b
        return F, Fov
    Bl = np.load(BASEP, mmap_mode='r')
    B = np.empty((H, W), np.float32)
    for y0 in range(0, H, 1024):   # (cada canal a float ABANS de sumar: 2·G en uint16 desborda a G > 32767)
        c_ = np.asarray(Bl[y0:y0 + 1024], np.float32); B[y0:y0 + 1024] = (c_[..., 0] + 2 * c_[..., 1] + c_[..., 2]) / (4 * 65535); del c_
    del Bl
    VAL = (m & (dL >= 0) & (B > 1e-4)).astype(np.float32)
    def suau(x, s):
        den = cv2.GaussianBlur(VAL, (0, 0), s); return (cv2.GaussianBlur(x * VAL, (0, 0), s) / np.maximum(den, 1e-6)).astype(np.float32)
    thS = ((np.degrees(np.arctan2(-(yy - CY), xx - CX)) + 360) % 360).astype(np.float32)
    SEC10 = (thS // 10).astype(np.int8) % 36                                   # sector de 10° (θ: 0° = dreta, 90° = amunt)
    xs_ = thS / 10 - 0.5; SEC_I0 = (np.floor(xs_).astype(np.int16) % 36).astype(np.int8); SEC_F = (xs_ - np.floor(xs_)).astype(np.float32); del xs_, thS
    marc = np.zeros((H, W), bool); marc[MARC[1]:MARC[3], MARC[0]:MARC[2]] = True
    # NORMA DEL RECTANGLE: el genoll actua a TOT el rectangle; només la falta de dada (fora del domini) i els 40 px del limbe (encàrrec) l'aturen.
    # (_R = diagnòstic antic, porta radial 4,7–5,0 R☉: PROHIBIT per la norma; es conserva només per documentar la cúpula que feia.)
    GATE_R = (LIMBF * (1 - smoothstep(rr, 4.7, 5.0))).astype(np.float32); GATE = LIMBF
    del dL
    rep['capes_V107'] = CAPA
    TROSSOS = [False]
    def h(x, n):
        """h(x) = x/(1 + xⁿ)^(1/n); amb _T («a trossos»), h = x fins a x = 0,5 exactament i 0,5 + 0,5·g((x − 0,5)/0,5) a sobre (g = la mateixa forma)."""
        x = np.minimum(x, 1e4)
        if not TROSSOS[0]: return (x / (1 + x ** n) ** (1.0 / n)).astype(np.float32)
        y = np.maximum(x - 0.5, 0) / 0.5; return np.where(x <= 0.5, x, 0.5 + 0.5 * y / (1 + y ** n) ** (1.0 / n)).astype(np.float32)
    def cel_i_nivell(Bs, Cs, ref):
        """Model del cel S (base de pantalla) i del compost en Multiplicar al cel C_cel = S·F_cel, al llenç sencer."""
        if ref == 'SEC':
            idx = np.flatnonzero((VAL > 0) & (rr >= 5.0) & (rr < 5.6) & marc); sec = SEC10.ravel()[idx]; bv = Bs.ravel()[idx]; cv_ = Cs.ravel()[idx]
            Sv = np.full(36, np.nan); Cv = np.full(36, np.nan)
            for i in range(36):
                k = sec == i
                if k.sum() > 2000: Sv[i] = np.median(bv[k]); Cv[i] = np.median(cv_[k])
            g = np.isfinite(Sv); ii = np.arange(36); Sv = np.interp(ii, ii[g], Sv[g], period=36).astype(np.float32); Cv = np.interp(ii, ii[g], Cv[g], period=36).astype(np.float32)
            i1_ = (SEC_I0.astype(np.int16) + 1) % 36
            S = (1 - SEC_F) * Sv[SEC_I0] + SEC_F * Sv[i1_]; C = (1 - SEC_F) * Cv[SEC_I0] + SEC_F * Cv[i1_]; del i1_
            info = dict(S_sectors=[float(v_) for v_ in Sv], Fcel_sectors=[float(c / s_) for c, s_ in zip(Cv, Sv)], sectors_amb_dada=int(g.sum()), px_anell=int(len(idx)))
            return S.astype(np.float32), C.astype(np.float32), info
        sel = (VAL > 0) & (rr >= 6.5) & (rr < 8.4); sub = np.zeros_like(sel); sub[::4, ::4] = True; sel &= sub
        ys_, xs_ = np.nonzero(sel); x_ = (xs_ - CX) / 4000; y_ = (ys_ - CY) / 4000
        Am = np.stack([np.ones_like(x_), x_, y_, x_ * x_ - y_ * y_, x_ * y_], 1); out = []; info = {}
        for nom_, img in (('S', Bs), ('C', Cs)):
            b = img[sel].astype(np.float64); okf = np.ones(len(b), bool)
            for _ in range(4):
                cf, *_ = np.linalg.lstsq(Am[okf], b[okf], rcond=None); res = b - Am @ cf; s_ = np.std(res[okf]); okf = np.abs(res) < 2.5 * s_
            c0, c1, c2, c3, c4 = [float(c) for c in cf]; out.append((c0 + c1 * X + c2 * Y + c3 * (X * X - Y * Y) + c4 * (X * Y)).astype(np.float32))
            info[nom_] = dict(coef=[float(c) for c in cf], residu_rms=float(s_), punts=int(okf.sum()))
        return out[0], out[1], info
    FO_CACHE, BS_CACHE = {}, {}
    BETA = [1.0]; EPS = [0.0]; SUPZ = [0.0]; RADIAL = [False]; GC = [0.01]; ITER = [False]; PESW = [False]; REFNOMS = [()]; HQ0 = [False]
    def knee_punt(Bs, REFS, A1, A2, Fo_, n):
        """Càlcul punt a punt (franges o submostres). REFS = [(S, Fcel), …]: per a cada cel, D = 1 − F/Fcel, w = 1 − S/B, sostre c = β·w − ε,
        D' = c·h(D/c) (D' = 0 si c ≤ 0 i D > 0); objectiu F' = Fcel·(1 − D'); amb diversos cels, el més restrictiu (el F' més alt)."""
        Fp = (1 - A1) * (1 - A2) * Fo_; Ft = None
        for k_, (S, Fcel) in enumerate(REFS):
            D = 1 - Fp / np.maximum(Fcel, 1e-6); w = 1 - S / np.maximum(Bs, 1e-6); c_ = BETA[0] * w - EPS[0]; cpos = np.maximum(c_, 1e-6)
            Dp = np.where(D > 0, np.where(c_ > 0, cpos * h(np.maximum(D, 0) / cpos, n), 0.0), D)
            if GC[0] > 0 and not (HQ0[0] and REFNOMS[0][k_] == 'HQ'):   # _H0: el cel vertader (HQ) és terra a tot arreu, sense pes (sense vora)
                # SEC (anell de 5–5,6 R☉, amb corona): el pes va sobre w (on la base és més clara que l'anell, el buit no pot quedar-hi per sota; a l'anell
                # mateix, la meitat més fosca no s'aixeca). HQ (cel vertader): el pes va sobre c = w − ε (cal corona per sobre del marge).
                gg = smoothstep(w if (PESW[0] and REFNOMS[0][k_] == 'SEC') else c_, 0.0, GC[0]); Dp = gg * Dp + (1 - gg) * D
            T_ = Fcel * (1 - Dp); Ft = T_ if Ft is None else np.maximum(Ft, T_)
            if Ft is T_: D0, w0 = D, w
        G = (1 - A1) * (1 - A2); Gt = np.clip(Ft / np.maximum(Fo_, 1e-6), G, 1.0); D, w = D0, w0
        P = A1 + A2; Qp = A1 * A2; c = 1 - Gt
        s = np.where(P > 1e-6, 2 * c / np.maximum(P + np.sqrt(np.maximum(P * P - 4 * Qp * c, 0)), 1e-9), 1.0)
        return D.astype(np.float32), w.astype(np.float32), np.clip(s, 0, 1).astype(np.float32), Fp.astype(np.float32)
    def genoll(U, ref, n, sig, pix, sup, info):
        """U = {tag: u (float32, llenç sencer)} → U' amb el genoll aplicat (només on GATE > 0). Franges de 512 files per al càlcul punt a punt."""
        kf = (sup, info['parametres']['z'] if sup else '')
        if kf not in FO_CACHE: FO_CACHE.clear(); FO_CACHE[kf] = (factor_altres(sup, U), None)
        Fo = FO_CACHE[kf][0]
        if FO_CACHE[kf][1] is None or FO_CACHE[kf][1][0] != (sig, SUPZ[0]):
            Fm, Fv = Fo; Fs_ = suau(Fm, sig)
            if Fv is not None: Fs_ *= suau(Fv, SUPZ[0] or sig)          # _SUPz: les de Superposar, només a escala de zona (σ 32 px)
            FO_CACHE[kf] = (Fo, ((sig, SUPZ[0]), Fs_))
        Fos = FO_CACHE[kf][1][1]; Fo = Fo[0] if Fo[1] is None else Fo[0] * Fo[1]
        if sig not in BS_CACHE: BS_CACHE.clear(); BS_CACHE[sig] = suau(B, sig)
        Bs = BS_CACHE[sig]
        u1, u2 = U['P01_NRGF'], U['P01_NRGF_extrap']
        u1s, u2s = suau(u1, sig), suau(u2, sig)
        Fs = (1 - a41 * (1 - u1s)); Fs *= (1 - a42 * (1 - u2s)); Fs *= Fos
        C = Bs * Fs; del Fs; REFS = []; info['cel'] = {}; REFNOMS[0] = ('SEC', 'HQ') if ref == 'MAX' else (ref,)
        for rf in (('SEC', 'HQ') if ref == 'MAX' else (ref,)):
            S, Cr, info['cel'][rf] = cel_i_nivell(Bs, C, rf); Cr /= np.maximum(S, 1e-6); REFS.append((S, Cr))
        del C
        def passada(REFS):
            s = np.ones((H, W), np.float32)
            for y0 in range(0, H, 512):
                sl = slice(y0, min(H, y0 + 512))
                GT = GATE_R if RADIAL[0] else GATE
                if not (GT[sl] > 0).any(): continue
                if pix: A1, A2, Fo_ = a41[sl] * (1 - u1[sl]), a42[sl] * (1 - u2[sl]), Fo[sl]
                else: A1, A2, Fo_ = a41[sl] * (1 - u1s[sl]), a42[sl] * (1 - u2s[sl]), Fos[sl]
                _, _, ss, _ = knee_punt(Bs[sl], [(S_[sl], F_[sl]) for S_, F_ in REFS], A1, A2, Fo_, n)
                s[sl] = 1 - GT[sl] * (1 - ss)                                         # a menys de 40 px del limbe, s = 1 (cap canvi)
            return s
        s = passada(REFS)
        if ITER[0] and ref in ('SEC', 'MAX'):
            # 2a passada: el cel SEC (el que es veu a 5–5,6 R☉ dins del marc) es torna a mesurar al compost DESPRÉS de la 1a passada del genoll
            # (el genoll hi aixeca la corona feble que el realç posava per sota del cel de fora); el genoll es refà des del ràster ORIGINAL.
            C2_ = (1 - a41 * (1 - (1 - s * (1 - u1s)))) * (1 - a42 * (1 - (1 - s * (1 - u2s)))) * Fos * Bs
            S2, Cr2, info['cel']['SEC_2a_passada'] = cel_i_nivell(Bs, C2_, 'SEC'); Cr2 /= np.maximum(S2, 1e-6); del C2_
            REFS = [(S2, Cr2) if (rf == 'SEC') else R_ for rf, R_ in zip((('SEC', 'HQ') if ref == 'MAX' else (ref,)), REFS)]
            del s; s = passada(REFS)
        out = {}
        for tag, u, us in (('P01_NRGF', u1, u1s), ('P01_NRGF_extrap', u2, u2s)):
            out[tag] = np.clip(1 - s * (1 - u) if pix else u + (1 - s) * (1 - us), 0, 1).astype(np.float32)
        # diagnòstic per bandes (subgraella de pas 2, dins del marc, fora del limbe)
        g2 = (slice(None, None, 2), slice(None, None, 2))
        if pix: A1, A2, Fo_ = a41[g2] * (1 - u1[g2]), a42[g2] * (1 - u2[g2]), Fo[g2]
        else: A1, A2, Fo_ = a41[g2] * (1 - u1s[g2]), a42[g2] * (1 - u2s[g2]), Fos[g2]
        D, w, _, Fp = knee_punt(Bs[g2], [(S_[g2], F_[g2]) for S_, F_ in REFS], A1, A2, Fo_, n); s2 = s[g2]; du = out['P01_NRGF'][g2] - u1[g2]
        okd = (VAL[g2] > 0) & marc[g2] & ~LIM40[g2]; r2 = rr[g2]; dg = {}
        for a_, b_ in ((1.02, 1.3), (1.3, 2), (2, 3), (3, 4.5), (4.5, 5), (5, 7)):
            k = okd & (r2 >= a_) & (r2 < b_)
            if not k.any(): continue
            dk = du[k]; wk = w[k]; Dk = D[k]
            dg[f'{a_:g}-{b_:g}'] = dict(w_p10_p50_p90=[float(q) for q in np.percentile(wk, [10, 50, 90])], D_p50_p90_p99=[float(q) for q in np.percentile(Dk, [50, 90, 99])],
                                         frac_D_sobre_w_gt_0_5=float(((Dk > 0.5 * np.maximum(wk, 0)) & (Dk > 0)).mean()), frac_D_sobre_w_gt_1=float(((Dk > np.maximum(wk, 0)) & (Dk > 0)).mean()),
                                         D_absoluta_sobre_w_gt_1=float(((1 - Fp[k]) > np.maximum(wk, 0)).mean()),
                                         s_mitjana=float(s2[k].mean()), frac_s_lt_0_999=float((s2[k] < 0.999).mean()), frac_tocats_du_gt_1_512=float((np.abs(dk) > 1 / 512).mean()),
                                         du41_mitjana=float(dk.mean()), du41_p99=float(np.percentile(dk, 99)))
        info['diagnostic'] = dg
        del u1s, u2s, REFS, s
        return out
# ---------- desament ----------
ALFA_FET = {}
def desa_variant(nom, U, info):
    d = SORT / nom; d.mkdir(parents=True, exist_ok=True)
    for tag, lo, hi in (('P01_NRGF', lo41, hi41), ('P01_NRGF_extrap', lo42, hi42)):
        u16 = np.round(np.clip(np.nan_to_num(U[tag], nan=0.5), 0, 1) * 65535).astype(np.uint16); np.save(d / f'{tag}_u16.npy', u16)
        fa = d / f'{tag}_alfa_u16.npy'
        if not fa.exists():
            if tag in ALFA_FET: subprocess.run(['cp', '-c', str(ALFA_FET[tag]), str(fa)], check=True)   # clon APFS (sense cost de disc)
            else: np.save(fa, ALFA); ALFA_FET[tag] = fa
        info[tag] = dict(display=[lo, hi], sha256_u16=sha(d / f'{tag}_u16.npy'))
        std = FSTD / f'{tag}_u16.npy'
        if std.exists():
            s0 = np.load(std, mmap_mode='r'); lim = LIM40
            info[tag]['igual_a_la_cadena_a_menys_de_40px_del_limbe'] = bool(np.array_equal(u16[lim], np.asarray(s0)[lim]))
            info[tag]['px_diferents_de_la_cadena'] = int((u16 != s0).sum())
            if nom == 'V107': info[tag]['control_bit_a_bit_amb_la_cadena'] = bool(np.array_equal(u16, s0))
    rep['variants'][nom] = info; log(f'{nom} desada · ' + json.dumps({k: v_ for k, v_ in info.items() if k in ('P01_NRGF',)}, ensure_ascii=False)[:300])
def gauss_dom(x, dom, sg):
    """mitjana gaussiana normalitzada al domini, calculada a 1/8 (camps suaus) i tornada a la mida original (bilineal)."""
    f = 8; h, w = x.shape; hs, ws = (h + f - 1) // f, (w + f - 1) // f
    xs = cv2.resize(np.where(dom, x, 0).astype(np.float32), (ws, hs), interpolation=cv2.INTER_AREA); ds = cv2.resize(dom.astype(np.float32), (ws, hs), interpolation=cv2.INTER_AREA)
    return cv2.resize(cv2.GaussianBlur(xs, (0, 0), sg / f) / np.maximum(cv2.GaussianBlur(ds, (0, 0), sg / f), 1e-6), (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32)
CACHE_U = {}
for nom in VARS:
    tok = nom.split('_'); info = dict(parametres={})
    zk = tok[0] if tok[0] in ('CEL', 'CELH') else 'V107'
    kf = next((int(t_[1:]) / 100 for t_ in tok if t_[:1] == 'k' and t_[1:].isdigit()), None)   # V115: costat fosc comprimit (z < 0 → k·z)
    kl = next((int(t_[2:]) / 100 for t_ in tok if t_[:2] == 'Lk' and t_[2:].isdigit()), None)  # V115 (2n intent): només l'estructura LOCAL fosca
    if (zk, kf, kl) not in CACHE_U:
        zz = ZV[zk] if kf is None else np.where(ZV[zk] < 0, ZV[zk] * np.float32(kf), ZV[zk]).astype(np.float32)
        if kl is not None:
            # z = z_gran + z_local (z_gran = mitjana gaussiana normalitzada al domini, σ 400 px): es comprimeix NOMÉS z_local < 0 (buits entre raigs)
            # i es torna el nivell de gran escala a l'original (el gradient del cel entre dalt i baix, la forma gran de la corona, no canvien)
            zl = zz - gauss_dom(zz, m, 400.0); dz = np.where(zl < 0, (np.float32(kl) - 1) * zl, 0).astype(np.float32); del zl
            zz = np.where(m, zz + dz - gauss_dom(dz, m, 400.0), zz).astype(np.float32); del dz
        CACHE_U[(zk, kf, kl)] = rasters(zz); del zz
    U = CACHE_U[(zk, kf, kl)]
    if 'G' in tok:
        ref = tok[tok.index('G') + 1]; assert ref in ('SEC', 'HQ', 'MAX'), nom
        n = next((int(k[1:]) for k in tok if k[:1] == 'n' and k[1:].isdigit()), 6); sig = next((float(k[1:]) for k in tok if k[:1] == 's' and k[1:].isdigit()), 6.0)
        pix, sup = 'PIX' in tok, ('SUP' in tok or 'SUPz' in tok); SUPZ[0] = 32.0 if 'SUPz' in tok else 0.0; RADIAL[0] = 'R' in tok; ITER[0] = 'I' in tok; PESW[0] = 'W' in tok; HQ0[0] = 'H0' in tok; GC[0] = next((int(k[1:]) / 1000 for k in tok if k[:1] == 'g' and k[1:].isdigit()), 0.01); TROSSOS[0] = 'T' in tok; BETA[0] = next((int(k[1:]) / 100 for k in tok if k[:1] == 'b' and k[1:].isdigit()), 1.0)
        EPS[0] = next((int(k[1:]) / 1000 for k in tok if k[:1] == 'e' and k[1:].isdigit()), 0.0)
        info['parametres'] = dict(z=zk, k_costat_fosc=kf, k_local_fosc_sigma400=kl, cel_ref=ref, n=n, beta=BETA[0], marge_eps=EPS[0], h_a_trossos=TROSSOS[0], sigma_suau_px=sig, pixel_a_pixel=pix, compta_superposar=sup, superposar_a_escala_de_zona_px=SUPZ[0], porta_radial_4_7_5_0_Rsol=RADIAL[0], pes_corona_smoothstep_c_0_a=GC[0], cel_SEC_autoconsistent=ITER[0], pes_SEC_sobre_w=PESW[0], HQ_sense_pes=HQ0[0], limbe_px=[40, 80])
        U = genoll(U, ref, n, sig, pix, sup, info)
    elif '_'.join(t_ for t_ in tok if not ((t_[:1] == 'k' and t_[1:].isdigit()) or (t_[:2] == 'Lk' and t_[2:].isdigit()))) not in ('V107', 'CEL', 'CELH'): raise SystemExit('variant desconeguda ' + nom)
    else: info['parametres'] = dict(z=zk, k_costat_fosc=kf, k_local_fosc_sigma400=kl)
    desa_variant(nom, U, info); del U
rep['segons'] = round(time.time() - T0)
p = SORT / f'G1_{"_".join(VARS)[:120]}.json'; p.write_text(json.dumps(rep, ensure_ascii=False, indent=1, default=float) + '\n'); log('FET ' + str(p))
