"""m5 · V116 (Claude, 29-09-2026): PSB de pas de la V116 a partir de 1-PHOTOSHOP/V115.psb DE PERE (desada el 29-09 a les 04:25, SHA 4fd1e803…, amb la
marca taronja nova a la 414; la resta, píxel a píxel la V115 que vaig lliurar), BYTE A BYTE, amb només aquests canvis:
  1. la 41 i la 42 (NRGF) de g3_nrgf_fosc_415.py (només l'estructura fosca LOCAL comprimida, k = 0, gran escala σ 800 px conservada; genoll que
     compta totes les capes de Superposar actives, també la 415 nova) i la 45 i la 46 (RHEF local amb el costat fosc limitat, k = 0, nivell de gran
     escala σ 800 conservat), amb la regla de control: canal = V115 de Pere, i on q(nou) ≠ q(control) el nou; COMPROVACIÓ V115[canvi] == q(control),
     amb el control = els ràsters que vaig muntar a la V115 (v115 nrgf_rL0/Lk20_G_MAX_T_e30_W_H0 i rhefL/k0_s400). Si Pere hagués retocat la
     41/42/45/46 on canvia, el muntatge s'atura;
  2. UNA CAPA NOVA (norma de Pere: cada canvi, una capa), id 415, «Detall radial coherent Sony A·B · V116»: Superposar, opacitat 40 % (102/255),
     visible (o OCULTA amb --oculta415: la V116 la lliura oculta), llenç sencer, sense màscara, gris R = G = B (32768 = neutre), alfa 65535; just damunt de la 56 i sota la 305. Plantilla del registre:
     la 305 (Superposar, sense màscara, canals −1, 0, 1, 2);
  3. opcionalment la 301 regenerada (--c301) sobre el render natiu de la pila de sota;
  4. la 414 (les marques de Pere, amb la taronja) es conserva tal qual (píxels i nom), però OCULTA (--amaga 414): Pere la pot tornar a encendre.
Els noms de 41/42/45/46 passen de «V115» a «V116». Res més no canvia.
Ús: m5_munta_v116.py <sortida.psb> --nrgf <carpeta> --rhef <carpeta> --capa415 <carpeta amb L415_G.npy i L415_alfa.npy> [--c301 <carpeta>] [--amaga 414]"""
from pathlib import Path
import sys, json, io, copy, struct, hashlib, re, time, argparse
import numpy as np
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, llegeix_registres, rid, enc, q_blocs, sha, renomena
from psd_tools.constants import Tag, BlendMode
ap = argparse.ArgumentParser(); ap.add_argument('sortida'); ap.add_argument('--nrgf', required=True); ap.add_argument('--rhef', required=True)
ap.add_argument('--capa415', required=True); ap.add_argument('--opac415', type=int, default=102); ap.add_argument('--oculta415', action='store_true'); ap.add_argument('--c301'); ap.add_argument('--amaga', type=int, nargs='*', default=[])
A = ap.parse_args(); t0 = time.time()
assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == 'CLAUDE_V116_20260929'
SRC = R / '1-PHOTOSHOP/V115.psb'
SHA_SRC = '4fd1e803ac9e0a61ed53caa0ddfb5f7b9b5d47a276fa9161f148da874c321b3c'
DST = Path(A.sortida).resolve(); assert str(DST).startswith(str(R / '4-RESULTATS/v116_20260929')) and not DST.exists()
C5 = R / '4-RESULTATS/v115_nrgf_20260929'; NG = Path(A.nrgf).resolve(); RH = Path(A.rhef).resolve(); C415 = Path(A.capa415).resolve()
FONT = {}
for lid, tg in ((41, 'P01_NRGF'), (42, 'P01_NRGF_extrap')):
    FONT[lid] = dict(nou=(NG / f'{tg}_u16.npy', NG / f'{tg}_alfa_u16.npy'), ctrl=(C5 / f'nrgf_rL0/Lk20_G_MAX_T_e30_W_H0/{tg}_u16.npy', C5 / f'nrgf_rL0/Lk20_G_MAX_T_e30_W_H0/{tg}_alfa_u16.npy'))
for lid, tg in ((45, 'P02c_RHEF_local60_native'), (46, 'P02d_RHEF_local30_native')):
    FONT[lid] = dict(nou=(RH / f'{tg}_u16.npy', RH / f'{tg}_alfa_u16.npy'), ctrl=(C5 / f'rhefL/k0_s400/{tg}_u16.npy', C5 / f'rhefL/k0_s400/{tg}_alfa_u16.npy'))
assert sha(SRC) == SHA_SRC, 'la V115 de Pere ha canviat al disc'
p = PSB(str(SRC)); s = llegeix_registres(SRC); MEM = {}; H, W = p.height, p.width
info = dict(font=str(SRC.relative_to(R)), sha256_font=SHA_SRC, nrgf=str(NG.relative_to(R)), rhef=str(RH.relative_to(R)), capa415=str(C415.relative_to(R)),
            regla='canal = V115 de Pere, amb canal[q(nou) ≠ q(control)] = q(nou); comprovat V115[canvi] == q(control) (ràsters muntats a la V115)', amagades=A.amaga, capes={})
# capa nova 415: ràster gris (R = G = B) i alfa, quantitzats com els desarà el Photoshop
G415 = q_blocs(np.load(C415 / 'L415_G.npy')); A415 = q_blocs(np.load(C415 / 'L415_alfa.npy')); assert G415.shape == (H, W) and A415.shape == (H, W)
B415 = {-1: enc(A415), 0: enc(G415)}; B415[1] = B415[0]; B415[2] = B415[0]
for cid, b in B415.items(): assert np.array_equal(p._decode(b, W, H), A415 if cid == -1 else G415)
NOM415 = 'Detall radial coherent Sony A·B · V116'
records = []
for rec, raw in s['recs']:
    lid = rid(rec); L = p.layer(lid)
    channels = [(Path(p.path), *L['chans'][int(ch.id)]) for ch in rec.channel_info]
    canvis = {}; toca_flags = False
    if lid in FONT:
        fn, fa = FONT[lid]['nou']; cn, ca = FONT[lid]['ctrl']; nou = np.load(fn, mmap_mode='r'); ctl = np.load(cn, mmap_mode='r'); gn = gc = None
        for cid in (0, 1, 2, -1):
            if cid == -1: n_, c_ = q_blocs(np.load(fa)), q_blocs(np.load(ca))
            elif nou.ndim == 3: n_, c_ = q_blocs(np.asarray(nou[..., cid])), q_blocs(np.asarray(ctl[..., cid]))
            else:
                if gn is None: gn, gc = q_blocs(np.asarray(nou)), q_blocs(np.asarray(ctl))
                n_, c_ = gn, gc
            act, org = p.channel(lid, cid); assert org == (0, 0) and act.shape == n_.shape
            ch = n_ != c_; dif = int(np.count_nonzero(act[ch] != c_[ch]))
            assert dif == 0, f'capa {lid} canal {cid}: la V115 de Pere no és el ràster muntat a la V115 a {dif} dels {int(ch.sum())} píxels que canvien (retoc de Pere?)'
            if ch.any(): t = act.copy(); t[ch] = n_[ch]; canvis[cid] = t
            info['capes'].setdefault(str(lid), {})[str(cid)] = dict(canviats=int(ch.sum()), max_abs_DN=int(np.abs(n_.astype(np.int32) - c_.astype(np.int32)).max()))
    if lid == 301 and A.c301:
        cdir = Path(A.c301).resolve(); rc = json.loads((cdir / 'RECEIPT.json').read_text()); assert rc['alpha_exact'] and rc['box'] == [7356, 4320, 9348, 6263]
        for cid in (0, 1, 2):
            n_ = q_blocs(np.load(cdir / f'L301_c{cid}.npy')); act, org = p.channel(lid, cid); assert org == (7356, 4320) and act.shape == n_.shape
            if (n_ != act).any(): canvis[cid] = n_
            info['capes'].setdefault('301', {})[str(cid)] = dict(canviats=int((n_ != act).sum()))
        info['c301'] = dict(carpeta=str(cdir.relative_to(R)), rebut_sha256=sha(cdir / 'RECEIPT.json'))
    if lid in A.amaga and rec.flags.visible: toca_flags = True
    if canvis or toca_flags:
        rec = copy.deepcopy(rec)
        for i, ch in enumerate(rec.channel_info):
            cid = int(ch.id)
            if cid in canvis:
                bts = enc(canvis[cid]); key = f'L{lid}_c{cid}'; MEM[key] = bts; ch.length = len(bts); channels[i] = (key, 0, ch.length)
        if lid in FONT and canvis:
            vell = rec.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME); nn = re.sub(r'\bV115\b', 'V116', vell, count=1); renomena(rec, nn)
            info['capes'][str(lid)]['nom'] = [str(vell), nn]
        if toca_flags: rec.flags.visible = False; info['capes'].setdefault(str(lid), {})['visible'] = [True, False]
        buf = io.BytesIO(); rec.write(buf, version=2); raw = buf.getvalue()
    records.append((raw, channels, lid))
    if lid in FONT or lid in (301,) or lid in A.amaga: print(lid, json.dumps(info['capes'].get(str(lid)), ensure_ascii=False)[:300], f'{time.time()-t0:.0f}s', flush=True)
    if lid == 56:
        # la capa nova, just damunt de la 56 (els registres van de baix a dalt)
        tpl = next(r for r, _ in s['recs'] if rid(r) == 305); assert [int(c.id) for c in tpl.channel_info] == [-1, 0, 1, 2] and tpl.mask_data is None
        nr = copy.deepcopy(tpl); nr.top, nr.left, nr.bottom, nr.right = 0, 0, H, W
        for ci in nr.channel_info: ci.length = len(B415[int(ci.id)])
        renomena(nr, NOM415); nr.opacity = A.opac415; nr.clipping = 0; nr.flags.visible = not A.oculta415; nr.blend_mode = BlendMode.OVERLAY
        nr.tagged_blocks.set_data(Tag.LAYER_ID, 415)
        for cid, b in B415.items(): MEM[f'L415_c{cid}'] = b
        buf = io.BytesIO(); nr.write(buf, version=2)
        records.append((buf.getvalue(), [(f'L415_c{int(ci.id)}', 0, len(B415[int(ci.id)])) for ci in nr.channel_info], 415))
        info['capes']['415'] = dict(nou=True, nom=NOM415, mode='Superposar', opacitat=A.opac415, visible=not A.oculta415, caixa=[0, 0, W, H], sobre=56, plantilla=305,
                                    sha256_L415_G=sha(C415 / 'L415_G.npy'), u_p1_p50_p99=[float(np.percentile(G415[::8, ::8], q)) / 65535 for q in (1, 50, 99)])
        print(415, json.dumps(info['capes']['415'], ensure_ascii=False)[:300], flush=True)
ids_src = [rid(r) for r, _ in s['recs']]; ids_dst = [lid for _, _, lid in records]
assert 415 not in ids_src and ids_dst == ids_src[:ids_src.index(56) + 1] + [415] + ids_src[ids_src.index(56) + 1:]
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
for lid in A.amaga: assert not Q.layer(lid)['visible']
L415 = Q.layer(415); assert (L415['blend'], L415['opacity'], L415['visible'], L415['left'], L415['top'], L415['right'], L415['bottom']) == ('OVERLAY', A.opac415, not A.oculta415, 0, 0, W, H), L415
assert all(np.array_equal(Q.channel(415, c)[0], G415) for c in (0, 1, 2)) and np.array_equal(Q.channel(415, -1)[0], A415)
assert sha(SRC) == SHA_SRC
info.update(sortida=str(DST.relative_to(R)), sha256=sha(DST), bytes=DST.stat().st_size, capes_total=len(Q.layers),
            verificacio='registres i canals iguals byte a byte a la V115 de Pere o al ràster nou codificat; la 415 descodificada = ràster', segons=round(time.time() - t0, 1))
DST.with_suffix('.json').write_text(json.dumps(info, ensure_ascii=False, indent=1)); print(json.dumps({k: v for k, v in info.items() if k != 'capes'}, ensure_ascii=False))
