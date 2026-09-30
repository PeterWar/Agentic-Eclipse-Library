"""z3 (verificador adversari 5) · FORA DELS LLOCS, LA v5 ÉS LA v4 BIT A BIT? Guió propi, etapa per etapa.
Llocs (propis): els píxels on l'apilat de la Vixen v5 difereix de la v4 (qualsevol canal) + els 7 fràgils de la protuberància (recalculats a z2).
Per a cada fitxer .npy/.npz de cada etapa (C, apilats, caixa lunar, fonts d4, lineal, franja, base, filtres, estat, fila_REC, compost):
  píxels diferents (bit a bit; NaN = NaN), màxim |dif|, i si la forma és la del llenç, la distància màxima dels píxels diferents als llocs i els
  píxels diferents a > 150 i > 300 px. Al compost, p99 i màxim de |ln(v5/v4)| a > 150 px per anells de R☉.
C (RAW): píxels diferents per subplà, components connexos i, com a prova de la regla, el pas baix (σ 6 subplans) de ln C dins del nucli
de cada component (v4 contra v5; la regla v5 = FONS − G(FONS) hi ha de deixar el pas baix a ~0).
Sortida: 4-RESULTATS/v108_20260926/verifica5_flat2d/Z3_V5_CONTRA_V4.json (només lectura; ~8 GB)."""
import json, time, zipfile
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica5_flat2d'; V8 = A / '4-RESULTATS/v108_20260926'; CAD = V8 / 'cadena'
T4 = Path.home() / '.Trash/Eclipse_V108_flat2d_v4_intermedis_20260927'; T5 = Path.home() / '.Trash/Eclipse_V108_flat2d_v5_intermedis_20260927'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603
F4, F5 = V8 / 'flat2d_v4', V8 / 'flat2d_v5'
t0 = time.time(); R = {}
FRAG = [(4897, 3785), (4898, 3784), (4904, 3779), (4905, 3779), (4906, 3779), (4906, 3780), (4907, 3780)]
# llocs
a = np.load(F4 / 'apilats/vixen_total.npy', mmap_mode='r'); b = np.load(F5 / 'apilats/vixen_total.npy', mmap_mode='r'); SITE = np.zeros((H, W), bool)
for y0 in range(0, H, 800):
    x, y = np.asarray(a[y0:y0 + 800]), np.asarray(b[y0:y0 + 800]); SITE[y0:y0 + 800] = (~((x == y) | (np.isnan(x) & np.isnan(y)))).any(-1)
for x_, y_ in FRAG: SITE[y_, x_] = True
R['llocs_px'] = int(SITE.sum())
DIST = cv2.distanceTransform((~SITE).astype(np.uint8), cv2.DIST_L2, 5)
n, lab, st, cen = cv2.connectedComponentsWithStats(cv2.dilate(SITE.astype(np.uint8), np.ones((25, 25), np.uint8)), 8)
R['llocs_components'] = [dict(centre=[round(float(cen[i][0])), round(float(cen[i][1]))], area=int(st[i, 4])) for i in range(1, n)]
print('llocs', R['llocs_px'], R['llocs_components'], flush=True)
def compara(pa, pb, key=None):
    xa = np.load(pa, mmap_mode='r') if key is None else np.load(pa)[key]; xb = np.load(pb, mmap_mode='r') if key is None else np.load(pb)[key]
    if xa.shape != xb.shape: return dict(forma=[list(xa.shape), list(xb.shape)])
    o = dict(forma=list(xa.shape), dtype=str(xa.dtype))
    if xa.dtype.kind not in 'fiub': o['iguals'] = bool(np.array_equal(xa, xb)); return o
    espai = xa.ndim >= 2 and xa.shape[:2] == (H, W)
    nd = 0; mx = 0.0; dmax = 0.0; n150 = 0; n300 = 0; step = 600 if espai else max(1, xa.shape[0])
    for y0 in range(0, xa.shape[0] if xa.ndim else 1, step):
        u = np.asarray(xa[y0:y0 + step]) if xa.ndim else np.asarray(xa); v = np.asarray(xb[y0:y0 + step]) if xa.ndim else np.asarray(xb)
        d = ~((u == v) | (np.isnan(u) & np.isnan(v))) if u.dtype.kind == 'f' else (u != v)
        if not d.any(): continue
        with np.errstate(invalid='ignore'):
            dd = np.abs(u.astype(np.float64) - v.astype(np.float64)); dd = dd[d & np.isfinite(dd)]
        mx = max(mx, float(dd.max()) if dd.size else float('nan'))
        if espai:
            dp = d.reshape(d.shape[0], W, -1).any(-1); ds = DIST[y0:y0 + step][dp]; nd += int(dp.sum()); dmax = max(dmax, float(ds.max())); n150 += int((ds > 150).sum()); n300 += int((ds > 300).sum())
        else: nd += int(d.sum())
    o.update(px_diferents=nd, max_abs_dif=mx)
    if espai: o.update(dist_max_als_llocs=round(dmax, 1), px_a_mes_150=n150, px_a_mes_300=n300)
    return o
def etapa(nom, parells):
    res = {}
    for k, (pa, pb) in parells.items():
        try:
            if pa.suffix == '.npz':
                z = np.load(pa); res[k] = {kk: compara(pa, pb, kk) for kk in z.files}
            else: res[k] = compara(pa, pb)
        except Exception as e: res[k] = dict(error=repr(e)[:200])
    R[nom] = res
    resum = {k: (v if 'px_diferents' not in v else {kk: v[kk] for kk in ('px_diferents', 'dist_max_als_llocs', 'px_a_mes_150', 'px_a_mes_300') if kk in v}) for k, v in res.items()}
    print(nom, json.dumps(resum)[:3000], f'{time.time()-t0:.0f}s', flush=True)
    (OUT / 'Z3_V5_CONTRA_V4.json').write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str))
# 1 · C
etapa('C', {f: (F4 / f'flat2d/{f}_flat2d_v4.npz', F5 / f'flat2d/{f}_flat2d_v5.npz') for f in ('VIXEN', 'SONYTOT_A', 'SONYTOT_B')})
c4 = np.load(F4 / 'flat2d/VIXEN_flat2d_v4.npz')['C'].astype(np.float64); c5 = np.load(F5 / 'flat2d/VIXEN_flat2d_v5.npz')['C'].astype(np.float64)
RC = {}
for nom, (dy, dx) in (('p00', (0, 0)), ('p01', (0, 1)), ('p10', (1, 0)), ('p11', (1, 1))):
    u = np.log(np.maximum(c4[dy::2, dx::2], 1e-9)).astype(np.float32); v = np.log(np.maximum(c5[dy::2, dx::2], 1e-9)).astype(np.float32); d = (u != v)
    nn, lb, stt, cc = cv2.connectedComponentsWithStats(cv2.dilate(d.astype(np.uint8), np.ones((5, 5), np.uint8)), 8)
    comps = []
    for i in range(1, nn):
        x0, y0, w, h = stt[i, :4]; core = cv2.erode((lb[y0:y0 + h, x0:x0 + w] == i).astype(np.uint8), np.ones((15, 15), np.uint8)) > 0
        pad = 40; ya, yb, xa, xb = max(0, y0 - pad), y0 + h + pad, max(0, x0 - pad), x0 + w + pad
        g4 = cv2.GaussianBlur(u[ya:yb, xa:xb], (0, 0), 6)[y0 - ya:y0 - ya + h, x0 - xa:x0 - xa + w]; g5 = cv2.GaussianBlur(v[ya:yb, xa:xb], (0, 0), 6)[y0 - ya:y0 - ya + h, x0 - xa:x0 - xa + w]
        e = dict(centre_subpla=[round(float(cc[i][0])), round(float(cc[i][1]))], px=int(d[y0:y0 + h, x0:x0 + w].sum()), nucli_px=int(core.sum()))
        if core.sum() > 20:
            e.update(rms_pasbaix_s6_v4_1e4=round(1e4 * float(np.sqrt((g4[core].astype(np.float64) ** 2).mean())), 2), rms_pasbaix_s6_v5_1e4=round(1e4 * float(np.sqrt((g5[core].astype(np.float64) ** 2).mean())), 2),
                     rms_lnC_v4_1e4=round(1e4 * float(np.sqrt((u[y0:y0 + h, x0:x0 + w][core].astype(np.float64) ** 2).mean())), 2), rms_lnC_v5_1e4=round(1e4 * float(np.sqrt((v[y0:y0 + h, x0:x0 + w][core].astype(np.float64) ** 2).mean())), 2))
        comps.append(e)
    RC[nom] = dict(px_diferents=int(d.sum()), components=comps)
R['C_VIXEN_regla'] = RC; del c4, c5
print('C regla', json.dumps(RC)[:3000], flush=True)
# 2 · apilats i caixa lunar
etapa('apilats', {f: (F4 / 'apilats' / f, F5 / 'apilats' / f) for f in ('vixen_total.npy', 'vixen_den.npy', 'sony_A_total.npy', 'sony_A_den.npy', 'cau/sony_B_total_v42.npy', 'cau/sony_B_weights_v42.npy')})
etapa('caixa_lunar', {p.name: (p, F5 / 'limb_frames_flat2d' / p.name) for p in sorted((F4 / 'limb_frames_flat2d').glob('*.npy'))})
# 3 · fonts d4 (totes)
s4 = F4 / 'fusio/d4/products/sources'; s5 = F5 / 'fusio/d4/products/sources'
n4 = sorted(p.name for p in s4.iterdir()); n5 = sorted(p.name for p in s5.iterdir()); R['fonts_noms_iguals'] = n4 == n5; R['fonts_n'] = [len(n4), len(n5)]
etapa('fonts_d4', {n: (s4 / n, s5 / n) for n in n4 if n.endswith(('.npy', '.npz'))})
# 4 · lineal
L4 = T4 / 'cadena/flat2d_v4/lineal'; L5 = T5 / 'cadena/flat2d_v5/lineal'
etapa('lineal', {'base_G.npy': (CAD / 'flat2d_v4/lineal/base_G.npy', CAD / 'flat2d_v5/lineal/base_G.npy'), 'fusion_starless.npy': (CAD / 'flat2d_v4/lineal/fusion_starless.npy', CAD / 'flat2d_v5/lineal/fusion_starless.npy'),
                 'sony_starless.npy': (L4 / 'sony_starless.npy_100113', L5 / 'sony_starless.npy'), 'vixen_starless.npy': (L4 / 'vixen_starless.npy_100113', L5 / 'vixen_starless.npy'),
                 'star_footprints.npy': (L4 / 'star_footprints.npy_100114', L5 / 'star_footprints.npy'), 'support.npy': (L4 / 'support.npy_100114', L5 / 'support.npy')})
# 5 · base, filtres, estat, fila_REC
etapa('base', {p.name: (p, T5 / 'cadena/flat2d_v5/base' / p.name) for p in sorted((T4 / 'cadena/flat2d_v4/base_100113').glob('*.npy'))})
etapa('filtres_v108', {p.name: (p, T5 / 'cadena/flat2d_v5/filtres_v108' / p.name) for p in sorted((T4 / 'cadena/flat2d_v4/filtres_v108').glob('*.npy'))})
etapa('estat_v108', {p.name: (p, T5 / 'cadena/flat2d_v5/estat_v108' / p.name) for p in sorted((T4 / 'cadena/flat2d_v4/estat_v108').glob('*.npy'))})
fr4 = sorted((T4 / 'cadena/flat2d_v4/fila_REC').rglob('*.np[yz]')); etapa('fila_REC', {str(p.relative_to(T4 / 'cadena/flat2d_v4/fila_REC')): (p, T5 / 'cadena/flat2d_v5/fila_REC' / p.relative_to(T4 / 'cadena/flat2d_v4/fila_REC')) for p in fr4})
# 6 · compost: escampada
x4 = np.asarray(np.load(F4 / 'compost_flat2d_v4.npy', mmap_mode='r'), np.float32); x5 = np.asarray(np.load(F5 / 'compost_flat2d_v5.npy', mmap_mode='r'), np.float32)
ok = np.isfinite(x4) & np.isfinite(x5) & (x4 > 0) & (x5 > 0); r = np.where(ok, np.abs(np.log(np.maximum(x5, 1e-20) / np.maximum(x4, 1e-20))), 0).astype(np.float32); del x4, x5
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; del yy, xx
o = dict(px_diferents=int((r > 0).sum()), px_diferents_a_mes_150=int(((r > 0) & (DIST > 150)).sum()))
for r0, r1 in ((1.0, 1.02), (1.02, 1.5), (1.5, 2.5), (2.5, 4), (4, 6), (6, 10), (10, 30)):
    k = ok & (DIST > 150) & (RS >= r0) & (RS < r1)
    if k.sum() == 0: continue
    v = r[k]; o[f'R{r0}-{r1}'] = dict(n=int(k.sum()), p99_ppm=round(1e6 * float(np.percentile(v, 99)), 1), max_ppm=round(1e6 * float(v.max()), 1))
k = ok & (DIST > 150); o['tot_a_mes_150'] = dict(p99_ppm=round(1e6 * float(np.percentile(r[k], 99)), 1), max_ppm=round(1e6 * float(r[k].max()), 1))
k = ok & (DIST <= 150); o['dins_150'] = dict(p99_pc=round(100 * float(np.percentile(r[k], 99)), 3), max_pc=round(100 * float(r[k].max()), 3))
R['compost_v5_contra_v4'] = o; print('compost', json.dumps(o), flush=True)
(OUT / 'Z3_V5_CONTRA_V4.json').write_text(json.dumps(R, ensure_ascii=False, indent=1, default=str)); print('FET', f'{time.time()-t0:.0f}s')
