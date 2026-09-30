"""o1 (V120, 29-09-2026) · L'ORDIT (raigs) I LA TRAMA (arcs) DE TRES TESTIMONIS A LA GEOMETRIA NOVA (la Sony deformada a la de la Vixen).
Són els filtres de la V119 (b8b: ordit; b9: trama) sobre les entrades de la V120, amb tres canvis:
  1. TESTIMONIS: Sony A i B DEFORMADES (f5, amb els seus pesos), sense estrelles amb els models de la d4 NOVA (ajustats a la Sony combinada a la
     geometria nova) amb amplitud pròpia; Vixen: la vixen_starless de la d4 nova, a la resolució de la Sony. Peus d'halo mesurats (com el b5).
     El registre es fa contra la FUSIÓ NOVA (fusion_starless, canal G), que és la geometria del compost de la V120 (abans, el render de la V115,
     que a fora seguia la Sony). Amb els tres testimonis ja a la mateixa geometria, el registre ha de sortir gairebé nul (es mesura i es desa).
  2. LA TACA DE L'EIX D'A (disc de 320 px, al seu lloc nou): allà hi ha B i Vixen; el detall hi és el de DOS testimonis (mínim concordant de B i V
     amb la coincidència w_BV), en lloc de deixar el disc neutre (a la V119 era un forat sense ordit ni trama).
  3. TRAMA, peus d'estrella (Pere, 29-09: «crea un petit artefacte fosc al voltant de l'estrella més propera al limbe, aprox. a les 6:00»):
     la trama és d'escala gran (fins al 12 % de r) i el seu nivell al voltant d'una estrella no és zero; un disc neutre enmig d'un camp de +1 %
     es veia un 1 % més fosc. Dins dels peus, la trama porta NOMÉS EL NIVELL de gran escala del voltant (convolució normalitzada des de fora
     del peu; sense detall: la trama no en té a aquesta escala). L'ordit, que és detall fi de mitjana zero, hi continua neutre.
Sortides (cartesianes): <sortida>/ordit/{D_minim_f32, W3_coherencia_f16, DA_f16}.npy i <sortida>/trama/{D_minim_f32, DA_f16}.npy (DA: per a la
cobertura del b25b), i O1_REBUT.json. El guany (κ) es calibra després contra el render de la pila de la V120 (o2).
Ús: o1_ordit_trama_v120.py <carpeta_sortida>"""
import sys, json, time, glob, importlib.util, numpy as np, cv2
from pathlib import Path
from scipy import ndimage as ndi
OUT = Path(sys.argv[1]).resolve(); OUT.mkdir(parents=True, exist_ok=True); (OUT / 'ordit').mkdir(exist_ok=True); (OUT / 'trama').mkdir(exist_ok=True)
sys.argv = [sys.argv[0], str(OUT / '_b1')]
R = Path(__file__).resolve().parents[3]; t0 = time.time()
spec = importlib.util.spec_from_file_location('b1', R / '3-RECERCA/tools/v117_20260929/b1_filtre_coherent_AB.py'); b1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b1)
spec = importlib.util.spec_from_file_location('camp_v120', Path(__file__).with_name('camp_v120.py')); cv_ = importlib.util.module_from_spec(spec); spec.loader.exec_module(cv_)
H, W, SOL, RS = b1.H, b1.W, b1.SOL, b1.RS
def log(*a): print(f'[{time.time() - t0:5.0f}s]', *a, flush=True)
V120 = R / '4-RESULTATS/v120_20260929'; SV = V120 / 'sony_v'; S4 = V120 / 'fonts/fusio/d4/products/sources'; AP = R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats'
MODEL = json.load(open(V120 / 'f1/CAMP_V120.json'))
ESCALA = 946.0 / RS; SIG_V = float(np.sqrt(8.3 ** 2 - 5.5 ** 2) / 2.355 / ESCALA); R_PEU = 25
# ------------------------------------------------------------------ entrades (com el b5 de la V118, amb les rutes de la V120)
def llum(ft, fw):
    t = np.load(ft, mmap_mode='r'); w = np.load(fw, mmap_mode='r'); L = np.zeros((H, W), np.float32); m = np.ones((H, W), bool)
    for y0 in range(0, H, 1024):
        s = slice(y0, min(H, y0 + 1024)); a = np.asarray(t[s], np.float32); ww = np.asarray(w[s], np.float32); ww = ww if ww.ndim == 3 else ww[..., None]
        L[s] = (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4; m[s] = np.all(np.isfinite(a) & (a > 0), axis=2) & np.all(ww > 0, axis=2)
    return np.where(m, L, 0).astype(np.float32), m
_yy, _xx = np.mgrid[0:65, 0:65].astype(np.float32); _u, _v = (_xx - 32) / 32, (_yy - 32) / 32
_BQ = np.stack([np.ones_like(_u), _u, _v, _u * _u, _u * _v, _v * _v], -1).reshape(-1, 6)
def treu_sony(L, m):
    out = []
    for f in sorted(glob.glob(str(S4 / 'sony_star_*.npz'))):
        z = np.load(f); x, y = (int(v) for v in z['xy']); c = z['component'].astype(np.float32); M_ = (c[..., 0] + 2 * c[..., 1] + c[..., 2]) / 4
        if x < 32 or y < 32 or x + 33 > W or y + 33 > H: continue
        ys, xs = slice(y - 32, y + 33), slice(x - 32, x + 33); P = L[ys, xs]; ok = m[ys, xs]
        if ok.mean() < 0.5: continue
        A_ = np.concatenate([M_.reshape(-1, 1), _BQ], 1)[ok.ravel()]; cf = np.linalg.lstsq(A_, P[ok], rcond=None)[0]; s = float(max(cf[0], 0.0)); nou = P - s * M_
        dolent = ok & (nou <= 0.2 * np.maximum(P, 1e-9)); m[ys, xs] &= ~dolent; L[ys, xs] = np.where(m[ys, xs], nou, 0); out.append(s)
    return out
def posicions():
    return sorted({tuple(int(v) for v in np.load(f)['xy']) for pat in ('sony_star_*.npz', 'vixen_star_*.npz', 'fusion_star_*.npz') for f in glob.glob(str(S4 / pat))})
def peus(radis=None):
    peu = ndi.binary_dilation(np.asarray(np.load(S4 / 'star_footprints.npy', mmap_mode='r')) > 0, iterations=3)
    for x, y in posicions():
        rp = int((radis or {}).get((x, y), R_PEU)); y0, y1, x0, x1 = max(0, y - rp), min(H, y + rp + 1), max(0, x - rp), min(W, x + rp + 1)
        yy, xx = np.ogrid[y0:y1, x0:x1]; peu[y0:y1, x0:x1] |= (xx - x) ** 2 + (yy - y) ** 2 <= rp ** 2
    return peu
LA, mA = llum(SV / 'sony_A_total_flat2d_v5.npy', SV / 'sony_A_weights.npy'); LB, mB = llum(SV / 'sony_B_total_v42.npy', SV / 'sony_B_weights_v42.npy')
sA, sB = treu_sony(LA, mA), treu_sony(LB, mB)
gx, gy = cv_.camp(MODEL, 'A', np.array([b1.GX]), np.array([b1.GY])); GXn, GYn = b1.GX + gx[0], b1.GY + gy[0]; yy_, xx_ = np.ogrid[:H, :W]
TACA = np.hypot(xx_ - GXn, yy_ - GYn) <= 320; mA &= ~TACA
t = np.load(S4 / 'vixen_starless.npy', mmap_mode='r'); LV = np.zeros((H, W), np.float32); mV = np.zeros((H, W), bool); dv = np.load(AP / 'vixen_den.npy', mmap_mode='r')
for y0 in range(0, H, 1024):
    s = slice(y0, min(H, y0 + 1024)); a = np.asarray(t[s], np.float32); LV[s] = (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4; mV[s] = np.all(np.isfinite(a) & (a > 0), axis=2) & (np.asarray(dv[s]) > 0)
LV = np.where(mV, LV, 0).astype(np.float32); g = lambda x: cv2.GaussianBlur(x, (0, 0), SIG_V)
LV = np.where(mV, g(np.where(mV, LV, 0).astype(np.float32)) / np.maximum(g(mV.astype(np.float32)), 1e-6), 0).astype(np.float32); mV = ndi.binary_erosion(mV, iterations=4)
log('entrades', dict(estrelles_restades_A=len(sA), B=len(sB), taca_A=[round(float(GXn), 1), round(float(GYn), 1)]))
# ------------------------------------------------------------------ el pla log-polar (b1) i els operadors
PB = lambda M: b1.polar(M.astype(np.float32)) > 0.999
CACHE = {}
def gn(x, M, sr, st_):
    """convolució normalitzada; el denominador es desa per màscara (la memòria cau es buida a cada passada: un id() reutilitzat donaria un denominador d'una altra màscara)."""
    k = (id(M), sr, st_)
    if k not in CACHE: CACHE[k] = (M, b1.gcv(M.astype(np.float32), sr, st_))
    assert CACHE[k][0] is M; den = CACHE[k][1]; return b1.gcv(np.where(M, x, 0).astype(np.float32), sr, st_) / np.maximum(den, 1e-6), den
def detall_az(L, M):
    x = np.where(M, np.log(np.maximum(b1.polar(L), 1e-9)), 0).astype(np.float32); a, _ = gn(x, M, b1.SR, b1.S1); c, _ = gn(x, M, b1.SR, b1.S2)
    return np.where(M, a - c, 0).astype(np.float32)
def coh(u, v, M, WR, WT):
    cov, den = gn(u * v, M, WR, WT); vu, _ = gn(u * u, M, WR, WT); vv, _ = gn(v * v, M, WR, WT)
    w = np.clip(cov / np.maximum(0.5 * (vu + vv), 1e-12), 0, 1).astype(np.float32); w[~M] = 0; return w * np.clip((den - 0.6) / 0.4, 0, 1).astype(np.float32)
def minim(Ds, w):
    mag = np.min(np.stack([np.abs(d) for d in Ds]), 0); s0 = np.sign(Ds[0]); igual = np.all(np.stack([np.sign(d) == s0 for d in Ds]), 0) & (s0 != 0)
    return (w * np.where(igual, s0 * mag, 0)).astype(np.float32)
# ------------------------------------------------------------------ ORDIT (azimutal), amb peus d'halo mesurats (dues passades, com el b5)
REF = np.load(S4 / 'fusion_starless.npy', mmap_mode='r'); GR = np.empty((H, W), np.float32)
for y0 in range(0, H, 1024): GR[y0:y0 + 1024] = np.nan_to_num(np.asarray(REF[y0:y0 + 1024, :, 1], np.float32))
peu0 = peus(); mAll = mA & mB & mV & ~peu0; mBV = mB & mV & TACA & ~peu0
def ordit(mAll, mBV, peu_):
    CACHE.clear(); P3, P2, PU = PB(mAll), PB(mBV), PB((GR > 0) & ~peu_)
    DA, DB, DV = detall_az(LA, P3), detall_az(LB, P3), detall_az(LV, P3); DU = detall_az(GR, PU)
    DB2, DV2 = detall_az(LB, P2), detall_az(LV, P2)
    return P3, P2, PU, DA, DB, DV, DU, DB2, DV2
P3, P2, PU, DA, DB, DV, DU, DB2, DV2 = ordit(mAll, mBV, peu0)
# peus d'halo (el criteri del b5: anells 26–100 px contra el fons de 100–130 px, al detall de CADA testimoni; les dues de V ≤ 6,5, 206 px)
spec = importlib.util.spec_from_file_location('b5', R / '3-RECERCA/tools/v118_20260929/b5_filtre_tres_testimonis.py')
sys.argv = [sys.argv[0], str(OUT / '_b5')]; b5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b5)
cat = json.load(open(V120 / 'estrelles/CATALEG_ACCEPTAT_V120.json'))['stars']
def radis_v120(Dc, pos):
    brill = [(s_['x'], s_['y']) for s_ in cat if s_['V'] <= b5.V_BRILLANT]; out, det = {}, {}
    yy, xx = np.mgrid[-b5.BASE[1]:b5.BASE[1] + 1, -b5.BASE[1]:b5.BASE[1] + 1]; rq = np.hypot(xx, yy)
    for x, y in pos:
        if any(np.hypot(x - bx, y - by) < 8 for bx, by in brill): out[(x, y)] = b5.R_BRILLANT; det[f'{x},{y}'] = dict(radi=b5.R_BRILLANT, regla='V ≤ 6,5'); continue
        if x < b5.BASE[1] or y < b5.BASE[1] or x + b5.BASE[1] >= W or y + b5.BASE[1] >= H: continue
        Ps = [np.asarray(D[y - b5.BASE[1]:y + b5.BASE[1] + 1, x - b5.BASE[1]:x + b5.BASE[1] + 1], np.float32) for D in Dc]
        def rms(P, a, b):
            k = (rq >= a) & (rq < b) & (P != 0); return float(np.sqrt(np.mean(P[k] ** 2))) if k.sum() > 40 else np.nan
        base = [rms(P, *b5.BASE) for P in Ps]
        if not all(np.isfinite(base)) or min(base) <= 0: continue
        r_ = R_PEU; qs = []
        for a, b in zip(b5.ANELLS[:-1], b5.ANELLS[1:]):
            v = [rms(P, a, b) / bs for P, bs in zip(Ps, base)]; v = [q for q in v if np.isfinite(q)]; q = float(np.mean(v)) if v else np.nan; qs.append(round(q, 2) if np.isfinite(q) else None)
            if not np.isfinite(q) or q <= b5.Q_HALO: break
            r_ = b + b5.MARGE
        out[(x, y)] = int(r_); det[f'{x},{y}'] = dict(radi=int(r_), q_anells=qs)
    return out, det
RADIS, HALO = radis_v120([b1.cart(DA), b1.cart(DB), b1.cart(DV)], posicions())
peu = peus(RADIS); mAll = mA & mB & mV & ~peu; mBV = mB & mV & TACA & ~peu
log('halo', dict(mesurables=len(RADIS), amb_radi_gran=sum(v > R_PEU for v in RADIS.values())))
P3, P2, PU, DA, DB, DV, DU, DB2, DV2 = ordit(mAll, mBV, peu)
# registre angular a la fusió nova (com el b8b; mapa continu). Amb els testimonis ja a la mateixa geometria, ha de ser ~0.
def mesura_desplacament(DX, DUx, M, MU):
    """mediana del desplaçament angular (°) de DX respecte de DUx per trams de radi (correlació per finestres, com el f6)."""
    DS = 4; red = lambda X: cv2.resize(X, (X.shape[1] // DS, X.shape[0] // DS), interpolation=cv2.INTER_AREA)
    x, u = red(np.where(M, DX, 0)), red(np.where(MU, DUx, 0)); v = red((M & MU).astype(np.float32)) > 0.99; nt = x.shape[1]; dth = 360.0 / nt
    wt = int(round(5.0 / dth)); wr = int(round(0.08 / (b1.dr * DS))); ms = int(np.ceil(0.6 / dth)); pad = wt
    def box(z): zp = np.concatenate([z[:, -pad:], z, z[:, :pad]], 1); return cv2.boxFilter(zp, -1, (wt, wr), normalize=True, borderType=cv2.BORDER_REFLECT)[:, pad:-pad]
    uu = box(np.where(v, u * u, 0)); cor = []
    for s in range(-ms, ms + 1):
        xs = np.roll(x, -s, axis=1); vs = v & np.roll(v, -s, axis=1); num = box(np.where(vs, xs * u, 0)); xx = box(np.where(vs, xs * xs, 0)); cov = box(vs.astype(np.float32))
        cor.append(np.where(cov > 0.9, num / np.sqrt(np.maximum(xx * uu, 1e-20)), np.nan))
    cor = np.nan_to_num(np.stack(cor), nan=-1); i = np.argmax(cor, 0); cm = np.take_along_axis(cor, i[None], 0)[0]; ok = (cm >= 0.6) & (i > 0) & (i < 2 * ms) & v
    rr = (np.exp(b1.rho.reshape(-1, DS).mean(1)) / RS)[:, None] * np.ones((1, nt)); d = (i - ms) * dth; o = {}
    for a, b in ((1.3, 2), (2, 3), (3, 4.5)):
        k = ok & (rr >= a) & (rr < b); o[f'{a}-{b}'] = round(float(np.median(d[k]) * np.pi / 180 * (a + b) / 2 * RS), 2) if k.sum() > 50 else None
    return o
REG = {n: mesura_desplacament(X, DU, P3, PU) for n, X in (('A', DA), ('B', DB), ('V', DV))}
log('desplaçament respecte de la fusió nova (px, mediana per tram)', REG)
w3 = np.minimum(np.minimum(coh(DA, DB, P3, b1.WR, b1.WT), coh(DA, DV, P3, b1.WR, b1.WT)), coh(DB, DV, P3, b1.WR, b1.WT)); D3 = minim([DA, DB, DV], w3)
w2 = coh(DB2, DV2, P2, b1.WR, b1.WT); D2 = minim([DB2, DV2], w2)
Dord = np.where(P3, D3, np.where(P2, D2, 0)).astype(np.float32); Word = np.where(P3, w3, np.where(P2, w2, 0)).astype(np.float32)
mc = b1.cart((P3 | P2).astype(np.float32)) > 0.5; viu = ~mc & ~ndi.binary_dilation(mc, iterations=2)
c = b1.cart(Dord); c[viu] = 0; np.save(OUT / 'ordit/D_minim_f32.npy', c.astype(np.float32)); np.save(OUT / 'ordit/W3_coherencia_f16.npy', b1.cart(Word).astype(np.float16))
np.save(OUT / 'ordit/DA_f16.npy', b1.cart(np.where(P3 | P2, np.where(P3, DA, DB2), 0)).astype(np.float16))
log('ordit fet', dict(taca_A_px_dos_testimonis=int(P2.sum())))
del DA, DB, DV, DB2, DV2, D3, D2, Dord, Word, c
# ------------------------------------------------------------------ TRAMA (tangencial), com el b9 (mapa radial continu), amb la taca d'A de B·V i els peus plens de nivell
FR_, FT_ = 2, 4; NRt, NTt = b1.NR // FR_, b1.NT // FT_; DRt = float(b1.dr * FR_); DTHt = 360.0 / NTt; RHOt = b1.rho.reshape(NRt, FR_).mean(1); RRt = (np.exp(RHOt) / RS)[:, None]
def gt(x, sr, st):
    p = int(4 * st) + 2; xp = np.concatenate([x[:, -p:], x, x[:, :p]], 1); return cv2.GaussianBlur(xp, (0, 0), sigmaX=float(st), sigmaY=float(sr), borderType=cv2.BORDER_REFLECT)[:, p:-p]
def gnt(x, M, sr, st):
    den = gt(M.astype(np.float32), sr, st); return gt(np.where(M, x, 0).astype(np.float32), sr, st) / np.maximum(den, 1e-6), den
def pla(L, mm):
    Mf = cv2.resize(b1.polar(mm.astype(np.float32)), (NTt, NRt), interpolation=cv2.INTER_AREA)
    P = cv2.resize(b1.polar(np.where(mm, np.log(np.maximum(L, 1e-9)), 0).astype(np.float32)), (NTt, NRt), interpolation=cv2.INTER_AREA)
    M = Mf > 0.999; return np.where(M, P / np.maximum(Mf, 1e-6), 0).astype(np.float32), M
def tangencial(x, M):
    xm = np.where(M, x, np.nan); med = np.nanmedian(xm, axis=1, keepdims=True); med = np.where(np.isfinite(med), med, 0); y = np.where(M, x - med, 0).astype(np.float32)
    S1, S2, S3, ST = 0.012 / DRt, 0.12 / DRt, 0.30 / DRt, 2.0 / DTHt
    a, _ = gnt(y, M, S1, ST); c, _ = gnt(y, M, S2, ST); T = np.where(M, a - c, 0).astype(np.float32); g_, den = gnt(T, M, S3, ST); T = np.where(M & (den > 0.3), T - g_, 0).astype(np.float32)
    Mk = M & (T != 0); n_ = Mk.sum(1, keepdims=True); mu = np.where(n_ > 0, np.where(Mk, T, 0).sum(1, keepdims=True) / np.maximum(n_, 1), 0); return np.where(Mk, T - mu, 0).astype(np.float32)
xA, M3t = pla(LA, mAll); xB, _ = pla(LB, mAll); xV, _ = pla(LV, mAll); xB2, M2t = pla(LB, mBV); xV2, _ = pla(LV, mBV)
TA, TB, TV = tangencial(xA, M3t), tangencial(xB, M3t), tangencial(xV, M3t); TB2, TV2 = tangencial(xB2, M2t), tangencial(xV2, M2t); del xA, xB, xV, xB2, xV2
def coht(u, v, M):
    WR, WT = 0.10 / DRt, 6.0 / DTHt; cov, den = gnt(u * v, M, WR, WT); vu, _ = gnt(u * u, M, WR, WT); vv, _ = gnt(v * v, M, WR, WT)
    w = np.clip(cov / np.maximum(0.5 * (vu + vv), 1e-12), 0, 1).astype(np.float32); w[~M] = 0; return w * np.clip((den - 0.6) / 0.4, 0, 1).astype(np.float32)
w3t = np.minimum(np.minimum(coht(TA, TB, M3t), coht(TA, TV, M3t)), coht(TB, TV, M3t)); T3 = minim([TA, TB, TV], w3t)
w2t = coht(TB2, TV2, M2t); T2 = minim([TB2, TV2], w2t)
Ttr = np.where(M3t, T3, np.where(M2t, T2, 0)).astype(np.float32); Mtr = M3t | M2t
# cartesià (la graella reduïda) i els peus plens de NIVELL: convolució normalitzada des de fora del peu (σ = el radi del peu / 2, com a mínim 20 px)
yq, xq = np.mgrid[0:H, 0:W].astype(np.float32); rc = np.hypot(xq - SOL[0], yq - SOL[1]); tc = np.mod(np.arctan2(-(yq - SOL[1]), xq - SOL[0]), 2 * np.pi); del yq, xq
IX = (tc / (2 * np.pi) * NTt).astype(np.float32); IY = ((np.log(np.maximum(rc, 1)) - RHOt[0]) / DRt).astype(np.float32); fora = (IY < 0) | (IY > NRt - 1); del rc, tc
def cartt(P): o = cv2.remap(np.concatenate([P, P[:, :2]], 1).astype(np.float32), IX, IY, cv2.INTER_LINEAR, borderValue=0); o[fora] = 0; return o
Tc = cartt(Ttr); Mc = cartt(Mtr.astype(np.float32)) > 0.5
# els peus: dins del suport de la trama (A∪B de la Sony i la Vixen, sense comptar les estrelles), omplerts de nivell
# (primera tirada: forat = peu & mB & mV; al centre de la S33 la resta de l'estrella deixava píxels invàlids a B o a la Vixen, i el peu hi quedava
#  neutre: un disc de +0,19 % al revés. Ara, TOT el peu dins del camp de la trama. El nivell, amb dues escales barrejades de manera contínua:
#  σ 30 px a la vora del peu i σ 120 px al centre dels peus grans (radis de fins a 206 px, on el σ 30 no arriba: el nucli de 4σ s'hi queda curt)
Mfora = Mc & ~peu
num = cv2.GaussianBlur(np.where(Mfora, Tc, 0).astype(np.float32), (0, 0), 30); den = cv2.GaussianBlur(Mfora.astype(np.float32), (0, 0), 30)
petit = lambda a: cv2.resize(a, (W // 4, H // 4), interpolation=cv2.INTER_AREA); gran = lambda a: cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR)
num2 = gran(cv2.GaussianBlur(petit(np.where(Mfora, Tc, 0).astype(np.float32)), (0, 0), 30)); den2 = gran(cv2.GaussianBlur(petit(Mfora.astype(np.float32)), (0, 0), 30))
w1 = np.clip(den / 0.2, 0, 1).astype(np.float32)
nivell = (w1 * num / np.maximum(den, 1e-6) + (1 - w1) * np.where(den2 > 1e-3, num2 / np.maximum(den2, 1e-6), 0)).astype(np.float32)
# el cercle d'1–2 px entre el peu i la màscara de la trama (que ve del pla polar reduït i no toca exactament el disc) també s'omple de nivell
# (segona tirada: a la S20 quedava un anell neutre, d'uns 95 px de radi, al voltant del peu)
prop = ndi.distance_transform_edt(~peu) <= 8
forat = (peu | (prop & ~Mc)) & (den2 > 0.2); del num, den, num2, den2, w1, prop
Tfinal = np.where(forat, nivell, np.where(Mc, Tc, 0)).astype(np.float32)
np.save(OUT / 'trama/D_minim_f32.npy', Tfinal); np.save(OUT / 'trama/DA_f16.npy', cartt(np.where(M3t, TA, np.where(M2t, TB2, 0))).astype(np.float16))
np.save(OUT / 'trama/TU_referencia_f16.npy', cartt(tangencial(*pla(GR, (GR > 0) & ~peu))).astype(np.float16))
rep = dict(guio=str(Path(__file__).relative_to(R)), entrades=dict(A=str((SV / 'sony_A_total_flat2d_v5.npy').relative_to(R)), B=str((SV / 'sony_B_total_v42.npy').relative_to(R)),
           V=str((S4 / 'vixen_starless.npy').relative_to(R)), models_sony=str(S4.relative_to(R)), referencia=str((S4 / 'fusion_starless.npy').relative_to(R))),
           estrelles=dict(restades_A=len(sA), restades_B=len(sB), peus_mesurables=len(RADIS), peus_grans=sum(v > R_PEU for v in RADIS.values())),
           taca_A=dict(centre=[round(float(GXn), 1), round(float(GYn), 1)], radi=320, regla='B·V (dos testimonis)'),
           registre_ordit_px=REG, trama_peus='nivell de gran escala del voltant (convolució normalitzada σ 30 px des de fora del peu), sense detall; tot el peu dins del camp de la trama; σ 30 px a la vora i 120 px al centre dels peus grans, barrejats de manera contínua; també el cercle de ≤ 8 px entre el peu i la màscara',
           segons=round(time.time() - t0, 1))
json.dump(rep, open(OUT / 'O1_REBUT.json', 'w'), ensure_ascii=False, indent=1); json.dump({f'{k[0]},{k[1]}': v for k, v in RADIS.items()}, open(OUT / 'O1_RADIS_HALO.json', 'w'))
log('fet', json.dumps(rep, ensure_ascii=False)[:600])
