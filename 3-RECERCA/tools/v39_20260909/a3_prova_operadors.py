"""A3 (V39) · Banc de proves dels operadors amb guany de Wiener (τ ∈ {0, 0,8, 1,0, 1,2}; τ = 0 = V38) a tres finestres de 1024² (1,6 / 3,7 / 5,5 R☉):
(a) descomposició en MEITATS: potència coherent P_c = ⟨f(E)·f(O)⟩ i potència de soroll P_n = ⟨(f(E)−f(O))²⟩/4 de la sortida de cada operador
    aplicat a les dues meitats independents (Vixen V38 parell/senar dins 1,9 R☉; fora, fusió de meitats amb els pesos V38 i les meitats Sony V29);
    el que volem: P_n cau, P_c es conserva (≥ 0,90 de τ = 0);
(b) injecció cega ±: parells de blobs DoG (σ 2/8/24 px, mitjana zero) a 1 %, 3 % i 10 % de la mediana local, resposta aparellada (f(a+i)−f(a−i))/2
    projectada sobre la injecció; quocient V39/V38 per escala i amplitud; porta 0,90–1,10 quan la injecció supera 3 σ_soroll de la seva escala;
(c) mapes de guany g_s de la finestra del mig (no han de dibuixar vores de pes ni del limbe). Només lectura; escriu rebuts i vistes."""
from comu39 import *
import os
from filtres_v39 import Soroll, wow_v39, mgn_v39, achf_v39, ng
from scipy.ndimage import gaussian_filter
TAUS = [float(x) for x in os.environ.get('A3_TAUS', '0,0.8,1.0,1.2').split(',')]; WIN = 1024; HALF = WIN // 2
WINDOWS = {'1.6R': (CX + 1.6 * RS * np.cos(np.radians(-135)), CY + 1.6 * RS * np.sin(np.radians(-135))), '3.7R': (5089.0, 5294.0), '5.5R': (CX - 5.5 * RS, CY + 0.6 * RS)}


class SorollRetall:
    def __init__(self, sor, y0, x0):
        self.sor = sor; self.y0 = y0; self.x0 = x0
    def N(self, key, shape):
        return self.sor.N(key, (H, W))[self.y0:self.y0 + shape[0], self.x0:self.x0 + shape[1]]


def operadors(a, m, sor, tau, amb_bilateral=True):
    """Retorna dict nom → sortida (float32) de cada operador sobre a (lineal) o ln a (ACHF)."""
    lim = [0.0, float(np.max(a[m]))]; out = {}
    out['MGN'] = mgn_v39(np.maximum(a, 0), m, sor, tau, limits=lim, log=lambda *_: None)
    out['WOW'] = wow_v39(a, m, 8, False, sor, tau, log=lambda *_: None)
    if amb_bilateral: out['WOWbil'] = wow_v39(a, m, 8, True, sor, tau, log=lambda *_: None)
    L = np.where(m & (a > 0), np.log(np.maximum(a, 1e-12)), 0).astype(np.float32); w = m.astype(np.float32)
    out['ACHF01'] = achf_v39(L, w, (2, 4, 8, 16, 32), sor, tau, log=lambda *_: None)
    out['ACHF04'] = achf_v39(L, w, (1, 2, 4, 8, 16), sor, tau, log=lambda *_: None)
    out['ACHF06'] = achf_v39(L, w, (4, 8, 16, 32, 64), sor, tau, log=lambda *_: None)
    return out


def main():
    while not (CAU39 / 'soroll_escales_1q.npz').exists():
        time.sleep(15)
    wv_full = np.nan_to_num(np.asarray(np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r'), np.float32)); sor = Soroll(CAU39 / 'soroll_escales_1q.npz', wv_full)
    m_all = np.load(CAU38 / 'support_v38.npy'); G = np.load(CAU38 / 'base_G_v38.npy', mmap_mode='r'); ms = np.load(CAUF / 'sony_support.npy')
    VE = np.load(CAU39 / 'vixen_total_v38_parell.npy', mmap_mode='r'); VO = np.load(CAU39 / 'vixen_total_v38_senar.npy', mmap_mode='r')
    SE = np.load(ROOT / 'research/tools/v29/cau_final/sony_even_total.npy', mmap_mode='r'); SO = np.load(ROOT / 'research/tools/v29/cau_final/sony_odd_total.npy', mmap_mode='r'); rho = np.load(CAU38 / 'rho_v38.npy', mmap_mode='r')
    rep = {'taus': TAUS, 'finestres': {}}; rng = np.random.default_rng(982471)
    yy, xx = np.mgrid[:WIN, :WIN]
    only = [a_ for a_ in sys.argv[1:] if a_ in WINDOWS]; rep_path = REB39 / ('A3_prova_operadors' + ('_' + only[0] if only else '') + os.environ.get('A3_SUFIX', '') + '.json')
    for wname, (cx, cy) in WINDOWS.items():
        if only and wname not in only: continue
        x0, y0 = int(cx) - HALF, int(cy) - HALF; sl = (slice(y0, y0 + WIN), slice(x0, x0 + WIN)); a = np.asarray(G[sl], np.float32); m = m_all[sl] & (a > 0); sorw = SorollRetall(sor, y0, x0)
        wv = wv_full[sl]; wsn = np.where(ms[sl], 1 - wv, 0); wvn = np.where(ms[sl], wv, 1.0)
        # meitats fusionades amb els pesos V38 (la Sony V29 escalada per ρ; nivell global igualat a la fusió dins la finestra)
        def half(Vh, Sh):
            v = np.nan_to_num(np.asarray(Vh[sl][..., 1], np.float32)); s = np.nan_to_num(np.asarray(Sh[sl][..., 1], np.float32)) * np.nan_to_num(np.asarray(rho[sl][..., 1], np.float32))
            f = wvn * v + wsn * s; ok = m & (f > 0); f = f * float(np.median(a[ok]) / np.median(f[ok])); return np.where(ok, f, 0).astype(np.float32), ok
        E, mE = half(VE, SE); O, mO = half(VO, SO); mh = m & mE & mO
        core = np.s_[128:-128, 128:-128]; res = {}
        log(f'finestra {wname}: origen ({x0},{y0}) · suport {m.mean():.2f} · mediana {np.median(a[m]):.4g} · pes Vixen mitjà {wv[m].mean():.2f}')
        base_out = None; inj_base = None
        for tau in TAUS:
            fe = operadors(E, mh, sorw, tau); fo = operadors(O, mh, sorw, tau); row = {}
            for k in fe:
                hx = fe[k] - ng(fe[k], mh, 32); hy = fo[k] - ng(fo[k], mh, 32); x, y = hx[core][mh[core]], hy[core][mh[core]]; Pc = float(np.mean(x * y)); Pn = float(np.mean((x - y) ** 2) / 4); row[k] = {'P_coherent': Pc, 'P_soroll': Pn}
            # injecció ± sobre la imatge sencera de la finestra
            med = float(np.median(a[m])); inj_rows = {}
            for sig in ((2, 8, 24) if tau in (0.0, 1.0) else ()):
                blob = np.zeros((WIN, WIN), np.float32)
                for _ in range(3):
                    cyx = rng.integers(200, WIN - 200, 2); g1 = np.exp(-((xx - cyx[1]) ** 2 + (yy - cyx[0]) ** 2) / (2 * sig * sig)); g2 = np.exp(-((xx - cyx[1]) ** 2 + (yy - cyx[0]) ** 2) / (2 * (2 * sig) ** 2)) / 4
                    blob += (g1 - g2).astype(np.float32)       # DoG de mitjana ~zero
                for amp_rel in (0.01, 0.05):
                    inj = amp_rel * med * blob; fp = operadors(np.maximum(a + inj, 0), m, sorw, tau, False); fm = operadors(np.maximum(a - inj, 0), m, sorw, tau, False)
                    for k in fp:
                        d = (fp[k] - fm[k]) / 2; good = m & (np.abs(blob) > 0.05); resp = float(np.sum(d[good] * blob[good]) / np.sum(blob[good] ** 2)); inj_rows[f'{k}_s{sig}_a{amp_rel:g}'] = resp
            row['injeccio'] = inj_rows
            if tau == 0:
                base_out = row
            else:
                # quocients contra τ = 0
                row['quocients'] = {k: {'P_coherent': row[k]['P_coherent'] / max(base_out[k]['P_coherent'], 1e-30), 'P_soroll': row[k]['P_soroll'] / max(base_out[k]['P_soroll'], 1e-30)} for k in fe}
                row['quocients_injeccio'] = {k: (v / base_out['injeccio'][k] if abs(base_out['injeccio'].get(k, 0)) > 1e-12 else None) for k, v in inj_rows.items()}
                log(f"  τ {tau}: " + ' | '.join(f"{k}: Pc {row['quocients'][k]['P_coherent']:.2f} Pn {row['quocients'][k]['P_soroll']:.2f}" for k in fe))
                qi = row['quocients_injeccio']
                if qi: log('    injecció V39/V38 (σ2/σ8/σ24 a 1 % i 5 %): ' + ' | '.join(f"{k}: " + ' '.join(f"{qi[f'{k}_s{s}_a{a_}']:.2f}" if qi.get(f'{k}_s{s}_a{a_}') is not None else 'nan' for s in (2, 8, 24) for a_ in ('0.01', '0.05')) for k in ('MGN', 'WOW', 'ACHF01', 'ACHF04', 'ACHF06')))
            res[str(tau)] = row
        rep['finestres'][wname] = {'origen_xy': [x0, y0], 'mediana': float(np.median(a[m])), 'pes_vixen_mitja': float(wv[m].mean()), 'resultats': res}
        savejson(rep_path, rep)
    # (c) mapes de guany a la finestra del mig per a τ = 1
    if (only and '3.7R' not in only) or os.environ.get('A3_SUFIX'): log('A3 fet'); return
    cx, cy = WINDOWS['3.7R']; x0, y0 = int(cx) - HALF, int(cy) - HALF; sl = (slice(y0, y0 + WIN), slice(x0, x0 + WIN)); a = np.asarray(G[sl], np.float32); m = m_all[sl] & (a > 0); sorw = SorollRetall(sor, y0, x0)
    gains = {}; mgn_v39(np.maximum(a, 0), m, sorw, 1.0, limits=[0, float(a[m].max())], log=lambda *_: None, gains_out=gains)
    from PIL import Image
    tiles = [np.uint8(np.clip(gains[s], 0, 1) * 255) for s in sorted(gains)]; sheet = np.concatenate([np.concatenate(tiles[:3], axis=1), np.concatenate(tiles[3:6], axis=1)], axis=0)
    Image.fromarray(sheet).resize((sheet.shape[1] // 2, sheet.shape[0] // 2)).save(VIS39 / 'A3_guanys_MGN_finestra_3.7R_tau1.png'); log('A3 fet')


if __name__ == '__main__':
    main()
