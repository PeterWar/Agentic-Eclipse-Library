"""c7 · La capa de Pere «Ajust cua protuberància esquerra» (262, Lluminositat, 96 %): què conté respecte de la 76 de sota (de la qual és còpia),
on actua la seva màscara, i què canvia al compost emulat (sense capes d'ajust) al llenç sencer i a la protuberància.
Sortida: CAPA_CUA.json, LAMINA_M7_capa_cua.png."""
from vm_comu import *
from psb69 import PSB
from vm_compost import comp, capa_box
import cv2
from PIL import Image, ImageDraw, ImageFont
claim()
p = PSB(str(PSB_PERE)); L = p.layer(262); L76 = p.layer(76)
box = (L['left'], L['top'], L['right'], L['bottom']); log('262 caixa %s, 76 caixa %s' % (box, (L76['left'], L76['top'], L76['right'], L76['bottom'])))
a262 = p.channel_box(262, -1, box).astype(np.float32) / 65535; a76 = p.channel_box(76, -1, box).astype(np.float32) / 65535
m262 = p.channel_box(262, -2, box, fill=65535).astype(np.float32) / 65535; m76 = p.channel_box(76, -2, box, fill=65535).astype(np.float32) / 65535
res = dict(caixa_262=box, alfa_igual_76=bool(np.array_equal(a262, a76)), mascara_262_mitjana=float(m262.mean()), mascara_262_px_mes_de_0_5=int((m262 > 0.5).sum()), mascara_262_px_entre_0_01_i_0_99=int(((m262 > 0.01) & (m262 < 0.99)).sum()))
ys, xs = np.nonzero(m262 > 0.02); res['mascara_262_caixa_activa'] = [int(xs.min() + box[0]), int(ys.min() + box[1]), int(xs.max() + box[0]), int(ys.max() + box[1])] if xs.size else None
c262 = np.stack([p.channel_box(262, c, box) for c in range(3)], -1).astype(np.float32) / 65535; c76 = np.stack([p.channel_box(76, c, box) for c in range(3)], -1).astype(np.float32) / 65535
def lum(C): return 0.3 * C[..., 0] + 0.59 * C[..., 1] + 0.11 * C[..., 2]
ok = a76 > 0.99; l262, l76 = lum(c262), lum(c76)
# relació de lluminància 262 vs 76 (corba aplicada?) per calaixos de la 76
bins = np.linspace(0, 1, 41); idx = np.clip(np.digitize(l76[ok], bins) - 1, 0, 39)
corba = [[round(float((bins[i] + bins[i + 1]) / 2), 3), round(float(np.median(l262[ok][idx == i])), 4) if (idx == i).sum() > 100 else None] for i in range(40)]
res['corba_lum_76_a_262'] = corba; res['diferencia_color_max'] = float(np.abs(c262 - c76)[ok].max()); res['px_diferents'] = int((np.abs(c262 - c76).max(-1) > 1 / 255)[ok].sum())
desa_json('CAPA_CUA.json', res); log(json.dumps({k: v for k, v in res.items() if k != 'corba_lum_76_a_262'}))
# compost emulat amb i sense 262 al llenç sencer (reduït ×4) i a la protuberància
vis = [l['id'] for l in p.layers if l['visible'] and l['right'] > l['left']]
BX = (0, 0, W, H); f = 4
def compost(ids, bx):
    x0, y0, x1, y1 = bx; lay = [capa_box(p, i, bx) for i in ids]; return comp(lay, y1 - y0, x1 - x0)[0]
BP = (4700, 3450, 5150, 4100)
amb = compost(vis, BP); sense = compost([i for i in vis if i != 262], BP)
np.savez_compressed(SORT / 'cua_protuberancia_amb_i_sense_262.npz', caixa=np.array(BP), amb=np.round(amb * 65535).astype(np.uint16), sense=np.round(sense * 65535).astype(np.uint16))
# mapa de la màscara 262 i de l'efecte de 262 al llenç sencer (lluminància amb − sense), reduït
m_full = p.channel_box(262, -2, BX, fill=65535)[::f, ::f].astype(np.float32) / 65535; a_full = p.channel_box(262, -1, BX)[::f, ::f].astype(np.float32) / 65535
try: F_ = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 16); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 20)
except Exception: F_ = FB = ImageFont.load_default()
Wd = W // f; Hd = H // f; S = Image.new('RGB', (2 * Wd + 10, Hd + 40), 'white'); d = ImageDraw.Draw(S)
d.text((6, 8), 'Capa 262 de Pere: màscara (blanc = actua) · alfa (blanc = la capa té píxels; és la de la 76, el camp de les fotos Vixen)', fill='black', font=FB)
S.paste(Image.fromarray(np.uint8(m_full * 255)).convert('RGB'), (0, 40)); S.paste(Image.fromarray(np.uint8(a_full * 255)).convert('RGB'), (Wd + 10, 40))
S.save(SORT / 'LAMINA_M7_capa_cua_mascara.png')
def v(C, lo, hi): return Image.fromarray(np.uint8(np.clip((C - lo) / (hi - lo), 0, 1) * 255))
la, ls = lum(amb), lum(sense); lo, hi = np.percentile(ls, [1, 99.8]); zf = 2; w_, h_ = (BP[2] - BP[0]) * zf, (BP[3] - BP[1]) * zf
S = Image.new('RGB', (3 * (w_ + 8), h_ + 40), 'white'); d = ImageDraw.Draw(S)
d.text((6, 8), 'Protuberància esquerra, compost emulat sense capes d\'ajust (2:1): sense la 262 · amb la 262 · diferència de lluminància (gris = 0)', fill='black', font=FB)
S.paste(Image.fromarray(np.uint8(np.clip(sense * 255, 0, 255))).resize((w_, h_), Image.LANCZOS), (0, 40)); S.paste(Image.fromarray(np.uint8(np.clip(amb * 255, 0, 255))).resize((w_, h_), Image.LANCZOS), (w_ + 8, 40))
S.paste(v(la - ls, -0.15, 0.15).resize((w_, h_), Image.NEAREST), (2 * (w_ + 8), 40)); S.save(SORT / 'LAMINA_M7_capa_cua_protuberancia.png'); log('fet')
