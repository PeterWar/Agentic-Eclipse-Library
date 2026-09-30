"""a1 (V108 · negres_v2) · Avaluació de les variants del ganxo g1 (NRGF 41/42 amb genoll) emulant la pila de la V107 (modes, opacitats i màscares
llegits del PSB per la ronda 1, estat_v107; sense capes d'ajust, com a la ronda 1 i al verificador). El candidat entra a la pila com
«ràster de la V107 + (candidat − ràster de la cadena)»: dins del disc lunar i a menys de 40 px del limbe el candidat és bit a bit el de la cadena,
de manera que els 2.258 px que el r3 fa a la V107 dins del disc hi queden tal qual.
MÈTRIQUES (quocients o diferències respecte de la V107 emulada):
  · zones negres «local suau» (L i cel suavitzats 6 px) a 1,3–4,5 R☉ dins del marc, amb DUES referències de cel:
      A = cel del mateix sector de 10° a 6,5–8,5 R☉ (la de la ronda 1: n1.zones / comu_negres.cel_local, mediana mòbil de 3 sectors);
      B = cel del mateix sector de 10° a 5,0–5,6 R☉ DINS del marc (la del verificador: vn1.cel_sector, sense mediana mòbil);
    total, per bandes (1,3–2 / 2–3 / 3–4,5) i per sectors de 45°; i píxel a píxel (A);
  · el cel que es veu: mediana del compost a dalt (45–135°) i a baix (225–315°) a 5,0–5,6 R☉ (dins del marc) i a 6,5–8,5 R☉; màx/mín entre sectors;
  · energia del detall: rms de la DoG de ln L a 0–1, 1–2, 2–8, 8–32 px (pas 1, al marc) i 32–128 px (pas 2), per bandes; ordre clar/fosc;
  · contrast plomall/buit: «flamarada» p90 − p10 del detall tangencial als anells 1,5…4,5 R☉ (la de la ronda 1) i, del verificador, la mitjana
    de la part negativa (buits) i positiva (plomalls) del pas alt 4–64 px (pas 2);
  · jutge Brno (230–233): correlació del detall tangencial 2–64 px d'arc, per bandes; perles del limbe (1,02–1,15 R☉); soroll del cel;
  · ràster de la 41: píxels tocats (|Δu| > 1/512) per bandes, control nul (baix, 225–315°, 1,3–3 R☉), energia fina del ràster, i l'ARC a
    r_edge ≈ 8,47 R☉ (salt i canvi de pendent del perfil radial de Δu i de u a θ = 0, 5, 175, 180, 185, 355°, dins del marc).
Ús: a1_avalua.py <nom>=<carpeta candidata> …  (carpeta relativa a 4-RESULTATS/v108_20260926/negres_v2/candidats o absoluta)
Sortida: 4-RESULTATS/v108_20260926/negres_v2/A1_<nom>.json, pas2/L_<nom>.npy (per a les vistes)"""
import sys, json, time
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
R0 = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(R0 / '3-RECERCA/tools/v108_20260926/negres'))
from comu_negres import Pila, E, E5, W, H, SOL, RSOL, LLUNA, RLLUNA, MARC, lum, radi, BANDES, NB, mascares, logL, dog, cel_local, desa   # només lectura
OUT = R0 / '4-RESULTATS/v108_20260926/negres_v2'; CAND = OUT / 'candidats'; D2 = OUT / 'pas2'; D2.mkdir(parents=True, exist_ok=True)
STD = R0 / '4-RESULTATS/v108_20260926/cadena/control/filtres_std/filtres'
BRNO = R0 / '4-RESULTATS/v108_20260926/negres/pas1'                    # Brno_23x.npy (luminància dels composts de Brno al marc, de la ronda 1)
TAG = {41: 'P01_NRGF', 42: 'P01_NRGF_extrap'}
# ---------------- geometria pas 2 (llenç sencer) ----------------
G2 = mascares((0, 0, W, H), 2); r2, th2, ok2, marc2 = G2['r'], G2['th'], G2['ok'], G2['marc']; okm2 = ok2 & marc2
yy2, xx2 = np.mgrid[0:H:2, 0:W:2].astype(np.float32)
lluna2 = np.hypot(xx2 - LLUNA[0], yy2 - LLUNA[1]) < RLLUNA + 3; del yy2, xx2
ZONA_B = marc2 & ~lluna2 & (r2 >= 1.3) & (r2 < 4.5)


def cel_sector_B(L, valid, ra=5.0, rb=5.6, nsec=36):
    """Referència B (verificador vn1.cel_sector): mediana per sector, sense mediana mòbil, interpolació circular."""
    s = valid & (r2 >= ra) & (r2 < rb) & (L > 1e-4); sec = (th2 * nsec / 360).astype(int) % nsec
    v = np.array([np.median(L[s & (sec == i)]) if (s & (sec == i)).sum() > 200 else np.nan for i in range(nsec)])
    good = ~np.isnan(v); idx = np.arange(nsec); v = np.interp(idx, idx[good], v[good], period=nsec)
    x = th2 * nsec / 360 - 0.5; i0 = np.floor(x).astype(int) % nsec; f = (x - np.floor(x)).astype(np.float32)
    return v, ((1 - f) * v[i0] + f * v[(i0 + 1) % nsec]).astype(np.float32)


def zones(L):
    """Zones negres amb les dues referències. A: n1.zones (local suau) de la ronda 1; B: vn4 del verificador."""
    out = {}
    Ls = cv2.GaussianBlur(L, (0, 0), 3.0)
    cvA, skyA = cel_local(L, r2, th2, ok2); cvAs, skyAs = cel_local(Ls, r2, th2, ok2)
    vB, skyB = cel_sector_B(Ls, marc2 & ~lluna2)
    zA = okm2 & (r2 >= 1.3) & (r2 < 4.5); zB = ZONA_B & (L > 1e-4)
    negA = zA & (Ls < skyAs); negB = zB & (Ls < skyB)
    for nom, neg, z in (('A_cel_6.5-8.5', negA, zA), ('B_cel_5-5.6_marc', negB, zB)):
        d = dict(total=float(neg.sum() / z.sum()))
        for a, b in ((1.3, 2), (2, 3), (3, 4.5)):
            m = z & (r2 >= a) & (r2 < b); d[f'{a:g}-{b:g}'] = float(neg[m].sum() / m.sum())
        d['sectors_45'] = {f'{s}-{s + 45}': float(neg[z & (th2 >= s) & (th2 < s + 45)].mean()) for s in range(0, 360, 45)}
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
    return out, Ls


def detall_pas2(L, Lref):
    l = logL(L); dd = dog(l, 16, 64); R = {}
    for b in BANDES:
        m = okm2 & (r2 >= b[0]) & (r2 < b[1]); R.setdefault('rms_32-128', {})[NB(b)] = float(np.sqrt(np.mean(dd[m] ** 2)))
    # contrast buit/plomall del verificador (vn5): pas alt 4–64 px del llenç (σ 2–32 a pas 2)
    ok = ZONA_B | (marc2 & ~lluna2 & (r2 >= 4.5) & (r2 < 7))
    v1 = dog(l, 2, 32); v0 = dog(logL(Lref), 2, 32) if Lref is not None else None
    for a, b in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 7)):
        m = ok & (r2 >= a) & (r2 < b); x = v1[m]
        R.setdefault('buits_plomalls_4-64px', {})[f'{a:g}-{b:g}'] = dict(buits_mitj_neg=float(x[x < 0].mean()), plomalls_mitj_pos=float(x[x > 0].mean()),
                                                                          p10=float(np.percentile(x, 10)), p90=float(np.percentile(x, 90)))
    return R


# ---------------- geometria pas 1 (marc) i Brno: com n3_avalua de la ronda 1 ----------------
BOX1 = MARC; G1 = mascares(BOX1, 1); r1, th1, ok1 = G1['r'], G1['th'], G1['ok']; mg = np.zeros_like(ok1); mg[100:-100, 100:-100] = True; okk = ok1 & mg
x0, y0 = MARC[0], MARC[1]
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
    """Còpia de n3_avalua.metriques_pas1 (ronda 1)."""
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
    R['perles_1.02-1.15'] = dict(p99_5_dog_1_4=float(np.percentile(d14[m], 99.5)), rms_dog_1_4=float(np.sqrt(np.mean(d14[m] ** 2))))
    del d14
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


# ---------------- ràster de la 41: tocats, control nul, energia fina, arc a r_edge ----------------
yyF, xxF = np.ogrid[:H, :W]
RF = (np.hypot(xxF - SOL[0], yyF - SOL[1]) / RSOL).astype(np.float32); THF = ((np.degrees(np.arctan2(-(yyF - SOL[1]), xxF - SOL[0])) + 360) % 360).astype(np.float32)
DLF = (np.hypot(xxF - LLUNA[0], yyF - LLUNA[1]) - RLLUNA).astype(np.float32); del yyF, xxF
U0 = {t: np.load(STD / f'{TAG[t]}_u16.npy') for t in (41, 42)}


def raster(c41):
    """c41: ràster candidat (uint16). Mètriques del canvi Δu = candidat − cadena (la de la V107)."""
    u0 = U0[41].astype(np.float32) / 65535; u1 = c41.astype(np.float32) / 65535; dA = u1 - u0; R = {}
    fora = DLF >= 40
    R['limbe_<40px'] = dict(px_diferents=int((c41[~fora] != U0[41][~fora]).sum()), max_abs=float(np.abs(dA[~fora]).max()))
    for a, b in ((1.02, 1.3), (1.3, 2), (2, 3), (3, 4.5), (4.5, 7), (7, 9.5)):
        m = fora & (RF >= a) & (RF < b)
        R.setdefault('per_bandes', {})[f'{a:g}-{b:g}'] = dict(frac_tocats_1_512=float((np.abs(dA[m]) > 1 / 512).mean()), mitj_dA=float(dA[m].mean()), mitj_abs_dA=float(np.abs(dA[m]).mean()),
                                                               p99_abs=float(np.percentile(np.abs(dA[m]), 99)), sd_u0=float(u0[m].std()), sd_u1=float(u1[m].std()))
    m = fora & (RF >= 1.3) & (RF < 3) & (THF >= 225) & (THF < 315)
    R['control_nul_baix_225-315_1.3-3'] = dict(mitj_abs_dA=float(np.abs(dA[m]).mean()), mitj_dA=float(dA[m].mean()), frac_tocats_1_512=float((np.abs(dA[m]) > 1 / 512).mean()))
    sl = (slice(MARC[1], MARC[3]), slice(MARC[0], MARC[2])); rr = RF[sl]; mm = fora[sl] & (DLF[sl] >= 60)
    for nom, (s1, s2) in {'1-2': (0.7, 2), '2-8': (2, 8), '8-32': (8, 32)}.items():
        D0 = dog(np.ascontiguousarray(u0[sl]), s1, s2); D1 = dog(np.ascontiguousarray(u1[sl]), s1, s2)
        for a, b in ((1.3, 2), (2, 3), (3, 4.5), (4.5, 7)):
            k = mm & (rr >= a) & (rr < b)
            R.setdefault('energia_raster_41', {}).setdefault(nom, {})[f'{a:g}-{b:g}'] = float(np.sqrt(np.mean(D1[k] ** 2)) / np.sqrt(np.mean(D0[k] ** 2)))
        del D0, D1
    # arc a r_edge: perfil radial (mitjana tangencial ±2°) de Δu i de u, a 7,9–9,0 R☉, pas 0,01 R☉
    arc = {}
    rs = np.arange(7.9, 9.0, 0.01)
    for thc in (0, 5, 175, 180, 185, 355):
        ths = np.radians(thc + np.linspace(-2, 2, 81)); X = (SOL[0] + np.outer(rs * RSOL, np.cos(ths))).astype(np.float32); Y = (SOL[1] - np.outer(rs * RSOL, np.sin(ths))).astype(np.float32)
        pd = cv2.remap(dA, X, Y, cv2.INTER_LINEAR).mean(1); p0 = cv2.remap(u0, X, Y, cv2.INTER_LINEAR).mean(1); p1 = cv2.remap(u1, X, Y, cv2.INTER_LINEAR).mean(1)
        k = (rs > 8.3) & (rs < 8.65)
        def kink(p):   # canvi de pendent: diferència de pendents (ajust lineal a 8,30–8,47 i a 8,48–8,65), per 0,1 R☉
            a1 = (rs >= 8.30) & (rs < 8.47); a2 = (rs >= 8.48) & (rs < 8.65)
            return float((np.polyfit(rs[a2], p[a2], 1)[0] - np.polyfit(rs[a1], p[a1], 1)[0]) * 0.1)
        arc[str(thc)] = dict(salt_max_dA_0_01R=float(np.abs(np.diff(pd[k])).max()), canvi_pendent_dA=kink(pd), canvi_pendent_u_V107=kink(p0), canvi_pendent_u_cand=kink(p1),
                             dA_8_0_8_4_8_6_8_8=[float(pd[np.argmin(np.abs(rs - x))]) for x in (8.0, 8.4, 8.6, 8.8)])
    R['arc_r_edge'] = arc
    return R


def combinat(cdir, lid):
    """Ràster per a la pila: el de l'estat V107 + (candidat − cadena), en uint16 (dins de 40 px del limbe, bit a bit el de la V107)."""
    c = np.load(cdir / f'{TAG[lid]}_u16.npy'); s = E._llegeix(lid, 'G', (0, 0, W, H))
    return c, np.clip(s.astype(np.int32) + c.astype(np.int32) - U0[lid].astype(np.int32), 0, 65535).astype(np.uint16)


if __name__ == '__main__':
    T = time.time(); P2 = Pila((0, 0, W, H), 2); P1 = Pila(BOX1, 1); print('piles', round(time.time() - T), 's', flush=True)
    L2ref = P2.compon({}); np.save(D2 / 'L_V107.npy', L2ref); L1ref = P1.compon({})
    res = dict(zones=zones(L2ref)[0], pas2=detall_pas2(L2ref, None), pas1=metriques_pas1(L1ref)); desa(OUT / 'A1_V107.json', res)
    print('V107', json.dumps({k: res['zones'][k]['total'] for k in ('A_cel_6.5-8.5', 'B_cel_5-5.6_marc')}), flush=True)
    for arg in sys.argv[1:]:
        t0 = time.time(); nom, sp = arg.split('=', 1); c = Path(sp); c = c if c.is_absolute() else CAND / c
        c41, f41 = combinat(c, 41); _, f42 = combinat(c, 42)
        esp = {41: {'F': 'mem', '_F': None}, 42: {'F': 'mem', '_F': None}}
        esp[41]['_F'] = f41[::2, ::2]; esp[42]['_F'] = f42[::2, ::2]; L2 = P2.compon(esp); np.save(D2 / f'L_{nom}.npy', L2)
        esp[41]['_F'] = f41[BOX1[1]:BOX1[3], BOX1[0]:BOX1[2]]; esp[42]['_F'] = f42[BOX1[1]:BOX1[3], BOX1[0]:BOX1[2]]; del f41, f42
        L1 = P1.compon(esp)
        r_ = dict(candidat=str(c), zones=zones(L2)[0], pas2=detall_pas2(L2, L2ref), pas1=metriques_pas1(L1, L1ref), raster_41=raster(c41))
        # canvi del compost per bandes (ln L_cand/L_V107): mediana, p1, p99; i al control nul (baix, 1,3–3 R☉)
        dl = np.log(np.maximum(L2, 1e-3)) - np.log(np.maximum(L2ref, 1e-3)); ch = {}
        for a, b in ((1.02, 1.3), (1.3, 2), (2, 3), (3, 4.5), (4.5, 7), (7, 9.5)):
            m = okm2 & (r2 >= a) & (r2 < b); ch[f'{a:g}-{b:g}'] = [float(q) for q in np.percentile(dl[m], [1, 50, 99])] + [float((np.abs(dl[m]) > 0.005).mean())]
        m = okm2 & (r2 >= 1.3) & (r2 < 3) & (th2 >= 225) & (th2 < 315); ch['control_nul_baix_225-315_1.3-3'] = [float(q) for q in np.percentile(dl[m], [1, 50, 99])] + [float((np.abs(dl[m]) > 0.005).mean())]
        r_['canvi_compost_ln_p1_p50_p99_frac_gt_0_5pc'] = ch
        desa(OUT / f'A1_{nom}.json', r_); del L1, L2, c41
        z = r_['zones']; print(nom, round(time.time() - t0), 's · negres A', round(z['A_cel_6.5-8.5']['total'], 4), 'B', round(z['B_cel_5-5.6_marc']['total'], 4),
                                '· cel A/B màx/mín', round(z['cel_A_max_sobre_min'], 3), round(z['cel_B_max_sobre_min'], 3), flush=True)
    print('FET', round(time.time() - T), 's')
