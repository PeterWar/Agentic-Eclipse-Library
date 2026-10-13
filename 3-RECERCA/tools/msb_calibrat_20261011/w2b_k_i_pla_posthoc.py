"""w2b · POST HOC (després de veure els dipols de w2). No canvia res adoptat.

Dues lectures dels dipols cap al zenit (DIPOL_C2_v2.json):
 (1) k que anul·la el dipol a cada anell, per a cada cel: k0 = −0,40·D(k=0)/P(0,40), on P és el dipol de ln E predit per a
     k = 0,40 (lineal en k); error propagat del bootstrap per blocs de 10° i de 30°.
 (2) Ajust de dos paràmetres que fa servir la dependència radial diferent dels dos efectes (suggeriment del verificador v2):
     D_i(k, λ) = D_i(a, k=0) − λ·[D_i(a, k=0) − D_i(b_new, k=0)] + (k/0,40)·P_i = 0 per als sis anells; λ escala el pla de b_new
     (λ = 0: cel constant; λ = 1: el pla mesurat a r ≥ 8 R☉). Mínims quadrats ponderats; errors amb les σ de blocs de 30°.
     Aproximació lineal; no inclou altres asimetries (halo, curvatura del cel, Sony·ρ, diferències de banda amb el C2), que
     la component perpendicular del dipol (+0,04 a +0,12 a 3,3–5,5 R☉) diu que hi són.
Escriu v2/mapa/dipol_c2/K_I_PLA_posthoc.json."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import msb_comu_v2 as m2   # noqa: E402

D = json.load(open(m2.MAPA2 / 'dipol_c2' / 'DIPOL_C2_v2.json'))
AN = [f'{a[0]}-{a[1]}' for a in D['anells']]
P = np.array([D['prediccio_lnE']['0.40'][a]['cap_al_zenit'] for a in AN])
out = dict(guio='w2b_k_i_pla_posthoc.py', caracter='POST HOC', anells=AN, P_lnE_k040=P.tolist(), k_que_anulla={})
for cel in ('a', 'b_old', 'b_new', 'joint_c0fix', 'c'):
    d0 = np.array([D['dipol'][cel]['0.00'][a]['cap_al_zenit'] for a in AN])
    e10 = np.array([D['dipol'][cel]['0.00'][a]['cap_al_zenit_err'] for a in AN])
    e30 = np.array([D['dipol'][cel]['0.00'][a]['cap_al_zenit_err_blocs30'] for a in AN])
    k0 = -0.40 * d0 / P
    out['k_que_anulla'][cel] = dict(k=k0.round(3).tolist(), err_blocs10=np.abs(0.40 * e10 / P).round(3).tolist(),
                                    err_blocs30=np.abs(0.40 * e30 / P).round(3).tolist())
# (2) ajust (k, λ)
da = np.array([D['dipol']['a']['0.00'][a]['cap_al_zenit'] for a in AN])
db = np.array([D['dipol']['b_new']['0.00'][a]['cap_al_zenit'] for a in AN])
ea = np.array([D['dipol']['a']['0.00'][a]['cap_al_zenit_err_blocs30'] for a in AN])
dD = da - db
res = {}
for nom, sel in (('6_anells', slice(0, 6)), ('interiors_2.4-3.8', slice(0, 4)), ('interiors_2.4-3.3', slice(0, 3))):
    y = da[sel]; Aj = np.c_[-P[sel] / 0.40, dD[sel]]          # y = (−P/0,4)·k + ΔD·λ
    w = 1.0 / ea[sel]
    c, *_ = np.linalg.lstsq(Aj * w[:, None], y * w, rcond=None)
    cov = np.linalg.inv((Aj * w[:, None]).T @ (Aj * w[:, None]))
    resid = y - Aj @ c
    chi2 = float(np.sum((resid * w) ** 2)); dof = int(len(y) - 2)
    res[nom] = dict(k=float(c[0]), k_err=float(np.sqrt(cov[0, 0])), lambda_=float(c[1]), lambda_err=float(np.sqrt(cov[1, 1])),
                    corr_k_lambda=float(cov[0, 1] / np.sqrt(cov[0, 0] * cov[1, 1])), chi2=chi2, graus_llibertat=dof,
                    residus=resid.round(4).tolist())
out['ajust_k_lambda'] = res
out['nota'] = ('λ escala el pla de b_new (gu 0,307, gv −3,738 ADU/s per R☉); errors amb les σ de blocs de 30° del cel a; '
               'la correlació entre anells veïns no s\'ha modelat, així que els errors són indicatius')
json.dump(out, open(m2.MAPA2 / 'dipol_c2' / 'K_I_PLA_posthoc.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
