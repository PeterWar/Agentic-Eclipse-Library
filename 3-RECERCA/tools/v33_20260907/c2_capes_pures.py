"""C2 · Les cinc vistes pures marcades (NRGF, RHEF, MGN, WOW, WOW bilateral) sobre base_G_v32,
amb el codi de v31_purs importat tal qual (com b4c de la V32) i DOS canvis declarats:
  1. NRGF/RHEF: més enllà de la primera vora del llenç (l'anell deixa de ser sencer), mitjana i
     desviació de l'anell SENCER s'estimen dels píxels presents amb la forma azimutal dels últims
     40 anells sencers (funció global, idea de la tesi §6), i el rang de la RHEF passa a la CDF
     empírica de la vora (contínua amb el rang empíric). Cap retall, cap radi d'exclusió.
  2. A totes cinc, el resultat float passa per f3.suavitza_sn (t 0,18, σ ≤ 24): on només hi ha
     gra, la resolució baixa. La LUT de pantalla és la mateixa de la V32 (negre/blanc del rebut).
"""
import os, sys, json, gc
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; PURS = ROOT / 'research/tools/v31_purs'; MINE = HERE / 'purs'
V32P = ROOT / 'research/tools/v32_arcs_20260907/purs'
sys.path = [str(PURS)] + [p for p in sys.path if 'research/tools' not in p]
os.environ['V29_FINAL_GRID'] = '1'
import common as vc
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.special import ndtr
from scipy.stats import rankdata
vc.C = MINE / 'cau'; vc.OUT = ROOT / 'output/v33_20260907/lliurables/vistes'; vc.D = MINE
C32 = ROOT / 'research/tools/v32_arcs_20260907/cau'
def readbase():
    return np.load(C32 / 'base_G_v32.npy', mmap_mode='r'), np.load(C32 / 'support_v32.npy')
vc.readbase = readbase
import radial_filters, local_filters, wow_filters
for mod in (radial_filters, local_filters, wow_filters):
    assert mod.C == vc.C and mod.readbase is readbase
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(ROOT / 'research/tools/eclipse_determinista')); sys.path.insert(0, str(ROOT / 'research/tools/v32_arcs_20260907')); sys.path.insert(0, str(ROOT / 'research/tools/v29'))
import f3
from snmap import sn_v33
from common import RS, CX, CY, H, W, log, savejson, coords, smooth
T_SN, SMAX, SIG_R, BLEND = 0.18, 32.0, 32.0, 64.0
REB = ROOT / 'output/v33_20260907/4-rebuts'


def display_of(tag):
    d = json.loads((V32P / 'receipts' / (tag + '.json')).read_text())['display']; return [d['black'], d['white']]


def radial_v33(a, m, r, t):
    """NRGF/RHEF amb anells INCOMPLETS tractats com a funció global (idea de la tesi §6):
    · anells sencers (r < r_edge): mitjana, desviació i rang empíric per anell, com el codi publicat;
    · anells incomplets: forma azimutal z-normalitzada P(θ) dels 40 últims anells sencers; mitjana i
      desviació de l'anell sencer estimades a partir dels píxels presents (μ_full = μ_p − σ·mean_p P;
      σ_full² = σ_p²/(var_p P + 1 − var_all P)); rang = CDF empírica de z dels últims anells sencers
      (F_edge), contínua amb el rang empíric a r_edge; barreja de 64 px."""
    ri = np.floor(r).astype('int32'); nr = int(ri.max()) + 1; ids = ri[m]; v = a[m].astype('float64')
    count = np.bincount(ids, minlength=nr); s = np.bincount(ids, weights=v, minlength=nr); s2 = np.bincount(ids, weights=v * v, minlength=nr)
    mean = np.divide(s, count, out=np.zeros(nr), where=count > 0); std = np.sqrt(np.maximum(0, np.divide(s2, count, out=np.zeros(nr), where=count > 0) - mean * mean))
    good = count > 0; nodes = np.arange(nr) + .5
    comp = count / (2 * np.pi * nodes); ref = np.median(comp[int(3 * RS):int(8 * RS)]); cand = np.flatnonzero((nodes > 3 * RS) & (comp < 0.98 * ref)); r_edge = int(cand[0]) if cand.size else nr
    # forma azimutal dels últims 40 anells sencers
    NB = 720; tb = np.floor((t[m] + np.pi) / (2 * np.pi) * NB).astype('int32') % NB
    ksel = (ids >= r_edge - 40) & (ids < r_edge); z_edge = (v[ksel] - mean[ids[ksel]]) / np.maximum(std[ids[ksel]], 1e-12)
    P = np.bincount(tb[ksel], weights=z_edge, minlength=NB) / np.maximum(np.bincount(tb[ksel], minlength=NB), 1); P = P - P.mean(); varP = float(np.var(P))
    Pf = np.load if False else P  # (llegibilitat)
    mean_u = mean.copy(); std_u = std.copy(); ok_ring = good.copy()
    for i in range(r_edge, nr):
        k = ids == i
        if k.sum() < 50:
            ok_ring[i] = False; continue
        Pp = P[tb[k]]; mp = float(Pp.mean()); vp = float(np.var(Pp))
        sig_full = std[i] / np.sqrt(max(vp + 1 - varP, 0.05)); mean_u[i] = mean[i] - sig_full * mp; std_u[i] = sig_full
    # barreja contínua 64 px cap endins de r_edge (els dos estimadors coincideixen a r_edge per construcció)
    mu = np.interp(r, nodes[ok_ring], mean_u[ok_ring]).astype('float32'); sd = np.interp(r, nodes[ok_ring], std_u[ok_ring]).astype('float32')
    z = np.divide(a - mu, sd, out=np.zeros_like(a), where=sd > 0).astype('float32'); nrgf = z
    # RHEF: rang empíric dins; F_edge(z) fora
    zs = np.sort(z_edge); Fedge = lambda q: np.searchsorted(zs, q, side='right') / len(zs)
    flat = np.flatnonzero(m); order = np.argsort(ri.ravel()[flat], kind='stable'); flat = flat[order]
    counts = np.bincount(ri.ravel()[flat], minlength=nr); cuts = np.r_[0, np.cumsum(counts)]
    rhef = np.zeros_like(a).ravel(); af = a.ravel()
    for i in range(min(r_edge, nr)):
        ix = flat[cuts[i]:cuts[i + 1]]
        if len(ix):
            rhef[ix] = rankdata(af[ix], method='average') / len(ix)
    rhef = rhef.reshape(a.shape); wgt = smooth(nodes, r_edge - BLEND - 32, r_edge - 32); wpix = np.interp(r, nodes, wgt).astype('float32')
    outer = wpix > 0
    rhef[outer] = (1 - wpix[outer]) * rhef[outer] + wpix[outer] * Fedge(z[outer]).astype('float32')
    return nrgf, rhef, {'annulus_width_px': 1, 'r_edge_px': r_edge, 'r_edge_R': r_edge / RS, 'blend_px': BLEND, 'completeness_ref': float(ref), 'varP_edge': varP, 'n_z_edge': int(len(zs)), 'count_min': int(count[good].min()), 'count_max': int(count.max())}


def post(tag, out, m, params, display):
    r_, _ = coords(); sm, sig = sn_v33(np.where(m, out, 0).astype(np.float32), m)
    np.save(MINE / 'cau' / (tag + '_sigma.npy'), sig.astype(np.float16))
    prof = []
    for a in (1.5, 2.0, 2.65, 3.0, 4.0, 5.0, 6.0, 8.0, 10.0):
        k = m & (r_ >= a * RS) & (r_ < (a + 0.3) * RS); prof.append({'r': a, 'sigma_p50': float(np.median(sig[k])) if k.sum() > 100 else None, 'frac_smax': float(np.mean(sig[k] >= SMAX - 1e-3)) if k.sum() > 100 else None})
    rep = vc.save_output(tag, sm, m, {**params, 'V33_post': f'snmap.sn_v33 (σ = max(mapa C0 λ_min/8, f3.suavitza_sn t={T_SN}), smax={SMAX}) sobre el float', 'perfil_sigma': prof, 'display_from': 'V32 receipt'}, display=display)
    return rep


def main():
    which = sys.argv[1:] or ['radial', 'local', 'wow']
    a, m = readbase(); a = np.array(a); r, _ = coords(); reps = {}
    if 'radial' in which:
        n, h, rep = radial_v33(a, m, r, coords()[1]); log(f"NRGF/RHEF v33: vora a {rep['r_edge_R']:.2f} R")
        reps['P01_NRGF'] = post('P01_NRGF', n, m, {**rep, 'paper': 'Morgan, Habbal & Woo 2006', 'V33_edge': 'incomplete rings: full-ring mean/std estimated from the azimuthal z-shape of the last complete rings'}, display_of('P01_NRGF')); del n
        reps['P02_RHEF'] = post('P02_RHEF', h, m, {**rep, 'paper': 'Gilly & Cranmer 2025', 'V33_edge': 'empirical rank inside; F_edge(z) (empirical CDF of the last complete rings) beyond first canvas edge'}, [0, 1]); del h; gc.collect()
    if 'local' in which:
        a_mgn = np.maximum(a, 0); limits = [float(a_mgn[m].min()), float(a_mgn[m].max())]
        out = local_filters.mgn(a_mgn, m, limits=limits)
        reps['P03_MGN'] = post('P03_MGN', out, m, {'paper': 'Morgan & Druckmuller 2014', 'sigma_px': [1.25, 2.5, 5, 10, 20, 40], 'k': .7, 'h': .7, 'gamma': 3.2}, display_of('P03_MGN')); del out, a_mgn; gc.collect()
    if 'wow' in which:
        scales = int(np.round(np.log2(min(a.shape)) - np.log2(5)))
        for bilateral, tag in [(False, 'P04_WOW'), (True, 'P05_WOW_bilateral')]:
            out = wow_filters.wow(a, m, scales, bilateral)
            reps[tag] = post(tag, out, m, {'paper': 'Auchere et al. 2023', 'scales': scales, 'bilateral': bilateral, 'denoise': False}, display_of(tag)); del out; gc.collect()
    old = json.loads((REB / 'C2_capes_pures.json').read_text()) if (REB / 'C2_capes_pures.json').exists() else {}
    old.update(reps); savejson(REB / 'C2_capes_pures.json', old); log('C2 fet')


if __name__ == '__main__':
    main()
