"""m8 · Prova CEL contra SENSOR per temps: el traç es mou amb el sensor (deriva de la Vixen ~25 px al llenç entre t = 24 s i t = 106 s;
salt de 1.110 px de la Sony entre A i B) o és quiet al llenç? Per a cada traç i grup de fotogrames (Vixen primers ≤ 40 s, Vixen 10 s,
Vixen darrers ≥ 85 s; Sony A llargs; Sony B llargs): perfil perpendicular (mitjana al llarg, graella 1/4, contrast v/g(σ12 cel·les) − 1),
posició del solc per correlació amb el perfil del grup central (subpíxel), i la posició on seria si fos fix al sensor.
Sortida: M8_DERIVA.json."""
import sys, json
from pathlib import Path
import numpy as np, cv2
sys.path.insert(0, str(Path(__file__).resolve().parent)); from comu_marrons import *
g = json.loads((OUT / 'M3_GEOMETRIA.json').read_text()); CR = ARREL / '4-RESULTATS/v97_refundacio_20260924/cadena_raw/sources_v36/cau'; Q = 4
GRUPS = {'vixen_primers': ('vixen', lambda m: m['t'] <= 40 and m['exp'] >= 0.25), 'vixen_10s': ('vixen', lambda m: m['exp'] >= 10),
         'vixen_darrers': ('vixen', lambda m: m['t'] >= 85 and m['exp'] >= 0.25), 'sony_A': ('sony', lambda m: m['group'] == 'sony_A' and m['exp'] >= 1),
         'sony_B': ('sony', lambda m: m['group'] == 'sony_B' and m['exp'] >= 1)}
def perfil_grup(tren, sel, tr):
    z = g[str(tr['k'])]; c = np.array(z['centre']); d = np.array(z['direccio']); n = np.array([-d[1], d[0]]); L = z['llarg']
    s = np.arange(-L / 2, L / 2 + 1e-6, 4.0); t = np.arange(-200, 200.01, 1.0)
    X = (((c[0] + s[:, None] * d[0] + t[None, :] * n[0]) - 1.5) / Q).astype(np.float32); Y = (((c[1] + s[:, None] * d[1] + t[None, :] * n[1]) - 1.5) / Q).astype(np.float32)
    meta = json.loads((CR / f'{tren}_meta.json').read_text())['frames']; V = np.load(CR / f'{tren}_v.npy', mmap_mode='r'); Wt = np.load(CR / f'{tren}_w.npy', mmap_mode='r')
    xa, xb = int(max(0, X.min() - 40)), int(min(V.shape[2], X.max() + 40)); ya, yb = int(max(0, Y.min() - 40)), int(min(V.shape[1], Y.max() + 40))
    num = np.zeros(len(t)); den = 0.0; noms = []; ts = []
    for j, m in enumerate(meta):
        if not sel(m): continue
        v = np.asarray(V[j, ya:yb, xa:xb], np.float32); w = np.asarray(Wt[j, ya:yb, xa:xb], np.float32); ok = (w > 0) & np.isfinite(v) & (v > 0)
        Pm = cv2.remap(ok.astype(np.float32), X - xa, Y - ya, cv2.INTER_NEAREST, borderValue=0)
        if Pm[:, np.abs(t) <= 150].mean() < 0.9: continue
        wf = ok.astype(np.float32); vv = np.where(ok, v, 0)
        sm = cv2.GaussianBlur(vv * wf, (0, 0), 12) / np.maximum(cv2.GaussianBlur(wf, (0, 0), 12), 1e-6)
        r = np.where(ok, vv / np.maximum(sm, 1e-12) - 1, np.nan).astype(np.float32)
        with np.errstate(all='ignore'): pr = np.nanmean(cv2.remap(r, X - xa, Y - ya, cv2.INTER_LINEAR, borderValue=np.nan), 0)
        num += m['exp'] * np.nan_to_num(pr); den += m['exp']; noms.append(m['name']); ts.append(m['t'])
    return (t, num / den if den else None, noms, ts)
def posicio(t, pr, ref):
    """desplaçament de pr respecte de ref (±40 px), per correlació en la finestra |t| ≤ 80, amb paràbola subpíxel."""
    k = np.abs(t) <= 80; best = []
    for sh in range(-40, 41):
        a = np.interp(t[k] - sh, t, ref); b = pr[k]; a = a - a.mean(); bb = b - b.mean()
        best.append((a * bb).sum() / np.sqrt((a * a).sum() * (bb * bb).sum() + 1e-30))
    best = np.array(best); i = int(np.argmax(best))
    if 0 < i < len(best) - 1:
        y0, y1, y2 = best[i - 1], best[i], best[i + 1]; dx = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-30)
    else: dx = 0
    return float(i - 40 + dx), float(best[i])
res = {}
for tr in TRACOS:
    P = {k: perfil_grup(tren, sel, tr) for k, (tren, sel) in GRUPS.items()}
    fila = {}
    for ref_nom in ('vixen_10s', 'sony_A', 'sony_B'):
        t, ref, _, _ = P[ref_nom]
        if ref is None: continue
        for k, (tt, pr, noms, ts) in P.items():
            if pr is None or k == ref_nom: continue
            if k.split('_')[0] != ref_nom.split('_')[0] and not (k.startswith('sony') and ref_nom.startswith('sony')): continue
            sh, cc = posicio(t, pr, ref); j = int(np.argmin(np.abs(t)))
            fila[f'{k}_contra_{ref_nom}'] = dict(desplacament_px=sh, correlacio=cc, n=len(noms), t_mitja_s=float(np.mean(ts)))
    def _solc(v):
        if v[1] is None: return None
        return float(np.mean(v[1][np.abs(v[0]) <= 4]) - np.mean(v[1][(np.abs(v[0]) >= 24) & (np.abs(v[0]) <= 160)]))
    res[tr['k']] = dict(grups={k: dict(n=len(v[2]), solc_t0=_solc(v)) for k, v in P.items()}, desplacaments=fila)
    print(f"T{tr['k']}", {k: (v['n'], None if v['solc_t0'] is None else round(v['solc_t0'] * 1e4, 1)) for k, v in res[tr['k']]['grups'].items()}, '|', {k: (round(v['desplacament_px'], 1), round(v['correlacio'], 2)) for k, v in fila.items()}, flush=True)
desa(OUT / 'M8_DERIVA.json', res)
