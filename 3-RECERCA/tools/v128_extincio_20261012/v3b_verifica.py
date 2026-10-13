"""v3b · Verificació de la V128.psb NOVA (regla del limbe, 12-10-2026): el v3 amb les entrades del v1b/v2b
(OUTB_rgb16_limbe.npy, V2B_PSB.json, el nom nou de la capa B), un TIFF de sips amb nom nou, i a més ael.photoshop.verify()
(51 capes de primer nivell: nom, mode, opacitat i visibilitat de totes; la capa A i la capa B píxel a píxel). Rebut:
V3B_VERIFICACIO.json.
Text del v3: verificació de la V128.psb amb tres lectors que no són l'escriptor (el v2 no fa servir psd-tools):
  A. psd-tools (lector complet): 51 capes; les 49 de Pere iguals a les de la V125-FINAL en nom, mode, opacitat, visibilitat,
     caixa, clipping, màscara i, per a CADA canal de CADA capa, les dades desades (sha-256 dels bytes comprimits i la
     compressió); les 2 noves descodificades amb psd-tools (layer.numpy) contra la matriu calculada; la fusionada contra la
     capa nova; la miniatura.
  B. lector cru propi (psb_cru, sense psd-tools): mapa de bytes de tot el fitxer contra la V125-FINAL: què és idèntic i què no.
  C. sips (ImageIO de macOS, cap línia compartida): llegeix la fusionada, la passa a TIFF i es compara amb la matriu.
A més: mida i SHA-256, i el mateix control de bytes sobre la V127 i la V126 (per documentar què hi va canviar psd-tools).
Ús: PYTHONDONTWRITEBYTECODE=1 <python> v3b_verifica.py <V128.psb> <carpeta_de_treball>"""
import hashlib
import io
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import psb_cru as pc  # noqa: E402

T0 = time.time()
ARREL = Path(__file__).resolve().parents[3]
SRC = ARREL / '1-PHOTOSHOP/V125-FINAL.psb'
RES = ARREL / '3-RECERCA/resultats/v128_extincio_20261012'
DST = Path(sys.argv[1]).resolve()
TREB = Path(sys.argv[2]).resolve()
NOM_A = 'Extinció diferencial corregida, aproximació sobre la final 12-10'
NOM_B = "Factor E de l'extinció, referència 12-10"
fallades = []


def comprova(ok, que, **dades):
    if not ok:
        fallades.append(dict(que=que, **dades))
        print('FALLA', que, dades, flush=True)
    return ok


def sha256(p, bloc=1 << 24):
    h = hashlib.sha256()
    with open(p, 'rb') as fh:
        for b in iter(lambda: fh.read(bloc), b''):
            h.update(b)
    return h.hexdigest()


sha_dst, sha_src = sha256(DST), sha256(SRC)
OUT = np.load(TREB / 'OUTB_rgb16_limbe.npy')
E16 = np.load(TREB / 'E_u16.npy')
H, W = OUT.shape[:2]
v2 = json.load(open(RES / 'V2B_PSB.json'))
v1b = json.load(open(RES / 'V1B_CORRECCIO_LIMBE.json'))
comprova(hashlib.sha256(np.ascontiguousarray(OUT).tobytes()).hexdigest() == v1b['matriu']['sha256_bytes_OUTB'], 'matriu_OUTB_del_v1b')
comprova(sha_dst == v2['desti']['sha256'], 'sha_igual_al_de_l_escriptor')
comprova(sha_src == v2['font']['sha256'], 'font_sense_canvis')

# ================================================================================================ B. lector cru
a, b = pc.PSB(SRC), pc.PSB(DST)
cru = {}
comprova(bytes(a.b[:26]) == bytes(b.b[:26]), 'capçalera_igual')
comprova(bytes(a.b[26:a.recursos_pos]) == bytes(b.b[26:b.recursos_pos]), 'color_mode_igual')
ra = {r['id']: bytes(a.b[r['dades']:r['dades'] + r['mida']]) for r in a.recursos}
rb = {r['id']: bytes(b.b[r['dades']:r['dades'] + r['mida']]) for r in b.recursos}
comprova([r['id'] for r in a.recursos] == [r['id'] for r in b.recursos], 'mateixos_recursos_i_ordre')
rec_dif = sorted(k for k in ra if ra[k] != rb.get(k))
comprova(rec_dif == [1026, 1036, 1072], 'nomes_canvien_1026_1036_1072', canvien=rec_dif)
comprova(rb[1026] == ra[1026] + b'\0' * 4 and rb[1072] == ra[1072] + b'\x01\x01', '1026_i_1072_nomes_afegeixen_2_valors')
comprova(ra[1039] == rb[1039], 'perfil_ICC_igual')
cru['recursos_canviats'] = rec_dif
ga = [(k['sig'], k['clau']) for k in a.blocs]
gb = [(k['sig'], k['clau']) for k in b.blocs]
comprova(ga == gb, 'mateixos_blocs_globals')
for ka, kb in zip(a.blocs, b.blocs):
    if ka['clau'] != b'Lr16':
        comprova(bytes(a.b[ka['pos']:ka['fi']]) == bytes(b.b[kb['pos']:kb['fi']]), 'bloc_global_igual', clau=ka['clau'].decode('latin-1'))
comprova(bytes(a.b[a.lmi_pos + 8:a.lr['pos'] + 8]) == bytes(b.b[b.lmi_pos + 8:b.lr['pos'] + 8]), 'inici_seccio_capes_igual')
comprova(b.lr_count == 51 and len(b.capes) == 51, 'recompte_51', recompte=b.lr_count)
canals_cru = []
for i in range(49):
    ca, cb = a.capes[i], b.capes[i]
    comprova(bytes(a.b[slice(*ca['reg'])]) == bytes(b.b[slice(*cb['reg'])]), 'registre_igual_byte_a_byte', capa=i)
    comprova(len(ca['dades']) == len(cb['dades']), 'mateix_nombre_de_canals', capa=i)
    for da, db in zip(ca['dades'], cb['dades']):
        ha = hashlib.sha256(a.b[da['pos']:da['pos'] + da['longitud']]).hexdigest()
        hb = hashlib.sha256(b.b[db['pos']:db['pos'] + db['longitud']]).hexdigest()
        comprova(ha == hb and da['id'] == db['id'], 'canal_igual_byte_a_byte', capa=i, canal=da['id'])
        canals_cru.append(dict(capa=i, canal=da['id'], bytes=da['longitud'], compressio=da['compressio'], sha256=hb))
nous_cru = []
for i, (nom, vis) in zip((49, 50), ((NOM_A, True), (NOM_B, False))):
    c = b.capes[i]
    comprova(c['caixa'] == (0, 0, W, H) and c['blend'] == b'norm' and c['opacitat'] == 255 and c['visible'] == vis
             and c['clipping'] == 0 and nom.encode('mac_roman')[:31].decode('mac_roman') == c['nom_pascal']
             and [d['compressio'] for d in c['dades']] == [3, 3, 3, 3] and [d['id'] for d in c['dades']] == [-1, 0, 1, 2],
             'registre_nou_cru', capa=i)
    nous_cru.append(dict(nom_pascal=c['nom_pascal'], caixa=c['caixa'], visible=c['visible'], flags=c['flags'],
                         canals=[(d['id'], d['longitud']) for d in c['dades']]))
comprova(bytes(a.b[a.lr['fi']:a.lmi_fi]) == bytes(b.b[b.lr['fi']:b.lmi_fi]), 'blocs_globals_finals_iguals')
comprova(b.id_compressio == 0 and b.mida - b.id_pos == 2 + 4 * H * W * 2, 'fusionada_RAW_4_canals')
n = H * W * 2
fus = np.stack([np.frombuffer(b.b, '>u2', H * W, b.id_pos + 2 + k * n).reshape(H, W) for k in range(3)], -1)
comprova(np.array_equal(fus, OUT), 'fusionada_crua_igual_a_la_capa_nova')
alfa = np.frombuffer(b.b, '>u2', H * W, b.id_pos + 2 + 3 * n)
comprova(int(alfa.min()) == 65535, 'alfa_fusionada_opaca')
alfa_v125 = np.frombuffer(a.b, '>u2', H * W, a.id_pos + 2 + 3 * n).reshape(H, W)
ys, xs = np.nonzero(alfa_v125 < 65535)
cru['alfa_V125_no_opaca'] = dict(n=int(len(ys)), minim=int(alfa_v125.min()),
                                 caixa=[int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1] if len(ys) else None)
del fus, alfa, alfa_v125
# total de bytes iguals: els 49 registres + tots els canals de Pere + tot el que no és Lr16 ni recursos ni fusionada
cru['bytes_canals_de_Pere'] = int(sum(c['bytes'] for c in canals_cru))
cru['canals_de_Pere'] = len(canals_cru)
cru['capes_noves'] = nous_cru
print(f'B (lector cru): {len(fallades)} fallades; {len(canals_cru)} canals de Pere iguals byte a byte '
      f'({cru["bytes_canals_de_Pere"] / 1e9:.3f} GB) ({time.time() - T0:.0f} s)', flush=True)

# --- el mateix control sobre la V127 i la V126 (documentació: què hi va canviar psd-tools en re-serialitzar)
altres = {}
for nom in ('V127.psb', 'V126.psb'):
    q = ARREL / '1-PHOTOSHOP' / nom
    if not q.exists():
        continue
    c = pc.PSB(q)
    regs = [i for i in range(49) if bytes(a.b[slice(*a.capes[i]['reg'])]) != bytes(c.b[slice(*c.capes[i]['reg'])])]
    canals = sum(1 for i in range(49) for da, dc in zip(a.capes[i]['dades'], c.capes[i]['dades'])
                 if da['longitud'] != dc['longitud'] or
                 hashlib.sha256(a.b[da['pos']:da['pos'] + da['longitud']]).digest() != hashlib.sha256(c.b[dc['pos']:dc['pos'] + dc['longitud']]).digest())
    altres[nom] = dict(registres_diferents=[(i, a.capes[i]['nom_pascal'],
                                             a.capes[i]['reg'][1] - a.capes[i]['reg'][0], c.capes[i]['reg'][1] - c.capes[i]['reg'][0]) for i in regs],
                       canals_diferents=canals)
    c.tanca()
print('V127/V126 contra la V125-FINAL:', altres, flush=True)

# ================================================================================================ A. psd-tools
from psd_tools import PSDImage  # noqa: E402
from psd_tools.constants import BlendMode, Tag  # noqa: E402

pa, pb = PSDImage.open(SRC), PSDImage.open(DST)
La, Lb = list(pa.descendants()), list(pb.descendants())
comprova(len(list(pb)) == len(list(pa)) + 2, 'psd_tools_capes_de_primer_nivell', a=len(list(pa)), b=len(list(pb)))
comprova(len(Lb) == len(La) + 2, 'psd_tools_totes_les_capes', a=len(La), b=len(Lb))
comprova((pb.width, pb.height, pb.depth, pb.channels) == (pa.width, pa.height, pa.depth, pa.channels), 'psd_tools_document')


def li(psd):
    return psd._record.layer_and_mask_information.tagged_blocks.get_data(Tag.LAYER_16)


Ia, Ib = li(pa), li(pb)
comprova(Ib.layer_count == 51 and len(Ib.layer_records) == 51 and len(Ib.channel_image_data) == 51, 'psd_tools_Lr16_51')
attrs = []
for i in range(49):
    x, y = La[i], Lb[i]
    ka = (x.name, x.kind, x.blend_mode, x.opacity, x.visible, x.bbox, x.clipping_layer, x.layer_id,
          (x.mask.bbox, x.mask.background_color, x.mask.disabled) if x.mask else None)
    kb = (y.name, y.kind, y.blend_mode, y.opacity, y.visible, y.bbox, y.clipping_layer, y.layer_id,
          (y.mask.bbox, y.mask.background_color, y.mask.disabled) if y.mask else None)
    comprova(ka == kb, 'psd_tools_atributs_iguals', capa=i, nom=x.name)
    attrs.append(dict(i=i, nom=x.name, tipus=x.kind, mode=str(x.blend_mode).split('.')[-1], opacitat=x.opacity, visible=x.visible,
                      caixa=list(x.bbox), mascara=bool(x.mask)))
    ra_, rb_ = Ia.layer_records[i], Ib.layer_records[i]
    ba, bb = io.BytesIO(), io.BytesIO()
    ra_.write(ba, version=2); rb_.write(bb, version=2)
    comprova(ba.getvalue() == bb.getvalue(), 'psd_tools_registre_igual', capa=i)
    for cda, cdb in zip(Ia.channel_image_data[i], Ib.channel_image_data[i]):
        comprova(cda.compression == cdb.compression and hashlib.sha256(cda.data).digest() == hashlib.sha256(cdb.data).digest(),
                 'psd_tools_canal_igual', capa=i)
print(f'A (psd-tools): 49 capes de Pere comprovades, {len(fallades)} fallades ({time.time() - T0:.0f} s)', flush=True)

nova_A, nova_B = Lb[49], Lb[50]
comprova(nova_A.name == NOM_A and nova_A.blend_mode == BlendMode.NORMAL and nova_A.opacity == 255 and nova_A.visible
         and nova_A.bbox == (0, 0, W, H), 'psd_tools_capa_A', nom=nova_A.name, vis=nova_A.visible)
comprova(nova_B.name == NOM_B and nova_B.blend_mode == BlendMode.NORMAL and nova_B.opacity == 255 and not nova_B.visible
         and nova_B.bbox == (0, 0, W, H), 'psd_tools_capa_B', nom=nova_B.name, vis=nova_B.visible)
pxA = nova_A.numpy()
comprova(pxA.shape == (H, W, 4), 'psd_tools_capa_A_forma', forma=pxA.shape)
difA = float(np.max(np.abs(pxA[..., :3] * 65535.0 - OUT)))
alfaA = float(pxA[..., 3].min())
del pxA
pxB = nova_B.numpy()
difB = float(np.max(np.abs(pxB[..., :3] * 65535.0 - E16[..., None])))
del pxB
comprova(difA < 0.01 and alfaA == 1.0, 'psd_tools_capa_A_igual_a_la_matriu', dif=difA, alfa_min=alfaA)
comprova(difB < 0.01, 'psd_tools_capa_B_igual_a_E', dif=difB)
comp = pb.numpy()
difC = float(np.max(np.abs(comp[..., :3] * 65535.0 - OUT)))
comprova(difC < 0.01 and float(comp[..., 3].min()) == 1.0, 'psd_tools_fusionada_igual_a_la_capa_A', dif=difC)
del comp
comp_a = pa.numpy()
canvi_fusionada = float(np.max(np.abs(comp_a[..., :3] * 65535.0 - OUT)))
del comp_a
th = pb.thumbnail()
print(f'A: capa A |dif| {difA:.2e}, capa B {difB:.2e}, fusionada {difC:.2e}; miniatura {th.size if th else None} '
      f'({time.time() - T0:.0f} s)', flush=True)

# ================================================================================================ C. sips (ImageIO)
sips = {}
r = subprocess.run(['sips', '-g', 'pixelWidth', '-g', 'pixelHeight', '-g', 'bitsPerSample', '-g', 'samplesPerPixel',
                    '-g', 'hasAlpha', '-g', 'profile', '-g', 'format', str(DST)], capture_output=True, text=True)
sips['propietats'] = r.stdout.strip().splitlines()[1:]
comprova(f'pixelWidth: {W}' in r.stdout and f'pixelHeight: {H}' in r.stdout, 'sips_obre_la_fusionada', sortida=r.stdout[-300:])
tif = TREB / 'V128b_fusionada_sips.tif'
comprova(not tif.exists(), 'tiff_de_sips_nou', tif=str(tif))
if not tif.exists():
    r2 = subprocess.run(['sips', '-s', 'format', 'tiff', str(DST), '--out', str(tif)], capture_output=True, text=True)
    sips['conversio'] = (r2.returncode, r2.stderr.strip()[-300:])
try:
    import tifffile
    t = tifffile.imread(tif)
    sips['tiff'] = dict(forma=list(t.shape), tipus=str(t.dtype))
    if t.dtype == np.uint16 and t.shape[:2] == (H, W):
        d = np.abs(t[..., :3].astype(np.int32) - OUT.astype(np.int32))
        sips['dif_max_DN16'] = int(d.max())
        sips['pixels_diferents'] = int(np.any(d > 0, axis=2).sum())
        comprova(int(d.max()) == 0, 'sips_fusionada_igual_a_la_matriu', dif=int(d.max()))
    elif t.dtype == np.uint8 and t.shape[:2] == (H, W):
        d = np.abs(t[..., :3].astype(np.float64) - OUT.astype(np.float64) / 257.0)
        sips['dif_max_DN8'] = float(d.max())
        comprova(float(d.max()) <= 0.5 + 1e-9, 'sips_fusionada_igual_a_la_matriu_8bits', dif=float(d.max()))
    else:
        comprova(False, 'sips_tiff_forma_inesperada', forma=list(t.shape), tipus=str(t.dtype))
    del t
except Exception as e:  # noqa: BLE001
    comprova(False, 'sips_tiff_no_llegible', error=repr(e))
print(f'C (sips): {sips} ({time.time() - T0:.0f} s)', flush=True)

# ================================================================================================ D. ael.photoshop.verify()
ael_rep = {}
try:
    sys.path.insert(0, str(ARREL.parent / '3-AEL/repo'))
    from ael import photoshop as aps  # noqa: E402
    exp = [dict(name=l.name, mode=l.blend_mode.name, opacity=l.opacity / 255.0, visible=l.visible) for l in pa]
    exp.append(dict(name=NOM_A, mode='NORMAL', opacity=1.0, visible=True, rgb16=OUT))
    exp.append(dict(name=NOM_B, mode='NORMAL', opacity=1.0, visible=False, rgb16=E16))
    del pa, pb
    rep = aps.verify(DST, exp)
    ael_rep = dict(ok=rep['ok'], capes=rep['layers'], bits=rep['depth'], mida=rep['size'], discrepancies=rep['mismatches'][:20],
                   modul=str(Path(aps.__file__).resolve()))
    comprova(rep['ok'], 'ael_photoshop_verify', discrepancies=rep['mismatches'][:5])
except Exception as e:  # noqa: BLE001
    ael_rep = dict(error=repr(e))
    comprova(False, 'ael_photoshop_verify_error', error=repr(e))
print(f'D (ael.photoshop.verify): {ael_rep} ({time.time() - T0:.0f} s)', flush=True)

info = dict(
    guio=str(Path(__file__).resolve().relative_to(ARREL)), data=time.strftime('%Y-%m-%dT%H:%M:%S'),
    fitxer=str(DST), sha256=sha_dst, mida=DST.stat().st_size, font=dict(fitxer='1-PHOTOSHOP/V125-FINAL.psb', sha256=sha_src),
    veredicte='PASSA' if not fallades else 'FALLA', fallades=fallades,
    lector_cru=cru, psd_tools=dict(capes=len(Lb), capes_de_Pere=attrs,
                                   capa_A=dict(nom=NOM_A, dif_max_DN16=difA, alfa_min=alfaA),
                                   capa_B=dict(nom=NOM_B, dif_max_DN16=difB),
                                   fusionada_dif_max_DN16_contra_capa_A=difC,
                                   fusionada_V125_contra_V128_dif_max_DN16=canvi_fusionada,
                                   miniatura=list(th.size) if th else None),
    sips=sips, ael_photoshop_verify=ael_rep, V127_i_V126_contra_V125=altres,
    segons=round(time.time() - T0, 1))
json.dump(info, open(RES / 'V3B_VERIFICACIO.json', 'w'), indent=1, ensure_ascii=False, default=str)
print('VEREDICTE', info['veredicte'], len(fallades), 'fallades', f'({time.time() - T0:.0f} s)')
sys.exit(1 if fallades else 0)
