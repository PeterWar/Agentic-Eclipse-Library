"""B4d (V35) · NRGF i RHEF amb anells INCOMPLETS tractats com a funció global (research/148 §1, sense el
suavitzat S/N de la V33): més enllà del primer anell que toca la vora del llenç, mitjana i desviació de
l'anell sencer estimades dels píxels presents amb la forma azimutal dels 40 últims anells sencers; el rang
de la RHEF passa a la CDF empírica d'aquests anells. Mateixa base (base_G_v34) i mateixa LUT de pantalla
que la V32. Escriu purs/cau/P01_NRGF_* i P02_RHEF_* de la V35."""
import os, sys, json
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; PURS = ROOT / 'research/tools/v31_purs'; MINE = HERE / 'purs'; V32P = ROOT / 'research/tools/v32_arcs_20260907/purs'
sys.path = [str(PURS)] + [p for p in sys.path if 'research/tools' not in p]
os.environ['V29_FINAL_GRID'] = '1'
import common as vc
import numpy as np
from scipy.stats import rankdata
vc.C = MINE / 'cau'; vc.OUT = ROOT / 'output/v35_20260908_replica/lliurables/vistes'; vc.D = MINE
CAU35 = HERE / 'cau'
def readbase():
    return np.load(CAU35 / 'base_G_v35.npy', mmap_mode='r'), np.load(CAU35 / 'support_v35.npy')
vc.readbase = readbase
from common import RS, coords, smooth, log
BLEND = 64.0


def radial_v35(a, m, r, t):
    ri = np.floor(r).astype('int32'); nr = int(ri.max()) + 1; ids = ri[m]; v = a[m].astype('float64')
    count = np.bincount(ids, minlength=nr); s = np.bincount(ids, weights=v, minlength=nr); s2 = np.bincount(ids, weights=v * v, minlength=nr)
    mean = np.divide(s, count, out=np.zeros(nr), where=count > 0); std = np.sqrt(np.maximum(0, np.divide(s2, count, out=np.zeros(nr), where=count > 0) - mean * mean))
    good = count > 0; nodes = np.arange(nr) + .5
    comp = count / (2 * np.pi * nodes); ref = np.median(comp[int(3 * RS):int(8 * RS)]); cand = np.flatnonzero((nodes > 3 * RS) & (comp < 0.98 * ref)); r_edge = int(cand[0]) if cand.size else nr
    NB = 720; tb = np.floor((t[m] + np.pi) / (2 * np.pi) * NB).astype('int32') % NB
    ksel = (ids >= r_edge - 40) & (ids < r_edge); z_edge = (v[ksel] - mean[ids[ksel]]) / np.maximum(std[ids[ksel]], 1e-12)
    P = np.bincount(tb[ksel], weights=z_edge, minlength=NB) / np.maximum(np.bincount(tb[ksel], minlength=NB), 1); P = P - P.mean(); varP = float(np.var(P))
    mean_u = mean.copy(); std_u = std.copy(); ok_ring = good.copy()
    for i in range(r_edge, nr):
        k = ids == i
        if k.sum() < 50:
            ok_ring[i] = False; continue
        Pp = P[tb[k]]; mp = float(Pp.mean()); vp = float(np.var(Pp)); sig_full = std[i] / np.sqrt(max(vp + 1 - varP, 0.05)); mean_u[i] = mean[i] - sig_full * mp; std_u[i] = sig_full
    mu = np.interp(r, nodes[ok_ring], mean_u[ok_ring]).astype('float32'); sd = np.interp(r, nodes[ok_ring], std_u[ok_ring]).astype('float32')
    z = np.divide(a - mu, sd, out=np.zeros_like(a), where=sd > 0).astype('float32')
    zs = np.sort(z_edge); Fedge = lambda q: np.searchsorted(zs, q, side='right') / len(zs)
    flat = np.flatnonzero(m); order = np.argsort(ri.ravel()[flat], kind='stable'); flat = flat[order]; counts = np.bincount(ri.ravel()[flat], minlength=nr); cuts = np.r_[0, np.cumsum(counts)]
    rhef = np.zeros_like(a).ravel(); af = a.ravel()
    for i in range(min(r_edge, nr)):
        ix = flat[cuts[i]:cuts[i + 1]]
        if len(ix):
            rhef[ix] = rankdata(af[ix], method='average') / len(ix)
    rhef = rhef.reshape(a.shape); wgt = smooth(nodes, r_edge - BLEND - 32, r_edge - 32); wpix = np.interp(r, nodes, wgt).astype('float32'); outer = wpix > 0
    rhef[outer] = (1 - wpix[outer]) * rhef[outer] + wpix[outer] * Fedge(z[outer]).astype('float32')
    return z, rhef, {'annulus_width_px': 1, 'r_edge_px': r_edge, 'r_edge_R': r_edge / RS, 'blend_px': BLEND, 'completeness_ref': float(ref), 'varP_edge': varP, 'n_z_edge': int(len(zs)), 'count_min': int(count[good].min()), 'count_max': int(count.max())}


def display_of(tag):
    d = json.loads((V32P / 'receipts' / (tag + '.json')).read_text())['display']; return [d['black'], d['white']]


def main():
    a, m = readbase(); a = np.array(a); r, t = coords(); n, h, rep = radial_v35(a, m, r, t); log(f"vora a {rep['r_edge_R']:.2f} R")
    vc.save_output('P01_NRGF', n, m, {**rep, 'paper': 'Morgan, Habbal & Woo 2006', 'V35_edge': 'full-ring mean/std from azimuthal z-shape of last complete rings beyond first canvas edge; no smoothing'}, display=display_of('P01_NRGF')); del n
    vc.save_output('P02_RHEF', h, m, {**rep, 'paper': 'Gilly & Cranmer 2025', 'V35_edge': 'empirical rank inside; F_edge(z) beyond; no smoothing'}, display=[0, 1]); log('B4d fet')


if __name__ == '__main__':
    main()
