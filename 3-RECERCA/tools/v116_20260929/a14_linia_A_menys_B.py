"""a14 (29-09-2026) · La línia de la marca taronja a la diferència δ = ln A + pred − ln B (A = la Sony A que va entrar a la fusió de la V114,
fonts_v113_vora; B = flat2d_v5 v42; pred = guany A→B congelat de la fusió de control V98, com f1_correccio_sonyA): el cel s'anul·la i queda el que
és d'un sol apuntament. Detall δ − G15(δ) i mitjana orientada al llarg de la línia (σ 40 px al llarg, 1 px a través). Perfil a través de la
recta de la línia (ajust del traç + 6 px), per trams de 100 px en x de 3500 a 9500: on hi és, i quant fa. Canal G. Sortida: taronja/A14_*"""
import json, numpy as np, cv2
from pathlib import Path
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929'; OUT = O / 'taronja'
lab = np.load(O / 'marques_V115_etiquetes.npy', mmap_mode='r')
sub = np.asarray(lab[4300:4800, 5900:7100]) == 11; cols = np.nonzero(sub.any(0))[0]; yc = np.array([np.nonzero(sub[:, c])[0].mean() for c in cols]) + 4300; xs = cols + 5900
a_, b_ = np.polyfit(xs, yc + 6, 1); ANG = np.degrees(np.arctan(a_))
A = np.load(R / '4-RESULTATS/v112_claude_20260928/fonts_v113_vora/apilats/sony_A_total.npy', mmap_mode='r')
B = np.load(R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_total_v42.npy', mmap_mode='r')
rec = json.loads((R / '4-RESULTATS/v98_20260925/cadena_v98/b3/receipts/B3_fusio.json').read_text())['pointings']['channels']
COEF = {c: np.asarray(rec[str(c)]['coefficients'], np.float64) for c in range(3)}
H, W = 7506, 10551; XA, XB = 3500, 9500; yl = a_ * np.arange(XA, XB) + b_; Y0, Y1 = int(yl.min()) - 120, int(yl.max()) + 120
st = np.load(R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/sources/star_footprints.npy', mmap_mode='r')
stars = ndi.binary_dilation(np.asarray(st[Y0:Y1, XA:XB]) > 0, iterations=4)
def orientat(d, m, sl=40, sc=1.0):
    k = int(4 * sl) | 1; yy, xx = np.mgrid[-(k // 2):k // 2 + 1, -(k // 2):k // 2 + 1].astype(np.float32); t = np.radians(-ANG)
    u = xx * np.cos(t) - yy * np.sin(t); v = xx * np.sin(t) + yy * np.cos(t); ker = np.exp(-0.5 * (u / sl) ** 2 - 0.5 * (v / sc) ** 2); ker /= ker.sum()
    return cv2.filter2D(d * m, -1, ker, borderType=cv2.BORDER_REFLECT) / np.maximum(cv2.filter2D(m, -1, ker, borderType=cv2.BORDER_REFLECT), 1e-6)
res = dict(recta=dict(a=a_, b=b_, angle_graus=ANG), canals={})
yy, xx = np.mgrid[Y0:Y1, XA:XB]; gx = (xx - W / 2) / 4000; gy = (yy - H / 2) / 4000
for c in (1, 0, 2):
    a = np.asarray(A[Y0:Y1, XA:XB, c], np.float64); b = np.asarray(B[Y0:Y1, XA:XB, c], np.float64)
    m = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0) & ~stars
    k_ = COEF[c]; pred = k_[0] + k_[1] * gx + k_[2] * gy + k_[3] * gx * gx + k_[4] * gx * gy + k_[5] * gy * gy
    dl = np.where(m, np.log(np.where(m, a, 1)) + pred - np.log(np.where(m, b, 1)), 0).astype(np.float32); mf = m.astype(np.float32)
    hp = np.where(m, dl - cv2.GaussianBlur(dl, (0, 0), 15) / np.maximum(cv2.GaussianBlur(mf, (0, 0), 15), 1e-6), 0).astype(np.float32)
    o = orientat(hp, mf)
    offs = np.arange(-40, 41); P = np.full((len(offs), XB - XA), np.nan, np.float32)
    for i, k in enumerate(offs):
        yi = np.round(yl + k).astype(int) - Y0; P[i] = np.where(m[yi, np.arange(XB - XA)], o[yi, np.arange(XB - XA)], np.nan)
    trams = {}
    for x0 in range(XA, XB, 100):
        kk = slice(x0 - XA, x0 - XA + 100); pr = np.nanmean(P[:, kk], 1) * 100
        if np.isfinite(pr).sum() < 60: continue
        fons = np.nanmean(pr[np.abs(offs) >= 15]); sd = np.nanstd(pr[np.abs(offs) >= 15])
        trams[x0] = dict(centre=round(float(pr[offs == 0][0] - fons), 3), min_o=int(offs[np.nanargmin(np.where(np.abs(offs) <= 8, pr, np.nan))]), z=round(float((pr[offs == 0][0] - fons) / max(sd, 1e-9)), 1))
    res['canals'][str(c)] = trams
    if c == 1:
        print('canal G · clot al centre de la línia (δ, %) per trams de 100 px [z]:')
        print('  ' + '  '.join(f'{x0}:{v["centre"]:+.3f}[{v["z"]:+.0f}]' for x0, v in trams.items()))
        g = np.clip(128 + o / 0.0015 * 127, 0, 255).astype(np.uint8); g = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR); g[~m] = (60, 0, 60)
        for x0 in range(XA, XB, 500): cv2.putText(g, str(x0), (x0 - XA + 4, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
        pts = np.c_[xs - XA, np.round(yc - Y0)].astype(np.int32); cv2.polylines(g, [pts], False, (0, 140, 255), 1)
        cv2.imwrite(str(OUT / 'A14_delta_AB_orientat.png'), g[:, ::2][::1])
(OUT / 'A14_LINIA_A_MENYS_B.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
