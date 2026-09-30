"""A2c (V39) · Com A2 però per als canals R (0) i B (2) de les meitats (l'ACHF treballa per canal; el soroll de R i B no és el de G): només les bandes DoG. Escriu cau/soroll_escales_1q_c{c}.npz.

Heretat: A2 (V39) · Soroll MESURAT per escala (no modelat): meitats independents de cada tren (Vixen: fotogrames alternats en el temps, recompostos
amb la cadena V38 sencera, b2_meitats; Sony: meitats even/odd de la V29, cau_final), diferència en ln G, passada pels MATEIXOS nuclis que cada
operador (à trous B3 escales 0–10 del WOW; DoG gaussianes 1,25/2,5/5/10/20/40 del MGN; 1/2/4/8/16/32/64 de l'ACHF), energia local
(E[(band(ln E)−band(ln O))²]/4, finestra σ_E = max(3 ℓ_s, 8 px)) desada a 1/4 de resolució. Fusió: N = wV²·N_V + wS²·N_S (pesos V38).
Sanejament: fracció de soroll per anell contra l'energia real de cada banda de la fusió."""
from comu39 import *
sys.path.insert(0, str(HERE39))
from scipy.ndimage import gaussian_filter, convolve1d
K = np.array([1, 4, 6, 4, 1], np.float32) / 16
ATROUS = list(range(11)); DOG = [1.0, 1.25, 2.0, 2.5, 4.0, 5.0, 8.0, 10.0, 16.0, 20.0, 32.0, 40.0, 64.0]


def down4(x):
    h, w = x.shape; hh, ww = h // 4 * 4, w // 4 * 4
    return x[:hh, :ww].reshape(hh // 4, 4, ww // 4, 4).mean(axis=(1, 3)).astype(np.float32)


def bands_of(D, m):
    """Totes les bandes (mateixos nuclis que els operadors) de la diferència D sobre el suport m. Retorna generador (clau, ℓ_px, banda)."""
    w = m.astype(np.float32); Dm = np.where(m, D, 0).astype(np.float32)
    def ng(x, s):
        return gaussian_filter(x * w, s) / np.maximum(gaussian_filter(w, s), 1e-6)
    for s in DOG:
        yield f'dog{s:g}', s, np.where(m, Dm - ng(Dm, s), 0)
    for nom, ladder in (('achf', [1, 2, 4, 8, 16, 32, 48, 64]), ('mgn', [1.25, 2.5, 5, 10, 20, 40])):   # V39: bandes ENTRE σ consecutives de cada escala d'operador (guany per banda, no per passa-alt)
        prev = Dm
        for s in ladder:
            sm = ng(Dm, s); yield f'bp{nom}{s:g}', s, np.where(m, prev - sm, 0); prev = sm
    from filtres_v39 import atrous_conv as conv   # dylib dispersa (ràpida a les escales grans)
    c = Dm.copy()
    for s in ATROUS:
        nxt = conv(c, s) / np.maximum(conv(w, s), 1e-20); yield f'atrous{s}', float(2 ** s), np.where(m, c - nxt, 0); c = np.where(m, nxt, 0)


def energia(band, m, ell):
    e4 = down4(band * band); m4 = down4(m.astype(np.float32)); s = max(3 * ell, 8.0) / 4.0
    return (gaussian_filter(e4 * m4, s) / np.maximum(gaussian_filter(m4, s), 1e-6) / 4.0).astype(np.float32)   # /4: (E−O)² té 4 σ² de la mitjana completa


def main():
    CANAL = int(sys.argv[1]); out = {}; rep = {'meitats': {'vixen': 'b2_meitats parell/senar (V38, alternats en el temps)', 'sony': 'v29/cau_final sony_even/odd_total (cadena V29; aproximació declarada)'}, 'finestra': 'σ_E = max(3 ℓ_s, 8 px)', 'escales': {}}
    PART = __import__('os').environ.get('PART', ''); PA, PB = ('pA', 'pB') if PART == 'pAB' else ('parell', 'senar'); PSUF = '_pAB' if PART == 'pAB' else ''   # segona partició (V40): parelles alternades AABB
    parells = {'vixen': (CAU39 / f'vixen_total_v38_{PA}.npy', CAU39 / f'vixen_total_v38_{PB}.npy'), 'sony': (ROOT / 'research/tools/v29/cau_final/sony_even_total.npy', ROOT / 'research/tools/v29/cau_final/sony_odd_total.npy')}
    for tren, (pe, po) in parells.items():
        E = np.asarray(np.load(pe, mmap_mode='r')[..., CANAL], np.float32); O = np.asarray(np.load(po, mmap_mode='r')[..., CANAL], np.float32)
        m = np.isfinite(E) & np.isfinite(O) & (E > 0) & (O > 0); dt = dist_vora_suport(m); m &= dt >= 16; D = np.where(m, np.log(np.maximum(E, 1e-12)) - np.log(np.maximum(O, 1e-12)), 0).astype(np.float32); del E, O   # V40: fora els 16 px de TOTES les vores del suport comú (no només el forat)
        log(f'{tren}: suport comú {m.sum()} px · rms ln(E/O) {np.sqrt(np.mean(D[m]**2)):.4f}')
        for key, ell, band in bands_of(D, m):
            if not (key.startswith('dog') or key.startswith('bpachf')): continue
            out[f'{tren}_{key}'] = energia(band, m & (dt >= max(16.0, ell)), ell); log(f'{tren} canal {CANAL} {key} fet')
        out[f'{tren}_suport4'] = down4(m.astype(np.float32)); del D, m
    np.savez(CAU39 / f'soroll_escales_1q_c{CANAL}{PSUF}.npz', **out); log(f'A2c canal {CANAL}{PSUF} fet')


if __name__ == '__main__':
    main()
