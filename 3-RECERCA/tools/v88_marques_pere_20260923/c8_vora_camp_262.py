"""c8 · La vora del camp Vixen que fa la capa 262: compost emulat (sense capes d'ajust) amb i sense la 262 al llenç sencer, reduït ×4 (cada capa es
llegeix sencera i es delma), i el mateix amb la màscara de la 262 posada a 0 on val ≤ 20/255 (només la cua pintada). Sortida: VORA_CAMP_262.json,
LAMINA_M8_vora_camp.png (mapa de la diferència de lluminància i perfil a través de la vora)."""
from vm_comu import *
from psb69 import PSB
from vm_compost import comp
from PIL import Image, ImageDraw, ImageFont
claim()
f = 4; p = PSB(str(PSB_PERE)); vis = [l['id'] for l in p.layers if l['visible'] and l['right'] > l['left']]; ids = vis[:vis.index(262) + 1]
def capa(lid, mask_llindar=None):
    L = p.layer(lid); bx = (0, 0, W, H)
    F = np.stack([p.channel_box(lid, c, bx)[::f, ::f] for c in range(3)], -1).astype(np.float32) / 65535
    a = p.channel_box(lid, -1, bx)[::f, ::f].astype(np.float32) / 65535 if -1 in L['chans'] else np.ones(F.shape[:2], np.float32)
    if L['mask'] is not None and -2 in L['chans']:
        m = p.channel_box(lid, -2, bx, fill=65535 if L['mask']['background'] == 255 else 0)[::f, ::f].astype(np.float32) / 65535
        if mask_llindar is not None: m = np.where(m <= mask_llindar, 0, m)
    else: m = 1
    return (L['blend'], F, a * m * (L['opacity'] / 255.0))
base = [capa(i) for i in ids[:-1]]; h, w = base[0][1].shape[:2]
C0 = comp(base, h, w)[0]; C1 = comp(base + [capa(262)], h, w)[0]; C2 = comp(base + [capa(262, 20 / 255)], h, w)[0]
def lum(C): return 0.3 * C[..., 0] + 0.59 * C[..., 1] + 0.11 * C[..., 2]
d1 = lum(C1) - lum(C0); d2 = lum(C2) - lum(C0)
a262 = p.channel_box(262, -1, (0, 0, W, H))[::f, ::f] > 32768
# a la vora del camp: píxels de dins a 1–6 px (reduïts) de la vora, contra els de fora
import cv2
ins = cv2.erode(a262.astype(np.uint8), np.ones((3, 3), np.uint8)); vora_in = (a262 & ~cv2.erode(a262.astype(np.uint8), np.ones((13, 13), np.uint8)).astype(bool))
lluny = np.hypot(*np.mgrid[:h, :w][::-1] - np.array([5375.8 / f, 3776 / f])[:, None, None]) > 1500 / f
res = dict(reduccio=f, capes_sota_262=ids[:-1], dL_mitja_dins_camp_lluny_de_la_lluna=float(np.median(d1[a262 & lluny])), dL_p5_p95=[float(np.percentile(d1[a262 & lluny], 5)), float(np.percentile(d1[a262 & lluny], 95))],
           dL_a_la_vora_del_camp=float(np.median(d1[vora_in & lluny])), amb_mascara_a_0_sota_20=dict(dL_mitja=float(np.median(d2[a262 & lluny])), dL_max_abs=float(np.abs(d2[a262 & lluny]).max())),
           L_compost_lluny_mitja=float(np.median(lum(C0)[a262 & lluny])))
desa_json('VORA_CAMP_262.json', res); log(json.dumps(res))
try: FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 22)
except Exception: FB = ImageFont.load_default()
def v(D, lim): return Image.fromarray(np.uint8(np.clip(D / lim * 0.5 + 0.5, 0, 1) * 255))
S = Image.new('RGB', (2 * w + 10, h + 40), 'white'); dr = ImageDraw.Draw(S)
dr.text((6, 8), 'Lluminància amb − sense la capa 262 (compost emulat, ±0,02; gris = 0): tal com és · amb la seva màscara a 0 on val ≤ 20/255', fill='black', font=FB)
S.paste(v(d1, 0.02), (0, 40)); S.paste(v(d2, 0.02), (w + 10, 40)); S.save(SORT / 'LAMINA_M8_vora_camp.png'); log('fet')
