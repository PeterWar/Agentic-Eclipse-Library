"""m1 · V113 (Claude, 28-09-2026): munta el PSB de pas de la V113 a partir de 1-PHOTOSHOP/V112.psb, BYTE A BYTE, canviant NOMÉS els canals
de les capes on la cadena nova (fonts amb la Sony A corregida, f1 --local) dona una altra cosa que la cadena de control (les fonts de la V108).
Regla per capa i canal (torre de Pisa, sense residus):
    nou = q(sortida de la cadena V113), ctrl = q(sortida de control), actual = canal de la V112
    canvi = nou ≠ ctrl;  COMPROVACIÓ: actual[canvi] == ctrl[canvi] (el control reprodueix la V112 on hi ha canvi; si no, s'atura)
    canal V113 = actual, amb canal[canvi] = nou[canvi]
  Controls: 3, 54, 47, 49, 51, 55, 56 → cadena V108 (4-RESULTATS/v108_20260926/cadena/v108/estat_v108, la que va fer aquests ràsters);
            45, 46 → RHEF «mass» del Codex (4-RESULTATS/v112_20260928/rhef_mass); 41, 42 → genoll recepta 8 del Codex (sensor_mass_raw/nrgf).
  Els filtres són grisos: el ràster va als tres canals. L'alfa, amb la mateixa regla. Màscares, modes, opacitats, visibilitat: de la V112.
  Les capes que canvien passen a dir «V113» on deien V108/V112. La 301 (cantonada del logo) s'hi posa si es dona --c301 <carpeta> amb
  L301_c{0,1,2}.npy i RECEIPT.json (alfa exacta, regenerada des del render natiu de la pila de sota).
Ús: m1_munta_v113.py <sortida.psb> [--c301 <carpeta>]  (la sortida ha de ser dins de 4-RESULTATS/v112_claude_20260928 i no pot existir)"""
from pathlib import Path
import sys, json, io, copy, struct, hashlib, re, time, argparse
import numpy as np
R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB, llegeix_registres, rid, enc, q_blocs, sha, renomena
from psd_tools.constants import Tag
ap = argparse.ArgumentParser(); ap.add_argument('sortida'); ap.add_argument('--c301'); ap.add_argument('--variant', default='v113'); A = ap.parse_args(); t0 = time.time()
assert json.loads((R / '.coordination/claim.lock/owner.json').read_text())['claim_id'] == 'CLAUDE_V112_MUNTATGE_20260928'
SRC = R / '1-PHOTOSHOP/V112.psb'; SHA_SRC = 'c64288633aada1550ff11216eb681354f56bc68a116e8d5044026893aa2711bd'
DST = Path(A.sortida).resolve(); assert str(DST).startswith(str(R / '4-RESULTATS/v112_claude_20260928')) and not DST.exists()
NOU = R / '4-RESULTATS/v112_claude_20260928/cadena' / A.variant; CT = R / '4-RESULTATS/v108_20260926/cadena/v108'; CX = R / '4-RESULTATS/v112_20260928'
FONT = {}
for lid in (54, 47, 49, 51, 55, 56):
    FONT[lid] = dict(nou=(NOU / f'estat_v108/L{lid}_G.npy', NOU / f'estat_v108/L{lid}_alfa.npy'), ctrl=(CT / f'estat_v108/L{lid}_G.npy', CT / f'estat_v108/L{lid}_alfa.npy'))
FONT[3] = dict(nou=(NOU / 'estat_v108/L3_RGB.npy', NOU / 'estat_v108/L3_alfa.npy'), ctrl=(CT / 'estat_v108/L3_RGB.npy', CT / 'estat_v108/L3_alfa.npy'))
for lid, tg in ((45, 'P02c_RHEF_local60_native'), (46, 'P02d_RHEF_local30_native')):
    FONT[lid] = dict(nou=(NOU / f'filtres_mass/filtres/{tg}_u16.npy', NOU / f'filtres_mass/filtres/{tg}_alfa_u16.npy'), ctrl=(CX / f'rhef_mass/filtres/{tg}_u16.npy', CX / f'rhef_mass/filtres/{tg}_alfa_u16.npy'))
for lid, tg in ((41, 'P01_NRGF'), (42, 'P01_NRGF_extrap')):
    d = 'nrgf/G_MAX_T_e30_W_H0'
    FONT[lid] = dict(nou=(NOU / f'{d}/{tg}_u16.npy', NOU / f'{d}/{tg}_alfa_u16.npy'), ctrl=(CX / f'sensor_mass_raw/{d}/{tg}_u16.npy', CX / f'sensor_mass_raw/{d}/{tg}_alfa_u16.npy'))
assert sha(SRC) == SHA_SRC, 'la V112 ha canviat'
p = PSB(str(SRC)); s = llegeix_registres(SRC)
MEM = {}   # canals codificats en memòria (sense memòria cau al disc: l'espai és just)
info = dict(font=str(SRC.relative_to(R)), sha256_font=SHA_SRC, variant=A.variant, regla='canal = V112, amb canal[nou≠ctrl] = nou; comprovat V112[nou≠ctrl] == ctrl', capes={})

def nom_v113(nom):
    return re.sub(r'\bV(9\d|1\d\d)\b', 'V113', nom, count=1) if re.search(r'\bV(9\d|1\d\d)\b', nom) else nom + ' · V113'

records = []
for rec, raw in s['recs']:
    lid = rid(rec); L = p.layer(lid)
    channels = [(Path(p.path), *L['chans'][int(ch.id)]) for ch in rec.channel_info]
    canvis = {}
    if lid in FONT:
        fn, fa = FONT[lid]['nou']; cn, ca = FONT[lid]['ctrl']
        nou = np.load(fn, mmap_mode='r'); ctl = np.load(cn, mmap_mode='r')
        for cid in (0, 1, 2, -1):
            if cid == -1: n_, c_ = q_blocs(np.load(fa)), q_blocs(np.load(ca))
            elif nou.ndim == 3: n_, c_ = q_blocs(np.asarray(nou[..., cid])), q_blocs(np.asarray(ctl[..., cid]))
            else:
                if cid > 0: n_, c_ = canvis.get('_n'), canvis.get('_c')
                else: n_, c_ = q_blocs(np.asarray(nou)), q_blocs(np.asarray(ctl)); canvis['_n'], canvis['_c'] = n_, c_
            act, org = p.channel(lid, cid); assert org == (0, 0) and act.shape == n_.shape
            ch = n_ != c_
            dif_ctrl = int(np.count_nonzero(act[ch] != c_[ch]))
            assert dif_ctrl == 0, f'capa {lid} canal {cid}: el control no reprodueix la V112 a {dif_ctrl} dels {int(ch.sum())} píxels que canvien'
            if ch.any():
                t = act.copy(); t[ch] = n_[ch]; canvis[cid] = t
            info['capes'].setdefault(str(lid), {})[str(cid)] = dict(canviats=int(ch.sum()), max_abs_DN=int(np.abs(n_.astype(np.int32) - c_.astype(np.int32)).max()))
        canvis.pop('_n', None); canvis.pop('_c', None)
    if lid == 301 and A.c301:
        cdir = Path(A.c301).resolve(); rc = json.loads((cdir / 'RECEIPT.json').read_text()); assert rc['alpha_exact'] and rc['box'] == [7356, 4320, 9348, 6263]
        for cid in (0, 1, 2):
            n_ = q_blocs(np.load(cdir / f'L301_c{cid}.npy')); act, org = p.channel(lid, cid); assert org == (7356, 4320) and act.shape == n_.shape
            if (n_ != act).any(): canvis[cid] = n_
            info['capes'].setdefault('301', {})[str(cid)] = dict(canviats=int((n_ != act).sum()))
        info['c301'] = dict(carpeta=str(cdir.relative_to(R)), rebut_sha256=sha(cdir / 'RECEIPT.json'))
    if canvis:
        rec = copy.deepcopy(rec)
        for i, ch in enumerate(rec.channel_info):
            cid = int(ch.id)
            if cid in canvis:
                bts = enc(canvis[cid]); key = f'L{lid}_c{cid}'; MEM[key] = bts; ch.length = len(bts); channels[i] = (key, 0, ch.length)
        if lid in FONT:
            vell = rec.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME); renomena(rec, nom_v113(vell)); info['capes'][str(lid)]['nom'] = [vell, nom_v113(vell)]
        buf = io.BytesIO(); rec.write(buf, version=2); raw = buf.getvalue()
    records.append((raw, channels, lid))
    if lid in FONT or lid == 301: print(lid, info['capes'].get(str(lid)), f'{time.time()-t0:.0f}s', flush=True)
# escriptura (com psb_munta.assemble del Codex): registres, canals, i la resta del fitxer tal qual
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
# verificació: cada registre i cada canal, byte a byte, igual al que s'ha volgut escriure
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
                while rem:
                    nn = min(rem, 32 << 20); hb.update(b2.read(nn)); rem -= nn
            else:
                with file.open('rb') as a_:
                    a_.seek(off)
                    while rem:
                        nn = min(rem, 32 << 20); ha.update(a_.read(nn)); hb.update(b2.read(nn)); rem -= nn
        assert ha.digest() == hb.digest(), (lid, int(c.id))
assert sha(SRC) == SHA_SRC
info.update(sortida=str(DST.relative_to(R)), sha256=sha(DST), bytes=DST.stat().st_size, verificacio='tots els registres i canals iguals byte a byte a la V112 o al ràster nou codificat', segons=round(time.time() - t0, 1))
DST.with_suffix('.json').write_text(json.dumps(info, ensure_ascii=False, indent=1)); print(json.dumps({k: v for k, v in info.items() if k != 'capes'}, ensure_ascii=False))
