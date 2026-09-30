"""G1 · Marques de Pere a V39_Artefactes.psb (pintades a sobre de cada capa, totes en Normal 100 %): detecció per saturació de color sobre capes grises,
components connexes, posició (r/R☉, azimut), color, mida, pes de la Vixen al punt i distància a la vora del camp de la Vixen. Vistes ÷8 per capa."""
from comu39 import *
import cv2
from psd_tools import PSDImage
from PIL import Image
P = Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V39_Artefactes.psb'); OUTM = HERE39 / 'marques'
psd = PSDImage.open(P); r, t = coords(); wv = np.nan_to_num(np.asarray(np.load(CAU38 / 'weight_vixen_v38.npy', mmap_mode='r'), np.float32))
mv = wv > 0.005; dt_in = cv2.distanceTransform(mv.astype(np.uint8), cv2.DIST_L2, 5); dt_out = cv2.distanceTransform((~mv).astype(np.uint8), cv2.DIST_L2, 5); dvora = np.where(mv, dt_in, -dt_out)   # >0 dins del camp Vixen
def hue_name(rgb):
    R, G, B = rgb; mx, mn = max(rgb), min(rgb)
    if mx - mn < 0.15: return 'gris'
    h = cv2.cvtColor(np.uint8([[[B * 255, G * 255, R * 255]]]), cv2.COLOR_BGR2HSV)[0, 0, 0] * 2
    return 'vermell' if h < 15 or h >= 345 else 'taronja' if h < 45 else 'groc' if h < 70 else 'verd' if h < 170 else 'cian' if h < 200 else 'blau' if h < 260 else 'lila' if h < 300 else 'magenta'
rep = {}
for l in psd:
    a = l.numpy(channel='color'); assert a.shape[:2] == (H, W), a.shape
    sat = a.max(axis=2) - a.min(axis=2); base = l.name.startswith('00 ')
    m = sat > (0.55 if base else 0.25)
    m4 = m.reshape(H // 2, 2, W // 2, 2).any(axis=(1, 3)) if H % 2 == 0 and W % 2 == 0 else m[:H // 2 * 2, :W // 2 * 2].reshape(H // 2, 2, W // 2, 2).any(axis=(1, 3))
    n, lab, st, cen = cv2.connectedComponentsWithStats(m4.astype(np.uint8), connectivity=8)
    comps = []
    for i in range(1, n):
        if st[i, cv2.CC_STAT_AREA] < 12: continue
        cy, cx = cen[i][1] * 2, cen[i][0] * 2; yy, xx = int(min(max(cy, 0), H - 1)), int(min(max(cx, 0), W - 1))
        sel = (lab == i); ys, xs = np.nonzero(sel); col = a[ys[::max(1, len(ys) // 200)] * 2, xs[::max(1, len(xs) // 200)] * 2].mean(axis=0)
        comps.append({'x': round(cx), 'y': round(cy), 'r_R': round(float(r[yy, xx] / RS), 2), 'az_deg': round(float(np.degrees(t[yy, xx])), 0), 'area_px': int(st[i, cv2.CC_STAT_AREA] * 4), 'bbox': [int(st[i, 0] * 2), int(st[i, 1] * 2), int(st[i, 2] * 2), int(st[i, 3] * 2)], 'color': hue_name(col.tolist()), 'rgb': [round(float(v), 2) for v in col], 'pes_vixen': round(float(wv[yy, xx]), 3), 'dist_vora_vixen_px': round(float(dvora[yy, xx]))})
    comps.sort(key=lambda c: -c['area_px']); rep[l.name] = comps
    log(f"{l.name}: {len(comps)} components" + (': ' + '; '.join(f"{c['color']} r{c['r_R']} az{c['az_deg']:.0f} wv{c['pes_vixen']:.2f} vora{c['dist_vora_vixen_px']:+d}" for c in comps[:12]) if comps else ''))
    # vista ÷8 amb les marques en vermell viu
    v = a[::8, ::8]; v = np.clip(v, 0, 1); mk = m[::8, ::8]; v[mk] = [1, 0, 0]; Image.fromarray(np.uint8(v * 255)).save(OUTM / (l.name.replace('/', '_').replace(' ', '_')[:60] + '.png'))
    del a, sat, m, m4, lab
savejson(REB39 / 'G1_marques_v39.json', rep); log('G1 fet')
