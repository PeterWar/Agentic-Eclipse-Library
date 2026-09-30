"""c2 · Vistes de les capes WOW (55 i 56) tal com són a WOW.psb, amb les marques de Pere perfilades: llenç a 1/4 i caixa de la Lluna a 1:1."""
import sys, json
from pathlib import Path
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/wow_marques_pere_20260924'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917')); from psb69 import PSB
p = PSB(str(ARREL / '1-PHOTOSHOP/WOW.psb')); W, H = 10551, 7506; Z = np.load(SORT / 'marques.npz')
COL = {'to_30_40': (255, 140, 0), 'to_100_110': (60, 230, 20), 'to_120_130': (20, 200, 60), 'to_350_360': (255, 0, 40), 'to_280_290': (190, 0, 255), 'gris_o_negre': (0, 255, 255)}
def canvas_mask(lid, nom):
    k = f'{lid}_{nom}'
    if k not in Z.files: return None
    m = Z[k]; x0, y0 = Z[f'{lid}_origen']; full = np.zeros((H, W), bool); full[y0:y0 + m.shape[0], x0:x0 + m.shape[1]] = m; return full
for lid, mk in ((55, 270), (56, 272)):
    Y = p.channel(lid, 0)[0].astype(np.float32) / 65535; A = p.channel(lid, -1)[0].astype(np.float32) / 65535
    Yd = np.where(A > 0.5, Y, 0.25)
    q = cv2.resize(Yd, (W // 4, H // 4), interpolation=cv2.INTER_AREA); img = np.stack([np.uint8(np.clip(q, 0, 1) * 255)] * 3, -1)
    L = img[3000:4550, 4600:6150] if False else None
    big = np.stack([np.uint8(np.clip(Yd[3000:4550, 4600:6150], 0, 1) * 255)] * 3, -1)
    for nom, col in COL.items():
        m = canvas_mask(mk, nom)
        if m is None: continue
        mq = cv2.resize(m.astype(np.float32), (W // 4, H // 4), interpolation=cv2.INTER_AREA) > 0.2; v = cv2.dilate(mq.astype(np.uint8), np.ones((3, 3), np.uint8)) & ~mq.astype(np.uint8); img[v > 0] = col
        mb = m[3000:4550, 4600:6150]; vb = cv2.dilate(mb.astype(np.uint8), np.ones((3, 3), np.uint8)) & ~mb.astype(np.uint8); big[vb > 0] = col
    Image.fromarray(img).save(SORT / f'VISTA_{lid}_llenc_quart.png'); Image.fromarray(big).save(SORT / f'VISTA_{lid}_lluna_1a1.png')
    print(lid, 'fet', flush=True)
