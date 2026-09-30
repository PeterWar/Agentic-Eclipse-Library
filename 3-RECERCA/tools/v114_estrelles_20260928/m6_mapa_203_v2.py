"""m6 · V114 (Claude, 28-09-2026, nit; Pere: «que el text sigui llegible i que estigui relativament ben alineat amb l'estrella, sobretot quan
n'hi ha diverses de juntes»): capa 203 «Mapa de N estrelles · HIP i TYC» amb els MATEIXOS cercles, colors, tipus de lletra i llegenda que la V65
(s24_star_package.py), però amb una COL·LOCACIÓ D'ETIQUETES nova. L'antiga només evitava que dues etiquetes es trepitgessin; no mirava els cercles de
les altres estrelles ni a quina estrella quedava més a prop cada etiqueta (S23/S47, S36/S45).
Regles, per ordre de preferència: a la dreta alineada amb l'estrella, a l'esquerra alineada, a sobre o a sota centrada, en diagonal; primer
tocant el cercle (22 px del centre) i, si no hi cap, més lluny amb una línia guia. Una posició només és vàlida si:
  · no surt del llenç ni entra a la llegenda;
  · no trepitja cap altra etiqueta ni cap cercle (el propi ni els altres), amb 3 px de marge;
  · ASSOCIACIÓ: el punt de l'etiqueta més proper a la seva estrella és almenys 1,6× (+6 px) més a prop d'ella que de qualsevol altra;
  · la línia guia, si n'hi ha, no passa a menys de 18 px de cap altra estrella.
Primer es col·loquen les estrelles amb la veïna més propera. Text: Arial 32 amb contorn negre de 3 px (V65: 30 i 2).
Sortida: npz (R, G, B, M) per a m3_munta_v114.py --c203, i un JSON amb la posició i les comprovacions de cada etiqueta.
Ús: m6_mapa_203_v2.py <sortida.npz> --cataleg <CATALEG_ACCEPTAT_V114.json> --llegenda <json>"""
import json, argparse
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
ap = argparse.ArgumentParser(); ap.add_argument('sortida'); ap.add_argument('--cataleg', required=True); ap.add_argument('--llegenda', required=True); A = ap.parse_args()
stars = json.loads(Path(A.cataleg).read_text())['stars']; H, W = 7506, 10551
lg = json.loads(Path(A.llegenda).read_text()); LLEGENDA = (180, 6630, 1940, 7245)
im = Image.new('RGBA', (W, H)); draw = ImageDraw.Draw(im)
font = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 32); head = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 48)
small = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 31)
P = np.array([[s['x'], s['y']] for s in stars]); RC, MARGE, FACTOR = 14, 3, 1.6
def solapa(a, b, m=MARGE): return not (a[2] + m <= b[0] or b[2] + m <= a[0] or a[3] + m <= b[1] or b[3] + m <= a[1])
def punt_proper(bb, x, y): return min(max(x, bb[0]), bb[2]), min(max(y, bb[1]), bb[3])
def dist_seg(p, a, b):
    p, a, b = map(np.asarray, (p, a, b)); t = np.clip(np.dot(p - a, b - a) / max(np.dot(b - a, b - a), 1e-9), 0, 1); return float(np.hypot(*(a + t * (b - a) - p)))
def disc_toca(bb, cx, cy, r):
    px, py = punt_proper(bb, cx, cy); return np.hypot(px - cx, py - cy) < r
nn = [float(np.sort(np.hypot(P[:, 0] - s['x'], P[:, 1] - s['y']))[1]) for s in stars]
ordre = sorted(range(len(stars)), key=lambda i: nn[i])
placed, rebut = [], {}
for i in ordre:
    s = stars[i]; x, y = s['x'], s['y']; col = (255, 221, 68, 255) if s['HIP'] else (104, 245, 155, 255)
    txt = s['id'] + (' · HIP ' + str(s['HIP']) if s['HIP'] else '') + (' · doble no resolta' if s['unresolved_blend'] else '')
    b = draw.textbbox((0, 0), txt, font=font, stroke_width=3); w, h = b[2] - b[0], b[3] - b[1]
    cands = []
    for g in (22, 34, 50, 70, 95):
        k = g * 0.72
        for pref, (l, t) in enumerate([(x + g, y - h / 2), (x - g - w, y - h / 2), (x - w / 2, y - g - h), (x - w / 2, y + g),
                                       (x + k, y - k - h), (x - k - w, y - k - h), (x + k, y + k), (x - k - w, y + k)]):
            cands.append((g / 10 + pref * 1.5 + (8 if g > 34 else 0), g, (l, t, l + w, t + h)))
    cands.sort(key=lambda c: c[0]); tria = None
    for factor in (FACTOR, 1.3, 1.1):
        for cost, g, bb in cands:
            if bb[0] < 2 or bb[1] < 2 or bb[2] > W - 2 or bb[3] > H - 2 or solapa(bb, LLEGENDA, 6): continue
            if any(solapa(bb, q) for q in placed): continue
            if any(disc_toca(bb, P[j, 0], P[j, 1], RC + 2 + MARGE) for j in range(len(stars))): continue
            ax, ay = punt_proper(bb, x, y); d0 = np.hypot(ax - x, ay - y); dj = np.hypot(P[:, 0] - ax, P[:, 1] - ay); dj[i] = 1e9
            if dj.min() < factor * d0 + 6: continue
            guia = bool(d0 > 30)
            if guia and any(dist_seg(P[j], (x, y), (ax, ay)) < 18 for j in range(len(stars)) if j != i): continue
            tria = (bb, g, guia, (ax, ay), float(d0), float(dj.min()), factor); break
        if tria: break
    assert tria, f'cap posició vàlida per a {s["id"]}'
    bb, g, guia, (ax, ay), d0, dmin, factor = tria; placed.append(bb)
    rebut[s['id']] = dict(text=txt, caixa=[round(v, 1) for v in bb], distancia_etiqueta_px=round(d0, 1), distancia_altra_estrella_px=round(dmin, 1), factor=factor, guia=guia)
    if guia:
        ux, uy = (ax - x) / d0, (ay - y) / d0; x0, y0 = x + ux * (RC + 3), y + uy * (RC + 3)
        draw.line((x0, y0, ax - ux * 3, ay - uy * 3), fill=(0, 0, 0, 220), width=6); draw.line((x0, y0, ax - ux * 3, ay - uy * 3), fill=col, width=2)
    draw.text((bb[0] - b[0], bb[1] - b[1]), txt, font=font, fill=col, stroke_width=3, stroke_fill=(0, 0, 0, 235))
for s in stars:
    x, y = s['x'], s['y']; col = (255, 221, 68, 255) if s['HIP'] else (104, 245, 155, 255)
    draw.ellipse((x - 14, y - 14, x + 14, y + 14), outline=(0, 0, 0, 200), width=6); draw.ellipse((x - 14, y - 14, x + 14, y + 14), outline=col, width=3)
draw.rounded_rectangle(LLEGENDA, radius=28, fill=(10, 17, 20, 225), outline=(180, 192, 188, 220), width=2)
draw.text((225, 6675), lg['titol'], font=head, fill=(238, 242, 239, 255))
for k, line in enumerate(lg['linies']): draw.text((225, 6760 + 63 * k), line, font=small, fill=(225, 231, 225, 255))
ann = np.asarray(im); rgb = ann[..., :3].astype('uint16') * 257; M = ann[..., 3].astype('uint16') * 257
np.savez_compressed(A.sortida, R=rgb[..., 0], G=rgb[..., 1], B=rgb[..., 2], M=M)
Path(A.sortida).with_suffix('.json').write_text(json.dumps(dict(etiquetes=rebut, relaxades=[k for k, v in rebut.items() if v['factor'] < FACTOR], amb_guia=[k for k, v in rebut.items() if v['guia']]), indent=1, ensure_ascii=False))
print('etiquetes', len(rebut), 'amb guia', sum(v['guia'] for v in rebut.values()), 'relaxades', [k for k, v in rebut.items() if v['factor'] < FACTOR])
for k in ('S23', 'S47', 'S36', 'S45'): print(k, rebut[k])
