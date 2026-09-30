"""nucli (V106 · Separació, Claude, 26-09-2026) · Dades i geometria comunes de la inversió conjunta.
δ_j = pas alt al llarg de l'arc de ln L_j (lògica de la c1 de la V105: mitjana gaussiana normalitzada σ_c = 32 px d'arc menys el suavitzat fi
de 0,5 px, només on el fotograma veu el píxel a D_j ≥ LO i amb la finestra gruixuda ≥ 90 % plena). Geometria de cada fotograma: centre lunar
del gradient de distance_model (+ correcció opcional), D_j = |x − c_j| − R − e_o2(PA_j) (silueta d'ordre 2 de la V99), φ_j = PA_j."""
import numpy as np, json
from pathlib import Path
from scipy.ndimage import gaussian_filter1d
R0 = Path.home() / 'Desktop/Eclipse 2026'
DADES = Path('/private/tmp/claude_v106/separacio/dades')
class Dades:
    def __init__(self):
        m = np.load(DADES / 'META.npz'); self.dg = m['dgrid'].astype(np.float64); self.nth = int(m['nth']); self.cx, self.cy, self.R = [float(v) for v in m['centre']]
        self.C0 = m['centres'].astype(np.float64); self.t = m['t']; self.e = m['e']; self.nF = len(self.t)
        self.LNL = np.load(DADES / 'LNL.npy', mmap_mode='r'); self.OK = np.load(DADES / 'OK.npy', mmap_mode='r'); self.WG = np.load(DADES / 'WG.npy', mmap_mode='r')
        self.th = np.linspace(0, 2 * np.pi, self.nth, endpoint=False); self.dth = np.degrees(self.th)
        self.X = self.cx + np.cos(self.th)[None, :] * (self.R + self.dg[:, None]); self.Y = self.cy - np.sin(self.th)[None, :] * (self.R + self.dg[:, None])
        sil = np.load(R0 / '4-RESULTATS/v99_banda_20260925/D21_silueta_o2.npz'); self.SPA = np.asarray(sil['pa'], float); self.SE = np.asarray(sil['e'], float)
        self.i4 = int(np.argmin(np.abs(self.dg + 4.0)))            # fila d = −4 (inici de la graella de la c1)
    def geom(self, j, dxy=(0.0, 0.0)):
        cxj = self.C0[j, 0] + dxy[0]; cyj = self.C0[j, 1] + dxy[1]
        u = self.X - cxj; v = -(self.Y - cyj); rho = np.hypot(u, v)
        a = np.degrees(np.arctan2(v, u)) % 360
        D = rho - self.R - np.interp(a.ravel(), self.SPA, self.SE, period=360).reshape(a.shape)
        return a, D, u, v, rho
    def delta(self, j, D, LO=0.6, sigc=32.0, extra=None):
        """δ_j i la seva validesa (lògica c1). extra: patró afegit a ln L abans del pas alt (injecció física)."""
        v = np.asarray(self.OK[j]) & (D >= LO)
        lL = np.where(v, np.asarray(self.LNL[j], np.float64), 0.0)
        if extra is not None: lL = np.where(v, lL + extra, 0.0)
        vf = v.astype(np.float64); sc = sigc / 0.5
        cw = gaussian_filter1d(vf, sc, axis=1, mode='wrap'); cm = gaussian_filter1d(lL, sc, axis=1, mode='wrap') / np.maximum(cw, 1e-12)
        fw = gaussian_filter1d(vf, 1.0, axis=1, mode='wrap'); fm = gaussian_filter1d(lL, 1.0, axis=1, mode='wrap') / np.maximum(fw, 1e-12)
        okd = v & (cw >= 0.9)
        return np.where(okd, fm - cm, 0.0).astype(np.float32), okd
