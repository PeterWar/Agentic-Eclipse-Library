"""q4 (V100 detall, dada) · INVENTARI (sense processar res): hi ha dada de la Sony per fotograma a la caixa lunar? Quina cobertura té la banda?
Mira 4-RESULTATS/v97_refundacio_20260924/cadena_raw/ i 4-RESULTATS/v98_20260925/cadena_raw/ (productes per fotograma = carpetes limb_frames*),
els rebuts dels apilats Sony (b2_sony_A/B) i el suport/pesos dels apilats Sony al llenç (sources_v29) per sector i distància al cercle.
Sortida: 4-RESULTATS/v100_detall_20260925/dada/Q4_INVENTARI_SONY.json"""
import json
from pathlib import Path
import numpy as np
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925/dada'; SORT = O / 'Q4_INVENTARI_SONY.json'; assert not SORT.exists()
C97 = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'; C98 = ARREL / '4-RESULTATS/v98_20260925/cadena_raw'
inv = dict(metode=__doc__, limb_frames={})
for c in (C97, C98):
    for p in sorted(c.glob('limb_frames*')):
        if p.is_dir() and (p / 'METADATA.json').exists():
            m = json.loads((p / 'METADATA.json').read_text()); noms = [f['name'] for f in m['frames']]
            inv['limb_frames'][str(p.relative_to(ARREL))] = dict(n=len(noms), camera='Vixen R6III (CR3)' if all(n.endswith('.CR3') for n in noms) else 'altres',
                                                                  sony=[n for n in noms if n.endswith('.ARW')])
rebuts = {}
for g, f in (('sony_A', C97 / 'b2_sony_A/receipts/B2_recomposicio.json'), ('sony_B', C97 / 'b2_sony_B/receipts/B2_sony_B.json')):
    d = json.loads(f.read_text()); fr = d['sony_A']['frames'] if g == 'sony_A' else d['frames']
    rebuts[g] = dict(n=len(fr), fotogrames=[(x['name'], x['exp']) for x in fr])
inv['apilats_sony_rebuts'] = rebuts
cau = {str(p.relative_to(ARREL)): p.stat().st_size for p in (C97 / 'b2_sony_A/cau').glob('*')} | {str(p.relative_to(ARREL)): p.stat().st_size for p in (C97 / 'b2_sony_B/cau').glob('*')}
inv['cau_sony'] = cau
raw = ARREL / '0-RAW/Sony A7RIIIA 300mm'; inv['raw_sony_arw'] = len(list(raw.glob('*.ARW'))) if raw.exists() else None
P = C97 / 'sources_v29'; LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; by0, by1, bx0, bx1 = 3077, 4477, 4677, 6077
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - LX, yy - LY) - RL; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
sup = np.load(P / 'sony_support.npy', mmap_mode='r')[by0:by1, bx0:bx1]; wg = np.load(P / 'sony_weight_G.npy', mmap_mode='r')[by0:by1, bx0:bx1]
cob = {}
for a0, a1 in ((75, 105), (105, 135), (150, 210), (205, 235), (235, 255), (285, 345)):
    z = (th >= a0) & (th < a1); cob[f'{a0}-{a1}'] = {f'd{b0}-{b1}': dict(suport=round(float(np.mean(sup[z & (d >= b0) & (d < b1)])), 3), pes_G_mediana=float(np.median(wg[z & (d >= b0) & (d < b1)])))
                                                     for b0, b1 in ((0, 2), (2, 4), (4, 6), (6, 10), (10, 20))}
inv['cobertura_apilats_sony_a_la_caixa'] = cob
SORT.write_text(json.dumps(inv, indent=1, ensure_ascii=False)); print(json.dumps({k: v for k, v in inv.items() if k != 'metode'}, ensure_ascii=False)[:3000])
