"""Reconstrueix el flat del FE 300 mm f/2,8 GM a la reixa de l'A7RIIIA (5320×7968) a partir del
perfil radial mesurat (research/tools/encaix_sony/flat_sony300_f28_perfil_radial.csv; part no radial
±0,3 %). Serveix quan `flat_a7r3a_rgb.npy` no hi és (els intermedis del 18-08 vivien a un scratchpad).
Ús: python flat_sony_des_del_perfil.py <sortida.npy>
"""
import sys, os, numpy as np
CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'encaix_sony', 'flat_sony300_f28_perfil_radial.csv')
PITCH_UM = 4.51
HR, WR = 5320, 7968
dat = np.genfromtxt(CSV, delimiter=',', skip_header=3, names=True)
r_mm = dat['r_mm']
yy, xx = np.mgrid[0:HR, 0:WR].astype(np.float32)
rr = np.hypot(xx - (WR - 1) / 2.0, yy - (HR - 1) / 2.0) * PITCH_UM / 1000.0
flat = np.empty((HR, WR, 3), np.float32)
for k, c in enumerate(('R', 'G', 'B')):
    flat[..., k] = np.interp(rr, r_mm, dat[c], left=dat[c][0], right=dat[c][-1]).astype(np.float32)
out = sys.argv[1] if len(sys.argv) > 1 else 'flat_a7r3a_rgb.npy'
np.save(out, flat)
print('flat', flat.shape, 'centre', flat[HR // 2, WR // 2], 'cantó', flat[0, 0], '→', out)
