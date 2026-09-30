"""p1_franja_protuberancia_v5 (V108, flat2d_v5) · LA PROTUBERÀNCIA: la regla de la v4 (domini de la franja congelat al del control) més la
REGLA DE FRAGILITAT que va demanar el verificador 4. Còpia de p1_franja_protuberancia.py (v4) amb un sol afegit, documentat aquí.
Què passa (verificadors 2, 3 i 4): al nucli vermell de la protuberància de l'esquerra (180°, 16–26 px del limbe) la llum és gairebé només R.
El senyal post-matriu G' = (M·(R, G, B)·guany)_G hi és la resta petita de dos nombres grans (R' ≈ 5·10⁶, G' ≈ 3.000–10.000). El flat 2D mou
G'/ΣE en 3–6·10⁻⁴ (mediana; p90 9·10⁻⁴) a tota la franja: on G' és d'aquest ordre, el canvi de flat li canvia la mida un 30–100 % o el signe.
  · v4 (sense canvis): el domini de la franja és geometria i es congela al del control; als píxels que el control té al domini i la variant hi
    perdria (pel signe de G'), els valors de la franja del CONTROL. Això tapava 2 píxels.
  · v5, FRAGILITAT: f = |E_G| / (|E_R| + |E_G| + |E_B|), amb E = la franja post-matriu del CONTROL (la de la V107). Als píxels del domini del
    control amb f < 0,002, la dada no pot dir res de nou (el que la variant hi posa és el soroll del flat amplificat: ×0,05 … ×30):
    hi van els valors de la franja del CONTROL, com als perduts (G, F, V, E, domini, domini_E, dins_franja, beta).
    El llindar 0,002 és el del verificador 4 (y3) i és ~2 vegades el p90 del canvi de G'/ΣE que fa el flat: per sota, el flat mou G' un
    30–100 % (mediana 65 %); a 0,002–0,005, un 10 % (mediana); per sobre de 0,01, ≤ 1 %. La f es llegeix del CONTROL (congelada, com el
    domini): la regla no depèn de la variant. Al rebut, també la f de la variant, per saber quins píxels a tocar del llindar hi entrarien.
  · Píxels que la variant hi afegeix i el control no: fora del domini, com al control (G, F, V = les fonts de la variant, beta = 0).
  · La resta de la franja, la de la variant byte a byte.
Entrades: la franja de a3d_congelat_v108.py a <franja_a3d>/, la del control, i les fonts de la variant. Sortida: <franja>/ (npz amb les
mateixes claus, els JSON de l'a3d amb la regla afegida, la geometria A2) i <franja>/P1_PROTUBERANCIA.json.
Ús: p1_franja_protuberancia_v5.py <franja_a3d> <franja_control> <fonts variant> <franja> [--f-max 0.002]"""
import sys, json, shutil, hashlib, argparse
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[4]
ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('ctl'); ap.add_argument('fonts'); ap.add_argument('out'); ap.add_argument('--f-max', type=float, default=0.002)
a = ap.parse_args()
SRC, CTL, FONTS, OUT = (Path(p) if Path(p).is_absolute() else ARREL / p for p in (a.src, a.ctl, a.fonts, a.out))
assert not (OUT / 'A3C_franja_silueta.npz').exists(), f'ja existeix {OUT}/A3C_franja_silueta.npz (mai no se sobreescriu)'
OUT.mkdir(parents=True, exist_ok=True)
V = dict(np.load(SRC / 'A3C_franja_silueta.npz')); C = np.load(CTL / 'A3C_franja_silueta.npz')
assert sorted(V) == sorted(C.files), 'claus diferents'
by0, by1, bx0, bx1 = [int(v) for v in V['box']]; assert [int(v) for v in C['box']] == [by0, by1, bx0, bx1]
assert np.array_equal(V['DMIN'], C['DMIN']), 'la DMIN no és la del control (cal a3d_congelat_v108 amb A3D_CONGELA)'
cx, cy, rl = [float(v) for v in C['centre']]
# la fragilitat, del control i (només per al rebut) de la variant
EC = C['E'].astype(np.float64); EV = V['E'].astype(np.float64)
SC = np.abs(EC).sum(-1); SV = np.abs(EV).sum(-1)
fC = np.where(SC > 0, np.abs(EC[..., 1]) / np.maximum(SC, 1e-9), np.inf); fV = np.where(SV > 0, np.abs(EV[..., 1]) / np.maximum(SV, 1e-9), np.inf)
perduts = C['domini_E'] & ~V['domini_E']; guanyats = ~C['domini_E'] & V['domini_E']
fragils = C['domini_E'] & (fC < a.f_max)
congela = perduts | fragils
CLAUS = ['G', 'F', 'V', 'E', 'domini', 'domini_E', 'dins_franja', 'beta']
doc = __doc__
rep = dict(regla_v4=doc.split('· v4 (sense canvis):')[1].split('· v5, FRAGILITAT:')[0].strip(),
           regla_fragilitat_v5=doc.split('· v5, FRAGILITAT:')[1].split('· Píxels que la variant')[0].strip(), f_max=a.f_max,
           font_variant=str(SRC.relative_to(ARREL) if SRC.is_relative_to(ARREL) else SRC), control=str(CTL.relative_to(ARREL) if CTL.is_relative_to(ARREL) else CTL), perduts=[], fragils=[], guanyats=[])
dGS = np.abs(EV[..., 1] - EC[..., 1]) / np.maximum(SC, 1e-9); domC = C['domini_E'] & np.isfinite(fC)
rep['canvi_de_Gprima_pel_flat'] = {}
for lo, hi in ((0, 0.002), (0.002, 0.005), (0.005, 0.01), (0.01, 0.05), (0.05, 1.01)):
    k = domC & (fC >= lo) & (fC < hi)
    if k.any(): rep['canvi_de_Gprima_pel_flat'][f'f{lo}-{hi}'] = dict(n=int(k.sum()), mediana_dG_sobre_SigmaE=float(np.median(dGS[k])), p90_dG_sobre_SigmaE=float(np.percentile(dGS[k], 90)),
                                                                     mediana_dG_sobre_G=float(np.median(dGS[k] / np.maximum(fC[k], 1e-12))))
def fila(y, x):
    return dict(x=int(x + bx0), y=int(y + by0), dL=round(float(np.hypot(x + bx0 - cx, y + by0 - cy) - rl), 1), f_control=round(float(fC[y, x]), 6), f_variant=round(float(fV[y, x]), 6),
                **{f'{k}_variant': np.asarray(V[k][y, x]).tolist() for k in ('G', 'F', 'V', 'E', 'beta')}, **{f'{k}_control': np.asarray(C[k][y, x]).tolist() for k in ('G', 'F', 'V', 'E', 'beta')},
                domini_E_variant=bool(V['domini_E'][y, x]), NF=[int(C['NF'][y, x]), int(V['NF'][y, x])])
for y, x in zip(*np.nonzero(perduts)): rep['perduts'].append(fila(y, x))
for y, x in zip(*np.nonzero(fragils)): e = fila(y, x); e['tambe_perdut_regla_v4'] = bool(perduts[y, x]); rep['fragils'].append(e)
# a tocar del llindar: els que hi entrarien amb la f de la variant (min(f_control, f_variant) < f_max) i no hi són (NO es congelen; només el rebut)
k = C['domini_E'] & ~fragils & (np.minimum(fC, fV) < a.f_max)
rep['a_tocar_del_llindar_no_congelats'] = [dict(x=int(x + bx0), y=int(y + by0), f_control=round(float(fC[y, x]), 6), f_variant=round(float(fV[y, x]), 6),
                                                G_control=float(C['G'][y, x]), G_variant=float(V['G'][y, x])) for y, x in zip(*np.nonzero(k))]
for kk in CLAUS:
    V[kk] = np.where(congela[..., None] if V[kk].ndim == 3 else congela, C[kk], V[kk]).astype(V[kk].dtype)
if guanyats.any():
    Fg = {'G': np.load(FONTS / 'base_G.npy', mmap_mode='r'), 'F': np.load(FONTS / 'fusion_starless.npy', mmap_mode='r'), 'V': np.load(FONTS / 'vixen_starless.npy', mmap_mode='r')}
    for y, x in zip(*np.nonzero(guanyats)):
        Y, X = y + by0, x + bx0; rep['guanyats'].append(dict(x=int(X), y=int(Y), G_variant=float(V['G'][y, x]), G_fonts=float(Fg['G'][Y, X])))
        V['G'][y, x] = Fg['G'][Y, X]; V['F'][y, x] = Fg['F'][Y, X]; V['V'][y, x] = Fg['V'][Y, X, 1]
        for kk in ('domini', 'domini_E', 'dins_franja'): V[kk][y, x] = C[kk][y, x]
        V['beta'][y, x] = 0
rep['n_perduts'] = int(perduts.sum()); rep['n_fragils'] = int(fragils.sum()); rep['n_fragils_que_no_eren_perduts'] = int((fragils & ~perduts).sum())
rep['n_congelats'] = int(congela.sum()); rep['n_guanyats'] = int(guanyats.sum())
for kk in CLAUS:
    d = V[kk] != C[kk]; rep.setdefault('despres_de_la_regla', {})[kk] = dict(px_diferents_del_control=int(d.any(-1).sum() if d.ndim == 3 else d.sum()))
rep['domini_E_igual_al_control'] = bool(np.array_equal(V['domini_E'], C['domini_E']))
rep['congelats_iguals_al_control'] = bool(all(np.array_equal(V[kk][congela], C[kk][congela]) for kk in CLAUS))
np.savez_compressed(OUT / 'A3C_franja_silueta.npz', **{kk: V[kk] for kk in C.files})
for f in ('A2_GEOMETRIA.json', 'A2_geometria.npz'):
    if (SRC / f).exists(): shutil.copy2(SRC / f, OUT / f)
for f in ('A3C_FRANJA_SILUETA.json', 'A3D_FRANJA_BANDA.json'):
    j = json.loads((SRC / f).read_text())
    j['v5_regla_protuberancia'] = dict(guio='p1_franja_protuberancia_v5.py', f_max=a.f_max, n_perduts=rep['n_perduts'], n_fragils=rep['n_fragils'], n_congelats=rep['n_congelats'],
                                       n_guanyats=rep['n_guanyats'], pixels=[[int(x + bx0), int(y + by0)] for y, x in zip(*np.nonzero(congela))])
    (OUT / f).write_text(json.dumps(j, ensure_ascii=False, indent=1) + '\n')
rep['sha256_npz'] = hashlib.sha256((OUT / 'A3C_franja_silueta.npz').read_bytes()).hexdigest()
(OUT / 'P1_PROTUBERANCIA.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
print('P1 v5 · perduts', rep['n_perduts'], '· fràgils (f <', a.f_max, ')', rep['n_fragils'], [(e['x'], e['y'], e['f_control'], round(e['G_variant'], 1), '→', round(e['G_control'], 1)) for e in rep['fragils']],
      '· congelats', rep['n_congelats'], '· guanyats', rep['n_guanyats'], '· domini_E = control:', rep['domini_E_igual_al_control'], '· congelats = control:', rep['congelats_iguals_al_control'],
      '· a tocar del llindar (no congelats)', [(e['x'], e['y'], e['f_control'], e['f_variant']) for e in rep['a_tocar_del_llindar_no_congelats']], flush=True)
