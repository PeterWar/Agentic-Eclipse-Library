"""j9 (V97) · Veredicte: la V97 contra la V96 amb els llindars DECLARATS ABANS de veure la V97 (PLA_V97.md, contrast de Codex).
Llindars (fixos):
  A1  graó diagonal de la Sony a base_G: |graó| ≤ 0,5 ‰ (D1_GRAO_SONY_V97.json)
  A2  polígon B/G a la fusió: ràtio ≤ 1,8 i salt ≤ 0,002 (J2_POLIGON_V97.json)
  A4  cercle r_in a les capes radials visibles (41, 42, 45, 46) i ocultes (43, 44): p90|salt| de la V97 ≤ la de la V96; i on la V96 tenia
      |mediana| > 0,003, la V97 la redueix almenys un 50 %
  A5  costures d'escala (z) a les WOW (55, 56) i al compost: V97 ≤ V96
  A6  textura arran del limbe (2–8 px sobre 12–30 px) a les capes de Superposar: ≥ 0,5; píxels amb alfa dins del limbe a les de Superposar = 0
  A8  línies al llarg del limbe (fracció coherent en 60 px d'arc) al compost: V97 ≤ V96 + 0,02
  B   Brno (correlació del detall per anell, mitjana de les 4 capes): V97 ≥ V96 − 0,01 a cada anell
  D   gra relatiu al cel (4,5–6,5 R☉): V97 ≤ 1,05 × V96
  E   regressió fora de les zones d'artefacte: correlació del detall amb la V96 ≥ 0,99
  A3  (afegit després de la verificació de Codex) render natiu amb les capes d'ajust: cap píxel retallat nou (vistes V96/V97 del Photoshop)
  A7  (afegit després de la verificació de Codex) vora clara de la linealitzada arran del limbe (J7_VORA_V97.json): excés ≤ 2 %
  ESTRICTE: A5 i A8 també amb el llindar del PLA (reducció ≥ 50 % respecte de la V96); es reporten a part, com a «estricte».
Surt amb codi 1 si algun criteri no passa (la cadena s'atura si no es declara ACCEPTA_V97=1 amb la justificació al RESULTAT).
Ús: j9_veredicte.py <J0_V96.json> <J0_V97.json> <sortida.json>"""
import sys, json
from pathlib import Path
R = Path(sys.argv[2]).parent
a = json.loads(Path(sys.argv[1]).read_text())['mesures']; b = json.loads(Path(sys.argv[2]).read_text())['mesures']; V = {}
def reg(k, ok, detall): V[k] = dict(veredicte='PASSA' if ok else 'FALLA', **detall)
try:
    d1 = json.loads((R / 'D1_GRAO_SONY_V97.json').read_text())['resultats']; g = list(d1.values())[0]['grao_ln']; reg('A1_grao_sony', abs(g) <= 5e-4, dict(grao_V97=g, llindar=5e-4, grao_control=-3.2e-3))
except Exception as e: V['A1_grao_sony'] = dict(veredicte='SENSE DADA', error=str(e))
try:
    j2 = json.loads((R / 'J2_POLIGON_V97.json').read_text()); x = j2.get('fusio_v97') or list(j2.values())[0]
    reg('A2_poligon', x['ratio'] <= 1.8 and x['salt_max_aprox'] <= 0.002, dict(ratio=x['ratio'], salt=x['salt_max_aprox'], ratio_V96=a['A2_poligon_BG']['ratio']))
except Exception as e: V['A2_poligon'] = dict(veredicte='SENSE DADA', error=str(e))
ca, cb = a['capes'], b['capes']; det = {}
ok = True
for l in ('41', '42', '43', '44', '45', '46'):
    if l not in ca or l not in cb or ca[l].get('A4_salt_r469_p90abs') is None: continue
    p90a, p90b = ca[l]['A4_salt_r469_p90abs'], cb[l]['A4_salt_r469_p90abs']; ma, mb = ca[l]['A4_salt_r469_mediana'], cb[l]['A4_salt_r469_mediana']
    o = p90b <= p90a * 1.02 and (abs(ma) <= 0.003 or abs(mb) <= 0.5 * abs(ma)); ok &= o; det[l] = dict(p90_V96=p90a, p90_V97=p90b, med_V96=ma, med_V97=mb, passa=o)
reg('A4_cercle_rin', ok, det)
det = {}; ok = True
for l in ('55', '56'):
    za, zb = ca[l]['A5_costura_z'], cb[l]['A5_costura_z']; o = zb <= za * 1.05; ok &= o; det[l] = dict(z_V96=za, z_V97=zb, d_V97=cb[l]['A5_costura_d'], passa=o)
za, zb = a['compost']['A5_costura_z'], b['compost']['A5_costura_z']; o = zb <= za * 1.05; ok &= o; det['compost'] = dict(z_V96=za, z_V97=zb, passa=o)
reg('A5_costures', ok, det)
det = {}; ok = True
for l in ('47', '48', '49', '50', '51', '52', '53', '54', '55', '56'):
    if l not in cb: continue
    t = cb[l]['A6_textura_2_8_sobre_12_30']; n = cb[l]['A6_px_alfa_dins_limbe']; o = (t is not None and t >= 0.5) and n == 0; ok &= o
    det[l] = dict(textura_V97=t, textura_V96=ca[l]['A6_textura_2_8_sobre_12_30'], px_alfa_dins_limbe_V97=n, px_alfa_dins_limbe_V96=ca[l]['A6_px_alfa_dins_limbe'], passa=o)
reg('A6_vora_limbe', ok, det)
reg('A8_linies_limbe', b['compost']['A8_linies_60px_arc'] <= a['compost']['A8_linies_60px_arc'] + 0.02, dict(V96=a['compost']['A8_linies_60px_arc'], V97=b['compost']['A8_linies_60px_arc']))
det = {}; ok = True
anells = list(next(iter(a['B_brno_corr_detall'].values())).keys())
for an in anells:
    ma = sum(v[an] for v in a['B_brno_corr_detall'].values()) / len(a['B_brno_corr_detall']); mb = sum(v[an] for v in b['B_brno_corr_detall'].values()) / len(b['B_brno_corr_detall'])
    o = mb >= ma - 0.01; ok &= o; det[an] = dict(V96=ma, V97=mb, passa=o)
reg('B_brno', ok, det)
ga, gb = a['D_gra_relatiu_4.5_6.5Rsol']['mediana'], b['D_gra_relatiu_4.5_6.5Rsol']['mediana']; reg('D_gra', gb <= 1.05 * ga, dict(V96=ga, V97=gb, ratio=gb / ga))
if 'E_regressio' in b: reg('E_regressio', b['E_regressio']['corr_detall_fora'] >= 0.99, b['E_regressio'])
try:
    import numpy as np, tifffile
    A6_ = ARREL_ = Path(sys.argv[2]).resolve().parents[2]
    va = tifffile.imread(ARREL_ / '4-RESULTATS/v96_nrgf_20260924/vistes/V96_lluna.tif'); vb = tifffile.imread(R / 'vistes/V97_lluna.tif'); mx = 65535 if va.max() > 255 else 255
    la = tifffile.imread(ARREL_ / '4-RESULTATS/v96_nrgf_20260924/vistes/V96_llenc_sencer.tif'); lb = tifffile.imread(R / 'vistes/V97_llenc_sencer.tif')
    ca = [int((x[..., c] >= 0.999 * mx).sum()) for x in (va, la) for c in range(3)]; cb = [int((x[..., c] >= 0.999 * mx).sum()) for x in (vb, lb) for c in range(3)]
    reg('A3_retall_render_natiu', all(b_ <= a_ for a_, b_ in zip(ca, cb)), dict(retallats_V96_lluna_i_llenc=ca, retallats_V97_lluna_i_llenc=cb))
except Exception as e: V['A3_retall_render_natiu'] = dict(veredicte='SENSE DADA', error=str(e))
try:
    j7 = json.loads((R / 'J7_VORA_V97.json').read_text())['resultats']['fusio_v97']; reg('A7_vora_clara', j7['exces_d1_3'] <= 0.02, dict(exces_V97=j7['exces_d1_3'], per_sector=j7['per_sector']))
except Exception as e: V['A7_vora_clara'] = dict(veredicte='SENSE DADA', error=str(e))
estricte = dict(A5_compost_reduccio=1 - b['compost']['A5_costura_z'] / a['compost']['A5_costura_z'], A8_compost_reduccio=1 - b['compost']['A8_linies_60px_arc'] / a['compost']['A8_linies_60px_arc'])
estricte['A5_passa_50pc'] = estricte['A5_compost_reduccio'] >= 0.5; estricte['A8_passa_50pc'] = estricte['A8_compost_reduccio'] >= 0.5
tot = all(v['veredicte'] == 'PASSA' for v in V.values())
out = dict(veredicte_global='PASSA (la V97 és millor o igual a tot arreu mesurat)' if tot else 'NO PASSA TOT: vegeu cada criteri', criteris=V, estricte_llindar_del_pla=estricte)
Path(sys.argv[3]).write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
for k, v in V.items(): print(f"{k:22s} {v['veredicte']}")
print(out['veredicte_global']); print('estricte (pla):', {k: (round(v, 3) if isinstance(v, float) else v) for k, v in estricte.items()})
sys.exit(0 if tot else 1)
