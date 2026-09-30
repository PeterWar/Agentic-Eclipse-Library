"""a6 (V116, 29-09-2026) · On neix la marca TARONJA de Pere (marca 11: traç gairebé horitzontal de 757 px a 3,1 R☉, x 6123–6880, y ≈ 4526)?
Per a cada font (lineals: Sony A, Sony B, Sony, Vixen, fusió; capes de filtre de la pila; la sortida V115 sense 414) a la finestra x 5950–7050, y 4300–4750:
  detall d = ln S − ln G_σ30(S) (normalitzat); perfil perpendicular al traç P(o) = mitjana_x d(x, y_c(x) + o), o ∈ [−90, 90] px, amb y_c(x) la línia central del traç;
  fondària de la línia = P(0) − mitjana(P a |o| ∈ [25, 90]) (%). Una línia HORITZONTAL (no radial) surt com a clot estret a o = 0; un buit entre raigs (inclinat)
  s'esmorteeix en fer la mitjana al llarg de x. Vista: una tira per font (±3σ), amb el traç. Sortida: 4-RESULTATS/v116_20260929/taronja/"""
import sys, json, numpy as np, cv2, tifffile
from pathlib import Path
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929'; OUT = O / 'taronja'; OUT.mkdir(exist_ok=True)
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB
X0, X1, Y0, Y1 = 5950, 7050, 4300, 4750
lab = np.asarray(np.load(O / 'marques_V115_etiquetes.npy', mmap_mode='r')[Y0:Y1, X0:X1]) == 11
cols = np.nonzero(lab.any(0))[0]; yc = np.array([np.nonzero(lab[:, c])[0].mean() for c in cols])
L = R / '4-RESULTATS/v114_estrelles_20260928/cadena/v114c/lineal'
def lum(a): a = np.asarray(a, np.float32); return (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4 if a.ndim == 3 else a
def ratio(t, w):
    t = np.asarray(np.load(t, mmap_mode='r')[Y0:Y1, X0:X1], np.float32); w = np.asarray(np.load(w, mmap_mode='r')[Y0:Y1, X0:X1], np.float32)
    return lum(t / np.maximum(w, 1e-6)), (w[..., 1] > 0.2 * np.median(w[..., 1][w[..., 1] > 0])) if (w[..., 1] > 0).any() else np.zeros(w.shape[:2], bool)
F = {}
F['Sony A (lineal)'], mA = ratio(R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/b3/cau/sony_A_corr_v42.npy', R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v29/sony_A_weights.npy')
F['Sony B (lineal)'], mB = ratio(R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_total_v42.npy', R / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/b2_sony_B/cau/sony_B_weights_v42.npy')
for nom, f in (('Sony (lineal)', 'sony_starless.npy'), ('Vixen (lineal)', 'vixen_starless.npy'), ('Fusió (lineal)', 'fusion_starless.npy')): F[nom] = lum(np.load(L / f, mmap_mode='r')[Y0:Y1, X0:X1])
p = PSB(str(R / '1-PHOTOSHOP/V115.psb'))
def capa(lid):
    out = []
    for c in (0, 1, 2):
        a, (x, y) = p.channel(lid, c); h, w = a.shape; z = np.full((Y1 - Y0, X1 - X0), np.nan, np.float32)
        ya, yb, xa, xb = max(Y0, y), min(Y1, y + h), max(X0, x), min(X1, x + w)
        if yb > ya and xb > xa: z[ya - Y0:yb - Y0, xa - X0:xb - X0] = a[ya - y:yb - y, xa - x:xb - x] / 65535
        out.append(z)
    return lum(np.stack(out, -1))
for lid in (3, 54, 41, 42, 47, 49, 51, 45, 46, 55, 56, 76, 96, 234, 308):
    nm = next(l['name'] for l in p.layers if l['id'] == lid); F[f'{lid} · {nm[:28]}'] = capa(lid)
F['Sortida V115 (sense 414)'] = lum(tifffile.memmap(R / '4-RESULTATS/v115_nrgf_20260929/V115_natiu/visible_complet.tif', mode='r')[Y0:Y1, X0:X1])
def detall(S):
    S = np.where(np.isfinite(S), S, 0).astype(np.float32); m = (S > 1e-5).astype(np.float32); x = np.log(np.maximum(S, 1e-5)) * m
    return np.where(m > 0, x - cv2.GaussianBlur(x, (0, 0), 30) / np.maximum(cv2.GaussianBlur(m, (0, 0), 30), 1e-6), np.nan)
offs = np.arange(-90, 91); res = {}; tires = []
for nom, S in F.items():
    d = detall(S); P = []
    for o in offs:
        yy = np.round(yc + o).astype(int); ok = (yy >= 0) & (yy < d.shape[0]); v = d[yy[ok], cols[ok]]; P.append(np.nanmean(v) if np.isfinite(v).any() else np.nan)
    P = np.array(P) * 100; fons = np.nanmean(P[np.abs(offs) >= 25]); sd = np.nanstd(P[np.abs(offs) >= 25])
    res[nom] = dict(fondaria_linia_pct=round(float(P[offs == 0][0] - fons), 3), min_a_o=int(offs[np.nanargmin(np.where(np.abs(offs) <= 20, P, np.nan))]) if np.isfinite(P).any() else None,
                    soroll_perfil_pct=round(float(sd), 3), perfil_pct=[round(float(v), 3) if np.isfinite(v) else None for v in P[::5]])
    print(f'{nom:45s} fondària {res[nom]["fondaria_linia_pct"]:+.3f} %  (soroll del perfil {sd:.3f})', flush=True)
    s = np.nanstd(d); g = np.clip(128 + np.nan_to_num(d) / (3 * s + 1e-9) * 127, 0, 255).astype(np.uint8); g = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    cont, _ = cv2.findContours(lab.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(g, cont, -1, (0, 140, 255), 1)
    cv2.putText(g, f'{nom}  ({res[nom]["fondaria_linia_pct"]:+.2f} %)', (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2); tires.append(g[::2, ::2])
fila = [np.hstack(tires[i:i + 3]) if len(tires[i:i + 3]) == 3 else np.hstack(tires[i:i + 3] + [np.zeros_like(tires[0])] * (3 - len(tires[i:i + 3]))) for i in range(0, len(tires), 3)]
cv2.imwrite(str(OUT / 'A6_fonts_taronja.png'), np.vstack(fila))
(OUT / 'A6_PERFIL_TARONJA.json').write_text(json.dumps(dict(nota=__doc__.split('\n')[0], finestra=[X0, X1, Y0, Y1], offsets_cada5=list(map(int, offs[::5])), fonts=res), ensure_ascii=False, indent=1))
