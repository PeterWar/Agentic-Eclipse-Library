"""Pas 2: imatge d'«estructura» (detall fi de tota la corona) a partir de la fusió lineal V120.

Ús: python p2_estructura.py <escala> [variant]
  escala 0.25 (proves) … 1.0 (resolució completa del llenç).
"""
import sys, json, time, numpy as np, cv2
from comu import *
from ael import render, filters, io as aio

ESC = float(sys.argv[1]) if len(sys.argv) > 1 else 0.25
VAR = sys.argv[2] if len(sys.argv) > 2 else 'a'
t0 = time.time()
geo_full = EclipseGeometry.from_json(RES / 'GEOMETRIA_LLENC_V120.json')
F = np.load(LINEAL / 'fusion_starless.npy', mmap_mode='r')
S = np.load(LINEAL / 'support.npy', mmap_mode='r')

def redueix(a, m, f):
    """Mitjana de les mostres vàlides per bloc (cap mostra sense dada hi entra)."""
    if f == 1.0:
        return np.where(m[..., None] if a.ndim == 3 else m, a, np.nan).astype(np.float32), m
    k = int(round(1 / f)); h, w = (a.shape[0] // k) * k, (a.shape[1] // k) * k
    mm = m[:h, :w].astype(np.float32)
    cnt = mm.reshape(h // k, k, w // k, k).sum(axis=(1, 3))
    if a.ndim == 3:
        out = np.stack([(np.where(m[:h, :w], a[:h, :w, c], 0) * 1.0).reshape(h // k, k, w // k, k).sum(axis=(1, 3)) for c in range(a.shape[2])], -1)
        out = out / np.maximum(cnt, 1)[..., None]
    else:
        out = np.where(m[:h, :w], a[:h, :w], 0).reshape(h // k, k, w // k, k).sum(axis=(1, 3)) / np.maximum(cnt, 1)
    ok = cnt >= 0.999 * k * k      # un bloc amb algun píxel sense dada queda sense dada
    out = np.where(ok[..., None] if out.ndim == 3 else ok, out, np.nan).astype(np.float32)
    return out, ok

rgb, ok = redueix(np.asarray(F), np.asarray(S).astype(bool), ESC)
geo = geo_full.scaled(ESC) if ESC != 1.0 else geo_full
geo.shape = rgb.shape[:2]
print('dades', rgb.shape, f'{time.time()-t0:.0f} s')
L = render.luminance(rgb)
sky, sinfo = render.sky_background(L, ok, geo, r_min_rsun=7.0, order=2)
print('cel', {k: sinfo[k] for k in ('n_used', 'rms')}, 'nivell al Sol', float(sky[int(geo.sun_xy[1]), int(geo.sun_xy[0])]))
PAR = dict(a=dict(b_limb=0.78, b_slope=0.28, angular_gain=0.12, detail_amount=0.35, detail_gamma=0.7),
           b=dict(b_limb=0.80, b_slope=0.30, angular_gain=0.10, detail_amount=0.50, detail_gamma=0.6),
           c=dict(b_limb=0.78, b_slope=0.28, angular_gain=0.12, detail_amount=0.35, detail_gamma=0.7, detail='mgn'),
           d=dict(b_limb=0.74, b_slope=0.26, angular_gain=0.14, detail_amount=0.42, detail_gamma=0.8,
                  noise_floor=3.5),
           e=dict(b_limb=0.68, b_slope=0.24, angular_gain=0.12, detail_amount=0.40, detail_gamma=0.6,
                  wow_scales=9, noise_floor=3.0, noise_region_rsun=None),
           f=dict(b_limb=0.68, b_slope=0.24, angular_gain=0.12, detail_amount=0.40, detail_gamma=0.6,
                  wow_scales=9, noise_floor=3.0, noise_region_rsun=6.0),
           g=dict(b_limb=0.68, b_slope=0.24, angular_gain=0.12, detail_amount=0.45, detail_gamma=0.6,
                  wow_scales=9, noise_floor=2.5, noise_region_rsun=6.0, soft_threshold=1.0))[VAR]
mono, parts = render.structure_image(L, ok, geo, sky=sky, return_parts=True, **PAR)
print('estructura', f'{time.time()-t0:.0f} s')
tag = f'{VAR}_x{ESC:g}'
np.save(RES / f'estructura_{tag}.npy', mono)
aio.save_png(OUT / f'estructura_mono_{tag}.png', render.to_uint(mono, 8))
json.dump(dict(escala=ESC, variant=VAR, parametres=PAR, cel=sinfo, terra=parts.get('floor'), factors_soroll=parts.get('noise_factors'), temps_s=time.time() - t0),
          open(RES / f'P2_{tag}.json', 'w'), indent=1, default=str)
print('fet', f'{time.time()-t0:.0f} s')
