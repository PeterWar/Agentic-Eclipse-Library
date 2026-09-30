"""a3b · Els filtres nous fan el mateix que els de la V84 lluny del limbe? (vara única amb la rèplica exacta dels filtres V58 de la V84,
4-RESULTATS/v85_regeneracio_20260922/filters_baseline). Correlació, diferència mitjana i relació de desviacions per anells centrats al Sol,
fora de la franja i d'un marge; i perfil de la diferència en funció de la distància a la vora exterior de la franja (fins on arriba l'efecte del contorn)."""
from v86_comu import *
import cv2
claim()
C = SORT / 'filtres'; BASE = V85D / 'filters_baseline/products/filters'
TAGS = ['P01_NRGF', 'P01_NRGF_extrap', 'P02_RHEF', 'P02b_RHEF_ups0.35', 'P02c_RHEF_local60_native', 'P02d_RHEF_local30_native', '01', '04', '05', '06', '03', '03v30', '07', 'P03_MGN', 'P04_WOW', 'P05_WOW_bilateral']
g = np.load(SORT / 'A2_geometria.npz'); by0, by1, bx0, bx1 = g['box']; franja = np.zeros((H, W), bool); franja[by0:by1, bx0:bx1] = g['franja']
sup = np.load(FONTS / 'support.npy'); r, _ = coords()
dist = cv2.distanceTransform((~franja).astype(np.uint8), cv2.DIST_L2, 5)     # distància a la franja (0 a dins)
S = (slice(0, H, 2), slice(0, W, 2)); ds = dist[S]; rs = r[S]; ss = sup[S]
rep = {}
for tag in TAGS:
    p = C / f'{tag}_u16.npy'; b = BASE / f'{tag}_u16.npy'
    if not p.exists(): continue
    a = np.load(p, mmap_mode='r')[S].astype('float32') / 65535; o = np.load(b, mmap_mode='r')[S].astype('float32') / 65535
    rows = []
    for r0, r1 in [(520, 700), (700, 1000), (1000, 1600), (1600, 2600), (2600, 4000)]:
        k = ss & (ds > 60) & (rs >= r0) & (rs < r1)
        if k.sum() < 1000: continue
        x = a[k]; y = o[k]; cc = float(np.corrcoef(x, y)[0, 1])
        rows.append(dict(r=[r0, r1], n=int(k.sum()), correlacio=round(cc, 5), dif_mitjana_DN16=round(float((x - y).mean() * 65535), 1), relacio_desviacio=round(float(x.std() / max(y.std(), 1e-9)), 4), dif_abs_p95_DN16=round(float(np.percentile(np.abs(x - y), 95) * 65535), 1)))
    prof = []
    for d0, d1 in [(0.5, 3), (3, 6), (6, 12), (12, 24), (24, 48), (48, 96), (96, 192)]:
        k = ss & (ds >= d0) & (ds < d1) & (rs < 900)
        if k.sum() > 100: prof.append(dict(d=[d0, d1], n=int(k.sum()), dif_abs_mediana_DN16=round(float(np.median(np.abs(a[k] - o[k])) * 65535), 1)))
    rep[tag] = dict(anells=rows, per_distancia_a_la_franja=prof); log(f"{tag}: " + ' '.join(f"{q['r'][0]}-{q['r'][1]}:{q['correlacio']:.4f}" for q in rows))
desa_json('A3B_COMPARA_V84.json', rep); log('A3B fet')
