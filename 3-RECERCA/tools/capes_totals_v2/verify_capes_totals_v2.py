"""Verificació estructural i de bytes per al preflight de CapesTotalsV2.

Sense ``--candidate`` valida exclusivament l'arbre construït en memòria pel
builder. Amb ``--candidate`` pot auditar un PSB futur, però aquest fitxer no el
crea ni el modifica. ``--self-test`` cobreix clonació raw, màscara u16,
``Lr16``, ``Mt16`` i merged RGBA4; el round-trip d'escriptura usa exclusivament
un PSB sintètic dins ``TemporaryDirectory``.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import sys
import tempfile
from pathlib import Path
from typing import Iterable

import numpy as np
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, ChannelID, Compression, Resource, Tag
from psd_tools.psd.tagged_blocks import TaggedBlocks


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_capes_totals_v2 as build  # noqa: E402

sys.path.insert(0, str(HERE.parent / "capes_interiors_v4"))
from psb_utils import add_mask16, add_pixel_layer, new_psb  # noqa: E402


def layer_record_sha256(layer, *, version: int = 2) -> str:
    stream = io.BytesIO()
    layer._record.write(stream, encoding="macroman", version=version)
    return hashlib.sha256(stream.getvalue()).hexdigest()


def _mask_roundtrip_metadata(layer, header) -> dict[str, object] | None:
    mask, mask_data = build._decoded_mask_u16(layer, header)
    if mask is None or mask_data is None:
        return None
    return {
        "bbox": [mask_data.left, mask_data.top, mask_data.right, mask_data.bottom],
        "background_color": mask_data.background_color,
        "dtype": str(mask.dtype),
        "shape": list(mask.shape),
        "min": int(mask.min()),
        "max": int(mask.max(initial=0)),
        "nonzero": int(np.count_nonzero(mask)),
        "decoded_sha256": build.sha256_u16_be(mask),
    }


def expected_source_layers(c2: PSDImage, ct1: PSDImage) -> dict[int, object]:
    c2_by_id = {layer.layer_id: layer for layer in c2}
    ct1_by_id = {layer.layer_id: layer for layer in ct1}
    result = {
        layer_id: c2_by_id[layer_id] for layer_id in build.CORRETGINT2_LAYER_IDS
    }
    result.update(
        {
            layer_id: ct1_by_id[layer_id]
            for layer_id in build.CAPES_TOTALS_SOURCE_IDS
        }
    )
    return result


def _expected_visibility(
    source_layers: dict[int, object],
    through_layer_id: int | None,
) -> dict[int, bool]:
    if through_layer_id is None:
        return {
            layer_id: bool(source_layers[layer_id].visible)
            for layer_id in build.OUTPUT_LAYER_IDS
        }
    stop = build.OUTPUT_LAYER_IDS.index(through_layer_id)
    return {
        layer_id: index <= stop
        for index, layer_id in enumerate(build.OUTPUT_LAYER_IDS)
    }


def verify_selected_document(
    document: PSDImage,
    c2: PSDImage,
    ct1: PSDImage,
    *,
    through_layer_id: int | None = None,
    modified_mask_ids: Iterable[int] = (),
    final_declaration: dict[str, object] | None = None,
    expect_merged_rgba4: bool = False,
) -> dict[str, object]:
    if final_declaration is not None and through_layer_id is not None:
        raise ValueError("final_declaration no es combina amb through_layer_id")
    declared_masks = (
        set(final_declaration["masks"]) if final_declaration is not None else set()
    )
    modified_masks = set(modified_mask_ids).union(declared_masks)
    unknown = modified_masks.difference(build.OUTPUT_LAYER_IDS)
    if unknown:
        raise AssertionError(f"modified_mask_ids desconeguts: {sorted(unknown)}")

    header = document._record.header
    actual_header = (
        header.version,
        header.depth,
        header.channels,
        document.width,
        document.height,
        int(document.color_mode),
    )
    expected_header = (2, 16, 4, build.WIDTH, build.HEIGHT, 3)
    if actual_header != expected_header:
        raise AssertionError(
            f"capçalera seleccionada inesperada: {actual_header} != {expected_header}"
        )

    layer_mask = document._record.layer_and_mask_information
    tags = build.document_layer_tags(document)
    if Tag.LAYER_16 not in tags:
        raise AssertionError("falta Lr16")
    if Tag.SAVING_MERGED_TRANSPARENCY16 not in tags:
        raise AssertionError("falta Mt16")
    if layer_mask.layer_info is None or layer_mask.layer_info.layer_count != 0:
        raise AssertionError("la secció clàssica de capes no és buida")

    icc = document.image_resources.get_data(Resource.ICC_PROFILE)
    if hashlib.sha256(icc).hexdigest() != build.DISPLAY_P3_ICC_SHA256:
        raise AssertionError("ICC Display P3 no preservat")

    layers = list(document)
    layer_ids = tuple(layer.layer_id for layer in layers)
    if layer_ids != build.OUTPUT_LAYER_IDS:
        raise AssertionError(f"ordre/selecció incorrectes: {layer_ids}")
    if len(layers) != len(build.OUTPUT_LAYER_IDS):
        raise AssertionError("recompte de capes incorrecte")
    if any(build.layer_has_forbidden_structure(layer) for layer in layers):
        raise AssertionError("hi ha grup, efecte, Smart Object o capa no píxel")

    expected = expected_source_layers(c2, ct1)
    if final_declaration is None:
        visibility = _expected_visibility(expected, through_layer_id)
        expected_names = {
            layer_id: expected[layer_id].name for layer_id in build.OUTPUT_LAYER_IDS
        }
        expected_opacities = {
            layer_id: expected[layer_id].opacity for layer_id in build.OUTPUT_LAYER_IDS
        }
    else:
        visibility = final_declaration["visibility"]
        expected_names = {
            layer_id: final_declaration["name_overrides"].get(
                layer_id,
                expected[layer_id].name,
            )
            for layer_id in build.OUTPUT_LAYER_IDS
        }
        expected_opacities = {
            layer_id: final_declaration["opacity_overrides"].get(
                layer_id,
                expected[layer_id].opacity,
            )
            for layer_id in build.OUTPUT_LAYER_IDS
        }
    layer_receipts: dict[str, object] = {}
    for layer in layers:
        source = expected[layer.layer_id]
        if layer.blend_mode != BlendMode.NORMAL:
            raise AssertionError(f"layer_id={layer.layer_id}: no és Normal")
        if (
            tuple(layer.bbox) != tuple(source.bbox)
            or layer.name != expected_names[layer.layer_id]
            or layer.opacity != expected_opacities[layer.layer_id]
            or layer.fill_opacity != source.fill_opacity
            or layer.visible != visibility[layer.layer_id]
        ):
            raise AssertionError(f"layer_id={layer.layer_id}: estat o geometria divergent")

        actual_nonmask = build.raw_nonmask_fingerprints(layer)
        source_nonmask = build.raw_nonmask_fingerprints(source)
        if actual_nonmask != source_nonmask:
            raise AssertionError(f"layer_id={layer.layer_id}: raster font alterat")

        if layer.layer_id not in modified_masks:
            actual_all = build.raw_channel_fingerprints(layer)
            source_all = build.raw_channel_fingerprints(source)
            if actual_all != source_all:
                raise AssertionError(f"layer_id={layer.layer_id}: canals crus divergents")
            if through_layer_id is None and final_declaration is None:
                actual_record = layer_record_sha256(layer)
                source_record = layer_record_sha256(source)
                if actual_record != source_record:
                    raise AssertionError(
                        f"layer_id={layer.layer_id}: LayerRecord cru divergent"
                    )

        mask_receipt = _mask_roundtrip_metadata(layer, header)
        if mask_receipt is not None and mask_receipt["dtype"] != ">u2":
            raise AssertionError(f"layer_id={layer.layer_id}: màscara no u16")
        if final_declaration is not None and layer.layer_id in declared_masks:
            declared = final_declaration["masks"][layer.layer_id]
            decoded, mask_data = build._decoded_mask_u16(layer, header)
            if decoded is None or mask_data is None:
                raise AssertionError(
                    f"layer_id={layer.layer_id}: falta la màscara final declarada"
                )
            actual_bbox = (
                mask_data.left,
                mask_data.top,
                mask_data.right,
                mask_data.bottom,
            )
            if actual_bbox != tuple(declared["bbox"]):
                raise AssertionError(
                    f"layer_id={layer.layer_id}: bbox de màscara final divergent"
                )
            if mask_data.background_color != 0:
                raise AssertionError(
                    f"layer_id={layer.layer_id}: background de màscara final no és zero"
                )
            actual_decoded_hash = build.sha256_u16_be(decoded)
            if actual_decoded_hash != declared["decoded_sha256"]:
                raise AssertionError(
                    f"layer_id={layer.layer_id}: contingut de màscara final divergent"
                )
        layer_receipts[str(layer.layer_id)] = {
            "source": "Corretgint2"
            if layer.layer_id in build.CORRETGINT2_LAYER_IDS
            else "CapesTotalsV1",
            "name": layer.name,
            "bbox": list(layer.bbox),
            "visible": layer.visible,
            "opacity": layer.opacity,
            "fill_opacity": layer.fill_opacity,
            "nonmask_channels": actual_nonmask,
            "mask": mask_receipt,
            "mask_modified_declared": layer.layer_id in modified_masks,
        }

    merged_receipt: dict[str, object]
    if expect_merged_rgba4:
        channels = document._record.image_data.get_data(header, split=True)
        if len(channels) != 4:
            raise AssertionError(f"merged no és RGBA4: {len(channels)} canals")
        expected_bytes = build.WIDTH * build.HEIGHT * 2
        if any(len(channel) != expected_bytes for channel in channels):
            raise AssertionError("merged no és u16 de mida completa")
        merged_receipt = {
            "status": "RGBA4_PRESENT",
            "channel_sha256": [hashlib.sha256(channel).hexdigest() for channel in channels],
        }
    else:
        merged_receipt = {"status": "NOT_CLAIMED"}

    return {
        "status": "PASS",
        "header": {
            "version": header.version,
            "depth": header.depth,
            "channels": header.channels,
            "size": [document.width, document.height],
        },
        "layer_ids_bottom_to_top": list(layer_ids),
        "filters_present": [],
        "document_tags": {"Lr16": True, "Mt16": True},
        "layers": layer_receipts,
        "merged": merged_receipt,
        "final_declaration_checked": final_declaration is not None,
    }


def verify_candidate(
    candidate_path: Path,
    c2: PSDImage,
    ct1: PSDImage,
    *,
    through_layer_id: int | None,
    modified_mask_ids: Iterable[int],
    final_declaration: dict[str, object] | None = None,
) -> dict[str, object]:
    candidate_path = candidate_path.resolve()
    if not candidate_path.is_file():
        raise AssertionError(f"no existeix el candidat: {candidate_path}")
    candidate = PSDImage.open(candidate_path)
    receipt = verify_selected_document(
        candidate,
        c2,
        ct1,
        through_layer_id=through_layer_id,
        modified_mask_ids=modified_mask_ids,
        final_declaration=final_declaration,
        expect_merged_rgba4=True,
    )
    receipt["candidate"] = {
        "path": str(candidate_path),
        "size": candidate_path.stat().st_size,
        "sha256": build.sha256_file(candidate_path),
    }
    return receipt


def self_test(
    corretgint2_path: Path,
    capes_totals_v1_path: Path,
) -> dict[str, object]:
    """Tests sense cap sortida persistent ni cap save sobre material científic."""

    c2, ct1, source_manifest = build.validate_sources(
        corretgint2_path,
        capes_totals_v1_path,
    )
    selected, build_manifest = build.build_selected_document(
        corretgint2_path,
        capes_totals_v1_path,
    )
    # build_selected_document obre còpies pròpies; les fonts d'aquí continuen
    # sent la referència independent per als hashes crus.
    selected_receipt = verify_selected_document(selected, c2, ct1)

    # Màscara u16: mutació només d'un objecte en memòria.
    mask_test = np.array(
        [[0, 1, 65_535], [13, 32_768, 65_534]],
        dtype=np.uint16,
    )
    test_layer = selected[0]
    original_nonmask = build.raw_nonmask_fingerprints(test_layer)
    build.replace_mask_u16(test_layer, mask_test, top=20, left=30)
    decoded, mask_data = build._decoded_mask_u16(test_layer, selected._record.header)
    if not np.array_equal(decoded, mask_test):
        raise AssertionError("self-test: màscara u16 no fa round-trip en memòria")
    if (mask_data.left, mask_data.top, mask_data.right, mask_data.bottom) != (30, 20, 33, 22):
        raise AssertionError("self-test: bbox de màscara incorrecta")
    if build.raw_nonmask_fingerprints(test_layer) != original_nonmask:
        raise AssertionError("self-test: replace_mask_u16 ha alterat el raster")

    # Merged RGBA4 sobre un document sintètic petit; zero save.
    tiny = PSDImage.new("RGB", (3, 2), color=0, depth=16)
    tiny._record.header.version = 2
    tiny._record.header.channels = 4
    tiny_layer_mask = tiny._record.layer_and_mask_information
    if tiny_layer_mask.tagged_blocks is None:
        tiny_layer_mask.tagged_blocks = TaggedBlocks()
    tiny_layer_mask.tagged_blocks.set_data(Tag.LAYER_16, 0, [], [])
    tiny_layer_mask.tagged_blocks.set_data(Tag.SAVING_MERGED_TRANSPARENCY16)
    if tiny_layer_mask.layer_info is None:
        tiny_layer_mask.layer_info = build.LayerInfo()
    tiny_layer_mask.layer_info.layer_count = 0
    rgba = np.array(
        [
            [[0, 1, 2, 3], [4, 5, 6, 7], [65_535, 32_768, 12, 9]],
            [[8, 9, 10, 11], [12, 13, 14, 15], [16, 17, 18, 65_535]],
        ],
        dtype=np.uint16,
    )
    expected_hashes = build.set_merged_rgba4(tiny, rgba, compression=Compression.RAW)
    channels = tiny._record.image_data.get_data(tiny._record.header, split=True)
    actual_hashes = [hashlib.sha256(channel).hexdigest() for channel in channels]
    if len(channels) != 4 or actual_hashes != expected_hashes:
        raise AssertionError("self-test: merged RGBA4 no fa round-trip en memòria")
    for channel_index, channel in enumerate(channels):
        actual = np.frombuffer(channel, dtype=">u2").reshape(2, 3)
        if not np.array_equal(actual, rgba[..., channel_index]):
            raise AssertionError(
                f"self-test: merged canal {channel_index} no coincideix"
            )
    if Tag.SAVING_MERGED_TRANSPARENCY16 not in build.document_layer_tags(tiny):
        raise AssertionError("self-test: s'ha perdut Mt16")

    # Compositor Normal + alfa source-over en un llenç sintètic. Els únics
    # fitxers creats són NPY dins un TemporaryDirectory, eliminat en sortir.
    composite_doc = new_psb(3, 2)
    bottom_rgb = np.array(
        [
            [[1_000, 2_000, 3_000], [10_000, 20_000, 30_000], [65_535, 0, 7]],
            [[5, 6, 7], [8_000, 9_000, 10_000], [11_000, 12_000, 13_000]],
        ],
        dtype=np.uint16,
    )
    top_rgb = np.array(
        [
            [[60_000, 50_000, 40_000], [1, 2, 3], [4_000, 5_000, 6_000]],
            [[7_000, 8_000, 9_000], [65_535, 32_768, 0], [14_000, 15_000, 16_000]],
        ],
        dtype=np.uint16,
    )
    bottom_mask = np.array(
        [[0, 16_384, 65_535], [32_768, 49_152, 65_535]],
        dtype=np.uint16,
    )
    top_mask = np.array(
        [[65_535, 32_768, 0], [1, 40_000, 60_000]],
        dtype=np.uint16,
    )
    bottom = add_pixel_layer(composite_doc, bottom_rgb, "bottom")
    add_mask16(bottom, bottom_mask, top=0, left=0)
    top = add_pixel_layer(composite_doc, top_rgb, "top")
    add_mask16(top, top_mask, top=0, left=0)
    build.finalize_lr16(composite_doc)
    composite_tags = composite_doc._record.layer_and_mask_information.tagged_blocks
    composite_tags.set_data(Tag.SAVING_MERGED_TRANSPARENCY16)

    with tempfile.TemporaryDirectory(prefix="ctv2_selftest_") as temporary:
        temporary_path = Path(temporary)
        composed = build.compose_normal_rgba4_to_npy(
            composite_doc,
            composite_doc._record.header,
            temporary_path / "float.npy",
            temporary_path / "rgba.npy",
            chunk_rows=1,
        )
        a0 = bottom_mask.astype(np.float32) * (1.0 / 65_535.0)
        a1 = top_mask.astype(np.float32) * (1.0 / 65_535.0)
        expected_rgb = (
            bottom_rgb.astype(np.float32) * (1.0 / 65_535.0) * a0[..., None]
        )
        expected_rgb = (
            expected_rgb * (1.0 - a1[..., None])
            + top_rgb.astype(np.float32) * (1.0 / 65_535.0) * a1[..., None]
        )
        expected_alpha = a1 + a0 * (1.0 - a1)
        expected_rgba_float = np.concatenate(
            [expected_rgb, expected_alpha[..., None]],
            axis=-1,
        )
        expected_rgba = np.clip(
            np.floor(expected_rgba_float.astype(np.float64) * 65_535.0 + 0.5),
            0,
            65_535,
        ).astype(np.uint16)
        if not np.array_equal(np.asarray(composed), expected_rgba):
            raise AssertionError("self-test: compositor Normal RGBA4 divergent")

    # Mode final complet sobre un PSB sintètic dins TemporaryDirectory. Cobreix
    # màscara full-document, màscara amb frame, estat final, round-trip PSB i
    # les dues barreres no-clobber. No toca cap candidat científic.
    final_doc = new_psb(3, 2)
    for layer_id, name, rgb in (
        (101, "base", bottom_rgb),
        (102, "outer", top_rgb),
        (103, "must-hide", np.full_like(bottom_rgb, 777)),
    ):
        layer = add_pixel_layer(final_doc, rgb, name)
        layer._record.tagged_blocks.set_data(Tag.LAYER_ID, layer_id)
    build.finalize_lr16(final_doc)
    final_tags = final_doc._record.layer_and_mask_information.tagged_blocks
    final_tags.set_data(Tag.SAVING_MERGED_TRANSPARENCY16)

    full_mask = np.array(
        [[0, 65_535, 32_768], [1, 12_345, 65_534]],
        dtype=np.uint16,
    )
    frame_mask = np.array([[2_000, 60_000]], dtype=np.uint16)
    with tempfile.TemporaryDirectory(prefix="ctv2_final_save_") as temporary:
        temporary_path = Path(temporary)
        mask_dir = temporary_path / "masks"
        empty_mask_dir = temporary_path / "empty_masks"
        work_dir = temporary_path / "work"
        mask_dir.mkdir()
        empty_mask_dir.mkdir()
        work_dir.mkdir()

        empty_config_path = temporary_path / "final_empty_masks.json"
        empty_config_payload = {
            "visibility": {"101": True, "102": False, "103": False},
            "name_overrides": {},
            "opacity_overrides": {},
            "masks": {},
        }
        empty_config_path.write_text(
            json.dumps(empty_config_payload, ensure_ascii=False),
            encoding="utf-8",
        )
        empty_declaration = build.load_final_declaration(
            empty_config_path,
            empty_mask_dir,
            allowed_ids=(101, 102, 103),
            allowed_mask_ids=(102,),
            canvas_width=3,
            canvas_height=2,
            required_hidden_ids=(103,),
        )
        if empty_declaration["masks"]:
            raise AssertionError("self-test: quarantena sense màscares no és buida")

        missing_mask_config_path = temporary_path / "final_missing_visible_mask.json"
        missing_mask_payload = dict(empty_config_payload)
        missing_mask_payload["visibility"] = {
            "101": True,
            "102": True,
            "103": False,
        }
        missing_mask_config_path.write_text(
            json.dumps(missing_mask_payload, ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            build.load_final_declaration(
                missing_mask_config_path,
                empty_mask_dir,
                allowed_ids=(101, 102, 103),
                allowed_mask_ids=(102,),
                canvas_width=3,
                canvas_height=2,
                required_hidden_ids=(103,),
            )
        except ValueError as error:
            if "màscara final" not in str(error):
                raise
        else:
            raise AssertionError(
                "self-test: una FONT_HDR visible sense màscara s'hauria de rebutjar"
            )

        np.save(mask_dir / "mask_101.npy", full_mask, allow_pickle=False)
        np.save(mask_dir / "mask_102.npy", frame_mask, allow_pickle=False)
        config_path = temporary_path / "final.json"
        config_payload = {
            "visibility": {"101": True, "102": True, "103": False},
            "name_overrides": {"101": "base-final"},
            "opacity_overrides": {"102": 211},
            "masks": {
                "101": {},
                "102": {"bbox": [1, 1, 3, 2]},
            },
        }
        config_path.write_text(
            json.dumps(config_payload, ensure_ascii=False),
            encoding="utf-8",
        )
        try:
            build.load_final_declaration(
                config_path,
                mask_dir,
                allowed_ids=(101, 102, 103),
                allowed_mask_ids=(101,),
                canvas_width=3,
                canvas_height=2,
                required_hidden_ids=(103,),
            )
        except ValueError as error:
            if "protegides" not in str(error):
                raise
        else:
            raise AssertionError("self-test: s'ha admès una màscara protegida")
        declaration = build.load_final_declaration(
            config_path,
            mask_dir,
            allowed_ids=(101, 102, 103),
            allowed_mask_ids=(101, 102),
            canvas_width=3,
            canvas_height=2,
            required_hidden_ids=(103,),
        )
        before_nonmask = {
            layer.layer_id: build.raw_nonmask_fingerprints(layer)
            for layer in final_doc
        }
        build.apply_final_declaration(
            final_doc,
            declaration,
            expected_ids=(101, 102, 103),
        )
        if any(
            build.raw_nonmask_fingerprints(layer) != before_nonmask[layer.layer_id]
            for layer in final_doc
        ):
            raise AssertionError("self-test: l'estat final ha alterat un raster")
        build.finalize_lr16(final_doc)
        final_rgba = build.compose_normal_rgba4_to_npy(
            final_doc,
            final_doc._record.header,
            work_dir / "float.npy",
            work_dir / "rgba.npy",
            chunk_rows=1,
        )
        build.set_merged_rgba4(final_doc, final_rgba, compression=Compression.RAW)
        candidate_path = temporary_path / "synthetic_candidate.psb"
        candidate_receipt = build.save_candidate_no_clobber(
            final_doc,
            candidate_path,
            expected_layer_ids=(101, 102, 103),
        )
        if candidate_receipt["sha256"] != build.sha256_file(candidate_path):
            raise AssertionError("self-test: receipt del candidat divergent")
        reopened = PSDImage.open(candidate_path)
        reopened_by_id = {layer.layer_id: layer for layer in reopened}
        if (
            reopened_by_id[101].name != "base-final"
            or reopened_by_id[102].opacity != 211
            or reopened_by_id[103].visible
        ):
            raise AssertionError("self-test: estat final no preservat al PSB")
        decoded_full, full_data = build._decoded_mask_u16(
            reopened_by_id[101], reopened._record.header
        )
        decoded_frame, frame_data = build._decoded_mask_u16(
            reopened_by_id[102], reopened._record.header
        )
        if not np.array_equal(decoded_full, full_mask) or (
            full_data.left,
            full_data.top,
            full_data.right,
            full_data.bottom,
        ) != (0, 0, 3, 2):
            raise AssertionError("self-test: màscara full-document divergent")
        if not np.array_equal(decoded_frame, frame_mask) or (
            frame_data.left,
            frame_data.top,
            frame_data.right,
            frame_data.bottom,
        ) != (1, 1, 3, 2):
            raise AssertionError("self-test: màscara frame divergent")
        try:
            build.save_candidate_no_clobber(final_doc, candidate_path)
        except FileExistsError:
            pass
        else:
            raise AssertionError("self-test: el candidat existent s'hauria de bloquejar")
        manifest_path = temporary_path / "synthetic_manifest.json"
        build.write_json_no_clobber(
            manifest_path,
            {
                "status": "PASS",
                "declaration": build.final_declaration_manifest(declaration),
            },
        )
        try:
            build.write_json_no_clobber(manifest_path, {"status": "OVERWRITE"})
        except FileExistsError:
            pass
        else:
            raise AssertionError("self-test: el manifest existent s'hauria de bloquejar")

    return {
        "status": "PASS",
        "tests": {
            "source_pins_and_shared_rasters": "PASS",
            "raw_layer_clone_and_Lr16_Mt16": "PASS",
            "mask_u16_roundtrip_without_raster_change": "PASS",
            "merged_rgba4_roundtrip_without_save": "PASS",
            "normal_compositor_and_source_over_alpha": "PASS",
            "final_declaration_full_and_frame_masks": "PASS",
            "hidden_quarantine_allows_empty_mask_inventory": "PASS",
            "visible_hdr_requires_declared_mask": "PASS",
            "synthetic_psb_save_roundtrip": "PASS",
            "candidate_and_manifest_no_clobber": "PASS",
            "protected_mask_rejected": "PASS",
            "no_scientific_output_psb_written": "PASS",
        },
        "source_manifest": source_manifest,
        "build_manifest": build_manifest,
        "selected_receipt_summary": {
            "layer_ids": selected_receipt["layer_ids_bottom_to_top"],
            "document_tags": selected_receipt["document_tags"],
            "filters_present": selected_receipt["filters_present"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="QA read-only de CapesTotalsV2")
    parser.add_argument("--corretgint2", type=Path, default=build.DEFAULT_CORRETGINT2)
    parser.add_argument(
        "--capes-totals-v1",
        type=Path,
        default=build.DEFAULT_CAPES_TOTALS_V1,
    )
    parser.add_argument("--candidate", type=Path)
    parser.add_argument(
        "--through-layer-id",
        type=int,
        choices=build.OUTPUT_LAYER_IDS,
    )
    parser.add_argument(
        "--modified-mask-id",
        type=int,
        action="append",
        default=[],
        choices=build.OUTPUT_LAYER_IDS,
    )
    parser.add_argument(
        "--final-config",
        type=Path,
        help="declaració final usada pel builder; habilita noms/opacitats/visibilitat finals",
    )
    parser.add_argument("--mask-dir", type=Path)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    if (args.final_config is None) != (args.mask_dir is None):
        parser.error("--final-config i --mask-dir s'han de proporcionar junts")
    if args.final_config is not None and (
        args.through_layer_id is not None or args.modified_mask_id
    ):
        parser.error(
            "--final-config ja declara estat/màscares i no es combina amb "
            "--through-layer-id/--modified-mask-id"
        )
    if args.self_test and args.final_config is not None:
        parser.error("--self-test crea la seva pròpia declaració sintètica")

    if args.self_test:
        receipt = self_test(args.corretgint2, args.capes_totals_v1)
    else:
        c2, ct1, source_manifest = build.validate_sources(
            args.corretgint2,
            args.capes_totals_v1,
        )
        final_declaration = None
        if args.final_config is not None:
            final_declaration = build.load_final_declaration(
                args.final_config,
                args.mask_dir,
            )
        if args.candidate is not None:
            receipt = verify_candidate(
                args.candidate,
                c2,
                ct1,
                through_layer_id=args.through_layer_id,
                modified_mask_ids=args.modified_mask_id,
                final_declaration=final_declaration,
            )
        else:
            if final_declaration is not None:
                parser.error("--final-config sense --candidate no verifica cap estat materialitzat")
            selected, build_manifest = build.build_selected_document(
                args.corretgint2,
                args.capes_totals_v1,
                through_layer_id=args.through_layer_id,
            )
            receipt = verify_selected_document(
                selected,
                c2,
                ct1,
                through_layer_id=args.through_layer_id,
                modified_mask_ids=args.modified_mask_id,
            )
            receipt["source_manifest"] = source_manifest
            receipt["build_manifest"] = build_manifest
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
