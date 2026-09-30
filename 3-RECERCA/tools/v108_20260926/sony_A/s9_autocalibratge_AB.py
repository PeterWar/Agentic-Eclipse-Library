"""s9 · PROVA GLOBAL de l'autocalibratge A − B (amb el flat 2D del pilot): hi ha cap patró fix que sigui NOMÉS de l'apuntament A?
Meitats independents (s8): A1, A2, B1, B2. Banda fina (residu relatiu σ 2 / σ 20 px). A la zona on les quatre tenen dada, 3–9,5 R☉:
  · corr(A1, A2) = cel + patró d'A (fix al sensor d'A, amb 2–3 px de deriva entre meitats) + tot el que és comú;
  · corr(A1, B2), corr(A2, B1) = NOMÉS el cel (els sensors són a 749 px l'un de l'altre) → la part «cel» de la textura fina;
  · corr(B1, B2) = cel + patró de B;
  · corr(E1, E2), amb E1 = A1 − B1 i E2 = A2 − B2 (soroll independent): els patrons fixos que A i B NO comparteixen (A − B).
Nuls: la mateixa correlació amb una de les dues imatges desplaçada 150 px (x i y). I, a la geometria de T1 i T2, el solc a cada meitat,
a E1, E2 i a E = A − B sencer. G de sortida (el que va a la base) i G de càmera. Sortida: S9_AUTOCALIBRATGE_AB.json."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
D = OUT / 'meitats_flat2d'; YM = 4200
yy, xx = np.mgrid[0:YM, 0:W].astype(np.float32); rs = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; del xx, yy
res = {}
for espai in ('G', 'Gcam'):
    R = {}; M = None
    for mn in ('A1', 'A2', 'B1', 'B2'):
        z = np.load(D / f'{mn}.npz'); img = z[espai]; w = z['w']; ok = np.isfinite(img) & (img > 0) & (w > 0.05 * np.nanmax(w))
        img = np.where(ok, img, 0).astype(np.float32); R[mn] = rel_map(img, sgran=20.0, sfi=2.0, erosio=61)
        M = np.isfinite(R[mn]) if M is None else (M & np.isfinite(R[mn]))
    zona = M & (rs > 3.0) & (rs < 9.5)
    E1 = R['A1'] - R['B1']; E2 = R['A2'] - R['B2']
    # retall robust dels valors extrems (estrelles residuals, el disc del centre del sensor)
    for q in (R['A1'], R['A2'], R['B1'], R['B2'], E1, E2):
        v = q[zona]; med = np.median(v); mad = 1.4826 * np.median(np.abs(v - med)); zona &= np.abs(q - med) < 6 * mad
    def corr(a, b, sh=(0, 0)):
        if sh != (0, 0): b = np.roll(b, sh, axis=(0, 1)); k = zona & np.roll(zona, sh, axis=(0, 1))
        else: k = zona
        x = a[k] - a[k].mean(); y = b[k] - b[k].mean(); return float((x * y).sum() / np.sqrt((x * x).sum() * (y * y).sum()))
    row = dict(pixels_zona=int(zona.sum()))
    for nom, (a, b) in {'A1_A2': (R['A1'], R['A2']), 'B1_B2': (R['B1'], R['B2']), 'A1_B1': (R['A1'], R['B1']), 'A1_B2': (R['A1'], R['B2']), 'A2_B1': (R['A2'], R['B1']), 'A2_B2': (R['A2'], R['B2']), 'E1_E2': (E1, E2)}.items():
        row[nom] = dict(corr=corr(a, b), nul_x150=corr(a, b, (0, 150)), nul_y150=corr(a, b, (150, 0)))
    row['sigma'] = {k: float(1.4826 * np.median(np.abs(v[zona] - np.median(v[zona])))) for k, v in (('A1', R['A1']), ('A2', R['A2']), ('B1', R['B1']), ('B2', R['B2']), ('E1', E1), ('E2', E2))}
    # part de variància per origen (covariàncies en les mateixes unitats)
    cov = lambda a, b: float(np.mean((a[zona] - a[zona].mean()) * (b[zona] - b[zona].mean())))
    cel = 0.5 * (cov(R['A1'], R['B2']) + cov(R['A2'], R['B1']))
    row['variancia_per_origen'] = dict(cel_i_comu=cel, patro_A=cov(R['A1'], R['A2']) - cel, patro_B=cov(R['B1'], R['B2']) - cel, total_A1=cov(R['A1'], R['A1']), total_B1=cov(R['B1'], R['B1']))
    print(f"{espai}: zona {zona.sum()} px · " + ' · '.join(f"{k} {v['corr']:+.3f} (nul {v['nul_x150']:+.3f}/{v['nul_y150']:+.3f})" for k, v in row.items() if isinstance(v, dict) and 'corr' in v), flush=True)
    vo = row['variancia_per_origen']; print(f"   variància fina: cel+comú {vo['cel_i_comu']:.3e} · patró A {vo['patro_A']:+.3e} · patró B {vo['patro_B']:+.3e} · total A1 {vo['total_A1']:.3e}", flush=True)
    # a la geometria de T1 i T2
    for k, tr in TRACOS.items():
        for nom, img in (('A1', R['A1']), ('A2', R['A2']), ('B1', R['B1']), ('B2', R['B2']), ('E1', E1), ('E2', E2), ('E_mitjana', 0.5 * (E1 + E2)), ('cel_mitjana_AB', 0.25 * (R['A1'] + R['A2'] + R['B1'] + R['B2']))):
            img2 = np.where(np.isfinite(img), img, np.nan).astype(np.float32)
            m, t, pr = mesura_amb_nul(img2, (0, 0), tr['centre'], tr['d'], tr['llarg'], girs=(-6, 6))
            row.setdefault(f'T{k}', {})[nom] = m
        print(f"   T{k}: " + ' · '.join(f"{n} {m['D']*1e4:+.1f}‱ (z {m.get('z', np.nan):+.1f})" for n, m in row[f'T{k}'].items()), flush=True)
    res[espai] = row
desa(OUT / 'S9_AUTOCALIBRATGE_AB.json', res)
