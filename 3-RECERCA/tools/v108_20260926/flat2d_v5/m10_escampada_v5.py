"""m10_escampada_v5 (V108, flat2d_v5) · QUANT es mouen, LLUNY DELS LLOCS, els productes que la v5 canvia arreu (m9: els valors dels filtres i el
compost). Els filtres no són locals (histogrames per radi de les RHEF i les ACHF, mitjanes per radi de les NRGF, normalització per escala de les
WOW): un canvi a 5 petjades i a 7 píxels mou una mica tot el llenç. Aquí, per bandes de distància al lloc més proper (M9_LLOCS.npz):
0 (dins), 0–50, 50–150, 150–300, > 300 px: n de píxels diferents, p50, p99 i màxim de |Δ| (DN per als ràsters u16 dels filtres; i |Δ|/valor
on la v4 hi val ≥ 2.000 DN) i de |ln(v5/v4)| per al compost. Només lectura (v4 dels filtres i de l'estat, de la Paperera).
Sortida: 4-RESULTATS/v108_20260926/flat2d_v5/M10_ESCAMPADA.json"""
import json, time
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
A = Path(__file__).resolve().parents[4]; R5 = A / '4-RESULTATS/v108_20260926/flat2d_v5'; R4 = A / '4-RESULTATS/v108_20260926/flat2d_v4'
C5 = A / '4-RESULTATS/v108_20260926/cadena/flat2d_v5'; T4 = Path.home() / '.Trash/Eclipse_V108_flat2d_v4_intermedis_20260927/cadena/flat2d_v4'
t0 = time.time(); LLOC = np.load(R5 / 'M9_LLOCS.npz')['lloc']
DIST = ndi.distance_transform_edt(LLOC == 0).astype(np.float32)
BANDES = [(-1, 0.5), (0.5, 50), (50, 150), (150, 300), (300, 1e9)]; NOMB = ['dins', '0-50', '50-150', '150-300', '>300']
def per_bandes(dm, mag, rel=None):
    o = {}
    for (a, b), nb in zip(BANDES, NOMB):
        k = (dm > a) & (dm <= b)
        if not k.any(): o[nb] = dict(n=0); continue
        m = mag[k]; e = dict(n=int(k.sum()), p50=float(np.percentile(m, 50)), p99=float(np.percentile(m, 99)), max=float(m.max()))
        if rel is not None:
            r = rel[k]; r = r[np.isfinite(r)]
            if r.size: e.update(rel_p50=float(np.percentile(r, 50)), rel_p99=float(np.percentile(r, 99)), rel_max=float(r.max()))
        o[nb] = e
    return o
R = {}
PR = [(p, T4 / 'filtres_v108' / p.name) for p in sorted((C5 / 'filtres_v108').glob('*_u16.npy')) if '_alfa_' not in p.name]
for p5, p4 in PR:
    a = np.load(p5, mmap_mode='r'); b = np.load(p4, mmap_mode='r'); ys, xs, mags, rels = [], [], [], []
    for y0 in range(0, a.shape[0], 512):
        x5 = np.asarray(a[y0:y0 + 512], np.int32); x4 = np.asarray(b[y0:y0 + 512], np.int32); d = x5 != x4
        if d.ndim == 3: d = d.any(-1); x5 = x5.max(-1); x4 = x4.max(-1)
        yy, xx = np.nonzero(d); ys.append(yy + y0); xs.append(xx); mg = np.abs(x5[d] - x4[d]).astype(np.float32); mags.append(mg)
        v4 = x4[d].astype(np.float32); rels.append(np.where(v4 >= 2000, mg / np.maximum(v4, 1), np.nan))
    ys = np.concatenate(ys); xs = np.concatenate(xs); mg = np.concatenate(mags); rl = np.concatenate(rels)
    R[p5.name] = dict(n_diferents=int(mg.size), per_distancia=per_bandes(DIST[ys, xs], mg, rl))
    print(p5.name, json.dumps({k: (v.get('n'), round(v.get('p99', 0), 1), round(v.get('max', 0), 1), round(v.get('rel_p99', float('nan')), 5) if 'rel_p99' in v else None) for k, v in R[p5.name]['per_distancia'].items()}), f'{time.time()-t0:.0f}s', flush=True)
a = np.asarray(np.load(R5 / 'compost_flat2d_v5.npy', mmap_mode='r'), np.float64); b = np.asarray(np.load(R4 / 'compost_flat2d_v4.npy', mmap_mode='r'), np.float64)
ok = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0); d = ok & (a != b); ys, xs = np.nonzero(d); mg = np.abs(np.log(a[d] / b[d])).astype(np.float32)
R['compost_flat2d_v5.npy'] = dict(n_diferents=int(mg.size), n_valids=int(ok.sum()), per_distancia=per_bandes(DIST[ys, xs], mg))
# el compost fora dels llocs, per anells de R☉ (com el y4 del verificador): rms i p99 del |ln(v5/v4)| a TOTS els píxels vàlids (també els iguals)
SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL; del yy, xx
lr = np.where(ok, np.abs(np.log(np.where(ok, a, 1) / np.where(ok, b, 1))), np.nan).astype(np.float32); fora = ok & (DIST > 150) & (DL > 30); an = {}
for r0, r1 in ((1.02, 1.5), (1.5, 2.5), (2.5, 4), (4, 6), (6, 10), (10, 30)):
    k = fora & (RS >= r0) & (RS < r1); v = lr[k].astype(np.float64)
    an[f'R{r0}-{r1}'] = dict(n=int(k.sum()), rms_ppm=round(1e6 * float(np.sqrt((v ** 2).mean())), 2), p99_ppm=round(1e6 * float(np.percentile(v, 99)), 2), max_ppm=round(1e6 * float(v.max()), 1))
for d0, d1 in ((0, 3), (3, 10), (10, 30)):
    k = ok & (DL >= d0) & (DL < d1) & (DIST > 150); v = lr[k].astype(np.float64)
    an[f'limbe_{d0}-{d1}px_fora_protuberancia'] = dict(n=int(k.sum()), rms_ppm=round(1e6 * float(np.sqrt((v ** 2).mean())), 2), p99_ppm=round(1e6 * float(np.percentile(v, 99)), 2), max_ppm=round(1e6 * float(v.max()), 1))
R['compost_fora_dels_llocs_150px_per_anells'] = an
print('compost', json.dumps(R['compost_flat2d_v5.npy']['per_distancia']), json.dumps(an), flush=True)
(R5 / 'M10_ESCAMPADA.json').write_text(json.dumps(R, ensure_ascii=False, indent=1) + '\n'); print('FET', f'{time.time()-t0:.0f}s')
