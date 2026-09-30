#!/usr/bin/env python3
"""Deriva de l'Skywatcher (Sony A7RIIIA + 300 GM): limbe + parcials.

EXIF Sony marca el FINAL de l'exposicio: t_mid = t_exif - exp/2.
"""
import json, os, re, time
import numpy as np, rawpy
from scipy.ndimage import map_coordinates
from numpy.fft import rfft2, irfft2

S = "/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/bd892f38-1fd3-470f-9bc5-71eb7485933a/scratchpad"
DIR = "/Users/USUARI/Desktop/Eclipse 2026/300mm A7RIIIA"
exif = json.load(open(f"{S}/exif_sony.json"))
tC2 = 20*3600+28*60+46.0

def pe(s):
    s = str(s); m = re.match(r"^(\d+)/(\d+)$", s)
    return int(m.group(1))/int(m.group(2)) if m else float(s)

def t_end(x):
    h, mi, se = x["DateTimeOriginal"].split()[1].split(":")
    t = int(h)*3600+int(mi)*60+float(se)
    ss = x.get("SubSecTimeOriginal")
    if ss not in (None, ""):
        t += float(f"0.{ss}")
    return t

def log(m):
    print(f"{time.strftime('%H:%M:%S')} {m}", flush=True)

R_MOON = 316.0   # esperat a ~3.10 arcsec/px; la mesura el corregira
NR = 720
ang = np.linspace(0, 2*np.pi, NR, endpoint=False)
ca, sa = np.cos(ang), np.sin(ang)
rs = np.arange(255, 390, 0.5)

def init_disc(g):
    DS = 4
    gd = g[::DS, ::DS].astype(np.float32)
    R0, R1, R2 = int((R_MOON-15)/DS), int((R_MOON+12)/DS), int((R_MOON+70)/DS)
    n = 2*R2+1
    yy, xx = np.mgrid[-R2:R2+1, -R2:R2+1]
    rr = np.hypot(yy, xx)
    disc = (rr <= R0).astype(np.float32)
    anell = ((rr >= R1) & (rr <= R2)).astype(np.float32)
    k = anell/anell.sum() - disc/disc.sum()
    kpad = np.zeros_like(gd); kpad[:n, :n] = k
    conv = irfft2(rfft2(gd)*rfft2(kpad), s=gd.shape)
    conv = np.roll(conv, (-R2, -R2), axis=(0, 1))
    m = R2+2
    conv[:m, :] = -np.inf; conv[-m:, :] = -np.inf; conv[:, :m] = -np.inf; conv[:, -m:] = -np.inf
    cy, cx = np.unravel_index(np.argmax(conv), conv.shape)
    return cx*DS, cy*DS

def fit_circle(px, py):
    A = np.c_[2*px, 2*py, np.ones(len(px))]
    sol, *_ = np.linalg.lstsq(A, px**2+py**2, rcond=None)
    cx, cy = sol[0], sol[1]
    return cx, cy, np.sqrt(sol[2]+cx**2+cy**2)

def limb_fit(g, cx, cy):
    cx2, cy2, R, rms, nok, spread = cx, cy, 0, 99, 0, 0
    for _ in range(5):
        X = cx + rs[None, :]*ca[:, None]; Y = cy + rs[None, :]*sa[:, None]
        prof = map_coordinates(g, [Y.ravel(), X.ravel()], order=1, mode="constant", cval=np.nan).reshape(NR, len(rs))
        d = np.nan_to_num(np.gradient(prof, axis=1))
        pk = d.argmax(axis=1)
        val = d[np.arange(NR), pk]
        ok = (val > max(np.percentile(val, 55)*0.3, 1.0)) & (pk > 3) & (pk < len(rs)-4)
        p0 = d[np.arange(NR), np.clip(pk-1, 0, None)]; p1 = val
        p2 = d[np.arange(NR), np.clip(pk+1, None, len(rs)-1)]
        den = p0-2*p1+p2
        off = np.where(np.abs(den) > 1e-9, 0.5*(p0-p2)/den, 0)
        rpk = rs[pk] + np.clip(off, -1, 1)*0.5
        px, py = cx+rpk*ca, cy+rpk*sa
        for _ in range(3):
            if ok.sum() < 12: break
            cx2, cy2, R = fit_circle(px[ok], py[ok])
            res = np.abs(np.hypot(px-cx2, py-cy2)-R)
            ok = ok & (res < np.maximum(2.5*np.median(res[ok]), 0.8))
        cx, cy = cx+np.clip(cx2-cx, -60, 60), cy+np.clip(cy2-cy, -60, 60)
        if ok.sum():
            rms = float(np.sqrt(np.mean((np.hypot(px[ok]-cx2, py[ok]-cy2)-R)**2)))
            az = np.sort(ang[ok]); nok = int(ok.sum())
            spread = float(np.degrees(az.max()-az.min()))
        if np.hypot(cx2-cx, cy2-cy) < 0.05: break
    return cx2, cy2, float(R), rms, nok, spread

# ── A. limbe als 18 de mig eclipsi ──────────────────────────────────────
mig = sorted([x for x in exif if pe(x["ExposureTime"]) >= 1/35 and 0 < t_end(x)-tC2 < 104], key=t_end)
res = []
for x in mig:
    name = os.path.basename(x["SourceFile"]).replace(".ARW", "")
    exp = pe(x["ExposureTime"])
    with rawpy.imread(x["SourceFile"]) as r:
        g = r.postprocess(use_camera_wb=True, no_auto_bright=True, output_bps=16,
                          gamma=(1, 1), half_size=False)[:, :, 1].astype(np.float32)
    cx0, cy0 = init_disc(g)
    cx, cy, R, rms, nok, spread = limb_fit(g, float(cx0), float(cy0))
    valid = (nok > 250) and (rms < 3.0) and (280 < R < 360) and spread > 200
    t_mid = t_end(x) - tC2 - exp/2
    res.append({"name": name, "exp": exp, "t_mid": t_mid, "moon_x": cx, "moon_y": cy,
                "moon_R": R, "rms": rms, "valid": bool(valid)})
    log(f"{name} exp {exp:g} t_mid={t_mid:+.1f} centre=({cx:.1f},{cy:.1f}) R={R:.2f} rms={rms:.2f} n={nok} {'OK' if valid else 'REBUTJAT'}")
np.save(f"{S}/limb_sony.npy", res, allow_pickle=True)
V = [f for f in res if f["valid"]]
Rs = np.array([f["moon_R"] for f in V])
ts = np.array([f["t_mid"] for f in V])
xs = np.array([f["moon_x"] for f in V]); ys = np.array([f["moon_y"] for f in V])
kx = np.polyfit(ts, xs, 1); ky = np.polyfit(ts, ys, 1)
resid = np.hypot(xs-np.polyval(kx, ts), ys-np.polyval(ky, ts))
plate = 979.1/Rs.mean()
log(f"VALIDS {len(V)}/{len(res)} · R={Rs.mean():.2f}±{Rs.std():.2f} px · ESCALA {plate:.4f} arcsec/px")
log(f"v_LLUNA=({kx[0]:+.4f},{ky[0]:+.4f}) px/s · |v|={np.hypot(kx[0],ky[0]):.4f} px/s = {np.hypot(kx[0],ky[0])*plate:.4f} arcsec/s · residu med {np.median(resid):.2f} px")
log(f"relatiu efemerides: 0.5905 arcsec/s = {0.5905/plate:.4f} px/s")
# desviacio de la DSC06990 respecte de la traça (l'ancora moguda)
for f in res:
    if f["name"] == "DSC06990":
        dx = f["moon_x"]-np.polyval(kx, f["t_mid"]); dy = f["moon_y"]-np.polyval(ky, f["t_mid"])
        log(f"DSC06990 (ancora moguda): desviacio de la traça ({dx:+.1f},{dy:+.1f}) px · rms limbe {f['rms']:.2f}")

# ── B. cercle solar a les 122 parcials 1/400 (mitja resolucio) ──────────
R_SUN_H = 947.0/plate/2
parts = sorted([x for x in exif if str(x["ExposureTime"]) == "1/400"], key=t_end)
rng = np.random.default_rng(7)
def circle3(p1, p2, p3):
    ax, ay = p1; bx, by = p2; cx, cy = p3
    dd = 2*(ax*(by-cy)+bx*(cy-ay)+cx*(ay-by))
    if abs(dd) < 1e-6: return None
    ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/dd
    uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/dd
    return ux, uy, np.hypot(ax-ux, ay-uy)
from scipy.ndimage import binary_erosion
sun = []
for i, x in enumerate(parts):
    name = os.path.basename(x["SourceFile"]).replace(".ARW", "")
    with rawpy.imread(x["SourceFile"]) as r:
        g = r.postprocess(half_size=True, use_camera_wb=True, no_auto_bright=True,
                          output_bps=16, gamma=(1, 1))[:, :, 1].astype(np.float32)
    mx = float(np.percentile(g, 99.99))
    if mx < 3000: continue
    level = 0.35*mx
    m = g > level
    if m.sum() < 200: continue
    edge = m & ~binary_erosion(m, iterations=2)
    ysn, xsn = np.nonzero(edge)
    if len(xsn) < 60: continue
    if len(xsn) > 4000:
        sel = rng.choice(len(xsn), 4000, replace=False); xsn, ysn = xsn[sel], ysn[sel]
    P = np.c_[xsn, ysn].astype(float)
    best = None
    for _ in range(400):
        idx = rng.choice(len(P), 3, replace=False)
        c = circle3(P[idx[0]], P[idx[1]], P[idx[2]])
        if c is None or not (R_SUN_H*0.88 < c[2] < R_SUN_H*1.12): continue
        dist = np.hypot(P[:, 0]-c[0], P[:, 1]-c[1])
        nin = int(np.count_nonzero(np.abs(dist-c[2]) < 2.5))
        if best is None or nin > best[0]: best = (nin, c)
    if best is None or best[0] < 25: continue
    cands = []
    for _ in range(120):
        idx = rng.choice(len(P), 3, replace=False)
        c = circle3(P[idx[0]], P[idx[1]], P[idx[2]])
        if c is None or not (R_SUN_H*0.88 < c[2] < R_SUN_H*1.12): continue
        dist = np.hypot(P[:, 0]-c[0], P[:, 1]-c[1])
        nin = int(np.count_nonzero(np.abs(dist-c[2]) < 2.5))
        if nin > 0.6*best[0]:
            th = rng.uniform(0, 2*np.pi, 250); rr2 = c[2]*0.85*np.sqrt(rng.uniform(0, 1, 250))
            sx = np.clip(c[0]+rr2*np.cos(th), 0, g.shape[1]-1).astype(int)
            sy = np.clip(c[1]+rr2*np.sin(th), 0, g.shape[0]-1).astype(int)
            cands.append((float(np.mean(g[sy, sx] > level)), nin, c))
    if not cands: continue
    cands.sort(key=lambda z: (-z[0], -z[1]))
    frac, nin, c = cands[0]
    if frac < 0.25: continue
    scx, scy = c[0], c[1]
    for _ in range(30):
        dx, dy = P[:, 0]-scx, P[:, 1]-scy
        dist = np.hypot(dx, dy)
        w = (np.abs(dist-R_SUN_H) < 4).astype(float)
        if w.sum() < 15: break
        scx += np.sum(w*dx*(1-R_SUN_H/np.maximum(dist, 1)))/w.sum()
        scy += np.sum(w*dy*(1-R_SUN_H/np.maximum(dist, 1)))/w.sum()
    nin2 = int(w.sum())
    rms = float(np.sqrt(np.average((dist[w > 0]-R_SUN_H)**2, weights=w[w > 0]))) if nin2 >= 15 else 99.0
    if nin2 >= 25 and rms < 3.0:
        sun.append({"name": name, "t": t_end(x)-1/800-tC2, "x": scx*2, "y": scy*2})
    if (i+1) % 20 == 0:
        log(f"parcials {i+1}/{len(parts)} · bones {len(sun)}")
np.save(f"{S}/sun_track_sony.npy", sun, allow_pickle=True)
log(f"FET: {len(sun)} posicions solars bones de {len(parts)} parcials")
