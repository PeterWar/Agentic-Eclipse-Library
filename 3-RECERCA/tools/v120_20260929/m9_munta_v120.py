"""m9 · V120 (Claude, 29-09-2026): PSB de pas de la V120 a partir de la V119 (1-PHOTOSHOP/V119.psb, SHA dafd8d4b…), BYTE A BYTE, amb:
  1. LES CAPES DERIVADES DE LA FUSIÓ, refetes sobre la fusió nova (la Sony deformada a la geometria de la Vixen; opció 3 de Pere), amb les MATEIXES
     receptes: 3 (base), 54 (MGN), 47, 49, 51 (ACHF), 55, 56 (WOW) de la cadena v120 (= la v114c), 45/46 (RHEF, recepta V115: k 0, σ 400) i
     41/42 (NRGF, recepta V115: Lk20_G_MAX_T_e30_W_H0). REGLA DE CONTROL (la de la V114/V115): canal = V119, i on q(nou) ≠ q(control) el nou;
     COMPROVACIÓ: la V119 hi ha de ser igual al control (la v114c per a 3/54/47/49/51/55/56; la V115 per a 41/42/45/46). Si Pere hagués retocat
     algun píxel que canvia, el muntatge s'atura;
  2. LES ESTRELLES a la geometria nova: 202 (els segells de llum mesurada, traslladats), 203 (el mapa, refet); control: el que es va muntar a la V114;
  3. BRNO per estrelles (230–232, ocultes), deformades amb el mateix camp; control: el que es va muntar a la V113;
  4. L'ORDIT i la TRAMA de la V119 (417, 418), OCULTES; opcionalment (--ordit/--trama) dues capes noves, 419 «Ordit» i 420 «Trama» de la V120,
     damunt de la 418, Superposar, transparents on són exactament neutres;
  5. opcionalment la 301 regenerada (--c301).
Els noms de les capes refetes canvien l'etiqueta de versió (V114/V115 → V120), com va fer la V115; res més del nom.
Ús: m9_munta_v120.py <sortida.psb> [--ordit <carpeta L415_G/L415_alfa> --trama <…>] [--opac419 64] [--opac420 102] [--c301 <carpeta>]"""
from pathlib import Path
import sys, json, io, copy, struct, hashlib, re, time, argparse
import numpy as np
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, llegeix_registres, rid, enc, q_blocs, sha, renomena
from psd_tools.constants import Tag, BlendMode
ap = argparse.ArgumentParser(); ap.add_argument('sortida'); ap.add_argument('--ordit'); ap.add_argument('--trama'); ap.add_argument('--opac419', type=int, default=64); ap.add_argument('--opac420', type=int, default=102); ap.add_argument('--c301')
A = ap.parse_args(); t0 = time.time()
# 30-09-2026: regla de l'escriptor únic retirada per Pere: assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == 'CLAUDE_V120_DISTORSIO_20260929'
SRC = R / '1-PHOTOSHOP/V119.psb'; SHA_SRC = 'dafd8d4b7f351a82e3c7535493253b117b9aae311836290d7c6b46bc227eb015'
DST = Path(A.sortida).resolve(); assert str(DST).startswith(str(R / '4-RESULTATS/v120_20260929')) and not DST.exists()
NOU = R / '4-RESULTATS/v120_20260929/cadena/v120'; C114 = R / '4-RESULTATS/v114_estrelles_20260928/cadena/v114c'; C115 = R / '4-RESULTATS/v115_nrgf_20260929'
E120 = R / '4-RESULTATS/v120_20260929/estrelles'; B120 = R / '4-RESULTATS/v120_20260929/brno'
FONT = {}
for lid in (54, 47, 49, 51, 55, 56): FONT[lid] = dict(nou=(NOU / f'estat_v108/L{lid}_G.npy', NOU / f'estat_v108/L{lid}_alfa.npy'), ctrl=(C114 / f'estat_v108/L{lid}_G.npy', C114 / f'estat_v108/L{lid}_alfa.npy'))
FONT[3] = dict(nou=(NOU / 'estat_v108/L3_RGB.npy', NOU / 'estat_v108/L3_alfa.npy'), ctrl=(C114 / 'estat_v108/L3_RGB.npy', C114 / 'estat_v108/L3_alfa.npy'))
for lid, tg in ((45, 'P02c_RHEF_local60_native'), (46, 'P02d_RHEF_local30_native')):
    FONT[lid] = dict(nou=(NOU / f'rhefL/k0_s400/{tg}_u16.npy', NOU / f'rhefL/k0_s400/{tg}_alfa_u16.npy'), ctrl=(C115 / f'rhefL/k0_s400/{tg}_u16.npy', C115 / f'rhefL/k0_s400/{tg}_alfa_u16.npy'))
for lid, tg in ((41, 'P01_NRGF'), (42, 'P01_NRGF_extrap')):
    FONT[lid] = dict(nou=(NOU / f'nrgf/Lk20_G_MAX_T_e30_W_H0/{tg}_u16.npy', NOU / f'nrgf/Lk20_G_MAX_T_e30_W_H0/{tg}_alfa_u16.npy'),
                     ctrl=(C115 / f'nrgf_rL0/Lk20_G_MAX_T_e30_W_H0/{tg}_u16.npy', C115 / f'nrgf_rL0/Lk20_G_MAX_T_e30_W_H0/{tg}_alfa_u16.npy'))
# capes de ràster complet (npz): canal → clau, amb el seu control
NPZ = {202: dict(nou=E120 / 'estrelles_202_V120.npz', ctrl=R / '4-RESULTATS/v114_estrelles_20260928/estrelles_202_V114.npz', canals={0: 'R', 1: 'G', 2: 'B', -1: 'A', -2: 'M'}),
       203: dict(nou=E120 / 'mapa_203_V120.npz', ctrl=R / '4-RESULTATS/v114_estrelles_20260928/mapa/mapa_203_V114_v2.npz', canals={0: 'R', 1: 'G', 2: 'B', -2: 'M'})}
for lid in (230, 231, 232): NPZ[lid] = dict(nou=B120 / f'L{lid}.npz', ctrl=R / f'4-RESULTATS/v113_estrelles_20260928/brno/L{lid}.npz', canals={0: 'R', 1: 'G', 2: 'B', -1: 'A'})
AMAGA = [417, 418]
assert sha(SRC) == SHA_SRC, 'la V119 ha canviat al disc'
p = PSB(str(SRC)); s = llegeix_registres(SRC); MEM = {}; H, W = p.height, p.width
NOVES = []
if A.ordit: NOVES.append(dict(id=419, nom='Ordit: raigs confirmats per tres testimonis, sense estrelles · V120', dir=Path(A.ordit).resolve(), opac=A.opac419))
if A.trama: NOVES.append(dict(id=420, nom='Trama: arcs confirmats per tres testimonis, sense estrelles · V120', dir=Path(A.trama).resolve(), opac=A.opac420))
for n in NOVES:
    G = q_blocs(np.load(n['dir'] / 'L415_G.npy')); Al = q_blocs(np.where(G == 32768, 0, 65535).astype(np.uint16)); assert G.shape == (H, W)
    B_ = {-1: enc(Al), 0: enc(G)}; B_[1] = B_[0]; B_[2] = B_[0]
    for cid, b in B_.items(): assert np.array_equal(p._decode(b, W, H), Al if cid == -1 else G)
    n.update(G=G, Al=Al, B=B_)
info = dict(font=str(SRC.relative_to(R)), sha256_font=SHA_SRC, regla='canal = V119, amb canal[q(nou) ≠ q(control)] = q(nou); comprovat V119[canvi] == q(control)', capes={}, amagades=AMAGA, noves=[n['id'] for n in NOVES])
def substitueix(lid, parells):
    """parells: {cid: (nou, ctrl)} en uint16 del marc de la capa; torna {cid: canal nou} només on canvia, amb la comprovació de control."""
    canvis = {}
    for cid, (n_, c_) in parells.items():
        act, org = p.channel(lid, cid); assert act is not None and act.shape == n_.shape, (lid, cid, None if act is None else act.shape, n_.shape)
        ch = n_ != c_; dif = int(np.count_nonzero(act[ch] != c_[ch]))
        assert dif == 0, f'capa {lid} canal {cid}: la V119 no és el control a {dif} dels {int(ch.sum())} píxels que canvien (retoc de Pere?)'
        if ch.any(): t = act.copy(); t[ch] = n_[ch]; canvis[cid] = t
        info['capes'].setdefault(str(lid), {})[str(cid)] = dict(canviats=int(ch.sum()), max_abs_DN=int(np.abs(n_.astype(np.int32) - c_.astype(np.int32)).max()) if ch.any() else 0)
    return canvis
records = []
tpl = next(r for r, _ in s['recs'] if rid(r) == 418)
for rec, raw in s['recs']:
    lid = rid(rec); L = p.layer(lid)
    channels = [(Path(p.path), *L['chans'][int(ch.id)]) for ch in rec.channel_info]
    canvis = {}; toca_flags = False; nou_nom = None
    if lid in FONT:
        fn, fa = FONT[lid]['nou']; cn, ca = FONT[lid]['ctrl']; nou = np.load(fn, mmap_mode='r'); ctl = np.load(cn, mmap_mode='r'); parells = {}
        for cid in (0, 1, 2, -1):
            if cid == -1: parells[cid] = (q_blocs(np.load(fa)), q_blocs(np.load(ca)))
            elif nou.ndim == 3: parells[cid] = (q_blocs(np.asarray(nou[..., cid])), q_blocs(np.asarray(ctl[..., cid])))
            else: parells[cid] = (q_blocs(np.asarray(nou)), q_blocs(np.asarray(ctl)))
        canvis = substitueix(lid, parells)
    if lid in NPZ:
        zn = np.load(NPZ[lid]['nou']); zc = np.load(NPZ[lid]['ctrl']); parells = {}
        for cid, k in NPZ[lid]['canals'].items():
            act, org = p.channel(lid, cid)
            if 'bbox' in zn.files and cid != -2:
                x0, y0, x1, y1 = [int(v) for v in zn['bbox']]; assert org == (x0, y0), (lid, cid, org)
            parells[cid] = (q_blocs(np.asarray(zn[k])), q_blocs(np.asarray(zc[k])))
        canvis = substitueix(lid, parells)
    if lid == 301 and A.c301:
        # (regenera_301_v120: l'alfa és la de la recepta sobre el render nou; el rebut prova que la recepta torna EXACTAMENT l'alfa de la V119 i la V115)
        cdir = Path(A.c301).resolve(); rc = json.loads((cdir / 'RECEIPT.json').read_text()); assert list(rc['box']) == [7356, 4320, 9348, 6263]
        assert rc['alpha_exact'] or all(rc['prova_recepta_V119'][k]['alfa_igual_a_la_recepta'] for k in ('V119', 'V115')), rc
        for cid in (0, 1, 2, -1):
            n_ = q_blocs(np.load(cdir / (f'L301_c{cid}.npy' if cid >= 0 else 'L301_alfa.npy'))); act, org = p.channel(lid, cid); assert org == (7356, 4320) and act.shape == n_.shape
            if (n_ != act).any(): canvis[cid] = n_
            info['capes'].setdefault('301', {})[str(cid)] = dict(canviats=int((n_ != act).sum()))
        info['c301'] = dict(carpeta=str(cdir.relative_to(R)), rebut_sha256=sha(cdir / 'RECEIPT.json'))
    if lid in AMAGA and rec.flags.visible: toca_flags = True
    if (lid in FONT or lid in (202, 203)) and canvis:
        vell = rec.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME); nou_nom = re.sub(r'\bV11[45]\b', 'V120', str(vell), count=1)
        if nou_nom == str(vell): nou_nom = None
    if canvis or toca_flags or nou_nom:
        rec = copy.deepcopy(rec)
        for i, ch in enumerate(rec.channel_info):
            cid = int(ch.id)
            if cid in canvis:
                bts = enc(canvis[cid]); key = f'L{lid}_c{cid}'; MEM[key] = bts; ch.length = len(bts); channels[i] = (key, 0, ch.length)
        if toca_flags: rec.flags.visible = False; info['capes'].setdefault(str(lid), {})['visible'] = [True, False]
        if nou_nom: renomena(rec, nou_nom); info['capes'].setdefault(str(lid), {})['nom'] = [str(vell), nou_nom]
        buf = io.BytesIO(); rec.write(buf, version=2); raw = buf.getvalue()
    records.append((raw, channels, lid))
    if lid in FONT or lid in NPZ or lid in (301,) or lid in AMAGA: print(lid, json.dumps(info['capes'].get(str(lid)), ensure_ascii=False)[:260], f'{time.time()-t0:.0f}s', flush=True)
    if lid == 418:
        for n in NOVES:
            nr = copy.deepcopy(tpl); nr.top, nr.left, nr.bottom, nr.right = 0, 0, H, W
            for ci in nr.channel_info: ci.length = len(n['B'][int(ci.id)])
            renomena(nr, n['nom']); nr.opacity = n['opac']; nr.clipping = 0; nr.flags.visible = True; nr.blend_mode = BlendMode.OVERLAY; nr.tagged_blocks.set_data(Tag.LAYER_ID, n['id'])
            for cid, b in n['B'].items(): MEM[f"L{n['id']}_c{cid}"] = b
            buf = io.BytesIO(); nr.write(buf, version=2)
            records.append((buf.getvalue(), [(f"L{n['id']}_c{int(ci.id)}", 0, len(n['B'][int(ci.id)])) for ci in nr.channel_info], n['id']))
            info['capes'][str(n['id'])] = dict(nou=True, nom=n['nom'], mode='Superposar', opacitat=n['opac'], visible=True, plantilla=418, frac_transparent=float((n['Al'] == 0).mean()), sha256_raster=sha(n['dir'] / 'L415_G.npy'))
            print(n['id'], json.dumps(info['capes'][str(n['id'])], ensure_ascii=False)[:260], flush=True)
ids_src = [rid(r) for r, _ in s['recs']]; ids_dst = [lid for _, _, lid in records]
assert ids_dst == ids_src[:ids_src.index(418) + 1] + [n['id'] for n in NOVES] + ids_src[ids_src.index(418) + 1:]
total = 2 + sum(len(b) + sum(n for _, _, n in ch) for b, ch, _ in records); pad = (total + 3) // 4 * 4
lmlen = s['lmlen'] + pad - (s['lrpadend'] - s['lrstart']); count = len(records) * (1 if s['count'] >= 0 else -1)
def cp(f, g, a, b):
    f.seek(a)
    while f.tell() < b: g.write(f.read(min(32 << 20, b - f.tell())))
opened = {}
with SRC.open('rb') as f, DST.open('xb') as g:
    cp(f, g, 0, s['lmpos']); g.write(struct.pack('>Q', lmlen)); cp(f, g, s['lmpos'] + 8, s['lenpos']); g.write(struct.pack('>Qh', total, count))
    for b, _, _ in records: g.write(b)
    for _, chs, _ in records:
        for file, off, n in chs:
            if isinstance(file, str): g.write(MEM[file]); continue
            if file not in opened: opened[file] = file.open('rb')
            cp(opened[file], g, off, off + n)
    g.write(b'\0' * (pad - total)); cp(f, g, s['lrpadend'], SRC.stat().st_size)
for f in opened.values(): f.close()
Q = PSB(str(DST)); assert [l['id'] for l in Q.layers] == ids_dst
Sq = llegeix_registres(DST)
for (r_, b_), (expect, chs, lid) in zip(Sq['recs'], records):
    assert b_ == expect, lid
    for c, (file, off, n) in zip(r_.channel_info, chs):
        qo, qn = Q.layer(lid)['chans'][int(c.id)]; assert qn == n
        ha = hashlib.sha256(); hb = hashlib.sha256()
        with DST.open('rb') as b2:
            b2.seek(qo); rem = n
            if isinstance(file, str):
                ha.update(MEM[file])
                while rem: nn = min(rem, 32 << 20); hb.update(b2.read(nn)); rem -= nn
            else:
                with file.open('rb') as a_:
                    a_.seek(off)
                    while rem: nn = min(rem, 32 << 20); ha.update(a_.read(nn)); hb.update(b2.read(nn)); rem -= nn
        assert ha.digest() == hb.digest(), (lid, int(c.id))
for lid in AMAGA: assert not Q.layer(lid)['visible']
assert sha(SRC) == SHA_SRC
info.update(sortida=str(DST.relative_to(R)), sha256=sha(DST), bytes=DST.stat().st_size, capes_total=len(Q.layers), segons=round(time.time() - t0, 1))
DST.with_suffix('.json').write_text(json.dumps(info, ensure_ascii=False, indent=1)); print(json.dumps({k: v for k, v in info.items() if k != 'capes'}, ensure_ascii=False))
