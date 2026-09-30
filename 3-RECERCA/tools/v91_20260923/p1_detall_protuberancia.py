"""p1 (V91) · Capa nova «Protuberància esquerra · guspires de la foto 76» (Sobreexposició lineal): les estructures fines de la foto de Pere 76
(«Interiors 06–12 · encaix de Pere», la foto no linealitzada que Pere va enviar com a referència) a la protuberància esquerra: guspires i
filaments. Al compost es perdien perquè la 76 i la 266 són en «Aclarir»: una guspira feble que a la foto destaca sobre un fons de corona FOSC no
supera la nostra corona brillant (i la màscara de la 96 només obre el nucli). Es transfereix el CONTRAST RELATIU de la foto:
  E = [top-hat blanc de la lluminància de la 76 (disc de 7 px) − 2·MAD] × (nivell local del compost sota les fotos / fons local de la foto) × GUANY,
  on GUANY és el realç de les guspires (els filtres realcen la textura de la corona però no veuen l'Hα; sense realç s'hi perden);
  amb el color rosa mitjà de la protuberància a la mateixa foto; a la regió de la protuberància (azimut 160–195°, d 6–60 px, vores suaus; la línia del limbe en queda fora),
  i FORA del cos de la protuberància (lluminància de la foto > fons + 0,12, dilatat 3 px i suavitzat 2 px), que ja el donen la 76 i la 266: així no es crema.
Sortida: P1_PROTUBERANCIA.npz, P1_PROTUBERANCIA.json i LAMINA_P1_protuberancia.png."""
from v91_comu import *
import os
from psb69 import PSB
from v86_operadors import smoothstep
import cv2, tifffile, io
from PIL import Image, ImageCms, ImageDraw, ImageFont
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v90_marques_pere_20260923'))
from vm_compost import comp, capa_box
claim(); GEO = json.loads((SORT / 'A2_GEOMETRIA.json').read_text())['lluna_presentacio']; cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
BX = (4740, 3470, 5020, 4040); x0, y0, x1, y1 = BX; h, w = y1 - y0, x1 - x0
p = PSB(str(ARREL / '1-PHOTOSHOP/V90.psb')); FOTO = 76
F = np.stack([p.channel_box(FOTO, c, BX) for c in range(3)], -1).astype(np.float32) / 65535; L = 0.3 * F[..., 0] + 0.59 * F[..., 1] + 0.11 * F[..., 2]
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
RSE = 7; ker = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * RSE + 1, 2 * RSE + 1)); TH = cv2.morphologyEx(L, cv2.MORPH_TOPHAT, ker)
refz = (((th >= 143) & (th <= 154)) | ((th >= 201) & (th <= 212))) & (d > 15) & (d < 60)
mad = float(np.median(np.abs(TH[refz] - np.median(TH[refz])))) * 1.4826; t = 2 * mad; Eth = np.clip(TH - t, 0, None)
# fons local de la foto (obertura gran i suavitzat) i nivell local del compost de sota les fotos (base + filtres + Lluna)
fons = cv2.GaussianBlur(cv2.morphologyEx(L, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (41, 41))), (0, 0), 8)
vis = [Lr['id'] for Lr in p.layers if Lr['visible'] and Lr['right'] > Lr['left']]; vis = vis[:vis.index(224) + 1]
sota = [i for i in vis if i not in (76, 266, 262, 96, 224)]; Cs = comp([capa_box(p, i, BX) for i in sota], h, w)[0]
nivell = cv2.GaussianBlur(0.3 * Cs[..., 0] + 0.59 * Cs[..., 1] + 0.11 * Cs[..., 2], (0, 0), 8)
GUANY = float(os.environ.get('GUANY_GUSPIRES', '3'))
g = (np.clip(nivell / np.maximum(fons, 1e-3), 1, 5) * GUANY).astype(np.float32)
prom = (th > 165) & (th < 190) & (d > 4) & (d < 45) & (F[..., 0] > F[..., 1] * 1.3); col = F[prom].mean(0); col = col / (0.3 * col[0] + 0.59 * col[1] + 0.11 * col[2])
reg = (smoothstep(th, 160, 164) * (1 - smoothstep(th, 191, 195)) * smoothstep(d, 6, 9) * (1 - smoothstep(d, 50, 60))).astype(np.float32)
# el cos de la protuberància (i el nucli i el limbe) ja el donen la 76 i la 266: fora de la capa, per no cremar-lo en blanc; només les guspires
cos = (L > fons + 0.12).astype(np.uint8); cos = cv2.dilate(cos, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))); w_cos = cv2.GaussianBlur(cos.astype(np.float32), (0, 0), 2)
reg = (reg * (1 - np.clip(w_cos, 0, 1))).astype(np.float32)
E = np.clip((Eth * g)[..., None] * col[None, None, :], 0, 1).astype(np.float32)
np.savez_compressed(SORT / 'P1_PROTUBERANCIA.npz', caixa=np.array(BX), rgb=np.round(E * 65535).astype(np.uint16), alfa=np.round(reg * 65535).astype(np.uint16))
rep = dict(font=f'capa {FOTO} de la V90 de Pere (lluminància)', top_hat_disc_radi_px=RSE, llindar_soroll=round(t, 5), guany_mitja_a_la_regio=round(float(g[reg > 0.5].mean()), 2), color_rosa=np.round(col, 3).tolist(),
           regio=dict(azimut=[160, 195], d_px=[6, 60]), guany_realc=GUANY, caixa=list(BX), afegit_max=round(float(E.max()), 3), px_amb_detall=int(((Eth > 0) & (reg > 0)).sum()))
desa_json('P1_PROTUBERANCIA.json', rep); log(json.dumps(rep, ensure_ascii=False))
icc = tifffile.TiffFile(ARREL / '4-RESULTATS/v88_marques_pere_20260923/compost_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
def im(C): return ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(C * 255, 0, 255))), TR)
Ctot = comp([capa_box(p, i, BX) for i in vis], h, w)[0]; amb = np.clip(Ctot + E * reg[..., None], 0, 1)
bp = (4868 - x0, 3690 - y0, 4936 - x0, 3850 - y0); cr = (slice(bp[1], bp[3]), slice(bp[0], bp[2]))
pan = [('76 sola', F[cr]), ('compost sense ajustos, ara', Ctot[cr]), ('+ guspires de la 76', amb[cr]), ('capa nova sola (×2)', np.clip(2 * E[cr] * reg[cr][..., None], 0, 1))]
FN = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 14); zf = 4; Wc, Hc = (bp[2] - bp[0]) * zf, (bp[3] - bp[1]) * zf
S = Image.new('RGB', (len(pan) * (Wc + 8), Hc + 24), 'white'); dr = ImageDraw.Draw(S)
for i, (et, C) in enumerate(pan): S.paste(im(C).resize((Wc, Hc), Image.LANCZOS), (i * (Wc + 8), 22)); dr.text((i * (Wc + 8) + 2, 3), et, fill='black', font=FN)
S.save(SORT / 'LAMINA_P1_protuberancia.png'); log('fet')
