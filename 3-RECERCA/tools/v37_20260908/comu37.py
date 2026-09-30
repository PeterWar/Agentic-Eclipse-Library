"""V37 · les marques de la V36 (research/154): les capes ACHF de cadena (01/02/04/05/06) reben la mateixa condició de contorn
declarada que els operadors purs: l'entrada de les gaussianes (ln TOTAL_c, per canal) porta el forat lunar i el fora-de-suport
omplerts pel perfil azimutal mitjà continuat (el farcit de la V35), i la sortida es desa només al suport físic. Sense això la
mitjana d'un sol costat contra el forat (gradient ×2 cada 44 px) satura la tanh: |d/escala| > 25 al limbe i > 1 fins a 1,08 (01),
1,10 (02), 1,16 (06) → banda SENSE estructura de 20–70 px al voltant de la Lluna i el detall comença de cop. Fusió: la de la V36."""
import os, sys, json, time
from pathlib import Path
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026')
sys.path.insert(0, str(ROOT / 'research/tools/v36_20260908'))
import comu36
from comu36 import *
from comu36 import CAU36, HERE36, REP_CANVIS as REP_CANVIS_V36
HERE37 = Path(__file__).resolve().parent
CAU37 = HERE37 / 'cau'; OUT37 = ROOT / 'output/v37_20260908'; VIS37 = OUT37 / 'lliurables/vistes'; REB37 = OUT37 / '4-rebuts'
IAOUT37 = Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v37_20260908')
for p in (CAU37, VIS37, REB37, IAOUT37):
    p.mkdir(parents=True, exist_ok=True)


FARCIT_L_PX = 60.0; FARCIT_PUJADA_MAX = 5.0
def farcit_perfil_ln(L, m, r):
    """Condició de contorn V37 (variant B de l'A11): ln B on hi ha suport; fora, el perfil azimutal mitjà de ln B per anells d'1 px
    CONSERVANT les mitjanes dels anells parcials (1,005–1,046: les dades que toquen el forat), continuat cap endins des del primer
    anell amb dada amb el pendent local dels 10 primers anells amb ≥ 30 px, que decau exp(−d/L) (L 60 px) i puja com a màxim 5 en ln;
    més enllà de l'últim anell, l'últim valor. (La V35 extrapolava des del primer anell SENCER amb el seu pendent, 7× més suau que
    el del limbe: el farcit quedava fosc a les corones parcials i feia un rivet clar de +1,5–2 σ a la vora, A11.)"""
    ri = np.round(r).astype('int32'); n = np.bincount(ri[m]); s = np.bincount(ri[m], weights=L[m].astype('float64')); prof = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    nodes = np.arange(len(n)); full = np.flatnonzero(n >= 0.999 * 2 * np.pi * np.maximum(nodes, 1)); first_full = int(full[full > 0.9 * RS][0]); has = np.flatnonzero(n > 0); first_data = int(has[has > 0.5 * RS][0])
    p = prof.copy(); ok = np.flatnonzero((n >= 30) & (nodes >= first_data))[:10]; slope = float(np.polyfit(ok, prof[ok], 1)[0])
    d = first_data - np.arange(first_data); p[:first_data] = prof[first_data] + np.minimum(-slope * FARCIT_L_PX * (1.0 - np.exp(-d / FARCIT_L_PX)), FARCIT_PUJADA_MAX)
    bad = ~np.isfinite(p[:first_full]); idx = np.flatnonzero(bad)
    if idx.size:
        good = np.flatnonzero(~bad); p[idx] = np.interp(idx, good, p[:first_full][good])
    last = int(np.flatnonzero(np.isfinite(p))[-1]); p[last + 1:] = p[last]; bad = ~np.isfinite(p); p[bad] = np.interp(nodes[bad], nodes[~bad], p[~bad])
    return np.where(m, L, np.interp(r, nodes, p)).astype(np.float32), {'primer_anell_amb_dada_px': first_data, 'primer_anell_sencer_px': first_full, 'pendent_local_ln_per_px': slope, 'L_px': FARCIT_L_PX, 'pujada_max_ln': FARCIT_PUJADA_MAX}


def farcit_perfil_ln_A(L, m, r):
    """Farcit A (el de la V35): perfil azimutal mitjà de ln B, extrapolat cap endins des del primer anell SENCER amb el seu pendent (sense fita)."""
    ri = np.round(r).astype('int32'); n = np.bincount(ri[m]); s = np.bincount(ri[m], weights=L[m].astype('float64')); prof = np.where(n > 0, s / np.maximum(n, 1), np.nan)
    nodes = np.arange(len(n)); full = np.flatnonzero(n >= 0.999 * 2 * np.pi * np.maximum(nodes, 1)); first = int(full[full > 0.9 * RS][0]); k = np.arange(first, first + 20); slope = float(np.polyfit(k, prof[k], 1)[0])
    p = prof.copy(); p[:first] = prof[first] + slope * (np.arange(first) - first); last = int(np.flatnonzero(np.isfinite(p))[-1]); p[last + 1:] = p[last]; bad = ~np.isfinite(p); p[bad] = np.interp(nodes[bad], nodes[~bad], p[~bad])
    return np.where(m, L, np.interp(r, nodes, p)).astype(np.float32), {'primer_anell_sencer_px': first, 'pendent_ln_per_px': slope, 'variant': 'A'}


ANIVELLA_SIGMA_ANELLS = 3.0
def anivella_fi(d, m, r):
    """Anivellament per anell ABANS de la tanh: mediana de d per anells d'1 px fins a 2,5 R☉ (i de 0,02 R☉ més enllà), interpolada
    linealment en r i restada. Treu el biaix RADIAL de la mitjana d'un sol costat contra el forat mentre d encara és lineal (la tanh
    després no satura); l'estructura azimutal (desviació respecte de l'anell) es conserva. Els anells amb < 200 px no es fan servir."""
    ri = np.where(r < 2.5 * RS, np.floor(r), 2.5 * RS + np.floor((r - 2.5 * RS) / (0.02 * RS)) * 0.02 * RS).astype('int64')
    ids = ri[m]; v = d[m].astype('float64'); order = np.argsort(ids, kind='stable'); ids_s = ids[order]; v_s = v[order]; uniq, start = np.unique(ids_s, return_index=True); cuts = np.r_[start, len(ids_s)]
    nodes = []; meds = []
    for i in range(len(uniq)):
        q = v_s[cuts[i]:cuts[i + 1]]
        if len(q) >= 200:
            nodes.append(float(np.median(r[m][order][cuts[i]:cuts[i + 1]]))); meds.append(float(np.median(q)))
    nodes = np.array(nodes); meds = np.array(meds)
    from scipy.ndimage import gaussian_filter1d
    meds_s = gaussian_filter1d(meds, ANIVELLA_SIGMA_ANELLS, mode='nearest')          # la mediana per anell d'1 px és sorollosa: suavitzada 3 anells (el biaix varia en ≥ 20 px); sense això H1b puja a 4 (anells de calaix)
    corr = np.interp(r, nodes, meds_s, left=meds_s[0], right=meds_s[-1]).astype(np.float32)
    return np.where(m, d - corr, 0).astype(np.float32), {'anells': int(len(nodes)), 'sigma_suavitzat_anells': ANIVELLA_SIGMA_ANELLS, 'mediana_p1_p50_p99': [float(np.percentile(meds, q)) for q in (1, 50, 99)], 'mediana_max_abs_dins_1.1R': float(np.max(np.abs(meds_s[nodes < 1.1 * RS]))) if (nodes < 1.1 * RS).any() else None}


REP_CANVIS = {'v36': REP_CANVIS_V36, 'capes_cadena': 'entrada de l\'ACHF (ln TOTAL_c per canal) amb el forat lunar i el fora-de-suport omplerts pel farcit A (perfil azimutal mitjà, V35); pesos de la convolució = 1; sense anivellament previ (provat i refusat: H1b 3–4); la resta de la recepta (tanh, sn_smooth, centre_rings, σ extern) igual', 'purs': 'P03/P04/P05 amb el mateix farcit B (bounded); operadors v31_purs amb una màscara com la V35; P01/P02 = V36 byte a byte (base idèntica)'}
