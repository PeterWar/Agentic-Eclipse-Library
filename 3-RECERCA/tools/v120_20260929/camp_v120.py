"""camp_v120 (V120, 29-09-2026) · EL CAMP DE DESPLAÇAMENT SONY → VIXEN DEFINITIU, autosuficient (tots els paràmetres són al JSON del model).
u_X(x) = afí_X(x) + τ_X(r) · r · δθ_X(ρ, θ) · e_t        (u = posició a V − posició a X, px del llenç final, x cap a la dreta, y cap avall)
  · afí_X: 6 paràmetres, fixats NOMÉS per les estrelles (S/N ≥ 6 a totes dues fonts);
  · δθ_X: correcció NOMÉS tangencial, harmònics k ≤ K × Legendre j ≤ J en ρ = ln r normalitzat a [R0, R1] R☉ (fora, ρ es limita a l'extrem),
    ajustada als residus dels raigs; τ_X = 1 fins a T0 R☉ i 0 a T1 R☉ (smoothstep).
Triat al f4c (validació creuada per sectors de 30° i estrelles deixant-ne una fora): A amb K 2, J 2; B amb K 3, J 2; R0 1,3, R1 5,0, τ 4,5 → 6,0.
ESVAÏMENT A LA VORA DEL MARC (si el model porta «vora»; f10): u × smoothstep(d_X / L), amb d_X la distància a la vora del marc del tren X
(MARC_X_dist_quart.npy, a 1/4, bilineal). A la vora u = 0: el marc de la Sony no es mou i res no queda sense dada (lliçó de la primera V120).
Ús com a mòdul: camp(model, X, x, y) → (u_x, u_y). Ús com a guió: camp_v120.py <carpeta_f1> → CAMP_V120.json (a partir dels F4C_*_t45_MODEL.json)."""
import sys, json, numpy as np
from pathlib import Path
from numpy.polynomial import legendre as LG
def _rho_n(r_rs, R0, R1): return np.clip((np.log(np.clip(r_rs, R0, R1)) - np.log(R0)) / (np.log(R1) - np.log(R0)) * 2 - 1, -1, 1)
def _base(r_rs, th, K, J, R0, R1):
    P = np.stack([LG.legval(_rho_n(r_rs, R0, R1), np.eye(J + 1)[j]) for j in range(J + 1)], 1); cols = []
    for k in range(K + 1):
        for j in range(J + 1):
            cols.append(np.cos(k * th) * P[:, j])
            if k > 0: cols.append(np.sin(k * th) * P[:, j])
    return np.stack(cols, 1)
_DIST = {}
def esvaiment(model, X, x, y):
    v = model.get('vora')
    if not v: return 1.0
    if X not in _DIST: _DIST[X] = np.load(Path(__file__).resolve().parents[3] / v['dist'][X])
    from scipy import ndimage as ndi
    d = ndi.map_coordinates(_DIST[X], [np.ravel(y) / v['factor'], np.ravel(x) / v['factor']], order=1, mode='nearest').reshape(np.shape(x))
    t = np.clip(d / v['L_px'], 0, 1); return t * t * (3 - 2 * t)
def camp(model, X, x, y):
    SOL, RS, N = model['SOL'], model['RS'], model['N']; m = model['models'][X]
    x = np.asarray(x, np.float64); y = np.asarray(y, np.float64); X_, Y_ = (x - SOL[0]) / N, (y - SOL[1]) / N; a = m['afi']
    ux = a[0] + a[1] * X_ + a[2] * Y_; uy = a[3] + a[4] * X_ + a[5] * Y_
    dx, dy = x - SOL[0], -(y - SOL[1]); r = np.hypot(dx, dy); th = np.arctan2(dy, dx); rr = r / RS
    t = np.clip((rr - m['T0']) / (m['T1'] - m['T0']), 0, 1); tau = 1 - t * t * (3 - 2 * t)
    dth = (_base(rr.ravel(), th.ravel(), m['K'], m['J'], m['R0'], m['R1']) @ np.asarray(m['dtheta'])).reshape(r.shape) * tau
    ut = r * dth; e = esvaiment(model, X, x, y); return (ux + ut * (-np.sin(th))) * e, (uy + ut * (-np.cos(th))) * e
if __name__ == '__main__':
    F1 = Path(sys.argv[1]).resolve()
    TRIA = {'A': ('F4C_K2J2_t45_MODEL.json', 2, 2), 'B': ('F4C_K3J2_t45_MODEL.json', 3, 2)}
    out = dict(conveni='u = posició a V − posició a X (px del llenç final, x cap a la dreta, y cap avall); X\'(q) = X(q − u(q))', models={})
    for X, (fn, K, J) in TRIA.items():
        src = json.load(open(F1 / fn)); assert src['KT'] == K and src['JT'] == J, (fn, src['KT'], src['JT'])
        out['SOL'], out['RS'], out['N'] = src['SOL'], src['RS'], src['N']
        out['models'][X] = dict(src['models'][X], K=K, J=J, R0=1.3, R1=5.0, T0=4.5, T1=6.0, font=fn)
    json.dump(out, open(F1 / 'CAMP_V120.json', 'w'), ensure_ascii=False, indent=1)
    # comprovació: el camp d'aquest mòdul = el del f4c amb els mateixos paràmetres, a una graella de punts
    import importlib.util, os
    for X, (fn, K, J) in TRIA.items():
        os.environ.update(F4_KT=str(K), F4_JT=str(J), F4_R1='5.0', F4_T0='4.5', F4_T1='6.0')
        spec = importlib.util.spec_from_file_location(f'f4c_{X}', Path(__file__).with_name('f4c_model_final.py')); f4c = importlib.util.module_from_spec(spec); spec.loader.exec_module(f4c)
        xs, ys = np.meshgrid(np.linspace(300, 10250, 40), np.linspace(300, 7200, 30)); a = f4c.camp(json.load(open(F1 / fn)), X, xs, ys); b = camp(out, X, xs, ys)
        print(X, 'diferència màxima amb el f4c (px):', float(max(np.abs(a[0] - b[0]).max(), np.abs(a[1] - b[1]).max())))
