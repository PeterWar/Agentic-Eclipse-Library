"""Flat del Sony FE 300 mm f/2,8 GM a f/2,8, dels flats de cel de l'A7III d'abril de 2025
(~/Desktop/Sony Calibration/Calibració A7III 04-2025/Flats NETS 300mm {3200,6400}), portat a la reixa
de l'A7RIIIA (5320×7968, raw_image_visible).

- black level restat, cada fotograma normalitzat a la seva mediana, mitjana dels fotogrames;
- per pla de Bayer (R, G=G1+G2, B) a mitja resolució;
- simetrització 180° (el gradient del cel de crepuscle és senar i se'n va; el vinyetatge òptic és parell);
- suavitzat fort (σ 25 px a mitja resolució ≈ 100 µm) perquè només en volem l'escala gran (i la pols
  del sensor de l'A7III no és a l'A7RIIIA);
- reescalat a la reixa de l'A7RIIIA amb els centres alineats: pitch 5,94 µm (A7III) / 4,51 µm (A7RIIIA).
Sortida: flat_a7r3a_rgb.npy (5320×7968×3, 1 al centre), flat_a7iii_planes.npy i un PNG de diagnòstic.
"""
import os, glob, numpy as np, rawpy
from scipy import ndimage as ndi
from PIL import Image

SP = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.expanduser('~/Desktop/Sony Calibration/Calibració A7III 04-2025')
SETS = {'3200': 'Flats NETS 300mm 3200', '6400': 'Flats NETS 300mm 6400'}
PITCH_A7III, PITCH_A7R3 = 5.94, 4.51
HR, WR = 5320, 7968

def carrega_set(dirn):
    files = sorted(glob.glob(os.path.join(BASE, dirn, '*.ARW')))
    acc = None; n = 0; meds = []
    for f in files:
        with rawpy.imread(f) as r:
            raw = r.raw_image_visible.astype(np.float32)
            col = r.raw_colors_visible.copy()
            bl = np.array(r.black_level_per_channel, np.float32)
            wl = r.white_level
        # black per pla
        b = np.zeros_like(raw)
        for k in range(4):
            b[col == k] = bl[k]
        raw = raw - b
        if (raw > 0.9 * (wl - bl.max())).mean() > 0.001:
            print('  saturat, salto', os.path.basename(f)); continue
        med = float(np.median(raw))
        meds.append(med)
        raw /= med
        acc = raw if acc is None else acc + raw
        n += 1
    print(f'{dirn}: {n} fotogrames, mediana ADU per fotograma {np.min(meds):.0f}…{np.max(meds):.0f}')
    return acc / n, col

planes_all = {}
for tag, dirn in SETS.items():
    F, col = carrega_set(dirn)
    H, W = F.shape
    # plans a mitja resolució: R (col 0), G (1 i 3), B (2)
    P = {}
    for c, ks in ((0, (0,)), (1, (1, 3)), (2, (2,))):
        m = np.isin(col, ks).astype(np.float32)
        num = (F * m)[:H // 2 * 2, :W // 2 * 2].reshape(H // 2, 2, W // 2, 2).sum(axis=(1, 3))
        den = m[:H // 2 * 2, :W // 2 * 2].reshape(H // 2, 2, W // 2, 2).sum(axis=(1, 3))
        P[c] = num / np.maximum(den, 1)
    planes_all[tag] = np.stack([P[0], P[1], P[2]], -1).astype(np.float32)
    print(f'  {tag}: forma plans {planes_all[tag].shape}')

# comparació entre els dos jocs (fets amb un minut de diferència)
A, Bs = planes_all['3200'], planes_all['6400']
q = ndi.gaussian_filter(A[..., 1], 20) / ndi.gaussian_filter(Bs[..., 1], 20)
print('quocient 3200/6400 (verd, suavitzat): p1 %.4f  p50 %.4f  p99 %.4f' % tuple(np.percentile(q, [1, 50, 99])))
# combinació (mitjana dels dos jocs, mateixa lent, mateixa obertura)
Fp = 0.5 * (A + Bs)
h, w = Fp.shape[:2]
# simetrització 180°
Fs = 0.5 * (Fp + Fp[::-1, ::-1])
odd = Fp - Fs
print('part senar (gradient del cel etc.): p1/p99 del verd %.4f / %.4f' % tuple(np.percentile(odd[..., 1], [1, 99])))
# suavitzat fort per pla (σ 25 px a mitja resolució) i normalització al centre
Fsm = np.stack([ndi.gaussian_filter(Fs[..., c], 25, mode='nearest') for c in range(3)], -1)
cy, cx = h / 2 - 0.5, w / 2 - 0.5
cen = Fsm[int(cy) - 50:int(cy) + 50, int(cx) - 50:int(cx) + 50].mean(axis=(0, 1))
Fsm /= cen
np.save(os.path.join(SP, 'flat_a7iii_planes.npy'), Fsm.astype(np.float32))
# perfil radial (verd) i asimetria residual (parell): compara els quatre cantons i els quatre costats
yy, xx = np.mgrid[0:h, 0:w]
rr = np.hypot((xx - cx) * 2 * PITCH_A7III, (yy - cy) * 2 * PITCH_A7III)   # µm des del centre
for rmm in (0, 5, 10, 15, 18, 20, 21.4):
    m = np.abs(rr / 1000 - rmm) < 0.3
    if m.any():
        print(f'  r = {rmm:4.1f} mm: flat R/G/B = ' + ' '.join(f'{Fsm[..., c][m].mean():.3f}' for c in range(3)))
print('  cantons (verd): dalt-esq %.3f dalt-dreta %.3f baix-esq %.3f baix-dreta %.3f' % (
    Fsm[20:120, 20:120, 1].mean(), Fsm[20:120, -120:-20, 1].mean(), Fsm[-120:-20, 20:120, 1].mean(), Fsm[-120:-20, -120:-20, 1].mean()))
print('  costats (verd): dalt %.3f baix %.3f esq %.3f dreta %.3f' % (
    Fsm[20:120, w//2-100:w//2+100, 1].mean(), Fsm[-120:-20, w//2-100:w//2+100, 1].mean(), Fsm[h//2-100:h//2+100, 20:120, 1].mean(), Fsm[h//2-100:h//2+100, -120:-20, 1].mean()))
# part parell no radial: flat − perfil radial (verd)
rb = np.clip((rr / 100).astype(int), 0, 400)
prof = np.bincount(rb.ravel(), weights=Fsm[..., 1].ravel(), minlength=401) / np.maximum(np.bincount(rb.ravel(), minlength=401), 1)
nr = Fsm[..., 1] - prof[rb]
print('  part parell no radial (verd): p1/p99 %.4f / %.4f' % tuple(np.percentile(nr, [1, 99])))

# reescalat a la reixa de l'A7RIIIA: posició física (µm) del píxel de l'A7RIIIA → píxel de pla A7III
yr, xr = np.mgrid[0:HR, 0:WR].astype(np.float32)
uy = (yr - (HR / 2 - 0.5)) * PITCH_A7R3 / (2 * PITCH_A7III) + cy
ux = (xr - (WR / 2 - 0.5)) * PITCH_A7R3 / (2 * PITCH_A7III) + cx
flat = np.empty((HR, WR, 3), np.float32)
for c in range(3):
    flat[..., c] = ndi.map_coordinates(Fsm[..., c], [uy, ux], order=1, mode='nearest')
np.save(os.path.join(SP, 'flat_a7r3a_rgb.npy'), flat)
print('flat A7RIIIA: forma', flat.shape, ' mínim per canal', flat.reshape(-1, 3).min(0), ' cantons', flat[0, 0], flat[-1, -1])
# PNG: flat verd (0,4–1,0), part senar i part parell no radial
def to8(a, lo, hi):
    return (np.clip((a - lo) / (hi - lo), 0, 1) * 255).astype(np.uint8)
pan = np.concatenate([to8(Fsm[::4, ::4, 1], 0.4, 1.0), to8(odd[::4, ::4, 1] + 0.5, 0.45, 0.55), to8(nr[::4, ::4] + 0.5, 0.47, 0.53)], 1)
Image.fromarray(pan).save(os.path.join(SP, 'flat_sony300_diag.png'))
print('PNG: flat verd 0,4–1 | part senar ±5 % | part parell no radial ±3 %')
