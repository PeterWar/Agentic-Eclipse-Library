"""cv2_comu · Mòdul comú de les COMPARACIONS de la versió 2 del mapa MSB (12-10-2026). No toca res de la v1 ni del mapa v2.

Importa msb_comu (geometria, cau, color), msb_comu_v2 (cel, extinció, punt zero de la v2) i comparacions/cmp_comu (models de p i
de corona F verificats a la font, calibratges del C2, lectors del K-Cor i del C2). Hi afegeix el que demanen els verificadors
(rev10/calcul.json, v1 i v2) per a la part de comparacions:
  - les DUES estadístiques sobre caselles aparellades (quocient de medianes i mediana dels quocients per casella);
  - bootstrap per blocs de 10° I de 30° de PA (els raigs ocupen 20–40°); totes les ± són NOMÉS estadístiques;
  - pendents robustes: la regressió de la c9 (retall 3σ MAD), Theil–Sen, la pendent RELATIVA f·med(x)/med(y) i la pendent
    log-log (Theil–Sen sobre ln x, ln y), les dues últimes sense escala (serveixen per al vermell, de punt zero incert);
  - diferència aparellada de pendents entre dos canals (mateixes caselles, mateix remostreig).

⛔ Normes: res inventat. Una casella que toqui un sol píxel de franja lunar, buit del limbe, sense dada, protuberància, fantasma
o fora del cercle inscrit queda fora sencera (regla de la v1). Importar-lo no escriu res ni llegeix cap fitxer gros."""
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

EINES = Path(__file__).resolve().parent
sys.path.insert(0, str(EINES))
sys.path.insert(0, str(EINES / 'comparacions'))
import msb_comu as mc          # noqa: E402
import msb_comu_v2 as m2       # noqa: E402
import cmp_comu as cc1         # noqa: E402

ARREL = mc.ARREL
RES2 = m2.V2 / 'comparacions'
COMPARTIR2 = m2.V2 / 'per_compartir'
PLE2 = m2.MAPA2 / 'ple'
TOCA = cc1.TOCA
BLOCS = (10, 30)                      # mides dels blocs del bootstrap (graus de PA)
NBOOT = 1000
PA_ZENIT = 33.21                      # capçalera PAZENITH del FITS v2
ANELLS_KCOR = cc1.ANELLS_KCOR         # 1,15–1,25 · 1,25–1,40 · 1,40–1,70 · 1,70–2,00 · 2,0–2,5
ANELLS_KCOR_US = 3                    # només els tres primers (fins a 1,7 R☉) es fan servir
ANELLS_C2 = cc1.ANELLS_C2
ANELLS_BANDA = [(1.15, 1.25), (1.25, 1.40), (1.40, 1.70), (1.70, 1.90)]
RADIS_FIG = cc1.RADIS_FIG
AMPLE_FIG = cc1.AMPLE_FIG
PILAR = cc1.PILAR


def sha256(ruta):
    return mc.sha256(ruta)


def rel(ruta):
    p = Path(ruta).resolve()
    try:
        return str(p.relative_to(ARREL))
    except ValueError:
        return str(p)


def json_dump(obj, ruta):
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(ruta, 'w'), indent=1, ensure_ascii=False, default=_def)


def _def(o):
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, (np.bool_,)):
        return bool(o)
    return str(o)


# ------------------------------------------------------------------------------------------------ bootstrap per blocs
def _blocs(pa_idx, bloc):
    return pa_idx // bloc


def remostreigs(pa_idx, bloc, nboot=NBOOT, llavor=7):
    """Llista d'índexs (dins del vector de caselles finites) per a cada remostreig per blocs de `bloc` graus de PA."""
    b = _blocs(pa_idx, bloc)
    ub = np.unique(b)
    pos = np.arange(len(pa_idx))
    grups = {u: pos[b == u] for u in ub}
    rng = np.random.default_rng(llavor + bloc)
    out = []
    for _ in range(nboot):
        tria = rng.choice(ub, len(ub))
        out.append(np.concatenate([grups[u] for u in tria]))
    return out


# ------------------------------------------------------------------------------------------------ estadístiques
def _theil(x, y):
    from scipy.stats import theilslopes
    t = theilslopes(y, x)
    return float(t[0]), float(t[1])


def _ls_retall(x, y, rondes=4):
    w = np.ones(len(x), bool)
    f = s = np.nan
    for _ in range(rondes):
        if w.sum() < 5:
            break
        f, s = np.polyfit(x[w], y[w], 1)
        res = y - (f * x + s)
        sd = 1.4826 * np.median(np.abs(res[w]))
        w = np.abs(res) < 3 * sd
    return float(f), float(s), w


def estadistiques(nostra, inst, pa_idx=None, nboot=NBOOT, pendents=True):
    """nostra, inst: vectors per casella d'1° (360). Només caselles amb tots dos finits i inst > 0.
    Retorna: n; quocient de medianes (QM) i mediana dels quocients (MQ) amb σ de bootstrap per blocs de 10° i de 30°;
    pendents (c9 LS amb retall, Theil–Sen, relativa, log-log) amb σ per blocs de 10° i 30°. Les ± són NOMÉS estadístiques."""
    nostra = np.asarray(nostra, float); inst = np.asarray(inst, float)
    if pa_idx is None:
        pa_idx = np.arange(len(nostra))
    ok = np.isfinite(nostra) & np.isfinite(inst) & (inst > 0)
    n = int(ok.sum())
    if n < 12:
        return dict(n=n, nota='menys de 12 caselles aparellades: no es calcula')
    y = nostra[ok]; x = inst[ok]; pa = np.asarray(pa_idx)[ok]
    out = dict(n=n, mediana_nostra=float(np.median(y)), mediana_instrument=float(np.median(x)),
               quocient_medianes=float(np.median(y) / np.median(x)), mediana_quocients=float(np.median(y / x)))
    if pendents:
        f, s, w = _ls_retall(x, y)
        ts, tsi = _theil(x, y)
        pos = (x > 0) & (y > 0)
        ll = _theil(np.log(x[pos]), np.log(y[pos]))[0] if pos.sum() >= 12 else np.nan
        out.update(pendent_c9=f, ordenada_c9=s, n_retall_c9=int(w.sum()), theil_sen=ts, ordenada_theil_sen=tsi,
                   pendent_relativa_c9=f * float(np.median(x)) / float(np.median(y)),
                   pendent_relativa_theil_sen=ts * float(np.median(x)) / float(np.median(y)),
                   pendent_loglog_theil_sen=float(ll), caselles_positives_loglog=int(pos.sum()),
                   rho=float(np.corrcoef(x[w], y[w])[0, 1]))
    for bloc in BLOCS:
        qm, mq, pf, pts, prel, pll = [], [], [], [], [], []
        for sel in remostreigs(pa, bloc, nboot):
            yy, xx = y[sel], x[sel]
            qm.append(np.median(yy) / np.median(xx)); mq.append(np.median(yy / xx))
            if pendents:
                fb, _, _ = _ls_retall(xx, yy)
                pf.append(fb); prel.append(fb * np.median(xx) / np.median(yy))
                tb = _theil(xx, yy)[0]; pts.append(tb)
                pp = (xx > 0) & (yy > 0)
                pll.append(_theil(np.log(xx[pp]), np.log(yy[pp]))[0] if pp.sum() >= 12 else np.nan)
        d = dict(quocient_medianes_err=float(np.std(qm)), mediana_quocients_err=float(np.std(mq)),
                 quocient_medianes_p16_p84=[float(np.percentile(qm, 16)), float(np.percentile(qm, 84))],
                 mediana_quocients_p16_p84=[float(np.percentile(mq, 16)), float(np.percentile(mq, 84))])
        if pendents:
            d.update(pendent_c9_err=float(np.std(pf)), theil_sen_err=float(np.std(pts)), pendent_relativa_c9_err=float(np.std(prel)),
                     pendent_loglog_err=float(np.nanstd(pll)))
        out[f'bootstrap_blocs_{bloc}'] = d
    return out


def diferencia_pendents(yA, yB, x, pa_idx=None, nboot=NBOOT):
    """Diferència aparellada de pendents sense escala (log-log Theil–Sen i relativa c9) entre dos canals A i B contra el mateix x,
    sobre les MATEIXES caselles i el MATEIX remostreig per blocs. Retorna valors i σ per blocs de 10° i 30°."""
    yA = np.asarray(yA, float); yB = np.asarray(yB, float); x = np.asarray(x, float)
    if pa_idx is None:
        pa_idx = np.arange(len(x))
    ok = np.isfinite(yA) & np.isfinite(yB) & np.isfinite(x) & (x > 0) & (yA > 0) & (yB > 0)
    if ok.sum() < 12:
        return dict(n=int(ok.sum()))
    a, b, xx, pa = yA[ok], yB[ok], x[ok], np.asarray(pa_idx)[ok]
    lx = np.log(xx)

    def calc(sel):
        llA = _theil(lx[sel], np.log(a[sel]))[0]; llB = _theil(lx[sel], np.log(b[sel]))[0]
        fA = _ls_retall(xx[sel], a[sel])[0] * np.median(xx[sel]) / np.median(a[sel])
        fB = _ls_retall(xx[sel], b[sel])[0] * np.median(xx[sel]) / np.median(b[sel])
        return llA, llB, fA, fB
    base = calc(np.arange(ok.sum()))
    out = dict(n=int(ok.sum()), loglog_A=base[0], loglog_B=base[1], dif_loglog=base[0] - base[1],
               relativa_A=base[2], relativa_B=base[3], dif_relativa=base[2] - base[3])
    for bloc in BLOCS:
        r = np.array([calc(sel) for sel in remostreigs(pa, bloc, nboot // 2)])
        out[f'bootstrap_blocs_{bloc}'] = dict(dif_loglog_err=float(np.std(r[:, 0] - r[:, 1])),
                                              dif_relativa_err=float(np.std(r[:, 2] - r[:, 3])),
                                              loglog_A_err=float(np.std(r[:, 0])), loglog_B_err=float(np.std(r[:, 1])))
    return out


def dipol(lnq, pa_deg, bloc=10, nboot=400, llavor=3):
    """ln q(PA) = c0 + a·cos PA + b·sin PA (4 rondes 3σ MAD); projecció sobre el zenit (PA_ZENIT) i la perpendicular;
    σ amb bootstrap per blocs de `bloc` caselles (la recepta de c3_lasco.py i de w2_dipol_c2_v2.py)."""
    ok = np.isfinite(lnq)
    if ok.sum() < 30:
        return dict(n=int(ok.sum()), nota='menys de 30 caselles finites: no es calcula')
    y = lnq[ok]; t = np.radians(pa_deg[ok])
    A = np.c_[np.ones(ok.sum()), np.cos(t), np.sin(t)]
    w = np.ones(ok.sum(), bool)
    for _ in range(4):
        c, *_ = np.linalg.lstsq(A[w], y[w], rcond=None); res = y - A @ c; sd = 1.4826 * np.median(np.abs(res[w])); w = np.abs(res) < 3 * sd
    tz = math.radians(PA_ZENIT)
    dz = c[1] * math.cos(tz) + c[2] * math.sin(tz); dp = -c[1] * math.sin(tz) + c[2] * math.cos(tz)
    idx = np.nonzero(ok)[0]; blocs = idx // bloc; ub = np.unique(blocs); rng = np.random.default_rng(llavor)
    pos = np.arange(ok.sum()); bz, bp = [], []
    for _ in range(nboot):
        tria = rng.choice(ub, len(ub)); sel = np.concatenate([pos[blocs == u] for u in tria]); sel = sel[w[sel]]
        cb, *_ = np.linalg.lstsq(A[sel], y[sel], rcond=None)
        bz.append(cb[1] * math.cos(tz) + cb[2] * math.sin(tz)); bp.append(-cb[1] * math.sin(tz) + cb[2] * math.cos(tz))
    return dict(cap_al_zenit=float(dz), cap_al_zenit_err=float(np.std(bz)), perpendicular=float(dp), perpendicular_err=float(np.std(bp)),
                amplitud=float(math.hypot(c[1], c[2])), direccio_PA=float(math.degrees(math.atan2(c[2], c[1])) % 360),
                n=int(w.sum()), n_finites=int(ok.sum()))


def dipol2(lnq, pa_deg):
    d = dipol(lnq, pa_deg, 10)
    if 'cap_al_zenit' in d:
        d30 = dipol(lnq, pa_deg, 30)
        d['cap_al_zenit_err_blocs30'] = d30['cap_al_zenit_err']; d['perpendicular_err_blocs30'] = d30['perpendicular_err']
    return d


# ------------------------------------------------------------------------------------------------ cel de la v2 (amb joint_c0fix)
def cel_v2_complet():
    cel = m2.coef_cel_v2()
    jf = json.load(open(m2.CELDIR / 'JOINT_C0FIX_posthoc.json'))
    cel['models']['joint_c0fix'] = dict(c0=jf['c0_fix_adu'], gu=jf['k']['0.40']['gu'], gv=jf['k']['0.40']['gv'],
                                        regla='POST HOC (mapa v2): c0 de b_new fix; gu, gv i C(r) lliures amb k = 0,40')
    return cel


# ------------------------------------------------------------------------------------------------ C2: calibratges
def mjd(data_iso):
    from astropy.time import Time
    return float(Time(data_iso).mjd)


# Colaninno & Howard 2015, Taula 2 (PMC4479163, llegida el 12-10-2026 al text de la pàgina): any, estrelles, PCF (1e-12), σm.
CH2015_TAULA2 = [(1996, 101, 6.56, 0.24), (1997, 232, 7.14, 0.04), (1998, 263, 7.37, 0.07), (1999, 339, 7.17, 0.07),
                 (2000, 453, 7.18, 0.03), (2001, 433, 7.23, 0.05), (2002, 455, 7.32, 0.05), (2003, 418, 7.26, 0.02),
                 (2004, 388, 7.32, 0.02), (2005, 412, 7.34, 0.03), (2006, 419, 7.38, 0.05), (2007, 426, 7.43, 0.04),
                 (2008, 448, 7.36, 0.05), (2009, 439, 7.28, 0.05), (2010, 460, 7.41, 0.04), (2011, 486, 7.31, 0.04),
                 (2012, 470, 7.38, 0.03), (2013, 502, 7.40, 0.05)]
