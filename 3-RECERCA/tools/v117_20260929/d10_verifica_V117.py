"""d10 · verificació de la V117 contra el contracte (4-RESULTATS/v117_20260929/CONTRACTE_V117.json). Només lectura. Còpia de v116/d10 sense els causants.
  1. Inventari i ordre = els de la V115 de Pere amb UNA capa nova, la 415, just damunt de la 56.
  2. Mateixes propietats (marcs, opacitat, mode, clipping, màscara, visibilitat, nom) llevat de la 414 oculta. La 415: Superposar, opacitat 64
     (25 %), visible, llenç sencer, sense màscara, nom Unicode «Detall radial coherent Sony A·B · V117».
  3. Totes les capes de la V115 fora de la 301: tots els canals iguals als de la V115 de Pere (l'estètica de la V115, byte a byte).
  4. 301: RGB = q(L301 regenerada); alfa igual a la V115.  4b. 415: RGB = q(L415_G), alfa = q(L415_alfa).
  5. El compost desat = el render natiu visible_complet.tif.
  6. NEGATIVA: la V115 de Pere ha de FALLAR el predicat de la capa nova (no porta la 415 amb el ràster del filtre).
Ús: d10_verifica_V117.py <V117.psb> <c301_dir> <capa415_dir> <render.tif> <sortida.json>"""
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
V117, C301, C415, TIF, OUT = [Path(x).resolve() for x in sys.argv[1:6]]
V115 = R / '1-PHOTOSHOP/V115.psb'; SHA115 = '4fd1e803ac9e0a61ed53caa0ddfb5f7b9b5d47a276fa9161f148da874c321b3c'
NOM = 'Detall radial coherent Sony A·B · V117'; OPAC = 64
assert sha(V115) == SHA115, 'la V115 de Pere ha canviat'
out = dict(fitxer=str(V117.relative_to(R)), sha256=sha(V117), bytes=V117.stat().st_size, font=dict(fitxer=str(V115.relative_to(R)), sha256=SHA115),
           contracte='4-RESULTATS/v117_20260929/CONTRACTE_V117.json', c301=str(C301.relative_to(R)), capa415=str(C415.relative_to(R)))
a, v = PSB(str(V117)), PSB(str(V115))
ids_a = [l['id'] for l in a.layers]; ids_v = [l['id'] for l in v.layers]
out['1_inventari_i_ordre_V115_mes_415_damunt_de_56'] = ids_a == ids_v[:ids_v.index(56) + 1] + [415] + ids_v[ids_v.index(56) + 1:]
props = []
for lid in ids_v:
    la, lv = a.layer(lid), v.layer(lid)
    for k in ('left', 'top', 'right', 'bottom', 'opacity', 'blend', 'clipping', 'mask', 'visible', 'name'):
        if la[k] == lv[k]: continue
        if k == 'visible' and lid == 414 and lv[k] and not la[k]: continue
        props.append(dict(id=lid, camp=k, v117=la[k], v115=lv[k]))
out['2_propietats_diferents_no_previstes'] = props
out['2_414_oculta'] = not a.layer(414)['visible']
def pred_415(p, path):
    """la capa nova: propietats i ràster del filtre. Torna (ok, detall)."""
    if 415 not in [l['id'] for l in p.layers]: return False, 'sense capa 415'
    n4 = p.layer(415); nomu = {rid(r): nom_de(r) for r, _ in llegeix_registres(path)['recs']}[415]
    G = q_blocs(np.load(C415 / 'L415_G.npy')); AL = q_blocs(np.load(C415 / 'L415_alfa.npy'))
    det = dict(nom_unicode=nomu, mode=n4['blend'], opacitat=n4['opacity'], visible=n4['visible'], caixa=[n4['left'], n4['top'], n4['right'], n4['bottom']], mascara=n4['mask'] is not None,
               raster={str(c): bool(np.array_equal(p.channel(415, c)[0], G)) for c in (0, 1, 2)}, alfa=bool(np.array_equal(p.channel(415, -1)[0], AL)))
    ok = (nomu == NOM and n4['blend'] == 'OVERLAY' and n4['opacity'] == OPAC and n4['visible'] and n4['mask'] is None and not n4['clipping']
          and det['caixa'] == [0, 0, p.width, p.height] and all(det['raster'].values()) and det['alfa'])
    return ok, det
ok415, out['2_4b_415'] = pred_415(a, V117)
dif = []; n = 0
for lid in ids_v:
    if lid == 301: continue
    la = a.layer(lid)
    if sorted(la['chans']) != sorted(v.layer(lid)['chans']): dif.append(dict(id=lid, problema='canals')); continue
    for cid in la['chans']:
        x, ox = a.channel(lid, cid); y, oy = v.channel(lid, cid); n += 1
        if ox != oy or x.shape != y.shape or not np.array_equal(x, y): dif.append(dict(id=lid, canal=cid))
out['3_canals_iguals_a_la_V115'] = dict(comprovats=n, diferents=dif)
c301 = {}
for cid in (0, 1, 2):
    e = q_blocs(np.load(C301 / f'L301_c{cid}.npy')); x, _ = a.channel(301, cid); c301[str(cid)] = bool(np.array_equal(x, e))
xa, _ = a.channel(301, -1); ya, _ = v.channel(301, -1); c301['alfa_igual_V115'] = bool(np.array_equal(xa, ya))
out['4_301_regenerada'] = c301
comp = a.composite()[..., :3]; tif = tifffile.imread(TIF)
out['5_compost_igual_al_render_natiu'] = bool(np.array_equal(comp, tif)); out['5_dif_max'] = int(np.abs(comp.astype(np.int32) - tif.astype(np.int32)).max())
out['render'] = dict(fitxer=str(TIF.relative_to(R)), sha256=sha(TIF))
neg_ok, neg_det = pred_415(v, V115); out['6_negativa_la_V115_falla_el_predicat_415'] = dict(falla=not neg_ok, detall=neg_det)
passa = (out['1_inventari_i_ordre_V115_mes_415_damunt_de_56'] and not props and out['2_414_oculta'] and ok415 and not dif and all(c301.values())
         and out['5_compost_igual_al_render_natiu'] and not neg_ok)
out['veredicte_metode_i_fitxer'] = 'PASSA' if passa else 'FALLA'
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False)); print(json.dumps(out, ensure_ascii=False, indent=1)[:3000])
