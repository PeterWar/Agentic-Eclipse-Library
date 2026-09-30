"""A3b (V39) · Porta d'injecció cega NETA (Codex: quocient V39/V38 ≥ 0,90 per cel·la quan la injecció supera 3 σ de soroll de la seva escala):
- blobs DoG ± (σ 2/8/24 px) a posicions FIXES dins d'un anell de radi controlat (lluny del forat i de les vores de la finestra);
- MGN amb h = 0 (només detall; el terme global és idèntic a V38/V39) i límits FIXOS; WOW sense el pla gros; ACHF tal qual;
- amplitud relativa 1 %, 3 %, 10 % de la mediana local; per a cada cel·la, l'amplitud en unitats de σ_soroll de l'escala corresponent (mapes A2)
  i el quocient resposta_V39/resposta_V38. Finestres: 1,6 R☉ (radi 1,4–1,8), 3,7 R☉, 5,5 R☉. Paràmetres: τ i SE_FACTOR de l'entorn."""
from comu39 import *
import os
from filtres_v39 import Soroll, wow_v39, mgn_v39, achf_v39, ng
import filtres_v39 as F
TAU = float(os.environ.get('A3B_TAU', '1.0')); WIN = 1024; HALF = 512
WINDOWS = {'1.6R': (CX + 1.6 * RS * np.cos(np.radians(-135)), CY + 1.6 * RS * np.sin(np.radians(-135))), '3.7R': (5089.0, 5294.0), '5.5R': (CX - 5.5 * RS, CY + 0.6 * RS)}


class SR:
    def __init__(s, sor, y0, x0): s.sor, s.y0, s.x0 = sor, y0, x0; s.z = sor.z; s.te_bilateral = getattr(sor, 'te_bilateral', False)
    def N(s, key, shape, canal=None): return s.sor.N(key, (H, W), canal=canal)[s.y0:s.y0 + shape[0], s.x0:s.x0 + shape[1]]


def ops(a, m, sor, tau, lim):
    out = {'MGN': mgn_v39(np.maximum(a, 0), m, sor, tau, h=0.0, limits=lim, log=lambda *_: None)}
    w = wow_v39(a, m, 8, False, sor, tau, log=lambda *_: None); out['WOW'] = w - ng(w, m, 96)   # sense el pla gros (que no es toca)
    L = np.where(m & (a > 0), np.log(np.maximum(a, 1e-12)), 0).astype(np.float32); wm = m.astype(np.float32)
    out['ACHF01'] = achf_v39(L, wm, (2, 4, 8, 16, 32), sor, tau, log=lambda *_: None); out['ACHF04'] = achf_v39(L, wm, (1, 2, 4, 8, 16), sor, tau, log=lambda *_: None); out['ACHF06'] = achf_v39(L, wm, (4, 8, 16, 32, 64), sor, tau, log=lambda *_: None)
    return out


def main():
    wv_full = np.nan_to_num(np.asarray(np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r'), np.float32)); sor = Soroll(CAU39 / 'soroll_escales_1q.npz', wv_full)
    m_all = np.load(CAU38 / 'support_v38.npy'); G = np.load(CAU38 / 'base_G_v38.npy', mmap_mode='r'); r, t = coords(); yy, xx = np.mgrid[:WIN, :WIN]
    only = [a_ for a_ in sys.argv[1:] if a_ in WINDOWS]; rep = {'tau': TAU, 'se_factor': F.SE_FACTOR, 'se_min': F.SE_MIN, 'mode': F.MODE, 'k': F.KSOFT, 'k_lo': F.KLO, 'k_hi': F.KHI, 'finestres': {}}
    for wname, (cx, cy) in WINDOWS.items():
        if only and wname not in only: continue
        x0, y0 = int(cx) - HALF, int(cy) - HALF; a = np.asarray(G[y0:y0 + WIN, x0:x0 + WIN], np.float32); m = m_all[y0:y0 + WIN, x0:x0 + WIN] & (a > 0); sr = SR(sor, y0, x0); rr = r[y0:y0 + WIN, x0:x0 + WIN] / RS
        lim = [0.0, float(np.max(a[m]))]; med = float(np.median(a[m]))
        # posicions: 3 per σ, a l'anell 1,4–1,8 (finestra 1,6R) o al nucli de la finestra (les altres), lluny del forat (> 60 px) i de la vora (> 200 px)
        cand = [(y, x) for y in range(220, 804, 40) for x in range(220, 804, 40) if m[y, x] and (wname != '1.6R' or 1.4 <= rr[y, x] <= 1.8) and rr[y, x] > 1.1]
        rng = np.random.default_rng(7); idx = rng.choice(len(cand), size=min(9, len(cand)), replace=False); pos = [cand[i] for i in idx]
        base = {t_: None for t_ in ('p', 'm')}; res = {}
        for sig, cyx3 in zip((2, 8, 24), (pos[0:3], pos[3:6], pos[6:9])):
            blob = np.zeros((WIN, WIN), np.float32)
            for cyx in cyx3:
                blob += (np.exp(-((xx - cyx[1]) ** 2 + (yy - cyx[0]) ** 2) / (2 * sig * sig)) - np.exp(-((xx - cyx[1]) ** 2 + (yy - cyx[0]) ** 2) / (2 * (2 * sig) ** 2)) / 4).astype(np.float32)
            good = m & (np.abs(blob) > 0.05); key_scale = {2: 'dog2', 8: 'dog8', 24: 'dog20'}[sig]; sig_n = float(np.sqrt(np.median(sr.N(key_scale, a.shape)[good])))   # σ relativa del soroll a l'escala
            for amp in (0.01, 0.03, 0.10):
                inj = amp * med * blob; fp0 = ops(np.maximum(a + inj, 0), m, sr, 0.0, lim); fm0 = ops(np.maximum(a - inj, 0), m, sr, 0.0, lim); fp1 = ops(np.maximum(a + inj, 0), m, sr, TAU, lim); fm1 = ops(np.maximum(a - inj, 0), m, sr, TAU, lim)
                for k in fp0:
                    d0 = (fp0[k] - fm0[k]) / 2; d1 = (fp1[k] - fm1[k]) / 2; r0 = float(np.sum(d0[good] * blob[good]) / np.sum(blob[good] ** 2)); r1 = float(np.sum(d1[good] * blob[good]) / np.sum(blob[good] ** 2))
                    res[f'{k}_s{sig}_a{amp:g}'] = {'amp_rel': amp, 'amp_en_sigma_soroll': amp / max(sig_n, 1e-9), 'resp_V38': r0, 'resp_V39': r1, 'quocient': (r1 / r0 if abs(r0) > 1e-12 else None)}
            log(f"{wname} σ{sig} (σ_soroll {100*sig_n:.2f} %): " + ' | '.join(f"{k} " + ' '.join(f"{res[f'{k}_s{sig}_a{amp:g}']['quocient']:.2f}" if res[f'{k}_s{sig}_a{amp:g}']['quocient'] is not None else 'nan' for amp in (0.01, 0.03, 0.10)) for k in ('MGN', 'WOW', 'ACHF01', 'ACHF04', 'ACHF06')))
        rep['finestres'][wname] = {'origen_xy': [x0, y0], 'posicions': [[int(p[1]) + x0, int(p[0]) + y0] for p in pos], 'resultats': res}
    savejson(REB39 / f"A3b_injeccio_{F.MODE}_k{F.KSOFT:g}_tau{TAU:g}_f{F.SE_FACTOR:g}_min{F.SE_MIN:g}{'_' + only[0] if only else ''}.json", rep); log('A3b fet')


if __name__ == '__main__':
    main()
