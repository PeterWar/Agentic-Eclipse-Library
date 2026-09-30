"""c1 · On queda la «lent» (Pere, 23-09 nit: «jo encara veig una mica d'efecte lent»). Mesura objectiva de l'ESTIRAMENT RADIAL de la textura
arran del limbe, a tots els azimuts, als composts de Photoshop (V88 de Pere 18:50, V90 de Pere 22:06, V91 22:32; caixa de la Lluna).
Mètode: lluminància en polars centrades a la Lluna (0,05° × 0,25 px). Textura fina = el que canvia al llarg de l'azimut a escala de pocs px
(pas alt NOMÉS en azimut, σ 3 px d'arc): així el salt de la Lluna i el perfil radial, que no canvien amb l'azimut, en surten (la trampa de la
curvatura i de l'índex a6). Per a la textura, energia del gradient radial E_d i azimutal E_s (en px). Una textura estirada al llarg del radi
(la lent) té E_d/E_s petit. Índex de lent L = (E_d/E_s a 16–30 px) / (E_d/E_s a 2,5–10 px): 1 = la vora com la corona del costat; > 1 = la
textura arran del limbe és més estirada radialment que la de més enfora. Sortida: C1_ESTIRAMENT.json, LAMINA_C1_index_lent.png i
LAMINA_C2_polars_<sector>.png (V88, V90 i V91 desenrotllades, d de −3 a 30 px, ×3)."""
from pathlib import Path
import json, sys, time
import numpy as np, cv2, tifffile, io
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
from PIL import Image, ImageCms, ImageDraw, ImageFont
ARREL = Path(__file__).resolve().parents[3]; SORT = ARREL / '4-RESULTATS/v91_lent_residual_20260923'
o = json.loads((ARREL / '.coordination/claim.lock/owner.json').read_text()); assert o.get('serial_writes') == 'HELD'
def log(s): print(time.strftime('%H:%M:%S'), s, flush=True)
GEO = json.loads((ARREL / '4-RESULTATS/v91_20260923/A2_GEOMETRIA.json').read_text())['lluna_presentacio']; B0 = (4600, 3000)
cx, cy, R = GEO['cx'] - B0[0], GEO['cy'] - B0[1], GEO['R']
V = {'V88': ARREL / '4-RESULTATS/v88_marques_pere_20260923/compost_lluna.tif', 'V90': ARREL / '4-RESULTATS/v91_20260923/compost_V90_2206_lluna.tif',
     'V91': ARREL / '4-RESULTATS/v91_20260923/compost_V91_lluna.tif'}
icc = tifffile.TiffFile(V['V88']).pages[0].tags['InterColorProfile'].value
DT = 0.05; NT = int(360 / DT); DR = 0.25; DS = np.arange(-3, 30.001, DR); TS = np.radians((np.arange(NT) + 0.5) * DT)
TT, DD = np.meshgrid(TS, DS); MX = (cx + (R + DD) * np.cos(TT)).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT)).astype(np.float32)
ds_arc = np.radians(DT) * (R + DS)[:, None]                         # px d'arc per mostra, per fila
near = (DS >= 2.5) & (DS <= 10); far = (DS >= 16) & (DS <= 30); rep = {}; POL = {}; LL = {}
for k, p in V.items():
    A = tifffile.imread(p)[..., :3].astype(np.float32) / 65535; Y = 0.2126 * A[..., 0] + 0.7152 * A[..., 1] + 0.0722 * A[..., 2]
    P = cv2.remap(Y, MX, MY, cv2.INTER_LINEAR); POL[k] = cv2.remap(A, MX, MY, cv2.INTER_LINEAR)
    sig = 3.0 / ds_arc.mean(); T = P - gaussian_filter1d(P, sig, axis=1, mode='wrap')      # pas alt en azimut (σ 3 px d'arc)
    Ed = (np.diff(T, axis=0) / DR) ** 2; Ed = np.vstack([Ed, Ed[-1:]]); Es = (np.diff(T, axis=1, append=T[:, :1]) / ds_arc) ** 2
    W = int(5 / DT); f = lambda E, m: uniform_filter1d(E[m].mean(0), W, mode='wrap')
    L = (f(Ed, far) / f(Es, far)) / (f(Ed, near) / f(Es, near)); LL[k] = L
    rep[k] = {f'{a}-{a + 15}': round(float(L[int(a / DT):int((a + 15) / DT)].mean()), 2) for a in range(0, 360, 15)}
    log(k + ' ' + json.dumps(rep[k]))
(SORT / 'C1_ESTIRAMENT.json').write_text(json.dumps(dict(index_lent_per_15_graus=rep, bandes=dict(prop=[2.5, 10], lluny=[16, 30]), pas_alt_azimut_px=3.0), ensure_ascii=False, indent=2) + '\n')
np.savez_compressed(SORT / 'C1_index_lent.npz', **{k: v.astype(np.float32) for k, v in LL.items()})
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 18)
Wd, Hd = 1800, 560; S = Image.new('RGB', (Wd, Hd), 'white'); d = ImageDraw.Draw(S); X0, Y0, XW, YH = 60, 40, Wd - 90, Hd - 120
top = 4.0; col = {'V88': (120, 120, 120), 'V90': (220, 60, 60), 'V91': (30, 90, 220)}
for a0, a1, c_, et in ((104, 228, (225, 235, 255), 'V91: suavitzat radial (104–228°)'), (0, 32, (255, 215, 235), 'lent V90'), (340, 360, (255, 215, 235), ''), (44.8, 98.4, (255, 215, 235), 'lent V90'), (230.5, 305, (255, 215, 235), 'lent V90')):
    d.rectangle((X0 + a0 / 360 * XW, Y0, X0 + a1 / 360 * XW, Y0 + YH), fill=c_); d.text((X0 + a0 / 360 * XW + 3, Y0 + 3), et, fill='black', font=F)
y1 = Y0 + YH - 1 / top * YH; d.line([(X0, y1), (X0 + XW, y1)], fill=(0, 0, 0), width=1)
for k, L in LL.items():
    t = np.arange(NT) * DT; pts = [(X0 + tt / 360 * XW, Y0 + YH - min(v / top, 1) * YH) for tt, v in zip(t[::10], L[::10])]; d.line(pts, fill=col[k], width=2)
for i, k in enumerate(LL): d.text((X0 + 10 + i * 90, Hd - 60), k, fill=col[k], font=FB)
for t in range(0, 361, 30): d.text((X0 + t / 360 * XW - 10, Y0 + YH + 6), f'{t}°', fill='black', font=F)
for v in range(0, 5): d.text((20, Y0 + YH - v / top * YH - 8), f'{v}', fill='black', font=F)
d.text((X0, 8), "Índex de lent: textura arran del limbe (2,5–10 px) estirada al llarg del radi, relativa a la de 16–30 px (1 = igual; més alt = més lent)", fill='black', font=FB)
S.save(SORT / 'LAMINA_C1_index_lent.png')
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
im = lambda A: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(A * 255, 0, 255))), TR)
for a0 in range(0, 360, 60):
    c0, c1 = int(a0 / DT), int((a0 + 60) / DT); z = 3; h_ = len(DS); w_ = (c1 - c0)
    S2 = Image.new('RGB', (w_ // 2 * 1 + 10, 3 * (h_ // 4 * z + 26) + 10), 'white'); d2 = ImageDraw.Draw(S2)
    for i, k in enumerate(POL):
        A = POL[k][::-1, c0:c1][::1, ::-1]                                    # d cap amunt; azimut creixent cap a l'esquerra (com al cel)
        img = im(A).resize((w_ // 2, h_ // 4 * z), Image.LANCZOS); S2.paste(img, (5, 5 + i * (h_ // 4 * z + 26) + 22))
        d2.text((8, 5 + i * (h_ // 4 * z + 26)), f'{k} · azimut {a0 + 60}° ← {a0}° · d de −3 (baix) a 30 px (dalt), radi ×3', fill='black', font=F)
    S2.save(SORT / f'LAMINA_C2_polars_{a0:03d}_{a0 + 60:03d}.png')
log('fet')
