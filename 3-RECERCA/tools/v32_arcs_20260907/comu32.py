"""V32 · arcs lila/blau: rutes, geometria i utilitats comunes.

Reutilitza la geometria de la V29 (graella final 10551x7506, Sol per efemèride)
i la cadena determinista (calibratge, registre, pesos LDIC) sense modificar-la.
Cap sortida d'aquest paquet toca els PSB, els RAW ni els runs.
"""
import os, sys, json, time, hashlib
from pathlib import Path
os.environ['V29_FINAL_GRID'] = '1'
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026')
sys.path.insert(0, str(ROOT / 'research/tools/v29'))
from common import *          # H, W, CX, CY, RS, RUNS, COMMON_TO_FINAL, coords, smooth, gauss, normgauss, comu, ...
import f2                     # cadena determinista: Ctx, finestra, mascara_lluna

HERE = Path(__file__).resolve().parent
CAU32 = HERE / 'cau'
OUT32 = ROOT / 'output/v32_arcs_20260907'
VIS = OUT32 / 'lliurables/vistes'
REB = OUT32 / '4-rebuts'
IAOUT = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v32_arcs_20260907')
for p in (CAU32, VIS, REB, IAOUT):
    p.mkdir(parents=True, exist_ok=True)
FIX = ROOT / 'research/tools/v29_c03_fix'
CAUF = CAU                    # v29/cau_final (graella final): fonts, suports i pesos del compost V29
assert CAUF.name == 'cau_final', CAUF
V31P = ROOT / 'research/tools/v31_purs'
CATALEG = ROOT / 'output/revisio_marques_v31_20260907/lliurables/CATALEG_MARQUES.csv'
CATALEG_JSON = ROOT / 'output/revisio_marques_v31_20260907/4-rebuts/review_catalog.json'
Q = 4                          # factor de la graella grossa de diagnosi
HC, WC = H // Q, W // Q

def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()

def coarse_coords():
    """Coordenades (x, y) al llenç final dels centres de les cel·les de la graella grossa."""
    yc = (np.arange(HC, dtype=np.float32) * Q + (Q - 1) / 2.0)
    xc = (np.arange(WC, dtype=np.float32) * Q + (Q - 1) / 2.0)
    return xc, yc

def coarse_polar():
    xc, yc = coarse_coords()
    r = np.hypot(xc[None, :] - CX, yc[:, None] - CY).astype(np.float32)
    t = np.arctan2(yc[:, None] - CY, xc[None, :] - CX).astype(np.float32)
    return r, t

def frame_groups(tag, names):
    if tag == 'vixen':
        return {n: 'vixen' for n in names}
    return {n: ('sony_A' if int(n[3:8]) <= 6987 else 'sony_B') for n in names}

def load_offsets():
    return json.loads((FIX / 'offset_model.json').read_text())

def marks(colors=('lila', 'blau')):
    j = json.loads(CATALEG_JSON.read_text())
    return [m for m in j['marks'] if m['color'] in colors]


# ---------------------------------------------------------------- flat: ondulació radial
FLAT_CENTRE_YX = {'sony': (2660.0, 4000.0)}     # centre declarat al rebut F0.3 (CENTRE DEL SENSOR)
FLAT_SIGMA_PX = 32.0                            # suavitzat radial del perfil del flat (px del sensor)

def flat_ripple_correction(ctx, tag, sigma=FLAT_SIGMA_PX):
    """Mapa multiplicatiu per subpla CFA que treu l'ondulació fina del flat radial.

    El flat FLAT_RADIAL de la Sony és un model radial (self-calibration del salt de muntura)
    amb una ondulació de ~0,09 % rms a escala de 8–30 px que NO és al sensor: el fotograma
    calibrat (raw/flat) la porta invertida (correlació −0,8, pendent −1,00; A6 d'aquesta ronda).
    Correcció: pl' = pl · exp(P(r) − P_s(r)), amb P el perfil radial del flat (ln, per subpla,
    calaixos d'1 px al voltant del centre del sensor) i P_s el mateix perfil suavitzat amb σ.
    Només toca la part RADIAL del flat a escales < ~3σ; el vinyetatge i qualsevol estructura no
    radial del flat es conserven exactament.
    """
    from scipy.ndimage import gaussian_filter1d
    if tag not in FLAT_CENTRE_YX:
        return None, None
    cy, cx = FLAT_CENTRE_YX[tag]; flat = ctx.flat; h, w = flat.shape
    yy, xx = np.mgrid[:h, :w]; r = np.hypot(xx - cx, yy - cy).astype(np.float32)
    out = {}; rep = {}
    for i in range(4):
        oy, ox = ctx.orig[i]; sub = (slice(oy, None, 2), slice(ox, None, 2))
        rs = r[sub]; fs = flat[sub]; valid = (ctx.valid[sub] > 0) & (fs > 0)
        rb = rs.astype(np.int32); nb = int(rb.max()) + 1
        n = np.bincount(rb[valid], minlength=nb); P = np.bincount(rb[valid], weights=np.log(fs[valid]), minlength=nb) / np.maximum(n, 1)
        good = n > 50
        okp = good.astype(float); Ps = gaussian_filter1d(np.where(good, P, 0), sigma, mode='nearest') / np.maximum(gaussian_filter1d(okp, sigma, mode='nearest'), 1e-9)
        rip = np.where(good, P - Ps, 0.0)
        corr = np.exp(np.interp(rs.ravel(), np.arange(nb), rip)).reshape(rs.shape).astype(np.float32)
        out[i] = corr
        rep[str(i)] = {'ripple_rms_pct_r400_2400': float(100 * np.std(rip[400:2400][good[400:2400]])), 'ripple_max_abs_pct': float(100 * np.max(np.abs(rip[good]))),
                       'corr_p1_p99': [float(np.percentile(corr, 1)), float(np.percentile(corr, 99))]}
    rep['sigma_px'] = sigma; rep['centre_yx'] = [cy, cx]; rep['definicio'] = 'pl·exp(P(r)−P_s(r)); P = perfil radial en ln del flat per subpla; P_s suavitzat gaussià σ'
    return out, rep
