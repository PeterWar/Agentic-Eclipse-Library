#!/usr/bin/env python3
"""Deriva de la muntura, v2: correlacio de banderols amb mascara d'unio.

- Imatge de treball: verd ds x4, dividit per l'exposicio, MENYS el perfil
  radial (vel i corona llisa fora): hi queda l'estructura azimutal.
- Parelles: mateix temps d'exposicio i tambe exposicions adjacents (ratio 2).
- Mascara: unio dels dos discs lunars -> el forat es identic als dos costats.
- Posicions solars per minims quadrats sobre el graf de parelles.
- Escala fixada pel radi lunar; nomes s'ajusta rotacio+mirall+offset.
"""
import os, time
import numpy as np
import tifffile
from scipy.ndimage import gaussian_filter, binary_dilation
from skimage.registration import phase_cross_correlation

SCRATCH = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/bd892f38-1fd3-470f-9bc5-71eb7485933a/scratchpad"
CAL = "/Users/USUARI/Desktop/Eclipse 2026/Derivats/Vixen/Calibrated_Claude"
DS = 4

def log(m):
    print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)

frames = sorted(np.load(f"{SCRATCH}/deriva_frames.npy", allow_pickle=True),
                key=lambda f: f["t_start"])
N = len(frames)
imgs, masks = [], []
for i, f in enumerate(frames):
    g = tifffile.imread(f"{CAL}/{f['name']}_cal.tif")[:, :, 1].astype(np.float32)
    gd = g[::DS, ::DS] / f["exp"]
    H, W = gd.shape
    yy, xx = np.mgrid[0:H, 0:W]
    cx, cy, R = f["moon_x"]/DS, f["moon_y"]/DS, f["moon_R"]/DS
    rr = np.hypot(xx - cx, yy - cy)
    rq = np.clip(rr.astype(int), 0, 2400)
    prof = np.zeros(2401, np.float32)
    moon = rr < R + 8
    for rad in range(2401):
        m = (rq == rad) & ~moon
        prof[rad] = np.median(gd[m]) if m.sum() > 40 else (prof[rad-1] if rad else 0)
    az = gd - prof[rq]
    # passa-alts isotrop: mata el dipol de centre i qualsevol residu llis
    az = az - gaussian_filter(az, 12)
    s = np.std(az[~moon])
    az = np.clip(az, -6*s, 6*s)
    imgs.append(az)
    sats = binary_dilation(gd > (16000.0/f["exp"]), iterations=3)
    masks.append(moon | sats)
    f["_i"] = i
    if (i+1) % 10 == 0:
        log(f"preparats {i+1}/{N}")

PH = 110  # semiamplada del pegat (ds)
h2 = (np.hanning(2*PH)[:, None] * np.hanning(2*PH)[None, :]).astype(np.float64)

def t_mid(f):
    return f["t_start"] + f["exp"]/2

# parelles: mateix exp (consecutives) + exposicions adjacents en temps
pairs = []
by_exp = {}
for f in frames:
    by_exp.setdefault(f["exp"], []).append(f)
exps = sorted(by_exp)
for e in exps:
    fl = by_exp[e]
    for a, b in zip(fl, fl[1:]):
        pairs.append((a, b))
for e1, e2 in zip(exps, exps[1:]):
    if e2/e1 <= 2.6:
        for a in by_exp[e1]:
            b = min(by_exp[e2], key=lambda x: abs(t_mid(x) - t_mid(a)))
            if abs(t_mid(b) - t_mid(a)) < 45:
                pairs.append((a, b))
log(f"{len(pairs)} parelles")

meas = []
Hs, Ws = imgs[0].shape
for a, b in pairs:
    dt = t_mid(b) - t_mid(a)
    if dt <= 0.5:
        continue
    ia, ib = imgs[a["_i"]], imgs[b["_i"]]
    valid = ~(masks[a["_i"]] | masks[b["_i"]])
    cx0 = 0.5*(a["moon_x"] + b["moon_x"])/DS
    cy0 = 0.5*(a["moon_y"] + b["moon_y"])/DS
    shifts = []
    for r_p in (280, 335):
        for ang in range(0, 360, 30):
            px = int(cx0 + r_p*np.cos(np.radians(ang)))
            py = int(cy0 + r_p*np.sin(np.radians(ang)))
            y0, y1, x0, x1 = py-PH, py+PH, px-PH, px+PH
            if y0 < 0 or x0 < 0 or y1 > Hs or x1 > Ws:
                continue
            if valid[y0:y1, x0:x1].mean() < 0.97:
                continue
            wa = (ia[y0:y1, x0:x1]*h2).astype(np.float64)
            wb = (ib[y0:y1, x0:x1]*h2).astype(np.float64)
            wa /= (wa.std() + 1e-12); wb /= (wb.std() + 1e-12)
            sh, _, _ = phase_cross_correlation(wa, wb, upsample_factor=200)
            shifts.append(sh)
    if len(shifts) < 4:
        continue
    S = np.array(shifts)
    med = np.median(S, axis=0)
    mad = float(np.median(np.abs(S - med))) * 1.4826 * DS
    meas.append({"a": a["_i"], "b": b["_i"], "dt": dt, "err": mad,
                 "np": len(S), "dx": -med[1]*DS, "dy": -med[0]*DS})
errs = np.array([m["err"] for m in meas])
log(f"dispersio entre pegats (px): mediana {np.median(errs):.2f} · p10 {np.percentile(errs,10):.2f} · p90 {np.percentile(errs,90):.2f}")
good = [m for m in meas if m["err"] < 0.8 and m["np"] >= 5]
log(f"{len(good)}/{len(meas)} parelles amb dispersio<0.8 px i >=5 pegats")
if len(good) < 8:
    raise SystemExit("massa poques parelles bones; cal revisar el correlador")
for m in good[:6]:
    log(f"  mostra: {frames[m['a']]['name']}->{frames[m['b']]['name']} dt={m['dt']:.1f}s "
        f"v=({m['dx']/m['dt']:+.3f},{m['dy']/m['dt']:+.3f}) px/s err={m['err']:.3f}")

# resol posicions solars p_i per minims quadrats sobre el graf
rows, rhs = [], []
for m in good:
    w = 1.0/max(m["err"], 0.2)
    r = np.zeros(2*N); r[2*m["b"]] = w; r[2*m["a"]] = -w
    rows.append(r); rhs.append(w*m["dx"])
    r = np.zeros(2*N); r[2*m["b"]+1] = w; r[2*m["a"]+1] = -w
    rows.append(r); rhs.append(w*m["dy"])
# ancoratge: p_0 = 0
for k in (0, 1):
    r = np.zeros(2*N); r[k] = 10.0
    rows.append(r); rhs.append(0.0)
A = np.array(rows); bvec = np.array(rhs)
sol, *_ = np.linalg.lstsq(A, bvec, rcond=None)
P = sol.reshape(N, 2)      # posicio del CONTINGUT solar de cada fotograma (px)
tms = np.array([t_mid(f) for f in frames])
connected = sorted({m["a"] for m in good} | {m["b"] for m in good})
log(f"nodes connectats: {len(connected)}/{N}")

# ajust lineal de la deriva (nomes nodes connectats)
idx = np.array(connected)
vx = np.polyfit(tms[idx], P[idx, 0], 1)
vy = np.polyfit(tms[idx], P[idx, 1], 1)
drift_rate = np.array([vx[0], vy[0]])
res_track = np.c_[P[idx, 0] - np.polyval(vx, tms[idx]), P[idx, 1] - np.polyval(vy, tms[idx])]
log(f"deriva solar (px/s): ({drift_rate[0]:+.4f}, {drift_rate[1]:+.4f})")
log(f"no-linealitat de la traca (rms): {np.sqrt((res_track**2).sum(1)).std():.2f} px")

# tancament amb escala fixa pel radi lunar
from skyfield.api import Loader, wgs84
load = Loader(os.path.expanduser("~/.cache/skyfield"))
tsc = load.timescale(); eph = load("de440s.bsp")
sun, moon, earth = eph["sun"], eph["moon"], eph["earth"]
lloc = earth + wgs84.latlon(42.299407, -5.02503, elevation_m=798)

def eph_offset(t_c2):
    t = tsc.utc(2026, 8, 12, 18, 28, 46.0 + t_c2)
    obs = lloc.at(t)
    s = obs.observe(sun).apparent(); m = obs.observe(moon).apparent()
    ra_s, dec_s, _ = s.radec(epoch="date"); ra_m, dec_m, dm = m.radec(epoch="date")
    return np.array([(ra_m._degrees - ra_s._degrees)*3600*np.cos(dec_s.radians),
                     (dec_m.degrees - dec_s.degrees)*3600]), \
           np.degrees(np.arcsin(1737.4/dm.km))*3600

E = np.array([eph_offset(t)[0] for t in tms])
Rarc = eph_offset(tms[N//2])[1]
moonR = np.mean([f["moon_R"] for f in frames])
plate = Rarc/moonR
log(f"escala de placa (radi lunar): {plate:.4f} arcsec/px")

mx = np.array([f["moon_x"] for f in frames]); my = np.array([f["moon_y"] for f in frames])
rel = np.c_[mx, my] - P     # Lluna respecte del Sol, en px de sensor
best = None
for mir in (1, -1):
    Em = E.copy(); Em[:, 0] *= mir
    for k in range(720):
        th = k*np.pi/360
        G = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])/plate
        pred = (G @ Em.T).T
        off = (rel[idx] - pred[idx]).mean(0)
        rmse = np.sqrt(((rel[idx] - pred[idx] - off)**2).sum(1).mean())
        if best is None or rmse < best[0]:
            best = (rmse, mir, np.degrees(th), off)
rmse, mir, theta, off = best
log(f"tancament (escala fixa): rmse={rmse:.2f} px · mirall={mir} · rotacio={theta:.2f} graus")

G = np.array([[np.cos(np.radians(theta)), -np.sin(np.radians(theta))],
              [np.sin(np.radians(theta)),  np.cos(np.radians(theta))]])/plate
Ginv = np.linalg.inv(G)
dsky = Ginv @ drift_rate
dsky[0] *= mir
rate = float(np.hypot(*dsky))
pa = float((np.degrees(np.arctan2(dsky[0], dsky[1])) + 360) % 360)
log(f"DERIVA MESURADA v2: {rate:.4f} arcsec/s · PA {pa:.1f} · {rate*105:.1f} arcsec en 105 s "
    f"({rate*105/plate:.1f} px)")
log(f"error polar equivalent: {np.degrees(np.arcsin(min(rate/15.041, 1)))*60:.1f} arcmin")
relrate = np.polyfit(tms[idx], rel[idx, 0], 1)[0], np.polyfit(tms[idx], rel[idx, 1], 1)[0]
log(f"ritme relatiu mesurat: {np.hypot(*relrate)*plate:.4f} arcsec/s (efem. 0.5905)")

np.savez(f"{SCRATCH}/deriva_v2.npz", P=P, tms=tms, rel=rel, E=E, idx=idx,
         drift_rate=drift_rate, plate=plate, theta=theta, mir=mir)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axs = plt.subplots(1, 3, figsize=(19, 6))
ax = axs[0]
ax.plot(tms[idx], P[idx, 0]*plate, "o-", ms=4, label="x")
ax.plot(tms[idx], P[idx, 1]*plate, "o-", ms=4, label="y")
ax.plot(tms[idx], np.polyval(vx, tms[idx])*plate, "--", color="gray")
ax.plot(tms[idx], np.polyval(vy, tms[idx])*plate, "--", color="gray")
ax.set_title(f"Traça del Sol al sensor = deriva de la muntura\n{rate:.3f}\"/s · PA {pa:.0f}° · error polar eq. ~{np.degrees(np.arcsin(min(rate/15.041,1)))*60:.0f}'")
ax.set_xlabel("t des de C2 (s)"); ax.set_ylabel("arcsec"); ax.legend(); ax.grid(alpha=0.3)
ax = axs[1]
pred = (G @ (E*np.array([mir, 1])).T).T + off
ax.plot(pred[idx, 0], pred[idx, 1], "-", color="gray", label="efemèrides")
ax.plot(rel[idx, 0], rel[idx, 1], "o", ms=4, color="crimson", label="mesurat")
ax.set_title(f"Lluna−Sol al sensor · rmse {rmse:.2f} px · rot {theta:.1f}°")
ax.set_xlabel("px"); ax.set_ylabel("px"); ax.legend(); ax.grid(alpha=0.3); ax.axis("equal")
ax = axs[2]
rr = np.sqrt(((rel[idx] - pred[idx] - 0*off)**2).sum(1))
rr = rr - rr.min()
ax.plot(tms[idx], np.sqrt(((rel[idx]-pred[idx]-off)**2).sum(1)), "o", ms=4)
ax.set_title("Residu del tancament per fotograma")
ax.set_xlabel("t des de C2 (s)"); ax.set_ylabel("px"); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(f"{SCRATCH}/deriva_mesurada_v2.png", dpi=110)
log("fet")
