"""Resolució que segueix el S/N (V33): σ(x) = max(σ_mapa, σ_local).
  σ_mapa: del mapa C0 (coherència entre trens per tessel·les): σ = λ_mín/4 (transferència 0,29 a la
          banda coherent més fina, 0,73 al doble), 32 px si cap banda fins a 256 px és coherent; suavitzat
          128 px; a l'interior (r < 2,0) σ fixa 0,7 com la V29, rampa fins a 2,65.
  σ_local: f3.suavitza_sn autocalibrat sobre la capa (t 0,18): els graons de gra fi locals.
Aplicació: piràmide gaussiana normalitzada al suport, barreja contínua en log2 σ (cap llindar, cap radi)."""
import sys, numpy as np, cv2
from pathlib import Path
ROOT = Path('/Users/USUARI/Downloads/Eclipse 2026'); sys.path.insert(0, str(ROOT / 'research/tools/eclipse_determinista'))
import f3
MAP = ROOT / 'research/tools/v33_20260907/cau/resolucio_v33.npy'
SMAX, T_SN, DIV = 32.0, 0.18, 4.0
SIG_IN, R_IN0, R_IN1, MAP_SMOOTH = 0.7, 2.0, 2.65, 128.0   # interior: σ fixa 0,7 (com la V29: les tessel·les de 512 px no mesuren la corona interior amb la Lluna dins); rampa 2,0→2,65; mapa suavitzat 128 px
LEVELS = [0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0]


def gn(a, w, s):
    k = 2 * int(3 * s + .5) + 1
    return cv2.GaussianBlur(a * w, (k, k), s, borderType=cv2.BORDER_REPLICATE) / np.maximum(cv2.GaussianBlur(w, (k, k), s, borderType=cv2.BORDER_REPLICATE), 1e-8)


_MAP = None
def sigma_map():
    global _MAP
    if _MAP is None:
        full = np.minimum(np.load(MAP) / 0.073058 / DIV, SMAX).astype(np.float32)
        k = 2 * int(3 * MAP_SMOOTH + .5) + 1; full = cv2.GaussianBlur(full, (k, k), MAP_SMOOTH, borderType=cv2.BORDER_REPLICATE)
        H, W = full.shape; CX, CY, RS = 5361.768111973117, 3775.747534140857, 440.60304883027544
        y, x = np.ogrid[:H, :W]; r = np.hypot(x - CX, y - CY) / RS; t = np.clip((r - R_IN0) / (R_IN1 - R_IN0), 0, 1); sw = (t * t * (3 - 2 * t)).astype(np.float32)
        _MAP = ((1 - sw) * SIG_IN + sw * full).astype(np.float32)
    return _MAP


def apply_sigma(F0, w, sig):
    ls = np.array([np.log2(s / 0.5) for s in LEVELS], np.float32)
    lev = np.where(sig > 0, np.log2(np.maximum(sig, 0.5) / 0.5), 0).astype(np.float32)
    li = np.clip(np.searchsorted(ls, lev) - 1, 0, len(LEVELS) - 2); frac = np.clip((lev - ls[li]) / np.maximum(ls[li + 1] - ls[li], 1e-9), 0, 1).astype(np.float32)
    out = np.zeros_like(F0); prev = F0
    for i in range(len(LEVELS) - 1):
        nxt = gn(F0, w, LEVELS[i + 1]); k = li == i
        if k.any():
            out[k] = prev[k] * (1 - frac[k]) + nxt[k] * frac[k]
        prev = nxt
    return np.where(sig >= 0.7, out, F0)


def sn_v33(F, m, smax=SMAX):
    F0 = np.where(m, F, 0).astype(np.float32); w = m.astype(np.float32)
    _, sloc = f3.suavitza_sn(F0, m, t=T_SN, smax=smax)
    sig = np.maximum(sloc.astype(np.float32), sigma_map()); sig[~m] = 0
    return np.where(m, apply_sigma(F0, w, sig), 0).astype(np.float32), sig
