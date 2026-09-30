"""c6 · Filtres V93 (a4v nivell + a5d línies coherents) contra els de la V92, al compost EMULAT de la V92 de Pere (01:34): índex de lent,
índex de línies (detall radial coherent), textura (energia del detall fi) i nivell, per sector; làmines a 5:1 a les marques grises, verdes i a
les línies de la V88. Sortida: C6_AVALUACIO.json i LAMINA_C6_*.png."""
from v93_comu import *
from psb69 import PSB
from vm_compost import comp, capa_box
import cv2, tifffile, io
from scipy.ndimage import gaussian_filter1d, uniform_filter1d
from PIL import Image, ImageCms, ImageDraw, ImageFont
claim(); BX = (4600, 3000, 6150, 4550); W_, H_ = BX[2] - BX[0], BX[3] - BX[1]; cx, cy, R = GEO['cx'] - BX[0], GEO['cy'] - BX[1], GEO['R']
DT = 0.05; NT = int(360 / DT); DR = 0.25; DS = np.arange(-3, 30.001, DR); TS = np.radians((np.arange(NT) + 0.5) * DT)
TT, DD = np.meshgrid(TS, DS); MX = (cx + (R + DD) * np.cos(TT)).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT)).astype(np.float32)
ds_arc = np.radians(DT) * (R + DS)[:, None]; far = (DS >= 16) & (DS <= 30); t = np.arange(NT) * DT
SECT = {'gris_80_96': [(80, 96)], 'gris_244_307': [(244, 307)], 'verd_193_227': [(193, 227)], 'linies_104_152': [(104, 152)], 'dreta_320_20': [(320, 360), (0, 20)]}
sel = lambda v: np.concatenate([np.flatnonzero((t >= a) & (t < b)) for a, b in v])
def mesures(Y):
    P = cv2.remap(Y.astype(np.float32), MX, MY, cv2.INTER_LINEAR); T = P - gaussian_filter1d(P, 3.0 / ds_arc.mean(), axis=1, mode='wrap')
    Ed = (np.diff(T, axis=0) / DR) ** 2; Ed = np.vstack([Ed, Ed[-1:]]); Es = (np.diff(T, axis=1, append=T[:, :1]) / ds_arc) ** 2; Wn = int(5 / DT)
    f = lambda E, mk: uniform_filter1d(E[mk].mean(0), Wn, mode='wrap'); out = {}
    for bn, (a, b) in {'1-5': (1, 5), '5-14': (5, 14)}.items():
        mk = (DS >= a) & (DS <= b); L = (f(Ed, far) / f(Es, far)) / (f(Ed, mk) / f(Es, mk)); tex = np.sqrt(f(T ** 2, mk) / f(T ** 2, far))
        out[f'lent_{bn}'] = {k: round(float(L[sel(v)].mean()), 2) for k, v in SECT.items()}; out[f'textura_{bn}'] = {k: round(float(tex[sel(v)].mean()), 3) for k, v in SECT.items()}
    HPr = P - gaussian_filter1d(P, 4 / DR, axis=0, mode='nearest'); COH = gaussian_filter1d(HPr, 1.5 / DT, axis=1, mode='wrap'); mk = (DS >= 1) & (DS <= 10)
    out['linies_coherents_rms_1_10'] = {k: round(float(np.sqrt((COH[mk][:, sel(v)] ** 2).mean()) * 1000), 3) for k, v in SECT.items()}
    out['nivell'] = {k: [round(float(P[np.abs(DS - dd) < 0.3][:, sel(v)].mean()), 4) for dd in (1, 2, 3, 4, 6, 8, 12)] for k, v in SECT.items()}
    return out
lum = lambda C: 0.2126 * C[..., 0] + 0.7152 * C[..., 1] + 0.0722 * C[..., 2]
p = PSB(str(PSB_PERE)); vis = [L['id'] for L in p.layers if L['visible'] and L['right'] > L['left'] and L['id'] not in (239, 240, 241, 242, 243, 244, 269)]
CAPES = {i: capa_box(p, i, BX) for i in vis}; COMP = {'V92': comp([CAPES[i] for i in vis], H_, W_)[0]}
for nom, carp in (('V93', 'filtres_v93'),):
    capes = []
    for i in vis:
        if i in FILTRES: md, F_, a_ = CAPES[i]; v = np.load(SORT / carp / f'{FILTRES[i]}_u16.npy', mmap_mode='r')[BX[1]:BX[3], BX[0]:BX[2]].astype(np.float32) / 65535; capes.append((md, np.repeat(v[..., None], 3, -1), a_))
        else: capes.append(CAPES[i])
    COMP[nom] = comp(capes, H_, W_)[0]
rep = {n: mesures(lum(C)) for n, C in COMP.items()}
for k in ('lent_1-5', 'lent_5-14', 'textura_1-5', 'textura_5-14', 'linies_coherents_rms_1_10'):
    print(k, ' | '.join(f"{n}: {json.dumps(rep[n][k])}" for n in COMP), flush=True)
for s in SECT: print('nivell', s, {n: rep[n]['nivell'][s] for n in COMP})
desa_json('C6_AVALUACIO.json', rep)
icc = tifffile.TiffFile(ARREL / '4-RESULTATS/v92_20260924/vistes/V92_lluna.tif').pages[0].tags['InterColorProfile'].value
TR = ImageCms.buildTransform(ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), 'RGB', 'RGB')
im = lambda A: ImageCms.applyTransform(Image.fromarray(np.uint8(np.clip(A * 255, 0, 255))), TR)
F = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf', 15); FB = ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf', 18)
def lamina(nom, titol, files, w=70, zf=6):
    S = Image.new('RGB', (len(COMP) * (w * zf + 8), 40 + len(files) * (w * zf + 24)), 'white'); d = ImageDraw.Draw(S); d.text((6, 8), titol, fill='black', font=FB)
    for j, (az, dm) in enumerate(files):
        tt = np.radians(az); px, py = cx + (R + dm) * np.cos(tt), cy - (R + dm) * np.sin(tt); x0, y0 = int(px - w / 2), int(py - w / 2); Y0 = 40 + j * (w * zf + 24)
        for i, n in enumerate(COMP): S.paste(im(COMP[n][y0:y0 + w, x0:x0 + w]).resize((w * zf, w * zf), Image.LANCZOS), (i * (w * zf + 8), Y0 + 20)); d.text((i * (w * zf + 8) + 3, Y0 + 2), f'{n} · {az:.0f}°', fill='black', font=F)
    S.save(SORT / nom)
lamina('LAMINA_C6_gris_mirall.png', 'Marques grises (mirall) · V92 contra V93, compost EMULAT, 6:1', [(88, 4), (246, 6), (270, 4), (287, 4), (300, 4)])
lamina('LAMINA_C6_verd_i_linies.png', 'Marques verdes (textura) i línies de la V88 · V92 contra V93, compost EMULAT, 6:1', [(200, 8), (219, 6), (112, 5), (136, 5), (211, 5), (223, 5)])
log('fet')
