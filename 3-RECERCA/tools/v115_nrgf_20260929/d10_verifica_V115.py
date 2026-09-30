"""d10 · verificació de la V115 contra el contracte (4-RESULTATS/v115_nrgf_20260929/CONTRACTE_V115.json). Només lectura.
  1. Mateix inventari i ordre de capes que la V114 de Pere; cap capa nova.
  2. Mateixes propietats (marcs, opacitat, mode, clipping, màscara, visibilitat, nom) llevat de: 414 oculta; noms de 41/42/45/46 «V114» → «V115».
  3. Totes les capes fora de {41, 42, 45, 46, 301}: tots els canals byte a byte iguals a la V114 de Pere.
  4. 41, 42, 45, 46: RGB i alfa = regla del muntatge (V114, i on q(nou) ≠ q(control), q(nou)); màscara igual a la V114.
  5. 301: RGB = q(L301 regenerada); alfa igual a la V114.
  6. El compost desat = el render natiu visible_complet.tif.
  7. NEGATIVA: el predicat 4 aplicat a la V114 de Pere ha de FALLAR (causants sense corregir).
Ús: d10_verifica_V115.py <V115.psb> <nrgf_dir> <rhef_dir> <c301_dir> <render.tif> <sortida.json>"""
from pathlib import Path
import sys, json, hashlib
import numpy as np, tifffile
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, q_blocs
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
    return h.hexdigest()
V115, NG, RH, C301, TIF, OUT = [Path(x).resolve() for x in sys.argv[1:7]]
V114 = R / '1-PHOTOSHOP/V114.psb'; SHA114 = '854705bfcbbdf0dcb05906a1ab7dd7b40805caca65cf09333ad7a7ab309d4861'
CT = R / '4-RESULTATS/v114_estrelles_20260928/cadena/v114c'
FONT = {41: (NG / 'P01_NRGF_u16.npy', NG / 'P01_NRGF_alfa_u16.npy', CT / 'nrgf/G_MAX_T_e30_W_H0/P01_NRGF_u16.npy', CT / 'nrgf/G_MAX_T_e30_W_H0/P01_NRGF_alfa_u16.npy'),
        42: (NG / 'P01_NRGF_extrap_u16.npy', NG / 'P01_NRGF_extrap_alfa_u16.npy', CT / 'nrgf/G_MAX_T_e30_W_H0/P01_NRGF_extrap_u16.npy', CT / 'nrgf/G_MAX_T_e30_W_H0/P01_NRGF_extrap_alfa_u16.npy'),
        45: (RH / 'P02c_RHEF_local60_native_u16.npy', RH / 'P02c_RHEF_local60_native_alfa_u16.npy', CT / 'filtres_mass/filtres/P02c_RHEF_local60_native_u16.npy', CT / 'filtres_mass/filtres/P02c_RHEF_local60_native_alfa_u16.npy'),
        46: (RH / 'P02d_RHEF_local30_native_u16.npy', RH / 'P02d_RHEF_local30_native_alfa_u16.npy', CT / 'filtres_mass/filtres/P02d_RHEF_local30_native_u16.npy', CT / 'filtres_mass/filtres/P02d_RHEF_local30_native_alfa_u16.npy')}
assert sha(V114) == SHA114, 'la V114 de Pere ha canviat'
out = dict(fitxer=str(V115.relative_to(R)), sha256=sha(V115), bytes=V115.stat().st_size, font=dict(fitxer=str(V114.relative_to(R)), sha256=SHA114),
           contracte=str((R / '4-RESULTATS/v115_nrgf_20260929/CONTRACTE_V115.json').relative_to(R)), nrgf=str(NG.relative_to(R)), rhef=str(RH.relative_to(R)), c301=str(C301.relative_to(R)))
a, v = PSB(str(V115)), PSB(str(V114))
ids_a = [l['id'] for l in a.layers]; ids_v = [l['id'] for l in v.layers]
out['1_inventari_i_ordre_iguals_a_la_V114'] = ids_a == ids_v
props = []
for la, lv in zip(a.layers, v.layers):
    for k in ('left', 'top', 'right', 'bottom', 'opacity', 'blend', 'clipping', 'mask', 'visible', 'name'):
        if la[k] == lv[k]: continue
        if k == 'visible' and la['id'] == 414 and lv[k] and not la[k]: continue
        if k == 'name' and la['id'] in FONT and la[k] == lv[k].replace('V114', 'V115', 1): continue
        props.append(dict(id=la['id'], camp=k, v115=la[k], v114=lv[k]))
out['2_propietats_diferents_no_previstes'] = props
out['2_414_oculta'] = not a.layer(414)['visible']
dif = []; n = 0
for la in a.layers:
    lid = la['id']
    if lid in FONT or lid == 301: continue
    if sorted(la['chans']) != sorted(v.layer(lid)['chans']): dif.append(dict(id=lid, problema='canals')); continue
    for cid in la['chans']:
        x, ox = a.channel(lid, cid); y, oy = v.channel(lid, cid); n += 1
        if ox != oy or x.shape != y.shape or not np.array_equal(x, y): dif.append(dict(id=lid, canal=cid))
out['3_canals_iguals_a_la_V114'] = dict(comprovats=n, diferents=dif)
def esperat(p, lid, cid):
    fn, fa, cn, ca = FONT[lid]
    if cid == -1: n_, c_ = q_blocs(np.load(fa)), q_blocs(np.load(ca))
    else: n_, c_ = q_blocs(np.load(fn)), q_blocs(np.load(cn))
    act, _ = v.channel(lid, cid); e = act.copy(); ch = n_ != c_; e[ch] = n_[ch]; return e, int(ch.sum())
cau = {}
for lid in FONT:
    for cid in (0, 1, 2, -1):
        e, nch = esperat(v, lid, cid); x, _ = a.channel(lid, cid); y, _ = v.channel(lid, cid)
        cau[f'{lid}/{cid}'] = dict(igual_a_l_esperat=bool(np.array_equal(x, e)), px_canviats=nch, v114_ja_era_l_esperat=bool(np.array_equal(y, e)))
    xm, _ = a.channel(lid, -2); ym, _ = v.channel(lid, -2); cau[f'{lid}/mascara_igual_V114'] = bool(np.array_equal(xm, ym))
out['4_causants_corregits_al_seu_lloc'] = cau
ok4 = all(d['igual_a_l_esperat'] for k, d in cau.items() if isinstance(d, dict)) and all(d for k, d in cau.items() if not isinstance(d, dict))
neg = all(d['v114_ja_era_l_esperat'] for k, d in cau.items() if isinstance(d, dict) and d['px_canviats'] > 0)
out['7_negativa_la_V114_falla_el_predicat_4'] = not neg
c301 = {}
for cid in (0, 1, 2):
    e = q_blocs(np.load(C301 / f'L301_c{cid}.npy')); x, _ = a.channel(301, cid); c301[str(cid)] = bool(np.array_equal(x, e))
xa, _ = a.channel(301, -1); ya, _ = v.channel(301, -1); c301['alfa_igual_V114'] = bool(np.array_equal(xa, ya))
out['5_301_regenerada'] = c301
comp = a.composite()[..., :3]; tif = tifffile.imread(TIF)
out['6_compost_igual_al_render_natiu'] = bool(np.array_equal(comp, tif)); out['6_dif_max'] = int(np.abs(comp.astype(np.int32) - tif.astype(np.int32)).max())
out['render'] = dict(fitxer=str(TIF.relative_to(R)), sha256=sha(TIF))
passa = (out['1_inventari_i_ordre_iguals_a_la_V114'] and not props and out['2_414_oculta'] and not dif and ok4 and all(c301.values())
         and out['6_compost_igual_al_render_natiu'] and out['7_negativa_la_V114_falla_el_predicat_4'])
out['veredicte_metode_i_fitxer'] = 'PASSA' if passa else 'FALLA'
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False)); print(json.dumps({k: out[k] for k in out if k not in ('4_causants_corregits_al_seu_lloc',)}, ensure_ascii=False, indent=1)[:3000])
