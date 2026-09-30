"""f2 (V120, 29-09-2026) · MODEL DEL CAMP SONY → VIXEN, AMB LES MESURES DEL f1 (i més estrelles).
El f1 va mostrar que:
  · els RAIGS (detall azimutal) mesuren bé la component tangencial a tots els radis (5.300 finestres per parella);
  · els ARCS (detall tangencial) només són fiables a prop del Sol: més enllà de 2 R☉ donen «desplaçaments radials» de 12–20 px que les estrelles
    desmenteixen (el detall tangencial hi és feble i la correlació troba pics falsos);
  · amb S/N ≥ 10 a totes dues fonts només hi havia 10–11 estrelles.
Aquí:
  1. ESTRELLES amb S/N ≥ 6 a totes dues fonts (el centroide del f1), al catàleg V114 i a les posicions de les llistes D4 (fusió, Sony i Vixen);
  2. ARCS només a r < 2,5 R☉ i correlació ≥ 0,8;
  3. models CARTESIANS centrats al Sol (u = posició a V − posició a X, en px): afí (6 paràmetres), quadràtic (12) i cúbic (20); i el polar del f1
     (K = 1, J = 2), per comparar. Validació creuada per sectors de 30° (un de cada 3 fora) i, a més, deixant fora totes les estrelles (el model
     s'ha de sostenir sense elles: la component radial ve de les estrelles i dels arcs interiors).
  4. Residus SISTEMÀTICS (la mediana per caselles de 30° × tram de radi, que treu el soroll de cada finestra), que és el que mira la porta.
Ús: f2_model_camp.py <carpeta_f1> → F2_MODEL.json, F2_REBUT.json, F2_ESTRELLES.json"""
import sys, json, time, numpy as np, cv2
from pathlib import Path
from numpy.polynomial import legendre as LG
F1 = Path(sys.argv[1]).resolve(); R = Path(__file__).resolve().parents[3]; t0 = time.time()
SOL = (5361.768111973117, 3775.747534140857); RS = 440.603; H, W = 7506, 10551
def log(*a): print(f'[{time.time() - t0:5.0f}s]', *a, flush=True)
Z = np.load(F1 / 'F1_MESURES.npz'); MES = {}
for k in Z.files:
    a, b = k.split('__'); MES.setdefault(a, {})[b] = Z[k]
# ---------------------------------------------------------------- 1. estrelles amb S/N ≥ 6 (centroide del f1)
AP = R / '4-RESULTATS/v108_20260926/flat2d_v5/apilats'; STACKS = dict(A=AP / 'sony_A_total.npy', B=AP / 'cau/sony_B_total_v42.npy', V=AP / 'vixen_total.npy')
pos = {}
for s_ in json.load(open(R / '4-RESULTATS/v114_estrelles_20260928/CATALEG_ACCEPTAT_V114.json'))['stars']: pos[(round(s_['x']), round(s_['y']))] = (float(s_['x']), float(s_['y']), s_.get('TYC', ''))
for row in json.load(open(R / '4-RESULTATS/v114_estrelles_20260928/fonts_c/fusio/d4/products/D4_sources.json'))['selected']:
    st = row['star']; k = (int(st['x']), int(st['y']))
    if not any(abs(k[0] - q[0]) < 6 and abs(k[1] - q[1]) < 6 for q in pos): pos[k] = (float(st['x']), float(st['y']), st.get('TYC', ''))
pos = list(pos.values()); log('posicions d\'estrelles a mesurar', len(pos))
yy8, xx8 = np.mgrid[-12:13, -12:13].astype(np.float64); rr8 = np.hypot(xx8, yy8); ring = (rr8 >= 8) & (rr8 <= 12); Xr = np.stack([np.ones(ring.sum()), xx8[ring], yy8[ring]], 1)
def centroide(Lmm, x, y):
    xi, yi = int(round(x)), int(round(y))
    if xi < 30 or yi < 30 or xi + 30 >= W or yi + 30 >= H: return None
    big = np.asarray(Lmm[yi - 22:yi + 23, xi - 22:xi + 23], np.float64)
    if not np.isfinite(big).all(): return None
    sm = cv2.GaussianBlur(big, (0, 0), 1.5); yb, xb = np.mgrid[-22:23, -22:23]; sm[np.hypot(xb, yb) > 10] = -np.inf
    j = np.unravel_index(np.argmax(sm), sm.shape); cx, cy = xi + xb[j], yi + yb[j]
    for _ in range(6):
        cxi, cyi = int(round(cx)), int(round(cy)); w = np.asarray(Lmm[cyi - 12:cyi + 13, cxi - 12:cxi + 13], np.float64)
        if w.shape != (25, 25) or not np.isfinite(w).all(): return None
        cf = np.linalg.lstsq(Xr, w[ring], rcond=None)[0]; z = w - (cf[0] + cf[1] * xx8 + cf[2] * yy8); rs_ = w[ring] - Xr @ cf; sd = 1.4826 * np.median(np.abs(rs_ - np.median(rs_))) + 1e-12
        dx, dy = xx8 - (cx - cxi), yy8 - (cy - cyi); mk = (np.hypot(dx, dy) <= 4) & (z > 0)
        if z[mk].sum() <= 0: return None
        ncx = cxi + (xx8[mk] * z[mk]).sum() / z[mk].sum(); ncy = cyi + (yy8[mk] * z[mk]).sum() / z[mk].sum()
        done = np.hypot(ncx - cx, ncy - cy) < 0.01; cx, cy = ncx, ncy
        if done: break
    cxi, cyi = int(round(cx)), int(round(cy)); w = np.asarray(Lmm[cyi - 12:cyi + 13, cxi - 12:cxi + 13], np.float64); cf = np.linalg.lstsq(Xr, w[ring], rcond=None)[0]
    z = w - (cf[0] + cf[1] * xx8 + cf[2] * yy8); rs_ = w[ring] - Xr @ cf; sd = 1.4826 * np.median(np.abs(rs_ - np.median(rs_))) + 1e-12
    return cx, cy, float(z[rr8 <= 2].max() / sd)
def lumin(p):
    t = np.load(p, mmap_mode='r'); L = np.zeros((H, W), np.float32)
    for y0 in range(0, H, 1024): a = np.asarray(t[y0:y0 + 1024], np.float32); L[y0:y0 + 1024] = np.where(np.all(np.isfinite(a), 2), (a[..., 0] + 2 * a[..., 1] + a[..., 2]) / 4, np.nan)
    return L
C = {}
for n, p in STACKS.items():
    L = lumin(p); C[n] = [centroide(L, x, y) for x, y, _ in pos]; del L
EST = {}
for X in ('A', 'B'):
    rows = [dict(x=cx[0], y=cx[1], ux=cv[0] - cx[0], uy=cv[1] - cx[1], TYC=tyc, sn_X=cx[2], sn_V=cv[2])
            for (x, y, tyc), cx, cv in zip(pos, C[X], C['V']) if cx and cv and cx[2] >= 6 and cv[2] >= 6 and np.hypot(cv[0] - cx[0], cv[1] - cx[1]) < 12]
    EST[X] = rows; log(f'estrelles {X}→V amb S/N ≥ 6: {len(rows)}')
json.dump(EST, open(F1.parent / 'F2_ESTRELLES.json', 'w'), ensure_ascii=False, indent=0) if False else json.dump(EST, open(F1 / 'F2_ESTRELLES.json', 'w'), ensure_ascii=False, indent=0)
# ---------------------------------------------------------------- equacions
def polar_de(x, y):
    dx, dy = x - SOL[0], -(y - SOL[1]); return np.hypot(dx, dy), np.arctan2(dy, dx)
def base_cart(x, y, grau):
    X_, Y_ = (x - SOL[0]) / 2000.0, (y - SOL[1]) / 2000.0; cols = []
    for i in range(grau + 1):
        for j in range(grau + 1 - i): cols.append(X_ ** i * Y_ ** j)
    return np.stack(cols, 1)
def rho_n(r_px): return np.clip((np.log(np.clip(r_px / RS, 1.3, 8.0)) - np.log(1.3)) / (np.log(8.0) - np.log(1.3)) * 2 - 1, -1, 1)
def base_pol(r_px, th, K=1, J=2):
    P = np.stack([LG.legval(rho_n(r_px), np.eye(J + 1)[j]) for j in range(J + 1)], 1); cols = []
    for k in range(K + 1):
        for j in range(J + 1):
            cols.append(np.cos(k * th) * P[:, j])
            if k > 0: cols.append(np.sin(k * th) * P[:, j])
    return np.stack(cols, 1)
def xy_de(r_px, th): return SOL[0] + r_px * np.cos(th), SOL[1] - r_px * np.sin(th)
KT, JT = 2, 1   # correcció tangencial dels híbrids: harmònics k ≤ 2, Legendre j ≤ 1
def sistema(X, tipus, grau, amb_estrelles=True):
    """files: [components del model] · p = observació (px). Cartesià: u_x = Bc·px, u_y = Bc·py (y cap avall). Polar: δθ, δρ (rad, ln r)."""
    a, r_ = MES[f'ang_{X}'], MES[f'rad_{X}']; kr = (r_['r'] < 2.5 * RS) & (r_['c'] >= 0.8)
    rows, obs, sig, sec, tip = [], [], [], [], []
    def proj_rows(x, y, ex, ey):   # observació d'una component (e = vector unitari en px, y cap avall) del desplaçament
        if tipus == 'cart':
            Bc = base_cart(x, y, grau); return np.hstack([Bc * ex[:, None], Bc * ey[:, None]])
        if tipus == 'hib':
            Bc = base_cart(x, y, grau); r0, th0 = polar_de(x, y); Bt = base_pol(r0, th0, KT, JT); et = (-np.sin(th0), -np.cos(th0)); ct = ex * et[0] + ey * et[1]
            return np.hstack([Bc * ex[:, None], Bc * ey[:, None], Bt * (r0 * ct)[:, None]])
        r0, th0 = polar_de(x, y); Bp = base_pol(r0, th0)
        # e_t = (−sin θ, −cos θ) en px amb y cap avall; e_r = (cos θ, −sin θ)
        et = (-np.sin(th0), -np.cos(th0)); er = (np.cos(th0), -np.sin(th0))
        ct = ex * et[0] + ey * et[1]; cr = ex * er[0] + ey * er[1]
        return np.hstack([Bp * (r0 * ct)[:, None], Bp * (r0 * cr)[:, None]])
    # raigs: component tangencial en px (u_t = r δθ)
    x, y = xy_de(a['r'], a['th']); et = (-np.sin(a['th']), -np.cos(a['th']))
    rows.append(proj_rows(x, y, et[0], et[1])); obs.append(a['r'] * a['dtheta']); sig.append(np.clip(0.3 * (1 - a['c']) / 0.1, 0.1, 1.5) * np.maximum(a['r'] / (2 * RS), 1))
    sec.append(np.floor(np.degrees(a['th']) % 360 / 30).astype(int)); tip.append(np.zeros(len(x), int))
    # arcs (només r < 2,5 R☉ i c ≥ 0,8): component radial en px
    x, y = xy_de(r_['r'][kr], r_['th'][kr]); er = (np.cos(r_['th'][kr]), -np.sin(r_['th'][kr]))
    rows.append(proj_rows(x, y, er[0], er[1])); obs.append(r_['r'][kr] * r_['drho'][kr]); sig.append(np.full(kr.sum(), 1.0))
    sec.append(np.floor(np.degrees(r_['th'][kr]) % 360 / 30).astype(int)); tip.append(np.ones(kr.sum(), int))
    if amb_estrelles and EST[X]:
        ex_ = np.array([e['x'] for e in EST[X]]); ey_ = np.array([e['y'] for e in EST[X]]); _, th_e = polar_de(ex_, ey_)
        for comp, obsv in ((0, np.array([e['ux'] for e in EST[X]])), (1, np.array([e['uy'] for e in EST[X]]))):
            e1 = np.full(len(ex_), 1.0 if comp == 0 else 0.0); e2 = np.full(len(ex_), 0.0 if comp == 0 else 1.0)
            rows.append(proj_rows(ex_, ey_, e1, e2)); obs.append(obsv); sig.append(np.array([max(0.35, 3.0 / e['sn_V']) for e in EST[X]]))
            sec.append(np.floor(np.degrees(th_e) % 360 / 30).astype(int)); tip.append(np.full(len(ex_), 2))
    return np.vstack(rows), np.concatenate(obs), np.concatenate(sig), np.concatenate(sec), np.concatenate(tip)
def ajusta(Am, b, s, k):
    w = 1 / s; p = np.linalg.lstsq(Am[k] * w[k, None], b[k] * w[k], rcond=None)[0]
    for _ in range(4):
        res = (Am @ p - b) * w; kk = k & (np.abs(res) < 4 * 1.4826 * np.median(np.abs(res[k])) + 1e-9); p = np.linalg.lstsq(Am[kk] * w[kk, None], b[kk] * w[kk], rcond=None)[0]
    return p
MODELS = [('cart', 1), ('cart', 2), ('pol', None), ('hib', 1), ('hib', 2)]
rep = dict(guio=str(Path(__file__).relative_to(R)), estrelles={X: len(EST[X]) for X in EST}, cv={}, sistematic={})
res_final = {}
for X in ('A', 'B'):
    for tipus, grau in MODELS:
        nom = f'{tipus}{grau or ""}'; Am, b, s, sec, tip = sistema(X, tipus, grau); errs = []; errs_e = []
        for fold in range(3):
            tr = (sec % 3) != fold; p = ajusta(Am, b, s, tr); te = ~tr
            errs.append(float(np.median(np.abs(Am[te] @ p - b[te]))))
        # sense estrelles: prediu les estrelles?
        kno = tip != 2; p = ajusta(Am, b, s, kno); ke = tip == 2
        if ke.any(): errs_e.append(float(np.sqrt(np.mean((Am[ke] @ p - b[ke]) ** 2))))
        rep['cv'][f'{X}_{nom}'] = dict(error_mediana_px_sectors_fora=round(float(np.mean(errs)), 3), rms_estrelles_px_sense_estrelles=round(errs_e[0], 2) if errs_e else None)
    log(X, {k: v for k, v in rep['cv'].items() if k.startswith(X)})
# tria: el de menys error de sectors fora; a igualtat (±3 %), el més simple; i que predigui les estrelles sense haver-les vist
def tria(X):
    # candidats: els que prediuen les estrelles SENSE haver-les vist amb un rms ≤ 3 px (la component radial no s'escapa)
    c = [(nom, rep['cv'][f'{X}_{nom}']) for nom in ('cart1', 'cart2', 'hib1', 'hib2', 'pol')]
    c = [(nom, v) for nom, v in c if v['rms_estrelles_px_sense_estrelles'] is not None and v['rms_estrelles_px_sense_estrelles'] <= 3.0]
    best = min(v['error_mediana_px_sectors_fora'] for _, v in c)
    return next(nom for nom, v in c if v['error_mediana_px_sectors_fora'] <= best * 1.03)
TRIAT = {X: tria(X) for X in ('A', 'B')}; log('triat', TRIAT)
model = dict(conveni='u = posició a V − posició a X (px, x cap a la dreta, y cap avall); X\'(q) = X(q − u(q))', SOL=list(SOL), RS=RS, escala_cart=2000.0, models={})
for X in ('A', 'B'):
  for nom in ('cart1', 'cart2', 'hib1', 'hib2', 'pol'):
    tipus = 'pol' if nom == 'pol' else nom[:-1]; grau = None if tipus == 'pol' else int(nom[-1])
    Am, b, s, sec, tip = sistema(X, tipus, grau); p = ajusta(Am, b, s, np.ones(len(b), bool))
    if tipus == 'cart': nb = len(p) // 2; mdl = dict(tipus=tipus, grau=grau, px=p[:nb].tolist(), py=p[nb:].tolist())
    elif tipus == 'hib': nc = base_cart(np.array([SOL[0] + 1.0]), np.array([SOL[1]]), grau).shape[1]; mdl = dict(tipus='hib', grau=grau, KT=KT, JT=JT, px=p[:nc].tolist(), py=p[nc:2 * nc].tolist(), pt=p[2 * nc:].tolist())
    else: nb = len(p) // 2; mdl = dict(tipus='pol', K=1, J=2, p_theta=p[:nb].tolist(), p_rho=p[nb:].tolist())
    if nom == TRIAT[X]: model['models'][X] = mdl
    model.setdefault('tots', {}).setdefault(X, {})[nom] = mdl
    r_obs = b - Am @ p
    # residus sistemàtics: mediana per casella (30° × tram), per tipus
    a = MES[f'ang_{X}']; na = len(a['r']); ra = r_obs[:na]; tb = {}
    for lo, hi in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 6), (6, 8)):
        k = (a['r'] >= lo * RS) & (a['r'] < hi * RS); meds = []; abans = []
        for sct in range(12):
            kk = k & (np.floor(np.degrees(a['th']) % 360 / 30) == sct)
            if kk.sum() >= 15: meds.append(np.median(ra[kk])); abans.append(np.median((a['r'] * a['dtheta'])[kk]))
        tb[f'{lo}-{hi}'] = dict(caselles=len(meds), abans_px_mediana_max=[round(float(np.median(np.abs(abans))), 2), round(float(np.max(np.abs(abans))), 2)] if abans else None,
                               residu_px_mediana_max=[round(float(np.median(np.abs(meds))), 2), round(float(np.max(np.abs(meds))), 2)] if meds else None,
                               soroll_finestra_px_mediana=round(float(np.median(np.abs(ra[k]))), 2) if k.any() else None)
    ke = tip == 2
    if ke.any():
        d = r_obs[ke].reshape(2, -1); bb = b[ke].reshape(2, -1)
        tb['estrelles'] = dict(n=int(ke.sum() // 2), residu_rms_px=round(float(np.sqrt(np.mean(np.sum(d ** 2, 0)))), 2), residu_max_px=round(float(np.sqrt(np.sum(d ** 2, 0)).max()), 2),
                               abans_rms_px=round(float(np.sqrt(np.mean(np.sum(bb ** 2, 0)))), 2))
    rep['sistematic'].setdefault(X, {})[nom] = tb
    log(X, nom, json.dumps({k: (v.get('residu_px_mediana_max') if 'residu_px_mediana_max' in v else [v.get('residu_rms_px'), v.get('residu_max_px')]) for k, v in tb.items()}, ensure_ascii=False)[:900])
json.dump(model, open(F1 / 'F2_MODEL.json', 'w'), ensure_ascii=False, indent=1)
rep['triat'] = TRIAT; rep['segons'] = round(time.time() - t0, 1); json.dump(rep, open(F1 / 'F2_REBUT.json', 'w'), ensure_ascii=False, indent=1)
log('fet')
