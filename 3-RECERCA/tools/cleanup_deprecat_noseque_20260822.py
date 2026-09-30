#!/usr/bin/env python3
"""Neteja reversible i no-clobber de dos directoris provisionals del projecte.

Abast deliberadament fix:

* ``~/Desktop/Eclipse 2026/Deprecat``;
* el fill Unicode-equivalent a ``No se que fa això aquí``;
* sis TIFF que es recuperen, amb SHA-256 conegut, del backup de 4 TB;
* un lot únic de Paperera que no es buida;
* un rebut auditable sota ``output/cleanup`` del worktree canònic.

No segueix symlinks, no toca RAW originals i no permet sobreescriure cap
destinació. ``--plan`` és read-only; ``--execute`` exigeix el SERIAL_WRITES
concret d'aquesta ronda.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys
import unicodedata


WORKTREE = Path("/Users/USUARI/Downloads/Eclipse 2026")
DESKTOP = Path("/Users/USUARI/Desktop/Eclipse 2026")
BACKUP = Path("/Volumes/4TB/Eclipse 2026-22Agost/Eclipse 2026")
TRASH_BATCH = Path("/Users/USUARI/.Trash/Eclipse2026_cleanup_20260822T151257Z")
RECEIPT_DIR = WORKTREE / "output/cleanup/20260822T151257Z_deprecat_noseque"
LOCK_OWNER = WORKTREE / ".coordination/claim.lock/owner.json"
CLAIM_ID = "DBC63AC4-B75F-4088-84BB-741EAF104581"

DEP = DESKTOP / "Deprecat"


def nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def resolve_child_nfc(parent: Path, wanted: str) -> Path:
    matches = [child for child in parent.iterdir() if nfc(child.name) == nfc(wanted)]
    if len(matches) != 1:
        raise SystemExit(
            f"Cal exactament un fill Unicode-equivalent a {wanted!r} sota {parent}; "
            f"n'hi ha {len(matches)}"
        )
    return matches[0]


NOSE = resolve_child_nfc(DESKTOP, "No se que fa això aquí")
COORD = resolve_child_nfc(DESKTOP / "IA", "Coordinació")


EXPECTED_DEP_TOP = {
    ".DS_Store",
    "APOD",
    "Corona_HDR_Vixen",
    "Earthshine_FINAL",
    "PROPOSTA_Normalitzacio_Exposicio_CapesTotalsV4.md",
}

EXPECTED_NOSE_TOP = {
    ".DS_Store",
    "300mm_apilat_v2",
    "300mm_apilat_v3",
    "Aplicant_Filtres.tif",
    "Calibrated_Claude",
    "CapesInteriorsV4.psb.anterior-disseny-claude",
    "CapesInteriorsV4_QA",
    "CapesTotalsV2.manifest.json",
    "CapesTotalsV2b.manifest.json",
    "CapesTotalsV3b.manifest.json",
    "CapesTotalsV3b_QA",
    "CapesTotalsV3c.manifest.json",
    "CapesTotalsV3c.manifest_v3c.json",
    "CapesTotalsV3c_QA",
    "CapesTotalsV4.manifest.json",
    "CapesTotalsV4.manifest_v4.json",
    "CapesTotalsV4_QA",
    "CapesTotalsV4b.manifest.json",
    "CapesTotalsV4b.manifest_v4.json",
    "CapesTotalsV4b_QA",
    "Druckmuller_2026-08-18",
    "Earthshine_Claude",
    "Earthshine_Claude Sony",
    "Estrelles",
    "HDR4",
    "LLEGEIX-ME_CapesInteriorsV4.md",
    "LLEGEIX-ME_CapesInteriorsV5.md",
    "LLEGEIX-ME_CapesTotalsV1.md",
    "LLEGEIX-ME_CapesTotalsV2b.md",
    "LLEGEIX-ME_CapesTotalsV3b.md",
    "LLEGEIX-ME_CapesTotalsV3c.md",
    "LLEGEIX-ME_CapesTotalsV4.md",
    "LLEGEIX-ME_CapesTotalsV4b.md",
    "LLEGEIX-ME_alineades.md",
    "SEMIFINAL3_capes",
    "_prova_skill",
    "_prova_skill_estrelles",
    "alineades_7648x5353",
    "observacions_skills.md",
}


RESTORE_TIFFS = {
    "POWAAAH3_ajustada_llencAjust.tif": (
        66_085_951,
        "fa33feb98530007fc7353eee0f3652b4d132e0b8b824b281730f40b5c6baff00",
    ),
    "POWAAAH3_ajustada_llencPere.tif": (
        163_283_233,
        "fc141294c04b357fd6bdc5cc22245b33de09cac0d785a2ee84c929001639d1ee",
    ),
    "POWAAAH3_ajustada_mascara_disc.tif": (
        86_425,
        "0f798e8c5422a7e05daf0ed08c7fb414d14d4e29fa8eb79884fc00127096aa57",
    ),
    "POWAAAH3_ajustada_nomes_disc.tif": (
        70_426_216,
        "e57aaf56c4e7432e5e7fd55365ca64bd247d683dee2b990048ed9b6f799cee37",
    ),
    "corona_vixen_HIBRID_base_lluna_negra_llencPere.tif": (
        143_749_632,
        "7aa1d2fed3e442379699e96b5c666224a6a2367dc93c72ed4de0be60a9142d91",
    ),
    "corona_vixen_HIBRID_llencPere.tif": (
        146_051_759,
        "3b85927bfbb9b02488f455654abcc7d11374bfb409034adf414af986b5c581b9",
    ),
}


DEP_TRASH_REL = [
    Path(".DS_Store"),
    Path("APOD/_fonts_apod_scratchpad_16-08"),
    Path("Earthshine_FINAL/EXPERIMENTAL_color_no_fiable_RGB_fullres_ADU16_per_s.tif"),
    Path("Earthshine_FINAL/EXPERIMENTAL_color_no_fiable_RGB_fullres_visible.tif"),
    Path("Earthshine_FINAL/EXPERIMENTAL_color_no_fiable_RGB_fullres_visible.png"),
    Path("Earthshine_FINAL/binat2_control_SONY_2x8s_visible.tif"),
    Path("Corona_HDR_Vixen/.DS_Store"),
    Path("Corona_HDR_Vixen/hdr_vixen_countss_v1_sense_correccions.npy"),
    Path("Corona_HDR_Vixen/hdr_vixen_var_v1_sense_correccions.npy"),
    Path("Corona_HDR_Vixen/hdr_vixen_cobertura_v1_sense_correccions.npy"),
    Path("Corona_HDR_Vixen/hdr_vixen_countss_prnu_v1_amb_estrelles.npy"),
    Path("Corona_HDR_Vixen/hdr_vixen_var_prnu_v1_amb_estrelles.npy"),
    Path("Corona_HDR_Vixen/hdr_vixen_cobertura_prnu_v1_amb_estrelles.npy"),
    Path("Corona_HDR_Vixen/_productes_prnu_v1_amb_estrelles"),
]


MAIN_MOVES: list[tuple[Path, Path, str]] = [
    (DEP / "APOD", DESKTOP / "Publicacio/APOD", "publicació"),
    (
        DEP / "Earthshine_FINAL",
        DESKTOP / "Derivats/Earthshine/Earthshine_FINAL",
        "màster earthshine",
    ),
    (
        DEP / "Corona_HDR_Vixen",
        DESKTOP / "Derivats/Vixen/Corona_HDR_Vixen",
        "màster HDR Vixen",
    ),
    (
        DEP / "PROPOSTA_Normalitzacio_Exposicio_CapesTotalsV4.md",
        COORD / "Historic/PROPOSTA_Normalitzacio_Exposicio_CapesTotalsV4.md",
        "document històric",
    ),
    (
        NOSE / "Calibrated_Claude",
        DESKTOP / "Derivats/Vixen/Calibrated_Claude",
        "calibrats Vixen",
    ),
    (NOSE / "HDR4", DESKTOP / "Derivats/Vixen/HDR4", "màster HDR4"),
    (
        NOSE / "300mm_apilat_v2",
        DESKTOP / "Derivats/Sony/Apilats/300mm_apilat_v2",
        "apilat Sony v2",
    ),
    (
        NOSE / "300mm_apilat_v3",
        DESKTOP / "Derivats/Sony/Apilats/300mm_apilat_v3",
        "apilat Sony v3",
    ),
    (
        NOSE / "Earthshine_Claude",
        DESKTOP / "Derivats/Earthshine/Historic/Earthshine_Claude_Vixen",
        "earthshine històric Vixen",
    ),
    (
        NOSE / "Earthshine_Claude Sony",
        DESKTOP / "Derivats/Earthshine/Historic/Earthshine_Claude_Sony",
        "earthshine històric Sony",
    ),
    (
        NOSE / "Aplicant_Filtres.tif",
        DESKTOP / "Projecte photoshop/2-Filtres/Recursos/Base/Aplicant_Filtres.tif",
        "recurs Photoshop",
    ),
    (
        NOSE / "alineades_7648x5353",
        DESKTOP / "Projecte photoshop/2-Filtres/Recursos/Alineats/alineades_7648x5353",
        "alineats Photoshop",
    ),
    (
        NOSE / "Druckmuller_2026-08-18",
        DESKTOP / "Projecte photoshop/2-Filtres/Recursos/Druckmuller/Druckmuller_2026-08-18",
        "recursos Druckmüller",
    ),
    (
        NOSE / "SEMIFINAL3_capes",
        DESKTOP / "Projecte photoshop/2-Filtres/Recursos/Capes_SEMIFINAL3_a_10",
        "capes de filtres",
    ),
    (
        NOSE / "LLEGEIX-ME_alineades.md",
        DESKTOP / "Projecte photoshop/2-Filtres/Recursos/Alineats/LLEGEIX-ME_alineades.md",
        "documentació d'alineats",
    ),
    (
        NOSE / "observacions_skills.md",
        COORD / "Historic/observacions_skills_2026-08-22.md",
        "observacions històriques de skills",
    ),
]


CAPES_DOC_MOVES: list[tuple[str, str]] = [
    ("LLEGEIX-ME_CapesTotalsV1.md", "V1/LLEGEIX-ME_CapesTotalsV1.md"),
    ("CapesTotalsV2.manifest.json", "V2/CapesTotalsV2.manifest.json"),
    ("LLEGEIX-ME_CapesTotalsV2b.md", "V2b/LLEGEIX-ME_CapesTotalsV2b.md"),
    ("CapesTotalsV2b.manifest.json", "V2b/CapesTotalsV2b.manifest.json"),
    ("LLEGEIX-ME_CapesTotalsV3b.md", "V3b/LLEGEIX-ME_CapesTotalsV3b.md"),
    ("CapesTotalsV3b.manifest.json", "V3b/CapesTotalsV3b.manifest.json"),
    ("CapesTotalsV3b_QA", "V3b/CapesTotalsV3b_QA"),
    ("LLEGEIX-ME_CapesTotalsV3c.md", "V3c/LLEGEIX-ME_CapesTotalsV3c.md"),
    ("CapesTotalsV3c.manifest.json", "V3c/CapesTotalsV3c.manifest.json"),
    ("CapesTotalsV3c.manifest_v3c.json", "V3c/CapesTotalsV3c.manifest_v3c.json"),
    ("CapesTotalsV3c_QA", "V3c/CapesTotalsV3c_QA"),
    ("LLEGEIX-ME_CapesTotalsV4.md", "V4/LLEGEIX-ME_CapesTotalsV4.md"),
    ("CapesTotalsV4.manifest.json", "V4/CapesTotalsV4.manifest.json"),
    ("CapesTotalsV4.manifest_v4.json", "V4/CapesTotalsV4.manifest_v4.json"),
    ("CapesTotalsV4_QA", "V4/CapesTotalsV4_QA"),
    ("LLEGEIX-ME_CapesTotalsV4b.md", "V4b/LLEGEIX-ME_CapesTotalsV4b.md"),
    ("CapesTotalsV4b.manifest.json", "V4b/CapesTotalsV4b.manifest.json"),
    ("CapesTotalsV4b.manifest_v4.json", "V4b/CapesTotalsV4b.manifest_v4.json"),
    ("CapesTotalsV4b_QA", "V4b/CapesTotalsV4b_QA"),
]

CAPES_TOTALS_DOC = (
    DESKTOP / "Projecte photoshop/1-Unint Capes/Capes Totals/Documentacio i QA"
)
CAPES_INTERIORS_DOC = (
    DESKTOP / "Projecte photoshop/1-Unint Capes/Capes interiors/Documentacio i QA"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_entries(root: Path):
    """Dona fitxers regulars i symlinks sense seguir cap symlink."""
    if root.is_symlink():
        yield root
        return
    if root.is_file():
        yield root
        return
    for current, directories, filenames in os.walk(root, followlinks=False):
        base = Path(current)
        kept = []
        for name in sorted(directories):
            child = base / name
            if child.is_symlink():
                yield child
            else:
                kept.append(name)
        directories[:] = kept
        for name in sorted(filenames):
            yield base / name


def summary(path: Path) -> dict[str, object]:
    metadata = path.lstat()
    regular = 0
    symlinks = 0
    logical_bytes = 0
    for item in iter_entries(path):
        item_meta = item.lstat()
        if stat.S_ISREG(item_meta.st_mode):
            regular += 1
            logical_bytes += item_meta.st_size
        elif stat.S_ISLNK(item_meta.st_mode):
            symlinks += 1
    return {
        "path": str(path),
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
        "regular_files": regular,
        "symlinks": symlinks,
        "logical_bytes": logical_bytes,
    }


def raw_snapshot() -> dict[str, object]:
    records: list[tuple[str, int, int]] = []
    counts = {".arw": 0, ".cr3": 0}
    for root in (DESKTOP / "300mm A7RIIIA", DESKTOP / "Vixen R6III"):
        for item in iter_entries(root):
            try:
                meta = item.lstat()
            except FileNotFoundError:
                raise SystemExit(f"RAW desaparegut durant l'inventari: {item}")
            suffix = item.suffix.lower()
            if stat.S_ISREG(meta.st_mode) and suffix in counts:
                counts[suffix] += 1
                records.append((item.relative_to(DESKTOP).as_posix(), meta.st_ino, meta.st_size))
    digest = hashlib.sha256()
    for relative, inode, size in sorted(records):
        digest.update(f"{relative}\t{inode}\t{size}\n".encode("utf-8"))
    return {"counts": counts, "path_inode_size_sha256": digest.hexdigest()}


def tree_regular_hashes(root: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for item in iter_entries(root):
        # El backup ExFAT materialitza els extended attributes de macOS com a
        # sidecars AppleDouble; no són contingut del projecte.
        if item.name.startswith("._") or item.name == ".DS_Store":
            continue
        meta = item.lstat()
        if stat.S_ISREG(meta.st_mode):
            values[item.relative_to(root).as_posix()] = sha256_file(item)
    return values


def assert_same_tree(left: Path, right: Path, label: str) -> None:
    left_hashes = tree_regular_hashes(left)
    right_hashes = tree_regular_hashes(right)
    if left_hashes != right_hashes:
        raise SystemExit(f"No coincideixen byte a byte: {label}: {left} <> {right}")


def assert_backup_copy(source: Path, backup_source: Path) -> None:
    if not source.exists() or not backup_source.exists():
        raise SystemExit(f"Còpia absent per validar: {source} <> {backup_source}")
    if source.is_dir():
        assert_same_tree(source, backup_source, source.name)
        return
    if source.stat().st_size != backup_source.stat().st_size:
        raise SystemExit(f"Mida divergent contra backup: {source}")
    if sha256_file(source) != sha256_file(backup_source):
        raise SystemExit(f"SHA divergent contra backup: {source}")


def assert_topology() -> None:
    if not DEP.is_dir() or not NOSE.is_dir():
        raise SystemExit("Falta algun dels dos directoris d'origen")
    dep_names = {child.name for child in DEP.iterdir()}
    nose_names = {child.name for child in NOSE.iterdir()}
    if dep_names != EXPECTED_DEP_TOP:
        raise SystemExit(
            "Topologia inesperada a Deprecat:\n"
            f"  falten={sorted(EXPECTED_DEP_TOP - dep_names)}\n"
            f"  sobren={sorted(dep_names - EXPECTED_DEP_TOP)}"
        )
    if nose_names != EXPECTED_NOSE_TOP:
        raise SystemExit(
            "Topologia inesperada a No se que fa això aquí:\n"
            f"  falten={sorted(EXPECTED_NOSE_TOP - nose_names)}\n"
            f"  sobren={sorted(nose_names - EXPECTED_NOSE_TOP)}"
        )


def all_leaf_destinations() -> list[Path]:
    destinations = [dst for _, dst, _ in MAIN_MOVES]
    destinations.extend(CAPES_TOTALS_DOC / relative for _, relative in CAPES_DOC_MOVES)
    destinations.extend(
        [
            CAPES_INTERIORS_DOC / "V4/LLEGEIX-ME_CapesInteriorsV4.md",
            CAPES_INTERIORS_DOC / "V4/CapesInteriorsV4_QA",
            CAPES_INTERIORS_DOC / "V5/LLEGEIX-ME_CapesInteriorsV5.md",
            DESKTOP / "Derivats/Astrometria/Estrelles",
        ]
    )
    return destinations


def assert_destinations_absent() -> None:
    seen: set[Path] = set()
    for destination in all_leaf_destinations():
        if destination in seen:
            raise SystemExit(f"Destinació duplicada al pla: {destination}")
        seen.add(destination)
        if destination.exists() or destination.is_symlink():
            raise SystemExit(f"Destinació ja existent; no es pot sobreescriure: {destination}")
    if TRASH_BATCH.exists() or TRASH_BATCH.is_symlink():
        raise SystemExit(f"El lot de Paperera ja existeix: {TRASH_BATCH}")
    if RECEIPT_DIR.exists():
        raise SystemExit(f"El directori de rebut ja existeix: {RECEIPT_DIR}")


def assert_claim() -> None:
    try:
        owner = json.loads(LOCK_OWNER.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise SystemExit(f"SERIAL_WRITES absent o invàlid: {error}") from error
    if owner.get("claim_id") != CLAIM_ID:
        raise SystemExit(f"SERIAL_WRITES no és d'aquesta operació: {owner}")


def verify_restoration_sources() -> None:
    live_dir = DEP / "Corona_HDR_Vixen"
    backup_dir = BACKUP / "Corona_HDR_Vixen"
    for name, (expected_size, expected_sha) in RESTORE_TIFFS.items():
        source = backup_dir / name
        destination = live_dir / name
        if not source.is_file():
            raise SystemExit(f"TIFF absent al backup: {source}")
        if destination.exists() or destination.is_symlink():
            raise SystemExit(f"El TIFF a restaurar ja existeix: {destination}")
        if source.stat().st_size != expected_size or sha256_file(source) != expected_sha:
            raise SystemExit(f"Mida o SHA inesperat al TIFF de backup: {source}")


def verify_safe_trash_candidates() -> None:
    # Poda de Deprecat: tot és al backup amb el mateix contingut.
    for relative in DEP_TRASH_REL:
        source = DEP / relative
        if relative.name == ".DS_Store":
            if not source.exists():
                raise SystemExit(f".DS_Store esperat absent: {source}")
            continue
        assert_backup_copy(source, BACKUP / relative)

    old_psb = NOSE / "CapesInteriorsV4.psb.anterior-disseny-claude"
    if sha256_file(old_psb) != "caaaac2007e3c47fb9bdaf82514b284e95d5f214a6dda8b5b944b3386c719fab":
        raise SystemExit("SHA inesperat al PSB antic")
    assert_backup_copy(
        old_psb,
        BACKUP / "Projecte photoshop/1-Unint Capes/CapesInteriorsV4.psb.anterior-disseny-claude",
    )

    verify_work = NOSE / "HDR4/revelat_v4/v4/QA/verify_work"
    build_work = NOSE / "HDR4/revelat_v4/v4/work/build"
    assert_same_tree(verify_work, build_work, "verify_work duplicat")

    # La prova de 22/22 només aporta registres nous. La resta ha de tenir una
    # còpia byte-idèntica a la primera prova abans de retirar-ne cap branca.
    first = NOSE / "_prova_skill"
    second = NOSE / "_prova_skill_estrelles"
    for item in iter_entries(second):
        meta = item.lstat()
        if not stat.S_ISREG(meta.st_mode):
            continue
        relative = item.relative_to(second)
        if item.name == ".DS_Store":
            continue
        if relative == Path("pipeline_estrelles_prova.log"):
            continue
        if relative.parts[:2] == ("Estrelles_work", "_registres"):
            continue
        counterpart = first / relative
        if not counterpart.is_file():
            raise SystemExit(f"Fitxer únic no promogut a la prova 22/22: {relative}")
        if meta.st_size != counterpart.stat().st_size or sha256_file(item) != sha256_file(counterpart):
            raise SystemExit(f"Fitxer divergent no promogut a la prova 22/22: {relative}")

    # El romanent de la primera prova que anirà a Paperera queda íntegre al backup.
    for name in ("APOD", "Corona_HDR_Vixen", "HDR4"):
        assert_backup_copy(first / name, BACKUP / "_prova_skill" / name)


def preflight() -> dict[str, object]:
    assert_claim()
    assert_topology()
    assert_destinations_absent()
    verify_restoration_sources()
    verify_safe_trash_candidates()
    return {
        "dep_before": summary(DEP),
        "nose_before": summary(NOSE),
        "raw_before": raw_snapshot(),
    }


class Journal:
    def __init__(self, baseline: dict[str, object]) -> None:
        self.data: dict[str, object] = {
            "schema": 1,
            "claim_id": CLAIM_ID,
            "desktop_root": str(DESKTOP),
            "backup_root_read_only": str(BACKUP),
            "trash_batch": str(TRASH_BATCH),
            "baseline": baseline,
            "operations": [],
            "restored": [],
            "validation": {},
        }

    def save(self) -> None:
        RECEIPT_DIR.mkdir(parents=True, exist_ok=True)
        target = RECEIPT_DIR / "operation_receipt.json"
        temporary = RECEIPT_DIR / ".operation_receipt.json.tmp"
        temporary.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, target)

    def add_operation(self, record: dict[str, object]) -> None:
        operations = self.data["operations"]
        assert isinstance(operations, list)
        operations.append(record)
        self.save()

    def add_restored(self, record: dict[str, object]) -> None:
        restored = self.data["restored"]
        assert isinstance(restored, list)
        restored.append(record)
        self.save()

    @classmethod
    def load_existing(cls) -> "Journal":
        target = RECEIPT_DIR / "operation_receipt.json"
        try:
            data = json.loads(target.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError) as error:
            raise SystemExit(f"No es pot reprendre: rebut absent o invàlid: {error}") from error
        if data.get("claim_id") != CLAIM_ID:
            raise SystemExit("No es pot reprendre: claim_id divergent al rebut")
        baseline = data.get("baseline")
        if not isinstance(baseline, dict):
            raise SystemExit("No es pot reprendre: baseline absent al rebut")
        journal = cls(baseline)
        journal.data = data
        return journal


def move_no_clobber(source: Path, destination: Path, category: str, journal: Journal) -> None:
    if not source.exists() and not source.is_symlink():
        raise SystemExit(f"Origen absent: {source}")
    if destination.exists() or destination.is_symlink():
        raise SystemExit(f"Destinació ocupada: {destination}")
    before = summary(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.rename(source, destination)
    after = summary(destination)
    invariant_keys = ("device", "inode", "regular_files", "symlinks", "logical_bytes")
    if any(before[key] != after[key] for key in invariant_keys):
        raise SystemExit(f"Invariants trencats després de moure {source} -> {destination}")
    journal.add_operation(
        {
            "kind": "move",
            "category": category,
            "source": str(source),
            "destination": str(destination),
            "before": before,
            "after": after,
        }
    )


def move_to_trash(source: Path, relative: Path, category: str, journal: Journal) -> None:
    destination = TRASH_BATCH / relative
    move_no_clobber(source, destination, f"Paperera: {category}", journal)


def restore_tiffs(journal: Journal) -> None:
    backup_dir = BACKUP / "Corona_HDR_Vixen"
    live_dir = DEP / "Corona_HDR_Vixen"
    for name, (expected_size, expected_sha) in RESTORE_TIFFS.items():
        source = backup_dir / name
        destination = live_dir / name
        shutil.copy2(source, destination, follow_symlinks=False)
        observed_sha = sha256_file(destination)
        if destination.stat().st_size != expected_size or observed_sha != expected_sha:
            raise SystemExit(f"Restauració TIFF no vàlida: {destination}")
        journal.add_restored(
            {
                "source": str(source),
                "destination": str(destination),
                "bytes": expected_size,
                "sha256": observed_sha,
            }
        )


def move_ds_store_outside_tests(journal: Journal) -> None:
    candidates: list[Path] = []
    for item in iter_entries(NOSE):
        if item.name != ".DS_Store":
            continue
        relative = item.relative_to(NOSE)
        if relative.parts and relative.parts[0] in {"_prova_skill", "_prova_skill_estrelles"}:
            continue
        candidates.append(item)
    # N'hi ha deu en total: sis viatgen dins les dues proves i quatre es
    # retiren ara. L'auditoria preliminar n'havia comptat set; el preflight
    # executable en resol la cardinalitat exacta sense seguir symlinks.
    if len(candidates) != 4:
        raise SystemExit(f"S'esperaven 4 .DS_Store fora de proves; n'hi ha {len(candidates)}")
    for source in sorted(candidates):
        move_to_trash(
            source,
            Path("No se que fa això aquí") / source.relative_to(NOSE),
            "metadata Finder",
            journal,
        )


def promote_astrometry(journal: Journal) -> None:
    base = DESKTOP / "Derivats/Astrometria/Estrelles"
    move_no_clobber(NOSE / "Estrelles", base, "resultats astromètrics inicials", journal)

    first = NOSE / "_prova_skill"
    second = NOSE / "_prova_skill_estrelles"
    move_no_clobber(
        first / "Estrelles_work",
        base / "Work_2026-08-17",
        "work astromètric necessari",
        journal,
    )
    move_no_clobber(
        first / "Estrelles",
        base / "Resultats_acceptacio_2026-08-17",
        "resultats astromètrics acceptats",
        journal,
    )

    prova_receipts = base / "Rebuts/prova_skill_2026-08-17"
    for name in (
        "pipeline_prova.log",
        "prediccio_prova.log",
        "xmatch_fotometria.log",
        "xmatch_prova_oficial.log",
        "xmatch_prova_oficial_phot2.log",
    ):
        move_no_clobber(first / name, prova_receipts / name, "rebut de prova astromètrica", journal)

    experiments = base / "Proves_2026-08-17"
    for name in ("Estrelles_work_xmatch_fotometria", "Estrelles_xmatch_fotometria"):
        move_no_clobber(first / name, experiments / name, "prova astromètrica preservada", journal)

    accepted_receipts = base / "Rebuts/acceptacio_22de22"
    move_no_clobber(
        second / "Estrelles_work/_registres",
        accepted_receipts / "registres",
        "registres d'acceptació 22/22",
        journal,
    )
    move_no_clobber(
        second / "pipeline_estrelles_prova.log",
        accepted_receipts / "pipeline_estrelles_prova.log",
        "rebut d'acceptació 22/22",
        journal,
    )


def move_capes_documentation(journal: Journal) -> None:
    for source_name, destination_relative in CAPES_DOC_MOVES:
        move_no_clobber(
            NOSE / source_name,
            CAPES_TOTALS_DOC / destination_relative,
            "documentació i QA Capes Totals",
            journal,
        )

    interior_moves = [
        (
            NOSE / "LLEGEIX-ME_CapesInteriorsV4.md",
            CAPES_INTERIORS_DOC / "V4/LLEGEIX-ME_CapesInteriorsV4.md",
        ),
        (NOSE / "CapesInteriorsV4_QA", CAPES_INTERIORS_DOC / "V4/CapesInteriorsV4_QA"),
        (
            NOSE / "LLEGEIX-ME_CapesInteriorsV5.md",
            CAPES_INTERIORS_DOC / "V5/LLEGEIX-ME_CapesInteriorsV5.md",
        ),
    ]
    for source, destination in interior_moves:
        move_no_clobber(source, destination, "documentació i QA Capes Interiors", journal)


def execute(baseline: dict[str, object]) -> None:
    RECEIPT_DIR.mkdir(parents=True)
    TRASH_BATCH.mkdir(mode=0o700)
    journal = Journal(baseline)
    journal.save()

    restore_tiffs(journal)

    for relative in DEP_TRASH_REL:
        move_to_trash(
            DEP / relative,
            Path("Deprecat") / relative,
            "intermedi supersedit o no fiable",
            journal,
        )

    finish_execute(baseline, journal)


def finish_execute(baseline: dict[str, object], journal: Journal) -> None:
    """Continua des del primer checkpoint complet i tanca la validació."""

    move_ds_store_outside_tests(journal)
    move_to_trash(
        NOSE / "CapesInteriorsV4.psb.anterior-disseny-claude",
        Path("No se que fa això aquí/CapesInteriorsV4.psb.anterior-disseny-claude"),
        "PSB antic declarat esborrable",
        journal,
    )
    move_to_trash(
        NOSE / "HDR4/revelat_v4/v4/QA/verify_work",
        Path("No se que fa això aquí/HDR4/revelat_v4/v4/QA/verify_work"),
        "duplicat exacte de work/build",
        journal,
    )

    promote_astrometry(journal)
    move_to_trash(
        NOSE / "_prova_skill_estrelles",
        Path("No se que fa això aquí/_prova_skill_estrelles"),
        "prova duplicada després de preservar rebuts 22/22",
        journal,
    )
    move_to_trash(
        NOSE / "_prova_skill",
        Path("No se que fa això aquí/_prova_skill"),
        "prova reproduïble després de preservar astrometria",
        journal,
    )

    for source, destination, category in MAIN_MOVES:
        move_no_clobber(source, destination, category, journal)
    move_capes_documentation(journal)

    if any(DEP.iterdir()) or any(NOSE.iterdir()):
        raise SystemExit(
            f"No s'eliminen els contenidors perquè no són buits: "
            f"Deprecat={list(DEP.iterdir())}, NoSe={list(NOSE.iterdir())}"
        )
    DEP.rmdir()
    NOSE.rmdir()
    journal.add_operation(
        {
            "kind": "remove_empty_containers",
            "paths": [str(DEP), str(NOSE)],
            "note": "Només s'han eliminat després de comprovar que eren buits.",
        }
    )

    raw_after = raw_snapshot()
    if raw_after != baseline["raw_before"]:
        raise SystemExit(f"La instantània RAW ha canviat: {baseline['raw_before']} -> {raw_after}")

    restored_checks = {}
    canonical_corona = DESKTOP / "Derivats/Vixen/Corona_HDR_Vixen"
    for name, (expected_size, expected_sha) in RESTORE_TIFFS.items():
        path = canonical_corona / name
        observed = sha256_file(path)
        if path.stat().st_size != expected_size or observed != expected_sha:
            raise SystemExit(f"TIFF restaurat divergent al destí final: {path}")
        restored_checks[name] = observed

    validation = {
        "dep_absent": not DEP.exists(),
        "nose_absent": not NOSE.exists(),
        "raw_after": raw_after,
        "trash": summary(TRASH_BATCH),
        "restored_tiffs_sha256": restored_checks,
        "backup_tiffs_still_present": all(
            (BACKUP / "Corona_HDR_Vixen" / name).is_file() for name in RESTORE_TIFFS
        ),
        "new_jpeg_generated": False,
    }
    journal.data["validation"] = validation
    journal.save()
    write_receipt_tables(journal)
    print(json.dumps(validation, ensure_ascii=False, indent=2, sort_keys=True))


def verify_resume_checkpoint(journal: Journal) -> dict[str, object]:
    """Valida l'únic checkpoint admès després de l'aturada fail-fast."""
    assert_claim()
    if not TRASH_BATCH.is_dir() or not RECEIPT_DIR.is_dir():
        raise SystemExit("No es pot reprendre: manca el lot de Paperera o el rebut")
    baseline = journal.data.get("baseline")
    operations = journal.data.get("operations")
    restored = journal.data.get("restored")
    if not isinstance(baseline, dict) or not isinstance(operations, list) or not isinstance(restored, list):
        raise SystemExit("No es pot reprendre: estructura de rebut invàlida")
    if len(operations) != len(DEP_TRASH_REL) or len(restored) != len(RESTORE_TIFFS):
        raise SystemExit(
            f"Checkpoint inesperat: operations={len(operations)}, restored={len(restored)}"
        )
    if {child.name for child in DEP.iterdir()} != EXPECTED_DEP_TOP - {".DS_Store"}:
        raise SystemExit("No es pot reprendre: topologia parcial inesperada a Deprecat")
    if {child.name for child in NOSE.iterdir()} != EXPECTED_NOSE_TOP:
        raise SystemExit("No es pot reprendre: topologia parcial inesperada a No se que fa això aquí")
    for relative in DEP_TRASH_REL:
        source = DEP / relative
        destination = TRASH_BATCH / "Deprecat" / relative
        if source.exists() or source.is_symlink() or not destination.exists():
            raise SystemExit(f"Checkpoint inconsistent per a {relative}")
    for name, (expected_size, expected_sha) in RESTORE_TIFFS.items():
        destination = DEP / "Corona_HDR_Vixen" / name
        if not destination.is_file():
            raise SystemExit(f"TIFF restaurat absent al checkpoint: {destination}")
        if destination.stat().st_size != expected_size or sha256_file(destination) != expected_sha:
            raise SystemExit(f"TIFF restaurat divergent al checkpoint: {destination}")
    for destination in all_leaf_destinations():
        if destination.exists() or destination.is_symlink():
            raise SystemExit(f"Destinació ocupada abans de reprendre: {destination}")
    if not (NOSE / "CapesInteriorsV4.psb.anterior-disseny-claude").is_file():
        raise SystemExit("PSB antic absent abans de reprendre")
    if not (NOSE / "HDR4/revelat_v4/v4/QA/verify_work").is_dir():
        raise SystemExit("verify_work absent abans de reprendre")
    raw_before = baseline.get("raw_before")
    if raw_snapshot() != raw_before:
        raise SystemExit("La instantània RAW ha canviat abans de reprendre")
    return baseline


def write_receipt_tables(journal: Journal) -> None:
    operations = journal.data["operations"]
    assert isinstance(operations, list)
    with (RECEIPT_DIR / "moves.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["kind", "category", "source", "destination", "files", "symlinks", "bytes"])
        for record in operations:
            if record.get("kind") != "move":
                continue
            before = record["before"]
            assert isinstance(before, dict)
            writer.writerow(
                [
                    record["kind"],
                    record["category"],
                    record["source"],
                    record["destination"],
                    before["regular_files"],
                    before["symlinks"],
                    before["logical_bytes"],
                ]
            )

    with (RECEIPT_DIR / "restored_tiffs.tsv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
        writer.writerow(["sha256", "bytes", "source", "destination"])
        restored = journal.data["restored"]
        assert isinstance(restored, list)
        for record in restored:
            writer.writerow([record["sha256"], record["bytes"], record["source"], record["destination"]])

    validation = journal.data["validation"]
    assert isinstance(validation, dict)
    trash = validation["trash"]
    assert isinstance(trash, dict)
    (RECEIPT_DIR / "VALIDATION.md").write_text(
        "\n".join(
            [
                "# Validació — neteja de `Deprecat` i `No se que fa això aquí`",
                "",
                "**PASS.** Els dos contenidors provisionals han desaparegut després de quedar buits.",
                "",
                f"- Lot recuperable de Paperera: `{TRASH_BATCH}`",
                f"- Fitxers regulars a la Paperera: {trash['regular_files']}",
                f"- Symlinks a la Paperera: {trash['symlinks']}",
                f"- Bytes lògics a la Paperera: {trash['logical_bytes']}",
                f"- TIFF restaurats i verificats: {len(RESTORE_TIFFS)}/6",
                f"- RAW camera-root abans/després: `{baseline_text(journal)}`",
                "- JPEG nous generats: 0",
                "- La Paperera no s'ha buidat; la retirada continua essent reversible.",
                "",
                "El detall complet és a `operation_receipt.json`, `moves.tsv` i `restored_tiffs.tsv`.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def baseline_text(journal: Journal) -> str:
    baseline = journal.data["baseline"]
    assert isinstance(baseline, dict)
    raw = baseline["raw_before"]
    assert isinstance(raw, dict)
    counts = raw["counts"]
    assert isinstance(counts, dict)
    return f"ARW {counts['.arw']}, CR3 {counts['.cr3']}, fingerprint {raw['path_inode_size_sha256']}"


def print_plan(baseline: dict[str, object]) -> None:
    print("PRE-FLIGHT PASS")
    print(json.dumps(baseline, ensure_ascii=False, indent=2, sort_keys=True))
    print("\nDestins principals:")
    for source, destination, category in MAIN_MOVES:
        print(f"- [{category}] {source} -> {destination}")
    print(f"- [astrometria] {NOSE / 'Estrelles'} -> {DESKTOP / 'Derivats/Astrometria/Estrelles'}")
    print(f"- [QA] {len(CAPES_DOC_MOVES) + 3} elements -> documentació Photoshop")
    print(f"- [Paperera recuperable] -> {TRASH_BATCH}")
    print(f"- [Rebut] -> {RECEIPT_DIR}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--plan", action="store_true", help="preflight read-only")
    mode.add_argument("--execute", action="store_true", help="executa el pla validat")
    mode.add_argument("--resume", action="store_true", help="reprèn el checkpoint registrat")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.resume:
        journal = Journal.load_existing()
        baseline = verify_resume_checkpoint(journal)
        finish_execute(baseline, journal)
        return 0
    baseline = preflight()
    if args.plan:
        print_plan(baseline)
        return 0
    execute(baseline)
    return 0


if __name__ == "__main__":
    sys.exit(main())
