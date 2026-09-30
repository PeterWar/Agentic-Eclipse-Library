"""m2 · V113 (estrelles, Claude, 28-09-2026): PSB de pas de la V113 corregida a partir de 1-PHOTOSHOP/V113.psb, BYTE A BYTE, amb:
  1. base i filtres (3, 54, 41, 42, 47, 49, 51, 45, 46, 55, 56) de la cadena v113c (fonts sense els fantasmes de la Vixen), amb la regla de
     control de m1: canal = V113, i on q(nou) ≠ q(control) el nou; COMPROVACIÓ V113[canvi] == q(control), amb el control = la cadena v113b
     (la que va fer la V113);
  2. les capes de referència de Brno 230/231/232, refetes per b1 amb l'encaix per estrelles (canvia el marc de la capa i el nom);
  3. opcionalment la 301 (--c301) i la 202 (--c202 <npz amb R,G,B,A del llenç sencer>).
Ús: m2_munta_v113c.py <sortida.psb> [--c301 <carpeta>] [--c202 <npz>]"""
from pathlib import Path
import sys, json, io, copy, struct, hashlib, re, time, argparse
import numpy as np
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, llegeix_registres, rid, enc, q_blocs, sha, renomena
from psd_tools.constants import Tag
ap = argparse.ArgumentParser(); ap.add_argument('sortida'); ap.add_argument('--c301'); ap.add_argument('--c202'); ap.add_argument('--sense-cadena', action='store_true')
ap.add_argument('--nova-capa', help='npz (R,G,B,A,bbox) d\'una capa NOVA que s\'insereix just damunt de la 202, amb la 267 de plantilla (Sobreexposició lineal, sense màscara)')
ap.add_argument('--nova-id', type=int, default=413); ap.add_argument('--nova-nom', default='Estrelles que faltaven · 4 Tycho · RAW'); A = ap.parse_args(); t0 = time.time()
assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == 'CLAUDE_V113_ESTRELLES_BRNO_20260928'
SRC = R / '4-RESULTATS/v113_estrelles_20260928/V113_abans_estrelles.psb'   # la V113 d'abans (mateix SHA), apartada aquí en lliurar la nova
SHA_SRC = '0a0aa1cf879be96bb50071a6a80375550175e7083add7bd0e84e7e0509ece5a4'
DST = Path(A.sortida).resolve(); assert str(DST).startswith(str(R / '4-RESULTATS/v113_estrelles_20260928')) and not DST.exists()
NOU = R / '4-RESULTATS/v113_estrelles_20260928/cadena/v113c'; CT = R / '4-RESULTATS/v112_claude_20260928/cadena/v113b'
FONT = {}
if not A.sense_cadena:
    for lid in (54, 47, 49, 51, 55, 56):
        FONT[lid] = dict(nou=(NOU / f'estat_v108/L{lid}_G.npy', NOU / f'estat_v108/L{lid}_alfa.npy'), ctrl=(CT / f'estat_v108/L{lid}_G.npy', CT / f'estat_v108/L{lid}_alfa.npy'))
    FONT[3] = dict(nou=(NOU / 'estat_v108/L3_RGB.npy', NOU / 'estat_v108/L3_alfa.npy'), ctrl=(CT / 'estat_v108/L3_RGB.npy', CT / 'estat_v108/L3_alfa.npy'))
    for lid, tg in ((45, 'P02c_RHEF_local60_native'), (46, 'P02d_RHEF_local30_native')):
        FONT[lid] = dict(nou=(NOU / f'filtres_mass/filtres/{tg}_u16.npy', NOU / f'filtres_mass/filtres/{tg}_alfa_u16.npy'), ctrl=(CT / f'filtres_mass/filtres/{tg}_u16.npy', CT / f'filtres_mass/filtres/{tg}_alfa_u16.npy'))
    for lid, tg in ((41, 'P01_NRGF'), (42, 'P01_NRGF_extrap')):
        d = 'nrgf/G_MAX_T_e30_W_H0'
        FONT[lid] = dict(nou=(NOU / f'{d}/{tg}_u16.npy', NOU / f'{d}/{tg}_alfa_u16.npy'), ctrl=(CT / f'{d}/{tg}_u16.npy', CT / f'{d}/{tg}_alfa_u16.npy'))
BRNO = {230: 'Brno 200 mm DHS · encaix per estrelles', 231: 'Brno 400 mm DHS · encaix per estrelles', 232: 'Brno 530 mm DHS · encaix per estrelles'}
assert sha(SRC) == SHA_SRC, 'la V113 ha canviat'
p = PSB(str(SRC)); s = llegeix_registres(SRC); MEM = {}
info = dict(font=str(SRC.relative_to(R)), sha256_font=SHA_SRC, regla_filtres='canal = V113, amb canal[nou≠ctrl] = nou; comprovat V113[nou≠ctrl] == ctrl (cadena v113b)', capes={})
records = []
for rec, raw in s['recs']:
    lid = rid(rec); L = p.layer(lid)
    channels = [(Path(p.path), *L['chans'][int(ch.id)]) for ch in rec.channel_info]
    canvis = {}; nou_marc = None; nou_nom = None
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
            assert dif == 0, f'capa {lid} canal {cid}: el control no reprodueix la V113 a {dif} dels {int(ch.sum())} píxels que canvien'
            if ch.any(): t = act.copy(); t[ch] = n_[ch]; canvis[cid] = t
            info['capes'].setdefault(str(lid), {})[str(cid)] = dict(canviats=int(ch.sum()), max_abs_DN=int(np.abs(n_.astype(np.int32) - c_.astype(np.int32)).max()))
    if lid in BRNO:
        z = np.load(R / f'4-RESULTATS/v113_estrelles_20260928/brno/L{lid}.npz'); x0, y0, x1, y1 = [int(v) for v in z['bbox']]
        for cid, k in ((0, 'R'), (1, 'G'), (2, 'B'), (-1, 'A')): canvis[cid] = q_blocs(z[k])
        nou_marc = (x0, y0, x1, y1); nou_nom = BRNO[lid]
        info['capes'][str(lid)] = dict(marc_V113=[L['left'], L['top'], L['right'], L['bottom']], marc_nou=list(nou_marc), nom=[rec.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME), nou_nom], font='4-RESULTATS/v113_estrelles_20260928/brno (b1, encaix per estrelles)')
    if lid == 301 and A.c301:
        cdir = Path(A.c301).resolve(); rc = json.loads((cdir / 'RECEIPT.json').read_text()); assert rc['alpha_exact'] and rc['box'] == [7356, 4320, 9348, 6263]
        for cid in (0, 1, 2):
            n_ = q_blocs(np.load(cdir / f'L301_c{cid}.npy')); act, org = p.channel(lid, cid); assert org == (7356, 4320) and act.shape == n_.shape
            if (n_ != act).any(): canvis[cid] = n_
            info['capes'].setdefault('301', {})[str(cid)] = dict(canviats=int((n_ != act).sum()))
        info['c301'] = dict(carpeta=str(cdir.relative_to(R)), rebut_sha256=sha(cdir / 'RECEIPT.json'))
    if lid == 202 and A.c202:
        z = np.load(A.c202); assert (L['left'], L['top'], L['right'], L['bottom']) == (0, 0, 10551, 7506)
        for cid, k in ((0, 'R'), (1, 'G'), (2, 'B'), (-1, 'A'), (-2, 'M')):
            if k not in z.files: continue
            n_ = q_blocs(z[k]) if cid != -2 else z[k]; act, _ = p.channel(lid, cid)
            if (n_ != act).any(): canvis[cid] = n_
            info['capes'].setdefault('202', {})[str(cid)] = dict(canviats=int((n_ != act).sum()))
        info['c202'] = dict(fitxer=str(Path(A.c202).resolve().relative_to(R)), sha256=sha(Path(A.c202)))
    if canvis or nou_marc:
        rec = copy.deepcopy(rec)
        if nou_marc: rec.left, rec.top, rec.right, rec.bottom = nou_marc
        for i, ch in enumerate(rec.channel_info):
            cid = int(ch.id)
            if cid in canvis:
                bts = enc(canvis[cid]); key = f'L{lid}_c{cid}'; MEM[key] = bts; ch.length = len(bts); channels[i] = (key, 0, ch.length)
            elif nou_marc and cid != -2: raise RuntimeError(f'capa {lid}: canvi de marc sense el canal {cid}')
        if lid in FONT and len(canvis):
            vell = rec.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME); nn = re.sub(r'\bV(9\d|1\d\d)\b', 'V113', vell, count=1); renomena(rec, nn)
        if nou_nom: renomena(rec, nou_nom)
        buf = io.BytesIO(); rec.write(buf, version=2); raw = buf.getvalue()
    records.append((raw, channels, lid))
    if lid == 202 and A.nova_capa:
        # capa nova just damunt de la 202 («cada canvi, una capa»): còpia del registre de la 267 (Sobreexposició lineal, sense màscara, canals −1,0,1,2)
        tpl = next(r for r, _ in s['recs'] if rid(r) == 267)
        assert [int(c.id) for c in tpl.channel_info] == [-1, 0, 1, 2] and tpl.mask_data is None and tpl.blend_mode.name == 'LINEAR_DODGE'
        assert A.nova_id not in {rid(r) for r, _ in s['recs']}
        z = np.load(A.nova_capa); x0, y0, x1, y1 = [int(v) for v in z['bbox']]
        nr = copy.deepcopy(tpl); nr.top, nr.left, nr.bottom, nr.right = y0, x0, y1, x1
        nr.opacity = 255; nr.clipping = 0; nr.flags.visible = True
        nr.tagged_blocks.set_data(Tag.LAYER_ID, A.nova_id); renomena(nr, A.nova_nom)
        nch = []
        for ci in nr.channel_info:
            cid = int(ci.id); arr = q_blocs(z[{-1: 'A', 0: 'R', 1: 'G', 2: 'B'}[cid]]); assert arr.shape == (y1 - y0, x1 - x0)
            bts = enc(arr); key = f'L{A.nova_id}_c{cid}'; MEM[key] = bts; ci.length = len(bts); nch.append((key, 0, ci.length))
        buf = io.BytesIO(); nr.write(buf, version=2); records.append((buf.getvalue(), nch, A.nova_id))
        info['capa_nova'] = dict(id=A.nova_id, nom=A.nova_nom, plantilla=267, darrere_de=202, marc=[x0, y0, x1, y1], font=str(Path(A.nova_capa).resolve().relative_to(R)), sha256=sha(Path(A.nova_capa)))
        print('capa nova', info['capa_nova'], flush=True)
    if lid in FONT or lid in BRNO or lid in (202, 301): print(lid, json.dumps(info['capes'].get(str(lid)), ensure_ascii=False)[:300], f'{time.time()-t0:.0f}s', flush=True)
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
for lid in BRNO:   # el marc nou llegit de nou
    l = Q.layer(lid); assert [l['left'], l['top'], l['right'], l['bottom']] == info['capes'][str(lid)]['marc_nou']
assert sha(SRC) == SHA_SRC
info.update(sortida=str(DST.relative_to(R)), sha256=sha(DST), bytes=DST.stat().st_size, verificacio='registres i canals iguals byte a byte a la V113 o al ràster nou codificat; marcs de Brno relegits', segons=round(time.time() - t0, 1))
DST.with_suffix('.json').write_text(json.dumps(info, ensure_ascii=False, indent=1)); print(json.dumps({k: v for k, v in info.items() if k != 'capes'}, ensure_ascii=False))
