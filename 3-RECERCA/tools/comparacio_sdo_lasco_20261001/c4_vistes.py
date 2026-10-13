"""c4 · Vistes per ensenyar la comparació (la final mai no es gira: tot va a la seva orientació, només s'hi redueix l'escala).
  M1  mosaic de continuïtat: la final fins a 4 R☉, LASCO C2 (18:24) de 4 a 6 R☉ i C3 (18:30) de 6 a 16 R☉ (com un mosaic publicat);
  M2  mosaic sencer: la final sencera i, fora del seu marc, C2 (fins a 6 R☉) i C3;
  P1  parells del mateix marc (±1,35 R☉): final | AIA 304 ; final | AIA 211-193-171;
  P2  parell ±2,0 R☉: final | K-Cor NRGF (mitjana de 2 min, 18:29:32);
  P3  parell del marc sencer: final | LASCO C2 NRGF (18:24:31);
  F1  protuberàncies: final | AIA 304 | contorns de l'AIA 304 sobre la final.
El LASCO es mostra amb NRGF (mitjana i dispersió de cada radi a la mateixa imatge), el K-Cor tal com el publica el HAO (NRGF)."""
import json, sys, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd
from astropy.io import fits
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *
Image.MAX_IMAGE_PIXELS = None
SRGB = ARREL / 'publicacions/APOD/enviament_20260930/Eclipse_2026-08-12_Pere_Guerra_Serra.jpg'   # V123 en sRGB, 7933×5021
OUTV = VISTES
gF = geo_final('efemeride')
lluna = np.array(GEO['lluna_px']); RL = GEO['R_lluna_px']
fin_srgb = Image.open(SRGB).convert('RGB'); W, H = fin_srgb.size
def font(sz, bold=False):
    return ImageFont.truetype('/System/Library/Fonts/HelveticaNeue.ttc', sz, index=1 if bold else 0)

# ------------------------------------------------ LASCO preparat (NRGF, pilar fora)
def lasco_nrgf(fitxer, rmin, rmax, pilar=(288, 360), suau=0.0):
    d, g, hd = carrega_lasco(fitxer)
    yy, xx = np.mgrid[0:d.shape[0], 0:d.shape[1]]
    r, pa = g.polar(xx, yy)
    ok = (r > rmin) & (r < rmax) & (d > 0)
    if hd['detector'] == 'C3':
        mk = fits.open(DADES / 'lasco_calib/c3clearmask2.fts')[0].data; ok &= mk > 0
    ok &= ~((pa >= pilar[0]) & (pa <= pilar[1]))
    v = np.where(ok, d, np.nan)
    if suau > 0:
        vz = np.where(ok, v, 0); w = nd.gaussian_filter(ok.astype(float), suau)
        v = np.where(ok, nd.gaussian_filter(vz, suau) / np.maximum(w, 1e-6), np.nan)
    edges = np.geomspace(rmin, rmax, 220); k = np.digitize(r, edges) - 1
    out = np.full(d.shape, np.nan, np.float32)
    for i in range(len(edges) - 1):
        m = ok & (k == i)
        if m.sum() < 50: continue
        mu = np.nanmedian(v[m]); sd = 1.4826 * np.nanmedian(np.abs(v[m] - mu))
        out[m] = (v[m] - mu) / sd
    return out, g
c2n, gC2 = lasco_nrgf('24038985.fts', 2.3, 6.3, pilar=(288, 360))
c3n, gC3 = lasco_nrgf('32869549.fts', 3.9, 30.0, pilar=(290, 360), suau=0.8)

def mostra_geo(img, gfont, gdest, forma):
    yy, xx = np.mgrid[0:forma[0], 0:forma[1]].astype(np.float64)
    r, pa = gdest.polar(xx, yy)
    return mostreja(np.nan_to_num(img, nan=np.nan), gfont, r, pa), r, pa

def final_a_escala(f):
    """La final reduïda per un factor f (≥ 1) amb mitjana d'àrea; retorna array float i la seva geometria."""
    if f <= 1: return np.asarray(fin_srgb).astype(np.float32), gF
    im = fin_srgb.resize((round(W / f), round(H / f)), Image.LANCZOS)
    g = Geo('final/f', (gF.cx + 0.5) / f - 0.5, (gF.cy + 0.5) / f - 0.5, gF.R / f, gF.n, gF.e, gF.data, gF.obs)
    return np.asarray(im).astype(np.float32), g

def tint(v, col, lo=-2.0, hi=3.5, gamma=0.9):
    t = np.clip((v - lo) / (hi - lo), 0, 1) ** gamma; t = np.where(np.isfinite(t), t, 0)
    return np.dstack([t * c for c in col])

# ------------------------------------------------ M1 i M2: mosaics
RPX = 100.0; S = 3300
gO = Geo('mosaic', S / 2 - 0.5, S / 2 - 0.5, RPX, gF.n, gF.e, '', '')
f_arr, gFf = final_a_escala(gF.R / RPX)
yy, xx = np.mgrid[0:S, 0:S].astype(np.float64); rO, paO = gO.polar(xx, yy)
fx, fy = gFf.px(rO, paO)
fin_O = np.dstack([nd.map_coordinates(f_arr[..., c], [fy, fx], order=1, mode='constant', cval=np.nan) for c in range(3)]) / 255.0
dins_marc = np.isfinite(fin_O[..., 0])
v2, _, _ = mostra_geo(c2n, gC2, gO, (S, S)); v3, _, _ = mostra_geo(c3n, gC3, gO, (S, S))
C2COL, C3COL = (1.0, 0.62, 0.30), (0.42, 0.66, 1.0)
t2 = tint(v2, C2COL); t3 = tint(v3, C3COL, lo=-2.0, hi=3.0)
def compon(rtall, tot_final=False):
    out = np.zeros((S, S, 3), np.float32)
    zona3 = (rO >= 6.0) & np.isfinite(v3); out[zona3] = t3[zona3]
    zona2 = (rO >= (rtall if not tot_final else 0)) & (rO < 6.0) & np.isfinite(v2); out[zona2] = t2[zona2]
    zf = dins_marc & ((rO < rtall) if not tot_final else True)
    out[zf] = fin_O[zf]
    return np.clip(out, 0, 1)
for nom, rt, tot in [('M1_mosaic_continuitat_final4Rsol_C2_C3', 4.0, False), ('M2_mosaic_final_sencera_C2_C3', 99, True)]:
    a = (compon(rt, tot) * 255).astype(np.uint8)
    im = Image.fromarray(a); d = ImageDraw.Draw(im)
    # cercles fins de les fronteres (honestedat: són instruments diferents)
    for rr_ in ([rt, 6.0] if not tot else [6.0]):
        rp = rr_ * RPX; d.ellipse([S / 2 - rp, S / 2 - rp, S / 2 + rp, S / 2 + rp], outline=(255, 255, 255, 60), width=1)
    f1, f2 = font(34, True), font(28)
    d.text((40, 36), 'SOHO/LASCO C3 · 18:30:23 UT', fill=tuple(int(255 * c) for c in C3COL), font=f1)
    d.text((40, 82), 'SOHO/LASCO C2 · 18:24:31 UT', fill=tuple(int(255 * c) for c in C2COL), font=f1)
    d.text((40, 128), 'Eclipse 2026-08-12 · 18:28:46 UT · Pere Guerra', fill=(240, 220, 170), font=f1)
    d.text((40, S - 70), 'LASCO: SOHO (ESA & NASA) · NRGF. Eclipse image unrotated; LASCO reprojected to it.', fill=(170, 170, 170), font=f2)
    # nord solar i escala
    n = gF.n; x1, y1 = S - 160, 200; d.line([x1, y1, x1 + 110 * n[0], y1 + 110 * n[1]], fill=(230, 230, 230), width=4)
    d.text((x1 + 125 * n[0] - 10, y1 + 125 * n[1] - 34), 'N☉', fill=(230, 230, 230), font=f1)
    d.line([S - 40 - 5 * RPX, S - 120, S - 40, S - 120], fill=(230, 230, 230), width=4); d.text((S - 40 - 5 * RPX, S - 165), '5 R☉', fill=(230, 230, 230), font=f1)
    im.save(OUTV / f'{nom}.jpg', quality=93); im.resize((1650, 1650), Image.LANCZOS).save(OUTV / f'{nom}_1650.jpg', quality=90)
    print('desat', nom)

# ------------------------------------------------ parells del mateix marc
def parell(nom, semi_R, sortida_px, font_img, font_geo, render, fons=0):
    """Retall quadrat ±semi_R R☉ de la final (orientació original) i la font remostrejada al mateix marc."""
    f = (2 * semi_R * gF.R) / sortida_px
    f_arr, gFf = final_a_escala(f)
    gP = Geo('p', sortida_px / 2 - 0.5, sortida_px / 2 - 0.5, sortida_px / (2 * semi_R), gF.n, gF.e, '', '')
    yy, xx = np.mgrid[0:sortida_px, 0:sortida_px].astype(np.float64); r, pa = gP.polar(xx, yy)
    fx, fy = gFf.px(r, pa)
    A = np.dstack([nd.map_coordinates(f_arr[..., c], [fy, fx], order=1, mode='constant', cval=0) for c in range(3)]).astype(np.uint8)
    v = mostreja(font_img, font_geo, r, pa) if font_geo is not None else None
    B = render(v, r, pa)
    Image.fromarray(A).save(OUTV / f'{nom}_A_final.jpg', quality=92)
    Image.fromarray(B).save(OUTV / f'{nom}_B.jpg', quality=92)
    return A, B, gP, r, pa

def rend_304(v, r, pa):
    lv = np.log10(np.clip(v, 0.05, None))
    disc = r < 1.0
    o = np.full(v.shape, np.nan, np.float32)
    for lo_, hi_, m in [(None, None, disc)]: pass
    # fora del disc: normalització per radi (NRGF suau) perquè es vegin les protuberàncies
    out = np.zeros(v.shape, np.float32)
    ld = lv[disc]; lo, hi = np.nanpercentile(ld, [1, 99.8]); out[disc] = np.clip((lv[disc] - lo) / (hi - lo), 0, 1) * 0.85
    fora = ~disc & np.isfinite(lv)
    edges = np.linspace(1.0, 1.36, 90); k = np.digitize(r[fora], edges) - 1; vals = lv[fora]; res = np.zeros_like(vals)
    for i in range(len(edges) - 1):
        m = k == i
        if m.sum() > 20:
            mu = np.nanmedian(vals[m]); sd = 1.4826 * np.nanmedian(np.abs(vals[m] - mu)); res[m] = (vals[m] - mu) / max(sd, 1e-6)
    out[fora] = np.clip((res + 1.5) / 6.0, 0, 1)
    t = out ** 0.9
    return (np.dstack([t, t * 0.62, t * 0.32]) * 255).astype(np.uint8)
d304, g304 = carrega_aia('1828', '0304')
parell('P1a_final_vs_AIA304', 1.35, 1400, d304, g304, rend_304)

def rend_euv(_, r, pa):
    chans = []
    for ona in ['0211', '0193', '0171']:
        d, g = carrega_aia('1828', ona); v = mostreja(d, g, r, pa); lv = np.log10(np.clip(v, 0.3, None))
        out = np.zeros(v.shape, np.float32); disc = r < 1.0
        lo, hi = np.nanpercentile(lv[disc], [1, 99.7]); out[disc] = np.clip((lv[disc] - lo) / (hi - lo), 0, 1)
        fora = ~disc & np.isfinite(lv)
        edges = np.linspace(1.0, 1.36, 90); k = np.digitize(r[fora], edges) - 1; vals = lv[fora]; res = np.zeros_like(vals)
        for i in range(len(edges) - 1):
            m = k == i
            if m.sum() > 20:
                mu = np.nanmedian(vals[m]); sd = 1.4826 * np.nanmedian(np.abs(vals[m] - mu)); res[m] = (vals[m] - mu) / max(sd, 1e-6)
        out[fora] = np.clip((res + 2.0) / 5.5, 0, 1)
        chans.append(out ** 0.9)
    return (np.dstack(chans) * 255).astype(np.uint8)
parell('P1b_final_vs_AIA211-193-171', 1.35, 1400, None, None, rend_euv)

kc, gK = carrega_kcor('20260812_182932_kcor_l2_nrgf_avg_cropped.gif')
kcv = kc.copy(); rK, _ = gK.polar(*np.meshgrid(np.arange(512), np.arange(512)))
kcv[rK < 1.075] = np.nan
for (a_, b_, c_, d_) in [(0, 150, 0, 48), (395, 512, 0, 40), (0, 265, 462, 512), (340, 512, 462, 512)]: kcv[c_:d_, a_:b_] = np.nan
def rend_kcor(v, r, pa):
    t = np.where(np.isfinite(v), v / 255.0, 0.0); return (np.dstack([t, t, t]) * 255).astype(np.uint8)
parell('P2_final_vs_KCor', 2.0, 1400, kcv, gK, rend_kcor)

def rend_c2(v, r, pa):
    return (tint(v, (1, 1, 1), lo=-2.5, hi=3.0) * 255).astype(np.uint8)
# P3: el marc sencer de la final (no quadrat): es fa a part
f = 4.0; f_arr, gFf = final_a_escala(f); Hh, Ww = f_arr.shape[:2]
yy, xx = np.mgrid[0:Hh, 0:Ww].astype(np.float64); r, pa = gFf.polar(xx, yy)
Image.fromarray(f_arr.astype(np.uint8)).save(OUTV / 'P3_final_vs_LASCO_C2_A_final.jpg', quality=92)
Image.fromarray(rend_c2(mostreja(c2n, gC2, r, pa), r, pa)).save(OUTV / 'P3_final_vs_LASCO_C2_B.jpg', quality=92)
print('parells desats')

# ------------------------------------------------ F1: protuberàncies (final | AIA 304 | contorns)
z = np.load(RES / 'C1_aia_al_marc.npz'); x0, y0 = int(z['x0']), int(z['y0'])
g0 = Geo('retall', gF.cx - x0, gF.cy - y0, gF.R, gF.n, gF.e, '', '')
fin_full = np.asarray(fin_srgb)
files = []
for nom, (pa_c, r_c, half) in {'est, PA 116°': (116, 1.05, 72), 'nord-est, PA 40°': (40, 1.05, 46), 'oest, PA 277°': (277, 1.06, 46)}.items():
    x, y = g0.px(r_c, pa_c); x, y = int(round(x)), int(round(y))
    A = fin_full[y0 + y - half:y0 + y + half, x0 + x - half:x0 + x + half].astype(np.float32) / 255
    a = z['0304_1828'][y - half:y + half, x - half:x + half]
    lo, hi = np.nanpercentile(a, [30, 99.8]); B = np.clip((a - lo) / (hi - lo), 0, 1) ** 0.7
    sm = nd.gaussian_filter(np.nan_to_num(a), 1.2); lv = np.nanpercentile(sm, [80, 92])
    k = 1400 // (2 * half * 3) if half > 50 else 1400 // (2 * half * 3)
    up = lambda q: np.kron(q, np.ones((k, k)) if q.ndim == 2 else np.ones((k, k, 1)))
    Au, Bu = up(A), up(B)
    smu = nd.zoom(sm, k, order=1)
    C = Au.copy()
    for lvl, col in zip(lv, [(0.45, 0.9, 1.0), (1.0, 1.0, 1.0)]):
        edge = (smu > lvl) & ~nd.binary_erosion(smu > lvl, iterations=2)
        C[edge] = col
    row = np.concatenate([Au, np.ones((Au.shape[0], 8, 3)), np.dstack([Bu] * 3) * np.array([1, 0.62, 0.32]), np.ones((Au.shape[0], 8, 3)), C], axis=1)
    files.append((nom, (np.clip(row, 0, 1) * 255).astype(np.uint8)))
wmax = max(r_.shape[1] for _, r_ in files)
canvas = Image.new('RGB', (wmax, sum(r_.shape[0] + 50 for _, r_ in files)), (12, 12, 12)); yo = 0; dd = ImageDraw.Draw(canvas)
for nom, r_ in files:
    dd.text((10, yo + 10), f'Prominence {nom}:  eclipse (H-alpha, 18:28:46 UT)  |  SDO/AIA 304 Å (He II, 18:28:06 UT)  |  AIA 304 contours on the eclipse',
            fill=(220, 220, 220), font=font(24)); yo += 50
    canvas.paste(Image.fromarray(r_), (0, yo)); yo += r_.shape[0]
canvas.save(OUTV / 'F1_protuberancies_final_vs_AIA304.jpg', quality=92)
print('fet')
