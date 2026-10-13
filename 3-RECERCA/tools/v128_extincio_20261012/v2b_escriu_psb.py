"""v2b · Escriu la V128.psb NOVA (regla del limbe, 12-10-2026) amb el MATEIX escriptor del v2: la V125-FINAL de Pere + 2 capes
a sobre de tot. NO fa servir psd-tools per escriure. Canvia només respecte del v2:
  · la capa A és la matriu OUTB del v1b (la regla del limbe predeclarada, PREDECLARACIO_LIMBE.md), no la OUT del v1;
  · la capa B (el mateix E/2 del v1, E_u16.npy, comprovat pel SHA del V1_CORRECCIO.json) es diu «Factor E de l'extinció,
    referència 12-10» (amb data, AGENTS §5);
  · el fitxer de 1-PHOTOSHOP pot existir encara (la V128 anterior): el v2b escriu només a la carpeta de treball; retirar
    l'anterior amb paperera.py i moure-hi la nova és un pas a part (executa_b.sh), després del v3b;
  · rebut: V2B_PSB.json.
Text del v2:

Per què no psd-tools: en re-serialitzar la V125-FINAL, psd-tools reescriu els registres de capa, i a la V127 el bloc «hue2» de
la capa d'ajust «Tono/saturación 1» de Pere va passar de 192 a 100 bytes (ho mostra el v3). Aquí la V128 és una CÒPIA dels
bytes de la V125-FINAL on només canvien, i en aquests llocs exactes:
  · el recompte de capes del bloc «Lr16» (49 → 51), la longitud del bloc i la de la secció de capes i màscares;
  · dos registres nous afegits darrere dels 49 de Pere, i les seves dades de canal darrere de les de Pere
    (a l'ordre del fitxer, el darrer registre és la capa de més amunt):
      1. «Extinció diferencial corregida, aproximació sobre la final 12-10»: Normal, 100 %, VISIBLE, llenç sencer, opaca;
         RGB = la matriu OUTB del v1b (l'e3 a resolució plena amb la regla del limbe);
      2. «Factor E de l'extinció, referència 12-10»: Normal, 100 %, OCULTA, gris = E/2 (gris del 50 % = E 1);
    compressió ZIP amb predicció (la de les capes de Pere), feta aquí amb numpy + zlib;
  · la imatge fusionada (RAW, 4 canals, com la de la V125-FINAL): RGB = OUTB (la capa nova és opaca i ho tapa tot) i
    l'alfa opaca a tot arreu;
  · tres recursos del document que depenen de les capes o de la fusionada: 1026 i 1072 (un valor per capa: s'hi afegeixen
    els de les 2 capes noves, iguals als de les de Pere) i 1036 (la miniatura, refeta de la fusionada nova i passada a sRGB,
    com la de la V125-FINAL).
Tota la resta (capçalera, perfil ICC, XMP, altres recursos, blocs globals, els 49 registres i totes les seves dades de
canal) es copia byte a byte. El fitxer s'escriu a la carpeta de treball; el v3b el verifica i només llavors, retirada
l'anterior, es mou a 1-PHOTOSHOP/V128.psb (mateix disc: és un canvi de nom, no una còpia).
Ús: PYTHONDONTWRITEBYTECODE=1 <python> v2b_escriu_psb.py <carpeta_de_treball>"""
import hashlib
import io
import json
import struct
import sys
import time
import zlib
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageCms

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psb_cru as pc  # noqa: E402

T0 = time.time()
ARREL = Path(__file__).resolve().parents[3]                              # …/4-Photoshop
SRC = ARREL / '1-PHOTOSHOP/V125-FINAL.psb'
FINAL = ARREL / '1-PHOTOSHOP/V128.psb'
RES = ARREL / '3-RECERCA/resultats/v128_extincio_20261012'
TREB = Path(sys.argv[1]).resolve()
DST = TREB / 'V128.psb'
SHA_SRC = 'bfa9daeef208f61c55bc736e6a71e01754edb4cab5f8fe2f747ed23281645797'
NOM_A = 'Extinció diferencial corregida, aproximació sobre la final 12-10'
NOM_B = "Factor E de l'extinció, referència 12-10"
for n in (NOM_A, NOM_B):
    assert len(n.split()) <= 9, n
    n.encode('mac_roman')
assert not DST.exists(), f'{DST} ja existeix'


def sha256(p, bloc=1 << 24):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(bloc), b''):
            h.update(b)
    return h.hexdigest()


sha_src = sha256(SRC)
assert sha_src == SHA_SRC, f'la V125-FINAL no és la de l\'ESTAT: {sha_src}'
p = pc.PSB(SRC)
H, W = p.alt, p.ample
assert (p.versio, p.canals, H, W, p.bits, p.mode) == (2, 4, 5021, 7933, 16, 3), pc.resum(p)
assert len(p.capes) == 49 and p.lr_count == 49 and p.id_compressio == 0
assert p.canals_fi == p.lr_cos_fi and p.lr['longitud'] % 4 == 0
print(f'V125-FINAL {sha_src[:12]}… llegida ({time.time() - T0:.0f} s)', flush=True)

OUT = np.load(TREB / 'OUTB_rgb16_limbe.npy')
E16 = np.load(TREB / 'E_u16.npy')
assert OUT.shape == (H, W, 3) and OUT.dtype == np.uint16 and E16.shape == (H, W) and E16.dtype == np.uint16
v1 = json.load(open(RES / 'V1_CORRECCIO.json'))
v1b = json.load(open(RES / 'V1B_CORRECCIO_LIMBE.json'))
assert hashlib.sha256(np.ascontiguousarray(OUT).tobytes()).hexdigest() == v1b['matriu']['sha256_bytes_OUTB']
assert hashlib.sha256(np.ascontiguousarray(E16).tobytes()).hexdigest() == v1['matriu']['E_u16']['sha256_bytes']
assert v1b['veredicte'] == 'PASSA' and v1b['e3']['E3_PIS2_identic'] and all(v1b['e3']['vistes_identiques'].values())


# ------------------------------------------------------------------------------------------------ blocs de la capa
def blocs_de(i):
    """(màscara, blending ranges, nom pascal, [(clau, dades)]) del registre i de Pere, llegit en cru."""
    c = p.capes[i]
    e0, ext = c['extra']
    b = p.b
    o = e0
    ml = pc.u32(b, o); o += 4 + ml
    bl = pc.u32(b, o); br = bytes(b[o + 4:o + 4 + bl]); o += 4 + bl
    pn = 1 + b[o]; pn += (-pn) % 4; o += pn
    out = []
    while o < e0 + ext:
        sig, clau = bytes(b[o:o + 4]), bytes(b[o + 4:o + 8])
        gros = sig == b'8B64' or clau in pc.CLAUS_GROSSES
        ln = pc.u64(b, o + 8) if gros else pc.u32(b, o + 8)
        d = o + 8 + (8 if gros else 4)
        out.append((clau, bytes(b[d:d + ln])))
        o = d + ln + (ln % 2)
    return br, out


ids = []
for i in range(49):
    _, bl = blocs_de(i)
    ids.append(struct.unpack('>I', dict(bl)[b'lyid'])[0])
BR, blocs_capa1 = blocs_de(41)                                   # «Capa 1» de Pere: la capa de píxels de més amunt
assert p.capes[41]['nom_pascal'] == 'Capa 1' and len(BR) == 40
B1 = dict(blocs_capa1)
ID_A, ID_B = max(ids) + 1, max(ids) + 2


def bloc(clau, dades):
    assert len(dades) % 4 == 0
    return b'8BIM' + clau + struct.pack('>I', len(dades)) + dades


def registre(nom, lyid, visible, longituds):
    pn = nom.encode('mac_roman')[:31]
    ps = bytes([len(pn)]) + pn
    ps += b'\0' * ((-len(ps)) % 4)
    lu = struct.pack('>I', len(nom)) + nom.encode('utf-16-be')
    lu += b'\0' * ((-len(lu)) % 4)
    extra = struct.pack('>I', 0)                                 # sense màscara
    extra += struct.pack('>I', len(BR)) + BR                     # blending ranges com la «Capa 1» (tot obert)
    extra += ps
    extra += bloc(b'luni', lu) + bloc(b'lnsr', b'layr') + bloc(b'lyid', struct.pack('>I', lyid))
    for k in (b'clbl', b'infx', b'knko', b'lspf', b'lclr'):     # mateixos valors que la «Capa 1»
        extra += bloc(k, B1[k])
    r = struct.pack('>4i', 0, 0, H, W) + struct.pack('>H', 4)   # dalt, esquerra, baix, dreta; 4 canals
    for cid in (-1, 0, 1, 2):
        r += struct.pack('>hQ', cid, longituds[cid])
    r += b'8BIM' + b'norm' + bytes([255, 0, 0x08 if visible else 0x0A, 0])   # opacitat 255, sense clipping, visibilitat
    r += struct.pack('>I', len(extra)) + extra
    return r


def zip_prediccio(pla):
    """ZIP amb predicció de 16 bits (com el Photoshop): diferència horitzontal per fila mòdul 2^16, big-endian, deflate."""
    a = np.ascontiguousarray(pla, np.uint16)
    d = a.copy()
    d[:, 1:] = a[:, 1:] - a[:, :-1]                              # uint16: mòdul 65536
    return struct.pack('>H', 3) + zlib.compress(d.astype('>u2').tobytes(), 6)


def desfes_zip_prediccio(dades):
    assert struct.unpack('>H', dades[:2])[0] == 3
    d = np.frombuffer(zlib.decompress(dades[2:]), '>u2').reshape(H, W).astype(np.uint16)
    return np.cumsum(d, axis=1, dtype=np.uint16)


opac = np.full((H, W), 65535, np.uint16)
canals_A = {-1: zip_prediccio(opac), 0: zip_prediccio(OUT[..., 0]), 1: zip_prediccio(OUT[..., 1]), 2: zip_prediccio(OUT[..., 2])}
canals_B = {-1: zip_prediccio(opac), 0: zip_prediccio(E16), 1: zip_prediccio(E16), 2: zip_prediccio(E16)}
for cid in (0, 1, 2):                                            # autocomprovació de l'escriptor (el v3 ho refà amb psd-tools)
    assert np.array_equal(desfes_zip_prediccio(canals_A[cid]), OUT[..., cid])
    assert np.array_equal(desfes_zip_prediccio(canals_B[cid]), E16)
assert np.array_equal(desfes_zip_prediccio(canals_A[-1]), opac)
reg_A = registre(NOM_A, ID_A, True, {k: len(v) for k, v in canals_A.items()})
reg_B = registre(NOM_B, ID_B, False, {k: len(v) for k, v in canals_B.items()})
dades_noves = b''.join(canals_A[c] for c in (-1, 0, 1, 2)) + b''.join(canals_B[c] for c in (-1, 0, 1, 2))
print(f'capes noves: canals {[len(canals_A[c]) for c in (-1, 0, 1, 2)]} + {[len(canals_B[c]) for c in (-1, 0, 1, 2)]} bytes '
      f'({time.time() - T0:.0f} s)', flush=True)

# ------------------------------------------------------------------------------------------------ recursos
icc = None
nous_recursos = {}
for r in p.recursos:
    d = bytes(p.b[r['dades']:r['dades'] + r['mida']])
    if r['id'] == 1039:
        icc = d
    if r['id'] == 1026:
        assert len(d) == 2 * 49 and set(d) == {0}
        nous_recursos[1026] = d + b'\0\0' * 2                    # grup d'arrossegament 0, com totes les de Pere
    elif r['id'] == 1072:
        assert len(d) == 49 and set(d) == {1}
        nous_recursos[1072] = d + b'\x01' * 2                    # «group enabled» 1, com totes les de Pere
    elif r['id'] == 1036:
        cap = struct.unpack('>6I2H', d[:28])
        assert cap[0] == 1 and cap[6:] == (24, 1), cap
        tw, th = cap[1], cap[2]
assert icc is not None and len(nous_recursos) == 2


def miniatura(rgb16):
    small = cv2.resize(rgb16.astype(np.float32) / 65535.0, (tw, th), interpolation=cv2.INTER_AREA)
    s8 = Image.fromarray((np.clip(small, 0, 1) * 255 + 0.5).astype(np.uint8))
    return ImageCms.profileToProfile(s8, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'),
                                     renderingIntent=ImageCms.Intent.RELATIVE_COLORIMETRIC, outputMode='RGB')


# control: la miniatura de la V125-FINAL refeta amb la mateixa recepta s'ha d'assemblar a la que hi ha (sRGB, no Adobe RGB)
r1036 = [r for r in p.recursos if r['id'] == 1036][0]
vella = np.asarray(Image.open(io.BytesIO(bytes(p.b[r1036['dades'] + 28:r1036['dades'] + r1036['mida']]))).convert('RGB'), np.float64)
U = np.stack([np.frombuffer(p.b, '>u2', H * W, p.id_pos + 2 + k * H * W * 2).reshape(H, W) for k in range(3)], -1)
mae_ctrl = float(np.abs(np.asarray(miniatura(U), np.float64) - vella).mean())
bio = io.BytesIO()
miniatura(OUT).save(bio, format='JPEG', quality=90, subsampling=0, optimize=False, progressive=False)
jpg = bio.getvalue()
wb = (tw * 24 + 31) // 32 * 4
nous_recursos[1036] = struct.pack('>6I2H', 1, tw, th, wb, wb * th, len(jpg), 24, 1) + jpg
print(f'miniatura {tw}×{th}: la recepta reprodueix la vella amb MAE {mae_ctrl:.2f}/255 ({time.time() - T0:.0f} s)', flush=True)

seccio_recursos = b''
for r in p.recursos:
    if r['id'] in nous_recursos:
        cap = bytes(p.b[r['pos']:r['dades'] - 4])                # signatura, id i nom, tal com són
        d = nous_recursos[r['id']]
        seccio_recursos += cap + struct.pack('>I', len(d)) + d + (b'\0' if len(d) % 2 else b'')
    else:
        seccio_recursos += bytes(p.b[r['pos']:r['fi']])

# ------------------------------------------------------------------------------------------------ fusionada
A16 = np.frombuffer(p.b, '>u2', H * W, p.id_pos + 2 + 3 * H * W * 2)
alfa_no_opaca = int((A16 < 65535).sum())
alfa_min = int(A16.min())
del U, A16

# ------------------------------------------------------------------------------------------------ escriptura
cos_lr_vell = p.lr['longitud']
cos_lr_nou = cos_lr_vell + len(reg_A) + len(reg_B) + len(dades_noves)
farciment = (-cos_lr_nou) % 4
cos_lr_nou += farciment
delta_lmi = cos_lr_nou - cos_lr_vell
mapa = []                                                       # (què, inici a la V128, fi a la V128, inici a la V125 o None)
h = hashlib.sha256()
pos = 0


def escriu(fh, dades, que, origen=None):
    global pos
    fh.write(dades)
    h.update(dades)
    mapa.append((que, pos, pos + len(dades), origen))
    pos += len(dades)


def copia(fh, a, z, que):
    global pos
    ini = pos
    o = a
    while o < z:
        q = min(z, o + (64 << 20))
        m = p.b[o:q]
        fh.write(m)
        h.update(m)
        o = q
    pos += z - a
    mapa.append((que, ini, pos, a))


with open(DST, 'xb') as fh:
    copia(fh, 0, p.recursos_pos, 'capçalera i color mode (iguals)')
    escriu(fh, struct.pack('>I', len(seccio_recursos)), 'longitud dels recursos')
    escriu(fh, seccio_recursos, 'recursos (1026, 1072 i 1036 nous; la resta iguals)')
    escriu(fh, struct.pack('>Q', p.lmi_len + delta_lmi), 'longitud de la secció de capes i màscares')
    copia(fh, p.lmi_pos + 8, p.lr['pos'] + 8, 'informació de capes principal (buida), màscara global, Mt16, signatura de Lr16 (iguals)')
    escriu(fh, struct.pack('>Q', cos_lr_nou), 'longitud de Lr16')
    escriu(fh, struct.pack('>h', 51 if p.lr_count > 0 else -51), 'recompte de capes')
    copia(fh, p.lr_count_pos + 2, p.registres_fi, '49 registres de Pere (iguals)')
    escriu(fh, reg_A, 'registre nou A (visible)')
    escriu(fh, reg_B, 'registre nou B (ocult)')
    copia(fh, p.registres_fi, p.canals_fi, 'dades de canal de les 49 capes de Pere (iguals)')
    escriu(fh, dades_noves, 'dades de canal de les capes noves')
    if farciment:
        escriu(fh, b'\0' * farciment, 'farciment de Lr16')
    copia(fh, p.lr['fi'], p.lmi_fi, 'blocs globals LMsk, Pat2, CAI, OCIO, GenI, FMsk, cinf (iguals)')
    escriu(fh, struct.pack('>H', 0), 'compressió de la fusionada: RAW')
    for c in range(3):
        escriu(fh, np.ascontiguousarray(OUT[..., c]).astype('>u2').tobytes(), f'fusionada, canal {"RGB"[c]} = capa nova')
    escriu(fh, opac.astype('>u2').tobytes(), 'fusionada, alfa opaca')
sha_dst = h.hexdigest()
mida = DST.stat().st_size
assert mida == pos
print(f'escrit {DST} ({mida / 1e9:.3f} GB, SHA {sha_dst[:12]}…) ({time.time() - T0:.0f} s)', flush=True)

info = dict(
    guio=str(Path(__file__).resolve().relative_to(ARREL)), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
    font=dict(fitxer='1-PHOTOSHOP/V125-FINAL.psb', sha256=sha_src, mida=p.mida),
    desti=dict(fitxer_de_treball=str(DST), fitxer_final='1-PHOTOSHOP/V128.psb', sha256=sha_dst, mida=mida),
    escriptor='còpia de bytes de la V125-FINAL + registres i canals nous fets a mà (struct, numpy, zlib); sense psd-tools',
    capes_noves=[dict(nom=NOM_A, lyid=ID_A, mode='Normal', opacitat=255, visible=True, caixa=[0, 0, W, H],
                      contingut='OUTB del v1b (e3 a resolució plena amb la regla del limbe predeclarada), alfa opaca', compressio='ZIP amb predicció',
                      bytes_canals={str(k): len(v) for k, v in canals_A.items()}),
                 dict(nom=NOM_B, lyid=ID_B, mode='Normal', opacitat=255, visible=False, caixa=[0, 0, W, H],
                      contingut='gris = E/2 (gris del 50 % = E 1), el mateix a R, G i B; alfa opaca', compressio='ZIP amb predicció',
                      bytes_canals={str(k): len(v) for k, v in canals_B.items()})],
    lyid_de_Pere=ids, fusionada=dict(compressio='RAW', canals='R, G, B = capa nova; alfa = 65535 a tot arreu',
                                     alfa_V125=dict(pixels_no_opacs=alfa_no_opaca, minim=alfa_min)),
    recursos_canviats={'1026': '49 → 51 valors (0, grup d\'arrossegament)', '1072': '49 → 51 valors (1)',
                       '1036': f'miniatura {tw}×{th} refeta de la fusionada nova, sRGB, JPEG {len(jpg)} bytes; '
                               f'control: la recepta refà la vella amb MAE {mae_ctrl:.2f}/255'},
    lr16=dict(longitud_vella=cos_lr_vell, longitud_nova=cos_lr_nou, farciment=farciment, recompte=[p.lr_count, 51]),
    mapa=[dict(que=q, v128=[a, z], v125=o) for q, a, z, o in mapa], segons=round(time.time() - T0, 1))
json.dump(info, open(RES / 'V2B_PSB.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps({k: info[k] for k in ('desti', 'fusionada', 'recursos_canviats', 'lr16')}, indent=1, ensure_ascii=False))
