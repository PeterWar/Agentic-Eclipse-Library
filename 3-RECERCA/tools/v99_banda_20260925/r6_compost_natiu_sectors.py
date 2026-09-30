"""r6 (V99 banda, tancament de Codex) · El COMPOST NATIU (render del Photoshop amb les capes d'ajust de Pere: vistes/V98_lluna.tif i V99_lluna.tif,
retall [4600, 3000, 6150, 4550]) per sector de 30° i distància al limbe de presentació: mediana de ln L (L = (R+2G+B)/4) de cada versió i la
diferència V99 − V98; i l'energia de detall (pas alt σ 1,5) per calaix, que diu on hi ha textura nova. Ús: r6_compost_natiu_sectors.py <V98.tif> <V99.tif> <sortida.json>"""
import sys, json
import numpy as np, tifffile, cv2
A = tifffile.imread(sys.argv[1])[..., :3].astype(np.float64); B = tifffile.imread(sys.argv[2])[..., :3].astype(np.float64)
LX, LY, RL = 5375.786804312011, 3775.9774911631, 452.9785129274736; ox, oy = 4600, 3000
h, w = A.shape[:2]; yy, xx = np.mgrid[oy:oy + h, ox:ox + w]; d = np.hypot(xx - LX, yy - LY) - RL; th = (np.degrees(np.arctan2(-(yy - LY), xx - LX)) + 360) % 360
def lum(X): return (X[..., 0] + 2 * X[..., 1] + X[..., 2]) / 4
LA, LB = lum(A), lum(B)
def hp(L): Lf = np.log(np.maximum(L, 1)).astype(np.float32); return Lf - cv2.GaussianBlur(Lf, (0, 0), 1.5)
HA, HB = hp(LA), hp(LB); rep = {}
for a0 in range(0, 360, 30):
    sec = ((th - a0) % 360) < 30; row = {}
    for k in np.arange(-1, 15, 1.0):
        m = sec & (d >= k) & (d < k + 1) & (LA > 0) & (LB > 0)
        if m.sum() < 30: continue
        row[f'{k:.0f}'] = dict(dif_ln=round(float(np.median(np.log(LB[m] / LA[m]))), 4), detall_V98=round(float(np.std(HA[m])), 4), detall_V99=round(float(np.std(HB[m])), 4))
    rep[f'{a0}-{a0+30}'] = row
    print(f'{a0:3d}-{a0+30:3d}', ' '.join(f"{k}:{v['dif_ln']:+.3f}({v['detall_V98']:.3f}→{v['detall_V99']:.3f})" for k, v in row.items() if -1 <= float(k) <= 9))
json.dump(rep, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
