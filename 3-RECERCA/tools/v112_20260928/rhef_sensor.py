"""V112 sensor boundary pilot. Topological support classification does not synthesize samples."""
"""RHEF local per sectors amb PARELLS SIMÈTRICS (V98). És v86_operadors.rhef_native_cdf amb un sol canvi: a cada cel·la (radi, sector),
el conjunt de referència del rang són NOMÉS les mostres θc ± δ que tenen totes dues dada (com els parells simètrics de la WOW V95).
Per què (punt 3 de Pere, capa 46 més negra arran del limbe): la Lluna de presentació està desplaçada 14 px del Sol, i a un radi solar fix
arran del limbe la dada d'un sector només existeix cap a un costat; el primer píxel es comparava amb mostres d'un sol costat (més brillants
o més fosques pel gradient azimutal) i sortia amb rang extrem. A la V93 ho tapava el farcit inventat dins de la Lluna (a4v, continua_ln).
Amb el sector complet, el conjunt és idèntic (el mateix rang que la V97); a la vora el conjunt es fa simètric i petit; si queda amb menys
de 50 mostres, aquella cel·la no vota (com abans). També es pot afinar el pas dels sectors (step_deg) perquè el centre quedi a prop del píxel.
2a iteració (detrend=True): el primer píxel de cada anell queda a l'EXTREM del conjunt simètric (lluny del seu centre θc), i el gradient
azimutal l'esbiaixa. Allà (asimetria a = |θq − θc| / δmax ≥ 0,35), el rang es calcula sobre els residus d'una recta ajustada al conjunt
(p − β·(θ − θc)), barrejat amb el rang pla amb smoothstep(a, 0,35, 0,8). Amb el sector complet (δmax = S/2, |θq − θc| ≤ pas/2) a ≤ 0,25:
EXACTAMENT el rang pla de sempre."""
import numpy as np, cv2, time
from scipy.ndimage import gaussian_filter1d, binary_fill_holes
def rhef_local_sim(a, m, r, t, S_deg, step_deg, cx, cy, log=print, dr=.5, nt=16384, simetric=True, detrend=False, nmin=50):
    idx = np.flatnonzero(m); rv = r.ravel()[idx]; ri = np.floor(rv).astype(int); lv = np.log(a.ravel()[idx]); n = np.bincount(ri); mu = np.bincount(ri, weights=lv) / np.maximum(n, 1); nodes = np.arange(len(n)); ok = n > 0; mu = np.interp(nodes, nodes[ok], mu[ok]); mu = gaussian_filter1d(mu, 16, mode='nearest')
    norm = np.zeros(a.shape, np.float32); norm.ravel()[idx] = lv - np.interp(rv, nodes + .5, mu); r0 = max(0, int(np.floor(rv.min())) - 1); nr = int(np.ceil((rv.max() - r0) / dr)) + 2
    b = np.floor((rv - r0) / dr).astype('int32'); fr = ((rv - r0) / dr - b).astype('float32'); ang = np.degrees(t.ravel()[idx]) % 360; K_ = int(round(360 / step_deg)); k0 = (ang / step_deg).astype('int32') % K_; wk = (ang / step_deg - k0).astype('float32')
    query = norm.ravel()[idx]; order = np.argsort(b, kind='stable'); cuts = np.searchsorted(b[order], np.arange(nr + 1)); theta = np.arange(nt, dtype='float32') * 2 * np.pi / nt; half = int(round(nt * S_deg / 720))
    centers = np.round(np.arange(K_) * step_deg * nt / 360).astype(int); sectors = [(np.arange(-half, half + 1) + c) % nt for c in centers]; out = np.zeros(len(idx), np.float32); denout = np.zeros(len(idx), np.float32); mf = m.astype('float32'); cache = {}; t0 = time.time(); sensor = binary_fill_holes(m).astype(np.float32); newout=np.full(len(idx),0.5,np.float32); affected=np.zeros(len(idx),np.float32)
    def cells(i):
        rad = np.float32(r0 + i * dr); mx = (cx + rad * np.cos(theta))[None, :].astype('float32'); my = (cy + rad * np.sin(theta))[None, :].astype('float32')
        wm = cv2.remap(mf, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[0]; p = cv2.remap(norm, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[0] / np.maximum(wm, 1e-8); good = wm > .999
        sensor_good = cv2.remap(sensor, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[0] > .999
        res = []; uu = np.arange(-half, half + 1) * 360.0 / nt   # desplaçament angular (graus) de cada mostra respecte del centre
        for ix in sectors:
            g = good[ix]
            if simetric: g = g & g[::-1]           # ix és simètric respecte del centre: g[::-1] és la mostra mirall θc − δ ↔ θc + δ
            v = p[ix][g]; partial_sensor = not bool(np.all(sensor_good[ix]))
            if detrend and partial_sensor and v.size >= nmin:
                u = uu[g]; dmax = float(np.abs(u).max()); beta = float(np.sum(u * (v - v.mean())) / max(np.sum(u * u), 1e-12))
                res.append((np.sort(v), np.sort(v - beta * u), beta, dmax, partial_sensor))
            else: res.append((np.sort(v), None, 0.0, float(S_deg / 2), partial_sensor))
        return res
    for i in range(nr):
        ii = order[cuts[i]:cuts[i + 1]]
        if not len(ii): continue
        for j in [i, i + 1]:
            if j not in cache: cache[j] = cells(j)
        for j, wr in [(i, 1 - fr[ii]), (i + 1, fr[ii])]:
            for kk, ww in [(k0[ii], 1 - wk[ii]), ((k0[ii] + 1) % K_, wk[ii])]:
                for k in np.unique(kk):
                    vals, vdet, beta, dmax, partial_sensor = cache[j][k]
                    use = kk == k; ix = ii[use]; weight = wr[use] * ww[use]
                    if partial_sensor: affected[ix] += weight
                    if len(vals) < nmin: continue          # V98: amb poques mostres el rang no és fiable (Gilly i Cranmer 2025); aquella cel·la no vota
                    use = kk == k; ix = ii[use]; weight = wr[use] * ww[use]; rank = (np.searchsorted(vals, query[ix], side='left') + np.searchsorted(vals, query[ix], side='right')) / (2 * len(vals))
                    rank_old=rank.copy()
                    if vdet is not None:
                        uq = ((ang[ix] - k * step_deg + 180) % 360) - 180; asim = np.abs(uq) / max(dmax, 1e-6)
                        wd = np.clip((asim - 0.35) / 0.45, 0, 1); wd = wd * wd * (3 - 2 * wd)
                        if (wd > 0).any():
                            qd = query[ix] - beta * uq; rd = (np.searchsorted(vdet, qd, side='left') + np.searchsorted(vdet, qd, side='right')) / (2 * len(vdet)); rank = (1 - wd) * rank + wd * rd
                    out[ix] += weight * rank_old; denout[ix] += weight
                    confidence = float(np.clip((len(vals)-nmin)/nmin,0,1)) if partial_sensor else 1.0; confidence=confidence*confidence*(3-2*confidence)
                    newout[ix] += weight*confidence*(rank-0.5)
        for j in list(cache):
            if j < i: del cache[j]
        if i % 2000 == 0: log(f'  RHEF local {S_deg:.0f}° (simètric={simetric}, pas {step_deg}°) radi {i}/{nr} ({time.time() - t0:.0f}s)')
    result = np.full(a.shape, np.nan, np.float32); result.ravel()[idx] = np.where(affected>0, newout, np.where(denout > 0, out / np.maximum(denout, 1e-9), np.nan)); return result
