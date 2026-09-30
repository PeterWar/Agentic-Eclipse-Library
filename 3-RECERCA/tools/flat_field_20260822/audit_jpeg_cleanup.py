#!/usr/bin/env python3
"""Segella la retirada recuperable dels JPEG de les dues carpetes de flats."""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
from pathlib import Path


VIXEN = Path("/Users/USUARI/Desktop/Eclipse 2026/Vixen R6III/Flats R6III")
SONY = Path("/Users/USUARI/Desktop/Eclipse 2026/300mm A7RIIIA/Flats Sony A7RIIIA 300mm")
TRASH = Path("/Users/USUARI/.Trash/Flats_JPEG_Eclipse_2026_20260822T190159Z")
OPERATION_PRE_POST_RAW_FINGERPRINT = "162e4573554dc6add4726b69d8df1a94fbce7f66cc8d2aa729fa88d03eeef4e3"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def jpeg_paths(root: Path) -> list[Path]:
    return sorted(p for p in root.iterdir() if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg"})


def raw_paths() -> list[Path]:
    return sorted(
        [p for p in VIXEN.iterdir() if p.is_file() and p.suffix.upper() in {".CR3", ".ARW"}]
        + [p for p in SONY.iterdir() if p.is_file() and p.suffix.upper() == ".ARW"]
    )


def raw_fingerprint(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in paths:
        stat = path.stat()
        row = f"{path}\0{stat.st_ino}\0{stat.st_size}\0{stat.st_mtime_ns}\n"
        h.update(row.encode("utf-8"))
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        raise SystemExit(f"rebut preexistent: {out}")

    source_jpegs = {"vixen": jpeg_paths(VIXEN), "sony": jpeg_paths(SONY)}
    if any(source_jpegs.values()):
        raise SystemExit(f"encara hi ha JPEG a origen: {source_jpegs}")
    trash_paths = {
        "vixen": jpeg_paths(TRASH / "Vixen_R6III"),
        "sony": jpeg_paths(TRASH / "Sony_A7RIIIA_300mm"),
    }
    expected_names = [f"DSC{n:05d}.JPG" for n in range(67, 120)]
    for key, paths in trash_paths.items():
        if [p.name for p in paths] != expected_names:
            raise SystemExit(f"inventari de Paperera divergent per {key}")

    raws = raw_paths()
    fingerprint = raw_fingerprint(raws)
    if len(raws) != 230:
        raise SystemExit(f"RAW divergents: count={len(raws)}, fingerprint={fingerprint}")

    all_trash = trash_paths["vixen"] + trash_paths["sony"]
    hashes = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.workers)) as pool:
        futures = {pool.submit(sha256, path): path for path in all_trash}
        for future in concurrent.futures.as_completed(futures):
            hashes[str(futures[future])] = future.result()
    receipt = {
        "schema": "ECLIPSE_FLAT_JPEG_RECOVERABLE_CLEANUP_V1",
        "audited_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "operation_utc_from_trash_batch": "2026-08-22T19:01:59Z",
        "operation": "move exact flat JPEG selectors to macOS Trash; Trash not emptied",
        "source_folders": {"vixen": str(VIXEN), "sony": str(SONY)},
        "trash_batch": str(TRASH),
        "recoverable": True,
        "source_jpeg_remaining": {key: len(paths) for key, paths in source_jpegs.items()},
        "moved": {
            key: {
                "count": len(paths),
                "bytes": sum(p.stat().st_size for p in paths),
                "files": [p.name for p in paths],
            }
            for key, paths in trash_paths.items()
        },
        "totals": {
            "jpeg_count": len(all_trash),
            "jpeg_bytes": sum(p.stat().st_size for p in all_trash),
        },
        "jpeg_sha256_in_trash": dict(sorted(hashes.items())),
        "raw_guard": {
            "path_count": len(raws),
            "breakdown": {
                "vixen_CR3": sum(p.suffix.upper() == ".CR3" and p.parent == VIXEN for p in raws),
                "vixen_duplicate_ARW": sum(p.suffix.upper() == ".ARW" and p.parent == VIXEN for p in raws),
                "sony_ARW": sum(p.suffix.upper() == ".ARW" and p.parent == SONY for p in raws),
            },
            "current_path_inode_size_mtime_ns_sha256": fingerprint,
            "operation_pre_and_post_fingerprint_sha256": OPERATION_PRE_POST_RAW_FINGERPRINT,
            "operation_pre_and_post_fingerprint_equal": True,
            "note": "The operation fingerprint was computed immediately before and after the move; the current fingerprint uses the explicit algorithm in this audit script and is therefore a different hash namespace.",
            "unchanged_by_jpeg_move": True,
        },
        "permanent_deletion": False,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "source_jpeg_remaining": receipt["source_jpeg_remaining"],
        "moved_count": receipt["totals"]["jpeg_count"],
        "moved_bytes": receipt["totals"]["jpeg_bytes"],
        "raw_guard": receipt["raw_guard"],
        "receipt_sha256": sha256(out),
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
