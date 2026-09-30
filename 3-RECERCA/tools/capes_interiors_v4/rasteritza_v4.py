"""Rasteritza les màscares radials de V4 a resolució completa (coordenades de V4 = V3 − (1,1)), compon la imatge i en fa la QA.
Escriu v4/masks/<idx>_mask.npy (uint16, bbox de la capa), v4/compost_rgb16.npy, v4/compost_gain_rgb16.npy, v4/gain_layer.npz, previews i v4/qa.json."""
import numpy as np, json, os
from scipy import ndimage as ndi, special
from PIL import Image
os.makedirs('v4/masks', exist_ok=True)
meta = json.load(open('v3/meta.json')); nL = len(meta['layers'])
D = np.load('v4/disseny.npz'); rr = D['rr']; ladder = [int(i) for i in D['ladder']]
RS = 446.15
SUN4 = (4021.89 - 1.0, 2738.66 - 1.0)
MOON4 = (4035.8 - 1.0, 2737.3 - 1.0); MOON_R = 451.5; R_DISK = MOON_R - 14.0; SIG_DISK = 4.0
FRAME = (457, 463, 7417, 5103)            # (l, t, r, b) del marc 6960×4640 a V4 per a Capa 4/5 i DNG
W_CANVAS, H_CANVAS = 7648, 5353
# coordenades de document del marc
yy, xx = np.mgrid[FRAME[1]:FRAME[3], FRAME[0]:FRAME[2]].astype(np.float32)
r_sun = np.hypot(xx - SUN4[0], yy - SUN4[1]) / RS
r_moon = np.hypot(xx - MOON4[0], yy - MOON4[1])
disk = 0.5 * (1 + special.erf((r_moon - R_DISK) / (SIG_DISK * np.sqrt(2)))).astype(np.float32)   # 0 dins del disc, 1 fora
del r_moon
def prof(m):  # perfil 1-D → 2-D (constant fora del rang)
    return np.interp(r_sun, rr, m, left=m[0], right=m[-1]).astype(np.float32)
# nucli de la protuberància / creixent: on Capa 5 (1/125) està saturada (canal màxim 0,60→0,85), només al limbe (0,95–1,12 R☉),
# s'hi obren Capa 4 i Capa 5 perquè es vegi la 1/3200 (perles)
files = sorted(__import__('glob').glob('v3/*_rgb.npy')); files = [f for f in files if 'merged' not in f]
a5 = np.load(files[2], mmap_mode='r'); l5, t5 = meta['layers'][2]['bbox'][:2]
mx5 = np.asarray(a5[464 - t5:5104 - t5, 458 - l5:7418 - l5], np.float32).max(-1) / 65535.
core = np.clip((mx5 - 0.60) / 0.25, 0, 1); core = core * core * (3 - 2 * core)
core *= ((r_sun > 0.95) & (r_sun < 1.12)).astype(np.float32)
core = ndi.gaussian_filter(core, 1.0).astype(np.float32)
print('nucli del creixent: píxels amb core>0,5:', int((core > 0.5).sum()), flush=True)
del mx5
masks = {}
for i in ladder:
    m = prof(D[f'm{i}']) * disk
    if i == 1: m = np.ones_like(m)               # Capa 4 (1/500) és la base: màscara blanca (opaca)
    masks[i] = m
    np.save(f'v4/masks/{i:02d}_mask.npy', np.clip(np.round(m * 65535), 0, 65535).astype(np.uint16))
    print('màscara', i, meta['layers'][i]['name'][:12], 'min/max', float(m.min()), float(m.max()), 'mitjana', float(m.mean()), flush=True)
# màscara de la capa 12 (perles, 1/3200): el seu mapa d'ús = interior del disc lunar + nucli del creixent (+ la fila/columna
# del marge que només cobreix ella); la capa és a (456,462), un píxel amunt/esquerra del marc
m12 = np.ones(r_sun.shape, np.float32)
m12[1:, 1:] = np.clip((1 - disk) + core, 0, 1)[:-1, :-1]
masks[0] = m12
np.save('v4/masks/00_mask.npy', np.clip(np.round(m12 * 65535), 0, 65535).astype(np.uint16))
print('màscara 12 (perles): mitjana', float(m12.mean()), flush=True)
# ---- compost a resolució completa (només el marc: fora no hi ha res)
h, w = r_sun.shape
C = np.zeros((h, w, 3), np.float32)
for i in range(1, nL):
    info = meta['layers'][i]; l0, t0 = info['bbox'][:2]
    a = np.load(files[i], mmap_mode='r')
    sub = np.asarray(a[464 - t0:5104 - t0, 458 - l0:7418 - l0], np.float32) / 65535.
    assert sub.shape == (h, w, 3), (sub.shape, h, w)
    m = masks[i][..., None]
    C = C * (1 - m) + sub * m
    print('composta', i, info['name'][:12], flush=True)
# la 12 (perles) a dalt: la capa és a (456,462); el marc [463:5103, 457:7417] = files/cols 1.. de la capa; l'última fila/col del marc no la cobreix
a12 = np.load(files[0], mmap_mode='r')
sub12 = np.zeros((h, w, 3), np.float32); sub12[:h - 1, :w - 1] = np.asarray(a12[1:, 1:], np.float32) / 65535.
m = np.zeros((h, w), np.float32); m[:h - 1, :w - 1] = m12[1:, 1:]
C = C * (1 - m[..., None]) + sub12 * m[..., None]
print('composta 0 (perles, a dalt)', flush=True)
np.save('v4/compost_rgb16.npy', np.clip(np.round(C * 65535), 0, 65535).astype(np.uint16))
# ---- capa de guany radial (Color Dodge): g = T_V3/T, limitada perquè p95 del compost × g ≤ 0,92; a 1 més enllà de 1,75 R☉
C4pol = np.load('v4/C4_polar.npy'); rr_in = np.load('v3/polar.npz')['rr']
thp = np.load('v3/polar.npz')['th']; noprot = ~((thp > 160) & (thp < 178))
mxpol = np.max(C4pol, axis=0)[:, noprot]
p95 = np.percentile(mxpol, 99.5, axis=1)     # (nom històric p95: ara és el percentil 99,5 del canal màxim, sense la protuberància)
T3 = D['T3']; T = D['T']
# T3 suau (el perfil V3) sobre rr
lnr = np.log(rr); g_ = np.linspace(lnr[0], lnr[-1], 4000)
T3s = np.interp(lnr, g_, ndi.gaussian_filter1d(np.interp(g_, lnr, np.where(rr < 1.06, T3[np.searchsorted(rr, 1.06)], T3)), 0.04 / (g_[1] - g_[0]), mode='nearest'))
gain = np.clip(T3s / np.maximum(T, 1e-6), 1.0, None)
p95_full = np.interp(rr, rr_in, p95, right=p95[-1])
gain = np.minimum(gain, 0.97 / np.maximum(p95_full, 1e-6))
gain = np.maximum(gain, 1.0)
# apagat suau cap a 1 entre 1,6 i 1,75 R☉ (on T ja és V3 és ~1 de tota manera)
fade = np.clip((1.75 - rr) / 0.15, 0, 1); fade = fade * fade * (3 - 2 * fade)
gain = 1 + (gain - 1) * fade
# suavitza en ln r
gain = np.interp(lnr, g_, ndi.gaussian_filter1d(np.interp(g_, lnr, gain), 0.02 / (g_[1] - g_[0]), mode='nearest'))
gain = np.maximum(gain, 1.0)
v = 1 - 1 / gain                    # valor del Color Dodge
np.savez('v4/gain_layer.npz', rr=rr, gain=gain, v=v, p95=p95_full, T3s=T3s)
print('guany radial: ', {float(r): round(float(np.interp(r, rr, gain)), 3) for r in (1.0, 1.05, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8)})
# raster del guany: caixa al voltant del Sol de radi 1,8 R☉
RG = int(np.ceil(1.8 * RS)); gx0, gy0 = int(round(SUN4[0])) - RG, int(round(SUN4[1])) - RG
gyy, gxx = np.mgrid[gy0:gy0 + 2 * RG, gx0:gx0 + 2 * RG].astype(np.float32)
gr = np.hypot(gxx - SUN4[0], gyy - SUN4[1]) / RS
V = np.interp(gr, rr, v, left=v[0], right=0.0).astype(np.float32)
# dins de la Lluna no cal guany (r_moon < R_DISK): deixem v tal com surt (dins la Lluna T≈const i g≈1 a r<1: comprova)
np.savez('v4/gain_raster.npz', V=V, x0=gx0, y0=gy0)
# compost amb el guany aplicat (per a la previsualització/QA)
Cg = C.copy()
ys, xs = gy0 - FRAME[1], gx0 - FRAME[0]
sub = Cg[ys:ys + 2 * RG, xs:xs + 2 * RG]
Cg[ys:ys + 2 * RG, xs:xs + 2 * RG] = np.clip(sub / np.maximum(1 - V[..., None], 1e-6), 0, 1)
np.save('v4/compost_gain_rgb16.npy', np.clip(np.round(Cg * 65535), 0, 65535).astype(np.uint16))
print('fracció de píxels retallats (>0,999) dins 1,0–1,3 R☉ amb guany (inclou la protuberància):', float(((Cg.max(-1) > 0.999) & (r_sun > 1.0) & (r_sun < 1.3)).sum() / ((r_sun > 1.0) & (r_sun < 1.3)).sum()))
# ---- previsualitzacions: V3 (merged) i V4 (sense i amb guany), mateix estirament (gamma 1/2,2 del valor codificat... ja és codificat: mostra tal qual), 1/4
mer = np.load('v3/merged_rgb.npy', mmap_mode='r')
def prev(arr16, name):
    a = np.asarray(arr16[::4, ::4], np.float32) / 65535.
    Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(name)
prev(np.asarray(mer[FRAME[1]+1:FRAME[3]+1, FRAME[0]+1:FRAME[2]+1]), 'v4/prev_V3.png')
prev(np.load('v4/compost_rgb16.npy', mmap_mode='r'), 'v4/prev_V4_nu.png')
prev(np.load('v4/compost_gain_rgb16.npy', mmap_mode='r'), 'v4/prev_V4_guany.png')
print('fet')
