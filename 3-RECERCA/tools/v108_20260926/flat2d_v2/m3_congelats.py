"""m3 (V108, flat2d_v2) · QUANT S'HAURIA MOGUT EL QUE ES VA CONGELAR (només lectura). Per a cada paràmetre que la cadena mesura de la dada i
que aquí es pren del control, compara el valor que s'hauria mesurat amb la dada del flat 2D amb el del control:
  · fusió (b3): guany A→B, fracció d'A, porta, ρ, δ i pes de la Vixen (rebut B3_CONGELAT_MESURAT.json);
  · franja (a3d): T de vora i escales de la unió (A3D_FRANJA_BANDA.json → «congelat»);
  · REC de la 56: el mapa de S/N (σ de promig i ρ) mesurat amb la dada nova contra el del control;
  · pesos de cada fotograma: SHA dels denominadors / pesos dels apilats i dels fotogrames de la caixa lunar contra el control.
Sortida: 4-RESULTATS/v108_20260926/flat2d_v2/M3_CONGELATS.json"""
import json, hashlib
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[4]; OUT = ARREL / '4-RESULTATS/v108_20260926/flat2d_v2'; R = ARREL / '4-RESULTATS/v108_20260926/cadena/flat2d_v2'
def sha(p):
    with open(p, 'rb') as f: return hashlib.file_digest(f, 'sha256').hexdigest()
res = {}
b3 = json.loads((OUT / 'fusio/b3/receipts/B3_CONGELAT_MESURAT.json').read_text()); res['fusio'] = dict(mesurat=b3['MESURAT'], control_coef=b3['COEF'])
res['fusio']['coef_A_B_diferencia_max_abs'] = {c: float(np.max(np.abs(np.array(b3['MESURAT']['coef_A_B'][c]) - np.array(b3['COEF'][c])))) for c in b3['COEF']}
fj = json.loads((R / 'franja/A3D_FRANJA_BANDA.json').read_text()); res['franja'] = fj['congelat']
esc_c = json.loads((ARREL / '4-RESULTATS/v108_20260926/cadena/control/franja/A3D_FRANJA_BANDA.json').read_text())['escales']
res['franja']['escales_mesurades_sobre_control_menys_1'] = {k: float(v[0] / esc_c[k][0] - 1) for k, v in fj['congelat']['escales_mesurades'].items()}
a = np.load(OUT / 'fila_sn_mesurat/SN_MAPA.npz'); b = np.load(R / 'fila_REC/SN_MAPA.npz'); sn = {}
for k in a.files:
    A = np.asarray(a[k], np.float64); B = np.asarray(b[k], np.float64)
    if A.shape != B.shape or A.dtype.kind not in 'fiu': continue
    ok = np.isfinite(A) & np.isfinite(B); d = (A - B)[ok]
    sn[k] = dict(forma=list(A.shape), iguals=bool(np.array_equal(A, B, equal_nan=True)), dif_abs_p50_p99_max=[float(np.median(np.abs(d))), float(np.percentile(np.abs(d), 99)), float(np.abs(d).max())] if d.size else None,
                 control_p50=float(np.median(B[ok])) if ok.any() else None)
res['mapa_SN_de_la_56'] = sn
ap = {}
for g in ('vixen', 'sony_A', 'sony_B'):
    j = json.loads((OUT / f'apilats/{g}_REBUT.json').read_text())
    ap[g] = {k: j.get(k) for k in ('den_G_sha256', 'den_RGB_sha256', 'pesos_sha256', 'pesos_iguals_a_la_cadena', 'injectat')}
ap['vixen']['den_G_igual_al_control'] = ap['vixen']['den_G_sha256'] == sha(ARREL / '4-RESULTATS/v108_20260926/marrons/pilot/control/vixen_den.npy')
cA = json.loads((OUT / 'apilats_control/sony_A_REBUT.json').read_text()); ap['sony_A']['den_RGB_igual_al_control'] = ap['sony_A']['den_RGB_sha256'] == cA['den_RGB_sha256']
ap['sony_A']['ondulacio_igual_al_control'] = ap['sony_A']['injectat'].get('ondulacio_sha256') == cA['injectat'].get('ondulacio_sha256')
cB = json.loads((OUT / 'apilats_control/sony_B_REBUT.json').read_text()); ap['sony_B']['ondulacio_igual_al_control'] = ap['sony_B']['injectat'].get('ondulacio_sha256') == cB['injectat'].get('ondulacio_sha256')
lf = json.loads((OUT / 'limb_frames_flat2d/COMPLETE.json').read_text()); ap['caixa_lunar'] = {r['name']: r['igual_a_la_cadena'] for r in lf['files']}
res['pesos_per_fotograma'] = ap
(OUT / 'M3_CONGELATS.json').write_text(json.dumps(res, ensure_ascii=False, indent=1, default=lambda x: x.item() if isinstance(x, np.generic) else str(x)))
print(json.dumps({'coef': res['fusio']['coef_A_B_diferencia_max_abs'], 'wv': b3['MESURAT'].get('wv_mesurat_menys_control'), 'franja_T': fj['congelat'].get('lnT_mesurada_menys_control_max_abs'),
                  'escales': res['franja']['escales_mesurades_sobre_control_menys_1'], 'SN': {k: v['dif_abs_p50_p99_max'] for k, v in sn.items()}, 'pesos': {g: {k: v for k, v in d.items() if 'igual' in k} for g, d in ap.items() if isinstance(d, dict)}}, ensure_ascii=False, indent=0)[:3000])
