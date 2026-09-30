"""d10 · verificació de la V120 contra el contracte (4-RESULTATS/v120_20260929/CONTRACTE_V120.json). Només lectura. Adaptat de v119/d10.
Les taules de fonts són pròpies (no s'importen del muntatge): la verificació no es pot equivocar de la mateixa manera que el muntatge.
  1. Inventari i ordre = els de la V119 amb DUES capes noves, la 419 (ordit) i la 420 (trama), just damunt de la 418.
  2. Mateixes propietats (marcs, opacitat, mode, clipping, màscara, visibilitat, nom) llevat de: la 417 i la 418, ocultes; el nom de les capes
     refetes, on només pot canviar l'etiqueta de versió (V114/V115 → V120).
  3. Les capes que no es refan (entre elles TOTES les de Pere) i fora de la 301: tots els canals iguals als de la V119, byte a byte.
  3b. Les capes refetes (3, 54, 41, 42, 47, 49, 51, 45, 46, 55, 56; 202, 203; 230–232): cada canal = el de la V119 amb q(nou) allà on q(nou) ≠
     q(control), i res més (la regla de control de la V114/V115).
  4. 301: RGB i alfa = q(L301 regenerada) (regenera_301_v120: el triangle buit creix amb la vora del camp de la Sony deformada); el rebut
     ha de provar que la mateixa recepta torna EXACTAMENT l'alfa de la V119 i de la V115 sobre el render de la V119 (l'alfa no és un retoc).  4b. 419 i 420: Superposar, opacitat, visibles, llenç sencer, sense màscara, noms,
     RGB = q(ràster), alfa 0 on és exactament neutra.
  5. El compost desat = el render natiu visible_complet.tif.
  6. NEGATIVA: la V119 ha de FALLAR els predicats 3b (la 56 i la 202) i 4b.
Ús: d10_verifica_V120.py <V120.psb> <c301_dir> <capa_ordit> <capa_trama> <render.tif> <sortida.json> [--opac419 64] [--opac420 102]"""
from pathlib import Path
import sys, json, hashlib, re
import numpy as np, tifffile
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, q_blocs, llegeix_registres, rid, nom_de
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): h.update(b)
    return h.hexdigest()
V120, C301, CO, CT, TIF, OUT = [Path(x).resolve() for x in sys.argv[1:7]]
OP = {419: int(sys.argv[sys.argv.index('--opac419') + 1]) if '--opac419' in sys.argv else 64, 420: int(sys.argv[sys.argv.index('--opac420') + 1]) if '--opac420' in sys.argv else 102}
V119 = R / '1-PHOTOSHOP/V119.psb'; SHA119 = 'dafd8d4b7f351a82e3c7535493253b117b9aae311836290d7c6b46bc227eb015'
NOVES = {419: ('Ordit: raigs confirmats per tres testimonis, sense estrelles · V120', OP[419], CO), 420: ('Trama: arcs confirmats per tres testimonis, sense estrelles · V120', OP[420], CT)}
SOTA, AMAGADES = 418, (417, 418)
N = R / '4-RESULTATS/v120_20260929/cadena/v120'; K = R / '4-RESULTATS/v114_estrelles_20260928/cadena/v114c'; K5 = R / '4-RESULTATS/v115_nrgf_20260929'
def g(nou, ctl, lid): return dict(nou=nou, ctl=ctl)
TAULA = {}
for lid in (54, 47, 49, 51, 55, 56): TAULA[lid] = [(c, N / f'estat_v108/L{lid}_G.npy', K / f'estat_v108/L{lid}_G.npy', None) for c in (0, 1, 2)] + [(-1, N / f'estat_v108/L{lid}_alfa.npy', K / f'estat_v108/L{lid}_alfa.npy', None)]
TAULA[3] = [(c, N / 'estat_v108/L3_RGB.npy', K / 'estat_v108/L3_RGB.npy', c) for c in (0, 1, 2)] + [(-1, N / 'estat_v108/L3_alfa.npy', K / 'estat_v108/L3_alfa.npy', None)]
for lid, tg, sub_n, sub_k in ((45, 'P02c_RHEF_local60_native', 'rhefL/k0_s400', 'rhefL/k0_s400'), (46, 'P02d_RHEF_local30_native', 'rhefL/k0_s400', 'rhefL/k0_s400'),
                              (41, 'P01_NRGF', 'nrgf/Lk20_G_MAX_T_e30_W_H0', 'nrgf_rL0/Lk20_G_MAX_T_e30_W_H0'), (42, 'P01_NRGF_extrap', 'nrgf/Lk20_G_MAX_T_e30_W_H0', 'nrgf_rL0/Lk20_G_MAX_T_e30_W_H0')):
    TAULA[lid] = [(c, N / f'{sub_n}/{tg}_u16.npy', K5 / f'{sub_k}/{tg}_u16.npy', None) for c in (0, 1, 2)] + [(-1, N / f'{sub_n}/{tg}_alfa_u16.npy', K5 / f'{sub_k}/{tg}_alfa_u16.npy', None)]
E = R / '4-RESULTATS/v120_20260929/estrelles'; B = R / '4-RESULTATS/v120_20260929/brno'
NPZ = {202: (E / 'estrelles_202_V120.npz', R / '4-RESULTATS/v114_estrelles_20260928/estrelles_202_V114.npz', {0: 'R', 1: 'G', 2: 'B', -1: 'A', -2: 'M'}),
       203: (E / 'mapa_203_V120.npz', R / '4-RESULTATS/v114_estrelles_20260928/mapa/mapa_203_V114_v2.npz', {0: 'R', 1: 'G', 2: 'B', -2: 'M'})}
for lid in (230, 231, 232): NPZ[lid] = (B / f'L{lid}.npz', R / f'4-RESULTATS/v113_estrelles_20260928/brno/L{lid}.npz', {0: 'R', 1: 'G', 2: 'B', -1: 'A'})
REFETES = set(TAULA) | set(NPZ)
def parells(lid):
    if lid in TAULA:
        for c, fn, fk, idx in TAULA[lid]:
            n_ = np.load(fn, mmap_mode='r'); k_ = np.load(fk, mmap_mode='r')
            yield c, q_blocs(np.asarray(n_[..., idx] if idx is not None else n_)), q_blocs(np.asarray(k_[..., idx] if idx is not None else k_))
    else:
        fn, fk, cc = NPZ[lid]; zn, zk = np.load(fn), np.load(fk)
        for c, k in cc.items(): yield c, q_blocs(zn[k]), q_blocs(zk[k])
assert sha(V119) == SHA119, 'la V119 ha canviat'
out = dict(fitxer=str(V120.relative_to(R)), sha256=sha(V120), bytes=V120.stat().st_size, font=dict(fitxer=str(V119.relative_to(R)), sha256=SHA119),
           contracte='4-RESULTATS/v120_20260929/CONTRACTE_V120.json', c301=str(C301.relative_to(R)), capa_ordit=str(CO.relative_to(R)), capa_trama=str(CT.relative_to(R)))
a, v = PSB(str(V120)), PSB(str(V119))
ids_a = [l['id'] for l in a.layers]; ids_v = [l['id'] for l in v.layers]
out['1_inventari_i_ordre_V119_mes_419_420_damunt_de_418'] = ids_a == ids_v[:ids_v.index(SOTA) + 1] + [419, 420] + ids_v[ids_v.index(SOTA) + 1:]
nom_a = {rid(r): nom_de(r) for r, _ in llegeix_registres(V120)['recs']}; nom_v = {rid(r): nom_de(r) for r, _ in llegeix_registres(V119)['recs']}
props, noms = [], {}
for lid in ids_v:
    la, lv = a.layer(lid), v.layer(lid)
    for k in ('left', 'top', 'right', 'bottom', 'opacity', 'blend', 'clipping', 'mask', 'visible', 'name'):
        if la[k] == lv[k]: continue
        if k == 'visible' and lid in AMAGADES and lv[k] and not la[k]: continue
        if k == 'name' and lid in REFETES and nom_a[lid] == re.sub(r'\bV11[45]\b', 'V120', nom_v[lid], count=1): continue
        props.append(dict(id=lid, camp=k, v120=la[k], v119=lv[k]))
    if nom_a[lid] != nom_v[lid]:
        noms[lid] = [nom_v[lid], nom_a[lid]]
        if not (lid in REFETES and nom_a[lid] == re.sub(r'\bV11[45]\b', 'V120', nom_v[lid], count=1)): props.append(dict(id=lid, camp='nom_unicode', v120=nom_a[lid], v119=nom_v[lid]))
out['2_propietats_diferents_no_previstes'] = props; out['2_noms_canviats'] = noms
out['2_417_418_ocultes'] = all(not a.layer(i)['visible'] for i in AMAGADES)
def pred_nova(p, path, NOVA):
    if NOVA not in [l['id'] for l in p.layers]: return False, f'sense capa {NOVA}'
    NOM, OPAC, d = NOVES[NOVA]
    n4 = p.layer(NOVA); nomu = {rid(r): nom_de(r) for r, _ in llegeix_registres(path)['recs']}[NOVA]
    G = q_blocs(np.load(d / 'L415_G.npy')); AL = q_blocs(np.where(G == 32768, 0, 65535).astype(np.uint16))
    det = dict(nom_unicode=nomu, mode=n4['blend'], opacitat=n4['opacity'], visible=n4['visible'], caixa=[n4['left'], n4['top'], n4['right'], n4['bottom']], mascara=n4['mask'] is not None,
               raster={str(c): bool(np.array_equal(p.channel(NOVA, c)[0], G)) for c in (0, 1, 2)}, alfa=bool(np.array_equal(p.channel(NOVA, -1)[0], AL)))
    ok = (nomu == NOM and n4['blend'] == 'OVERLAY' and n4['opacity'] == OPAC and n4['visible'] and n4['mask'] is None and not n4['clipping']
          and det['caixa'] == [0, 0, p.width, p.height] and all(det['raster'].values()) and det['alfa'])
    return ok, det
ok419, out['4b_419'] = pred_nova(a, V120, 419); ok420, out['4b_420'] = pred_nova(a, V120, 420)
dif = []; n = 0
for lid in ids_v:
    if lid == 301 or lid in REFETES: continue
    la = a.layer(lid)
    if sorted(la['chans']) != sorted(v.layer(lid)['chans']): dif.append(dict(id=lid, problema='canals')); continue
    for cid in la['chans']:
        x, ox = a.channel(lid, cid); y, oy = v.channel(lid, cid); n += 1
        if ox != oy or x.shape != y.shape or not np.array_equal(x, y): dif.append(dict(id=lid, canal=cid))
out['3_canals_iguals_a_la_V119'] = dict(comprovats=n, diferents=dif)
ref, neg3 = {}, {}
for lid in sorted(REFETES):
    r_ = {}
    for c, qn, qk in parells(lid):
        y, oy = v.channel(lid, c); x, ox = a.channel(lid, c); ch = qn != qk; esp = y.copy(); esp[ch] = qn[ch]
        r_[str(c)] = dict(igual=bool(ox == oy and np.array_equal(x, esp)), canviats=int(ch.sum()), control_V119=bool(np.array_equal(y[ch], qk[ch])))
        if lid in (56, 202) and c == 0: neg3[lid] = bool(np.array_equal(y, esp))            # la V119 hauria de fallar-lo
    ref[lid] = r_
out['3b_capes_refetes'] = ref
ok3b = all(d_['igual'] and d_['control_V119'] for r_ in ref.values() for d_ in r_.values()) and all(ref[l]['0']['canviats'] > 0 for l in (3, 56, 202, 45, 41))
c301 = {}
for cid in (0, 1, 2):
    e = q_blocs(np.load(C301 / f'L301_c{cid}.npy')); x, _ = a.channel(301, cid); c301[str(cid)] = bool(np.array_equal(x, e))
xa, _ = a.channel(301, -1); rc = json.loads((C301 / 'RECEIPT.json').read_text())
c301['alfa_de_la_recepta'] = bool(np.array_equal(xa, q_blocs(np.load(C301 / 'L301_alfa.npy'))))
c301['recepta_torna_l_alfa_V119_i_V115'] = bool(rc.get('alpha_exact') or all(rc['prova_recepta_V119'][k]['alfa_igual_a_la_recepta'] for k in ('V119', 'V115')))
out['4_301_regenerada'] = c301
comp = a.composite()[..., :3]; tif = tifffile.imread(TIF)
out['5_compost_igual_al_render_natiu'] = bool(np.array_equal(comp, tif)); out['5_dif_max'] = int(np.abs(comp.astype(np.int32) - tif.astype(np.int32)).max())
out['render'] = dict(fitxer=str(TIF.relative_to(R)), sha256=sha(TIF))
n9, d9_ = pred_nova(v, V119, 419); n0, d0_ = pred_nova(v, V119, 420)
neg_ok = n9 or n0 or any(neg3.values())
out['6_negativa_la_V119_falla'] = dict(falla=not neg_ok, capes_noves={'419': d9_, '420': d0_}, v119_ja_era_la_refeta={str(k): v_ for k, v_ in neg3.items()})
passa = (out['1_inventari_i_ordre_V119_mes_419_420_damunt_de_418'] and not props and out['2_417_418_ocultes'] and ok419 and ok420 and not dif and ok3b
         and all(c301.values()) and out['5_compost_igual_al_render_natiu'] and not neg_ok)
out['veredicte_metode_i_fitxer'] = 'PASSA' if passa else 'FALLA'
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False)); print(json.dumps({k: v_ for k, v_ in out.items() if k not in ('3b_capes_refetes',)}, ensure_ascii=False, indent=1)[:3500])
print('3b:', 'PASSA' if ok3b else 'FALLA', {l: {c: (d_['igual'], d_['canviats']) for c, d_ in r_.items()} for l, r_ in ref.items()})
