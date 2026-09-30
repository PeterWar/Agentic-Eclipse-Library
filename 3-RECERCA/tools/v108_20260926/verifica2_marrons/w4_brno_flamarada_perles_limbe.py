"""w4 (verificador adversari 2) · El que no s'ha de perdre, abans i després, amb codi propi.
  B · Brno (mitjana RGB de L230–L233 de l'estat de control; al v2 són les mateixes) contra compost i base: correlació del DoG del ln a DUES
      bandes (σ1–8, la de la ronda 1, i σ2–16), per anells; NUL = Brno desplaçat (41, −27) px (ha de donar ≈ 0).
  F · Flamarada: contrast azimutal dels plomalls (desviació del perfil azimutal del ln, calaixos de 0,5°, per anells de 0,1 R☉) i perfil
      radial (mediana azimutal), després/abans.
  P · Perles: els 300 màxims locals més forts del DoG σ1–4 del compost d'ABANS a 0–60 px del limbe; amplitud després/abans (mediana, p5, p95)
      i NUL: 300 punts a l'atzar de la mateixa franja.
  L · Limbe: rms de després/abans − 1 del compost a 0–3, 3–10, 10–30, 30–90 px; i els dos píxels de la protuberància (4905, 3779), (4897, 3786):
      base, lineal i alfes de 47–56 abans i després.
  AB · T1 a (A − B): detall de ln A − ln B (σ3−σ30) al traç T1 (t0 de C5) amb 300 nuls a l'atzar, control i v2.
Sortida: W4_BRNO_FLAMARADA_PERLES_LIMBE.json"""
import json, sys
from pathlib import Path
import numpy as np, cv2
A = Path(__file__).resolve().parents[4]; OUT = A / '4-RESULTATS/v108_20260926/verifica2_marrons'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
F2 = A / '4-RESULTATS/v108_20260926/flat2d_v2'; CAD = A / '4-RESULTATS/v108_20260926/cadena'; CR = A / '4-RESULTATS/v97_refundacio_20260924'
quins = sys.argv[1:] or ['B', 'F', 'P', 'L', 'AB']
fp = OUT / 'W4_BRNO_FLAMARADA_PERLES_LIMBE.json'; R = json.loads(fp.read_text()) if fp.exists() else {}
def desa(): fp.write_text(json.dumps(R, ensure_ascii=False, indent=1))
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL
TH = (np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) % 360).astype(np.float32); del yy, xx
def lnm(img):
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
def ng(l, m, s): return cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
def ld(p, ch=None):
    a = np.load(p, mmap_mode='r'); return np.asarray(a if ch is None else a[..., ch], np.float32)
IM = {'compost': (F2 / 'compost_control.npy', F2 / 'compost_flat2d_v2.npy'), 'base': (CAD / 'control/lineal/base_G.npy', CAD / 'flat2d_v2/lineal/base_G.npy')}
if 'B' in quins:
    res = {}
    for cb in (230, 231, 232):   # la L233 és una caixa (5095×5225), no el llenç: fora
        b = np.load(CAD / f'control/estat_v108/L{cb}_RGB.npy', mmap_mode='r'); bb = np.asarray(b, np.float32).mean(-1); lb, mb = lnm(bb); del bb
        for nom, (pa, pd) in IM.items():
            for et, p in (('abans', pa), ('despres', pd)):
                li, mi = lnm(ld(p)); m = mb * mi
                for (s1, s2) in ((1, 8), (2, 16)):
                    db = ng(lb, m, s1) - ng(lb, m, s2); di = ng(li, m, s1) - ng(li, m, s2)
                    dbs = np.roll(np.roll(db, 41, 1), -27, 0)
                    ok = cv2.erode(m, np.ones((41, 41), np.uint8)) > 0
                    for r0, r1 in ((1.02, 1.5), (1.5, 2.5), (2.5, 4), (4, 6)):
                        k = ok & (RS >= r0) & (RS < r1) & (DL > 3)
                        k[::2] = False
                        if k.sum() < 2000: continue
                        c = float(np.corrcoef(db[k], di[k])[0, 1]); cn = float(np.corrcoef(dbs[k], di[k])[0, 1])
                        res.setdefault(f'L{cb}', {}).setdefault(nom, {}).setdefault(f'{s1}-{s2}', {}).setdefault(f'{r0}-{r1}', {})[et] = dict(r=round(c, 4), nul=round(cn, 4))
                    del db, di, dbs
                del li, mi, m
        print('B', cb, json.dumps(res[f'L{cb}']), flush=True)
    R['B_brno'] = res; desa()
if 'F' in quins:
    res = {}
    for nom, (pa, pd) in IM.items():
        la, ma = lnm(ld(pa)); lb, mb = lnm(ld(pd)); m = (ma * mb > 0) & (DL > 3)
        ib = np.clip((TH / 0.5).astype(np.int32), 0, 719); o = {}
        for r0 in np.arange(1.05, 6.0, 0.1):
            k = m & (RS >= r0) & (RS < r0 + 0.1)
            if k.sum() < 3000: continue
            n = np.bincount(ib[k], minlength=720); pa_ = np.bincount(ib[k], la[k], 720) / np.maximum(n, 1); pb_ = np.bincount(ib[k], lb[k], 720) / np.maximum(n, 1); v = n > 20
            sa = float(np.std(pa_[v] - np.median(pa_[v]))); sb = float(np.std(pb_[v] - np.median(pb_[v])))
            o[f'{r0:.2f}'] = dict(contrast_azimutal_despres_sobre_abans=round(sb / sa, 4), nivell_radial_despres_sobre_abans=round(float(np.exp(np.median(lb[k]) - np.median(la[k]))), 5),
                                  corr_perfils_azimutals=round(float(np.corrcoef(pa_[v], pb_[v])[0, 1]), 5))
        res[nom] = o; print('F', nom, {k_: o[k_] for k_ in list(o)[::8]}, flush=True); del la, lb, ma, mb, m
    R['F_flamarada'] = res; desa()
if 'P' in quins:
    res = {}
    la, ma = lnm(ld(IM['compost'][0])); lb, mb = lnm(ld(IM['compost'][1])); m = ma * mb
    da = ng(la, m, 1) - ng(la, m, 4); db = ng(lb, m, 1) - ng(lb, m, 4)
    franja = (DL >= 0) & (DL < 60) & (m > 0)
    mx = cv2.dilate(da, np.ones((9, 9), np.uint8)); pk = franja & (da == mx) & (da > 0)
    ys, xs = np.nonzero(pk); ordre = np.argsort(-da[ys, xs])[:300]; ys, xs = ys[ordre], xs[ordre]
    rat = db[ys, xs] / da[ys, xs]
    rng = np.random.default_rng(99); fy, fx = np.nonzero(franja); sel = rng.choice(len(fy), 300, replace=False)
    dif_nul = np.abs(db[fy[sel], fx[sel]] - da[fy[sel], fx[sel]])
    res = dict(n=int(len(ys)), amplitud_ppm_mediana_abans=round(1e4 * float(np.median(da[ys, xs])), 1), despres_sobre_abans_p5_p50_p95=np.percentile(rat, [5, 50, 95]).round(4).tolist(),
               dif_abs_ppm_perles_mediana=round(1e4 * float(np.median(np.abs(db[ys, xs] - da[ys, xs]))), 2), dif_abs_ppm_nul_atzar_mediana=round(1e4 * float(np.median(dif_nul)), 2))
    R['P_perles'] = res; print('P', res, flush=True); desa(); del la, lb, da, db, m, mx
if 'L' in quins:
    a = ld(IM['compost'][0]); b = ld(IM['compost'][1]); ok = (a > 0) & (b > 0) & np.isfinite(a) & np.isfinite(b); d = np.where(ok, b / np.where(ok, a, 1) - 1, np.nan)
    o = {}
    for d0, d1 in ((0, 3), (3, 10), (10, 30), (30, 90), (90, 200)):
        k = ok & (DL >= d0) & (DL < d1); o[f'{d0}-{d1}px'] = dict(rms_pc=round(100 * float(np.sqrt(np.nanmean(d[k] ** 2))), 3), p99_abs_pc=round(100 * float(np.nanpercentile(np.abs(d[k]), 99)), 3),
                                                             mitjana_pc=round(100 * float(np.nanmean(d[k])), 4))
    px = {}
    for (x, y) in ((4905, 3779), (4897, 3786)):
        e = dict(DL=round(float(DL[y, x]), 2), TH=round(float(TH[y, x]), 2), compost=[float(a[y, x]), float(b[y, x])])
        for cam, nm in (('lineal/base_G.npy', 'base_G'),):
            e[nm] = [float(np.load(CAD / 'control' / cam, mmap_mode='r')[y, x]), float(np.load(CAD / 'flat2d_v2' / cam, mmap_mode='r')[y, x])]
        for L in range(41, 57):
            fa = CAD / f'control/estat_v108/L{L}_alfa.npy'; fb = CAD / f'flat2d_v2/estat_v108/L{L}_alfa.npy'
            if fa.exists() and fb.exists():
                va, vb = int(np.load(fa, mmap_mode='r')[y, x]), int(np.load(fb, mmap_mode='r')[y, x])
                ga, gb = int(np.load(CAD / f'control/estat_v108/L{L}_G.npy', mmap_mode='r')[y, x]), int(np.load(CAD / f'flat2d_v2/estat_v108/L{L}_G.npy', mmap_mode='r')[y, x])
                e[f'L{L}_alfa_G'] = [va, vb, ga, gb]
        px[f'{x},{y}'] = e
    # quantes alfes canvien en total, capa per capa
    na = {}
    for L in range(41, 57):
        fa = CAD / f'control/estat_v108/L{L}_alfa.npy'; fb = CAD / f'flat2d_v2/estat_v108/L{L}_alfa.npy'
        if fa.exists() and fb.exists():
            dd = np.load(fa, mmap_mode='r') != np.load(fb, mmap_mode='r'); na[f'L{L}'] = int(dd.sum())
            if dd.sum(): ys_, xs_ = np.nonzero(dd); na[f'L{L}_on'] = [[int(xs_[i]), int(ys_[i])] for i in range(min(6, len(ys_)))]
    R['L_limbe'] = dict(bandes=o, pixels_protuberancia=px, alfes_que_canvien=na); print('L', json.dumps(R['L_limbe']), flush=True); desa(); del a, b, d
if 'AB' in quins:
    C5 = json.loads((A / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']; t = C5[0]['info']
    d0 = np.array(t['direccio'], float); d0 /= np.linalg.norm(d0); n0 = np.array([-d0[1], d0[0]]); c0 = np.array(t['centre'], float) + t['V0_minim_t'] * n0; L = float(t['llarg'])
    TT = np.arange(-80, 81, 1.0); CORE = np.abs(TT) <= 6; FL = (np.abs(TT) >= 20) & (np.abs(TT) <= 80)
    def solc(D, c, d):
        n = np.array([-d[1], d[0]]); s = np.arange(-L / 2, L / 2 + 1e-6, 2.0)
        X = (c[0] + s[:, None] * d[0] + TT[None, :] * n[0]).astype(np.float32); Y = (c[1] + s[:, None] * d[1] + TT[None, :] * n[1]).astype(np.float32)
        P = cv2.remap(D, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
        if np.isfinite(P[:, CORE | FL]).all(1).mean() < 0.9: return np.nan
        pr = np.nanmean(P, 0); return float(1e4 * (np.nanmean(pr[CORE]) - np.nanmean(pr[FL])))
    rng = np.random.default_rng(4242); rs = np.linalg.norm(c0 - np.array(SOL)); NUL = []
    while len(NUL) < 300:
        ang = rng.uniform(0, 2 * np.pi); rr = rs * rng.uniform(0.65, 1.35); c = np.array(SOL) + rr * np.array([np.cos(ang), np.sin(ang)]); th = rng.uniform(0, np.pi); d = np.array([np.cos(th), np.sin(th)])
        e1, e2 = c + d * L / 2, c - d * L / 2
        if min(e1[0], e2[0]) > 150 and min(e1[1], e2[1]) > 150 and max(e1[0], e2[0]) < W - 150 and max(e1[1], e2[1]) < H - 150: NUL.append((c, d))
    PA = {'control': (CR / 'cadena_raw/b2_sony_A/cau/sony_A_total_v36.npy', CR / 'cadena_raw/b2_sony_B/cau/sony_B_total_v42.npy'), 'v2': (F2 / 'apilats/sony_A_total.npy', F2 / 'apilats/cau/sony_B_total_v42.npy')}
    res = {}
    for et, (pa, pb) in PA.items():
        la, ma = lnm(ld(pa, 1)); lb, mb = lnm(ld(pb, 1)); m = ma * mb
        D = np.where(cv2.erode(m, np.ones((61, 61), np.uint8)) > 0, (ng(la, m, 3) - ng(la, m, 30)) - (ng(lb, m, 3) - ng(lb, m, 30)), np.nan).astype(np.float32)
        v = solc(D, c0, d0); nn = np.array([solc(D, c, d) for c, d in NUL]); ok = np.isfinite(nn)
        res[et] = dict(T1_AmenysB_ppm=round(v, 2), z=round(float((v - nn[ok].mean()) / nn[ok].std()), 2), p=round(float(((nn[ok] <= v).sum() + 1) / (ok.sum() + 1)), 4), sd_nul_ppm=round(float(nn[ok].std()), 2), n=int(ok.sum()))
        print('AB', et, res[et], flush=True); del la, lb, ma, mb, m, D
    R['AB_T1_AmenysB'] = res; desa()
