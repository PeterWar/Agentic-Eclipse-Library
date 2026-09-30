"""WOW sobre el domini de dada, sense farcit (V94, 24-09-2026). Norma canònica de Pere: res inventat ni reflectit.
Diferències amb v86_operadors.wow (el de la V86–V93):
  (1) NO s'omple res fora del domini: el de la V86–V93 calculava la WOW sobre una entrada continuada (continua_ln: perfil radial extrapolat
      + residu pull-push + Laplace a dins de la Lluna i fora del suport), dada inventada que la WOW veia fins a ~150 px del limbe.
      Aquí totes les convolucions i la potència es fan NOMÉS amb píxels del domini (convolució normalitzada).
  (2) Prop de la vora del domini, la mitjana local d'un sol costat té biaix quan la corona té pendent (el limbe hauria sortit clar o fosc);
      aquí s'hi ajusta un PLA local (mínims quadrats ponderats d'ordre 1 sobre els mateixos 5×5 tocs à trous, amb els mateixos pesos B3 i,
      a la bilateral, el mateix pes de rang). Allà on el suport és complet (lluny de les vores) el resultat és el d'ordre 0, com abans.
  (3) Només les escales 0..N_ESC−1 (per defecte 8: fins a ~128 px) i SENSE el terme residual gruixut (c/sd): la capa és detall pur, de
      mitjana local nul·la; en Superposició no enfosqueix ni aclareix a gran escala (l'«ombra quadrada»: la WOW bilateral de la V93 tenia
      mitjana 0,39–0,47 i, amb la màscara de Pere en quadrat arrodonit, enfosquia just a dins de la màscara).
Retorna la suma blanquejada (NaN fora del domini)."""
import numpy as np, numexpr as ne, time
K = np.array([1, 4, 6, 4, 1], np.float32) / 16
def _refl(n, idx):
    idx = np.mod(idx, 2 * n); return np.where(idx < n, idx, 2 * n - 1 - idx)
def b3conv(a, s):
    d = 2 ** s; a = np.ascontiguousarray(a, np.float32); h, w = a.shape; tmp = np.zeros_like(a)
    for kk, kv in zip(range(-2, 3), K): tmp += kv * a[_refl(h, np.arange(h) + kk * d)]
    out = np.zeros_like(a)
    for kk, kv in zip(range(-2, 3), K): out += kv * tmp[:, _refl(w, np.arange(w) + kk * d)]
    return out
def nconv(a, m, s):
    return b3conv(np.where(m, a, 0), s) / np.maximum(b3conv(m.astype(np.float32), s), 1e-20)
def smoothstep(x, lo, hi):
    q = np.clip((x - lo) / (hi - lo), 0, 1); return q * q * (3 - 2 * q)
def conv_pla(a, m, s, bilateral):
    """Suavitzat à trous d'escala s sobre el domini m: ordre 0 on el suport és complet, pla local (ordre 1) on és incomplet (vores).
    Retorna (valor, completesa)."""
    h, w = a.shape; d = 2 ** s; out = np.zeros_like(a); compl = np.zeros_like(a)
    for y0 in range(0, h, 192):
        y1 = min(h, y0 + 192); ctr = a[y0:y1]; nb = y1 - y0
        if bilateral:   # variància local per al pes de rang (com v86_operadors.bilateral_conv)
            mo = np.zeros_like(ctr); mo2 = np.zeros_like(ctr); ma = np.zeros_like(ctr)
            for dy, ky in zip(range(-2, 3), K):
                iy = _refl(h, np.arange(y0, y1) + dy * d)
                for dx, kx in zip(range(-2, 3), K):
                    ix = _refl(w, np.arange(w) + dx * d); val = m[iy[:, None], ix]; dl = np.where(val, a[iy[:, None], ix] - ctr, 0); k = float(ky * kx)
                    mo += k * dl; mo2 += k * dl * dl; ma += k * val
            mean = mo / np.maximum(ma, 1e-20); vv = np.maximum(mo2 / np.maximum(ma, 1e-20) - mean * mean, 1e-20)
        S = {n: np.zeros((nb, w), np.float64) for n in ('w', 'wx', 'wy', 'wxx', 'wxy', 'wyy', 'wv', 'wvx', 'wvy')}; ksum = np.zeros((nb, w), np.float32)
        for dy, ky in zip(range(-2, 3), K):
            iy = _refl(h, np.arange(y0, y1) + dy * d)
            for dx, kx in zip(range(-2, 3), K):
                ix = _refl(w, np.arange(w) + dx * d); val = m[iy[:, None], ix]; v = np.where(val, a[iy[:, None], ix], 0).astype(np.float32); k = float(ky * kx)
                wt = (ne.evaluate('k*exp(-0.5*(ctr-v)**2/vv)') * val) if bilateral else (k * val).astype(np.float32)
                ksum += k * val; wt64 = wt.astype(np.float64); vd = (v - ctr).astype(np.float64)
                S['w'] += wt64; S['wx'] += wt64 * dx; S['wy'] += wt64 * dy; S['wxx'] += wt64 * dx * dx; S['wxy'] += wt64 * dx * dy; S['wyy'] += wt64 * dy * dy
                S['wv'] += wt64 * vd; S['wvx'] += wt64 * vd * dx; S['wvy'] += wt64 * vd * dy
        W0 = np.maximum(S['w'], 1e-30); ord0 = S['wv'] / W0
        # sistema 3×3: [w wx wy; wx wxx wxy; wy wxy wyy] [a gx gy] = [wv wvx wvy]  (Cramer)
        a11, a12, a13, a22, a23, a33 = S['w'], S['wx'], S['wy'], S['wxx'], S['wxy'], S['wyy']; b1, b2, b3 = S['wv'], S['wvx'], S['wvy']
        det = a11 * (a22 * a33 - a23 * a23) - a12 * (a12 * a33 - a23 * a13) + a13 * (a12 * a23 - a22 * a13)
        num = b1 * (a22 * a33 - a23 * a23) - a12 * (b2 * a33 - a23 * b3) + a13 * (b2 * a23 - a22 * b3)
        ok = np.abs(det) > 1e-6 * np.maximum(a11, 1e-30) ** 3; ord1 = np.where(ok, num / np.where(ok, det, 1), ord0)
        cp = ksum.astype(np.float64); wpla = 1 - smoothstep(cp, 0.90, 0.999)          # pla només on el suport és incomplet
        out[y0:y1] = (ctr + (wpla * ord1 + (1 - wpla) * ord0)).astype(np.float32); compl[y0:y1] = cp.astype(np.float32)
    return out, compl
def wow_domini(a, m, n_esc=8, bilateral=False, log=print):
    c = np.where(m, a, 0).astype(np.float32); out = np.zeros_like(c)
    for s in range(n_esc):
        t0 = time.time(); nxt, _ = conv_pla(c, m, s, bilateral); nxt = np.where(m, nxt, 0).astype(np.float32)
        wave = np.where(m, c - nxt, 0).astype(np.float32); wave[np.abs(wave) <= 8 * np.finfo('float32').eps * np.maximum(np.abs(c), np.abs(nxt))] = 0
        amp = np.sqrt(np.maximum(nconv(wave * wave, m, s), 1e-20)); out += np.where(m, wave / amp, 0); c = nxt
        log(f"  WOW{' bilateral' if bilateral else ''} (domini, pla a les vores) escala {s} · {time.time() - t0:.0f} s")
    return np.where(m, out, np.nan).astype(np.float32)

# ---- post-procés de la capa: nivell neutre (0,5) i sense biaix coherent arran del limbe (tot calculat de la mateixa sortida, dins del domini)
def ng(a, m, s):
    import cv2
    num = cv2.GaussianBlur(np.where(m, a, 0).astype(np.float32), (0, 0), s); den = cv2.GaussianBlur(m.astype(np.float32), (0, 0), s)
    return num / np.maximum(den, 1e-6)
def neutralitza(q, m, cx, cy, R, sig_gran=150.0, sig_arc_graus=5.0, d_ple=60.0, d_zero=120.0, box=None):
    """q (NaN fora del domini) → q − mitjana local gran (σ 150 px, només domini) − perfil radial coherent al llarg de l'arc (σ 5°) a d ≤ 120 px.
    box = (x0, y0) de l'origen de q al llenç. Retorna q corregit (NaN fora del domini)."""
    import cv2
    from scipy.ndimage import gaussian_filter1d
    x0, y0 = box if box is not None else (0, 0); qq = np.where(m, q, 0).astype(np.float32)
    q1 = np.where(m, qq - ng(qq, m, sig_gran), 0).astype(np.float32)
    DT, DR = 0.05, 0.25; NT = int(360 / DT); DS = np.arange(-5.0, d_zero + 10 + 1e-6, DR); TS = np.radians((np.arange(NT) + 0.5) * DT)
    TT, DD = np.meshgrid(TS, DS); MX = (cx + (R + DD) * np.cos(TT) - x0).astype(np.float32); MY = (cy - (R + DD) * np.sin(TT) - y0).astype(np.float32)
    P = cv2.remap(q1, MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0); V = cv2.remap(m.astype(np.float32), MX, MY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    sg = sig_arc_graus / DT; num = gaussian_filter1d(P * V, sg, axis=1, mode='wrap'); den = gaussian_filter1d(V, sg, axis=1, mode='wrap')
    bias = np.where(den > 0.05, num / np.maximum(den, 1e-6), 0) * (1 - smoothstep(DS, d_ple, d_zero))[:, None]
    h, w = q.shape; yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w]; d = np.hypot(xx - cx, yy - cy) - R; t = (np.arctan2(-(yy - cy), xx - cx) + 2 * np.pi) % (2 * np.pi)
    IX = (t / (2 * np.pi) * NT - 0.5).astype(np.float32); IY = ((d - DS[0]) / DR).astype(np.float32); dins = (d > DS[0]) & (d < DS[-1])
    bk = cv2.remap(bias.astype(np.float32), np.mod(IX, NT), IY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return np.where(m, q1 - np.where(dins, bk, 0), np.nan).astype(np.float32)
