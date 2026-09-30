"""b2e · Prova E de la vora esquerra: la prova B (filtres sense pujada) EXACTA, amb una sola diferència: la capa d'ajust 241 «Claridad y borrar neblina 1»
oculta (bandera de visibilitat del registre). Per saber si les línies paral·leles al limbe que queden les fa (o les amplia) aquest ajust de
contrast local, que actua sobre el compost sencer i és més fort a la vora de màxim contrast. Sortida: V89_prova_D.psb i B2E.json."""
from v89_comu import *
from psb69 import PSB, BIG_KEYS, _rf
import struct, io, copy, logging
from psd_tools.psd.layer_and_mask import LayerRecord
from psd_tools.constants import Tag
logging.getLogger('psd_tools').setLevel(logging.ERROR)
claim()
SRC = SORT / 'V89_prova_B.psb'; SHA_SRC = sha(SRC); DST = SORT / 'V89_prova_E.psb'; assert not DST.exists()
pass
def llegeix_registres(path):
    with open(path, 'rb') as f:
        f.seek(26)
        for _ in range(2): n = _rf(f, 'I')[0]; f.seek(n, 1)
        lmpos = f.tell(); lmlen = _rf(f, 'Q')[0]; lmend = f.tell() + lmlen; n = _rf(f, 'Q')[0]; assert n == 0; n = _rf(f, 'I')[0]; f.seek(n, 1)
        while f.tell() + 12 <= lmend:
            sig, key = _rf(f, '4s4s'); fmt = 'Q' if key in BIG_KEYS else 'I'; lenpos = f.tell(); n = _rf(f, fmt)[0]; start = f.tell()
            if key == b'Lr16': break
            f.seek(start + (n + 3) // 4 * 4)
        count = _rf(f, 'h')[0]; recs = []
        for _ in range(abs(count)):
            pos = f.tell(); r = LayerRecord.read(f, version=2); end = f.tell(); f.seek(pos); raw = f.read(end - pos); recs.append((r, raw, pos))
        chan_start = f.tell()
    return dict(lmpos=lmpos, lmlen=lmlen, lenpos=lenpos, lrstart=start, lrpadend=start + (n + 3) // 4 * 4, count=count, recs=recs, chan_start=chan_start)
S = llegeix_registres(SRC); rid = lambda r: int(r.tagged_blocks.get_data(Tag.LAYER_ID))
nous = []; canvi = None
for r, raw, pos in S['recs']:
    if rid(r) == 241:
        assert r.flags.visible; r2 = copy.deepcopy(r); r2.flags.visible = False; b = io.BytesIO(); r2.write(b, version=2); nr = b.getvalue()
        assert len(nr) == len(raw), 'el registre ha de mantenir la mida'; nous.append(nr); canvi = str(r.tagged_blocks.get_data(Tag.UNICODE_LAYER_NAME))
    else: nous.append(raw)
assert canvi is not None
# el registre nou té la mateixa mida: es copia el fitxer sencer i se sobreescriuen només els bytes dels registres
with open(SRC, 'rb') as f, open(DST, 'xb') as g:
    while True:
        blk = f.read(64 << 20)
        if not blk: break
        g.write(blk)
with open(DST, 'r+b') as g:
    for (r, raw, pos), nr in zip(S['recs'], nous):
        if nr is not raw: g.seek(pos); g.write(nr)
q = PSB(str(DST)); v = {L['id']: L['visible'] for L in q.layers}; p = PSB(str(SRC)); v0 = {L['id']: L['visible'] for L in p.layers}
dif = [k for k in v if v[k] != v0[k]]; assert dif == [241], dif
desa_json('B2E.json', dict(font=dict(path=str(SRC.relative_to(ARREL)), sha256=SHA_SRC), desti=str(DST.relative_to(ARREL)), unic_canvi=f'capa 241 «{canvi}» oculta', capes=len(q.layers)))
log(f'V89_prova_E.psb (B sense claredat): {len(q.layers)} capes; única diferència, la 241 oculta')
