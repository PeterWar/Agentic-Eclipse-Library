"""Operadors dels filtres de la V86 (Claude, 23-09-2026), autocontinguts.

Són els mètodes publicats (NRGF, RHEF, RHEF local, MGN, WOW, WOW bilateral, ACHF isòtrop i ACHF angular) amb la mateixa
recepta i els mateixos paràmetres que els filtres V58/V63 que porta la V84 de Pere (rebuts de 3-RECERCA/tools/v42_20260910/purs,
2-ARXIU/.../v29_profiles_round1 i filters_v58_dependencies), perquè el resultat tingui el mateix aspecte lluny del limbe.
Què canvia respecte de la V58/V85, i per què:
  1. DOMINI: cap filtre veu la franja on el limbe lunar en moviment contamina la suma (norma de Pere del 17-09, research/165);
     la franja es mesura a a2_geometria.py amb els pesos i les distàncies de cada fotograma, no amb la silueta pintada.
  2. CONDICIÓ DE CONTORN dels operadors espacials (MGN, WOW, ACHF isòtrop): fora del domini, perfil radial de ln I (Sol al centre)
     més la continuació suau del residu local per piràmide (pull-push). Continua el nivell local sense graó a la vora del domini;
     no és corona mesurada i la sortida d'aquesta zona no s'usa mai (a4 hi posa la interpolació declarada).
  3. Convolució B3 dilatada escrita aquí amb numpy (reflexió simètrica a les vores del llenç), sense biblioteca compilada.
La resta (anells d'1 px amb radi continu, CDF entre anells veïns, tanh, suavitzat pel S/N, anivellament per anell, rangs de pantalla)
és idèntica a la V58."""
import numpy as np, cv2, gc, time
import numexpr as ne
from scipy.ndimage import gaussian_filter1d
from scipy.interpolate import PchipInterpolator, CubicHermiteSpline
from v86_comu import CX, CY, RS, H, W, log
cv2.setNumThreads(8)
NB = 720; DR = 1.; BLEND = 64.
K = np.array([1, 4, 6, 4, 1], np.float32) / 16

# ---------------------------------------------------------------- utilitats
def gauss(a, s):
    return cv2.GaussianBlur(np.asarray(a, np.float32), (0, 0), s, borderType=cv2.BORDER_REFLECT_101)
def normgauss(a, w, s):
    return gauss(np.where(w > 0, a, 0) * w, s) / np.maximum(gauss(w, s), 1e-8)
def gaussian_t(a, s, truncate=3):
    return cv2.GaussianBlur(np.asarray(a, np.float32), (2 * int(truncate * s + .5) + 1,) * 2, s, borderType=cv2.BORDER_REPLICATE)
def ng(a, m, s, truncate=3):
    return gaussian_t(np.where(m, a, 0), s, truncate) / np.maximum(gaussian_t(m.astype('float32'), s, truncate), 1e-20)
def smoothstep(a, lo, hi):
    q = np.clip((a - lo) / (hi - lo), 0, 1); return q * q * (3 - 2 * q)

# ---------------------------------------------------------------- suavitzat pel S/N i anivellament per anell (V29, idèntics)
def sn_smooth(F, m, sigma):
    w = m.astype(np.float32); levels = np.array([0, .5, 1, 2, 4, 8], np.float32); variance = sigma * sigma; vlevels = levels * levels
    out = np.zeros_like(F); remaining = np.ones_like(F)
    for i, s in enumerate(levels):
        if i == 0: weight = np.clip(1 - variance / vlevels[1], 0, 1); sm = F
        else:
            lo = vlevels[i - 1]; hi = vlevels[min(i + 1, len(levels) - 1)]; v = vlevels[i]
            weight = np.minimum(np.clip((variance - lo) / (v - lo), 0, 1), np.clip((hi - variance) / max(hi - v, 1e-8), 0, 1)) if i < len(levels) - 1 else np.clip((variance - lo) / (v - lo), 0, 1)
            sm = normgauss(F, w, float(s))
        out += weight * sm; remaining -= weight
    assert np.max(np.abs(remaining)) < 2e-6
    return np.where(m, out, 0).astype(np.float32)

def centre_rings(a, m, r):
    rr = r[m]; lo = np.log(20.); hi = np.log(float(rr.max())); nb = 200
    idx = np.clip(((np.log(np.maximum(rr, 1)) - lo) / (hi - lo) * nb).astype(int), 0, nb - 1)
    order = np.argsort(idx, kind='stable'); n = np.bincount(idx, minlength=nb); off = np.r_[0, np.cumsum(n)]
    sx = np.log(np.maximum(rr, 1))[order]; ks = np.flatnonzero(n >= 400)
    nodes = np.array([np.median(sx[off[k]:off[k + 1]]) for k in ks]); vals = a[m][order].copy(); history = []
    for it in range(8):
        p = np.array([np.median(vals[off[k]:off[k + 1]]) for k in ks]); error = float(np.max(np.abs(p))); history.append(error)
        if error <= .03: break
        slopes = PchipInterpolator(nodes, p).derivative()(nodes); slopes[0] = slopes[-1] = 0
        curve = CubicHermiteSpline(nodes, p, slopes, extrapolate=False)
        vals = (vals - curve(np.clip(sx, nodes[0], nodes[-1]))).astype(np.float32)
    assert history[-1] <= .03, history
    unsorted = np.empty_like(vals); unsorted[order] = vals; out = np.zeros_like(a); out[m] = unsorted
    return out, history

def h1_setup(r, m, nb=200):
    rv = r[m]; rmax = float(rv.max()); lo = np.log10(20 / rmax)
    idx = np.clip(((np.log10(np.maximum(rv, 1) / rmax) - lo) / (-lo) * nb).astype(int), 0, nb - 1)
    order = np.argsort(idx, kind='stable'); cuts = np.searchsorted(idx[order], np.arange(nb + 1))
    radii = 10 ** (lo + (np.arange(nb) + .5) / nb * (-lo)) * rmax / RS
    return order, cuts, radii
def h1(a, m, ctx):
    order, cuts, radii = ctx; v = a[m][order]; rows = []
    for k in range(len(radii)):
        q = v[cuts[k]:cuts[k + 1]]
        if len(q) < 400: continue
        med = float(np.median(q)); rows.append({'R': radii[k], 'n': len(q), 'median': med, 'error': abs(med - .5)})
    worst = max(rows, key=lambda x: x['error'])
    return {'worst': worst, 'PASS': worst['error'] <= .05, 'rings': rows}

# ---------------------------------------------------------------- condició de contorn nova (2): perfil + residu continuat
def perfil_ln(L, m, r):
    """Perfil azimutal mitjà de ln I per anells d'1 px (centre = Sol), cap endins des del primer anell SENCER amb el seu pendent (com el farcit A)."""
    ri = np.round(r).astype('int32'); n = np.bincount(ri[m], minlength=int(ri.max()) + 1); s = np.bincount(ri[m], weights=L[m].astype('float64'), minlength=len(n))
    prof = np.where(n > 0, s / np.maximum(n, 1), np.nan); nodes = np.arange(len(n))
    full = np.flatnonzero(n >= 0.999 * 2 * np.pi * np.maximum(nodes, 1)); first = int(full[full > 0.9 * RS][0]); k = np.arange(first, first + 20); slope = float(np.polyfit(k, prof[k], 1)[0])
    p = prof.copy(); p[:first] = prof[first] + slope * (np.arange(first) - first); last = int(np.flatnonzero(np.isfinite(p))[-1]); p[last + 1:] = p[last]
    bad = ~np.isfinite(p); p[bad] = np.interp(nodes[bad], nodes[~bad], p[~bad])
    return nodes, p, dict(primer_anell_sencer_px=first, pendent_ln_per_px=slope)

def pull_push(e, known, levels=12):
    """Continuació suau d'un camp conegut només a `known`: piràmide de (Σw·e, Σw) amb pyrDown i reconstrucció amb pyrUp.
    Prop de la vora hereta el nivell de l'escala fina; lluny, el d'escales cada cop més grosses. Els valors coneguts no es toquen."""
    num = [np.where(known, e, 0).astype(np.float32)]; den = [known.astype(np.float32)]
    for l in range(levels):
        if min(num[-1].shape) < 8: break
        num.append(cv2.pyrDown(num[-1])); den.append(cv2.pyrDown(den[-1]))
    est = np.where(den[-1] > 1e-6, num[-1] / np.maximum(den[-1], 1e-6), 0).astype(np.float32)
    for l in range(len(num) - 2, -1, -1):
        up = cv2.pyrUp(est, dstsize=(num[l].shape[1], num[l].shape[0]))
        w = np.clip(den[l], 0, 1); est = (w * np.where(den[l] > 1e-6, num[l] / np.maximum(den[l], 1e-6), 0) + (1 - w) * up).astype(np.float32)
    return np.where(known, e, est).astype(np.float32)

def relaxa(f, known, iters=200):
    """Relaxació de Laplace (Jacobi, 4 veïns) només als píxels desconeguts: fa la continuació contínua a la vora del domini
    (sense graó), amb els valors observats fixos. Sobre la sortida del pull-push convergeix de pressa."""
    f = f.astype(np.float32).copy(); unk = ~known; k = np.array([[0, .25, 0], [.25, 0, .25], [0, .25, 0]], np.float32)
    for _ in range(iters):
        g = cv2.filter2D(f, -1, k, borderType=cv2.BORDER_REPLICATE); f[unk] = g[unk]
    return f

def continua_ln(L, m, r):
    """ln I fora del domini = perfil radial + residu continuat. Retorna el camp complet i el rebut."""
    nodes, p, info = perfil_ln(L, m, r); P = np.interp(r, nodes, p).astype(np.float32)
    e = relaxa(pull_push(np.where(m, L - P, 0).astype(np.float32), m), m)
    return np.where(m, L, P + e).astype(np.float32), dict(info, metode='perfil radial de ln I (anells d1 px, centre Sol, cap endins amb el pendent del primer anell sencer) + residu continuat per piràmide pull-push i 200 iteracions de relaxació de Laplace (continu a la vora del domini); valors observats intactes')

# ---------------------------------------------------------------- E1 · NRGF, NRGF estès cap endins, RHEF (V36/V42, idèntic)
def ring_stats(v, ids, nr):
    count = np.bincount(ids, minlength=nr); s = np.bincount(ids, weights=v, minlength=nr); s2 = np.bincount(ids, weights=v * v, minlength=nr)
    mean = np.divide(s, count, out=np.zeros(nr), where=count > 0); std = np.sqrt(np.maximum(0, np.divide(s2, count, out=np.zeros(nr), where=count > 0) - mean * mean)); return count, mean, std
def complete_from_partial(mean, std, ids, tb, v, rings, ref_rings):
    ksel = np.isin(ids, ref_rings); z = (v[ksel] - mean[ids[ksel]]) / np.maximum(std[ids[ksel]], 1e-12)
    P = np.bincount(tb[ksel], weights=z, minlength=NB) / np.maximum(np.bincount(tb[ksel], minlength=NB), 1); P = P - P.mean(); varP = float(np.var(P))
    mean_u = mean.copy(); std_u = std.copy(); ok = np.ones(len(mean), bool)
    for i in rings:
        k = ids == i
        if k.sum() < 50: ok[i] = False; continue
        Pp = P[tb[k]]; mp = float(Pp.mean()); vp = float(np.var(Pp)); sig_full = std[i] / np.sqrt(max(vp + 1 - varP, 0.05)); mean_u[i] = mean[i] - sig_full * mp; std_u[i] = sig_full
    return mean_u, std_u, ok, P, varP
def radial_v36(a, m, r, t):
    ri = np.floor(r).astype('int32'); nr = int(ri.max()) + 1; ids = ri[m]; v = a[m].astype('float64'); tb = np.floor((t[m] + np.pi) / (2 * np.pi) * NB).astype('int32') % NB
    count, mean, std = ring_stats(v, ids, nr); good = count > 0; nodes = np.arange(nr) + .5
    comp = count / (2 * np.pi * nodes); ref = np.median(comp[int(3 * RS):int(8 * RS)])
    cand_out = np.flatnonzero((nodes > 3 * RS) & (comp < 0.98 * ref)); r_edge = int(cand_out[0]) if cand_out.size else nr
    full_in = np.flatnonzero((comp >= 0.98 * ref) & (nodes > 0.9 * RS)); r_in = int(full_in[0])
    inner = []
    outer = list(range(r_edge, nr))
    mean_u, std_u, ok_o, P_o, varP_o = complete_from_partial(mean, std, ids, tb, v, outer, list(range(r_edge - 40, r_edge)))
    mean_u, std_u2, ok_i, P_i, varP_i = complete_from_partial(mean_u, std_u, ids, tb, v, inner, list(range(r_in, r_in + 40)))
    ok_ring = good & ok_o & ok_i
    mu = np.interp(r, nodes[ok_ring], mean_u[ok_ring]).astype('float32'); sd = np.interp(r, nodes[ok_ring], std_u2[ok_ring]).astype('float32')
    z = np.divide(a - mu, sd, out=np.zeros_like(a), where=sd > 0).astype('float32')
    kk = np.arange(r_in, r_in + 40); ok_k = ok_ring[kk] & (mean_u[kk] > 0) & (std_u2[kk] > 0)
    pm = np.polyfit(nodes[kk][ok_k], np.log(mean_u[kk][ok_k]), 1); ps = np.polyfit(nodes[kk][ok_k], np.log(std_u2[kk][ok_k]), 1)
    mean_x = mean_u.copy(); std_x = std_u2.copy(); ok_x = ok_ring.copy(); n_x = 0
    for i in range(r_in):
        if count[i] > 0: mean_x[i] = np.exp(np.polyval(pm, nodes[i])); std_x[i] = np.exp(np.polyval(ps, nodes[i])); ok_x[i] = True; n_x += 1
    mu2 = np.interp(r, nodes[ok_x], mean_x[ok_x]).astype('float32'); sd2 = np.interp(r, nodes[ok_x], std_x[ok_x]).astype('float32')
    z2 = np.divide(a - mu2, sd2, out=np.zeros_like(a), where=sd2 > 0).astype('float32'); del mu2, sd2
    extrap_info = {'anells_parcials_extrapolats': int(n_x), 'pendent_ln_mu_per_px': float(pm[0]), 'pendent_ln_sigma_per_px': float(ps[0]), 'anells_ajust': [int(r_in), int(r_in + 40)]}
    flat = np.flatnonzero(m); rflat = r.ravel()[flat]; order = np.argsort(ri.ravel()[flat], kind='stable'); flat_o = flat[order]
    counts = np.bincount(ri.ravel()[flat_o], minlength=nr); cuts = np.r_[0, np.cumsum(counts)]; af = a.ravel()
    sorted_rings = [np.sort(af[flat_o[cuts[i]:cuts[i + 1]]]) for i in range(nr)]
    def F(i, vals):
        s = sorted_rings[i]
        if len(s) == 0: return np.full(vals.shape, np.nan, 'float32')
        return (np.searchsorted(s, vals, side='left') + np.searchsorted(s, vals, side='right')).astype('float32') / (2.0 * len(s))
    rhef = np.zeros_like(a).ravel(); vals = af[flat]; i0 = np.clip(np.floor(rflat - 0.5).astype('int32'), 0, nr - 1); i1 = np.clip(i0 + 1, 0, nr - 1); al = np.clip(rflat - (i0 + 0.5), 0, 1).astype('float32')
    out = np.empty(len(flat), 'float32')
    for i in range(nr):
        k = np.flatnonzero(i0 == i)
        if not k.size: continue
        f0 = F(i, vals[k]); f1 = F(min(i + 1, nr - 1), vals[k]); f1 = np.where(np.isfinite(f1), f1, f0); f0 = np.where(np.isfinite(f0), f0, f1)
        out[k] = (1 - al[k]) * f0 + al[k] * f1
    rhef[flat] = out; rhef = rhef.reshape(a.shape)
    ksel = np.isin(ids, list(range(r_edge - 40, r_edge))); z_edge = (v[ksel] - mean[ids[ksel]]) / np.maximum(std[ids[ksel]], 1e-12); zs = np.sort(z_edge); Fedge = lambda q: np.searchsorted(zs, q, side='right') / len(zs)
    wgt = smoothstep(nodes, r_edge - BLEND - 32, r_edge - 32); wpix = np.interp(r, nodes, wgt).astype('float32'); outer_px = wpix > 0
    rhef[outer_px] = (1 - wpix[outer_px]) * rhef[outer_px] + wpix[outer_px] * Fedge(z[outer_px]).astype('float32')
    return z, rhef, z2, extrap_info, {'annulus_width_px': 1, 'r_edge_px': r_edge, 'r_in_px': r_in, 'r_in_R': r_in / RS, 'blend_px': BLEND, 'completeness_ref': float(ref), 'count_min': int(count[good].min()), 'count_max': int(count.max())}

def upsilon(x, ups=0.35):
    mid = float(np.nanmean(x)); y = np.full_like(x, np.nan); lo = x < mid; y[lo] = ((2 * x[lo]) ** ups) / 2; hi = (~lo) & np.isfinite(x); y[hi] = 1 - ((2 - 2 * x[hi]) ** ups) / 2; return y

# ---------------------------------------------------------------- E6 · RHEF local nadiu (V58, idèntic)
def rhef_native_cdf(a, m, r, t, S_deg, step_deg, dr=.5, nt=16384, cx=CX, cy=CY):
    idx = np.flatnonzero(m); rv = r.ravel()[idx]; ri = np.floor(rv).astype(int); lv = np.log(a.ravel()[idx]); n = np.bincount(ri); mu = np.bincount(ri, weights=lv) / np.maximum(n, 1); nodes = np.arange(len(n)); ok = n > 0; mu = np.interp(nodes, nodes[ok], mu[ok]); mu = gaussian_filter1d(mu, 16, mode='nearest')
    norm = np.zeros(a.shape, np.float32); norm.ravel()[idx] = lv - np.interp(rv, nodes + .5, mu); r0 = max(0, int(np.floor(rv.min())) - 1); nr = int(np.ceil((rv.max() - r0) / dr)) + 2
    b = np.floor((rv - r0) / dr).astype('int32'); fr = ((rv - r0) / dr - b).astype('float32'); ang = np.degrees(t.ravel()[idx]) % 360; K_ = int(round(360 / step_deg)); k0 = (ang / step_deg).astype('int32') % K_; wk = (ang / step_deg - k0).astype('float32')
    query = norm.ravel()[idx]; order = np.argsort(b, kind='stable'); cuts = np.searchsorted(b[order], np.arange(nr + 1)); theta = np.arange(nt, dtype='float32') * 2 * np.pi / nt; half = int(round(nt * S_deg / 720))
    centers = np.round(np.arange(K_) * step_deg * nt / 360).astype(int); sectors = [(np.arange(-half, half + 1) + c) % nt for c in centers]; out = np.zeros(len(idx), np.float32); denout = np.zeros(len(idx), np.float32); mf = m.astype('float32'); cache = {}; t0 = time.time()
    def cells(i):
        rad = np.float32(r0 + i * dr); mx = (cx + rad * np.cos(theta))[None, :].astype('float32'); my = (cy + rad * np.sin(theta))[None, :].astype('float32')
        wm = cv2.remap(mf, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[0]; p = cv2.remap(norm, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)[0] / np.maximum(wm, 1e-8); good = wm > .999
        return [np.sort(p[ix][good[ix]]) for ix in sectors]
    for i in range(nr):
        ii = order[cuts[i]:cuts[i + 1]]
        if not len(ii): continue
        for j in [i, i + 1]:
            if j not in cache: cache[j] = cells(j)
        for j, wr in [(i, 1 - fr[ii]), (i + 1, fr[ii])]:
            for kk, ww in [(k0[ii], 1 - wk[ii]), ((k0[ii] + 1) % K_, wk[ii])]:
                for k in np.unique(kk):
                    vals = cache[j][k]
                    if len(vals) < 50: continue
                    use = kk == k; ix = ii[use]; weight = wr[use] * ww[use]; rank = (np.searchsorted(vals, query[ix], side='left') + np.searchsorted(vals, query[ix], side='right')) / (2 * len(vals)); out[ix] += weight * rank; denout[ix] += weight
        for j in list(cache):
            if j < i: del cache[j]
        if i % 2000 == 0: log(f'  RHEF local {S_deg:.0f}° radi {i}/{nr} ({time.time() - t0:.0f}s)')
    result = np.full(a.shape, np.nan, np.float32); result.ravel()[idx] = np.where(denout > 0, out / np.maximum(denout, 1e-9), np.nan); return result

# ---------------------------------------------------------------- E2 · MGN (Morgan & Druckmüller 2014) i WOW (Auchère et al. 2023)
def mgn(a, m, sigmas=(1.25, 2.5, 5, 10, 20, 40), k=.7, h=.7, gamma=3.2, limits=None):
    lo, hi = limits or (float(np.min(a[m])), float(np.max(a[m])))
    detail = np.zeros_like(a, dtype='float32')
    for s in sigmas:
        mu = ng(a, m, s); d = a - mu
        d[np.abs(d) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(a), np.abs(mu))] = 0
        den = np.sqrt(ng(d * d, m, s)); z = np.divide(d, den, out=np.zeros_like(d), where=den > 0)
        detail += np.arctan(k * z) / len(sigmas); log('  MGN sigma ' + str(s))
    global_term = np.clip((a - lo) / (hi - lo), 0, 1) ** (1 / gamma)
    return h * global_term + (1 - h) * detail

def _refl(n, idx):
    idx = np.mod(idx, 2 * n); return np.where(idx < n, idx, 2 * n - 1 - idx)
def b3conv(a, s):
    """Convolució B3 dilatada (à trous, pas 2^s) separable, amb reflexió simètrica a les vores del llenç."""
    d = 2 ** s; a = np.ascontiguousarray(a, np.float32); h, w = a.shape
    tmp = np.zeros_like(a)
    for kk, kv in zip(range(-2, 3), K): tmp += kv * a[_refl(h, np.arange(h) + kk * d)]
    out = np.zeros_like(a)
    for kk, kv in zip(range(-2, 3), K): out += kv * tmp[:, _refl(w, np.arange(w) + kk * d)]
    return out
def nconv(a, m, s):
    den = b3conv(m.astype('float32'), s)
    return b3conv(np.where(m, a, 0), s) / np.maximum(den, 1e-20)
def bilateral_conv(a, m, s):
    h, w = a.shape; d = 2 ** s; out = np.zeros_like(a)
    for y0 in range(0, h, 192):
        y1 = min(h, y0 + 192); center = a[y0:y1]; moment = np.zeros_like(center); moment2 = np.zeros_like(center); mass = np.zeros_like(center)
        for dy, ky in zip(range(-2, 3), K):
            iy = _refl(h, np.arange(y0, y1) + dy * d)
            for dx, kx in zip(range(-2, 3), K):
                ix = _refl(w, np.arange(w) + dx * d); valid = m[iy[:, None], ix]; delta = np.where(valid, a[iy[:, None], ix] - center, 0); k = float(ky * kx)
                moment += k * delta; moment2 += k * delta * delta; mass += k * valid
        mean = moment / np.maximum(mass, 1e-20); vv = np.maximum(moment2 / np.maximum(mass, 1e-20) - mean * mean, 1e-20)
        num = np.zeros_like(center); norm = np.zeros_like(center)
        for dy, ky in zip(range(-2, 3), K):
            iy = _refl(h, np.arange(y0, y1) + dy * d)
            for dx, kx in zip(range(-2, 3), K):
                ix = _refl(w, np.arange(w) + dx * d); valid = m[iy[:, None], ix]; v = np.where(valid, a[iy[:, None], ix], 0); k = float(ky * kx)
                weight = ne.evaluate('k*exp(-0.5*(center-v)**2/vv)') * valid; num += (v - center) * weight; norm += weight
        out[y0:y1] = center + num / np.maximum(norm, 1e-20)
    return out
def wow(a, m, n_scales=11, bilateral=False):
    c = np.where(m, a, 0).astype('float32'); out = np.zeros_like(c)
    for s in range(n_scales):
        nxt = bilateral_conv(c, m, s) if bilateral else nconv(c, m, s)
        wave = c - nxt; wave[np.abs(wave) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(c), np.abs(nxt))] = 0
        power = nconv(wave * wave, m, s); amp = np.sqrt(np.maximum(power, 1e-20))
        out += wave / amp; c = np.where(m, nxt, 0)
        log(('  WOW bilateral' if bilateral else '  WOW') + ' escala ' + str(s)); del wave, power, amp; gc.collect()
    sd = float(np.std(c[m], dtype='float64'))
    if sd > 16 * np.finfo('float32').eps * float(np.max(np.abs(c[m]))): out += c / sd
    return out

# ---------------------------------------------------------------- E4 · ACHF angular (al llarg de l'arc, V42 idèntic)
def angular_polar(x, m, r, t):
    x = np.where(m, x, 0).astype(np.float32); mf = m.astype(np.float32)
    r0 = 400; nr = int(np.ceil(r.max())) - r0 + 2; nt = 16384; theta = np.arange(nt, dtype=np.float32) * 2 * np.pi / nt
    freq = np.fft.rfftfreq(nt)[None, :]; p = np.empty((nr, nt), np.float32); valid = np.empty_like(p)
    for start in range(0, nr, 64):
        rr = (r0 + np.arange(start, min(start + 64, nr), dtype=np.float32))[:, None]
        mx = (CX + rr * np.cos(theta)[None, :]).astype(np.float32); my = (CY + rr * np.sin(theta)[None, :]).astype(np.float32)
        wm = cv2.remap(mf, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT); xp = cv2.remap(x, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        fx = np.fft.rfft(xp, axis=1); fw = np.fft.rfft(wm, axis=1); bands = []
        for sigma in (8, 32, 64, 128):
            sp = sigma * nt / (2 * np.pi * rr); g = np.exp(-2 * np.pi ** 2 * sp ** 2 * freq ** 2)
            den = np.fft.irfft(fw * g, n=nt, axis=1); num = np.fft.irfft(fx * g, n=nt, axis=1)
            bands.append(np.where(den > 1e-5, num / np.maximum(den, 1e-5), 0).astype(np.float32))
        p[start:start + len(rr)] = bands[0] - (bands[1] + bands[2] + bands[3]) / 3; valid[start:start + len(rr)] = wm
    return p, valid, r0, nt
def back(p, m, r, t, r0, nt):
    ext = np.concatenate([p[:, -1:], p, p[:, :1]], axis=1)
    mx = (np.mod(t, 2 * np.pi) * nt / (2 * np.pi) + 1).astype(np.float32); my = (r - r0).astype(np.float32)
    return np.where(m, cv2.remap(ext, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT), 0)
