"""09 — Genera final_config_v4.json a partir del resultat real de la cadena:
visibles = fonament (3,4,5,7) + capes ACCEPTADES de la cadena; la resta, ocultes en quarantena.
Màscares declarades: totes les derivades (4,5,7 + acceptades). Opacitat 255 a tot arreu (R12)."""
import json, sys
from pathlib import Path
from v4_lib import V4W, ORDER, LAYER_PREFIX

HERE = Path(__file__).resolve().parent
NOMS = {3: '12_1-3200s_572A2956', 4: '11_1-500s_572A2968', 5: '10_1-125s_572A2969',
        7: '09_1-60s_572A2975_apilat2', 8: '08_1-30s_572A2970_apilat4', 9: '07_1-15s_572A2976_apilat2',
        10: '06_1-8s_572A2971_apilat4', 11: '05_1-4s_572A2977_apilat2', 12: '04_1-2s_572A2972_apilat4',
        13: '03_1s_572A2978_apilat2', 16: '02_2s_572A2979_apilat3', 17: '01_10.3s_572A2982_apilat3'}

cad = json.load(open(V4W / 'QA/cadena/cadena.json'))
accepted = [i for i in (8, 9, 10, 11, 12, 13, 16, 17) if cad.get(str(i), {}).get('veredicte') == 'ACCEPTADA']
visible = [3, 4, 5, 7] + accepted
cfg = {'visibility': {}, 'name_overrides': {}, 'opacity_overrides': {'17': 255}, 'masks': {}}
for i in ORDER:
    v = i in visible
    cfg['visibility'][str(i)] = v
    base = NOMS[i] + ('.CR3' if i in (3, 4, 5) else '.dng')
    if i == 3:
        tag = 'FONT_PROTEGIDA · FONAMENT V4 (base, màscara blanca)'
    elif i in (4, 5, 7):
        tag = 'FONAMENT V4 RE-DERIVAT · revelat normalitzat'
    elif i in accepted:
        c = cad[str(i)]
        tag = f"ACCEPTADA V4 · rampa {c['r_a']}→{c['r_b']} R☉ · w={c['w_max']} · revelat normalitzat"
    else:
        tag = 'QUARANTENA OCULTA · no acceptada a la V4'
    cfg['name_overrides'][str(i)] = f'{base} · {tag}'
for i in (4, 5, 7) + tuple(accepted):
    cfg['masks'][str(i)] = {}
out = HERE / 'final_config_v4.json'
if out.exists():
    raise SystemExit(f'existeix: {out}')
out.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
print('visibles:', visible)
print('màscares declarades:', list(cfg['masks']))
print('->', out)
