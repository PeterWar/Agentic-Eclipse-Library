"""d35b (V100/V101 detall; configurable per entorn: D35B_FONT, D35B_GUANYS, D35B_SORTIDA, D35B_EXCLOU="pa0,pa1", D35B_MITJANA_ZERO=1) · LA CAPA DE DETALL REAL DE LA BANDA amb el guany CALIBRAT CONTRA LA VERITAT (d38), no contra meitats.
Dada A: D29_primerencs_20_35_temps.npz (només fotogrames t < 40 s: els que veuen la banda; rampa 2→3,5 sobre D_real; dividits per T).
Detall TANGENCIAL (mitjana zero al llarg de cada arc: no pot fer anells): bandes DoG al llarg de l'arc σ 2→4, 4→8, 8→16 px (el gra més fi no hi és:
a la banda és soroll, agents i d38). Guany de cada banda = pendent de regressió de la VERITAT sobre A mesurat a la dreta amb els mateixos
fotogrames primerencs (D38_DETALL_CONTRA_VERITAT.json: E[veritat | A] = pendent·A), interpolat en D_real (el màxim dels fotogrames primerencs del
píxel); zero per sota de D_real 2,75 px (r < 0,6: hi mana la contaminació de la vora de la Lluna).
Zona: rampa D_real 2,75→3,5 cap endins; fins a la vora de dada de la V99 + 2 px cap enfora (fosa 0,5→2): allà prenen el relleu els filtres.
Sortida: CAPA_DETALL_BANDA_FINAL.npz (delta, alfa, box) i un JSON amb els guanys."""
import json, os
from pathlib import Path
import numpy as np, cv2
from scipy.ndimage import gaussian_filter1d
ARREL = Path(__file__).resolve().parents[3]; O = ARREL / '4-RESULTATS/v100_detall_20260925'; R9 = ARREL / '4-RESULTATS/v99_banda_20260925/B'
Z = np.load(O / os.environ.get('D35B_FONT', 'D29_primerencs_20_35_temps.npz')); by0, by1, bx0, bx1 = [int(v) for v in Z['box']]; LX, LY, RL = [float(v) for v in Z['centre']]
esc = json.loads((R9 / 'lineal_v99_franja/A3C_FRANJA_SILUETA.json').read_text())['escales']; cF = [esc[f'c_F{c}'][0] for c in range(3)]
Q9 = np.load(R9 / 'lineal_v99_franja/A3C_franja_silueta.npz'); DMIN9 = np.maximum(Q9['DMIN'], 0); NBZ = DMIN9.size
V38 = json.loads((O / os.environ.get('D35B_GUANYS', 'D38_DETALL_CONTRA_VERITAT.json')).read_text())
BANDES = ['2-4', '4-8', '8-16']; cent = []; gs = {b: [] for b in BANDES}
for k, v in V38.items():
    lo, hi = [float(x) for x in k.split('-')]
    if (lo, hi) in ((2.0, 2.5),): continue           # calaix solapat amb 1,5–2,5 (mateixos píxels)
    cent.append((lo + hi) / 2); [gs[b].append(max(0.0, min(1.0, v[b]['pendent_B_sobre_A']))) for b in BANDES]
o = np.argsort(cent); cent = np.array(cent)[o]; gs = {b: np.array(gs[b])[o] for b in BANDES}
P = Z['RGB']; L = (cF[0] * P[..., 0] + 2 * cF[1] * P[..., 1] + cF[2] * P[..., 2]) / 4; ok = (Z['NF'] >= 3) & (L > 0); DX = Z['DREAL_MAX']
DR_, DS_ = 0.25, 0.5; rr = np.arange(-1.0, 16.0, DR_); nth = int(round(2 * np.pi * RL / DS_)); tt = np.arange(nth) * 2 * np.pi / nth
R_, T_ = np.meshgrid(RL + rr, tt, indexing='ij'); mx = (LX + R_ * np.cos(T_) - bx0).astype(np.float32); my = (LY - R_ * np.sin(T_) - by0).astype(np.float32)
a = cv2.remap(np.where(ok, L, 0).astype(np.float32), mx, my, cv2.INTER_LINEAR); w = cv2.remap(ok.astype(np.float32), mx, my, cv2.INTER_LINEAR)
OK = w > 0.999; X = np.where(OK, np.log(np.maximum(a / np.maximum(w, 1e-6), 1e-30)), 0.0); DXp = cv2.remap(DX.astype(np.float32), mx, my, cv2.INTER_NEAREST)
def gt(s):
    ww = OK.astype(float); return gaussian_filter1d(X * ww, s / DS_, axis=1, mode='wrap') / np.maximum(gaussian_filter1d(ww, s / DS_, axis=1, mode='wrap'), 1e-6)
G = {s: gt(s) for s in (2, 4, 8, 16)}; B = {'2-4': G[2] - G[4], '4-8': G[4] - G[8], '8-16': G[8] - G[16]}
tall = np.clip((DXp - 2.75) / 0.75, 0, 1)            # zero per sota de D_real 2,75; complet a 3,5
delta = np.zeros_like(X)
for b in BANDES: delta += np.interp(DXp, cent, gs[b], left=0.0, right=gs[b][-1]) * B[b]
delta = np.where(OK, delta * tall, 0.0)
thp_ = np.degrees(tt)
if os.environ.get('D35B_EXCLOU'):   # V101: cap capa on manen les capes d'interiors de Pere (k no mesurada; protuberància esquerra retallada)
    e0, e1 = [float(v) for v in os.environ['D35B_EXCLOU'].split(',')]
    def ss_(x, a_, b_): u = np.clip((x - a_) / (b_ - a_), 0, 1); return u * u * (3 - 2 * u)
    delta *= (1 - ss_(thp_, e0 - 5, e0) * (1 - ss_(thp_, e1, e1 + 5)))[None, :]
yy, xx = np.mgrid[by0:by1, bx0:bx1]; r_ = np.hypot(xx - LX, yy - LY); t_ = np.arctan2(-(yy - LY), xx - LX) % (2 * np.pi)
ri = ((r_ - RL - rr[0]) / DR_).astype(np.float32); ti = (t_ / (2 * np.pi) * nth).astype(np.float32)
dC = cv2.remap(delta.astype(np.float32), ti, ri, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
d = r_ - RL; th = np.degrees(t_); dd = d - DMIN9[(th / 360 * NBZ).astype(int) % NBZ]
def ss(x, a_, b_): u = np.clip((x - a_) / (b_ - a_), 0, 1); return u * u * (3 - 2 * u)
alfa = (ss(DX, 2.75, 3.5) * (1 - ss(dd, 0.5, 2.0)) * ok * (d < 15)).astype(np.float32)
if os.environ.get('D35B_EXCLOU'):
    e0, e1 = [float(v) for v in os.environ['D35B_EXCLOU'].split(',')]; alfa = (alfa * (1 - ss(th, e0 - 5, e0) * (1 - ss(th, e1, e1 + 5)))).astype(np.float32)
SORT_ = os.environ.get('D35B_SORTIDA', 'CAPA_DETALL_BANDA_FINAL')
np.savez_compressed(O / f'{SORT_}.npz', box=Z['box'], delta=dC.astype(np.float32), alfa=alfa)
thp = np.degrees(tt); rep = dict(guanys_per_Dreal=dict(D=cent.tolist(), **{b: gs[b].round(3).tolist() for b in BANDES}), sectors={})
for a0, a1 in ((75, 105), (105, 135), (205, 235), (235, 255)):
    sel = ((thp - a0) % 360) < ((a1 - a0) % 360); r = {}
    for lo, hi in ((0.5, 1.5), (1.5, 2.5), (2.5, 3.5), (3.5, 5.0)):
        rows = (rr >= lo) & (rr < hi); m = OK[rows][:, sel]
        if m.sum() > 50: r[f'd {lo}-{hi}'] = dict(Dreal_mediana=round(float(np.median(DXp[rows][:, sel][m])), 2), rms_delta=round(float(np.std(delta[rows][:, sel][m])), 4))
    rep['sectors'][f'{a0}-{a1}'] = r; print(a0, a1, r)
(O / f'{SORT_}.json').write_text(json.dumps(rep, ensure_ascii=False, indent=1)); print('guanys', rep['guanys_per_Dreal'])
