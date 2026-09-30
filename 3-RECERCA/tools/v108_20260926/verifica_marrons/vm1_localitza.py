"""vm1 (verificador adversari, V108 marrons) · LOCALITZACIÓ INDEPENDENT dels sis traços (geometria: C5_PERFILS de la V93 = marca 269 de Pere).
Mesura diferent de la de l'agent «marrons» (que fa servir σ4/σ40 − 1 i un nul d'agulles a l'atzar):
  · detall = DoG del ln de la lluminància, σ 3 − σ 30 (convolució normalitzada a la zona vàlida), mapa del llenç sencer;
  · perfil perpendicular: MITJANA al llarg del traç (pas 3 px) a t ∈ [−400, 400]; solc = mín a |t| ≤ 60 (cerca ±1,5°, pas 0,5°);
  · TRES nuls: (P) el mateix traç desplaçat en paral·lel ±150…±1450 px (nul LOCAL: mateixa textura, mateixa orientació);
               (R) el mateix traç girat ±10…±80° sobre el seu centre; (A) 200 segments a l'atzar a la mateixa distància del Sol (llavor pròpia).
  · p = (n nuls ≤ valor + 1) / (n + 1); z robust (mediana, MAD).
Ús: vm1_localitza.py <nom_font> [<nom_font> …]   (fonts definides a FONTS). Sortida: VM1_<nom>.json a 4-RESULTATS/v108_20260926/verifica_marrons."""
import sys, json, struct, os
from pathlib import Path
import numpy as np, cv2
ARREL = Path(__file__).resolve().parents[4]; OUT = ARREL / '4-RESULTATS/v108_20260926/verifica_marrons'; OUT.mkdir(parents=True, exist_ok=True)
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603
C5 = json.loads((ARREL / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']
TR = []
for k, t in enumerate(C5):
    d = np.array(t['info']['direccio'], float); d /= np.linalg.norm(d); TR.append((k + 1, np.array(t['info']['centre'], float), d, float(t['info']['llarg'])))
ES = ARREL / '4-RESULTATS/v105_limbe_20260926/claude/estat_v105'; PI = ARREL / '4-RESULTATS/v108_20260926/marrons/pilot'
CR = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
def psb_compost():
    psb = ARREL / '1-PHOTOSHOP/V107.psb'
    with open(psb, 'rb') as fh:
        hdr = fh.read(26); nch = struct.unpack('>H', hdr[12:14])[0]
        n = struct.unpack('>I', fh.read(4))[0]; fh.seek(n, 1); n = struct.unpack('>I', fh.read(4))[0]; fh.seek(n, 1); n = struct.unpack('>Q', fh.read(8))[0]; fh.seek(n, 1); pos = fh.tell()
        assert struct.unpack('>H', fh.read(2))[0] == 0
    mm = np.memmap(psb, dtype='>u2', mode='r', offset=pos + 2, shape=(nch, H, W))
    out = np.zeros((H, W), np.float32)
    for c in range(3): out += np.asarray(mm[c], np.float32)
    return out / 3
def npy(p, ch=None, conv=None):
    def f():
        a = np.load(p, mmap_mode='r'); x = np.asarray(a if ch is None else a[..., ch], np.float32)
        if conv == 'rgbmean': x = np.asarray(a, np.float32).mean(-1)
        return x
    return f
FONTS = {'V107_compost': psb_compost,
         'L55_P04_WOW': npy(ES / 'L55_G.npy'), 'L56_P05_WOW': npy(ES / 'L56_G.npy'), 'L45_RHEF60': npy(ES / 'L45_G.npy'), 'L46_RHEF30': npy(ES / 'L46_G.npy'),
         'L49_ACHF': npy(ES / 'L49_G.npy'), 'L54_MGN': npy(ES / 'L54_G.npy'), 'L41_NRGF': npy(ES / 'L41_G.npy'),
         'base_G_E': npy(ARREL / '4-RESULTATS/v103_banda_20260926/E/lineal_v103/base_G.npy'), 'base_G_pilot': npy(PI / 'lineal_v108/base_G.npy'),
         'vixen_ctrl': npy(PI / 'control/vixen_total.npy', 1), 'vixen_f2d': npy(PI / 'flat2d/vixen_total.npy', 1),
         'sonyA_ctrl': npy(PI / 'control/sony_A_total.npy', 1), 'sonyA_f2d': npy(PI / 'flat2d/sony_A_total.npy', 1),
         'sonyB_ctrl': npy(CR / 'b2_sony_B/cau/sony_B_total_v42.npy', 1), 'sonyB_f2d': npy(PI / 'flat2d/cau/sony_B_total_v42.npy', 1),
         'compost_abans': npy(PI / 'compost_v107mascares_abans.npy'), 'compost_despres': npy(PI / 'compost_v107mascares_despres.npy')}
def rat(fa, fb):
    def f():
        a = fa(); b = fb(); ok = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
        return np.where(ok, b / np.where(ok, a, 1), np.nan).astype(np.float32)
    return f
for _t in ('vixen', 'sonyA', 'sonyB'): FONTS[f'ratio_{_t}'] = rat(FONTS[f'{_t}_ctrl'], FONTS[f'{_t}_f2d'])
FONTS['ratio_base'] = rat(FONTS['base_G_E'], FONTS['base_G_pilot']); FONTS['ratio_compost'] = rat(FONTS['compost_abans'], FONTS['compost_despres'])
for _k in list(FONTS):
    if _k.startswith('ratio_'):
        FONTS[_k + '_inv'] = (lambda g: (lambda: 1.0 / g()))(FONTS[_k])
def detall(img):
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); l = np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32)
    ng = lambda s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
    ok = cv2.erode(m, np.ones((61, 61), np.uint8)) > 0
    return np.where(ok, ng(3) - ng(30), np.nan).astype(np.float32)
TT = np.arange(-400, 401, 2.0)
def perfil(D, c, d, L):
    n = np.array([-d[1], d[0]]); s = np.arange(-L / 2, L / 2 + 1e-6, 3.0)
    X = (c[0] + s[:, None] * d[0] + TT[None, :] * n[0]).astype(np.float32); Y = (c[1] + s[:, None] * d[1] + TT[None, :] * n[1]).astype(np.float32)
    P = cv2.remap(D, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
    cov = np.isfinite(P).mean(0)
    with np.errstate(all='ignore'): pr = np.nanmean(P, 0)
    return np.where(cov > 0.8, pr, np.nan)
def solc(D, c, d, L):
    best = np.nan
    for dth in np.arange(-1.5, 1.51, 0.5):
        a = np.radians(dth); dd = np.array([d[0] * np.cos(a) - d[1] * np.sin(a), d[0] * np.sin(a) + d[1] * np.cos(a)])
        pr = perfil(D, c, dd, L); f = np.abs(TT) <= 60; fl = (np.abs(TT) >= 120) & (np.abs(TT) <= 400)
        if np.isfinite(pr[f]).sum() < 20 or np.isfinite(pr[fl]).sum() < 50: continue
        v = np.nanmin(pr[f]) - np.nanmedian(pr[fl])
        best = v if not np.isfinite(best) else min(best, v)
    return best
def dins(c, d, L, marge=100):
    e1 = c + d * L / 2; e2 = c - d * L / 2
    return min(e1[0], e2[0]) > marge and min(e1[1], e2[1]) > marge and max(e1[0], e2[0]) < W - marge and max(e1[1], e2[1]) < H - marge
rng = np.random.default_rng(777)
NULS = {}
for k, c0, d0, L in TR:
    n0 = np.array([-d0[1], d0[0]]); rs = np.hypot(*(c0 - SOL))
    P_ = [(c0 + n0 * sh, d0) for sh in list(range(150, 1451, 130)) + list(range(-150, -1451, -130))]
    R_ = []
    for ang in list(range(10, 81, 10)) + list(range(-10, -81, -10)):
        a = np.radians(ang); R_.append((c0, np.array([d0[0] * np.cos(a) - d0[1] * np.sin(a), d0[0] * np.sin(a) + d0[1] * np.cos(a)])))
    A_ = []
    while len(A_) < 200:
        rr = rs * rng.uniform(0.8, 1.2); ph = rng.uniform(0, 2 * np.pi); c = np.array([SOL[0] + rr * np.cos(ph), SOL[1] + rr * np.sin(ph)]); an = rng.uniform(0, np.pi)
        d = np.array([np.cos(an), np.sin(an)])
        if dins(c, d, L) and np.hypot(*(c - c0)) > 300 + L / 2: A_.append((c, d))
    NULS[k] = dict(P=[x for x in P_ if dins(x[0], x[1], L)], R=[x for x in R_ if dins(x[0], x[1], L)], A=A_)
for nom in sys.argv[1:]:
    D = detall(FONTS[nom]()); res = {'font': nom, 'mesura': 'DoG ln σ3−σ30, mitjana al llarg, mín |t|≤60 − mediana flancs 120–400', 'tracos': {}}
    for k, c0, d0, L in TR:
        v0 = float(solc(D, c0, d0, L)); r = {"solc": float(v0)}
        for q, lst in NULS[k].items():
            vn = np.array([solc(D, c, d, L) for c, d in lst]); vn = vn[np.isfinite(vn)]
            if len(vn) < 5 or not np.isfinite(v0): continue
            med = float(np.median(vn)); mad = float(1.4826 * np.median(np.abs(vn - med))) or 1e-9
            r[q] = dict(valors=[round(float(x),6) for x in vn], n=int(len(vn)), mediana=med, mad=mad, z=float((v0 - med) / mad), p=float((np.sum(vn <= v0) + 1) / (len(vn) + 1)))
        res['tracos'][k] = r
        print(nom, f'T{k}', f"solc {v0*1e4:+.1f}‱", ' '.join(f"{q}: z {r[q]['z']:+.1f} p {r[q]['p']:.3f}" for q in 'PRA' if q in r), flush=True)
    (OUT / f'VM1_{nom}.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    del D
