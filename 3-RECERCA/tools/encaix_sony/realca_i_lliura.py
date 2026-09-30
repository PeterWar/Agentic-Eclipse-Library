"""Detall de la corona exterior + lliurables en TIFF 16 bits (Display P3, com el document de Pere).

Detall: tres bandes en unitats angulars (2,1495 ″/px), calculades sobre la luminància del compost
encaixat, amb coring pel soroll (estimador robust emmascarat), rampa radial (0 dins de R_IN, 1 a
partir de R_OUT) i guanys declarats. Sense dividir mai per la desviació local. Les estrelles
arreglades s'exclouen del detall (màscara suau) perquè no s'inflin.
"""
import sys, os, json
import numpy as np
from scipy import ndimage as ndi
import tifffile
from PIL import Image

OUTDIR = os.path.expanduser('~/Downloads/Encaixada_2026-08-18')
os.makedirs(OUTDIR, exist_ok=True)
ICC = open('perfil.icc', 'rb').read()
SCALE = 2.1495  # "/px

fit_vix = np.load('sony_fit_rgb.npy')        # capa Sony encaixada seguint la Vixen fins a les vores
fit = np.load('sony_fit_vores_rgb.npy')      # variant «vores netes»: cel natural de la Sony a les vores (base del detall i dels cuits)
vix = np.load('vixen_canvas_rgb.npy')
r = np.load('r_rsol.npy')
w = np.load('pes_valid.npy')
mask_pere = np.load('sony_canvas_mask.npy')
stars = json.load(open('sony_canvas_rgb_estrelles_estrelles.json'))['stars']
H, W = r.shape

# --- detall ---------------------------------------------------------------------
L = fit.mean(-1)
# bandes (σ en px): fina 12–35 (26–75″), mitjana 35–100 (1,3–3,6′), gruixuda 100–280 (3,6–10′)
BANDS = [(12, 35), (35, 100), (100, 280), (280, 600)]
PRESETS = {'SUAU': [1.5, 3.0, 2.5, 0.0], 'FORT': [3.0, 6.0, 5.0, 2.0]}
PRESET = (sys.argv[1] if len(sys.argv) > 1 else 'SUAU').upper()
GAINS = PRESETS[PRESET]
SUF = '' if PRESET == 'SUAU' else '_' + PRESET
R_IN, R_OUT = 3.2, 4.4
t = np.clip((r - R_IN) / (R_OUT - R_IN), 0, 1)
ramp = t * t * (3 - 2 * t)
# màscara d'estrelles (les 15 arreglades): 0 al centre, 1 a 14 px
star_m = np.ones((H, W), np.float32)
yy, xx = np.mgrid[-16:17, -16:17]
for s in stars:
    yi, xi = int(round(s['y'])), int(round(s['x']))
    if 16 <= yi < H - 16 and 16 <= xi < W - 16:
        d = np.hypot(yy, xx)
        star_m[yi - 16:yi + 17, xi - 16:xi + 17] *= np.clip((d - 6) / 8, 0, 1)

sky = (r > 5.5) & (w > 0.99)   # zona per estimar el soroll de cada banda (cel, poca estructura)
D = np.zeros((H, W), np.float32)
info = []
for (a, b), G in zip(BANDS, GAINS):
    band = ndi.gaussian_filter(L, a) - ndi.gaussian_filter(L, b)
    # treu la component d'anell (m = 0): la resposta de la banda al perfil radial llis, mitjana per
    # anell de 0,02 R☉ (sobre els sectors que hi ha al llenç), suavitzada i restada com a funció de r
    rb = np.clip(((r - 0.9) / 0.02).astype(int), 0, 449)
    cnt = np.bincount(rb.ravel(), minlength=450).astype(float)
    sm_ = np.bincount(rb.ravel(), weights=band.ravel(), minlength=450)
    prof_r = np.where(cnt > 0, sm_ / np.maximum(cnt, 1), 0.0)
    prof_r = ndi.gaussian_filter1d(prof_r, 3, mode='nearest')
    band = band - prof_r[rb]
    sig = 1.4826 * np.median(np.abs(band[sky] - np.median(band[sky])))
    # coring suau: el que és per sota d'1,5σ s'atenua (soroll), el que és per sobre passa sencer
    k = 1 - np.exp(-(band / (1.5 * sig)) ** 2)
    band_c = band * k
    D += G * band_c
    info.append(dict(banda_px=(a, b), banda_arcmin=(round(a * SCALE / 60, 2), round(b * SCALE / 60, 2)), guany=G, sigma_soroll=float(sig),
                     std_banda_cel=float(band[sky].std()), std_banda_4_5Rsol=float(band[(r > 4) & (r < 5) & (w > 0.99)].std())))
# rampa de vora: el detall s'apaga als últims 350 px de cada vora del llenç (allà la Vixen porta un
# enfosquiment de vora que la banda gruixuda convertiria en «detall»)
BORDER = 150
yy_, xx_ = np.mgrid[0:H, 0:W]
dist_b = np.minimum(np.minimum(yy_, H - 1 - yy_), np.minimum(xx_, W - 1 - xx_)).astype(np.float32)
tb = np.clip(dist_b / BORDER, 0, 1); border_ramp = tb * tb * (3 - 2 * tb)
D *= star_m
# la component d'anell del detall total (després del coring i dels guanys, que són asimètrics
# perquè la corona té cues positives): mitjana ponderada per anell de 0,02 R☉ (només zona plena i
# lluny de les vores), suavitzada, i restada amb la mateixa rampa de vora
rb = np.clip(((r - 0.9) / 0.02).astype(int), 0, 449)
wgt = ((border_ramp > 0.99) & (w > 0.99)).astype(np.float64)   # pesos durs: la mitjana per anell surt exactament zero a la zona plena
cnt = np.bincount(rb.ravel(), weights=wgt.ravel(), minlength=450)
sm_ = np.bincount(rb.ravel(), weights=(D * wgt).ravel(), minlength=450)
prof_D = ndi.gaussian_filter1d(np.where(cnt > 100, sm_ / np.maximum(cnt, 1), 0.0), 3, mode='nearest')
D = (D - prof_D[rb]) * border_ramp * ramp
# límit de seguretat: cap píxel de detall per sobre de ±0,06 (evita punts calents i vores)
D = np.clip(D, -0.06, 0.06).astype(np.float32)
np.save(f'D_exterior{SUF}.npy', D)

# test d'anell per sectors (D nu, sense rampa dins la zona plena): mitjana per sector, anells 4,6–5,4 i 5,5–7
print('bandes:', json.dumps(info, indent=1))
th = np.load('theta_deg.npy')
Lm = fit.mean(-1)
for a, b in ((4.6, 5.4), (5.5, 7.0)):
    means = []
    for t0 in range(-180, 180, 15):
        sel = (r >= a) & (r < b) & (th >= t0) & (th < t0 + 15) & (w > 0.99) & (border_ramp > 0.99)
        if sel.sum() > 2000:
            means.append(D[sel].mean() / max(Lm[sel].mean(), 1e-6))
    ann = (r >= a) & (r < b) & (w > 0.99) & (border_ramp > 0.99)
    ring = D[ann].mean() / Lm[ann].mean()
    print(f"test d'anell {a}–{b} R☉: component d'anell (mitjana de tot l'anell) = {100*ring:.3f} % (llindar 0,15 %); "
          f"entre sectors de 15°: de {100*np.min(means):.2f} a {100*np.max(means):.2f} % (això és estructura, no anell)")
# a més: perfil de la mitjana de D per anell fi, màxim absolut relatiu entre 4,4 i 7,2 R☉
mx = 0
for a in np.arange(4.4, 7.2, 0.1):
    ann = (r >= a) & (r < a + 0.1) & (w > 0.99) & (border_ramp > 0.99)
    if ann.sum() > 5000: mx = max(mx, abs(D[ann].mean() / Lm[ann].mean()))
print(f"màxim de la component d'anell en anells de 0,1 R☉ (4,4–7,2): {100*mx:.3f} %")

# --- capes ------------------------------------------------------------------------
enh = np.clip(fit + D[..., None], 0, 1)
passalt = np.clip(0.5 + D / 2, 0, 1)   # Linear Light al 100 % → base + D

def save16(name, arr, desc):
    a16 = np.round(np.clip(arr, 0, 1) * 65535).astype(np.uint16)
    tifffile.imwrite(os.path.join(OUTDIR, name), a16, photometric='rgb' if a16.ndim == 3 else 'minisblack',
                     compression='zlib', extratags=[(34675, 'B', len(ICC), ICC, False)], description=desc,
                     resolution=(300, 300), metadata=None)
    print('desat', name, a16.shape)

if PRESET == 'SUAU':
    save16('Capa_Sony_encaixada_6748x4553.tif', fit_vix, 'Sony 300 mm encaixada a la Vixen (LUT per canal + residu de baixa frequencia restat, tambe a les vores); Vixen dins de la zona cremada; 15 estrelles arrodonides')
    save16('Capa_Sony_encaixada_VORESNETES_6748x4553.tif', fit, 'Com l\'anterior, pero a les vores del llenc la Sony continua el seu cel natural en lloc de copiar l\'enfosquiment de vora de la capa Vixen')
save16(f'Capa_Sony_encaixada_VORESNETES_REALCADA{SUF or "_SUAU"}_6748x4553.tif', enh, f'Encaixada + detall exterior (bandes {BANDS} px, guanys {GAINS}, rampa {R_IN}-{R_OUT} Rsol)')
save16(f'Detall_exterior_PASSALT{SUF or "_SUAU"}_6748x4553.tif', np.repeat(passalt[..., None], 3, -1), 'Gris 50% + D/2: en Linear Light al 100% afegeix D; opacitat = dosi')
np.save(f'enh_rgb{SUF}.npy', enh.astype(np.float32))

# --- comparacions -----------------------------------------------------------------
comp_before = np.load('composite_u16.npy').astype(np.float32) / 65535.
comp_after_pere = vix * (1 - mask_pere[..., None]) + enh * mask_pere[..., None]
def to8(a, s=4):
    return (np.clip(a[::s, ::s], 0, 1) * 255).astype(np.uint8)
Image.fromarray(np.concatenate([to8(comp_before), np.full((H // 4 + 1, 12, 3), 255, np.uint8)[:to8(comp_before).shape[0]], to8(comp_after_pere)], 1)).save(os.path.join(OUTDIR, f'comparacio_abans_despres{SUF}.jpg'), quality=92)
Image.fromarray(to8(comp_before)).save(os.path.join(OUTDIR, 'abans_compost_de_Pere.jpg'), quality=92)
Image.fromarray(to8(fit)).save(os.path.join(OUTDIR, 'despres_encaixada.jpg'), quality=92)
Image.fromarray(to8(enh)).save(os.path.join(OUTDIR, f'despres_encaixada_realcada{SUF}.jpg'), quality=92)
# retall exterior a mida real: quadrant esquerre-inferior
y0, y1, x0, x1 = 2200, 4200, 200, 2600
crop = np.concatenate([np.clip(comp_before[y0:y1, x0:x1], 0, 1), np.ones((y1 - y0, 10, 3)), np.clip(enh[y0:y1, x0:x1], 0, 1)], 1)
Image.fromarray((crop[::2, ::2] * 255).astype(np.uint8)).save(os.path.join(OUTDIR, f'retall_exterior_abans_despres{SUF}.jpg'), quality=92)
print('fet a', OUTDIR)
