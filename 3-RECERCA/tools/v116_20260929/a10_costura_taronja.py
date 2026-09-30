"""a10 (29-09-2026, després de la V116) · La marca taronja (11): hi ha una COSTURA (graó d'un mapa de pesos o de cobertura) paral·lela al traç?
Perfil a 1 px perpendicular al traç (línia central per columna del traç, com a6) de cada mapa de pesos/cobertura de la cadena i de les fonts,
i on és el graó més fort (derivada del perfil). Vista: finestra x 5700–7100, y 4350–4700 de cada mapa, amb el traç. Sortida: taronja/A10_*."""
import json, numpy as np, cv2
from pathlib import Path
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929'; OUT = O / 'taronja'
X0, X1, Y0, Y1 = 5700, 7100, 4350, 4700
lab = np.asarray(np.load(O / 'marques_V115_etiquetes.npy', mmap_mode='r')[Y0:Y1, X0:X1]) == 11
cols = np.nonzero(lab.any(0))[0]; yc = np.array([np.nonzero(lab[:, c])[0].mean() for c in cols])
C97 = R / '4-RESULTATS/v97_refundacio_20260924'; FC = R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio'
MAPES = {'weight_vixen_v42 (fusió V114)': FC / 'b3/cau/weight_vixen_v42.npy', 'support_v42 (fusió V114)': FC / 'b3/cau/support_v42.npy',
         'support (fonts d4 V114)': FC / 'd4/products/sources/support.npy', 'vixen_weights (v29)': C97 / 'cadena_raw/sources_v29/vixen_weights.npy',
         'vixen_weight_G (v29)': C97 / 'cadena_raw/sources_v29/vixen_weight_G.npy', 'sony_weight_G (v29)': C97 / 'cadena_raw/sources_v29/sony_weight_G.npy',
         'sony_A_weights (v29)': C97 / 'cadena_raw/sources_v29/sony_A_weights.npy', 'sony_B_weights (v29)': C97 / 'cadena_raw/sources_v29/sony_B_weights.npy',
         'sony_B_weights_v42 (flat2d v5)': R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_weights_v42.npy',
         'sony_odd_weights (v29)': C97 / 'cadena_raw/sources_v29/sony_odd_weights.npy', 'sony_even_weights (v29)': C97 / 'cadena_raw/sources_v29/sony_even_weights.npy'}
offs = np.arange(-60, 61); res = {}; tires = []
for nom, f in MAPES.items():
    if not f.exists(): res[nom] = 'falta'; continue
    a = np.load(f, mmap_mode='r'); sh = a.shape
    x = np.asarray(a[Y0:Y1, X0:X1, 1] if a.ndim == 3 else a[Y0:Y1, X0:X1], np.float32)
    P = np.array([np.mean(x[np.clip(np.round(yc + o).astype(int), 0, Y1 - Y0 - 1), cols]) for o in offs])
    d = np.diff(P); i = int(np.argmax(np.abs(d))); rang = float(P.max() - P.min())
    res[nom] = dict(forma=list(sh), dtype=str(a.dtype), mitjana=round(float(P.mean()), 5), rang_perfil=round(rang, 5), rang_relatiu=round(rang / max(abs(float(P.mean())), 1e-9), 4),
                    grao_max_a_o=int(offs[i]) + 0.5, grao_max=round(float(d[i]), 5), perfil_cada5=[round(float(v), 5) for v in P[::5]])
    print(f'{nom:34s} rang relatiu {res[nom]["rang_relatiu"]:.4f}  graó màx {res[nom]["grao_max"]:+.5f} a o={res[nom]["grao_max_a_o"]:+.1f}', flush=True)
    lo, hi = np.percentile(x, [0.5, 99.5]); g = np.clip((x - lo) / max(hi - lo, 1e-12) * 255, 0, 255).astype(np.uint8); g = cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)
    cont, _ = cv2.findContours(lab.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); cv2.drawContours(g, cont, -1, (0, 140, 255), 1)
    cv2.putText(g, nom, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2); tires.append(g[::2, ::2])
while len(tires) % 2: tires.append(np.zeros_like(tires[0]))
cv2.imwrite(str(OUT / 'A10_mapes_pesos_taronja.png'), np.vstack([np.hstack(tires[i:i + 2]) for i in range(0, len(tires), 2)]))
(OUT / 'A10_COSTURA.json').write_text(json.dumps(dict(nota=__doc__.split('\n')[0], offsets_cada5=list(map(int, offs[::5])), mapes=res), ensure_ascii=False, indent=1))
