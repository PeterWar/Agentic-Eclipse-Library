# ⛔ NO ADOPTAT (A8): farcit separable + dues màscares; a la ROI empitjora el biaix d'anell i el graó a la vora del forat respecte del farcit V35 (vegeu A8_roi_farcit.json). Es conserva com a prova.
"""B4c (V36) · P03 MGN, P04 WOW, P05 WOW bilateral amb la condició de contorn SEPARABLE i la normalització sobre el suport real.
Entrada de l'operador (mai al producte): a on hi ha suport; fora (forat lunar i fora del llenç de dades):
  exp( P(r) + A(θ) ), amb P(r) = perfil azimutal mitjà de ln B (anells d'1 px; a partir de l'últim anell amb dada cap endins,
  continuació amb el pendent dels 20 primers anells sencers que DECAU exp(−d/L), L = 100 px, i més enllà de l'últim anell l'últim valor)
  i A(θ) = modulació azimutal (ln B − P(r)) mesurada a 1,05–1,15 R☉, suavitzada 3° (només dins del forat; fora del llenç A = 0).
Per què (research/153): el farcit de la V35 era el perfil MITJÀ (a les corones brillants quedava un 30–50 % fosc → graó a la vora del
forat → anell fi a 1,04–1,06 al MGN/WOW) i creixia exponencialment fins al centre (×29.000: còpies de l'à trous a ±2^s).
Els operadors són els de v31_purs amb DUES màscares: la mitjana veu el farcit; la variància (MGN) i la potència (WOW) es normalitzen
només amb píxels reals (el farcit no té gra: si entrés a la variància, el σ local cauria a la vora i z s'inflaria).
LUT de pantalla: la de la V34 (receipts), com la V35."""
import os, sys, json, time, ctypes, gc
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; PURS = ROOT / 'research/tools/v31_purs'; MINE = HERE / 'purs'; V34P = ROOT / 'research/tools/v34_20260907/purs'
for p in (MINE / 'receipts', MINE / 'cau'):
    p.mkdir(parents=True, exist_ok=True)
sys.path = [str(PURS)] + [p for p in sys.path if 'research/tools' not in p]
os.environ['V29_FINAL_GRID'] = '1'
import common as vc
import numpy as np
import numexpr as ne
vc.C = MINE / 'cau'; vc.OUT = ROOT / 'output/v36_20260908/lliurables/vistes'; vc.D = MINE
CAU36 = HERE / 'cau'; REB36 = ROOT / 'output/v36_20260908/4-rebuts'
def readbase():
    return np.load(CAU36 / 'base_G_v36.npy', mmap_mode='r'), np.load(CAU36 / 'support_v36.npy')
vc.readbase = readbase
for fn in ('nafe_native.dylib', 'sparse_conv.dylib', 'sources/nafe_published.py'):
    assert (MINE / fn).read_bytes() == (PURS / fn).read_bytes(), fn
import wow_filters, local_filters
from common import RS, CX, CY, coords, log, savejson, ng
from wow_filters import K, conv, nconv, bilateral_conv
L_PX = 100.0; AZ_RINGS = (1.05, 1.15); AZ_SIGMA_DEG = 3.0


def display_of(tag):
    d = json.loads((V34P / 'receipts' / (tag + '.json')).read_text())['display']; return [d['black'], d['white']]


def farcit_separable(a, m, r, t):
    """Entrada de l'operador: a on hi ha suport; exp(P(r) + A(θ)) fora. Retorna (entrada, rebut)."""
    ri = np.round(r).astype('int32'); L = np.where(m, np.log(np.maximum(a, 1e-9)), 0).astype('float64')
    n = np.bincount(ri[m]); s = np.bincount(ri[m], weights=L[m]); prof = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    nodes = np.arange(len(n)); full = np.flatnonzero(n >= 0.999 * 2 * np.pi * np.maximum(nodes, 1)); first_full = int(full[full > 0.9 * RS][0])
    k = np.arange(first_full, first_full + 20); slope = float(np.polyfit(k, prof[k], 1)[0])
    has = np.flatnonzero(n > 0); first_data = int(has[has > 0.5 * RS][0])           # primer anell amb alguna dada (vora del forat, ~1,005 R☉)
    p = prof.copy()
    # anells parcials (first_data … first_full): la mitjana dels presents és esbiaixada per la modulació azimutal: hi posem la recta dels sencers
    kk = np.arange(first_data, first_full); p[kk] = prof[first_full] + slope * (kk - first_full)
    d = np.arange(first_data) - first_data                              # d ≤ 0 cap endins
    p[:first_data] = p[first_data] - slope * L_PX * (1.0 - np.exp(d / L_PX))   # pendent (negatiu cap enfora) que decau cap endins: pujada màxima |slope|·L
    last = int(np.flatnonzero(np.isfinite(p))[-1]); p[last + 1:] = p[last]; bad = ~np.isfinite(p); p[bad] = np.interp(nodes[bad], nodes[~bad], p[~bad])
    radial = np.interp(r, nodes, p).astype(np.float32)
    # modulació azimutal a AZ_RINGS, suavitzada
    NB = 720; tb = np.floor((t + np.pi) / (2 * np.pi) * NB).astype('int32') % NB; band = m & (r >= AZ_RINGS[0] * RS) & (r < AZ_RINGS[1] * RS)
    res = (L - radial.astype('float64'))[band]; A = np.bincount(tb[band], weights=res, minlength=NB) / np.maximum(np.bincount(tb[band], minlength=NB), 1)
    sg = AZ_SIGMA_DEG / 360 * NB; x = np.arange(-int(3 * sg), int(3 * sg) + 1); g = np.exp(-0.5 * (x / sg) ** 2); g /= g.sum()
    A = np.convolve(np.r_[A[-len(x):], A, A[:len(x)]], g, mode='same')[len(x):-len(x)]; A -= A.mean()
    az = np.where(r < first_full, A[tb], 0.0).astype(np.float32)                # només dins del forat; fora del llenç A = 0
    ent = np.where(m, a, np.exp(radial + az)).astype(np.float32)
    return ent, {'primer_anell_amb_dada_px': first_data, 'primer_anell_sencer_px': first_full, 'pendent_ln_per_px': slope, 'L_px': L_PX, 'pujada_max_centre_ln': -slope * L_PX,
                 'A_theta_p05_p95': [float(np.percentile(A, 5)), float(np.percentile(A, 95))], 'anells_az': AZ_RINGS, 'sigma_az_deg': AZ_SIGMA_DEG, 'ultim_anell_amb_dada_px': last, 'px_farcits': int((~m).sum())}


def mgn2(a, m_conv, m_real, sigmas=(1.25, 2.5, 5, 10, 20, 40), k=.7, h=.7, gamma=3.2, limits=None):
    """local_filters.mgn amb dues màscares: mitjana amb m_conv (farcit), variància amb m_real."""
    lo, hi = limits; detail = np.zeros_like(a, dtype='float32')
    for s in sigmas:
        mu = ng(a, m_conv, s); d = a - mu
        d[np.abs(d) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(a), np.abs(mu))] = 0
        den = np.sqrt(ng(d * d, m_real, s)); z = np.divide(d, den, out=np.zeros_like(d), where=den > 0)
        detail += np.arctan(k * z) / len(sigmas); log('MGN sigma ' + str(s))
    global_term = np.clip((a - lo) / (hi - lo), 0, 1) ** (1 / gamma)
    return h * global_term + (1 - h) * detail


def wow2(a, m_conv, m_real, n_scales=10, bilateral=False):
    """wow_filters.wow amb dues màscares: suavitzat à trous amb m_conv (farcit), potència amb m_real; pla gros normalitzat sobre m_real."""
    c = np.where(m_conv, a, 0).astype('float32'); out = np.zeros_like(c)
    for s in range(n_scales):
        nxt = bilateral_conv(c, m_conv, s) if bilateral else nconv(c, m_conv, s)
        wave = c - nxt
        wave[np.abs(wave) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(c), np.abs(nxt))] = 0
        power = nconv(wave * wave, m_real, s); amp = np.sqrt(np.maximum(power, 1e-20))
        out += wave / amp; c = np.where(m_conv, nxt, 0)
        log(('WOW bilateral ' if bilateral else 'WOW ') + 'scale ' + str(s)); del wave, power, amp; gc.collect()
    sd = float(np.std(c[m_real], dtype='float64'))
    if sd > 16 * np.finfo('float32').eps * float(np.max(np.abs(c[m_real]))):
        out += c / sd
    return out


def ring_bias(out, m, r):
    sd = float(np.nanstd(out[m & (r > 1.05 * RS) & (r < 1.6 * RS)])); rs = np.arange(0.98, 1.6, 0.01); med = []
    for a0 in rs:
        k = m & (r >= a0 * RS) & (r < (a0 + 0.01) * RS); med.append(float(np.median(out[k])) / sd if k.sum() > 50 else np.nan)
    z = np.array(med); zz = z - np.nanmedian(z[rs > 1.3]); return {'r': rs.round(2).tolist(), 'mediana_sobre_sigma': [None if not np.isfinite(v) else float(v) for v in z], 'max_abs_1.03_1.3_rel_1.3plus': float(np.nanmax(np.abs(zz[(rs >= 1.03) & (rs < 1.3)])))}


def main():
    which = sys.argv[1:] or ['mgn', 'wow']
    a, m = readbase(); a = np.array(a, np.float32); r, t = coords(); assert a.shape == (vc.H, vc.W)
    ent, frep = farcit_separable(a, m, r, t); full = np.ones_like(m); log(f'farcit: {frep}')
    np.save(CAU36 / 'entrada_operadors_farcida_v36.npy', ent)
    from PIL import Image
    y0, y1, x0, x1 = int(CY - 2 * RS), int(CY + 2 * RS), int(CX - 2 * RS), int(CX + 2 * RS); crop = np.log(np.maximum(ent[y0:y1, x0:x1], 1)); lo, hi = np.percentile(crop, [1, 99.5])
    Image.fromarray(np.uint8(np.clip((crop - lo) / (hi - lo), 0, 1) * 255)).save(vc.OUT / 'B4c_entrada_farcida_ln_2R.png')
    bound = {'boundary': 'operator input = base on support, exp(P(r)+A(theta)) elsewhere (radial profile with decaying slope L=100 px x azimuthal modulation at 1.05-1.15 R); mean with filled support, variance/power with REAL support only; output saved on physical support', 'farcit': frep, 'display': 'V34 receipts LUT'}
    if 'mgn' in which:
        a_mgn = np.maximum(a, 0); limits = [float(a_mgn[m].min()), float(a_mgn[m].max())]
        out = mgn2(np.maximum(ent, 0), full, m, limits=limits); out = np.where(m, out, np.nan); rb = ring_bias(out, m, r)
        vc.save_output('P03_MGN', out, m, {'paper': 'Morgan & Druckmuller 2014, equations1-5', 'sigma_px': [1.25, 2.5, 5, 10, 20, 40], 'k': .7, 'h': .7, 'gamma': 3.2, 'weights': [1] * 6, 'input_limits': limits, **bound, 'ring_bias_limb_1.03_1.3': rb['max_abs_1.03_1.3_rel_1.3plus']}, display=display_of('P03_MGN'))
        log(f"P03 biaix d'anell 1,03–1,3: {rb['max_abs_1.03_1.3_rel_1.3plus']:.2f} σ"); del out
    if 'wow' in which:
        scales = int(np.round(np.log2(min(a.shape)) - np.log2(5)))
        for bilateral, tag in [(False, 'P04_WOW'), (True, 'P05_WOW_bilateral')]:
            out = wow2(ent, full, m, scales, bilateral); out = np.where(m, out, np.nan); rb = ring_bias(out, m, r)
            vc.save_output(tag, out, m, {'paper': 'Auchere et al. 2023 A&A670 A66 equations4-9,16-18', 'author_reference': 'watroo', 'scales': scales, 'B3_kernel_1d': K.tolist(), 'weights': 'all1', 'h': 0, 'denoise': False, 'bilateral': 1 if bilateral else None, **bound, 'ring_bias_limb_1.03_1.3': rb['max_abs_1.03_1.3_rel_1.3plus']}, display=display_of(tag))
            log(f"{tag} biaix d'anell 1,03–1,3: {rb['max_abs_1.03_1.3_rel_1.3plus']:.2f} σ"); del out
    savejson(REB36 / 'B4c_purs.json', {'farcit': frep, 'canvis': bound}); log('B4c fet')


if __name__ == '__main__':
    main()
