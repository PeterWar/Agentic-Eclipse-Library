"""Preflight no-clobber del pilot Vixen LDIC 0 -> 1 -> 2.

La comanda només llegeix actius canònics i escriu un build nou sota `--out`.
No executa la fase 2 mentre F0/F1 no estiguin demostrades.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import platform
import re
import subprocess
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np
import rawpy
from scipy.ndimage import map_coordinates

from contracts import (
    CANVAS_SCALE_ARCSEC_PX,
    CFA4_SHAPE,
    DARK_LEGACY_SHAPE,
    MOSAIC_SHAPE,
    PHYSICAL_LONG_EXPOSURE_S,
    RAW_CROP_Y_X_H_W,
    ContractError,
    common_canvas_from_perimeters,
    frame_order_sha256,
    physical_exposure_s,
    quadratic_axis_plane_degeneracy_error,
    registration_gate,
)


WORKTREE = Path(__file__).resolve().parents[3]
DESKTOP = Path.home() / "Desktop/Eclipse 2026"
RAW_ROOT = DESKTOP / "Vixen R6III/Vixen Fase totalitat"
DARK_ROOT = DESKTOP / "Vixen R6III/Darks Canon R6III Eclipse"
MASTER_DARK_ROOT = RAW_ROOT / "Masters_v2"
FLAT_SOURCE_ROOT = DESKTOP / "Vixen R6III/Flats R6III"
FLAT_ROOT = WORKTREE / "output/flats_20260822/vixen_r6iii_posterior_v1"
MANIFEST = DESKTOP / "Derivats/Vixen/Corona_HDR_Vixen/manifest.csv"
GEOMETRY = DESKTOP / "Derivats/Vixen/Corona_HDR_Vixen/geometria.json"
CORONA_DRIFT = DESKTOP / "Derivats/Vixen/Corona_HDR_Vixen/deriva_corona.json"
PLATE = DESKTOP / "Derivats/Astrometria/Estrelles/Resultats_acceptacio_2026-08-17/final_solution.json"
PLATE_SOURCE = WORKTREE / "research/tools/astrometria/xmatch/final_solve.py"
LEDGER_68 = WORKTREE / "output/postprocessat_final_20260822/masters/vixen_s6_ACCEPTED/LEDGER_68.json"
VIXEN_S6 = WORKTREE / "output/postprocessat_final_20260822/masters/vixen_s6_ACCEPTED"
CLAIM = WORKTREE / ".coordination/claim.lock/owner.json"
S6_SHA256SUMS = VIXEN_S6 / "SHA256SUMS.txt"
FLAT_SHA256SUMS = FLAT_ROOT / "SHA256SUMS.txt"

FROZEN_AUTHORITY_SHA256 = {
    str(MANIFEST): "e15dfc0538cb95af43a60c985c2fce6e6d4fb91f486873aad925eb973455f05c",
    str(PLATE): "249bdfa8d762c155f1b2fbc49ae1dfb71b9a10614f9b760f79e765822e3ed681",
    str(GEOMETRY): "c5e570948734a706066f4f792f0908f87f81ee7bfa27e39e02b35bd54cd392cc",
    str(CORONA_DRIFT): "32765754c83dba18064822e3c35ec3a6500f24c15a76f55b3816d4e6e5917088",
    str(FLAT_SHA256SUMS): "d9b94d157b9a9e7577336ca2dd773d635b01eaf726d03b1d971a85f2bc6633ba",
    str(S6_SHA256SUMS): "b140cc7b4a730c88ddb4ccadd42ebe12b2f26c8d7082525d2d290c7ef9ec5bd6",
}
EXPECTED_MANIFEST_ORDER_SHA256 = "950baed4b306155adc468415f70e680e1fbf607ea8e2a67cdac49a56f76e8530"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_bytes_hashed(path: Path) -> tuple[bytes, dict[str, object]]:
    if not path.is_file() or path.is_symlink():
        raise ContractError(f"font absent o symlink no admès: {path}")
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        payload = handle.read()
        after = os.fstat(handle.fileno())
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or len(payload) != before.st_size
    ):
        raise ContractError(f"font canviada durant la lectura: {path}")
    return payload, {
        "path": str(path),
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def read_frozen_bytes(path: Path) -> tuple[bytes, dict[str, object]]:
    expected = FROZEN_AUTHORITY_SHA256.get(str(path))
    if expected is None:
        raise ContractError(f"font sense anchor congelat: {path}")
    payload, row = read_bytes_hashed(path)
    if row["sha256"] != expected:
        raise ContractError(
            f"anchor divergent per {path}: esperat {expected}, actual {row['sha256']}"
        )
    return payload, {**row, "status": "PASS_FROZEN_SHA256_SAME_BYTES"}


def require_frozen_authority(path: Path) -> dict[str, object]:
    _, row = read_frozen_bytes(path)
    return row


def frozen_sha256sums(root: Path, sums_path: Path) -> dict[str, str]:
    payload, _ = read_frozen_bytes(sums_path)
    entries: dict[str, str] = {}
    for line_number, line in enumerate(
        payload.decode("ascii").splitlines(), start=1
    ):
        if not line:
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-f]{64}", parts[0]):
            raise ContractError(f"SHA256SUMS invàlid a {sums_path}:{line_number}")
        name = parts[1].lstrip("* ")
        relative = Path(name)
        if (
            not name
            or relative.is_absolute()
            or ".." in relative.parts
            or relative.as_posix() != name
            or name in entries
        ):
            raise ContractError(f"ruta insegura/duplicada a {sums_path}:{line_number}")
        entries[name] = parts[0]
    if not entries:
        raise ContractError(f"SHA256SUMS buit: {sums_path}")
    return entries


def read_sums_entry(
    path: Path, root: Path, entries: dict[str, str]
) -> tuple[bytes, dict[str, object]]:
    try:
        relative = path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ContractError(f"font fora de l'arrel d'autoritat: {path}") from exc
    expected = entries.get(relative)
    if expected is None:
        raise ContractError(f"font no llistada a l'anchor: {relative}")
    payload, row = read_bytes_hashed(path)
    if row["sha256"] != expected:
        raise ContractError(f"hash divergent contra l'anchor: {relative}")
    return payload, {**row, "status": "PASS_ROOT_SHA256SUMS_SAME_BYTES"}


def verify_sums_entry(path: Path, root: Path, entries: dict[str, str]) -> dict[str, object]:
    _, row = read_sums_entry(path, root, entries)
    return row


def json_load_bytes(payload: bytes, *, source: Path) -> Any:
    def reject_nonstandard_constant(value: str) -> None:
        raise ValueError(f"constant JSON no estàndard a {source}: {value}")

    return json.loads(payload.decode("utf-8"), parse_constant=reject_nonstandard_constant)


def json_load(path: Path) -> Any:
    payload, _ = read_bytes_hashed(path)
    return json_load_bytes(payload, source=path)


def require_codex_claim() -> dict[str, object]:
    if (
        not CLAIM.parent.is_dir()
        or CLAIM.parent.is_symlink()
        or not CLAIM.is_file()
        or CLAIM.is_symlink()
    ):
        raise ContractError(f"falta SERIAL_WRITES: {CLAIM}")
    payload, claim_row = read_bytes_hashed(CLAIM)
    owner = json_load_bytes(payload, source=CLAIM)
    scope = str(owner.get("scope", ""))
    task = str(owner.get("task", ""))
    required_scope_fragments = (
        "research/tools/pilot_vixen_ldic",
        "output/pilot_vixen_ldic_20260823",
    )
    if (
        owner.get("owner") != "Codex"
        or not owner.get("claim_id")
        or "Pilot Vixen" not in task
        or any(fragment not in scope for fragment in required_scope_fragments)
    ):
        raise ContractError(f"SERIAL_WRITES no pertany a Codex o no cobreix el pilot: {owner}")
    return {
        "path": str(CLAIM),
        "bytes": claim_row["bytes"],
        "sha256": claim_row["sha256"],
        "claim_id": owner["claim_id"],
        "owner": owner["owner"],
        "task": task,
        "scope": scope,
    }


def canonical_output_root() -> Path:
    allowed = WORKTREE / "output/pilot_vixen_ldic_20260823"
    try:
        resolved = allowed.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise ContractError(f"arrel d'output canònica absent: {allowed}") from exc
    if not allowed.is_dir() or allowed.is_symlink() or resolved != allowed:
        raise ContractError(f"arrel d'output o ancestre és symlink/no canònic: {allowed}")
    return allowed


def write_json_exclusive(path: Path, value: object) -> None:
    payload = json.dumps(
        value,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
    with path.open("x", encoding="utf-8") as handle:
        handle.write(payload)


def write_text_exclusive(path: Path, value: str, *, encoding: str = "ascii") -> None:
    with path.open("x", encoding=encoding) as handle:
        handle.write(value)


def _write_all_and_fsync(path: Path, payload: str) -> None:
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        written = handle.write(payload)
        if written != len(payload):
            raise OSError(f"short write: {written}/{len(payload)}")
        handle.flush()
        os.fsync(handle.fileno())


def write_terminal_json_atomic(path: Path, value: object) -> None:
    """Publica STATUS complet amb no-clobber; mai deixa STATUS parcial."""
    payload = json.dumps(
        value,
        indent=2,
        ensure_ascii=False,
        sort_keys=True,
        allow_nan=False,
    ) + "\n"
    temporary = path.parent.parent / f".{path.parent.name}.{path.name}.tmp"
    if path.exists() or path.is_symlink() or temporary.exists() or temporary.is_symlink():
        raise ContractError(f"commit terminal preexistent: {path}")
    published = False
    try:
        _write_all_and_fsync(temporary, payload)
        # hard-link és atòmic i no sobreescriu mai un STATUS preexistent.
        os.link(temporary, path, follow_symlinks=False)
        published = True
    finally:
        if temporary.exists() and not temporary.is_symlink():
            try:
                temporary.unlink()
            except OSError:
                if not published:
                    raise
                # STATUS ja és complet i autoritatiu; un hard-link temporal
                # residual no pot convertir-se en ERROR posterior.
    if not published:
        raise ContractError("STATUS no publicat")


def hash_one(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink():
        raise ContractError(f"font absent o symlink no admès: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        before = os.fstat(handle.fileno())
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
        after = os.fstat(handle.fileno())
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
    ):
        raise ContractError(f"font canviada durant el hash: {path}")
    return {"path": str(path), "bytes": before.st_size, "sha256": digest.hexdigest()}


def hash_many(paths: list[Path]) -> list[dict[str, object]]:
    with ThreadPoolExecutor(max_workers=4) as pool:
        rows = list(pool.map(hash_one, paths))
    return sorted(rows, key=lambda row: str(row["path"]))


def load_manifest() -> tuple[list[dict[str, Any]], dict[str, object]]:
    payload, manifest_anchor = read_frozen_bytes(MANIFEST)
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8-sig"), newline=""))
    required_columns = {
        "nom",
        "t_rel_c2",
        "exp_nominal",
        "exp_s",
        "temp_C",
        "sol_x",
        "sol_y",
        "n_sat",
        "usat",
    }
    if reader.fieldnames is None or not required_columns.issubset(reader.fieldnames):
        raise ContractError("manifest sense totes les columnes obligatòries")
    rows = list(reader)
    if len(rows) != 68:
        raise ContractError(f"manifest amb {len(rows)} files; esperades 68")
    names = [row["nom"] for row in rows]
    if len(set(names)) != 68:
        raise ContractError("manifest amb noms duplicats")
    for row in rows:
        name = row["nom"]
        if (
            Path(name).name != name
            or not re.fullmatch(r"572A\d{4}\.CR3", name)
        ):
            raise ContractError(f"selector RAW invàlid: {name!r}")
        if row["usat"].strip().lower() != "true":
            raise ContractError(f"fotograma no usat dins el contracte: {row['nom']}")
        try:
            row.update(
                t_rel_c2=float(row["t_rel_c2"]),
                exp_nominal=float(row["exp_nominal"]),
                exp_s=float(row["exp_s"]),
                temp_C=float(row["temp_C"]),
                sol_x=float(row["sol_x"]),
                sol_y=float(row["sol_y"]),
                n_sat=int(row["n_sat"]),
            )
        except (TypeError, ValueError) as exc:
            raise ContractError(f"camp numèric invàlid al manifest: {name}") from exc
        row["physical_exp_s"] = physical_exposure_s(row["exp_nominal"], row["exp_s"])
        finite_values = np.asarray(
            [
                row["t_rel_c2"],
                row["exp_nominal"],
                row["exp_s"],
                row["physical_exp_s"],
                row["temp_C"],
                row["sol_x"],
                row["sol_y"],
            ],
            dtype=np.float64,
        )
        if not np.all(np.isfinite(finite_values)):
            raise ContractError(f"camp no finit al manifest: {name}")
        if not (0 < row["exp_nominal"] <= 60 and 0 < row["exp_s"] <= 60):
            raise ContractError(f"exposició fora de rang al manifest: {name}")
        if not (-50 <= row["temp_C"] <= 100):
            raise ContractError(f"temperatura fora de rang al manifest: {name}")
        if not (0 <= row["sol_x"] < MOSAIC_SHAPE[1] and 0 <= row["sol_y"] < MOSAIC_SHAPE[0]):
            raise ContractError(f"centre solar fora del sensor al manifest: {name}")
        if not (0 <= row["n_sat"] <= MOSAIC_SHAPE[0] * MOSAIC_SHAPE[1]):
            raise ContractError(f"n_sat fora de rang al manifest: {name}")
    times = np.asarray([row["t_rel_c2"] for row in rows], dtype=np.float64)
    if not np.all(np.diff(times) > 0):
        raise ContractError("temps del manifest no estrictament creixents")
    actual_order_sha256 = frame_order_sha256(names)
    if actual_order_sha256 != EXPECTED_MANIFEST_ORDER_SHA256:
        raise ContractError("ordre del manifest divergent de l'ordre congelat de 68 frames")
    missing = [row["nom"] for row in rows if not (RAW_ROOT / row["nom"]).is_file()]
    if missing:
        raise ContractError(f"RAW absents: {missing}")
    return rows, manifest_anchor


def verify_raw_ledger(rows: list[dict[str, Any]]) -> dict[str, object]:
    s6_sums = frozen_sha256sums(VIXEN_S6, S6_SHA256SUMS)
    ledger_payload, ledger_anchor = read_sums_entry(LEDGER_68, VIXEN_S6, s6_sums)
    accepted = json_load_bytes(ledger_payload, source=LEDGER_68)
    if accepted.get("schema") is None or not isinstance(accepted.get("entries"), list):
        raise ContractError("LEDGER_68 sense esquema/entrades")
    if len(accepted["entries"]) != 68:
        raise ContractError("LEDGER_68 no conté exactament 68 entrades")
    expected = {row["frame"]: row for row in accepted["entries"]}
    if len(expected) != 68 or set(expected) != {row["nom"] for row in rows}:
        raise ContractError("LEDGER_68 divergent del conjunt congelat del manifest")
    paths = [RAW_ROOT / row["nom"] for row in rows]
    actual = hash_many(paths)
    failures = []
    for item in actual:
        name = Path(str(item["path"])).name
        authority = expected.get(name)
        if authority is None:
            failures.append({"frame": name, "reason": "not_in_LEDGER_68"})
            continue
        if item["bytes"] != authority["input_bytes"] or item["sha256"] != authority["input_sha256"]:
            failures.append({"frame": name, "reason": "bytes_or_sha256_mismatch"})
    return {
        "authority": str(LEDGER_68),
        "authority_sha256": ledger_anchor["sha256"],
        "authority_chain": {
            "root_sha256sums": require_frozen_authority(S6_SHA256SUMS),
            "ledger": ledger_anchor,
        },
        "checked": len(actual),
        "status": "PASS" if not failures and len(actual) == 68 else "FAIL",
        "failures": failures,
        "entries": actual,
    }


def audit_replicated_dark_border(
    master_path: Path,
    receipt: dict[str, object],
    dark_expected_by_name: dict[str, dict[str, object]],
    master_expected_by_name: dict[str, dict[str, object]],
) -> dict[str, object]:
    y0, x0, height, width = RAW_CROP_Y_X_H_W
    rows = []
    columns = []
    for name in receipt["darks"]:
        path = DARK_ROOT / name
        payload, row = read_bytes_hashed(path)
        expected = dark_expected_by_name.get(name)
        if (
            expected is None
            or row["sha256"] != expected["sha256"]
            or row["bytes"] != expected["bytes"]
        ):
            raise ContractError(f"dark canviat abans de l'auditoria de vora: {name}")
        with rawpy.imread(io.BytesIO(payload)) as raw:
            mosaic = raw.raw_image[y0 : y0 + height, x0 : x0 + width]
            rows.append(np.asarray(mosaic[-2:, :], dtype=np.float32))
            columns.append(np.asarray(mosaic[:, -2:], dtype=np.float32))
    # Mateix estimador que masters_vixen_v2.py: mitjana retallada min/max.
    full_rows = np.sort(np.stack(rows), axis=0)[1:-1].mean(axis=0, dtype=np.float32)
    full_columns = np.sort(np.stack(columns), axis=0)[1:-1].mean(axis=0, dtype=np.float32)
    master_payload, master_row = read_bytes_hashed(master_path)
    expected_master = master_expected_by_name.get(master_path.name)
    if (
        expected_master is None
        or master_row["sha256"] != expected_master["sha256"]
        or master_row["bytes"] != expected_master["bytes"]
    ):
        raise ContractError(f"màster dark canviat abans de l'auditoria: {master_path.name}")
    legacy = np.load(io.BytesIO(master_payload), allow_pickle=False)
    replicated = np.pad(legacy, ((0, 2), (0, 2)), mode="edge")

    def residual_stats(values: np.ndarray) -> dict[str, object]:
        residual = np.abs(np.asarray(values, dtype=np.float64)).ravel()
        return {
            "n": int(residual.size),
            "median_abs_adu": float(np.median(residual)),
            "p95_abs_adu": float(np.percentile(residual, 95)),
            "max_abs_adu": float(np.max(residual)),
        }

    return {
        "master": master_path.name,
        "exposure_s": receipt["exposure_s"],
        "n_darks": len(receipt["darks"]),
        "method": "rebuild full-grid final 2 rows/columns from listed CR3; discard per-pixel min/max; mean; compare with edge replication",
        "rows": residual_stats(full_rows - replicated[-2:, :]),
        "columns": residual_stats(full_columns - replicated[:, -2:]),
        "verdict": "EDGE_REPLICATION_NOT_SCIENTIFIC_DATA_USE_NAN_WEIGHT_ZERO",
    }


def accepted_s6_master_hashes() -> tuple[
    dict[str, dict[str, object]], list[dict[str, object]]
]:
    authority: dict[str, dict[str, object]] = {}
    receipt_ledger: list[dict[str, object]] = []
    s6_sums = frozen_sha256sums(VIXEN_S6, S6_SHA256SUMS)

    def visit(value: object, receipt: Path) -> None:
        if isinstance(value, dict):
            path = str(value.get("path", ""))
            name = Path(path).name
            if name.startswith("master_") and name.endswith((".npy", ".json")) and value.get("sha256"):
                row = authority.setdefault(
                    name,
                    {"sha256": value["sha256"], "bytes": value.get("bytes"), "receipts": []},
                )
                if row["sha256"] != value["sha256"] or row["bytes"] != value.get("bytes"):
                    raise ContractError(f"autoritats S6 divergents per {name}")
                row["receipts"].append(str(receipt))
            for child in value.values():
                visit(child, receipt)
        elif isinstance(value, list):
            for child in value:
                visit(child, receipt)

    receipts = sorted(VIXEN_S6.rglob("STACK_RECEIPT.json"))
    if not receipts:
        raise ContractError("cap STACK_RECEIPT a l'autoritat S6")
    expected_receipts = {
        name for name in s6_sums if Path(name).name == "STACK_RECEIPT.json"
    }
    actual_receipts = {receipt.relative_to(VIXEN_S6).as_posix() for receipt in receipts}
    if actual_receipts != expected_receipts:
        raise ContractError("conjunt de STACK_RECEIPT divergent de l'anchor S6")
    for receipt in receipts:
        payload, receipt_row = read_sums_entry(receipt, VIXEN_S6, s6_sums)
        receipt_ledger.append(receipt_row)
        visit(json_load_bytes(payload, source=receipt), receipt)
    if not authority:
        raise ContractError("els STACK_RECEIPT S6 no autoritzen cap màster dark")
    return authority, receipt_ledger


def dark_inventory() -> dict[str, object]:
    master_npy = sorted(MASTER_DARK_ROOT.glob("master_*.npy"))
    master_json = sorted(MASTER_DARK_ROOT.glob("master_*.json"))
    if len(master_npy) != 15 or len(master_json) != 15:
        raise ContractError("no hi ha exactament 15 parelles de màster dark")
    authority, s6_receipt_ledger = accepted_s6_master_hashes()
    current_master_names = {path.name for path in [*master_npy, *master_json]}
    if set(authority) != current_master_names:
        raise ContractError(
            "conjunt de 15 parelles de màster dark divergent de l'autoritat S6"
        )
    selected_names: set[str] = set()
    master_rows = []
    receipts_by_master: dict[str, dict[str, object]] = {}
    for path in master_npy:
        receipt_path = path.with_suffix(".json")
        npy_payload, npy_row = read_bytes_hashed(path)
        receipt_payload, receipt_row = read_bytes_hashed(receipt_path)
        for current in (npy_row, receipt_row):
            expected = authority.get(Path(str(current["path"])).name)
            if (
                expected is None
                or expected["sha256"] != current["sha256"]
                or expected["bytes"] != current["bytes"]
            ):
                raise ContractError(
                    "màster/rebut dark divergent abans de parsejar: "
                    f"{Path(str(current['path'])).name}"
                )
        array = np.load(io.BytesIO(npy_payload), allow_pickle=False)
        if array.shape != DARK_LEGACY_SHAPE:
            raise ContractError(f"{path.name}: forma {array.shape}")
        receipt = json_load_bytes(receipt_payload, source=receipt_path)
        receipts_by_master[path.name] = receipt
        dark_names = receipt.get("darks")
        if (
            not isinstance(dark_names, list)
            or len(dark_names) < 3
            or len(set(dark_names)) != len(dark_names)
            or any(
                not isinstance(name, str)
                or Path(name).name != name
                or not re.fullmatch(r"[A-Z0-9_]+\.CR3", name)
                for name in dark_names
            )
        ):
            raise ContractError(f"selector de darks invàlid: {receipt_path.name}")
        selected_names.update(dark_names)
        master_rows.append(
            {
                "npy": npy_row,
                "receipt": receipt_row,
                "shape": list(array.shape),
                "exposure_s": receipt["exposure_s"],
                "n_darks": receipt["n_darks"],
                "pedestal_median_adu": receipt["pedestal_mediana_ADU"],
            }
        )
        del array, npy_payload
    selected_paths = [DARK_ROOT / name for name in sorted(selected_names)]
    missing = [str(path) for path in selected_paths if not path.is_file()]
    if missing:
        raise ContractError(f"darks seleccionats absents: {missing[:5]}")
    selected_dark_ledger = hash_many(selected_paths)
    dark_expected_by_name = {
        Path(str(row["path"])).name: row for row in selected_dark_ledger
    }
    master_expected_by_name = {
        Path(str(row[key]["path"])).name: row[key]
        for row in master_rows
        for key in ("npy", "receipt")
    }
    authority_failures = []
    for row in master_rows:
        for key in ("npy", "receipt"):
            current = row[key]
            name = Path(str(current["path"])).name
            expected = authority.get(name)
            if (
                expected is None
                or expected["sha256"] != current["sha256"]
                or expected["bytes"] != current["bytes"]
            ):
                authority_failures.append(name)
    border_audits = [
        audit_replicated_dark_border(
            MASTER_DARK_ROOT / "master_0.0003125.npy",
            receipts_by_master["master_0.0003125.npy"],
            dark_expected_by_name,
            master_expected_by_name,
        ),
        audit_replicated_dark_border(
            MASTER_DARK_ROOT / "master_10.npy",
            receipts_by_master["master_10.npy"],
            dark_expected_by_name,
            master_expected_by_name,
        ),
    ]
    return {
        "root": str(DARK_ROOT),
        "root_cr3_count": len(list(DARK_ROOT.glob("*.CR3"))),
        "selected_unique_count": len(selected_paths),
        "selected_dark_ledger": selected_dark_ledger,
        "masters": master_rows,
        "accepted_s6_master_authority": {
            "root": str(VIXEN_S6),
            "expected_unique_files": len(authority),
            "checked_files": 2 * len(master_rows),
            "status": "PASS" if not authority_failures else "FAIL",
            "failures": sorted(authority_failures),
            "stack_receipt_ledger": s6_receipt_ledger,
        },
        "edge_replication_audit": border_audits,
        "padding_contract": {
            "source_shape": list(DARK_LEGACY_SHAPE),
            "target_shape": list(MOSAIC_SHAPE),
            "shape_adapter": "allocate full float grid as NaN and copy the measured 4638x6958 region into the top-left",
            "scientific_validity": "last two rows and last two columns remain NaN/no-data before and after subtraction",
            "weight_contract": "w=0 on the no-data border in every later accumulation",
            "reason": "replicated edge values are not measurements of the missing dark pixels",
        },
    }


def flat_inventory() -> dict[str, object]:
    flat_sums = frozen_sha256sums(FLAT_ROOT, FLAT_SHA256SUMS)
    receipt_path = FLAT_ROOT / "MASTER_FLAT_RECEIPT.json"
    receipt_payload, receipt_anchor = read_sums_entry(
        receipt_path, FLAT_ROOT, flat_sums
    )
    receipt = json_load_bytes(receipt_payload, source=receipt_path)
    source_expected = receipt["source_sha256"]
    source_paths = [Path(path) for path in sorted(source_expected)]
    if len(source_paths) != 125:
        raise ContractError("el rebut del flat no selecciona exactament 125 fonts")
    for path in source_paths:
        if (
            path.parent != FLAT_SOURCE_ROOT
            or not re.fullmatch(r"[A-Z0-9_]+\.CR3", path.name)
            or not re.fullmatch(r"[0-9a-f]{64}", str(source_expected[str(path)]))
            or path.is_symlink()
        ):
            raise ContractError(f"selector/hash de font flat invàlid: {path}")
    actual = hash_many(source_paths)
    failures = [
        Path(str(item["path"])).name
        for item in actual
        if item["sha256"] != source_expected[str(item["path"])]
    ]
    sums_failures = []
    products_ledger = []
    for name in sorted(flat_sums):
        try:
            products_ledger.append(
                verify_sums_entry(FLAT_ROOT / name, FLAT_ROOT, flat_sums)
            )
        except ContractError:
            sums_failures.append(name)
    radial_path = FLAT_ROOT / "MASTER_OPTICAL_RADIAL_CFA4.npy"
    radial_payload, radial_anchor = read_sums_entry(radial_path, FLAT_ROOT, flat_sums)
    radial = np.load(io.BytesIO(radial_payload), allow_pickle=False)
    if radial.shape != CFA4_SHAPE:
        raise ContractError(f"radial CFA4 amb forma {radial.shape}")
    return {
        "source_root": str(FLAT_SOURCE_ROOT),
        "source_count": len(source_paths),
        "source_ledger": actual,
        "source_status": "PASS" if not failures else "FAIL",
        "source_failures": failures,
        "receipt": hash_one(receipt_path),
        "authority_chain": {
            "root_sha256sums": require_frozen_authority(FLAT_SHA256SUMS),
            "receipt": receipt_anchor,
        },
        "radial_cfa4": radial_anchor,
        "radial_fits": hash_one(FLAT_ROOT / "MASTER_OPTICAL_RADIAL_CFA.fits"),
        "products_sha256_status": "PASS" if not sums_failures else "FAIL",
        "products_sha256_failures": sums_failures,
        "products_ledger": products_ledger,
        "policy": receipt["product_policy"],
        "grid": receipt["grid"],
        "axis_authority": {
            "status": "UNIDENTIFIABLE_FROM_CURRENT_SINGLE_ORIENTATION_FLAT",
            "radial_master_center": "hard-coded geometric centre (h-1)/2,(w-1)/2 by radialize_log",
            "quadratic_axis_plus_plane_exact_degeneracy_max_abs": quadratic_axis_plane_degeneracy_error(),
            "meaning": "the radial product is constructed about the geometric centre; it is not an independent optical-axis measurement",
        },
    }


def sensor_grid(
    rows: list[dict[str, Any]], raw_ledger: dict[str, object]
) -> dict[str, object]:
    sample = RAW_ROOT / rows[0]["nom"]
    expected = {
        Path(str(row["path"])).name: row for row in raw_ledger["entries"]
    }[sample.name]
    payload, sample_row = read_bytes_hashed(sample)
    if (
        sample_row["sha256"] != expected["sha256"]
        or sample_row["bytes"] != expected["bytes"]
    ):
        raise ContractError("RAW mostra canviat entre ledger i parse")
    y0, x0, height, width = RAW_CROP_Y_X_H_W
    with rawpy.imread(io.BytesIO(payload)) as raw:
        raw_shape = list(raw.raw_image.shape)
        visible_shape = list(raw.raw_image_visible.shape)
        crop = raw.raw_image[y0 : y0 + height, x0 : x0 + width]
        pattern = "".join("RGBG"[int(value)] for value in raw.raw_pattern.ravel())
    if crop.shape != MOSAIC_SHAPE or pattern != "RGGB":
        raise ContractError(f"crop/patró inesperat: {crop.shape}, {pattern}")
    return {
        "sample": str(sample),
        "sample_same_bytes_ledger": sample_row,
        "raw_image_shape": raw_shape,
        "raw_image_visible_shape": visible_shape,
        "chosen_crop_y_x_h_w": list(RAW_CROP_Y_X_H_W),
        "chosen_crop_shape": list(crop.shape),
        "cfa_pattern": pattern,
        "reason": "full 6960x4640 sensor grid used by posterior flat; avoids libraw visible off-by-one",
    }


def flat_leverage(rows: list[dict[str, Any]]) -> dict[str, object]:
    """Palanca del radial Vixen entre el primer i l'últim Sol, sense cel."""
    flat_sums = frozen_sha256sums(FLAT_ROOT, FLAT_SHA256SUMS)
    radial_payload, radial_anchor = read_sums_entry(
        FLAT_ROOT / "MASTER_OPTICAL_RADIAL_CFA4.npy", FLAT_ROOT, flat_sums
    )
    radial = np.load(io.BytesIO(radial_payload), allow_pickle=False)
    green = 0.5 * (np.asarray(radial[1], dtype=np.float64) + np.asarray(radial[2], dtype=np.float64))
    first, last = rows[0], rows[-1]
    solar_radius_px = 947.068 / CANVAS_SCALE_ARCSEC_PX
    step = 16
    yy, xx = np.mgrid[0 : MOSAIC_SHAPE[0] : step, 0 : MOSAIC_SHAPE[1] : step]
    dx = xx - first["sol_x"]
    dy = yy - first["sol_y"]
    radius = np.hypot(dx, dy) / solar_radius_px
    bx = last["sol_x"] + dx
    by = last["sol_y"] + dy
    valid = (
        (radius >= 1.3)
        & (radius <= 7.0)
        & (bx >= 2)
        & (bx < MOSAIC_SHAPE[1] - 2)
        & (by >= 2)
        & (by < MOSAIC_SHAPE[0] - 2)
    )
    fa = map_coordinates(green, [yy[valid] / 2.0, xx[valid] / 2.0], order=1, mode="nearest")
    fb = map_coordinates(green, [by[valid] / 2.0, bx[valid] / 2.0], order=1, mode="nearest")
    predictor = np.log(fb / fa)
    percentiles = np.percentile(predictor, [1, 5, 50, 95, 99])
    return {
        "frame_a": first["nom"],
        "frame_b": last["nom"],
        "sun_shift_xy_px": [last["sol_x"] - first["sol_x"], last["sol_y"] - first["sol_y"]],
        "domain_solar_radii": [1.3, 7.0],
        "sample_count": int(predictor.size),
        "radial_input": radial_anchor,
        "log_flat_ratio_percentiles_p01_p05_p50_p95_p99": percentiles.tolist(),
        "p95_minus_p05": float(percentiles[3] - percentiles[1]),
        "standard_deviation": float(np.std(predictor)),
        "verdict": "INSUFFICIENT_VIXEN_DITHER_FOR_SONY_STYLE_TWO_POINTING_GATE",
        "note": "diagnostic of leverage only; no sky signal is used and this cannot PASS F0",
    }


def geometry_audit(rows: list[dict[str, Any]]) -> dict[str, object]:
    plate_payload, plate_anchor = read_frozen_bytes(PLATE)
    geometry_payload, geometry_anchor = read_frozen_bytes(GEOMETRY)
    drift_payload, drift_anchor = read_frozen_bytes(CORONA_DRIFT)
    plate_source_row = hash_one(PLATE_SOURCE)
    authority_chain = {
        "plate": plate_anchor,
        "historical_geometry": geometry_anchor,
        "partial_drift": drift_anchor,
    }
    plate_document = json_load_bytes(plate_payload, source=PLATE)
    solution = plate_document["r6_radial"]
    historical = json_load_bytes(geometry_payload, source=GEOMETRY)
    drift = json_load_bytes(drift_payload, source=CORONA_DRIFT)
    historical_rms = float(
        np.hypot(historical["residu_px"]["x"], historical["residu_px"]["y"])
    )
    drift_rms = float(np.hypot(drift["residu_model_x_px"], drift["residu_model_y_px"]))
    frames = [
        {
            "width": MOSAIC_SHAPE[1],
            "height": MOSAIC_SHAPE[0],
            "sun_x": row["sol_x"],
            "sun_y": row["sol_y"],
            "pa_north_deg": solution["pa_north"],
            "scale_arcsec_px": solution["scale"],
        }
        for row in rows
    ]
    canvas = common_canvas_from_perimeters(frames, kernel_support_px=4)
    canvas.update(
        {
            "status": "DIAGNOSTIC_AFFINE_ENVELOPE_NOT_F1_AUTHORITY",
            "omitted_from_diagnostic": "inverse of the px/py radial plate terms and per-frame apparent-plane epoch",
        }
    )
    angles = np.linspace(0.0, 2.0 * np.pi, 8, endpoint=False)
    validation_points = np.vstack(
        [
            np.column_stack((radius * np.cos(angles), radius * np.sin(angles)))
            for radius in (1000.0, 3000.0)
        ]
    )

    def constant_control(value: float) -> dict[str, object]:
        residuals = np.tile([value, 0.0], (validation_points.shape[0], 1))
        ids = ["fixture"]
        return registration_gate(
            {"fixture": residuals},
            {"fixture": validation_points},
            held_out=True,
            expected_frame_ids=ids,
            expected_order_sha256=frame_order_sha256(ids),
        )

    outlier_residuals = {
        **{
            f"ok_{index:02d}": np.zeros_like(validation_points)
            for index in range(67)
        },
        "bad_67": np.tile([2.0, 0.0], (validation_points.shape[0], 1)),
    }
    outlier_points = {name: validation_points for name in outlier_residuals}
    outlier_ids = list(outlier_residuals)
    theta = np.deg2rad(0.01)
    rotation = np.array(
        [[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]],
        dtype=np.float64,
    )
    rotation_residual = (rotation @ validation_points.T).T - validation_points
    controls = {
        "0.299_px": constant_control(0.299),
        "0.301_px": constant_control(0.301),
        "global_can_hide_one_2px_outlier": registration_gate(
            outlier_residuals,
            outlier_points,
            held_out=True,
            expected_frame_ids=outlier_ids,
            expected_order_sha256=frame_order_sha256(outlier_ids),
        ),
        "rotation_0.01deg_at_1000_3000px": registration_gate(
            {"field": rotation_residual},
            {"field": validation_points},
            held_out=True,
            expected_frame_ids=["field"],
            expected_order_sha256=frame_order_sha256(["field"]),
        ),
        "one_central_point_is_not_a_gate": registration_gate(
            {"central": np.array([[0.0, 0.0]])},
            {"central": np.array([[0.0, 0.0]])},
            held_out=True,
            expected_frame_ids=["central"],
            expected_order_sha256=frame_order_sha256(["central"]),
        ),
    }
    return {
        "authority_chain": authority_chain,
        "plate_solution": {
            "path": str(PLATE),
            "sha256": plate_anchor["sha256"],
            "n": solution["n"],
            "rms_px": solution["rms"],
            "scale_arcsec_px": solution["scale"],
            "pa_north_deg": solution["pa_north"],
            "status_against_0.3px": "PASS" if solution["rms"] <= 0.3 else "FAIL",
            "context_source_not_cryptographically_linked": {
                **plate_source_row,
                "status": "CONTEXT_ONLY_NOT_PROVENANCE_OF_FROZEN_SOLUTION",
                "declared_frame": "topocentric apparent horizontal tangent plane with refraction",
                "r6_epoch_utc": "2026-08-12T18:29:18.600000Z",
                "temperature_C": 20.0,
                "pressure_mbar": 930.0,
                "metadata_gap": "these projection/epoch fields are in source code but absent from final_solution.json",
            },
        },
        "historical_geometry": {
            "path": str(GEOMETRY),
            "sha256": geometry_anchor["sha256"],
            "rms_2d_px": historical_rms,
            "status_against_0.3px": "PASS" if historical_rms <= 0.3 else "FAIL",
        },
        "partial_same_exposure_drift": {
            "path": str(CORONA_DRIFT),
            "sha256": drift_anchor["sha256"],
            "rms_2d_px": drift_rms,
            "pairs": drift["n_parelles"],
            "status": "PARTIAL_PASS_NOT_68_FRAME_ORACLE" if drift_rms <= 0.3 else "FAIL",
        },
        "missing_for_full_gate": [
            "independent held-out residuals for every included frame",
            "per-frame rotation or a leave-one-out bound proving constant PA is sufficient",
            "ledger of excluded/interpolated frames",
            "physical-midpoint geometry recomputation for the three 10.079368399159 s frames",
            "direct inversion/use of the full radial px/py plate terms instead of scale+PA affine only",
            "apparent tangent-plane epoch and refraction parameters frozen per frame in the transform receipt",
        ],
        "derived_common_canvas": canvas,
        "adversarial_controls": controls,
        "status": "FAIL",
    }


def architecture_receipt() -> dict[str, object]:
    return {
        "status": "DESIGN_DIRECTION_ONLY_NOT_FROZEN_FOR_PRODUCTION",
        "authority": "OFFLINE_FLOAT_NUMERATOR_DENOMINATOR",
        "formula": {
            "per_frame": "J_i = k_i(phi) * f_i + q_i(phi)",
            "numerator": "N = sum_i(w_i * J_i)",
            "denominator": "D = sum_i(w_i)",
            "result": "g = N / D where D > 0; NaN where D == 0",
        },
        "single_pass": "each F1-admitted individual frame contributes exactly once to one additive N/D; target 68, but rejected/interpolated frames do not enter",
        "input_frame_order": {
            "count": 68,
            "source": str(MANIFEST),
            "sha256_join_newline": EXPECTED_MANIFEST_ORDER_SHA256,
        },
        "production_frame_order": {
            "status": "NOT_FROZEN_UNTIL_F1_INCLUSION_EXCLUSION_LEDGER",
            "rule": "manifest order filtered by the frozen F1 inclusion ledger; hash the resulting ordered IDs",
        },
        "per_frame_payload_authority": {
            "status": "NOT_YET_MATERIALIZED",
            "required": "hash by frame ID of calibrated f_i, weight w_i, k_i, q_i and resulting J_i; ID order hash alone is insufficient",
        },
        "photoshop": {
            "role": "reversible weight-editing interface and preview only",
            "editable_source": "one weight map w_i per individual frame",
            "round_trip": "extract/hash weights, recompute N/D/g offline, create a successor PSB",
            "not_authority": "normal alpha compositing is order-dependent and does not compute sum(wI)/sum(w)",
        },
        "unresolved_before_phase_2": [
            "freeze the F1 inclusion/exclusion/interpolation ledger and resulting ordered frame hash",
            "freeze the gauge, fitting order and iteration count for all 60 k_i/q_i segments",
            "freeze the weight formula, masks, precision and per-frame hashes",
            "freeze the explicit F-domain and finite relative floor",
            "freeze storage dtype, colour encoding and no-data representation",
            "persist and hash N, D and g as independent scientific payloads",
            "validate Photoshop weight encoding and numerical round-trip against offline N/D",
        ],
        "phase_2_status": "NOT_RUN_UPSTREAM_F0_F1",
    }


def effective_manifest(
    rows: list[dict[str, Any]], manifest_anchor: dict[str, object]
) -> dict[str, object]:
    entries = []
    for row in rows:
        correction = 0.5 * (row["physical_exp_s"] - row["exp_s"])
        is_long = abs(row["exp_nominal"] - 10.0) < 1e-9
        entries.append(
            {
                "frame": row["nom"],
                "t_rel_c2_manifest_s": row["t_rel_c2"],
                "t_rel_c2_physical_midpoint_s": row["t_rel_c2"] + correction,
                "midpoint_correction_s": correction,
                "exposure_nominal_s": row["exp_nominal"],
                "exposure_manifest_s": row["exp_s"],
                "exposure_physical_s": row["physical_exp_s"],
                "dark_master_nominal_s": row["exp_nominal"],
                "temperature_C": row["temp_C"],
                "sun_xy_manifest_px": [row["sol_x"], row["sol_y"]],
                "geometry_status": (
                    "REQUIRES_ACCEPTED_S6_PHYSICAL_RECOMPUTE_BEFORE_F1"
                    if is_long
                    else "MANIFEST_UNCHANGED"
                ),
            }
        )
    return {
        "schema": "VIXEN_68_EFFECTIVE_INPUT_V1",
        "source_manifest": str(MANIFEST),
        "source_manifest_sha256": manifest_anchor["sha256"],
        "input_frame_order_sha256_join_newline": frame_order_sha256(
            [row["nom"] for row in rows]
        ),
        "historical_manifest_mutated": False,
        "long_exposure_authority": "Canon MakerNote as frozen by accepted S6",
        "entries": entries,
    }


def source_provenance() -> dict[str, object]:
    import scipy

    source_paths = [
        Path(__file__).resolve(),
        Path(__file__).with_name("contracts.py").resolve(),
        Path(__file__).with_name("test_contracts.py").resolve(),
        Path(__file__).with_name("test_preflight.py").resolve(),
        Path(__file__).with_name("README.md").resolve(),
        Path(__file__).with_name("run_preflight.sh").resolve(),
    ]
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=WORKTREE,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "schema": "PILOT_VIXEN_LDIC_PROVENANCE_V1",
        "argv": sys.argv,
        "resolved_interpreter_recorded_not_hardcoded": sys.executable,
        "python": sys.version,
        "platform": platform.platform(),
        "packages": {
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "rawpy": rawpy.__version__,
        },
        "worktree": str(WORKTREE),
        "git_head": commit,
        "source_files": [hash_one(path) for path in source_paths],
    }


def write_payload_sha256sums(directory: Path) -> Path:
    paths = sorted(
        path
        for path in directory.iterdir()
        if path.is_file()
        and path.name not in {"PAYLOAD_SHA256SUMS.txt", "STATUS.json", "ERROR.json"}
    )
    sums_path = directory / "PAYLOAD_SHA256SUMS.txt"
    with sums_path.open("x", encoding="ascii") as handle:
        for path in paths:
            handle.write(f"{sha256(path)}  {path.name}\n")
    return sums_path


def verify_payload_sha256sums(directory: Path, sums_path: Path) -> int:
    entries = {}
    for line in sums_path.read_text(encoding="ascii").splitlines():
        expected, name = line.split(maxsplit=1)
        name = name.lstrip("* ")
        if (
            not re.fullmatch(r"[0-9a-f]{64}", expected)
            or Path(name).name != name
            or name in entries
        ):
            raise ContractError("PAYLOAD_SHA256SUMS invàlid")
        entries[name] = expected
    current_names = sorted(
        path.name
        for path in directory.iterdir()
        if path.is_file()
        and path.name not in {"PAYLOAD_SHA256SUMS.txt", "STATUS.json", "ERROR.json"}
    )
    if sorted(entries) != current_names:
        raise ContractError("PAYLOAD_SHA256SUMS no cobreix exactament el payload")
    for name, expected in entries.items():
        if sha256(directory / name) != expected:
            raise ContractError(f"payload divergent després del commit: {name}")
    return len(entries)


def revalidate_consumed_inputs(*documents: object) -> dict[str, object]:
    """Rehasheja al gate terminal cada path+sha256 consumit pels rebuts."""
    expected_by_path: dict[str, dict[str, object]] = {}

    def visit(value: object) -> None:
        if isinstance(value, dict):
            path = value.get("path")
            expected_hash = value.get("sha256")
            if (
                isinstance(path, str)
                and isinstance(expected_hash, str)
                and re.fullmatch(r"[0-9a-f]{64}", expected_hash)
            ):
                existing = expected_by_path.setdefault(
                    path,
                    {
                        "sha256": expected_hash,
                        "bytes": value.get("bytes"),
                    },
                )
                if existing["sha256"] != expected_hash or (
                    existing.get("bytes") is not None
                    and value.get("bytes") is not None
                    and existing["bytes"] != value["bytes"]
                ):
                    raise ContractError(f"hash/bytes esperats divergents per {path}")
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    for document in documents:
        visit(document)
    if not expected_by_path:
        raise ContractError("cap input consumit disponible per revalidar")
    verified = []
    for path_string in sorted(expected_by_path):
        path = Path(path_string)
        if not path.is_absolute():
            raise ContractError(f"input consumit amb ruta no absoluta: {path}")
        current = hash_one(path)
        expected = expected_by_path[path_string]
        if current["sha256"] != expected["sha256"] or (
            expected.get("bytes") is not None
            and current["bytes"] != expected["bytes"]
        ):
            raise ContractError(f"input canviat abans del commit terminal: {path}")
        verified.append(current)
    digest = hashlib.sha256()
    for row in verified:
        digest.update(str(row["path"]).encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(row["bytes"]).encode("ascii"))
        digest.update(b"\0")
        digest.update(str(row["sha256"]).encode("ascii"))
        digest.update(b"\n")
    return {
        "status": "PASS_REHASHED_IMMEDIATELY_BEFORE_STATUS",
        "unique_file_count": len(verified),
        "aggregate_sha256_path_bytes_hash": digest.hexdigest(),
        "total_bytes_with_unique_paths": sum(int(row["bytes"]) for row in verified),
    }


def build_preflight(out: Path) -> int:
    claim = require_codex_claim()
    allowed = canonical_output_root()
    if (
        out.parent != allowed
        or out.name in {"", ".", ".."}
        or "\n" in out.name
        or out.is_symlink()
        or not out.parent.is_dir()
        or out.parent.is_symlink()
    ):
        raise ContractError(f"arrel d'output absent o symlink: {out.parent}")
    try:
        out.mkdir()
    except FileExistsError as exc:
        raise ContractError(f"output preexistent: {out}") from exc
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    terminal_committed = False
    try:
        write_json_exclusive(
            out / "RUN_STARTED.json",
            {
                "schema": "PILOT_VIXEN_LDIC_RUN_EVENT_V1",
                "event": "RUN_STARTED",
                "terminal": False,
                "started_utc": started,
                "claim": claim,
            },
        )
        rows, manifest_anchor = load_manifest()
        raw_count = len(list(RAW_ROOT.glob("*.CR3")))
        raw_ledger = verify_raw_ledger(rows)
        darks = dark_inventory()
        flats = flat_inventory()
        if raw_ledger["status"] != "PASS":
            raise ContractError(f"integritat RAW contra LEDGER_68: {raw_ledger['failures']}")
        if darks["accepted_s6_master_authority"]["status"] != "PASS":
            raise ContractError(
                "integritat màsters dark contra S6: "
                f"{darks['accepted_s6_master_authority']['failures']}"
            )
        if flats["source_status"] != "PASS" or flats["products_sha256_status"] != "PASS":
            raise ContractError(
                "integritat flat: "
                f"sources={flats['source_status']} products={flats['products_sha256_status']}"
            )
        grid = sensor_grid(rows, raw_ledger)
        leverage = flat_leverage(rows)
        geometry = geometry_audit(rows)
        effective = effective_manifest(rows, manifest_anchor)
        inventory = {
            "raw_root": str(RAW_ROOT),
            "raw_root_cr3_count": raw_count,
            "handoff_claimed_raw_count": 129,
            "canonical_prior_count": 124,
            "manifest": manifest_anchor,
            "manifest_selected_count": len(rows),
            "manifest_unique_count": len({row["nom"] for row in rows}),
            "exposure_histogram": dict(
                sorted(Counter(str(row["exp_nominal"]) for row in rows).items())
            ),
            "physical_long_exposure_s": PHYSICAL_LONG_EXPOSURE_S,
            "raw_ledger_68": raw_ledger,
            "darks": darks,
            "flats": flats,
            "sensor_grid": grid,
        }
        gates = {
            "F0_calibration": {
                "status": "BLOCKED_CONTRACT_MISMATCH_AND_INSUFFICIENT_LEVERAGE",
                "official_gate": "coefficient 1.00 +/- 0.05 and R2 >= 0.95",
                "finding": "the +1.019/R2=0.981 positive fixture belongs to Sony's two pointings, not Vixen",
                "flat_policy": "radial-only candidate; full/2D/fine excluded",
                "axis": flats["axis_authority"],
                "vixen_leverage": leverage,
                "required_positive_evidence": "same-exposure held-out Vixen pairs with enough flat-ratio leverage, beta CI95 inside [0.95,1.05], R2>=0.95",
                "known_bad_controls_specified": [
                    "flat=1 -> UNDECIDABLE_INSUFFICIENT_LEVERAGE",
                    "inverse flat -> beta approximately -1 -> FAIL",
                    "multiply rather than divide -> residual slope approximately 2 -> FAIL",
                    "MASTER_FULL/2D -> FAIL by quarantined product policy",
                    "Sony model/serial/shape -> FAIL identity contract",
                ],
            },
            "F1_registration": geometry,
            "F2_composition": {
                "status": "NOT_RUN_UPSTREAM_F0_F1",
                "required_F": "relative max deviation < 1e-3 with declared floor, frozen order and iterations",
                "required_E": "monotonic radial profile evaluated before fitting k/q",
            },
        }
        overall = "BLOCKED_UPSTREAM_GATES"
        architecture = architecture_receipt()
        provenance = source_provenance()
        write_json_exclusive(out / "INPUT_INVENTORY.json", inventory)
        write_json_exclusive(out / "EFFECTIVE_MANIFEST.json", effective)
        write_json_exclusive(out / "GATES.json", gates)
        write_json_exclusive(out / "ARCHITECTURE.json", architecture)
        write_json_exclusive(out / "PROVENANCE.json", provenance)
        write_text_exclusive(out / "BLOCKED", "BLOCKED_UPSTREAM_GATES\n")
        sums_path = write_payload_sha256sums(out)
        payload_count = verify_payload_sha256sums(out, sums_path)
        terminal_claim_before_rehash = require_codex_claim()
        if terminal_claim_before_rehash != claim:
            raise ContractError("SERIAL_WRITES ha canviat durant la materialització")
        terminal_inputs = revalidate_consumed_inputs(
            inventory,
            effective,
            gates,
            architecture,
            provenance,
            claim,
        )
        if len(list(RAW_ROOT.glob("*.CR3"))) != raw_count:
            raise ContractError("recompte de l'arrel RAW canviat abans de STATUS")
        if len(list(DARK_ROOT.glob("*.CR3"))) != darks["root_cr3_count"]:
            raise ContractError("recompte de l'arrel dark canviat abans de STATUS")
        payload_count = verify_payload_sha256sums(out, sums_path)
        terminal_claim = require_codex_claim()
        if terminal_claim != claim:
            raise ContractError("SERIAL_WRITES ha canviat durant el rehash terminal")
        status = {
            "schema": "PILOT_VIXEN_LDIC_PREFLIGHT_V1",
            "status": overall,
            "started_utc": started,
            "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "terminal_commit": True,
            "terminal_status_publish": "ATOMIC_HARDLINK_NO_CLOBBER_AFTER_PAYLOAD_VERIFY",
            "claim": terminal_claim,
            "payload_sha256sums": hash_one(sums_path),
            "payload_file_count": payload_count,
            "terminal_input_revalidation": terminal_inputs,
            "hardware_contact": False,
            "raw_mutations": 0,
            "historical_product_mutations": 0,
            "phase_2_executed": False,
            "blockers": [
                "F0 positive coefficient/R2 fixture is Sony-only; no equivalent Vixen gate can currently PASS",
                "Vixen optical axis is not independently identifiable from the present single-orientation flat",
                "F1 plate RMS 0.424193 px exceeds 0.3 px and there is no 68-frame held-out oracle",
                "F1 production transform still needs full radial plate inversion and per-frame apparent-plane epoch",
            ],
        }
        # Commit terminal: després d'aquest create exclusiu no es toca cap fitxer del build.
        write_terminal_json_atomic(out / "STATUS.json", status)
        terminal_committed = True
        return 2
    except Exception as exc:
        error = {
            "schema": "PILOT_VIXEN_LDIC_PREFLIGHT_V1",
            "status": "INCOMPLETE_ERROR",
            "started_utc": started,
            "failed_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
            "error_type": type(exc).__name__,
            "error": str(exc),
        }
        if not terminal_committed:
            try:
                write_json_exclusive(out / "ERROR.json", error)
            except Exception:
                pass
        print(json.dumps(error, indent=2, ensure_ascii=False), file=sys.stderr)
        print(f"build parcial preservat: {out}", file=sys.stderr)
        return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True, help="build ID nou; mai se sobreescriu")
    return parser.parse_args()


def report_terminal_build(out: Path) -> None:
    """Reporta un commit ja tancat; mai no escriu dins del build."""
    status_path = out / "STATUS.json"
    if status_path.is_file():
        print(json.dumps(json_load(status_path), indent=2, ensure_ascii=False))
        print(f"output: {out}")


def main() -> int:
    args = parse_args()
    out = Path(os.path.abspath(os.fspath(args.out.expanduser())))
    try:
        allowed = canonical_output_root()
    except ContractError as exc:
        raise SystemExit(str(exc)) from exc
    if (
        out.parent != allowed
        or out.name in {"", ".", ".."}
        or "\n" in out.name
        or out.is_symlink()
        or allowed.is_symlink()
    ):
        raise SystemExit(f"--out ha de ser un fill directe de {allowed}")
    try:
        result = build_preflight(out)
    except ContractError as exc:
        print(
            json.dumps(
                {"status": "FAIL_NO_CLOBBER_OR_CONTRACT", "error": str(exc)},
                indent=2,
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    # Reporting is deliberately outside build_preflight's exception/ERROR path:
    # a closed stdout after terminal commit must never append ERROR after STATUS.
    report_terminal_build(out)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
