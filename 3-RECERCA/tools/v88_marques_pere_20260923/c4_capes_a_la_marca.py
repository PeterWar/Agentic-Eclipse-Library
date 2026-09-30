"""c4 · Cada capa per separat a les marques de limb (6:1, cadascuna amb el seu estirament): color i alfa efectiva (alfa × màscara × opacitat)
de la base 3, els ràsters dels filtres visibles, l'alfa de l'Earthshine V88 i els pisos compostos. Sortida: LAMINA_M4_capes_a_la_marca.png."""
from vm_comu import *
from psb69 import PSB
from vm_compost import capa_box
from PIL import Image, ImageDraw, ImageFont
claim()
z = np.load(SORT / 'pisos_caixa.npz'); BX = tuple(int(v) for v in z['caixa']); x0, y0, x1, y1 = BX
p = PSB(str(PSB_PERE)); cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
M = json.loads((SORT / 'MARQUES_V88.json').read_text()); llocs = [(g['nom'], cc) for g in M['grups_de_to'] for cc in g['components'] if cc['d_limbe_px'][1] < 10]
def lum(C): return 0.3 * C[..., 0] + 0.59 * C[..., 1] + 0.11 * C[..., 2]
panells = []
for lid in [3, 41, 42, 51, 56, 258, 76, 262, 96]:
    mode, F, a = capa_box(p, lid, BX); panells.append((f'{lid} color', lum(F), False)); panells.append((f'{lid} alfa ef.', a, True))
for k in ['+_filtres', '+_Earthshine_258', '+_96_i_224', 'natiu_(amb_ajustos)']:
    panells.append((k.replace('_', ' '), lum(z[k].astype(np.float32) / 65535), False))
try: F_ = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 12); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 17)
except Exception: F_ = FB = ImageFont.load_default()
cw, zf, ncol = 44, 5, 11; nfil = -(-len(panells) // ncol)
S = Image.new('RGB', (ncol * (cw * zf + 4), 34 + len(llocs) * nfil * (cw * zf + 16)), 'white'); dr = ImageDraw.Draw(S)
dr.text((6, 8), 'Capa per capa a les marques de limb (5:1). Colors: lluminància estirada p1–p99 a la finestra; alfes: 0 negre, 1 blanc. Cercle vermell = limbe de presentació (R 453)', fill='black', font=FB)
for j, (nom, cc) in enumerate(llocs):
    az, dm = cc['azimut'][1], cc['d_limbe_px'][1]; t = np.radians(az); px, py = cx + (R + dm) * np.cos(t) - x0, cy - (R + dm) * np.sin(t) - y0
    ax0, ay0 = int(px - cw / 2), int(py - cw / 2)
    for i, (et, A, es_alfa) in enumerate(panells):
        c = A[ay0:ay0 + cw, ax0:ax0 + cw]
        if es_alfa: v = np.clip(c, 0, 1)
        else: lo, hi = np.percentile(c, [1, 99]); v = np.clip((c - lo) / max(hi - lo, 1e-6), 0, 1)
        im = Image.fromarray(np.uint8(v * 255)).convert('RGB').resize((cw * zf, cw * zf), Image.NEAREST); di = ImageDraw.Draw(im)
        # limbe de presentació
        tt = np.linspace(0, 2 * np.pi, 2000); lx = (cx + R * np.cos(tt) - x0 - ax0 + 0.5) * zf - 0.5; ly = (cy - R * np.sin(tt) - y0 - ay0 + 0.5) * zf - 0.5
        pts = [(a_, b_) for a_, b_ in zip(lx, ly) if 0 <= a_ < cw * zf and 0 <= b_ < cw * zf]
        for q in pts[::3]: di.point(q, fill=(255, 0, 0))
        r, cc_ = divmod(i, ncol); X = cc_ * (cw * zf + 4); Y = 34 + (j * nfil + r) * (cw * zf + 16)
        S.paste(im, (X, Y + 14)); dr.text((X + 2, Y), f'{et} · {az:.0f}°', fill='black', font=F_)
S.save(SORT / 'LAMINA_M4_capes_a_la_marca.png'); log('làmina M4 %s' % (S.size,))
