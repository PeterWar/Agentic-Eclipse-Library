"""m1 (V108 · v108_final) · MESURES de la V108 contra la V107, amb les mateixes mètriques i els mateixos nuls de les rondes anteriors, sobre els
composts de m0 (V107, V108, F = flat2d_v5 sol, N = negres_v2 sol). Totes les funcions són CÒPIES literals (només canvien les entrades):
  Z · zones negres i cel (sobre PLE, pas 2): a1_avalua.zones de negres_v2 (A = cel del sector de 10° a 6,5–8,5 R☉ amb mediana mòbil;
      B = 5,0–5,6 R☉ dins del marc), per bandes, sectors de 45° i píxel a píxel; + VARA FIXA (el cel de la V107 aplicat a totes les piles);
      i el mateix amb el mètode del verificador (verifica2_negres/w1_zones: geometria pròpia, sense mediana mòbil, Afix/Bfix, cel dalt/baix,
      canvi del compost i la rectificació de la cua fosca 6–64 px). El cel que es veu (dalt, baix, dreta, esquerra).
  D · detall de a1_avalua (PLE): rms de la DoG del ln a 0–1, 1–2, 2–8, 8–32 px (pas 1, al marc) i 32–128 (pas 2) per bandes; soroll del cel;
      ordre clar/fosc; perles 1,02–1,15; flamarada (p90 − p10 del detall tangencial als anells 1,5…4,5 R☉); buits i plomalls 4–64 px;
      Brno 230–233 (correlació del detall tangencial 2–64 px d'arc, per bandes). I el canvi del compost per bandes amb el control nul.
  T · els sis traços T1–T6 (sobre C1): geometria fixa de la V93 C5 (t0 = V0_minim_t), DoG σ3−σ30 del ln, solc |t| ≤ 6 − flancs 20–80 px;
      nuls a cada imatge: 28 paral·leles i 300 segments a l'atzar (llavor 4242, la de m1 de flat2d_v3/v4); z_canvi contra el canvi dels nuls.
  S · prova cura/injecció per bandes (DoG del ln 0–1 … 16–32 px) i anells, nul desplaçat (53, −37) (m1 S, sobre C1): l'energia per escales.
  B · Brno 230–232 (m1 B, sobre C1): DoG σ1–8 i σ2–16 per anells, nul = Brno desplaçat (41, −27).
  FP· plomalls: contrast azimutal per anells de 0,1 R☉ (m1 F) · perles: 300 pics a 0–60 px del limbe (m1 P). Sobre C1.
  L · limbe: rms de (X/V107 − 1) a 0–3, 3–10, 10–30, 30–90, 90–200 px del limbe (m1 L), sobre C1 i sobre PLE; els 7 píxels de la protuberància.
  K · color a gran escala del compost PLE (pas 2): |Δ ln R/G| i |Δ ln B/G| a σ100 px i el nivell a σ100 (m1 K, adaptat al compost RGB).
  C · la COMBINACIÓ: Δ_X = ln X − ln V107; interacció I = Δ_V108 − Δ_F − Δ_N (el que la V108 fa i no fan per separat), per bandes, per escales
      i on és màxima.
  G · el ganxo: el ràster del genoll a la v108 (ganxo − estàndard, base del flat 2D) contra el de negres_v2 (candidat − estàndard del control);
      el rebut del ganxo (base, filtres, màscares i opacitats de la V107).
Ús: m1_mesures_v108.py [Z D T S B FP FP2 L K C C2 G]   Sortida: 4-RESULTATS/v108_20260926/v108_final/M1_<part>.json (només lectura de la resta)."""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
R0 = Path(__file__).resolve().parents[4]
V8R = R0 / '4-RESULTATS/v108_20260926'; OUT = V8R / 'v108_final'; CO = OUT / 'composts'
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v108_20260926/negres'))
from comu_negres import W, H, SOL, RSOL, LLUNA, RLLUNA, MARC, BANDES, NB, mascares, logL, dog, cel_local, desa, E   # noqa: E402
cv2.setNumThreads(6)
PILES = ('V107', 'V108', 'F', 'N'); ALTRES = ('V108', 'F', 'N')
quins = sys.argv[1:] or ['Z', 'D', 'T', 'S', 'B', 'FP', 'FP2', 'L', 'K', 'C', 'C2', 'G']
T0 = time.time()
def Lp(nom): return np.load(CO / f'L_{nom}.npy', mmap_mode='r')
def C1(nom): return np.load(CO / f'C1_{nom}.npy', mmap_mode='r')
def desa_m(nom, d): desa(OUT / f'M1_{nom}.json', d); print('desat M1', nom, round(time.time() - T0), 's', flush=True)
def lnm(img):
    m = (np.isfinite(img) & (img > 0)).astype(np.float32); return np.where(m > 0, np.log(np.maximum(img, 1e-12)), 0).astype(np.float32), m
def ng(l, m, s): return cv2.GaussianBlur(l * m, (0, 0), s) / np.maximum(cv2.GaussianBlur(m, (0, 0), s), 1e-6)
def rms(x): return float(np.sqrt(np.mean(x.astype(np.float64) ** 2))) if x.size else None


# ============================================================ Z · zones negres i cel (PLE, pas 2)
if 'Z' in quins or 'D' in quins:
    G2 = mascares((0, 0, W, H), 2); r2, th2, ok2, marc2 = G2['r'], G2['th'], G2['ok'], G2['marc']; okm2 = ok2 & marc2
    yy2, xx2 = np.mgrid[0:H:2, 0:W:2].astype(np.float32)
    lluna2 = np.hypot(xx2 - LLUNA[0], yy2 - LLUNA[1]) < RLLUNA + 3; del yy2, xx2
    ZONA_B = marc2 & ~lluna2 & (r2 >= 1.3) & (r2 < 4.5)
    L2 = {p: np.ascontiguousarray(Lp(p)[::2, ::2]) for p in PILES}

if 'Z' in quins:
    def cel_sector_B(L, valid, ra=5.0, rb=5.6, nsec=36):
        """Còpia de a1_avalua.cel_sector_B (vn1.cel_sector del verificador)."""
        s = valid & (r2 >= ra) & (r2 < rb) & (L > 1e-4); sec = (th2 * nsec / 360).astype(int) % nsec
        v = np.array([np.median(L[s & (sec == i)]) if (s & (sec == i)).sum() > 200 else np.nan for i in range(nsec)])
        good = ~np.isnan(v); idx = np.arange(nsec); v = np.interp(idx, idx[good], v[good], period=nsec)
        x = th2 * nsec / 360 - 0.5; i0 = np.floor(x).astype(int) % nsec; f = (x - np.floor(x)).astype(np.float32)
        return v, ((1 - f) * v[i0] + f * v[(i0 + 1) % nsec]).astype(np.float32)

    def zones_a1(L, fix=None):
        """Còpia de a1_avalua.zones + la VARA FIXA (fix = els cels suaus de la V107)."""
        out = {}; Ls = cv2.GaussianBlur(L, (0, 0), 3.0)
        cvA, skyA = cel_local(L, r2, th2, ok2); cvAs, skyAs = cel_local(Ls, r2, th2, ok2)
        vB, skyB = cel_sector_B(Ls, marc2 & ~lluna2)
        zA = okm2 & (r2 >= 1.3) & (r2 < 4.5); zB = ZONA_B & (L > 1e-4)
        refs = {'A_cel_6.5-8.5': (skyAs, zA), 'B_cel_5-5.6_marc': (skyB, zB)}
        if fix is not None: refs.update({'Afix_cel_V107_6.5-8.5': (fix['skyAs'], zA), 'Bfix_cel_V107_5-5.6_marc': (fix['skyB'], zB)})
        masks = {}
        for nom, (sky, z) in refs.items():
            neg = z & (Ls < sky); masks[nom] = neg; d = dict(total=float(neg.sum() / z.sum()))
            for a, b in ((1.3, 2), (2, 3), (3, 4.5)):
                m = z & (r2 >= a) & (r2 < b); d[f'{a:g}-{b:g}'] = float(neg[m].sum() / m.sum())
            d['sectors_45'] = {f'{s}-{s + 45}': float(neg[z & (th2 >= s) & (th2 < s + 45)].mean()) for s in range(0, 360, 45)}
            d['deficit_mitja_rel_suau'] = float(np.mean(1 - Ls[neg] / sky[neg])) if neg.any() else 0.0
            out[nom] = d
        out['A_cel_6.5-8.5']['pixel_a_pixel'] = float((L[zA] < skyA[zA]).mean())
        neg = zA & (L < skyA); out['A_cel_6.5-8.5']['deficit_mitja_rel_pixel'] = float(np.mean(1 - L[neg] / skyA[neg])) if neg.any() else 0.0
        out['cel_A_sectors_10'] = [float(v) for v in cvA]; out['cel_B_sectors_10'] = [float(v) for v in vB]
        out['cel_A_max_sobre_min'] = float(cvA.max() / cvA.min()); out['cel_B_max_sobre_min'] = float(vB.max() / vB.min())
        for nom, (ra, rb, vm) in {'cel_5-5.6_marc': (5.0, 5.6, marc2 & ~lluna2), 'cel_6.5-8.5': (6.5, 8.5, ok2)}.items():
            for lloc, (s0, s1) in {'dalt_45-135': (45, 135), 'baix_225-315': (225, 315), 'dreta_315-45': (315, 405), 'esquerra_135-225': (135, 225)}.items():
                th_ = np.where(th2 < s0 % 360, th2 + 360, th2) if s1 > 360 else th2
                m = vm & (r2 >= ra) & (r2 < rb) & (th_ >= s0) & (th_ < s1) & (L > 1e-4)
                out.setdefault('cel_que_es_veu', {}).setdefault(nom, {})[lloc] = float(np.median(L[m]))
        return out, dict(skyAs=skyAs, skyB=skyB), masks

    # --- el mètode del verificador (w1_zones), amb la seva geometria
    sys.path.insert(0, str(R0 / '3-RECERCA/tools/v108_20260926/verifica2_negres'))
    from w0_comu import geo as geo_w1   # noqa: E402
    GW = geo_w1(pas=2); rw, thw, okw, marcw = GW['r'], GW['th'], GW['ok'], GW['marc']; ZW = okw & marcw & (rw >= 1.3) & (rw < 4.5)
    def cel_sector_w(Ls, valid, ra, rb):
        s = valid & (rw >= ra) & (rw < rb) & (Ls > 1e-4); sec = (thw // 10).astype(int) % 36
        v = np.array([np.median(Ls[s & (sec == i)]) if (s & (sec == i)).sum() > 200 else np.nan for i in range(36)])
        g = np.isfinite(v); ii = np.arange(36); return np.interp(ii, ii[g], v[g], period=36)
    def camp_w(v):
        x = thw / 10 - 0.5; i0 = np.floor(x).astype(int) % 36; f = (x - np.floor(x)).astype(np.float32)
        return ((1 - f) * v[i0] + f * v[(i0 + 1) % 36]).astype(np.float32)
    def zones_w1(L, vfix=None):
        Ls = cv2.GaussianBlur(L, (0, 0), 3.0); o = {}
        vA = cel_sector_w(Ls, okw, 6.5, 8.5); vB = cel_sector_w(Ls, okw & marcw, 5.0, 5.6); refs = {'A': vA, 'B': vB}
        if vfix: refs.update({'Afix': vfix['A'], 'Bfix': vfix['B']})
        for k, v in refs.items():
            neg = ZW & (Ls < camp_w(v)); d = dict(total=float(neg.sum() / ZW.sum()))
            for a, b in ((1.3, 2), (2, 3), (3, 4.5)):
                m = ZW & (rw >= a) & (rw < b); d[f'{a:g}-{b:g}'] = float(neg[m].mean())
            d['sectors45'] = [float(neg[ZW & (thw >= s) & (thw < s + 45)].mean()) for s in range(0, 360, 45)]; o[k] = d
        sky = camp_w(vA); o['A']['pixel_a_pixel'] = float((L[ZW] < sky[ZW]).mean())
        o['cel_A_max_min'] = float(vA.max() / vA.min()); o['cel_B_max_min'] = float(vB.max() / vB.min())
        return o, refs
    def cel_veu_w(L):
        o = {}
        for nom, (ra, rb, vm) in {'5-5.6_marc': (5.0, 5.6, okw & marcw), '6.5-8.5': (6.5, 8.5, okw)}.items():
            for lloc, (s0, s1) in {'dalt': (45, 135), 'baix': (225, 315)}.items():
                m = vm & (rw >= ra) & (rw < rb) & (thw >= s0) & (thw < s1); o[f'{nom}_{lloc}'] = float(np.median(L[m]))
        return o
    def resid(L):
        l = np.log(np.maximum(L, 1e-4)); return cv2.GaussianBlur(l, (0, 0), 3.0) - cv2.GaussianBlur(l, (0, 0), 32.0)
    res = {}; mapes = {}
    z0, fix0, m0 = zones_a1(L2['V107']); res['a1'] = {'V107': z0}; mapes['V107'] = m0
    w0, refw0 = zones_w1(L2['V107']); res['w1'] = {'V107': w0}; cw0 = cel_veu_w(L2['V107']); R0r = resid(L2['V107'])
    for p in ALTRES:
        z, _, mm = zones_a1(L2[p], fix0); res['a1'][p] = z; mapes[p] = mm
        w, _ = zones_w1(L2[p], refw0); res['w1'][p] = w
        cw = cel_veu_w(L2[p]); res.setdefault('w1_cel_quocient', {})[p] = {k: cw[k] / cw0[k] for k in cw0}
        res.setdefault('a1_cel_que_es_veu_quocient', {})[p] = {n: {k: z['cel_que_es_veu'][n][k] / z0['cel_que_es_veu'][n][k] for k in z0['cel_que_es_veu'][n]} for n in z0['cel_que_es_veu']}
        dl = np.log(np.maximum(L2[p], 1e-4)) - np.log(np.maximum(L2['V107'], 1e-4)); ch = {}
        zonesn = {'1.02-1.3': (1.02, 1.3, 0, 360), '1.3-2': (1.3, 2, 0, 360), '2-3': (2, 3, 0, 360), '3-4.5': (3, 4.5, 0, 360), '4.5-7': (4.5, 7, 0, 360), '7-9.5': (7, 9.5, 0, 360),
                  'nul_baix_225-315_1.3-3': (1.3, 3, 225, 315)}
        for k, (a, b, s0, s1) in zonesn.items():
            m = okw & marcw & (rw >= a) & (rw < b) & (thw >= s0) & (thw < s1); x = dl[m]
            ch[k] = dict(p1_p50_p99=[float(q) for q in np.percentile(x, [1, 50, 99])], frac_gt_0_5pc=float((np.abs(x) > 0.005).mean()), frac_gt_2pc=float((np.abs(x) > 0.02).mean()), mitj_abs=float(np.abs(x).mean()))
        res.setdefault('w1_canvi_compost_lnL', {})[p] = ch; del dl
        R1r = resid(L2[p]); rect = {}
        for a, b in ((2, 3), (3, 4.5), (4.5, 7), (7, 9.5)):
            m = okw & marcw & (rw >= a) & (rw < b) & (GW['dl'] > 60); x0, x1 = R0r[m], R1r[m]; q0 = np.percentile(x0, [1, 5, 50, 95, 99]); q1 = np.percentile(x1, [1, 5, 50, 95, 99])
            rect[f'{a:g}-{b:g}'] = dict(cua_fosca_p5_quocient=float((q1[1] - q1[2]) / (q0[1] - q0[2])), cua_clara_p95_quocient=float((q1[3] - q1[2]) / (q0[3] - q0[2])),
                                       cua_fosca_p1_quocient=float((q1[0] - q1[2]) / (q0[0] - q0[2])), cua_clara_p99_quocient=float((q1[4] - q1[2]) / (q0[4] - q0[2])))
        res.setdefault('w1_rectificacio_6-64px', {})[p] = rect; del R1r
    del R0r
    np.savez_compressed(OUT / 'ZONES_NEGRES_pas2.npz', **{f'{p}__{k.split("_")[0]}': np.packbits(v) for p, mm in mapes.items() for k, v in mm.items()}, forma=np.array(L2['V107'].shape))
    desa_m('Z_ZONES_NEGRES', res)

# ============================================================ D · detall, flamarada, buits/plomalls, perles, soroll, Brno (a1_avalua, PLE)
if 'D' in quins:
    def detall_pas2(L):
        """Còpia de a1_avalua.detall_pas2."""
        l = logL(L); dd = dog(l, 16, 64); R = {}
        for b in BANDES:
            m = okm2 & (r2 >= b[0]) & (r2 < b[1]); R.setdefault('rms_32-128', {})[NB(b)] = float(np.sqrt(np.mean(dd[m] ** 2)))
        ok = ZONA_B | (marc2 & ~lluna2 & (r2 >= 4.5) & (r2 < 7)); v1 = dog(l, 2, 32)
        for a, b in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 7)):
            m = ok & (r2 >= a) & (r2 < b); x = v1[m]
            R.setdefault('buits_plomalls_4-64px', {})[f'{a:g}-{b:g}'] = dict(buits_mitj_neg=float(x[x < 0].mean()), plomalls_mitj_pos=float(x[x > 0].mean()),
                                                                              p10=float(np.percentile(x, 10)), p90=float(np.percentile(x, 90)))
        return R
    BOX1 = MARC; G1 = mascares(BOX1, 1); r1, th1, ok1 = G1['r'], G1['th'], G1['ok']; mg = np.zeros_like(ok1); mg[100:-100, 100:-100] = True; okk = ok1 & mg
    x0, y0 = MARC[0], MARC[1]; BRNO = V8R / 'negres/pas1'
    RINGS = []
    for b in BANDES:
        hi = min(b[1], 9.2)
        for a_ in np.arange(b[0], hi - 1e-6, 0.1):
            rr_ = np.arange(a_ * RSOL, min(a_ + 0.1, hi) * RSOL, 4.0, dtype=np.float32)
            if len(rr_) == 0: continue
            nth = int(round(2 * np.pi * (a_ + 0.05) * RSOL)); t = np.linspace(0, 2 * np.pi, nth, endpoint=False, dtype=np.float32)
            RINGS.append((NB(b), (SOL[0] - x0 + np.cos(t)[None, :] * rr_[:, None]).astype(np.float32), (SOL[1] - y0 - np.sin(t)[None, :] * rr_[:, None]).astype(np.float32)))
    def pol(a, X, Y): return cv2.remap(np.ascontiguousarray(a, np.float32), X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0.0)
    okf = ok1.astype(np.float32); WR = [pol(okf, X, Y) > 0.999 for _, X, Y in RINGS]
    def hp(l, wv, s1=2.0, s2=64.0):
        ww = wv.astype(np.float32); lw = l * ww
        g1 = gaussian_filter1d(lw, s1, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(ww, s1, axis=1, mode='wrap'), 1e-6)
        W2 = gaussian_filter1d(ww, s2, axis=1, mode='wrap'); g2 = gaussian_filter1d(lw, s2, axis=1, mode='wrap') / np.maximum(W2, 1e-6)
        return g1 - g2, wv & (W2 > 0.5)
    BR = {}
    for lid in (230, 231, 232, 233):
        B_ = np.ascontiguousarray(np.load(BRNO / f'Brno_{lid}.npy', mmap_mode='r')); BR[lid] = []
        for (nb, X, Y), wv in zip(RINGS, WR):
            q = pol(B_, X, Y); BR[lid].append(hp(np.log(np.maximum(q, 1e-3)), wv & (q > 1e-3)))
        del B_
    def metriques_pas1(L, Lref=None):
        """Còpia de a1_avalua.metriques_pas1."""
        l = logL(L); R = {}
        SC = {'0-1': (0, 1), '1-2': (1, 2), '2-8': (2, 8), '8-32': (8, 32)}
        D = {k: dog(l, *s) for k, s in SC.items()}
        for b in BANDES:
            m = okk & (r1 >= b[0]) & (r1 < b[1]); R[NB(b)] = {f'rms_{k}': float(np.sqrt(np.mean(D[k][m] ** 2))) for k in SC}; R[NB(b)]['mediana_L'] = float(np.median(L[m]))
        R['soroll'] = {z: {k: float(np.sqrt(np.mean(D[k][m] ** 2))) for k in ('0-1', '1-2')} for z, m in {'cel_>7': okk & (r1 >= 7), 'corona_feble_4.5-7': okk & (r1 >= 4.5) & (r1 < 7)}.items()}
        del D
        if Lref is not None:
            d232 = dog(l, 2, 32); dr = dog(logL(Lref), 2, 32); R['ordre'] = {}
            for b in BANDES[1:5]:
                m = okk & (r1 >= b[0]) & (r1 < b[1]); x = dr[m]; y = d232[m]; pos = x > 0; neg = x < 0
                R['ordre'][NB(b)] = dict(corr=float(np.corrcoef(x, y)[0, 1]), pendent_clars=float((x[pos] * y[pos]).sum() / (x[pos] ** 2).sum()),
                                         pendent_foscos=float((x[neg] * y[neg]).sum() / (x[neg] ** 2).sum()), signe_invertit=float(((x * y) < 0)[np.abs(x) > np.std(x)].mean()))
            del dr, d232
        d14 = dog(l, 1, 4); m = okk & (r1 >= 1.02) & (r1 < 1.15)
        R['perles_1.02-1.15'] = dict(p99_5_dog_1_4=float(np.percentile(d14[m], 99.5)), rms_dog_1_4=float(np.sqrt(np.mean(d14[m] ** 2)))); del d14
        fl = {}
        for rs in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5):
            n = int(2 * np.pi * rs * RSOL); t = np.linspace(0, 2 * np.pi, n, endpoint=False, dtype=np.float32)
            rr_ = np.arange(rs * RSOL - 6, rs * RSOL + 6.1, 2.0, dtype=np.float32)
            X = (SOL[0] - x0 + np.cos(t)[None, :] * rr_[:, None]).astype(np.float32); Y = (SOL[1] - y0 - np.sin(t)[None, :] * rr_[:, None]).astype(np.float32)
            v = pol(okf, X, Y).min(0) > 0.999; p = pol(L, X, Y).mean(0)
            lp = np.log(np.maximum(p, 1e-3)); ww = v.astype(np.float64)
            s3 = gaussian_filter1d(lp * ww, 3.0, mode='wrap') / np.maximum(gaussian_filter1d(ww, 3.0, mode='wrap'), 1e-6)
            s128 = gaussian_filter1d(lp * ww, 128.0, mode='wrap') / np.maximum(gaussian_filter1d(ww, 128.0, mode='wrap'), 1e-6)
            hpp = (s3 - s128)[v]; fl[f'{rs:g}'] = dict(p90_menys_p10_ln=float(np.percentile(hpp, 90) - np.percentile(hpp, 10)), p10_ln=float(np.percentile(hpp, 10)), p90_ln=float(np.percentile(hpp, 90)))
        R['flamarada'] = fl
        pols = []
        for (nb, X, Y), wv in zip(RINGS, WR):
            q = pol(L, X, Y); pols.append(hp(np.log(np.maximum(q, 1e-3)), wv & (q > 1e-3)))
        fb = {}
        for nb in [NB(b) for b in BANDES]:
            ii = [i for i, rg in enumerate(RINGS) if rg[0] == nb]
            for lid in BR:
                xs, ys = [], []
                for i in ii:
                    mm = pols[i][1] & BR[lid][i][1]; xs.append(pols[i][0][mm]); ys.append(BR[lid][i][0][mm])
                xs = np.concatenate(xs); ys = np.concatenate(ys)
                if len(xs) > 5000: fb.setdefault(str(lid), {})[nb] = float(np.corrcoef(xs, ys)[0, 1])
        R['brno_corr_tangencial_2-64'] = fb
        return R
    res = {}
    L1ref = np.ascontiguousarray(Lp('V107')[MARC[1]:MARC[3], MARC[0]:MARC[2]])
    res['V107'] = dict(pas1=metriques_pas1(L1ref), pas2=detall_pas2(L2['V107']))
    for p in ALTRES:
        L1 = np.ascontiguousarray(Lp(p)[MARC[1]:MARC[3], MARC[0]:MARC[2]])
        res[p] = dict(pas1=metriques_pas1(L1, L1ref), pas2=detall_pas2(L2[p])); del L1
        dl = np.log(np.maximum(L2[p], 1e-3)) - np.log(np.maximum(L2['V107'], 1e-3)); ch = {}
        for a, b in ((1.02, 1.3), (1.3, 2), (2, 3), (3, 4.5), (4.5, 7), (7, 9.5)):
            m = okm2 & (r2 >= a) & (r2 < b); ch[f'{a:g}-{b:g}'] = [float(q) for q in np.percentile(dl[m], [1, 50, 99])] + [float((np.abs(dl[m]) > 0.005).mean())]
        m = okm2 & (r2 >= 1.3) & (r2 < 3) & (th2 >= 225) & (th2 < 315); ch['control_nul_baix_225-315_1.3-3'] = [float(q) for q in np.percentile(dl[m], [1, 50, 99])] + [float((np.abs(dl[m]) > 0.005).mean())]
        res[p]['canvi_compost_ln_p1_p50_p99_frac_gt_0_5pc'] = ch; del dl
        print('D', p, round(time.time() - T0), 's', flush=True)
    desa_m('D_DETALL', res)

# ============================================================ geometria de ple (T S B FP L)
if any(q in quins for q in ('T', 'S', 'B', 'FP', 'FP2', 'L', 'C', 'C2')):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); RS = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; DL = np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA
    TH = (np.degrees(np.arctan2(-(yy - LLUNA[1]), xx - LLUNA[0])) % 360).astype(np.float32); del yy, xx
    def ld(p, nom='C1'): return np.asarray(C1(p) if nom == 'C1' else Lp(p), np.float32)

# ============================================================ T · traços T1–T6, geometria fixa (còpia de m1 T de flat2d_v4)
if 'T' in quins:
    C5 = json.loads((R0 / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']; TR = []
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
        n0 = np.array([-d0[1], d0[0]]); rs = np.linalg.norm(c0 - np.array(SOL)); P_ = [(c0 + n0 * sh, d0) for sh in list(range(100, 1401, 100)) + list(range(-100, -1401, -100))]; A_ = []
        while len(A_) < 300:
            ang = rng.uniform(0, 2 * np.pi); rr = rs * rng.uniform(0.65, 1.35); c = np.array(SOL) + rr * np.array([np.cos(ang), np.sin(ang)]); th = rng.uniform(0, np.pi); d = np.array([np.cos(th), np.sin(th)])
            e1, e2 = c + d * L / 2, c - d * L / 2
            if min(e1[0], e2[0]) > 150 and min(e1[1], e2[1]) > 150 and max(e1[0], e2[0]) < W - 150 and max(e1[1], e2[1]) < H - 150: A_.append((c, d))
        NUL[k] = dict(P=P_, A=A_)
    R = {}
    for nom in ('C1', 'PLE'):
        vals = {}
        for p in PILES:
            D = detall(ld(p, nom)); vals[p] = {k: dict(t=solc(D, c0, d0, L), P=[solc(D, c, d, L) for c, d in NUL[k]['P']], A=[solc(D, c, d, L) for c, d in NUL[k]['A']]) for k, c0, d0, L in TR}; del D
        res = {}
        for k, c0, d0, L in TR:
            o = {}
            for p in PILES:
                x = vals[p][k]; An = np.array(x['A'], float); Pn = np.array(x['P'], float); ok = np.isfinite(An); okp = np.isfinite(Pn)
                if not np.isfinite(x['t']) or ok.sum() < 30: o[p] = None; continue
                o[p] = dict(solc_ppm=round(x['t'], 2), z_atzar=round(float((x['t'] - An[ok].mean()) / An[ok].std()), 2), p_atzar=round(float(((An[ok] <= x['t']).sum() + 1) / (ok.sum() + 1)), 4),
                            z_paral=(round(float((x['t'] - Pn[okp].mean()) / Pn[okp].std()), 2) if okp.sum() >= 8 else None), sd_atzar_ppm=round(float(An[ok].std()), 2))
            for p in ALTRES:
                if o.get(p) and o.get('V107'):
                    dn = np.array(vals[p][k]['A'], float) - np.array(vals['V107'][k]['A'], float); ok = np.isfinite(dn); dt = vals[p][k]['t'] - vals['V107'][k]['t']
                    o[f'canvi_{p}'] = round(dt, 2); o[f'z_canvi_{p}'] = round(float((dt - dn[ok].mean()) / dn[ok].std()), 2); o[f'canvi_nuls_mitja_sd_{p}'] = [round(float(dn[ok].mean()), 2), round(float(dn[ok].std()), 2)]
            res[f'T{k}'] = o
        R[nom] = res; print('T', nom, json.dumps({t: {p: (x['solc_ppm'], x['p_atzar']) if isinstance(x, dict) and 'solc_ppm' in x else x for p, x in o.items() if p in PILES} for t, o in res.items()}), flush=True)
    desa_m('T_TRACOS', R)

# ============================================================ S · cura/injecció per bandes (còpia de m1 S), sobre C1 i PLE
ANELLS = [(1.05, 1.5), (1.5, 2.5), (2.5, 4), (4, 6), (6, 10), (10, 30)]; SIG = [0, 1, 2, 4, 8, 16, 32]
if 'S' in quins:
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
    R = {}
    for nom in ('C1', 'PLE'):
        X, mx = lnm(ld('V107', nom))
        for p in ALTRES:
            Y, my = lnm(ld(p, nom)); m = (mx * my).astype(np.float32); R[f'{nom}_{p}'] = prova_s(X, Y, m); del Y, my, m
            print('S', nom, p, json.dumps({b: {r: (x['s'], x['dE_pc']) for r, x in o.items()} for b, o in R[f'{nom}_{p}'].items()}), flush=True)
        del X, mx
    desa_m('S_ENERGIA_ESCALES', R)

# ============================================================ B · Brno 230–232 (còpia de m1 B), sobre C1
if 'B' in quins:
    res = {}; CT = V8R / 'cadena/control/estat_v108'
    for cb in (230, 231, 232):
        b = np.load(CT / f'L{cb}_RGB.npy', mmap_mode='r'); bb = np.asarray(b, np.float32).mean(-1); lb, mb = lnm(bb); del bb
        for p in PILES:
            li, mi = lnm(ld(p)); m = mb * mi
            for (s1, s2) in ((1, 8), (2, 16)):
                db = ng(lb, m, s1) - ng(lb, m, s2); di = ng(li, m, s1) - ng(li, m, s2); dbs = np.roll(np.roll(db, 41, 1), -27, 0); ok = cv2.erode(m, np.ones((41, 41), np.uint8)) > 0
                for r0, r1 in ((1.02, 1.5), (1.5, 2.5), (2.5, 4), (4, 6)):
                    k = ok & (RS >= r0) & (RS < r1) & (DL > 3); k[::2] = False
                    if k.sum() < 2000: continue
                    res.setdefault(f'L{cb}', {}).setdefault(f'{s1}-{s2}', {}).setdefault(f'{r0}-{r1}', {})[p] = dict(r=round(float(np.corrcoef(db[k], di[k])[0, 1]), 4), nul=round(float(np.corrcoef(dbs[k], di[k])[0, 1]), 4))
                del db, di, dbs
            del li, mi, m
        print('B', cb, json.dumps(res[f'L{cb}'])[:800], flush=True)
    desa_m('B_BRNO', res)

# ============================================================ FP · plomalls (m1 F) i perles (m1 P), sobre C1
if 'FP' in quins:
    res = {}; la, ma = lnm(ld('V107')); ib = np.clip((TH / 0.5).astype(np.int32), 0, 719)
    for p in ALTRES:
        lb, mb = lnm(ld(p)); m = (ma * mb > 0) & (DL > 3); o = {}
        for r0 in np.arange(1.05, 6.0, 0.1):
            k = m & (RS >= r0) & (RS < r0 + 0.1)
            if k.sum() < 3000: continue
            n = np.bincount(ib[k], minlength=720); pa_ = np.bincount(ib[k], la[k], 720) / np.maximum(n, 1); pb_ = np.bincount(ib[k], lb[k], 720) / np.maximum(n, 1); vv = n > 20
            o[f'{r0:.2f}'] = dict(contrast_azimutal=round(float(np.std(pb_[vv] - np.median(pb_[vv])) / np.std(pa_[vv] - np.median(pa_[vv]))), 4),
                                  nivell_radial=round(float(np.exp(np.median(lb[k]) - np.median(la[k]))), 5), corr_perfils=round(float(np.corrcoef(pa_[vv], pb_[vv])[0, 1]), 5))
        res.setdefault('plomalls', {})[p] = o; c_ = [x['contrast_azimutal'] for x in o.values()]; r_ = [x['corr_perfils'] for x in o.values()]
        print('F', p, 'contrast', min(c_), max(c_), 'corr mín', min(r_), flush=True); del lb, mb, m
    da = ng(la, ma, 1) - ng(la, ma, 4)
    for p in ALTRES:
        lb, mb = lnm(ld(p)); m = ma * mb; db = ng(lb, m, 1) - ng(lb, m, 4)
        franja = (DL >= 0) & (DL < 60) & (m > 0); mx = cv2.dilate(da, np.ones((9, 9), np.uint8)); pk = franja & (da == mx) & (da > 0)
        ys, xs = np.nonzero(pk); o_ = np.argsort(-da[ys, xs])[:300]; ys, xs = ys[o_], xs[o_]; rat = db[ys, xs] / da[ys, xs]
        rng = np.random.default_rng(99); fy, fx = np.nonzero(franja); sel = rng.choice(len(fy), 300, replace=False); dnul = np.abs(db[fy[sel], fx[sel]] - da[fy[sel], fx[sel]])
        res.setdefault('perles', {})[p] = dict(n=int(len(ys)), despres_sobre_abans_p5_p50_p95=np.percentile(rat, [5, 50, 95]).round(4).tolist(), dif_abs_ppm_perles=round(1e4 * float(np.median(np.abs(db[ys, xs] - da[ys, xs]))), 2),
                                               dif_abs_ppm_nul=round(1e4 * float(np.median(dnul)), 2)); print('P', p, res['perles'][p], flush=True); del lb, mb, db
    desa_m('FP_PLOMALLS_PERLES', res)

# ============================================================ L · limbe (m1 L), sobre C1 i PLE
if 'L' in quins:
    res = {}; PX = [(4904, 3779), (4905, 3779), (4906, 3779), (4906, 3780), (4907, 3780), (4898, 3784), (4897, 3785)]
    for nom in ('C1', 'PLE'):
        a_ = ld('V107', nom)
        for p in ALTRES:
            b_ = ld(p, nom); ok = (a_ > 0) & (b_ > 0) & np.isfinite(a_) & np.isfinite(b_); d = np.where(ok, b_ / np.where(ok, a_, 1) - 1, np.nan); o = {}
            for d0, d1 in ((0, 3), (3, 10), (10, 30), (30, 90), (90, 200)):
                k = ok & (DL >= d0) & (DL < d1); o[f'{d0}-{d1}px'] = dict(rms_pc=round(100 * float(np.sqrt(np.nanmean(d[k] ** 2))), 3), p99_abs_pc=round(100 * float(np.nanpercentile(np.abs(d[k]), 99)), 3),
                                                                        mitjana_pc=round(100 * float(np.nanmean(d[k])), 3))
            res.setdefault(nom, {})[p] = o; del b_, d
        res.setdefault('protuberancia_7_pixels', {})[nom] = {f'{x},{y}': {p: float((C1(p) if nom == 'C1' else Lp(p))[y, x]) for p in PILES} for x, y in PX}
        del a_
    print('L', json.dumps(res)[:1500], flush=True)
    desa_m('L_LIMBE', res)

# ============================================================ K · color i nivell a gran escala (PLE, RGB a pas 2)
if 'K' in quins:
    res = {}
    def rgb2(p): return np.load(CO / f'RGB2_{p}.npy', mmap_mode='r')
    yy2, xx2 = np.mgrid[0:H:2, 0:W:2].astype(np.float32); rs2 = np.hypot(xx2 - SOL[0], yy2 - SOL[1]) / RSOL; dl2 = np.hypot(xx2 - LLUNA[0], yy2 - LLUNA[1]) - RLLUNA; del yy2, xx2
    A0 = np.asarray(rgb2('V107'), np.float32)
    for p in ALTRES:
        B0 = np.asarray(rgb2(p), np.float32); o = {}
        m = ((A0 > 1e-4).all(-1) & (B0 > 1e-4).all(-1) & (dl2 > 10)).astype(np.float32); ok3 = cv2.erode(m, np.ones((151, 151), np.uint8)) > 0
        for nm, c in (('R_G', 0), ('B_G', 2)):
            la = np.log(np.maximum(A0[..., c], 1e-6) / np.maximum(A0[..., 1], 1e-6)).astype(np.float32); lb = np.log(np.maximum(B0[..., c], 1e-6) / np.maximum(B0[..., 1], 1e-6)).astype(np.float32)
            z = (ng(lb, m, 50) - ng(la, m, 50)); o[f'color_{nm}_sigma100'] = dict(p50=float(np.median(np.abs(z[ok3]))), p99=float(np.percentile(np.abs(z[ok3]), 99)), max=float(np.abs(z[ok3]).max()),
                                                                                   per_anells_mitjana={f'{a}-{b}': float(z[ok3 & (rs2 >= a) & (rs2 < b)].mean()) for a, b in ((1.05, 1.5), (1.5, 3), (3, 6), (6, 10), (10, 30)) if (ok3 & (rs2 >= a) & (rs2 < b)).sum() > 1000})
            z2 = (ng(lb, m, 10) - ng(la, m, 10)) - z; o[f'color_{nm}_sigma20-100'] = dict(p50=float(np.median(np.abs(z2[ok3]))), p99=float(np.percentile(np.abs(z2[ok3]), 99)))
            del la, lb, z, z2
        LA = (A0[..., 0] + 2 * A0[..., 1] + A0[..., 2]) / 4; LB = (B0[..., 0] + 2 * B0[..., 1] + B0[..., 2]) / 4
        z = np.abs(ng(LB * m, m, 50) / np.maximum(ng(LA * m, m, 50), 1e-9) - 1)
        o['nivell_sigma100_abs'] = dict(p50=float(np.median(z[ok3])), p99=float(np.percentile(z[ok3], 99)), max=float(z[ok3].max()))
        res[p] = o; print('K', p, json.dumps(o)[:600], flush=True); del B0, m, ok3, LA, LB, z
    desa_m('K_COLOR', res)

# ============================================================ C · la combinació: interacció I = Δ_V108 − Δ_F − Δ_N (PLE)
if 'C' in quins:
    res = {}
    a3 = E.alfa_efectiva(3) > 0.5
    lV = np.log(np.maximum(ld('V107', 'PLE'), 1e-4)); ok = a3 & (ld('V107', 'PLE') > 1e-4)
    dX = {}
    for p in ALTRES:
        x = ld(p, 'PLE'); ok &= x > 1e-4; dX[p] = (np.log(np.maximum(x, 1e-4)) - lV).astype(np.float32); del x
    del lV
    I = (dX['V108'] - dX['F'] - dX['N']).astype(np.float32)
    bandes = {**{f'R_{a:g}-{b:g}': ok & (RS >= a) & (RS < b) & (DL >= 40) for a, b in ((1.02, 1.3), (1.3, 2), (2, 3), (3, 4.5), (4.5, 7), (7, 9.5), (9.5, 99))},
              **{f'limbe_{a}-{b}px': ok & (DL >= a) & (DL < b) for a, b in ((0, 3), (3, 10), (10, 30), (30, 90))}, 'dins_lluna': ok & (DL < 0)}
    for nb, k in bandes.items():
        if k.sum() < 1000: continue
        i_ = I[k]; o = dict(px=int(k.sum()))
        for p in ALTRES: o[f'rms_delta_{p}'] = rms(dX[p][k])
        o['rms_interaccio'] = rms(i_); o['p99_9_abs_interaccio'] = float(np.percentile(np.abs(i_), 99.9)); o['max_abs_interaccio'] = float(np.abs(i_).max())
        o['frac_abs_interaccio_gt_0_1pc'] = float((np.abs(i_) > 1e-3).mean()); o['frac_abs_interaccio_gt_0_5pc'] = float((np.abs(i_) > 5e-3).mean())
        s_ = (dX['F'] + dX['N'])[k]; v_ = dX['V108'][k]
        o['corr_delta_V108_i_suma'] = float(np.corrcoef(v_, s_)[0, 1]) if np.std(s_) > 0 and np.std(v_) > 0 else None
        o['interaccio_sobre_delta_V108'] = (o['rms_interaccio'] / o['rms_delta_V108']) if o['rms_delta_V108'] else None
        res.setdefault('per_bandes', {})[nb] = o
    # per escales (pas 2): rms de la DoG de I i de Δ_V108 a 0–2, 2–8, 8–32, 32–128 px, per bandes radials
    I2 = np.ascontiguousarray(I[::2, ::2]); V2 = np.ascontiguousarray(dX['V108'][::2, ::2]); ok2_ = ok[::2, ::2]; RS2 = RS[::2, ::2]; DL2 = DL[::2, ::2]
    I2 = np.where(ok2_, I2, 0).astype(np.float32); V2 = np.where(ok2_, V2, 0).astype(np.float32)
    for esc, (s1, s2) in {'0-2': (0, 1), '2-8': (1, 4), '8-32': (4, 16), '32-128': (16, 64)}.items():
        di = dog(I2, s1, s2); dv = dog(V2, s1, s2)
        for a, b in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 7), (7, 9.5)):
            k = ok2_ & (RS2 >= a) & (RS2 < b) & (DL2 >= 60)
            res.setdefault('per_escales_rms_I_sobre_rms_delta_V108', {}).setdefault(esc, {})[f'{a:g}-{b:g}'] = dict(rms_I=rms(di[k]), rms_dV108=rms(dv[k]), quocient=(rms(di[k]) / rms(dv[k])) if rms(dv[k]) else None)
        del di, dv
    # on és més gran (blocs de 64 px, fora de 40 px del limbe)
    Ib = np.where(ok & (DL >= 40), np.abs(I), 0); hb, wb = H // 64, W // 64
    blk = Ib[:hb * 64, :wb * 64].reshape(hb, 64, wb, 64).max((1, 3)); top = np.argsort(blk.ravel())[::-1][:12]; llocs = []
    for t in top:
        by, bx = divmod(int(t), wb); sub = Ib[by * 64:(by + 1) * 64, bx * 64:(bx + 1) * 64]; yy_, xx_ = np.unravel_index(int(np.argmax(sub)), sub.shape); y_, x_ = by * 64 + yy_, bx * 64 + xx_
        llocs.append(dict(x=int(x_), y=int(y_), R_sol=round(float(RS[y_, x_]), 3), d_limbe_px=round(float(DL[y_, x_]), 1), theta=round(float(TH[y_, x_]), 1), I=round(float(I[y_, x_]), 5),
                          dF=round(float(dX['F'][y_, x_]), 5), dN=round(float(dX['N'][y_, x_]), 5), dV108=round(float(dX['V108'][y_, x_]), 5)))
    res['on_es_mes_gran_fora_40px'] = llocs; del Ib
    Il = np.where(ok & (DL >= 0) & (DL < 40), np.abs(I), 0); t = int(np.argmax(Il)); y_, x_ = divmod(t, W)
    res['maxim_0_40px'] = dict(x=int(x_), y=int(y_), d_limbe_px=round(float(DL[y_, x_]), 2), theta=round(float(TH[y_, x_]), 1), I=float(I[y_, x_]), dF=float(dX['F'][y_, x_]), dN=float(dX['N'][y_, x_]), dV108=float(dX['V108'][y_, x_])); del Il
    np.save(CO / 'I_interaccio_pas2.npy', np.where(ok[::2, ::2], I[::2, ::2], 0).astype(np.float32))
    print('C', json.dumps(res['per_bandes'])[:2500], flush=True)
    desa_m('C_COMBINACIO', res)

# ============================================================ C2 · la interacció, dins del marc: d'on ve (regressió sobre Δ_F i Δ_N) i als traços (DoG de I, nuls)
if 'C2' in quins:
    res = {}; a3 = E.alfa_efectiva(3) > 0.5; mc = np.zeros((H, W), bool); mc[MARC[1]:MARC[3], MARC[0]:MARC[2]] = True
    lV = np.log(np.maximum(ld('V107', 'PLE'), 1e-4)); ok = a3 & (ld('V107', 'PLE') > 1e-4); dX = {}
    for p in ALTRES:
        x = ld(p, 'PLE'); ok &= x > 1e-4; dX[p] = (np.log(np.maximum(x, 1e-4)) - lV).astype(np.float32); del x
    del lV
    I = (dX['V108'] - dX['F'] - dX['N']).astype(np.float32)
    for a, b in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 7), (7, 9.5), (9.5, 99)):
        k = ok & mc & (RS >= a) & (RS < b) & (DL >= 40)
        if k.sum() < 1000: continue
        i_, f_, n_ = I[k].astype(np.float64), dX['F'][k].astype(np.float64), dX['N'][k].astype(np.float64)
        A_ = np.stack([np.ones_like(f_), f_, n_, f_ * n_], 1); cf, *_ = np.linalg.lstsq(A_, i_, rcond=None); r_ = i_ - A_ @ cf
        res.setdefault('dins_del_marc_per_bandes', {})[f'{a:g}-{b:g}'] = dict(px=int(k.sum()), mitjana_I=float(i_.mean()), rms_I=rms(i_), p99_9_abs_I=float(np.percentile(np.abs(i_), 99.9)), max_abs_I=float(np.abs(i_).max()),
            frac_abs_I_gt_0_5pc=float((np.abs(i_) > 5e-3).mean()), rms_dV108=rms(dX['V108'][k]), corr_I_dF=float(np.corrcoef(i_, f_)[0, 1]), corr_I_dN=float(np.corrcoef(i_, n_)[0, 1]),
            corr_I_dFxdN=float(np.corrcoef(i_, f_ * n_)[0, 1]), regressio_1_dF_dN_dFxdN=[float(c) for c in cf], frac_variancia_explicada=float(1 - r_.var() / i_.var()))
    # als traços: DoG σ3−σ30 de I (normalitzada amb la màscara), solc a la geometria fixa i els mateixos 300 nuls (llavor 4242)
    C5 = json.loads((R0 / '4-RESULTATS/v93_20260924/C5_PERFILS.json').read_text())['tracos']; TR = []
    for kk, t in enumerate(C5):
        d = np.array(t['info']['direccio'], float); d /= np.linalg.norm(d); TR.append((kk + 1, np.array(t['info']['centre'], float) + float(t['info']['V0_minim_t']) * np.array([-d[1], d[0]]), d, float(t['info']['llarg'])))
    TT = np.arange(-80, 81, 1.0); CORE = np.abs(TT) <= 6; FLANC = (np.abs(TT) >= 20) & (np.abs(TT) <= 80)
    m_ = ok.astype(np.float32); Iz = np.where(ok, I, 0).astype(np.float32)
    g = lambda s: cv2.GaussianBlur(Iz * m_, (0, 0), s) / np.maximum(cv2.GaussianBlur(m_, (0, 0), s), 1e-6)
    D = np.where(cv2.erode(m_, np.ones((61, 61), np.uint8)) > 0, g(3) - g(30), np.nan).astype(np.float32)
    def solc(D, c, d, L):
        n = np.array([-d[1], d[0]]); s = np.arange(-L / 2, L / 2 + 1e-6, 2.0)
        X = (c[0] + s[:, None] * d[0] + TT[None, :] * n[0]).astype(np.float32); Y = (c[1] + s[:, None] * d[1] + TT[None, :] * n[1]).astype(np.float32)
        P = cv2.remap(D, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=np.nan)
        if np.isfinite(P[:, CORE | FLANC]).all(1).mean() < 0.9: return np.nan
        with np.errstate(all='ignore'): pr = np.nanmean(P, 0)
        return float(1e4 * (np.nanmean(pr[CORE]) - np.nanmean(pr[FLANC])))
    rng = np.random.default_rng(4242)
    for kk, c0, d0, L in TR:
        n0 = np.array([-d0[1], d0[0]]); rs = np.linalg.norm(c0 - np.array(SOL)); _ = [(c0 + n0 * sh, d0) for sh in list(range(100, 1401, 100)) + list(range(-100, -1401, -100))]; A_ = []
        while len(A_) < 300:
            ang = rng.uniform(0, 2 * np.pi); rr = rs * rng.uniform(0.65, 1.35); c = np.array(SOL) + rr * np.array([np.cos(ang), np.sin(ang)]); th = rng.uniform(0, np.pi); d = np.array([np.cos(th), np.sin(th)])
            e1, e2 = c + d * L / 2, c - d * L / 2
            if min(e1[0], e2[0]) > 150 and min(e1[1], e2[1]) > 150 and max(e1[0], e2[0]) < W - 150 and max(e1[1], e2[1]) < H - 150: A_.append((c, d))
        t_ = solc(D, c0, d0, L); nn = np.array([solc(D, c, d, L) for c, d in A_]); okn = np.isfinite(nn)
        res.setdefault('tracos_interaccio', {})[f'T{kk}'] = dict(solc_I_ppm=round(t_, 2), nul_mitjana_sd_ppm=[round(float(nn[okn].mean()), 2), round(float(nn[okn].std()), 2)], z=round(float((t_ - nn[okn].mean()) / nn[okn].std()), 2))
    print('C2', json.dumps(res)[:2500], flush=True)
    desa_m('C2_INTERACCIO_MARC', res)

# ============================================================ FP2 · plomalls amb el perfil azimutal separat: < 10° (plomalls) i > 10° (nivell i cel), sobre C1
if 'FP2' in quins:
    res = {}; la, ma = lnm(ld('V107')); ib = np.clip((TH / 0.5).astype(np.int32), 0, 719)
    def sep(p_, vv, s=20.0):
        w = vv.astype(np.float64); x = np.where(vv, p_, 0.0)
        lp = gaussian_filter1d(x * w, s, mode='wrap') / np.maximum(gaussian_filter1d(w, s, mode='wrap'), 1e-6); return (p_ - lp)[vv], lp[vv]
    for p in ALTRES:
        lb, mb = lnm(ld(p)); m = (ma * mb > 0) & (DL > 3); o = {}
        for r0 in np.arange(1.05, 6.0, 0.1):
            k = m & (RS >= r0) & (RS < r0 + 0.1)
            if k.sum() < 3000: continue
            n = np.bincount(ib[k], minlength=720); pa_ = np.bincount(ib[k], la[k], 720) / np.maximum(n, 1); pb_ = np.bincount(ib[k], lb[k], 720) / np.maximum(n, 1); vv = n > 20
            ha, lpa = sep(pa_, vv); hb, lpb = sep(pb_, vv)
            o[f'{r0:.2f}'] = dict(contrast_menys_10graus=round(float(np.std(hb) / np.std(ha)), 4), contrast_mes_10graus=round(float(np.std(lpb - np.median(lpb)) / np.std(lpa - np.median(lpa))), 4),
                                  corr_menys_10graus=round(float(np.corrcoef(ha, hb)[0, 1]), 4))
        res[p] = o; print('FP2', p, {k_: (v['contrast_menys_10graus'], v['contrast_mes_10graus']) for k_, v in list(o.items())[::5]}, flush=True); del lb, mb, m
    desa_m('FP2_PLOMALLS_ESCALES', res)

# ============================================================ G · el ganxo: ràster del genoll a la v108 contra negres_v2, i el rebut
if 'G' in quins:
    res = {}; V8 = V8R / 'cadena/v108'; CT = V8R / 'cadena/control'; CAND = V8R / 'negres_v2/candidats_v4/CEL_G_MAX_T_e30_W_H0'
    org = {l.split('\t')[0]: l.rstrip('\n').split('\t')[2] for l in open(V8 / 'filtres_v108/ORIGEN.tsv').readlines()[1:]}
    yy, xx = np.ogrid[:H, :W]; RF = (np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL).astype(np.float32); DLF = (np.hypot(xx - LLUNA[0], yy - LLUNA[1]) - RLLUNA).astype(np.float32); del yy, xx
    mc = np.zeros((H, W), bool); mc[MARC[1]:MARC[3], MARC[0]:MARC[2]] = True
    for lid, tag in ((41, 'P01_NRGF'), (42, 'P01_NRGF_extrap')):
        d8 = (np.load(R0 / org[str(lid)]).astype(np.float32) - np.load(V8 / f'filtres_std/filtres/{tag}_u16.npy').astype(np.float32)) / 65535
        dn = (np.load(CAND / f'{tag}_u16.npy').astype(np.float32) - np.load(CT / f'filtres_std/filtres/{tag}_u16.npy').astype(np.float32)) / 65535
        o = {}
        for a, b in ((1.02, 1.3), (1.3, 2), (2, 3), (3, 4.5), (4.5, 7), (7, 9.5)):
            k = mc & (RF >= a) & (RF < b) & (DLF >= 40); x, y = d8[k], dn[k]
            o[f'{a:g}-{b:g}'] = dict(mitjana_v108=float(x.mean()), mitjana_negres_v2=float(y.mean()), rms_v108=rms(x), rms_negres_v2=rms(y), rms_diferencia=rms(x - y),
                                     corr=(float(np.corrcoef(x, y)[0, 1]) if x.std() > 0 and y.std() > 0 else None), frac_tocats_v108=float((np.abs(x) > 1 / 512).mean()), frac_tocats_negres_v2=float((np.abs(y) > 1 / 512).mean()))
        o['dins_40px_px_diferents'] = dict(v108=int((d8[DLF < 40] != 0).sum()), negres_v2=int((dn[DLF < 40] != 0).sum()))
        res[f'delta_genoll_{lid}'] = o; del d8, dn
    # el rebut del ganxo a la v108
    g = sorted((V8 / 'filtres_alt').glob('*/G1_*.json')); rb = json.loads(g[0].read_text()) if g else {}
    gn = [f for f in (V8R / 'negres_v2/candidats_v4').glob('G1_*.json') if 'CEL_G_MAX_T_e30_W_H0' in f.name]; rn = json.loads(gn[0].read_text()) if gn else {}
    res['rebut_ganxo_v108'] = {k: rb.get(k) for k in ('guio', 'variants_demanades', 'font', 'franja', 'base', 'filtres_std', 'psb', 'variant_cadena', 'capes', 'r_in', 'r_edge', 'r_edge_Rsol', 'model_cel_lineal_CEL', 'capes_V107', 'segons')}
    res['rebut_ganxo_v108_fitxer'] = str(g[0].relative_to(R0)) if g else None
    res['rebut_negres_v2'] = {k: rn.get(k) for k in ('base', 'filtres_std', 'psb', 'r_in', 'r_edge', 'model_cel_lineal_CEL', 'capes_V107')}
    for nom, r_ in (('v108', rb), ('negres_v2', rn)):
        v = (r_.get('variants') or {}).get('CEL_G_MAX_T_e30_W_H0', {})
        res.setdefault('diagnostic_per_bandes', {})[nom] = {b: {k: x.get(k) for k in ('s_mitjana', 'frac_s_lt_0_999', 'frac_tocats_du_gt_1_512', 'du41_mitjana', 'du41_p99', 'frac_D_sobre_w_gt_1', 'w_p10_p50_p90')}
                                                            for b, x in (v.get('diagnostic') or {}).items() if isinstance(x, dict)}
        res.setdefault('cel_del_genoll', {})[nom] = v.get('cel')
    print('G', json.dumps({k: res[k] for k in ('delta_genoll_41',)})[:2000], flush=True)
    desa_m('G_GANXO', res)
print('FET', round(time.time() - T0), 's')
