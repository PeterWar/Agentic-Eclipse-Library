#!/usr/bin/env python3
"""Lot de calibratge Vixen: 124 CR3 d'Eclipse Vixen Unfiltered.

Per a cada exposicio de l'escala: master dark per MEDIANA (cap 25 darks,
pedestal vigilat), resta en espai raw i demosaic AHD amb WB de camera.
Sortida: TIFF lineal 16 bits + manifest CSV amb SHA-256. Idempotent.
"""
import csv, hashlib, json, os, subprocess, sys, time
import numpy as np
import rawpy
import tifffile

LIGHTS = "/Users/USUARI/Desktop/Eclipse Vixen Unfiltered"
DARKS = "/Users/USUARI/Desktop/Darks Canon R6III Eclipse"
OUT = os.path.join(LIGHTS, "Calibrated_Claude")
MASTERS = os.path.join(OUT, "_masters")
os.makedirs(MASTERS, exist_ok=True)
LOG = os.path.join(OUT, "proces.log")
CAP = 25

def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a") as fh:
        fh.write(line + "\n")

def exposure_of(path):
    r = subprocess.run(["mdls", "-raw", "-name", "kMDItemExposureTimeSeconds", path],
                       capture_output=True, text=True)
    v = r.stdout.strip()
    return None if v in ("", "(null)") else float(v)

def sha256(path, blocksize=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(blocksize), b""):
            h.update(chunk)
    return h.hexdigest()

def key_of(exp):
    return f"{exp:.9g}"

def scan(folder):
    out = {}
    for name in sorted(os.listdir(folder)):
        if name.lower().endswith(".cr3"):
            e = exposure_of(os.path.join(folder, name))
            if e is not None:
                out[name] = e
    return out

log("inventari de lights i darks (mdls)...")
lights = scan(LIGHTS)
darks = scan(DARKS)
log(f"{len(lights)} lights, {len(darks)} darks")

# agrupa darks per exposicio de cada llum (tolerancia relativa 3%)
need = sorted({key_of(e) for e in lights.values()}, key=float)
groups = {k: [n for n, e in darks.items() if abs(e - float(k)) <= 0.03 * float(k)]
          for k in need}
for k in need:
    if len(groups[k]) < 9:
        log(f"AVIS: nomes {len(groups[k])} darks per a {k}s")

masters = {}
master_info = {}
for k in need:
    npy = os.path.join(MASTERS, f"master_{k}.npy")
    if os.path.exists(npy):
        masters[k] = np.load(npy)
        with open(os.path.join(MASTERS, f"master_{k}.json")) as fh:
            master_info[k] = json.load(fh)
        log(f"master {k}s reutilitzat")
        continue
    stack, used, stds = None, [], []
    for name in groups[k]:
        if len(used) >= CAP:
            break
        with rawpy.imread(os.path.join(DARKS, name)) as r:
            img = r.raw_image.copy()
        sub = img[::4, ::4].astype(np.float32)
        med = float(np.median(sub))
        if not (505.0 <= med <= 520.0) or float(np.percentile(sub, 99)) > 560.0:
            log(f"  descartat {name} (mediana {med:.1f})")
            continue
        if stack is None:
            stack = np.empty((min(CAP, len(groups[k])),) + img.shape, np.uint16)
        stack[len(used)] = img
        used.append(name)
        stds.append(float(sub.std()))
    if not used:
        log(f"ERROR: cap dark valid per a {k}s")
        sys.exit(1)
    stack = stack[:len(used)]
    H = stack.shape[1]
    m = np.empty(stack.shape[1:], np.float32)
    for r0 in range(0, H, 512):
        m[r0:r0 + 512] = np.median(stack[:, r0:r0 + 512, :], axis=0)
    del stack
    ped = float(np.median(m))
    if not (505.0 <= ped <= 520.0):
        log(f"ERROR: pedestal del master {k}s fora de rang: {ped:.1f}")
        sys.exit(1)
    np.save(npy, m)
    masters[k] = m
    master_info[k] = {"exposure_s": float(k), "n_darks": len(used), "darks": used,
                      "pedestal_adu": ped,
                      "frame_std_min": min(stds), "frame_std_max": max(stds)}
    with open(os.path.join(MASTERS, f"master_{k}.json"), "w") as fh:
        json.dump(master_info[k], fh, indent=1)
    log(f"master {k}s: {len(used)} darks · pedestal {ped:.1f} · std frames {min(stds):.1f}-{max(stds):.1f}")

rows, t0 = [], time.time()
for i, (name, exp) in enumerate(sorted(lights.items()), 1):
    k = key_of(exp)
    dst = os.path.join(OUT, name.replace(".CR3", "_cal.tif"))
    if os.path.exists(dst):
        log(f"[{i}/{len(lights)}] {name} ja fet, el salto")
        continue
    src = os.path.join(LIGHTS, name)
    with rawpy.imread(src) as raw:
        black_map = np.array(raw.black_level_per_channel, np.float32)[raw.raw_colors]
        white = float(raw.white_level)
        dark_signal = np.clip(masters[k] - black_map, 0, None)
        cal = np.clip(raw.raw_image.astype(np.float32) - dark_signal, 0, white)
        raw.raw_image[:] = cal.astype(np.uint16)
        rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=True,
                              output_bps=16, gamma=(1, 1),
                              demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD)
    tifffile.imwrite(dst, rgb, photometric="rgb", compression="zlib")
    sky = rgb[300:1300, -1700:-200]
    rows.append({"original": name, "exposure_s": exp,
                 "sha256_original": sha256(src),
                 "master": f"master_{k}.npy", "n_darks": master_info[k]["n_darks"],
                 "output": os.path.basename(dst), "sha256_output": sha256(dst),
                 "sky_R_adu14": round(float(np.median(sky[..., 0])) / 4, 1),
                 "sky_G_adu14": round(float(np.median(sky[..., 1])) / 4, 1),
                 "sky_B_adu14": round(float(np.median(sky[..., 2])) / 4, 1)})
    if i % 10 == 0 or i == len(lights):
        rate = (time.time() - t0) / max(1, i)
        log(f"[{i}/{len(lights)}] {name} fet · ritme {rate:.1f} s/foto")

mpath = os.path.join(OUT, "manifest.csv")
exists = os.path.exists(mpath)
with open(mpath, "a", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    if not exists:
        w.writeheader()
    w.writerows(rows)
log(f"FET: {len(rows)} calibrades noves · manifest a {mpath}")
