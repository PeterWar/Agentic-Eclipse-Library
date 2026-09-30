"""m1 (V108, flat2d_v2) · ABANS (control = la V107) i DESPRÉS (flat2d_v2), amb LA MATEIXA MESURA I ELS MATEIXOS NULS a totes dues imatges.
També el pilot de la ronda 1 (flat2d v1) com a tercera imatge, per veure què han canviat la correcció del disc i la fusió congelada.
Mesures (les del verificador de la ronda 1, vm1/vm2/vm3, amb les imatges noves):
  T  · els sis traços (geometria C5_PERFILS = marca 269): detall = DoG del ln σ3−σ30; solc = mín a |t| ≤ 60 − mediana dels flancs 120–400
       (cerca ±1,5°); tres nuls calculats A CADA IMATGE amb les mateixes posicions (llavor 777): P (desplaçat en paral·lel), R (girat), A (200 a
       l'atzar a la mateixa distància del Sol). p = (n nuls ≤ valor + 1)/(n + 1).
  E  · energia per escales (DoG del ln: 0–1, 1–2, 2–4, 4–8, 8–16, 16–32 px) per anells de R☉ (el soroll de píxel és la banda 0–1).
  B  · Brno (L230–233 de l'estat E) contra la imatge: correlació del DoG σ1–8 a pas 2, a 1,02–1,5 / 1,5–2,5 / 2,5–4 / 4–6 R☉.
  N  · nivell a gran escala: |G100(després)/G100(abans) − 1| p50/p99/màx; color: ln R/G i ln B/G de fusion_starless (σ100 i DoG 2–30).
  V  · la vora del camp de la Vixen: textura (MAD del DoG σ2–16 del ln) per calaixos de distància a la vora, dins/fora − 1 (r > 3 R☉).
  L  · arran del limbe: D = després/abans − 1 per bandes de distància al limbe (0–3, 3–10, 10–30, 30–60, 60–90, 90–120, 120–200 px) i per
       sectors de 30°: rms del D, i energia tangencial (DoG del ln al llarg de l'arc) abans i després.
Ús: m1_mesura_flat2d_v2.py T|E|B|N|V|L [...]   Sortida: 4-RESULTATS/v108_20260926/flat2d_v2/M1_<mesura>.json"""
import sys, json
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import distance_transform_edt as edt
ARREL = Path(__file__).resolve().parents[4]; OUT = ARREL / '4-RESULTATS/v108_20260926/flat2d_v2'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.787, 3775.977); RL = 452.98
CAD = ARREL / '4-RESULTATS/v108_20260926/cadena'; CTL = CAD / 'control'; V2 = CAD / 'flat2d_v2'; PI = ARREL / '4-RESULTATS/v108_20260926/marrons/pilot'
CR = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw'
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/v97_refundacio_20260924')); from jutge_comu import Estat
def npy(p, ch=None):
    def f():
        a = np.load(p, mmap_mode='r'); return np.asarray(a if ch is None else a[..., ch], np.float32)
    return f
TRIOS = {   # nom: (abans, després, pilot o None)
    'compost': (npy(OUT / 'compost_control.npy'), npy(OUT / 'compost_flat2d_v2.npy'), npy(PI / 'compost_v107mascares_despres.npy')),
    'base_G': (npy(CTL / 'lineal/base_G.npy'), npy(V2 / 'lineal/base_G.npy'), npy(PI / 'lineal_v108/base_G.npy')),
    'L55_P04_WOW': (npy(CTL / 'estat_v108/L55_G.npy'), npy(V2 / 'estat_v108/L55_G.npy'), None),
    'L56_P05_WOW': (npy(CTL / 'estat_v108/L56_G.npy'), npy(V2 / 'estat_v108/L56_G.npy'), None),
    'vixen_G': (npy(PI / 'control/vixen_total.npy', 1), npy(OUT / 'apilats/vixen_total.npy', 1), npy(PI / 'flat2d/vixen_total.npy', 1)),
    'sonyA_G': (npy(CR / 'b2_sony_A/cau/sony_A_total_v36.npy', 1), npy(OUT / 'apilats/sony_A_total.npy', 1), npy(PI / 'flat2d/sony_A_total.npy', 1)),
    'sonyB_G': (npy(CR / 'b2_sony_B/cau/sony_B_total_v42.npy', 1), npy(OUT / 'apilats/cau/sony_B_total_v42.npy', 1), npy(PI / 'flat2d/cau/sony_B_total_v42.npy', 1)),
}
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RL
TH = (np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) % 360).astype(np.float32); del yy, xx
def lnv(img):
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
def ng(l, m, s): return cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
def dog(l, m, a, b): return (ng(l, m, a) if a > 0 else l) - ng(l, m, b)
def rms(x): return float(np.sqrt(np.mean(x ** 2))) if x.size else None
def mad(x): return float(1.4826 * np.median(np.abs(x - np.median(x)))) if x.size else None
def desa(nom, d):
    p = OUT / f'M1_{nom}.json'; prev = json.loads(p.read_text()) if p.exists() else {}; prev.update(d)
    p.write_text(json.dumps(prev, ensure_ascii=False, indent=1, default=lambda x: x.item() if isinstance(x, np.generic) else (x.tolist() if isinstance(x, np.ndarray) else str(x))))
quins = sys.argv[1:] or list('TEBNVL')
# ------------------------------------------------------------------ T · traços amb nuls a cada imatge
if 'T' in quins:
    C5 = json.loads((ARREL / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']; TR = []
    for k, t in enumerate(C5):
        d = np.array(t['info']['direccio'], float); d /= np.linalg.norm(d); TR.append((k + 1, np.array(t['info']['centre'], float), d, float(t['info']['llarg'])))
    def detall(img):
        m = (np.isfinite(img) & (img > 0)).astype(np.float32); l = np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32)
        ok = cv2.erode(m, np.ones((61, 61), np.uint8)) > 0
        return np.where(ok, ng(l, m, 3) - ng(l, m, 30), np.nan).astype(np.float32)
    TT = np.arange(-400, 401, 2.0)
    def perfil(D, c, d, L):
        n = np.array([-d[1], d[0]]); s = np.arange(-L / 2, L / 2 + 1e-6, 3.0)
        X = (c[0] + s[:, None] * d[0] + TT[None, :] * n[0]).astype(np.float32); Y = (c[1] + s[:, None] * d[1] + TT[None, :] * n[1]).astype(np.float32)
        P = cv2.remap(D, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan); cov = np.isfinite(P).mean(0)
        with np.errstate(all='ignore'): pr = np.nanmean(P, 0)
        return np.where(cov > 0.8, pr, np.nan)
    def solc(D, c, d, L):
        best = np.nan
        for dth in np.arange(-1.5, 1.51, 0.5):
            a = np.radians(dth); dd = np.array([d[0] * np.cos(a) - d[1] * np.sin(a), d[0] * np.sin(a) + d[1] * np.cos(a)])
            pr = perfil(D, c, dd, L); f = np.abs(TT) <= 60; fl = (np.abs(TT) >= 120) & (np.abs(TT) <= 400)
            if np.isfinite(pr[f]).sum() < 20 or np.isfinite(pr[fl]).sum() < 50: continue
            v = np.nanmin(pr[f]) - np.nanmedian(pr[fl]); best = v if not np.isfinite(best) else min(best, v)
        return best
    def dins(c, d, L, marge=100):
        e1 = c + d * L / 2; e2 = c - d * L / 2
        return min(e1[0], e2[0]) > marge and min(e1[1], e2[1]) > marge and max(e1[0], e2[0]) < W - marge and max(e1[1], e2[1]) < H - marge
    rng = np.random.default_rng(777); NULS = {}
    for k, c0, d0, L in TR:
        n0 = np.array([-d0[1], d0[0]]); rs = np.hypot(*(c0 - SOL))
        P_ = [(c0 + n0 * sh, d0) for sh in list(range(150, 1451, 130)) + list(range(-150, -1451, -130))]; R_ = []
        for ang in list(range(10, 81, 10)) + list(range(-10, -81, -10)):
            a = np.radians(ang); R_.append((c0, np.array([d0[0] * np.cos(a) - d0[1] * np.sin(a), d0[0] * np.sin(a) + d0[1] * np.cos(a)])))
        A_ = []
        while len(A_) < 200:
            rr = rs * rng.uniform(0.8, 1.2); ph = rng.uniform(0, 2 * np.pi); c = np.array([SOL[0] + rr * np.cos(ph), SOL[1] + rr * np.sin(ph)]); an = rng.uniform(0, np.pi)
            d = np.array([np.cos(an), np.sin(an)])
            if dins(c, d, L) and np.hypot(*(c - c0)) > 300 + L / 2: A_.append((c, d))
        NULS[k] = dict(P=[x for x in P_ if dins(x[0], x[1], L)], R=[x for x in R_ if dins(x[0], x[1], L)], A=A_)
    res = {}
    for nom in [n for n in TRIOS if n in (sys.argv[2:] if len(sys.argv) > 2 and sys.argv[1] == 'T' else TRIOS)]:
        for qui, f in zip(('abans', 'despres', 'pilot'), TRIOS[nom]):
            if f is None: continue
            D = detall(f()); r = {}
            for k, c0, d0, L in TR:
                v0 = float(solc(D, c0, d0, L)); rr_ = {'solc': v0}
                for q, lst in NULS[k].items():
                    vn = np.array([solc(D, c, d, L) for c, d in lst]); vn = vn[np.isfinite(vn)]
                    if len(vn) < 5 or not np.isfinite(v0): continue
                    med = float(np.median(vn)); md = float(1.4826 * np.median(np.abs(vn - med))) or 1e-9
                    rr_[q] = dict(n=int(len(vn)), mediana=med, mad=md, z=float((v0 - med) / md), p=float((np.sum(vn <= v0) + 1) / (len(vn) + 1)))
                r[f'T{k}'] = rr_
            res.setdefault(nom, {})[qui] = r; del D
            print(nom, qui, ' '.join(f"T{k}:{r[f'T{k}']['solc']*1e4:+.0f}‱(pA {r[f'T{k}'].get('A', {}).get('p', float('nan')):.3f})" for k in range(1, 7)), flush=True)
        desa('T_TRACOS', {nom: res[nom]})
# ------------------------------------------------------------------ E · energia per escales i anells (soroll de píxel = banda 0–1)
ANELLS = [(1.05, 1.5), (1.5, 2.5), (2.5, 4.0), (4.0, 6.0), (6.0, 10.0)]
if 'E' in quins:
    res = {}
    for nom in ('base_G', 'compost', 'vixen_G'):
        ab, dp, pl = TRIOS[nom]; A = ab(); B = dp(); P = pl() if pl else None
        la, ma = lnv(A); lb, mb = lnv(B); m = ma * mb
        if P is not None: lp, mp = lnv(P); m = m * mp
        ok = cv2.erode(m, np.ones((41, 41), np.uint8)) > 0; r = {}
        for a_, b_ in [(0, 1), (1, 2), (2, 4), (4, 8), (8, 16), (16, 32)]:
            da = dog(la, m, a_, b_); db = dog(lb, m, a_, b_); dpl = dog(lp, m, a_, b_) if P is not None else None; row = {}
            for r0, r1 in ANELLS:
                k = ok & (RS >= r0) & (RS < r1) & (DL > 30)
                if k.sum() < 1e4: continue
                ea, eb = rms(da[k]), rms(db[k]); row[f'{r0}-{r1}'] = dict(abans=ea, despres=eb, energia_despres_sobre_abans=(eb / ea) ** 2, dif_rms_sobre_abans=rms((db - da)[k]) / ea)
                if dpl is not None: row[f'{r0}-{r1}']['energia_pilot_sobre_abans'] = (rms(dpl[k]) / ea) ** 2
            r[f'{a_}-{b_}px'] = row; del da, db, dpl
        k = ok & (RS > 4); da = dog(la, m, 2, 16); db = dog(lb, m, 2, 16)
        r['textura_MAD_2_16_r_gt_4'] = dict(abans=mad(da[k]), despres=mad(db[k]), canvi=mad(db[k]) / mad(da[k]) - 1)
        if P is not None: r['textura_MAD_2_16_r_gt_4']['pilot_canvi'] = mad(dog(lp, m, 2, 16)[k]) / mad(da[k]) - 1
        res[nom] = r; print(nom, json.dumps({k_: {kk: round(v['energia_despres_sobre_abans'], 4) for kk, v in r[k_].items()} for k_ in ('0-1px', '2-4px')}), json.dumps(r['textura_MAD_2_16_r_gt_4']), flush=True)
        del A, B, P, la, lb, ma, mb, m
    desa('E_ENERGIA', res)
# ------------------------------------------------------------------ B · Brno per bandes
if 'B' in quins:
    ESTAT = Estat(ARREL / '4-RESULTATS/v103_banda_20260926/E/estat_v103'); res = {}; P = 2
    rs2 = RS[::P, ::P]; dl2 = DL[::P, ::P]; BR = {}
    for lid in (230, 231, 232, 233):
        Br = ESTAT.rgb(lid, pas=P); Br = 0.25 * Br[..., 0] + 0.5 * Br[..., 1] + 0.25 * Br[..., 2]; okb = Br > 0.002
        BR[lid] = (dog(np.log(np.maximum(Br, 1e-4)).astype(np.float32), okb.astype(np.float32), 1, 8), cv2.erode(okb.astype(np.uint8), np.ones((9, 9), np.uint8)).astype(bool))
    for nom in ('base_G', 'compost'):
        ab, dp, pl = TRIOS[nom]; imgs = {'abans': ab()[::P, ::P], 'despres': dp()[::P, ::P], 'pilot': pl()[::P, ::P]}
        mm = np.ones_like(imgs['abans']); L_ = {}
        for q, X in imgs.items(): l_, m_ = lnv(X); L_[q] = l_; mm = mm * m_
        Dg = {q: dog(l_, mm, 1, 8) for q, l_ in L_.items()}; okm = cv2.erode(mm, np.ones((9, 9), np.uint8)) > 0; r = {}
        for lid, (dbr, okb) in BR.items():
            row = {}
            for a_, b_ in ((1.02, 1.5), (1.5, 2.5), (2.5, 4.0), (4.0, 6.0)):
                k = okb[:okm.shape[0], :okm.shape[1]] & okm & (rs2 >= a_) & (rs2 < b_) & (dl2 > 6)
                if k.sum() < 1000: continue
                row[f'{a_}-{b_}'] = {q: float(np.corrcoef(Dg[q][k], dbr[:okm.shape[0], :okm.shape[1]][k])[0, 1]) for q in Dg}
            r[str(lid)] = row
        res[nom] = r; print(nom, json.dumps(r)[:900], flush=True)
    desa('B_BRNO', res)
# ------------------------------------------------------------------ N · nivell i color a gran escala
if 'N' in quins:
    res = {}
    for nom in ('base_G', 'compost'):
        ab, dp, pl = TRIOS[nom]; A = ab(); B = dp(); m = ((np.isfinite(A) & (A > 0)) & (np.isfinite(B) & (B > 0))).astype(np.float32)
        ok3 = cv2.erode(m, np.ones((301, 301), np.uint8)) > 0; ga = ng(A * m, m, 100); gb = ng(B * m, m, 100); z = np.abs(gb[ok3] / ga[ok3] - 1)
        res[f'nivell_{nom}'] = dict(p50=float(np.median(z)), p99=float(np.percentile(z, 99)), max=float(z.max()))
        P = pl(); gp = ng(P * m, m, 100); zp = np.abs(gp[ok3] / ga[ok3] - 1); res[f'nivell_{nom}']['pilot'] = dict(p50=float(np.median(zp)), p99=float(np.percentile(zp, 99)), max=float(zp.max()))
        print(nom, res[f'nivell_{nom}'], flush=True); del A, B, P, ga, gb, gp
    fa = np.load(CTL / 'lineal/fusion_starless.npy', mmap_mode='r'); fb = np.load(V2 / 'lineal/fusion_starless.npy', mmap_mode='r'); fp = np.load(PI / 'lineal_v108/fusion_starless.npy', mmap_mode='r')
    for nomc, ch in (('lnRG', 0), ('lnBG', 2)):
        def croma(f):
            X = np.asarray(f[..., ch], np.float32); G = np.asarray(f[..., 1], np.float32); m = (np.isfinite(X) & np.isfinite(G) & (X > 0) & (G > 0)).astype(np.float32)
            return np.where(m > 0, np.log(np.maximum(X, 1e-12) / np.maximum(G, 1e-12)), 0).astype(np.float32), m
        ca, ma = croma(fa); cb, mb = croma(fb); cp, mp = croma(fp); m = ma * mb * mp; ok = cv2.erode(m, np.ones((41, 41), np.uint8)) > 0
        da = dog(ca, m, 2, 30); db = dog(cb, m, 2, 30); row = {}
        for r0, r1 in ANELLS:
            k = ok & (RS >= r0) & (RS < r1) & (DL > 30)
            if k.sum() > 1e4: row[f'{r0}-{r1}'] = dict(abans=rms(da[k]), despres=rms(db[k]), dif=rms((db - da)[k]))
        ok3 = cv2.erode(m, np.ones((301, 301), np.uint8)) > 0; ga = ng(ca, m, 100); gb = ng(cb, m, 100); gp = ng(cp, m, 100); z = np.abs(gb - ga)[ok3]; zp = np.abs(gp - ga)[ok3]
        res[f'color_{nomc}'] = dict(dog_2_30_per_anell=row, gran_escala_abs_p50=float(np.median(z)), gran_escala_abs_p99=float(np.percentile(z, 99)), gran_escala_abs_max=float(z.max()),
                                   pilot_gran_escala_abs_p50=float(np.median(zp)), pilot_gran_escala_abs_p99=float(np.percentile(zp, 99)))
        print(nomc, json.dumps(res[f'color_{nomc}'])[:600], flush=True); del ca, cb, cp, da, db, ga, gb, gp
    desa('N_NIVELL_COLOR', res)
# ------------------------------------------------------------------ V · vora del camp de la Vixen
if 'V' in quins:
    den = np.asarray(np.load(PI / 'control/vixen_den.npy', mmap_mode='r')[::2, ::2], np.float32) > 0
    den = cv2.morphologyEx(den.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)).astype(bool)
    ds = (edt(den) - edt(~den)) * 2; ds = cv2.resize(ds.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
    yy, xx = np.mgrid[0:H, 0:W]; lliure = (xx > 200) & (yy > 200) & (xx < W - 200) & (yy < H - 200); del yy, xx
    def det(X):
        m = (np.isfinite(X) & (X > 0)).astype(np.float32); l = np.where(m > 0, np.log(np.maximum(X, 1e-12)), 0).astype(np.float32)
        return np.where(cv2.erode(m, np.ones((41, 41), np.uint8)) > 0, ng(l, m, 2) - ng(l, m, 16), np.nan)
    res = {}
    for nom in ('base_G', 'compost'):
        Ds = {q: det(f()) for q, f in zip(('abans', 'despres', 'pilot'), TRIOS[nom])}; r = {}
        for a_, b_ in ((-900, -600), (-600, -300), (-300, -100), (-100, 0), (0, 100), (100, 300), (300, 600), (600, 900), (900, 1500)):
            k = (ds >= a_) & (ds < b_) & (RS > 3) & lliure
            for X in Ds.values(): k &= np.isfinite(X)
            if k.sum() < 2e4: continue
            r[f'{a_}..{b_}'] = dict(n=int(k.sum()), **{q: mad(X[k]) for q, X in Ds.items()})
        fora = [v for k_, v in r.items() if k_.startswith('-9') or k_.startswith('-6')]; dins_ = [v for k_, v in r.items() if k_.startswith('600') or k_.startswith('900')]
        r['dins_sobre_fora'] = {q: float(np.mean([v[q] for v in dins_]) / np.mean([v[q] for v in fora]) - 1) for q in Ds}
        res[nom] = r; print(nom, json.dumps(r['dins_sobre_fora']), flush=True); del Ds
    desa('V_VORA_VIXEN', res)
# ------------------------------------------------------------------ L · arran del limbe (franja, costura, línies)
if 'L' in quins:
    y0, y1, x0, x1 = 3077 - 300, 4477 + 300, 4677 - 300, 6077 + 300   # la caixa lunar i 300 px al voltant (per veure la costura)
    sl = (slice(y0, y1), slice(x0, x1)); dl = DL[sl]; th = TH[sl]; res = {}
    BANDES = [(0, 3), (3, 10), (10, 30), (30, 60), (60, 90), (90, 120), (120, 200), (200, 400)]
    for nom in ('base_G', 'compost', 'L56_P05_WOW', 'L55_P04_WOW'):
        ab, dp, _ = TRIOS[nom]; A = ab()[sl]; B = dp()[sl]; ok = np.isfinite(A) & np.isfinite(B) & (A > 0) & (B > 0) & (dl > 0)
        D = np.where(ok, B / np.where(ok, A, 1) - 1, np.nan).astype(np.float32)
        # energia tangencial: detall al llarg de l'arc (DoG del ln, σ 1–6 px), abans i després
        la, ma = lnv(np.where(ok, A, 0)); lb, mb = lnv(np.where(ok, B, 0)); mm = ma * mb; ta = dog(la, mm, 1, 6); tb = dog(lb, mm, 1, 6)
        r = {}
        for d0, d1 in BANDES:
            k = ok & (dl >= d0) & (dl < d1)
            if k.sum() < 500: continue
            per_sector = {}
            for s0 in range(0, 360, 30):
                ks = k & (th >= s0) & (th < s0 + 30)
                if ks.sum() > 200: per_sector[s0] = dict(D_rms=rms(D[ks] - np.nanmedian(D[ks])), D_mediana=float(np.nanmedian(D[ks])), tang_abans=rms(ta[ks]), tang_despres=rms(tb[ks]))
            r[f'{d0}-{d1}px'] = dict(n=int(k.sum()), D_p1_p50_p99=np.nanpercentile(D[k], [1, 50, 99]).tolist(), D_rms=rms(D[k] - np.nanmedian(D[k])),
                                   tang_abans=rms(ta[k]), tang_despres=rms(tb[k]), tang_despres_sobre_abans=rms(tb[k]) / max(rms(ta[k]), 1e-12), per_sector_30=per_sector)
        # costura a la vora de la caixa lunar (1.400 × 1.400): |D| suavitzat just dins i just fora de cada costat
        Ds_ = cv2.GaussianBlur(np.nan_to_num(D, nan=0.0), (0, 0), 8); cost = {}
        # (fora_0, fora_1, dins_0, dins_1): 40 px a cada banda de la vora de la caixa (la caixa és [300, 1700) en aquest retall)
        for nomc, (a1, a2, b1, b2) in {'dalt': (260, 300, 300, 340), 'baix': (1700, 1740, 1660, 1700)}.items():
            cost[nomc] = dict(dins=float(np.abs(Ds_[b1:b2, 300:1700]).mean()), fora=float(np.abs(Ds_[a1:a2, 300:1700]).mean()), salt_mitja=float(Ds_[b1:b2, 300:1700].mean() - Ds_[a1:a2, 300:1700].mean()))
        for nomc, (a1, a2, b1, b2) in {'esquerra': (260, 300, 300, 340), 'dreta': (1700, 1740, 1660, 1700)}.items():
            cost[nomc] = dict(dins=float(np.abs(Ds_[300:1700, b1:b2]).mean()), fora=float(np.abs(Ds_[300:1700, a1:a2]).mean()), salt_mitja=float(Ds_[300:1700, b1:b2].mean() - Ds_[300:1700, a1:a2].mean()))
        r['costura_caixa'] = cost
        res[nom] = r; print(nom, json.dumps({k_: (round(v['D_rms'], 5), round(v['tang_despres_sobre_abans'], 4)) for k_, v in r.items() if k_.endswith('px')}), json.dumps(cost), flush=True)
    desa('L_LIMBE', res)
print('M1 FET', quins, flush=True)
