"""s3 (V106 · Separació, Claude, 26-09-2026) · Inversió conjunta sobre la dada real + proves.
  · Ĉ de TOTS els fotogrames (IRLS: 1/σ² amb σ empíric per fotograma i franja de D/d, 2 passades).
  · Dues inversions INDEPENDENTS amb conjunts disjunts: S1 = A (0–10) ∪ meitat dels altres, S2 = B (13–18) ∪ l'altra meitat.
    hA = grup A netejat amb la Λ de S1; hB = grup B netejat amb la Λ de S2 (cap soroll compartit entre hA i hB) → prova «Lluna o corona».
    ρ entre Ĉ(S1) i Ĉ(S2) → reproductibilitat.
  · Desa DELTA (format de la c1: delta, pes, dgrid, nth, centre, h125/p125, hcurts/pcurts, hA/pA, hB/pB, centres) amb d −4…40.
Ús: s3_real.py '<config json>' <etiqueta>"""
import numpy as np, sys, json, time, pickle
from inversio import Inversio
from proves import m1, rho, taula
cfg = dict(DMAX=4.0, dphi=0.125, LO=0.6, regD=0.05, ridge=1e-4, irls=2)
if len(sys.argv) > 1: cfg.update(json.loads(sys.argv[1]))
TAG = sys.argv[2] if len(sys.argv) > 2 else 'base'
sig = dict(np.load('SIG.npz')); t0 = time.time()
def nova():
    return Inversio(sig_tab=sig, verbose=False, DMAX=cfg['DMAX'], dphi=cfg['dphi'], LO=cfg['LO'])
fr = [j for j in range(67) if sig['sig'][j].min() < 0.5]
A = [j for j in fr if j <= 10]; B = [j for j in fr if 13 <= j <= 18]; R = [j for j in fr if j not in A + B]
R1 = R[0::2]; R2 = R[1::2]; S1 = sorted(A + R1); S2 = sorted(B + R2)
def inverteix(frames, I=None):
    I = I or nova(); I.prepara(frames)
    for it in range(cfg['irls'] + 1):
        I.construeix(frames); I.resol(ridge=cfg['ridge'], regD=cfg['regD'])
        if it < cfg['irls']: I.reestima_soroll()
    return I
IT = inverteix(fr); print('tots', round(time.time() - t0), 's', flush=True)
I1 = inverteix(S1); I2 = inverteix(S2); print('dues meitats', round(time.time() - t0), 's', flush=True)
S = IT.S; i4 = S.i4; dg = S.dg[i4:]; nth = S.nth
hA, pA = I1.grup(A); hB, pB = I2.grup(B)
cA = S.C0[A].mean(0); cB = S.C0[B].mean(0)
res = m1(dg, nth, hA[i4:], pA[i4:], hB[i4:], pB[i4:], cA, cB)
print('--- prova Lluna/corona (hA de S1, hB de S2; inversions independents) ---'); print(taula(res))
W1 = I1.Wt.reshape(I1.C.shape); W2 = I2.Wt.reshape(I2.C.shape)
rr = rho(dg, nth, I1.C[i4:], W1[i4:], I2.C[i4:], W2[i4:])
print('--- ρ entre Ĉ(S1) i Ĉ(S2) ---'); print(taula(rr, fmt='{:+.2f}'))
# δ cru per grups (referència: la mateixa prova sense separar, mateixos pesos)
lam1 = I1.lam.copy(); lam2 = I2.lam.copy(); I1.lam[:] = 0; I2.lam[:] = 0
hA0, pA0 = I1.grup(A); hB0, pB0 = I2.grup(B); I1.lam[:] = lam1; I2.lam[:] = lam2
res0 = m1(dg, nth, hA0[i4:], pA0[i4:], hB0[i4:], pB0[i4:], cA, cB)
print('--- la mateixa prova sense separar (δ cru, pesos IRLS) ---'); print(taula(res0))
WT = IT.Wt.reshape(IT.C.shape)
out = f'DELTA_sep_{TAG}.npz'
np.savez_compressed(out, delta=np.where(WT[i4:] > 0, IT.C[i4:], 0).astype(np.float32), pes=WT[i4:].astype(np.float32), dgrid=dg.astype(np.float32), nth=nth,
    centre=np.array([S.cx, S.cy, S.R]),
    h125=np.where(W1[i4:] > 0, I1.C[i4:], np.nan).astype(np.float32), p125=W1[i4:].astype(np.float32),
    hcurts=np.where(W2[i4:] > 0, I2.C[i4:], np.nan).astype(np.float32), pcurts=W2[i4:].astype(np.float32),
    hA=np.where(pA[i4:] > 0, hA[i4:], np.nan).astype(np.float32), pA=pA[i4:].astype(np.float32),
    hB=np.where(pB[i4:] > 0, hB[i4:], np.nan).astype(np.float32), pB=pB[i4:].astype(np.float32),
    centres=np.array([[j, *S.C0[j]] for j in fr]), lam=IT.Lam().astype(np.float32), lam_obs=IT.lam_obs,
    cfg=json.dumps(cfg), S1=np.array(S1), S2=np.array(S2))
json.dump(dict(cfg=cfg, m1={f'{k[0]}-{k[1]} d{k[2]}': v for k, v in res.items()}, m1_cru={f'{k[0]}-{k[1]} d{k[2]}': v for k, v in res0.items()},
               rho={f'{k[0]}-{k[1]} d{k[2]}': v for k, v in rr.items()}), open(f'PROVES_{TAG}.json', 'w'), indent=1)
pickle.dump(dict(var=IT.var_tab), open(f'VAR_{TAG}.pkl', 'wb'))
print('desat', out, round(time.time() - t0), 's')
