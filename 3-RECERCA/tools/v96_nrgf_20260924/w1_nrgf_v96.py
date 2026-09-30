"""w1 (V96) · P01 NRGF al llenç sencer: el de la V88 (E1, radial_v36, només dada) amb els ANELLS INTERIORS PARCIALS completats pel mateix mètode que la V36
ja fa servir als anells exteriors (complete_from_partial, patró azimutal P dels 40 anells complets de sobre). Sense cap farcit de píxels, ni a4v, ni a5d:
on no hi ha dada, alfa 0 (la mateixa alfa de domini de la WOW V94/V95). Lluny de la Lluna (r ≥ r_in = 469 px del Sol) és la V88 idèntica (es comprova).
Per què: sota r_in la Lluna tapa la part dreta de cada anell del Sol; l'estadística de l'arc visible està esbiaixada i a r_in canvia de règim → un cercle
centrat al SOL a r ≈ 469 (a d ≈ 16 a dalt i a baix) i una franja clara entre el limbe i aquest cercle (les marques de Pere a Artefactes_V95, capa 277).
Sortida: 4-RESULTATS/v96_nrgf_20260924/P01_NRGF_u16.npy, _alfa_u16.npy, _float.npy i W1_NRGF.json."""
import sys, json, time, hashlib
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v96_nrgf_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v86_neta_20260923')); from v86_operadors import ring_stats, complete_from_partial, NB
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
H, W = 7506, 10551; CX, CY, RS = 5361.768111973117, 3775.747534140857, 440.60304883027544
FONTS = ARREL / '4-RESULTATS/v85_regeneracio_20260922/d4_baseline/products/sources'; V88 = ARREL / '4-RESULTATS/v88_20260923'
Q = np.load(V88 / 'A3A_franja_un_instant.npz'); qy0, qy1, qx0, qx1 = [int(v) for v in Q['box']]
a = np.load(FONTS / 'base_G.npy').astype(np.float32); m = np.load(FONTS / 'support.npy') & np.isfinite(a) & (a > 0)
a[qy0:qy1, qx0:qx1] = Q['G']; m[qy0:qy1, qx0:qx1] = Q['domini'] & (Q['G'] > 0); a = np.nan_to_num(a); log(f'domini {m.sum()} px')
y, x = np.ogrid[:H, :W]; r = np.hypot(y - CY, x - CX).astype(np.float32); t = np.arctan2(y - CY, x - CX).astype(np.float32)
ri = np.floor(r).astype('int32'); nr = int(ri.max()) + 1; ids = ri[m]; v = a[m].astype('float64'); tb = np.floor((t[m] + np.pi) / (2 * np.pi) * NB).astype('int32') % NB
count, mean, std = ring_stats(v, ids, nr); good = count > 0; nodes = np.arange(nr) + .5
comp = count / (2 * np.pi * nodes); ref = np.median(comp[int(3 * RS):int(8 * RS)])
cand_out = np.flatnonzero((nodes > 3 * RS) & (comp < 0.98 * ref)); r_edge = int(cand_out[0]) if cand_out.size else nr
full_in = np.flatnonzero((comp >= 0.98 * ref) & (nodes > 0.9 * RS)); r_in = int(full_in[0])
inner = [i for i in range(r_in) if count[i] > 0]; outer = list(range(r_edge, nr)); log(f'r_in {r_in} · r_edge {r_edge} · anells interiors parcials {len(inner)} ({inner[0]}–{inner[-1]})')
mean_u, std_u, ok_o, _, _ = complete_from_partial(mean, std, ids, tb, v, outer, list(range(r_edge - 40, r_edge)))
mean_u, std_u2, ok_i, _, _ = complete_from_partial(mean_u, std_u, ids, tb, v, inner, list(range(r_in, r_in + 40)))
ok_ring = good & ok_o & ok_i
mu = np.interp(r, nodes[ok_ring], mean_u[ok_ring]).astype('float32'); sd = np.interp(r, nodes[ok_ring], std_u2[ok_ring]).astype('float32')
z = np.divide(a - mu, sd, out=np.zeros_like(a), where=sd > 0).astype('float32'); del mu, sd
z88 = np.load(V88 / 'filtres/P01_NRGF_float.npy', mmap_mode='r'); lluny = m & (r >= r_in + 0.5)   # a r_in..r_in+0,5 la interpolació ja usa el node r_in−0,5 (anell completat)
dif_lluny = float(np.max(np.abs(z[lluny] - z88[lluny]))); dif_dins = float(np.max(np.abs(z[m & (r < r_in)] - z88[m & (r < r_in)]))); log(f'|z − z_V88|: r ≥ r_in {dif_lluny:.2e} · r < r_in {dif_dins:.3f}')
assert dif_lluny < 1e-5, 'lluny de la Lluna ha de ser la V88'
lo, hi = -2.3811454010009765, 3.09986613345147
u = np.round(np.clip((z - lo) / (hi - lo), 0, 1) * 65535).astype(np.uint16); u[~m] = 32768; np.save(SORT / 'P01_NRGF_u16.npy', u); np.save(SORT / 'P01_NRGF_float.npy', np.where(m, z, np.nan).astype(np.float32))
al94 = np.load(ARREL / '4-RESULTATS/v94_20260924/wow/P05_WOW_bilateral_alfa_w1.npy', mmap_mode='r'); assert np.array_equal(np.asarray(al94) > 32767, m), 'domini diferent del de la V94'
al = np.load(ARREL / '4-RESULTATS/v94_20260924/wow/P05_WOW_bilateral_alfa_u16.npy'); np.save(SORT / 'P01_NRGF_alfa_u16.npy', al)
rep = dict(r_in=r_in, r_edge=r_edge, anells_interiors_completats=len(inner), display=[lo, hi], dif_z_V88_lluny=dif_lluny, dif_z_V88_dins_r_in=dif_dins,
           sha256=sha(SORT / 'P01_NRGF_u16.npy'), alfa='domini de dada (la de la WOW V94/V95, fosa d 1,5 px a la vora)')
(SORT / 'W1_NRGF.json').write_text(json.dumps(rep, ensure_ascii=False, indent=2) + '\n'); log('W1 fet')
