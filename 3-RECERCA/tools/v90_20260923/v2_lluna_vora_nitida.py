"""v2 · (A) L'alfa nova de la Lluna per a la V90: a l'esquerra, vora nítida just a la línia vermella de la cromosfera de les fotos de Pere.
Per azimut (0,25°): e(θ) = d_línia − 1 px on V1 troba la línia (contrast ≥ 0,06; al sector 115–235°, fora de la protuberància 168–192° on el
nucli blanc falseja la detecció); entre els trams detectats, interpolació lineal; suavitzat gaussià 1°; e ≥ −1 px. Alfa de la vora: 1 − smoothstep
(d, e − 0,75, e + 0,75) (transició d'1,5 px). Pes per azimut w: 1 a 120–230°, fosa lineal fins a 0 a 115° i 235°. Alfa nova = w·mín(alfa de Pere,
alfa de la vora) + (1 − w)·alfa de Pere: mai no és més gran que la de Pere (se'n respecten els retalls) i fora del sector és idèntica.
Sortida: V2_lluna.npz (alfa nova a la caixa de la 258, uint16), V2_LLUNA.json i LAMINA_V2_lluna.png (polars: alfa de Pere, alfa nova, línia)."""
from v90_comu import *
from psb69 import PSB
from v86_operadors import smoothstep
from scipy.ndimage import gaussian_filter1d
import cv2
from PIL import Image, ImageDraw, ImageFont
claim(); GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
V1 = json.loads((SORT / 'V1_CROMOSFERA.json').read_text()); NBZ = 1440; TS = (np.arange(NBZ) + 0.5) * 360 / NBZ
dl = np.array([np.nan if v is None else v for v in V1['d_linia']], float)
ok = np.isfinite(dl) & (TS >= 115) & (TS <= 235) & ~((TS >= 168) & (TS <= 192))
e = np.full(NBZ, np.nan); e[ok] = dl[ok] - 1.0
ks = np.flatnonzero(ok); e_int = np.interp(np.arange(NBZ), ks, e[ks], period=NBZ)
e_s = np.maximum(gaussian_filter1d(e_int, 4, mode='wrap'), -1.0)
w = np.clip(np.minimum((TS - 115) / 5, (235 - TS) / 5), 0, 1)
p = PSB(str(ARREL / '1-PHOTOSHOP/V88.psb')); aP, (ox, oy) = p.channel(258, -1); aP = aP.astype(np.float32) / 65535
yy, xx = np.mgrid[oy:oy + aP.shape[0], ox:ox + aP.shape[1]]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
ib = (th / 360 * NBZ).astype(int) % NBZ; ee = e_s[ib]; ww = w[ib]
a_vora = 1 - smoothstep(d, ee - 0.75, ee + 0.75)
a_new = (ww * np.minimum(aP, a_vora) + (1 - ww) * aP).astype(np.float32)
np.savez_compressed(SORT / 'V2_lluna.npz', alfa=np.round(a_new * 65535).astype(np.uint16), org=np.array([ox, oy]), e=e_s, w=w)
rep = dict(caixa_258=[int(ox), int(oy), int(ox + aP.shape[1]), int(oy + aP.shape[0])], px_que_baixen=int((a_new < aP - 1 / 255).sum()), px_opacs_que_deixen_de_ser_ho=int(((aP >= 0.999) & (a_new < 0.999)).sum()),
           e_per_sector={f'{a}-{a + 10}': round(float(np.mean(e_s[a * 4:(a + 10) * 4])), 2) for a in range(110, 240, 10)}, fraccio_amb_linia_detectada=round(float(ok[(TS >= 115) & (TS <= 235)].mean()), 2))
desa_json('V2_LLUNA.json', rep); log(json.dumps(rep, ensure_ascii=False))
# polars
DS = np.arange(-4, 12.01, 0.25); TT, DD = np.meshgrid(np.radians(TS), DS)
MX = (cx + (R + DD) * np.cos(TT) - ox).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT) - oy).astype(np.float32)
PA = cv2.remap(aP, MX, MY, cv2.INTER_LINEAR); PN = cv2.remap(a_new, MX, MY, cv2.INTER_LINEAR)
k0, k1 = 95 * 4, 245 * 4; zx, zy = 2, 6
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15)
S = Image.new('RGB', ((k1 - k0) * zx, 2 * (len(DS) * zy + 24) + 10), 'white'); dr = ImageDraw.Draw(S)
for i, (M_, et) in enumerate([(PA, 'alfa de la teva Lluna (258)'), (PN, 'alfa nova (V90): vora nítida a la línia de la cromosfera')]):
    pil = Image.fromarray(np.uint8(np.clip(M_[:, k0:k1], 0, 1) * 255)).resize(((k1 - k0) * zx, len(DS) * zy), Image.NEAREST).convert('RGB'); di = ImageDraw.Draw(pil)
    pts = [((k - k0) * zx, int((dl[k] - DS[0]) / 0.25 * zy)) for k in range(k0, k1) if np.isfinite(dl[k])]; di.point(pts, fill=(255, 0, 0))
    yl = int((0 - DS[0]) / 0.25 * zy); di.line([(0, yl), (pil.width, yl)], fill=(255, 200, 0))
    for az in range(100, 245, 10): xl = (az * 4 - k0) * zx; di.line([(xl, 0), (xl, 8)], fill=(0, 200, 0)); di.text((xl + 2, 0), str(az), fill=(0, 200, 0), font=F)
    Y0 = i * (len(DS) * zy + 24); S.paste(pil, (0, Y0 + 22)); dr.text((4, Y0 + 3), et + ' · polars 95°→245°, d −4..+12 px (×6); vermell: línia de cromosfera; groc: d = 0', fill='black', font=F)
S.save(SORT / 'LAMINA_V2_lluna.png'); log('fet')
