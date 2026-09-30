"""a15b: CÒPIA de a15 sobre els COMPOSTOS desats (V115, V116) i Brno. a15 (29-09-2026) · Significació de la línia de la marca taronja a cada font (entrades exactes de la fusió de la V114 i la fusió) i CONTROL Brno 200:
mesura = clot del detall orientat (σ15, al llarg 30 px, a través 1,2 px, θ de la línia 2,8°) a la línia central del traç (o ∈ [−8, +12]) respecte del
fons (|o| ≥ 15), sobre tota la longitud del traç. Distribució NUL·LA: la mateixa plantilla (traç traslladat) a 200 llocs a l'atzar al mateix radi
(±0,6 R☉) i amb la mateixa orientació de pantalla, lluny del traç; z = (clot − mediana nul·la) / σ robusta nul·la. Sortida: taronja/A15_SIGNIFICACIO.json"""
import sys, json, numpy as np, cv2
from pathlib import Path
from scipy import ndimage as ndi
R = Path(__file__).resolve().parents[3]; O = R / '4-RESULTATS/v116_20260929'
sys.path.insert(0, str(R / '3-RECERCA/tools/v108_20260926/cadena'))
from comu_v108 import PSB
H, W = 7506, 10551; SOL = (5361.768, 3775.748); RS = 440.603
lab = np.load(O / 'marques_V115_etiquetes.npy', mmap_mode='r')
sub = np.asarray(lab[4300:4800, 5900:7100]) == 11; cols = np.nonzero(sub.any(0))[0]; yc = np.array([np.nonzero(sub[:, c])[0].mean() for c in cols]) + 4300; xs = cols + 5900
st = np.load(R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/sources/star_footprints.npy', mmap_mode='r')
Lc = R / '4-RESULTATS/v114_estrelles_20260928/cadena/v114c/lineal'
SRC = {'A (entrada fusió)': R / '4-RESULTATS/v112_claude_20260928/fonts_v113_vora/apilats/sony_A_total.npy',
       'B (entrada fusió)': R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/cau/sony_B_total_v42.npy',
       'Vixen (entrada fusió)': R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats/vixen_total.npy',
       'fusió G (entrada filtres)': Lc / 'base_G.npy'}
p = PSB(str(R / '1-PHOTOSHOP/V115.psb'))
def brno_canal():
    a, (x, y) = p.channel(230, 1); z = np.full((H, W), np.nan, np.float32); h, w = a.shape; z[max(y, 0):y + h, max(x, 0):x + w] = a[max(-y, 0):, max(-x, 0):][:H - max(y, 0), :W - max(x, 0)] / 65535; return z
def orientat(d, m, th=-2.8, sl=30, sc=1.2):
    k = int(4 * sl) | 1; yy, xx = np.mgrid[-(k // 2):k // 2 + 1, -(k // 2):k // 2 + 1].astype(np.float32); t = np.radians(th)
    u = xx * np.cos(t) - yy * np.sin(t); v = xx * np.sin(t) + yy * np.cos(t); ker = np.exp(-0.5 * (u / sl) ** 2 - 0.5 * (v / sc) ** 2); ker /= ker.sum()
    return cv2.filter2D(d * m, -1, ker, borderType=cv2.BORDER_REFLECT) / np.maximum(cv2.filter2D(m, -1, ker, borderType=cv2.BORDER_REFLECT), 1e-6)
def mesura(get, dx, dy):
    x0, x1 = int(xs.min() + dx - 80), int(xs.max() + dx + 80); y0, y1 = int(yc.min() + dy - 80), int(yc.max() + dy + 80)
    if x0 < 0 or y0 < 0 or x1 > W or y1 > H: return None
    s = get(y0, y1, x0, x1); stt = ndi.binary_dilation(np.asarray(st[y0:y1, x0:x1]) > 0, iterations=4)
    m = np.isfinite(s) & (s > 0) & ~stt
    if m.mean() < 0.9: return None
    mf = m.astype(np.float32); x = np.where(m, np.log(np.where(m, s, 1)), 0).astype(np.float32)
    d = np.where(m, x - cv2.GaussianBlur(x, (0, 0), 15) / np.maximum(cv2.GaussianBlur(mf, (0, 0), 15), 1e-6), 0).astype(np.float32); o = orientat(d, mf)
    P = np.array([np.mean(o[np.round(yc + dy - y0 + k).astype(int), xs + dx - x0]) for k in range(-30, 31)]) * 100
    ks = np.arange(-30, 31); fons = P[np.abs(ks) >= 15].mean(); win = (ks >= -8) & (ks <= 12); i = np.argmin(np.where(win, P, np.inf))
    return float(P[i] - fons), int(ks[i])
rng = np.random.default_rng(11); rT = np.hypot(xs.mean() - SOL[0], yc.mean() - SOL[1]) / RS; LLOCS = []
while len(LLOCS) < 200:
    ang = rng.uniform(0, 2 * np.pi); rr_ = rng.uniform(rT - 0.6, rT + 0.6) * RS
    dx = int(SOL[0] + rr_ * np.cos(ang) - xs.mean()); dy = int(SOL[1] - rr_ * np.sin(ang) - yc.mean())
    if abs(dx) < 500 and abs(dy) < 250: continue
    LLOCS.append((dx, dy))
res = {}
BR = None
import tifffile
fonts = {'Compost V115 (sense 414)': 'V115', 'Compost V116': 'V116', 'Brno 200 (control)': None}
for nom, f in fonts.items():
    if f in ('V115', 'V116'):
        tif = tifffile.memmap(R / ('4-RESULTATS/v115_nrgf_20260929/V115_natiu/visible_complet.tif' if f == 'V115' else '4-RESULTATS/v116_20260929/V116_natiu/visible_complet.tif'), mode='r')
        get = (lambda t: (lambda y0, y1, x0, x1: np.asarray(t[y0:y1, x0:x1, 1], np.float32)))(tif)
    elif f is None:
        if BR is None: BR = brno_canal()
        get = lambda y0, y1, x0, x1: BR[y0:y1, x0:x1]
    else:
        arr = np.load(f, mmap_mode='r'); get = (lambda arr: (lambda y0, y1, x0, x1: np.asarray(arr[y0:y1, x0:x1, 1] if arr.ndim == 3 else arr[y0:y1, x0:x1], np.float32)))(arr)
    v0 = mesura(get, 0, 0); nul = [m_[0] for m_ in (mesura(get, dx, dy) for dx, dy in LLOCS) if m_ is not None]; nul = np.array(nul)
    med = float(np.median(nul)); sr = float(1.4826 * np.median(np.abs(nul - med))); z = (v0[0] - med) / max(sr, 1e-9)
    res[nom] = dict(clot_pct=round(v0[0], 4), a_o=v0[1], nul_n=len(nul), nul_mediana=round(med, 4), nul_sigma_robusta=round(sr, 4), z=round(z, 2), fraccio_nul_mes_fonda=round(float(np.mean(nul <= v0[0])), 4))
    print(f'{nom:26s} clot {v0[0]:+.4f} % a o={v0[1]:+d} · nul (n={len(nul)}) mediana {med:+.4f} σ {sr:.4f} → z {z:+.2f} · fracció nul·la més fonda {np.mean(nul <= v0[0]):.3f}', flush=True)
(O / 'taronja/A15b_SIGNIFICACIO_COMPOSTOS.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
