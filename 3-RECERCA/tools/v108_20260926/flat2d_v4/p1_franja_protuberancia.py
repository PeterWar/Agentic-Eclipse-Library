"""p1_franja_protuberancia (V108, flat2d_v4) · ELS 2 PÍXELS DE LA PROTUBERÀNCIA: el domini de la franja, congelat al del control (com ja ho és
la vora DMIN), i on la dada de la variant no pot dir res de nou, el valor del control.
Què passa (verificador 2 i 3; ja amb la v2): a la protuberància de l'esquerra (180°, 17,8 px del limbe), a (4905, 3779) i (4897, 3785), la llum
és vermella i G' post-matriu = (M·(R, G, B)·guany)_G és la diferència petita de dos nombres grans (R' ≈ 5,6·10⁶, G' ≈ 3.600: soroll al voltant
de 0). Un canvi de flat del 0,1 % a R ja li canvia el signe; la validesa de la franja («G' > 0») el deixa fora del domini, la franja hi passa a
valer la fusió (que dins de la caixa lunar no és d'un sol instant) i la base_G hi salta de 3.590 a 107.976 (×30), R de 5,69·10⁶ a 3,17·10⁶.
Regla (sense inventar res): el domini de la franja és una MÀSCARA de geometria i es congela al del control, com la DMIN (a3d_congelat_v108).
  · Píxels que el control té al domini i la variant no (només pel signe de G'): hi van els valors de la franja del CONTROL (G, F, V, E, domini,
    domini_E, dins_franja, beta). Allà G' ≈ 0 ± soroll i la dada no pot dir res de nou: es conserva la V107.
  · Píxels que la variant hi afegeix i el control no: fora del domini, com al control (G, F, V = les fonts de la variant, beta = 0).
  · La resta de la franja, la de la variant byte a byte.
Entrades: la franja de a3d_congelat_v108.py a <franja_a3d>/, la del control, i les fonts de la variant. Sortida: <franja>/ (npz amb les
mateixes claus, els JSON de l'a3d amb la regla afegida, la geometria A2) i <franja>/P1_PROTUBERANCIA.json.
Ús: p1_franja_protuberancia.py <franja_a3d> <franja_control> <fonts variant> <franja>"""
import sys, json, shutil, hashlib
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[4]
SRC, CTL, FONTS, OUT = (Path(p) if Path(p).is_absolute() else ARREL / p for p in sys.argv[1:5])
assert not (OUT / 'A3C_franja_silueta.npz').exists(), f'ja existeix {OUT}/A3C_franja_silueta.npz (mai no se sobreescriu)'
OUT.mkdir(parents=True, exist_ok=True)
V = dict(np.load(SRC / 'A3C_franja_silueta.npz')); C = np.load(CTL / 'A3C_franja_silueta.npz')
assert sorted(V) == sorted(C.files), 'claus diferents'
by0, by1, bx0, bx1 = [int(v) for v in V['box']]; assert [int(v) for v in C['box']] == [by0, by1, bx0, bx1]
assert np.array_equal(V['DMIN'], C['DMIN']), 'la DMIN no és la del control (cal a3d_congelat_v108 amb A3D_CONGELA)'
perduts = C['domini_E'] & ~V['domini_E']; guanyats = ~C['domini_E'] & V['domini_E']
CLAUS = ['G', 'F', 'V', 'E', 'domini', 'domini_E', 'dins_franja', 'beta']
rep = dict(regla=__doc__.split('Regla (sense inventar res):')[1].split('Entrades:')[0].strip(), font_variant=str(SRC.relative_to(ARREL)), control=str(CTL.relative_to(ARREL)),
           perduts=[], guanyats=[])
for y, x in zip(*np.nonzero(perduts)):
    e = dict(x=int(x + bx0), y=int(y + by0), **{f'{k}_variant': np.asarray(V[k][y, x]).tolist() for k in ('G', 'F', 'V', 'E', 'beta')}, **{f'{k}_control': np.asarray(C[k][y, x]).tolist() for k in ('G', 'F', 'V', 'E', 'beta')},
             NF=[int(C['NF'][y, x]), int(V['NF'][y, x])], dL=float(np.hypot(x + bx0 - float(C['centre'][0]), y + by0 - float(C['centre'][1])) - float(C['centre'][2])))
    rep['perduts'].append(e)
for k in CLAUS:
    V[k] = np.where(perduts[..., None] if V[k].ndim == 3 else perduts, C[k], V[k]).astype(V[k].dtype)
if guanyats.any():
    Fg = {'G': np.load(FONTS / 'base_G.npy', mmap_mode='r'), 'F': np.load(FONTS / 'fusion_starless.npy', mmap_mode='r'), 'V': np.load(FONTS / 'vixen_starless.npy', mmap_mode='r')}
    for y, x in zip(*np.nonzero(guanyats)):
        Y, X = y + by0, x + bx0; rep['guanyats'].append(dict(x=int(X), y=int(Y), G_variant=float(V['G'][y, x]), G_fonts=float(Fg['G'][Y, X])))
        V['G'][y, x] = Fg['G'][Y, X]; V['F'][y, x] = Fg['F'][Y, X]; V['V'][y, x] = Fg['V'][Y, X, 1]
        for k in ('domini', 'domini_E', 'dins_franja'): V[k][y, x] = C[k][y, x]
        V['beta'][y, x] = 0
rep['n_perduts'] = int(perduts.sum()); rep['n_guanyats'] = int(guanyats.sum())
for k in CLAUS:
    d = V[k] != C[k]; rep.setdefault('despres_de_la_regla', {})[k] = dict(px_diferents_del_control=int(d.any(-1).sum() if d.ndim == 3 else d.sum()))
rep['domini_E_igual_al_control'] = bool(np.array_equal(V['domini_E'], C['domini_E']))
np.savez_compressed(OUT / 'A3C_franja_silueta.npz', **{k: V[k] for k in C.files})
for f in ('A2_GEOMETRIA.json', 'A2_geometria.npz'):
    if (SRC / f).exists(): shutil.copy2(SRC / f, OUT / f)
for f in ('A3C_FRANJA_SILUETA.json', 'A3D_FRANJA_BANDA.json'):
    j = json.loads((SRC / f).read_text()); j['v4_regla_protuberancia'] = dict(guio='p1_franja_protuberancia.py', n_perduts=rep['n_perduts'], n_guanyats=rep['n_guanyats'],
                                                                                 pixels=[[e['x'], e['y']] for e in rep['perduts']])
    (OUT / f).write_text(json.dumps(j, ensure_ascii=False, indent=1) + '\n')
rep['sha256_npz'] = hashlib.sha256((OUT / 'A3C_franja_silueta.npz').read_bytes()).hexdigest()
(OUT / 'P1_PROTUBERANCIA.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
print('P1 · perduts', rep['n_perduts'], [(e['x'], e['y'], round(e['G_variant'], 1), '→', round(e['G_control'], 1)) for e in rep['perduts']], '· guanyats', rep['n_guanyats'],
      '· domini_E = control:', rep['domini_E_igual_al_control'], flush=True)
