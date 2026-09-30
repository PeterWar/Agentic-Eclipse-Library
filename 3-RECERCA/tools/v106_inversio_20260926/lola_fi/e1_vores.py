"""e1 (V106, «LOLA fi», Claude, 26-09-2026) · Vora observada de cada fotograma a calaixos de 0,25°.
Per a cada fotograma j i canal c: perfils radials al voltant del centre del model (distance_model), mostreig 0,05° × 0,25 px, mitjana a
calaixos de 0,25° (≈ 2 px d'arc), i ajust del graó (corona exponencial tallada per la Lluna, PSF doble gaussiana, fons lineal) → u0 = posició
de la vora respecte de la vora prevista R + e_o2(θ) (px), amb error formal. Validesa: dada a −2…+4 px de la vora prevista (els llargs, saturats
fora de la Lluna, no en tenen: es declara). PSF: la de b1 per fotograma i canal si n'hi ha; si no, (1,2; 0,3; 2,3). Passada 2 (PSF=refet):
la PSF es torna a ajustar per fotograma amb les vores fixes (quadrícula) i es refà l'ajust.
Ús: e1_vores.py [PSF_JSON_opcional] ; sortida: E1_VORES{tag}.npz"""
import sys, json, time, numpy as np, os
from multiprocessing import Pool
from vora_lib import *
TAG = os.environ.get('E1_TAG', '')
CANALS = [int(c) for c in os.environ.get('E1_CANALS', '1').split(',')]
PSF_OVR = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 else None
B1 = {c: {r['j']: r for r in json.loads((R0 / f'4-RESULTATS/v106_inversio_20260926/b1/B1_PSF_LOLA_canal{c}.json').read_text())['fotogrames']} for c in range(3)}
def psf_de(j, c):
    if PSF_OVR is not None and str(j) in PSF_OVR.get(str(c), {}): return tuple(PSF_OVR[str(c)][str(j)])
    if j in B1[c] and not B1[c][j]['saturat']: return (B1[c][j]['s1'], B1[c][j]['f'], B1[c][j]['s2'])
    return (1.2, 0.3, 2.3)
def feina(arg):
    j, c = arg
    V, W, th, r = polar(j, c); Pb = bins(V).T                 # (1440, ns)
    okc = np.isfinite(Pb)
    fin = lambda lo, hi: okc[:, (S >= lo) & (S <= hi)].mean(1)
    valid = (fin(-2, 4) >= 0.95) & (fin(-8, -3) >= 0.6) & (fin(4, 10) >= 0.6)
    psf = psf_de(j, c)
    if valid.sum() < 50:
        return j, c, None
    p, err, s2, n = ajusta(np.where(valid[:, None], Pb, np.nan), S, psf)
    p[~valid] = np.nan; err[~valid] = np.nan; s2[~valid] = np.nan
    # nivell de senyal a la vora (A) relatiu al soroll (per a la qualitat)
    return j, c, dict(p=p, err=err, chi2=s2, n=n, valid=valid, psf=np.array(psf))
if __name__ == '__main__':
    t0 = time.time(); tasks = [(j, c) for j in range(nF) for c in CANALS]
    with Pool(8) as pool: out = pool.map(feina, tasks, chunksize=1)
    nb = 360 * 4; U0 = np.full((3, nF, nb), np.nan); ER = np.full_like(U0, np.nan); PAR = np.full((3, nF, nb, 5), np.nan); CHI = np.full_like(U0, np.nan); PSF = np.full((3, nF, 3), np.nan)
    for j, c, d in out:
        if d is None: continue
        U0[c, j] = d['p'][:, 4]; ER[c, j] = d['err']; PAR[c, j] = d['p']; CHI[c, j] = d['chi2']; PSF[c, j] = d['psf']
    C = np.array([centre_model(j) for j in range(nF)])
    th_b = (np.arange(nb) + 0.5) * 0.25
    np.savez_compressed(Path(__file__).parent / f'E1_VORES{TAG}.npz', u0=U0, err=ER, par=PAR, chi2=CHI, psf=PSF, centres=C, theta=th_b, t=TIMES, exp=EXPO,
                        R=R, e_o2=e_o2(th_b), nota='u0 = vora observada − (R + e_o2(θ)) respecte del centre del model de cada fotograma; θ del llenç (0 = dreta, 90 = amunt)')
    for j in range(nF):
        v = np.isfinite(U0[1, j])
        print(j, FR[j]['name'], f"t {TIMES[j]:6.2f} exp {EXPO[j]:.5f}", 'calaixos vàlids', int(v.sum()), 'err med', np.round(np.nanmedian(ER[1, j]), 3) if v.any() else '-', 'psf', np.round(PSF[1, j], 2))
    print('fet', round(time.time() - t0, 1), 's')
