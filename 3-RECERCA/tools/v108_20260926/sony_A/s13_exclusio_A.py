"""s13 · L'ALTERNATIVA «EXCLOURE D'A LA FRANJA DEL SENSOR» emulada a la fusió A+B de la Sony (la de b3 del pilot, flat 2D): dins d'una franja
de ±w px al voltant de T1 (la franja del sensor d'A que el veu; la deriva d'A hi és ≤ 3,5 px), el pes d'A a la fusió passa a 0 amb una
rampa de 12 px, i la dada hi queda NOMÉS de B (independent del sensor d'A). T2 no es pot tractar així: allà només hi ha A (fA = 1).
Nul: la mateixa exclusió en una franja paral·lela a +250 px (on no hi ha traç): no hi ha de canviar res de significatiu.
Es mesura T1 (geometria fixa, nul a la mateixa imatge) i el soroll local (σ del nul). Sortida: S13_EXCLUSIO_A.json."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
B3 = PIL / 'cadena_v108/b3/cau'; tr = TRACOS[1]; box = caixa_tr(tr, 700); x0, y0, x1, y1 = box
Ac = retall(np.load(B3 / 'sony_A_corr_v42.npy', mmap_mode='r'), 1, box); Bb = retall(np.load(FONTS['B_f2d'][0], mmap_mode='r'), 1, box)
fA = np.asarray(np.load(B3 / 'sony_fA_v42.npy', mmap_mode='r')[y0:y1, x0:x1], np.float32); Sref = retall(np.load(B3 / 'sony_corrected_total_v42.npy', mmap_mode='r'), 1, box)
yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32); tt = (xx - tr['centre'][0]) * tr['n'][0] + (yy - tr['centre'][1]) * tr['n'][1]
ss = (xx - tr['centre'][0]) * tr['d'][0] + (yy - tr['centre'][1]) * tr['d'][1]
def fusio(f): return np.where(np.isfinite(Ac) & np.isfinite(Bb), f * np.nan_to_num(Ac) + (1 - f) * np.nan_to_num(Bb), np.nan).astype(np.float32)
chk = fusio(fA); k = np.isfinite(chk) & np.isfinite(Sref) & (Sref > 0)
res = dict(reproduccio_fusio_pilot_max_rel=float(np.nanmax(np.abs(chk[k] / Sref[k] - 1))))
print('reproducció de la fusió del pilot: |rel| màx', res['reproduccio_fusio_pilot_max_rel'], flush=True)
L = tr['llarg']
for nom, t0, w in (('sense_exclusio', None, 0), ('exclou_A_pm15', 0.0, 15), ('exclou_A_pm30', 0.0, 30), ('nul_pm30_a_250px', 250.0, 30)):
    f = fA.copy()
    if t0 is not None:
        dist = np.abs(tt - t0); along = np.abs(ss) <= L / 2 + 60
        m = np.clip((dist - w) / 12.0, 0, 1); m = np.where(along, m, 1.0); f = f * m
    S = fusio(f); r = rel_map(np.where(np.isfinite(S) & (S > 0), S, 0).astype(np.float32))
    m1, t, pr = mesura_amb_nul(r, box[:2], tr['centre'], tr['d'], tr['llarg'])
    # i a la franja nul·la de +250 px (per veure que el nul no la mou)
    c2 = tr['centre'] + 250 * tr['n']; m2, _, _ = mesura_amb_nul(r, box[:2], c2, tr['d'], tr['llarg'])
    res[nom] = dict(T1=m1, recta_a_250px=m2, D_t0_menys4_a_mes8=[profunditat(t, pr, q) for q in range(-4, 9, 2)])
    print(f"{nom:18s}: T1 {m1['D']*1e4:+.2f}‱ (z {m1['z']:+.1f}, p {m1['p']:.3f}, σ nul {m1['nul_mad']*1e4:.2f}) · D(t0 −4…+8) " + ' '.join(f'{v*1e4:+.1f}' for v in res[nom]['D_t0_menys4_a_mes8']) + f" · recta a +250 px {m2['D']*1e4:+.2f}‱ (z {m2['z']:+.1f})", flush=True)
desa(OUT / 'S13_EXCLUSIO_A.json', res)
