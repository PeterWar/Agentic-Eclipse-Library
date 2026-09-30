"""a2 · Geometria del limbe per a la V86.
(1) Lluna de presentació = la capa 30 de Pere (Earthshine · revelat de Pere): cercle ajustat a la seva vora del 50 % fora del bony de la protuberància.
(2) Trajectòria de la Lluna als 67 fotogrames Vixen (model de distància de 4-RESULTATS/v85.../limb_frames).
(3) Franja sense dada neta (norma de Pere del 17-09, research/165): píxels on més d'una fracció f0 del pes del compost ve de fotogrames
    en què el píxel era a menys de d_e px del seu propi limbe (dèficit de vora i barreja temporal), més tot el que queda dins de la Lluna.
    Els filtres NO veuen aquesta franja; la seva sortida s'hi interpola (a4)."""
from v86_comu import *
from psb69 import PSB
import cv2
claim(); SORT.mkdir(exist_ok=True)
D_E, F0 = 12.0, 0.10
meta = json.loads((V85D / 'limb_frames/METADATA.json').read_text()); by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
# (1) Lluna de presentació: alfa×màscara de la capa 30
p = PSB(str(ARREL / '1-PHOTOSHOP/V85.psb')); L30 = p.layer(30); box = (bx0, by0, bx1, by1)
a30 = p.channel_box(30, -1, box).astype('float32') / 65535; m30 = p.channel_box(30, -2, box, fill=0).astype('float32') / 65535; e30 = a30 * m30
cs, _ = cv2.findContours((e30 >= 0.5).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE); c = max(cs, key=len)[:, 0, :].astype('float64')
def fit(xs, ys):
    A = np.c_[2 * xs, 2 * ys, np.ones_like(xs)]; s = np.linalg.lstsq(A, xs ** 2 + ys ** 2, rcond=None)[0]; return s[0], s[1], np.sqrt(s[2] + s[0] ** 2 + s[1] ** 2)
xc, yc, R = fit(c[:, 0], c[:, 1])
for it in range(4):   # descarta el bony (protuberància/cromosfera pintada a mà) amb un tall robust
    res = np.hypot(c[:, 0] - xc, c[:, 1] - yc) - R; ok = np.abs(res) < max(1.0, 2.5 * np.median(np.abs(res)))
    xc, yc, R = fit(c[ok, 0], c[ok, 1])
res = np.hypot(c[:, 0] - xc, c[:, 1] - yc) - R
lluna = dict(cx=float(xc + bx0), cy=float(yc + by0), R=float(R), residu_rms_px=float(np.std(res[ok])), fraccio_contorn_usada=float(ok.mean()), bony_max_px=float(res.max()))
# (2) trajectòria Vixen
Dm = np.load(V85D / 'limb_frames/distance_model.npy', mmap_mode='r'); Wt = np.load(V85D / 'limb_frames/weight.npy', mmap_mode='r'); Rm = meta['radius_model']
track = []
for i, f in enumerate(meta['frames']):
    d = np.array(Dm[i]); yy, xx = np.nonzero(np.abs(d) < 30); k = slice(None, None, max(1, len(yy) // 20000)); yy, xx = yy[k], xx[k]; rr = d[yy, xx] + Rm
    A = np.c_[2 * xx, 2 * yy, np.ones_like(xx)].astype(float); s = np.linalg.lstsq(A, (xx ** 2 + yy ** 2 - rr ** 2).astype(float), rcond=None)[0]
    track.append(dict(nom=f['name'], t=f['time'], exp=f['exposure'], cx=float(s[0] + bx0), cy=float(s[1] + by0)))
tt = np.array([q['t'] for q in track]); tx = np.array([q['cx'] for q in track]); ty = np.array([q['cy'] for q in track])
# instant de la Lluna de presentació: el punt de la trajectòria més proper al centre ajustat
tf = np.linspace(tt.min(), tt.max(), 5000); px = np.interp(tf, tt, tx); py = np.interp(tf, tt, ty); j = int(np.argmin(np.hypot(px - lluna['cx'], py - lluna['cy'])))
lluna.update(instant_s=float(tf[j]), distancia_a_trajectoria_px=float(np.hypot(px[j] - lluna['cx'], py[j] - lluna['cy'])), R_model_fotogrames=float(Rm))
# (3) franja: fracció del pes (canal G) que ve de fotogrames amb D < d_e
Wsum = np.zeros((by1 - by0, bx1 - bx0), 'float64'); Wnear = np.zeros_like(Wsum); Dmin = np.full(Wsum.shape, 999.0, 'float32')
for i in range(len(track)):
    w = np.asarray(Wt[i, :, :, 1], 'float64'); d = np.asarray(Dm[i]); Wsum += w; Wnear += w * (d < D_E); Dmin = np.where(w > 0, np.minimum(Dmin, d), Dmin)
frac = np.where(Wsum > 0, Wnear / np.maximum(Wsum, 1e-30), np.nan)
yy, xx = np.mgrid[by0:by1, bx0:bx1]; rL = np.hypot(xx - lluna['cx'], yy - lluna['cy'])
franja_box = ((frac > F0) | (Wsum <= 0)) & (rL < R + 80)
franja_box |= rL <= R + 0.5            # tot el disc de presentació queda fora del domini dels filtres
# la franja és un objecte geomètric continu: tapa forats petits i treu illes aïllades lluny del limbe
franja_box = cv2.morphologyEx(franja_box.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)).astype(bool)
n, lab, st, _ = cv2.connectedComponentsWithStats(franja_box.astype(np.uint8), 8); big = np.argmax(st[1:, cv2.CC_STAT_AREA]) + 1; franja_box = lab == big
# vora exterior de la franja per azimut (al voltant del centre de la Lluna de presentació)
th = (np.degrees(np.arctan2(-(yy - lluna['cy']), xx - lluna['cx'])) + 360) % 360; nb = 1440; ib = (th / 360 * nb).astype(int) % nb
rb = np.zeros(nb)
for k in range(nb):
    s = franja_box & (ib == k); rb[k] = rL[s].max() if s.any() else R
from scipy.ndimage import maximum_filter1d, gaussian_filter1d
rb_s = gaussian_filter1d(maximum_filter1d(rb, 9, mode='wrap'), 4, mode='wrap')   # vora contínua i suau (cap vora dentada)
franja = np.zeros((H, W), bool); franja[by0:by1, bx0:bx1] = franja_box
np.savez_compressed(SORT / 'A2_geometria.npz', franja=franja_box, box=np.array([by0, by1, bx0, bx1]), frac=np.nan_to_num(frac, nan=-1).astype('float32'), Dmin=Dmin, rb=rb, rb_s=rb_s, e30=e30.astype('float32'))
az = np.arange(nb) * 360 / nb
rep = dict(lluna_presentacio=lluna, d_e_px=D_E, f0=F0, trajectoria=dict(n=len(track), primer=track[0], ultim=track[-1], desplacament_px=float(np.hypot(tx[-1] - tx[0], ty[-1] - ty[0]))),
           franja=dict(pixels=int(franja_box.sum()), pixels_fora_disc=int((franja_box & (rL > R + 0.5)).sum()), vora_exterior_px_per_azimut={f'{a:.0f}': float(rb_s[int(a / 360 * nb)]) for a in range(0, 360, 15)},
                       amplada_max_fora_limbe_px=float(rb_s.max() - R), amplada_min_fora_limbe_px=float(rb_s.min() - R), azimut_amplada_max=float(az[np.argmax(rb_s)])),
           criteri='franja = (fracció del pes G dels fotogrames Vixen amb D < d_e) > f0, o sense pes; + disc de presentació; tancament 5×5 i component connex principal; vora exterior suavitzada per azimut (màx. 9 cel·les de 0,25°, gauss 1°)')
desa_json('A2_GEOMETRIA.json', rep); log('A2 fet'); print(json.dumps(rep, indent=1)[:3000])
