"""b5 · Làmines de revisió de la V88 per a Pere (norma: sempre el llenç sencer, i els detalls a més, mai en lloc seu).
Fonts: vistes natives de Photoshop de la V87 sense marques (b1) i de la V88 (b3); capes de la Lluna (225 de Pere i Earthshine V88); apilat Vixen
des de zero (e1). Tot amb el perfil ICC del document convertit a sRGB per a la pantalla, llevat de les vistes estirades (diagnòstic)."""
from v88_comu import *
from psb69 import PSB
import tifffile, io, cv2
from PIL import Image, ImageCms, ImageDraw, ImageFont
from scipy.ndimage import gaussian_filter1d
claim(); VIS = SORT / 'vistes'; V87 = SORT / 'vistes_v87'
tf = tifffile.TiffFile(VIS / 'V88_lluna.tif'); icc = tf.pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
try: FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16); FONTB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 20)
except Exception: FONT = FONTB = ImageFont.load_default()
def im16(a): return ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(a.astype(np.float32) / 257, 0, 255))), TR)
def etiqueta(im, t, h=24):
    c = Image.new('RGB', (im.width, im.height + h), 'white'); c.paste(im, (0, h)); ImageDraw.Draw(c).text((4, 3), t, fill='black', font=FONT); return c
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = geo['cx'], geo['cy'], geo['R']
B = (4600, 3000); l87 = tifffile.imread(V87 / 'V87_lluna.tif')[..., :3]; l88 = tf.asarray()[..., :3]; amb = tifffile.imread(V87 / 'V87_amb_marques_lluna.tif')[..., :3]
# ---- 1: llenç sencer i Lluna
f87 = im16(tifffile.imread(V87 / 'V87_llenc_sencer.tif')[..., :3]); f88 = im16(tifffile.imread(VIS / 'V88_llenc_sencer.tif')[..., :3])
f87 = f87.resize((1400, round(f87.height * 1400 / f87.width)), Image.LANCZOS); f88 = f88.resize((1400, round(f88.height * 1400 / f88.width)), Image.LANCZOS)
S = Image.new('RGB', (2 * 1410, 50 + f87.height + 24 + 10 + 1024 + 24), 'white'); d = ImageDraw.Draw(S)
d.text((8, 12), 'V88: llenç sencer (a dalt) i Lluna a escala 2:3 (a baix). Esquerra: V87 (sense la capa de marques) · Dreta: V88', fill='black', font=FONTB)
S.paste(etiqueta(f87, 'V87 · compost natiu de Photoshop'), (0, 45)); S.paste(etiqueta(f88, 'V88 · compost natiu de Photoshop'), (1410, 45))
y = 45 + f87.height + 24 + 10
S.paste(etiqueta(im16(l87).resize((1024, 1024), Image.LANCZOS), 'V87 · Lluna'), (0, y)); S.paste(etiqueta(im16(l88).resize((1024, 1024), Image.LANCZOS), 'V88 · Lluna'), (1410, y))
S.save(SORT / 'LAMINA_V88_1_llenc_i_lluna.png'); log('làmina 1')
# ---- 2: les marques de la V87, a 3:1 amb el to natiu i a 6:1 amb els foscos aixecats
M = json.loads((SORT / 'MARQUES_V87.json').read_text()); llocs = []
for nom, tria in [('verd', [(0, 0.35), (1, 0.3)]), ('marro', [(1, 0.5), (2, 0.5)]), ('blau_clar', [(0, 0.5)]), ('lila', [(0, 0.5), (1, 0.4), (2, 0.5)])]:
    for k, q in tria:
        a0, a1 = M[nom][k]['azimut']; dmed = M[nom][k]['d_limbe_px'][1]; llocs.append((nom, a0 + q * (a1 - a0), dmed))
H, Wd = l88.shape[:2]; yy, xx = np.mgrid[B[1]:B[1] + H, B[0]:B[0] + Wd]; dd = np.hypot(xx - cx, yy - cy) - R
w3, w6 = 100, 50; S = Image.new('RGB', (3 * (w3 * 3 + 8) + 2 * (w6 * 6 + 8) + 10, 50 + len(llocs) * (w3 * 3 + 30)), 'white'); d = ImageDraw.Draw(S)
d.text((8, 4), 'Marques de la capa Artefactes V87: V87 amb marques · V87 · V88 (3:1, to natiu) | V87 · V88 (6:1, Lluna i corona estirades per separat)', fill='black', font=FONTB)
d.text((8, 28), 'A 6:1, la línia puntejada just al limbe la fa l\'estirament per separat (els píxels de la vora s\'estiren amb el rang de la corona); al to natiu no hi és.', fill='black', font=FONT)
for j, (nom, az, dmed) in enumerate(llocs):
    t = np.radians(az); y0 = 50 + j * (w3 * 3 + 30)
    px, py = cx + (R + dmed) * np.cos(t) - B[0], cy - (R + dmed) * np.sin(t) - B[1]; x0_, y0_ = int(px - w3 / 2), int(py - w3 / 2)
    for i, (arr, n) in enumerate([(amb, 'V87 amb marques'), (l87, 'V87'), (l88, 'V88')]):
        S.paste(etiqueta(im16(arr[y0_:y0_ + w3, x0_:x0_ + w3]).resize((w3 * 3, w3 * 3), Image.LANCZOS), f'{n} · {nom} · {az:.0f}°', 22), (i * (w3 * 3 + 8), y0))
    x6, y6 = int(px - w6 / 2), int(py - w6 / 2); sl = (slice(y6, y6 + w6), slice(x6, x6 + w6)); lluna = dd[sl] < -2; cor = dd[sl] > 3
    ref = l87[sl].astype(np.float32).mean(-1) / 65535
    for i, (arr, n) in enumerate([(l87, 'V87'), (l88, 'V88')]):
        a = arr[sl].astype(np.float32) / 65535
        lo_l, hi_l = (np.percentile(ref[lluna], [1, 99.5]) if lluna.sum() > 20 else (0, 0.2)); lo_c, hi_c = (np.percentile(ref[cor], [1, 99.5]) if cor.sum() > 20 else (0, 1))
        o = np.where(lluna[..., None], (a - lo_l) / max(hi_l - lo_l, 1e-6), (a - lo_c) / max(hi_c - lo_c, 1e-6))
        im = Image.fromarray(np.uint8(np.clip(o, 0, 1) * 255)).resize((w6 * 6, w6 * 6), Image.NEAREST)
        S.paste(etiqueta(im, f'{n} · 6:1 estirat', 22), (3 * (w3 * 3 + 8) + 10 + i * (w6 * 6 + 8), y0))
S.save(SORT / 'LAMINA_V88_2_marques.png'); log('làmina 2')
# ---- 3: l'earthshine
p = PSB(str(ARREL / '1-PHOTOSHOP/V88.psb')); L = p.layer(258); box = (L['left'], L['top'], L['right'], L['bottom'])
e88 = np.stack([p.channel_box(258, c, box) for c in range(3)], -1).astype(np.float32) / 65535; e225 = np.stack([p.channel_box(225, c, box) for c in range(3)], -1).astype(np.float32) / 65535
al = p.channel_box(258, -1, box).astype(np.float32) / 65535; m = al > 0.99; lo, hi = np.percentile(e225.mean(-1)[m], [0.5, 99.5])
def estira(e): return Image.fromarray(np.uint8(np.clip((e - lo) / (hi - lo), 0, 1) * al[..., None] * 255))
z = np.load(SORT / 'E1_earthshine_lineal.npz'); by0, by1, bx0, bx1 = [int(v) for v in z['box']]; Ez = z['E'][..., 1].astype(np.float64); ct = z['centre']
yb, xb = np.mgrid[by0:by1, bx0:bx1]; db = np.hypot(xb - ct[0], yb - ct[1]) - R; tb = (np.degrees(np.arctan2(-(yb - ct[1]), xb - ct[0])) + 360) % 360
okb = (z['W'][..., 1] > 0) & (db < -2); kb = np.clip((-db).astype(int), 0, 470); isec = (tb / 360 * 90).astype(int) % 90; P = np.full((90, 471), np.nan)
for s in range(90):
    q = okb & (isec == s); cnt = np.bincount(kb[q], minlength=471); sm = np.bincount(kb[q], weights=Ez[q], minlength=471); P[s] = np.where(cnt > 5, sm / np.maximum(cnt, 1), np.nan)
    f_ = np.isfinite(P[s]); P[s] = np.interp(np.arange(471), np.flatnonzero(f_), P[s][f_])
P = gaussian_filter1d(gaussian_filter1d(P, 3, axis=1, mode='nearest'), 1.5, axis=0, mode='wrap'); rel = np.where(okb, Ez / P[isec, kb] - 1, 0).astype(np.float32)
rel = rel - cv2.GaussianBlur(rel, (0, 0), 60) * okb; q = okb & (db < -25); lo2, hi2 = np.percentile(rel[q], [1, 99])
zim = Image.fromarray(np.uint8(np.clip((cv2.GaussianBlur(rel, (0, 0), 1.2) - lo2) / (hi2 - lo2), 0, 1) * (db < -2) * 255)).convert('RGB')
cs = 600
S = Image.new('RGB', (3 * (cs + 10), 50 + cs + 24 + 70), 'white'); d = ImageDraw.Draw(S)
d.text((8, 12), "Earthshine: la capa 225 de Pere (oculta a la V88) · Earthshine V88 (visible) · apilat Vixen des de zero (relleu, només per comparar)", fill='black', font=FONTB)
S.paste(etiqueta(estira(e225).resize((cs, round(cs * e225.shape[0] / e225.shape[1])), Image.LANCZOS), 'capa 225 (Pere) · estirada'), (0, 45))
S.paste(etiqueta(estira(e88).resize((cs, round(cs * e88.shape[0] / e88.shape[1])), Image.LANCZOS), 'Earthshine V88 · estirada'), (cs + 10, 45))
S.paste(etiqueta(zim.resize((cs, round(cs * zim.height / zim.width)), Image.LANCZOS), 'apilat Vixen des de zero · relleu sense vel'), (2 * (cs + 10), 45))
d.text((8, 50 + cs + 30), "Correlació amb LROC a 6 px: capa 225 0,66 · apilat Vixen des de zero 0,52 (a 12 px: 0,66 contra 0,35). A −30..−2 px del limbe, dues meitats\nindependents de l'apilat coincideixen (0,88–0,99) però no amb LROC (0,01–0,21): hi ha estructura de llum dispersa, no Lluna. L'interior de la V88 és la 225 tal qual.", fill='black', font=FONT)
S.save(SORT / 'LAMINA_V88_3_earthshine.png'); log('làmina 3')
# ---- 4: la cantonada
c87 = tifffile.imread(V87 / 'V87_llenc_sencer.tif')[..., :3]; c88 = tifffile.imread(VIS / 'V88_cantonada.tif')[..., :3]
sc = c87.shape[1] / 10551; cb = (7356, 4320, 9348, 6263); c87b = c87[int(cb[1] * sc):int(cb[3] * sc), int(cb[0] * sc):int(cb[2] * sc)]
S = Image.new('RGB', (2 * 710, 50 + 700 + 30), 'white'); d = ImageDraw.Draw(S); d.text((8, 10), 'Cantonada del logo · V87 (de la vista del llenç, reduïda) | V88 (regenerada)', fill='black', font=FONTB)
for i, arr in enumerate([c87b, c88]):
    im = im16(arr); im = im.resize((700, round(im.height * 700 / im.width)), Image.LANCZOS); S.paste(etiqueta(im, ['V87', 'V88'][i]), (i * 710, 45))
S.save(SORT / 'LAMINA_V88_4_cantonada.png'); log('làmina 4')
