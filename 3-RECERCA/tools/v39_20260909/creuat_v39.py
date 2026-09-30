"""creuat_v39 · Terme de Wiener CREUAT entre trens (V39, ronda 2 de Codex: «cross-power preserved»).

Per què: el llindar tou per coeficient (Auchère, k=2) no pot separar el que és per SOTA del soroll d'un sol coeficient: a 3,5–4 R☉, on el 90 %
de l'energia de les bandes ≤ 32 px és soroll, atenua la component correlacionada amb la Vixen original quasi tant com el rms (C3b: ACHF ×0,40–0,45,
MGN ×0,62–0,70). El que SÍ que es pot mesurar és la potència que els DOS telescopis veuen alhora: el soroll de la Vixen i el de la Sony són
independents (sensors diferents), o sigui que E[b_V·b_S] = potència del senyal compartit (corona + cel comú, tots dos reals i tots dos al TOTAL).
Guany regional g_c = clip((C − guarda)/E_F, 0, 1) amb C = <b_V b_S> (finestra σ_c = max(6 ℓ, 24 px), 4× l'àrea de la finestra del soroll perquè
l'estimador no faci taques), guarda = sqrt(E_V E_S)/sqrt(N_ef) (1 σ de l'estimador: on no hi ha res compartit, C oscil·la al voltant de zero i
sense guarda el max(C,0) deixaria passar soroll a taques), E_F = <b_F²> de la banda fusionada que el filtre toca. El guany final del filtre és
max(g_Auchère, g_c): el llindar protegeix el compacte (porta A3b), el creuat protegeix el difús confirmat pels dos trens. Només on tots dos trens
tenen suport; enlloc més no canvia res. Les injeccions de l'A3b entren només a la fusió (no a V ni a S) → el terme creuat no les veu → l'A3b
continua sent una cota inferior vàlida.

Imatges per tren en UNITATS DE LA FUSIÓ (b3_fusio V38: fusió = w_V·V·e^{−δ} + w_S·S·ρ): V = vixen_total_v38·e^{−δ}, S = sony_corrected_total_v36·ρ."""
import numpy as np, cv2
from pathlib import Path
from scipy.ndimage import gaussian_filter
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[2]   # sense comu39: b4c (v31_purs) no té el sys.path de la cadena comu38→f2
CAU38 = ROOT / 'research/tools/v38_20260908/cau'; CAUF = ROOT / 'research/tools/v29/cau_final'; CAU36_ = ROOT / 'research/tools/v36_20260908/cau'; CAU39 = HERE / 'cau'
CX, CY, RS = 5361.768111973117, 3775.747534140857, 440.60304883027544   # geometria del llenç (comu)


def down4(x):
    h, w = x.shape; hh, ww = h // 4 * 4, w // 4 * 4
    return x[:hh, :ww].reshape(hh // 4, 4, ww // 4, 4).mean(axis=(1, 3)).astype(np.float32)


class Creuat:
    def __init__(self, canal, sigma_factor=6.0, sigma_min=24.0, z=1.0, log=print):
        self.c = canal; self.sf = sigma_factor; self.smin = sigma_min; self.z = z; self.log = log; self.stats = {}
        V = np.load(CAU38 / 'vixen_total_v38.npy', mmap_mode='r'); S = np.load(CAU36_ / 'sony_corrected_total_v36.npy', mmap_mode='r')
        d = np.asarray(np.load(CAU38 / 'delta_v38.npy', mmap_mode='r')[..., canal], np.float32); rho = np.asarray(np.load(CAU38 / 'rho_v38.npy', mmap_mode='r')[..., canal], np.float32)
        v = np.asarray(V[..., canal], np.float32); s = np.asarray(S[..., canal], np.float32)
        self.mV = np.load(CAUF / 'vixen_support.npy') & np.isfinite(v) & (v > 0); self.mS = np.isfinite(s) & (s > 0)
        wv = np.nan_to_num(np.asarray(np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r'), np.float32)); self.mS &= (1 - wv) > 0.02; self.mV &= wv > 0.02   # només on el tren ENTRA a la fusió
        self.V = np.where(self.mV, v * np.exp(-np.nan_to_num(d)), 0).astype(np.float32); self.S = np.where(self.mS, s * np.nan_to_num(rho, nan=1.0), 0).astype(np.float32); del v, s, d, rho, wv
        self.m2 = self.mV & self.mS; self.log(f'creuat canal {canal}: suport comú {int(self.m2.sum())} px (V {int(self.mV.sum())}, S {int(self.mS.sum())})')
        wv_ = np.nan_to_num(np.asarray(np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r'), np.float32)); self._wv4 = down4(wv_); z0 = np.load(CAU39 / 'soroll_escales_1q.npz'); self._sV4 = z0['vixen_suport4'] > 0.5; self._sS4 = z0['sony_suport4'] > 0.5; del wv_
        import json as _j; self.mode = _j.loads((HERE / 'cau/tau.json').read_text()).get('creuat_mode', 'guany') if (HERE / 'cau/tau.json').exists() else 'guany'
        self.cx, self.cy, self.rs = CX, CY, RS; self.ref = _j.loads((HERE / 'cau/tau.json').read_text()).get('soroll_ref', 'sony') if (HERE / 'cau/tau.json').exists() else 'sony'

    def soroll_total(self, bV, bS, bF, mF, ell, NV4, NS4, nivell=None, tag=''):
        """V40 · MODEL DE SOROLL TOTAL per tren (estimador del 31-08, research/127 §8: potència total − potència creuada entre sensors), no un guany.
        Al solapament: N_V = max(E_V − C, N_V,meitats), N_S = max(E_S − C, N_S,meitats) amb C = ⟨b_V·b_S⟩ (el que els dos sensors veuen alhora: corona + cel;
        el que no és compartit —gra, patrons fixos, ratllat, arcs d'un tren— compta com a soroll). Fora del solapament, el soroll de meitats de cada tren es
        multiplica pel quocient (N_total/N_meitats) MEDIÀ del seu anell radial al solapament (calibratge per anell, continu en r). Fusió amb els pesos V38
        (w_V² N_V + w_S² N_S). Finestra σ_c = max(6ℓ, 24 px); suport comú eroditat 3ℓ per no fabricar coherència a les vores (omplert per la finestra
        normalitzada). `nivell`: si els coeficients són lineals i N de meitats és en ln, N_meitats·nivell²."""
        m2 = self.m2 & mF
        if not hasattr(self, '_dt2'): self._dt2 = cv2.distanceTransform(self.m2.astype(np.uint8), cv2.DIST_L2, 5)
        m2e = m2 & (self._dt2 >= 3 * float(ell)); m4 = down4(m2e.astype(np.float32)); sc = max(self.sf * float(ell), self.smin) / 4.0
        def W(x):
            return gaussian_filter(down4(np.where(m2e, x, 0).astype(np.float32)) * m4, sc) / np.maximum(gaussian_filter(m4, sc), 1e-6)
        C = np.maximum(W(bV * bS), 0); EV = W(bV * bV); ES = W(bS * bS); ok = gaussian_filter(m4, sc) > 0.02
        h4, w4 = C.shape; NV = np.asarray(NV4[:h4, :w4], np.float32); NS = np.asarray(NS4[:h4, :w4], np.float32)
        if nivell is not None:
            L4 = down4(np.maximum(nivell, 0).astype(np.float32))[:h4, :w4] ** 2; NV = NV * L4; NS = NS * L4
        NVt = np.where(ok, np.maximum(EV - C, NV), NV); NSt = np.where(ok, np.maximum(ES - C, NS), NS)
        # calibratge per anell fora del solapament: quocient medià N_total/N_meitats al solapament del mateix anell
        if not hasattr(self, '_r4'):
            H_, W_ = mF.shape; yy, xx = np.mgrid[0:h4, 0:w4]; self._r4 = np.hypot((xx * 4 + 2) - self.cx, (yy * 4 + 2) - self.cy) / self.rs
        rb = np.clip((self._r4 / 0.1).astype(int), 0, 200); kV = np.ones(201, np.float32); kS = np.ones(201, np.float32)
        for i in range(201):
            sel = ok & (rb == i) & (NV > 0) & (NS > 0)
            if sel.sum() > 200: kV[i] = float(np.median(NVt[sel] / NV[sel])); kS[i] = float(np.median(NSt[sel] / NS[sel]))
        # anells sense solapament: el valor de l'anell veí més proper amb solapament
        for k_ in (kV, kS):
            idx = np.where(k_ != 1.0)[0]
            if len(idx):
                for i in range(201):
                    if k_[i] == 1.0: k_[i] = k_[idx[np.argmin(np.abs(idx - i))]]
        NVt = np.where(ok, NVt, NV * kV[rb]); NSt = np.where(ok, NSt, NS * kS[rb])
        wv4 = self._wv4[:h4, :w4]; sV = self._sV4[:h4, :w4]; sS = self._sS4[:h4, :w4]
        if getattr(self, 'ref', 'sony') == 'sony':
            # V40: soroll de REFERÈNCIA = el de la SONY allà on la Sony hi és (cobreix tot l'exterior i és continu a través del rectangle de la Vixen:
            # cap contorn de tren), i el de la Vixen només a l'interior on la Sony no arriba. El coeficient de la fusió conserva l'avantatge del segon tren.
            # (Provat: 'pitjor tren' = max(N_V, N_S) feia un clot a la franja d'entrada de la Vixen, on la Vixen pesa poc però hi és molt sorollosa.)
            n4 = np.where(sS, NSt, NVt)
        elif getattr(self, 'ref', 'sony') == 'pitjor':
            n4 = np.where(sV & sS, np.maximum(NVt, NSt), np.where(sV, NVt, NSt))
        else:
            n4 = np.where(sV, wv4 * wv4 * NVt, 0) + np.where(sS, (1 - wv4) ** 2 * NSt, 0); n4 = np.where(sV & ~sS, NVt, n4); n4 = np.where(sS & ~sV, NSt, n4)
        H_, W_ = bF.shape; full = cv2.resize(n4.astype(np.float32), (w4 * 4, h4 * 4), interpolation=cv2.INTER_LINEAR)
        out = np.zeros((H_, W_), np.float32); hh, ww = min(H_, full.shape[0]), min(W_, full.shape[1]); out[:hh, :ww] = full[:hh, :ww]; out[hh:, :ww] = out[hh - 1:hh, :ww]; out[:, ww:] = out[:, ww - 1:ww]
        coh = float(np.median((C / np.maximum(np.sqrt(EV * ES), 1e-30))[ok])) if ok.any() else float('nan')
        self.stats[tag or str(ell)] = {'coherencia_mediana': coh, 'quocient_total_meitats_V_median': float(np.median(kV)), 'quocient_total_meitats_S_median': float(np.median(kS)), 'sigma_c_px': sc * 4}
        self.log(f'  soroll total {tag} ℓ={ell:g}: coherència mediana {coh:.3f} · N_total/N_meitats medià V {np.median(kV):.2f} S {np.median(kS):.2f}'); del C, EV, ES, full
        return np.maximum(out, 0)

    def guany(self, bV, bS, bF, mF, ell, tag=''):
        """Guany creuat a resolució plena (0 fora del suport comú). bV, bS, bF: coeficients de la mateixa escala dels dos trens i de la fusió."""
        m2 = self.m2 & mF; m4 = down4(m2.astype(np.float32)); sc = max(self.sf * float(ell), self.smin) / 4.0
        def W(x):
            return gaussian_filter(down4(np.where(m2, x, 0).astype(np.float32)) * m4, sc) / np.maximum(gaussian_filter(m4, sc), 1e-6)
        C = W(bV * bS); EV = W(bV * bV); ES = W(bS * bS); EF = W(bF * bF)
        neff = 2.0 * (sc * 4.0) ** 2 / max(float(ell), 1.0) ** 2; guard = self.z * np.sqrt(np.maximum(EV * ES, 0)) / np.sqrt(neff)
        g4 = np.clip(np.maximum(C - guard, 0) / np.maximum(EF, 1e-30), 0, 1); g4 = np.where(m4 > 0.5, g4, 0).astype(np.float32)
        H_, W_ = bF.shape; full = cv2.resize(g4, (g4.shape[1] * 4, g4.shape[0] * 4), interpolation=cv2.INTER_LINEAR)
        g = np.zeros((H_, W_), np.float32); hh, ww = min(H_, full.shape[0]), min(W_, full.shape[1]); g[:hh, :ww] = full[:hh, :ww]; g[hh:, :ww] = g[hh - 1:hh, :ww]; g[:, ww:] = g[:, ww - 1:ww]
        g = np.where(m2, g, 0).astype(np.float32); coh = float(np.median((C / np.maximum(np.sqrt(EV * ES), 1e-30))[m4 > 0.5])) if (m4 > 0.5).any() else float('nan')
        self.stats[tag or str(ell)] = {'g_creuat_mitja_suport_comu': float(np.mean(g[m2])), 'coherencia_mediana': coh, 'sigma_c_px': sc * 4, 'n_ef': neff}
        self.log(f'  creuat {tag} ℓ={ell:g}: g_c mitjà {float(np.mean(g[m2])):.3f} · coherència mediana {coh:.3f}'); del C, EV, ES, EF, g4, full
        return g
