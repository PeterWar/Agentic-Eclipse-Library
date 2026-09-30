"""a11 (29-09-2026) · Resseguir la línia fosca de la marca taronja amb un filtre ORIENTAT a la direcció del traç (2,8°):
detall d = ln S − ln G15(S); després, suavitzat anisòtrop al llarg de la direcció θ (σ 30 px) i gairebé res a través (σ 1,5 px): el que és
paral·lel al traç es reforça; els raigs (a ~20–25°) s'esborren. Per a θ = 2,8° i, de control, θ = 22° (la direcció dels raigs) i θ = −17°.
Fonts: compost V115 (sense 414), capes 41, 45, 46, 47, 49, 51, 54, 55, 56, base 3, fusió lineal, Sony (lineal), Vixen (lineal), Sony A, Sony B.
Finestra x 5400–7300, y 4250–4800. Sortida: taronja/A11_orientat_*.png i A11_ORIENTAT.json (valor a la línia central del traç + 5 px)."""
import sys, json, numpy as np, cv2, tifffile
from pathlib import Path
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929'; OUT = O / 'taronja'
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB
X0, X1, Y0, Y1 = 5400, 7300, 4250, 4800
labw = np.asarray(np.load(O / 'marques_V115_etiquetes.npy', mmap_mode='r')[Y0:Y1, X0:X1]) == 11
cols = np.nonzero(labw.any(0))[0]; yc = np.array([np.nonzero(labw[:, c])[0].mean() for c in cols])
p = PSB(str(R / '1-PHOTOSHOP/V115.psb'))
def capa(lid):
    out = []
    for c in (0, 1, 2):
        a, (x, y) = p.channel(lid, c); z = np.full((Y1 - Y0, X1 - X0), np.nan, np.float32); h, w = a.shape
        ya, yb, xa, xb = max(Y0, y), min(Y1, y + h), max(X0, x), min(X1, x + w)
        if yb > ya and xb > xa: z[ya - Y0:yb - Y0, xa - X0:xb - X0] = a[ya - y:yb - y, xa - x:xb - x] / 65535
        out.append(z)
    z = np.stack(out, -1); return (z[..., 0] + 2 * z[..., 1] + z[..., 2]) / 4
def lum(a): a = np.asarray(a, np.float32); return (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4 if a.ndim == 3 else a
def ratio(t, w):
    t = np.asarray(np.load(t, mmap_mode='r')[Y0:Y1, X0:X1], np.float32); w = np.asarray(np.load(w, mmap_mode='r')[Y0:Y1, X0:X1], np.float32); return lum(t / np.maximum(w, 1e-6))
Lc = R / '4-RESULTATS/v114_estrelles_20260928/cadena/v114c/lineal'
F = {'Compost V115': lum(tifffile.memmap(R / '4-RESULTATS/v115_nrgf_20260929/V115_natiu/visible_complet.tif', mode='r')[Y0:Y1, X0:X1] / 65535.)}
for lid in (41, 45, 46, 47, 49, 51, 54, 55, 56, 3): F[f'capa {lid}'] = capa(lid)
for nom, f in (('fusió lineal', 'fusion_starless.npy'), ('Sony lineal', 'sony_starless.npy'), ('Vixen lineal', 'vixen_starless.npy')): F[nom] = lum(np.load(Lc / f, mmap_mode='r')[Y0:Y1, X0:X1])
F['Sony A'] = ratio(R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/b3/cau/sony_A_corr_v42.npy', R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v29/sony_A_weights.npy')
F['Sony B'] = ratio(R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_total_v42.npy', R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_B/cau/sony_B_weights_v42.npy')
def orientat(d, th_deg, sl=30, sc=1.5):
    k = int(4 * sl) | 1; yy, xx = np.mgrid[-(k // 2):k // 2 + 1, -(k // 2):k // 2 + 1].astype(np.float32); t = np.radians(th_deg)
    u = xx * np.cos(t) - yy * np.sin(t); v = xx * np.sin(t) + yy * np.cos(t)          # θ mesurat en pantalla (y avall): la recta del traç baixa 2,8°
    ker = np.exp(-0.5 * (u / sl) ** 2 - 0.5 * (v / sc) ** 2); ker /= ker.sum(); return cv2.filter2D(d, -1, ker, borderType=cv2.BORDER_REFLECT)
res = {}; tir = {2.8: [], 22.0: []}
for nom, S in F.items():
    S = np.nan_to_num(S).astype(np.float32); m = (S > 1e-6).astype(np.float32); x = np.log(np.maximum(S, 1e-6)) * m
    d = np.where(m > 0, x - cv2.GaussianBlur(x, (0, 0), 15) / np.maximum(cv2.GaussianBlur(m, (0, 0), 15), 1e-6), 0).astype(np.float32)
    res[nom] = {}
    for th in (2.8, 22.0, -17.0):
        o = orientat(d, -th)                                     # signe: en coordenades de pantalla la recta baixa cap a la dreta
        prof = np.array([np.mean(o[np.clip(np.round(yc + k).astype(int), 0, Y1 - Y0 - 1), cols]) for k in range(-40, 41)]) * 100
        sd = float(np.std(o[m > 0])) * 100; kmin = int(np.argmin(prof[30:61])) + 30
        res[nom][f'{th}'] = dict(sd_pct=round(sd, 3), min_prop_o=int(kmin - 40), valor_min_pct=round(float(prof[kmin]), 3), z=round(float(prof[kmin]) / max(sd, 1e-9), 2))
        if th in tir:
            g = np.clip(128 + o / (3 * sd / 100) * 127, 0, 255).astype(np.uint8); g = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
            cont, _ = cv2.findContours(labw.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(g, cont, -1, (0, 140, 255), 1)
            cv2.putText(g, f'{nom} · orientat {th}°', (8, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2); tir[th].append(g[::2, ::2])
    print(f'{nom:18s} ' + '  '.join(f'θ={th}: mín a o={v["min_prop_o"]:+d} {v["valor_min_pct"]:+.3f} % (z {v["z"]:+.1f})' for th, v in res[nom].items()), flush=True)
for th, ts in tir.items():
    while len(ts) % 3: ts.append(np.zeros_like(ts[0]))
    cv2.imwrite(str(OUT / f'A11_orientat_{th}.png'), np.vstack([np.hstack(ts[i:i + 3]) for i in range(0, len(ts), 3)]))
(OUT / 'A11_ORIENTAT.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
