"""a1 (29-09-2026) · Les marques de Pere a la V114 (capa 414 «V114 Artefactes»: negre translúcid, ~6 %) i el que hi ha a sota.
Llegeix el PSB del disc (mai no l'obre al Photoshop). Treu la 414 del compost desat de manera exacta, C = (1−a)·U + a·K ⇒ U = (C − a·K)/(1−a),
i desa:
  - U_compost_sense_414_u16.npy       el compost que Pere veu, sense les marques (Adobe RGB, 16 bits)
  - MARQUES_414.json                  cada marca: caixa, centre, r (R☉), angle de pantalla i angle de posició (des del nord celeste, cap a l'est)
  - marques_414_etiquetes.npy         etiqueta de marca per píxel (llenç sencer, 0 = cap)
  - vistes/V1_llenc_sencer_marques.png, V2_llenc_sencer.png (1/4, sRGB), V3_llenc_sencer_marques_realcat.png (contrast local, per veure'ls)
  - vistes/detall_marca_NN.png          cada marca a 1:1 amb el seu voltant (A MÉS del llenç sencer), natural i realçada
Ús: python3 a1_marques_i_vistes.py"""
import sys, json, numpy as np
from pathlib import Path
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB
OUT = ARREL / '4-RESULTATS/v114_artefactes_foscos_20260929'; (OUT / 'vistes').mkdir(parents=True, exist_ok=True)
PSB_V114 = ARREL / '1-PHOTOSHOP/V114.psb'
SOL = (5361.768, 3775.748); RSOL = 440.603        # graella del llenç (jutge_comu)
NORD = 45.253                                      # nord celeste al llenç, graus de pantalla (V106)
H, W = 7506, 10551

p = PSB(str(PSB_V114))
A, (x0, y0) = p.channel(414, -1); K = [p.channel(414, c)[0] for c in (0, 1, 2)]
C = p.composite()[..., :3].astype(np.float32)
a = np.zeros((H, W), np.float32); a[y0:y0 + A.shape[0], x0:x0 + A.shape[1]] = A / 65535.0
U = C.copy()
for c in range(3):
    k = np.zeros((H, W), np.float32); k[y0:y0 + A.shape[0], x0:x0 + A.shape[1]] = K[c]
    m = a > 0; U[..., c][m] = (C[..., c][m] - a[m] * k[m]) / (1 - a[m])
U = np.clip(np.round(U), 0, 65535).astype(np.uint16)
np.save(OUT / 'U_compost_sense_414_u16.npy', U)

# marques: components de l'alfa > 0 (8-veïns)
lab, n = ndi.label(a > 0, structure=np.ones((3, 3)))
np.save(OUT / 'marques_414_etiquetes.npy', lab.astype(np.uint8))
M = []
for i, sl in enumerate(ndi.find_objects(lab), 1):
    ys, xs = np.nonzero(lab[sl] == i); ys += sl[0].start; xs += sl[1].start
    cx, cy = float(xs.mean()), float(ys.mean()); r = float(np.hypot(cx - SOL[0], cy - SOL[1]) / RSOL)
    ang = float(np.degrees(np.arctan2(-(cy - SOL[1]), cx - SOL[0])) % 360)
    pa = float((ang - NORD) % 360)                  # angle de posició: des del nord celeste, antihorari a la pantalla (cap a l'est si el llenç no és mirall)
    M.append(dict(marca=i, pixels=int(len(ys)), caixa=[int(sl[1].start), int(sl[0].start), int(sl[1].stop), int(sl[0].stop)],
                  centre=[round(cx, 1), round(cy, 1)], r_Rsol=round(r, 2), angle_pantalla=round(ang, 1), angle_des_del_nord=round(pa, 1),
                  alfa_max=round(float(a[ys, xs].max()), 3), alfa_mediana=round(float(np.median(a[ys, xs])), 3)))
json.dump(dict(psb=str(PSB_V114.relative_to(ARREL)), capa=414, nom='V114 Artefactes', color_pinzell_RGB16=[int(np.median(k)) for k in (K[0][A > 0], K[1][A > 0], K[2][A > 0])],
               convencio='negre translúcid = artefacte fosc (com la 412 de la V111, on el blanc marcava els clars)', sol=SOL, rsol=RSOL, nord=NORD, marques=M),
          open(OUT / 'MARQUES_414.json', 'w'), ensure_ascii=False, indent=1)

# vistes (Adobe RGB → sRGB, 8 bits)
MA = np.array([[0.5767309, 0.1855540, 0.1881852], [0.2973769, 0.6273491, 0.0752741], [0.0270343, 0.0706872, 0.9911085]])
MS = np.linalg.inv(np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]]))
T = MS @ MA
def srgb(u16):
    lin = (u16.astype(np.float32) / 65535) ** 2.19921875
    s = np.clip(lin @ T.T, 0, 1)
    s = np.where(s <= 0.0031308, 12.92 * s, 1.055 * s ** (1 / 2.4) - 0.055)
    return (s * 255 + 0.5).astype(np.uint8)
def realca(u8, sig=60):
    """contrast local per veure nivells fins: (L − L suavitzat)·6 + 128, sobre la lluminància."""
    L = u8.astype(np.float32).mean(2); Ls = ndi.gaussian_filter(L, sig)
    v = np.clip((L - Ls) * 6 + 128, 0, 255).astype(np.uint8); return np.stack([v] * 3, 2)
def contorns(img, lab, f, color=(255, 64, 0)):
    ed = lab != ndi.grey_erosion(lab, size=(3, 3))
    ed = ed & (lab > 0)
    if f != 1:
        ys, xs = np.nonzero(ed); img[(ys // f).clip(0, img.shape[0] - 1), (xs // f).clip(0, img.shape[1] - 1)] = color
    else: img[ed] = color
    return img
try: FONT = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 44)
except Exception: FONT = ImageFont.load_default()
f = 4
S = srgb(U)
petit = S[::f, ::f].copy()
Image.fromarray(petit).save(OUT / 'vistes/V2_llenc_sencer.png')
v1 = contorns(petit.copy(), lab, f); im = Image.fromarray(v1); d = ImageDraw.Draw(im)
for m in M:
    x, y = m['caixa'][2] / f + 6, m['caixa'][1] / f - 4
    d.text((x, max(y, 2)), str(m['marca']), fill=(255, 64, 0), font=FONT, stroke_width=3, stroke_fill=(0, 0, 0))
im.save(OUT / 'vistes/V1_llenc_sencer_marques.png')
R_ = realca(S[::2, ::2], 30)[::2, ::2]
v3 = contorns(R_.copy(), lab, f); im = Image.fromarray(v3); d = ImageDraw.Draw(im)
for m in M: d.text((m['caixa'][2] / f + 6, max(m['caixa'][1] / f - 4, 2)), str(m['marca']), fill=(255, 64, 0), font=FONT, stroke_width=3, stroke_fill=(0, 0, 0))
im.save(OUT / 'vistes/V3_llenc_sencer_marques_realcat.png')
for m in M:
    x0_, y0_, x1_, y1_ = m['caixa']; mg = max(250, (x1_ - x0_) // 3)
    X0, Y0, X1, Y1 = max(0, x0_ - mg), max(0, y0_ - mg), min(W, x1_ + mg), min(H, y1_ + mg)
    s = S[Y0:Y1, X0:X1].copy(); l = lab[Y0:Y1, X0:X1]
    fd = max(1, int(np.ceil(max(X1 - X0, Y1 - Y0) / 1800)))
    nat = contorns(s[::fd, ::fd].copy(), np.where(l == m['marca'], l, 0)[::fd, ::fd], 1)
    rea = contorns(realca(s, 40)[::fd, ::fd].copy(), np.where(l == m['marca'], l, 0)[::fd, ::fd], 1)
    Image.fromarray(np.concatenate([nat, np.full((nat.shape[0], 8, 3), 255, np.uint8), rea], 1)).save(OUT / f"vistes/detall_marca_{m['marca']:02d}.png")
print(json.dumps([{k: m[k] for k in ('marca', 'caixa', 'r_Rsol', 'angle_des_del_nord')} for m in M], ensure_ascii=False))
