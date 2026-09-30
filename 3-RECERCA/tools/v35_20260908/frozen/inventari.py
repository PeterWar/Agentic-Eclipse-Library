"""Inventari de replicació de la V35: SHA-256 i mida de cada entrada, paràmetre congelat, artefacte intermedi i sortida.
Escriu INVENTARI_REPLICACIO_V35.json i INVENTARI_REPLICACIO_V35.md (taula). Només lectura."""
import hashlib, json, sys, time
from pathlib import Path
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026'); T = ROOT / 'research/tools'; RUNS = Path('/Users/USUARI/Desktop/Eclipse determinista/1-RUNS'); CT = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals')
HERE = Path(__file__).resolve().parent
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(16 << 20), b''):
            h.update(b)
    return h.hexdigest()
GROUPS = {
 'A. runs de la cadena (immutables; MANIFEST amb el SHA de cada RAW)': [RUNS / '019_VIXEN_CIENCIA_20260827T212404Z/MANIFEST.json', RUNS / '016_SONYTOT_CIENCIA_20260827T183356Z/MANIFEST.json', RUNS / '019_VIXEN_CIENCIA_20260827T212404Z/4-rebuts/F1.3_registre.json', RUNS / '016_SONYTOT_CIENCIA_20260827T183356Z/4-rebuts/F1.3_registre.json', RUNS / '019_VIXEN_CIENCIA_20260827T212404Z/4-rebuts/F2.2_coherencia.json', RUNS / '016_SONYTOT_CIENCIA_20260827T183356Z/4-rebuts/F2.2_coherencia.json'],
 'B. geometria a la graella de Pere i paràmetres congelats (còpia a frozen/params)': [T / 'v25_lineal/cau_v25/geometria_v27.json', T / 'v29/cau_final/refined_detail_receipt.json', T / 'v29/cau_final/coherent_resolution.json', T / 'v29/cau_final/pointing_merge_receipt.json', T / 'v30/cau/fine_variants_receipt.json', T / 'v29_c03_fix/offset_model.json', ROOT / 'output/revisio_marques_v33_20260907/4-rebuts/R33_linealitat_sensor.json'],
 'C. artefactes de la V29 a la graella final (suports, pesos, mapa de resolució)': [T / 'v29/cau_final/vixen_support.npy', T / 'v29/cau_final/sony_support.npy', T / 'v29/cau_final/fusion_support.npy', T / 'v29/cau_final/vixen_weight_G.npy', T / 'v29/cau_final/sony_weight_G.npy', T / 'v29/cau_final/sony_A_weights.npy', T / 'v29/cau_final/sony_B_weights.npy', T / 'v29/cau_final/sony_A_blend_weight.npy', T / 'v29/cau_final/resolution_sigma.npy'],
 'D. codi (cadena determinista, v29 common, v31_purs operadors, v32/v34/v35)': [T / 'eclipse_determinista/cadena.py', T / 'eclipse_determinista/comu.py', T / 'eclipse_determinista/f0.py', T / 'eclipse_determinista/f1.py', T / 'eclipse_determinista/f2.py', T / 'eclipse_determinista/f3.py', T / 'v29/common.py', T / 'v29/fuse_and_filter.py', T / 'v29/audit_geometry.py', T / 'v29/qa_rasters.py', T / 'v29/inspect_inputs.py', T / 'encaix_sony/psb_utils.py', T / 'v31_purs/common.py', T / 'v31_purs/wow_filters.py', T / 'v31_purs/local_filters.py', T / 'v31_purs/radial_filters.py', T / 'v31_purs/sparse_conv.cpp', T / 'v31_purs/sparse_conv.dylib', T / 'v32_arcs_20260907/comu32.py', T / 'v34_20260907/comu34.py', T / 'v34_20260907/a1_pesos_per_fotograma.py', T / 'v34_20260907/b1_camps_per_fotograma.py', T / 'v34_20260907/b2_recomposicio.py', T / 'v35_20260908/comu35.py', T / 'v35_20260908/b3_fusio.py', T / 'v35_20260908/b4a_capes_cadena.py', T / 'v35_20260908/b4c_purs.py', T / 'v35_20260908/b4d_radial_vora.py', T / 'v35_20260908/c4_psb.py', T / 'capes_totals_v14/porta_photoshop.sh'],
 'E. composició per grup (V34 a1/b1/b2)': [T / 'v34_20260907/cau/vixen_total_v34.npy', T / 'v34_20260907/cau/sony_A_total_v34.npy', T / 'v34_20260907/cau/sony_B_total_v34.npy', T / 'v34_20260907/cau/vixen_meta.json', T / 'v34_20260907/cau/sony_meta.json'],
 'F. fusió i capes V35': [T / 'v35_20260908/cau/sony_corrected_total_v35.npy', T / 'v35_20260908/cau/fusion_total_v35.npy', T / 'v35_20260908/cau/base_G_v35.npy', T / 'v35_20260908/cau/support_v35.npy', T / 'v35_20260908/cau/weight_vixen_v35.npy', T / 'v35_20260908/cau/rho_v35.npy', T / 'v35_20260908/cau/delta_v35.npy'] + [T / f'v35_20260908/cau/{k}_v35_u16.npy' for k in ('01', '02', '04', '05', '06')] + [T / f'v35_20260908/purs/cau/{k}_u16.npy' for k in ('P01_NRGF', 'P02_RHEF', 'P03_MGN', 'P04_WOW', 'P05_WOW_bilateral')],
 'G. modes i màscares de les capes (de V32.psb, congelats)': [HERE / 'modes_mascares_v32.npz', HERE / 'modes_mascares_v32.json'],
 'H. producte': [CT / 'V35.psb', CT / 'V35_REBUT.md'],
}
inv = {'generat': time.strftime('%Y-%m-%dT%H:%M:%S'), 'grups': {}}; L = ['# Inventari de replicació de la V35 (SHA-256)', '', 'Generat per `frozen/inventari.py`. Un replicador comprova cada fila abans (A–D) i després (E–H) de cada etapa.', '']
for g, files in GROUPS.items():
    rows = []; L += [f'## {g}', '', '| fitxer | bytes | SHA-256 |', '|---|---:|---|']
    for p in files:
        if not p.exists():
            rows.append({'path': str(p), 'missing': True}); L.append(f'| `{p}` | – | ABSENT |'); print('ABSENT', p, flush=True); continue
        h = sha(p); rows.append({'path': str(p), 'bytes': p.stat().st_size, 'sha256': h}); L.append(f'| `{p.relative_to(ROOT) if str(p).startswith(str(ROOT)) else p}` | {p.stat().st_size:,} | `{h}` |'); print(p.name, h[:16], flush=True)
    inv['grups'][g] = rows; L.append('')
(HERE / 'INVENTARI_REPLICACIO_V35.json').write_text(json.dumps(inv, indent=1, ensure_ascii=False) + '\n'); (HERE / 'INVENTARI_REPLICACIO_V35.md').write_text('\n'.join(L) + '\n'); print('inventari fet')
