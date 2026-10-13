"""c4b · El parell del mateix marc final | K-Cor (±2,0 R☉, 1400 px), amb la geometria afí corregida (substitueix el P2 de c4)."""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from comu_comp import *
Image.MAX_IMAGE_PIXELS = None
SRGB = ARREL / 'publicacions/APOD/enviament_20260930/Eclipse_2026-08-12_Pere_Guerra_Serra.jpg'
gF = geo_final('efemeride'); fin = Image.open(SRGB).convert('RGB'); W, H = fin.size
N, SEMI = 1400, 2.0
f = (2 * SEMI * gF.R) / N
fa = np.asarray(fin.resize((round(W / f), round(H / f)), Image.LANCZOS)).astype(np.float32)
gf = Geo('f', (gF.cx + 0.5) / f - 0.5, (gF.cy + 0.5) / f - 0.5, gF.R / f, gF.n, gF.e, '', '')
gP = Geo('p', N / 2 - 0.5, N / 2 - 0.5, N / (2 * SEMI), gF.n, gF.e, '', '')
yy, xx = np.mgrid[0:N, 0:N].astype(np.float64); r, pa = gP.polar(xx, yy); fx, fy = gf.px(r, pa)
A = np.dstack([nd.map_coordinates(fa[..., c], [fy, fx], order=1, mode='constant', cval=0) for c in range(3)]).astype(np.uint8)
kc, gK = carrega_kcor('20260812_182932_kcor_l2_nrgf_avg_cropped.gif')
kv = kc.copy(); rK, _ = gK.polar(*np.meshgrid(np.arange(512), np.arange(512))); kv[rK < 1.075] = np.nan
for (a_, b_, c_, d_) in [(0, 150, 0, 48), (395, 512, 0, 40), (0, 265, 462, 512), (340, 512, 462, 512)]: kv[c_:d_, a_:b_] = np.nan
v = mostreja(kv, gK, r, pa); t = np.where(np.isfinite(v), v / 255.0, 0.0)
Image.fromarray(A).save(VISTES / 'P2_final_vs_KCor_A_final.jpg', quality=92)
Image.fromarray((np.dstack([t, t, t]) * 255).astype(np.uint8)).save(VISTES / 'P2_final_vs_KCor_B.jpg', quality=92)
print('P2 refet')
