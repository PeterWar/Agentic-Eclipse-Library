"""x3 (verificador adversari de la V108 final, 27-09) · Refà amb codi PROPI quatre famílies de xifres clau sobre els composts de x2 (llegits
dels PSB) i, per a la combinació, sobre els composts F i N de v108_final (que abans es validen contra els de les rondes anteriors):
  Z · zones negres (PLE, pas 2): % de píxels a 1,3–4,5 R☉ dins del marc amb L suau (σ3) < cel; cel A = mediana per sector de 10° a 6,5–8,5 R☉
      (mediana mòbil de 3, interpolat), cel B = 5–5,6 R☉ dins del marc; amb el cel PROPI de cada versió i amb la VARA FIXA (el de la V107);
      sectors de 45°; el cel que es veu (dalt 45–135°, baix 225–315°). Màscares pròpies: base de la V107 (alfa > 0,5, erosió 150 px),
      estrelles (capa 202 de la V107 dilatada 8 px), caixa del logo, Lluna + 3 px.
  T · T1 i T2 (C1): geometria de la V93 C5; DoG σ3 − σ30 del ln; solc = mitjana |t| ≤ 6 − flancs 20–80 px (‱); p contra 300 segments a
      l'atzar amb una LLAVOR DIFERENT (777).
  B · Brno 230 (del PSB de la V107): correlació del detall tangencial 2–64 px d'arc (log, anells cada 4 px) a 2–3 i 3–4,5 R☉ (PLE).
  F · flamarada: p90 − p10 del detall tangencial σ3 − σ128 (anell ±6 px) a 3, 3,5, 4 i 4,5 R☉ (PLE).
  C · combinació: I = ln V108 − ln F − ln N + ln V107 (C1), per bandes, perfil radial (anells?) i mapa; F i N validats abans.
Sortida: 4-RESULTATS/v108_20260926/verifica_v108_final/X3_XIFRES.json i vistes/X3_*.png."""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
R0 = Path('/Users/USUARI/Desktop/Eclipse 2026')
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v73_marques_v71_20260917'))
from psb69 import PSB  # noqa: E402
cv2.setNumThreads(6)
OUT = R0 / '4-RESULTATS/v108_20260926/verifica_v108_final'; CO = OUT / 'composts'; VI = OUT / 'vistes'; VI.mkdir(exist_ok=True)
VF = R0 / '4-RESULTATS/v108_20260926/v108_final/composts'
W, H = 10551, 7506; SOL = (5361.768, 3775.748); RSOL = 440.603; LLUNA = (5375.786804312011, 3775.9774911631); RLLUNA = 452.9785129274736
MARC = (1325, 1142, 9348, 6263); T0 = time.time(); rep = {}
quins = sys.argv[1:] or ['Z', 'T', 'B', 'F', 'C']
def log(*a): print(round(time.time() - T0), 's ·', *a, flush=True)


def canvas(p, lid, cid, fill=0):
    a, (x, y) = p.channel(lid, cid); out = np.full((H, W), fill, np.uint16); h, w = a.shape
    xa, ya, xb, yb = max(x, 0), max(y, 0), min(x + w, W), min(y + h, H)
    if xb > xa and yb > ya: out[ya:yb, xa:xb] = a[ya - y:yb - y, xa - x:xb - x]
    return out


P7 = PSB(str(R0 / '1-PHOTOSHOP/V107.psb'))
# ---- geometria pròpia (pas 1)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL
TH = (np.degrees(np.arctan2(-(yy - SOL[1]), xx - SOL[0])) % 360).astype(np.float32); LL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) < RLLUNA + 3; del yy, xx
base = canvas(P7, 3, -1) > 32767; base = cv2.erode(base.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (151, 151))) > 0
a202 = canvas(P7, 202, -1).astype(np.float32) * canvas(P7, 202, -2).astype(np.float32) > 0
est = cv2.dilate(a202.astype(np.uint8), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17))) > 0; del a202
logo = np.zeros((H, W), bool); logo[5187 - 60:6264 + 60, 8228 - 60:9351 + 60] = True
OK = base & ~est & ~logo & ~LL; MC = np.zeros((H, W), bool); MC[MARC[1]:MARC[3], MARC[0]:MARC[2]] = True
rep['mascara_ok_frac'] = float(OK.mean())
L = {p: np.load(CO / f'L_{p}.npy', mmap_mode='r') for p in ('V107', 'V108')}
C1 = {p: np.load(CO / f'C1_{p}.npy', mmap_mode='r') for p in ('V107', 'V108')}

# ================================================================ Z
if 'Z' in quins:
    r2, t2, ok2, mc2, ll2 = RS[::2, ::2], TH[::2, ::2], OK[::2, ::2], MC[::2, ::2], LL[::2, ::2]
    def cel(Ls, sel):
        sec = (t2 // 10).astype(int) % 36
        v = np.array([np.median(Ls[sel & (sec == i)]) if (sel & (sec == i)).sum() > 300 else np.nan for i in range(36)])
        i_ = np.arange(36); g = np.isfinite(v); v = np.interp(i_, i_[g], v[g], period=36)
        vv = np.concatenate([v[-1:], v, v[:1]]); v = np.array([np.median(vv[i:i + 3]) for i in range(36)])
        x = t2 / 10 - 0.5; i0 = np.floor(x).astype(int) % 36; f = x - np.floor(x)
        return v, ((1 - f) * v[i0] + f * v[(i0 + 1) % 36]).astype(np.float32)
    Z = ok2 & mc2 & (r2 >= 1.3) & (r2 < 4.5); res = {}; fix = {}
    for p in ('V107', 'V108'):
        L2 = np.ascontiguousarray(L[p][::2, ::2]); Ls = cv2.GaussianBlur(L2, (0, 0), 3.0)
        vA, sA = cel(Ls, ok2 & (r2 >= 6.5) & (r2 < 8.5) & (Ls > 1e-3)); vB, sB = cel(Ls, ok2 & mc2 & (r2 >= 5.0) & (r2 < 5.6) & (Ls > 1e-3))
        if p == 'V107': fix = dict(A=sA, B=sB)
        o = {}
        for k, s in (('A', sA), ('B', sB), ('Afix_V107', fix['A']), ('Bfix_V107', fix['B'])):
            n = Z & (Ls < s); o[k] = dict(total_pc=round(100 * n.sum() / Z.sum(), 2),
                                          sectors45_pc=[round(100 * float(n[Z & (t2 >= a) & (t2 < a + 45)].mean()), 1) for a in range(0, 360, 45)],
                                          bandes_pc={f'{a}-{b}': round(100 * float(n[Z & (r2 >= a) & (r2 < b)].mean()), 2) for a, b in ((1.3, 2), (2, 3), (3, 4.5))})
        o['cel_A_max_min'] = round(float(vA.max() / vA.min()), 3)
        for nom, (ra, rb, vm) in {'5-5.6_marc': (5.0, 5.6, ok2 & mc2), '6.5-8.5': (6.5, 8.5, ok2)}.items():
            for lloc, (a, b) in {'dalt': (45, 135), 'baix': (225, 315)}.items():
                o.setdefault('cel_que_es_veu', {})[f'{nom}_{lloc}'] = float(np.median(L2[vm & (r2 >= ra) & (r2 < rb) & (t2 >= a) & (t2 < b)]))
        res[p] = o; del L2, Ls
    res['cel_quocient_V108_V107'] = {k: round(res['V108']['cel_que_es_veu'][k] / v, 3) for k, v in res['V107']['cel_que_es_veu'].items()}
    rep['Z'] = res; log('Z', json.dumps({p: {k: res[p][k]['total_pc'] for k in ('A', 'B', 'Afix_V107', 'Bfix_V107')} for p in ('V107', 'V108')}), res['cel_quocient_V108_V107'])

# ================================================================ T
def lnm(img):
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
if 'T' in quins or 'C' in quins:
    C5 = json.loads((R0 / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']; TR = []
    for k, t in enumerate(C5):
        d = np.array(t['info']['direccio'], float); d /= np.linalg.norm(d)
        TR.append((k + 1, np.array(t['info']['centre'], float) + float(t['info']['V0_minim_t']) * np.array([-d[1], d[0]]), d, float(t['info']['llarg'])))
    TT = np.arange(-80, 81, 1.0); CORE = np.abs(TT) <= 6; FL = (np.abs(TT) >= 20) & (np.abs(TT) <= 80)
    def detall(img):
        l, m = lnm(np.asarray(img, np.float32)); g = lambda s: cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
        return np.where(cv2.erode(m, np.ones((61, 61), np.uint8)) > 0, g(3) - g(30), np.nan).astype(np.float32)
    def solc(D, c, d, Lg):
        n = np.array([-d[1], d[0]]); s = np.arange(-Lg / 2, Lg / 2 + 1e-6, 2.0)
        X = (c[0] + s[:, None] * d[0] + TT[None, :] * n[0]).astype(np.float32); Y = (c[1] + s[:, None] * d[1] + TT[None, :] * n[1]).astype(np.float32)
        P = cv2.remap(D, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
        if np.isfinite(P).all(1).mean() < 0.9: return np.nan
        with np.errstate(all='ignore'): pr = np.nanmean(P, 0)
        return float(1e4 * (np.nanmean(pr[CORE]) - np.nanmean(pr[FL])))
if 'T' in quins:
    rng = np.random.default_rng(777); NUL = {}
    for k, c0, d0, Lg in TR[:2]:
        rs = np.linalg.norm(c0 - np.array(SOL)); A_ = []
        while len(A_) < 300:
            ang = rng.uniform(0, 2 * np.pi); rr = rs * rng.uniform(0.65, 1.35); c = np.array(SOL) + rr * np.array([np.cos(ang), np.sin(ang)])
            th = rng.uniform(0, np.pi); d = np.array([np.cos(th), np.sin(th)]); e1, e2 = c + d * Lg / 2, c - d * Lg / 2
            if min(e1[0], e2[0]) > 150 and min(e1[1], e2[1]) > 150 and max(e1[0], e2[0]) < W - 150 and max(e1[1], e2[1]) < H - 150: A_.append((c, d))
        NUL[k] = A_
    res = {}; vals = {}
    for p in ('V107', 'V108'):
        D = detall(C1[p])
        for k, c0, d0, Lg in TR[:2]:
            t = solc(D, c0, d0, Lg); A_ = np.array([solc(D, c, d, Lg) for c, d in NUL[k]]); ok = np.isfinite(A_); vals[(p, k)] = (t, A_)
            res.setdefault(f'T{k}', {})[p] = dict(solc_ppm=round(t, 1), p_atzar=round(float(((A_[ok] <= t).sum() + 1) / (ok.sum() + 1)), 4), z=round(float((t - A_[ok].mean()) / A_[ok].std()), 2))
        del D
    for k in (1, 2):
        dn = vals[('V108', k)][1] - vals[('V107', k)][1]; ok = np.isfinite(dn); dt = vals[('V108', k)][0] - vals[('V107', k)][0]
        res[f'T{k}']['z_canvi'] = round(float((dt - dn[ok].mean()) / dn[ok].std()), 2)
    rep['T'] = res; log('T', json.dumps(res))

# ================================================================ B i F (PLE, dins del marc)
if 'B' in quins or 'F' in quins:
    x0, y0, x1, y1 = MARC; okf = OK[y0:y1, x0:x1].astype(np.float32)
    def pol(a, X, Y): return cv2.remap(np.ascontiguousarray(a, np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)
    def anell(rs_list):
        out = []
        for rr in rs_list:
            n = int(2 * np.pi * rr); t = np.linspace(0, 2 * np.pi, n, endpoint=False, dtype=np.float32)
            out.append(((SOL[0] - x0 + np.cos(t) * rr).astype(np.float32)[None, :], (SOL[1] - y0 - np.sin(t) * rr).astype(np.float32)[None, :]))
        return out
    def hpw(l, w, s1, s2):
        g = lambda s: gaussian_filter1d(l * w, s, mode='wrap') / np.maximum(gaussian_filter1d(w, s, mode='wrap'), 1e-6)
        return g(s1) - g(s2), (w > 0) & (gaussian_filter1d(w, s2, mode='wrap') > 0.5)
    LM = {p: np.ascontiguousarray(L[p][y0:y1, x0:x1]) for p in ('V107', 'V108')}
if 'B' in quins:
    bb = np.stack([canvas(P7, 230, k)[y0:y1, x0:x1] for k in (0, 1, 2)], -1).astype(np.float32)
    B230 = (bb[..., 0] + 2 * bb[..., 1] + bb[..., 2]) / 4 / 65535; ab = canvas(P7, 230, -1)[y0:y1, x0:x1] > 32767; del bb
    res = {}
    for a, b in ((2, 3), (3, 4.5)):
        xs = {'V107': [], 'V108': []}; ys = []; ysn = []
        for (X, Y) in anell(np.arange(a * RSOL, b * RSOL, 4.0)):
            w = (pol(okf, X, Y)[0] > 0.999) & (pol(ab.astype(np.float32), X, Y)[0] > 0.999)
            qb = pol(B230, X, Y)[0]; w &= qb > 1e-4
            hb, wb = hpw(np.log(np.maximum(qb, 1e-4)), w.astype(np.float64), 2.0, 64.0)
            for p in ('V107', 'V108'):
                qi = pol(LM[p], X, Y)[0]; hi, wi = hpw(np.log(np.maximum(qi, 1e-4)), (w & (qi > 1e-4)).astype(np.float64), 2.0, 64.0)
                m = wb & wi; xs[p].append(hi[m])
            ys.append(hb[m]); ysn.append(np.roll(hb, len(hb) // 7)[m])   # nul: Brno girat 1/7 de volta
        yc = np.concatenate(ys); yn = np.concatenate(ysn)
        res[f'{a}-{b}'] = {p: round(float(np.corrcoef(np.concatenate(xs[p]), yc)[0, 1]), 4) for p in xs}
        res[f'{a}-{b}']['nul_V108'] = round(float(np.corrcoef(np.concatenate(xs['V108']), yn)[0, 1]), 4)
    rep['B'] = res; log('B', json.dumps(res))
if 'F' in quins:
    res = {}
    for rs in (3.0, 3.5, 4.0, 4.5):
        rr_ = np.arange(rs * RSOL - 6, rs * RSOL + 6.1, 2.0); n = int(2 * np.pi * rs * RSOL); t = np.linspace(0, 2 * np.pi, n, endpoint=False)
        X = (SOL[0] - x0 + np.cos(t)[None, :] * rr_[:, None]).astype(np.float32); Y = (SOL[1] - y0 - np.sin(t)[None, :] * rr_[:, None]).astype(np.float32)
        v = pol(okf, X, Y).min(0) > 0.999; o = {}
        for p in ('V107', 'V108'):
            lp = np.log(np.maximum(pol(LM[p], X, Y).mean(0), 1e-3)).astype(np.float64); h, wv = hpw(lp, v.astype(np.float64), 3.0, 128.0)
            x = h[v]; o[p] = float(np.percentile(x, 90) - np.percentile(x, 10))
        o['quocient'] = round(o['V108'] / o['V107'], 3); res[f'{rs:g}'] = o
    rep['F'] = res; log('F', json.dumps({k: v['quocient'] for k, v in res.items()}))

# ================================================================ C · combinació
if 'C' in quins:
    val = {}
    for nom, a, b in (('C1_F_vs_compost_flat2d_v5', VF / 'C1_F.npy', R0 / '4-RESULTATS/v108_20260926/flat2d_v5/compost_flat2d_v5.npy'),
                      ('C1_V107_verif_vs_compost_control', CO / 'C1_V107.npy', R0 / '4-RESULTATS/v108_20260926/flat2d_v2/compost_control.npy')):
        A_ = np.load(a, mmap_mode='r'); B_ = np.load(b, mmap_mode='r'); mx = 0.0
        for y in range(0, H, 1000): mx = max(mx, float(np.abs(np.asarray(A_[y:y + 1000], np.float64) - np.asarray(B_[y:y + 1000], np.float64)).max()))
        val[nom] = mx
    A_ = np.load(VF / 'L_N.npy', mmap_mode='r')[::2, ::2]; B_ = np.load(R0 / '4-RESULTATS/v108_20260926/negres_v2/pas2/L_v4_CEL_G_MAX_T_e30_W_H0.npy')
    val['L_N_pas2_vs_negres_v2'] = float(np.abs(np.asarray(A_, np.float64) - B_).max()); rep['C_validacio_F_N'] = val; log('C val', val)
    def ln(a): return np.log(np.maximum(np.asarray(a, np.float32), 1e-4))
    I = ln(C1['V108']) - ln(np.load(VF / 'C1_F.npy', mmap_mode='r')) - ln(np.load(VF / 'C1_N.npy', mmap_mode='r')) + ln(C1['V107'])
    DV = ln(C1['V108']) - ln(C1['V107'])
    DLb = np.hypot(*np.meshgrid(np.arange(W, dtype=np.float32) - LLUNA[0], np.arange(H, dtype=np.float32) - LLUNA[1])) - RLLUNA
    zona = OK & MC & (DLb > 40); res = {}
    for a, b in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 7), (7, 9.5)):
        m = zona & (RS >= a) & (RS < b); x = I[m]; y = DV[m]
        res[f'{a}-{b}'] = dict(rms_I_pc=round(100 * float(np.sqrt(np.mean(x.astype(np.float64) ** 2))), 3), rms_canvi_V108_pc=round(100 * float(np.sqrt(np.mean(y.astype(np.float64) ** 2))), 3),
                              p99_9_absI_pc=round(100 * float(np.percentile(np.abs(x), 99.9)), 3), max_absI_pc=round(100 * float(np.abs(x).max()), 3))
    res['limbe_0-30px_max_absI'] = float(np.abs(I[(DLb >= 0) & (DLb < 30)]).max()); res['lluna_max_absI'] = float(np.abs(I[DLb < 0]).max())
    # anells: perfil radial de la mediana azimutal de I (pas 2 px) i el seu salt més gran entre radis veïns
    rb = (RS * RSOL / 2).astype(np.int32); sel = zona & (RS >= 1.1) & (RS < 9.5)
    idx = rb[sel]; vals = I[sel]; order = np.argsort(idx, kind='stable'); idx = idx[order]; vals = vals[order]; u, st = np.unique(idx, return_index=True)
    prof = np.array([np.median(v) for v in np.split(vals, st[1:])]); dprof = np.abs(np.diff(prof))
    res['perfil_radial_I'] = dict(rang_pc=round(100 * float(prof.max() - prof.min()), 3), salt_max_entre_radis_veins_pc=round(100 * float(dprof.max()), 4),
                                  salt_p99_pc=round(100 * float(np.percentile(dprof, 99)), 4), on_R_sol=round(float(u[np.argmax(dprof)] * 2 / RSOL), 3))
    # línies: el mateix per azimut (mediana per 0,25°) a 1,3–7 R☉
    tb = (TH * 4).astype(np.int32); sel2 = zona & (RS >= 1.3) & (RS < 7); a_ = np.bincount(tb[sel2], I[sel2].astype(np.float64), 1440) / np.maximum(np.bincount(tb[sel2], None, 1440), 1)
    da = np.abs(np.diff(a_)); res['perfil_azimutal_I'] = dict(salt_max_pc=round(100 * float(da.max()), 4), salt_p99_pc=round(100 * float(np.percentile(da, 99)), 4), on_graus=float(np.argmax(da) / 4))
    rep['C'] = res; log('C', json.dumps(res))
    # mapa de I (pas 4, ±0,5 %) i de ln V108 − ln V107 (±15 %)
    for nom, arr, s in (('X3_INTERACCIO_I', I, 0.005), ('X3_CANVI_V108_V107', DV, 0.15)):
        a4 = cv2.resize(arr, (W // 4, H // 4), interpolation=cv2.INTER_AREA); v = np.clip(a4 / s, -1, 1)
        img = np.stack([np.clip(1 + np.minimum(v, 0), 0, 1), 1 - np.abs(v), np.clip(1 - np.maximum(v, 0), 0, 1)], -1)[..., ::-1]  # blau = negatiu, vermell = positiu
        cv2.imwrite(str(VI / f'{nom}.png'), (img * 255).astype(np.uint8))
    del I, DV
(OUT / ('X3_XIFRES_' + ''.join(quins) + '.json')).write_text(json.dumps(rep, ensure_ascii=False, indent=1) + '\n'); log('FET')
