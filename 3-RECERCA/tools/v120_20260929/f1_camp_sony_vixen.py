"""f1 (V120, 29-09-2026) · EL CAMP DE DESPLAÇAMENT DE LA SONY (A i B, per separat) CAP A LA GEOMETRIA DE LA VIXEN.
Encàrrec de Pere: corregir la distorsió òptica entre la Vixen i la Sony a la fusió; opció 3: «moure la Sony cap a la Vixen» (les capes de Pere,
fetes sobre la geometria de la Vixen a la corona interior, no es mouen). Regla 9 de postprocessat-corona.
Tres mesures independents, sobre els apilats de la fusió (A original de flat2d_v5, B v42, Vixen flat2d_v5), per a cada parella X→V (X = A, B):
  1. RAIGS (angle): el detall azimutal del b1 (0,15°–1,5°) de X i de V, sense estrelles (b5 de la V118), correlació per finestres de 5° × 0,08 ln r
     al pla log-polar (delmat ×4), desplaçaments de ±0,6°, subpíxel; es guarden les finestres amb correlació ≥ 0,6.
  2. ARCS (radi): el detall tangencial de la trama (b9 de la V119: 1,2–12 % de r, promig de 2° a l'arc, sense la part circular), correlació per
     finestres de 10° × 0,15 ln r, ±0,02 ln r; correlació ≥ 0,6.
  3. ESTRELLES: centroides subpíxel a cada apilat AMB estrelles (lluminància, pla de fons a l'anell 8–12 px, centroide de la llum positiva a
     r ≤ 4 px, iterat), a les 56 del catàleg V114 i a les posicions de la D4; S/N ≥ 10 a totes dues fonts.
Conveni: u = posició a V − posició a X (px). Per deformar X a la geometria de V: X'(q) = X(q − u(q)).
MODEL: u_t = r · δθ(ρ, θ) i u_r = r · δρ(ρ, θ), amb ρ = ln r normalitzat a [−1, 1] entre 1,3 i 8 R☉, i δθ, δρ = Σ_k Σ_j (a_kj cos kθ + b_kj sin kθ) P_j(ρ)
(harmònics k ≤ K, Legendre j ≤ J; fora de [1,3; 8] R☉, ρ es limita a l'extrem: δ constant). Mínims quadrats ponderats (finestres per la
nitidesa de la correlació; estrelles, 0,4 px). Es tria (K, J) per validació creuada: es deixen fora sectors sencers de 30° (un de cada 3).
Sortides: <carpeta>/F1_MESURES.npz (finestres i estrelles), F1_MODEL.json (coeficients per a A i B i el (K, J) triat), F1_REBUT.json (residus).
Ús: f1_camp_sony_vixen.py <carpeta_b5 de la V118> <carpeta_sortida>"""
import sys, json, time, importlib.util, numpy as np, cv2
from pathlib import Path
from numpy.polynomial import legendre as LG
B5D, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
sys.argv = [sys.argv[0], str(OUT / '_b5')]
R_ = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('b5', R_ / '3-RECERCA/tools/v118_20260929/b5_filtre_tres_testimonis.py'); b5 = importlib.util.module_from_spec(spec); spec.loader.exec_module(b5)
b1, R, H, W, SOL, RS = b5.b1, b5.R, b5.H, b5.W, b5.SOL, b5.RS
AP = R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats'
STACKS = dict(A=AP / 'sony_A_total.npy', B=AP / 'cau/sony_B_total_v42.npy', V=AP / 'vixen_total.npy')
RMIN, RMAX = 1.3, 8.0
t0 = time.time()
def log(*a): print(f'[{time.time() - t0:5.0f}s]', *a, flush=True)
# ------------------------------------------------------------------ entrades sense estrelles (b5 de la V118, amb els peus d'halo)
HALO = json.load(open(B5D / 'B5_AJUSTOS_ESTRELLES.json'))['halo']; RADIS = {tuple(int(v) for v in k.split(',')): d['radi'] for k, d in HALO.items()}
LA, LB, LV, m, _ = b5.entrades(RADIS); log('entrades')
# ------------------------------------------------------------------ 1. raigs: detall azimutal (b1) i correlació per finestres en angle
PM = b1.polar(m.astype(np.float32)) > 0.999; den_c = {}
def gn(x, sr, st_):
    if (sr, st_) not in den_c: den_c[(sr, st_)] = b1.gcv(PM.astype(np.float32), sr, st_)
    den = den_c[(sr, st_)]; return b1.gcv(np.where(PM, x, 0).astype(np.float32), sr, st_) / np.maximum(den, 1e-6), den
def detall_az(L):
    x = np.where(PM, np.log(np.maximum(b1.polar(L), 1e-9)), 0).astype(np.float32); a, _ = gn(x, b1.SR, b1.S1); c, _ = gn(x, b1.SR, b1.S2)
    return np.where(PM, a - c, 0).astype(np.float32)
DS = 4
def redueix(X): return cv2.resize(X, (X.shape[1] // DS, X.shape[0] // DS), interpolation=cv2.INTER_AREA)
def finestres(Xp, Up, Vm, eix, amp_graus_o_lnr, ft, fr, maxd, cmin, rho_rows, nt):
    """correlació per finestres: desplaçament s (en mostres del pla) que fa U(p) ≈ X(p + s) al llarg de l'eix (1 = θ, 0 = ρ).
    Torna llistes (fila, columna, s, cmax) als centres de finestra (graella a mig pas) amb cmax ≥ cmin."""
    nr_, nt_ = Xp.shape; wt = max(int(round(ft)), 3); wr = max(int(round(fr)), 3); ms = int(np.ceil(maxd))
    padt = wt
    def box(z):
        zp = np.concatenate([z[:, -padt:], z, z[:, :padt]], 1); return cv2.boxFilter(zp, -1, (wt, wr), normalize=True, borderType=cv2.BORDER_REFLECT)[:, padt:-padt]
    uu = box(np.where(Vm, Up * Up, 0)); cor = []
    for s in range(-ms, ms + 1):
        xs = np.roll(Xp, -s, axis=eix); vs = Vm & np.roll(Vm, -s, axis=eix)
        num = box(np.where(vs, xs * Up, 0)); xx = box(np.where(vs, xs * xs, 0)); cov = box(vs.astype(np.float32))
        cor.append(np.where(cov > 0.9, num / np.sqrt(np.maximum(xx * uu, 1e-20)), np.nan))
    cor = np.nan_to_num(np.stack(cor), nan=-1); i = np.argmax(cor, 0); cmax = np.take_along_axis(cor, i[None], 0)[0]
    ii = np.clip(i, 1, 2 * ms - 1); y0, y1, y2 = [np.take_along_axis(cor, (ii + k)[None], 0)[0] for k in (-1, 0, 1)]
    dd = y0 - 2 * y1 + y2; sub = np.where(np.abs(dd) > 1e-9, 0.5 * (y0 - y2) / np.where(np.abs(dd) > 1e-9, dd, 1), 0)
    s = ii + sub - ms; bo = (cmax >= cmin) & (i > 0) & (i < 2 * ms) & Vm
    rows = np.arange(wr // 2, nr_, max(wr // 2, 1)); cols = np.arange(wt // 2, nt_, max(wt // 2, 1))
    rr, cc = np.meshgrid(rows, cols, indexing='ij'); rr, cc = rr.ravel(), cc.ravel(); k = bo[rr, cc]
    return rr[k], cc[k], s[rr, cc][k].astype(np.float32), cmax[rr, cc][k].astype(np.float32)
DAz = {n: redueix(detall_az(L)) for n, L in (('A', LA), ('B', LB), ('V', LV))}; PMr = redueix(PM.astype(np.float32)) > 0.99
log('detall azimutal')
rho_red = b1.rho.reshape(-1, DS).mean(1); nt_red = b1.NT // DS; dth_red = 360.0 / nt_red
MES = {}
for X in ('A', 'B'):
    rr, cc, s, cm = finestres(DAz[X], DAz['V'], PMr, 1, None, 5.0 / dth_red, 0.08 / (b1.dr * DS), 0.6 / dth_red, 0.6, rho_red, nt_red)
    r_px = np.exp(rho_red[rr]); th = cc * 2 * np.pi / nt_red
    MES[f'ang_{X}'] = dict(r=r_px, th=th, dtheta=(-s * dth_red * np.pi / 180).astype(np.float64), c=cm)   # δθ = θ_V − θ_X (rad)
    log(f'raigs {X}→V: {len(s)} finestres; mediana δθ {np.degrees(np.median(-s * dth_red * np.pi / 180)):.3f}°')
del DAz
# ------------------------------------------------------------------ 2. arcs: detall tangencial (trama) i correlació per finestres en radi
FR_, FT_ = 2, 4; NRt, NTt = b1.NR // FR_, b1.NT // FT_; DRt = float(b1.dr * FR_); DTHt = 360.0 / NTt; RHOt = b1.rho.reshape(NRt, FR_).mean(1)
def gt(x, sr, st):
    p = int(4 * st) + 2; xp = np.concatenate([x[:, -p:], x, x[:, :p]], 1)
    return cv2.GaussianBlur(xp, (0, 0), sigmaX=float(st), sigmaY=float(sr), borderType=cv2.BORDER_REFLECT)[:, p:-p]
def gnt(x, M, sr, st):
    den = gt(M.astype(np.float32), sr, st); return gt(np.where(M, x, 0).astype(np.float32), sr, st) / np.maximum(den, 1e-6), den
def pla(L, mm):
    Mf = cv2.resize(b1.polar(mm.astype(np.float32)), (NTt, NRt), interpolation=cv2.INTER_AREA)
    P = cv2.resize(b1.polar(np.where(mm, np.log(np.maximum(L, 1e-9)), 0).astype(np.float32)), (NTt, NRt), interpolation=cv2.INTER_AREA)
    M = Mf > 0.999; return np.where(M, P / np.maximum(Mf, 1e-6), 0).astype(np.float32), M
def tangencial(x, M):
    xm = np.where(M, x, np.nan); med = np.nanmedian(xm, axis=1, keepdims=True); med = np.where(np.isfinite(med), med, 0)
    y = np.where(M, x - med, 0).astype(np.float32); S1, S2, S3, ST = 0.012 / DRt, 0.12 / DRt, 0.30 / DRt, 2.0 / DTHt
    a, _ = gnt(y, M, S1, ST); c, _ = gnt(y, M, S2, ST); T = np.where(M, a - c, 0).astype(np.float32)
    g, den = gnt(T, M, S3, ST); T = np.where(M & (den > 0.3), T - g, 0).astype(np.float32)
    Mk = M & (T != 0); n_ = Mk.sum(1, keepdims=True); mu = np.where(n_ > 0, np.where(Mk, T, 0).sum(1, keepdims=True) / np.maximum(n_, 1), 0)
    return np.where(Mk, T - mu, 0).astype(np.float32)
xA, Mt = pla(LA, m); xB, _ = pla(LB, m); xV, _ = pla(LV, m); del LA, LB, LV
T = {'A': tangencial(xA, Mt), 'B': tangencial(xB, Mt), 'V': tangencial(xV, Mt)}; del xA, xB, xV
log('detall tangencial')
for X in ('A', 'B'):
    rr, cc, s, cm = finestres(T[X], T['V'], Mt, 0, None, 10.0 / DTHt, 0.15 / DRt, 0.02 / DRt, 0.6, RHOt, NTt)
    r_px = np.exp(RHOt[rr]); th = cc * 2 * np.pi / NTt
    MES[f'rad_{X}'] = dict(r=r_px, th=th, drho=(-s * DRt).astype(np.float64), c=cm)   # δρ = ln r_V − ln r_X
    log(f'arcs {X}→V: {len(s)} finestres; mediana δρ·r {np.median(-s * DRt * r_px):.2f} px')
del T
# ------------------------------------------------------------------ 3. estrelles: centroides subpíxel a cada apilat amb estrelles
cat = json.load(open(R / '4-RESULTATS/v114_estrelles_20260928/CATALEG_ACCEPTAT_V114.json'))['stars']
pos = [(float(s_['x']), float(s_['y']), s_.get('TYC', '')) for s_ in cat]
yy8, xx8 = np.mgrid[-12:13, -12:13].astype(np.float64); rr8 = np.hypot(xx8, yy8); ring = (rr8 >= 8) & (rr8 <= 12)
Xr = np.stack([np.ones(ring.sum()), xx8[ring], yy8[ring]], 1)
def centroide(Lmm, x, y):
    """cerca el pic dins de r ≤ 10 px i en torna el centroide subpíxel (pla de fons a l'anell 8–12 px, llum positiva a r ≤ 4 px) i el S/N."""
    xi, yi = int(round(x)), int(round(y))
    if xi < 30 or yi < 30 or xi + 30 >= W or yi + 30 >= H: return None
    big = np.asarray(Lmm[yi - 22:yi + 23, xi - 22:xi + 23], np.float64)
    if not np.isfinite(big).all(): return None
    sm = cv2.GaussianBlur(big, (0, 0), 1.5); yb, xb = np.mgrid[-22:23, -22:23]; sm[np.hypot(xb, yb) > 10] = -np.inf
    j = np.unravel_index(np.argmax(sm), sm.shape); cx, cy = xi + xb[j], yi + yb[j]
    for _ in range(5):
        cxi, cyi = int(round(cx)), int(round(cy)); w = np.asarray(Lmm[cyi - 12:cyi + 13, cxi - 12:cxi + 13], np.float64)
        if w.shape != (25, 25) or not np.isfinite(w).all(): return None
        cf = np.linalg.lstsq(Xr, w[ring], rcond=None)[0]; z = w - (cf[0] + cf[1] * xx8 + cf[2] * yy8); sd = 1.4826 * np.median(np.abs(w[ring] - (Xr @ cf) - np.median(w[ring] - (Xr @ cf)))) + 1e-12
        dx, dy = xx8 - (cx - cxi), yy8 - (cy - cyi); mk = (np.hypot(dx, dy) <= 4) & (z > 0)
        if z[mk].sum() <= 0: return None
        ncx = cxi + (xx8[mk] * z[mk]).sum() / z[mk].sum(); ncy = cyi + (yy8[mk] * z[mk]).sum() / z[mk].sum()
        if np.hypot(ncx - cx, ncy - cy) < 0.01: cx, cy = ncx, ncy; break
        cx, cy = ncx, ncy
    return cx, cy, float(z[np.hypot(xx8 - (cx - cxi), yy8 - (cy - cyi)) <= 2].max() / sd)
def lumin(p):
    t = np.load(p, mmap_mode='r'); L = np.zeros((H, W), np.float32)
    for y0 in range(0, H, 1024): a = np.asarray(t[y0:y0 + 1024], np.float32); L[y0:y0 + 1024] = np.where(np.all(np.isfinite(a), 2), (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4, np.nan)
    return L
C = {}
for n, p in STACKS.items():
    L = lumin(p); C[n] = [centroide(L, x, y) for x, y, _ in pos]; del L
est = {}
for X in ('A', 'B'):
    rows = []
    for (x, y, tyc), cx, cv in zip(pos, C[X], C['V']):
        if cx and cv and cx[2] >= 10 and cv[2] >= 10 and np.hypot(cv[0] - cx[0], cv[1] - cx[1]) < 12: rows.append((cx[0], cx[1], cv[0] - cx[0], cv[1] - cx[1], tyc, cx[2], cv[2]))
    est[X] = rows; log(f'estrelles {X}→V: {len(rows)}')
MES['est_A'] = dict(x=np.array([r_[0] for r_ in est['A']]), y=np.array([r_[1] for r_ in est['A']]), ux=np.array([r_[2] for r_ in est['A']]), uy=np.array([r_[3] for r_ in est['A']]))
MES['est_B'] = dict(x=np.array([r_[0] for r_ in est['B']]), y=np.array([r_[1] for r_ in est['B']]), ux=np.array([r_[2] for r_ in est['B']]), uy=np.array([r_[3] for r_ in est['B']]))
np.savez(OUT / 'F1_MESURES.npz', **{f'{k}__{kk}': vv for k, v in MES.items() for kk, vv in v.items()})
json.dump({X: [dict(x=r_[0], y=r_[1], ux=r_[2], uy=r_[3], TYC=r_[4], sn_X=r_[5], sn_V=r_[6]) for r_ in est[X]] for X in est}, open(OUT / 'F1_ESTRELLES.json', 'w'), ensure_ascii=False, indent=0)
# ------------------------------------------------------------------ model: δθ(ρ, θ) i δρ(ρ, θ) harmònics × Legendre
def rho_n(r_px): return np.clip((np.log(np.clip(r_px / RS, RMIN, RMAX)) - np.log(RMIN)) / (np.log(RMAX) - np.log(RMIN)) * 2 - 1, -1, 1)
def base(r_px, th, K, J):
    P = np.stack([LG.legval(rho_n(r_px), np.eye(J + 1)[j]) for j in range(J + 1)], 1); cols = []
    for k in range(K + 1):
        for j in range(J + 1):
            cols.append(np.cos(k * th) * P[:, j])
            if k > 0: cols.append(np.sin(k * th) * P[:, j])
    return np.stack(cols, 1)
def sistema(X, K, J, excl=None):
    """equacions: [δθ | δρ] = [Bθ 0; 0 Bρ] p. Finestres d'angle: δθ; de radi: δρ; estrelles: totes dues (u_t/r, u_r/r). Pesos 1/σ."""
    a, r_ = MES[f'ang_{X}'], MES[f'rad_{X}']; e = MES[f'est_{X}']; nb = base(np.array([RS * 2]), np.array([0.]), K, J).shape[1]
    rows, rhs, wts, grup = [], [], [], []
    def sector(th): return (np.floor(np.degrees(th) % 360 / 30).astype(int))
    Ba = base(a['r'], a['th'], K, J); sa = np.clip(np.radians(0.03) * (1 - a['c']) / 0.1, np.radians(0.008), np.radians(0.1))
    rows.append(np.hstack([Ba, np.zeros_like(Ba)])); rhs.append(a['dtheta']); wts.append(1 / sa); grup.append(sector(a['th']))
    Br = base(r_['r'], r_['th'], K, J); sr = np.clip(0.004 * (1 - r_['c']) / 0.1, 0.001, 0.01)
    rows.append(np.hstack([np.zeros_like(Br), Br])); rhs.append(r_['drho']); wts.append(1 / sr); grup.append(sector(r_['th']))
    if len(e['x']):
        dx, dy = e['x'] - SOL[0], -(e['y'] - SOL[1]); rr = np.hypot(dx, dy); th = np.arctan2(dy, dx)
        ut = -np.sin(th) * e['ux'] + np.cos(th) * (-e['uy']); ur = np.cos(th) * e['ux'] + np.sin(th) * (-e['uy'])   # y cap amunt
        Be = base(rr, th, K, J); se = 0.4 / rr
        rows += [np.hstack([Be, np.zeros_like(Be)]), np.hstack([np.zeros_like(Be), Be])]; rhs += [ut / rr, ur / rr]; wts += [1 / se, 1 / se]; grup += [sector(th), sector(th)]
    Am = np.vstack(rows); bv = np.concatenate(rhs); wv = np.concatenate(wts); gv = np.concatenate(grup)
    return Am, bv, wv, gv, nb
def ajusta(Am, bv, wv, k=None):
    k = np.ones(len(bv), bool) if k is None else k
    p = np.linalg.lstsq(Am[k] * wv[k, None], bv[k] * wv[k], rcond=None)[0]
    for _ in range(3):   # robust: fora els > 4σ
        res = (Am @ p - bv) * wv; kk = k & (np.abs(res) < 4 * 1.4826 * np.median(np.abs(res[k])) + 1e-12)
        p = np.linalg.lstsq(Am[kk] * wv[kk, None], bv[kk] * wv[kk], rcond=None)[0]
    return p
res_cv = {}
for X in ('A', 'B'):
    for K in (1, 2, 3, 4):
        for J in (0, 1, 2):
            Am, bv, wv, gv, nb = sistema(X, K, J); errs = []
            for fold in range(3):
                tr = (gv % 3) != fold; p = ajusta(Am, bv, wv, tr); te = ~tr
                errs.append(np.median(np.abs((Am[te] @ p - bv[te]) * wv[te])))
            res_cv[f'{X}_K{K}_J{J}'] = float(np.mean(errs))
    log(X, 'validació creuada (error mitjà normalitzat, menys és millor):', {k: round(v, 3) for k, v in res_cv.items() if k.startswith(X)})
millor = {X: min(((K, J) for K in (1, 2, 3, 4) for J in (0, 1, 2)), key=lambda kj: res_cv[f'{X}_K{kj[0]}_J{kj[1]}']) for X in ('A', 'B')}
model = dict(conveni='u = posició a V − posició a X (px, x cap a la dreta, y cap avall); X\'(q) = X(q − u(q))', SOL=list(SOL), RS=RS, rho=[RMIN, RMAX], models={})
rep = dict(guio=str(Path(__file__).relative_to(R)), mesures={k: int(len(v[list(v)[0]])) for k, v in MES.items()}, validacio_creuada=res_cv, triat=millor, residus={})
def camp(Xmodel, x, y):
    dx, dy = x - SOL[0], -(y - SOL[1]); rr = np.hypot(dx, dy); th = np.arctan2(dy, dx); K, J = Xmodel['K'], Xmodel['J']
    Bb = base(rr.ravel(), th.ravel(), K, J); dth = (Bb @ np.array(Xmodel['p_theta'])).reshape(rr.shape); drh = (Bb @ np.array(Xmodel['p_rho'])).reshape(rr.shape)
    ut, ur = rr * dth, rr * drh; ux = np.cos(th) * ur - np.sin(th) * ut; uy_up = np.sin(th) * ur + np.cos(th) * ut
    return ux, -uy_up
for X in ('A', 'B'):
    K, J = millor[X]; Am, bv, wv, gv, nb = sistema(X, K, J); p = ajusta(Am, bv, wv)
    model['models'][X] = dict(K=K, J=J, p_theta=p[:nb].tolist(), p_rho=p[nb:].tolist())
    # residus en px, per mesura i tram de radi
    a, r_, e = MES[f'ang_{X}'], MES[f'rad_{X}'], MES[f'est_{X}']
    pa = base(a['r'], a['th'], K, J) @ p[:nb]; pr = base(r_['r'], r_['th'], K, J) @ p[nb:]
    ra_px = (a['dtheta'] - pa) * a['r']; rr_px = (r_['drho'] - pr) * r_['r']; ab_px = a['dtheta'] * a['r']; rb_px = r_['drho'] * r_['r']
    tr = {}
    for lo, hi in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 6), (6, 8)):
        ka = (a['r'] >= lo * RS) & (a['r'] < hi * RS); kr = (r_['r'] >= lo * RS) & (r_['r'] < hi * RS)
        tr[f'{lo}-{hi}'] = dict(raigs_n=int(ka.sum()), raigs_abans_px_mediana_p90=[round(float(np.median(np.abs(ab_px[ka]))), 2), round(float(np.percentile(np.abs(ab_px[ka]), 90)), 2)] if ka.sum() else None,
                                raigs_residu_px_mediana_p90=[round(float(np.median(np.abs(ra_px[ka]))), 2), round(float(np.percentile(np.abs(ra_px[ka]), 90)), 2)] if ka.sum() else None,
                                arcs_n=int(kr.sum()), arcs_abans_px_mediana_p90=[round(float(np.median(np.abs(rb_px[kr]))), 2), round(float(np.percentile(np.abs(rb_px[kr]), 90)), 2)] if kr.sum() else None,
                                arcs_residu_px_mediana_p90=[round(float(np.median(np.abs(rr_px[kr]))), 2), round(float(np.percentile(np.abs(rr_px[kr]), 90)), 2)] if kr.sum() else None)
    if len(e['x']):
        ux, uy = camp(model['models'][X], e['x'], e['y']); d = np.hypot(e['ux'] - ux, e['uy'] - uy)
        tr['estrelles'] = dict(n=int(len(d)), abans_rms_px=round(float(np.sqrt(np.mean(e['ux'] ** 2 + e['uy'] ** 2))), 2), residu_rms_px=round(float(np.sqrt(np.mean(d ** 2))), 2), residu_max_px=round(float(d.max()), 2))
    # el camp a radis clau (px): mediana i màxim del mòdul al llarg de l'arc
    th = np.linspace(0, 2 * np.pi, 360, endpoint=False); mag = {}
    for rR in (1.0, 1.1, 1.5, 2, 3, 4, 6, 8, 12):
        ux, uy = camp(model['models'][X], SOL[0] + rR * RS * np.cos(th), SOL[1] - rR * RS * np.sin(th)); mm = np.hypot(ux, uy); mag[str(rR)] = [round(float(np.median(mm)), 2), round(float(mm.max()), 2)]
    tr['modul_camp_px_mediana_max_per_radi'] = mag; rep['residus'][X] = tr
    log(X, json.dumps(tr, ensure_ascii=False)[:900])
json.dump(model, open(OUT / 'F1_MODEL.json', 'w'), ensure_ascii=False, indent=1)
rep['segons'] = round(time.time() - t0, 1); json.dump(rep, open(OUT / 'F1_REBUT.json', 'w'), ensure_ascii=False, indent=1)
log('fet')
