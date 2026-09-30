"""b2b (V117, 29-09-2026) · PROVA D'INJECCIÓ del filtre A·B (norma de portes de senyal feble): raigs sintètics coneguts, multiplicatius
(L' = L·e^s), perfil azimutal gaussià σ 0,2°, de 2,0 a 6,0 R☉ (extrems suaus), amplitud ±0,5 % en ln (com el detall real a 2–3,5 R☉):
  · 12 raigs NOMÉS a A (artefacte d'un apuntament: ideal, passa 0),
  · 12 raigs NOMÉS a B (ideal 0),
  · 12 raigs a TOTES DUES (cel: ideal, passa 1), signes alternats.
Mesura (v2): fracció que passa = projecció de Δ(detall filtrat) sobre el perfil injectat / projecció de Δ(detall d'un apuntament), a ±1° del raig,
per bandes de radi (2–3,5 i 3,5–5,5 R☉); mediana i quartils per tipus,
per a les dues combinacions: D_wiener = w·(DA + DB)/2 (la de la V116) i D_min = w·[mateix signe]·signe·min(|DA|, |DB|) (nova).
Ús: b2b_injeccio.py <carpeta_sortida>  → B2B_INJECCIO.json"""
import sys, json, importlib.util, numpy as np
from pathlib import Path
R = Path(__file__).resolve().parents[3]; OUT = Path(sys.argv[1]).resolve(); OUT.mkdir(parents=True, exist_ok=True)
spec = importlib.util.spec_from_file_location('b1', Path(__file__).with_name('b1_filtre_coherent_AB.py')); b1 = importlib.util.module_from_spec(spec); sys.argv_ = sys.argv; spec.loader.exec_module(b1)
H, W, SOL, RS = b1.H, b1.W, b1.SOL, b1.RS
LA, LB, m = b1.suport()
PM0, DA0, DB0, w0, Dw0, Dm0 = b1.nucli(LA, LB, m)
# azimuts amb camp comú de 2 a 6 R☉ (≥ 95 % de les files), separats ≥ 12°
rows = (np.exp(b1.rho) / RS >= 2.0) & (np.exp(b1.rho) / RS <= 6.0); cob = PM0[rows].mean(0)
cands = [int(j) for j in np.argsort(-cob) if cob[j] >= 0.95]
tria = []
for j in cands:
    if all(min(abs(j - k), b1.NT - abs(j - k)) * 360 / b1.NT >= 5 for k in tria): tria.append(j)
    if len(tria) == 36: break
assert len(tria) == 36, f'només {len(tria)} azimuts amb camp comú'
tria = sorted(tria)
TIPUS = ['A', 'B', 'AB'] * 12; SIGNE = ([+1] * 3 + [-1] * 3) * 6
AMP, SIG_T = 0.005, np.radians(0.2)
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); rr = np.hypot(xx - SOL[0], yy - SOL[1]) / RS; tt = np.mod(np.arctan2(-(yy - SOL[1]), xx - SOL[0]), 2 * np.pi); del yy, xx
def smooth(x, a, c): t = np.clip((x - a) / (c - a), 0, 1); return t * t * (3 - 2 * t)
env = (smooth(rr, 2.0, 2.3) * (1 - smooth(rr, 5.7, 6.0))).astype(np.float32); del rr
sA = np.zeros((H, W), np.float32); sB = np.zeros((H, W), np.float32)
for j, tp, sg in zip(tria, TIPUS, SIGNE):
    t0 = j * 2 * np.pi / b1.NT; dt = np.angle(np.exp(1j * (tt - t0))).astype(np.float32); prof = (sg * AMP * np.exp(-0.5 * (dt / SIG_T) ** 2)).astype(np.float32) * env
    if tp in ('A', 'AB'): sA += prof
    if tp in ('B', 'AB'): sB += prof
del tt
PM1, DA1, DB1, w1, Dw1, Dm1 = b1.nucli(LA * np.exp(sA), LB * np.exp(sB), m)
rrp = np.exp(b1.rho) / RS; res = dict(amplitud_ln=AMP, sigma_graus=0.2, azimuts_graus=[round(j * 360 / b1.NT, 2) for j in tria], tipus=TIPUS, signe=SIGNE, bandes={})
HW = int(np.radians(1.0) / (2 * np.pi / b1.NT)); kk = np.arange(-HW, HW + 1); pesos = np.exp(-0.5 * (kk * (2 * np.pi / b1.NT) / SIG_T) ** 2)
for a, b in ((2.0, 3.5), (3.5, 5.5)):
    rw = (rrp >= a + 0.1) & (rrp <= b - 0.1); o = {}
    for tp in ('A', 'B', 'AB'):
        fw, fm = [], []
        for j, t_, sg in zip(tria, TIPUS, SIGNE):
            if t_ != tp: continue
            cols = (j + kk) % b1.NT; ok = rw[:, None] & PM0[:, cols] & PM1[:, cols]
            def proj(X1, X0): return float(np.sum(np.where(ok, (X1[:, cols] - X0[:, cols]) * pesos[None, :], 0)))
            ref = proj(DA1, DA0) if tp in ('A', 'AB') else proj(DB1, DB0)
            fw.append(proj(Dw1, Dw0) / ref); fm.append(proj(Dm1, Dm0) / ref)
        q = lambda v: [round(float(x), 3) for x in np.percentile(v, [25, 50, 75])]
        o[tp] = dict(wiener_q25_q50_q75=q(fw), minim_q25_q50_q75=q(fm), per_raig_wiener=[round(v, 3) for v in fw], per_raig_minim=[round(v, 3) for v in fm])
    res['bandes'][f'{a}-{b}'] = o
    print(f'{a}–{b} R☉ (mediana [q25, q75]): ' + ' · '.join(f'{tp}: Wiener {o[tp]["wiener_q25_q50_q75"][1]:.2f} [{o[tp]["wiener_q25_q50_q75"][0]:.2f}, {o[tp]["wiener_q25_q50_q75"][2]:.2f}], mínim {o[tp]["minim_q25_q50_q75"][1]:.2f} [{o[tp]["minim_q25_q50_q75"][0]:.2f}, {o[tp]["minim_q25_q50_q75"][2]:.2f}]' for tp in ('A', 'B', 'AB')), flush=True)
(OUT / 'B2B_INJECCIO.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
