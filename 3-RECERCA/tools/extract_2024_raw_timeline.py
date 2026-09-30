#!/usr/bin/env python3
"""Extracció forense offline de la seqüència RAW curta de l'eclipsi de 2024.

El programa només llegeix els originals de Dropbox. Escriu CSV reproduïbles
dins ``research/data`` i no copia ni modifica cap RAW.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import pathlib
import re
import statistics
import sys
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Sequence


PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_RAW_ROOT = pathlib.Path(
    "/Users/USUARI/Dropbox/Astrofotografia/"
    "Eclipse Solar 2024/Eclipse (short)"
)
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "research" / "data"
RAW_SUFFIXES = {".arw", ".cr2"}
A7S_SCHEDULED_C2 = datetime(2024, 4, 8, 11, 8, 49)
A7S_SCHEDULED_C3 = datetime(2024, 4, 8, 11, 13, 17)


def load_tiff_module() -> Any:
    module_path = PROJECT_ROOT / "controller" / "tools" / "inspect_arw.py"
    spec = importlib.util.spec_from_file_location("eclipse_inspect_arw", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("No es pot carregar {}".format(module_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


TIFF = load_tiff_module()


def scalar(ifds: Iterable[Any], tag: int) -> Any:
    value = TIFF.first_tag(ifds, tag)
    if isinstance(value, tuple) and len(value) == 1:
        return value[0]
    return value


def rational(ifds: Iterable[Any], tag: int) -> Optional[float]:
    return TIFF.rational_number(TIFF.first_tag(ifds, tag))


def sequence_number(path: pathlib.Path) -> Optional[int]:
    patterns = (
        r"^DSC0?(\d+)$",
        r"^_MG_(\d+)$",
    )
    for pattern in patterns:
        match = re.match(pattern, path.stem, flags=re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def controller_filename_datetime(path: pathlib.Path) -> Optional[datetime]:
    match = re.match(r"^(\d{8})_(\d{6})total$", path.stem, flags=re.IGNORECASE)
    if not match:
        return None
    return datetime.strptime("".join(match.groups()), "%Y%m%d%H%M%S")


def parse_exif_datetime(value: Any, subsec: Any) -> Optional[datetime]:
    if not isinstance(value, str):
        return None
    try:
        result = datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
    except ValueError:
        return None
    if isinstance(subsec, str) and subsec.strip().isdigit():
        digits = subsec.strip()[:6].ljust(6, "0")
        result = result.replace(microsecond=int(digits))
    return result


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(8 * 1024 * 1024)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def fmt_dt(value: Optional[datetime]) -> str:
    if value is None:
        return ""
    if value.microsecond:
        return value.strftime("%Y-%m-%dT%H:%M:%S.%f").rstrip("0")
    return value.strftime("%Y-%m-%dT%H:%M:%S")


def fmt_exposure(seconds: Optional[float]) -> str:
    return TIFF.format_exposure(seconds) or ""


def inspect(path: pathlib.Path, include_hash: bool) -> Dict[str, Any]:
    stat = path.stat()
    with TIFF.TiffReader(path) as reader:
        ifds = reader.walk()
        raw_ifd = TIFF.choose_raw_ifd(ifds)
        dt_original_text = scalar(ifds, 0x9003)
        subsec_original = scalar(ifds, 0x9291)
        dt_original = parse_exif_datetime(dt_original_text, subsec_original)
        controller_dt = controller_filename_datetime(path)
        analysis_dt = controller_dt or dt_original
        exposure_s = rational(ifds, 0x829A)
        row: Dict[str, Any] = {
            "system": path.parent.name,
            "filename": path.name,
            "extension": path.suffix.upper(),
            "sequence_number": sequence_number(path),
            "bytes": stat.st_size,
            "sha256": sha256(path) if include_hash else "",
            "make": scalar(ifds, 0x010F) or "",
            "model": scalar(ifds, 0x0110) or "",
            "body_serial": scalar(ifds, 0xA431) or "",
            "datetime_original_text": dt_original_text or "",
            "subsec_original": subsec_original or "",
            "offset_time_original": scalar(ifds, 0x9011) or "",
            "datetime_original": fmt_dt(dt_original),
            "controller_filename_time": fmt_dt(controller_dt),
            "analysis_time_source": (
                "controller_filename_request"
                if controller_dt is not None
                else "EXIF_DateTimeOriginal"
            ),
            "analysis_time": fmt_dt(analysis_dt),
            "seconds_from_scheduled_C2": (
                (analysis_dt - A7S_SCHEDULED_C2).total_seconds()
                if controller_dt is not None and analysis_dt is not None
                else ""
            ),
            "seconds_from_scheduled_C3": (
                (analysis_dt - A7S_SCHEDULED_C3).total_seconds()
                if controller_dt is not None and analysis_dt is not None
                else ""
            ),
            "scheduled_phase": (
                "pre_C2"
                if controller_dt is not None
                and analysis_dt is not None
                and analysis_dt < A7S_SCHEDULED_C2
                else (
                    "totality"
                    if controller_dt is not None
                    and analysis_dt is not None
                    and analysis_dt < A7S_SCHEDULED_C3
                    else ("post_C3" if controller_dt is not None else "")
                )
            ),
            "mtime": datetime.fromtimestamp(stat.st_mtime).astimezone().isoformat(),
            "exposure_seconds": exposure_s,
            "exposure": fmt_exposure(exposure_s),
            "iso": scalar(ifds, 0x8827) or "",
            "f_number": rational(ifds, 0x829D),
            "focal_length_mm": rational(ifds, 0x920A),
            "exposure_bias_ev": rational(ifds, 0x9204),
            "raw_width": raw_ifd.scalar(0x0100) if raw_ifd else "",
            "raw_height": raw_ifd.scalar(0x0101) if raw_ifd else "",
            "raw_bits_per_sample": raw_ifd.scalar(0x0102) if raw_ifd else "",
            "raw_compression": raw_ifd.scalar(0x0103) if raw_ifd else "",
            "_analysis_dt": analysis_dt,
            "_exif_dt": dt_original,
        }
    return row


def percentile(values: Sequence[float], fraction: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def missing_sequence_numbers(rows: Sequence[Dict[str, Any]]) -> List[int]:
    values = [
        int(row["sequence_number"])
        for row in rows
        if isinstance(row["sequence_number"], int)
    ]
    if len(values) != len(rows) or not values:
        return []
    present = set(values)
    return [value for value in range(min(values), max(values) + 1) if value not in present]


def consecutive_runs(rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    runs: List[Dict[str, Any]] = []
    current: List[Dict[str, Any]] = []
    for row in rows:
        if (
            current
            and (
                row["exposure_seconds"] != current[-1]["exposure_seconds"]
                or row["iso"] != current[-1]["iso"]
            )
        ):
            runs.append(summarize_run(len(runs) + 1, current))
            current = []
        current.append(row)
    if current:
        runs.append(summarize_run(len(runs) + 1, current))
    return runs


def summarize_run(index: int, rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    start = rows[0]["_analysis_dt"]
    end = rows[-1]["_analysis_dt"]
    return {
        "system": rows[0]["system"],
        "run_index": index,
        "first_filename": rows[0]["filename"],
        "last_filename": rows[-1]["filename"],
        "start_time": fmt_dt(start),
        "end_time": fmt_dt(end),
        "count": len(rows),
        "span_seconds": (end - start).total_seconds() if start and end else "",
        "exposure_seconds": rows[0]["exposure_seconds"],
        "exposure": rows[0]["exposure"],
        "iso": rows[0]["iso"],
    }


def clean_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in row.items() if not key.startswith("_")}


def write_csv(path: pathlib.Path, rows: Sequence[Dict[str, Any]]) -> None:
    if not rows:
        raise RuntimeError("No hi ha files per escriure a {}".format(path))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_summary(system_rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    ordered = sorted(
        system_rows,
        key=lambda row: (
            row["_analysis_dt"] or datetime.min,
            row["sequence_number"] if row["sequence_number"] is not None else -1,
            row["filename"],
        ),
    )
    times = [row["_analysis_dt"] for row in ordered]
    deltas = [
        (right - left).total_seconds()
        for left, right in zip(times, times[1:])
        if left is not None and right is not None
    ]
    missing = missing_sequence_numbers(ordered)
    hashes = [row["sha256"] for row in ordered if row["sha256"]]
    duplicate_hashes = len(hashes) - len(set(hashes))
    exposure_values = sorted(
        {float(row["exposure_seconds"]) for row in ordered if row["exposure_seconds"]}
    )
    iso_values = sorted({str(row["iso"]) for row in ordered})
    return {
        "system": ordered[0]["system"],
        "make": ordered[0]["make"],
        "model": ordered[0]["model"],
        "body_serial": ordered[0]["body_serial"],
        "raw_count": len(ordered),
        "first_filename": ordered[0]["filename"],
        "last_filename": ordered[-1]["filename"],
        "first_analysis_time": fmt_dt(times[0]),
        "last_analysis_time": fmt_dt(times[-1]),
        "span_seconds": (times[-1] - times[0]).total_seconds(),
        "cadence_min_s": min(deltas) if deltas else "",
        "cadence_median_s": statistics.median(deltas) if deltas else "",
        "cadence_p90_s": percentile(deltas, 0.90) or "",
        "cadence_p95_s": percentile(deltas, 0.95) or "",
        "cadence_max_s": max(deltas) if deltas else "",
        "gaps_gt_10_s": sum(delta > 10 for delta in deltas),
        "gaps_gt_30_s": sum(delta > 30 for delta in deltas),
        "sequence_missing_count": len(missing),
        "sequence_missing_numbers": " ".join(map(str, missing)),
        "bit_identical_duplicate_count": duplicate_hashes,
        "iso_values": " ".join(iso_values),
        "exposure_values_seconds": " ".join("{:.10g}".format(v) for v in exposure_values),
        "total_bytes": sum(int(row["bytes"]) for row in ordered),
        "time_source": ordered[0]["analysis_time_source"],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-root", type=pathlib.Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--output-dir", type=pathlib.Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--skip-hash",
        action="store_true",
        help="No calcula SHA-256 complet (més ràpid, no detecta duplicats exactes)",
    )
    args = parser.parse_args(argv)

    raw_root = args.raw_root.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not raw_root.is_dir():
        raise SystemExit("No existeix el directori RAW: {}".format(raw_root))
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(
        (
            path
            for path in raw_root.rglob("*")
            if path.is_file() and path.suffix.lower() in RAW_SUFFIXES
        ),
        key=lambda path: (path.parent.name, sequence_number(path) or -1, path.name),
    )
    rows = [inspect(path, not args.skip_hash) for path in files]
    systems = sorted({row["system"] for row in rows})

    ordered_rows: List[Dict[str, Any]] = []
    runs: List[Dict[str, Any]] = []
    summaries: List[Dict[str, Any]] = []
    for system in systems:
        system_rows = [row for row in rows if row["system"] == system]
        system_rows.sort(
            key=lambda row: (
                row["_analysis_dt"] or datetime.min,
                row["sequence_number"] if row["sequence_number"] is not None else -1,
                row["filename"],
            )
        )
        for index, row in enumerate(system_rows):
            previous = system_rows[index - 1] if index else None
            row["delta_previous_seconds"] = (
                (row["_analysis_dt"] - previous["_analysis_dt"]).total_seconds()
                if previous
                and row["_analysis_dt"] is not None
                and previous["_analysis_dt"] is not None
                else ""
            )
            if (
                row["controller_filename_time"]
                and row["_exif_dt"] is not None
                and row["_analysis_dt"] is not None
            ):
                row["camera_clock_minus_controller_seconds"] = (
                    row["_exif_dt"] - row["_analysis_dt"]
                ).total_seconds()
            else:
                row["camera_clock_minus_controller_seconds"] = ""
            row["sequence_increment"] = (
                int(row["sequence_number"]) - int(previous["sequence_number"])
                if previous
                and isinstance(row["sequence_number"], int)
                and isinstance(previous["sequence_number"], int)
                else ""
            )
            ordered_rows.append(clean_row(row))
        runs.extend(consecutive_runs(system_rows))
        summaries.append(build_summary(system_rows))

    write_csv(output_dir / "2024_raw_timeline.csv", ordered_rows)
    write_csv(output_dir / "2024_exposure_runs.csv", runs)
    write_csv(output_dir / "2024_raw_summary.csv", summaries)
    manifest = {
        "source": str(raw_root),
        "raw_count": len(rows),
        "systems": systems,
        "hashes_included": not args.skip_hash,
        "outputs": [
            "2024_raw_timeline.csv",
            "2024_exposure_runs.csv",
            "2024_raw_summary.csv",
        ],
    }
    (output_dir / "2024_raw_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
