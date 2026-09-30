"""A4 (V39) · Soroll MESURAT de les bandes à trous BILATERALS (P05): el bilateral és no lineal (Codex: cal Monte Carlo o meitats), o sigui que el soroll
de cada banda es mesura passant CADA meitat pel bilateral sencer i restant: N_s = E[(w_s(E) − w_s(O))²]/4, on w_s(·) és la banda bilateral de
l'escala s (mateix codi v31_purs bilateral_conv, mateixa dylib). Vixen: meitats V38 (parell/senar); Sony: meitats V29. En unitats RELATIVES
(banda de la imatge lineal dividida pel nivell local de l'escala), a 1/4 de resolució, finestra σ_E = max(3·2^s, 8 px). Escriu cau/soroll_bilateral_1q.npz."""
from comu39 import *
sys.path.insert(0, str(HERE39)); from filtres_v39 import bilateral_conv, nconv
from scipy.ndimage import gaussian_filter
NS = 11


def down4(x):
    h, w = x.shape; hh, ww = h // 4 * 4, w // 4 * 4; return x[:hh, :ww].reshape(hh // 4, 4, ww // 4, 4).mean(axis=(1, 3)).astype(np.float32)


def bandes_bilaterals(a, m):
    """Generador de (s, banda_relativa) del WOW bilateral sobre a (lineal): banda = (c − bil(c)) / nivell local."""
    c = np.where(m, a, 0).astype(np.float32)
    for s in range(NS):
        nxt = bilateral_conv(c, m, s); wave = c - nxt; rel = np.where(m, wave / np.maximum(nxt, 1e-9), 0).astype(np.float32); yield s, rel; c = np.where(m, nxt, 0)


def main():
    out = {}
    PART = __import__('os').environ.get('PART', ''); PA, PB = ('pA', 'pB') if PART == 'pAB' else ('parell', 'senar'); PSUF = '_pAB' if PART == 'pAB' else ''   # segona partició (V40): parelles alternades AABB
    parells = {'vixen': (CAU39 / f'vixen_total_v38_{PA}.npy', CAU39 / f'vixen_total_v38_{PB}.npy'), 'sony': (ROOT / 'research/tools/v29/cau_final/sony_even_total.npy', ROOT / 'research/tools/v29/cau_final/sony_odd_total.npy')}
    for tren, (pe, po) in parells.items():
        E = np.nan_to_num(np.asarray(np.load(pe, mmap_mode='r')[..., 1], np.float32)); O = np.nan_to_num(np.asarray(np.load(po, mmap_mode='r')[..., 1], np.float32)); m = (E > 0) & (O > 0); dt = dist_vora_suport(m); m &= dt >= 16   # V40: fora els 16 px de TOTES les vores del suport comú
        gE = bandes_bilaterals(E, m); gO = bandes_bilaterals(O, m)
        for (s, be), (_, bo) in zip(gE, gO):
            d = be - bo; mg = m & (dt >= max(16.0, float(2 ** s))); e4 = down4(np.where(mg, d * d, 0)); m4 = down4(mg.astype(np.float32)); sg = max(3.0 * 2 ** s, 8.0) / 4.0   # guarda per escala
            out[f'{tren}_bilat{s}'] = (gaussian_filter(e4 * m4, sg) / np.maximum(gaussian_filter(m4, sg), 1e-6) / 4.0).astype(np.float32); log(f'{tren} bilateral escala {s} fet')
        out[f'{tren}_suport4'] = down4(m.astype(np.float32)); del E, O, m
    np.savez(CAU39 / f'soroll_bilateral_1q{PSUF}.npz', **out); log(f'A4{PSUF} fet')


if __name__ == '__main__':
    main()
