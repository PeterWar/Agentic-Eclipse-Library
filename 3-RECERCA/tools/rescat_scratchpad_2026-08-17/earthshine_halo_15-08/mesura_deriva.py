#!/usr/bin/env python3
"""Mesura de la deriva de la muntura durant la totalitat (tren Vixen/R6).

1. Ajust subpixel del limbe lunar (cercle) a cada fotograma de mig eclipsi.
2. Traça solar per correlacio de fase entre parelles del MATEIX temps
   d'exposicio, amb la Lluna esborrada (farciment radial).
3. Tancament: (Lluna - Sol) mesurat contra efemerides topocentriques
   -> orientacio del sensor, escala de placa i residus.
"""
import json, os, re, time
import numpy as np
import tifffile
from scipy.ndimage import map_coordinates, uniform_filter
from skimage.registration import phase_cross_correlation

SCRATCH = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/bd892f38-1fd3-470f-9bc5-71eb7485933a/scratchpad"
CALDIR = "/Users/USUARI/Desktop/Eclipse Vixen Unfiltered/Calibrated_Claude"
C2_LOCAL = ("20", "28", "46.0")

def log(m):
    print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)

def parse_exp(s):
    s = str(s)
    if s == "10": return 10.3
    m = re.match(r"^(\d+)/(\d+)$", s)
    if m: return int(m.group(1)) / int(m.group(2))
    return float(s)

def t_since_c2(dto, subsec):
    h, mi, se = dto.split()[1].split(":")
    t = int(h)*3600 + int(mi)*60 + float(se) + float(f"0.{subsec}")
    c2 = int(C2_LOCAL[0])*3600 + int(C2_LOCAL[1])*60 + float(C2_LOCAL[2])
    return t - c2

exif = json.load(open(f"{SCRATCH}/exif_unfiltered.json"))
frames = []
for x in exif:
    exp = parse_exp(x["ExposureTime"])
    if abs(exp - 1/3200) < 1e-6 or abs(exp - 1/320) < 1e-6:
        continue
    name = os.path.basename(x["SourceFile"]).replace(".CR3", "")
    frames.append({"name": name, "exp": exp,
                   "t_start": t_since_c2(x["DateTimeOriginal"], x.get("SubSecTimeOriginal", 0))})
frames.sort(key=lambda f: f["t_start"])
log(f"{len(frames)} fotogrames de mig eclipsi")

# ── 1. limbe lunar + imatge reduida amb la Lluna esborrada ──────────────
DS = 4
NRAYS = 720
R_WIN = (370, 520)
angles = np.linspace(0, 2*np.pi, NRAYS, endpoint=False)
ca, sa = np.cos(angles), np.sin(angles)
rs = np.arange(R_WIN[0], R_WIN[1], 0.5)

def fit_circle(px, py):
    A = np.c_[2*px, 2*py, np.ones(len(px))]
    b = px**2 + py**2
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    cx, cy = sol[0], sol[1]
    R = np.sqrt(sol[2] + cx**2 + cy**2)
    return cx, cy, R

def limb_fit(g, cx, cy):
    for _ in range(3):
        # perfil radial per a cada raig, derivada, pic subpixel
        X = cx + rs[None, :]*ca[:, None]
        Y = cy + rs[None, :]*sa[:, None]
        prof = map_coordinates(g, [Y.ravel(), X.ravel()], order=1,
                               mode="nearest").reshape(NRAYS, len(rs))
        d = np.gradient(prof, axis=1)
        pk = d.argmax(axis=1)
        val = d[np.arange(NRAYS), pk]
        ok = (val > np.median(val)*0.25) & (pk > 2) & (pk < len(rs)-3)
        # subpixel per parabola
        p0 = d[np.arange(NRAYS), np.clip(pk-1, 0, None)]
        p1 = val
        p2 = d[np.arange(NRAYS), np.clip(pk+1, None, len(rs)-1)]
        denom = (p0 - 2*p1 + p2)
        off = np.where(np.abs(denom) > 1e-9, 0.5*(p0-p2)/denom, 0.0)
        rpk = rs[pk] + np.clip(off, -1, 1)*0.5
        px = cx + rpk*ca
        py = cy + rpk*sa
        cx2, cy2, R = fit_circle(px[ok], py[ok])
        res = np.abs(np.hypot(px-cx2, py-cy2) - R)
        ok &= res < np.maximum(2.5*np.median(res[ok]), 1.0)
        cx, cy, R = fit_circle(px[ok], py[ok])
        rms = float(np.sqrt(np.mean((np.hypot(px[ok]-cx, py[ok]-cy) - R)**2)))
    return cx, cy, R, rms, int(ok.sum())

results, ds_cache = [], {}
init = None
for i, f in enumerate(frames):
    g = tifffile.imread(f"{CALDIR}/{f['name']}_cal.tif")[:, :, 1].astype(np.float32)
    if init is None:
        # primer fotograma: filtre adaptat de disc sobre versio reduida
        gs = uniform_filter(g[::DS, ::DS], 12)
        R0 = int(441/DS)
        best, bxy = None, None
        for yy in range(R0+10, gs.shape[0]-R0-10, 8):
            for xx in range(R0+10, gs.shape[1]-R0-10, 8):
                v = gs[yy, xx]
                if best is None or v < best:
                    best, bxy = v, (xx*DS, yy*DS)
        init = bxy
    cx, cy, R, rms, nrays = limb_fit(g, *init)
    init = (cx, cy)
    f.update(moon_x=cx, moon_y=cy, moon_R=R, fit_rms=rms, nrays=nrays)
    results.append(f)
    # versio reduida normalitzada amb la Lluna esborrada per farciment radial
    gd = g[::DS, ::DS] / f["exp"]
    yy, xx = np.mgrid[0:gd.shape[0], 0:gd.shape[1]]
    rr = np.hypot(xx - cx/DS, yy - cy/DS)
    moon = rr < (R/DS + 6)
    rq = np.clip(rr.astype(int), 0, 2000)
    fill = np.zeros(2001, np.float32)
    for rad in range(2001):
        m = (rq == rad) & ~moon
        fill[rad] = np.median(gd[m]) if m.sum() > 40 else (fill[rad-1] if rad else 0)
    gd2 = gd.copy()
    gd2[moon] = fill[rq[moon]]
    ds_cache[f["name"]] = np.log1p(np.clip(gd2, 0, None))
    log(f"[{i+1}/{len(frames)}] {f['name']} exp {f['exp']:g}s t={f['t_start']:+.1f}s "
        f"centre=({cx:.2f},{cy:.2f}) R={R:.2f} rms={rms:.2f} rays={nrays}")

# ── 2. parelles del mateix temps d'exposicio -> vectors de deriva ───────
by_exp = {}
for f in results:
    by_exp.setdefault(f["exp"], []).append(f)
pairs = []
hann = None
for exp, fl in sorted(by_exp.items()):
    for a, b in zip(fl, fl[1:]):
        ia, ib = ds_cache[a["name"]], ds_cache[b["name"]]
        if hann is None:
            wy = np.hanning(ia.shape[0])[:, None]
            wx = np.hanning(ia.shape[1])[None, :]
            hann = (wy*wx).astype(np.float32)
        sh, err, _ = phase_cross_correlation(ia*hann, ib*hann, upsample_factor=100)
        # sh = despl. per portar b sobre a  ->  contingut de b = a - sh
        dt = (b["t_start"] + b["exp"]/2) - (a["t_start"] + a["exp"]/2)
        pairs.append({"exp": exp, "a": a["name"], "b": b["name"], "dt": dt,
                      "dx": -sh[1]*DS, "dy": -sh[0]*DS, "err": float(err)})
        log(f"parella {exp:g}s {a['name']}->{b['name']} dt={dt:.1f}s "
            f"despl=({-sh[1]*DS:+.2f},{-sh[0]*DS:+.2f}) px err={err:.3f}")

np.save(f"{SCRATCH}/deriva_pairs.npy", pairs, allow_pickle=True)
np.save(f"{SCRATCH}/deriva_frames.npy", results, allow_pickle=True)
log("mesures desades; ara l'analisi i el grafic")

# ── 3. analisi: deriva solar, tancament amb efemerides ──────────────────
from skyfield.api import Loader, wgs84
load = Loader(os.path.expanduser("~/.cache/skyfield"))
tsc = load.timescale()
eph = load("de440s.bsp")
sun, moon, earth = eph["sun"], eph["moon"], eph["earth"]
lloc = earth + wgs84.latlon(42.299407, -5.02503, elevation_m=798)

def eph_offset(t_c2):
    t = tsc.utc(2026, 8, 12, 18, 28, 46.0 + t_c2)
    obs = lloc.at(t)
    s = obs.observe(sun).apparent()
    m = obs.observe(moon).apparent()
    ra_s, dec_s, _ = s.radec(epoch="date")
    ra_m, dec_m, dist_m = m.radec(epoch="date")
    dra = (ra_m._degrees - ra_s._degrees)*3600*np.cos(dec_s.radians)
    ddec = (dec_m.degrees - dec_s.degrees)*3600
    ang_R = np.degrees(np.arcsin(1737.4/dist_m.km))*3600
    return np.array([dra, ddec]), ang_R

# deriva solar: mitjana ponderada dels vectors de parella
W = np.array([abs(p["dt"]) for p in pairs])
vx = np.array([p["dx"]/p["dt"] for p in pairs])
vy = np.array([p["dy"]/p["dt"] for p in pairs])
drift_rate = np.array([np.sum(W*vx)/W.sum(), np.sum(W*vy)/W.sum()])
scat = np.array([np.sqrt(np.sum(W*(vx-drift_rate[0])**2)/W.sum()),
                 np.sqrt(np.sum(W*(vy-drift_rate[1])**2)/W.sum())])
log(f"deriva solar (px/s): ({drift_rate[0]:+.4f}, {drift_rate[1]:+.4f}) "
    f"dispersio ({scat[0]:.4f}, {scat[1]:.4f})")

# tancament: track lunar corregit de deriva contra efemerides (Procrustes)
tm = np.array([f["t_start"] + f["exp"]/2 for f in results])
mx = np.array([f["moon_x"] for f in results])
my = np.array([f["moon_y"] for f in results])
rel = np.c_[mx - drift_rate[0]*tm, my - drift_rate[1]*tm]
E = np.array([eph_offset(t)[0] for t in tm])
Rm_arc = np.mean([eph_offset(t)[1] for t in tm[:1]])
# ajust: rel ~ s * G(theta, mirall) @ E + c
best = None
for mir in (1, -1):
    Em = E.copy(); Em[:, 0] *= mir
    A = np.c_[Em[:, 0], -Em[:, 1], np.ones(len(E)), np.zeros(len(E))]
    B = np.c_[Em[:, 1],  Em[:, 0], np.zeros(len(E)), np.ones(len(E))]
    M = np.vstack([A, B])
    obs = np.concatenate([rel[:, 0], rel[:, 1]])
    sol, *_ = np.linalg.lstsq(M, obs, rcond=None)
    pred = M @ sol
    rmse = float(np.sqrt(np.mean((obs - pred)**2)))
    if best is None or rmse < best[0]:
        best = (rmse, mir, sol)
rmse, mir, sol = best
scale_px_per_arcsec = np.hypot(sol[0], sol[1])
theta = np.degrees(np.arctan2(sol[1], sol[0]))
plate = 1/scale_px_per_arcsec
log(f"tancament: rmse={rmse:.3f} px · mirall={mir} · rotacio sensor={theta:.2f} graus")
log(f"escala de placa per tancament: {plate:.4f} arcsec/px")
moonR = float(np.mean([f["moon_R"] for f in results]))
log(f"escala per radi lunar: {Rm_arc/moonR:.4f} arcsec/px (R_lluna {moonR:.1f} px, efem. {Rm_arc:.1f} arcsec)")

# deriva en el mon real: passa la deriva de px a arcsec pel tancament
c, s_ = np.cos(np.radians(theta)), np.sin(np.radians(theta))
G = np.array([[c, -s_], [s_, c]]) * scale_px_per_arcsec
Ginv = np.linalg.inv(G)
drift_sky = Ginv @ drift_rate      # (dRA*cosd, dDec) arcsec/s, amb mirall aplicat a x
drift_sky[0] *= mir
rate_arc = np.hypot(*drift_sky)
pa = (np.degrees(np.arctan2(drift_sky[0], drift_sky[1])) + 360) % 360
log(f"DERIVA MESURADA: {rate_arc:.4f} arcsec/s · PA {pa:.1f} graus · "
    f"{rate_arc*105:.1f} arcsec en tota la totalitat")
log(f"error polar equivalent (si tot fos alineacio): {np.degrees(np.arcsin(min(rate_arc/15.041,1)))*60:.1f} arcmin")

# residus del tancament per fotograma
pred = (G @ (E*np.array([mir, 1])).T).T + np.array([sol[2], sol[3]])
resid = rel - pred
per_res = np.hypot(resid[:, 0], resid[:, 1])
log(f"residus tancament: mediana {np.median(per_res):.2f} px · p95 {np.percentile(per_res,95):.2f} px")

# comprovacio del ritme relatiu mesurat contra efemerides
relv = np.polyfit(tm, rel[:, 0], 1)[0], np.polyfit(tm, rel[:, 1], 1)[0]
rate_rel_px = np.hypot(*relv)
log(f"ritme relatiu Lluna-Sol mesurat: {rate_rel_px*plate:.4f} arcsec/s "
    f"(efemerides: 0.5905)")

# ── 4. grafics ──────────────────────────────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, axs = plt.subplots(1, 3, figsize=(19, 6))
ax = axs[0]
tp = np.array([(p_ := p)["dt"]*0 + (results[0]["t_start"]) for p in pairs])
for p in pairs:
    ax.arrow(0, 0, p["dx"]/p["dt"]*60, p["dy"]/p["dt"]*60, head_width=0.15,
             alpha=0.45, color="steelblue")
ax.arrow(0, 0, drift_rate[0]*60, drift_rate[1]*60, head_width=0.2, color="crimson")
ax.set_title(f"Deriva solar per parella (px/min)\nmitjana: {rate_arc:.3f}\"/s · PA {pa:.0f}°")
ax.set_xlabel("x (px/min)"); ax.set_ylabel("y (px/min)"); ax.grid(alpha=0.3); ax.axis("equal")
ax = axs[1]
ax.plot(E[:, 0]*mir*scale_px_per_arcsec + 0*sol[2], E[:, 1]*scale_px_per_arcsec, "-",
        color="gray", label="efemèrides (escalades)")
ax.plot(rel[:, 0]-sol[2], rel[:, 1]-sol[3], "o", ms=4, color="crimson", label="mesurat")
ax.set_title(f"Track Lluna−Sol · tancament rmse {rmse:.2f} px")
ax.set_xlabel("px"); ax.set_ylabel("px"); ax.legend(); ax.grid(alpha=0.3); ax.axis("equal")
ax = axs[2]
ax.plot(tm, per_res, "o", ms=4)
ax.set_title("Residu del tancament per fotograma")
ax.set_xlabel("t des de C2 (s)"); ax.set_ylabel("px"); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig(f"{SCRATCH}/deriva_mesurada.png", dpi=110)
log("grafic desat")