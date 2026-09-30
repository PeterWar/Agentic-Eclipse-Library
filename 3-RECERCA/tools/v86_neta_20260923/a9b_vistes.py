"""a9b · Làmines de revisió per a Pere (norma: sempre el llenç sencer, i els detalls a més, mai en lloc seu).
Fonts: compost natiu de Photoshop de la V86 (vistes d'a8), compostos desats de la V84 (referència de Pere, amb PixInsight) i de la V85;
ràsters de filtre de les tres versions al mateix lloc. Tot amb el perfil ICC del document convertit a sRGB per a la pantalla."""
from v86_comu import *
from psb69 import PSB
import tifffile, io, struct
from PIL import Image, ImageCms, ImageDraw, ImageFont
claim(); VIS = SORT / 'vistes'
with open(ARREL / '1-PHOTOSHOP/V86.psb', 'rb') as f:
    from psd_tools.psd.image_resources import ImageResources
    from psd_tools.constants import Resource
    f.seek(26); n = struct.unpack('>I', f.read(4))[0]; f.seek(n, 1); icc = ImageResources.read(f).get_data(Resource.ICC_PROFILE)
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
try: FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16); FONTB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 20)
except Exception: FONT = FONTB = ImageFont.load_default()
def im16(a): return ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(a.astype(np.float32) / 257, 0, 255))), TR)
def etiqueta(im, t, h=24):
    o = Image.new('RGB', (im.width, im.height + h), 'white'); o.paste(im, (0, h)); ImageDraw.Draw(o).text((4, 3), t, fill='black', font=FONT); return o
def full_psb(path, ample=1400):
    c = PSB(str(path)).composite()[..., :3]; hh = round(H * ample / W)
    return im16(np.stack([np.asarray(Image.fromarray(c[..., k]).resize((ample, hh), Image.BOX)) for k in range(3)], -1)), c
def full_tif(path, ample=1400):
    a = tifffile.imread(path)[..., :3]; im = im16(a); return im.resize((ample, round(im.height * ample / im.width)), Image.LANCZOS)
geo = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy = geo['cx'], geo['cy']
f84, c84 = full_psb(ARREL / '1-PHOTOSHOP/V84.psb'); f85, c85 = full_psb(ARREL / '1-PHOTOSHOP/V85.psb'); f86 = full_tif(VIS / 'V86_llenc_sencer.tif')
lluna86 = tifffile.imread(VIS / 'V86_lluna.tif')[..., :3]      # caixa 4600,3000,6150,4550
def crop(c, box): x0, y0, x1, y1 = box; return c[y0:y1, x0:x1]
B = (4600, 3000, 6150, 4550)
# ---- Làmina 1: llenç sencer i Lluna (V84 referència · V85 · V86)
S = Image.new('RGB', (1400 * 3 + 20, 60 + 1022 + 10 + 1024 + 30), 'white'); d = ImageDraw.Draw(S)
d.text((8, 10), 'V86 neta: llenç sencer (a dalt) i Lluna a escala 2:3 (a baix). Esquerra: V84 (la teva referència, amb PixInsight) · Centre: V85 · Dreta: V86 (abans de PixInsight)', fill='black', font=FONTB)
for k, (im, nom) in enumerate([(f84, 'V84 · compost desat (amb PixInsight)'), (f85, 'V85 · compost desat'), (f86, 'V86 · compost natiu de Photoshop')]):
    S.paste(etiqueta(im, nom), (k * 1410, 50))
for k, (arr, nom) in enumerate([(crop(c84, B), 'V84'), (crop(c85, B), 'V85'), (lluna86, 'V86')]):
    S.paste(etiqueta(im16(arr).resize((1024, 1024), Image.LANCZOS), nom + ' · Lluna'), (k * 1410, 50 + 1022 + 10))
S.save(SORT / 'LAMINA_V86_1_llenc_i_lluna.png'); log('làmina 1')
# ---- Làmina 2: el limbe a 1:1 (esquerra, amb la protuberància; dalt; dreta; baix) en les tres versions
S = Image.new('RGB', (3 * 410 + 20, 60 + 4 * 434), 'white'); d = ImageDraw.Draw(S); d.text((8, 10), 'El limbe a 1:1 · V84 | V85 | V86 (vistes de 400 px centrades a 30 px fora del limbe)', fill='black', font=FONTB)
R = geo['R']
for j, az in enumerate([180, 90, 0, 270]):
    t = np.radians(az); px = int(cx + (R + 30) * np.cos(t)); py = int(cy - (R + 30) * np.sin(t)); bx = (px - 200, py - 200, px + 200, py + 200)
    for k, arr in enumerate([crop(c84, bx), crop(c85, bx), lluna86[bx[1] - B[1]:bx[3] - B[1], bx[0] - B[0]:bx[2] - B[0]]]):
        S.paste(etiqueta(im16(arr), f"{['V84', 'V85', 'V86'][k]} · azimut {az}°"), (k * 410, 50 + j * 434))
S.save(SORT / 'LAMINA_V86_2_limbe_1a1.png'); log('làmina 2')
# ---- Làmina 3: ràsters dels filtres principals al limbe esquerre (V84 · V85 · V86)
bx = (4880, 3340, 5200, 3990); S = Image.new('RGB', (3 * 330 + 20, 60 + 3 * 684), 'white'); d = ImageDraw.Draw(S)
d.text((8, 10), 'Filtres al limbe esquerre (la franja escombrada és a la dreta de cada vista) · V84 | V85 | V86', fill='black', font=FONTB)
paths = [ARREL / '1-PHOTOSHOP/V84.psb', ARREL / '1-PHOTOSHOP/V85.psb', ARREL / '1-PHOTOSHOP/V86.psb']; psbs = [PSB(str(q)) for q in paths]
for j, (lid, nom) in enumerate([(56, 'WOW bilateral'), (41, 'NRGF'), (51, 'ACHF micro 1-16')]):
    for k, ps in enumerate(psbs):
        a = ps.channel_box(lid, 1, bx); im = Image.fromarray(np.uint8(a / 257)).convert('RGB')
        S.paste(etiqueta(im, f"{['V84', 'V85', 'V86'][k]} · {nom}"), (k * 330, 50 + j * 684))
S.save(SORT / 'LAMINA_V86_3_filtres_al_limbe.png'); log('làmina 3')
# ---- Làmina 4: cantonada (V84 · V85 · V86) i enquadrament final de la V86
cb = (7356, 4320, 9348, 6263); c86 = tifffile.imread(VIS / 'V86_cantonada.tif')[..., :3]
S = Image.new('RGB', (3 * 700 + 20, 60 + 700 + 30), 'white'); d = ImageDraw.Draw(S); d.text((8, 10), 'Cantonada del logo · V84 (cuita dins PixInsight) | V85 (negra) | V86 (capa que es regenera)', fill='black', font=FONTB)
for k, arr in enumerate([crop(c84, cb), crop(c85, cb), c86]):
    im = im16(arr); im = im.resize((700, round(im.height * 700 / im.width)), Image.LANCZOS); S.paste(etiqueta(im, ['V84', 'V85', 'V86'][k]), (k * 710, 50))
S.save(SORT / 'LAMINA_V86_4_cantonada.png'); log('làmina 4')
# mesura de la costura de la cantonada a la V86 (nivell i gra a banda i banda de la hipotenusa)
ca = json.loads((SORT / 'A7_CANTONADA.json').read_text()); P1, P2 = ca['hipotenusa']['P1'], ca['hipotenusa']['P2']; m_ = (P2[1] - P1[1]) / (P2[0] - P1[0]); b_ = P1[1] - m_ * P1[0]
Hs, Ws = c86.shape[:2]; YY, XX = np.mgrid[0:Hs, 0:Ws]; dn = (m_ * XX - YY + b_) / np.sqrt(m_ * m_ + 1); L = c86.astype(np.float32).mean(-1) / 65535
from scipy.ndimage import gaussian_filter
hp = L - gaussian_filter(L, 8)
dins = (dn < -30) & (dn > -120) & (XX < Ws - 5) & (YY < Hs - 5); fora = (dn > 30) & (dn < 120)    # dins del triangle dn < 0
cost = dict(nivell_dins=float(L[dins].mean()), nivell_fora=float(L[fora].mean()), gra_dins=float(hp[dins].std()), gra_fora=float(hp[fora].std()))
cost['PASS'] = bool(abs(cost['nivell_dins'] - cost['nivell_fora']) < 0.005 and 0.8 < cost['gra_dins'] / cost['gra_fora'] < 1.25)
desa_json('A9B_COSTURA_CANTONADA.json', cost); log('costura ' + json.dumps(cost))
