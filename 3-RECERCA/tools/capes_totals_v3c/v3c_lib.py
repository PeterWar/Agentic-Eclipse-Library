"""Biblioteca de CapesTotalsV3c: fonament re-derivat (ID4, ID5, ID7) amb màscares = rampa RADIAL solar × porta LUNAR per
capa × protecció de fenòmens per PÍXELS (P3 perles/diamant de la 1/3200, P4 cromosfera/protuberàncies de la 1/500), i la
cadena 8/9(/10) refeta a sobre. Tot en coordenades de LLENÇ (7648x5353). Reutilitza v3b_lib/geom per import.
Fonts: els intermedis extrets de les fonts pinades (scratchpad v2b/v3b), mai els PSB vius."""
import os, sys, json, hashlib, numpy as np
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'capes_totals_v3b'))
from geom import V2B, V3B, OFF, W as FW, H as FH, R_SUN, V_MOON, smootherstep, member_centres, ELL as ELL_V3B
from v3b_lib import CW, CH, SUN, ring_medians, minima_report, rampa, quantize, lum, sha256_u16, _stretch
stretch = _stretch
SCR = os.environ.get('V3C_SCR', os.path.join(os.path.dirname(V3B), 'v3c'))
for d in ('QA', 'masks', 'states', 'work'): os.makedirs(os.path.join(SCR, d), exist_ok=True)
# Posició de cada capa al llenç (V2b/V3b, després dels offsets): (left, top, width, height)
FRAMES = {3: (459, 461, FW, FH), 4: (-1, -1, CW, CH), 5: (-1, -1, CW, CH), 7: (457, 463, FW, FH),
          8: (457, 463, FW, FH), 9: (457, 463, FW, FH), 10: (457, 463, FW, FH)}
ORDER = (3, 4, 5, 7, 8, 9, 10)

def canvas_grid():
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32); return xx, yy

def r_sun(xx, yy):
    return np.hypot(xx-SUN[0], yy-SUN[1])/np.float32(R_SUN)

def az_sun(xx, yy):
    return np.degrees(np.arctan2(-(yy-SUN[1]), xx-SUN[0])) % 360

def _src_paths(i):
    return (f'{V3B}/src_id{i}_R.npy', f'{V2B}/src_id{i}_G.npy', f'{V3B}/src_id{i}_B.npy')

def layer_rgb_canvas(i, dtype=np.float32):
    """RGB float32 0..1 de la capa i col·locada al llenç (zeros fora del seu marc)."""
    l, t, w, h = FRAMES[i]
    out = np.zeros((CH, CW, 3), dtype)
    x0, y0 = max(l, 0), max(t, 0); x1, y1 = min(l+w, CW), min(t+h, CH)
    for k, p in enumerate(_src_paths(i)):
        src = np.load(p, mmap_mode='r')
        out[y0:y1, x0:x1, k] = np.asarray(src[y0-t:y1-t, x0-l:x1-l], np.float32)/65535.
    return out

def layer_channel_canvas(i, k):
    l, t, w, h = FRAMES[i]
    out = np.zeros((CH, CW), np.float32)
    x0, y0 = max(l, 0), max(t, 0); x1, y1 = min(l+w, CW), min(t+h, CH)
    src = np.load(_src_paths(i)[k], mmap_mode='r')
    out[y0:y1, x0:x1] = np.asarray(src[y0-t:y1-t, x0-l:x1-l], np.float32)/65535.
    return out

def layer_maxmin_canvas(i):
    """(max, min) dels tres canals, float32 0..1, al llenç."""
    R = layer_channel_canvas(i, 0); G = layer_channel_canvas(i, 1); B = layer_channel_canvas(i, 2)
    return np.maximum(np.maximum(R, G), B), np.minimum(np.minimum(R, G), B)

def frame_sel(i):
    l, t, w, h = FRAMES[i]; s = np.zeros((CH, CW), bool)
    s[max(t, 0):min(t+h, CH), max(l, 0):min(l+w, CW)] = True; return s

def old_mask_canvas(i):
    """Màscara actual (V3b) de la capa i, u16 al llenç. ID3 blanca; ID4/5 màscara de Corretgint2 desplaçada (−1,−1);
    ID7 màscara de Corretgint2 (bbox llenç); ID8/9 màscares de V3b; ID10 crua CT1."""
    out = np.zeros((CH, CW), np.uint16)
    if i == 3:
        m = np.load(f'{V2B}/src_id3_mask.npy', mmap_mode='r'); l, t, w, h = FRAMES[3]
        out[t:t+h, l:l+w] = np.asarray(m); return out
    if i in (4, 5):
        m = np.load(f'{V2B}/src_id{i}_mask.npy', mmap_mode='r')
        out[0:CH-1, 0:CW-1] = np.asarray(m[1:, 1:]); return out
    if i == 7: return np.asarray(np.load(f'{V3B}/src_id7_mask.npy', mmap_mode='r')).astype(np.uint16)
    if i in (8, 9): return np.asarray(np.load(f'{V3B}/masks_final/mask_{i}.npy', mmap_mode='r')).astype(np.uint16)
    if i == 10: return np.asarray(np.load(f'{V3B}/src_id10_mask.npy', mmap_mode='r')).astype(np.uint16)
    raise KeyError(i)

def compose_over(base_f32, i, alpha_u16, rgb=None):
    """DESPRÉS = ABANS·(1-α) + capa·α (Normal 100 %, espai codificat), només dins del marc de la capa."""
    out = np.array(base_f32, dtype=np.float32, copy=True)
    l, t, w, h = FRAMES[i]
    x0, y0 = max(l, 0), max(t, 0); x1, y1 = min(l+w, CW), min(t+h, CH)
    a = alpha_u16[y0:y1, x0:x1].astype(np.float32)/65535.
    for k, p in enumerate(_src_paths(i)):
        src = np.load(p, mmap_mode='r')
        s = np.asarray(src[y0-t:y1-t, x0-l:x1-l], np.float32)/65535.
        out[y0:y1, x0:x1, k] = out[y0:y1, x0:x1, k]*(1-a) + s*a
    return out

def effective_weights(masks):
    """Pes efectiu Normal de cada capa (dict id->u16) en ordre ORDER: w_i = α_i·Π_{j>i}(1-α_j); α_3 = 1 dins del seu marc."""
    ids = [i for i in ORDER if i in masks or i == 3]
    alphas = {}
    for i in ids:
        if i == 3: a = frame_sel(3).astype(np.float32)
        else: a = masks[i].astype(np.float32)/65535.; a[~frame_sel(i)] = 0
        alphas[i] = a
    W = {}; trans = np.ones((CH, CW), np.float32)
    for i in reversed(ids):
        W[i] = alphas[i]*trans; trans = trans*(1-alphas[i])
    return W

# ---------- geometria lunar per capa ----------
def ellipse_canvas(i, ell):
    e = ell[str(i)]; return e

def d_moon(e, xx, yy):
    """Distància el·líptica equivalent (px) al centre lunar (llenç)."""
    cx, cy, a, b, th = e['cx'], e['cy'], e['a'], e['b'], np.radians(e['theta_deg'])
    dx, dy = xx-cx, yy-cy; c, s = np.cos(th), np.sin(th)
    u = dx*c + dy*s; v = -dx*s + dy*c
    return (np.sqrt((u/a)**2 + (v/b)**2) * np.float32(np.sqrt(a*b))).astype(np.float32)

def R_eq(e): return float(np.sqrt(e['a']*e['b']))

def lunar_gate_single(e, xx, yy, core_px, feather_px):
    """Zero fins a R+core, ploma radial smootherstep de feather_px."""
    d = d_moon(e, xx, yy); return smootherstep((d-(R_eq(e)+core_px))/feather_px).astype(np.float32), d

def feather_from_core(core_bool, dilate_px, feather_px):
    """Protecció per píxels: nucli dilatat (EDT ≤ dilate_px) = 1; ploma smootherstep fins a dilate+feather; 0 més enllà.
    Retorna P en [0,1] (1 = alfa zero de les capes superiors)."""
    dist = ndi.distance_transform_edt(~core_bool)
    P = np.zeros(core_bool.shape, np.float32)
    P[dist <= dilate_px] = 1.0
    z = (dist > dilate_px) & (dist < dilate_px+feather_px)
    P[z] = 1.0 - smootherstep((dist[z]-dilate_px)/feather_px)
    return P, dist

def ring_profile(img, rad, r0, r1, step, sel):
    c, g, _ = ring_medians(img, rad, r0, r1, step, sel); return c, g

def sector_table(img, d, az, r0, r1, dr, nsec, sel):
    """Mediana per cel·la (anell dr × sector 360/nsec). Retorna (centres_r, taula[nsec, nr])."""
    c, _, S = ring_medians(img, d, r0, r1, dr, sel, nsec, az); return c, S

def save_png(arr01, path):
    from PIL import Image
    Image.fromarray((np.clip(arr01, 0, 1)*255).astype(np.uint8)).save(path)

def jdump(o, path):
    json.dump(o, open(path, 'w'), indent=1, ensure_ascii=False, default=lambda x: float(x) if isinstance(x, (np.floating,)) else int(x) if isinstance(x, np.integer) else str(x))
