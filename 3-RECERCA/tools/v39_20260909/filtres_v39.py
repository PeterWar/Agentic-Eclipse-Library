"""filtres_v39 · Els mateixos operadors de la V31 purs / cadena V29 (WOW à trous B3 amb i sense bilateral, MGN, ACHF) amb UNA sola diferència
causal: cada coeficient d'escala s es multiplica per un guany de Wiener local g_s(x) = clip(1 − τ·N_s(x)/E_s(x), 0, 1) ABANS de la normalització/tanh,
amb N_s l'energia de soroll MESURADA (meitats independents, A2 V39) i E_s l'energia local del coeficient; log(E_s/N_s) suavitzat una vegada amb
σ_E = max(3 ℓ_s, 8 px) (convolució normalitzada al suport). τ = 0 reprodueix exactament l'operador de la V38.
Variant 'auchere': atenuació suau per coeficient w·erf(|w|/(√2·k·σ_s)) (Auchère et al. 2023, denoise) amb σ_s = sqrt(N_s) local.
DECISIÓ V39 (cau/tau.json): mode auchere k=2 + terme CREUAT entre trens (creuat_v39.Creuat: potència compartida Vixen×Sony per escala i regió,
sorolls independents); guany final = max(g_Auchère, g_creuat). El llindar protegeix el compacte (A3b), el creuat protegeix el difús que els dos
telescopis confirmen (C3b). El soroll N_s ve de meitats amb els 16 px de la vora del forat lunar exclosos (comu39.lluny_del_forat)."""
import sys
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter, convolve1d
from scipy.special import erf
HERE = Path(__file__).resolve().parent
K = np.array([1, 4, 6, 4, 1], np.float32) / 16
import os as _os0
SE_FACTOR = float(_os0.environ.get('FILTRES_V39_SE_FACTOR', '3.0')); SE_MIN = float(_os0.environ.get('FILTRES_V39_SE_MIN', '8.0'))   # finestra de l'energia local: σ_E = clip(SE_FACTOR·ℓ, SE_MIN, 256)
MODE = _os0.environ.get('FILTRES_V39_MODE', 'wiener'); KSOFT = float(_os0.environ.get('FILTRES_V39_K', '3.0'))
KLO = float(_os0.environ.get('FILTRES_V39_KLO', '1.5')); KHI = float(_os0.environ.get('FILTRES_V39_KHI', '3.0'))   # mode 'adapt': k(x) = KLO + (KHI−KLO)·clip(N/E_regional, 0, 1)
import json as _json0
_tj = HERE / 'cau/tau.json'
if _tj.exists():   # la decisió (A3) mana sobre l'entorn: mateixos paràmetres a b4a, b4c i c3
    _d = _json0.loads(_tj.read_text()); SE_FACTOR = float(_d.get('se_factor', SE_FACTOR)); SE_MIN = float(_d.get('se_min', SE_MIN)); MODE = _d.get('mode', MODE); KSOFT = float(_d.get('k', KSOFT)); KLO = float(_d.get('k_lo', KLO)); KHI = float(_d.get('k_hi', KHI))
CREUAT = bool(_json0.loads(_tj.read_text()).get('creuat', False)) if _tj.exists() else False
CREUAT_MODE = (_json0.loads(_tj.read_text()).get('creuat_mode', 'guany') if _tj.exists() else 'guany')   # 'guany' (V39: max amb g_creuat) | 'soroll' (V40: N = potència total − creuada, per tren)
_dc = _json0.loads(_tj.read_text()) if _tj.exists() else {}; CREUAT_SF = float(_dc.get('creuat_sigma_factor', 6.0)); CREUAT_SMIN = float(_dc.get('creuat_sigma_min', 24.0)); CREUAT_Z = float(_dc.get('creuat_z', 1.0))
# à trous amb la dylib dispersa de v31_purs (sparse_conv): idèntica al filter2D dilatat de l'autor i ràpida a les escales grans
import os as _os; _os.environ.setdefault('V29_FINAL_GRID', '1')
_PURS = HERE.parent / 'v31_purs'
if str(_PURS) not in sys.path: sys.path.insert(0, str(_PURS))
import common as _vc
if not hasattr(_vc, 'D') or not (Path(str(_vc.D)) / 'sparse_conv.dylib').exists(): _vc.D = HERE / 'purs'
if not hasattr(_vc, 'C'): _vc.C = HERE / 'purs/cau'
import wow_filters as _wf


class Soroll:
    """Mapes de soroll per escala (1/4 de resolució, A2) fusionats amb els pesos V38; retorna N_s a resolució completa en unitats de ln."""
    def __init__(self, npz, wv_full):
        self.z = dict(np.load(npz)); self.wv4 = self._down4(np.nan_to_num(wv_full.astype(np.float32))); self.cache = {}; self.dispersio = {}
        def fusiona(z1, p2, etiqueta):   # V40: si hi ha la segona partició (pAB), N = mitjana de les dues; dispersió mediana |N1−N2|/(N1+N2) anotada
            if not Path(p2).exists(): return z1
            z2 = dict(np.load(p2)); out = dict(z1)
            for k in z1:
                if k in z2 and z1[k].shape == z2[k].shape and 'suport' not in k:
                    a, b = z1[k], z2[k]; ok = (a > 0) & (b > 0); self.dispersio[f'{etiqueta}:{k}'] = float(np.median(np.abs(a[ok] - b[ok]) / (a[ok] + b[ok]))) if ok.any() else None; out[k] = 0.5 * (a + b)
            return out
        self.z = fusiona(self.z, Path(npz).with_name(Path(npz).stem + '_pAB.npz'), 'G')
        self.zc = {}
        for c in (0, 2):   # soroll per canal R/B (A2c) per a l'ACHF; G = el general
            pc = Path(npz).parent / f'soroll_escales_1q_c{c}.npz'
            if pc.exists(): self.zc[c] = fusiona(dict(np.load(pc)), Path(npz).parent / f'soroll_escales_1q_c{c}_pAB.npz', f'c{c}')
        pb = Path(npz).parent / 'soroll_bilateral_1q.npz'
        if pb.exists():
            zb = fusiona({k: v for k, v in dict(np.load(pb)).items() if 'bilat' in k}, Path(npz).parent / 'soroll_bilateral_1q_pAB.npz', 'bilat'); self.z.update(zb); self.te_bilateral = True
        else:
            self.te_bilateral = False
        self.sV = self.z['vixen_suport4'] > 0.5; self.sS = self.z['sony_suport4'] > 0.5
    @staticmethod
    def _down4(x):
        h, w = x.shape; hh, ww = h // 4 * 4, w // 4 * 4; return x[:hh, :ww].reshape(hh // 4, 4, ww // 4, 4).mean(axis=(1, 3)).astype(np.float32)
    def N(self, key, shape, canal=None):
        if canal in (0, 2) and canal in self.zc and f'vixen_{key}' in self.zc[canal]:
            ck = f'c{canal}_{key}'
            if ck not in self.cache:
                z0 = self.z; self.z = {**self.z, **self.zc[canal]}; self.cache[ck] = self._fuse(key, shape); self.z = z0
            return self.cache[ck]
        if key not in self.cache:
            if f'vixen_{key}' not in self.z and key.startswith('dog'):   # escala no mesurada (p. ex. σ48): interpolació log-log entre les escales veïnes mesurades
                sc = float(key[3:]); avail = sorted(float(k[len('vixen_dog'):]) for k in self.z if k.startswith('vixen_dog'))
                lo = max([a for a in avail if a <= sc], default=avail[0]); hi = min([a for a in avail if a >= sc], default=avail[-1]); t = 0.0 if hi == lo else (np.log(sc) - np.log(lo)) / (np.log(hi) - np.log(lo))
                for tren in ('vixen', 'sony'):
                    A = np.log(np.maximum(self.z[f'{tren}_dog{lo:g}'], 1e-30)); B = np.log(np.maximum(self.z[f'{tren}_dog{hi:g}'], 1e-30)); self.z[f'{tren}_{key}'] = np.exp((1 - t) * A + t * B).astype(np.float32)
            self.cache[key] = self._fuse(key, shape)
        return self.cache[key]
    def per_tren(self, key, canal=None):
        """(N_V, N_S) a 1/4 de resolució per a la clau (canal R/B si escau), amb les particions ja fusionades; per al model de soroll total (creuat_v39)."""
        z = self.z
        if canal in (0, 2) and canal in self.zc and f'vixen_{key}' in self.zc[canal]: z = {**self.z, **self.zc[canal]}
        if f'vixen_{key}' not in z and key.startswith('dog'): self.N(key, (1, 1), canal=canal); z = self.z if canal not in (0, 2) else {**self.z, **self.zc.get(canal, {})}
        return np.maximum(z[f'vixen_{key}'], 0), np.maximum(z[f'sony_{key}'], 0)
    def _fuse(self, key, shape=None):
        NV = self.z[f'vixen_{key}']; NS = self.z[f'sony_{key}']; wv = self.wv4
        n4 = np.where(self.sV, wv * wv * NV, 0) + np.where(self.sS, (1 - wv) ** 2 * NS, 0)
        n4 = np.where(self.sV & ~self.sS, NV, n4); n4 = np.where(self.sS & ~self.sV, NS, n4)   # on només hi ha un tren, el seu soroll sencer
        import cv2
        H, W = shape if shape is not None else (n4.shape[0] * 4, n4.shape[1] * 4); full = cv2.resize(n4.astype(np.float32), (n4.shape[1] * 4, n4.shape[0] * 4), interpolation=cv2.INTER_LINEAR)
        out = np.zeros((H, W), np.float32); hh, ww = min(H, full.shape[0]), min(W, full.shape[1]); out[:hh, :ww] = full[:hh, :ww]
        out[hh:, :ww] = out[hh - 1:hh, :ww]; out[:, ww:] = out[:, ww - 1:ww]; return np.maximum(out, 0)


def ng(x, m, s):
    w = m.astype(np.float32); return gaussian_filter(np.where(m, x, 0) * w, s) / np.maximum(gaussian_filter(w, s), 1e-6)


def guany(coef, m, N_coef, ell, tau, mode=None, k=None):
    mode = MODE if mode is None else mode; k = KSOFT if k is None else k
    """g_s(x): 'wiener' → clip(1 − τ N/E) amb E = energia local de coef (σ_E = max(3ℓ, 8)); log(E/N) suavitzat un cop. 'auchere' → erf(|w|/(√2 k σ))."""
    if tau <= 0:
        return np.ones_like(coef)
    if mode == 'auchere':
        sig = np.sqrt(np.maximum(N_coef, 1e-30)); return np.where(m, erf(np.abs(coef) / (np.sqrt(2.0) * k * tau * sig)), 0).astype(np.float32)
    if mode == 'wg':   # V40: max(Wiener REGIONAL, garrote per coeficient). g_W = clip(1 − N/E, 0, 1) amb E l'energia regional del coeficient (σ_E = max(3ℓ, 8)):
        # on la banda és 95 % soroll val 0,05 (el gra desapareix), on és senyal val 1. g_G = max(0, 1 − (kσ)²/w²) protegeix el compacte fort (5 σ 0,64, 7 σ 0,82).
        # Residu de soroll pur ≈ 0,06 (contra 0,58 del llindar tou k=2 de la V39). Codex xhigh 09-09: regla acordada; el creuat deixa de ser guany.
        sE = min(max(SE_FACTOR * ell, SE_MIN), 256.0); E = ng(coef * coef, m, sE); ratio = ng(np.log(np.maximum(E, 1e-30) / np.maximum(N_coef, 1e-30)), m, sE)   # log(E/N) suavitzat un cop (contra els pedaços)
        gW = np.clip(1.0 - tau * np.exp(-ratio), 0.0, 1.0)
        gG = np.clip(1.0 - (k * tau) ** 2 * np.maximum(N_coef, 0) / np.maximum(coef * coef, 1e-30), 0.0, 1.0)
        return np.where(m, np.maximum(gW, gG), 0).astype(np.float32)
    if mode == 'adapt':   # llindar tou per coeficient amb k que segueix el S/N REGIONAL: k baix on domina l'estructura, alt on domina el soroll
        sE = min(max(SE_FACTOR * ell, SE_MIN), 256.0); E = ng(coef * coef, m, sE); frac = np.clip(np.exp(-ng(np.log(np.maximum(E, 1e-30) / np.maximum(N_coef, 1e-30)), m, sE)), 0, 1)
        kx = KLO + (KHI - KLO) * frac; sig = np.sqrt(np.maximum(N_coef, 1e-30)); return np.where(m, erf(np.abs(coef) / (np.sqrt(2.0) * kx * tau * sig)), 0).astype(np.float32)
    sE = min(max(SE_FACTOR * ell, SE_MIN), 256.0); E = ng(coef * coef, m, sE); ratio = np.log(np.maximum(E, 1e-30) / np.maximum(N_coef, 1e-30))
    ratio = ng(ratio, m, sE)   # suavitzat una vegada de log(E/N)
    g = np.clip(1.0 - tau * np.exp(-ratio), 0.0, 1.0); return np.where(m, g, 0).astype(np.float32)


# ---------- WOW (Auchère 2023) com a wow_filters.wow, amb el guany
def atrous_conv(a, s):
    return _wf.conv(np.ascontiguousarray(a, np.float32), s)


def nconv(a, m, s):
    return atrous_conv(np.where(m, a, 0).astype(np.float32), s) / np.maximum(atrous_conv(m.astype(np.float32), s), 1e-20)


def bilateral_conv(a, m, s):
    return _wf.bilateral_conv(a, m, s)   # mateix bilateral (equació 18), mateixa dylib


def wow_v39(a, m, n_scales, bilateral, soroll, tau, mode=None, log=print, gains_out=None, creuat=None):
    c = np.where(m, a, 0).astype('float32'); out = np.zeros_like(c)
    if creuat is not None: cV = np.where(m, creuat.aV, 0).astype('float32'); cS = np.where(m, creuat.aS, 0).astype('float32')   # els dos trens, mateixa descomposició
    for s in range(n_scales):
        nxt = bilateral_conv(c, m, s) if bilateral else nconv(c, m, s)
        wave = c - nxt; wave[np.abs(wave) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(c), np.abs(nxt))] = 0
        power = nconv(wave * wave, m, s); amp = np.sqrt(np.maximum(power, 1e-20))
        if tau > 0 and soroll is not None:
            key = f'bilat{s}' if (bilateral and getattr(soroll, 'te_bilateral', False)) else f'atrous{s}'
            N_ln = soroll.N(key, a.shape); N_lin = N_ln * np.maximum(nxt, 0) ** 2      # soroll en unitats lineals: relatiu × nivell local (bilateral: mesurat amb el bilateral sencer, A4)
            if creuat is not None and getattr(creuat, 'mode', 'guany') == 'soroll':   # V40: soroll TOTAL per tren (auto − creuat) en lloc del de les meitats
                nV = bilateral_conv(cV, m, s) if bilateral else nconv(cV, m, s); nS = bilateral_conv(cS, m, s) if bilateral else nconv(cS, m, s); NV4, NS4 = soroll.per_tren(key)
                N_lin = creuat.soroll_total(cV - nV, cS - nS, wave, m, float(2 ** s), NV4, NS4, nivell=np.maximum(nxt, 0), tag=('wowb' if bilateral else 'wow') + str(s)); cV = np.where(m, nV, 0); cS = np.where(m, nS, 0); del nV, nS
            g = guany(wave, m, N_lin, float(2 ** s), tau, mode)
            if creuat is not None and getattr(creuat, 'mode', 'guany') != 'soroll':
                nV = bilateral_conv(cV, m, s) if bilateral else nconv(cV, m, s); nS = bilateral_conv(cS, m, s) if bilateral else nconv(cS, m, s)
                g = np.maximum(g, creuat.guany(cV - nV, cS - nS, wave, m, float(2 ** s), tag=('wowb' if bilateral else 'wow') + str(s))); cV = np.where(m, nV, 0); cS = np.where(m, nS, 0); del nV, nS
            if gains_out is not None: gains_out[s] = g
        else:
            g = 1.0
        out += g * wave / amp; c = np.where(m, nxt, 0)
        log(('WOW bilateral ' if bilateral else 'WOW ') + 'scale ' + str(s) + (f' · g mitjà {float(np.mean(g[m])):.3f}' if tau > 0 else ''))
        del wave, power, amp
    sd = float(np.std(c[m], dtype='float64'))
    if sd > 16 * np.finfo('float32').eps * float(np.max(np.abs(c[m]))): out += c / sd
    return out


# ---------- MGN (Morgan & Druckmüller 2014) com a local_filters.mgn, amb el guany sobre cada terme local
def mgn_v39(a, m, soroll, tau, sigmas=(1.25, 2.5, 5, 10, 20, 40), k=.7, h=.7, gamma=3.2, limits=None, mode=None, log=print, gains_out=None, creuat=None):
    """V39: el passa-alt d_s = a − G_s(a) de cada terme es descompon en BANDES entre σ consecutives (b_1 = a − G_{s1} a; b_j = G_{s_{j−1}} a − G_{s_j} a) i el
    guany (Auchère amb el soroll de la banda, clau bpmgn, i el creuat entre trens) s'aplica a cada banda: d_guanyat = Σ_j g_j b_j. Amb g ≡ 1 és exactament
    l'operador de la V38 (a − G_s a). Motiu: un passa-alt barreja el gra fi amb l'estructura gran; per banda, la banda gran confirmada pels dos trens es
    conserva i la fina que és soroll s'atenua. La normalització (den) es calcula amb el passa-alt SENSE guany, com abans."""
    lo, hi = limits or (float(np.min(a[m])), float(np.max(a[m])))
    if hi <= lo: return np.zeros_like(a, dtype='float32')
    detail = np.zeros_like(a, dtype='float32'); prev = np.where(m, a, 0).astype('float32'); dg = np.zeros_like(prev)
    if creuat is not None: aV = np.where(m, np.maximum(creuat.aV, 0), 0).astype('float32'); aS = np.where(m, np.maximum(creuat.aS, 0), 0).astype('float32'); prevV = aV; prevS = aS
    for j, s in enumerate(sigmas):
        mu = ng(a, m, s); d = a - mu
        d[np.abs(d) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(a), np.abs(mu))] = 0
        den = np.sqrt(ng(d * d, m, s)); bp = prev - mu
        if tau > 0 and soroll is not None:
            key = f'bpmgn{s:g}' if (j > 0 and f'vixen_bpmgn{s:g}' in soroll.z) else f'dog{s:g}'   # primera banda = passa-alt sencer (dog); les altres, la banda mesurada
            if creuat is not None and getattr(creuat, 'mode', 'guany') == 'soroll':
                muV = ng(aV, m, s); muS = ng(aS, m, s); NV4, NS4 = soroll.per_tren(key)
                N_lin = creuat.soroll_total(prevV - muV, prevS - muS, bp, m, float(s), NV4, NS4, nivell=np.maximum(mu, 0), tag=f'mgn{s:g}'); prevV = muV; prevS = muS; g = guany(bp, m, N_lin, float(s), tau, mode)
            else:
                N_lin = soroll.N(key, a.shape) * np.maximum(mu, 0) ** 2; g = guany(bp, m, N_lin, float(s), tau, mode)
                if creuat is not None:
                    muV = ng(aV, m, s); muS = ng(aS, m, s); g = np.maximum(g, creuat.guany(prevV - muV, prevS - muS, bp, m, float(s), tag=f'mgn{s:g}')); prevV = muV; prevS = muS
            if gains_out is not None: gains_out[s] = g
            dg = dg + bp * g; gm = float(np.mean(g[m])); del g
        else:
            dg = dg + bp; gm = 1.0
        z = np.divide(dg, den, out=np.zeros_like(dg), where=den > 0)
        detail += np.arctan(k * z) / len(sigmas); prev = mu; log('MGN sigma ' + str(s) + (f' · g mitjà {gm:.3f} (banda {key})' if tau > 0 and soroll is not None else ''))
        del d, den, bp, z
    global_term = np.clip((a - lo) / (hi - lo), 0, 1) ** (1 / gamma) if hi > lo else np.zeros_like(a)
    return h * global_term + (1 - h) * detail


# ---------- ACHF (cadena V29 fuse_and_filter.achf): out += (x − G_s(x))/n, amb el guany per escala
def achf_v39(x, w, sigmas, soroll, tau, mode=None, log=print, gains_out=None, canal=None, creuat=None):
    """V39: out = Σ_s hp_s/n amb hp_s = Σ_{j≤s} g_j b_j (bandes entre σ consecutives de la llista; la primera = x − G_{s1} x, soroll dog; les altres, soroll
    bpachf mesurat). Amb g ≡ 1 és exactament (x − G_s x) i l'operador V29/V38."""
    m = w > 0; out = np.zeros_like(x); sig = sorted(sigmas); prev = np.where(m, x, 0).astype(np.float32); hp = np.zeros_like(prev)
    for j, s in enumerate(sig):
        sm = ng(x, m, s); bp = prev - sm
        if tau > 0 and soroll is not None:
            key = f'bpachf{s:g}' if (j > 0 and f'vixen_bpachf{s:g}' in soroll.z) else f'dog{s:g}'
            g = guany(bp, m, soroll.N(key, x.shape, canal=canal), float(s), tau, mode)
            if gains_out is not None: gains_out[s] = g
            hp = hp + bp * g; log(f'ACHF σ{s} · g mitjà {float(np.mean(g[m])):.3f} (banda {key})')
        else:
            hp = hp + bp
        out += hp / len(sig); prev = sm
    return np.where(m, out, 0).astype(np.float32)
