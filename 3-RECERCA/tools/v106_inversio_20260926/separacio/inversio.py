"""inversio (V106 · Separació, Claude, 26-09-2026) · INVERSIÓ CONJUNTA del detall tangencial arran del limbe lunar.
Model:  δ_j(θ, d) = C(θ, d) + A_j · Λ(φ_j, D_j) + soroll,
  C fix al llenç (corona, fix al Sol) a la graella polar de la c1 (θ a 0,5 px d'arc, d a 0,25 px; estesa a d −32…40 px);
  Λ fix a la Lluna: φ_j = angle de posició respecte del centre lunar del fotograma j, D_j = distància a la seva silueta d'ordre 2;
  Λ viu a una graella lunar (φ a Δφ, D a 0,25 px) NOMÉS on la Lluna fa de vora (LO ≤ D < DMAX), amb Λ(DMAX) = 0; interpolació bilineal.
Mínims quadrats ponderats (pes 1/σ_j(d)², soroll empíric per fotograma): C s'elimina exactament (mitjana ponderada per píxel) i el
sistema reduït de Λ (complement de Schur) es resol amb gradient conjugat, amb una cresta mínima i suavitat en D (la PSF fa Λ suau en D).
Res fora d'on hi ha observació: C només on almenys un fotograma veu el píxel (pes > 0)."""
import numpy as np, time
import scipy.sparse as sp
from scipy.sparse.linalg import cg, LinearOperator
from nucli import Dades

class Inversio:
    def __init__(self, S=None, LO=0.6, DMAX=4.0, D0=0.5, dD=0.25, dphi=0.125, sigc=32.0, sig_tab=None, verbose=True):
        self.S = S or Dades(); self.LO, self.DMAX, self.D0, self.dD, self.dphi, self.sigc = LO, DMAX, D0, dD, dphi, sigc
        self.nphi = int(round(360 / dphi)); self.nD = int(round((DMAX - D0) / dD))            # nodes lliures k = 0..nD−1; el node nD (D = DMAX) val 0
        self.dxy = np.zeros((self.S.nF, 2)); self.A = np.ones(self.S.nF); self.sig_tab = sig_tab; self.v = verbose
        self.cache = {}
    # ---------- geometria i δ de cada fotograma (amb la correcció de centre vigent) ----------
    def prepara(self, frames, extra=None):
        S = self.S; self.cache = {}
        for j in frames:
            a, D, u, v, rho = S.geom(j, self.dxy[j])
            d, ok = S.delta(j, D, self.LO, self.sigc, None if extra is None else extra(j, a, D))
            self.cache[j] = dict(a=a.astype(np.float32), D=D.astype(np.float32), d=d, ok=ok)
            if getattr(self, 'desa_uv', False): self.cache[j].update(u=u.astype(np.float32), v=v.astype(np.float32), rho=rho.astype(np.float32))
    def pes(self, j):
        """Pes de cada observació del fotograma j: 1/σ² amb σ² = soroll empíric per fila (taula) o, després d'una passada, la variància
        del residu per franja de D (a la vora) i per franja de d (lluny), amb correcció de palanca (IRLS)."""
        c = self.cache[j]
        if getattr(self, 'var_tab', None) is not None and j in self.var_tab:
            vt = self.var_tab[j]; D = c['D']
            v = np.interp(D, vt['Dmid'], vt['vD'])                                     # franges de D (fins a 12 px)
            vfar = np.interp(self.S.dg, vt['dmid'], vt['vd'])[:, None] * np.ones((1, self.S.nth))
            v = np.where(D < vt['Dmid'][-1], v, vfar)
            return 1.0 / np.maximum(v, 1e-8)
        return (1.0 / self.sigma(j) ** 2)[:, None] * np.ones((1, self.S.nth))
    def reestima_soroll_y(self, ydelta, **kw):
        keep = {j: self.cache[j]['d'] for j in self.frames}
        for j in self.frames: self.cache[j]['d'] = ydelta(j)
        try: return self.reestima_soroll(**kw)
        finally:
            for j in self.frames: self.cache[j]['d'] = keep[j]
    def reestima_soroll(self, Dedges=(0.5, 0.8, 1.1, 1.4, 1.7, 2.0, 2.5, 3.0, 3.5, 4.0, 5.0, 6.0, 8.0, 10.0, 12.0), dedges=np.arange(-32, 41, 4.0), frames=None):
        """Variància empírica del residu de cada fotograma (δ_j − C − A_j Λ), corregida per la palanca (1 − w/Σw), per franges de D i de d."""
        S = self.S; Wt = self.Wt.reshape(len(S.dg), S.nth); self.var_tab = {}
        Dm = 0.5 * (np.array(Dedges[1:]) + np.array(Dedges[:-1])); dm = 0.5 * (dedges[1:] + dedges[:-1])
        for j in (frames or self.frames):
            c = self.cache[j]; ok = c['ok']; w = self.pes(j)
            r = np.where(ok, c['d'] - self.C - self.A[j] * self.avalua_lam(c['a'], c['D']), 0.0)
            h = np.clip(np.where(ok, w / np.maximum(Wt, 1e-300), 1.0), 0, 1)
            q = np.where(ok & (h < 0.9), r * r / np.maximum(1 - h, 0.1), np.nan)
            vD = np.array([np.nanmean(q[(c['D'] >= a) & (c['D'] < b)]) if np.isfinite(q[(c['D'] >= a) & (c['D'] < b)]).sum() > 300 else np.nan for a, b in zip(Dedges[:-1], Dedges[1:])])
            vd = np.array([np.nanmean(q[(S.dg >= a) & (S.dg < b)][(c['D'][(S.dg >= a) & (S.dg < b)] >= Dedges[-1])]) if np.isfinite(q[(S.dg >= a) & (S.dg < b)][(c['D'][(S.dg >= a) & (S.dg < b)] >= Dedges[-1])]).sum() > 300 else np.nan for a, b in zip(dedges[:-1], dedges[1:])])
            for arr, mid in ((vD, Dm), (vd, dm)):
                okk = np.isfinite(arr)
                if okk.any(): arr[:] = np.interp(mid, mid[okk], arr[okk])
                else: arr[:] = 1.0
            self.var_tab[j] = dict(Dmid=Dm, vD=vD, dmid=dm, vd=vd)
        return self.var_tab
    def sigma(self, j):
        """σ_j(d) per fila (taula empírica per franges de d; es completa amb la franja més propera)."""
        return np.interp(self.S.dg, self.sig_tab['dmid'], self.sig_tab['sig'][j])
    # ---------- matriu bilineal de Λ ----------
    def Bmat(self, a, D):
        fphi = a / self.dphi; i0 = np.floor(fphi).astype(np.int64); tp = fphi - i0; i0 %= self.nphi; i1 = (i0 + 1) % self.nphi
        fD = (np.maximum(D, self.D0) - self.D0) / self.dD; k0 = np.floor(fD).astype(np.int64); tD = fD - k0; k1 = k0 + 1
        n = a.size; rows = np.repeat(np.arange(n), 4)
        cols = np.stack([k0 * self.nphi + i0, k0 * self.nphi + i1, k1 * self.nphi + i0, k1 * self.nphi + i1], 1).ravel()
        vals = np.stack([(1 - tD) * (1 - tp), (1 - tD) * tp, tD * (1 - tp), tD * tp], 1).ravel()
        keep = np.repeat(np.ones(n, bool), 4) & (np.stack([k0, k0, k1, k1], 1).ravel() < self.nD)
        return sp.csr_matrix((vals[keep], (rows[keep], cols[keep])), shape=(n, self.nD * self.nphi))
    # ---------- construcció del sistema ----------
    def construeix(self, frames, ydelta=None, pesos=None):
        """ydelta(j) → δ_j alternatiu (simulacions/injeccions) a la mateixa geometria i validesa. pesos: {j: factor}."""
        S = self.S; npx = len(S.dg) * S.nth; W0 = np.zeros(npx); Y0 = np.zeros(npx); L = {k: [] for k in ('p', 'a', 'D', 'y', 'w', 'j')}
        for j in frames:
            c = self.cache[j]; y = c['d'] if ydelta is None else ydelta(j)
            w = self.pes(j) * (1.0 if pesos is None else pesos.get(j, 1.0))
            ok = c['ok']; lun = ok & (c['D'] < self.DMAX); net = ok & ~lun
            W0 += np.where(net, w, 0).ravel(); Y0 += np.where(net, w * y, 0).ravel()
            idx = np.flatnonzero(lun.ravel())
            L['p'].append(idx.astype(np.int64)); L['a'].append(c['a'].ravel()[idx]); L['D'].append(c['D'].ravel()[idx]); L['y'].append(np.asarray(y, np.float64).ravel()[idx])
            L['w'].append(w.ravel()[idx]); L['j'].append(np.full(idx.size, j, np.int16))
        self.L = {k: np.concatenate(v) for k, v in L.items()}; self.W0, self.Y0 = W0, Y0; self.frames = list(frames)
        Aj = self.A[self.L['j']]
        self.B = self.Bmat(self.L['a'].astype(np.float64), self.L['D'].astype(np.float64)).multiply(Aj[:, None]).tocsr()
        self.Wt = W0 + np.bincount(self.L['p'], self.L['w'], minlength=npx)
        if self.v: print(f'  sistema: {len(frames)} fotogrames, {self.L["p"].size} observacions a la vora, {self.B.shape[1]} incògnites de Λ', flush=True)
    # ---------- resolució ----------
    def resol(self, ridge=1e-4, regD=0.05, tol=1e-7, maxiter=3000):
        B, L = self.B, self.L; p, w, y = L['p'], L['w'], L['y']; npx = self.Wt.size; Wt = np.maximum(self.Wt, 1e-300)
        BtWB_diag = np.asarray(B.multiply(B).T @ w).ravel(); obs = BtWB_diag > 0; sc = np.median(BtWB_diag[obs]) if obs.any() else 1.0
        n = B.shape[1]; nphi = self.nphi
        # suavitat en D: segona diferència per cada φ (node nD = 0 fix)
        rows = []; cols = []; vals = []; r = 0
        for k in range(1, self.nD):
            for (kk, c) in ((k - 1, 1.0), (k, -2.0), (k + 1, 1.0)):
                if kk < self.nD: rows.append(np.arange(nphi) + r * nphi); cols.append(kk * nphi + np.arange(nphi)); vals.append(np.full(nphi, c))
            r += 1
        D2 = sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(r * nphi, n))
        Rm = (regD * sc) * (D2.T @ D2) + (ridge * sc) * sp.identity(n)
        def mv(x):
            u = B @ x; m = np.bincount(p, w * u, minlength=npx) / Wt
            return B.T @ (w * (u - m[p])) + Rm @ x
        mt = (self.Y0 + np.bincount(p, w * y, minlength=npx)) / Wt
        b = B.T @ (w * (y - mt[p]))
        Mpre = LinearOperator((n, n), matvec=lambda x: x / (BtWB_diag + ridge * sc + 2 * regD * sc))
        t0 = time.time(); it = [0]
        def cb(xk): it[0] += 1
        lam, info = cg(LinearOperator((n, n), matvec=mv), b, rtol=tol, maxiter=maxiter, M=Mpre, callback=cb)
        self.lam = lam; self.lam_obs = obs.reshape(self.nD, nphi)
        u = B @ lam; self.C = (mt - np.bincount(p, w * u, minlength=npx) / Wt).reshape(len(self.S.dg), self.S.nth)
        self.C[self.Wt.reshape(self.C.shape) <= 0] = 0.0
        self.pred_lun = u
        if self.v: print(f'  CG: {it[0]} iteracions, info {info}, {time.time() - t0:.1f} s', flush=True)
        return self.C
    def Lam(self):
        return self.lam.reshape(self.nD, self.nphi)
    def avalua_lam(self, a, D, lam=None):
        lam = self.lam if lam is None else lam
        B = self.Bmat(np.asarray(a, np.float64).ravel(), np.asarray(D, np.float64).ravel())
        out = (B @ lam).reshape(np.shape(a)); return np.where(np.asarray(D) < self.DMAX, out, 0.0)
    # ---------- netejat per fotograma i per grups ----------
    def net_frame(self, j, ydelta=None):
        """δ_j − A_j Λ(φ_j, D_j) a la graella (només on el fotograma veu el píxel)."""
        c = self.cache[j]; y = c['d'] if ydelta is None else ydelta(j)
        lamv = self.A[j] * self.avalua_lam(c['a'], c['D'])
        return np.where(c['ok'], y - lamv, 0.0), c['ok']
    def grup(self, frames, ydelta=None):
        S = self.S; sw = np.zeros((len(S.dg), S.nth)); sy = np.zeros_like(sw)
        for j in frames:
            if j not in self.cache: continue
            yn, ok = self.net_frame(j, ydelta); w = self.pes(j) * ok
            sw += w; sy += w * yn
        return np.where(sw > 0, sy / np.maximum(sw, 1e-300), 0.0), sw
    def amplitud_frames(self, lim=(0.5, 2.0), dany=1.0):
        """Amplitud A_j del terme lunar de cada fotograma (la PSF/halo de cada fotograma no és igual): A_j = Σ w f (y − C) / Σ w f², f = Λ(φ_j, D_j)."""
        L = self.L; p, w, y = L['p'], L['w'], L['y']; f0 = self.Bmat(L['a'].astype(np.float64), L['D'].astype(np.float64)) @ self.lam; r = y - self.C.ravel()[p]
        out = {}
        for j in self.frames:
            m = L['j'] == j
            if m.sum() < 2000: continue
            a = float(np.sum(w[m] * f0[m] * r[m]) / max(np.sum(w[m] * f0[m] ** 2), 1e-30)); out[j] = np.clip(self.A[j] * (1 + dany * (a - self.A[j]) / max(self.A[j], 1e-6)) if False else a, *lim)
        js = list(out); g = np.exp(np.mean(np.log([out[j] for j in js])))
        for j in js: self.A[j] = out[j] / g
        return {j: float(self.A[j]) for j in js}
    # ---------- autocalibratge: desplaçament del centre lunar (i amplitud) de cada fotograma ----------
    def autocalibra(self, amplitud=False, dany=0.7, hD=0.05, ha=0.02):
        L = self.L; p, w, y = L['p'], L['w'], L['y']; Cv = self.C.ravel()[p]; lam = self.lam
        a = L['a'].astype(np.float64); D = L['D'].astype(np.float64)
        f0 = self.Bmat(a, D) @ lam
        gD = (self.Bmat(a, D + hD) @ lam - self.Bmat(a, np.maximum(D - hD, self.D0)) @ lam) / (2 * hD)
        gA = (self.Bmat((a + ha) % 360, D) @ lam - self.Bmat((a - ha) % 360, D) @ lam) / (2 * ha)
        out = {}
        for j in self.frames:
            m = L['j'] == j
            if m.sum() < 2000: continue
            c = self.cache[j]; idx = p[m]
            u = c['u'].ravel()[idx].astype(np.float64); v = c['v'].ravel()[idx].astype(np.float64); rho = c['rho'].ravel()[idx].astype(np.float64)
            dDdx = -u / rho; dDdy = v / rho                                   # centre (cx, cy) al llenç (y avall): v = −(Y − cy)
            dadx = np.degrees(v / rho ** 2); dady = np.degrees(u / rho ** 2)
            Aj = self.A[j]
            J = [Aj * (gD[m] * dDdx + gA[m] * dadx), Aj * (gD[m] * dDdy + gA[m] * dady)]
            if amplitud: J.append(f0[m])
            J = np.stack(J, 1); r = y[m] - Cv[m] - Aj * f0[m]; ww = w[m]
            H = J.T @ (J * ww[:, None]); g = J.T @ (ww * r)
            try: sol = np.linalg.solve(H + 1e-9 * np.trace(H) * np.eye(len(g)), g)
            except np.linalg.LinAlgError: continue
            out[j] = sol
        # mitjana ponderada del desplaçament = 0 (el zero de Λ és convencional)
        js = list(out); M = np.array([out[j][:2] for j in js]); M -= M.mean(0)
        for jj, j in enumerate(js):
            self.dxy[j] += dany * M[jj]
            if amplitud: self.A[j] *= (1 + dany * out[j][2])
        if amplitud:
            fr = [j for j in js]; g = np.exp(np.mean(np.log(self.A[fr]))); self.A[fr] /= g
        return {j: (float(self.dxy[j, 0]), float(self.dxy[j, 1]), float(self.A[j])) for j in js}
