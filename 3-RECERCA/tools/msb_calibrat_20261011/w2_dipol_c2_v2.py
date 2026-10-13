"""w2 · Dipol del quocient nostra/C2 per a cada cel i cada k (v2, 12-10-2026). Es corre DESPRÉS de la tria del cel (w1, 23:46:47).

Caselles i regles de la v1 (c1_caselles_nostra.py + c3_lasco.py): anells del C2 2,4–2,6 … 4,5–5,5 R☉, caselles d'1° de PA, mediana
dels píxels vàlids de cada casella; una casella que toqui un sol píxel de NO_DATA, LIMB_GAP, MOON_BAND, PROMINENCE, SONY_GHOST o
OUTSIDE_INSCRIBED queda fora (màscara «usable» de lasco/c2_caselles.npz, que també treu el pilar del C2, 288–360°).
C2: la mitjana per casella dels dos fotogrames (18:24:31 i 18:36:15) amb el calibratge SolarSoft (el calibratge és una constant
i no canvia el dipol).
Nostra: MSB = FAC_G·(G_cam − S)·10^(0,4·k·(X − X_ZP)) per a S ∈ {a, b_old, b_new, joint (predeclarat), joint_c0fix (post hoc),
c (contaminat, registre)} i k ∈ {0; 0,40; 0,57; 0,72}.
Dipol: ln q(PA) = c0 + a·cos PA + b·sin PA per anell, 4 rondes de retall a 3σ (MAD); projecció sobre el zenit (PA 33,21°) i la
perpendicular; amplitud i direcció; errors amb bootstrap de 400 per blocs de 10 caselles (com la v1) i de 30 caselles.
Controls: (1) el cel b_old amb k = 0,40 i la referència de la v1 (X☉ 6,053) reprodueix les caselles de caselles_nostra.npz i el
dipol de LASCO.json; (2) la predicció ln E per a cada k.
Escriu v2/mapa/dipol_c2/DIPOL_C2_v2.json."""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / 'comparacions'))
import msb_comu as mc          # noqa: E402
import msb_comu_v2 as m2       # noqa: E402
import cmp_comu as cc          # noqa: E402

T0 = time.time()
OUT = m2.MAPA2 / 'dipol_c2'; OUT.mkdir(parents=True, exist_ok=True)
CEL2 = m2.coef_cel_v2()
JF = json.load(open(m2.CELDIR / 'JOINT_C0FIX_posthoc.json'))
CEL2['models']['joint_c0fix'] = dict(c0=JF['c0_fix_adu'], gu=JF['k']['0.40']['gu'], gv=JF['k']['0.40']['gv'],
                                     regla='POST HOC: c0 de b_new fix; gu, gv i C(r) lliures amb k = 0,40')
C2N = np.load(cc.RES / 'lasco' / 'c2_caselles.npz')
NOS1 = np.load(cc.RES / 'caselles_nostra.npz')
AN = [tuple(a) for a in C2N['anells']]
usable = C2N['usable']
C2 = C2N['c2_SSW_c2_calfactor']
C2CH = C2N['c2_Colaninno_Howard_2015_eq8']
PA_ZENIT = 33.21
pa_c = np.arange(0.5, 360, 1.0)

# ---------------------------------------------------------------- píxels dels anells del C2
cau = mc.obre_cau(); MA = mc.MassaAire(); g = mc.geo_llenc()
flg1 = np.load(mc.MAPA / 'ple' / 'flags_ple.npy', mmap_mode='r')    # bits de zona (no depenen del cel): iguals a la v2
RM = 5.5
y0 = int(mc.SOL_XY[1] - RM * 1.01 * mc.RSOL_PX); y1 = int(mc.SOL_XY[1] + RM * 1.01 * mc.RSOL_PX) + 1
x0 = int(mc.SOL_XY[0] - RM * 1.01 * mc.RSOL_PX); x1 = int(mc.SOL_XY[0] + RM * 1.01 * mc.RSOL_PX) + 1
acc = {k: [] for k in ('key', 'G', 'x', 'y', 'X')}
for ya in range(y0, y1, 512):
    yb = min(ya + 512, y1)
    yy = np.arange(ya, yb, dtype=np.float64)[:, None] * np.ones((1, x1 - x0))
    xx = np.ones((yb - ya, 1)) * np.arange(x0, x1, dtype=np.float64)[None, :]
    r, pa = g.polar(xx, yy)
    key, nb = cc.clau_caselles(r, pa, AN)
    sel = key >= 0
    if not sel.any():
        continue
    F = np.asarray(cau['fusion_total_v42'][ya:yb, x0:x1], np.float32)
    sup = np.asarray(cau['support_v42'][ya:yb, x0:x1])
    dada = sup & np.all(np.isfinite(F), 2) & np.all(F > 0, 2)
    f = np.asarray(flg1[ya:yb, x0:x1])
    toca = (f & cc.TOCA) > 0
    ok = sel & dada & ~toca
    G = mc.verd_camera(F)
    X = mc.kasten_young(MA.altura_bloc(ya, yb, x0, x1))
    for k_, val in (('key', key), ('G', G), ('x', xx), ('y', yy), ('X', X)):
        acc[k_].append(val[ok])
    print(f'files {ya}-{yb} ({time.time() - T0:.0f} s)', flush=True)
P = {k: np.concatenate(v) for k, v in acc.items()}
del acc
NG = len(AN) * 360
print(f'{P["key"].size} píxels ({time.time() - T0:.0f} s)', flush=True)


def caselles(val):
    _, q = cc.percentils_grup(P['key'], val, NG)
    return q[50].reshape(len(AN), 360)


def dipol(lnq, pa, bloc=10, nboot=400, llavor=3):
    ok = np.isfinite(lnq)
    if ok.sum() < 30:
        return dict(n=int(ok.sum()), nota='massa poques caselles finites (< 30): no es pot calcular')
    y = lnq[ok]; t = np.radians(pa[ok])
    A = np.c_[np.ones(ok.sum()), np.cos(t), np.sin(t)]
    w = np.ones(ok.sum(), bool)
    for _ in range(4):
        c, *_ = np.linalg.lstsq(A[w], y[w], rcond=None); res = y - A @ c; sd = 1.4826 * np.median(np.abs(res[w])); w = np.abs(res) < 3 * sd
    tz = math.radians(PA_ZENIT)
    dz = c[1] * math.cos(tz) + c[2] * math.sin(tz); dperp = -c[1] * math.sin(tz) + c[2] * math.cos(tz)
    idx = np.nonzero(ok)[0]; blocs = idx // bloc; ub = np.unique(blocs); rng = np.random.default_rng(llavor); bz, bp, ba = [], [], []
    pos = np.arange(ok.sum())
    for _ in range(nboot):
        tria = rng.choice(ub, len(ub)); sel = np.concatenate([pos[blocs == b] for b in tria]); sel = sel[w[sel]]
        cb, *_ = np.linalg.lstsq(A[sel], y[sel], rcond=None)
        bz.append(cb[1] * math.cos(tz) + cb[2] * math.sin(tz)); bp.append(-cb[1] * math.sin(tz) + cb[2] * math.cos(tz)); ba.append(math.hypot(cb[1], cb[2]))
    return dict(cap_al_zenit=float(dz), cap_al_zenit_err=float(np.std(bz)), perpendicular=float(dperp), perpendicular_err=float(np.std(bp)),
                amplitud=float(math.hypot(c[1], c[2])), amplitud_err=float(np.std(ba)),
                direccio_PA=float(math.degrees(math.atan2(c[2], c[1])) % 360), c0=float(c[0]), n=int(w.sum()), n_finites=int(ok.sum()))


def dipol2(lnq, pa):
    d10 = dipol(lnq, pa, 10)
    if 'cap_al_zenit' in d10:
        d30 = dipol(lnq, pa, 30)
        d10['cap_al_zenit_err_blocs30'] = d30['cap_al_zenit_err']; d10['amplitud_err_blocs30'] = d30['amplitud_err']
        d10['perpendicular_err_blocs30'] = d30['perpendicular_err']
    return d10


# ---------------------------------------------------------------- control 1: rèplica de la v1 (b_old, k 0,40, X☉ 6,053)
X_SOL_V1 = MA.X_sol
Sb_old = m2.cel_model_v2(P['x'], P['y'], 'b_old', CEL2)
v1rep = caselles(mc.FAC_G * (P['G'] - Sb_old) * 10 ** (0.4 * 0.40 * (P['X'] - X_SOL_V1)))
dif = np.nanmax(np.abs(v1rep[usable] / NOS1['c2_msb'][usable] - 1))
L1 = json.load(open(cc.RES / 'lasco' / 'LASCO.json'))
rep = {'guio': 'w2_dipol_c2_v2.py', 'data_execucio': time.strftime('%Y-%m-%dT%H:%M:%S'),
       'tria_del_cel_feta_a': CEL2.get('motiu'), 'cel_adoptat': CEL2['adoptat'],
       'control_replica_v1': dict(max_dif_rel_caselles=float(dif), passa=bool(dif < 1e-5), dipol_v1={}, dipol_replica={})}
for i, a in enumerate(AN):
    kk = f'{a[0]}-{a[1]}'
    with np.errstate(invalid='ignore', divide='ignore'):
        d = dipol(np.log(np.where(usable[i], v1rep[i], np.nan) / C2[i]), pa_c)
    rep['control_replica_v1']['dipol_replica'][kk] = round(d['cap_al_zenit'], 5)
    rep['control_replica_v1']['dipol_v1'][kk] = round(L1['dipol'][kk]['amb_extincio']['cap_al_zenit'], 5)
print('control', rep['control_replica_v1'], flush=True)

# ---------------------------------------------------------------- tots els cels × k
CELS = ('a', 'b_old', 'b_new', 'joint', 'joint_c0fix', 'c')
taula = {}
med_q = {}
for cel in CELS:
    S = m2.cel_model_v2(P['x'], P['y'], cel, CEL2)
    net = mc.FAC_G * (P['G'] - S)
    taula[cel] = {}
    for k in m2.K_DIPOL:
        ours = caselles(net * m2.factor_extincio(P['X'], k))
        taula[cel][f'{k:.2f}'] = {}
        for i, a in enumerate(AN):
            kk = f'{a[0]}-{a[1]}'
            with np.errstate(invalid='ignore', divide='ignore'):
                y = np.where(usable[i] & (ours[i] > 0), ours[i], np.nan)
                d = dipol2(np.log(y / C2[i]), pa_c)
            d['caselles_negatives_o_zero'] = int((usable[i] & ~(ours[i] > 0)).sum())
            taula[cel][f'{k:.2f}'][kk] = d
        if cel == CEL2['adoptat'] and abs(k - 0.40) < 1e-9:
            for i, a in enumerate(AN):
                kk = f'{a[0]}-{a[1]}'
                med_q[kk] = dict(SSW=cc.quocients(np.where(usable[i], ours[i], np.nan), C2[i]),
                                 CH2015=cc.quocients(np.where(usable[i], ours[i], np.nan), C2CH[i]))
    print(cel, {kz: {kk: (round(d.get('cap_al_zenit', np.nan), 3), round(d.get('cap_al_zenit_err', np.nan), 3))
                     for kk, d in v.items()} for kz, v in taula[cel].items()}, f'({time.time() - T0:.0f} s)', flush=True)
# predicció: dipol de ln E per a cada k (la mediana de E per casella)
pred = {}
for k in m2.K_DIPOL[1:]:
    Ek = caselles(m2.factor_extincio(P['X'], k))
    pred[f'{k:.2f}'] = {f'{a[0]}-{a[1]}': dipol(np.log(np.where(usable[i], Ek[i], np.nan)), pa_c) for i, a in enumerate(AN)}
rep.update(dict(PA_zenit=PA_ZENIT, anells=AN, k=list(m2.K_DIPOL), cels=list(CELS),
                definicio='dipol de ln(nostra/C2): positiu cap al zenit = la nostra és més brillant cap al zenit que el C2',
                dipol=taula, prediccio_lnE=pred, quocients_cel_adoptat_k040=med_q,
                models_cel={c: CEL2['models'][c] for c in CELS}, temps_s=time.time() - T0))
json.dump(rep, open(OUT / 'DIPOL_C2_v2.json', 'w'), indent=1, ensure_ascii=False, default=float)
print(f'fet en {time.time() - T0:.0f} s')
