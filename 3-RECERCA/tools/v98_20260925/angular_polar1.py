"""angular_polar d'ORDRE 1 (V98). És v86_operadors.angular_polar (pas alt al llarg de l'arc centrat al Sol: banda σ 8 − mitjana de σ 32/64/128,
amb convolució normalitzada per la dada) amb la mitjana de cada banda feta amb un PLA LOCAL al llarg de l'arc (convolució normalitzada
d'ordre 1, Knutsson i Westin 1993), calculada per FFT sobre el cercle:
  m_k = (u^k g) ⋆ w, b_k = (u^k g) ⋆ (w x); a0 = (m2 b0 − m1 b1)/(m0 m2 − m1²).
Per què: la Lluna està desplaçada 14 px del Sol; a un radi solar fix arran del limbe, l'arc amb dada s'acaba d'un costat, i la mitjana
d'ordre 0 d'un sol costat té el biaix del gradient azimutal (vorell fosc o clar d'1–4 px a la vora de la dada, capa 47 a dalt).
Amb el cercle sencer (sense cap forat) m1 = 0 i a0 = b0/m0: EXACTAMENT el valor d'ordre 0 (lluny de la Lluna i de les vores del camp, igual que la V97)."""
import numpy as np, cv2
def angular_polar1(x, m, r, t, CX, CY, qmin=0.02):
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
            s_ = sp                                     # coordenada u en unitats de σ (condicionament)
            g1 = (2j * np.pi * sp ** 2 * freq * g) / s_  # correlació amb u·g (conjugat del FT de u·g), u/σ
            g2 = (sp ** 2 - 4 * np.pi ** 2 * sp ** 4 * freq ** 2) * g / s_ ** 2
            m0 = np.fft.irfft(fw * g, n=nt, axis=1); m1 = np.fft.irfft(fw * g1, n=nt, axis=1); m2 = np.fft.irfft(fw * g2, n=nt, axis=1)
            b0 = np.fft.irfft(fx * g, n=nt, axis=1); b1 = np.fft.irfft(fx * g1, n=nt, axis=1)
            det = m0 * m2 - m1 * m1; q = det / np.maximum(m0 * m2, 1e-12)
            o1 = (m2 * b0 - m1 * b1) / np.where(np.abs(det) > 1e-12, det, 1e-12); o0 = np.where(m0 > 1e-5, b0 / np.maximum(m0, 1e-5), 0)
            bands.append(np.where(m0 > 1e-5, np.where(q > qmin, o1, o0), 0).astype(np.float32))
        p[start:start + len(rr)] = bands[0] - (bands[1] + bands[2] + bands[3]) / 3; valid[start:start + len(rr)] = wm
    return p, valid, r0, nt
if __name__ == '__main__':   # prova: cercle sencer → igual que l'ordre 0; arc tallat amb rampa lineal → sense biaix
    import sys; sys.path.insert(0, sys.argv[1]); from v86_operadors import angular_polar
    H, W = 1200, 1200; CX, CY = 600.0, 600.0; y, xg = np.ogrid[:H, :W]; r = np.hypot(y - CY, xg - CX).astype(np.float32); t = np.arctan2(y - CY, xg - CX).astype(np.float32)
    rng = np.random.default_rng(0); a = (rng.normal(size=(H, W)) * 0.1).astype(np.float32) + (t * 0.3).astype(np.float32)
    m = (r > 405) & (r < 560)
    import v86_operadors as V; V.CX, V.CY = CX, CY
    p0, v0, r0, nt = V.angular_polar(a, m, r, t); p1, v1, _, _ = angular_polar1(a, m, r, t, CX, CY)
    ok = (v0 > 0.999)[: , :]; print('complet: max |o1 − o0| =', float(np.abs(p1 - p0)[20:140].max()))
    lin = (t * 1.0).astype(np.float32); m2 = m & (t > 0.2)          # arc tallat a θ = 0,2 rad, rampa lineal en θ (el pas alt ideal és 0)
    q0, w0, _, _ = V.angular_polar(lin, m2, r, t); q1, w1, _, _ = angular_polar1(lin, m2, r, t, CX, CY)
    k = int(0.21 / (2 * np.pi) * 16384); print('vora de l\'arc (θ≈0,21): ordre 0', np.round(q0[60, k:k + 6], 4), '· ordre 1', np.round(q1[60, k:k + 6], 4))
