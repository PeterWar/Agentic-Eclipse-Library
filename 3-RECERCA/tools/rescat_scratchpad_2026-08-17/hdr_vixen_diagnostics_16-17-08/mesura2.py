import sys, math, time
import numpy as np, cv2
sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools")
import hdr_corona_vixen as M
from scipy.ndimage import uniform_filter1d

SP = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/8222da38-0c6f-46a7-867a-f0224834d74e/scratchpad/"
z = np.load(SP + "bandes.npz")
valid = z["valid"]
H, W = valid.shape
cy, cx = H / 2.0, W / 2.0
Rmax = 3479.0
Wp, Hp = 8000, 8192          # radial (log), angular
def lp(a):
    return cv2.warpPolar(np.ascontiguousarray(a, np.float32), (Wp, Hp), (cx, cy), Rmax,
                         cv2.WARP_POLAR_LOG + cv2.INTER_LINEAR)
vp = lp(valid.astype(np.float32)) > 0.999
rho = np.arange(Wp)
r_of = np.exp(rho * math.log(Rmax) / Wp)      # radi de cada columna
rs_of = r_of / M.R_SOL_PX
# soroll sintètic amb la correlació del drizzle, mateixa mida, mateixes bandes
rng = np.random.default_rng(1)
noise = cv2.blur(rng.standard_normal((H, W)).astype(np.float32), (2, 2))
esc = M.BANDES_PX
zones = [(1.25, 1.6), (1.6, 2.2), (2.2, 3.0), (3.0, 4.0), (4.0, 5.0)]
print("Anisotropia radial de la banda: var(suau al llarg de r) / var(suau al llarg de theta),")
print("amb finestres de longitud igual (~0.008 r). Soroll pur → 1.0. Zones en Rsol.")
prev_n = M.desenfoca(noise, esc[0])
for j, (s0, s1) in enumerate(zip(esc[:-1], esc[1:])):
    seg_n = M.desenfoca(noise, s1)
    bn = prev_n - seg_n
    prev_n = seg_n
    if f"b{j}" not in z:
        continue
    b = z[f"b{j}"]
    bp = lp(b)
    bnp = lp(bn)
    row = []
    for k in (8, 24, 64):
        kt = int(round(k * 1.30))
        sr = uniform_filter1d(bp, k, axis=1, mode="nearest")     # al llarg de rho (columnes = radi)
        st = uniform_filter1d(bp, kt, axis=0, mode="wrap")       # al llarg de theta (files)
        srn = uniform_filter1d(bnp, k, axis=1, mode="nearest")
        stn = uniform_filter1d(bnp, kt, axis=0, mode="wrap")
        cel = []
        for (a, c) in zones:
            cols = (rs_of > a) & (rs_of < c)
            m = vp[:, cols]
            vr = float(np.mean(sr[:, cols][m] ** 2)); vt = float(np.mean(st[:, cols][m] ** 2))
            vrn = float(np.mean(srn[:, cols][m] ** 2)); vtn = float(np.mean(stn[:, cols][m] ** 2))
            cel.append(f"{vr/vt:4.2f}({vrn/vtn:3.2f})")
        row.append(f"k={k}: " + " ".join(cel))
    print(f"{s0:5.1f}-{s1:5.1f} px  " + " | ".join(row))
