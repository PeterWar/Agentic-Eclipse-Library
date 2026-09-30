"""F1c · quin fotograma porta el punt brillant del residu d'earthshine (vist a F1 prop de (5367, 3545) del llenç)? Cada fotograma normalitzat contra la
referència de l'ALTRE sensor (Vixen vs Sony 8 s A; Sony vs mitjana Vixen), diferència suavitzada σ 4 (escala de la mota de 22 px), màxim en 40 px."""
import json, numpy as np
from scipy.ndimage import gaussian_filter
from comu42 import *
MC = (CX + 14.8, CY + 0.9); WIN = 700; RL = 453.5; SPOT = (5367, 3545)
FR = [('sony', 'DSC06987'), ('sony', 'DSC06993'), ('sony', 'DSC06984'), ('sony', 'DSC06996'), ('sony', 'DSC06999'), ('vixen', '572A2982'), ('vixen', '572A2983'), ('vixen', '572A2984')]
x0, y0 = int(round(MC[0])) - WIN, int(round(MC[1])) - WIN; yy, xx = np.mgrid[0:2 * WIN, 0:2 * WIN]; r = np.hypot(xx + x0 - MC[0], yy + y0 - MC[1]); inn = r < 0.93 * RL
def sm(z, m, s):
    return gaussian_filter(np.where(m, z, 0).astype(np.float32), s) / np.maximum(gaussian_filter(m.astype(np.float32), s), 1e-6)
T = {}
for tag, stem in FR:
    a = np.load(CAU42 / f'lluna_{tag}_{stem}_v42.npy')[..., 1]; p = np.load(CAU42 / f'lluna_{tag}_{stem}_v42_pes.npy'); ok = np.isfinite(a) & (p > 0) & inn
    a = a / np.nanmedian(a[ok]); T[stem] = (np.where(ok, a, 0), ok)
V = np.mean([T[s][0] for s in ('572A2982', '572A2983', '572A2984')], axis=0); Vok = T['572A2982'][1] & T['572A2983'][1] & T['572A2984'][1]
S = T['DSC06987'][0]; Sok = T['DSC06987'][1]
sx, sy = SPOT[0] - x0, SPOT[1] - y0; box = (slice(sy - 40, sy + 41), slice(sx - 40, sx + 41)); rep = {}
for tag, stem in FR:
    z, ok = T[stem]; refz, refok = (S, Sok) if tag == 'vixen' else (V, Vok); m = ok & refok
    d = sm(z - refz, m, 4) - sm(z - refz, m, 30); sd = float(np.std(d[m])); sub = d[box]; k = np.unravel_index(np.argmax(np.abs(sub)), sub.shape)
    amp = float(sub[k]); rep[stem] = dict(x_llenc=int(k[1] + sx - 40 + x0), y_llenc=int(k[0] + sy - 40 + y0), amplitud_pct=100 * amp, z=amp / sd, sigma_pct=100 * sd)
    print(f'{stem:9s} vs {"Sony 8 s" if tag == "vixen" else "Vixen":8s}: extrem a ({rep[stem]["x_llenc"]}, {rep[stem]["y_llenc"]}) {100*amp:+.2f} % ({amp/sd:+.1f} σ; σ del mapa {100*sd:.2f} %)')
(REB42 / 'F1c_punt_brillant.json').write_text(json.dumps(rep, indent=1, ensure_ascii=False))
