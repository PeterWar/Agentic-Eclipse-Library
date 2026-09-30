#!/usr/bin/env python3
"""Lot de calibratge del tren Sony: 194 ARW d'`Eclipse 2026/300mm A7RIIIA`.

Mateix mètode que `lot_calibratge_vixen.py` (research/71), adaptat a
l'A7RIIIA: per a cada exposicio de l'escala, master dark per MEDIANA de la
biblioteca del 15-08 (llargs tots a 40 C, la temperatura real de la
totalitat), resta en espai raw i demosaic AHD amb WB de camera.

Sortida: TIFF lineal de 16 bits a `300mm A7RIIIA/calibrated/` + manifest CSV amb
SHA-256. Idempotent: es pot reprendre. Els ARW originals no es toquen.

Els tres shutters que Pere va disparar a ma i que la biblioteca no cobreix
(1/1000, 1/500, 1/640) fan servir el master mes rapid disponible com a bias:
a menys de 2 ms el corrent fosc es < 0,01 ADU i el que importa nomes es el
pedestal, que viatja dins el master.
"""
import csv
import hashlib
import json
import os
import subprocess
import sys
import time

import numpy as np
import rawpy
import tifffile

BASE = "/Users/USUARI/Desktop/Eclipse 2026"
LIGHTS = os.path.join(BASE, "300mm A7RIIIA")
DARKS = os.path.join(LIGHTS, "Darks A7RIIIA Eclipse")
OUT = os.path.join(LIGHTS, "calibrated")
MASTERS = os.path.join(OUT, "_masters")
LOG = os.path.join(OUT, "proces.log")

MODEL = "ILCE-7RM3A"
PEDESTAL_MIN, PEDESTAL_MAX = 505.0, 520.0
CAP = 52  # sostre de darks per master; el grup mes gran (1/400) en te 52


def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG, "a") as fh:
        fh.write(line + "\n")


def sha256(path, blocksize=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(blocksize), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_exposure(txt):
    txt = txt.strip()
    if not txt or txt == "-":
        return None
    if "/" in txt:
        a, b = txt.split("/", 1)
        return float(a) / float(b)
    return float(txt)


def key_of(exp):
    return f"{exp:.9g}"


def inventory(folder):
    """FileName, ExposureTime, ISO, Model i CameraTemperature per ARW.

    Sense `-fast2`: les notes de fabricant Sony hi porten la temperatura.
    """
    out = subprocess.run(
        ["exiftool", "-q", "-T", "-FileName", "-ExposureTime", "-ISO",
         "-Model", "-CameraTemperature", "-ext", "ARW", folder],
        capture_output=True, text=True).stdout
    items = {}
    for line in out.splitlines():
        parts = line.rstrip("\n").split("\t")
        if len(parts) < 5:
            continue
        name, exp, iso, model, temp = parts[:5]
        e = parse_exposure(exp)
        if e is None:
            continue
        items[name] = {"exposure_s": e, "iso": iso.strip(),
                       "model": model.strip(), "temp": temp.strip()}
    return items


def main():
    os.makedirs(MASTERS, exist_ok=True)
    log("=" * 62)
    log("inventari de llums i darks (exiftool, amb notes de fabricant)...")
    lights = inventory(LIGHTS)
    darks = inventory(DARKS)
    log(f"{len(lights)} llums · {len(darks)} darks")

    wrong_model = [n for n, m in list(lights.items()) + list(darks.items())
                   if m["model"] != MODEL]
    if wrong_model:
        log(f"ERROR: {len(wrong_model)} fitxers d'un altre cos: {wrong_model[:5]}")
        return 1
    if any(m["iso"] != "100" for m in darks.values()):
        log("ERROR: hi ha darks fora d'ISO 100")
        return 1
    # Llums fora d'ISO 100: no aturen el lot. Als shutters rapids on surten,
    # el master nomes hi aporta el pedestal, que a l'A7RIIIA es 512 a tots
    # els ISO; queda marcat al manifest.
    for n, m in sorted(lights.items()):
        if m["iso"] != "100":
            log(f"AVIS: {n} a ISO {m['iso']} ({m['exposure_s']:.6g}s) → "
                f"master d'ISO 100 com a bias, marcat al manifest")

    need = sorted({key_of(m["exposure_s"]) for m in lights.values()}, key=float)
    groups = {}
    for k in need:
        t = float(k)
        groups[k] = sorted(n for n, m in darks.items()
                           if abs(m["exposure_s"] - t) <= 0.03 * t)

    # Els shutters sense darks propis prenen el master mes rapid disponible:
    # a aquestes velocitats el master nomes hi aporta el pedestal.
    have = [k for k in need if groups[k]]
    if not have:
        log("ERROR: cap grup de darks utilitzable")
        return 1
    fastest = min(have, key=float)
    substitute = {}
    for k in need:
        if not groups[k]:
            substitute[k] = fastest
            log(f"AVIS: cap dark per a {k}s → master de {fastest}s com a bias "
                f"({sum(1 for m in lights.values() if key_of(m['exposure_s']) == k)} llums)")

    masters, info = {}, {}
    for k in have:
        npy = os.path.join(MASTERS, f"master_{k}.npy")
        jsn = os.path.join(MASTERS, f"master_{k}.json")
        if os.path.exists(npy) and os.path.exists(jsn):
            masters[k] = np.load(npy)
            with open(jsn) as fh:
                info[k] = json.load(fh)
            log(f"master {k}s reutilitzat ({info[k]['n_darks']} darks)")
            continue

        names = groups[k][:CAP]
        stack, used, stds = None, [], []
        for name in names:
            with rawpy.imread(os.path.join(DARKS, name)) as r:
                img = r.raw_image.copy()
            sub = img[::4, ::4].astype(np.float32)
            med = float(np.median(sub))
            if not (PEDESTAL_MIN <= med <= PEDESTAL_MAX):
                log(f"  descartat {name} (mediana {med:.1f})")
                continue
            if stack is None:
                stack = np.empty((len(names),) + img.shape, np.uint16)
            stack[len(used)] = img
            used.append(name)
            stds.append(float(sub.std()))
        if not used:
            log(f"ERROR: cap dark valid per a {k}s")
            return 1
        stack = stack[:len(used)]

        H = stack.shape[1]
        m = np.empty(stack.shape[1:], np.float32)
        for r0 in range(0, H, 512):
            r1 = min(r0 + 512, H)
            m[r0:r1] = np.median(stack[:, r0:r1, :].astype(np.float32), axis=0)
        del stack

        ped = float(np.median(m))
        if not (PEDESTAL_MIN <= ped <= PEDESTAL_MAX):
            log(f"ERROR: pedestal del master {k}s fora de rang: {ped:.1f}")
            return 1
        temps = sorted({darks[n]["temp"] for n in used})
        np.save(npy, m)
        masters[k] = m
        info[k] = {"exposure_s": float(k), "n_darks": len(used),
                   "pedestal_adu": ped, "temps": temps,
                   "dark_signal_median_adu": round(float(np.median(m)) - 512.0, 3),
                   "dark_signal_p999_adu": round(float(np.percentile(m[::4, ::4], 99.9)) - 512.0, 1),
                   "frame_std_min": min(stds), "frame_std_max": max(stds),
                   "darks": used}
        with open(jsn, "w") as fh:
            json.dump(info[k], fh, indent=1)
        log(f"master {k}s: {len(used)} darks · pedestal {ped:.1f} · "
            f"temps {','.join(temps)} · corrent fosc p99,9 "
            f"{info[k]['dark_signal_p999_adu']:.1f} ADU")

    rows, t0, done = [], time.time(), 0
    todo = sorted(lights.items())
    for i, (name, meta) in enumerate(todo, 1):
        k = key_of(meta["exposure_s"])
        mk = k if k in masters else substitute[k]
        dst = os.path.join(OUT, name.replace(".ARW", "_cal.tif"))
        if os.path.exists(dst):
            continue
        src = os.path.join(LIGHTS, name)
        with rawpy.imread(src) as raw:
            black_map = np.array(raw.black_level_per_channel,
                                 np.float32)[raw.raw_colors]
            white = float(raw.white_level)
            dark_signal = np.clip(masters[mk] - black_map, 0, None)
            cal = np.clip(raw.raw_image.astype(np.float32) - dark_signal,
                          0, white)
            raw.raw_image[:] = cal.astype(np.uint16)
            rgb = raw.postprocess(use_camera_wb=True, no_auto_bright=True,
                                  output_bps=16, gamma=(1, 1),
                                  demosaic_algorithm=rawpy.DemosaicAlgorithm.AHD)
        tifffile.imwrite(dst, rgb, photometric="rgb", compression="zlib")
        sky = rgb[300:1300, -1700:-200]
        rows.append({
            "original": name,
            "exposure_s": round(meta["exposure_s"], 9),
            "iso": meta["iso"],
            "camera_temp": meta["temp"],
            "sha256_original": sha256(src),
            "master": f"master_{mk}.npy",
            "master_substitute": "si" if mk != k else "no",
            "n_darks": info[mk]["n_darks"],
            "output": os.path.basename(dst),
            "sha256_output": sha256(dst),
            "sky_R_adu14": round(float(np.median(sky[..., 0])) / 4, 1),
            "sky_G_adu14": round(float(np.median(sky[..., 1])) / 4, 1),
            "sky_B_adu14": round(float(np.median(sky[..., 2])) / 4, 1),
        })
        done += 1
        if done % 10 == 0 or i == len(todo):
            rate = (time.time() - t0) / max(1, done)
            log(f"[{i}/{len(todo)}] {name} · {done} noves · {rate:.1f} s/foto")

        if len(rows) >= 10:
            write_manifest(rows)
            rows = []

    if rows:
        write_manifest(rows)
    log(f"FET: {done} calibrades noves en aquesta passada")
    return 0


def write_manifest(rows):
    mpath = os.path.join(OUT, "manifest.csv")
    exists = os.path.exists(mpath)
    with open(mpath, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        if not exists:
            w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    sys.exit(main())
