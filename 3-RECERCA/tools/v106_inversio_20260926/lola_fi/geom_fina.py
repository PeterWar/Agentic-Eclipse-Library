"""geom_fina (V106, «LOLA fi», Claude, 26-09-2026) · La «vora fina»: el limbe real de cada fotograma al llenç.
r_L,j(θ) = R + e_o2(θ) [silueta D21] + a_j + b_j·cos θ + c_j·sin θ [radi i centre del fotograma, mesurats a la seva vora]
           + Σ_{n=2,3} [p_n + q_n·(t_j − t0)]·(cos nθ, sin nθ) [refracció comuna, lenta]  + h_LOLA64(θ − θN) ⊗ g(σ_arc) [relleu]
           (+ opcional: ε_j(θ) = residu propi del fotograma suavitzat, variant «propi»)
θ: angle del llenç al voltant del centre del MODEL del fotograma (0 = dreta, 90 = amunt), igual que la silueta D21.
D_fina_j(x) = |x − C_j| − r_L,j(θ_x), amb C_j el centre del model (distance_model). Per a la transmissió amb PSF de dues gaussianes, el relleu es
suavitza al llarg de l'arc amb la σ de cada component (primer ordre de la convolució 2D): D_core (σ 1,25 px) i D_ala (σ 2,5 px).
Ús: from geom_fina import G; D = G.dfina(j, X, Y, sig_px=1.25, variant='lola')"""
import numpy as np, json
from pathlib import Path
from scipy.ndimage import gaussian_filter1d
H = Path(__file__).parent
class Geometria:
    def __init__(self, path=H / 'GEOMETRIA_FINA.npz'):
        Z = np.load(path, allow_pickle=True); self.Z = Z
        for k in Z.files: setattr(self, k, Z[k])
        self.R = float(self.R); self.thN = float(self.thN); self.k = float(self.k); self.t0 = float(self.t0)
        self._cache = {}
    def relleu(self, sig_px):
        """Relleu LOLA-64 (px) al llenç en una graella de 0,01°, suavitzat al llarg de l'arc amb σ (px)."""
        key = round(float(sig_px), 3)
        if key not in self._cache:
            h = self.h_lola_001.astype(np.float64)
            if sig_px > 0: h = gaussian_filter1d(h, sig_px / (self.R * np.pi / 180) / 0.01, mode='wrap')
            self._cache[key] = self.k * h
        return self._cache[key]
    def rL(self, j, th_deg, sig_px=1.25, variant='lola'):
        th = np.asarray(th_deg, np.float64) % 360; tr = np.radians(th)
        a, b, c = self.pf[j]; tj = self.t[j] - self.t0; pc = self.comuns
        r = self.R + np.interp(th, self.eo2_pa, self.eo2_e, period=360) + a + b * np.cos(tr) + c * np.sin(tr)
        for n, (i0) in ((2, 0), (3, 2)):
            r = r + (pc[i0] + pc[4 + i0] * tj) * np.cos(n * tr) + (pc[i0 + 1] + pc[5 + i0] * tj) * np.sin(n * tr)
        r = r + np.interp(th, self.g001, self.relleu(sig_px), period=360)
        if variant == 'propi' and self.mesurat[j]:
            r = r + np.interp(th, self.theta_b, self.eps_propi[j], period=360)
        return r
    def dfina(self, j, X, Y, sig_px=1.25, variant='lola'):
        cx, cy = self.centres_model[j]
        th = np.degrees(np.arctan2(-(Y - cy), X - cx)) % 360
        return np.hypot(X - cx, Y - cy) - self.rL(j, th, sig_px, variant)
G = None
try:
    import os as _os; G = Geometria(H / _os.environ.get('GEOM_FINA', 'GEOMETRIA_FINA.npz'))
except FileNotFoundError:
    pass
