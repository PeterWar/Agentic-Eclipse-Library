#!/usr/bin/env python3
"""Del gradient de brillantor DINS del disc solar al vinyetatge del sistema.

Model per fotograma f i cel.la polar (rho, theta) de la fotosfera:

    log2 I = S(rho)  +  z_f  +  gx_f * ux  +  gy_f * uy

S(rho) es l'enfosquiment del limbe, comu a tots els fotogrames; z_f absorbeix
l'extincio i l'exposicio; (gx_f, gy_f) es el gradient lineal a traves del disc,
en EV per pixel raw. Aquest gradient te dues fonts:

  - ATMOSFERA: el gradient d'extincio, que apunta cap al zenit i canvia a poc a
    poc amb el temps;
  - VINYETATGE: si V(r) = -A*(r/rc)^2 EV, el gradient val -2A*p/rc^2, o sigui que
    depen de la POSICIO p del disc al sensor.

Els SALTS de muntura mouen p de cop sense que l'atmosfera canvii: son la
palanca que separa els dos termes.
"""
import numpy as np, sys, datetime as dt

Z = np.load(sys.argv[1], allow_pickle=True)
LABEL = sys.argv[2]
W_RAW, H_RAW = (int(sys.argv[3]), int(sys.argv[4]))   # mida del sensor en px raw
names = [str(x) for x in Z["names"]]
cx, cy = Z["cx"], Z["cy"]      # centre del disc, pla G1
maps, cnts = Z["maps"], Z["cnts"]
R = float(Z["R"])              # radi solar, pla G1
dts = [dt.datetime.strptime(str(s), "%Y:%m:%d %H:%M:%S") for s in Z["dts"]]
N, NRHO, NTH = maps.shape
RHO_MAX = 0.93

mean = maps / np.maximum(cnts, 1)
valid = cnts > 20
rho = (np.arange(NRHO) + 0.5) / NRHO * RHO_MAX
th = (np.arange(NTH) + 0.5) / NTH * 2 * np.pi - np.pi
ux = (rho[:, None] * np.cos(th)[None, :]) * R      # pla G1
uy = (rho[:, None] * np.sin(th)[None, :]) * R

# nomes fotosfera: descarta cel.les fosques (Lluna) i el limbe extrem
ref = np.array([np.percentile(mean[i][valid[i]], 97) if valid[i].any() else 0 for i in range(N)])
lit = valid & (mean > 0.45 * ref[:, None, None]) & (rho[None, :, None] < 0.88)
L = np.where(lit, np.log2(np.maximum(mean, 1e-3)), np.nan)

# --- S(rho) comu: mediana, per fotograma, del perfil normalitzat
S = np.zeros(NRHO)
for _ in range(4):
    resid = L - S[None, :, None]
    zf = np.nanmedian(resid.reshape(N, -1), axis=1)
    S = np.nanmedian((L - zf[:, None, None]).reshape(N, NRHO, NTH), axis=(0, 2))
    S = np.where(np.isfinite(S), S, 0.0)

print(f"=== {LABEL} ===")
print("enfosquiment del limbe mesurat (EV respecte del centre del disc):")
for i in range(0, NRHO, 5):
    print(f"   rho={rho[i]:.2f}  {S[i]-S[0]:+.3f} EV")

# --- gradient per fotograma
gx = np.full(N, np.nan); gy = np.full(N, np.nan); ncel = np.zeros(N, int)
rms = np.full(N, np.nan)
for i in range(N):
    m = lit[i] & np.isfinite(L[i])
    if m.sum() < 250:
        continue
    y = L[i][m] - S[None, :].repeat(NTH, 0).T[m] if False else L[i][m] - np.broadcast_to(S[:, None], (NRHO, NTH))[m]
    A = np.stack([np.ones(m.sum()), ux[m], uy[m]], 1)
    sol, *_ = np.linalg.lstsq(A, y, rcond=None)
    r = y - A @ sol
    gx[i], gy[i], ncel[i], rms[i] = sol[1], sol[2], m.sum(), np.std(r)

ok = np.isfinite(gx) & (ncel > 250)
# posicio del disc respecte del centre del sensor, en px RAW
px = (cx * 2 - W_RAW / 2)
py = (cy * 2 - H_RAW / 2)
rc = np.hypot(W_RAW, H_RAW) / 2      # radi de la cantonada, px raw

print(f"\n{ok.sum()} fotogrames amb gradient ajustat. "
      f"Gradient en mil.lielectronvolts... (EV per 1000 px raw)")
print(f"{'fitxer':<15}{'hora':<10}{'px':>7}{'py':>7}{'gx':>9}{'gy':>9}{'rms%':>7}")
for i in range(N):
    if not ok[i]:
        continue
    print(f"{names[i]:<15}{dts[i].strftime('%H:%M:%S'):<10}{px[i]:7.0f}{py[i]:7.0f}"
          f"{gx[i]*500:9.3f}{gy[i]*500:9.3f}{rms[i]*69.3:7.2f}")

# --- SALTS: parelles consecutives en el temps amb desplacament gran
print("\n--- salts de muntura: canvi de gradient contra canvi de posicio ---")
idx = np.argsort([d.timestamp() for d in dts])
rows = []
for a, b in zip(idx[:-1], idx[1:]):
    if not (ok[a] and ok[b]):
        continue
    dsec = (dts[b] - dts[a]).total_seconds()
    dpx, dpy = px[b] - px[a], py[b] - py[a]
    d = np.hypot(dpx, dpy)
    if d < 150 or dsec > 120:
        continue
    dgx, dgy = (gx[b] - gx[a]) / 2, (gy[b] - gy[a]) / 2   # EV per px RAW
    # projeccio del canvi de gradient sobre la direccio del salt
    proj = (dgx * dpx + dgy * dpy) / d
    # per V = -A (r/rc)^2 : dg = -2A d / rc^2  ->  A = -proj*rc^2/(2*d)
    Aest = -proj * rc ** 2 / (2 * d)
    rows.append((names[a], names[b], dsec, dpx, dpy, d, dgx * 500, dgy * 500, Aest))
    print(f"  {names[a]} -> {names[b]}  Dt={dsec:5.0f}s  "
          f"salt=({dpx:+6.0f},{dpy:+6.0f}) |d|={d:5.0f}px")
    print(f"      canvi de gradient = ({dgx*500:+.3f}, {dgy*500:+.3f}) EV/1000px raw"
          f"   ->  A(cantonada) = {Aest:+.2f} EV")

if rows:
    As = np.array([r[-1] for r in rows])
    print(f"\n  A(cantonada) de {len(As)} salts: mediana {np.median(As):+.2f} EV, "
          f"mitjana {As.mean():+.2f} +/- {As.std(ddof=1)/np.sqrt(len(As)):.2f} EV (e.e.)")

# --- regressio global g vs p amb l'atmosfera com a polinomi suau en el temps
t0 = min(d.timestamp() for d in dts)
tt = np.array([(d.timestamp() - t0) / 3600.0 for d in dts])
sel = ok
n = sel.sum()
deg = 2
Acols = []
for k in range(deg + 1):
    Acols.append(np.concatenate([tt[sel] ** k, np.zeros(n)]))   # atm x
for k in range(deg + 1):
    Acols.append(np.concatenate([np.zeros(n), tt[sel] ** k]))   # atm y
Acols.append(np.concatenate([-2 * px[sel] / rc ** 2, -2 * py[sel] / rc ** 2]))  # vinyetatge
M = np.stack(Acols, 1)
yv = np.concatenate([gx[sel] / 2, gy[sel] / 2])                  # EV per px raw
sol, res, *_ = np.linalg.lstsq(M, yv, rcond=None)
resid = yv - M @ sol
cov = np.linalg.pinv(M.T @ M) * (resid @ resid) / (len(yv) - M.shape[1])
print(f"\n--- regressio global (atmosfera = polinomi de grau {deg} en el temps) ---")
print(f"  A(cantonada) = {sol[-1]:+.3f} +/- {np.sqrt(cov[-1,-1]):.3f} EV")
print(f"  rms residual del gradient: {np.std(resid)*500:.3f} EV/1000px raw")
print(f"  gradient atmosferic tipic: {np.hypot(sol[0],sol[3])*500:.3f} EV/1000px raw")
np.save("vig_S.npy", S)
