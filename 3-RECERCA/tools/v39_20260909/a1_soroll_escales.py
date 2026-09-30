"""A1 (V39) · Model de soroll per escala: quanta energia de cada coeficient (à trous B3 escales 0–9 com el WOW; DoG gaussianes 1,2,4,8,16,32,64 com
ACHF/MGN) és soroll, en funció del radi, i com es relaciona amb la variància de la banda fina mesurada a la fusió (V_f = wv²·var_vixen + ws²·var_sony).
(a) ρ_s^blanc: quocient energia(coef_s)/energia(banda fina) sobre soroll BLANC (nuclis exactes); (b) ρ_s^emp(r): el mateix quocient mesurat a la
imatge real per anells (a 5–8 R☉ hauria de ser soroll; a dins, senyal + soroll); (c) fracció de l'energia de cada escala que és soroll per anell
segons el model V_f·ρ_s^blanc. Només lectura."""
from comu39 import *
from scipy.ndimage import gaussian_filter
sys.path.insert(0, str(ROOT / 'research/tools/v31_purs'))

K = np.array([1, 4, 6, 4, 1], np.float32) / 16


def atrous_scales(a, m, n):
    """Coeficients à trous B3 normalitzats al suport (com nconv del WOW), escales 0..n-1; retorna la llista de bandes."""
    from scipy.ndimage import convolve1d
    def conv(x, s):
        d = 2 ** s; k = np.zeros(4 * d + 1, np.float32); k[::d] = K
        return convolve1d(convolve1d(x, k, axis=0, mode='reflect'), k, axis=1, mode='reflect')
    c = np.where(m, a, 0).astype(np.float32); mf = m.astype(np.float32); out = []
    for s in range(n):
        nxt = conv(c, s) / np.maximum(conv(mf, s), 1e-20); out.append(np.where(m, c - nxt, 0).astype(np.float32)); c = np.where(m, nxt, 0)
    return out


def main():
    r, t = coords(); m = np.load(CAU38 / 'support_v38.npy'); G = np.asarray(np.load(CAU38 / 'base_G_v38.npy', mmap_mode='r'), np.float32)
    ok = m & (G > 0); L = np.where(ok, np.log(np.maximum(G, 1e-12)), 0).astype(np.float32); w = ok.astype(np.float32)
    Vf = var_fusio_fina(); rq = r / RS
    def ng(x, s):
        return gaussian_filter(x * w, s) / np.maximum(gaussian_filter(w, s), 1e-6)
    fina = np.where(ok, ng(L, 1.5) - ng(L, 3.0), 0)
    rings = [(1.1, 1.5), (1.5, 2.0), (2.0, 2.65), (2.65, 3.5), (3.5, 5.0), (5.0, 6.5), (6.5, 8.0)]
    rep = {'anells_R': rings, 'blanc': {}, 'emp': {}, 'fraccio_soroll_model': {}}
    # (a) soroll blanc: nuclis exactes sobre 1024² de N(0,1)
    rng = np.random.default_rng(1); nz = rng.standard_normal((1536, 1536)).astype(np.float32); mm = np.ones_like(nz, bool); wz = mm.astype(np.float32)
    fz = gaussian_filter(nz, 1.5) - gaussian_filter(nz, 3.0); ef = float(np.var(fz[200:-200, 200:-200]))
    white = {}
    for s in (1, 2, 4, 8, 16, 32, 64):
        d = nz - gaussian_filter(nz, s); white[f'dog{s}'] = float(np.var(d[200:-200, 200:-200]) / ef)
    for s, band in enumerate(atrous_scales(nz, mm, 8)):
        white[f'atrous{s}'] = float(np.var(band[200:-200, 200:-200]) / ef)
    rep['blanc'] = white; log('ρ blanc: ' + ' '.join(f'{k}:{v:.3f}' for k, v in white.items()))
    # (b) empíric per anells sobre la imatge real (ln G): DoG i à trous
    bands = {f'dog{s}': np.where(ok, L - ng(L, s), 0) for s in (1, 2, 4, 8, 16, 32)}
    for s, band in enumerate(atrous_scales(L, ok, 8)):
        bands[f'atrous{s}'] = band
    Ef = fina * fina
    for k, b in bands.items():
        e = b * b; row = {}; frac = {}
        for a0, a1 in rings:
            s = ok & (rq > a0) & (rq < a1); Es = float(np.mean(e[s])); Efr = float(np.mean(Ef[s])); Vr = float(np.mean(Vf[s]))
            row[f'{a0}-{a1}'] = {'E_escala': Es, 'E_fina_mesurada': Efr, 'V_f_mapa': Vr, 'rho_emp': Es / max(Efr, 1e-20)}
            frac[f'{a0}-{a1}'] = float(min(1.0, Vr * white[k] / max(Es, 1e-20)))
        rep['emp'][k] = row; rep['fraccio_soroll_model'][k] = frac
        log(f"{k}: ρ_emp per anell " + ' '.join(f"{a0}-{a1}:{row[f'{a0}-{a1}']['rho_emp']:.2f}" for a0, a1 in rings) + f" | blanc {white[k]:.2f} | fracció soroll (model) " + ' '.join(f"{frac[f'{a0}-{a1}']:.2f}" for a0, a1 in rings))
    # el mapa V_f contra la banda fina mesurada (hauria de ser ≈ 1 on la banda fina és soroll)
    row = {}
    for a0, a1 in rings:
        s = ok & (rq > a0) & (rq < a1); row[f'{a0}-{a1}'] = float(np.mean(Vf[s]) / max(np.mean(Ef[s]), 1e-20))
    rep['V_f_sobre_E_fina'] = row; log('V_f / E_fina per anell: ' + ' '.join(f'{k}:{v:.2f}' for k, v in row.items()))
    savejson(REB39 / 'A1_soroll_escales.json', rep); np.save(CAU39 / 'var_fusio_fina.npy', Vf); log('A1 fet')


if __name__ == '__main__':
    main()
