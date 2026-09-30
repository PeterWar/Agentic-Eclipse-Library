"""m1_mesura_flat2d_v4 (V108, flat2d_v4) · CÒPIA de m1_mesura_flat2d_v3.py: les MATEIXES mesures, amb la MATEIXA geometria fixa i els mateixos nuls,
ara amb DESPRÉS = v3 i v4 (control = la V107). Canvis: les carpetes; el segon píxel de la protuberància és (4897, 3785) (el que la franja perd:
p1_franja_protuberancia), i a L s'hi afegeixen els valors d'aquests 2 píxels a la base (capa 3), als 16 filtres i al compost.
─── Text de la v3 ───
m1_mesura_flat2d_v3 (V108, flat2d_v3) · ABANS (control = la V107) i DESPRÉS (v3), amb la v2 al costat, AMB GEOMETRIA FIXA I NULS A LA MATEIXA IMATGE.
Les mesures són les del verificador de la ronda 2 (verifica2_marrons/w2c, w3, w4, w8, w9) i les de la v2 (m1 V), amb els camins parametritzats:
  T · els sis traços amb GEOMETRIA FIXA (t0 = V0_minim_t de la V93 C5, sense cerca): DoG σ3−σ30 del ln, solc = mitjana |t| ≤ 6 − flancs
      20–80 px; nuls a cada imatge: 28 paral·leles i 300 segments a l'atzar (llavor 4242). També T1 a A − B.
  S · prova cura/injecció s = (E_després − E_abans)/|Δ|² per bandes (DoG del ln 0–1 … 16–32 px) i anells (R☉), amb el nul desplaçat (53, −37):
      −1 = cura, +1 = injecció. Als apilats, la base, el compost i les capes 54 i 56. (La banda 0–1 px és el soroll de píxel.)
  K · el mateix al COLOR: ln R/G i ln B/G de fusion_starless, bandes σ2–20 i σ20–200, per anells; i el nivell i el color a gran escala (σ100).
  B · Brno (L230–L232 de l'estat de control) contra compost i base, DoG σ1–8 i σ2–16, per anells; nul = Brno desplaçat (41, −27).
  F · plomalls: contrast azimutal del ln per anells de 0,1 R☉ (després/abans) i correlació dels perfils.   P · perles (300, 0–60 px del limbe).
  L · limbe: rms de després/abans − 1 per bandes de distància; els dos píxels de la protuberància; alfes que canvien (capes 41–56).
  V · el graó de textura a la vora del camp de la Vixen (MAD del DoG σ2–16 per calaixos de distància a la vora; dins/fora − 1).
  Q · taques de pols del canvi (w8 a la Vixen, w9 a la Sony A: fracció curada global i les taques noves amb z) i els quatre punts del verificador.
Ús: m1_mesura_flat2d_v3.py T|S|K|B|F|P|L|V|Q [...]   Sortida: 4-RESULTATS/v108_20260926/flat2d_v3/M1_<mesura>.json   (només lectura; ≤ ~10 GB)"""
import sys, json
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import distance_transform_edt as edt
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/flat2d_v4'; F3 = A / '4-RESULTATS/v108_20260926/flat2d_v3'
W, H = 10551, 7506; SOL = np.array([5361.768, 3775.748]); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
CAD = A / '4-RESULTATS/v108_20260926/cadena'; CR = A / '4-RESULTATS/v97_refundacio_20260924'; F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'
VAR = {'control': dict(cad=CAD / 'control', vixen=CR / 'proves_apilat/vixen_comuna_taula_original/vixen_total.npy', sony_A=CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy',
                       sony_B=CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy', compost=F2 / 'compost_control.npy'),
       'v2': dict(cad=CAD / 'flat2d_v2', vixen=F2 / 'apilats/vixen_total.npy', sony_A=F2 / 'apilats/sony_A_total.npy', sony_B=F2 / 'apilats/cau/sony_B_total_v42.npy', compost=F2 / 'compost_flat2d_v2.npy'),
       'v3': dict(cad=CAD / 'flat2d_v3', vixen=F3 / 'apilats/vixen_total.npy', sony_A=F3 / 'apilats/sony_A_total.npy', sony_B=F3 / 'apilats/cau/sony_B_total_v42.npy', compost=F3 / 'compost_flat2d_v3.npy'),
       'v4': dict(cad=CAD / 'flat2d_v4', vixen=OUT / 'apilats/vixen_total.npy', sony_A=OUT / 'apilats/sony_A_total.npy', sony_B=OUT / 'apilats/cau/sony_B_total_v42.npy', compost=OUT / 'compost_flat2d_v4.npy')}
def cami(v, nom):
    d = VAR[v]
    if nom in ('vixen_G', 'sonyA_G', 'sonyB_G'): return d[{'vixen_G': 'vixen', 'sonyA_G': 'sony_A', 'sonyB_G': 'sony_B'}[nom]], 1
    if nom == 'compost': return d['compost'], None
    if nom == 'base_G': return d['cad'] / 'lineal/base_G.npy', None
    if nom.startswith('L') and nom[1:3].isdigit(): return d['cad'] / f'estat_v108/{nom[:3]}_G.npy', None
    raise KeyError(nom)
def ld(v, nom):
    p, ch = cami(v, nom); a = np.load(p, mmap_mode='r'); return np.asarray(a if ch is None else a[..., ch], np.float32)
def lnm(img):
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
def ng(l, m, s): return cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
def rms(x): return float(np.sqrt(np.mean(x.astype(np.float64) ** 2))) if x.size else None
def mad(x): return float(1.4826 * np.median(np.abs(x - np.median(x)))) if x.size else None
def desa(nom, d):
    p = OUT / f'M1_{nom}.json'; prev = json.loads(p.read_text()) if p.exists() else {}; prev.update(d)
    p.write_text(json.dumps(prev, ensure_ascii=False, indent=1, default=lambda x: x.item() if isinstance(x, np.generic) else (x.tolist() if isinstance(x, np.ndarray) else str(x))))
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL
TH = (np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) % 360).astype(np.float32); del yy, xx
quins = sys.argv[1:] or list('TSKBFPLVQ')
DESPRES = ('v3', 'v4')
# ------------------------------------------------------------------ T · traços, geometria fixa (w2c)
if 'T' in quins:
    C5 = json.loads((A / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']; TR = []
    for k, t in enumerate(C5):
        d = np.array(t['info']['direccio'], float); d /= np.linalg.norm(d); TR.append((k + 1, np.array(t['info']['centre'], float) + float(t['info']['V0_minim_t']) * np.array([-d[1], d[0]]), d, float(t['info']['llarg'])))
    TT = np.arange(-80, 81, 1.0); CORE = np.abs(TT) <= 6; FLANC = (np.abs(TT) >= 20) & (np.abs(TT) <= 80)
    def detall(img):
        l, m = lnm(img); g = lambda s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
        return np.where(cv2.erode(m, np.ones((61, 61), np.uint8)) > 0, g(3) - g(30), np.nan).astype(np.float32)
    def solc(D, c, d, L):
        n = np.array([-d[1], d[0]]); s = np.arange(-L / 2, L / 2 + 1e-6, 2.0)
        X = (c[0] + s[:, None] * d[0] + TT[None, :] * n[0]).astype(np.float32); Y = (c[1] + s[:, None] * d[1] + TT[None, :] * n[1]).astype(np.float32)
        P = cv2.remap(D, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
        if np.isfinite(P[:, CORE | FLANC]).all(1).mean() < 0.9: return np.nan
        with np.errstate(all='ignore'): pr = np.nanmean(P, 0)
        return float(1e4 * (np.nanmean(pr[CORE]) - np.nanmean(pr[FLANC])))
    rng = np.random.default_rng(4242); NUL = {}
    for k, c0, d0, L in TR:
        n0 = np.array([-d0[1], d0[0]]); rs = np.linalg.norm(c0 - SOL); P_ = [(c0 + n0 * sh, d0) for sh in list(range(100, 1401, 100)) + list(range(-100, -1401, -100))]; A_ = []
        while len(A_) < 300:
            ang = rng.uniform(0, 2 * np.pi); rr = rs * rng.uniform(0.65, 1.35); c = SOL + rr * np.array([np.cos(ang), np.sin(ang)]); th = rng.uniform(0, np.pi); d = np.array([np.cos(th), np.sin(th)])
            e1, e2 = c + d * L / 2, c - d * L / 2
            if min(e1[0], e2[0]) > 150 and min(e1[1], e2[1]) > 150 and max(e1[0], e2[0]) < W - 150 and max(e1[1], e2[1]) < H - 150: A_.append((c, d))
        NUL[k] = dict(P=P_, A=A_)
    R = {}
    for nom in ('compost', 'base_G', 'sonyA_G', 'sonyB_G', 'vixen_G'):
        vals = {}
        for v in ('control',) + DESPRES:
            D = detall(ld(v, nom)); vals[v] = {k: dict(t=solc(D, c0, d0, L), P=[solc(D, c, d, L) for c, d in NUL[k]['P']], A=[solc(D, c, d, L) for c, d in NUL[k]['A']]) for k, c0, d0, L in TR}; del D
        res = {}
        for k, c0, d0, L in TR:
            o = {}
            for v in ('control',) + DESPRES:
                x = vals[v][k]; An = np.array(x['A'], float); Pn = np.array(x['P'], float); ok = np.isfinite(An); okp = np.isfinite(Pn)
                if not np.isfinite(x['t']) or ok.sum() < 30: o[v] = None; continue
                o[v] = dict(solc_ppm=round(x['t'], 2), z_atzar=round(float((x['t'] - An[ok].mean()) / An[ok].std()), 2), p_atzar=round(float(((An[ok] <= x['t']).sum() + 1) / (ok.sum() + 1)), 4),
                            z_paral=(round(float((x['t'] - Pn[okp].mean()) / Pn[okp].std()), 2) if okp.sum() >= 8 else None), sd_atzar_ppm=round(float(An[ok].std()), 2))
            res[f'T{k}'] = o
        R[nom] = res; print('T', nom, json.dumps({t: {v: (x['solc_ppm'], x['p_atzar']) if x else None for v, x in o.items()} for t, o in res.items()}), flush=True)
    # T1 a A − B (w4 AB)
    t = C5[0]['info']; d0 = np.array(t['direccio'], float); d0 /= np.linalg.norm(d0); n0 = np.array([-d0[1], d0[0]]); c0 = np.array(t['centre'], float) + t['V0_minim_t'] * n0; L0 = float(t['llarg'])
    ab = {}
    for v in ('control',) + DESPRES:
        la, ma = lnm(ld(v, 'sonyA_G')); lb, mb = lnm(ld(v, 'sonyB_G')); m = ma * mb
        D = np.where(cv2.erode(m, np.ones((61, 61), np.uint8)) > 0, (ng(la, m, 3) - ng(la, m, 30)) - (ng(lb, m, 3) - ng(lb, m, 30)), np.nan).astype(np.float32)
        x = solc(D, c0, d0, L0); nn = np.array([solc(D, c, d, L0) for c, d in NUL[1]['A']]); ok = np.isfinite(nn)
        ab[v] = dict(T1_AmenysB_ppm=round(x, 2), z=round(float((x - nn[ok].mean()) / nn[ok].std()), 2), sd_nul_ppm=round(float(nn[ok].std()), 2)); del la, lb, ma, mb, m, D
    R['T1_AmenysB'] = ab; print('T1 A−B', ab, flush=True); desa('T_TRACOS', R)
# ------------------------------------------------------------------ S · cura o injecció per bandes (w3)
ANELLS = [(1.05, 1.5), (1.5, 2.5), (2.5, 4), (4, 6), (6, 10), (10, 30)]; SIG = [0, 1, 2, 4, 8, 16, 32]
def prova_s(Xl, Yl, m):
    ok = cv2.erode(m, np.ones((131, 131), np.uint8)) > 0; msh = np.roll(np.roll(ok, 53, 1), -37, 0) & ok
    g = lambda l, s: (l if s == 0 else ng(l, m, s)); res = {}; gx0 = g(Xl, 0); gy0 = g(Yl, 0)
    for i in range(len(SIG) - 1):
        gx1 = g(Xl, SIG[i + 1]); gy1 = g(Yl, SIG[i + 1]); bx = (gx0 - gx1).astype(np.float32); by = (gy0 - gy1).astype(np.float32); d = by - bx; bxs = np.roll(np.roll(bx, 53, 1), -37, 0)
        banda = f'{SIG[i]}-{SIG[i + 1]}px'; res[banda] = {}
        for r0, r1 in ANELLS:
            k = ok & (RS >= r0) & (RS < r1) & (DL > 12); ks = msh & (RS >= r0) & (RS < r1) & (DL > 12)
            if k.sum() < 5000: continue
            EX = float((bx[k].astype(np.float64) ** 2).sum()); EY = float((by[k].astype(np.float64) ** 2).sum()); ED = float((d[k].astype(np.float64) ** 2).sum())
            EXs = float((bxs[ks].astype(np.float64) ** 2).sum()); EYs = float(((bxs[ks] + d[ks]).astype(np.float64) ** 2).sum()); EDs = float((d[ks].astype(np.float64) ** 2).sum())
            res[banda][f'{r0}-{r1}'] = dict(s=round((EY - EX) / ED, 3) if ED > 0 else None, s_nul=round((EYs - EXs) / EDs, 3) if EDs > 0 else None,
                                            dE_pc=round(100 * (EY / EX - 1), 2), rms_delta_ppm=round(1e4 * np.sqrt(ED / k.sum()), 2), rms_X_ppm=round(1e4 * np.sqrt(EX / k.sum()), 2))
        gx0, gy0 = gx1, gy1; del bx, by, d, bxs
    return res
if 'S' in quins:
    R = {}
    for nom in ('vixen_G', 'sonyA_G', 'sonyB_G', 'base_G', 'compost', 'L56_WOW', 'L54_MGN'):
        X, mx = lnm(ld('control', nom))
        for v in DESPRES:
            Y, my = lnm(ld(v, nom)); m = (mx * my).astype(np.float32); R[f'{nom}_{v}'] = prova_s(X, Y, m); del Y, my, m
            print('S', nom, v, json.dumps({b: {r: (x['s'], x['dE_pc']) for r, x in o.items()} for b, o in R[f'{nom}_{v}'].items()}), flush=True)
        del X, mx; desa('S_CURA_INJECCIO', R)
# ------------------------------------------------------------------ K · color (w9 i m1 N)
if 'K' in quins:
    R = {}; fa = np.load(VAR['control']['cad'] / 'lineal/fusion_starless.npy', mmap_mode='r'); Ga = np.asarray(fa[..., 1], np.float32)
    for v in DESPRES:
        fb = np.load(VAR[v]['cad'] / 'lineal/fusion_starless.npy', mmap_mode='r'); Gb = np.asarray(fb[..., 1], np.float32)
        for nm, c in (('R_G', 0), ('B_G', 2)):
            la, m1 = lnm(np.asarray(fa[..., c], np.float32) / np.maximum(Ga, 1e-12)); lb, m2 = lnm(np.asarray(fb[..., c], np.float32) / np.maximum(Gb, 1e-12)); m = m1 * m2 * (Ga > 0) * (Gb > 0)
            o = {}
            for (s1, s2, er, sh) in ((2, 20, 81, (61, -43)), (20, 200, 401, (97, -71))):
                X = ng(la, m, s1) - ng(la, m, s2); Y = ng(lb, m, s1) - ng(lb, m, s2); D = Y - X; Xs = np.roll(np.roll(X, sh[0], 1), sh[1], 0)
                okc = cv2.erode(m, np.ones((er, er), np.uint8)) > 0; oks = okc & np.roll(np.roll(okc, sh[0], 1), sh[1], 0)
                for r0, r1 in ((1.05, 1.5), (1.5, 3), (3, 6), (6, 10), (10, 30)):
                    k = okc & (RS >= r0) & (RS < r1) & (DL > 20); ks = oks & (RS >= r0) & (RS < r1) & (DL > 20)
                    if k.sum() < 20000: continue
                    EX = float((X[k].astype(np.float64) ** 2).sum()); EY = float((Y[k].astype(np.float64) ** 2).sum()); ED = float((D[k].astype(np.float64) ** 2).sum())
                    EDs = float((D[ks].astype(np.float64) ** 2).sum()); EXs = float((Xs[ks].astype(np.float64) ** 2).sum()); EYs = float(((Xs[ks] + D[ks]).astype(np.float64) ** 2).sum())
                    o[f'{s1}-{s2}_{r0}-{r1}'] = dict(s=round((EY - EX) / ED, 3) if ED > 0 else None, s_nul=round((EYs - EXs) / EDs, 3) if EDs > 0 else None, dE_pc=round(100 * (EY / EX - 1), 2),
                                                     rms_D_ppm=round(1e4 * np.sqrt(ED / k.sum()), 3), rms_X_ppm=round(1e4 * np.sqrt(EX / k.sum()), 2))
                del X, Y, D, Xs
            ok3 = cv2.erode(m, np.ones((301, 301), np.uint8)) > 0; z = np.abs(ng(lb, m, 100) - ng(la, m, 100))[ok3]
            o['gran_escala_sigma100_abs'] = dict(p50=float(np.median(z)), p99=float(np.percentile(z, 99)), max=float(z.max()))
            R[f'color_{nm}_{v}'] = o; print('K', nm, v, json.dumps(o), flush=True); del la, lb, m1, m2, m
        for nom in ('base_G', 'compost'):
            A_ = ld('control', nom); B_ = ld(v, nom); m = ((np.isfinite(A_) & (A_ > 0)) & (np.isfinite(B_) & (B_ > 0))).astype(np.float32)
            ok3 = cv2.erode(m, np.ones((301, 301), np.uint8)) > 0; z = np.abs(ng(B_ * m, m, 100)[ok3] / ng(A_ * m, m, 100)[ok3] - 1)
            R[f'nivell_{nom}_{v}'] = dict(p50=float(np.median(z)), p99=float(np.percentile(z, 99)), max=float(z.max())); print('K nivell', nom, v, R[f'nivell_{nom}_{v}'], flush=True); del A_, B_, m
        del fb, Gb
    desa('K_COLOR', R)
# ------------------------------------------------------------------ B · Brno (w4 B)
if 'B' in quins:
    res = {}
    for cb in (230, 231, 232):
        b = np.load(CAD / f'control/estat_v108/L{cb}_RGB.npy', mmap_mode='r'); bb = np.asarray(b, np.float32).mean(-1); lb, mb = lnm(bb); del bb
        for nom in ('compost', 'base_G'):
            for v in ('control',) + DESPRES:
                li, mi = lnm(ld(v, nom)); m = mb * mi
                for (s1, s2) in ((1, 8), (2, 16)):
                    db = ng(lb, m, s1) - ng(lb, m, s2); di = ng(li, m, s1) - ng(li, m, s2); dbs = np.roll(np.roll(db, 41, 1), -27, 0); ok = cv2.erode(m, np.ones((41, 41), np.uint8)) > 0
                    for r0, r1 in ((1.02, 1.5), (1.5, 2.5), (2.5, 4), (4, 6)):
                        k = ok & (RS >= r0) & (RS < r1) & (DL > 3); k[::2] = False
                        if k.sum() < 2000: continue
                        res.setdefault(f'L{cb}', {}).setdefault(nom, {}).setdefault(f'{s1}-{s2}', {}).setdefault(f'{r0}-{r1}', {})[v] = dict(r=round(float(np.corrcoef(db[k], di[k])[0, 1]), 4), nul=round(float(np.corrcoef(dbs[k], di[k])[0, 1]), 4))
                    del db, di, dbs
                del li, mi, m
        print('B', cb, json.dumps(res[f'L{cb}'])[:1500], flush=True)
    desa('B_BRNO', dict(B_brno=res))
# ------------------------------------------------------------------ F · plomalls, P · perles, L · limbe (w4)
if 'F' in quins:
    res = {}
    for nom in ('compost', 'base_G'):
        la, ma = lnm(ld('control', nom)); ib = np.clip((TH / 0.5).astype(np.int32), 0, 719)
        for v in DESPRES:
            lb, mb = lnm(ld(v, nom)); m = (ma * mb > 0) & (DL > 3); o = {}
            for r0 in np.arange(1.05, 6.0, 0.1):
                k = m & (RS >= r0) & (RS < r0 + 0.1)
                if k.sum() < 3000: continue
                n = np.bincount(ib[k], minlength=720); pa_ = np.bincount(ib[k], la[k], 720) / np.maximum(n, 1); pb_ = np.bincount(ib[k], lb[k], 720) / np.maximum(n, 1); vv = n > 20
                o[f'{r0:.2f}'] = dict(contrast_azimutal=round(float(np.std(pb_[vv] - np.median(pb_[vv])) / np.std(pa_[vv] - np.median(pa_[vv]))), 4),
                                      nivell_radial=round(float(np.exp(np.median(lb[k]) - np.median(la[k]))), 5), corr_perfils=round(float(np.corrcoef(pa_[vv], pb_[vv])[0, 1]), 5))
            res[f'{nom}_{v}'] = o; c_ = [x['contrast_azimutal'] for x in o.values()]; r_ = [x['corr_perfils'] for x in o.values()]
            print('F', nom, v, 'contrast', min(c_), max(c_), 'corr mín', min(r_), flush=True); del lb, mb, m
        del la, ma
    desa('F_PLOMALLS', res)
if 'P' in quins:
    res = {}
    la, ma = lnm(ld('control', 'compost')); da = ng(la, ma, 1) - ng(la, ma, 4)
    for v in DESPRES:
        lb, mb = lnm(ld(v, 'compost')); m = ma * mb; db = ng(lb, m, 1) - ng(lb, m, 4)
        franja = (DL >= 0) & (DL < 60) & (m > 0); mx = cv2.dilate(da, np.ones((9, 9), np.uint8)); pk = franja & (da == mx) & (da > 0)
        ys, xs = np.nonzero(pk); o_ = np.argsort(-da[ys, xs])[:300]; ys, xs = ys[o_], xs[o_]; rat = db[ys, xs] / da[ys, xs]
        rng = np.random.default_rng(99); fy, fx = np.nonzero(franja); sel = rng.choice(len(fy), 300, replace=False); dnul = np.abs(db[fy[sel], fx[sel]] - da[fy[sel], fx[sel]])
        res[v] = dict(n=int(len(ys)), despres_sobre_abans_p5_p50_p95=np.percentile(rat, [5, 50, 95]).round(4).tolist(), dif_abs_ppm_perles=round(1e4 * float(np.median(np.abs(db[ys, xs] - da[ys, xs]))), 2),
                      dif_abs_ppm_nul=round(1e4 * float(np.median(dnul)), 2)); print('P', v, res[v], flush=True); del lb, mb, db
    desa('P_PERLES', res)
if 'L' in quins:
    res = {}; a_ = ld('control', 'compost')
    for v in DESPRES:
        b_ = ld(v, 'compost'); ok = (a_ > 0) & (b_ > 0) & np.isfinite(a_) & np.isfinite(b_); d = np.where(ok, b_ / np.where(ok, a_, 1) - 1, np.nan); o = {}
        for d0, d1 in ((0, 3), (3, 10), (10, 30), (30, 90), (90, 200)):
            k = ok & (DL >= d0) & (DL < d1); o[f'{d0}-{d1}px'] = dict(rms_pc=round(100 * float(np.sqrt(np.nanmean(d[k] ** 2))), 3), p99_abs_pc=round(100 * float(np.nanpercentile(np.abs(d[k]), 99)), 3))
        px = {}
        for (x, y) in ((4905, 3779), (4897, 3785), (4897, 3786)):
            e = dict(DL=round(float(DL[y, x]), 2), compost=[float(a_[y, x]), float(b_[y, x])], base_G=[float(np.load(VAR['control']['cad'] / 'lineal/base_G.npy', mmap_mode='r')[y, x]), float(np.load(VAR[v]['cad'] / 'lineal/base_G.npy', mmap_mode='r')[y, x])])
            e['L3_RGB'] = [np.asarray(np.load(VAR[q]['cad'] / 'estat_v108/L3_RGB.npy', mmap_mode='r')[y, x], np.float64).round(1).tolist() for q in ('control', v)]
            e['filtres_G_i_alfa'] = {f'L{Lc}': [[float(np.load(VAR[q]['cad'] / f'estat_v108/L{Lc}_G.npy', mmap_mode='r')[y, x]) for q in ('control', v)], [float(np.load(VAR[q]['cad'] / f'estat_v108/L{Lc}_alfa.npy', mmap_mode='r')[y, x]) for q in ('control', v)]] for Lc in range(41, 57) if (VAR[v]['cad'] / f'estat_v108/L{Lc}_G.npy').exists()}
            px[f'{x},{y}'] = e
        na = {}
        for Lc in range(41, 57):
            fa = VAR['control']['cad'] / f'estat_v108/L{Lc}_alfa.npy'; fb = VAR[v]['cad'] / f'estat_v108/L{Lc}_alfa.npy'
            if fa.exists() and fb.exists(): na[f'L{Lc}'] = int((np.load(fa, mmap_mode='r') != np.load(fb, mmap_mode='r')).sum())
        res[v] = dict(bandes=o, pixels_protuberancia=px, alfes_que_canvien=na); print('L', v, json.dumps(res[v]), flush=True); del b_, d
    desa('L_LIMBE', res)
# ------------------------------------------------------------------ V · vora del camp de la Vixen (m1 V de la v2)
if 'V' in quins:
    den = np.asarray(np.load(OUT / 'apilats/vixen_den.npy', mmap_mode='r')[::2, ::2], np.float32) > 0     # els pesos no depenen de C: iguals al control (rebut b2)
    den = cv2.morphologyEx(den.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)).astype(bool)
    ds = (edt(den) - edt(~den)) * 2; ds = cv2.resize(ds.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    yy, xx = np.mgrid[0:H, 0:W]; lliure = (xx > 200) & (yy > 200) & (xx < W - 200) & (yy < H - 200); del yy, xx
    def det(X):
        l, m = lnm(X); return np.where(cv2.erode(m, np.ones((41, 41), np.uint8)) > 0, ng(l, m, 2) - ng(l, m, 16), np.nan)
    res = {}
    for nom in ('base_G', 'compost'):
        Ds = {v: det(ld(v, nom)) for v in ('control',) + DESPRES}; r = {}
        for a_, b_ in ((-900, -600), (-600, -300), (-300, -100), (-100, 0), (0, 100), (100, 300), (300, 600), (600, 900), (900, 1500)):
            k = (ds >= a_) & (ds < b_) & (RS > 3) & lliure
            for X in Ds.values(): k &= np.isfinite(X)
            if k.sum() < 2e4: continue
            r[f'{a_}..{b_}'] = dict(n=int(k.sum()), **{v: mad(X[k]) for v, X in Ds.items()})
        fora = [x for k_, x in r.items() if k_.startswith('-9') or k_.startswith('-6')]; dins_ = [x for k_, x in r.items() if k_.startswith('600') or k_.startswith('900')]
        r['dins_sobre_fora'] = {v: float(np.mean([x[v] for x in dins_]) / np.mean([x[v] for x in fora]) - 1) for v in Ds}
        res[nom] = r; print('V', nom, json.dumps(r['dins_sobre_fora']), flush=True); del Ds
    desa('V_VORA_VIXEN', res)
# ------------------------------------------------------------------ Q · taques de pols (w8 Vixen, w9 Sony A) i els quatre punts del verificador
if 'Q' in quins:
    res = {}
    yy_, xx_ = np.mgrid[-120:121, -120:121]; rr_ = np.hypot(yy_, xx_)
    for nom, (rdisc, r0a, r1a, thr, sep, llav) in (('vixen_G', (35, 70, 110, 0.0015, 151, 7)), ('sonyA_G', (30, 60, 100, 0.0008, 121, 11))):
        DISC = rr_ < rdisc; ANELL = (rr_ >= r0a) & (rr_ < r1a)
        va, ma = lnm(ld('control', nom))
        def E(l, mk, x, y):
            t = l[y - 120:y + 121, x - 120:x + 121]; k = mk[y - 120:y + 121, x - 120:x + 121] > 0
            if t.shape != rr_.shape or (k & DISC).sum() < 0.9 * DISC.sum() or (k & ANELL).sum() < 0.9 * ANELL.sum(): return np.nan
            return float(1e4 * (t[k & DISC].mean() - t[k & ANELL].mean()))
        for v in DESPRES:
            vb, mb = lnm(ld(v, nom)); m = ma * mb; d = np.where(m > 0, vb - va, 0).astype(np.float32); dd = ng(d, m, 10) - ng(d, m, 60)
            ok = cv2.erode(m, np.ones((251, 251), np.uint8)) > 0
            if nom == 'vixen_G': ok &= RS > 1.6
            else: zona = np.zeros((H, W), bool); zona[800:3300, 5400:8200] = True; ok &= zona
            mx = cv2.dilate(np.abs(dd), np.ones((sep, sep), np.uint8)); pk = ok & (np.abs(dd) == mx) & (np.abs(dd) > thr); ys, xs = np.nonzero(pk)
            rng = np.random.default_rng(llav); tq = []
            for y, x in zip(ys, xs):
                r0 = np.hypot(x - SOL[0], y - SOL[1]); nul = []
                for _ in range(400):
                    if len(nul) >= 60: break
                    ang = rng.uniform(0, 2 * np.pi); r_ = r0 * rng.uniform(0.9, 1.1); cx, cy = int(SOL[0] + r_ * np.cos(ang)), int(SOL[1] + r_ * np.sin(ang))
                    if 130 < cx < W - 130 and 130 < cy < H - 130 and ok[cy, cx]:
                        e_ = E(va, m, cx, cy)
                        if np.isfinite(e_): nul.append(e_)
                ea, eb = E(va, m, x, y), E(vb, m, x, y)
                if not (np.isfinite(ea) and np.isfinite(eb)) or len(nul) < 20: continue
                nul = np.array(nul); tq.append(dict(x=int(x), y=int(y), R_sol=round(float(r0 / RSOL), 2), E_abans=round(ea, 1), E_despres=round(eb, 1), canvi=round(eb - ea, 1), sd_nul=round(float(nul.std()), 1),
                                                    z_abans=round(float((ea - nul.mean()) / nul.std()), 2), z_despres=round(float((eb - nul.mean()) / nul.std()), 2)))
            num = sum(-t['E_abans'] * t['canvi'] for t in tq); den_ = sum(t['canvi'] ** 2 for t in tq)
            noves = [t for t in tq if abs(t['z_abans']) < 1.5 and abs(t['z_despres']) >= 3]
            res[f'{nom}_{v}'] = dict(n=len(tq), fraccio_curada_global=round(num / den_, 3) if den_ else None, taques_noves_z3=noves, n_taques_noves=len(noves),
                                     max_abs_canvi_ppm=max((abs(t['canvi']) for t in tq), default=None))
            # els punts del verificador (sempre, encara que ja no siguin màxims del canvi)
            PUNTS = [(5839, 5350), (3943, 4714)] if nom == 'vixen_G' else [(8175, 1538), (8015, 1001)]
            res[f'{nom}_{v}']['punts_verificador'] = {f'{x},{y}': dict(E_abans=round(E(va, m, x, y), 1), E_despres=round(E(vb, m, x, y), 1)) for x, y in PUNTS}
            print('Q', nom, v, 'n', len(tq), 'fracció curada', res[f'{nom}_{v}']['fraccio_curada_global'], 'noves', len(noves), res[f'{nom}_{v}']['punts_verificador'], flush=True)
            del vb, mb, m, d, dd, mx
        del va, ma
    desa('Q_TAQUES', res)
# ------------------------------------------------------------------ Q2 · les taques de la Sony A amb el cel ANUL·LAT (A − B): la mateixa estadística que Q (w9), però
#      E_abans i el canvi es mesuren a ln A − ln B (el cel i la corona s'anul·len; només hi queda el que va fix al sensor). Els màxims del canvi són els de Q.
if 'Q2' in quins:
    res = {}; yy_, xx_ = np.mgrid[-120:121, -120:121]; rr_ = np.hypot(yy_, xx_); DISC = rr_ < 30; ANELL = (rr_ >= 60) & (rr_ < 100)
    la, ma = lnm(ld('control', 'sonyA_G')); lbb, mbb = lnm(ld('control', 'sonyB_G')); Zab = np.where(ma * mbb > 0, la - lbb, 0).astype(np.float32); mab = ma * mbb; del lbb
    def E2(l, mk, x, y):
        t = l[y - 120:y + 121, x - 120:x + 121]; k = mk[y - 120:y + 121, x - 120:x + 121] > 0
        if t.shape != rr_.shape or (k & DISC).sum() < 0.9 * DISC.sum() or (k & ANELL).sum() < 0.9 * ANELL.sum(): return np.nan
        return float(1e4 * (t[k & DISC].mean() - t[k & ANELL].mean()))
    for v in DESPRES:
        vA, mA = lnm(ld(v, 'sonyA_G')); vB, mB = lnm(ld(v, 'sonyB_G')); m = mab * mA * mB
        dA = np.where(m > 0, vA - la, 0).astype(np.float32); dB = np.where(m > 0, vB - (la - Zab), 0).astype(np.float32); del vA, vB
        dd = ng(dA, m, 10) - ng(dA, m, 60); ok = cv2.erode(m, np.ones((251, 251), np.uint8)) > 0; zona = np.zeros((H, W), bool); zona[800:3300, 5400:8200] = True; ok &= zona
        mx = cv2.dilate(np.abs(dd), np.ones((121, 121), np.uint8)); pk = ok & (np.abs(dd) == mx) & (np.abs(dd) > 0.0008); ys, xs = np.nonzero(pk)
        rng = np.random.default_rng(11); tq = []; dAB = (dA - dB).astype(np.float32)
        for y, x in zip(ys, xs):
            r0 = np.hypot(x - SOL[0], y - SOL[1]); nul = []
            for _ in range(400):
                if len(nul) >= 60: break
                ang = rng.uniform(0, 2 * np.pi); r_ = r0 * rng.uniform(0.9, 1.1); cx, cy = int(SOL[0] + r_ * np.cos(ang)), int(SOL[1] + r_ * np.sin(ang))
                if 130 < cx < W - 130 and 130 < cy < H - 130 and ok[cy, cx]:
                    e_ = E2(Zab, m, cx, cy)
                    if np.isfinite(e_): nul.append(e_)
            ea = E2(Zab, m, x, y); de = E2(dAB, m, x, y)
            if not (np.isfinite(ea) and np.isfinite(de)) or len(nul) < 20: continue
            nul = np.array(nul); tq.append(dict(x=int(x), y=int(y), E_abans=round(ea, 1), canvi=round(de, 1), E_despres=round(ea + de, 1), sd_nul=round(float(nul.std()), 1),
                                                z_abans=round(float((ea - nul.mean()) / nul.std()), 2), z_despres=round(float((ea + de - nul.mean()) / nul.std()), 2)))
        num = sum(-t['E_abans'] * t['canvi'] for t in tq); den_ = sum(t['canvi'] ** 2 for t in tq)
        noves = [t for t in tq if abs(t['z_abans']) < 1.5 and abs(t['z_despres']) >= 3]
        PUNTS = [(8175, 1538), (8015, 1001)]
        res[v] = dict(n=len(tq), fraccio_curada_global_AmenysB=round(num / den_, 3) if den_ else None, n_taques_noves_z3=len(noves), taques_noves=noves,
                      sd_nul_mediana_ppm=float(np.median([t['sd_nul'] for t in tq])) if tq else None,
                      punts_verificador={f'{x},{y}': dict(E_abans_AmenysB=round(E2(Zab, m, x, y), 1), canvi_AmenysB=round(E2(dAB, m, x, y), 1)) for x, y in PUNTS})
        print('Q2', v, json.dumps({k_: res[v][k_] for k_ in ('n', 'fraccio_curada_global_AmenysB', 'n_taques_noves_z3', 'sd_nul_mediana_ppm', 'punts_verificador')}), flush=True)
        del dA, dB, dAB, dd, mx, m
    desa('Q2_TAQUES_SONYA_AmenysB', res)
# ------------------------------------------------------------------ Q3 · les taques de la Vixen amb el cel ANUL·LAT per la Sony (V − S, la Sony A+B del control):
#      E_abans a ln V − ln S; el canvi, el de l'apilat de la Vixen. Màxims del canvi com a Q (w8).
if 'Q3' in quins:
    res = {}; yy_, xx_ = np.mgrid[-120:121, -120:121]; rr_ = np.hypot(yy_, xx_); DISC = rr_ < 35; ANELL = (rr_ >= 70) & (rr_ < 110)
    la, ma = lnm(ld('control', 'vixen_G')); xs_ = np.load(A / '4-RESULTATS/v98_20260925/cadena_v98/b3/cau/sony_corrected_total_v42.npy', mmap_mode='r')
    ls, ms = lnm(np.asarray(xs_[..., 1], np.float32)); Zvs = np.where(ma * ms > 0, la - ls, 0).astype(np.float32); mvs = ma * ms; del ls
    def E3(l, mk, x, y):
        t = l[y - 120:y + 121, x - 120:x + 121]; k = mk[y - 120:y + 121, x - 120:x + 121] > 0
        if t.shape != rr_.shape or (k & DISC).sum() < 0.9 * DISC.sum() or (k & ANELL).sum() < 0.9 * ANELL.sum(): return np.nan
        return float(1e4 * (t[k & DISC].mean() - t[k & ANELL].mean()))
    for v in DESPRES:
        vb, mb = lnm(ld(v, 'vixen_G')); m = mvs * mb; d = np.where(m > 0, vb - la, 0).astype(np.float32); del vb
        dd = ng(d, m, 10) - ng(d, m, 60); ok = (cv2.erode(m, np.ones((251, 251), np.uint8)) > 0) & (RS > 1.6)
        mx = cv2.dilate(np.abs(dd), np.ones((151, 151), np.uint8)); pk = ok & (np.abs(dd) == mx) & (np.abs(dd) > 0.0015); ys, xs = np.nonzero(pk)
        rng = np.random.default_rng(7); tq = []
        for y, x in zip(ys, xs):
            r0 = np.hypot(x - SOL[0], y - SOL[1]); nul = []
            for _ in range(400):
                if len(nul) >= 60: break
                ang = rng.uniform(0, 2 * np.pi); r_ = r0 * rng.uniform(0.9, 1.1); cx, cy = int(SOL[0] + r_ * np.cos(ang)), int(SOL[1] + r_ * np.sin(ang))
                if 130 < cx < W - 130 and 130 < cy < H - 130 and ok[cy, cx]:
                    e_ = E3(Zvs, m, cx, cy)
                    if np.isfinite(e_): nul.append(e_)
            ea = E3(Zvs, m, x, y); de = E3(d, m, x, y)
            if not (np.isfinite(ea) and np.isfinite(de)) or len(nul) < 20: continue
            nul = np.array(nul); tq.append(dict(x=int(x), y=int(y), R_sol=round(float(r0 / RSOL), 2), E_abans=round(ea, 1), canvi=round(de, 1), sd_nul=round(float(nul.std()), 1),
                                                z_abans=round(float((ea - nul.mean()) / nul.std()), 2), z_despres=round(float((ea + de - nul.mean()) / nul.std()), 2)))
        num = sum(-t['E_abans'] * t['canvi'] for t in tq); den_ = sum(t['canvi'] ** 2 for t in tq)
        noves = [t for t in tq if abs(t['z_abans']) < 1.5 and abs(t['z_despres']) >= 3]
        PUNTS = [(5839, 5350), (3943, 4714)]
        res[v] = dict(n=len(tq), fraccio_curada_global_VmenysS=round(num / den_, 3) if den_ else None, n_taques_noves_z3=len(noves), taques_noves=noves,
                      sd_nul_mediana_ppm=float(np.median([t['sd_nul'] for t in tq])) if tq else None,
                      punts_verificador={f'{x},{y}': dict(E_abans_VmenysS=round(E3(Zvs, m, x, y), 1), canvi=round(E3(d, m, x, y), 1)) for x, y in PUNTS})
        print('Q3', v, json.dumps({k_: res[v][k_] for k_ in ('n', 'fraccio_curada_global_VmenysS', 'n_taques_noves_z3', 'sd_nul_mediana_ppm', 'punts_verificador')}), flush=True)
        del d, dd, mx, m
    desa('Q3_TAQUES_VIXEN_VmenysS', res)
