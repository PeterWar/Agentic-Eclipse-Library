"""c5 · Mosaic de la final amb SOHO/LASCO C2 (com un mosaic publicat), amb la vista de lasco_vista (harmònics d'angle fora).
  M1  la final fins a 3,5 R☉ i el C2 (18:24:31) de 3,5 a 6,4 R☉.
  ⛔ El C3 no hi va: sense el fons mensual oficial de la NRL, la seva vista queda dominada per llum difusa i soroll
     (provat amb m ≤ 4, 8 i 12 harmònics; descartat). Si cal, baixar el fons o les vistes processades de la NRL.
La final no es gira ni es retoca: només se'n redueix l'escala (100 px per R☉). El LASCO es remostreja a la seva orientació.
El pilar dels ocultadors es deixa en negre (no s'hi extrapola res)."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *
from lasco_vista import VistaLasco
Image.MAX_IMAGE_PIXELS = None
import os
CA = os.environ.get('LANG_FIG') == 'ca'; SUF = '_ca' if CA else ''
SRGB = ARREL / 'publicacions/APOD/enviament_20260930/Eclipse_2026-08-12_Pere_Guerra_Serra.jpg'
FONT = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
def font(sz): return ImageFont.truetype(FONT, sz)
gF = geo_final('efemeride')
fin = Image.open(SRGB).convert('RGB'); W, H = fin.size

v2 = VistaLasco('24038985.fts', 2.25, 6.4, mmax=3, suau_r=1.0)
v3 = VistaLasco('32869549.fts', 3.9, 30.0, mmax=8, suau_r=2.5)
PIL2, PIL3 = (290.0, 352.0), (288.0, 356.0)

RPX = 200.0; S = 2640
gO = Geo('mosaic', S / 2 - 0.5, S / 2 - 0.5, RPX, gF.n, gF.e, '', '')
f = gF.R / RPX
fr = fin.resize((round(W / f), round(H / f)), Image.LANCZOS); fa = np.asarray(fr).astype(np.float32) / 255
gFf = Geo('f', (gF.cx + 0.5) / f - 0.5, (gF.cy + 0.5) / f - 0.5, gF.R / f, gF.n, gF.e, '', '')
yy, xx = np.mgrid[0:S, 0:S].astype(np.float64); rO, paO = gO.polar(xx, yy)
fx, fy = gFf.px(rO, paO)
finO = np.dstack([nd.map_coordinates(fa[..., c], [fy, fx], order=1, mode='constant', cval=np.nan) for c in range(3)])
dins_marc = np.isfinite(finO[..., 0])

def vista(v, pil, lo=-1.3, hi=4.0, suau_pa=0.0):
    z = v.mostra(rO, paO)
    z[(paO >= pil[0]) & (paO <= pil[1])] = np.nan
    t = np.clip((z - lo) / (hi - lo), 0, 1); return np.where(np.isfinite(t), t, np.nan)
t2 = vista(v2, PIL2, lo=-0.8, hi=3.8) ** 1.15; t3 = np.full_like(t2, np.nan)   # C3 fora (vegeu la nota)
C2COL, C3COL = np.array([1.0, 0.60, 0.28]), np.array([0.40, 0.64, 1.0])

def compon(rtall, sencera):
    out = np.zeros((S, S, 3), np.float32)
    z3 = (rO >= 6.3) & np.isfinite(t3); out[z3] = t3[z3][:, None] * C3COL
    z2 = (rO < 6.3) & np.isfinite(t2) & ((rO >= rtall) | sencera); out[z2] = t2[z2][:, None] * C2COL
    zf = dins_marc & ((rO < rtall) | sencera); out[zf] = finO[zf]
    return np.clip(out, 0, 1)

for nom, rt, sencera in [('M1_mosaic_final_i_LASCO_C2', 3.5, False)]:
    a = (compon(rt, sencera) * 255).astype(np.uint8)
    im = Image.fromarray(a); d = ImageDraw.Draw(im, 'RGBA')
    for r_ in [rt]:
        rp = r_ * RPX; d.ellipse([S / 2 - rp, S / 2 - rp, S / 2 + rp, S / 2 + rp], outline=(255, 255, 255, 70), width=2)
    f1, f2 = font(36), font(24)
    d.text((44, 36), 'SOHO/LASCO C2 · 18:24:31 UT  (més enllà de 3,5 R☉)' if CA else 'SOHO/LASCO C2 · 18:24:31 UT  (beyond 3.5 R☉)', fill=tuple(int(255 * c) for c in C2COL), font=f1)
    d.text((44, 84), 'Eclipsi total 2026-08-12 · 18:28:46 UT · Pere Guerra  (fins a 3,5 R☉)' if CA else 'Total eclipse 2026-08-12 · 18:28:46 UT · Pere Guerra  (inside 3.5 R☉)', fill=(242, 222, 170), font=f1)
    d.text((44, S - 92), 'Dades del LASCO: SOHO (ESA i NASA), nivell 0,5, vinyetatge corregit; sense les components d’angle de gran escala.' if CA else 'LASCO data: SOHO (ESA & NASA), level 0.5, vignetting-corrected; low-order angular background removed.', fill=(165, 165, 165), font=f2)
    d.text((44, S - 58), 'Fotografia tal com es va publicar (sense girar, només reduïda); el LASCO s’hi ha reprojectat. Falca negra: braç de l’ocultador.' if CA else 'Eclipse image as published (not rotated, only rescaled); LASCO reprojected onto it. Black wedge: occulter pylon.', fill=(165, 165, 165), font=f2)
    n = gF.n; x1, y1 = S - 170, 230
    d.line([x1, y1, x1 + 110 * n[0], y1 + 110 * n[1]], fill=(235, 235, 235), width=4)
    d.text((x1 + 128 * n[0] - 20, y1 + 128 * n[1] - 40), 'N☉', fill=(235, 235, 235), font=f1)
    d.line([S - 44 - 1 * RPX, S - 150, S - 44, S - 150], fill=(235, 235, 235), width=4)
    d.text((S - 44 - 1 * RPX, S - 200), '1 R☉', fill=(235, 235, 235), font=f1)
    im.save(VISTES / f'{nom}{SUF}.jpg', quality=93)
    im.resize((1600, 1600), Image.LANCZOS).save(VISTES / f'{nom}_1600{SUF}.jpg', quality=90)
    print('desat', nom)

# P3 refet amb la vista nova: el marc sencer de la final (reduïda ×4) i el C2 al mateix marc
f4 = 4.0; fr4 = fin.resize((round(W / f4), round(H / f4)), Image.LANCZOS); Hh, Ww = fr4.size[1], fr4.size[0]
g4 = Geo('f4', (gF.cx + 0.5) / f4 - 0.5, (gF.cy + 0.5) / f4 - 0.5, gF.R / f4, gF.n, gF.e, '', '')
yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float64); r4, pa4 = g4.polar(xx, yy)
z = v2.mostra(r4, pa4); z[(pa4 >= PIL2[0]) & (pa4 <= PIL2[1])] = np.nan
t = np.clip((z + 1.3) / 5.3, 0, 1); t = np.where(np.isfinite(t), t, 0)
fr4.save(VISTES / 'P3_final_vs_LASCO_C2_A_final.jpg', quality=92)
Image.fromarray((np.dstack([t, t, t]) * 255).astype(np.uint8)).save(VISTES / 'P3_final_vs_LASCO_C2_B.jpg', quality=92)
print('P3 refet; fet')
