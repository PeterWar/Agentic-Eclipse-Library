"""Pilots 1:1 finals (vista de diferència en EV) per a ID8 (sobre V2b) i ID9 (sobre V2b+8), compost final 1/4 i
la revisió d'ID7 (polar del compost final al voltant de la Lluna amb la banda d'ID7)."""
import json, numpy as np
from v3b_lib import *
from geom import R_moon
QA = f'{V3B}/QA_final'
import os; os.makedirs(QA, exist_ok=True)
xx, yy = canvas_grid()
abans = np.asarray(load_abans_rgb()[..., :3], np.float32)/65535.
l, t, r_, b = FRAME
def getter(i):
    R_, G_, B_ = load_layer_rgb(i)
    def get(y0, y1, x0, x1):
        out = np.zeros((y1-y0, x1-x0, 3), np.float32)
        ly0, ly1 = max(y0, t), min(y1, b); lx0, lx1 = max(x0, l), min(x1, r_)
        if ly1 > ly0 and lx1 > lx0:
            for k, ch in enumerate((R_, G_, B_)):
                out[ly0-y0:ly1-y0, lx0-x0:lx1-x0, k] = np.asarray(ch[ly0-t:ly1-t, lx0-l:lx1-l], np.float32)/65535.
        return out
    return get
rec = {}
for i, r_a, r_b in ((8, 1.29, 1.59), (9, 1.43, 2.23)):
    m = np.asarray(np.load(f'{V3B}/masks_final/mask_{i}.npy', mmap_mode='r'))
    despres = compose(abans, i, m)
    cxm, cym = moon_centre_canvas(i); ang = np.radians(150)
    r_mid = 0.5*(r_a+r_b)*R_SUN
    pts = {'a_limbe_banda_150deg': (cxm+470*np.cos(ang), cym-470*np.sin(ang)), 'b_protuberancia_P4': (3578, 2653),
           'c1_costura_45deg': (SUN[0]+r_mid*np.cos(np.radians(45)), SUN[1]-r_mid*np.sin(np.radians(45))),
           'c2_costura_225deg': (SUN[0]+r_mid*np.cos(np.radians(225)), SUN[1]-r_mid*np.sin(np.radians(225)))}
    g = getter(i); rec[i] = {}
    for k, (px, py) in pts.items():
        rec[i][k] = pilot_crop(abans, despres, g, m, px, py, f'{QA}/pilot_ID{i}_{k}.png', title=f'ID{i} {k}')
    overview(despres, f'{QA}/compost_fins_ID{i}_1de4.png')
    abans = despres
np.save(f'{V3B}/compost_final_offline_u16.npy', quantize(abans))
json.dump(rec, open(f'{QA}/pilots.json', 'w'), indent=1)
print('fet')
