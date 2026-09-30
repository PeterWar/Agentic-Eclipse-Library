"""m9_v5_contra_v4 (V108, flat2d_v5) · ON CANVIA LA v5 RESPECTE DE LA v4, a cada etapa, i si FORA DELS LLOCS DE L'ENCÀRREC és la v4 bit a bit.
Llocs (px del llenç):
  · POLS MOGUDA: la regió on l'APILAT DE LA VIXEN canvia (v5 ≠ v4 a qualsevol canal; el flat és fix al sensor i els fotogrames es mouen, per
    això la petjada al llenç és més ampla que al sensor). Primer es comprova que cada component d'aquesta regió és a ≤ 150 px del centre d'una
    de les 5 estructures de l'encàrrec (si no, s'atura: voldria dir que la C ha canviat on no tocava).
  · PROTUBERÀNCIA: els píxels que la regla de fragilitat congela (cadena/flat2d_v5/franja/P1_PROTUBERANCIA.json, «fragils»).
Per a cada producte (mateixa forma a la v4 i a la v5): n de píxels diferents (NaN = NaN compta com a igual) i, per a cadascun, la distància al
lloc més proper: n a > 0, > 50, > 150 i > 300 px, i quin lloc és el més proper. Magnitud: p99 i màxim de |Δ| (ln per a les dades en coma
flotant positives, DN per als u16).
v4: 4-RESULTATS/v108_20260926/flat2d_v4 i cadena/flat2d_v4 (el que s'hi queda) i, per a la linealitzada que no s'hi queda, la base, els filtres
i l'estat, la Paperera (~/.Trash/Eclipse_V108_flat2d_v4_intermedis_20260927/cadena/flat2d_v4: filtres_v108, estat_v108, base_100113,
lineal/*_100113|100114 = els de la v4 final, segons el manifest MOVIMENTS_PAPERERA_FLAT2D_V4.jsonl). Tot, només lectura.
Sortida: 4-RESULTATS/v108_20260926/flat2d_v5/M9_V5_CONTRA_V4.json (s'hi afegeix cada etapa) i M9_LLOCS.npz (la màscara dels llocs, a 1/1).
Ús: m9_v5_contra_v4.py fonts|cadena|compost|tot"""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
from scipy import ndimage as ndi
A = Path(__file__).resolve().parents[4]; R5 = A / '4-RESULTATS/v108_20260926/flat2d_v5'; R4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'
C5 = A / '4-RESULTATS/v108_20260926/cadena/flat2d_v5'; C4 = A / '4-RESULTATS/v108_20260926/cadena/flat2d_v4'
T4 = Path.home() / '.Trash/Eclipse_V108_flat2d_v4_intermedis_20260927/cadena/flat2d_v4'
H, W = 7506, 10551; OUTJ = R5 / 'M9_V5_CONTRA_V4.json'; t0 = time.time()
POLS = {73: (5860, 5354), 2: (2864, 2088), 32: (3898, 2503), 66: (6408, 4793), 57: (6149, 4386)}
etapa = sys.argv[1] if len(sys.argv) > 1 else 'tot'
RES = json.loads(OUTJ.read_text()) if OUTJ.exists() else {}
def desa(): OUTJ.write_text(json.dumps(RES, ensure_ascii=False, indent=1) + '\n')
def diff_mask(a, b, fer_mag=True):
    """a, b: arrays (mmap) de la mateixa forma, amb el pla del llenç (H, W) a les dues primeres dimensions espacials. Torna (màscara 2D, mags)."""
    sp = a.shape; m = np.zeros(sp[:2], bool); mags = []
    for y0 in range(0, sp[0], 512):
        x = np.asarray(a[y0:y0 + 512]); y = np.asarray(b[y0:y0 + 512]); d = x != y
        if np.issubdtype(x.dtype, np.floating): d &= ~(np.isnan(x) & np.isnan(y))
        dd = d.reshape(d.shape[0], d.shape[1], -1).any(-1) if d.ndim > 2 else d
        m[y0:y0 + 512] = dd
        if fer_mag and d.any():
            xs, ys = x[d].astype(np.float64), y[d].astype(np.float64)
            if np.issubdtype(x.dtype, np.floating):
                ok = (xs > 0) & (ys > 0) & np.isfinite(xs) & np.isfinite(ys); mags.append(np.abs(np.log(ys[ok] / xs[ok])))
            else: mags.append(np.abs(ys - xs))
    mg = np.concatenate(mags) if mags else np.zeros(0)
    return m, mg
# ---------------------------------------------------------------------------------------------------------------------------------------
# els llocs
# ---------------------------------------------------------------------------------------------------------------------------------------
LL = R5 / 'M9_LLOCS.npz'
if LL.exists():
    z = np.load(LL); LLOC = z['lloc']
else:
    mv, _ = diff_mask(np.load(R5 / 'apilats/vixen_total.npy', mmap_mode='r'), np.load(R4 / 'apilats/vixen_total.npy', mmap_mode='r'), fer_mag=False)
    md, _ = diff_mask(np.load(R5 / 'apilats/vixen_den.npy', mmap_mode='r'), np.load(R4 / 'apilats/vixen_den.npy', mmap_mode='r'), fer_mag=False)
    mv |= md
    n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.dilate(mv.astype(np.uint8), np.ones((11, 11), np.uint8)), 8)
    LLOC = np.zeros((H, W), np.uint8); comp = []; ids = list(POLS)
    for i in range(1, n):
        c = cen[i]; ds = {k: float(np.hypot(c[0] - v[0], c[1] - v[1])) for k, v in POLS.items()}; k = min(ds, key=ds.get)
        x0, y0, w_, h_ = [int(v) for v in st[i, :4]]
        comp.append(dict(centre=[round(float(c[0]), 1), round(float(c[1]), 1)], caixa_xywh=[x0, y0, w_, h_], px=int((mv & (lab == i)).sum()), estructura=k, dist_al_centre=round(ds[k], 1)))
        if ds[k] > 150: sys.exit(f'ATURAT: l’apilat de la Vixen canvia a {c} (a {ds[k]:.0f} px de la pols moguda més propera)')
        LLOC[(lab == i) & mv] = 1 + ids.index(k)
    fr = json.loads((C5 / 'franja/P1_PROTUBERANCIA.json').read_text())
    for e in fr['fragils']: LLOC[e['y'], e['x']] = 6
    np.savez_compressed(LL, lloc=LLOC, ids=np.array(ids + [0]))
    RES['llocs'] = dict(estructures_pols_moguda=dict(zip([str(k) for k in ids], [list(v) for v in POLS.values()])), components_apilat_vixen=comp,
                        px_pols_moguda=int(((LLOC >= 1) & (LLOC <= 5)).sum()),
                        protuberancia_fragils=[[e['x'], e['y']] for e in fr['fragils']], codi=dict(zip(['1', '2', '3', '4', '5', '6'], [f'pols {k}' for k in ids] + ['protuberància'])))
    desa(); print('llocs', RES['llocs']['px_pols_moguda'], 'px de pols moguda,', len(comp), 'components;', len(fr['fragils']), 'px de la protuberància', f'{time.time()-t0:.0f}s', flush=True)
DIST, IND = ndi.distance_transform_edt(LLOC == 0, return_indices=True); LABL = LLOC[IND[0], IND[1]]; del IND
NOMS = {1: 'pols 73', 2: 'pols 2', 3: 'pols 32', 4: 'pols 66', 5: 'pols 57', 6: 'protuberància'}
def estad(m, mg, off=(0, 0)):
    n = int(m.sum()); o = dict(n_px_diferents=n)
    if n == 0: o['igual_bit_a_bit'] = True; return o
    o['igual_bit_a_bit'] = False; ys, xs = np.nonzero(m); ys = ys + off[0]; xs = xs + off[1]; d = DIST[ys, xs]; lb = LABL[ys, xs]
    o.update(dist_max_px=round(float(d.max()), 1), n_a_dist_mes_0=int((d > 0).sum()), n_a_dist_mes_50=int((d > 50).sum()), n_a_dist_mes_150=int((d > 150).sum()), n_a_dist_mes_300=int((d > 300).sum()),
             caixa_xyxy=[int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())],
             per_lloc={NOMS[int(k)]: dict(n=int((lb == k).sum()), dist_max_px=round(float(d[lb == k].max()), 1)) for k in np.unique(lb)})
    if mg.size: o.update(mag_p99=float(np.percentile(mg, 99)), mag_max=float(mg.max()))
    return o
def compara(p5, p4, off=(0, 0), nom=None):
    nom = nom or str(p5.relative_to(A))
    if not p4.exists(): return nom, dict(error=f'no hi és la v4: {p4}')
    if p5.suffix == '.npz':
        a, b = np.load(p5), np.load(p4); o = dict(claus_diferents=[], per_clau={})
        if sorted(a.files) != sorted(b.files): o['claus_no_iguals'] = [sorted(a.files), sorted(b.files)]
        for k in a.files:
            x, y = a[k], b[k]
            if x.shape != y.shape or x.dtype != y.dtype: o['claus_diferents'].append(k); o['per_clau'][k] = dict(forma=[list(x.shape), list(y.shape)]); continue
            if x.ndim >= 2 and x.shape[:2] == (1400, 1400):
                m, mg = diff_mask(x, y); e = estad(m, mg, off)
            else:
                eq = x.tobytes() == y.tobytes(); e = dict(igual_bit_a_bit=bool(eq))
            if not e['igual_bit_a_bit']: o['claus_diferents'].append(k); o['per_clau'][k] = e
        o['igual_bit_a_bit'] = not o['claus_diferents']; return nom, o
    a, b = np.load(p5, mmap_mode='r'), np.load(p4, mmap_mode='r')
    if a.shape != b.shape or a.dtype != b.dtype: return nom, dict(error='forma o tipus diferent', forma=[list(a.shape), list(b.shape)])
    if a.ndim == 4:        # fotogrames de la caixa lunar: (n, 1400, 1400, 3) → la unió de tots els fotogrames
        m = np.zeros(a.shape[1:3], bool); mags = []
        for i in range(a.shape[0]): mi, mg = diff_mask(a[i], b[i]); m |= mi; mags.append(mg)
        e = estad(m, np.concatenate(mags), off); e['n_fotogrames_diferents'] = int(sum(1 for i in range(a.shape[0]) if not np.array_equal(a[i], b[i], equal_nan=True))); return nom, e
    if a.ndim == 3 and a.shape[1:] == (1400, 1400):
        m = np.zeros(a.shape[1:], bool); mags = []
        for i in range(a.shape[0]): mi, mg = diff_mask(a[i], b[i]); m |= mi; mags.append(mg)
        return nom, estad(m, np.concatenate(mags), off)
    m, mg = diff_mask(a, b); return nom, estad(m, mg, off)
def fa(llista, clau):
    out = RES.setdefault(clau, {})
    for p5, p4, off in llista:
        nom, o = compara(p5, p4, off); out[nom] = o
        print(clau, nom, json.dumps({k: v for k, v in o.items() if k not in ('per_clau',)})[:400], f'{time.time()-t0:.0f}s', flush=True)
    desa()
BOX = (3077, 4677)
if etapa in ('fonts', 'tot'):
    # la C (al RAW): quants píxels canvien (f0 ja comprova que tots són a la petjada de la pols moguda)
    oC = {}
    for f in ('VIXEN', 'SONYTOT_A', 'SONYTOT_B'):
        a, b = np.load(R5 / f'flat2d/{f}_flat2d_v5.npz')['C'], np.load(R4 / f'flat2d/{f}_flat2d_v4.npz')['C']; oC[f] = dict(igual_bit_a_bit=bool(np.array_equal(a, b)), n_px_RAW_diferents=int((a != b).sum()))
    RES['C_RAW'] = oC; print('C', oC, flush=True)
    L = [(R5 / f'apilats/{f}', R4 / f'apilats/{f}', (0, 0)) for f in ('vixen_total.npy', 'vixen_den.npy', 'sony_A_total.npy', 'sony_A_den.npy', 'cau/sony_B_total_v42.npy', 'cau/sony_B_weights_v42.npy')]
    L += [(R5 / f'limb_frames_flat2d/{f}', R4 / f'limb_frames_flat2d/{f}', BOX) for f in ('numerator.npy', 'weight.npy', 'distance_model.npy')]
    S5, S4 = R5 / 'fusio/d4/products/sources', R4 / 'fusio/d4/products/sources'
    L += [(S5 / f, S4 / f, (0, 0)) for f in ('base_G.npy', 'fusion_starless.npy', 'vixen_starless.npy', 'sony_starless.npy', 'support.npy', 'star_footprints.npy')]
    fa(L, 'fonts')
    st = {}
    for p in sorted(S5.glob('*.npz')):
        nom, o = compara(p, S4 / p.name); st[p.name] = o['igual_bit_a_bit']
    RES['fonts_estrelles_npz'] = dict(n=len(st), iguals=sum(st.values()), diferents=[k for k, v in st.items() if not v]); desa(); print('estrelles', RES['fonts_estrelles_npz'], flush=True)
if etapa in ('cadena', 'tot'):
    L = [(C5 / 'franja/A3C_franja_silueta.npz', C4 / 'franja/A3C_franja_silueta.npz', BOX)]
    L += [(C5 / f'lineal/{f}', C4 / f'lineal/{f}', (0, 0)) for f in ('base_G.npy', 'fusion_starless.npy')]
    L += [(C5 / 'lineal/vixen_starless.npy', T4 / 'lineal/vixen_starless.npy_100113', (0, 0))]
    L += [(C5 / f'base/{f}', T4 / f'base_100113/{f}', (0, 0)) for f in ('base_v108_u16.npy', 'base_v108_u16_alfa.npy', 'base_v108_final_u16.npy')]
    L += [(p, T4 / 'filtres_v108' / p.name, (0, 0)) for p in sorted((C5 / 'filtres_v108').glob('*.npy'))]
    L += [(p, T4 / 'estat_v108' / p.name, (0, 0)) for p in sorted((C5 / 'estat_v108').glob('*.npy'))]
    fa(L, 'cadena')
if etapa in ('compost', 'tot'):
    fa([(R5 / 'compost_flat2d_v5.npy', R4 / 'compost_flat2d_v4.npy', (0, 0))], 'compost')
# resum: per etapa, els productes que canvien i la distància màxima dels canvis als llocs
res = {}
for et in ('fonts', 'cadena', 'compost'):
    if et not in RES: continue
    cv = {k: v for k, v in RES[et].items() if not v.get('igual_bit_a_bit', False)}
    res[et] = dict(n_productes=len(RES[et]), n_iguals_bit_a_bit=len(RES[et]) - len(cv),
                   canvien={k: dict(n=v.get('n_px_diferents'), dist_max_px=v.get('dist_max_px'), n_mes_150=v.get('n_a_dist_mes_150'), n_mes_300=v.get('n_a_dist_mes_300'),
                                    claus=v.get('claus_diferents')) for k, v in cv.items()})
RES['resum'] = res; desa(); print(json.dumps(res, ensure_ascii=False)[:3000]); print('FET', f'{time.time()-t0:.0f}s')
