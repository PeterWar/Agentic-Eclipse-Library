"""E3d · l'«angle» entre les capes de Pere i la cadena en funció del radi (bandes de 0,10 R☉ de 1,02 a 1,62): capes 10/08/06 contra la base V42, la 08 contra la 10 (les dues
de Pere: coherència interna), i el control (base contra base girada +0,30°: ha de ser +0,30 a totes les bandes). Una rotació rígida és constant amb r."""
import json, numpy as np
from scipy.ndimage import rotate, shift as ndshift
from comu42 import *
import e3c_rotacio_bandes as X   # (torna a executar E3c: barat)
def gira_sol(img, ang):
    H_, W_ = img.shape; c = np.array([H_ / 2 - 0.5, W_ / 2 - 0.5]); d = np.array([CY, CX]) - c; a = np.deg2rad(ang); Rm = np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]]); t = d - Rm @ d
    return ndshift(rotate(img, -ang, reshape=False, order=1, mode='nearest'), t, order=1, mode='nearest')
lb = X.lb; caps = X.caps; lbg = gira_sol(lb, 0.30); rep = {}; bands = [(a, a + 0.10) for a in np.arange(1.02, 1.60, 0.05)]
print('banda        10 vs base   08 vs base   06 vs base   08 vs 10    control +0,30')
for r0, r1 in bands:
    pb = X.polar(lb, CX, CY, r0 * RS, r1 * RS); p10 = X.polar(caps['10 1/125'], CX, CY, r0 * RS, r1 * RS); p08 = X.polar(caps['08 1/30 x4 quar'], CX, CY, r0 * RS, r1 * RS); p06 = X.polar(caps['06 1/8 x4 quar'], CX, CY, r0 * RS, r1 * RS)
    row = {'10_vs_base': X.rot_az(p10, pb), '08_vs_base': X.rot_az(p08, pb), '06_vs_base': X.rot_az(p06, pb), '08_vs_10': X.rot_az(p08, p10), 'control_+0.30': X.rot_az(X.polar(lbg, CX, CY, r0 * RS, r1 * RS), pb)}
    rep[f'{r0:.2f}-{r1:.2f}'] = row; print(f'{r0:.2f}–{r1:.2f}   ' + '   '.join(f"{v[0]:+.3f}({v[1]:.2f})" for v in row.values()))
(REB42 / 'E3d_rotacio_per_radi.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False)); print('E3d fet')
