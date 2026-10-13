"""c7 · Vistes de l'SDO/AIA refetes (substitueixen les de c4): P1a (304 Å), P1b (211-193-171 Å) i F1 (protuberàncies).
Vista de cada canal: log10; fora del disc es resta la mediana de cada anell (compensació radial, sense dividir per la
dispersió, perquè el soroll no s'amplifiqui) i es suavitza una mica a partir de 1,15 R☉. Fora del camp de l'AIA, negre.
F1: contorns de l'AIA 304 només fora del disc solar i fora de la Lluna, amb nivells presos de la mateixa zona."""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as nd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *
Image.MAX_IMAGE_PIXELS = None
import os
CA = os.environ.get('LANG_FIG') == 'ca'; SUF = '_ca' if CA else ''
SRGB = ARREL / 'publicacions/APOD/enviament_20260930/Eclipse_2026-08-12_Pere_Guerra_Serra.jpg'
FONT = '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
gF = geo_final('efemeride'); lluna = np.array(GEO['lluna_px']); RL = GEO['R_lluna_px']
fin = Image.open(SRGB).convert('RGB'); W, H = fin.size

def vista_aia(d, g, r_out, pa_out, eps, p=(1.0, 99.7), rmax=1.32, comp=0.85):
    """Vista d'un canal AIA mostrejada a (r_out, pa_out)."""
    yy, xx = np.mgrid[0:d.shape[0], 0:d.shape[1]]
    r, _ = g.polar(xx, yy)
    v = np.log10(np.clip(d, eps, None)).astype(np.float32)
    fora = r > 1.0
    edges = np.linspace(1.0, 1.9, 181); k = np.digitize(r, edges) - 1
    med = nd.median(v, labels=np.where(fora, k + 1, 0), index=np.arange(1, len(edges)))
    med = np.asarray(med, float); rc = 0.5 * (edges[1:] + edges[:-1]); ok = np.isfinite(med)
    m_r = np.interp(r, rc[ok], med[ok]); m1 = np.interp(1.0, rc[ok], med[ok])
    vc = np.where(fora, v - (m_r - m1) * comp, v)          # compensació radial (85 % per defecte; 55 % al 304)
    sm = nd.gaussian_filter(vc, 1.2); w = np.clip((r - 1.12) / 0.08, 0, 1)
    vc = vc * (1 - w) + sm * w
    out = mostreja(vc, g, r_out, pa_out)
    lo, hi = np.nanpercentile(vc[r < 1.3], p)
    t = np.clip((out - lo) / (hi - lo), 0, 1)
    t = np.where(r_out > rmax, t * np.clip((rmax + 0.05 - r_out) / 0.05, 0, 1), t)
    return np.where(np.isfinite(t), t, 0)

def marc_quadrat(semi_R, n):
    f = (2 * semi_R * gF.R) / n
    im = fin.resize((round(W / f), round(H / f)), Image.LANCZOS); a = np.asarray(im).astype(np.float32)
    gf = Geo('f', (gF.cx + 0.5) / f - 0.5, (gF.cy + 0.5) / f - 0.5, gF.R / f, gF.n, gF.e, '', '')
    gP = Geo('p', n / 2 - 0.5, n / 2 - 0.5, n / (2 * semi_R), gF.n, gF.e, '', '')
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float64); r, pa = gP.polar(xx, yy); fx, fy = gf.px(r, pa)
    A = np.dstack([nd.map_coordinates(a[..., c], [fy, fx], order=1, mode='constant', cval=0) for c in range(3)]).astype(np.uint8)
    return A, r, pa

N = 1400
A, r, pa = marc_quadrat(1.35, N)
Image.fromarray(A).save(VISTES / 'P1a_final_vs_AIA304_A_final.jpg', quality=92)
Image.fromarray(A).save(VISTES / 'P1b_final_vs_AIA211-193-171_A_final.jpg', quality=92)
d, g = carrega_aia('1828', '0304'); t = vista_aia(d, g, r, pa, 0.3, p=(3.0, 99.9), comp=0.55) ** 1.1
Image.fromarray((np.dstack([t, t * 0.60, t * 0.28]) * 255).astype(np.uint8)).save(VISTES / 'P1a_final_vs_AIA304_B.jpg', quality=92)
ch = []
for ona, eps in [('0211', 0.5), ('0193', 1.0), ('0171', 1.0)]:
    d, g = carrega_aia('1828', ona); ch.append(vista_aia(d, g, r, pa, eps) ** 0.9)
Image.fromarray((np.dstack(ch) * 255).astype(np.uint8)).save(VISTES / 'P1b_final_vs_AIA211-193-171_B.jpg', quality=92)
print('P1a i P1b refets')

# ------------------------------------------------ F1: protuberàncies
z = np.load(RES / 'C1_aia_al_marc.npz'); x0, y0 = int(z['x0']), int(z['y0'])
g0 = Geo('retall', gF.cx - x0, gF.cy - y0, gF.R, gF.n, gF.e, '', '')
fa = np.asarray(fin)
font = ImageFont.truetype(FONT, 22); fontp = ImageFont.truetype(FONT, 18)
files = []
for nom, (pa_c, r_c, half) in ({'PA 116° (limbe est)': (116, 1.05, 72), 'PA 40° (nord-est)': (40, 1.05, 46), 'PA 277° (limbe oest)': (277, 1.06, 46)} if CA else {'PA 116° (east limb)': (116, 1.05, 72), 'PA 40° (north-east)': (40, 1.05, 46), 'PA 277° (west limb)': (277, 1.06, 46)}).items():
    x, y = g0.px(r_c, pa_c); x, y = int(round(x)), int(round(y))
    sl = (slice(y - half, y + half), slice(x - half, x + half))
    Aimg = fa[y0 + y - half:y0 + y + half, x0 + x - half:x0 + x + half].astype(np.float32) / 255
    a = z['0304_1828'][sl].astype(np.float32)
    yy, xx = np.mgrid[y - half:y + half, x - half:x + half]
    rr, _ = g0.polar(xx, yy)
    lunar = np.hypot(xx + x0 - lluna[0], yy + y0 - lluna[1]) < RL + 1
    la = np.log10(np.clip(a, 0.3, None)); fora = (rr > 1.012) & ~lunar; fora_niv = (rr > 1.025) & ~lunar
    lo, hi = np.nanpercentile(la, [20, 99.8]); B = np.clip((la - lo) / (hi - lo), 0, 1) ** 0.9
    sm = nd.gaussian_filter(la, 1.0)
    lv = np.nanpercentile(sm[fora_niv], [85, 95]) if fora_niv.sum() > 50 else [np.inf, np.inf]
    k = max(2, 1350 // (2 * half * 3))
    up = lambda q: np.kron(q, np.ones((k, k, 1))) if q.ndim == 3 else np.kron(q, np.ones((k, k)))
    Au, Bu = up(Aimg), up(B); smu = nd.zoom(sm, k, order=1); foru = up(fora.astype(float)) > 0.5
    C = Au.copy()
    for lvl, col in zip(lv, [(0.35, 0.85, 1.0), (1.0, 1.0, 1.0)]):
        edge = (smu > lvl) & ~nd.binary_erosion(smu > lvl, iterations=2) & foru
        C[edge] = col
    sep = np.ones((Au.shape[0], 8, 3)) * 0.05
    row = np.concatenate([Au, sep, np.dstack([Bu, Bu * 0.60, Bu * 0.28]), sep, C], axis=1)
    files.append((nom, (np.clip(row, 0, 1) * 255).astype(np.uint8)))
wmax = max(r_.shape[1] for _, r_ in files)
H2 = sum(r_.shape[0] + 44 for _, r_ in files) + 92
canvas = Image.new('RGB', (wmax, H2), (13, 13, 13)); dd = ImageDraw.Draw(canvas); yo = 0
for nom, r_ in files:
    dd.text((10, yo + 10), (f'{nom}:   eclipsi   |   SDO/AIA 304 Å   |   contorns de l’AIA 304 (fora del disc) sobre l’eclipsi' if CA else f'{nom}:   eclipse   |   SDO/AIA 304 Å   |   AIA 304 contours (off-limb) on the eclipse'), fill=(225, 225, 225), font=font)
    yo += 44; canvas.paste(Image.fromarray(r_), (0, yo)); yo += r_.shape[0]
dd.text((10, yo + 12), ('Eclipsi: protuberàncies en H-alfa, 18:28:46 UT (segon contacte). SDO/AIA 304 Å (He II): 18:28:06 UT. Mateixa escala i orientació.' if CA else 'Eclipse: H-alpha prominences, 18:28:46 UT (2nd contact). SDO/AIA 304 Å (He II): 18:28:06 UT. Same scale and orientation.'), fill=(170, 170, 170), font=fontp)
dd.text((10, yo + 36), ('A 277°, la Lluna amaga la base de la protuberància. Contorns: percentils 85 i 95 de l’AIA 304 per sobre de 1,025 R☉.' if CA else 'At 277° the Moon hides the base of the prominence. Contours: 85th and 95th percentiles of AIA 304 above 1.025 R☉.'), fill=(170, 170, 170), font=fontp)
dd.text((10, yo + 60), ('Dades de l’AIA: cortesia de NASA/SDO i dels equips científics de l’AIA.' if CA else 'AIA data courtesy of NASA/SDO and the AIA science team.'), fill=(170, 170, 170), font=fontp)
canvas.save(VISTES / f'F1_protuberancies_final_vs_AIA304{SUF}.jpg', quality=92)
print('F1 refet; fet')
