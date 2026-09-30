"""c8 (V108, cadena) · Compara els productes d'una variant de la cadena V108 amb les referències, i diu QUINES CAPES CANVIARIEN a la V108:
  · la franja (A3C_franja_silueta.npz, clau per clau) i la linealitzada (base_G, fusion/vixen/sony_starless, support) contra la variant E;
  · base final (capa 3) contra 4-RESULTATS/v103_banda_20260926/E/base_v103/base_v103_final_u16.npy (la de la V104–V107);
  · els 16 ràsters de filtre i les seves alfes (filtres_std i filtres_v108) contra E/filtres_v103/filtres (la sortida f3 de la variant E);
  · l'estat (L3_RGB, L{41–56}_G i _alfa) contra l'estat de la V105 (4-RESULTATS/v105_limbe_20260926/claude/estat_v105); la 56, contra el canal
    que es va posar al PSB (L56_G_V105_psb.npy: la fosa de la REC sobre q(56));
  · I EL QUE COMPTA: q(estat) (la quantització del Photoshop) contra els canals de la V107 de Pere: una capa «canvia» si q(ràster nou) ≠ V107.
Per a cada comparació: iguals (byte a byte), px diferents, |dif| màxima i la caixa dels píxels diferents (x0, y0, x1, y1).
Ús: c8_compara_v108.py <carpeta de la variant> [--sense-v107]. Escriu <variant>/C8_COMPARA.json. Només lectura, fora del json."""
import sys, json, time, argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from comu_v108 import ARREL, PSB, V107, TAG, FILTRES, q_blocs, rel
ap = argparse.ArgumentParser(); ap.add_argument('variant'); ap.add_argument('--sense-v107', action='store_true'); A = ap.parse_args(); t0 = time.time()
R = Path(A.variant); E = ARREL / '4-RESULTATS/v103_banda_20260926/E'; E105 = ARREL / '4-RESULTATS/v105_limbe_20260926/claude'


def compara(a, b, pas=1024):
    """a, b: arrays 2D (o mmap) del mateix format → dict(iguals, px, max, caixa)."""
    a = np.load(a, mmap_mode='r') if isinstance(a, (str, Path)) else a; b = np.load(b, mmap_mode='r') if isinstance(b, (str, Path)) else b
    if a.shape != b.shape: return dict(iguals=False, motiu=f'formes {a.shape} ≠ {b.shape}')
    px = 0; mx = 0; ys = []; xs = []
    for y in range(0, a.shape[0], pas):
        if a.dtype.kind == 'f':
            xa, xb = np.asarray(a[y:y + pas], np.float64), np.asarray(b[y:y + pas], np.float64); d = np.abs(xa - xb); d[np.isnan(xa) & np.isnan(xb)] = 0; d[np.isnan(d)] = np.inf
        else: d = np.abs(np.asarray(a[y:y + pas], np.int32) - np.asarray(b[y:y + pas], np.int32))
        if d.ndim == 3: d = d.max(-1)
        nz = d > 0; n = int(nz.sum())
        if n:
            px += n; mx = max(mx, float(d.max()) if a.dtype.kind == 'f' else int(d.max())); yy, xx = np.nonzero(nz); ys += [y + yy.min(), y + yy.max()]; xs += [xx.min(), xx.max()]
    return dict(iguals=px == 0, px=px, max=mx, caixa=[int(min(xs)), int(min(ys)), int(max(xs)) + 1, int(max(ys)) + 1] if px else None)


rep = dict(variant=rel(R), referencies=dict(base=rel(E / 'base_v103/base_v103_final_u16.npy'), filtres=rel(E / 'filtres_v103/filtres'), estat=rel(E105 / 'estat_v105'),
           L56_psb=rel(E105 / 'L56_G_V105_psb.npy'), v107=rel(V107)))
rep['franja'] = {}
if (R / 'franja/A3C_franja_silueta.npz').exists():
    Zn = np.load(R / 'franja/A3C_franja_silueta.npz'); Ze = np.load(E / 'lineal_v103_franja/A3C_franja_silueta.npz')
    for k in sorted(set(Zn.files) | set(Ze.files)):
        if k not in Zn.files or k not in Ze.files: rep['franja'][k] = dict(iguals=False, motiu='clau absent'); continue
        x, y = Zn[k], Ze[k]
        rep['franja'][k] = dict(iguals=bool(x.shape == y.shape and np.array_equal(x, y, equal_nan=x.dtype.kind == 'f')), max=float(np.nanmax(np.abs(x.astype(np.float64) - y.astype(np.float64)))) if x.shape == y.shape and x.size else None)
rep['lineal'] = {f: compara(R / 'lineal' / f, E / 'lineal_v103' / f) for f in ('base_G.npy', 'fusion_starless.npy', 'vixen_starless.npy', 'sony_starless.npy', 'support.npy') if (R / 'lineal' / f).exists()}
rep['base'] = compara(R / 'base/base_v108_final_u16.npy', E / 'base_v103/base_v103_final_u16.npy')
for nom in ('filtres_std/filtres', 'filtres_v108'):
    d = R / nom; out = {}
    if d.exists():
        for lid, tag in TAG.items():
            for suf in ('_u16', '_alfa_u16'):
                f = d / f'{tag}{suf}.npy'
                if f.exists(): out[f'{lid} {tag}{suf}'] = compara(f, E / 'filtres_v103/filtres' / f'{tag}{suf}.npy')
    rep[nom] = out
EST = R / 'estat_v108'; rep['estat'] = {}
if EST.exists():
    rep['estat']['L3_RGB'] = compara(EST / 'L3_RGB.npy', E105 / 'estat_v105/L3_RGB.npy'); rep['estat']['L3_alfa'] = compara(EST / 'L3_alfa.npy', E105 / 'estat_v105/L3_alfa.npy')
    for lid in FILTRES:
        rep['estat'][f'L{lid}_G'] = compara(EST / f'L{lid}_G.npy', (E105 / 'L56_G_V105_psb.npy') if lid == 56 else (E105 / f'estat_v105/L{lid}_G.npy'))
        rep['estat'][f'L{lid}_alfa'] = compara(EST / f'L{lid}_alfa.npy', E105 / f'estat_v105/L{lid}_alfa.npy')
if EST.exists() and not A.sense_v107:
    p = PSB(str(V107))
    def contra_v107(lid):
        L = p.layer(lid); assert (L['left'], L['top'], L['right'], L['bottom']) == (0, 0, p.width, p.height), lid
        o = {}
        if lid == 3:
            B = np.load(EST / 'L3_RGB.npy', mmap_mode='r')
            for k in (0, 1, 2): o[f'canal_{k}'] = compara(q_blocs(B[..., k]), p.channel(3, k)[0])
            o['alfa'] = compara(q_blocs(np.load(EST / 'L3_alfa.npy', mmap_mode='r')), p.channel(3, -1)[0])
        else:
            c = [p.channel(lid, k)[0] for k in (0, 1, 2)]; o['v107_gris'] = bool(np.array_equal(c[0], c[1]) and np.array_equal(c[1], c[2]))
            o['G'] = compara(q_blocs(np.load(EST / f'L{lid}_G.npy', mmap_mode='r')), c[1]); del c
            o['alfa'] = compara(q_blocs(np.load(EST / f'L{lid}_alfa.npy', mmap_mode='r')), p.channel(lid, -1)[0])
        o['canvia'] = not all(v['iguals'] for k, v in o.items() if isinstance(v, dict))
        return lid, o
    with ThreadPoolExecutor(4) as ex: res = dict(ex.map(contra_v107, [3] + FILTRES))
    rep['v107'] = {str(k): res[k] for k in [3] + FILTRES}; rep['capes_que_canvien'] = [k for k in [3] + FILTRES if res[k]['canvia']]
rep['segons'] = round(time.time() - t0, 1)
(R / 'C8_COMPARA.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n')
iguals = lambda dct: sum(v.get('iguals', False) for v in dct.values())
print('franja igual a E:', iguals(rep['franja']), 'de', len(rep['franja']), '· linealitzada igual a E:', iguals(rep['lineal']), 'de', len(rep['lineal']))
print('base igual a E:', rep['base']['iguals'], '· filtres_std iguals a E:', iguals(rep.get('filtres_std/filtres', {})), 'de', len(rep.get('filtres_std/filtres', {})),
      '· filtres_v108 iguals a E:', iguals(rep.get('filtres_v108', {})), 'de', len(rep.get('filtres_v108', {})), '· estat igual a la V105:', iguals(rep['estat']), 'de', len(rep['estat']))
if 'v107' in rep: print('capes que canviarien a la V108 (q(estat) ≠ V107):', rep['capes_que_canvien'] or 'CAP')
print('FET', rep['segons'], 's')
