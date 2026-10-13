"""w1 · Cel de la v2 del mapa MSB (11/12-10-2026). Escriu v2/mapa/cel/CEL_v2.json i v2/mapa/cel/PROVES_W1.json.

Segueix v2/mapa/PREDECLARACIO_CEL_v2.md (escrita abans de córrer res):
  - refà a, b_old i c de la v1 amb les mateixes màscares (control: han de sortir iguals que mapa/CEL.json);
  - b_new: constant + pla ajustats a G a r ≥ 8 R☉ (tot el camp amb dada), 4 rondes 3σ MAD;
  - joint: c0 + pla + C(r)·10^(−0,4·0,40·(X − X_ZP)), C(r) per anells de 0,1 R☉ des de 3,546 R☉, 4 rondes 3σ MAD;
  - jackknife per 12 sectors de 30° de PA, meitats u < 0 i u > 0, diagnòstic quadràtic a r ≥ 8 (només registre);
  - biaix K+F (van de Hulst 1950 K_max + F; variants K_min i F de Koutchmy & Lamy 1985) passat pel mateix estimador de cada cel;
  - la regla de tria D1–D4 i les alternatives de σ_cel.
NO calcula cap quocient amb el C2 (això és w2, després de triar)."""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from scipy import ndimage as nd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu as mc          # noqa: E402
import msb_comu_v2 as m2       # noqa: E402

T0 = time.time()
OUT = m2.CELDIR; OUT.mkdir(parents=True, exist_ok=True)
rep = {'guio': 'w1_cel_v2.py', 'data_execucio': time.strftime('%Y-%m-%dT%H:%M:%S'),
       'predeclaracio': 'v2/mapa/PREDECLARACIO_CEL_v2.md (2026-10-11 23:45)'}
Z = mc.zones(); RINS = float(Z['R_inscrit_Rsol'])
CEL1 = json.load(open(mc.MAPA / 'CEL.json'))
cau = mc.obre_cau()
s = 4
f = np.asarray(cau['fusion_total_v42'][::s, ::s], np.float64)
sp = np.asarray(cau['support_v42'][::s, ::s])
yy, xx = np.mgrid[0:mc.H:s, 0:mc.W:s].astype(np.float64)
g = mc.geo_llenc()
r, pa = g.polar(xx, yy)
u, v = m2.uv(xx, yy)
dada = sp & np.all(np.isfinite(f), 2) & np.all(f > 0, 2)
G = np.where(dada, mc.verd_camera(f), np.nan)
del f
print(f'submostreig {G.shape} ({time.time() - T0:.0f} s)', flush=True)

# ---------------------------------------------------------------- màscares (còpia literal de p1_cel_i_massa_aire.py)
ghost = np.hypot(xx - mc.GHOST_XY[0], yy - mc.GHOST_XY[1]) < mc.GHOST_R_PX
Gf = np.where(dada, G, 0.0)
medf = nd.median_filter(Gf, size=9)
res = np.where(dada, G - medf, np.nan)
zona_soroll = dada & (r > 3.0) & ~ghost
sd = 1.4826 * np.nanmedian(np.abs(res[zona_soroll] - np.nanmedian(res[zona_soroll])))
est = dada & (r > 2.0) & (res > 6 * sd)
est = nd.binary_dilation(est, iterations=2)
prom = np.zeros_like(dada)
for p0, dpa in mc.PROM_SECTORS:
    prom |= (np.abs((pa - p0 + 180) % 360 - 180) <= dpa) & (r < mc.PROM_RMAX)
valid = dada & ~ghost & ~est & ~prom & (np.hypot(xx - mc.LLUNA_XY[0], yy - mc.LLUNA_XY[1]) >= mc.R_BANDA_PX)
del Gf, medf, res
rep['mascares'] = dict(submostreig=s, pixels_valids=int(valid.sum()), pixels_estrella=int(est.sum()))

# ---------------------------------------------------------------- massa d'aire al submostreig i factor atmosfèric A = 1/E
MA = mc.MassaAire()
hgt = MA.sp.ev(yy.ravel(), xx.ravel()).reshape(yy.shape)
X = mc.kasten_young(hgt)
A040 = 1.0 / m2.factor_extincio(X, 0.40)        # corona observada = C_veritable · A
print(f'massa d\'aire ({time.time() - T0:.0f} s)', flush=True)


def ajust_retall(Am, y, rondes=4, nsig=3.0):
    """Mínims quadrats amb 4 rondes de retall a 3σ (MAD), com el model (c) de la v1. Retorna (coef, màscara final, σ_MAD)."""
    w = np.ones(len(y), bool)
    sdx = np.nan
    for _ in range(rondes):
        c, *_ = np.linalg.lstsq(Am[w], y[w], rcond=None)
        rr_ = y - Am @ c
        md = np.median(rr_[w]); sdx = 1.4826 * np.median(np.abs(rr_[w] - md))
        w = np.abs(rr_ - md) < nsig * sdx
    c, *_ = np.linalg.lstsq(Am[w], y[w], rcond=None)
    return c, w, float(sdx)


def jackknife(fun, sel, sector, n=12):
    """Jackknife traient d'un en un els sectors de 30° que tenen píxels a la selecció."""
    presents = [j for j in range(n) if np.any(sel & (sector == j))]
    th = np.array([fun(sel & (sector != j)) for j in presents])
    m = len(presents)
    mu = th.mean(axis=0)
    sig = np.sqrt((m - 1) / m * ((th - mu) ** 2).sum(axis=0))
    return sig, presents, th


SECTOR = (np.floor(pa / 30.0).astype(np.int64)) % 12
K76 = 959.0 / mc.RSOL_ARCSEC

# ---------------------------------------------------------------- (a), (b_old), (c): rèplica de la v1
ma_a = valid & (r > 7.2 * K76)
c0_a = float(np.median(G[ma_a]))
r76 = r / K76
edges76 = np.arange(1.0, 13.0, 0.02)


def recepta_b_old(Gx):
    kb = np.digitize(r76, edges76) - 1
    okb = valid & (kb >= 0) & (kb < len(edges76) - 1)
    med = np.asarray(nd.median(Gx[okb], labels=kb[okb], index=np.arange(len(edges76) - 1)), float)
    cnt = np.bincount(kb[okb], minlength=len(edges76) - 1)[:len(edges76) - 1]
    med[cnt < 30] = np.nan
    rc = 0.5 * (edges76[1:] + edges76[:-1]); okm = np.isfinite(med)
    base = np.interp(r76, rc[okm], med[okm])
    fb = valid & (r76 > 3.5)
    Ab = np.c_[np.ones(fb.sum()), u[fb], v[fb]]
    cb, *_ = np.linalg.lstsq(Ab, (Gx - base)[fb], rcond=None)
    return cb, fb


cb_old, fb_old = recepta_b_old(G)
fc = valid & (r > 4.0) & (r < RINS)
Ac = np.c_[np.ones(fc.sum()), u[fc], v[fc], u[fc] ** 2, u[fc] * v[fc], v[fc] ** 2]
cc_, wc, sdc = ajust_retall(Ac, G[fc])
control = dict(a_c0=(c0_a, CEL1['a']['c0']), b_gu=(float(cb_old[1]), CEL1['b']['gu']), b_gv=(float(cb_old[2]), CEL1['b']['gv']),
               c_coef_max_dif=float(np.max(np.abs(np.array(cc_) - np.array(CEL1['c']['coef'])))))
control['passa'] = bool(abs(c0_a - CEL1['a']['c0']) < 1e-9 and abs(cb_old[1] - CEL1['b']['gu']) < 1e-9
                        and abs(cb_old[2] - CEL1['b']['gv']) < 1e-9 and control['c_coef_max_dif'] < 1e-6)
rep['control_replica_v1'] = control
print('control v1', control, flush=True)

# ---------------------------------------------------------------- (b_new): pla a r ≥ 8 R☉
R8 = 8.0
sel8 = valid & (r >= R8)


def fit_pla(sel):
    Am = np.c_[np.ones(sel.sum()), u[sel], v[sel]]
    c, w, sdx = ajust_retall(Am, G[sel])
    return c, w, sdx


cn, wn, sdn = fit_pla(sel8)
sel8_final = np.zeros_like(sel8); sel8_final[np.nonzero(sel8)] = wn
c_ols, *_ = np.linalg.lstsq(np.c_[np.ones(sel8.sum()), u[sel8], v[sel8]], G[sel8], rcond=None)
jk_n, pres_n, th_n = jackknife(lambda m: fit_pla(m)[0], sel8, SECTOR)
cL = fit_pla(sel8 & (u < 0))[0]; cR = fit_pla(sel8 & (u > 0))[0]
Aq = np.c_[np.ones(sel8.sum()), u[sel8], v[sel8], u[sel8] ** 2, u[sel8] * v[sel8], v[sel8] ** 2]
cq, wq, sdq = ajust_retall(Aq, G[sel8])
# estructura del residu en caixes d'1 R☉ (forma del cel que el pla no recull)
resn = np.where(sel8_final, G - (cn[0] + cn[1] * u + cn[2] * v), np.nan)
bx = 110   # 110 px del submostreig = 440 px del llenç ≈ 1 R☉
nby, nbx = resn.shape[0] // bx, resn.shape[1] // bx
caixes = []
for iy in range(nby):
    for ix in range(nbx):
        blk = resn[iy * bx:(iy + 1) * bx, ix * bx:(ix + 1) * bx]
        if np.isfinite(blk).sum() > 0.5 * bx * bx:
            caixes.append(float(np.nanmedian(blk)))
caixes = np.array(caixes)
rep['b_new'] = dict(regla='c0 + gu·u + gv·v ajustat a G_cam a r ≥ 8 R☉ (tot el camp amb dada), 4 rondes 3σ MAD',
                    c0=float(cn[0]), gu=float(cn[1]), gv=float(cn[2]), n=int(sel8.sum()), n_final=int(wn.sum()), sigma_mad_adu=sdn,
                    r_max_Rsol=float(r[sel8].max()), ols_sense_retall=[float(x) for x in c_ols],
                    jackknife=dict(sigma_c0=float(jk_n[0]), sigma_gu=float(jk_n[1]), sigma_gv=float(jk_n[2]), sectors=pres_n,
                                   valors=th_n.tolist()),
                    meitats=dict(u_negatiu=[float(x) for x in cL], u_positiu=[float(x) for x in cR], dif_gv=float(cL[2] - cR[2]),
                                 dif_gu=float(cL[1] - cR[1]), dif_c0=float(cL[0] - cR[0])),
                    quadratic_registre=dict(coef=[float(x) for x in cq], nota='c0, u, v, u², uv, v²: només diagnòstic de curvatura'),
                    residu_caixes_1Rsol=dict(n=int(caixes.size), rms_adu=float(np.sqrt(np.mean(caixes ** 2))) if caixes.size else None,
                                             max_abs_adu=float(np.max(np.abs(caixes))) if caixes.size else None,
                                             p95_abs_adu=float(np.percentile(np.abs(caixes), 95)) if caixes.size else None))
print('b_new', {k: rep['b_new'][k] for k in ('c0', 'gu', 'gv', 'n', 'jackknife', 'meitats')}, f'({time.time() - T0:.0f} s)', flush=True)

# ---------------------------------------------------------------- (joint): cel + C(r)·A, k = 0,40
RJ0 = 3.5 * K76
dj = valid & (r > RJ0)
ej = np.arange(RJ0, float(r[dj].max()) + 0.1, 0.1)
ring_all = np.digitize(r, ej) - 1


def fit_joint(sel, y=None, A=A040, rondes=4, nsig=3.0, w_fix=None):
    """Equacions normals per a c0, gu, gv i C_j (columna A·1_j). Anells amb < 200 píxels, fora. Retorna dict."""
    yv = (G if y is None else y)[sel]; uu = u[sel]; vv = v[sel]; Av = A[sel]; jv = ring_all[sel]
    nr = len(ej) - 1
    cnt = np.bincount(jv, minlength=nr)[:nr]
    okr = cnt >= 200
    use = okr[jv]
    w = use.copy() if w_fix is None else (w_fix & use)
    nit = rondes if w_fix is None else 0
    for it in range(nit + 1):
        P = 3 + nr
        N = np.zeros((P, P)); b = np.zeros(P)
        B = [np.ones(w.sum()), uu[w], vv[w]]
        for i in range(3):
            for k in range(3):
                N[i, k] = np.dot(B[i], B[k])
            b[i] = np.dot(B[i], yv[w])
            N[i, 3:] = np.bincount(jv[w], weights=B[i] * Av[w], minlength=nr)[:nr]
            N[3:, i] = N[i, 3:]
        N[np.arange(3, P), np.arange(3, P)] = np.bincount(jv[w], weights=Av[w] ** 2, minlength=nr)[:nr]
        b[3:] = np.bincount(jv[w], weights=Av[w] * yv[w], minlength=nr)[:nr]
        act = np.r_[np.ones(3, bool), okr & (np.diag(N)[3:] > 0)]
        beta = np.zeros(P)
        beta[act] = np.linalg.solve(N[np.ix_(act, act)], b[act])
        model = beta[0] + beta[1] * uu + beta[2] * vv + beta[3 + np.clip(jv, 0, nr - 1)] * Av
        rr_ = yv - model
        if it < nit:
            md = np.median(rr_[w]); sdx = 1.4826 * np.median(np.abs(rr_[w] - md))
            w = use & (np.abs(rr_ - md) < nsig * sdx)
    Ninv = np.linalg.inv(N[np.ix_(act, act)])
    cor = Ninv[0, 2] / math.sqrt(Ninv[0, 0] * Ninv[2, 2])
    return dict(beta=beta, w=w, act=act, cond=float(np.linalg.cond(N[np.ix_(act, act)])), corr_c0_gv_formal=float(cor),
                rms=float(1.4826 * np.median(np.abs(rr_[w] - np.median(rr_[w])))), n=int(w.sum()))


J = fit_joint(dj)
jk_j, pres_j, th_j = jackknife(lambda m: fit_joint(m)['beta'][:3], dj, SECTOR)
cjL = fit_joint(dj & (u < 0))['beta'][:3]; cjR = fit_joint(dj & (u > 0))['beta'][:3]
rc_j = 0.5 * (ej[1:] + ej[:-1])
rep['joint'] = dict(regla='G = c0 + gu·u + gv·v + C(r)·10^(−0,4·0,40·(X − X_ZP)), C per anells de 0,1 R☉ des de 3,546 R☉; 4 rondes 3σ MAD',
                    c0=float(J['beta'][0]), gu=float(J['beta'][1]), gv=float(J['beta'][2]), n_final=J['n'], rms_adu=J['rms'],
                    nombre_condicio=J['cond'], correlacio_formal_c0_gv=J['corr_c0_gv_formal'],
                    jackknife=dict(sigma_c0=float(jk_j[0]), sigma_gu=float(jk_j[1]), sigma_gv=float(jk_j[2]), sectors=pres_j,
                                   valors=th_j.tolist(), correlacio_c0_gv=float(np.corrcoef(th_j[:, 0], th_j[:, 2])[0, 1])),
                    meitats=dict(u_negatiu=[float(x) for x in cjL], u_positiu=[float(x) for x in cjR]),
                    C_r=dict(r_mig=rc_j.tolist(), C_adu=[float(x) if a else None for x, a in zip(J['beta'][3:], J['act'][3:])]))
print('joint', {k: rep['joint'][k] for k in ('c0', 'gu', 'gv', 'nombre_condicio', 'correlacio_formal_c0_gv', 'jackknife')},
      f'({time.time() - T0:.0f} s)', flush=True)

# ---------------------------------------------------------------- biaix K+F de cada estimador (model, k = 0,40)
sys.path.insert(0, str(Path(__file__).resolve().parent / 'comparacions'))
import cmp_comu as ccm   # noqa: E402
kl = ccm.kl1985_coefs()
F_MODELS = {'vdH1950': m2.f_vdh(r),
            'KL1985_equ': 10 ** np.polyval(np.array(kl['coef_equ']), np.log10(np.maximum(r, 1.0))),
            'KL1985_pol': 10 ** np.polyval(np.array(kl['coef_pol']), np.log10(np.maximum(r, 1.0)))}
K_MODELS = {'Kmax': m2.k_max_vdh(r), 'Kmin': m2.k_min_vdh(r)}
VARIANTS = {'central': ('Kmax', 'vdH1950'), 'Kmin_vdH': ('Kmin', 'vdH1950'), 'Kmax_KLequ': ('Kmax', 'KL1985_equ'),
            'Kmin_KLpol': ('Kmin', 'KL1985_pol'), 'Kmax_KLpol': ('Kmax', 'KL1985_pol'), 'Kmin_KLequ': ('Kmin', 'KL1985_equ')}
A8_final = np.c_[np.ones(sel8_final.sum()), u[sel8_final], v[sel8_final]]
biaix = {m: {} for m in ('a', 'b_old', 'b_new', 'joint', 'c')}
for nv, (kk, ff) in VARIANTS.items():
    KF_true = K_MODELS[kk] + F_MODELS[ff]                    # B☉ (fora de l'atmosfera)
    KFg = KF_true * A040 / m2.FAC_G                          # ADU/s de G_cam, com es veu a terra
    # a: mediana
    biaix['a'][nv] = dict(dc0=float(np.median(G[ma_a]) - np.median((G - KFg)[ma_a])))
    # b_old: la recepta sencera amb G − KF
    cbo, _ = recepta_b_old(G - KFg)
    biaix['b_old'][nv] = dict(dc0=biaix['a'][nv]['dc0'], dgu=float(cb_old[1] - cbo[1]), dgv=float(cb_old[2] - cbo[2]))
    # b_new: resposta lineal amb la màscara final
    db, *_ = np.linalg.lstsq(A8_final, KFg[sel8_final], rcond=None)
    biaix['b_new'][nv] = dict(dc0=float(db[0]), dgu=float(db[1]), dgv=float(db[2]))
    # c (registre)
    dcq, *_ = np.linalg.lstsq(Ac[wc], KFg[fc][wc], rcond=None)
    biaix['c'][nv] = dict(coef=[float(x) for x in dcq], dc0=float(dcq[0]))
    # joint: lineal amb la màscara final
    wj = np.zeros_like(dj); wj[np.nonzero(dj)] = J['w']
    Jb = fit_joint(dj, y=np.where(np.isfinite(KFg), KFg, 0.0), w_fix=J['w'])
    biaix['joint'][nv] = dict(dc0=float(Jb['beta'][0]), dgu=float(Jb['beta'][1]), dgv=float(Jb['beta'][2]))
# dipol coronal (part de A − 1) i nivell (A = 1) per al pla b_new i el b_old, model central
KFc = (K_MODELS['Kmax'] + F_MODELS['vdH1950'])
d_nivell, *_ = np.linalg.lstsq(A8_final, (KFc / m2.FAC_G)[sel8_final], rcond=None)
d_total, *_ = np.linalg.lstsq(A8_final, (KFc * A040 / m2.FAC_G)[sel8_final], rcond=None)
cbo_n, _ = recepta_b_old(G - KFc / m2.FAC_G)
cbo_t, _ = recepta_b_old(G - KFc * A040 / m2.FAC_G)
nivells = {}
for rr0 in (7.3, 8.0, 9.0, 10.0, 12.0):
    nivells[f'{rr0:g}'] = dict(Kmax=float(m2.k_max_vdh(rr0)), Kmin=float(m2.k_min_vdh(rr0)), F_vdH=float(m2.f_vdh(rr0)),
                               Kmax_mes_F_BSOL=float(m2.k_max_vdh(rr0) + m2.f_vdh(rr0)),
                               Kmax_mes_F_ADU=float((m2.k_max_vdh(rr0) + m2.f_vdh(rr0)) / m2.FAC_G))
rep['biaix_KF'] = dict(models=dict(K='van de Hulst 1950 eq. 5 (K_max) i 6 (K_min), equador; ×1e-8 B☉ mitjà',
                                   F='van de Hulst 1950 eq. 7; Koutchmy & Lamy 1985 Fig. 3 (digitalitzada a la v1) equatorial i polar'),
                       metode='corona observada = model · 10^(−0,4·0,40·(X − X_ZP)) / FAC_G; biaix = estimador(G) − estimador(G − corona)',
                       per_model=biaix, nivells_model=nivells,
                       contaminacio_pla_b_new=dict(nomes_nivell=[float(x) for x in d_nivell], total_amb_A=[float(x) for x in d_total],
                                                   part_dipol=[float(a - b) for a, b in zip(d_total, d_nivell)]),
                       contaminacio_pla_b_old=dict(nomes_nivell_dgv=float(cb_old[2] - cbo_n[2]), total_amb_A_dgv=float(cb_old[2] - cbo_t[2]),
                                                   nomes_nivell_dgu=float(cb_old[1] - cbo_n[1]), total_amb_A_dgu=float(cb_old[1] - cbo_t[1])))
print('biaix', json.dumps({m: biaix[m]['central'] for m in biaix}, ensure_ascii=False), flush=True)
print('contaminació b_new', rep['biaix_KF']['contaminacio_pla_b_new'], 'b_old', rep['biaix_KF']['contaminacio_pla_b_old'], flush=True)

# ---------------------------------------------------------------- regla de tria (predeclarada)
bn = rep['b_new']; bc = biaix['b_new']['central']
D = dict(D1=bool(bn['jackknife']['sigma_gu'] <= 1.0 and bn['jackknife']['sigma_gv'] <= 1.0),
         D2=bool(abs(bn['meitats']['dif_gv']) <= 1.5),
         D3=bool(abs(bc['dgu']) <= 0.5 and abs(bc['dgv']) <= 0.5),
         D4=bool(bn['jackknife']['sigma_c0'] <= 5.0))
adoptat = 'b_new' if all(D.values()) else 'a'
joint_ok = bool(rep['joint']['jackknife']['sigma_c0'] <= 10.0 and rep['joint']['jackknife']['sigma_gv'] <= 1.0)
alternatives = (['a'] if adoptat == 'b_new' else ['b_new']) + (['joint'] if joint_ok else [])
motiu = ('b_new compleix D1–D4: el pla ajustat on el dipol coronal és negligible està ben determinat' if adoptat == 'b_new' else
         'b_new NO compleix ' + ', '.join(k for k, ok in D.items() if not ok) + ': s\'adopta el cel constant (a)')
rep['tria'] = dict(condicions=D, adoptat=adoptat, motiu=motiu, joint_entra_a_sigma=joint_ok, alternatives_sigma=alternatives,
                   escrit_abans_del_quocient_C2=time.strftime('%Y-%m-%dT%H:%M:%S'))
print('TRIA', rep['tria'], flush=True)

# ---------------------------------------------------------------- CEL_v2.json
def pla(c0, gu, gv, regla, **kw):
    return dict(c0=float(c0), gu=float(gu), gv=float(gv), regla=regla, **kw)


CEL2 = {
    'unitats': 'ADU/s del verd natiu (G_cam), per píxel natiu de la R6; u = (x − cx)/R☉, v = (fila − cy)/R☉',
    'centre_px': mc.SOL_XY, 'R_sol_px': mc.RSOL_PX, 'X_ref_extincio': m2.X_REF,
    'models': {
        'a': dict(c0=c0_a, regla='mediana de G_cam a r > 7,29 R☉ (v1)', n=int(ma_a.sum())),
        'b_old': pla(c0_a, cb_old[1], cb_old[2], 'v1: constant d\'(a) + pla al residu G − perfil azimutal a r > 3,546 R☉ (només registre)'),
        'b_new': pla(cn[0], cn[1], cn[2], 'constant + pla ajustats a G a r ≥ 8 R☉, tot el camp amb dada, 4 rondes 3σ MAD',
                     n=int(wn.sum())),
        'joint': pla(J['beta'][0], J['beta'][1], J['beta'][2], 'ajust conjunt amb C(r)·10^(−0,4·0,40·(X − X_ZP)) des de 3,546 R☉',
                     n=J['n']),
        'c': dict(coef=[float(x) for x in cc_], regla='v1: quadràtic ajustat a G a 4 R☉ < r < R_inscrit. CONTAMINAT DE CORONA: '
                  'no és un model de cel; només registre (fora de σ_cel i de les alternatives)'),
    },
    'adoptat': adoptat, 'motiu': motiu, 'alternatives_sigma': alternatives,
    'sigma_floor_BSOL': m2.SIGMA_SKY_FLOOR_BSOL, 'sigma_floor_adu': m2.SIGMA_SKY_FLOOR_BSOL / m2.FAC_G,
    'biaix_KF': biaix, 'condicions_tria': D, 'R_inscrit_Rsol': RINS,
}
json.dump(CEL2, open(OUT / 'CEL_v2.json', 'w'), indent=1, ensure_ascii=False)
# diagnosi en B☉ al centre i gradient
rep['diagnosi'] = {}
for nom in ('a', 'b_old', 'b_new', 'joint'):
    mm = CEL2['models'][nom]
    rep['diagnosi'][nom] = dict(cel_centre_adu=mm['c0'], cel_centre_BSOL=mm['c0'] * m2.FAC_G,
                                gradient_pct_per_Rsol=100 * math.hypot(mm.get('gu', 0), mm.get('gv', 0)) / mm['c0'],
                                direccio_PA_mes_brillant=(None if nom == 'a' else
                                                          float(g.polar(mc.SOL_XY[0] + 50 * mm['gu'], mc.SOL_XY[1] + 50 * mm['gv'])[1])),
                                biaix_KF_central_dc0_adu=biaix[nom]['central']['dc0'],
                                biaix_KF_central_dc0_BSOL=biaix[nom]['central']['dc0'] * m2.FAC_G)
rep['temps_s'] = time.time() - T0
json.dump(rep, open(OUT / 'PROVES_W1.json', 'w'), indent=1, ensure_ascii=False, default=float)
print(json.dumps(rep['diagnosi'], indent=1, ensure_ascii=False))
print(f'fet en {time.time() - T0:.0f} s')
