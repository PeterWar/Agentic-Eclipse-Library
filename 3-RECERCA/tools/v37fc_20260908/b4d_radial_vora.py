"""B4d (V36) · NRGF i RHEF: (a) anells INCOMPLETS a la vora del llenç com la V34/V35 (la compleció dels anells interiors del forat es va provar i refusar: vegeu `inner = []`);
(b) RHEF amb rang en radi CONTINU: F(B) interpolada entre les CDF empíriques dels dos anells d'1 px veïns segons la posició
subpíxel del radi. Per què (research/153): amb anells d'1 px, prop dels eixos ±x/±y la fase r mod 1 és constant al llarg de
files/columnes senceres i el rang discret hi fa bandes (les tres línies horitzontals de Pere a az 178°). Sense suavitzat; mateixa
base i mateixa LUT de pantalla (receipts V32) que la V35."""
import os, sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; PURS = ROOT / 'research/tools/v31_purs'; MINE = HERE / 'purs'; V32P = ROOT / 'research/tools/v32_arcs_20260907/purs'
sys.path = [str(PURS)] + [p for p in sys.path if 'research/tools' not in p]
os.environ['V29_FINAL_GRID'] = '1'
import common as vc
import numpy as np
vc.C = MINE / 'cau'; vc.OUT = ROOT / 'output/v37fc_20260908/lliurables/vistes'; vc.D = MINE
CAU36 = HERE / 'cau'
def readbase():
    return np.load(CAU36 / 'base_G_v37fc.npy', mmap_mode='r'), np.load(CAU36 / 'support_v37fc.npy')
vc.readbase = readbase
from common import RS, coords, smooth, log
BLEND = 64.0; NB = 720


def ring_stats(v, ids, nr):
    count = np.bincount(ids, minlength=nr); s = np.bincount(ids, weights=v, minlength=nr); s2 = np.bincount(ids, weights=v * v, minlength=nr)
    mean = np.divide(s, count, out=np.zeros(nr), where=count > 0); std = np.sqrt(np.maximum(0, np.divide(s2, count, out=np.zeros(nr), where=count > 0) - mean * mean)); return count, mean, std


def complete_from_partial(mean, std, ids, tb, v, rings, ref_rings):
    """Per als anells `rings` (incomplets), estima mitjana i desviació de l'anell sencer amb la forma azimutal P(θ) dels `ref_rings` (sencers)."""
    ksel = np.isin(ids, ref_rings); z = (v[ksel] - mean[ids[ksel]]) / np.maximum(std[ids[ksel]], 1e-12)
    P = np.bincount(tb[ksel], weights=z, minlength=NB) / np.maximum(np.bincount(tb[ksel], minlength=NB), 1); P = P - P.mean(); varP = float(np.var(P))
    mean_u = mean.copy(); std_u = std.copy(); ok = np.ones(len(mean), bool)
    for i in rings:
        k = ids == i
        if k.sum() < 50:
            ok[i] = False; continue
        Pp = P[tb[k]]; mp = float(Pp.mean()); vp = float(np.var(Pp)); sig_full = std[i] / np.sqrt(max(vp + 1 - varP, 0.05)); mean_u[i] = mean[i] - sig_full * mp; std_u[i] = sig_full
    return mean_u, std_u, ok, P, varP


def radial_v36(a, m, r, t):
    ri = np.floor(r).astype('int32'); nr = int(ri.max()) + 1; ids = ri[m]; v = a[m].astype('float64'); tb = np.floor((t[m] + np.pi) / (2 * np.pi) * NB).astype('int32') % NB
    count, mean, std = ring_stats(v, ids, nr); good = count > 0; nodes = np.arange(nr) + .5
    comp = count / (2 * np.pi * nodes); ref = np.median(comp[int(3 * RS):int(8 * RS)])
    cand_out = np.flatnonzero((nodes > 3 * RS) & (comp < 0.98 * ref)); r_edge = int(cand_out[0]) if cand_out.size else nr
    full_in = np.flatnonzero((comp >= 0.98 * ref) & (nodes > 0.9 * RS)); r_in = int(full_in[0])            # primer anell sencer (≈1,046 R☉)
    inner = []   # ⛔ V36b: la compleció dels anells interiors parcials amb la forma azimutal de 1,046–1,135 es va provar i REFUSAR (la forma azimutal al limbe canvia amb r: prominències; empitjorava 1,003–1,02 de −0,4 a +0,8 σ). Es conserven les estadístiques parcials de la V35.
    outer = list(range(r_edge, nr))
    mean_u, std_u, ok_o, P_o, varP_o = complete_from_partial(mean, std, ids, tb, v, outer, list(range(r_edge - 40, r_edge)))
    mean_u, std_u2, ok_i, P_i, varP_i = complete_from_partial(mean_u, std_u, ids, tb, v, inner, list(range(r_in, r_in + 40)))
    ok_ring = good & ok_o & ok_i
    mu = np.interp(r, nodes[ok_ring], mean_u[ok_ring]).astype('float32'); sd = np.interp(r, nodes[ok_ring], std_u2[ok_ring]).astype('float32')
    z = np.divide(a - mu, sd, out=np.zeros_like(a), where=sd > 0).astype('float32')
    # RHEF: CDF empírica per anell, interpolada en radi continu entre els dos anells veïns (nodes a i + 0,5)
    flat = np.flatnonzero(m); rflat = r.ravel()[flat]; order = np.argsort(ri.ravel()[flat], kind='stable'); flat_o = flat[order]
    counts = np.bincount(ri.ravel()[flat_o], minlength=nr); cuts = np.r_[0, np.cumsum(counts)]; af = a.ravel()
    sorted_rings = [np.sort(af[flat_o[cuts[i]:cuts[i + 1]]]) for i in range(nr)]
    def F(i, vals):
        s = sorted_rings[i]
        if len(s) == 0:
            return np.full(vals.shape, np.nan, 'float32')
        return (np.searchsorted(s, vals, side='left') + np.searchsorted(s, vals, side='right')).astype('float32') / (2.0 * len(s))
    rhef = np.zeros_like(a).ravel(); vals = af[flat]; i0 = np.clip(np.floor(rflat - 0.5).astype('int32'), 0, nr - 1); i1 = np.clip(i0 + 1, 0, nr - 1); al = np.clip(rflat - (i0 + 0.5), 0, 1).astype('float32')
    out = np.empty(len(flat), 'float32')
    for i in range(nr):
        k = np.flatnonzero(i0 == i)
        if not k.size:
            continue
        f0 = F(i, vals[k]); f1 = F(min(i + 1, nr - 1), vals[k]); f1 = np.where(np.isfinite(f1), f1, f0); f0 = np.where(np.isfinite(f0), f0, f1)
        out[k] = (1 - al[k]) * f0 + al[k] * f1
    rhef[flat] = out; rhef = rhef.reshape(a.shape)
    # més enllà de la vora del llenç: F_edge(z) com a la V34/V35
    ksel = np.isin(ids, list(range(r_edge - 40, r_edge))); z_edge = (v[ksel] - mean[ids[ksel]]) / np.maximum(std[ids[ksel]], 1e-12); zs = np.sort(z_edge); Fedge = lambda q: np.searchsorted(zs, q, side='right') / len(zs)
    wgt = smooth(nodes, r_edge - BLEND - 32, r_edge - 32); wpix = np.interp(r, nodes, wgt).astype('float32'); outer_px = wpix > 0
    rhef[outer_px] = (1 - wpix[outer_px]) * rhef[outer_px] + wpix[outer_px] * Fedge(z[outer_px]).astype('float32')
    # dins del forat parcial (anells incomplets interiors): rang contra la CDF de l'anell sencer estimat: z → Φ amb la forma dels anells interiors sencers
    ksel_i = np.isin(ids, list(range(r_in, r_in + 40))); z_in = (v[ksel_i] - mean[ids[ksel_i]]) / np.maximum(std[ids[ksel_i]], 1e-12); zsi = np.sort(z_in); Fin = lambda q: np.searchsorted(zsi, q, side='right') / len(zsi)
    inner_px = m & (r < r_in)
    # (V36b) sense compleció interior: el rang dins dels anells parcials és el continu de dalt; Fin no s'aplica
    # rhef[inner_px] = Fin(z[inner_px]).astype('float32')
    return z, rhef, {'annulus_width_px': 1, 'r_edge_px': r_edge, 'r_edge_R': r_edge / RS, 'r_in_px': r_in, 'r_in_R': r_in / RS, 'blend_px': BLEND, 'completeness_ref': float(ref), 'varP_edge': varP_o, 'varP_in': varP_i, 'n_inner_partial_rings': len(inner), 'count_min': int(count[good].min()), 'count_max': int(count.max()), 'rhef_rank': 'continuous radius: CDFs of the two neighbouring 1-px rings interpolated by the sub-pixel radial position'}


def display_of(tag):
    d = json.loads((V32P / 'receipts' / (tag + '.json')).read_text())['display']; return [d['black'], d['white']]


def main():
    a, m = readbase(); a = np.array(a); r, t = coords(); n, h, rep = radial_v36(a, m, r, t); log(f"vora del llenç a {rep['r_edge_R']:.2f} R · primer anell sencer a {rep['r_in_R']:.3f} R ({rep['n_inner_partial_rings']} anells parcials interiors)")
    vc.save_output('P01_NRGF', n, m, {**rep, 'paper': 'Morgan, Habbal & Woo 2006', 'V36': 'full-ring mean/std for incomplete rings at BOTH ends (canvas edge and lunar hole) from the azimuthal z-shape of neighbouring complete rings; no smoothing'}, display=display_of('P01_NRGF')); del n
    vc.save_output('P02_RHEF', h, m, {**rep, 'paper': 'Gilly & Cranmer 2025', 'V36': 'continuous-radius rank (interpolated ring CDFs); F_edge(z) beyond canvas edge; F_in(z) inside partial inner rings; no smoothing'}, display=[0, 1]); log('B4d fet')


if __name__ == '__main__':
    main()
