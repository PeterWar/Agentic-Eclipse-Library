"""m4 · V115 (Claude, 29-09-2026): PSB de pas de la V115 a partir de 1-PHOTOSHOP/V114.psb DE PERE (la desada el 29-09 00:00, amb la capa de marques
414 i sense la 412), BYTE A BYTE, amb només aquests canvis:
  1. la 41 i la 42 (NRGF) d'una variant de g2_nrgf_fosc.py (costat fosc comprimit) i, opcionalment, la 45 i la 46 (RHEF) de r1_rhef_fosc.py, amb la
     regla de control de la V114: canal = V114, i on q(nou) ≠ q(control) el nou; COMPROVACIÓ V114[canvi] == q(control), amb el control = la cadena
     v114c (la que va fer la V114: nrgf/G_MAX_T_e30_W_H0 i filtres_mass). Si Pere hagués retocat la 41/42/46 on canvia, el muntatge s'atura;
  2. opcionalment la 301 regenerada (--c301) sobre el render natiu de la pila de sota;
  3. la 414 (marques de Pere) es conserva tal qual, però OCULTA (--amaga 414), perquè el compost no la porti; Pere la pot tornar a encendre.
Els noms de 41/42/46 passen de «V114» a «V115». Res més no canvia. Ús: m4_munta_v115.py <sortida.psb> --nrgf <carpeta> [--rhef <carpeta amb 45 i/o 46>] [--c301 <carpeta>] [--amaga 414]"""
from pathlib import Path
import sys, json, io, copy, struct, hashlib, re, time, argparse
import numpy as np
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, llegeix_registres, rid, enc, q_blocs, sha, renomena
from psd_tools.constants import Tag
ap = argparse.ArgumentParser(); ap.add_argument('sortida'); ap.add_argument('--nrgf', required=True); ap.add_argument('--rhef'); ap.add_argument('--c301')
ap.add_argument('--amaga', type=int, nargs='*', default=[]); A = ap.parse_args(); t0 = time.time()
assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == 'CLAUDE_V115_NRGF_CLOTADES_20260929'
SRC = R / '1-PHOTOSHOP/V114.psb'
SHA_SRC = '854705bfcbbdf0dcb05906a1ab7dd7b40805caca65cf09333ad7a7ab309d4861'
DST = Path(A.sortida).resolve(); assert str(DST).startswith(str(R / '4-RESULTATS/v115_nrgf_20260929')) and not DST.exists()
CT = R / '4-RESULTATS/v114_estrelles_20260928/cadena/v114c'; NG = Path(A.nrgf).resolve()
FONT = {}
for lid, tg in ((41, 'P01_NRGF'), (42, 'P01_NRGF_extrap')):
    FONT[lid] = dict(nou=(NG / f'{tg}_u16.npy', NG / f'{tg}_alfa_u16.npy'), ctrl=(CT / f'nrgf/G_MAX_T_e30_W_H0/{tg}_u16.npy', CT / f'nrgf/G_MAX_T_e30_W_H0/{tg}_alfa_u16.npy'))
if A.rhef:
    RH = Path(A.rhef).resolve()
    for lid, tg in ((45, 'P02c_RHEF_local60_native'), (46, 'P02d_RHEF_local30_native')):
        if (RH / f'{tg}_u16.npy').exists():
            FONT[lid] = dict(nou=(RH / f'{tg}_u16.npy', RH / f'{tg}_alfa_u16.npy'), ctrl=(CT / f'filtres_mass/filtres/{tg}_u16.npy', CT / f'filtres_mass/filtres/{tg}_alfa_u16.npy'))
assert sha(SRC) == SHA_SRC, 'la V114 de Pere ha canviat'
p = PSB(str(SRC)); s = llegeix_registres(SRC); MEM = {}
info = dict(font=str(SRC.relative_to(R)), sha256_font=SHA_SRC, nrgf=str(NG.relative_to(R)), rhef=(str(RH.relative_to(R)) if A.rhef else None),
            regla='canal = V114 de Pere, amb canal[q(nou) ≠ q(control)] = q(nou); comprovat V114[canvi] == q(control) (cadena v114c)', amagades=A.amaga, capes={})
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
            assert dif == 0, f'capa {lid} canal {cid}: la V114 de Pere no és la cadena v114c a {dif} dels {int(ch.sum())} píxels que canvien (retoc de Pere?)'
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
            vell = rec.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME); nn = re.sub(r'\bV114\b', 'V115', vell, count=1); renomena(rec, nn)
        if toca_flags: rec.flags.visible = False; info['capes'].setdefault(str(lid), {})['visible'] = [True, False]
        buf = io.BytesIO(); rec.write(buf, version=2); raw = buf.getvalue()
    records.append((raw, channels, lid))
    if lid in FONT or lid in (301,) or lid in A.amaga: print(lid, json.dumps(info['capes'].get(str(lid)), ensure_ascii=False)[:300], f'{time.time()-t0:.0f}s', flush=True)
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
Q = PSB(str(DST)); assert [l['id'] for l in Q.layers] == [lid for _, _, lid in records]
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
assert sha(SRC) == SHA_SRC
info.update(sortida=str(DST.relative_to(R)), sha256=sha(DST), bytes=DST.stat().st_size, verificacio='registres i canals iguals byte a byte a la V114 de Pere o al ràster nou codificat', segons=round(time.time() - t0, 1))
DST.with_suffix('.json').write_text(json.dumps(info, ensure_ascii=False, indent=1)); print(json.dumps({k: v for k, v in info.items() if k != 'capes'}, ensure_ascii=False))
