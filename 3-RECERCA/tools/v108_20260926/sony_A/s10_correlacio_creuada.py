"""s10 · A QUÈ ESTÀ LLIGAT el patró fi que comparteixen les dues meitats d'un apuntament? Correlació creuada 2D (banda σ 2/20 px) entre
meitats independents, en funció del desplaçament s del llenç (±16 px). Un patró del CEL té el pic a s = 0; un patró fix al SENSOR, al
desplaçament que la deriva del Sol sobre el sensor predit entre les dues meitats (A: ~2 px, B: ~11 px al llenç). Parelles: A1×A2, B1×B2,
A1×B2, A2×B1 (aquestes dues, només cel: sensors a 749 px). Predicció calculada amb el mapatge de cada fotograma (s3/MAPATGE.json),
mitjana ponderada pel pes G a la zona. Sortida: S10_CORRELACIO_CREUADA.json i la vista dels mapes de correlació."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_sonyA import *
D = OUT / 'meitats_flat2d'; YM = 4200; RB = json.loads((D / 'REBUT.json').read_text()); MP = json.loads((OUT / 'fotogrames_flat2d/MAPATGE.json').read_text())
inv = np.array(MP['inv_common_to_final']); CX, CY, K, ca, sa, dB = MP['CX'], MP['CY'], MP['k'], MP['ca'], MP['sa'], MP['delta_B_rad']
def a_sensor(x, y, f):
    qx = inv[0, 0] * x + inv[0, 1] * y + inv[0, 2]; qy = inv[1, 0] * x + inv[1, 1] * y + inv[1, 2]; dx = (qx - CX) * K; dy = (qy - CY) * K
    if f['grup'] == 'sony_B': c_, s_ = np.cos(dB), np.sin(dB); dx, dy = c_ * dx - s_ * dy, s_ * dx + c_ * dy
    return np.array([ca * dx + sa * dy + f['sol_x'] + f['cx'], -sa * dx + ca * dy + f['sol_y'] + f['cy']])
def jac(f):
    p0 = a_sensor(5000., 2000., f); return np.stack([a_sensor(5001., 2000., f) - p0, a_sensor(5000., 2001., f) - p0], 1)
# pes efectiu de cada fotograma a la zona exterior: exp² (la variància baixa amb l'exposició) només dels que hi tenen dada (≥ 0,125 s)
def sol_mitja(noms):
    ws = np.array([MP['fotogrames'][n]['exp'] ** 2 if MP['fotogrames'][n]['exp'] >= 0.1 else 0 for n in noms]); P = np.array([[MP['fotogrames'][n]['sol_x'] + MP['fotogrames'][n]['cx'], MP['fotogrames'][n]['sol_y'] + MP['fotogrames'][n]['cy']] for n in noms])
    return (ws[:, None] * P).sum(0) / ws.sum()
pred = {}
for p1, p2 in (('A1', 'A2'), ('B1', 'B2')):
    n1 = [u['nom'] for u in RB['meitats'][p1]]; n2 = [u['nom'] for u in RB['meitats'][p2]]
    d_sol = sol_mitja(n2) - sol_mitja(n1); J = jac(MP['fotogrames'][n2[0]])
    pred[f'{p1}_{p2}'] = np.linalg.solve(J, -d_sol)   # on apareix a la 2a meitat, al llenç, un patró fix al sensor (respecte de la 1a)
    print(f'{p1}→{p2}: Δsol sensor {d_sol.round(2)} px → desplaçament al llenç si és fix al sensor {pred[f"{p1}_{p2}"].round(2)} px', flush=True)
yy, xx = np.mgrid[0:YM, 0:W].astype(np.float32); rs = np.hypot(xx - SOL[0], yy - SOL[1]) / RSOL; del xx, yy
res = dict(prediccio_desplacament_llenc_si_sensor={k: v.tolist() for k, v in pred.items()})
for espai in ('Gcam', 'G'):
    R = {}; M = None
    for mn in ('A1', 'A2', 'B1', 'B2'):
        z = np.load(D / f'{mn}.npz'); img = z[espai]; w = z['w']; ok = np.isfinite(img) & (img > 0) & (w > 0.05 * np.nanmax(w))
        R[mn] = rel_map(np.where(ok, img, 0).astype(np.float32), sgran=20.0, sfi=2.0, erosio=61); M = np.isfinite(R[mn]) if M is None else (M & np.isfinite(R[mn]))
    zona = M & (rs > 3.0) & (rs < 9.5)
    for mn in R:
        v = R[mn][zona]; med = np.median(v); mad = 1.4826 * np.median(np.abs(v - med)); zona &= np.abs(np.nan_to_num(R[mn]) - med) < 6 * mad
    S = 16; out = {}
    for p1, p2 in (('A1', 'A2'), ('B1', 'B2'), ('A1', 'B2'), ('A2', 'B1'), ('A1', 'B1'), ('A2', 'B2')):
        a = np.where(zona, R[p1] - R[p1][zona].mean(), 0).astype(np.float32); b = np.where(zona, R[p2] - R[p2][zona].mean(), 0).astype(np.float32)
        # correlació creuada per FFT (normalitzada per les energies); c[dy,dx] = Σ a(x)·b(x + s)
        Fa = np.fft.rfft2(a); Fb = np.fft.rfft2(b); cc = np.fft.irfft2(np.conj(Fa) * Fb, s=a.shape)
        cc = np.fft.fftshift(cc); cy, cx = YM // 2, W // 2; win = cc[cy - S:cy + S + 1, cx - S:cx + S + 1] / np.sqrt((a * a).sum() * (b * b).sum())
        iy, ix = np.unravel_index(np.argmax(win), win.shape); pk = (ix - S, iy - S)
        # refinament subpíxel (paràbola)
        def sub(v_m, v_0, v_p): d = v_m - 2 * v_0 + v_p; return 0.0 if d == 0 else 0.5 * (v_m - v_p) / d
        sx = sub(win[iy, ix - 1], win[iy, ix], win[iy, ix + 1]) if 0 < ix < 2 * S else 0.0; sy = sub(win[iy - 1, ix], win[iy, ix], win[iy + 1, ix]) if 0 < iy < 2 * S else 0.0
        anell = win.copy(); anell[S - 6:S + 7, S - 6:S + 7] = np.nan
        out[f'{p1}_{p2}'] = dict(pic=float(win[iy, ix]), pic_a_dx_dy=[pk[0] + sx, pk[1] + sy], a_zero=float(win[S, S]), fons_mediana=float(np.nanmedian(anell)), fons_mad=float(1.4826 * np.nanmedian(np.abs(anell - np.nanmedian(anell)))), mapa=win)
        pr = pred.get(f'{p1}_{p2}')
        print(f"{espai} {p1}×{p2}: pic {win[iy, ix]:+.4f} a (dx, dy) = ({pk[0]+sx:+.2f}, {pk[1]+sy:+.2f}) px · a s=0 {win[S, S]:+.4f} · fons {np.nanmedian(anell):+.4f}±{out[f'{p1}_{p2}']['fons_mad']:.4f}" + (f" · predit si sensor ({pr[0]:+.2f}, {pr[1]:+.2f})" if pr is not None else ''), flush=True)
    res[espai] = out
# vista: mapes de correlació (Gcam), cada un escalat al seu pic
import cv2
tiles = []
for key in ('A1_A2', 'B1_B2', 'A1_B2', 'A2_B1'):
    m = res['Gcam'][key]['mapa']; m = (m - np.median(m)) / max(np.max(np.abs(m - np.median(m))), 1e-9); u8 = np.clip(128 + 127 * m, 0, 255).astype(np.uint8)
    t = cv2.resize(u8, (330, 330), interpolation=cv2.INTER_NEAREST); t = cv2.cvtColor(t, cv2.COLOR_GRAY2BGR); cv2.drawMarker(t, (165, 165), (0, 200, 0), cv2.MARKER_CROSS, 20, 1)
    pr = pred.get(key)
    if pr is not None: cv2.drawMarker(t, (int(165 + pr[0] * 330 / 33), int(165 + pr[1] * 330 / 33)), (0, 0, 255), cv2.MARKER_TILTED_CROSS, 20, 2)
    cv2.putText(t, key.replace('_', ' x '), (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2); tiles.append(t)
img = np.hstack(tiles); cap = np.zeros((60, img.shape[1], 3), np.uint8)
cv2.putText(cap, 'Correlacio creuada entre meitats (G camera, banda s2/s20, 3-9,5 Rsol), +-16 px. Verd: s=0 (cel). Vermell: on cauria si fos fix al sensor.', (8, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
cv2.putText(cap, 'A1 x A2 i B1 x B2: el mateix apuntament; A1 x B2 i A2 x B1: nomes el cel pot correlacionar (sensors a 749 px).', (8, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
cv2.imwrite(str(OUT / 'diag_correlacio_creuada_meitats.png'), np.vstack([cap, img]))
for e in ('Gcam', 'G'):
    for k in res[e]: res[e][k].pop('mapa')
desa(OUT / 'S10_CORRELACIO_CREUADA.json', res)
