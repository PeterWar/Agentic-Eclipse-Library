#!/usr/bin/env python3
"""Inventaria i retira JPEG del projecte sense tocar TIFF ni RAW.

L'abast és deliberadament fix: el worktree canònic i l'arbre de productes de
l'Escriptori. No segueix symlinks. Identifica JPEG per extensió o signatura
SOI, després d'excloure explícitament TIFF i RAW. En mode ``--move`` conserva
cada JPEG en un lot únic de la Paperera, mantenint l'arbre relatiu i un
manifest SHA-256.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Iterable


ROOTS = (
    ("worktree", Path("/Users/USUARI/Downloads/Eclipse 2026")),
    ("products", Path("/Users/USUARI/Desktop/Eclipse 2026")),
)
JPEG_EXTENSIONS = {".jpg", ".jpeg"}
TIFF_EXTENSIONS = {".tif", ".tiff"}
RAW_EXTENSIONS = {".arw", ".cr2", ".cr3"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def has_jpeg_signature(path: Path) -> bool:
    """Detecta un JPEG encara que l'extensió sigui incorrecta o absent."""
    try:
        with path.open("rb") as handle:
            return handle.read(3) == b"\xff\xd8\xff"
    except OSError as error:
        raise SystemExit(f"No es pot llegir la signatura de {path}: {error}") from error


def iter_regular_files(root: Path) -> Iterable[Path]:
    """Recorre ``root`` sense seguir enllaços ni entrar a ``.git``."""
    for current, directories, filenames in os.walk(root, followlinks=False):
        directories[:] = sorted(
            name
            for name in directories
            if name != ".git" and not (Path(current) / name).is_symlink()
        )
        for filename in sorted(filenames):
            path = Path(current) / filename
            try:
                mode = path.stat(follow_symlinks=False).st_mode
            except FileNotFoundError:
                raise SystemExit(f"Fitxer desaparegut durant l'inventari: {path}")
            if stat.S_ISREG(mode):
                yield path


def fingerprint(records: list[dict[str, object]]) -> str:
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: (str(item["root"]), str(item["relative"]))):
        line = (
            f'{record["root"]}/{record["relative"]}\t'
            f'{record["inode"]}\t{record["size"]}\n'
        )
        digest.update(line.encode("utf-8", "surrogateescape"))
    return digest.hexdigest()


def inventory(hash_jpeg: bool) -> dict[str, object]:
    by_class: dict[str, list[dict[str, object]]] = {
        "jpeg": [],
        "tiff": [],
        "raw": [],
    }
    for root_id, root in ROOTS:
        if not root.is_dir():
            raise SystemExit(f"Arrel absent: {root}")
        for path in iter_regular_files(root):
            extension = path.suffix.lower()
            if extension in TIFF_EXTENSIONS:
                media_class = "tiff"
            elif extension in RAW_EXTENSIONS:
                media_class = "raw"
            elif extension in JPEG_EXTENSIONS or has_jpeg_signature(path):
                media_class = "jpeg"
            else:
                continue
            metadata = path.stat(follow_symlinks=False)
            record: dict[str, object] = {
                "root": root_id,
                "relative": path.relative_to(root).as_posix(),
                "path": str(path),
                "inode": metadata.st_ino,
                "size": metadata.st_size,
                "mtime_ns": metadata.st_mtime_ns,
            }
            if media_class == "jpeg" and hash_jpeg:
                record["sha256"] = sha256_file(path)
            by_class[media_class].append(record)

    summary: dict[str, object] = {"roots": {key: str(value) for key, value in ROOTS}}
    for media_class, records in by_class.items():
        summary[media_class] = {
            "count": len(records),
            "bytes": sum(int(record["size"]) for record in records),
            "fingerprint_path_inode_size": fingerprint(records),
        }
    summary["records"] = by_class
    return summary


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for record in sorted(records, key=lambda item: (str(item["root"]), str(item["relative"]))):
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def validate_jpeg_snapshot(records: list[dict[str, object]]) -> None:
    """Valida tota la selecció abans de moure el primer byte."""
    for record in records:
        path = Path(str(record["path"]))
        try:
            metadata = path.stat(follow_symlinks=False)
        except FileNotFoundError:
            raise SystemExit(f"JPEG desaparegut abans del moviment: {path}")
        if not stat.S_ISREG(metadata.st_mode):
            raise SystemExit(f"La selecció ja no és un fitxer regular: {path}")
        observed = (metadata.st_ino, metadata.st_size, metadata.st_mtime_ns)
        expected = (record["inode"], record["size"], record["mtime_ns"])
        if observed != expected:
            raise SystemExit(f"JPEG modificat després de l'inventari: {path}")


def move_jpeg(records: list[dict[str, object]], trash_batch: Path) -> None:
    expected_parent = Path("/Users/USUARI/.Trash")
    if trash_batch.parent != expected_parent:
        raise SystemExit(f"El lot ha de ser fill directe de {expected_parent}: {trash_batch}")
    if trash_batch.exists():
        raise SystemExit(f"El lot de destí ja existeix: {trash_batch}")
    validate_jpeg_snapshot(records)
    trash_batch.mkdir(mode=0o700)
    root_map = dict(ROOTS)
    for record in records:
        source = Path(str(record["path"]))
        root_id = str(record["root"])
        relative = Path(str(record["relative"]))
        if source != root_map[root_id] / relative:
            raise SystemExit(f"Ruta fora de l'arrel declarada: {source}")
        destination = trash_batch / root_id / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise SystemExit(f"Col·lisió al lot recuperable: {destination}")
        os.replace(source, destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt-dir", type=Path, required=True)
    parser.add_argument("--move", action="store_true")
    parser.add_argument("--trash-batch", type=Path)
    arguments = parser.parse_args()
    if arguments.move != bool(arguments.trash_batch):
        parser.error("--move i --trash-batch s'han de donar junts")

    arguments.receipt_dir.mkdir(parents=True, exist_ok=False)
    before = inventory(hash_jpeg=True)
    jpeg_records = before["records"]["jpeg"]
    write_jsonl(arguments.receipt_dir / "jpeg_before.jsonl", jpeg_records)
    summary_before = {key: value for key, value in before.items() if key != "records"}
    if arguments.move:
        summary_before["trash_batch"] = str(arguments.trash_batch)
    write_json(arguments.receipt_dir / "summary_before.json", summary_before)

    if not arguments.move:
        print(json.dumps(summary_before, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    move_jpeg(jpeg_records, arguments.trash_batch)
    after = inventory(hash_jpeg=False)
    summary_after = {key: value for key, value in after.items() if key != "records"}
    summary_after["trash_batch"] = str(arguments.trash_batch)
    summary_after["moved_jpeg"] = len(jpeg_records)
    summary_after["moved_bytes"] = sum(int(record["size"]) for record in jpeg_records)
    write_json(arguments.receipt_dir / "summary_after.json", summary_after)
    if int(summary_after["jpeg"]["count"]) != 0:
        raise SystemExit("La verificació posterior encara troba JPEG")
    for media_class in ("tiff", "raw"):
        if summary_before[media_class] != summary_after[media_class]:
            raise SystemExit(f"Fingerprint preservat divergent: {media_class}")
    print(json.dumps(summary_after, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
