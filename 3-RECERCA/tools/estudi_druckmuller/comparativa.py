"""Comparativa: el que lliurem avui / el mateix a la manera de Brno / Brno.
Els dos nostres son el LLENC SENCER, cap retall (norma de Pere del 26-08)."""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geometria import CARPETA, carrega, retalla_marc

RUN = (__import__("glob").glob(os.path.expanduser("/Users/USUARI/Desktop/Eclipse determinista/1-RUNS/*20260826T112542Z*")) + [""])[0] + "/"
OUT = "/Users/USUARI/Desktop/Eclipse determinista/2-OUTPUT/ESTUDI_DRUCKMULLER"


def overlay(a, b):
    return np.where(a < 0.5, 2*a*b, 1.0 - 2.0*(1.0-a)*(1.0-b))


base = np.load(RUN + "3-filtres/BASE_rgb.npy").astype(np.float32)
det = np.load(RUN + "3-filtres/DETALL_PASSA_ALT.npy").astype(np.float32)
if det.ndim == 3:
    det = det.mean(axis=2)
avui = np.clip(overlay(base, det[:, :, None]), 0, 1)
H, W = avui.shape[:2]
avui_x8 = np.asarray(Image.fromarray((avui*255+0.5).astype(np.uint8)).resize((W//8, H//8), Image.LANCZOS))
nou_x8 = np.asarray(Image.open(os.path.join(OUT, "PROVA_BRNO_brno_x8.png")).convert("RGB"))

nom = "TSE_2026_400mm_DHS.png"
rgb = carrega(nom); f0, f1, c0, c1 = retalla_marc(rgb)
brno = (rgb[f0+3:f1-3, c0+3:c1-3] * 255 + 0.5).astype(np.uint8)

alt = max(avui_x8.shape[0], nou_x8.shape[0], brno.shape[0])
pans = []
for a, t in [(avui_x8, "1. EL QUE LLIUREM AVUI  (llenc sencer)"),
             (nou_x8, "2. EL MATEIX, A LA MANERA DE BRNO  (llenc sencer · PROVA)"),
             (brno, "3. DRUCKMULLER 400 mm · Pico Trigaza · 12-08-2026")]:
    im = Image.fromarray(a)
    if im.height != alt:
        im = im.resize((int(im.width*alt/im.height), alt), Image.LANCZOS)
    pans.append((im, t))

marge, cap = 24, 46
Wt = sum(p.width for p, _ in pans) + marge*(len(pans)+1)
lien = Image.new("RGB", (Wt, alt + cap + marge*2), (12, 12, 14))
d = ImageDraw.Draw(lien)
try:
    fo = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 19)
except Exception:
    fo = ImageFont.load_default()
x = marge
for im, t in pans:
    lien.paste(im, (x, cap))
    d.text((x, cap - 28), t, fill=(232, 232, 236), font=fo)
    x += im.width + marge
d.text((marge, alt + cap + 8),
       "ESTUDI · el color de la corona: 1 i 2 son la MATEIXA dada; nomes canvia com es renderitza el color i la corba de to.",
       fill=(150, 150, 158), font=fo)
lien.save(os.path.join(OUT, "COMPARATIVA_BRNO.png"))
print("desat COMPARATIVA_BRNO.png", lien.size)
