"""B4c (V35) · P03 MGN, P04 WOW i P05 WOW bilateral amb el MATEIX CODI de v31_purs (importat tal qual) i UNA
condició de contorn declarada per als operadors isotròpics: l'entrada de l'operador és la base G amb el forat
lunar i el fora-de-suport OMPLERTS pel perfil azimutal mitjà (ln) de la pròpia imatge (anells d'1 px; dins del
forat, continuació lineal en ln amb el pendent dels 20 primers anells sencers; més enllà de l'últim anell,
l'últim valor). El producte es desa NOMÉS al suport físic (com sempre): cap píxel del farcit hi entra.
Per què (research/151, A2): amb el forat com a suport absent, la mitjana local d'un sol costat contra un
gradient de ×2 cada 44 px fa anells clars al limbe (biaix 4–5 σ a 1,0–1,3 R☉ al MGN i als dos WOW) i
l'à trous dispers del WOW hi dibuixa rectangles a ±2^s px del Sol; amb el farcit el biaix cau a ≤ 1 σ.
LUT de pantalla: la de la V34 (receipts), perquè les capes es puguin comparar 1:1."""
import os, sys, json, time
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]; PURS = ROOT / 'research/tools/v31_purs'; MINE = HERE / 'purs'; V34P = ROOT / 'research/tools/v34_20260907/purs'
for p in (MINE / 'receipts', MINE / 'cau'):
    p.mkdir(parents=True, exist_ok=True)
sys.path = [str(PURS)] + [p for p in sys.path if 'research/tools' not in p]
os.environ['V29_FINAL_GRID'] = '1'
import common as vc
import numpy as np
vc.C = MINE / 'cau'; vc.OUT = ROOT / 'output/v35_20260908_replica/lliurables/vistes'; vc.D = MINE
CAU35 = HERE / 'cau'; REB35 = ROOT / 'output/v35_20260908_replica/4-rebuts'
def readbase():
    return np.load(CAU35 / 'base_G_v35.npy', mmap_mode='r'), np.load(CAU35 / 'support_v35.npy')
vc.readbase = readbase
for fn in ('nafe_native.dylib', 'sparse_conv.dylib', 'sources/nafe_published.py'):
    assert (MINE / fn).read_bytes() == (PURS / fn).read_bytes(), fn
import wow_filters, local_filters
for mod in (wow_filters, local_filters):
    assert mod.C == vc.C and mod.readbase is readbase and mod.D == vc.D, mod.__name__
from common import RS, CX, CY, coords, log, savejson
from wow_filters import wow, K
from local_filters import mgn


def display_of(tag):
    d = json.loads((V34P / 'receipts' / (tag + '.json')).read_text())['display']; return [d['black'], d['white']]


def farcit_perfil(a, m, r):
    """Entrada de l'operador: a on hi ha suport; fora, exp(perfil azimutal mitjà de ln a). Retorna (entrada, rebut)."""
    ri = np.round(r).astype('int32'); L = np.where(m, np.log(np.maximum(a, 1e-9)), 0).astype('float64')
    n = np.bincount(ri[m]); s = np.bincount(ri[m], weights=L[m]); prof = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    nodes = np.arange(len(n)); full = np.flatnonzero(n >= 0.999 * 2 * np.pi * np.maximum(nodes, 1)); first = int(full[full > 0.9 * RS][0])
    k = np.arange(first, first + 20); slope = float(np.polyfit(k, prof[k], 1)[0])
    p = prof.copy(); p[:first] = prof[first] + slope * (np.arange(first) - first)
    last = int(np.flatnonzero(np.isfinite(p))[-1]); p[last + 1:] = p[last]; bad = ~np.isfinite(p); p[bad] = np.interp(nodes[bad], nodes[~bad], p[~bad])
    radial = np.interp(r, nodes, p).astype(np.float32); ent = np.where(m, a, np.exp(radial)).astype(np.float32)
    return ent, {'primer_anell_sencer_px': first, 'primer_anell_sencer_R': first / RS, 'pendent_ln_per_px_dins': slope, 'ultim_anell_amb_dada_px': last, 'anells_incomplets_usats': 'mitjana dels píxels presents', 'px_farcits': int((~m).sum())}


def ring_bias(out, m, r):
    """Mediana per anell (0,98–1,6 R☉, 0,01) dividida per σ a 1,05–1,6: un anell coherent és biaix, no detall."""
    sd = float(np.nanstd(out[m & (r > 1.05 * RS) & (r < 1.6 * RS)])); rs = np.arange(0.98, 1.6, 0.01); med = []
    for a0 in rs:
        k = m & (r >= a0 * RS) & (r < (a0 + 0.01) * RS); med.append(float(np.median(out[k])) / sd if k.sum() > 50 else np.nan)
    z = np.array(med); zz = z - np.nanmedian(z[rs > 1.3]); sel = (rs >= 1.0) & (rs < 1.3)
    return {'r': rs.round(2).tolist(), 'mediana_sobre_sigma': [None if not np.isfinite(v) else float(v) for v in z], 'max_abs_1.0_1.3_rel_1.3plus': float(np.nanmax(np.abs(zz[sel])))}


def main():
    which = sys.argv[1:] or ['mgn', 'wow']
    a, m = readbase(); a = np.array(a, np.float32); r, _ = coords(); assert a.shape == (vc.H, vc.W)
    ent, frep = farcit_perfil(a, m, r); full = np.ones_like(m); log(f'farcit: {frep}')
    np.save(CAU35 / 'entrada_operadors_farcida_v35.npy', ent)
    from PIL import Image
    y0, y1, x0, x1 = int(CY - 2 * RS), int(CY + 2 * RS), int(CX - 2 * RS), int(CX + 2 * RS); crop = np.log(np.maximum(ent[y0:y1, x0:x1], 1)); lo, hi = np.percentile(crop, [1, 99.5])
    Image.fromarray(np.uint8(np.clip((crop - lo) / (hi - lo), 0, 1) * 255)).save(vc.OUT / 'B4c_entrada_farcida_ln_2R.png')
    bound = {'boundary': 'input = base where supported, exp(azimuthal mean ln profile) elsewhere (lunar hole + outside support), used ONLY as operator input; output saved on physical support', 'farcit': frep, 'display': 'V34 receipts LUT'}
    v34 = {}
    for tag in (['P03_MGN'] if 'mgn' in which else []) + (['P04_WOW', 'P05_WOW_bilateral'] if 'wow' in which else []):
        o34 = np.load(V34P / 'cau' / f'{tag}_float.npy', mmap_mode='r'); v34[tag] = ring_bias(np.asarray(o34), m, r); log(f'{tag} V34: biaix d\'anell {v34[tag]["max_abs_1.0_1.3_rel_1.3plus"]:.2f} σ')
    if 'mgn' in which:
        a_mgn = np.maximum(a, 0); limits = [float(a_mgn[m].min()), float(a_mgn[m].max())]
        out = mgn(np.maximum(ent, 0), full, limits=limits); out = np.where(m, out, np.nan); rb = ring_bias(out, m, r)
        vc.save_output('P03_MGN', out, m, {'paper': 'Morgan & Druckmuller 2014, equations1-5', 'sigma_px': [1.25, 2.5, 5, 10, 20, 40], 'k': .7, 'h': .7, 'gamma': 3.2, 'weights': [1] * 6, 'input_limits': limits, 'nonpositive_input': 'native limb pixels clipped to 0 as allowed in paper; base itself unchanged', **bound, 'ring_bias_limb': {'V34': v34['P03_MGN']['max_abs_1.0_1.3_rel_1.3plus'], 'V35': rb['max_abs_1.0_1.3_rel_1.3plus']}}, display=display_of('P03_MGN'))
        log(f"P03 biaix d'anell al limbe: V34 {v34['P03_MGN']['max_abs_1.0_1.3_rel_1.3plus']:.2f} → V35 {rb['max_abs_1.0_1.3_rel_1.3plus']:.2f} σ"); del out
    if 'wow' in which:
        scales = int(np.round(np.log2(min(a.shape)) - np.log2(5)))
        for bilateral, tag in [(False, 'P04_WOW'), (True, 'P05_WOW_bilateral')]:
            out = wow(ent, full, scales, bilateral); out = np.where(m, out, np.nan); rb = ring_bias(out, m, r)
            vc.save_output(tag, out, m, {'paper': 'Auchere et al. 2023 A&A670 A66 equations4-9,16-18', 'author_reference': 'watroo', 'scales': scales, 'B3_kernel_1d': K.tolist(), 'weights': 'all1', 'h': 0, 'denoise': False, 'reason_no_denoise': 'no validated full-canvas HDR noise sigma', 'bilateral': 1 if bilateral else None, **bound, 'ring_bias_limb': {'V34': v34[tag]['max_abs_1.0_1.3_rel_1.3plus'], 'V35': rb['max_abs_1.0_1.3_rel_1.3plus']}}, display=display_of(tag))
            log(f"{tag} biaix d'anell al limbe: V34 {v34[tag]['max_abs_1.0_1.3_rel_1.3plus']:.2f} → V35 {rb['max_abs_1.0_1.3_rel_1.3plus']:.2f} σ"); del out
    savejson(REB35 / 'B4c_purs.json', {'farcit': frep, 'ring_bias_V34': v34}); log('B4c fet')


if __name__ == '__main__':
    main()
