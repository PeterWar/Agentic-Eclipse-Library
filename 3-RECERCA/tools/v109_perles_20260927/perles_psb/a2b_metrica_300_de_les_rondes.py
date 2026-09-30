"""a2b (V109 · perles_psb) · Reprodueix la mètrica «P · perles» de les rondes de la V108 (w4/m1: els 300 màxims locals més forts del DoG σ1–4 del
ln del compost d'ABANS a 0–60 px del limbe, finestra 9×9, amplitud després/abans) sobre els PSB (fusionat i recompost), i diu ON són aquests
300 punts (azimut, distància al limbe) i quants són perles de veritat (sector 150–200°, d < 8 px). Sortida: A2B_METRICA_300.json"""
import numpy as np, cv2
from comu_perles import CAIXA, OUT, geom, lum, fusionat, V107, V108, desa
d, th = geom(CAIXA)
def lnm(img):
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
def ng(l, m, s): return cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
rep = {}
for fam, (A, B) in dict(fusionat=(lum(fusionat(V107, CAIXA)), lum(fusionat(V108, CAIXA))), recompost=(lum(np.load(OUT / 'REC_V107.npy')), lum(np.load(OUT / 'REC_V108.npy')))).items():
    la, ma = lnm(A); lb, mb = lnm(B); m = ma * mb; da = ng(la, m, 1) - ng(la, m, 4); db = ng(lb, m, 1) - ng(lb, m, 4)
    franja = (d >= 0) & (d < 60) & (m > 0); mx = cv2.dilate(da, np.ones((9, 9), np.uint8)); pk = franja & (da == mx) & (da > 0)
    ys, xs = np.nonzero(pk); o = np.argsort(-da[ys, xs])[:300]; ys, xs = ys[o], xs[o]; rat = db[ys, xs] / da[ys, xs]
    perla = (th[ys, xs] >= 150) & (th[ys, xs] < 200) & (d[ys, xs] < 8)
    h_th, _ = np.histogram(th[ys, xs], bins=12, range=(0, 360)); h_d, _ = np.histogram(d[ys, xs], bins=[0, 4, 8, 20, 40, 60])
    rep[fam] = dict(n=int(len(ys)), despres_sobre_abans_p5_p50_p95=np.percentile(rat, [5, 50, 95]).round(4).tolist(),
                    n_perles_de_veritat=int(perla.sum()), perles_p5_p50_p95=(np.percentile(rat[perla], [5, 50, 95]).round(4).tolist() if perla.sum() > 2 else None),
                    resta_p5_p50_p95=np.percentile(rat[~perla], [5, 50, 95]).round(4).tolist(),
                    histograma_azimut_30graus=h_th.tolist(), histograma_distancia_0_4_8_20_40_60=h_d.tolist())
    print(fam, rep[fam])
desa(OUT / 'A2B_METRICA_300.json', rep)
