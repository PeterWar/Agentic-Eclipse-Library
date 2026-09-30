"""Builder fail-closed per a ``CapesTotalsV2``.

El document de treball parteix del contenidor ``CapesTotalsV1.psb`` perquè
conservi els recursos de document, ``Lr16``, ``Mt16`` i la semàntica de
previsualització RGBA. Les quatre capes interiors provenen de
``Corretgint2.psb`` i les vuit capes d'exposició restants provenen del PSB
gran. Els ``LayerRecord`` i ``ChannelData`` es clonen crus: cap raster passa
per ``float`` ni es torna a comprimir.

El mode per defecte continua sent només preflight. El mode final s'ha d'activar
explícitament amb una declaració JSON completa, màscares ``mask_<id>.npy`` u16,
un directori de treball i un path candidat nou. Recompòn el merged RGBA4,
manté ``Mt16`` i promociona el PSB amb una operació que no pot sobreescriure
un fitxer existent. No aplica cap filtre ni modifica els rasters font.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
from typing import Iterable, MutableMapping, Sequence
import uuid

import numpy as np
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import BlendMode, ChannelID, Compression, Resource, Tag
from psd_tools.psd.image_data import ImageData
from psd_tools.psd.layer_and_mask import (
    ChannelData,
    ChannelInfo,
    LayerInfo,
    MaskData,
    MaskFlags,
)
from psd_tools.psd.tagged_blocks import TaggedBlocks


WIDTH = 7_648
HEIGHT = 5_353

DEFAULT_CORRETGINT2 = Path("/Users/USUARI/Downloads/Corretgint2.psb")
DEFAULT_CAPES_TOTALS_V1 = Path(
    "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/"
    "1-Unint Capes/Capes Totals/CapesTotalsV1.psb"
)

CORRETGINT2_SIZE = 557_302_530
CORRETGINT2_SHA256 = "1777d41f29e9644faae527c1b4aed3be25f3ff1079f1418aabbcc58d9109e052"
CAPES_TOTALS_V1_SIZE = 2_370_519_442
CAPES_TOTALS_V1_SHA256 = "4d0480f1d6508c225f5dbb13fb5c4e608d35a07b58acc2625853284ba48f2a28"
DISPLAY_P3_ICC_SHA256 = "7e1c7ec53e8ea35fed3e169dee62115ac045f26c7bc256fab16a5c26c29eacbd"

CORRETGINT2_LAYER_IDS = (3, 4, 5, 7)
CAPES_TOTALS_SOURCE_IDS = (8, 9, 10, 11, 12, 13, 16, 17)
FINAL_MASK_IDS = (8, 9, 10, 11, 12, 13, 16)
OUTPUT_LAYER_IDS = CORRETGINT2_LAYER_IDS + CAPES_TOTALS_SOURCE_IDS
CAPES_TOTALS_ALL_IDS = (
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    19,
    20,
    21,
    22,
    23,
    24,
    25,
    26,
    27,
    28,
    29,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    38,
)

FORBIDDEN_LAYER_TAGS = frozenset(
    tag
    for tag in (
        getattr(Tag, "EFFECTS_LAYER", None),
        getattr(Tag, "OBJECT_BASED_EFFECTS_LAYER_INFO", None),
        getattr(Tag, "OBJECT_BASED_EFFECTS_LAYER_INFO_V0", None),
        getattr(Tag, "OBJECT_BASED_EFFECTS_LAYER_INFO_V1", None),
        getattr(Tag, "SMART_OBJECT_LAYER_DATA1", None),
        getattr(Tag, "SMART_OBJECT_LAYER_DATA2", None),
        getattr(Tag, "PLACED_LAYER1", None),
        getattr(Tag, "PLACED_LAYER2", None),
        getattr(Tag, "SECTION_DIVIDER_SETTING", None),
        getattr(Tag, "NESTED_SECTION_DIVIDER_SETTING", None),
    )
    if tag is not None
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_u16_be(array: np.ndarray, *, chunk_rows: int = 192) -> str:
    """Hash canònic d'una matriu u16 sense materialitzar-ne una còpia sencera."""

    if array.dtype.kind != "u" or array.dtype.itemsize != 2 or array.ndim != 2:
        raise TypeError("sha256_u16_be exigeix una matriu uint16 2-D")
    if chunk_rows <= 0:
        raise ValueError("chunk_rows ha de ser positiu")
    digest = hashlib.sha256()
    for row0 in range(0, array.shape[0], chunk_rows):
        row1 = min(array.shape[0], row0 + chunk_rows)
        digest.update(
            np.ascontiguousarray(array[row0:row1]).astype(">u2").tobytes()
        )
    return digest.hexdigest()


def channel_map(layer) -> MutableMapping[int, tuple[ChannelInfo, ChannelData]]:
    return {
        int(info.id): (info, data)
        for info, data in zip(layer._record.channel_info, layer._channels)
    }


def raw_channel_fingerprints(layer) -> dict[str, dict[str, object]]:
    """Hash del payload comprimit, sense decodificar ni requantitzar."""

    result: dict[str, dict[str, object]] = {}
    for info, data in zip(layer._record.channel_info, layer._channels):
        result[str(int(info.id))] = {
            "compression": int(data.compression.value),
            "compressed_size": len(data.data),
            "compressed_sha256": sha256_bytes(data.data),
        }
    return result


def raw_nonmask_fingerprints(layer) -> dict[str, dict[str, object]]:
    return {
        key: value
        for key, value in raw_channel_fingerprints(layer).items()
        if int(key) != int(ChannelID.USER_LAYER_MASK)
    }


def layer_has_forbidden_structure(layer) -> bool:
    if layer.kind != "pixel":
        return True
    blocks = layer._record.tagged_blocks
    return bool(blocks and FORBIDDEN_LAYER_TAGS.intersection(blocks.keys()))


def document_layer_tags(psd: PSDImage) -> set[Tag]:
    blocks = psd._record.layer_and_mask_information.tagged_blocks
    return set(blocks.keys()) if blocks else set()


def _validate_file_pin(path: Path, expected_size: int, expected_sha256: str) -> None:
    if not path.is_file():
        raise AssertionError(f"no existeix la font: {path}")
    if path.stat().st_size != expected_size:
        raise AssertionError(
            f"mida inesperada a {path}: {path.stat().st_size}, esperada={expected_size}"
        )
    actual = sha256_file(path)
    if actual != expected_sha256:
        raise AssertionError(f"SHA-256 inesperat a {path}: {actual}")


def _validate_header(psd: PSDImage, expected_channels: int, label: str) -> None:
    header = psd._record.header
    actual = (
        header.version,
        header.depth,
        header.channels,
        psd.width,
        psd.height,
        int(psd.color_mode),
    )
    expected = (2, 16, expected_channels, WIDTH, HEIGHT, 3)
    if actual != expected:
        raise AssertionError(f"capçalera {label} inesperada: {actual}, esperada={expected}")

    tags = document_layer_tags(psd)
    if Tag.LAYER_16 not in tags:
        raise AssertionError(f"{label}: falta Lr16")
    classic = psd._record.layer_and_mask_information.layer_info
    if classic is None or classic.layer_count != 0:
        raise AssertionError(f"{label}: la secció clàssica de capes no és buida")

    icc = psd.image_resources.get_data(Resource.ICC_PROFILE)
    if icc is None or sha256_bytes(icc) != DISPLAY_P3_ICC_SHA256:
        raise AssertionError(f"{label}: ICC Display P3 inesperat")


def _validate_selected_layers(
    psd: PSDImage,
    expected_ids: Sequence[int],
    label: str,
) -> dict[int, object]:
    by_id = {layer.layer_id: layer for layer in psd}
    if len(by_id) != len(list(psd)):
        raise AssertionError(f"{label}: IDs de capa duplicats")
    missing = [layer_id for layer_id in expected_ids if layer_id not in by_id]
    if missing:
        raise AssertionError(f"{label}: falten capes {missing}")
    for layer_id in expected_ids:
        layer = by_id[layer_id]
        if layer_has_forbidden_structure(layer):
            raise AssertionError(f"{label}: layer_id={layer_id} no és una capa píxel plana")
        if layer.blend_mode != BlendMode.NORMAL:
            raise AssertionError(f"{label}: layer_id={layer_id} no és Normal")
        if layer.fill_opacity != 255:
            raise AssertionError(f"{label}: layer_id={layer_id} no té fill 100 %")
    return by_id


def validate_sources(
    corretgint2_path: Path = DEFAULT_CORRETGINT2,
    capes_totals_v1_path: Path = DEFAULT_CAPES_TOTALS_V1,
) -> tuple[PSDImage, PSDImage, dict[str, object]]:
    """Valida els dos pins i demostra que els quatre rasters comuns són iguals."""

    corretgint2_path = corretgint2_path.resolve()
    capes_totals_v1_path = capes_totals_v1_path.resolve()
    _validate_file_pin(corretgint2_path, CORRETGINT2_SIZE, CORRETGINT2_SHA256)
    _validate_file_pin(
        capes_totals_v1_path,
        CAPES_TOTALS_V1_SIZE,
        CAPES_TOTALS_V1_SHA256,
    )

    c2 = PSDImage.open(corretgint2_path)
    ct1 = PSDImage.open(capes_totals_v1_path)
    _validate_header(c2, expected_channels=3, label="Corretgint2")
    _validate_header(ct1, expected_channels=4, label="CapesTotalsV1")

    c2_ids = tuple(layer.layer_id for layer in c2)
    if c2_ids != CORRETGINT2_LAYER_IDS:
        raise AssertionError(f"Corretgint2: ordre inesperat {c2_ids}")
    ct1_ids = tuple(layer.layer_id for layer in ct1)
    if ct1_ids != CAPES_TOTALS_ALL_IDS:
        raise AssertionError(f"CapesTotalsV1: ordre inesperat {ct1_ids}")

    c2_by_id = _validate_selected_layers(c2, CORRETGINT2_LAYER_IDS, "Corretgint2")
    ct1_by_id = _validate_selected_layers(ct1, CAPES_TOTALS_SOURCE_IDS, "CapesTotalsV1")
    if Tag.SAVING_MERGED_TRANSPARENCY16 in document_layer_tags(c2):
        raise AssertionError("Corretgint2: Mt16 no era esperat")
    if Tag.SAVING_MERGED_TRANSPARENCY16 not in document_layer_tags(ct1):
        raise AssertionError("CapesTotalsV1: falta Mt16")

    shared_raster_hashes: dict[str, object] = {}
    ct1_all = {layer.layer_id: layer for layer in ct1}
    for layer_id in CORRETGINT2_LAYER_IDS:
        left = raw_nonmask_fingerprints(c2_by_id[layer_id])
        right = raw_nonmask_fingerprints(ct1_all[layer_id])
        if left != right:
            raise AssertionError(
                f"els rasters comuns divergeixen a layer_id={layer_id}"
            )
        shared_raster_hashes[str(layer_id)] = left

    manifest: dict[str, object] = {
        "sources": {
            "corretgint2": {
                "path": str(corretgint2_path),
                "size": CORRETGINT2_SIZE,
                "sha256": CORRETGINT2_SHA256,
            },
            "capes_totals_v1": {
                "path": str(capes_totals_v1_path),
                "size": CAPES_TOTALS_V1_SIZE,
                "sha256": CAPES_TOTALS_V1_SHA256,
            },
        },
        "icc_sha256": DISPLAY_P3_ICC_SHA256,
        "shared_inner_nonmask_channels": shared_raster_hashes,
        "selected_layer_ids": list(OUTPUT_LAYER_IDS),
        "filters_selected": [],
        "known_gate": {
            "layer_id_17_opacity": ct1_by_id[17].opacity,
            "note": "es conserva cru; qualsevol normalització futura ha de ser explícita",
        },
    }
    return c2, ct1, manifest


def clone_pixel_layer_raw(parent: PSDImage, source_layer) -> PixelLayer:
    """Clona registre i canals comprimits sense passar per numpy/PIL."""

    if layer_has_forbidden_structure(source_layer):
        raise AssertionError(
            f"no es pot clonar com a píxel pla layer_id={source_layer.layer_id}"
        )
    return PixelLayer(
        parent,
        copy.deepcopy(source_layer._record),
        copy.deepcopy(source_layer._channels),
    )


def _remove_user_mask_channel(layer) -> None:
    kept = [
        (info, data)
        for info, data in zip(layer._record.channel_info, layer._channels)
        if int(info.id) != int(ChannelID.USER_LAYER_MASK)
    ]
    layer._record.channel_info[:] = [pair[0] for pair in kept]
    layer._channels[:] = [pair[1] for pair in kept]


def replace_mask_u16(
    layer,
    mask16: np.ndarray,
    *,
    top: int,
    left: int,
    background_color: int = 0,
    compression: Compression = Compression.ZIP_WITH_PREDICTION,
) -> None:
    """Substitueix una única màscara per un canal real de 16 bits.

    No toca transparència ni RGB. El caller ha de reimposar abans els zeros de
    cobertura, disc lunar i nuclis protegits.
    """

    if mask16.dtype != np.uint16 or mask16.ndim != 2:
        raise TypeError("mask16 ha de ser una matriu uint16 2-D")
    if not 0 <= background_color <= 255:
        raise ValueError("background_color ha d'estar entre 0 i 255")
    height, width = mask16.shape
    _remove_user_mask_channel(layer)
    data = ChannelData(compression)
    data.set_data(
        np.ascontiguousarray(mask16).astype(">u2").tobytes(),
        width,
        height,
        16,
        layer._psd._record.header.version,
    )
    layer._record.mask_data = MaskData(
        top=top,
        left=left,
        bottom=top + height,
        right=left + width,
        background_color=background_color,
        flags=MaskFlags(),
    )
    layer._record.channel_info.append(
        ChannelInfo(id=ChannelID.USER_LAYER_MASK, length=len(data.data) + 2)
    )
    layer._channels.append(data)
    if hasattr(layer, "_mask"):
        del layer._mask
    layer._psd._mark_updated()


def replace_mask_raw(target_layer, source_layer) -> None:
    """Copia ``MaskData`` i el canal -2 comprimit exactes d'una altra capa."""

    source_channels = channel_map(source_layer)
    mask_id = int(ChannelID.USER_LAYER_MASK)
    if source_layer._record.mask_data is None or mask_id not in source_channels:
        raise AssertionError("la capa font no té màscara raster")
    _remove_user_mask_channel(target_layer)
    info, data = source_channels[mask_id]
    target_layer._record.mask_data = copy.deepcopy(source_layer._record.mask_data)
    target_layer._record.channel_info.append(copy.deepcopy(info))
    target_layer._channels.append(copy.deepcopy(data))
    if hasattr(target_layer, "_mask"):
        del target_layer._mask
    target_layer._psd._mark_updated()


def finalize_lr16(psd: PSDImage) -> None:
    """Mou l'arbre actual a ``Lr16`` i buida la secció clàssica."""

    psd._update_record()
    layer_mask = psd._record.layer_and_mask_information
    layer_info = layer_mask.layer_info
    if layer_mask.tagged_blocks is None:
        layer_mask.tagged_blocks = TaggedBlocks()
    layer_mask.tagged_blocks.set_data(
        Tag.LAYER_16,
        layer_info.layer_count,
        layer_info.layer_records,
        layer_info.channel_image_data,
    )
    layer_mask.layer_info = LayerInfo()


def set_merged_rgba4(
    psd: PSDImage,
    rgba16: np.ndarray,
    *,
    compression: Compression = Compression.RAW,
) -> list[str]:
    """Instal·la merged RGBA16 i conserva l'indicador ``Mt16``."""

    expected_shape = (psd.height, psd.width, 4)
    if rgba16.dtype != np.uint16 or rgba16.shape != expected_shape:
        raise TypeError(
            f"rgba16 ha de ser uint16 {expected_shape}, rebut {rgba16.dtype} {rgba16.shape}"
        )
    layer_mask = psd._record.layer_and_mask_information
    if layer_mask.tagged_blocks is None:
        raise AssertionError("falten tagged blocks de document")
    if Tag.LAYER_16 not in layer_mask.tagged_blocks:
        raise AssertionError("cal finalitzar Lr16 abans del merged")
    if Tag.SAVING_MERGED_TRANSPARENCY16 not in layer_mask.tagged_blocks:
        raise AssertionError("el contenidor ha perdut Mt16")

    psd._record.header.channels = 4
    channels = [
        np.ascontiguousarray(rgba16[..., channel]).astype(">u2").tobytes()
        for channel in range(4)
    ]
    image_data = ImageData(compression=compression)
    image_data.set_data(channels, psd._record.header)
    psd._record.image_data = image_data
    # Evita que PSDImage.save substitueixi el merged de 16 bits per composite().
    psd._updated = False
    return [sha256_bytes(channel) for channel in channels]


def _decoded_channel_u16(layer, channel_id: ChannelID, header) -> np.ndarray:
    channels = channel_map(layer)
    key = int(channel_id)
    if key not in channels:
        raise AssertionError(f"layer_id={layer.layer_id}: falta canal {key}")
    raw = channels[key][1].get_data(
        layer.width,
        layer.height,
        header.depth,
        header.version,
    )
    expected = layer.width * layer.height * 2
    if len(raw) != expected:
        raise AssertionError(
            f"layer_id={layer.layer_id}: canal {key} no és u16 ({len(raw)} != {expected})"
        )
    return np.frombuffer(raw, dtype=">u2").reshape(layer.height, layer.width)


def _decoded_mask_u16(layer, header) -> tuple[np.ndarray, MaskData] | tuple[None, None]:
    mask_data = layer._record.mask_data
    channels = channel_map(layer)
    key = int(ChannelID.USER_LAYER_MASK)
    if mask_data is None and key not in channels:
        return None, None
    if mask_data is None or key not in channels:
        raise AssertionError(f"layer_id={layer.layer_id}: màscara incompleta")
    if (
        mask_data.flags.mask_disabled
        or mask_data.flags.invert_mask
        or mask_data.flags.parameters_applied
        or mask_data.parameters is not None
    ):
        raise AssertionError(
            f"layer_id={layer.layer_id}: el compositor només admet una màscara raster simple"
        )
    width = mask_data.right - mask_data.left
    height = mask_data.bottom - mask_data.top
    raw = channels[key][1].get_data(width, height, header.depth, header.version)
    expected = width * height * 2
    if len(raw) != expected:
        raise AssertionError(
            f"layer_id={layer.layer_id}: màscara no és u16 ({len(raw)} != {expected})"
        )
    return np.frombuffer(raw, dtype=">u2").reshape(height, width), mask_data


def _alpha_region(
    layer,
    transparency: np.ndarray,
    mask: np.ndarray | None,
    mask_data: MaskData | None,
    y0: int,
    y1: int,
    x0: int,
    x1: int,
) -> np.ndarray:
    alpha = transparency[
        y0 - layer.top : y1 - layer.top,
        x0 - layer.left : x1 - layer.left,
    ].astype(np.float32)
    alpha *= 1.0 / 65535.0
    if mask is not None and mask_data is not None:
        mask_region = np.full(
            alpha.shape,
            mask_data.background_color / 255.0,
            dtype=np.float32,
        )
        mx0 = max(x0, mask_data.left)
        my0 = max(y0, mask_data.top)
        mx1 = min(x1, mask_data.right)
        my1 = min(y1, mask_data.bottom)
        if mx1 > mx0 and my1 > my0:
            mask_region[
                my0 - y0 : my1 - y0,
                mx0 - x0 : mx1 - x0,
            ] = (
                mask[
                    my0 - mask_data.top : my1 - mask_data.top,
                    mx0 - mask_data.left : mx1 - mask_data.left,
                ].astype(np.float32)
                * (1.0 / 65535.0)
            )
        alpha *= mask_region
    alpha *= layer.opacity / 255.0
    return alpha


def compose_normal_rgba4_to_npy(
    layers: Iterable[object],
    header,
    float_work_path: Path,
    output_rgba_path: Path,
    *,
    chunk_rows: int = 128,
) -> np.memmap:
    """Compon capes Normal en espai codificat, amb treball float en memmap.

    Escriu només dos NPY de treball, mai un PSB. El canal alfa usa source-over
    ``Aout = Acapa + Aanterior*(1-Acapa)``; aquesta fórmula reprodueix el
    ``Mt16`` del PSB font exactament.
    """

    if chunk_rows <= 0:
        raise ValueError("chunk_rows ha de ser positiu")
    float_work_path = float_work_path.resolve()
    output_rgba_path = output_rgba_path.resolve()
    if float_work_path.exists() or output_rgba_path.exists():
        raise FileExistsError("no se sobreescriu cap NPY de treball")
    if float_work_path.parent != output_rgba_path.parent:
        raise ValueError("els dos NPY han d'estar al mateix directori de treball")
    if not float_work_path.parent.is_dir():
        raise FileNotFoundError("el directori de treball ha d'existir")

    canvas_width = int(header.width)
    canvas_height = int(header.height)
    accumulator = np.lib.format.open_memmap(
        float_work_path,
        mode="w+",
        dtype=np.float32,
        shape=(canvas_height, canvas_width, 4),
    )
    accumulator[:] = 0.0

    for layer in layers:
        if not layer.visible:
            continue
        if layer.blend_mode != BlendMode.NORMAL:
            raise AssertionError(f"layer_id={layer.layer_id}: només s'admet Normal")
        x0 = max(0, layer.left)
        y0 = max(0, layer.top)
        x1 = min(canvas_width, layer.right)
        y1 = min(canvas_height, layer.bottom)
        if x1 <= x0 or y1 <= y0:
            continue

        transparency = _decoded_channel_u16(
            layer,
            ChannelID.TRANSPARENCY_MASK,
            header,
        )
        mask, mask_data = _decoded_mask_u16(layer, header)
        for channel_index, channel_id in enumerate(
            (ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2)
        ):
            source = _decoded_channel_u16(layer, channel_id, header)
            for row0 in range(y0, y1, chunk_rows):
                row1 = min(y1, row0 + chunk_rows)
                alpha = _alpha_region(
                    layer,
                    transparency,
                    mask,
                    mask_data,
                    row0,
                    row1,
                    x0,
                    x1,
                )
                source_region = source[
                    row0 - layer.top : row1 - layer.top,
                    x0 - layer.left : x1 - layer.left,
                ].astype(np.float32)
                source_region *= 1.0 / 65535.0
                previous = np.asarray(
                    accumulator[row0:row1, x0:x1, channel_index],
                    dtype=np.float32,
                )
                accumulator[row0:row1, x0:x1, channel_index] = (
                    previous * (1.0 - alpha) + source_region * alpha
                )
            del source

        for row0 in range(y0, y1, chunk_rows):
            row1 = min(y1, row0 + chunk_rows)
            alpha = _alpha_region(
                layer,
                transparency,
                mask,
                mask_data,
                row0,
                row1,
                x0,
                x1,
            )
            previous_alpha = np.asarray(
                accumulator[row0:row1, x0:x1, 3],
                dtype=np.float32,
            )
            accumulator[row0:row1, x0:x1, 3] = (
                alpha + previous_alpha * (1.0 - alpha)
            )
        accumulator.flush()
        del transparency, mask

    output = np.lib.format.open_memmap(
        output_rgba_path,
        mode="w+",
        dtype=np.uint16,
        shape=(canvas_height, canvas_width, 4),
    )
    for row0 in range(0, canvas_height, chunk_rows):
        row1 = min(canvas_height, row0 + chunk_rows)
        values = np.asarray(accumulator[row0:row1], dtype=np.float64)
        output[row0:row1] = np.clip(
            np.floor(values * 65535.0 + 0.5),
            0,
            65535,
        ).astype(np.uint16)
    output.flush()
    del accumulator
    return output


def set_stage_visibility(psd: PSDImage, through_layer_id: int) -> None:
    """Activa fonts consecutivament; cap filtre no forma part del document."""

    if through_layer_id not in OUTPUT_LAYER_IDS:
        raise ValueError(f"stage invàlid: {through_layer_id}")
    stop = OUTPUT_LAYER_IDS.index(through_layer_id)
    for index, layer in enumerate(psd):
        layer.visible = index <= stop


FINAL_CONFIG_KEYS = frozenset(
    {"visibility", "name_overrides", "opacity_overrides", "masks"}
)


def _layer_id_from_json_key(raw_key: object, *, field: str) -> int:
    if not isinstance(raw_key, str):
        raise TypeError(f"{field}: els IDs han de ser claus JSON de text")
    try:
        layer_id = int(raw_key)
    except ValueError as error:
        raise ValueError(f"{field}: ID invàlid {raw_key!r}") from error
    if raw_key != str(layer_id):
        raise ValueError(f"{field}: ID no canònic {raw_key!r}")
    return layer_id


def _parse_layer_map(
    value: object,
    *,
    field: str,
    allowed_ids: Sequence[int],
) -> dict[int, object]:
    if not isinstance(value, dict):
        raise TypeError(f"{field} ha de ser un objecte JSON")
    result: dict[int, object] = {}
    allowed = set(allowed_ids)
    for raw_key, item in value.items():
        layer_id = _layer_id_from_json_key(raw_key, field=field)
        if layer_id not in allowed:
            raise ValueError(f"{field}: layer_id={layer_id} no forma part de la sortida")
        if layer_id in result:
            raise ValueError(f"{field}: layer_id={layer_id} repetit")
        result[layer_id] = item
    return result


def _parse_mask_bbox(
    value: object,
    *,
    layer_id: int,
    canvas_width: int,
    canvas_height: int,
) -> tuple[int, int, int, int]:
    if not isinstance(value, list) or len(value) != 4:
        raise TypeError(
            f"masks[{layer_id}].bbox ha de ser [left, top, right, bottom]"
        )
    if any(type(coordinate) is not int for coordinate in value):
        raise TypeError(f"masks[{layer_id}].bbox només admet enters")
    left, top, right, bottom = value
    if not (0 <= left < right <= canvas_width and 0 <= top < bottom <= canvas_height):
        raise ValueError(
            f"masks[{layer_id}].bbox queda fora del document: {value}"
        )
    return left, top, right, bottom


def load_final_declaration(
    config_path: Path,
    mask_dir: Path,
    *,
    allowed_ids: Sequence[int] = OUTPUT_LAYER_IDS,
    allowed_mask_ids: Sequence[int] = FINAL_MASK_IDS,
    canvas_width: int = WIDTH,
    canvas_height: int = HEIGHT,
    required_hidden_ids: Sequence[int] = (17,),
) -> dict[str, object]:
    """Carrega un estat final estricte sense inferir cap decisió científica.

    Les màscares interiors de ``Corretgint2`` i la capa 17 en quarantena
    queden excloses per defecte. Una màscara de document complet pot ometre
    ``bbox``; una màscara retallada l'ha de declarar com
    ``[left, top, right, bottom]``.
    """

    config_path = config_path.resolve()
    mask_dir = mask_dir.resolve()
    if not config_path.is_file():
        raise FileNotFoundError(f"no existeix la declaració final: {config_path}")
    if not mask_dir.is_dir():
        raise FileNotFoundError(f"no existeix el directori de màscares: {mask_dir}")
    with config_path.open("r", encoding="utf-8") as stream:
        config = json.load(stream)
    if not isinstance(config, dict):
        raise TypeError("la declaració final ha de ser un objecte JSON")
    unknown_keys = set(config).difference(FINAL_CONFIG_KEYS)
    missing_keys = FINAL_CONFIG_KEYS.difference(config)
    if unknown_keys or missing_keys:
        raise ValueError(
            "claus de declaració final incorrectes: "
            f"falten={sorted(missing_keys)}, sobren={sorted(unknown_keys)}"
        )

    allowed_ids = tuple(allowed_ids)
    visibility_raw = _parse_layer_map(
        config["visibility"],
        field="visibility",
        allowed_ids=allowed_ids,
    )
    if set(visibility_raw) != set(allowed_ids):
        missing = sorted(set(allowed_ids).difference(visibility_raw))
        raise ValueError(f"visibility ha de declarar totes les capes; falten={missing}")
    if any(type(value) is not bool for value in visibility_raw.values()):
        raise TypeError("visibility només admet true/false")
    visibility = {layer_id: bool(value) for layer_id, value in visibility_raw.items()}
    for layer_id in required_hidden_ids:
        if layer_id not in visibility or visibility[layer_id]:
            raise ValueError(f"layer_id={layer_id} ha de quedar hidden en l'estat final")

    names_raw = _parse_layer_map(
        config["name_overrides"],
        field="name_overrides",
        allowed_ids=allowed_ids,
    )
    names: dict[int, str] = {}
    for layer_id, value in names_raw.items():
        if not isinstance(value, str) or not value or "\x00" in value:
            raise TypeError(
                f"name_overrides[{layer_id}] ha de ser text no buit i sense NUL"
            )
        names[layer_id] = value

    opacities_raw = _parse_layer_map(
        config["opacity_overrides"],
        field="opacity_overrides",
        allowed_ids=allowed_ids,
    )
    opacities: dict[int, int] = {}
    for layer_id, value in opacities_raw.items():
        if type(value) is not int or not 0 <= value <= 255:
            raise TypeError(f"opacity_overrides[{layer_id}] ha de ser un enter 0..255")
        opacities[layer_id] = value

    masks_raw = _parse_layer_map(
        config["masks"],
        field="masks",
        allowed_ids=allowed_ids,
    )
    protected = set(masks_raw).difference(allowed_mask_ids)
    if protected:
        raise ValueError(
            "el mode final no pot substituir les màscares interiors/protegides: "
            f"{sorted(protected)}"
        )
    missing_visible_masks = sorted(
        layer_id
        for layer_id in allowed_mask_ids
        if visibility.get(layer_id, False) and layer_id not in masks_raw
    )
    if missing_visible_masks:
        raise ValueError(
            "tota FONT_HDR exterior visible ha de declarar la seva màscara final: "
            f"{missing_visible_masks}"
        )

    expected_names = {f"mask_{layer_id}.npy" for layer_id in masks_raw}
    actual_paths = list(mask_dir.glob("mask_*.npy"))
    actual_names = {path.name for path in actual_paths}
    if actual_names != expected_names:
        raise ValueError(
            "inventari mask_<id>.npy divergent: "
            f"falten={sorted(expected_names - actual_names)}, "
            f"sobren={sorted(actual_names - expected_names)}"
        )

    masks: dict[int, dict[str, object]] = {}
    for layer_id, value in masks_raw.items():
        if not isinstance(value, dict):
            raise TypeError(f"masks[{layer_id}] ha de ser un objecte JSON")
        unknown_mask_keys = set(value).difference({"bbox"})
        if unknown_mask_keys:
            raise ValueError(
                f"masks[{layer_id}]: claus desconegudes {sorted(unknown_mask_keys)}"
            )
        mask_path = mask_dir / f"mask_{layer_id}.npy"
        if mask_path.is_symlink() or mask_path.resolve().parent != mask_dir:
            raise ValueError(f"masks[{layer_id}]: no s'admeten symlinks ni escapades de directori")
        if not mask_path.is_file():
            raise FileNotFoundError(mask_path)
        array = np.load(mask_path, mmap_mode="r", allow_pickle=False)
        if array.dtype != np.dtype(np.uint16) or array.ndim != 2:
            raise TypeError(
                f"masks[{layer_id}]: s'esperava uint16 2-D, rebut {array.dtype} {array.shape}"
            )
        if "bbox" in value:
            bbox = _parse_mask_bbox(
                value["bbox"],
                layer_id=layer_id,
                canvas_width=canvas_width,
                canvas_height=canvas_height,
            )
        else:
            bbox = (0, 0, canvas_width, canvas_height)
        left, top, right, bottom = bbox
        expected_shape = (bottom - top, right - left)
        if tuple(array.shape) != expected_shape:
            raise ValueError(
                f"masks[{layer_id}]: shape {array.shape} != frame {expected_shape}"
            )
        decoded_sha256 = sha256_u16_be(array)
        masks[layer_id] = {
            "path": mask_path,
            "bbox": bbox,
            "array": array,
            "npy_sha256": sha256_file(mask_path),
            "decoded_sha256": decoded_sha256,
        }

    return {
        "config_path": config_path,
        "config_sha256": sha256_file(config_path),
        "mask_dir": mask_dir,
        "visibility": visibility,
        "name_overrides": names,
        "opacity_overrides": opacities,
        "masks": masks,
    }


def apply_final_declaration(
    psd: PSDImage,
    declaration: dict[str, object],
    *,
    expected_ids: Sequence[int] = OUTPUT_LAYER_IDS,
) -> None:
    """Aplica exclusivament els valors ja declarats; no calcula màscares."""

    layers = list(psd)
    if tuple(layer.layer_id for layer in layers) != tuple(expected_ids):
        raise AssertionError("l'arbre no coincideix amb els IDs declarats")
    by_id = {layer.layer_id: layer for layer in layers}
    visibility = declaration["visibility"]
    names = declaration["name_overrides"]
    opacities = declaration["opacity_overrides"]
    masks = declaration["masks"]
    for layer_id in expected_ids:
        layer = by_id[layer_id]
        if layer.blend_mode != BlendMode.NORMAL or layer.fill_opacity != 255:
            raise AssertionError(f"layer_id={layer_id}: només Normal/fill 100 %")
        layer.visible = visibility[layer_id]
        if layer_id in names:
            layer.name = names[layer_id]
        if layer_id in opacities:
            layer.opacity = opacities[layer_id]
    for layer_id, mask in masks.items():
        left, top, _right, _bottom = mask["bbox"]
        replace_mask_u16(
            by_id[layer_id],
            mask["array"],
            top=top,
            left=left,
        )


def final_declaration_manifest(declaration: dict[str, object]) -> dict[str, object]:
    masks = declaration["masks"]
    return {
        "config": {
            "path": str(declaration["config_path"]),
            "sha256": declaration["config_sha256"],
        },
        "mask_dir": str(declaration["mask_dir"]),
        "visibility": {
            str(layer_id): value
            for layer_id, value in declaration["visibility"].items()
        },
        "name_overrides": {
            str(layer_id): value
            for layer_id, value in declaration["name_overrides"].items()
        },
        "opacity_overrides": {
            str(layer_id): value
            for layer_id, value in declaration["opacity_overrides"].items()
        },
        "masks": {
            str(layer_id): {
                "path": str(mask["path"]),
                "bbox": list(mask["bbox"]),
                "shape": list(mask["array"].shape),
                "dtype": str(mask["array"].dtype),
                "npy_sha256": mask["npy_sha256"],
                "decoded_sha256": mask["decoded_sha256"],
            }
            for layer_id, mask in masks.items()
        },
    }


def _candidate_path_without_clobber(candidate_path: Path) -> Path:
    candidate_path = candidate_path.expanduser()
    parent = candidate_path.parent.resolve()
    candidate_path = parent / candidate_path.name
    if candidate_path.suffix.lower() != ".psb":
        raise ValueError("el candidat ha de tenir extensió .psb")
    if not parent.is_dir():
        raise FileNotFoundError(f"no existeix el directori candidat: {parent}")
    if candidate_path.exists() or candidate_path.is_symlink():
        raise FileExistsError(f"no se sobreescriu el candidat: {candidate_path}")
    return candidate_path


def save_candidate_no_clobber(
    psd: PSDImage,
    candidate_path: Path,
    *,
    expected_layer_ids: Sequence[int] | None = None,
) -> dict[str, object]:
    """Desa a staging i crea el candidat amb hard-link atòmic sense clobber."""

    candidate_path = _candidate_path_without_clobber(candidate_path)
    staging = candidate_path.parent / (
        f".{candidate_path.name}.staging-{os.getpid()}-{uuid.uuid4().hex}"
    )
    try:
        psd.save(staging, mode="xb")
        if not staging.is_file() or staging.stat().st_size == 0:
            raise AssertionError("el save de staging no ha produït un PSB")
        probe = PSDImage.open(staging)
        header = probe._record.header
        if (header.version, header.depth, header.channels) != (2, 16, 4):
            raise AssertionError("staging no és PSB RGB16 RGBA4")
        tags = document_layer_tags(probe)
        if Tag.LAYER_16 not in tags or Tag.SAVING_MERGED_TRANSPARENCY16 not in tags:
            raise AssertionError("staging ha perdut Lr16 o Mt16")
        classic = probe._record.layer_and_mask_information.layer_info
        if classic is None or classic.layer_count != 0:
            raise AssertionError("staging: la secció clàssica de capes no és buida")
        merged_channels = probe._record.image_data.get_data(header, split=True)
        expected_channel_bytes = probe.width * probe.height * 2
        if len(merged_channels) != 4 or any(
            len(channel) != expected_channel_bytes for channel in merged_channels
        ):
            raise AssertionError("staging: merged RGBA16 incomplet")
        if expected_layer_ids is not None:
            actual_ids = tuple(layer.layer_id for layer in probe)
            if actual_ids != tuple(expected_layer_ids):
                raise AssertionError(f"staging: IDs inesperats {actual_ids}")
            if any(layer_has_forbidden_structure(layer) for layer in probe):
                raise AssertionError("staging: hi ha grups, efectes o capes no píxel")
            if any(
                layer.blend_mode != BlendMode.NORMAL or layer.fill_opacity != 255
                for layer in probe
            ):
                raise AssertionError("staging: una capa no és Normal/fill 100 %")
        del merged_channels, probe
        with staging.open("rb") as stream:
            os.fsync(stream.fileno())
        # link(2) falla amb EEXIST i, a diferència de replace/rename, no pot
        # substituir un candidat creat per una altra sessió entre els checks.
        os.link(staging, candidate_path)
        receipt = {
            "path": str(candidate_path),
            "size": candidate_path.stat().st_size,
            "sha256": sha256_file(candidate_path),
            "promotion": "atomic_hard_link_no_clobber",
        }
    finally:
        if staging.exists() or staging.is_symlink():
            staging.unlink()
    return receipt


def write_json_no_clobber(path: Path, payload: dict[str, object]) -> None:
    path = path.expanduser()
    parent = path.parent.resolve()
    path = parent / path.name
    if not parent.is_dir():
        raise FileNotFoundError(f"no existeix el directori del manifest: {parent}")
    if path.exists() or path.is_symlink():
        raise FileExistsError(f"no se sobreescriu el manifest: {path}")
    created_here = False
    try:
        with path.open("x", encoding="utf-8") as stream:
            created_here = True
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        if created_here and path.exists() and path.is_file():
            path.unlink()
        raise


def build_selected_document(
    corretgint2_path: Path = DEFAULT_CORRETGINT2,
    capes_totals_v1_path: Path = DEFAULT_CAPES_TOTALS_V1,
    *,
    through_layer_id: int | None = None,
) -> tuple[PSDImage, dict[str, object]]:
    """Construeix l'arbre seleccionat en memòria; no desa res."""

    c2, ct1, manifest = validate_sources(corretgint2_path, capes_totals_v1_path)
    c2_by_id = {layer.layer_id: layer for layer in c2}
    ct1_by_id = {layer.layer_id: layer for layer in ct1}
    clones = [clone_pixel_layer_raw(ct1, c2_by_id[layer_id]) for layer_id in CORRETGINT2_LAYER_IDS]
    clones.extend(
        clone_pixel_layer_raw(ct1, ct1_by_id[layer_id])
        for layer_id in CAPES_TOTALS_SOURCE_IDS
    )
    ct1._layers = clones
    ct1._update_children()
    if through_layer_id is not None:
        set_stage_visibility(ct1, through_layer_id)
    finalize_lr16(ct1)

    if tuple(layer.layer_id for layer in ct1) != OUTPUT_LAYER_IDS:
        raise AssertionError("l'arbre seleccionat no és determinista")
    tags = document_layer_tags(ct1)
    if Tag.LAYER_16 not in tags or Tag.SAVING_MERGED_TRANSPARENCY16 not in tags:
        raise AssertionError("s'han perdut Lr16 o Mt16")
    if ct1._record.layer_and_mask_information.layer_info.layer_count != 0:
        raise AssertionError("la secció clàssica no és buida després de finalize_lr16")
    if ct1._record.header.channels != 4:
        raise AssertionError("el contenidor ja no declara quatre canals")

    manifest.update(
        {
            "status": "PREFLIGHT_PASS",
            "psb_saved": False,
            "output_layer_ids": list(OUTPUT_LAYER_IDS),
            "layer_count": len(list(ct1)),
            "visible_layer_ids": [layer.layer_id for layer in ct1 if layer.visible],
            "through_layer_id": through_layer_id,
            "document_tags_required": ["Lr16", "Mt16"],
            "merged_status": "STALE_NOT_SET",
        }
    )
    return ct1, manifest


def materialize_final_candidate(
    *,
    corretgint2_path: Path,
    capes_totals_v1_path: Path,
    config_path: Path,
    mask_dir: Path,
    work_dir: Path,
    candidate_path: Path,
    manifest_path: Path,
) -> dict[str, object]:
    """Materialitza un candidat nou a partir d'una declaració final completa."""

    candidate_path = _candidate_path_without_clobber(candidate_path)
    manifest_parent = manifest_path.expanduser().parent.resolve()
    manifest_path = manifest_parent / manifest_path.name
    if not manifest_parent.is_dir():
        raise FileNotFoundError(f"no existeix el directori del manifest: {manifest_parent}")
    if manifest_path == candidate_path:
        raise ValueError("el manifest i el candidat no poden compartir path")
    if manifest_path.exists() or manifest_path.is_symlink():
        raise FileExistsError(f"no se sobreescriu el manifest: {manifest_path}")
    work_dir = work_dir.resolve()
    if not work_dir.is_dir():
        raise FileNotFoundError("--work-dir ha de ser un directori existent")

    declaration = load_final_declaration(config_path, mask_dir)
    document, manifest = build_selected_document(
        corretgint2_path,
        capes_totals_v1_path,
    )
    original_nonmask = {
        layer.layer_id: raw_nonmask_fingerprints(layer) for layer in document
    }
    original_undeclared_masks = {
        layer.layer_id: raw_channel_fingerprints(layer).get(
            str(int(ChannelID.USER_LAYER_MASK))
        )
        for layer in document
        if layer.layer_id not in declaration["masks"]
    }
    apply_final_declaration(document, declaration)
    for layer in document:
        if raw_nonmask_fingerprints(layer) != original_nonmask[layer.layer_id]:
            raise AssertionError(f"layer_id={layer.layer_id}: raster alterat per l'estat final")
        if layer.layer_id in original_undeclared_masks:
            actual_mask = raw_channel_fingerprints(layer).get(
                str(int(ChannelID.USER_LAYER_MASK))
            )
            if actual_mask != original_undeclared_masks[layer.layer_id]:
                raise AssertionError(
                    f"layer_id={layer.layer_id}: màscara no declarada alterada"
                )

    finalize_lr16(document)
    float_path = work_dir / "merged_float32.npy"
    rgba_path = work_dir / "merged_rgba16.npy"
    rgba = compose_normal_rgba4_to_npy(
        document,
        document._record.header,
        float_path,
        rgba_path,
    )
    merged_hashes = set_merged_rgba4(document, rgba)
    manifest.update(
        {
            "status": "FINAL_CANDIDATE_READY_TO_SAVE",
            "final_declaration": final_declaration_manifest(declaration),
            "visible_layer_ids": [layer.layer_id for layer in document if layer.visible],
            "layer_state": {
                str(layer.layer_id): {
                    "name": layer.name,
                    "opacity": layer.opacity,
                    "visible": layer.visible,
                    "blend_mode": layer.blend_mode.value.decode("ascii"),
                    "fill_opacity": layer.fill_opacity,
                }
                for layer in document
            },
            "modified_mask_ids": sorted(declaration["masks"]),
            "protected_mask_ids": sorted(
                set(OUTPUT_LAYER_IDS).difference(declaration["masks"])
            ),
            "merged_status": "RGBA4_SET",
            "merged_rgba16_npy": {
                "path": str(rgba_path),
                "sha256": sha256_file(rgba_path),
                "channel_sha256": merged_hashes,
            },
            "filters_selected": [],
        }
    )
    candidate_receipt = save_candidate_no_clobber(
        document,
        candidate_path,
        expected_layer_ids=OUTPUT_LAYER_IDS,
    )
    manifest.update(
        {
            "status": "FINAL_CANDIDATE_SAVED",
            "psb_saved": True,
            "candidate": candidate_receipt,
            "manifest_path": str(manifest_path),
        }
    )
    write_json_no_clobber(manifest_path, manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Preflight en memòria o materialització final fail-closed de CapesTotalsV2."
    )
    parser.add_argument("--corretgint2", type=Path, default=DEFAULT_CORRETGINT2)
    parser.add_argument("--capes-totals-v1", type=Path, default=DEFAULT_CAPES_TOTALS_V1)
    parser.add_argument(
        "--through-layer-id",
        type=int,
        choices=OUTPUT_LAYER_IDS,
        help="opcional: estat visible acumulatiu per als pilots capa a capa",
    )
    parser.add_argument(
        "--compose-work",
        type=Path,
        help="directori existent i buit on crear merged_float32.npy i merged_rgba16.npy",
    )
    parser.add_argument(
        "--final-config",
        type=Path,
        help="JSON final estricte: visibilitat, overrides i inventari de màscares",
    )
    parser.add_argument("--mask-dir", type=Path)
    parser.add_argument("--work-dir", type=Path)
    parser.add_argument("--candidate", type=Path)
    parser.add_argument("--manifest", type=Path)
    args = parser.parse_args()

    final_values = (
        args.final_config,
        args.mask_dir,
        args.work_dir,
        args.candidate,
        args.manifest,
    )
    if any(value is not None for value in final_values):
        if any(value is None for value in final_values):
            parser.error(
                "el mode final requereix --final-config, --mask-dir, --work-dir, "
                "--candidate i --manifest"
            )
        if args.through_layer_id is not None or args.compose_work is not None:
            parser.error("el mode final no es combina amb --through-layer-id/--compose-work")
        manifest = materialize_final_candidate(
            corretgint2_path=args.corretgint2,
            capes_totals_v1_path=args.capes_totals_v1,
            config_path=args.final_config,
            mask_dir=args.mask_dir,
            work_dir=args.work_dir,
            candidate_path=args.candidate,
            manifest_path=args.manifest,
        )
        print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
        return

    document, manifest = build_selected_document(
        args.corretgint2,
        args.capes_totals_v1,
        through_layer_id=args.through_layer_id,
    )
    if args.compose_work is not None:
        work = args.compose_work.resolve()
        if not work.is_dir():
            raise SystemExit("--compose-work ha de ser un directori existent")
        float_path = work / "merged_float32.npy"
        rgba_path = work / "merged_rgba16.npy"
        rgba = compose_normal_rgba4_to_npy(
            document,
            document._record.header,
            float_path,
            rgba_path,
        )
        merged_hashes = set_merged_rgba4(document, rgba)
        manifest["merged_status"] = "IN_MEMORY_SET_NOT_SAVED"
        manifest["merged_rgba16_npy"] = {
            "path": str(rgba_path),
            "sha256": sha256_file(rgba_path),
            "channel_sha256": merged_hashes,
        }
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
