"""d41 (V102 detall; pregunta de Pere del 26-09) · GUANY PER CONTINUÏTAT RADIAL (fix al cel, immune a la contaminació lligada a la Lluna):
per a cada escala al llarg de l'arc (DoG 2→4, 4→8, 8→16 px), cada fila de distància d al cercle (0,5 px) i cada bloc d'angle (10°), la correlació r
entre el detall de la banda (dada A: primerencs, D_real ≥ 0,75, dividits per T) i el de la mateixa dada als raigs nets de 6–10 px.
Referència: la correlació ρ que dona una dada NETA amb la mateixa separació radial (base_G lineal de la V99 a baix 250–300° i a la dreta 320–40°,
on la Lluna s'allunya i la dada és neta fins al limbe). Fracció de senyal real f = clip((r/ρ)², 0, 1), suavitzada; és el guany de Wiener de la capa.
Sortida: GUANY_CONTINUITAT.npz (g[banda, fila, bloc PA]) i JSON."""
import json
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d, gaussian_filter
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925/B'
Z = np.load(O / 'D29_primerencs_075_15.npz'); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]; LX, LY, RL = [float(v) for v in Z['centre']]
esc = json.loads((R9 / 'lineal_v99_franja/A3C_FRANJA_SILUETA.json').read_text())['escales']; cF = [esc[f'c_F{c}'][0] for c in range(3)]
P = Z['RGB']; L = (cF[0] * P[..., 0] + 2 * cF[1] * P[..., 1] + cF[2] * P[..., 2]) / 4; ok = (Z['NF'] >= 3) & (L > 0)
G9 = np.asarray(np.load(R9 / 'lineal_v99/base_G.npy', mmap_mode='r')[by0:by1, bx0:bx1], np.float64); Q9 = np.load(R9 / 'lineal_v99_franja/A3C_franja_silueta.npz'); ok9 = Q9['domini_E'] & (G9 > 0)
DR_, DS_ = 0.25, 0.5; rr = np.arange(-1.0, 12.0, DR_); nth = int(round(2 * np.pi * RL / DS_)); tt = np.arange(nth) * 2 * np.pi / nth; thp = np.degrees(tt)
R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); mx = (LX + R_ * np.cos(T_) - bx0).astype(np.float32); my = (LY - R_ * np.sin(T_) - by0).astype(np.float32)
def pol(img, m):
    a = cv2.remap(np.where(m, np.log(np.maximum(img, 1e-30)), 0).astype(np.float32), mx, my, cv2.INTER_LINEAR); w = cv2.remap(m.astype(np.float32), mx, my, cv2.INTER_LINEAR)
    return np.where(w > 0.999, a / np.maximum(w, 1e-6), np.nan)
def bands(Pp):
    okp = np.isfinite(Pp); x = np.where(okp, Pp, 0); w = okp.astype(float)
    g = {s: gaussian_filter1d(x * w, s / DS_, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(w, s / DS_, axis=1, mode='wrap'), 1e-6) for s in (2, 4, 8, 16)}
    return {'2-4': np.where(okp, g[2] - g[4], np.nan), '4-8': np.where(okp, g[4] - g[8], np.nan), '8-16': np.where(okp, g[8] - g[16], np.nan)}
BA, B9 = bands(pol(L, ok)), bands(pol(G9, ok9))
ROWS = np.arange(0.0, 6.01, 0.5); BLK = np.arange(0, 360, 10)
def corrrow(B, lo, sel):
    ref = np.nanmean(B[(rr >= 6) & (rr < 10)][:, sel], 0); row = np.nanmean(B[(rr >= lo) & (rr < lo + 0.5)][:, sel], 0); m = np.isfinite(ref) & np.isfinite(row)
    return float(np.corrcoef(ref[m], row[m])[0, 1]) if m.sum() > 60 else np.nan
# ρ de dada neta (baix i dreta)
rho = {}
for b in B9:
    vals = []
    for lo in ROWS:
        cs = [corrrow(B9[b], lo, (((thp - a0) % 360) < 20)) for a0 in list(range(250, 300, 10)) + list(range(320, 400, 10))]
        vals.append(np.nanmedian(cs))
    rho[b] = np.array(vals)
g = np.full((3, ROWS.size, BLK.size), np.nan); rtab = np.full_like(g, np.nan)
for ib, b in enumerate(BA):
    for ir, lo in enumerate(ROWS):
        for ia, a0 in enumerate(BLK):
            sel = ((((thp - a0 - 5) + 180) % 360) - 180) ** 2 < 10 ** 2    # finestra de 20° centrada al bloc
            r = corrrow(BA[b], lo, sel); rtab[ib, ir, ia] = r
            if np.isfinite(r) and np.isfinite(rho[b][ir]) and rho[b][ir] > 0.2: g[ib, ir, ia] = np.clip((max(r, 0) / rho[b][ir]) ** 2, 0, 1)
# suavitzat (d i PA) i omplert dels buits amb 0 (sense evidència, sense detall)
okg = np.isfinite(g); gs = gaussian_filter(np.where(okg, g, 0), (0, 0.7, 0.7), mode=('nearest', 'nearest', 'wrap')) / np.maximum(gaussian_filter(okg.astype(float), (0, 0.7, 0.7), mode=('nearest', 'nearest', 'wrap')), 1e-6)
gs = np.where(gaussian_filter(okg.astype(float), (0, 0.7, 0.7), mode=('nearest', 'nearest', 'wrap')) > 0.3, gs, 0.0)
np.savez(O / 'GUANY_CONTINUITAT.npz', g=gs, rows=ROWS, blocs=BLK, bandes=np.array(list(BA)))
rep = dict(rho_net={b: [round(float(v), 3) for v in rho[b]] for b in rho}, files=ROWS.tolist(),
           dalt_95_125={b: [round(float(np.nanmean(gs[ib, ir, 9:13])), 2) for ir in range(ROWS.size)] for ib, b in enumerate(BA)},
           dalt_75_95={b: [round(float(np.nanmean(gs[ib, ir, 7:10])), 2) for ir in range(ROWS.size)] for ib, b in enumerate(BA)},
           baixesq_225_255={b: [round(float(np.nanmean(gs[ib, ir, 22:26])), 2) for ir in range(ROWS.size)] for ib, b in enumerate(BA)},
           r_dalt_95_125={b: [round(float(np.nanmean(rtab[ib, ir, 9:13])), 2) for ir in range(ROWS.size)] for ib, b in enumerate(BA)})
(O / 'GUANY_CONTINUITAT.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1))
for k in ('rho_net', 'r_dalt_95_125', 'dalt_95_125', 'dalt_75_95', 'baixesq_225_255'): print(k, 'files d', ROWS[:9].tolist()); [print('  ', b, v[:9]) for b, v in rep[k].items()]
