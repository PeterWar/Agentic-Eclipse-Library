"""WOW amb PARELLS SIMÈTRICS de dada (V95, 24-09-2026). Norma canònica: res inventat ni reflectit.
A cada escala à trous, un toc (dy, dx) del nucli B3 5×5 només compta si el seu simètric (−dy, −dx) també té dada. El pes de cada parell és igual
per als dos tocs (a la bilateral, la mitjana dels dos pesos de rang). Així la mitjana local no té biaix d'ordre 1 ni 2 perpendicular a la vora de la
dada: les tendències lineals i la curvatura del perfil es cancel·len dins de cada parell. Arran del limbe només queden els tocs al llarg del limbe.
No es copia ni es reflecteix cap valor: només es descarten tocs. La potència local, amb els mateixos pesos. Pes de completesa per escala
(fracció del pes B3 en parells vàlids), estricte a les escales gruixudes, on fins i tot els tocs al llarg del limbe cauen lluny de la corba.
Cada escala blanquejada es fa de mitjana local nul·la (σ = 4·2^s) abans de sumar-la: detall de nivell neutre."""
import numpy as np, numexpr as ne, time, cv2
K = np.array([1, 4, 6, 4, 1], np.float32) / 16
def _refl(n, idx):
    idx = np.mod(idx, 2 * n); return np.where(idx < n, idx, 2 * n - 1 - idx)
def smoothstep(x, lo, hi):
    q = np.clip((x - lo) / (hi - lo), 0, 1); return q * q * (3 - 2 * q)
TAPS = [(dy, dx) for dy in range(-2, 3) for dx in range(-2, 3)]
def conv_parells(a, m, s, bilateral, x2=None):
    """Retorna (suavitzat, completesa, potència de x2 amb els mateixos pesos si x2 no és None)."""
    h, w = a.shape; d = 2 ** s; out = np.zeros_like(a); compl = np.zeros_like(a); pot = np.zeros_like(a) if x2 is not None else None
    for y0 in range(0, h, 192):
        y1 = min(h, y0 + 192); ctr = a[y0:y1]; mc = m[y0:y1]; nb = y1 - y0
        V = {}; VAL = {}
        for dy, dx in TAPS:
            iy = _refl(h, np.arange(y0, y1) + dy * d); ix = _refl(w, np.arange(w) + dx * d); VAL[(dy, dx)] = m[iy[:, None], ix]; V[(dy, dx)] = a[iy[:, None], ix]
        PV = {t: VAL[t] & VAL[(-t[0], -t[1])] & mc for t in TAPS}
        if bilateral:
            mo = np.zeros_like(ctr); mo2 = np.zeros_like(ctr); ma = np.zeros_like(ctr)
            for (dy, dx) in TAPS:
                k = float(K[dy + 2] * K[dx + 2]); dl = np.where(PV[(dy, dx)], V[(dy, dx)] - ctr, 0); mo += k * dl; mo2 += k * dl * dl; ma += k * PV[(dy, dx)]
            mean = mo / np.maximum(ma, 1e-20); vv = np.maximum(mo2 / np.maximum(ma, 1e-20) - mean * mean, 1e-20)
            RW = {t: ne.evaluate('exp(-0.5*(c-v)**2/vv)', local_dict=dict(c=ctr, v=V[t], vv=vv)) for t in TAPS}
        num = np.zeros_like(ctr); den = np.zeros_like(ctr); ks = np.zeros_like(ctr); pn = np.zeros_like(ctr) if x2 is not None else None
        for (dy, dx) in TAPS:
            k = float(K[dy + 2] * K[dx + 2]); pv = PV[(dy, dx)]
            wt = (k * pv * 0.5 * (RW[(dy, dx)] + RW[(-dy, -dx)])) if bilateral else (k * pv).astype(np.float32)
            num += wt * np.where(pv, V[(dy, dx)] - ctr, 0); den += wt; ks += k * pv
            if x2 is not None:
                iy = _refl(h, np.arange(y0, y1) + dy * d); ix = _refl(w, np.arange(w) + dx * d); pn += (k * pv) * x2[iy[:, None], ix]
        out[y0:y1] = ctr + num / np.maximum(den, 1e-20); compl[y0:y1] = ks
        if x2 is not None: pot[y0:y1] = pn / np.maximum(ks, 1e-20)
    return out, compl, pot
def ng_pes(x, w, s):
    num = cv2.GaussianBlur((x * w).astype(np.float32), (0, 0), s); den = cv2.GaussianBlur(w.astype(np.float32), (0, 0), s); return num / np.maximum(den, 1e-6)
def wow_parells(a, m, n_esc=8, bilateral=False, log=print, llindar=lambda s: (0.30 + 0.08 * s, 0.60 + 0.05 * s)):
    c = np.where(m, a, 0).astype(np.float32); out = np.zeros_like(c); pesos = []
    for s in range(n_esc):
        t0 = time.time(); nxt, compl, _ = conv_parells(c, m, s, bilateral); nxt = np.where(m, nxt, 0).astype(np.float32)
        wave = np.where(m, c - nxt, 0).astype(np.float32)
        _, _, pot = conv_parells(c, m, s, False, x2=(wave * wave).astype(np.float32))
        g = np.where(m & (compl > 0), wave / np.sqrt(np.maximum(pot, 1e-20)), 0).astype(np.float32)
        C0, C1 = llindar(min(s, 7)); w = (smoothstep(compl, C0, C1) * m).astype(np.float32)
        g = g - ng_pes(g, w, max(8.0, 4.0 * 2 ** s)); out += np.where(m, w * g, 0); c = nxt; pesos.append(w)
        log(f"  WOW{' bilateral' if bilateral else ''} (parells simètrics) escala {s} · {time.time() - t0:.0f} s")
    return np.where(m, out, np.nan).astype(np.float32), pesos

def treu_anell_coherent(X, dom, cx, cy, R, box=(0, 0), d_ple=10.0, d_zero=16.0, sig_arc=6.0):
    """Treu del ràster de visualització X (dom = on hi ha dada) NOMÉS la part del detall radial fi que és coherent al llarg del limbe
    (pas alt radial σ 4 px, mitjana al llarg de l'arc σ 6 px d'arc), a tot el voltant i a d ≤ 16 px (pes 1 fins a 10 px). És l'anell de la
    vora difuminada de la Lluna (la brillantor puja els primers ~5–7 px); la textura, que canvia al llarg de l'arc, es queda."""
    from scipy.ndimage import gaussian_filter1d
    x0, y0 = box; h, w = X.shape; DR, NT = 0.25, 7200; DS = np.arange(-4.0, 30.0 + 1e-6, DR); TS = np.radians((np.arange(NT) + 0.5) * 360 / NT)
    TT, DD = np.meshgrid(TS, DS); PX = (cx + (R + DD) * np.cos(TT) - x0).astype(np.float32); PY = (cy - (R + DD) * np.sin(TT) - y0).astype(np.float32)
    P = cv2.remap(X.astype(np.float32), PX, PY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE); V = cv2.remap(dom.astype(np.float32), PX, PY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    num = gaussian_filter1d(P * V, 4.0 / DR, axis=0, mode='nearest'); den = gaussian_filter1d(V, 4.0 / DR, axis=0, mode='nearest'); HP = np.where(V > 0.5, P - num / np.maximum(den, 1e-6), 0)
    sig_th = sig_arc / ((R + DS) * np.radians(360 / NT)); COH = np.empty_like(HP)
    for i in range(HP.shape[0]):
        a_ = gaussian_filter1d(HP[i] * V[i], sig_th[i], mode='wrap'); b_ = gaussian_filter1d(V[i], sig_th[i], mode='wrap'); COH[i] = np.where(b_ > 0.05, a_ / np.maximum(b_, 1e-6), 0)
    COH *= (1 - smoothstep(DS, d_ple, d_zero))[:, None]
    yy, xx = np.mgrid[y0:y0 + h, x0:x0 + w]; d = np.hypot(xx - cx, yy - cy) - R; t = (np.arctan2(-(yy - cy), xx - cx) + 2 * np.pi) % (2 * np.pi)
    IX = (t / (2 * np.pi) * NT - 0.5).astype(np.float32); IY = ((d - DS[0]) / DR).astype(np.float32); dins = (d > DS[0]) & (d < DS[-1]) & dom
    back = cv2.remap(COH.astype(np.float32), np.mod(IX, NT), IY, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return np.where(dins, X - back, X).astype(np.float32)
