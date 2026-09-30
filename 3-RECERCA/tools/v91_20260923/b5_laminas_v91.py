"""b5 · Làmines de la V91 amb el compost de Photoshop (capes d'ajust incloses): la V90 de Pere (imatge fusionada desada dins del PSB de les
22:06, amb la seva màscara nova de la 56) contra la V91 (imatge fusionada del desament natiu), i la V88 de Pere (18:50) com a referència sense
suavitzat radial. 1) les marques roses de la capa «Artefactes V90» (la «lent») a 4:1; 2) les marques de la V88 (les línies del limbe esquerre)
a 4:1, per comprovar que no tornen; 3) la protuberància esquerra (marques liles): la foto 76 sola, V90 i V91; 4) la Lluna a 2:3.
També mesura on difereixen els dos composts (V91 − V90). Sortida: LAMINA_V91_1..4 i B5_LAMINES.json."""
from v91_comu import *
from psb69 import PSB
from v86_operadors import smoothstep
import tifffile, io, cv2
from PIL import Image, ImageCms, ImageDraw, ImageFont
claim(); GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
B = (4600, 3000, 6150, 4550); VM88 = ARREL / '4-RESULTATS/v88_marques_pere_20260923'; VM90 = ARREL / '4-RESULTATS/v90_marques_pere_20260923'
assert sha(ARREL / '1-PHOTOSHOP/V90.psb') == '5a9233ac85554321ac75c0d43d1c43ab69e86b1861c7f488aef4369fba9ac70d'
C90 = PSB(str(ARREL / '1-PHOTOSHOP/V90.psb')).composite()[..., :3]; C91 = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb')).composite()[..., :3]
# on difereixen els composts
D = np.abs(C91.astype(np.int32) - C90.astype(np.int32)).max(-1); rep = {}
for llindar in (1, 64, 256):
    ys, xs = np.nonzero(D > llindar); dd = np.hypot(xs - cx, ys - cy) - R; az = (np.degrees(np.arctan2(-(ys - cy), xs - cx)) + 360) % 360
    prot = (xs >= 4740) & (xs < 5020) & (ys >= 3470) & (ys < 4040); fora = ~prot
    rep[f'dif_mes_de_{llindar}_DN16'] = dict(px=int(xs.size), px_caixa_protuberancia=int(prot.sum()), fora_protuberancia=dict(
        px=int(fora.sum()), d_max=round(float(dd[fora].max()), 1) if fora.any() else None, d_p99=round(float(np.percentile(dd[fora], 99)), 1) if fora.any() else None,
        px_a_99_232_graus=int((fora & (az >= 98.5) & (az <= 232.5)).sum())))
log(json.dumps(rep))
V90 = C90[B[1]:B[3], B[0]:B[2]].copy(); V91 = C91[B[1]:B[3], B[0]:B[2]].copy(); del C90, C91, D
tf = tifffile.TiffFile(VM88 / 'compost_lluna.tif'); icc = tf.pages[0].tags['InterColorProfile'].value; V88 = tf.asarray()[..., :3]; assert V88.shape == V90.shape
icc91 = tifffile.TiffFile(SORT / 'vistes/V91_lluna.tif').pages[0].tags['InterColorProfile'].value; assert icc91 == icc, 'perfils diferents'
tifffile.imwrite(SORT / 'compost_V90_2206_lluna.tif', V90, photometric='rgb', iccprofile=icc); tifffile.imwrite(SORT / 'compost_V91_lluna.tif', V91, photometric='rgb', iccprofile=icc)
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
def im(a): return ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(a.astype(np.float32) / 257, 0, 255))), TR)
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 19)
def hS(az):
    a_ = np.array(float(az)); return None, 4.0 * float(smoothstep(a_, 99.0, 104.0)) * (1 - float(smoothstep(a_, 228.0, 232.0)))
def amb_contorn(arr, mask, org):
    out = im(arr).convert('RGB'); a = np.asarray(out).copy(); m = np.zeros(arr.shape[:2], np.uint8); oy, ox = org[1] - B[1], org[0] - B[0]
    m[oy:oy + mask.shape[0], ox:ox + mask.shape[1]] = mask; vora = cv2.dilate(m, np.ones((3, 3), np.uint8)) & ~m; a[vora > 0] = (255, 0, 200); return a
def lamina(nom, titol, files, cols, w=100, zf=4):
    S = Image.new('RGB', (len(cols) * (w * zf + 8), 44 + len(files) * (w * zf + 26)), 'white'); d = ImageDraw.Draw(S); d.text((6, 8), titol, fill='black', font=FB)
    for j, (az, dm, extra) in enumerate(files):
        t = np.radians(az); px, py = cx + (R + dm) * np.cos(t) - B[0], cy - (R + dm) * np.sin(t) - B[1]; x0, y0 = int(px - w / 2), int(py - w / 2); Y = 44 + j * (w * zf + 26)
        for i, (arr, et) in enumerate(cols):
            tile = arr[y0:y0 + w, x0:x0 + w]; tile = Image.fromarray(tile) if tile.dtype == np.uint8 else im(tile)
            S.paste(tile.resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y + 22)); d.text((i * (w * zf + 8) + 3, Y + 3), f'{et} · {az:.0f}°' + (f' · {extra}' if i == 0 and extra else ''), fill='black', font=F)
    S.save(SORT / nom); return nom
# 1) la «lent»: marques roses de la V90
z = np.load(VM90 / 'marques_v90_classes.npz'); mk = z['to_280_290']; mo = z['origin']
yy, xx = np.nonzero(mk); yy = yy + mo[1]; xx = xx + mo[0]; dmk = np.hypot(xx - cx, yy - cy) - R; amk = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
files1 = []
for az in (5, 26, 55, 80, 236, 248, 268, 292):
    s = np.abs((amk - az + 180) % 360 - 180) < 3
    if s.any(): h, Sv = hS(az); files1.append((az, float(np.median(dmk[s])), f'σ V90 4 px, V91 {Sv:.1f} px'))
V90c = amb_contorn(V90, mk.astype(np.uint8), mo)
rep['lamina1_files'] = [(a, round(d_, 1), e) for a, d_, e in files1]
lamina('LAMINA_V91_1_lent.png', "La «lent» (marques roses de la V90): V90 amb la teva marca, V90, V91 i V88 (sense suavitzat), compost de Photoshop, 4:1",
       files1, [(V90c, 'V90 amb la marca'), (V90, 'V90'), (V91, 'V91'), (V88, 'V88')])
# 2) les línies de la V88: no han de tornar
M88 = json.loads((VM88 / 'MARQUES_V88.json').read_text()); files2 = []
for g in M88['grups_de_to']:
    for cc in g['components']:
        az = cc['azimut'][1]; h, Sv = hS(az); files2.append((az, cc['d_limbe_px'][1], f'σ V91 {Sv:.1f} px'))
files2.sort(); z8 = np.load(VM88 / 'marques_v88_crues.npz'); V88c = amb_contorn(V88, (z8['alpha'] > 32768).astype(np.uint8), z8['origin'])
rep['lamina2_files'] = [(a, round(d_, 1), e) for a, d_, e in files2]
lamina('LAMINA_V91_2_linies.png', "Les línies del limbe esquerre (marques de la V88): V88 amb la marca, V88, V90 i V91, compost de Photoshop, 4:1",
       files2, [(V88c, 'V88 amb la marca'), (V88, 'V88'), (V90, 'V90'), (V91, 'V91')])
# 3) la protuberància esquerra (marques liles): foto 76 sola, V90, V91 a 2:1, i les guspires a 4:1
P = PSB(str(ARREL / '1-PHOTOSHOP/V91.psb')); bx = (4740, 3470, 5020, 4040); F76 = np.stack([P.channel_box(76, c, bx) for c in range(3)], -1)
sub = lambda A: A[bx[1] - B[1]:bx[3] - B[1], bx[0] - B[0]:bx[2] - B[0]]; cols3 = [(F76, 'foto 76 sola'), (sub(V90), 'V90'), (sub(V91), 'V91')]
mkp = np.zeros((B[3] - B[1], B[2] - B[0]), np.uint8); mkp[mo[1] - B[1]:mo[1] - B[1] + mk.shape[0], mo[0] - B[0]:mo[0] - B[0] + mk.shape[1]] = mk; mkp = sub(mkp)
zf = 2; wv, hv = bx[2] - bx[0], bx[3] - bx[1]; S3 = Image.new('RGB', (4 * (wv * zf + 8), hv * zf + 40), 'white'); d3 = ImageDraw.Draw(S3)
V90cp = np.asarray(im(sub(V90))).copy(); vora = cv2.dilate(mkp, np.ones((3, 3), np.uint8)) & ~mkp; V90cp[vora > 0] = (255, 0, 200)
for i, (arr, et) in enumerate([(V90cp, 'V90 amb la marca')] + cols3):
    t_ = Image.fromarray(arr) if arr.dtype == np.uint8 else im(arr); S3.paste(t_.resize((wv * zf, hv * zf), Image.LANCZOS), (i * (wv * zf + 8), 34)); d3.text((i * (wv * zf + 8) + 4, 8), f'{et} · 2:1', fill='black', font=FB)
S3.save(SORT / 'LAMINA_V91_3_protuberancia.png')
cmp = [c for g in json.loads((VM90 / 'MARQUES_V90.json').read_text())['grups_de_to'] for c in g['components'] if 165 <= c['azimut'][1] <= 185][0]['caixa']   # la marca lila
gx, gy = (cmp[0] + cmp[2]) / 2 - bx[0], (cmp[1] + cmp[3]) / 2 - bx[1]; w4 = 130
x0 = int(np.clip(gx - w4 / 2, 0, wv - w4)); y0 = int(np.clip(gy - w4 / 2, 0, hv - w4)); rep['guspires_4a1_caixa'] = [bx[0] + x0, bx[1] + y0, bx[0] + x0 + w4, bx[1] + y0 + w4]
S4 = Image.new('RGB', (4 * (w4 * 4 + 8), w4 * 4 + 40), 'white'); d4 = ImageDraw.Draw(S4)
for i, (arr, et) in enumerate([(V90cp, 'V90 amb la marca')] + cols3):
    t_ = arr[y0:y0 + w4, x0:x0 + w4]; t_ = Image.fromarray(t_) if t_.dtype == np.uint8 else im(t_)
    S4.paste(t_.resize((w4 * 4, w4 * 4), Image.LANCZOS), (i * (w4 * 4 + 8), 34)); d4.text((i * (w4 * 4 + 8) + 4, 8), f'{et} · marca lila · 4:1', fill='black', font=FB)
S4.save(SORT / 'LAMINA_V91_3b_guspires_4a1.png')
# 4) la Lluna a 2:3
k = 1024; S5 = Image.new('RGB', (2 * (k + 8), k + 36), 'white'); d5 = ImageDraw.Draw(S5)
for i, (arr, et) in enumerate([(V90, 'V90 de Pere (22:06)'), (V91, 'V91')]):
    S5.paste(im(arr).resize((k, k), Image.LANCZOS), (i * (k + 8), 34)); d5.text((i * (k + 8) + 4, 8), 'Lluna 2:3 · ' + et, fill='black', font=FB)
S5.save(SORT / 'LAMINA_V91_4_lluna.png'); desa_json('B5_LAMINES.json', rep); log('làmines fetes')
