"""e3 (V106, «LOLA fi») · Vora observada (mitjana de tots els fotogrames mesurables, en coordenades lunars) contra el perfil LOLA-64 i LOLA-16.
Orientació (angle del nord celeste al llenç θN, i paritat), escala del relleu, correlació per bandes d'escala i per sectors.
La vora observada de cada fotograma ja és en coordenades lunars (angle al voltant del SEU centre lunar; el llenç no gira)."""
import numpy as np, json, sys
from pathlib import Path
from scipy.ndimage import gaussian_filter1d
from e2_repro import U, E, th, nF, nb, treu_harm, bandes, gsm, corr, HARM2, Z
H = Path(__file__).parent; R0 = Path.home() / 'Desktop/Eclipse 2026'
R = float(Z['R']); PXKM = R / 1737.4
def rob(x): return 1.4826 * np.median(np.abs(x - np.median(x)))
# pes empíric per fotograma: invers de la variància robusta de la banda fina (soroll + seeing)
def mitjana(js, pes_emp=True):
    S = np.zeros(nb); W = np.zeros(nb); info = {}
    for j in js:
        u = U[j]; e = E[j]
        if np.isfinite(u).sum() < 600: continue
        w0 = np.where(np.isfinite(u) & np.isfinite(e), 1.0, 0.0)
        r, _ = treu_harm(np.nan_to_num(u), w0)
        B = bandes(r, w0); s = rob(B['fina'][w0 > 0]) if pes_emp else 0.05
        # rebuig de calaixos atípics (ajust fallit): |r − mitjana local 1°| > 5 σ
        loc = gsm(r, w0, 0.5); bad = np.abs(r - loc) > 5 * max(s, 0.03) * 1.8
        w = np.where((w0 > 0) & ~bad, 1 / s ** 2, 0); info[j] = s
        S += w * r; W += w
    return np.where(W > 0, S / np.maximum(W, 1e-30), np.nan), W, info
def perfil_lola(nom, thN, parit=1, sig_px=1.25):
    L = np.load(R0 / f'4-RESULTATS/v106_inversio_20260926/lola/{nom}'); pa = L['pa']; h = L['h_km'] * PXKM
    ang = (thN + parit * pa) % 360; o = np.argsort(ang); g = np.arange(0, 360, 0.01)
    hl = np.interp(g, ang[o], h[o], period=360)
    s = sig_px / (R * np.pi / 180) / 0.01; hl = gaussian_filter1d(hl, s, mode='wrap')                     # PSF al llarg de l'arc
    hl = hl.reshape(nb, 25).mean(1)                                                                       # calaix de 0,25°
    return hl
if __name__ == '__main__':
    tots = [j for j in range(nF) if np.isfinite(U[j]).sum() >= 600]
    u, W, info = mitjana(tots)
    print('fotogrames:', len(tots), ' σ fina per fotograma (robust):', ' '.join(f'{j}:{s:.3f}' for j, s in info.items()))
    ok = W > 0; w = ok.astype(float)
    u2, _ = treu_harm(np.nan_to_num(u), w)
    Bo = bandes(u2, w)
    for nom in ['PERFIL_LDEM64_182849.npz', 'PERFIL_LDEM16_182849.npz', 'PERFIL_prova.npz']:
        best = None
        for parit in (1, -1):
            for thN in np.arange(40.0, 49.0, 0.05):
                hl = perfil_lola(nom, thN, parit); h2, _ = treu_harm(hl, w)
                Bl = bandes(h2, w); c = corr(Bl['mitjana'] + Bl['fina'], Bo['mitjana'] + Bo['fina'], ok)
                if best is None or c > best[0]: best = (c, thN, parit)
        c0, thN0, par0 = best
        # afinament
        fine = [(corr(*(lambda Bl: (Bl['mitjana'] + Bl['fina'], Bo['mitjana'] + Bo['fina']))(bandes(treu_harm(perfil_lola(nom, t, par0), w)[0], w)), ok), t) for t in np.arange(thN0 - 0.1, thN0 + 0.1001, 0.005)]
        cF, thF = max(fine)
        hl = perfil_lola(nom, thF, par0); h2, _ = treu_harm(hl, w); Bl = bandes(h2, w)
        # escala (regressió observat = k·LOLA) per banda
        print(f'\n{nom}: paritat {par0:+d}, θN òptim {thF:.3f}° (ρ mitjana+fina {cF:+.3f});  a 44,25°: ' +
              f"{corr((lambda B: B['mitjana'] + B['fina'])(bandes(treu_harm(perfil_lola(nom, 44.25, par0), w)[0], w)), Bo['mitjana'] + Bo['fina'], ok):+.3f}")
        for k in ('gran', 'mitjana', 'fina'):
            x = Bl[k][ok]; y = Bo[k][ok]; kk = np.dot(x, y) / np.dot(x, x)
            print(f'   banda {k:8s}: ρ {corr(Bl[k], Bo[k], ok):+.3f}   rms LOLA {np.std(x):.3f} px  rms obs {np.std(y):.3f} px  pendent obs/LOLA {kk:+.2f}')
        SECT = [(0, 45), (45, 90), (90, 135), (135, 180), (180, 225), (225, 270), (270, 315), (315, 360)]
        for k in ('gran', 'mitjana', 'fina'):
            print(f'   sectors {k:8s}: ' + ' '.join(f'{lo}-{hi}:{corr(Bl[k], Bo[k], ok & (th >= lo) & (th < hi)):+.2f}' for lo, hi in SECT))
        # perfil de correlació contra θN (banda mitjana i fina)
        prof = [(t, corr((lambda B: B['mitjana'])(bandes(treu_harm(perfil_lola(nom, t, par0), w)[0], w)), Bo['mitjana'], ok), corr((lambda B: B['fina'])(bandes(treu_harm(perfil_lola(nom, t, par0), w)[0], w)), Bo['fina'], ok)) for t in np.arange(thF - 1.0, thF + 1.001, 0.1)]
        print('   ρ(θN) mitjana/fina: ' + ' '.join(f'{t:.1f}:{a:+.2f}/{b:+.2f}' for t, a, b in prof))
    np.savez_compressed(H / 'E3_OBS_MITJANA.npz', u=u, W=W, theta=th, u_sense_o2=u2)
