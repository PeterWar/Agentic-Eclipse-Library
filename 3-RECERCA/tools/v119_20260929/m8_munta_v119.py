"""m8 · V119 (Claude, 29-09-2026): PSB de pas de la V119 = la V118 (1-PHOTOSHOP/V118.psb, SHA c76b47fc…) BYTE A BYTE, amb només aquests canvis
(encàrrec de Pere: «pots aprofitar la relliscada de la muntura per fer un altre filtre per captar justament l'altre tipus de detall? assigna'ls nom»):
  1. DUES CAPES NOVES (cada canvi, una capa), Superposar, llenç sencer, sense màscara, gris R = G = B (32768 = neutre), alfa 65535 on la capa diu alguna cosa i 0 on és exactament neutra, just damunt de la 416:
     · 417 «Ordit: raigs confirmats per tres testimonis, sense estrelles · V119»: l'ordit (el filtre de la 416) amb el mapa de registre CONTINU
       (v119 b8b; la 416 de la V118 tenia costures de fins a ~3 px on el registre queia a zero), --opac417 (per defecte 64/255 = 25 %);
     · 418 «Trama: arcs confirmats per tres testimonis, sense estrelles · V119»: el detall tangencial (arcs, cims de llaços, cascs) confirmat
       per la Sony A, la Sony B i la Vixen (v119 b9), --opac418 (per defecte 102/255 = 40 %);
  2. la 416 de la V118, intacta però OCULTA (la 415 ja ho era), com a referència;
  3. opcionalment la 301 regenerada (--c301) sobre el render natiu de la pila de sota.
Cap altra capa canvia. Plantilla dels registres nous: la 416. Adaptat de v118_20260929/m7_munta_v118.py.
Ús: m8_munta_v119.py <sortida.psb> --ordit <carpeta L415_G/L415_alfa> --trama <carpeta L415_G/L415_alfa> [--opac417 64] [--opac418 102] [--c301 <carpeta>]"""
from pathlib import Path
import sys, json, io, copy, struct, hashlib, time, argparse
import numpy as np
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, llegeix_registres, rid, enc, q_blocs, sha, renomena
from psd_tools.constants import Tag, BlendMode
ap = argparse.ArgumentParser(); ap.add_argument('sortida')
ap.add_argument('--ordit', required=True); ap.add_argument('--trama', required=True)
ap.add_argument('--opac417', type=int, default=64); ap.add_argument('--opac418', type=int, default=102); ap.add_argument('--c301')
A = ap.parse_args(); t0 = time.time()
assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == 'CLAUDE_V119_TRAMA_20260929'
SRC = R / '1-PHOTOSHOP/V118.psb'
SHA_SRC = 'c76b47fc87cfcae91cdbfd8d684326c7156bfa48406578ef06c72cd7c08de5d7'
DST = Path(A.sortida).resolve(); assert str(DST).startswith(str(R / '4-RESULTATS/v119_20260929')) and not DST.exists()
assert sha(SRC) == SHA_SRC, 'la V118 ha canviat al disc'
p = PSB(str(SRC)); s = llegeix_registres(SRC); MEM = {}; H, W = p.height, p.width
NOVES = [dict(id=417, nom='Ordit: raigs confirmats per tres testimonis, sense estrelles · V119', dir=Path(A.ordit).resolve(), opac=A.opac417),
         dict(id=418, nom='Trama: arcs confirmats per tres testimonis, sense estrelles · V119', dir=Path(A.trama).resolve(), opac=A.opac418)]
for n in NOVES:
    # ALFA 0 on la capa és exactament neutra (32768): el Photoshop compon en enters i una capa neutra en Superposar hi deixava arrodoniments que les
    # corbes de sobre amplifiquen (fins a 18 DN dins la Lluna i 110 DN a l'anell del limbe al primer desat de la V119). Transparent on no diu res.
    G = q_blocs(np.load(n['dir'] / 'L415_G.npy')); Al = q_blocs(np.where(G == 32768, 0, 65535).astype(np.uint16)); assert G.shape == (H, W) and Al.shape == (H, W)
    assert not (Al == 0).any() or (G[Al == 0] == 32768).all()
    B = {-1: enc(Al), 0: enc(G)}; B[1] = B[0]; B[2] = B[0]
    for cid, b in B.items(): assert np.array_equal(p._decode(b, W, H), Al if cid == -1 else G)
    n.update(G=G, Al=Al, B=B)
ids_src = [rid(r) for r, _ in s['recs']]; assert 417 not in ids_src and 418 not in ids_src and p.layer(416)['visible'] and not p.layer(415)['visible']
info = dict(font=str(SRC.relative_to(R)), sha256_font=SHA_SRC, regla='tots els registres i canals de la V118 byte a byte; capes noves 417 (ordit) i 418 (trama) damunt de la 416; 416 oculta; 301 regenerada', capes={})
records = []
tpl = next(r for r, _ in s['recs'] if rid(r) == 416); assert [int(c.id) for c in tpl.channel_info] == [-1, 0, 1, 2] and tpl.mask_data is None
for rec, raw in s['recs']:
    lid = rid(rec); L = p.layer(lid)
    channels = [(Path(p.path), *L['chans'][int(ch.id)]) for ch in rec.channel_info]
    canvis = {}; toca_flags = False
    if lid == 301 and A.c301:
        cdir = Path(A.c301).resolve(); rc = json.loads((cdir / 'RECEIPT.json').read_text()); assert rc['alpha_exact'] and rc['box'] == [7356, 4320, 9348, 6263]
        for cid in (0, 1, 2):
            n_ = q_blocs(np.load(cdir / f'L301_c{cid}.npy')); act, org = p.channel(lid, cid); assert org == (7356, 4320) and act.shape == n_.shape
            if (n_ != act).any(): canvis[cid] = n_
            info['capes'].setdefault('301', {})[str(cid)] = dict(canviats=int((n_ != act).sum()))
        info['c301'] = dict(carpeta=str(cdir.relative_to(R)), rebut_sha256=sha(cdir / 'RECEIPT.json'))
    if lid == 416 and rec.flags.visible: toca_flags = True
    if canvis or toca_flags:
        rec = copy.deepcopy(rec)
        for i, ch in enumerate(rec.channel_info):
            cid = int(ch.id)
            if cid in canvis:
                bts = enc(canvis[cid]); key = f'L{lid}_c{cid}'; MEM[key] = bts; ch.length = len(bts); channels[i] = (key, 0, ch.length)
        if toca_flags: rec.flags.visible = False; info['capes'].setdefault(str(lid), {})['visible'] = [True, False]
        buf = io.BytesIO(); rec.write(buf, version=2); raw = buf.getvalue()
    records.append((raw, channels, lid))
    if lid in (301, 416): print(lid, json.dumps(info['capes'].get(str(lid)), ensure_ascii=False)[:300], f'{time.time()-t0:.0f}s', flush=True)
    if lid == 416:
        for n in NOVES:                                          # els registres van de baix a dalt: 417 i, damunt, 418
            nr = copy.deepcopy(tpl); nr.top, nr.left, nr.bottom, nr.right = 0, 0, H, W
            for ci in nr.channel_info: ci.length = len(n['B'][int(ci.id)])
            renomena(nr, n['nom']); nr.opacity = n['opac']; nr.clipping = 0; nr.flags.visible = True; nr.blend_mode = BlendMode.OVERLAY
            nr.tagged_blocks.set_data(Tag.LAYER_ID, n['id'])
            for cid, b in n['B'].items(): MEM[f"L{n['id']}_c{cid}"] = b
            buf = io.BytesIO(); nr.write(buf, version=2)
            records.append((buf.getvalue(), [(f"L{n['id']}_c{int(ci.id)}", 0, len(n['B'][int(ci.id)])) for ci in nr.channel_info], n['id']))
            info['capes'][str(n['id'])] = dict(nou=True, nom=n['nom'], mode='Superposar', opacitat=n['opac'], visible=True, caixa=[0, 0, W, H], plantilla=416, alfa_0_on_neutra=True, frac_transparent=float((n['Al'] == 0).mean()),
                                               sha256_raster=sha(n['dir'] / 'L415_G.npy'), u_p1_p50_p99=[float(np.percentile(n['G'][::8, ::8], q)) / 65535 for q in (1, 50, 99)])
            print(n['id'], json.dumps(info['capes'][str(n['id'])], ensure_ascii=False)[:300], flush=True)
ids_dst = [lid for _, _, lid in records]
assert ids_dst == ids_src[:ids_src.index(416) + 1] + [417, 418] + ids_src[ids_src.index(416) + 1:]
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
assert not Q.layer(416)['visible'] and not Q.layer(415)['visible']
for n in NOVES:
    Ln = Q.layer(n['id']); assert (Ln['blend'], Ln['opacity'], Ln['visible'], Ln['left'], Ln['top'], Ln['right'], Ln['bottom']) == ('OVERLAY', n['opac'], True, 0, 0, W, H), Ln
    assert all(np.array_equal(Q.channel(n['id'], c)[0], n['G']) for c in (0, 1, 2)) and np.array_equal(Q.channel(n['id'], -1)[0], n['Al'])
assert sha(SRC) == SHA_SRC
info.update(sortida=str(DST.relative_to(R)), sha256=sha(DST), bytes=DST.stat().st_size, capes_total=len(Q.layers),
            verificacio='registres i canals iguals byte a byte a la V118 (la 301, a la regenerada; la 416, oculta); la 417 i la 418 descodificades = ràsters', segons=round(time.time() - t0, 1))
DST.with_suffix('.json').write_text(json.dumps(info, ensure_ascii=False, indent=1)); print(json.dumps({k: v for k, v in info.items() if k != 'capes'}, ensure_ascii=False))
