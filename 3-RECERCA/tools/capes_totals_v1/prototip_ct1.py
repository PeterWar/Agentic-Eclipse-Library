"""Prototip de CapesTotalsV1: V5 (compost) + PONT radial + cadena exterior amb porta + filtres SF10 + ANELL nou.
Variants de traspàs (R1, R2, pont). Escriu compostos uint16 i mètriques."""
import os, sys, json, time, numpy as np, tifffile
t0 = time.time()
def log(*a): print(f'[{time.time()-t0:6.0f} s]', *a, flush=True)
D = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(D, 'ext'); SF = os.path.join(D, 'sf10')
W, H = 7648, 5353; SOL = (4021.35, 2737.90); R_SOL = 446.15
LLUNA = (4034.7, 2736.7)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
r = np.hypot(xx - SOL[0], yy - SOL[1]) / R_SOL
r_ll = np.hypot(xx - LLUNA[0], yy - LLUNA[1])
def sstep(t):
    t = np.clip(t, 0, 1); return t*t*t*(t*(t*6-15)+10)

meta_ext = json.load(open(os.path.join(EXT, 'meta.json')))
meta_sf = {m['i']: m for m in json.load(open(os.path.join(SF, 'meta.json')))}

def canvas_rgb(folder, pref, i, m):
    rgb = np.load(os.path.join(folder, f'{pref}{i:02d}_rgb.npy')).astype(np.float32)/65535.0
    l, t2 = m['left'], m['top']
    s = np.zeros((H, W, 3), np.float32)
    sy0, sx0 = max(0,-t2), max(0,-l); dy0, dx0 = max(0,t2), max(0,l)
    hh = min(m['bottom'],H)-dy0; ww = min(m['right'],W)-dx0
    s[dy0:dy0+hh, dx0:dx0+ww] = rgb[sy0:sy0+hh, sx0:sx0+ww]
    cov = np.zeros((H, W), np.float32); cov[dy0:dy0+hh, dx0:dx0+ww] = 1.0
    return s, cov

def canvas_mask(folder, pref, i, m):
    mk = m.get('mask')
    if mk is None: return np.ones((H, W), np.float32)
    mask = np.load(os.path.join(folder, f'{pref}{i:02d}_mask.npy')).astype(np.float32)/65535.0
    mfull = np.full((H, W), mk['bg']/255.0, np.float32)
    ml, mt2 = mk['left'], mk['top']
    msy0, msx0 = max(0,-mt2), max(0,-ml); mdy0, mdx0 = max(0,mt2), max(0,ml)
    mhh = min(mk['bottom'],H)-mdy0; mww = min(mk['right'],W)-mdx0
    mfull[mdy0:mdy0+mhh, mdx0:mdx0+mww] = mask[msy0:msy0+mhh, msx0:msx0+mww]
    return mfull

def blend(comp, s, a, mode):
    if 'LINEAR_LIGHT' in mode:
        out = np.clip(comp + 2.0*s - 1.0, 0.0, 1.0)
    elif 'OVERLAY' in mode:
        out = np.where(comp <= 0.5, 2.0*comp*s, 1.0 - 2.0*(1.0-comp)*(1.0-s))
    else:
        out = s
    return comp*(1.0 - a[...,None]) + out*a[...,None]

def ring_median_rgb(img, rbins):
    med = np.zeros((len(rbins)-1, 3), np.float32)
    idx = np.digitize(r.ravel(), rbins) - 1
    flat = img.reshape(-1, 3)
    for k in range(len(rbins)-1):
        sel = idx == k
        if sel.sum() > 100:
            med[k] = np.median(flat[sel], axis=0)
    return med

# ---------- entrades ----------
v5 = np.load(os.environ.get('CT1_V5', '/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/47c293ed-2e8a-4c78-a543-00c84f771077/scratchpad/v5out/compost_rgb16.npy')).astype(np.float32)/65535.0
base = tifffile.imread(os.path.expanduser('~/Desktop/Eclipse 2026/Projecte photoshop/2-Filtres/Recursos/Base/Aplicant_Filtres.tif')).astype(np.float32)/65535.0
log('v5 i base llegides')

# ---------- pont radial (medianes per anell, per canal) ----------
rbins = np.arange(0.9, 11.5, 0.02)
rc = 0.5*(rbins[:-1] + rbins[1:])
med_v5 = ring_median_rgb(v5, rbins); med_b = ring_median_rgb(base, rbins)
delta = med_b - med_v5
from scipy.ndimage import gaussian_filter1d
delta_s = gaussian_filter1d(delta, sigma=2.5, axis=0, mode='nearest')
np.savez(os.path.join(D, 'pont_delta.npz'), rc=rc, delta=delta_s, med_v5=med_v5, med_b=med_b)
log('pont calculat; delta a r=1.5/2/2.5/3:', [np.round(delta_s[np.argmin(np.abs(rc-x))],4).tolist() for x in (1.5,2.0,2.5,3.0)])

def pont_map(r1_on):
    """LL content del PONT: 0,5 + delta(r)/2, en marxa des de r1_on (rampa 0,15 R☉)."""
    d = np.zeros((H, W, 3), np.float32)
    w_on = sstep((r - r1_on)/0.15)
    for c in range(3):
        d[..., c] = np.interp(r, rc, delta_s[:, c]) * w_on
    return np.clip(0.5 + d/2.0, 0.0, 1.0)

# ---------- variants ----------
VARIANTS = {
    'A_pont_22_29': dict(R1=2.2, R2=2.9, pont=True, pont_on=1.35),
    'B_pont_15_28': dict(R1=1.5, R2=2.8, pont=True, pont_on=1.30),
    'C_sensepont_135_195': dict(R1=1.35, R2=1.95, pont=False, pont_on=None),
    'D_pont_135_195': dict(R1=1.35, R2=1.95, pont=True, pont_on=1.30),
}
only = sys.argv[1:] if len(sys.argv) > 1 else None

# filtres visibles de SF10 (ordre 1..15), l'ANELL (13) es recalcula
VIS_FILTRES = [1, 2, 5, 6, 7, 8, 9, 10, 11, 12]   # FLAT, HALO fora, DETALL v9, RADIALS, MGN, NRGF, RadB org, RadB net, v2_40, CONTROL
OVERLAY_SET = {6, 7, 8, 9, 10, 11, 12}
CEL = 15

resultats = {}
for nomv, V in VARIANTS.items():
    if only and nomv not in only: continue
    log('=== variant', nomv, V)
    g = sstep((r - V['R1'])/(V['R2'] - V['R1']))
    comp = v5.copy()
    if V['pont']:
        pm = pont_map(V['pont_on'])
        comp = np.clip(comp + 2.0*pm - 1.0, 0.0, 1.0)
        del pm
    # cadena exterior amb porta
    w_moon = sstep((448.0 - r_ll)/7.0)
    for m in meta_ext:
        if m['i'] == 0: continue          # 03_1s: V5 ja el porta
        if not m['visible']: continue
        a = canvas_mask(EXT, 'capa', m['i'], m) * (m['opacity']/255.0)
        if m['i'] == 3:
            a = a * np.maximum(g, w_moon)  # EDITAT PERE: earthshine dins la Lluna + exterior
        else:
            a = a * g
        s, cov = canvas_rgb(EXT, 'capa', m['i'], m)
        a = a * cov
        comp = blend(comp, s, a, m['blend'])
        log(f'  ext {m["i"]} ({m["blend"].split(".")[-1]})')
        del s, a
    np.save(os.path.join(D, f'compost_{nomv}_prefiltres.npy'), np.clip(np.rint(comp*65535),0,65535).astype(np.uint16))
    # filtres
    pre_overlay = None
    for i in VIS_FILTRES:
        m = meta_sf[i]
        if i == min(OVERLAY_SET):
            pre_overlay = ring_median_rgb(comp, rbins)
        a = canvas_mask(SF, 'f', i, m) * (m['opacity']/255.0)
        s, cov = canvas_rgb(SF, 'f', i, m)
        a = a * cov
        comp = blend(comp, s, a, m['blend'])
        log(f'  filtre {i} ({m["nom"][:28]})')
        del s, a
    # ANELL: el de la SF10, tal qual (és zero per dins de 3 R☉ a propòsit; a fora el nostre exterior = base)
    post_overlay = ring_median_rgb(comp, rbins)
    rho = gaussian_filter1d(pre_overlay - post_overlay, sigma=3.0, axis=0, mode='nearest')
    m13 = meta_sf[13]
    a = canvas_mask(SF, 'f', 13, m13) * (m13['opacity']/255.0)
    s, cov = canvas_rgb(SF, 'f', 13, m13)
    comp = blend(comp, s, a*cov, m13['blend'])
    del s, a
    log('  ANELL SF10 aplicat (rho de referència desat; màx', float(np.abs(rho).max()), ')')
    # CEL V2
    m = meta_sf[CEL]
    a = canvas_mask(SF, 'f', CEL, m) * (m['opacity']/255.0)
    s, cov = canvas_rgb(SF, 'f', CEL, m)
    a = a * cov
    comp = blend(comp, s, a, m['blend'])
    del s, a
    out16 = np.clip(np.rint(comp*65535),0,65535).astype(np.uint16)
    np.save(os.path.join(D, f'compost_{nomv}.npy'), out16)
    np.savez(os.path.join(D, f'anell_{nomv}.npz'), rc=rc, rho=rho)
    log('  compost desat')
    del comp
resultats and None
log('FET')
