"""Builder de ``CapesTotalsV2b``: el V2 de Codex regenerat amb la reixa corregida A LA BASE.

Importa ``build_capes_totals_v2`` (clonació crua de LayerRecord/ChannelData de
Corretgint2 i CapesTotalsV1, compositor RGBA4, promoció no-clobber) i hi afegeix
``--offsets``: un JSON ``{layer_id: [dx, dy]}`` que desplaça **només les
metadades** de posició —top/left/bottom/right del LayerRecord i de la MaskData
(i els rectangles «real» de la màscara si n'hi ha)— pel mateix vector enter.
Cap píxel es remostreja ni es toca: els canals comprimits (RGB, alfa i màscara)
queden byte-idèntics a la font i es verifiquen abans i després d'aplicar-ho.

Decisió de Pere (research/87 §9): corregir tota la reixa a la base, cap capa
compensadora, i la capa 01 passa a opacitat 100 % («Normal 100 %, tot via
màscara»; la màscara es re-derivarà en una fase posterior).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Mapping

from psd_tools.constants import ChannelID

import build_capes_totals_v2 as base


def load_offsets(path: Path) -> dict[int, tuple[int, int]]:
    """Llegeix ``{"id": [dx, dy]}``; només IDs de sortida i enters."""

    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"no existeix el fitxer d'offsets: {path}")
    with path.open("r", encoding="utf-8") as stream:
        raw = json.load(stream)
    if not isinstance(raw, dict):
        raise TypeError("--offsets ha de ser un objecte JSON {layer_id: [dx, dy]}")
    offsets: dict[int, tuple[int, int]] = {}
    for key, value in raw.items():
        layer_id = base._layer_id_from_json_key(key, field="offsets")
        if layer_id not in base.OUTPUT_LAYER_IDS:
            raise ValueError(f"offsets: layer_id={layer_id} no forma part de la sortida")
        if (
            not isinstance(value, list)
            or len(value) != 2
            or any(type(v) is not int for v in value)
        ):
            raise TypeError(f"offsets[{layer_id}] ha de ser [dx, dy] amb enters")
        if value == [0, 0]:
            continue
        offsets[layer_id] = (value[0], value[1])
    return offsets


def _shift_rect(obj, dx: int, dy: int, *, prefix: str = "") -> None:
    for name, delta in (("top", dy), ("bottom", dy), ("left", dx), ("right", dx)):
        attr = prefix + name
        value = getattr(obj, attr, None)
        if value is None:
            continue
        setattr(obj, attr, int(value) + delta)


def apply_offsets(document, offsets: Mapping[int, tuple[int, int]]) -> dict[str, object]:
    """Desplaça les metadades de posició; retorna el rebut abans/després per capa."""

    by_id = {layer.layer_id: layer for layer in document}
    receipt: dict[str, object] = {}
    for layer_id, (dx, dy) in offsets.items():
        layer = by_id[layer_id]
        record = layer._record
        before_channels = base.raw_channel_fingerprints(layer)
        before = {
            "bbox": [record.left, record.top, record.right, record.bottom],
            "mask_bbox": None,
        }
        mask = record.mask_data
        if mask is not None:
            before["mask_bbox"] = [mask.left, mask.top, mask.right, mask.bottom]
        _shift_rect(record, dx, dy)
        if mask is not None:
            _shift_rect(mask, dx, dy)
            if getattr(mask, "real_top", None) is not None:
                _shift_rect(mask, dx, dy, prefix="real_")
        if hasattr(layer, "_bbox"):
            layer._bbox = None
        after = {
            "bbox": [record.left, record.top, record.right, record.bottom],
            "mask_bbox": None
            if mask is None
            else [mask.left, mask.top, mask.right, mask.bottom],
        }
        if (
            after["bbox"][2] - after["bbox"][0] != before["bbox"][2] - before["bbox"][0]
            or after["bbox"][3] - after["bbox"][1] != before["bbox"][3] - before["bbox"][1]
        ):
            raise AssertionError(f"layer_id={layer_id}: la mida del registre ha canviat")
        if base.raw_channel_fingerprints(layer) != before_channels:
            raise AssertionError(f"layer_id={layer_id}: els canals han canviat en desplaçar")
        receipt[str(layer_id)] = {
            "dx": dx,
            "dy": dy,
            "before": before,
            "after": after,
            "channels_sha256_unchanged": True,
        }
    document._mark_updated()
    return receipt


def materialize_v2b(
    *,
    corretgint2_path: Path,
    capes_totals_v1_path: Path,
    config_path: Path,
    mask_dir: Path,
    offsets_path: Path,
    work_dir: Path,
    candidate_path: Path,
    manifest_path: Path,
) -> dict[str, object]:
    candidate_path = base._candidate_path_without_clobber(candidate_path)
    manifest_parent = manifest_path.expanduser().parent.resolve()
    manifest_path = manifest_parent / manifest_path.name
    if not manifest_parent.is_dir():
        raise FileNotFoundError(f"no existeix el directori del manifest: {manifest_parent}")
    if manifest_path.exists() or manifest_path.is_symlink():
        raise FileExistsError(f"no se sobreescriu el manifest: {manifest_path}")
    work_dir = work_dir.resolve()
    if not work_dir.is_dir():
        raise FileNotFoundError("--work-dir ha de ser un directori existent")

    offsets = load_offsets(offsets_path)
    declaration = base.load_final_declaration(config_path, mask_dir)
    document, manifest = base.build_selected_document(corretgint2_path, capes_totals_v1_path)

    original_all = {layer.layer_id: base.raw_channel_fingerprints(layer) for layer in document}
    base.apply_final_declaration(document, declaration)
    offsets_receipt = apply_offsets(document, offsets)
    for layer in document:
        if base.raw_channel_fingerprints(layer) != original_all[layer.layer_id]:
            raise AssertionError(f"layer_id={layer.layer_id}: canal cru alterat")
        if layer.blend_mode != base.BlendMode.NORMAL or layer.fill_opacity != 255:
            raise AssertionError(f"layer_id={layer.layer_id}: no és Normal/fill 100 %")
        if layer.opacity != 255:
            raise AssertionError(f"layer_id={layer.layer_id}: opacitat {layer.opacity} != 255")

    base.finalize_lr16(document)
    float_path = work_dir / "merged_float32.npy"
    rgba_path = work_dir / "merged_rgba16.npy"
    rgba = base.compose_normal_rgba4_to_npy(
        document, document._record.header, float_path, rgba_path
    )
    merged_hashes = base.set_merged_rgba4(document, rgba)
    manifest.update(
        {
            "status": "FINAL_CANDIDATE_READY_TO_SAVE",
            "variant": "V2b",
            "final_declaration": base.final_declaration_manifest(declaration),
            "offsets": {
                "path": str(offsets_path.resolve()),
                "sha256": base.sha256_file(offsets_path),
                "applied": offsets_receipt,
                "semantics": "metadades: LayerRecord i MaskData desplaçats pel mateix vector enter; cap píxel remostrejat",
            },
            "visible_layer_ids": [layer.layer_id for layer in document if layer.visible],
            "layer_state": {
                str(layer.layer_id): {
                    "name": layer.name,
                    "opacity": layer.opacity,
                    "visible": layer.visible,
                    "blend_mode": layer.blend_mode.value.decode("ascii"),
                    "fill_opacity": layer.fill_opacity,
                    "bbox": list(layer.bbox),
                    "mask_bbox": None
                    if layer._record.mask_data is None
                    else [
                        layer._record.mask_data.left,
                        layer._record.mask_data.top,
                        layer._record.mask_data.right,
                        layer._record.mask_data.bottom,
                    ],
                    "channels": base.raw_channel_fingerprints(layer),
                }
                for layer in document
            },
            "modified_mask_ids": [],
            "protected_mask_ids": sorted(base.OUTPUT_LAYER_IDS),
            "merged_status": "RGBA4_SET",
            "merged_rgba16_npy": {
                "path": str(rgba_path),
                "sha256": base.sha256_file(rgba_path),
                "channel_sha256": merged_hashes,
            },
            "filters_selected": [],
        }
    )
    candidate_receipt = base.save_candidate_no_clobber(
        document, candidate_path, expected_layer_ids=base.OUTPUT_LAYER_IDS
    )
    manifest.update(
        {
            "status": "FINAL_CANDIDATE_SAVED",
            "psb_saved": True,
            "candidate": candidate_receipt,
            "manifest_path": str(manifest_path),
        }
    )
    base.write_json_no_clobber(manifest_path, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Materialització fail-closed de CapesTotalsV2b (reixa corregida a la base).")
    parser.add_argument("--corretgint2", type=Path, default=base.DEFAULT_CORRETGINT2)
    parser.add_argument("--capes-totals-v1", type=Path, default=base.DEFAULT_CAPES_TOTALS_V1)
    parser.add_argument("--final-config", type=Path, required=True)
    parser.add_argument("--mask-dir", type=Path, required=True, help="directori existent (buit: cap màscara es substitueix)")
    parser.add_argument("--offsets", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = materialize_v2b(
        corretgint2_path=args.corretgint2,
        capes_totals_v1_path=args.capes_totals_v1,
        config_path=args.final_config,
        mask_dir=args.mask_dir,
        offsets_path=args.offsets,
        work_dir=args.work_dir,
        candidate_path=args.candidate,
        manifest_path=args.manifest,
    )
    print(json.dumps({k: manifest[k] for k in ("status", "candidate", "offsets", "visible_layer_ids")}, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
