#!/usr/bin/env python3
"""S0 read-only inventory for the Vixen/R6 and Sony/A7RIIIA eclipse trains.

The source trees are never modified.  The script writes only JSON/CSV receipts
below the explicit output directory.  It inventories the complete 273-frame
Vixen sequence (247 files in the project data tree plus the 26-file spill in
Downloads), verifies the 124-file ``Vixen Unfiltered`` selection against that
union, and inventories the complete Sony 300 mm tree.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
import os
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


VIXEN_ALL = Path("/Users/USUARI/Desktop/Eclipse 2026/Vixen R6III")
VIXEN_SPILL = Path("/Users/USUARI/Downloads")
VIXEN_UNFILTERED = Path("/Users/USUARI/Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat")
SONY_ALL = Path("/Users/USUARI/Desktop/Eclipse 2026/300mm A7RIIIA")

# Actual contact geometry used by the validated Vixen pipeline.  Sony EXIF is
# only second-resolved and records exposure end, so its relative times remain
# labelled as an inventory aid rather than a registration authority.
C2_LOCAL = dt.datetime(2026, 8, 12, 20, 28, 45, tzinfo=dt.timezone(dt.timedelta(hours=2)))
TOTALITY_S = 103.7

EXIF_TAGS = [
    "FileName", "SubSecDateTimeOriginal", "DateTimeOriginal", "ExposureTime",
    "ISO", "CameraTemperature", "BatteryTemperature", "Model", "LensModel",
    "FNumber", "ShutterType", "DriveMode", "Quality", "BitsPerSample",
    "RawJpgSize", "ImageWidth", "ImageHeight",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def parse_time(value: object) -> dt.datetime | None:
    if not isinstance(value, str) or not value or value == "-":
        return None
    s = value.strip()
    # ExifTool: YYYY:MM:DD HH:MM:SS[.ff][+HH:MM]
    s = s[:4] + "-" + s[5:7] + "-" + s[8:]
    try:
        parsed = dt.datetime.fromisoformat(s)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=C2_LOCAL.tzinfo)
    return parsed


def exif_rows(files: list[Path]) -> dict[str, dict]:
    cmd = ["exiftool", "-q", "-n", "-j"]
    cmd.extend(f"-{tag}" for tag in EXIF_TAGS)
    cmd.extend(str(p) for p in files)
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    rows = json.loads(result.stdout)
    return {Path(row["SourceFile"]).name: row for row in rows}


def classify(train: str, name: str, timestamp: dt.datetime | None,
             exposure_s: float, in_unfiltered: bool | None) -> tuple[str, float | None]:
    if timestamp is None:
        return "TIME_UNKNOWN", None
    midpoint = timestamp + dt.timedelta(seconds=exposure_s / 2) if train == "VIXEN_R6" \
        else timestamp - dt.timedelta(seconds=exposure_s / 2)
    rel = (midpoint - C2_LOCAL).total_seconds()
    if train == "VIXEN_R6":
        if not in_unfiltered:
            return "FILTERED_PARTIAL_OR_OTHER", rel
        if 0.0 <= rel <= TOTALITY_S:
            return "CORONA_TOTALITY", rel
        return "UNFILTERED_CONTACT_OR_TRANSITION", rel
    if -6.0 <= rel <= TOTALITY_S + 6.0:
        return "TOTALITY_OR_CONTACT_CANDIDATE", rel
    return "PARTIAL_OR_MANUAL_OTHER", rel


def collect_paths(train: str, files: list[Path], hashes: dict[Path, str],
                  unfiltered_names: set[str]) -> list[dict]:
    meta = exif_rows(files)
    out: list[dict] = []
    for p in files:
        m = meta.get(p.name, {})
        exp = float(m.get("ExposureTime", 0.0) or 0.0)
        ts_raw = m.get("SubSecDateTimeOriginal") or m.get("DateTimeOriginal")
        timestamp = parse_time(ts_raw)
        in_unfiltered = p.name in unfiltered_names if train == "VIXEN_R6" else None
        phase, rel = classify(train, p.name, timestamp, exp, in_unfiltered)
        row = {
            "train": train,
            "path": str(p),
            "name": p.name,
            "size": p.stat().st_size,
            "sha256": hashes[p],
            "camera": m.get("Model"),
            "lens": m.get("LensModel"),
            "timestamp_exif": ts_raw,
            "exposure_s": exp,
            "iso": m.get("ISO"),
            "camera_temperature": m.get("CameraTemperature"),
            "battery_temperature": m.get("BatteryTemperature"),
            "f_number": m.get("FNumber"),
            "shutter_type": m.get("ShutterType"),
            "drive_mode": m.get("DriveMode"),
            "quality": m.get("Quality"),
            "bits_per_sample": m.get("BitsPerSample"),
            "raw_jpg_size": m.get("RawJpgSize"),
            "image_width": m.get("ImageWidth"),
            "image_height": m.get("ImageHeight"),
            "in_vixen_unfiltered_selection": in_unfiltered,
            "midpoint_rel_c2_s_inventory": rel,
            "phase_inventory": phase,
            "mount": "iOptron" if train == "VIXEN_R6" else "Skywatcher",
            "frame_authority": "INVENTORY_ONLY; final solar/lunar/stellar registration is separate",
        }
        out.append(row)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    if args.out.exists() and any(args.out.iterdir()):
        raise SystemExit(f"output directory is not empty: {args.out}")
    args.out.mkdir(parents=True, exist_ok=True)

    vixen_tree = sorted(p for p in VIXEN_ALL.glob("*.CR3") if p.is_file() and not p.is_symlink())
    vixen_names = {p.name for p in vixen_tree}
    vixen_spill = sorted(
        p for p in VIXEN_SPILL.glob("572A????.CR3")
        if p.is_file() and not p.is_symlink()
        and "572A2905.CR3" <= p.name <= "572A3177.CR3"
        and p.name not in vixen_names
    )
    vixen = sorted(vixen_tree + vixen_spill, key=lambda p: p.name)
    vixen_u = sorted(p for p in VIXEN_UNFILTERED.glob("*.CR3") if p.is_file() and not p.is_symlink())
    sony = sorted(p for p in SONY_ALL.glob("*.ARW") if p.is_file() and not p.is_symlink())
    all_paths = vixen + vixen_u + sony
    print(f"hashing {len(all_paths)} source files ({len(vixen)} Vixen "
          f"[{len(vixen_tree)} tree + {len(vixen_spill)} spill] + "
          f"{len(vixen_u)} Vixen selection copies + {len(sony)} Sony)", flush=True)
    hashes: dict[Path, str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(sha256, p): p for p in all_paths}
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            p = futures[future]
            hashes[p] = future.result()
            if index % 25 == 0 or index == len(futures):
                print(f"  {index}/{len(futures)}", flush=True)

    unfiltered_names = {p.name for p in vixen_u}
    rows = collect_paths("VIXEN_R6", vixen, hashes, unfiltered_names)
    rows += collect_paths("SONY_300MM", sony, hashes, unfiltered_names)

    copy_check = []
    canonical = {p.name: p for p in vixen}
    for copy in vixen_u:
        src = canonical.get(copy.name)
        copy_check.append({
            "name": copy.name,
            "canonical_path": str(src) if src else None,
            "selection_copy_path": str(copy),
            "size_match": bool(src and src.stat().st_size == copy.stat().st_size),
            "sha256_canonical": hashes.get(src) if src else None,
            "sha256_selection_copy": hashes[copy],
            "sha256_match": bool(src and hashes[src] == hashes[copy]),
        })

    with (args.out / "inventory.jsonl").open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with (args.out / "vixen_unfiltered_copy_check.jsonl").open("w", encoding="utf-8") as fh:
        for row in copy_check:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    duplicate_groups: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        duplicate_groups[row["sha256"]].append(row["path"])
    duplicates = {h: paths for h, paths in duplicate_groups.items() if len(paths) > 1}

    group_rows = []
    grouped = Counter((r["train"], r["phase_inventory"], r["exposure_s"], r["iso"])
                      for r in rows)
    for (train, phase, exposure, iso), count in sorted(grouped.items(), key=lambda x: (x[0][0], x[0][1], x[0][2], str(x[0][3]))):
        group_rows.append({"train": train, "phase": phase, "exposure_s": exposure,
                           "iso": iso, "count": count})
    with (args.out / "groups.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["train", "phase", "exposure_s", "iso", "count"])
        writer.writeheader()
        writer.writerows(group_rows)

    summary = {
        "schema": "STACK_S0_INVENTORY_V1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "sources": {
            "vixen_canonical_tree": str(VIXEN_ALL),
            "vixen_canonical_spill": str(VIXEN_SPILL),
            "vixen_unfiltered_selection": str(VIXEN_UNFILTERED),
            "sony_canonical": str(SONY_ALL),
        },
        "counts": {
            "vixen_canonical_cr3": len(vixen),
            "vixen_canonical_tree_cr3": len(vixen_tree),
            "vixen_canonical_spill_cr3": len(vixen_spill),
            "vixen_unfiltered_selection_cr3": len(vixen_u),
            "sony_arw": len(sony),
            "inventory_rows": len(rows),
        },
        "bytes": {
            "vixen_canonical": sum(p.stat().st_size for p in vixen),
            "vixen_unfiltered_selection_copies": sum(p.stat().st_size for p in vixen_u),
            "sony": sum(p.stat().st_size for p in sony),
        },
        "vixen_unfiltered_copy_matches": sum(r["sha256_match"] for r in copy_check),
        "vixen_unfiltered_copy_mismatches": [r["name"] for r in copy_check if not r["sha256_match"]],
        "byte_duplicate_groups_within_canonical_inventory": duplicates,
        "groups": group_rows,
        "notes": [
            "Vixen/Canon EXIF is interpreted as exposure start; Sony EXIF as exposure end.",
            "Sony second-resolution timestamps are inventory aids only, never registration authority.",
            "Filtered Vixen partials are inventoried but incompatible with the unfiltered totality stack.",
            "The Vixen sequence is the name-unique union 572A2905--572A3177 across the project tree and Downloads spill.",
            "No source file was modified.",
        ],
    }
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary["counts"], ensure_ascii=False), flush=True)
    print(f"copy matches {summary['vixen_unfiltered_copy_matches']}/{len(copy_check)}; "
          f"canonical duplicate groups {len(duplicates)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
