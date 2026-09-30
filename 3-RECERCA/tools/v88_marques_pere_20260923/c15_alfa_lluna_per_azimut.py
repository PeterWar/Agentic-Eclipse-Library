"""c15 · On acaba l'alfa de la Lluna mostrada (258, = la 225 de Pere) per azimut, comparat amb on comença la dada vàlida de la corona (la corba
DMIN de a3a) i amb les marques. Per a cada grau: radis (des del limbe de presentació R 453) on l'alfa baixa de 0,95, 0,5 i 0,05, i la cobertura de
corona vàlida que l'alfa enfosqueix (∑ alfa sobre els píxels amb dada vàlida, per grau). Sortida: ALFA_LLUNA_PER_AZIMUT.json, LAMINA_M15_alfa_lluna.png."""
from vm_comu import *
from psb69 import PSB
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
claim()
p = PSB(str(PSB_PERE)); a, org = p.channel(258, -1); a = a.astype(np.float32) / 65535; x0, y0 = org
cx, cy, R = GEO['cx'], GEO['cy'], GEO['R']; yy, xx = np.mgrid[y0:y0 + a.shape[0], x0:x0 + a.shape[1]]; d = np.hypot(xx - cx, yy - cy) - R
th = (np.degrees(np.arctan2(-(yy - cy), xx - cx)) + 360) % 360; ib = th.astype(int) % 360
Q = np.load(V88D / 'A3A_franja_un_instant.npz'); DMIN = Q['DMIN']; NBZ = len(DMIN); dmin_deg = np.array([np.mean(DMIN[int(k * NBZ / 360):int((k + 1) * NBZ / 360)]) for k in range(360)])
by0, by1, bx0, bx1 = [int(v) for v in Q['box']]; dom = np.zeros_like(a, bool); oy, ox = by0 - y0, bx0 - x0
sub = Q['domini'][max(0, -oy):, max(0, -ox):]; hh, ww = min(sub.shape[0], a.shape[0] - max(oy, 0)), min(sub.shape[1], a.shape[1] - max(ox, 0)); dom[max(oy, 0):max(oy, 0) + hh, max(ox, 0):max(ox, 0) + ww] = sub[:hh, :ww]
r95, r50, r05, tapat = np.full(360, np.nan), np.full(360, np.nan), np.full(360, np.nan), np.zeros(360)
for k in range(360):
    s = (ib == k) & (d > -20) & (d < 20)
    if s.sum() < 20: continue
    dk, ak = d[s], a[s]; o = np.argsort(dk); dk, ak = dk[o], ak[o]
    # radi on l'alfa (mediana mòbil en 0,5 px) creua cada nivell per última vegada
    bins = np.arange(-20, 20, 0.5); med = np.array([np.median(ak[(dk >= b) & (dk < b + 0.5)]) if ((dk >= b) & (dk < b + 0.5)).any() else np.nan for b in bins])
    for lv, arr in [(0.95, r95), (0.5, r50), (0.05, r05)]:
        above = np.flatnonzero(med >= lv); arr[k] = bins[above[-1]] + 0.5 if above.size else np.nan
    tapat[k] = float((a[(ib == k) & dom & (d > 0)]).sum())      # «píxels de corona vàlida» enfosquits per l'alfa (en unitats de píxel)
res = dict(alfa_0_95_px=np.round(r95, 1).tolist(), alfa_0_5_px=np.round(r50, 1).tolist(), alfa_0_05_px=np.round(r05, 1).tolist(), dmin_px=np.round(dmin_deg, 2).tolist(), corona_valida_tapada_px_per_grau=np.round(tapat, 1).tolist())
for a0, a1 in [(100, 120), (120, 152), (152, 170), (170, 190), (190, 205), (205, 230), (230, 260), (260, 300), (300, 360), (0, 60), (60, 100)]:
    sl = slice(a0, a1); res[f'resum_{a0}_{a1}'] = dict(alfa05=float(np.nanmedian(r05[sl])), alfa50=float(np.nanmedian(r50[sl])), dmin=float(np.median(dmin_deg[sl])), tapat=float(np.sum(tapat[sl])))
desa_json('ALFA_LLUNA_PER_AZIMUT.json', res)
for k, v in res.items():
    if k.startswith('resum'): print(k, {kk: round(vv, 1) for kk, vv in v.items()})
fig, ax = plt.subplots(figsize=(15, 4.5)); az = np.arange(360)
ax.plot(az, r95, color='0.6', label='alfa 0,95'); ax.plot(az, r50, 'k', lw=1.5, label='alfa 0,5'); ax.plot(az, r05, 'k:', label='alfa 0,05'); ax.plot(az, dmin_deg, 'b', lw=1.5, label='on comença la dada de corona vàlida (DMIN)')
for a0, a1, c in [(104, 119, 'c'), (121, 152, 'm'), (171, 178, 'm'), (210, 212, 'm'), (216, 229, 'm')]: ax.axvspan(a0, a1, color=c, alpha=0.15)
ax.axhline(0, color='r', lw=0.8); ax.set_xlabel('azimut (°; 0 = dreta, 90 = dalt, 180 = esquerra)'); ax.set_ylabel('distància al limbe de presentació (px)'); ax.set_ylim(-6, 14); ax.grid(alpha=0.3); ax.legend(fontsize=8, ncol=4)
ax.set_title("On acaba l'alfa de la Lluna mostrada (258 = 225) i on comença la corona vàlida. Bandes de color: les marques de la V88", fontsize=10)
fig.tight_layout(); fig.savefig(SORT / 'LAMINA_M15_alfa_lluna.png', dpi=100); plt.close(fig); log('fet')
