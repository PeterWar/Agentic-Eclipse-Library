"""c4 · Les màscares de capa dels 16 filtres (V95, iguals a Artefactes_V95) contra les marques de Pere: contorns de la màscara (nivells 10/50/90 %)
a 1/4, amb les marques. Només lectura."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/artefactes_v95_pere_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
p = PSB(str(ARREL / '1-PHOTOSHOP/V95.psb')); W, H = 10551, 7506; f = 4
Z = np.load(SORT / 'marques.npz'); M = json.loads((SORT / 'MARQUES.json').read_text())['marques']
MAP = {48: '284', 50: '283', 53: '282', 43: '280', 44: '279', 41: '277', 42: '276', 47: '275', 49: '274', 51: '273', 45: '272', 46: '271', 56: '270', 54: '54', 52: '52'}
def marca(clau):
    out = np.zeros((H, W), bool)
    if f'{clau}_origen' not in Z.files: return out
    x0, y0 = Z[f'{clau}_origen']
    for k in Z.files:
        if k.startswith(clau + '_') and not k.endswith('origen'): mm = Z[k]; out[y0:y0 + mm.shape[0], x0:x0 + mm.shape[1]] |= mm
    return out
tiles = []; F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 20)
for lid, clau in MAP.items():
    L = p.layer(lid); mk, (mx, my) = p.channel(lid, -2)
    full = np.full((H, W), 0, np.float32)
    if mk is not None and mk.size:
        mk = mk.astype(np.float32) / (65535 if mk.dtype == np.uint16 else 255); x1, y1 = min(W, mx + mk.shape[1]), min(H, my + mk.shape[0]); full[max(0, my):y1, max(0, mx):x1] = mk[max(0, -my):y1 - my, max(0, -mx):x1 - mx]
    m4 = cv2.resize(full, (W // f, H // f), interpolation=cv2.INTER_AREA); img = np.stack([np.uint8(m4 * 200)] * 3, -1)
    for lv, col in ((0.1, (0, 160, 255)), (0.5, (0, 255, 0)), (0.9, (255, 0, 255))):
        cs, _ = cv2.findContours((m4 >= lv).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE); cv2.drawContours(img, cs, -1, col, 2)
    mm = cv2.resize(marca(clau).astype(np.float32), (W // f, H // f), interpolation=cv2.INTER_AREA) > 0.05; ov = img.copy(); ov[mm] = (255, 60, 0); img = cv2.addWeighted(ov, 0.7, img, 0.3, 0)
    im = Image.fromarray(img).resize((W // 8, H // 8), Image.LANCZOS); ImageDraw.Draw(im).text((8, 8), f'{lid} {L["name"][:34]} · màscara (gris) i marques (taronja)', fill='white', font=F)
    tiles.append(im); print(lid, 'màscara: mitjana', round(float(full.mean()), 3), 'mín', round(float(full.min()), 3), 'màx', round(float(full.max()), 3))
cols = 3; tw, th = tiles[0].size; out = Image.new('RGB', (cols * tw, ((len(tiles) + cols - 1) // cols) * th), 'black')
for i, t in enumerate(tiles): out.paste(t, ((i % cols) * tw, (i // cols) * th))
out.save(SORT / 'MASCARES_FILTRES_I_MARQUES.png'); print('fet', out.size)
