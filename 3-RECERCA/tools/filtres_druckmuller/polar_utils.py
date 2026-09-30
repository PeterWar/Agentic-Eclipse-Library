"""Utilitats log-polars compartides (les mateixes de filtre_corona_externa.py, factoritzades):
mapes imatge ↔ log-polar centrats al Sol, desenfocament anisòtrop periòdic en angle, ompliment
radial per dins del limbe, fons de Fourier per columna, residu polar."""
import math
import numpy as np
import cv2


class LogPolar:
    def __init__(self, H, W, cx, cy, NA=8192, NR=3072, r_min=400.0):
        self.H, self.W, self.cx, self.cy, self.NA, self.NR, self.r_min = H, W, cx, cy, NA, NR, r_min
        self.r_max = math.hypot(max(cx, W - cx), max(cy, H - cy)) + 4.0
        self.K = NR / math.log(self.r_max / r_min)
        thp = (2 * math.pi * np.arange(NA, dtype=np.float64) / NA)[:, None]
        self.r_of = r_min * np.exp(np.arange(NR, dtype=np.float64) / self.K)
        self.map_x = (cx + self.r_of[None, :] * np.cos(thp)).astype(np.float32)
        self.map_y = (cy + self.r_of[None, :] * np.sin(thp)).astype(np.float32)
        yy = (np.arange(H, dtype=np.float32) - cy)[:, None]
        xx = (np.arange(W, dtype=np.float32) - cx)[None, :]
        rr = np.hypot(xx, yy)
        tt = np.arctan2(yy, xx); tt = np.where(tt < 0, tt + 2 * math.pi, tt)
        self.imap_x = (self.K * np.log(np.maximum(rr, r_min) / r_min)).astype(np.float32)
        self.imap_y = (tt / (2 * math.pi) * NA).astype(np.float32)
        self.px_deg = NA / 360.0
        self.iso = 2 * math.pi * self.K / NA        # σ_ρ = σ_θ·iso → isòtrop en la imatge
        self.th = (2 * math.pi * np.arange(NA) / NA).astype(np.float32)

    def cap_a_polar(self, a):
        return cv2.remap(np.ascontiguousarray(a, np.float32), self.map_x, self.map_y, cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    def cap_a_imatge(self, Dp):
        Dp2 = np.concatenate([Dp[-2:], Dp, Dp[:2]], axis=0)
        return cv2.remap(np.ascontiguousarray(Dp2, np.float32), self.imap_x, self.imap_y + 2.0, cv2.INTER_LINEAR,
                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)

    @staticmethod
    def desenfoca_polar(x, s_rho, s_ang):
        a = np.ascontiguousarray(x, np.float32)
        pad = int(math.ceil(3 * s_ang)) + 1
        ap = np.concatenate([a[-pad:], a, a[:pad]], axis=0)
        s_min = min(s_rho, s_ang)

        def k(s):
            return int(2 * math.ceil(3 * max(s, 0.5)) + 1)
        if s_min <= 6.0:
            out = cv2.GaussianBlur(ap, (k(s_rho), k(s_ang)), sigmaX=s_rho, sigmaY=s_ang, borderType=cv2.BORDER_REPLICATE)
        else:
            f = max(1, int(s_min / 4.0))
            h, w = ap.shape
            pt = cv2.resize(ap, (max(8, w // f), max(8, h // f)), interpolation=cv2.INTER_AREA)
            sr, sa = s_rho / f, s_ang / f
            pt = cv2.GaussianBlur(pt, (k(sr), k(sa)), sigmaX=sr, sigmaY=sa, borderType=cv2.BORDER_REPLICATE)
            out = cv2.resize(pt, (w, h), interpolation=cv2.INTER_LINEAR)
        return out[pad:pad + a.shape[0]]

    def blur(self, a, s_ang):
        return self.desenfoca_polar(a, s_ang * self.iso, s_ang)

    def blur_n(self, a, ok, s_ang):
        return self.blur(a, s_ang) / np.maximum(self.blur(ok, s_ang), 1e-3)

    @staticmethod
    def inpaint_radial(xp, mp, n_pend=30):
        na, nr = xp.shape
        ok = mp > 0.5
        te = ok.any(axis=1)
        c0 = np.where(te, np.argmax(ok, axis=1), 0)
        c1 = np.where(te, nr - 1 - np.argmax(ok[:, ::-1], axis=1), nr - 1)
        fila = np.arange(na)
        col = np.arange(nr)[None, :]
        a = xp[fila, c0]
        b = xp[fila, np.minimum(c0 + n_pend, c1)]
        pend_in = np.where(c1 - c0 > n_pend, (b - a) / n_pend, 0.0)
        dins = col < c0[:, None]
        return np.where(dins, a[:, None] + pend_in[:, None] * (col - c0[:, None]), xp).astype(np.float32)

    @staticmethod
    def fons_fourier(xp, mp, m_max=4, ridge=5.0, frac_min_fit=0.999):
        from scipy.ndimage import gaussian_filter1d
        na, nr = xp.shape
        th = 2 * math.pi * np.arange(na) / na
        cols = [np.ones(na)]
        for k_ in range(1, m_max + 1):
            cols += [np.cos(k_ * th), np.sin(k_ * th)]
        A = np.stack(cols, axis=1).astype(np.float32)
        p_ = A.shape[1]
        M = mp.astype(np.float32)
        coef = None
        for passada in range(2):
            S = np.einsum('ia,ib,ic->cab', A, A, M, optimize=True).astype(np.float64)
            T = np.einsum('ia,ic->ca', A, (M * xp).astype(np.float32), optimize=True).astype(np.float64)
            S[:, np.arange(1, p_), np.arange(1, p_)] += ridge
            S[:, 0, 0] += 1e-6
            coef = np.linalg.solve(S, T[..., None])[..., 0]
            if passada == 0:
                F0 = (A @ coef.T.astype(np.float32))
                res = np.where(mp > 0.5, xp - F0, np.nan)
                med = np.nanmedian(res, axis=0)
                mad = 1.4826 * np.nanmedian(np.abs(res - med[None, :]), axis=0) + 1e-6
                M = M * (np.abs(np.nan_to_num(res)) < 4.0 * mad[None, :])
                del F0, res
        frac = mp.mean(axis=0)
        plenes = np.where(frac >= frac_min_fit)[0]      # v9: amb frac_min_fit < 1 s'usa l'ajust també amb anells parcials (cap extrapolació abans)
        c_ple = int(plenes.max()) if plenes.size else nr - 1
        coef = gaussian_filter1d(coef, 3.0, axis=0, mode='nearest')
        xt = np.arange(nr, dtype=np.float64)
        x_out = xt - c_ple
        ext = coef.copy()
        amb = np.where(frac > 0.05)[0]
        c_fi = int(amb.max()) if amb.size else nr - 1
        n_p = 20
        for j in range(p_):
            v0 = float(coef[c_ple, j])
            s0 = float(coef[c_ple, j] - coef[max(c_ple - n_p, 0), j]) / n_p
            if j <= 4 and c_fi > c_ple + 60:
                xo = np.arange(c_ple + 1, c_fi + 1, dtype=np.float64) - c_ple
                wo = np.sqrt(np.clip(frac[c_ple + 1:c_fi + 1], 0, 1))
                res = coef[c_ple + 1:c_fi + 1, j] - (v0 + s0 * xo)
                A2 = np.stack([xo ** 2, xo ** 3], axis=1) * wo[:, None]
                ab, *_ = np.linalg.lstsq(A2, res * wo, rcond=None)
                fora = v0 + s0 * x_out + ab[0] * x_out ** 2 + ab[1] * x_out ** 3
            else:
                fora = v0 + s0 * 150.0 * (1.0 - np.exp(-np.clip(x_out, 0, None) / 150.0))
            ext[:, j] = np.where(x_out > 0, fora, coef[:, j])
        coef = ext
        return (A @ coef.T.astype(np.float32)).astype(np.float32), c_ple

    def residu_polar(self, L, valid, frac_min_fit=0.999):
        """ln L en polars, omplert per dins, menys el fons de Fourier m ≤ 4. Retorna R, ok, mp0, c_ple."""
        mp0 = self.cap_a_polar(valid.astype(np.float32))
        xp = self.cap_a_polar(np.where(valid, np.log(np.maximum(L, 1.0)), 0.0)) / np.maximum(mp0, 1e-3)
        mp0 = (mp0 > 0.5).astype(np.float32)
        xp = self.inpaint_radial(xp, mp0)
        ok = mp0.copy()
        c0 = np.argmax(mp0 > 0.5, axis=1)
        ok[np.arange(self.NR)[None, :] < c0[:, None]] = 1.0
        F, c_ple = self.fons_fourier(xp, ok, frac_min_fit=frac_min_fit)
        R = ((xp - F) * ok).astype(np.float32)
        return R, ok, mp0, c_ple


def smooth01(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)
