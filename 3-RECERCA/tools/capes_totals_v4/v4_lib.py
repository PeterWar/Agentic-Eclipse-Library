"""Biblioteca de CapesTotalsV4: mateixa recepta que V3c (research/84 + 87 §11.3, guardrails G4.10/G4.11)
però AUTOCONTINGUDA: cap dependència de scratchpads de /private/tmp (deute de research/87 §8 i §11.2).
Fonts: els 12 revelats normalitzats de `revelat_normalitzat` (TIFF u16 Display P3, escala fotomètrica
comuna t_ref = 1/15 s), no pas ràsters ACR no normalitzats. Coordenades de LLENÇ (7648x5353).

Geometria: la de V2b/V3c (offsets a la base). A V4 totes les capes es tracten com a ràsters de frame
6960x4640: ID3 a (459,461) i la resta a (457,463) del llenç (ID4/ID5 eren ràsters de llenç amb marge:
la imatge hi queda exactament a (457,463); el marge només importa al builder, no a la fotometria).
"""
import json, hashlib, os, sys
from pathlib import Path
import numpy as np
from scipy import ndimage as ndi
from scipy.signal import find_peaks

HERE = Path(__file__).resolve().parent
REVELAT = Path(os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Vixen/HDR4/revelat_v4'))
V4W = REVELAT / 'v4'
QA_HDR4 = Path(os.path.expanduser('~/Desktop/Eclipse 2026/Derivats/Vixen/HDR4/qa'))
for d in ('npy', 'masks', 'states', 'QA', 'work'):
    (V4W / d).mkdir(parents=True, exist_ok=True)

CW, CH = 7648, 5353
FW, FH = 6960, 4640
SUN = (4020.89, 2737.66)          # llenç
R_SUN = 446.15
V_MOON = (-0.2492, -0.1317)       # px/s, Lluna respecte del Sol
R_APILAT, MARGE_APILAT, TRANS_APILAT = 460.0, 4.0, 14.0
BAND_R = R_APILAT + MARGE_APILAT + TRANS_APILAT   # 478 px
MOON7_C2 = (4033.62, 2735.62, 451.34)             # referència històrica de Corretgint2 (llenç)

ORDER = (3, 4, 5, 7, 8, 9, 10, 11, 12, 13, 16, 17)
FRAME_XY = {3: (459, 461)}
for _i in (4, 5, 7, 8, 9, 10, 11, 12, 13, 16, 17):
    FRAME_XY[_i] = (457, 463)
FRAMES = {i: (FRAME_XY[i][0], FRAME_XY[i][1], FW, FH) for i in ORDER}
LAYER_PREFIX = {3: '12', 4: '11', 5: '10', 7: '09', 8: '08', 9: '07', 10: '06',
                11: '05', 12: '04', 13: '03', 16: '02', 17: '01'}
# apilats (tenen banda d'artefacte per membre); 3/4/5 són fotogrames únics
APILAT_JSON = {7: '09_1-60s_572A2975_apilat2.json', 8: '08_1-30s_572A2970_apilat4.json',
               9: '07_1-15s_572A2976_apilat2.json', 10: '06_1-8s_572A2971_apilat4.json',
               11: '05_1-4s_572A2977_apilat2.json', 12: '04_1-2s_572A2972_apilat4.json',
               13: '03_1s_572A2978_apilat2.json', 16: '02_2s_572A2979_apilat3.json',
               17: '01_10.3s_572A2982_apilat3.json'}

def ell_all():
    return json.load(open(V4W / 'lluna_ellipse_v4.json'))

def rang_all():
    return json.load(open(V4W / 'rang.json'))

def P3():
    return np.load(V4W / 'masks/P3.npy', mmap_mode='r')

def P4():
    return np.load(V4W / 'masks/P4.npy', mmap_mode='r')

# ---------- IO de capes (revelats nous) ----------
def layer_channel_frame(i, k):
    """Canal k (0=R,1=G,2=B) u16 del frame 6960x4640 de la capa i (revelat V4)."""
    return np.load(V4W / 'npy' / f'id{i}_{k}.npy', mmap_mode='r')

def layer_channel_canvas(i, k, dtype=np.float32):
    l, t, w, h = FRAMES[i]
    out = np.zeros((CH, CW), dtype)
    src = layer_channel_frame(i, k)
    out[t:t+h, l:l+w] = np.asarray(src, dtype) / (65535.0 if dtype != np.uint16 else 1)
    return out

def layer_rgb_canvas(i, dtype=np.float32):
    out = np.zeros((CH, CW, 3), dtype)
    l, t, w, h = FRAMES[i]
    for k in range(3):
        out[t:t+h, l:l+w, k] = np.asarray(layer_channel_frame(i, k), dtype) / 65535.0
    return out

def layer_maxmin_canvas(i):
    R = layer_channel_canvas(i, 0); G = layer_channel_canvas(i, 1); B = layer_channel_canvas(i, 2)
    return np.maximum(np.maximum(R, G), B), np.minimum(np.minimum(R, G), B)

def frame_sel(i):
    l, t, w, h = FRAMES[i]
    s = np.zeros((CH, CW), bool)
    s[t:t+h, l:l+w] = True
    return s

def compose_over(base_f32, i, alpha_u16, rgb=None):
    """DESPRÉS = ABANS·(1-α) + capa·α (Normal 100 %, espai codificat), dins del marc de la capa."""
    out = np.array(base_f32, dtype=np.float32, copy=True)
    l, t, w, h = FRAMES[i]
    a = alpha_u16[t:t+h, l:l+w].astype(np.float32) / 65535.0
    if rgb is not None:
        out[t:t+h, l:l+w] = out[t:t+h, l:l+w] * (1-a[..., None]) + rgb[t:t+h, l:l+w] * a[..., None]
    else:
        for k in range(3):
            src = np.asarray(layer_channel_frame(i, k), np.float32) / 65535.0
            out[t:t+h, l:l+w, k] = out[t:t+h, l:l+w, k] * (1-a) + src * a
    return out

def effective_weights(masks):
    ids = [i for i in ORDER if i in masks or i == 3]
    alphas = {}
    for i in ids:
        if i == 3:
            a = frame_sel(3).astype(np.float32)
        else:
            a = masks[i].astype(np.float32) / 65535.0
            a[~frame_sel(i)] = 0
        alphas[i] = a
    W = {}
    trans = np.ones((CH, CW), np.float32)
    for i in reversed(ids):
        W[i] = alphas[i] * trans
        trans = trans * (1 - alphas[i])
    return W

# ---------- geometria ----------
def canvas_grid():
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
    return xx, yy

def r_sun(xx, yy):
    return np.hypot(xx - SUN[0], yy - SUN[1]) / np.float32(R_SUN)

def az_sun(xx, yy):
    return np.degrees(np.arctan2(-(yy - SUN[1]), xx - SUN[0])) % 360

def d_moon(e, xx, yy):
    cx, cy, a, b, th = e['cx'], e['cy'], e['a'], e['b'], np.radians(e['theta_deg'])
    dx, dy = xx - cx, yy - cy
    c, s = np.cos(th), np.sin(th)
    u = dx * c + dy * s
    v = -dx * s + dy * c
    return (np.sqrt((u / a) ** 2 + (v / b) ** 2) * np.float32(np.sqrt(a * b))).astype(np.float32)

def R_eq(e):
    return float(np.sqrt(e['a'] * e['b']))

def lunar_gate_single(e, xx, yy, core_px, feather_px):
    d = d_moon(e, xx, yy)
    return smootherstep((d - (R_eq(e) + core_px)) / feather_px).astype(np.float32), d

def member_centres(i, e):
    """Centres del disc de cada membre de l'apilat (llenç): centre de l'el·lipse pròpia + v·Δt."""
    ap = json.load(open(QA_HDR4 / APILAT_JSON[i]))
    t = ap['t_rel_c2_s']
    ref = ap['referencia']
    t0 = t[ref]
    out = {}
    for f in ap['membres']:
        dt = t[f] - t0
        out[f] = (e['cx'] + V_MOON[0] * dt, e['cy'] + V_MOON[1] * dt, dt)
    return ref, out

def band_gate(i, e, xx, yy, feather_px=20.0):
    """Porta lunar d'una capa APILADA: zero on qualsevol membre té el disc (478 px), ploma smootherstep."""
    ref, cs = member_centres(i, e)
    dmin = None
    for f, (cx, cy, dt) in cs.items():
        d = np.hypot(xx - cx, yy - cy)
        dmin = d if dmin is None else np.minimum(dmin, d)
    g = smootherstep((dmin - BAND_R) / feather_px).astype(np.float32)
    return g, dmin

def smootherstep(x):
    x = np.clip(x, 0, 1)
    return x * x * x * (x * (x * 6 - 15) + 10)

RAMPA_SIGMA_RSUN = 0.05

def rampa(r, r_a, r_b, sig=RAMPA_SIGMA_RSUN):
    from scipy.special import erf
    def F(x):
        z = x / sig
        return x * 0.5 * (1 + erf(z / np.sqrt(2))) + sig * np.exp(-0.5 * z * z) / np.sqrt(2 * np.pi)
    return np.clip((F(r - r_a) - F(r - r_b)) / (r_b - r_a), 0, 1).astype(np.float32)

def feather_from_core(core_bool, dilate_px, feather_px):
    dist = ndi.distance_transform_edt(~core_bool)
    P = np.zeros(core_bool.shape, np.float32)
    P[dist <= dilate_px] = 1.0
    z = (dist > dilate_px) & (dist < dilate_px + feather_px)
    P[z] = 1.0 - smootherstep((dist[z] - dilate_px) / feather_px)
    return P, dist

# ---------- utilitats ----------
def sha256_u16(a):
    return hashlib.sha256(np.ascontiguousarray(a).astype('>u2').tobytes()).hexdigest()

def quantize(f):
    return np.clip(np.floor(np.asarray(f, np.float64) * 65535.0 + 0.5), 0, 65535).astype(np.uint16)

def lum(rgb):
    return (np.asarray(rgb[..., 0], np.float32) + np.asarray(rgb[..., 1], np.float32) + np.asarray(rgb[..., 2], np.float32)) / 3.0

def _stretch(a, lo, hi, gamma=0.5):
    return np.clip((a - lo) / max(hi - lo, 1e-6), 0, 1) ** gamma
stretch = _stretch

def save_png(arr01, path):
    from PIL import Image
    Image.fromarray((np.clip(arr01, 0, 1) * 255).astype(np.uint8)).save(path)

def jdump(o, path):
    json.dump(o, open(path, 'w'), indent=1, ensure_ascii=False,
              default=lambda x: float(x) if isinstance(x, np.floating) else int(x) if isinstance(x, np.integer) else str(x))

# ---------- perfils i mínims (porta recalibrada §9.4) ----------
def ring_medians(img, rad, r0, r1, step, sel=None, sectors=None, az=None):
    bins = np.arange(r0, r1 + step * 0.5, step)
    nb = len(bins) - 1
    m = (rad >= r0) & (rad < bins[-1])
    if sel is not None:
        m &= sel
    idx = np.digitize(rad[m], bins) - 1
    v = img[m]
    g = np.full(nb, np.nan, np.float32)
    order = np.argsort(idx, kind='stable')
    idx = idx[order]
    v = v[order]
    st = np.searchsorted(idx, np.arange(nb))
    en = np.searchsorted(idx, np.arange(nb) + 1)
    for k in range(nb):
        if en[k] - st[k] >= 30:
            g[k] = np.median(v[st[k]:en[k]])
    S = None
    if sectors:
        a = az[m][order]
        S = np.full((sectors, nb), np.nan, np.float32)
        sidx = np.floor(a / (360.0 / sectors)).astype(int) % sectors
        key = idx * sectors + sidx
        o2 = np.argsort(key, kind='stable')
        key = key[o2]
        v2 = v[o2]
        st2 = np.searchsorted(key, np.arange(nb * sectors))
        en2 = np.searchsorted(key, np.arange(nb * sectors) + 1)
        for kk in range(nb * sectors):
            if en2[kk] - st2[kk] >= 30:
                S[kk % sectors, kk // sectors] = np.median(v2[st2[kk]:en2[kk]])
    return 0.5 * (bins[:-1] + bins[1:]), g, S

def _peaks(profile_ok, ok):
    f = np.interp(np.arange(len(profile_ok)), np.nonzero(ok)[0], profile_ok[ok])
    f = ndi.gaussian_filter1d(f, 1.0, mode='nearest')
    pk, pr = find_peaks(-f, prominence=0, width=1)
    return f, pk, pr

def minima_report(centres, before, after, step_px, name, layer=None, min_width_px=10.0, min_rel=0.01, nsigma=3.0, r_max_defecte=1e9):
    out = []
    ok = np.isfinite(after) & np.isfinite(before)
    if layer is not None:
        ok &= np.isfinite(layer)
    if ok.sum() < 20:
        return out, None
    af, pk, props = _peaks(after, ok)
    sm = ndi.gaussian_filter1d(af, 6, mode='nearest')
    resid = (af - sm) / np.maximum(sm, 1e-6)
    sigma = 1.4826 * np.median(np.abs(resid[ok]))
    _, pk_b, pr_b = _peaks(before, ok)
    pk_l = np.array([], int)
    pr_l = None
    if layer is not None:
        _, pk_l, pr_l = _peaks(layer, ok)
    for j, p in enumerate(pk):
        if not ok[p]:
            continue
        prom = props['prominences'][j]
        wbins = props['widths'][j]
        width = wbins * step_px
        rel = prom / max(af[p], 1e-6)
        tol = max(3, int(wbins / 4) + 1)
        def present(pks, prs):
            if len(pks) == 0:
                return False
            near = np.abs(pks - p) <= tol
            return bool(np.any(near & (prs['prominences'] >= prom / 2.0)))
        nou = not present(pk_b, pr_b) and not (layer is not None and present(pk_l, pr_l))
        dins = centres[p] <= r_max_defecte
        defecte = nou and dins and rel >= min_rel and rel >= nsigma * sigma and width >= min_width_px
        if (nou and rel >= 0.003) or defecte:
            out.append(dict(perfil=name, r=round(float(centres[p]), 3), prominencia_DN=round(float(prom * 65535), 1),
                            prominencia_pct=round(float(100 * rel), 3), amplada_px=round(float(width), 1),
                            n_sigma=round(float(rel / max(sigma, 1e-9)), 1), nou=bool(nou), defecte=bool(defecte)))
    return out, float(sigma)

def created_rises(centres, pa, pl, w, floor_l, sigma_bins=3):
    ok = np.isfinite(pa) & np.isfinite(pl)
    if ok.sum() < 20:
        return 0.0
    x = np.arange(len(pa))
    A = ndi.gaussian_filter1d(np.interp(x, x[ok], pa[ok]), sigma_bins, mode='nearest')
    L = ndi.gaussian_filter1d(np.interp(x, x[ok], pl[ok]), sigma_bins, mode='nearest')
    C = (1 - w) * A + w * L
    dA, dL, dC = np.gradient(A), np.gradient(L), np.gradient(C)
    bad = (dC > 0) & (dA <= 0) & (dL <= 0) & (L >= 3 * floor_l) & ok
    worst = 0.0
    run = 0.0
    lvl = None
    for k in range(len(C)):
        if bad[k]:
            run += dC[k]
            lvl = C[k] if lvl is None else lvl
        else:
            if lvl is not None:
                worst = max(worst, run / max(lvl, 1e-6))
            run = 0.0
            lvl = None
    if lvl is not None:
        worst = max(worst, run / max(lvl, 1e-6))
    return float(worst)
