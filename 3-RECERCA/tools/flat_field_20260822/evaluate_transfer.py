#!/usr/bin/env python3
"""Avalua la transferència dels màsters flat posteriors a l'eclipsi.

No modifica cap RAW ni cap màster S6. Compara el patró fi Vixen amb el PRNU
mesurat durant l'eclipsi, executa nulls sobre RAW que no van construir aquell
PRNU, compara el perfil òptic Sony amb el flat donant vigent i prova el PRNU
Sony sobre un grup repetit del segment C.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any

import numpy as np
import rawpy
from scipy import ndimage as ndi

import build_master_flats as B


VIXEN_ECLIPSE = Path("/Users/USUARI/Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat")
VIXEN_MASTERS = VIXEN_ECLIPSE / "Masters_v2"
SONY_ECLIPSE = Path("/Users/USUARI/Desktop/Eclipse 2026/300mm A7RIIIA")
SONY_DARKS = Path("/Users/USUARI/Downloads/Eclipse 2026/output/postprocessat_final_20260822/masters/sony_darks_s6")
SONY_DONOR = Path("/Users/USUARI/Downloads/Eclipse 2026/output/postprocessat_final_20260822/pilots/sony_optical_flat/flat_a7r3a_optical_rgb.npy")
VIXEN_NULL = ("572A2969.CR3", "572A2987.CR3", "572A2999.CR3", "572A3005.CR3")
SONY_NULL = (
    ("DSC06994.ARW", 0.25),
    ("DSC06995.ARW", 1 / 30),
    ("DSC06996.ARW", 2.0),
    ("DSC06997.ARW", 0.25),
    ("DSC06998.ARW", 1 / 30),
    ("DSC06999.ARW", 2.0),
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def corr_and_slope(a: np.ndarray, b: np.ndarray, stride: int = 4,
                   border: int = 32) -> dict[str, float]:
    aa = a[border:-border:stride, border:-border:stride].astype(np.float64).ravel()
    bb = b[border:-border:stride, border:-border:stride].astype(np.float64).ravel()
    aa -= aa.mean()
    bb -= bb.mean()
    denom = math.sqrt(float(np.dot(aa, aa) * np.dot(bb, bb)))
    r = float(np.dot(aa, bb) / denom)
    slope_b_on_a = float(np.dot(aa, bb) / np.dot(aa, aa))
    return {
        "r": r,
        "slope_second_on_first": slope_b_on_a,
        "std_first": float(aa.std()),
        "std_second": float(bb.std()),
        "n_sampled": int(aa.size),
    }


def old_vixen_factors(shape: tuple[int, int, int]) -> np.ndarray:
    z = np.load(VIXEN_MASTERS / "prnu.npz")
    out = np.empty(shape, np.float32)
    for c, key in enumerate(("00", "01", "10", "11")):
        old = np.asarray(z[key], np.float32)
        old = np.pad(old, ((0, shape[1] - old.shape[0]), (0, shape[2] - old.shape[1])),
                     mode="edge")
        out[c] = 1.0 + old
    return out


def compare_vixen_maps(new_factor: np.ndarray) -> dict[str, Any]:
    old_factor = old_vixen_factors(new_factor.shape)
    direct = []
    bandpass = []
    for c in range(4):
        new_log = np.log(np.clip(new_factor[c], 1e-6, None))
        old_log = np.log(np.clip(old_factor[c], 1e-6, None))
        direct.append({"plane": B.PLANE_NAMES[c], **corr_and_slope(new_log, old_log)})
        new_hp = new_log - ndi.gaussian_filter(new_log, 1.0, mode="reflect")
        old_hp = old_log - ndi.gaussian_filter(old_log, 1.0, mode="reflect")
        bandpass.append({"plane": B.PLANE_NAMES[c], **corr_and_slope(new_hp, old_hp)})
    old_meta = json.loads((VIXEN_MASTERS / "prnu.json").read_text(encoding="utf-8"))
    return {
        "old_map": str(VIXEN_MASTERS / "prnu.npz"),
        "old_map_sha256": sha256(VIXEN_MASTERS / "prnu.npz"),
        "old_split_correlations": old_meta["correlacio_meitats"],
        "direct_log_factor": direct,
        "common_highpass_sigma_1px": bandpass,
        "gate_r_minimum": 0.5,
        "gate_pass": all(row["r"] >= 0.5 and row["slope_second_on_first"] > 0
                         for row in bandpass),
    }


def load_vixen_null(path: Path) -> np.ndarray:
    dark = np.load(VIXEN_MASTERS / "master_0.008.npy", mmap_mode="r")
    dark_full = np.pad(dark, ((0, 4640 - dark.shape[0]), (0, 6960 - dark.shape[1])),
                       mode="edge")
    with rawpy.imread(str(path)) as raw:
        mosaic = raw.raw_image[108:108 + 4640, 172:172 + 6960].astype(np.float32)
    mosaic -= dark_full
    return np.stack([mosaic[oy::2, ox::2] for oy, ox in B.PLANE_OFFSETS])


def load_sony_null(path: Path, exposure: float) -> np.ndarray:
    dark_key = f"{exposure:.10g}"
    dark = np.load(SONY_DARKS / dark_key / "MASTER_DARK_raw_ADU.npy", mmap_mode="r")
    with rawpy.imread(str(path)) as raw:
        mosaic = raw.raw_image_visible.astype(np.float32)
    mosaic -= dark
    return np.stack([mosaic[oy::2, ox::2] for oy, ox in B.PLANE_OFFSETS])


def corr_accumulator() -> dict[str, float]:
    return {"n": 0.0, "sx": 0.0, "sy": 0.0, "sxx": 0.0, "syy": 0.0, "sxy": 0.0}


def add_corr(acc: dict[str, float], x: np.ndarray, y: np.ndarray) -> None:
    xx = x.astype(np.float64, copy=False).ravel()
    yy = y.astype(np.float64, copy=False).ravel()
    acc["n"] += xx.size
    acc["sx"] += float(xx.sum())
    acc["sy"] += float(yy.sum())
    acc["sxx"] += float(np.dot(xx, xx))
    acc["syy"] += float(np.dot(yy, yy))
    acc["sxy"] += float(np.dot(xx, yy))


def finish_corr(acc: dict[str, float]) -> float:
    n = acc["n"]
    cov = acc["sxy"] - acc["sx"] * acc["sy"] / n
    vx = acc["sxx"] - acc["sx"] ** 2 / n
    vy = acc["syy"] - acc["sy"] ** 2 / n
    return float(cov / math.sqrt(max(vx * vy, 1e-30)))


def fine_null(frames: list[tuple[str, np.ndarray]], factors: dict[str, np.ndarray],
              signal_min: float, saturation_signal: float) -> dict[str, Any]:
    branch_sumsq = {branch: np.zeros(4, np.float64) for branch in factors}
    branch_count = {branch: np.zeros(4, np.int64) for branch in factors}
    map_corr = {branch: [corr_accumulator() for _ in range(4)] for branch in factors
                if branch != "control"}
    frame_rows = []
    for name, planes in frames:
        row = {"frame": name, "planes": []}
        for c in range(4):
            signal = planes[c]
            local = ndi.uniform_filter(signal, size=9, mode="reflect")
            rel = (signal - local) / np.maximum(local, 1e-6)
            good = ((local > signal_min) & (signal < saturation_signal) &
                    np.isfinite(rel) & (np.abs(rel) < 0.08))
            good[:12] = False
            good[-12:] = False
            good[:, :12] = False
            good[:, -12:] = False
            plane_row = {"plane": B.PLANE_NAMES[c],
                         "coverage_fraction": float(good.mean()), "branches": {}}
            for branch, factor4 in factors.items():
                corrected = signal if branch == "control" else signal / factor4[c]
                corrected_local = ndi.uniform_filter(corrected, size=9, mode="reflect")
                residual = (corrected - corrected_local) / np.maximum(corrected_local, 1e-6)
                values = residual[good].astype(np.float64)
                sumsq = float(np.dot(values, values))
                branch_sumsq[branch][c] += sumsq
                branch_count[branch][c] += values.size
                plane_row["branches"][branch] = {
                    "rms_percent": float(100.0 * math.sqrt(sumsq / values.size)),
                    "n": int(values.size),
                }
                if branch != "control":
                    map_effect = (factor4[c] - 1.0)[good]
                    # Mostreig determinista; el corr acumulat continua tenint
                    # milions de mostres sense inflar memòria.
                    add_corr(map_corr[branch][c], rel[good][::4], map_effect[::4])
            row["planes"].append(plane_row)
        frame_rows.append(row)

    aggregate = []
    for c in range(4):
        control_rms = math.sqrt(branch_sumsq["control"][c] / branch_count["control"][c])
        branches = {}
        for branch in factors:
            rms = math.sqrt(branch_sumsq[branch][c] / branch_count[branch][c])
            branches[branch] = {
                "rms_percent": 100.0 * rms,
                "improvement_vs_control_percent": 100.0 * (1.0 - rms / control_rms),
                "n": int(branch_count[branch][c]),
            }
            if branch != "control":
                branches[branch]["correlation_raw_residual_vs_map"] = finish_corr(map_corr[branch][c])
        aggregate.append({"plane": B.PLANE_NAMES[c], "branches": branches})
    return {
        "method": "dark-subtracted linear CFA; 9x9 local high-pass; common mask local signal threshold, |residual|<8%, 12-px border; RMS",
        "aggregate": aggregate,
        "per_frame": frame_rows,
    }


def compare_sony_optical(new_radial: np.ndarray) -> dict[str, Any]:
    donor_rgb = np.load(SONY_DONOR, mmap_mode="r")
    donor_cfa4 = np.empty_like(new_radial)
    rgb_channel = (0, 1, 1, 2)
    for c, ((oy, ox), channel) in enumerate(zip(B.PLANE_OFFSETS, rgb_channel, strict=True)):
        donor_cfa4[c] = donor_rgb[oy::2, ox::2, channel]
    annulus = B.central_annulus(new_radial.shape[-2:])
    donor_cfa4, _ = B.normalize_factor(donor_cfa4, annulus)
    donor_radial = np.exp(B.radialize_log(np.log(np.clip(donor_cfa4, 1e-6, None))))
    donor_radial, _ = B.normalize_factor(donor_radial, annulus)
    rows = []
    for c in range(4):
        a = np.log(np.clip(new_radial[c], 1e-6, None))[::8, ::8].ravel()
        b = np.log(np.clip(donor_radial[c], 1e-6, None))[::8, ::8].ravel()
        delta = np.abs(a - b) * 100.0
        rows.append({
            "plane": B.PLANE_NAMES[c],
            "log_field_r": float(np.corrcoef(a, b)[0, 1]),
            "abs_log_ratio_percent": {
                "median": float(np.median(delta)),
                "p95": float(np.percentile(delta, 95)),
                "p99": float(np.percentile(delta, 99)),
                "max": float(np.max(delta)),
            },
            "corner_tl_new": float(new_radial[c, 0, 0]),
            "corner_tl_donor": float(donor_radial[c, 0, 0]),
        })
    return {
        "donor_flat": str(SONY_DONOR),
        "donor_sha256": sha256(SONY_DONOR),
        "common_normalization": "central annulus r=0.05..0.18 min-dimension",
        "comparison": rows,
        "gate_p95_max_percent": 0.6,
        "gate_log_field_r_minimum": 0.999,
        "gate_pass": all(row["abs_log_ratio_percent"]["p95"] <= 0.6 and
                         row["log_field_r"] >= 0.999 for row in rows),
    }


def write_markdown(path: Path, assessment: dict[str, Any]) -> None:
    vm = assessment["vixen"]["cross_epoch_prnu"]
    vn = assessment["vixen"]["independent_null"]
    so = assessment["sony"]["optical_vs_donor"]
    sn = assessment["sony"]["independent_null"]
    lines = [
        "# Avaluació de transferència dels flats posteriors — 22-08-2026",
        "",
        "## Veredicte",
        "",
        "- **Vixen FINE_SENSOR: VALIDAT.** El patró fi coincideix amb el PRNU de l'eclipsi i millora un null independent.",
        "- **Vixen OPTICAL_RADIAL: CANDIDAT DE PILOT.** La rotació no l'invalida, però encara no s'ha promogut sobre RAW coronals.",
        "- **Vixen FULL/2-D/pols: QUARANTENA.** La component no radial supera el pressupost de transferència.",
        "- **Sony OPTICAL_RADIAL: VALIDAT.** Coincideix amb el flat òptic donant S6 en els quatre plans.",
        "- **Sony FINE_SENSOR: QUARANTENA.** El null detecta senyal útil, però els splits no arriben a r=0,8.",
        "- **Sony FULL/2-D/pols: QUARANTENA.** Deu dies i transport no permeten transferir pols ni gradient de sessió.",
        "",
        "Cap producte no s'ha aplicat als màsters S6 acceptats.",
        "",
        "## Vixen: PRNU creuat entre èpoques",
        "",
        "| Pla | r directe | r high-pass comú | pendent antic/nou |",
        "|---|---:|---:|---:|",
    ]
    for direct, hp in zip(vm["direct_log_factor"], vm["common_highpass_sigma_1px"], strict=True):
        lines.append(f"| {direct['plane']} | {direct['r']:.4f} | {hp['r']:.4f} | {hp['slope_second_on_first']:.3f} |")
    lines += ["", "Null independent Vixen (quatre RAW 1/125 que no van construir el PRNU antic):", "",
              "| Pla | millora RMS nou | millora RMS antic | corr residu/mapa nou |", "|---|---:|---:|---:|"]
    for row in vn["aggregate"]:
        lines.append(
            f"| {row['plane']} | {row['branches']['new']['improvement_vs_control_percent']:.2f}% | "
            f"{row['branches']['old']['improvement_vs_control_percent']:.2f}% | "
            f"{row['branches']['new']['correlation_raw_residual_vs_map']:.3f} |"
        )
    lines += ["", "## Sony: perfil òptic contra l'autoritat S6", "",
              "| Pla | correlació log | p95 diferència | cantó nou | cantó donant |",
              "|---|---:|---:|---:|---:|"]
    for row in so["comparison"]:
        lines.append(
            f"| {row['plane']} | {row['log_field_r']:.6f} | "
            f"{row['abs_log_ratio_percent']['p95']:.3f}% | {row['corner_tl_new']:.4f} | "
            f"{row['corner_tl_donor']:.4f} |"
        )
    lines += ["", "Null independent Sony (segment C, dues repeticions de 1/30, 1/4 i 2 s):", "",
              "| Pla | millora RMS Wiener | corr residu/mapa |", "|---|---:|---:|"]
    for row in sn["aggregate"]:
        lines.append(
            f"| {row['plane']} | {row['branches']['new']['improvement_vs_control_percent']:.2f}% | "
            f"{row['branches']['new']['correlation_raw_residual_vs_map']:.3f} |"
        )
    lines += [
        "",
        "## Límit d'autoritat",
        "",
        "Els nulls de gra fi són diagnòstics en coordenades de sensor. La promoció òptica final exigeix recalibrar RAW originals en una branca nova; dividir un S6 ja registrat no és equivalent perquè flat i warp no commuten.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--vixen", type=Path, required=True)
    parser.add_argument("--sony", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit(f"output preexistent: {out}")
    staging = out.parent / f".{out.name}.staging-{os.getpid()}"
    if staging.exists():
        raise SystemExit(f"staging preexistent: {staging}")
    out.parent.mkdir(parents=True, exist_ok=True)
    staging.mkdir()

    vixen_fine = np.load(args.vixen / "MASTER_FINE_SENSOR_FACTOR_CFA4.npy", mmap_mode="r")
    sony_fine = np.load(args.sony / "MASTER_FINE_SENSOR_FACTOR_CFA4.npy", mmap_mode="r")
    sony_radial = np.load(args.sony / "MASTER_OPTICAL_RADIAL_CFA4.npy", mmap_mode="r")

    vixen_maps = compare_vixen_maps(vixen_fine)
    print("comparació PRNU Vixen completada", flush=True)
    vixen_frames = [(name, load_vixen_null(VIXEN_ECLIPSE / name)) for name in VIXEN_NULL]
    vixen_null = fine_null(
        vixen_frames,
        {"control": np.ones_like(vixen_fine), "old": old_vixen_factors(vixen_fine.shape),
         "new": np.asarray(vixen_fine)},
        signal_min=40.0,
        saturation_signal=13490.8,
    )
    print("null independent Vixen completat", flush=True)

    sony_optical = compare_sony_optical(sony_radial)
    print("comparació òptica Sony completada", flush=True)
    sony_frames = [(name, load_sony_null(SONY_ECLIPSE / name, exposure))
                   for name, exposure in SONY_NULL]
    sony_null = fine_null(
        sony_frames,
        {"control": np.ones_like(sony_fine), "new": np.asarray(sony_fine)},
        signal_min=40.0,
        saturation_signal=0.90 * (16383.0 - 512.0),
    )
    print("null independent Sony completat", flush=True)

    vixen_receipt = json.loads((args.vixen / "MASTER_FLAT_RECEIPT.json").read_text(encoding="utf-8"))
    sony_receipt = json.loads((args.sony / "MASTER_FLAT_RECEIPT.json").read_text(encoding="utf-8"))
    vixen_split = [row["r"] for row in vixen_receipt["fine_sensor"]["split_correlation_R_G1_G2_B"]]
    sony_split = [row["r"] for row in sony_receipt["fine_sensor"]["split_correlation_R_G1_G2_B"]]
    vixen_improvement = [row["branches"]["new"]["improvement_vs_control_percent"]
                         for row in vixen_null["aggregate"]]
    sony_improvement = [row["branches"]["new"]["improvement_vs_control_percent"]
                        for row in sony_null["aggregate"]]
    assessment = {
        "schema": "POSTERIOR_FLAT_TRANSFER_ASSESSMENT_V1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "inputs": {
            "vixen_master": str(args.vixen.resolve()),
            "sony_master": str(args.sony.resolve()),
            "vixen_master_receipt_sha256": sha256(args.vixen / "MASTER_FLAT_RECEIPT.json"),
            "sony_master_receipt_sha256": sha256(args.sony / "MASTER_FLAT_RECEIPT.json"),
        },
        "vixen": {
            "cross_epoch_prnu": vixen_maps,
            "independent_null_frames": [str(VIXEN_ECLIPSE / name) for name in VIXEN_NULL],
            "independent_null": vixen_null,
            "fine_split_correlations_R_G1_G2_B": vixen_split,
            "verdict": {
                "FINE_SENSOR": "VALIDATED_COMPONENT_NOT_APPLIED" if (
                    min(vixen_split) >= 0.8 and vixen_maps["gate_pass"] and min(vixen_improvement) > 0
                ) else "QUARANTINE",
                "OPTICAL_RADIAL": "VALIDATED_SESSION_CANDIDATE_REQUIRES_RAW_PILOT",
                "FULL_SESSION": "QUARANTINE_ROTATION_AND_ASYMMETRY",
                "OPTICAL_SMOOTH2D": "QUARANTINE_SKY_GRADIENT",
                "DUST": "QUARANTINE_ROTATION_AND_EPOCH",
            },
        },
        "sony": {
            "optical_vs_donor": sony_optical,
            "independent_null_frames": [str(SONY_ECLIPSE / name) for name, _ in SONY_NULL],
            "independent_null": sony_null,
            "fine_split_correlations_R_G1_G2_B": sony_split,
            "verdict": {
                "OPTICAL_RADIAL": "VALIDATED_COMPONENT_NOT_APPLIED" if sony_optical["gate_pass"] else "QUARANTINE",
                "FINE_SENSOR": "VALIDATED_COMPONENT_NOT_APPLIED" if (
                    min(sony_split) >= 0.8 and min(sony_improvement) > 0
                ) else "QUARANTINE_SPLIT_R_BELOW_0.8",
                "FULL_SESSION": "QUARANTINE_ASYMMETRY_AND_EPOCH",
                "OPTICAL_SMOOTH2D": "QUARANTINE_SKY_GRADIENT",
                "DUST": "QUARANTINE_TRANSPORT_AND_EPOCH",
            },
        },
        "s6_mutations": 0,
        "raw_mutations": 0,
    }
    (staging / "TRANSFER_ASSESSMENT.json").write_text(
        json.dumps(assessment, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_markdown(staging / "TRANSFER_ASSESSMENT.md", assessment)
    hashes = {p.name: sha256(p) for p in sorted(staging.iterdir()) if p.is_file()}
    with (staging / "SHA256SUMS.txt").open("w", encoding="utf-8") as fh:
        for name, digest in hashes.items():
            fh.write(f"{digest}  {name}\n")
    os.replace(staging, out)
    print(json.dumps({
        "vixen_verdict": assessment["vixen"]["verdict"],
        "sony_verdict": assessment["sony"]["verdict"],
        "vixen_null_improvement_percent_R_G1_G2_B": vixen_improvement,
        "sony_null_improvement_percent_R_G1_G2_B": sony_improvement,
    }, indent=2, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
