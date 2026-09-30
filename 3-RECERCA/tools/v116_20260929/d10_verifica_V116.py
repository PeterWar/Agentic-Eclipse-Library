"""d10 · verificació de la V116 contra el contracte (4-RESULTATS/v116_20260929/CONTRACTE_V116.json). Només lectura.
  1. Inventari i ordre = els de la V115 de Pere amb UNA capa nova, la 415, just damunt de la 56.
  2. Mateixes propietats (marcs, opacitat, mode, clipping, màscara, visibilitat, nom) llevat de: 414 oculta; noms de 41/42/45/46 «V115» → «V116».
     La 415: Superposar, opacitat 102, visible (oculta amb --415-oculta), llenç sencer, sense màscara, nom Unicode «Detall radial coherent Sony A·B · V116».
  3. Totes les capes fora de {41, 42, 45, 46, 301, 415}: tots els canals iguals als de la V115 de Pere.
  4. 41, 42, 45, 46: RGB i alfa = regla del muntatge (V115, i on q(nou) ≠ q(control), q(nou)); màscara igual a la V115.
  5. 301: RGB = q(L301 regenerada); alfa igual a la V115.  5b. 415: RGB = q(L415_G), alfa = q(L415_alfa).
  6. El compost desat = el render natiu visible_complet.tif.
  7. NEGATIVA: el predicat 4 aplicat a la V115 de Pere ha de FALLAR (causants sense corregir).
Ús: d10_verifica_V116.py <V116.psb> <nrgf_dir> <rhef_dir> <c301_dir> <capa415_dir> <render.tif> <sortida.json> [--415-oculta]"""
from pathlib import Path
import sys, json, hashlib
import numpy as np, tifffile
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, q_blocs, llegeix_registres, rid, nom_de
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
    return h.hexdigest()
V116, NG, RH, C301, C415, TIF, OUT = [Path(x).resolve() for x in sys.argv[1:8]]
VIS415 = not (len(sys.argv) > 8 and sys.argv[8] == '--415-oculta')   # la V116 lliurada la porta oculta
V115 = R / '1-PHOTOSHOP/V115.psb'; SHA115 = '4fd1e803ac9e0a61ed53caa0ddfb5f7b9b5d47a276fa9161f148da874c321b3c'
C5 = R / '4-RESULTATS/v115_nrgf_20260929'
FONT = {41: (NG / 'P01_NRGF_u16.npy', NG / 'P01_NRGF_alfa_u16.npy', C5 / 'nrgf_rL0/Lk20_G_MAX_T_e30_W_H0/P01_NRGF_u16.npy', C5 / 'nrgf_rL0/Lk20_G_MAX_T_e30_W_H0/P01_NRGF_alfa_u16.npy'),
        42: (NG / 'P01_NRGF_extrap_u16.npy', NG / 'P01_NRGF_extrap_alfa_u16.npy', C5 / 'nrgf_rL0/Lk20_G_MAX_T_e30_W_H0/P01_NRGF_extrap_u16.npy', C5 / 'nrgf_rL0/Lk20_G_MAX_T_e30_W_H0/P01_NRGF_extrap_alfa_u16.npy'),
        45: (RH / 'P02c_RHEF_local60_native_u16.npy', RH / 'P02c_RHEF_local60_native_alfa_u16.npy', C5 / 'rhefL/k0_s400/P02c_RHEF_local60_native_u16.npy', C5 / 'rhefL/k0_s400/P02c_RHEF_local60_native_alfa_u16.npy'),
        46: (RH / 'P02d_RHEF_local30_native_u16.npy', RH / 'P02d_RHEF_local30_native_alfa_u16.npy', C5 / 'rhefL/k0_s400/P02d_RHEF_local30_native_u16.npy', C5 / 'rhefL/k0_s400/P02d_RHEF_local30_native_alfa_u16.npy')}
assert sha(V115) == SHA115, 'la V115 de Pere ha canviat'
out = dict(fitxer=str(V116.relative_to(R)), sha256=sha(V116), bytes=V116.stat().st_size, font=dict(fitxer=str(V115.relative_to(R)), sha256=SHA115),
           contracte='4-RESULTATS/v116_20260929/CONTRACTE_V116.json', nrgf=str(NG.relative_to(R)), rhef=str(RH.relative_to(R)), c301=str(C301.relative_to(R)), capa415=str(C415.relative_to(R)))
a, v = PSB(str(V116)), PSB(str(V115))
ids_a = [l['id'] for l in a.layers]; ids_v = [l['id'] for l in v.layers]
esperat_ids = ids_v[:ids_v.index(56) + 1] + [415] + ids_v[ids_v.index(56) + 1:]
out['1_inventari_i_ordre_V115_mes_415_damunt_de_56'] = ids_a == esperat_ids
props = []
for lid in ids_v:
    la, lv = a.layer(lid), v.layer(lid)
    for k in ('left', 'top', 'right', 'bottom', 'opacity', 'blend', 'clipping', 'mask', 'visible', 'name'):
        if la[k] == lv[k]: continue
        if k == 'visible' and lid == 414 and lv[k] and not la[k]: continue
        if k == 'name' and lid in FONT and la[k] == lv[k].replace('V115', 'V116', 1): continue
        props.append(dict(id=lid, camp=k, v116=la[k], v115=lv[k]))
out['2_propietats_diferents_no_previstes'] = props
out['2_414_oculta'] = not a.layer(414)['visible']
n4 = a.layer(415)
NOMU = {rid(r): nom_de(r) for r, _ in llegeix_registres(V116)['recs']}   # el nom Unicode (psb69 dona el nom Pascal, tallat a 31 caràcters)
out['2_415_propietats'] = dict(nom_unicode=NOMU[415], nom_pascal=n4['name'], mode=n4['blend'], opacitat=n4['opacity'], visible=n4['visible'], caixa=[n4['left'], n4['top'], n4['right'], n4['bottom']], mascara=n4['mask'] is not None, clipping=n4['clipping'])
ok415p = (NOMU[415] == 'Detall radial coherent Sony A·B · V116' and n4['blend'] == 'OVERLAY' and n4['opacity'] == 102 and n4['visible'] == VIS415 and n4['mask'] is None
          and [n4['left'], n4['top'], n4['right'], n4['bottom']] == [0, 0, a.width, a.height] and not n4['clipping'])
dif = []; n = 0
for lid in ids_v:
    la = a.layer(lid)
    if lid in FONT or lid == 301: continue
    if sorted(la['chans']) != sorted(v.layer(lid)['chans']): dif.append(dict(id=lid, problema='canals')); continue
    for cid in la['chans']:
        x, ox = a.channel(lid, cid); y, oy = v.channel(lid, cid); n += 1
        if ox != oy or x.shape != y.shape or not np.array_equal(x, y): dif.append(dict(id=lid, canal=cid))
out['3_canals_iguals_a_la_V115'] = dict(comprovats=n, diferents=dif)
def esperat(lid, cid):
    fn, fa, cn, ca = FONT[lid]
    if cid == -1: n_, c_ = q_blocs(np.load(fa)), q_blocs(np.load(ca))
    else: n_, c_ = q_blocs(np.load(fn)), q_blocs(np.load(cn))
    act, _ = v.channel(lid, cid); e = act.copy(); ch = n_ != c_; e[ch] = n_[ch]; return e, int(ch.sum())
cau = {}
for lid in FONT:
    for cid in (0, 1, 2, -1):
        e, nch = esperat(lid, cid); x, _ = a.channel(lid, cid); y, _ = v.channel(lid, cid)
        cau[f'{lid}/{cid}'] = dict(igual_a_l_esperat=bool(np.array_equal(x, e)), px_canviats=nch, v115_ja_era_l_esperat=bool(np.array_equal(y, e)))
    xm, _ = a.channel(lid, -2); ym, _ = v.channel(lid, -2); cau[f'{lid}/mascara_igual_V115'] = bool(np.array_equal(xm, ym))
out['4_causants_corregits_al_seu_lloc'] = cau
ok4 = all(d['igual_a_l_esperat'] for k, d in cau.items() if isinstance(d, dict)) and all(d for k, d in cau.items() if not isinstance(d, dict))
neg = all(d['v115_ja_era_l_esperat'] for k, d in cau.items() if isinstance(d, dict) and d['px_canviats'] > 0)
out['7_negativa_la_V115_falla_el_predicat_4'] = not neg
c301 = {}
for cid in (0, 1, 2):
    e = q_blocs(np.load(C301 / f'L301_c{cid}.npy')); x, _ = a.channel(301, cid); c301[str(cid)] = bool(np.array_equal(x, e))
xa, _ = a.channel(301, -1); ya, _ = v.channel(301, -1); c301['alfa_igual_V115'] = bool(np.array_equal(xa, ya))
out['5_301_regenerada'] = c301
G = q_blocs(np.load(C415 / 'L415_G.npy')); AL = q_blocs(np.load(C415 / 'L415_alfa.npy'))
c415 = {str(c): bool(np.array_equal(a.channel(415, c)[0], G)) for c in (0, 1, 2)}; c415['alfa'] = bool(np.array_equal(a.channel(415, -1)[0], AL))
out['5b_415_raster'] = c415
comp = a.composite()[..., :3]; tif = tifffile.imread(TIF)
out['6_compost_igual_al_render_natiu'] = bool(np.array_equal(comp, tif)); out['6_dif_max'] = int(np.abs(comp.astype(np.int32) - tif.astype(np.int32)).max())
out['render'] = dict(fitxer=str(TIF.relative_to(R)), sha256=sha(TIF))
passa = (out['1_inventari_i_ordre_V115_mes_415_damunt_de_56'] and not props and out['2_414_oculta'] and ok415p and not dif and ok4 and all(c301.values())
         and all(c415.values()) and out['6_compost_igual_al_render_natiu'] and out['7_negativa_la_V115_falla_el_predicat_4'])
out['veredicte_metode_i_fitxer'] = 'PASSA' if passa else 'FALLA'
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False)); print(json.dumps({k: out[k] for k in out if k not in ('4_causants_corregits_al_seu_lloc',)}, ensure_ascii=False, indent=1)[:3500])
