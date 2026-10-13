"""c12 · Rètols (mouse-over), requadre ©, PSD amb capes i JPG per a l'enviament a l'APOD del mosaic final + LASCO C2.
Llegeix les capes de c11 (apod_lasco/capes). Rètols en anglès (per a l'APOD); geometria AA amb OpenCV (subpíxel), text amb PIL.
Sortides: 1-PHOTOSHOP/APOD_LASCO_v1.psd · publicacions/APOD/enviament_lasco_20261001/*.jpg · apod_lasco/C12_PSD.json"""
import sys, json, os, hashlib
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *
Image.MAX_IMAGE_PIXELS = None
OUT = RES / 'apod_lasco'; CAP = OUT / 'capes'
ENV = ARREL / 'publicacions/APOD/enviament_lasco_20261001'; ENV.mkdir(parents=True, exist_ok=True)
PSD = ARREL / '1-PHOTOSHOP/APOD_LASCO_v1.psd'
ICC = open(OUT / 'srgb.icc', 'rb').read()
S = 3960; C = S / 2 - 0.5; RPX = 300.0
gF = geo_final('efemeride'); N = np.array(gF.n, float); N /= np.hypot(*N)
HN = '/System/Library/Fonts/HelveticaNeue.ttc'
def font(sz, w='regular'): return ImageFont.truetype(HN, sz, index={'regular': 0, 'bold': 1, 'medium': 10}[w])
TARONJA = (255, 153, 71); TARONJA_C = (255, 196, 150); CREMA = (242, 222, 170); BLANC = (236, 236, 236)
CORALL = (255, 165, 130); CEL = (190, 206, 216)

capes = {k: Image.open(CAP / f'{k}.png') for k in ('2_lasco_c2', '2b_lasco_c2_M1', '3_eclipsi_disc', '3b_eclipsi_sencer')}

# ------------------------------------------------ dibuix AA: una màscara per color
class Llenç:
    def __init__(s): s.m = {}
    def _m(s, col): return s.m.setdefault(col, np.zeros((S, S), np.uint8))
    def linia(s, p, q, col, w=4):
        cv2.line(s._m(col), tuple(int(round(v * 16)) for v in p), tuple(int(round(v * 16)) for v in q), 255, w, cv2.LINE_AA, shift=4)
    def fletxa(s, p, q, col, w=4, llarg=34, ample=13):
        p, q = np.array(p, float), np.array(q, float); u = (q - p) / np.hypot(*(q - p)); v = np.array([-u[1], u[0]])
        base = q - u * llarg; s.linia(p, base, col, w)
        tri = np.array([q, base + v * ample, base - v * ample]) * 16
        cv2.fillPoly(s._m(col), [np.round(tri).astype(np.int32)], 255, cv2.LINE_AA, shift=4)
    def arc_discontinu(s, r_px, col, w=4, on=3.0, off=2.4):
        a = 0.0
        while a < 360:
            cv2.ellipse(s._m(col), (int(round(C * 16)), int(round(C * 16))), (int(round(r_px * 16)), int(round(r_px * 16))), 0, a, a + on, 255, w, cv2.LINE_AA, shift=4)
            a += on + off
    def rgba(s):
        out = np.zeros((S, S, 4), np.float32)
        for col, m in s.m.items():
            al = m.astype(np.float32)[..., None] / 255
            out[..., :3] = np.array(col, np.float32) / 255 * al + out[..., :3] * (1 - al)
            out[..., 3:] = al + out[..., 3:] * (1 - al)
        return Image.fromarray((out * 255 + 0.5).astype(np.uint8), 'RGBA')

def text(d, xy, s, f, col, ancora='la', halo=6):
    d.text(xy, s, font=f, fill=col + (255,), anchor=ancora, stroke_width=halo, stroke_fill=(0, 0, 0, 215))
    return d.textbbox(xy, s, font=f, anchor=ancora, stroke_width=halo)

def pol(r_rsol, ang_pant):   # angle de pantalla: 0 = dreta, antihorari
    t = np.radians(ang_pant); return (C + r_rsol * RPX * np.cos(t), C - r_rsol * RPX * np.sin(t))

# ------------------------------------------------ capa de rètols (anotada)
lz = Llenç(); rot = Image.new('RGBA', (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(rot)
fT, fL, fl = font(72, 'bold'), font(50), font(46)
M = 100
# des de l'espai (dalt a l'esquerra) + mostra de la línia discontínua
text(d, (M, M), 'FROM SPACE', fT, TARONJA)
text(d, (M, M + 98), 'SOHO / LASCO C2 coronagraph · 18:24:31 UT', fL, TARONJA_C)
y3 = M + 98 + 74
for i in range(4): lz.linia((M + 4 + i * 28, y3 + 26), (M + 4 + i * 28 + 16, y3 + 26), TARONJA, 5)
text(d, (M + 126, y3), 'edge of its occulting disk (2.2 solar radii)', fl, TARONJA_C)
lz.arc_discontinu(2.2 * RPX, TARONJA, 5)
# des de terra (baix a l'esquerra)
yb = S - M - 72 - 2 * 72
text(d, (M, yb), 'FROM THE GROUND', fT, CREMA)
text(d, (M, yb + 98), 'Total solar eclipse from León, Spain · 18:28–18:30 UT', fL, CREMA)
text(d, (M, yb + 98 + 72), 'The Moon hides the Sun almost exactly', fl, CREMA)
# el cel de la Terra: just sota el disc (6 h), on la corona és més feble (angle de pantalla 240–285°, lluminància ≈ 30/255);
# el rètol va a la zona fosca del C2 entre els dos serpentins de baix
cx_, ys = C + 20, C + 3.92 * RPX
text(d, (cx_, ys), "Earth's sky, still glowing", fl, CEL, ancora='mt'); b2 = text(d, (cx_, ys + 58), 'during totality', fl, CEL, ancora='mt')
lz.fletxa((cx_, ys - 22), pol(3.30, 268), CEL, 4, llarg=30, ample=11)
# protuberància (centre de la taca rosada: 1666, 1990; vora esquerra del limbe)
pp = (1648.0, 1998.0); tp = pol(2.55, 214)
bp = text(d, (tp[0], tp[1]), 'prominence', fl, CORALL, ancora='rm')
lz.fletxa((bp[2] + 10, tp[1] - 4), (pp[0] - 16, pp[1] + 10), CORALL, 4, llarg=30, ample=11)
# nord solar i escala (dalt a la dreta)
x0, y0 = S - 330, 520
lz.fletxa((x0, y0), (x0 + 230 * N[0], y0 + 230 * N[1]), BLANC, 5)
text(d, (x0 + 285 * N[0], y0 + 285 * N[1]), 'N', fL, BLANC, ancora='mm')
ye = 660; lz.linia((S - M - RPX, ye), (S - M, ye), BLANC, 5)
for xx_ in (S - M - RPX, S - M): lz.linia((xx_, ye - 14), (xx_, ye + 14), BLANC, 5)
text(d, (S - M - RPX / 2, ye + 30), '1 solar radius', fl, BLANC, ancora='mt')
rotols = Image.alpha_composite(lz.rgba(), rot)

# ------------------------------------------------ requadre © (baix a la dreta, estil de l'enviament del 30-09)
cr = Image.new('RGBA', (S, S), (0, 0, 0, 0)); dc = ImageDraw.Draw(cr)
f1, f2 = font(46, 'bold'), font(34)
t1, t2 = '© 2026 Pere Guerra Serra', 'LASCO C2 data: SOHO (ESA & NASA)'
w = max(dc.textlength(t1, font=f1), dc.textlength(t2, font=f2)); pad = 30
bx1, by1 = S - 70, S - 70; bx0, by0 = bx1 - w - 2 * pad, by1 - (46 + 14 + 34) - 2 * pad - 6
dc.rectangle([bx0, by0, bx1, by1], fill=(14, 16, 18, 235), outline=(120, 130, 130, 255), width=4)
dc.text((bx0 + pad, by0 + pad - 4), t1, font=f1, fill=(240, 236, 224, 255))
dc.text((bx0 + pad, by0 + pad + 56), t2, font=f2, fill=(200, 200, 196, 255))

# ------------------------------------------------ compostos
negre = Image.new('RGBA', (S, S), (0, 0, 0, 255))
net = Image.alpha_composite(Image.alpha_composite(negre, capes['2_lasco_c2']), capes['3_eclipsi_disc'])
net_c = Image.alpha_composite(net, cr)
anot_c = Image.alpha_composite(Image.alpha_composite(net, rotols), cr)

if os.environ.get('PREVIA'):     # només previsualitzacions, sense PSD ni JPG d'enviament
    anot_c.convert('RGB').resize((1400, 1400), Image.LANCZOS).save(OUT / 'previ_anotada_1400.jpg', quality=90)
    anot_c.convert('RGB').save(OUT / 'previ_anotada_3960.jpg', quality=90); sys.exit(0)

# ------------------------------------------------ PSD (8 bits, RGBA: capes amb transparència real)
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import Resource
from psd_tools.psd.image_resources import ImageResource
ordre = [('Fons negre', negre, True),
         ('LASCO C2 18:24 UT · SOHO, sense falca', capes['2_lasco_c2'], True),
         ('LASCO C2 com al M1 (falca i taques)', capes['2b_lasco_c2_M1'], False),
         ('Eclipsi publicat fins a 3,5 radis solars', capes['3_eclipsi_disc'], True),
         ('Eclipsi publicat sencer, per remascarar', capes['3b_eclipsi_sencer'], False),
         ("Rètols de l'anotada (mouse-over)", rotols, False),
         ('© Pere Guerra Serra i crèdit SOHO', cr, True)]
assert not PSD.exists(), f'{PSD} ja existeix: no se sobreescriu'
psd = PSDImage.frompil(net_c)
for nom, im, vis in ordre:
    bb = im.getbbox() if nom != 'Fons negre' else (0, 0, S, S)
    ly = PixelLayer.frompil(im.crop(bb), psd, nom, bb[1], bb[0]); psd.append(ly); ly.visible = vis
psd._record.image_resources[Resource.ICC_PROFILE] = ImageResource(signature=b'8BIM', key=Resource.ICC_PROFILE, name='', data=ICC)
psd.save(str(PSD))
p2 = PSDImage.open(str(PSD))
dif = int(np.abs(np.asarray(p2.composite(force=True).convert('RGB')).astype(int) - np.asarray(net_c.convert('RGB')).astype(int)).max())
noms = [(l.name, l.visible) for l in p2]

# ------------------------------------------------ JPG per a l'enviament (sRGB amb perfil)
def jpg(im, nom, mida, q=92):
    im = im.convert('RGB'); im = im if mida == S else im.resize((mida, mida), Image.LANCZOS)
    im.save(ENV / nom, quality=q, icc_profile=ICC, subsampling=0); return nom
fitxers = [jpg(net_c, 'Guerra_eclipse_LASCO_2026.jpg', 2400), jpg(anot_c, 'Guerra_eclipse_LASCO_2026_annotated.jpg', 2400),
           jpg(net_c, 'Guerra_eclipse_LASCO_2026_960.jpg', 960, 90), jpg(anot_c, 'Guerra_eclipse_LASCO_2026_960_annotated.jpg', 960, 90),
           jpg(net_c, 'Guerra_eclipse_LASCO_2026_full_3960.jpg', S, 94), jpg(anot_c, 'Guerra_eclipse_LASCO_2026_full_3960_annotated.jpg', S, 94)]
anot_c.convert('RGB').resize((1400, 1400), Image.LANCZOS).save(OUT / 'previ_anotada_1400.jpg', quality=90)
net_c.convert('RGB').resize((1400, 1400), Image.LANCZOS).save(OUT / 'previ_neta_1400.jpg', quality=90)
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
rebut = dict(script=Path(__file__).name, psd=str(PSD.relative_to(ARREL)), psd_sha256=sha(PSD), psd_capes=noms,
             psd_compost_dif_max_DN=dif, jpg={f: dict(sha256=sha(ENV / f), bytes=os.path.getsize(ENV / f)) for f in fitxers})
json.dump(rebut, open(OUT / 'C12_PSD.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(rebut, indent=1, ensure_ascii=False))
