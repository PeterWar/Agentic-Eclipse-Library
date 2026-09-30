"""c3 · On neix cada marca: el compost acumulat pis per pis (de baix a dalt) a la caixa de la meitat esquerra de la Lluna, i el perfil radial
de la lluminància a cada marca. Pisos: base (3) · + filtres visibles · + Earthshine V88 (258) · + fotos 76 (Aclarir) · + 262 (Lluminositat, de Pere)
· + 96 i 224 = tot sense capes d'ajust; i el compost natiu (amb les capes d'ajust).
Sortida: pisos_caixa.npz, PISOS_PERFILS.json, LAMINA_M2_pisos.png, LAMINA_M3_perfils.png."""
from vm_comu import *
from psb69 import PSB
from vm_compost import comp, capa_box
import tifffile, io
from PIL import Image, ImageCms, ImageDraw, ImageFont
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
claim()
BX = (4780, 3230, 5420, 4300); x0, y0, x1, y1 = BX; h, w = y1 - y0, x1 - x0
p = PSB(str(PSB_PERE)); vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left']]
log('capes visibles amb píxels (de baix a dalt): %s' % vis)
FILTRES = [i for i in vis if i in (41, 42, 47, 49, 51, 45, 46, 55, 56)]
pisos = [('base 3', [3]), ('+ filtres', FILTRES), ('+ Earthshine 258', [258]), ('+ 76 Aclarir', [76]), ('+ 262 Lluminositat', [262]), ('+ 96 i 224', [96, 224])]
capes = {i: capa_box(p, i, BX) for i in vis if i in sum([l for _, l in pisos], [])}
acc = []; res = {}
for nom, ids in pisos:
    acc += [capes[i] for i in ids]; C, a = comp(acc, h, w); res[nom] = C; log('pis %s' % nom)
nat = p.composite()[y0:y1, x0:x1, :3].astype(np.float32) / 65535; res['natiu (amb ajustos)'] = nat
np.savez_compressed(SORT / 'pisos_caixa.npz', caixa=np.array(BX), **{k.replace(' ', '_'): (v * 65535).round().astype(np.uint16) for k, v in res.items()})
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']
yy, xx = np.mgrid[y0:y1, x0:x1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
M = json.loads((SORT / 'MARQUES_V88.json').read_text()); llocs = [(g['nom'], cc) for g in M['grups_de_to'] for cc in g['components']]
def lum(C): return 0.3 * C[..., 0] + 0.59 * C[..., 1] + 0.11 * C[..., 2]
perf = {}; fig, axs = plt.subplots(len(llocs), 1, figsize=(10, 3.2 * len(llocs)))
for (nom, cc), ax in zip(llocs, axs):
    a0, a1 = cc['azimut'][0], cc['azimut'][2]; sel = (th >= a0) & (th <= a1); db = np.round(d * 2) / 2; clau = f"{nom} az {cc['azimut'][1]:.0f}"; perf[clau] = {}
    for k, C in res.items():
        L = lum(C); xs = np.arange(-6, 45.5, 0.5); ys = [float(np.median(L[sel & (db == v)])) if (sel & (db == v)).sum() > 3 else np.nan for v in xs]
        perf[clau][k] = dict(d=xs.tolist(), L=ys); ax.plot(xs, ys, label=k, lw=1.2 if 'natiu' not in k else 2.2)
    ax.axvspan(cc['d_limbe_px'][0], cc['d_limbe_px'][2], color='k', alpha=0.08); ax.set_title(f"{clau}° · marca a d {cc['d_limbe_px'][0]}..{cc['d_limbe_px'][2]} px (ombra)", fontsize=9)
    ax.set_xlabel('distància al limbe de la Lluna de presentació (px)'); ax.set_ylabel('lluminància (mediana)'); ax.grid(alpha=0.3)
axs[0].legend(fontsize=7, ncol=4); fig.tight_layout(); fig.savefig(SORT / 'LAMINA_M3_perfils.png', dpi=110); plt.close(fig)
desa_json('PISOS_PERFILS.json', perf)
# làmina de pisos: cada marca, 7 pisos a 3:1, estirats amb el mateix rang per fila (percentils del compost sense ajustos)
icc = tifffile.TiffFile(V88D / 'vistes/V88_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
try: F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 13); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 18)
except Exception: F = FB = ImageFont.load_default()
cw, zf = 100, 3; noms = list(res); S = Image.new('RGB', (len(noms) * (cw * zf + 6), 36 + len(llocs) * (cw * zf + 20)), 'white'); dr = ImageDraw.Draw(S)
dr.text((6, 8), 'Pis per pis a cada marca (3:1). Cada fila, el mateix estirament (p1–p99,5 del compost sense ajustos); el natiu, amb el seu to', fill='black', font=FB)
for j, (nom, cc) in enumerate(llocs):
    az, dm = cc['azimut'][1], cc['d_limbe_px'][1]; t = np.radians(az); px, py = cx + (R + dm) * np.cos(t) - x0, cy - (R + dm) * np.sin(t) - y0
    cx0, cy0 = int(px - cw / 2), int(py - cw / 2); ref = lum(res['+ 96 i 224'][cy0:cy0 + cw, cx0:cx0 + cw]); lo, hi = np.percentile(ref, [1, 99.5]); y = 36 + j * (cw * zf + 20)
    for i, k in enumerate(noms):
        C = res[k][cy0:cy0 + cw, cx0:cx0 + cw]
        im = ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(C * 255, 0, 255))), TR) if 'natiu' in k else Image.fromarray(np.uint8(np.clip((C - lo) / (hi - lo), 0, 1) * 255))
        S.paste(im.resize((cw * zf, cw * zf), Image.LANCZOS), (i * (cw * zf + 6), y + 18)); dr.text((i * (cw * zf + 6) + 2, y + 2), f'{k} · {az:.0f}°', fill='black', font=F)
S.save(SORT / 'LAMINA_M2_pisos.png'); log('fet')
