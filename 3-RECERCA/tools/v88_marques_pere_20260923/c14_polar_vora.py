"""c14 · La vora esquerra desplegada en polars (θ 90–250°, d −6..24 px, 0,1° × 0,25 px): el verd de la dada d'un instant (E, entrada dels filtres
a la franja) dividit pel seu perfil radial mitjà per sectors de 20° (per veure-hi l'estructura azimutal), el mateix sense dividir, R/G (cromosfera),
l'alfa de la Lluna mostrada (258), l'NRGF 41 de la V88 i el compost natiu desat. Per decidir si la pujada dels primers 6–7 px és llisa (desenfocament)
o granulada (muntanyes i valls de la vora lunar). Sortida: LAMINA_M14_polar_vora.png."""
from vm_comu import *
from psb69 import PSB
import cv2
from PIL import Image, ImageDraw, ImageFont
claim()
Q = np.load(V88D / 'A3A_franja_un_instant.npz'); by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; E = Q['E']
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
T0, T1, DT = 90.0, 250.0, 0.1; D0, D1, DD = -6.0, 24.0, 0.25
tt = np.arange(T0, T1, DT); dd = np.arange(D0, D1, DD); TT, DDg = np.meshgrid(np.radians(tt), dd)
X = (cx + (R + DDg) * np.cos(TT)).astype(np.float32); Yc = (cy - (R + DDg) * np.sin(TT)).astype(np.float32)
def polar(A, x0, y0): return cv2.remap(A.astype(np.float32), X - x0, Yc - y0, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
G = polar(E[..., 1], bx0, by0); RG = polar(E[..., 0], bx0, by0) / np.maximum(G, 1e-6)
p = PSB(str(PSB_PERE)); L = p.layer(258); a258 = p.channel(258, -1); A = polar(a258[0].astype(np.float32) / 65535, *a258[1])
n41 = np.load(V88D / 'filtres_finals/P01_NRGF_u16.npy', mmap_mode='r'); bb = (3300, 4300, 4750, 5500)
N = polar(np.asarray(n41[bb[0]:bb[1], bb[2]:bb[3]]).astype(np.float32) / 65535, bb[2], bb[0])
comp = p.composite()[bb[0]:bb[1], bb[2]:bb[3], :3].astype(np.float32) / 65535; C = np.stack([polar(comp[..., c], bb[2], bb[0]) for c in range(3)], -1)
# perfil radial mitjà per sectors de 20° (per treure la pujada i veure l'estructura azimutal)
Gs = G.copy(); nsec = int((T1 - T0) / 20)
for s in range(nsec):
    j0, j1 = int(s * 20 / DT), int((s + 1) * 20 / DT); prof = np.nanmedian(G[:, j0:j1], 1); Gs[:, j0:j1] = G[:, j0:j1] / prof[:, None]
def v(A_, lo, hi): return np.uint8(np.clip(np.nan_to_num((A_ - lo) / (hi - lo)), 0, 1) * 255)
k = np.isfinite(G) & (DDg > 0)
pan = [('verd de la dada d\'un instant (E)', v(G, *np.nanpercentile(G[k], [1, 99]))), ('el mateix / perfil mitjà per 20° (estructura azimutal)', v(Gs, 0.7, 1.3)),
       ('R/G (vermell = cromosfera)', v(RG, 1.5, 4.5)), ('alfa de la Lluna mostrada (258)', v(A, 0, 1)), ('NRGF 41 de la V88', v(N, *np.nanpercentile(N[k], [1, 99]))),
       ('compost natiu desat (lluminància)', v(0.3 * C[..., 0] + 0.59 * C[..., 1] + 0.11 * C[..., 2], *np.nanpercentile((0.3 * C[..., 0] + 0.59 * C[..., 1] + 0.11 * C[..., 2])[k], [1, 99.5])))]
try: F_ = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 18)
except Exception: F_ = FB = ImageFont.load_default()
h_, w_ = G.shape; zy = 4
S = Image.new('RGB', (w_ + 60, 40 + len(pan) * (h_ * zy + 26)), 'white'); dr = ImageDraw.Draw(S)
dr.text((6, 8), f'Vora esquerra en polars: azimut {T0:.0f}° (esquerra) → {T1:.0f}° (dreta), 0,1°/px; distància al limbe {D0:.0f}..{D1:.0f} px (de dalt a baix), ×4 en vertical. Línies: d = 0 i d = 6 px', fill='black', font=FB)
for i, (et, im) in enumerate(pan):
    y0 = 40 + i * (h_ * zy + 26); pil = Image.fromarray(im).resize((w_, h_ * zy), Image.NEAREST).convert('RGB'); di = ImageDraw.Draw(pil)
    for dl in (0, 6): yl = int((dl - D0) / DD * zy); di.line([(0, yl), (w_, yl)], fill=(255, 0, 0) if dl == 0 else (0, 160, 255))
    for az in range(100, 250, 10): xl = int((az - T0) / DT); di.line([(xl, 0), (xl, 6)], fill=(255, 255, 0))
    S.paste(pil, (0, y0 + 22)); dr.text((4, y0 + 3), et + '   (marques de 10° a dalt: 100°, 110°, …)', fill='black', font=F_)
S.save(SORT / 'LAMINA_M14_polar_vora.png'); log('fet %s' % (S.size,))
