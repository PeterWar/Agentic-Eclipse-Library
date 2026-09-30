"""Pas 3: color i desplegat polar de la imatge d'estructura (llibreria ael sobre la fusió V120).

Ús: python p3_presentacio.py <variant_estructura> (per defecte f)

Sortides a IA/output/ael_20260930/:
- estructura_<v>_blava_16x9.tif/.jpg   corona neutra, protuberàncies amb el color mesurat, to fred declarat a fora
- estructura_<v>_daurada_16x9.tif/.jpg corona amb el color mitjà mesurat (Sol a 9°), protuberàncies mesurades
- polar_<v>_sol_<estil>.png / polar_<v>_lluna_<estil>.png   corona desplegada (centre al Sol o a la Lluna)
"""
import sys, json, time, numpy as np, cv2
from comu import *
from ael import render, polar, annotate, io as aio, gates

V = sys.argv[1] if len(sys.argv) > 1 else 'f'
t0 = time.time()
geo = EclipseGeometry.from_json(RES / 'GEOMETRIA_LLENC_V120.json')
mono = np.load(RES / f'estructura_{V}_x1.npy')
F = np.load(LINEAL / 'fusion_starless.npy', mmap_mode='r')
S = np.load(LINEAL / 'support.npy').astype(bool)
ok = S & np.isfinite(mono)
rs = geo.rsun_map()
cx, cy = geo.sun_xy
R = geo.sun_radius_px

# --- color mesurat -------------------------------------------------------------------------------
# cel per canal (el mateix model que el pas 2, ara per a R, G i B) i color mitjà de la corona a 1,15–2,5 R☉
rgb = np.asarray(F, np.float32)
sky = np.stack([render.sky_background(rgb[..., c], S, geo, r_min_rsun=7.0, order=2)[0] for c in range(3)], -1)
net = rgb - sky
ring = S & (rs > 1.15) & (rs < 2.5)
col_corona = np.array([np.median(net[..., c][ring]) for c in range(3)], np.float64)
col_corona = col_corona / render.luminance(col_corona[None, None, :].astype(np.float32))[0, 0]
print('color mitjà de la corona (lluminància 1):', np.round(col_corona, 3), 'R/G', round(col_corona[0] / col_corona[1], 3),
      'B/G', round(col_corona[2] / col_corona[1], 3))
# balanç sobre la corona per trobar la cromosfera i les protuberàncies (H-alfa: vermell/rosa)
bal = net / col_corona[None, None, :].astype(np.float32)
wchr = render.chromosphere_weight(bal, S, geo, band_rsun=(0.95, 1.25), ratio_lo=1.25, ratio_hi=1.8, smooth_px=1.0)
print('píxels de cromosfera/protuberància (pes > 0,5):', int((wchr > 0.5).sum()))
# croma de les protuberàncies: el color mesurat, suavitzat només en color (σ 1,5 px)
chr_bal = np.stack([cv2.GaussianBlur(np.nan_to_num(bal[..., c]), (0, 0), 1.5) for c in range(3)], -1)
chr_nat = np.stack([cv2.GaussianBlur(np.nan_to_num(rgb[..., c]), (0, 0), 1.5) for c in range(3)], -1)
# color local de la dada (cel inclòs): daurat a la corona, gris blavós al cel, com el va veure Pere
loc = render.local_chromaticity(rgb, S, sigma=24.0)
del rgb, sky, net

# --- estils ---------------------------------------------------------------------------------------
tint_w = np.clip((rs - 1.25) / 2.75, 0, 1).astype(np.float32) * 0.85
blava = render.compose_color(mono, chroma_rgb=chr_bal, chroma_weight=wchr, tint=(0.62, 0.74, 1.0), tint_weight=tint_w)
daurada = render.compose_color(mono, chroma_rgb=chr_nat, chroma_weight=wchr, corona_rgb=loc, corona_color_strength=1.0)
g1 = gates.nothing_outside_data(np.where(ok[..., None], blava, np.nan), ok)
print('porta res fora de la dada:', g1)

def retall_16x9(img, alt_rsun=3.2):
    h = int(round(2 * alt_rsun * R)); w = int(round(h * 16 / 9))
    y0 = int(round(cy - h / 2)); x0 = int(round(cx - w / 2))
    return img[y0:y0 + h, x0:x0 + w], (x0, y0)

sortides = {}
for nom, im in (('blava', blava), ('daurada', daurada)):
    c, off = retall_16x9(im)
    t16 = render.to_uint(c, 16, srgb_gamma=False)
    p = aio.save_tiff(OUT / f'estructura_{V}_{nom}_16x9.tif', t16,
                      description=f'Eclipse 2026-08-12, Pere Guerra. Structure image ({nom}); radial gradient compressed; '
                                  'detail from data only (WOW with measured noise); chromosphere colour measured.')
    small = cv2.resize(c, (3840, int(round(3840 * c.shape[0] / c.shape[1]))), interpolation=cv2.INTER_AREA)
    aio.save_jpeg(OUT / f'estructura_{V}_{nom}_16x9_4k.jpg', render.to_uint(small, 8), quality=93)
    sortides[f'{nom}_tif'] = str(p.relative_to(ARREL)); sortides[f'{nom}_off'] = off
    print(nom, c.shape, f'{time.time()-t0:.0f} s')

# --- desplegat polar --------------------------------------------------------------------------------
for centre in ('sol', 'lluna'):
    cname = 'sun' if centre == 'sol' else 'moon'
    r0 = 0.95 * R if centre == 'sol' else 0.985 * geo.moon_radius_px
    P = polar.to_polar(np.where(ok[..., None], blava, np.nan), geo, center=cname, r_range=(r0, 4.0 * R),
                       n_pa=7200, radial='linear', interp='cubic', valid=ok)
    Pd = polar.to_polar(np.where(ok[..., None], daurada, np.nan), geo, center=cname, r_range=(r0, 4.0 * R),
                        n_pa=7200, radial='linear', interp='cubic', valid=ok)
    for nom, PP in (('blava', P), ('daurada', Pd)):
        disp = np.nan_to_num(PP.display(), nan=0.0)
        img8 = annotate.to_rgb8(disp)
        mb, ml = 40, 110
        canvas = np.zeros((img8.shape[0] + mb, img8.shape[1] + ml, 3), np.uint8)
        canvas[:img8.shape[0], ml:] = img8
        annotate.polar_axes(canvas, PP, pa_ticks=range(0, 360, 30), rsun_ticks=(1.0, 1.5, 2, 2.5, 3, 3.5, 4) if centre == 'sol' else (1.5, 2, 2.5, 3, 3.5),
                            size=26, margin_bottom=mb, margin_left=ml)
        aio.save_png(OUT / f'polar_{V}_{centre}_{nom}.png', canvas,
                     description=f'Unrolled corona around the {"Sun" if centre == "sol" else "Moon"}; x = position angle '
                                 '(N=0, E=90), y = distance from the centre.')
        np.save(RES / f'polar_{V}_{centre}_{nom}.npy', PP.data)
        print('polar', centre, nom, PP.data.shape, PP.meta, f'{time.time()-t0:.0f} s')

aio.write_receipt(RES / f'P3_{V}_REBUT.json', product='ael structure + polar views (Eclipse 2026-08-12)',
                  inputs=dict(fusio='4-RESULTATS/v120_20260929/cadena/v120/lineal/fusion_starless.npy',
                              estructura=str((RES / f'estructura_{V}_x1.npy').relative_to(ARREL))),
                  parameters=dict(color_corona=col_corona.tolist(), tint=(0.62, 0.74, 1.0), tint_rsun=(1.25, 4.0),
                                  chromosphere=dict(band_rsun=(0.95, 1.25), ratio=(1.25, 1.8)), polar=dict(n_pa=7200, r_max_rsun=4.0)),
                  gates=dict(nothing_outside_data=g1), outputs=sortides, hash_inputs=False,
                  notes='El to blau és una tria de presentació declarada; el daurat és el color mitjà mesurat de la corona.')
print('fet', f'{time.time()-t0:.0f} s')
