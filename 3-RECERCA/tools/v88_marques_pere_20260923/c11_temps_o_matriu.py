"""c11 · La vall de l'esquerra: barreja de temps (A) o matriu de color (B)? Per a cada fotograma primerenc: RGB amb els buits del mosaic omplerts
(σ 0,8, com a a3a), guanys i matriu → verd matricial; perfils als sectors de les marques i de control. I dues combinacions noves amb la mateixa
validesa i rampes que a3a: E_temps (pes temporal gaussià σ_t 0,8 s centrat a l'instant de la Lluna mostrada, 18,43 s) i E_sense_matriu (verd de càmera).
Sortida: TEMPS_O_MATRIU.json i LAMINA_M11_temps_o_matriu.png."""
from vm_comu import *
from v86_operadors import smoothstep
import cv2
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
claim()
V85D = ARREL / '4-RESULTATS/v85_regeneracio_20260922'
meta = json.loads((V85D / 'limb_frames/METADATA.json').read_text()); fr = meta['frames']; by0, by1, bx0, bx1 = meta['box_y0y1x0x1']
num = np.load(V85D / 'limb_frames/numerator.npy', mmap_mode='r'); wt = np.load(V85D / 'limb_frames/weight.npy', mmap_mode='r'); Dm = np.load(V85D / 'limb_frames/distance_model.npy', mmap_mode='r')
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']; DR = float(meta['radius_model']) - R
yy, xx = np.mgrid[by0:by1, bx0:bx1]; d = np.hypot(xx - cx, yy - cy) - R; th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360
Mx = np.array(meta['matrix'], np.float32); gn = np.array(meta['gain'], np.float32)
early = [i for i, f in enumerate(fr) if f['time'] <= 22.3]; T0, ST = 18.433, 0.8
SECT = {'esquerra-dalt 130–170°': (130, 170), 'esquerra-baix 190–225°': (190, 225), 'dalt 75–105°': (75, 105), 'baix 255–285°': (255, 285)}
xs = np.arange(-2, 20.01, 0.5); kb = np.round(d * 2) / 2
def perfil(A, sel, ok=None):
    s0 = sel if ok is None else sel & ok
    ys = np.array([np.nanmedian(A[s0 & (kb == v)]) if np.isfinite(A[s0 & (kb == v)]).sum() > 5 else np.nan for v in xs]); return ys / np.nanmedian(ys[(xs >= 10) & (xs <= 14)])
# per fotograma: RGB omplert i matricial
per_f = {}; Nt = np.zeros((by1 - by0, bx1 - bx0, 3)); Wt = np.zeros_like(Nt); Na = np.zeros_like(Nt); Wa = np.zeros_like(Nt)
for i in early:
    Do = np.asarray(Dm[i]) + DR; ok = Do >= 1.0; a_, b_ = (1.0, 3.0) if fr[i]['exposure'] < 0.0004 else (2.0, 6.0); rampa = smoothstep(Do, a_, b_)
    tau = np.exp(-0.5 * ((fr[i]['time'] - T0) / ST) ** 2)
    rgb = np.zeros((by1 - by0, bx1 - bx0, 3), np.float32)
    for c in range(3):
        n_ = np.asarray(num[i, :, :, c], np.float32); w_ = np.asarray(wt[i, :, :, c], np.float32)
        Ns = cv2.GaussianBlur(n_, (0, 0), 0.8); Ws = cv2.GaussianBlur(w_, (0, 0), 0.8); rgb[..., c] = np.where(Ws > 0, Ns / np.maximum(Ws, 1e-30), np.nan)
        wr = np.where(ok, w_ * rampa, 0); Na[..., c] += np.where(ok, n_ * rampa, 0); Wa[..., c] += wr; Nt[..., c] += np.where(ok, n_ * rampa, 0) * tau; Wt[..., c] += wr * tau
    m = np.einsum('ij,...j->...i', Mx, rgb * gn); per_f[i] = (rgb[..., 1], m[..., 1], ok)
def comb(N_, W_):
    out = np.zeros_like(N_, dtype=np.float32)
    for c in range(3):
        Ns = cv2.GaussianBlur(N_[..., c].astype(np.float32), (0, 0), 0.8); Ws = cv2.GaussianBlur(W_[..., c].astype(np.float32), (0, 0), 0.8); out[..., c] = np.where(Ws > 0, Ns / np.maximum(Ws, 1e-30), np.nan)
    return out
Ea = comb(Na, Wa); Et = comb(Nt, Wt); Eam = np.einsum('ij,...j->...i', Mx, Ea * gn); Etm = np.einsum('ij,...j->...i', Mx, Et * gn)
out = {'matriu': Mx.tolist(), 'd': xs.tolist()}
fig, axs = plt.subplots(2, len(SECT), figsize=(5.2 * len(SECT), 9), sharey='row')
for k, (nom, (a0, a1)) in enumerate(SECT.items()):
    sel = (th >= a0) & (th <= a1); o = out[nom] = {}
    for j, i in enumerate(early):
        g_cam, g_mat, ok = per_f[i]; col = plt.get_cmap('viridis')(j / (len(early) - 1))
        axs[0, k].plot(xs, perfil(g_cam, sel), color=col, lw=0.9); axs[1, k].plot(xs, perfil(g_mat, sel), color=col, lw=0.9, label=f"{fr[i]['time']:.1f} s")
        o[fr[i]['name']] = dict(t=fr[i]['time'], verd_camera=np.round(perfil(g_cam, sel), 3).tolist(), verd_matricial=np.round(perfil(g_mat, sel), 3).tolist())
    for row, (A, B, et) in enumerate([(Ea[..., 1], Et[..., 1], 'verd de càmera'), (Eam[..., 1], Etm[..., 1], 'verd matricial')]):
        pa, pt = perfil(A, sel), perfil(B, sel); o[f'combinacio_V88_{row}'] = np.round(pa, 3).tolist(); o[f'combinacio_temps_{row}'] = np.round(pt, 3).tolist()
        axs[row, k].plot(xs, pa, 'r', lw=2.5, label='combinació V88 (sense σ 1,3)'); axs[row, k].plot(xs, pt, 'k--', lw=2.5, label='amb pes temporal σ 0,8 s a 18,4 s')
        axs[row, k].set_title(f'{nom} · {et}', fontsize=10); axs[row, k].grid(alpha=0.3); axs[row, k].set_ylim(0, 3)
axs[1, 0].legend(fontsize=6); [a.set_xlabel('distància al limbe de presentació (px)') for a in axs[1]]
fig.tight_layout(); fig.savefig(SORT / 'LAMINA_M11_temps_o_matriu.png', dpi=100); plt.close(fig)
desa_json('TEMPS_O_MATRIU.json', out); log('fet')
