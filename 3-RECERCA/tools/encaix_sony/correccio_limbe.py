"""Capes correctores del limbe lunar per a CapesExteriors.psb (llenç 7648×5353), en un PSB a part
(CorreccioLimbe.psb) per duplicar-les cap al projecte («Enganxa al lloc» o Capa › Duplica la capa).

Diagnòstic (polars al voltant de la Lluna, sobre EDITAT PERE i sobre la composició d'Interiors):
 - franja de color al limbe: el canal blau té la vora més tova (Bayer/PSF): just DINS de la vora
   (r 0,985–1,000 R) el disc surt blau ((R−B)/L −0,38) i just fora (1,000–1,008) hi ha un anell
   groc-verd; el color de la corona (+0,41) es recupera a 1,012;
 - la banda 1,01–1,06 té un 30 % més de variància azimutal a EDITAT que a la composició
   d'Interiors (el «pixelat»: revelat/enfocament antic).
Capes:
 A «Limbe · desfranja de color» — mode COLOR: dins del limbe el color del disc (mesurat a −14…−8 px),
   fora el color de la corona/protuberància del mateix azimut (+9…+15 px); només toca to i saturació.
   Màscara: −7…+5 px del limbe real (vora detectada per azimut), ploma 3 px.
 B «Limbe · suavitzat tangencial» — Normal: la composició d'Interiors suavitzada al llarg de l'azimut
   (σ 0,4°) a la banda +3…+25 px del limbe. Màscara amb ploma 3 px. Dosar amb l'opacitat.
"""
import os, numpy as np
from scipy import ndimage as ndi
from PIL import Image
from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, Compression

SP = os.path.dirname(os.path.abspath(__file__))
D = os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes exteriors/')
OUT = D + 'CorreccioLimbe.psb'
X0, Y0 = 3000, 1700                    # origen dels retalls al llenç
IM = np.load(os.path.join(SP, 'I_merged_rgb_crop.npy')).astype(np.float32)   # composició d'Interiors (retall)
ED = np.load(os.path.join(SP, 'E_editat_rgb_crop.npy')).astype(np.float32)
cx, cy, R = np.load(os.path.join(SP, 'lluna_centre.npy'))[:3]
cx -= X0; cy -= Y0
H, W = IM.shape[:2]
L = 0.2126 * IM[..., 0] + 0.7152 * IM[..., 1] + 0.0722 * IM[..., 2]

# --- 1. vora del disc per azimut (subpíxel) -----------------------------------------------------
NT = 3600; th = np.linspace(0, 2 * np.pi, NT, endpoint=False)
rr = np.arange(0.95 * R, 1.05 * R, 0.25)
TH, RR = np.meshgrid(th, rr); X = cx + RR * np.cos(TH); Y = cy - RR * np.sin(TH)
PL = ndi.map_coordinates(L, [Y, X], order=1, mode='nearest')          # (nr, nt)
lo = np.median(PL[(rr >= 0.96 * R) & (rr <= 0.98 * R)], axis=0)
hi = np.max(PL[(rr >= 1.005 * R) & (rr <= 1.03 * R)], axis=0)
mid = 0.5 * (lo + hi)
re = np.empty(NT)
for j in range(NT):
    col = PL[:, j]; k = np.argmax(col > mid[j])
    if k == 0: re[j] = rr[0]
    else:
        f = (mid[j] - col[k - 1]) / max(col[k] - col[k - 1], 1e-6); re[j] = rr[k - 1] + f * 0.25
# suavitzat circular (σ 0,5° = 5 columnes) i estadística
re_s = ndi.gaussian_filter1d(re, 5, mode='wrap')
print(f'vora del disc: radi mitjà {re_s.mean():.2f} px (cercle ajustat {R:.2f}); rang {re_s.min():.1f}–{re_s.max():.1f}; desviació respecte del cercle: rms {np.std(re_s - R):.2f} px')
# reajust del centre amb la vora subpíxel (perquè d = r − r_e sigui net)
xs = cx + re_s * np.cos(th); ys = cy - re_s * np.sin(th)
A = np.c_[2 * xs, 2 * ys, np.ones_like(xs)]; b = xs ** 2 + ys ** 2
p, *_ = np.linalg.lstsq(A, b, rcond=None); cx2, cy2 = p[0], p[1]; R2 = np.sqrt(p[2] + cx2 ** 2 + cy2 ** 2)
print(f'centre reajustat: ({cx2 + X0:.2f}, {cy2 + Y0:.2f}) R {R2:.2f}; desplaçament respecte de l\'anterior ({cx2 - cx:+.2f}, {cy2 - cy:+.2f})')
# tornem a mesurar la vora amb el centre nou
cx, cy = cx2, cy2
X = cx + RR * np.cos(TH); Y = cy - RR * np.sin(TH)
PL = ndi.map_coordinates(L, [Y, X], order=1, mode='nearest')
lo = np.median(PL[(rr >= 0.96 * R) & (rr <= 0.98 * R)], axis=0); hi = np.max(PL[(rr >= 1.005 * R) & (rr <= 1.03 * R)], axis=0); mid = 0.5 * (lo + hi)
for j in range(NT):
    col = PL[:, j]; k = np.argmax(col > mid[j])
    re[j] = rr[0] if k == 0 else rr[k - 1] + (mid[j] - col[k - 1]) / max(col[k] - col[k - 1], 1e-6) * 0.25
re_s = ndi.gaussian_filter1d(re, 5, mode='wrap')
print(f'vora (centre nou): rms respecte del cercle {np.std(re_s - re_s.mean()):.2f} px, radi mitjà {re_s.mean():.2f}')

# --- 2. mapes cartesians d (px des de la vora real) i θ ------------------------------------------
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rmap = np.hypot(xx - cx, yy - cy); tmap = np.arctan2(-(yy - cy), xx - cx) % (2 * np.pi)
re_at = np.interp(tmap.ravel(), np.r_[th, 2 * np.pi], np.r_[re_s, re_s[0]]).reshape(H, W)
d = rmap - re_at
def ss(t): t = np.clip(t, 0, 1); return t * t * (3 - 2 * t)

# --- 3. capa A: colors de referència per azimut ------------------------------------------------
def color_ref(d0, d1):
    """color mitjà (RGB) per azimut a la banda d ∈ [d0, d1] (píxels des de la vora), suavitzat 1° en θ"""
    rr_ = np.arange(d0, d1 + 0.01, 0.5)
    cols = []
    for c in range(3):
        acc = np.zeros(NT)
        for dd in rr_:
            Xq = cx + (re_s + dd) * np.cos(th); Yq = cy - (re_s + dd) * np.sin(th)
            acc += ndi.map_coordinates(IM[..., c], [Yq, Xq], order=1, mode='nearest')
        cols.append(ndi.gaussian_filter1d(acc / len(rr_), 10, mode='wrap'))
    return np.stack(cols, -1)   # (NT, 3)
disc_col = color_ref(-14, -8); cor_col = color_ref(9, 15)
print('color disc (mitjana):', disc_col.mean(0).round(4), ' color corona (mitjana):', cor_col.mean(0).round(4))
tidx = (tmap / (2 * np.pi) * NT).astype(int) % NT
wcor = ss((d + 1.5) / 3.0)[..., None]                       # 0 dins, 1 fora, transició ±1,5 px
capaA = (disc_col[tidx] * (1 - wcor) + cor_col[tidx] * wcor).astype(np.float32)
maskA = ss((d + 10) / 3.0) * ss((8 - d) / 3.0)             # 1 entre −7 i +5, ploma 3 px
# --- 4. capa B: textura del limbe (LINEAR LIGHT): canvia només l'estructura fina (σ 2 px) d'EDITAT per la de
# la composició d'Interiors a la banda −3…+14 px: treu l'ondulació d'enfocament (anells d'1–2 px) sense tocar
# els nivells (cap graó a les vores de la màscara). Només val sobre EDITAT: si les capes interiors tapen el limbe, s'apaga.
def hp(a, s_=2.0): return a - np.stack([ndi.gaussian_filter(a[..., c], s_) for c in range(3)], -1)
dB = hp(IM) - hp(ED)
capaB = np.clip(0.5 + dB / 2.0, 0, 1).astype(np.float32)
maskB = ss((d + 6) / 3.0) * ss((17 - d) / 3.0)              # 1 entre −3 i +14, ploma 3 px
# --- 5. previsualització: simulació de la fusió Color (A) i Normal (B) sobre la composició d'Interiors ---
def lum(c): return 0.3 * c[..., 0] + 0.59 * c[..., 1] + 0.11 * c[..., 2]
def clipcolor(c):
    l = lum(c); n = c.min(-1); x = c.max(-1)
    out = c.copy()
    m = n < 0; out[m] = (l[m][:, None] + (c[m] - l[m][:, None]) * l[m][:, None] / np.maximum(l[m][:, None] - n[m][:, None], 1e-6))
    m = x > 1; out[m] = (l[m][:, None] + (out[m] - l[m][:, None]) * (1 - l[m][:, None]) / np.maximum(x[m][:, None] - l[m][:, None], 1e-6))
    return out
def setlum(c, l): return clipcolor(c + (l - lum(c))[..., None])
base = ED.copy()                                            # el que Pere veu ara a Exteriors: EDITAT
comp = np.clip(base + dB * maskB[..., None], 0, 1)          # B (Linear Light) a sota
blendA = setlum(capaA, lum(comp))
comp = comp * (1 - maskA[..., None]) + blendA * maskA[..., None]  # A (Color) a sobre
np.save(os.path.join(SP, 'limbe_comp_preview.npy'), comp)
def g(a, gam=1 / 2.2): return (np.clip(a, 0, 1) ** gam * 255).astype(np.uint8)
for tag, ang in (('dalt_dreta', 45), ('esq_protuberancia', 170), ('baix', 270), ('dreta', 0)):
    px = cx + R * np.cos(np.radians(ang)); py = cy - R * np.sin(np.radians(ang)); s = 300
    x0, y0 = int(px - s / 2), int(py - s / 2)
    a = g(base[y0:y0 + s, x0:x0 + s]); b_ = g(comp[y0:y0 + s, x0:x0 + s])
    im = np.concatenate([a, np.full((s, 6, 3), 255, np.uint8), b_], 1)
    Image.fromarray(im).resize((im.shape[1] * 3, im.shape[0] * 3), Image.BILINEAR).save(os.path.join(SP, f'limbe_correccio_{tag}.png'))
# perfil de color abans/després
rrp = np.arange(-12, 20, 1.0)
def prof(img):
    out = []
    for dd in rrp:
        Xq = cx + (re_s + dd) * np.cos(th); Yq = cy - (re_s + dd) * np.sin(th)
        v = np.stack([np.median(ndi.map_coordinates(img[..., c], [Yq, Xq], order=1, mode='nearest')) for c in range(3)])
        out.append(v)
    return np.array(out)
pb = prof(base); pa = prof(comp)
print('d(px)   abans R G B  (R−B)/L      després R G B  (R−B)/L')
for i, dd in enumerate(rrp):
    Lb = pb[i].mean(); La = pa[i].mean()
    print(f'{dd:+5.0f}   {pb[i,0]:.3f} {pb[i,1]:.3f} {pb[i,2]:.3f}  {(pb[i,0]-pb[i,2])/max(Lb,1e-4):+.2f}      {pa[i,0]:.3f} {pa[i,1]:.3f} {pa[i,2]:.3f}  {(pa[i,0]-pa[i,2])/max(La,1e-4):+.2f}')

# --- 6. PSB amb les dues capes (retall de l'anell, a la posició del llenç) ---------------------------
Wc, Hc = 7648, 5353
bx0 = int(cx - R - 45); by0 = int(cy - R - 45); bx1 = int(cx + R + 46); by1 = int(cy + R + 46)
sl = (slice(by0, by1), slice(bx0, bx1))
E = PSDImage.open(D + 'CapesExteriors.psb')
psd = new_psb(Wc, Hc, resources_from=E)
u16 = lambda a: np.clip(np.rint(a * 65535), 0, 65535).astype(np.uint16)
u8 = lambda a: np.clip(np.rint(a * 255), 0, 255).astype(np.uint8)
add_pixel_layer(psd, u16(capaB[sl]), 'Limbe · textura (LINEAR LIGHT): estructura fina d\'Interiors en lloc de la d\'EDITAT, −3…+14 px; NOMÉS sobre EDITAT',
                top=Y0 + by0, left=X0 + bx0, mask8=u8(maskB[sl]), blend=BlendMode.LINEAR_LIGHT, compression=Compression.ZIP_WITH_PREDICTION)
add_pixel_layer(psd, u16(capaA[sl]), 'Limbe · desfranja de color (mode COLOR): disc a dins, corona/protuberància a fora, per azimut; −7…+5 px',
                top=Y0 + by0, left=X0 + bx0, mask8=u8(maskA[sl]), blend=BlendMode.COLOR, compression=Compression.ZIP_WITH_PREDICTION)
finalize_lr16(psd)
hdrE = E._record.header; chE = E._record.image_data.get_data(hdrE)
mergedE = np.stack([np.frombuffer(c, dtype='>u2').reshape(hdrE.height, hdrE.width) for c in chE[:3]], -1).astype(np.uint16)
set_merged(psd, mergedE)
psd.save(OUT)
print('desat (B a sota, A a sobre)', OUT, os.path.getsize(OUT) / 1e6, 'MB; capes al retall', (X0 + bx0, Y0 + by0), '→', (X0 + bx1, Y0 + by1))
np.save(os.path.join(SP, 'limbe_re_s.npy'), np.c_[th, re_s]); np.save(os.path.join(SP, 'lluna_centre2.npy'), np.array([cx + X0, cy + Y0, re_s.mean()]))
