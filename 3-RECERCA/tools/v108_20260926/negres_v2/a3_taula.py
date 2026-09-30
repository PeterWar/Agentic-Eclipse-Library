"""a3 (V108 · negres_v2) · Taula compacta de tots els A1_<variant>.json: zones negres (A, B), contrast buit/plomall 4–64 px a 3–4,5 R☉, flamarada
a 3 i 4,5 R☉, detall 8–32 i 32–128 px a 3–4,5 R☉, Brno 230 (3–4,5 i 2–3 R☉), energia 2–8 px del ràster a 2–3 R☉ i píxels tocats a 1,3–2 R☉.
Ús: a3_taula.py [--json SORTIDA]"""
import json, sys
from pathlib import Path
OUT = Path(__file__).resolve().parents[4] / '4-RESULTATS/v108_20260926/negres_v2'; V = json.loads((OUT / 'A1_V107.json').read_text())
files = [f for f in sorted(OUT.glob('A1_*.json')) if f.stem != 'A1_V107']; rows = []
print(f"{'variant':28s} {'A%':>5s} {'B%':>5s} {'buit3':>6s} {'plom3':>6s} {'fl3':>6s} {'fl4.5':>6s} {'d8-32':>6s} {'d32+':>6s} {'Brno3':>6s} {'Brno2':>6s} {'rE2-8':>6s} {'toc1.3':>6s}")
for f in files:
    d = json.loads(f.read_text()); z = d['zones']; p1 = d['pas1']; bp = d['pas2']['buits_plomalls_4-64px']; bp0 = V['pas2']['buits_plomalls_4-64px']; r = d.get('raster_41', {})
    row = dict(variant=f.stem[3:], A=100 * z['A_cel_6.5-8.5']['total'], B=100 * z['B_cel_5-5.6_marc']['total'], buit3=bp['3-4.5']['buits_mitj_neg'] / bp0['3-4.5']['buits_mitj_neg'],
               plom3=bp['3-4.5']['plomalls_mitj_pos'] / bp0['3-4.5']['plomalls_mitj_pos'], fl3=p1['flamarada']['3']['p90_menys_p10_ln'] / V['pas1']['flamarada']['3']['p90_menys_p10_ln'],
               fl45=p1['flamarada']['4.5']['p90_menys_p10_ln'] / V['pas1']['flamarada']['4.5']['p90_menys_p10_ln'], d832=p1['3-4.5']['rms_8-32'] / V['pas1']['3-4.5']['rms_8-32'],
               d32=d['pas2']['rms_32-128']['3-4.5'] / V['pas2']['rms_32-128']['3-4.5'], brno3=p1['brno_corr_tangencial_2-64']['230']['3-4.5'], brno2=p1['brno_corr_tangencial_2-64']['230']['2-3'],
               rE=r['energia_raster_41']['2-8']['2-3'] if r else float('nan'), toc13=100 * r['per_bandes']['1.3-2']['frac_tocats_1_512'] if r else float('nan'))
    rows.append(row); print(f"{row['variant']:28s} " + ' '.join(f"{row[k]:{'5.2f' if k in ('A', 'B') else '6.3f' if k != 'toc13' else '6.2f'}}" for k in ('A', 'B', 'buit3', 'plom3', 'fl3', 'fl45', 'd832', 'd32', 'brno3', 'brno2', 'rE', 'toc13')))
print('V107: Brno 230 3–4,5 =', round(V['pas1']['brno_corr_tangencial_2-64']['230']['3-4.5'], 3), '· 2–3 =', round(V['pas1']['brno_corr_tangencial_2-64']['230']['2-3'], 3))
if '--json' in sys.argv: Path(sys.argv[sys.argv.index('--json') + 1]).write_text(json.dumps(rows, ensure_ascii=False, indent=1) + '\n')
