"""m7 · V118 (Claude, 29-09-2026): PSB de pas de la V118 = la V117 (1-PHOTOSHOP/V117.psb, SHA 61fd8a6f…, la candidata que Pere ha mirat) BYTE A BYTE,
amb només aquests canvis (encàrrec de Pere: «fes V118 amb els 3 testimonis, incloent el Vixen i treu les estrelles del filtre»):
  1. UNA CAPA NOVA (cada canvi, una capa), id 416, «Detall radial coherent A·B·Vixen sense estrelles · V118»: el filtre de tres testimonis
     (v118 b5: Sony A, Sony B i Vixen, mínim concordant, entrades sense estrelles i peu fins on arriba l'halo), Superposar, opacitat --opac416
     (per defecte 64/255 = 25 %), visible, llenç sencer, sense màscara, gris R = G = B (32768 = neutre), alfa 65535; just damunt de la 415.
     Plantilla del registre: la 415 de la V117;
  2. la 415 de la V117 (filtre A·B, amb estrelles) es conserva tal qual però OCULTA, com a referència per comparar;
  3. opcionalment la 301 regenerada (--c301) sobre el render natiu de la pila de sota.
Cap altra capa canvia. Adaptat de v117_20260929/m6_munta_v117.py (sense la maquinària de substitució de capes, que no es fa servir).
Ús: m7_munta_v118.py <sortida.psb> --capa416 <carpeta amb L415_G.npy i L415_alfa.npy del b3> [--opac416 64] [--c301 <carpeta>]"""
from pathlib import Path
import sys, json, io, copy, struct, hashlib, time, argparse
import numpy as np
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, llegeix_registres, rid, enc, q_blocs, sha, renomena
from psd_tools.constants import Tag, BlendMode
ap = argparse.ArgumentParser(); ap.add_argument('sortida')
ap.add_argument('--capa416', required=True); ap.add_argument('--opac416', type=int, default=64); ap.add_argument('--c301')
A = ap.parse_args(); t0 = time.time()
assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == 'CLAUDE_V118_TRES_TESTIMONIS_20260929'
SRC = R / '1-PHOTOSHOP/V117.psb'
SHA_SRC = '61fd8a6f2bc6315efc77137085ea03db44211c5fc4db5d75c83741996332f29a'
DST = Path(A.sortida).resolve(); assert str(DST).startswith(str(R / '4-RESULTATS/v118_20260929')) and not DST.exists()
C416 = Path(A.capa416).resolve()
assert sha(SRC) == SHA_SRC, 'la V117 ha canviat al disc'
p = PSB(str(SRC)); s = llegeix_registres(SRC); MEM = {}; H, W = p.height, p.width
NOM416 = 'Detall radial coherent A·B·Vixen sense estrelles · V118'
info = dict(font=str(SRC.relative_to(R)), sha256_font=SHA_SRC, capa416=str(C416.relative_to(R)),
            regla='tots els registres i canals de la V117 byte a byte; capa nova 416 damunt de la 415; 415 oculta; 301 regenerada', capes={})
G416 = q_blocs(np.load(C416 / 'L415_G.npy')); A416 = q_blocs(np.load(C416 / 'L415_alfa.npy')); assert G416.shape == (H, W) and A416.shape == (H, W)
B416 = {-1: enc(A416), 0: enc(G416)}; B416[1] = B416[0]; B416[2] = B416[0]
for cid, b in B416.items(): assert np.array_equal(p._decode(b, W, H), A416 if cid == -1 else G416)
assert 416 not in [rid(r) for r, _ in s['recs']] and p.layer(415)['visible']
records = []
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
    if lid == 415 and rec.flags.visible: toca_flags = True
    if canvis or toca_flags:
        rec = copy.deepcopy(rec)
        for i, ch in enumerate(rec.channel_info):
            cid = int(ch.id)
            if cid in canvis:
                bts = enc(canvis[cid]); key = f'L{lid}_c{cid}'; MEM[key] = bts; ch.length = len(bts); channels[i] = (key, 0, ch.length)
        if toca_flags: rec.flags.visible = False; info['capes'].setdefault(str(lid), {})['visible'] = [True, False]
        buf = io.BytesIO(); rec.write(buf, version=2); raw = buf.getvalue()
    records.append((raw, channels, lid))
    if lid in (301, 415): print(lid, json.dumps(info['capes'].get(str(lid)), ensure_ascii=False)[:300], f'{time.time()-t0:.0f}s', flush=True)
    if lid == 415:
        # la capa nova, just damunt de la 415 (els registres van de baix a dalt); plantilla: el registre ORIGINAL de la 415
        tpl = next(r for r, _ in s['recs'] if rid(r) == 415); assert [int(c.id) for c in tpl.channel_info] == [-1, 0, 1, 2] and tpl.mask_data is None
        nr = copy.deepcopy(tpl); nr.top, nr.left, nr.bottom, nr.right = 0, 0, H, W
        for ci in nr.channel_info: ci.length = len(B416[int(ci.id)])
        renomena(nr, NOM416); nr.opacity = A.opac416; nr.clipping = 0; nr.flags.visible = True; nr.blend_mode = BlendMode.OVERLAY
        nr.tagged_blocks.set_data(Tag.LAYER_ID, 416)
        for cid, b in B416.items(): MEM[f'L416_c{cid}'] = b
        buf = io.BytesIO(); nr.write(buf, version=2)
        records.append((buf.getvalue(), [(f'L416_c{int(ci.id)}', 0, len(B416[int(ci.id)])) for ci in nr.channel_info], 416))
        info['capes']['416'] = dict(nou=True, nom=NOM416, mode='Superposar', opacitat=A.opac416, visible=True, caixa=[0, 0, W, H], sobre=415, plantilla=415,
                                    sha256_L416_G=sha(C416 / 'L415_G.npy'), u_p1_p50_p99=[float(np.percentile(G416[::8, ::8], q)) / 65535 for q in (1, 50, 99)])
        print(416, json.dumps(info['capes']['416'], ensure_ascii=False)[:300], flush=True)
ids_src = [rid(r) for r, _ in s['recs']]; ids_dst = [lid for _, _, lid in records]
assert ids_dst == ids_src[:ids_src.index(415) + 1] + [416] + ids_src[ids_src.index(415) + 1:]
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
assert not Q.layer(415)['visible']
L416 = Q.layer(416); assert (L416['blend'], L416['opacity'], L416['visible'], L416['left'], L416['top'], L416['right'], L416['bottom']) == ('OVERLAY', A.opac416, True, 0, 0, W, H), L416
assert all(np.array_equal(Q.channel(416, c)[0], G416) for c in (0, 1, 2)) and np.array_equal(Q.channel(416, -1)[0], A416)
assert sha(SRC) == SHA_SRC
info.update(sortida=str(DST.relative_to(R)), sha256=sha(DST), bytes=DST.stat().st_size, capes_total=len(Q.layers),
            verificacio='registres i canals iguals byte a byte a la V117 (la 301, a la regenerada; la 415, oculta); la 416 descodificada = ràster', segons=round(time.time() - t0, 1))
DST.with_suffix('.json').write_text(json.dumps(info, ensure_ascii=False, indent=1)); print(json.dumps({k: v for k, v in info.items() if k != 'capes'}, ensure_ascii=False))
