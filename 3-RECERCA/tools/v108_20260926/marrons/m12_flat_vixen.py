"""m12 · El flat de la Vixen té les rectes/arcs de T3, T4 i T5? Màster G (subplans 1 i 3) de N flats normals (mediana de fotogrames normalitzats,
menys el pedestal 2048 de la R6 III segons F0.1), dividit pel seu perfil RADIAL (el mateix model que FLAT_RADIAL: centre del sensor declarat,
260 calaixos) → el que el flat radial NO corregeix. Es mostra el residu (passa alt σ 3/40 a la graella del subpla) a tot el sensor i
es marquen on cauen els traços T3, T4 i T5 (llenç → sensor amb la geometria mesurada: eixos del marc de la Vixen al llenç, Sol del fotograma).
Sortida: M12_FLAT_VIXEN.json, flat_vixen_residu_no_radial.npy (1/2 del sensor) i la vista del SENSOR sencer."""
import sys, json, glob
from pathlib import Path
import numpy as np, cv2, rawpy
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
RI = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/raw_inputs/VIXEN'
NF = int(sys.argv[1]) if len(sys.argv) > 1 else 24
fl = sorted(glob.glob(str(RI / 'flats/*.CR3')))
exps = {}
for f in fl:
    with rawpy.imread(f) as r: pass
# totes les exposicions de flats iguals? agafa N fotogrames repartits
sel = fl[::max(1, len(fl) // NF)][:NF]
stack = []
for f in sel:
    with rawpy.imread(f) as r:
        raw = r.raw_image.astype(np.float32); pat = r.raw_pattern; bl = float(np.mean(r.black_level_per_channel))
    g1 = raw[0::2, 1::2] - bl; g2 = raw[1::2, 0::2] - bl       # patró [[0,1],[3,2]] = R G / G B (RGBG)
    g = 0.5 * (g1 + g2); stack.append(g / np.median(g[500:1800, 800:2800]))
M = np.median(np.stack(stack), 0).astype(np.float32); del stack
h, w = M.shape
# el visible al subpla: marges 108/172 del raw → 54/86 al subpla
vy0, vx0 = 54, 86; vis = np.zeros_like(M, bool); vis[vy0:vy0 + 4640 // 2, vx0:vx0 + 6960 // 2] = True
CY, CX = 4760 / 2 / 2, 7144 / 2 / 2            # centre del sensor (raw 2380, 3572) a la graella del subpla
yy, xx = np.mgrid[0:h, 0:w].astype(np.float32); rad = np.hypot(yy - CY, xx - CX); RMAX = float(rad[vis].max()); nb = 260
idx = np.clip((rad / RMAX * nb).astype(np.int32), 0, nb - 1)
s = np.bincount(idx[vis], M[vis], nb); c = np.bincount(idx[vis], None, nb); prof = np.where(c > 75, s / np.maximum(c, 1), np.nan)
prof = np.where(np.isfinite(prof), prof, np.nanmedian(prof)); rad_model = prof[idx]
res = np.where(vis, M / rad_model - 1, 0).astype(np.float32)
np.save(OUT / 'flat_vixen_residu_no_radial.npy', res)
wv = vis.astype(np.float32); ng = lambda x, s_: cv2.GaussianBlur(x * wv, (0, 0), s_) / np.maximum(cv2.GaussianBlur(wv, (0, 0), s_), 1e-6)
SA, SB = float(__import__('os').environ.get('M12_SA', 1.5)), float(__import__('os').environ.get('M12_SB', 20)); hp = np.where(vis, ng(res, SA) - ng(res, SB), 0)
# traços → sensor (raw) a t ≈ 55 s: raw = sol_raw + [(c − Sol)·ux, (c − Sol)·uy]
g = json.loads((OUT / 'M3_GEOMETRIA.json').read_text())
ux = np.array([0.98290, -0.18415]); uy = np.array([0.18415, 0.98290]); sol_raw = np.array([3745.0, 2373.9]); solc = np.array(SOL)
def a_sensor(p): d = np.array(p) - solc; return sol_raw + np.array([d @ ux, d @ uy])
LIM = float(__import__('os').environ.get('M12_LIM', 0.004)); u8 = np.clip(128 + 127 * hp / LIM, 0, 255).astype(np.uint8); rgb = cv2.cvtColor(u8, cv2.COLOR_GRAY2BGR); info = {}
for tr in TRACOS:
    z = g[str(tr['k'])]; p0, p1 = z['extrems']; a0 = a_sensor(p0) / 2; a1 = a_sensor(p1) / 2
    if not (0 <= a0[0] < w and 0 <= a0[1] < h and 0 <= a1[0] < w and 0 <= a1[1] < h): info[tr['k']] = 'fora del sensor de la Vixen'; continue
    # perfil perpendicular del residu del flat al llarg del traç (graella del subpla)
    d = (a1 - a0) / np.linalg.norm(a1 - a0); n = np.array([-d[1], d[0]]); L = np.linalg.norm(a1 - a0)
    s_ = np.arange(0, L, 1.0); t = np.arange(-100, 100.1, 0.5)
    X = (a0[0] + s_[:, None] * d[0] + t[None, :] * n[0]).astype(np.float32); Y = (a0[1] + s_[:, None] * d[1] + t[None, :] * n[1]).astype(np.float32)
    P = cv2.remap(np.where(vis, ng(res, 1.0), np.nan).astype(np.float32), X, Y, cv2.INTER_LINEAR, borderValue=np.nan)
    with np.errstate(all='ignore'): pr = np.nanmean(P, 0)
    q = solc_ = None
    k = (np.abs(t) >= 20) & (np.abs(t) <= 90); aa = np.polyfit(t[k], pr[k], 1); rr = pr - np.polyval(aa, t); j = np.argmin(np.where(np.abs(t) <= 15, rr, np.inf))
    info[tr['k']] = dict(extrems_subpla=[a0.round(1).tolist(), a1.round(1).tolist()], solc_residu_flat=float(rr[j]), t_minim_subpla=float(t[j]), soroll_flancs=float(np.std(rr[k])))
    cv2.line(rgb, tuple(map(int, a0 + 12 * n)), tuple(map(int, a1 + 12 * n)), (0, 0, 255), 1); cv2.line(rgb, tuple(map(int, a0 - 12 * n)), tuple(map(int, a1 - 12 * n)), (0, 0, 255), 1)
    cv2.putText(rgb, f"T{tr['k']}", tuple(map(int, a1 + 20 * n)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2)
    print(f"T{tr['k']} al sensor (subpla) {a0.round(0)}→{a1.round(0)}: solc del residu del flat {rr[j]*1e4:+.1f}‱ a t {t[j]:+.1f} (soroll {np.std(rr[k])*1e4:.1f}‱)", flush=True)
cv2.putText(rgb, f'FLAT Vixen (mediana de {len(sel)} flats, G) / perfil radial - 1, passa alt s{SA:g}/s{SB:g} a +-{LIM*100:g} % - SENSOR sencer (1/2)', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 220, 255), 2)
cv2.imwrite(str(OUT / 'diag_flat_vixen_residu_no_radial_sensor.png'), cv2.resize(rgb, (w * 2 // 3, h * 2 // 3), interpolation=cv2.INTER_AREA))
desa(OUT / 'M12_FLAT_VIXEN.json', dict(flats=[Path(f).name for f in sel], n=len(sel), traços=info, amplitud_residu_p1_p99=np.percentile(res[vis], [1, 99]).tolist()))
