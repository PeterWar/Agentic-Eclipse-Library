"""Detall exterior TANGENCIAL (només azimutal) sobre la base APILAT VORESNETES.

El DoG isotròpic feia halos on acaben els lòbuls de la corona (banda de 100–280 px: +1,9 % a 5,4–5,8 R☉ al
sector dret i un tall net a 6,0). Aquí el filtre només actua AL LLARG DE L'AZIMUT a cada radi (coordenades
polars): realça plomalls contra forats sense diferenciar mai en r → cap arc, cap anell, cap halo radial, i la
mitjana azimutal a cada radi es conserva exactament. Bandes en graus (a 4 R☉, 1° = 31 px):
  fina 0,6–2°, mitjana 2–6°, gruixuda 6–16°. Suavitzat radial previ σ 4 px (soroll). Coring 1,5 σ.
  Rampa radial 3,2 → 4,4 R☉ (la corona interior no es toca). Estrelles fora del detall.
Sortides: TANGENCIAL_SUAU / _FORT (cuits) i PASSALT.
"""
import os, sys, json
import numpy as np
from scipy import ndimage as ndi
import tifffile
from PIL import Image

OUTDIR = os.path.expanduser('~/Downloads/Encaixada_2026-08-18/APILAT')
ICC = open('perfil.icc', 'rb').read()
T, B, Lm, Rm = 550, 250, 600, 300
H0, W0 = 4553, 6748
H, W = H0 + T + B, W0 + Lm + Rm
sl = (slice(T, T + H0), slice(Lm, Lm + W0))
sc = np.load('similitud_sony_canvas.npy'); CX, CY = sc[2] + Lm, sc[3] + T
RS = 446.15
base = np.load('fit_ext_VORESNETES_APILAT.npy')
L = base.mean(-1)
yy, xx = np.mgrid[0:H, 0:W]
r = (np.hypot(xx - CX, yy - CY) / RS).astype(np.float32)
th = np.degrees(np.arctan2(-(yy - CY), xx - CX)).astype(np.float32)
inside = np.zeros((H, W), bool); inside[sl] = True

# --- reixa polar --------------------------------------------------------------------
R0, R1, DR = 2.4, 8.6, 2.0 / RS          # r en R☉, pas de 2 px
DTH = 0.05                                 # graus
rs = np.arange(R0, R1, DR); ths = np.arange(-180, 180, DTH)
RR, TT = np.meshgrid(rs, ths, indexing='ij')
PX = CX + RR * RS * np.cos(np.radians(TT)); PY = CY - RR * RS * np.sin(np.radians(TT))
Lp = ndi.map_coordinates(L, [PY, PX], order=1, mode='constant', cval=np.nan)
valid = np.isfinite(Lp) & (Lp > 0)
Lp0 = np.nan_to_num(Lp)
print('reixa polar', Lp.shape, ' vàlid', valid.mean())
# suavitzat radial previ (σ 4 px = 2 files) amb convolució normalitzada
vf = valid.astype(np.float32)
num = ndi.gaussian_filter1d(Lp0 * vf, 2.0, axis=0, mode='nearest'); den = ndi.gaussian_filter1d(vf, 2.0, axis=0, mode='nearest')
Ls = np.where(den > 0.3, num / np.maximum(den, 1e-6), 0.0)
def gth(a, sig_deg):
    """gaussiana al llarg de θ (embolcall), normalitzada pels píxels vàlids"""
    s = sig_deg / DTH
    n_ = ndi.gaussian_filter1d(a * vf, s, axis=1, mode='wrap'); d_ = ndi.gaussian_filter1d(vf, s, axis=1, mode='wrap')
    return np.where(d_ > 0.05, n_ / np.maximum(d_, 1e-6), 0.0)
SIGS = [0.6, 2.0, 6.0, 16.0]
G = [gth(Ls, s) for s in SIGS]
bands = [G[i] - G[i + 1] for i in range(3)]      # 0,6–2°, 2–6°, 6–16°
# soroll de cada banda: MAD a 5,5–8 R☉
sky = valid & (RR > 5.5)
info = []
bands_c = []
for i, bnd in enumerate(bands):
    sig = 1.4826 * np.median(np.abs(bnd[sky] - np.median(bnd[sky])))
    k = 1 - np.exp(-(bnd / (1.5 * sig)) ** 2)
    bands_c.append(bnd * k)
    info.append(dict(banda_graus=(SIGS[i], SIGS[i + 1]), sigma_soroll=float(sig), std_4_5=float(bnd[valid & (RR > 4) & (RR < 5)].std())))
print(json.dumps(info))

PRESETS = {'SUAU': [1.5, 2.5, 0.8], 'MITJA': [2.2, 3.5, 1.2], 'FORT': [3.0, 5.0, 2.0]}
# rampes en r (a la reixa polar)
tt = np.clip((RR - 3.2) / (4.4 - 3.2), 0, 1); ramp_p = tt * tt * (3 - 2 * tt)
def to_cart(Dp):
    ri = (r - R0) / DR; ti = (th + 180) / DTH
    ok = (r >= R0) & (r < R1 - DR)
    Dp2 = np.concatenate([Dp, Dp[:, :1]], axis=1)   # embolcall a +180
    out = ndi.map_coordinates(Dp2, [np.clip(ri, 0, Dp.shape[0] - 1), np.mod(ti, Dp.shape[1])], order=1, mode='nearest')
    return np.where(ok, out, 0.0).astype(np.float32)

# estrelles: detectades a l'apilat natiu (verd, pics compactes > 7σ amb pes complet), portades al llenç
# amb la similitud de les estrelles → màscara suau (radi 5–12 px) perquè el detall no les infli
Sref = np.nan_to_num(np.load('sony_stack_ref_rgb.npy')[..., 1]); WTr = np.load('sony_stack_ref_wt.npy')[..., 1]
SXr, SYr = 3894.7, 2768.7
Hs, Ws = Sref.shape; ys_, xs_ = np.mgrid[0:Hs, 0:Ws]; rs_ = np.hypot(xs_ - SXr, ys_ - SYr) / 295.8
hps = Sref - ndi.gaussian_filter(Sref, 8); sms = ndi.gaussian_filter(hps, 1.0)
okz = (rs_ > 3.0) & (WTr >= 20)
nzs = 1.4826 * np.median(np.abs(sms[okz] - np.median(sms[okz])))
pks = (sms == ndi.maximum_filter(sms, 9)) & (sms > 7 * nzs) & okz
py_, px_ = np.nonzero(pks)
g5 = np.mgrid[-6:7, -6:7]; ring5 = (np.hypot(*g5) >= 4) & (np.hypot(*g5) <= 6)
star_m = np.ones((H, W), np.float32)
sy, sx = np.mgrid[-16:17, -16:17]
scl, thd = sc[0], np.radians(sc[1]); ct, st_ = np.cos(thd), np.sin(thd)
nst = 0
for y_, x_ in zip(py_, px_):
    if not (6 <= y_ < Hs - 6 and 6 <= x_ < Ws - 6): continue
    cut = sms[y_ - 6:y_ + 7, x_ - 6:x_ + 7]
    if cut[6, 6] <= 3 * max(cut[ring5].mean(), 1e-9): continue
    ux_, uy_ = x_ - SXr, y_ - SYr
    cx_ = CX + scl * (ux_ * ct + uy_ * st_); cy_ = CY + scl * (-ux_ * st_ + uy_ * ct)
    yi, xi = int(round(cy_)), int(round(cx_))
    if 16 <= yi < H - 16 and 16 <= xi < W - 16:
        star_m[yi - 16:yi + 17, xi - 16:xi + 17] *= np.clip((np.hypot(sy, sx) - 5) / 7, 0, 1); nst += 1
print('estrelles emmascarades del detall (de l\'apilat natiu):', nst)
dist_ext = np.minimum(np.minimum(yy, H - 1 - yy), np.minimum(xx, W - 1 - xx)).astype(np.float32)
te = np.clip(dist_ext / 120.0, 0, 1); border_ramp = te * te * (3 - 2 * te)

def save16(name, arr, desc):
    a16 = np.round(np.clip(arr, 0, 1) * 65535).astype(np.uint16)
    tifffile.imwrite(os.path.join(OUTDIR, name), a16, photometric='rgb', compression='zlib',
                     extratags=[(34675, 'B', len(ICC), ICC, False)], description=desc, resolution=(300, 300), metadata=None)
    print('desat', name, a16.shape)
def to8(a, s=4): return (np.clip(a[::s, ::s], 0, 1) * 255).astype(np.uint8)

for preset, gains in PRESETS.items():
    Dp = sum(gg * bc for gg, bc in zip(gains, bands_c)) * ramp_p
    # per construcció la mitjana azimutal per fila (radi) és ~0; ho comprovem i ho forcem exactament
    rowmean = np.where(valid.sum(1) > 100, (Dp * vf).sum(1) / np.maximum(vf.sum(1), 1), 0.0)
    print(f'{preset}: component d\'anell abans de forçar (màx |mitjana per radi| / L): {100*np.max(np.abs(rowmean[(rs>3.2)&(rs<7)]))/np.median(L[(r>4)&(r<5)&inside]):.3f} %')
    Dp = (Dp - rowmean[:, None]) * vf
    D = to_cart(Dp) * star_m * border_ramp
    D = np.clip(D, -0.06, 0.06).astype(np.float32)
    # QA: perfil per radi als sectors esquerre/dret
    Lm_ = L
    for a in (3.6, 4.0, 4.4, 4.8, 5.2, 5.4, 5.6, 5.8, 6.0, 6.4):
        s1 = (r >= a) & (r < a + 0.2) & (np.abs(np.abs(th) - 180) < 15) & inside; s2 = (r >= a) & (r < a + 0.2) & (np.abs(th) < 15) & inside
        sa = (r >= a) & (r < a + 0.2) & inside
        print(f'  {preset} {a:.1f}: esq {100*D[s1].mean()/Lm_[s1].mean():+.2f} %  dreta {100*D[s2].mean()/Lm_[s2].mean():+.2f} %  anell sencer (dins llenç) {100*D[sa].mean()/Lm_[sa].mean():+.3f} %')
    np.save(f'D_tang_{preset}.npy', D)
    enh = np.clip(base + D[..., None], 0, 1)
    passalt = np.clip(0.5 + D / 2, 0, 1)
    save16(f'APILAT_Capa_Sony_encaixada_VORESNETES_TANGENCIAL_{preset}_6748x4553.tif', enh[sl], f'Base APILAT VORESNETES + detall tangencial {preset}: bandes {SIGS} graus, guanys {gains}, rampa 3,2-4,4 Rsol; cap anell ni halo radial per construccio')
    save16(f'APILAT_Detall_TANGENCIAL_PASSALT_{preset}_6748x4553.tif', np.repeat(passalt[sl][..., None], 3, -1), f'Gris 50% + D/2 ({preset} tangencial): Linear Light al 100% afegeix D')
    save16(f'APILAT_ESTESA_7648x5353_encaixada_VORESNETES_TANGENCIAL_{preset}.tif', enh, f'Domini estes: base + tangencial {preset}')
    Image.fromarray(to8(enh[sl])).save(os.path.join(OUTDIR, f'APILAT_despres_TANGENCIAL_{preset}.jpg'), quality=92)
    np.save(f'enh_tang_{preset}.npy', enh.astype(np.float32))
# --- EXTENSIO radial: guany k(r) sobre el senyal per sobre del cel (declarat, azimutalment uniforme, monòton) ---
K = 1.4
ann_sky = (r > 7.0) & (r < 7.8) & (base.sum(-1) > 0)
sky = np.array([np.median(base[..., c][ann_sky]) for c in range(3)], np.float32)
tk = np.clip((r - 3.4) / (6.0 - 3.4), 0, 1); k = (1 + (K - 1) * (tk * tk * (3 - 2 * tk)))[..., None]
ext = np.clip(sky + (base - sky) * k, 0, 1).astype(np.float32)
print('EXTENSIO: nivell del camp llunyà (mediana 7,0–7,8 R☉) RGB =', np.round(sky, 4), ' K =', K)
save16('APILAT_Capa_Sony_encaixada_VORESNETES_EXTENSIO_6748x4553.tif', ext[sl], f'Base + extensio radial: cel + (base-cel)*k(r), k de 1 (3,4 Rsol) a {K} (6 Rsol) smoothstep, constant enlla')
D_s = np.load('D_tang_MITJA.npy')
ext_t = np.clip(ext + D_s[..., None] * k, 0, 1).astype(np.float32)
save16('APILAT_Capa_Sony_encaixada_VORESNETES_EXTENSIO_TANGENCIAL_MITJA_6748x4553.tif', ext_t[sl], 'Extensio radial K=1.4 + detall tangencial MITJA')
save16('APILAT_ESTESA_7648x5353_encaixada_VORESNETES_EXTENSIO_TANGENCIAL_MITJA.tif', ext_t, 'Domini estes: extensio + tangencial MITJA')
Image.fromarray(to8(ext[sl])).save(os.path.join(OUTDIR, 'APILAT_despres_EXTENSIO.jpg'), quality=92)
Image.fromarray(to8(ext_t[sl])).save(os.path.join(OUTDIR, 'APILAT_despres_EXTENSIO_TANGENCIAL_MITJA.jpg'), quality=92)
np.save('ext_rgb.npy', ext); np.save('ext_tang_rgb.npy', ext_t)
# (v4: la base ja la desa pipeline_stack_v4.py; aquí no es torna a escriure)
# save16('APILAT_Capa_Sony_encaixada_VORESNETES_6748x4553.tif', base[sl], 'Base: apilat Sony encaixat (vores netes), corredor del raig amb la Vixen')
# save16('APILAT_ESTESA_7648x5353_encaixada_VORESNETES.tif', base, 'Base, domini estes')
# Image.fromarray(to8(base[sl])).save(os.path.join(OUTDIR, 'APILAT_despres_encaixada.jpg'), quality=92)
print('fet')
