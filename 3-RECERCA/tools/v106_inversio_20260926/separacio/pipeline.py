"""pipeline (V106 · Separació, Claude, 26-09-2026) · Inversió conjunta completa + proves, reutilitzable per a la dada real, per als
bessons sintètics (veritat coneguda) i per a les injeccions.
  inverteix(frames, ydelta)      → Inversio ajustada (IRLS amb el soroll re-estimat, o pesos fixos si var_tab es dona)
  proves(ydelta)                 → Ĉ de tots, Ĉ(S1), Ĉ(S2), hA (A netejat amb la Λ de S1), hB (B netejat amb la Λ de S2),
                                   prova «Lluna o corona» (m1) i ρ entre Ĉ(S1) i Ĉ(S2)."""
import numpy as np, json, time, copy
from inversio import Inversio
from proves import m1, rho, taula
CFG = dict(DMAX=4.0, dphi=0.125, LO=0.6, regD=0.05, ridge=1e-4, irls=2)
class Pipeline:
    def __init__(self, cfg=None, S=None):
        self.cfg = dict(CFG); self.cfg.update(cfg or {})
        self.sig = dict(np.load('/private/tmp/claude_v106/separacio/SIG.npz'))
        self.fr = [j for j in range(67) if self.sig['sig'][j].min() < 0.5]
        self.A = [j for j in self.fr if j <= 10]; self.B = [j for j in self.fr if 13 <= j <= 18]
        R = [j for j in self.fr if j not in self.A + self.B]; self.S1 = sorted(self.A + R[0::2]); self.S2 = sorted(self.B + R[1::2])
        self.S = S
    def nova(self):
        c = self.cfg; I = Inversio(S=self.S, sig_tab=self.sig, verbose=False, DMAX=c['DMAX'], dphi=c['dphi'], LO=c['LO']); self.S = I.S; return I
    def inverteix(self, frames, ydelta=None, var_tab=None, I=None, prepara=True):
        c = self.cfg; I = I or self.nova()
        if prepara: I.prepara(frames)
        if var_tab is not None:
            I.var_tab = var_tab; I.construeix(frames, ydelta=ydelta); I.resol(ridge=c['ridge'], regD=c['regD']); return I
        I.var_tab = None
        for it in range(c['irls'] + 1):
            I.construeix(frames, ydelta=ydelta); I.resol(ridge=c['ridge'], regD=c['regD'])
            if it < c['irls']: I.reestima_soroll_y(ydelta) if ydelta is not None else I.reestima_soroll()
        for it in range(c.get('amplitud', 0)):          # amplitud del terme lunar per fotograma (opcional)
            I.amplitud_frames(); I.construeix(frames, ydelta=ydelta); I.resol(ridge=c['ridge'], regD=c['regD'])
        return I
    def proves(self, ydelta=None, var_tab=None, verbose=True, caches=None):
        S = self.S if self.S is not None else self.nova().S
        IT = self.inverteix(self.fr, ydelta, var_tab)
        I1 = self.inverteix(self.S1, ydelta, var_tab); I2 = self.inverteix(self.S2, ydelta, var_tab)
        S = IT.S; i4 = S.i4; dg = S.dg[i4:]; nth = S.nth
        hA, pA = I1.grup(self.A, ydelta); hB, pB = I2.grup(self.B, ydelta)
        cA = S.C0[self.A].mean(0); cB = S.C0[self.B].mean(0)
        r_m1 = m1(dg, nth, hA[i4:], pA[i4:], hB[i4:], pB[i4:], cA, cB)
        W1 = I1.Wt.reshape(I1.C.shape); W2 = I2.Wt.reshape(I2.C.shape)
        r_rho = rho(dg, nth, I1.C[i4:], W1[i4:], I2.C[i4:], W2[i4:])
        if verbose:
            print('--- prova Lluna/corona (inversions independents S1/S2) ---'); print(taula(r_m1))
            print('--- ρ entre Ĉ(S1) i Ĉ(S2) ---'); print(taula(r_rho))
        return dict(IT=IT, I1=I1, I2=I2, hA=hA, pA=pA, hB=hB, pB=pB, m1=r_m1, rho=r_rho, cA=cA, cB=cB)
