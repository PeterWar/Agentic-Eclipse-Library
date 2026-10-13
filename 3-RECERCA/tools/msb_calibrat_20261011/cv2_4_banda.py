"""cv2_4 · Prova de banda v2 (12-10-2026). Segueix PREDECLARACIO_COMPARACIONS_v2.md (D).

MSB_R/MSB_G = (fac_R/fac_G)·(raw_R/raw_G), amb raw_c = canal natiu menys el seu cel b_new (cv2_0) i la mateixa E per als dos
(s'anul·la). Zona Vixen pura (wv ≥ 0,99), 1,15–1,9 R☉, sectors de 10° amb ≥ 200 píxels; mediana dels sectors per anell.
El factor fac_R/fac_G = F☉G/F☉R es dona amb TOTS els estimadors:
  1. els dos ajustos de punt zero fets per separat (adoptat a zp_canal: 2,633/2,7714 = 0,950);
  2. el bootstrap d'aquests ajustos (SENSIBILITAT_ZP.json, F_sol_R_sobre_G), amb els percentils EN L'ORDRE BO (la v1 els
     tenia girats a BANDA.json: p16 i p84 de F☉R/F☉G invertits sense reordenar);
  3. l'ajust aparellat del color m_R − m_G sobre les MATEIXES estrelles (constant + (B−V − 0,653) + (X − X☉)): totes, retall
     2,5σ, només les usades pels dos ajustos separats (la recepta del verificador v4b, refeta aquí des de la taula per estrella).
Predicció de Thomson amb els termes que la v1 oblidava (línies d'emissió, enrogiment de la F) i la nota 109 §12 com a
evidència independent indicativa. Escriu v2/comparacions/banda/BANDA_v2.json i quocients_per_sector_v2.csv."""
import csv
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cv2_comu as cv   # noqa: E402

mc, m2, cc1 = cv.mc, cv.m2, cv.cc1
T0 = time.time()
OUT = cv.RES2 / 'banda'; OUT.mkdir(parents=True, exist_ok=True)
N = np.load(cv.RES2 / 'caselles_v2.npz')
AN = [tuple(a) for a in N['banda_anells']]
us = N['banda_usable']
ZPJ = json.load(open(mc.RES / 'zp_canal/ZP_CANAL.json'))
SENS = json.load(open(mc.RES / 'zp_canal/SENSIBILITAT_ZP.json'))
FAC = {c: float(ZPJ['canals'][c]['fac']) for c in 'RG'}

# ---------------------------------------------------------------- 1–2. ajustos separats i el seu bootstrap
est = {}
est['ajustos_separats_adoptat'] = dict(fac_R_sobre_fac_G=FAC['R'] / FAC['G'], FsolR_sobre_FsolG=FAC['G'] / FAC['R'],
                                       nota='zp_canal: R n 17/21, correcció d\'obertura 1,109; G n 14/21')
bf = SENS['r6']['bootstrap_conjunt']['F_sol_R_sobre_G']          # percentils de F☉R/F☉G
# fac_R/fac_G = 1/(F☉R/F☉G): el percentil q del factor és 1/(percentil 100 − q del quocient de fluxos)
fac_boot = {'p2_5': 1 / bf['p97_5'], 'p16': 1 / bf['p84'], 'p50': 1 / bf['p50'], 'p84': 1 / bf['p16'], 'p97_5': 1 / bf['p2_5']}
assert fac_boot['p2_5'] < fac_boot['p16'] < fac_boot['p50'] < fac_boot['p84'] < fac_boot['p97_5']
est['bootstrap_ajustos_separats'] = dict(fac_R_sobre_fac_G=fac_boot, FsolR_sobre_FsolG=bf)

# ---------------------------------------------------------------- 3. ajust aparellat del color sobre les mateixes estrelles
import pandas as pd   # noqa: E402
W17 = mc.ARREL / '3-RECERCA/resultats/derivats/Astrometria/Estrelles/Work_2026-08-17/xmatch'
ZPC = mc.RES / 'zp_canal/work/canal/zp_canal_per_estrella.csv'
Xs = json.load(open(W17 / 'zp.json'))['r6']['Xsun']; BVS = 0.653
e = pd.read_csv(ZPC)
q = e[np.isfinite(e.minst_R_interp) & np.isfinite(e.minst_G_interp)].reset_index(drop=True)
col = (q.minst_R_interp - q.minst_G_interp).values
A = np.column_stack([np.ones(len(q)), q.BV.values - BVS, q.X.values - Xs])


def fit(ok, clip=None):
    ok = ok.copy()
    for _ in range(6 if clip else 1):
        s, *_ = np.linalg.lstsq(A[ok], col[ok], rcond=None)
        r = col - A @ s; sd = 1.4826 * np.median(np.abs(r[ok] - np.median(r[ok])))
        if not clip:
            break
        nou = np.abs(r - np.median(r[ok])) < clip * max(sd, 0.02)
        if (nou == ok).all():
            break
        ok = nou
    s, *_ = np.linalg.lstsq(A[ok], col[ok], rcond=None)
    rr = col[ok] - A[ok] @ s; s2 = (rr ** 2).sum() / max(ok.sum() - 3, 1); cov = s2 * np.linalg.pinv(A[ok].T @ A[ok])
    FR = float(10 ** (-0.4 * s[0]))
    return dict(n=int(ok.sum()), FsolR_sobre_FsolG=FR, fac_R_sobre_fac_G=1 / FR, err_rel=float(0.4 * np.log(10) * np.sqrt(cov[0, 0])),
                pendent_BV=float(s[1]), pendent_X=float(s[2]), pendent_X_err=float(np.sqrt(cov[2, 2])), rms=float(np.sqrt(s2)))


tot = np.ones(len(q), bool)
amb = (q.usada_R_interp.astype(bool) & q.usada_G_interp.astype(bool)).values
apar = {'totes': fit(tot), 'retall_2_5sigma': fit(tot, 2.5), 'usades_pels_dos_ajustos': fit(amb)}
rng = np.random.default_rng(20261012); bs = []
for _ in range(2000):
    i = rng.integers(0, len(q), len(q))
    s, *_ = np.linalg.lstsq(A[i], col[i], rcond=None); bs.append(10 ** (0.4 * s[0]))        # fac_R/fac_G = 1/(F☉R/F☉G)
apar['bootstrap_totes'] = dict(fac_R_sobre_fac_G={k: float(np.percentile(bs, p)) for k, p in
                                                  (('p2_5', 2.5), ('p16', 16), ('p50', 50), ('p84', 84), ('p97_5', 97.5))})
est['ajust_aparellat_del_color'] = apar
VX = json.load(open(mc.RES / 'verificacio_xifres/sortides/COLOR_ESTRELLES_VX.json'))
control_vx = {k: (apar[k2]['FsolR_sobre_FsolG'], VX[k]['RG_sol']) for k, k2 in (('totes', 'totes'), ('retall_2.5sigma', 'retall_2_5sigma'),
                                                                                ('usades_als_dos_ajustos', 'usades_pels_dos_ajustos'))}
print('control contra el verificador (F☉R/F☉G aquí, VX):', control_vx, flush=True)

# ---------------------------------------------------------------- quocients per anell
pa_sec = np.arange(36)


def anell(num, den, i, nboot=2000):
    ok = us[i] & np.isfinite(num[i]) & np.isfinite(den[i]) & (den[i] > 0)
    qs = num[i][ok] / den[i][ok]; ps = pa_sec[ok]
    out = dict(sectors=int(ok.sum()), mediana=float(np.median(qs)), dispersio_entre_sectors=float(1.4826 * np.median(np.abs(qs - np.median(qs)))),
               min=float(qs.min()), max=float(qs.max()))
    for bloc in (1, 3):                    # 1 sector = 10°; 3 sectors = 30°
        b = ps // bloc; ub = np.unique(b); r_ = np.random.default_rng(11 + bloc); bb = []
        for _ in range(nboot):
            tria = r_.choice(ub, len(ub)); sel = np.concatenate([np.nonzero(b == u)[0] for u in tria]); bb.append(np.median(qs[sel]))
        out[f'ic68_blocs_{10 * bloc}'] = [float(np.percentile(bb, 16)), float(np.percentile(bb, 84))]
    return out


cru = [anell(N['banda_raw_R'], N['banda_raw_G'], i) for i in range(len(AN))]
cru_a = [anell(N['banda_msbR_a'] / FAC['R'], N['banda_msbG_a'] / FAC['G'], i) for i in range(len(AN))]
FACTORS = {'separats_adoptat': FAC['R'] / FAC['G'], 'separats_bootstrap_p50': fac_boot['p50'],
           'aparellat_totes': apar['totes']['fac_R_sobre_fac_G'], 'aparellat_retall': apar['retall_2_5sigma']['fac_R_sobre_fac_G'],
           'aparellat_usades_pels_dos': apar['usades_pels_dos_ajustos']['fac_R_sobre_fac_G'],
           'aparellat_bootstrap_p50': apar['bootstrap_totes']['fac_R_sobre_fac_G']['p50']}
taula = []
for i, a in enumerate(AN):
    fila = dict(anell=list(a), color_cru_R_sobre_G=cru[i], color_cru_cel_constant=cru_a[i]['mediana'],
                MSB_R_sobre_MSB_G={k: cru[i]['mediana'] * f for k, f in FACTORS.items()},
                MSB_R_sobre_MSB_G_bootstrap_separats={k: cru[i]['mediana'] * f for k, f in fac_boot.items()},
                MSB_R_sobre_MSB_G_bootstrap_aparellat={k: cru[i]['mediana'] * f for k, f in apar['bootstrap_totes']['fac_R_sobre_fac_G'].items()})
    v = list(fila['MSB_R_sobre_MSB_G'].values())
    fila['rang_dels_estimadors'] = [float(min(v)), float(max(v))]
    taula.append(fila)
    print(a, 'cru', round(cru[i]['mediana'], 4), 'estimadors', {k: round(x, 3) for k, x in fila['MSB_R_sobre_MSB_G'].items()}, flush=True)

# ---------------------------------------------------------------- predicció (amb hipòtesis escrites)
# (a) K: transferència entre bandes per l'enfosquiment del limbe, K_MSB(R)/K_MSB(G), Baumbach–Allen, u_R 0,52–0,60, u_G 0,60–0,68
TK = {}
for a, b in AN:
    rm = 0.5 * (a + b)
    v = [cc1.transfer_banda_k(rm, cc1.MODELS_DENSITAT['Baumbach-Allen'], uR, uG) for uR in (0.52, 0.60) for uG in (0.60, 0.68)]
    TK[f'{a}-{b}'] = [float(min(v)), float(max(v))]
# (b) fracció de F al total: F de van de Hulst 1950 sobre la NOSTRA MSB (mediana de les caselles usables), a cada anell del K-Cor
#     (no pB/p: més enllà d'1,7 R☉ el pB L2 té un residu negatiu i faria la K massa petita)
K2 = np.load(cv.RES2 / 'kcor' / 'kcor_caselles_v2.npz')
fF = {}
for i, (a, b) in enumerate(cv.ANELLS_KCOR[:4]):
    usk = N['kcor_usable'][i]
    fF[f'{a}-{b}'] = float(np.nanmedian(np.where(usk, K2['F_vdH1950'][i], np.nan)) / np.nanmedian(np.where(usk, N['kcor_msb'][i], np.nan)))
fF_banda = {f'{a}-{b}': fF.get(f'{a}-{b}', fF['1.7-2.0']) for a, b in AN}
RHO_F = (1.00, 1.10)          # HIPÒTESI: color de la F respecte del Sol entre el verd i el vermell (0 a +10 %)
EPS_G = (0.0, 0.06)           # HIPÒTESI: Fe XIV 530,3 nm al verd, en fracció del continu (0–6 %, ordre de magnitud)
EPS_R = (0.0, 0.02)           # HIPÒTESI: Fe X 637,4 nm al vermell (0–2 %)
pred = {}
for a, b in AN:
    k = f'{a}-{b}'
    lo = TK[k][0] * (1 + fF_banda[k] * (RHO_F[0] - 1)) * (1 + EPS_R[0]) / (1 + EPS_G[1])
    hi = TK[k][1] * (1 + fF_banda[k] * (RHO_F[1] - 1)) * (1 + EPS_R[1]) / (1 + EPS_G[0])
    pred[k] = dict(transferencia_K=TK[k], fraccio_F=fF_banda[k], prediccio=[float(lo), float(hi)])
nota109 = dict(font='3-RECERCA/109_EL_COLOR_DE_BRNO_MESURAT_2026-08-26.md §12',
               prediccio_Sol_extingit_X_6_12=dict(R_sobre_G=1.818, B_sobre_G=0.250),
               fotograma_572A2996_a_1_70_Rsol=dict(R_sobre_G=1.796, B_sobre_G=0.243, cel='~5 %'),
               desacord=dict(R_sobre_G=-0.012, B_sobre_G=-0.028),
               banda_de_sensibilitat_atmosferica=dict(R_sobre_G=[1.71, 1.95], AOD=[0.18, 0.30], angstrom=[1.0, 1.6]),
               corona_respecte_del_Sol_R_sobre_G=[1.796 / 1.95, 1.796 / 1.71],
               avisos=['sRGB lineal (CIE 1931 → sRGB), Sol de Planck 5772 K, no els canals natius', 'un sol fotograma; el compost Vixen dona B/G 7,6 % per sota de la banda'])
with open(OUT / 'quocients_per_sector_v2.csv', 'w', newline='') as fh:
    w = csv.writer(fh)
    w.writerow(['r_in', 'r_out', 'pa_from', 'pa_to', 'n_px', 'usable', 'raw_R_minus_sky', 'raw_G_minus_sky', 'raw_R_over_G', 'MSB_R_over_G_adopted_separate_fits'])
    for i, (a, b) in enumerate(AN):
        for s in range(36):
            rr = N['banda_raw_R'][i, s] / N['banda_raw_G'][i, s]
            w.writerow([a, b, 10 * s, 10 * s + 10, int(N['banda_nvalid'][i, s]), bool(us[i, s]), f"{N['banda_raw_R'][i, s]:.4f}",
                        f"{N['banda_raw_G'][i, s]:.4f}", f'{rr:.5f}', f"{rr * FAC['R'] / FAC['G']:.5f}"])
cv.json_dump(dict(
    guio=cv.rel(__file__), data=time.strftime('%Y-%m-%dT%H:%M:%S'), predeclaracio=cv.rel(cv.RES2 / 'PREDECLARACIO_COMPARACIONS_v2.md'),
    zona='wv ≥ 0,99, 1,15–1,9 R☉, sectors de 10° amb ≥ 200 px, cap píxel de franja, buit, protuberància, fantasma',
    cel_per_canal='b_new de la v2 per canal (cv2_0_cel_canals.py)', E='k = 0,40 per als dos canals (s\'anul·la al quocient)',
    estimadors_fac_R_sobre_fac_G=est, control_contra_verificador=control_vx, factors_usats=FACTORS, anells=taula, prediccio=pred,
    hipotesis_prediccio=dict(u_R=[0.52, 0.60], u_G=[0.60, 0.68], color_F_respecte_Sol=RHO_F, Fe_XIV_al_verd=EPS_G, Fe_X_al_vermell=EPS_R,
                             nota='ordres de magnitud, no mesures: la corba espectral de la càmera no s\'ha mesurat'),
    nota_109_s12=nota109,
    avisos=['No es cita 0,77 ± 0,01 ni l\'Orange −11 % com a mesura: el resultat el mana el punt zero vermell (retall per canal i correcció d\'obertura +11 %).',
            'Les ± (IC dels sectors) són estadístiques; el rang dels estimadors és la incertesa que compta.',
            'Els factors per canal són de fotometria d\'estrelles sense flat; el compost porta flat: la normalització R/G del flat al lloc del Sol no s\'ha mesurat.',
            'La v1 (comparacions/banda/BANDA.json) tenia els percentils de fac_R/fac_G girats (p16 1,228 > p84 0,979). Aquí, en ordre.'],
    entrades_sha256={cv.rel(p): cv.sha256(p) for p in (cv.RES2 / 'caselles_v2.npz', mc.RES / 'zp_canal/ZP_CANAL.json', mc.RES / 'zp_canal/SENSIBILITAT_ZP.json',
                                                       ZPC, W17 / 'zp.json', cv.RES2 / 'kcor' / 'KCOR_v2.json')},
    segons=round(time.time() - T0, 1)), OUT / 'BANDA_v2.json')
print('predicció', pred)
print(f'fet ({time.time() - T0:.0f} s)')
