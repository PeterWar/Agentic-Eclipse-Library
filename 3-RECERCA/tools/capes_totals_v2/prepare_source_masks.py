"""Prepara les màscares font u16 de CapesTotalsV2; no crea cap PSB.

El flux és deliberadament separat del builder del document:

1. extreu les màscares raster de ``CapesTotalsV1`` en enters u16, sense cap
   round-trip float;
2. aplica una gaussiana local determinista de sigma 48 px només a ID9/ID11;
3. aplica conjuntament, de baix cap amunt, ``T_q`` per a P3 i després P4 als
   set nous ``FONT_HDR`` admesos;
4. escriu set ``mask_<id>.npy`` u16 i un rebut JSON. ID17 queda en quarantena,
   oculta, byte-idèntica i sense cap màscara derivada.

No hi ha cap crida a ``PSDImage.save`` ni cap mutació dels PSB font.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np
from psd_tools import PSDImage
from scipy import ndimage as ndi


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_capes_totals_v2 as build  # noqa: E402

sys.path.insert(0, str(HERE.parent / "corretgint2"))
from build_corretgint2 import joint_protect_stack_u16  # noqa: E402


FRAME = (457, 463, 7417, 5103)  # left, top, right, bottom
FRAME_W = FRAME[2] - FRAME[0]
FRAME_H = FRAME[3] - FRAME[1]

PROCESSED_IDS = (8, 9, 10, 11, 12, 13, 16)
BLUR_IDS = (9, 11)
NO_BLUR_IDS = (8, 10, 12, 13, 16)
QUARANTINE_ID = 17

GAUSSIAN_SIGMA_PX = 48.0
GAUSSIAN_TRUNCATE = 4.0
DOMAIN_RADIUS_SIGMA = 3.0
GRADIENT_QUANTILE = 0.90
GRADIENT_ABSOLUTE_FLOOR = 2.0 / 65535.0

DEFAULT_WORK11 = (
    HERE.parent
    / "corretgint2"
    / ".build_perles_D2896CDB"
    / "work11"
)

WORK11_INPUTS = {
    "protected_core_layer_3.npy": {
        "dtype": "bool",
        "array_sha256": "42bb5022358d325e7411ceaac175b428180d55c78eed25048df648f5b1791148",
    },
    "protected_gate_layer_3.npy": {
        "dtype": "float32",
        "array_sha256": "769d2fdb06f16c162bb9103e4910860acff263e8d2cf4112137962d14865fb99",
    },
    "protected_core_layer_4.npy": {
        "dtype": "bool",
        "array_sha256": "1647bd9fbedd5789239c590d56a0456c3a10e98bfab309e569c42a95269cab7c",
    },
    "protected_gate_layer_4_u16.npy": {
        "dtype": "uint16",
        "array_sha256": "72f128ecb06937028d1c1e58962820796e89d679cfbe73f900d61e6c0d0e13e6",
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_array_native(array: np.ndarray, chunk_rows: int = 192) -> str:
    """Hash del payload ndarray natiu, per reproduir els pins de work11."""

    digest = hashlib.sha256()
    if array.ndim == 0:
        digest.update(np.ascontiguousarray(array).tobytes())
        return digest.hexdigest()
    for row0 in range(0, array.shape[0], chunk_rows):
        row1 = min(array.shape[0], row0 + chunk_rows)
        digest.update(np.ascontiguousarray(array[row0:row1]).tobytes())
    return digest.hexdigest()


def sha256_u16_be(array: np.ndarray, chunk_rows: int = 192) -> str:
    """Hash canònic independent de l'endianness per a una màscara u16."""

    if array.dtype != np.uint16 or array.ndim != 2:
        raise TypeError("sha256_u16_be exigeix una màscara uint16 2-D")
    digest = hashlib.sha256()
    for row0 in range(0, array.shape[0], chunk_rows):
        row1 = min(array.shape[0], row0 + chunk_rows)
        digest.update(np.ascontiguousarray(array[row0:row1]).astype(">u2").tobytes())
    return digest.hexdigest()


def _new_memmap(path: Path, shape: tuple[int, int], dtype) -> np.memmap:
    if path.exists():
        raise FileExistsError(f"no se sobreescriu: {path}")
    return np.lib.format.open_memmap(path, mode="w+", dtype=dtype, shape=shape)


def _coverage_rect(layer) -> tuple[int, int, int, int]:
    left = max(0, int(layer.left))
    top = max(0, int(layer.top))
    right = min(build.WIDTH, int(layer.right))
    bottom = min(build.HEIGHT, int(layer.bottom))
    if left >= right or top >= bottom:
        raise AssertionError(f"layer_id={layer.layer_id}: cobertura buida")
    return left, top, right, bottom


def extract_mask_canvas_u16(layer, header, output_path: Path) -> dict[str, object]:
    """Expandeix la màscara CT1 al llenç només amb assignacions enteres.

    Fora del bbox real del raster la cobertura és zero, encara que el
    ``background_color`` de la màscara sigui blanc. Dins cobertura, els
    píxels fora del bbox explícit de la màscara prenen ``background*257``.
    """

    decoded, mask_data = build._decoded_mask_u16(layer, header)
    if decoded is None or mask_data is None:
        raise AssertionError(f"layer_id={layer.layer_id}: falta màscara font")
    canvas = _new_memmap(output_path, (build.HEIGHT, build.WIDTH), np.uint16)
    canvas[:] = 0
    left, top, right, bottom = _coverage_rect(layer)
    canvas[top:bottom, left:right] = np.uint16(mask_data.background_color * 257)

    x0 = max(left, int(mask_data.left))
    y0 = max(top, int(mask_data.top))
    x1 = min(right, int(mask_data.right))
    y1 = min(bottom, int(mask_data.bottom))
    if x0 < x1 and y0 < y1:
        canvas[y0:y1, x0:x1] = decoded[
            y0 - mask_data.top : y1 - mask_data.top,
            x0 - mask_data.left : x1 - mask_data.left,
        ]
    canvas.flush()

    outside_nonzero = (
        int(np.count_nonzero(canvas[:top]))
        + int(np.count_nonzero(canvas[bottom:]))
        + int(np.count_nonzero(canvas[top:bottom, :left]))
        + int(np.count_nonzero(canvas[top:bottom, right:]))
    )
    if outside_nonzero:
        raise AssertionError(
            f"layer_id={layer.layer_id}: la màscara ha sortit de cobertura"
        )
    receipt = {
        "source_mask_bbox": [
            int(mask_data.left),
            int(mask_data.top),
            int(mask_data.right),
            int(mask_data.bottom),
        ],
        "source_background_color": int(mask_data.background_color),
        "coverage_bbox": [left, top, right, bottom],
        "dtype": "uint16",
        "shape": [build.HEIGHT, build.WIDTH],
        "min": int(canvas.min()),
        "max": int(canvas.max(initial=0)),
        "nonzero_pixels": int(np.count_nonzero(canvas)),
        "outside_coverage_nonzero_pixels": outside_nonzero,
        "u16_be_sha256": sha256_u16_be(canvas),
    }
    del canvas
    receipt["npy_sha256"] = sha256_file(output_path)
    return receipt


def frame_coverage(layer) -> np.ndarray:
    left, top, right, bottom = _coverage_rect(layer)
    coverage = np.zeros((FRAME_H, FRAME_W), dtype=bool)
    x0 = max(FRAME[0], left)
    y0 = max(FRAME[1], top)
    x1 = min(FRAME[2], right)
    y1 = min(FRAME[3], bottom)
    if x0 < x1 and y0 < y1:
        coverage[y0 - FRAME[1] : y1 - FRAME[1], x0 - FRAME[0] : x1 - FRAME[0]] = True
    return coverage


def copy_canvas_frame_u16(canvas_path: Path, frame_path: Path) -> None:
    source = np.load(canvas_path, mmap_mode="r")
    if source.shape != (build.HEIGHT, build.WIDTH) or source.dtype != np.uint16:
        raise AssertionError(f"màscara de llenç inesperada: {canvas_path}")
    target = _new_memmap(frame_path, (FRAME_H, FRAME_W), np.uint16)
    target[:] = source[FRAME[1] : FRAME[3], FRAME[0] : FRAME[2]]
    target.flush()
    del target, source


def quantize_half_up_u16(values: np.ndarray) -> np.ndarray:
    return np.clip(
        np.floor(np.asarray(values, dtype=np.float64) * 65535.0 + 0.5),
        0,
        65535,
    ).astype(np.uint16)


def local_gaussian_gradient_domain_u16(
    source_path: Path,
    output_path: Path,
    domain_path: Path,
    coverage: np.ndarray,
    protected_union: np.ndarray,
) -> dict[str, object]:
    """Gaussiana sigma48 només al domini explícit de gradients forts.

    El 10 % superior dels gradients no nuls és la llavor. La zona editable és
    la seva distància euclidiana estrictament menor que 3 sigma. Un
    ``smootherstep`` porta el pes a zero a la frontera; fora del domini es
    copien els enters font byte a byte. Després es reimposa cobertura zero.
    """

    source = np.load(source_path, mmap_mode="r")
    if source.shape != (FRAME_H, FRAME_W) or source.dtype != np.uint16:
        raise AssertionError("màscara pre-gaussiana inesperada")
    if coverage.shape != source.shape or protected_union.shape != source.shape:
        raise AssertionError("geometria de domini inesperada")

    alpha = source.astype(np.float32)
    alpha *= np.float32(1.0 / 65535.0)
    # El pilot calculava gradients i gaussiana sobre una alfa ja fail-closed
    # als nuclis protegits i fora de cobertura. T_q en farà després la
    # imposició jeràrquica exacta sobre la pila completa.
    alpha[protected_union] = 0.0
    alpha[~coverage] = 0.0
    gx = ndi.sobel(alpha, axis=1, mode="nearest")
    gy = ndi.sobel(alpha, axis=0, mode="nearest")
    strength = np.hypot(gx, gy).astype(np.float32)
    del gx, gy
    eligible = coverage & ~protected_union & (strength > GRADIENT_ABSOLUTE_FLOOR)
    positive = strength[eligible]
    if positive.size == 0:
        raise AssertionError("domini gaussià sense gradients elegibles")
    threshold = max(
        GRADIENT_ABSOLUTE_FLOOR,
        float(np.quantile(positive, GRADIENT_QUANTILE)),
    )
    seed = eligible & (strength >= threshold)
    del strength, positive, eligible
    if not np.any(seed):
        raise AssertionError("domini gaussià sense llavor")

    radius = int(math.ceil(DOMAIN_RADIUS_SIGMA * GAUSSIAN_SIGMA_PX))
    distance = ndi.distance_transform_edt(~seed)
    domain = (distance < radius) & coverage
    taper = np.clip((radius - distance) / radius, 0.0, 1.0).astype(np.float32)
    weight = taper * taper * taper * (taper * (taper * 6.0 - 15.0) + 10.0)
    del taper, distance
    blurred = ndi.gaussian_filter(
        alpha,
        sigma=GAUSSIAN_SIGMA_PX,
        mode="nearest",
        truncate=GAUSSIAN_TRUNCATE,
    )
    mixed = alpha[domain] + (blurred[domain] - alpha[domain]) * weight[domain]
    mixed_u16 = quantize_half_up_u16(mixed)

    target = _new_memmap(output_path, (FRAME_H, FRAME_W), np.uint16)
    target[:] = source
    target[domain] = mixed_u16
    target[~coverage] = 0
    target.flush()
    changed_outside_domain = int(
        np.count_nonzero((target != source) & ~domain)
    )
    outside_coverage_nonzero = int(np.count_nonzero(target[~coverage]))
    if changed_outside_domain or outside_coverage_nonzero:
        raise AssertionError(
            "gaussiana local no fail-closed: "
            f"fora_domini={changed_outside_domain}, "
            f"fora_cobertura={outside_coverage_nonzero}"
        )

    domain_file = _new_memmap(domain_path, (FRAME_H, FRAME_W), np.bool_)
    domain_file[:] = domain
    domain_file.flush()
    receipt = {
        "sigma_px": GAUSSIAN_SIGMA_PX,
        "truncate_sigma": GAUSSIAN_TRUNCATE,
        "domain_radius_sigma": DOMAIN_RADIUS_SIGMA,
        "gradient_quantile": GRADIENT_QUANTILE,
        "gradient_absolute_floor": GRADIENT_ABSOLUTE_FLOOR,
        "gradient_threshold": threshold,
        "seed_pixels": int(np.count_nonzero(seed)),
        "seed_sha256": sha256_array_native(seed),
        "domain_pixels": int(np.count_nonzero(domain)),
        "domain_sha256": sha256_array_native(domain),
        "domain_npy": str(domain_path),
        "domain_npy_sha256": sha256_file(domain_path),
        "changed_pixels": int(np.count_nonzero(target != source)),
        "changed_outside_domain": changed_outside_domain,
        "outside_coverage_nonzero_pixels": outside_coverage_nonzero,
        "output_u16_be_sha256": sha256_u16_be(target),
        "output_npy_sha256": sha256_file(output_path),
    }
    del (
        source,
        alpha,
        seed,
        domain,
        weight,
        blurred,
        mixed,
        mixed_u16,
        target,
        domain_file,
    )
    return receipt


def load_work11(work11: Path) -> tuple[dict[str, np.ndarray], dict[str, object]]:
    arrays: dict[str, np.ndarray] = {}
    receipt: dict[str, object] = {}
    for name, pin in WORK11_INPUTS.items():
        path = work11 / name
        if not path.is_file():
            raise FileNotFoundError(f"falta work11: {path}")
        value = np.load(path, mmap_mode="r")
        if value.shape != (FRAME_H, FRAME_W) or str(value.dtype) != pin["dtype"]:
            raise AssertionError(
                f"work11 inesperat {name}: {value.shape} {value.dtype}"
            )
        actual = sha256_array_native(value)
        if actual != pin["array_sha256"]:
            raise AssertionError(
                f"work11 ha canviat {name}: {actual} != {pin['array_sha256']}"
            )
        arrays[name] = value
        receipt[name] = {
            "path": str(path),
            "dtype": str(value.dtype),
            "shape": list(value.shape),
            "array_sha256": actual,
            "npy_sha256": sha256_file(path),
        }
    return arrays, receipt


def write_full_final_mask(
    frame_path: Path,
    output_path: Path,
    coverage: np.ndarray,
    core3: np.ndarray,
    core4: np.ndarray,
) -> dict[str, object]:
    frame = np.load(frame_path, mmap_mode="r")
    if frame.shape != (FRAME_H, FRAME_W) or frame.dtype != np.uint16:
        raise AssertionError("màscara final de frame inesperada")
    final_frame = np.asarray(frame, dtype=np.uint16).copy()
    before_core3 = int(np.count_nonzero(final_frame[core3]))
    before_core4 = int(np.count_nonzero(final_frame[core4]))
    final_frame[core3 | core4] = 0
    final_frame[~coverage] = 0
    if before_core3 or before_core4:
        raise AssertionError(
            "T_q no havia forçat els nuclis exactes: "
            f"P3={before_core3}, P4={before_core4}"
        )

    canvas = _new_memmap(output_path, (build.HEIGHT, build.WIDTH), np.uint16)
    canvas[:] = 0
    canvas[FRAME[1] : FRAME[3], FRAME[0] : FRAME[2]] = final_frame
    canvas.flush()
    receipt = {
        "path": str(output_path),
        "dtype": "uint16",
        "shape": [build.HEIGHT, build.WIDTH],
        "nonzero_pixels": int(np.count_nonzero(canvas)),
        "core3_nonzero_pixels": int(np.count_nonzero(final_frame[core3])),
        "core4_nonzero_pixels": int(np.count_nonzero(final_frame[core4])),
        "outside_coverage_nonzero_pixels": int(
            np.count_nonzero(final_frame[~coverage])
        ),
        "u16_be_sha256": sha256_u16_be(canvas),
        "npy_sha256": sha256_file(output_path),
    }
    del frame, final_frame, canvas
    return receipt


def validate_source(path: Path) -> tuple[PSDImage, dict[int, object], dict[str, object]]:
    path = path.resolve()
    build._validate_file_pin(
        path,
        build.CAPES_TOTALS_V1_SIZE,
        build.CAPES_TOTALS_V1_SHA256,
    )
    psd = PSDImage.open(path)
    build._validate_header(psd, expected_channels=4, label="CapesTotalsV1")
    ids = tuple(layer.layer_id for layer in psd)
    if ids != build.CAPES_TOTALS_ALL_IDS:
        raise AssertionError(f"ordre CT1 inesperat: {ids}")
    by_id = build._validate_selected_layers(
        psd,
        build.CAPES_TOTALS_SOURCE_IDS,
        "CapesTotalsV1",
    )
    for layer_id in PROCESSED_IDS:
        layer = by_id[layer_id]
        if tuple(layer.bbox) != FRAME:
            raise AssertionError(
                f"layer_id={layer_id}: bbox no canònic {tuple(layer.bbox)}"
            )
        if layer.opacity != 255:
            raise AssertionError(f"layer_id={layer_id}: opacitat no és 100 %")
    quarantine = by_id[QUARANTINE_ID]
    if quarantine.visible or quarantine.opacity != 173:
        raise AssertionError(
            "ID17 ja no coincideix amb la quarantena viva hidden/173"
        )
    return psd, by_id, {
        "path": str(path),
        "size": path.stat().st_size,
        "sha256": build.CAPES_TOTALS_V1_SHA256,
        "layer_ids": list(ids),
    }


def prepare_masks(source_path: Path, work11: Path, output_dir: Path) -> dict[str, object]:
    output_dir = output_dir.resolve()
    if output_dir.exists():
        raise FileExistsError(f"no se sobreescriu: {output_dir}")
    psd, by_id, source_receipt = validate_source(source_path)
    gates, work11_receipt = load_work11(work11.resolve())
    # No deixem ni tan sols un directori buit si una font o un gate fixat no
    # passa la validació fail-closed.
    output_dir.mkdir(parents=True, exist_ok=False)
    work_dir = output_dir / "work"
    final_mask_dir = output_dir / "final_masks"
    work_dir.mkdir()
    final_mask_dir.mkdir()
    core3 = gates["protected_core_layer_3.npy"]
    gate3 = gates["protected_gate_layer_3.npy"]
    core4 = gates["protected_core_layer_4.npy"]
    gate4_u16 = gates["protected_gate_layer_4_u16.npy"]
    protected_union = np.asarray(core3 | core4, dtype=bool)

    layers: dict[str, object] = {}
    preprotect_paths: list[Path] = []
    coverages: dict[int, np.ndarray] = {}
    for layer_id in PROCESSED_IDS:
        layer = by_id[layer_id]
        source_mask_path = work_dir / f"mask_{layer_id}_source_u16.npy"
        extraction = extract_mask_canvas_u16(
            layer,
            psd._record.header,
            source_mask_path,
        )
        coverage = frame_coverage(layer)
        coverages[layer_id] = coverage
        raw_frame_path = work_dir / f"mask_{layer_id}_source_frame_u16.npy"
        copy_canvas_frame_u16(source_mask_path, raw_frame_path)
        if layer_id in BLUR_IDS:
            preprotect = work_dir / f"mask_{layer_id}_sigma48_frame_u16.npy"
            domain_path = work_dir / f"domain_{layer_id}_sigma48.npy"
            gaussian = local_gaussian_gradient_domain_u16(
                raw_frame_path,
                preprotect,
                domain_path,
                coverage,
                protected_union,
            )
        else:
            preprotect = raw_frame_path
            gaussian = {
                "sigma_px": 0,
                "status": "BYTE_EXACT_NO_BLUR",
                "output_u16_be_sha256": sha256_u16_be(
                    np.load(preprotect, mmap_mode="r")
                ),
                "output_npy_sha256": sha256_file(preprotect),
            }
        preprotect_paths.append(preprotect)
        layers[str(layer_id)] = {
            "source_name": layer.name,
            "source_visible": bool(layer.visible),
            "source_opacity": int(layer.opacity),
            "source_mask_npy": str(source_mask_path),
            "preprotect_frame_npy": str(preprotect),
            "extraction_integer_only": extraction,
            "gaussian": gaussian,
        }

    # P3 governa conjuntament tota la pila nova. No es multiplica cap màscara
    # independentment: T_q preserva el coeficient Normal de cada font.
    p3_paths = [work_dir / f"mask_{layer_id}_p3_frame_u16.npy" for layer_id in PROCESSED_IDS]
    p3_stats = joint_protect_stack_u16(
        preprotect_paths,
        gate3,
        core3,
        p3_paths,
        list(PROCESSED_IDS),
        "P3_PERLES_DIAMANT_NEW_SOURCES",
    )

    # P4 s'aplica després sobre les alfas ja transformades per P3. El gate u16
    # de work11 és l'autoritat; la vista float només satisfà la interfície.
    gate4 = gate4_u16.astype(np.float32) * np.float32(1.0 / 65535.0)
    p4_paths = [work_dir / f"mask_{layer_id}_p4_frame_u16.npy" for layer_id in PROCESSED_IDS]
    p4_stats = joint_protect_stack_u16(
        p3_paths,
        gate4,
        core4,
        p4_paths,
        list(PROCESSED_IDS),
        "P4_LIMBE_PROTUBERANCIES_NEW_SOURCES",
        gate_u16_authority=gate4_u16,
    )
    del gate4

    for layer_id, p4_path in zip(PROCESSED_IDS, p4_paths):
        final_path = final_mask_dir / f"mask_{layer_id}.npy"
        layers[str(layer_id)]["final"] = write_full_final_mask(
            p4_path,
            final_path,
            coverages[layer_id],
            core3,
            core4,
        )

    # ID17 no es decodifica ni es reencodifica. El builder conservarà el seu
    # LayerRecord i tots els ChannelData crus; aquests fingerprints fixen la
    # quarantena, incloent el canal de màscara comprimit.
    quarantine = by_id[QUARANTINE_ID]
    quarantine_channels = build.raw_channel_fingerprints(quarantine)
    mask_channel_key = str(int(build.ChannelID.USER_LAYER_MASK))
    if mask_channel_key not in quarantine_channels:
        raise AssertionError("ID17 de quarantena ha perdut el canal de màscara")
    layers[str(QUARANTINE_ID)] = {
        "source_name": quarantine.name,
        "source_visible": bool(quarantine.visible),
        "source_opacity": int(quarantine.opacity),
        "source_fill_opacity": int(quarantine.fill_opacity),
        "source_blend_mode": str(quarantine.blend_mode),
        "source_bbox": list(quarantine.bbox),
        "source_raw_channel_fingerprints": quarantine_channels,
        "source_raw_mask_channel_fingerprint": quarantine_channels[
            mask_channel_key
        ],
        "status": "UNCHANGED_RAW",
        "quarantine_policy": "HIDDEN_NOT_TQ_NOT_ENABLE",
        "derived_mask_written": False,
    }

    expected_final_names = {
        f"mask_{layer_id}.npy" for layer_id in PROCESSED_IDS
    }
    actual_final_names = {path.name for path in final_mask_dir.iterdir()}
    if actual_final_names != expected_final_names:
        raise AssertionError(
            "final_masks no és canònic: "
            f"actual={sorted(actual_final_names)}, "
            f"esperat={sorted(expected_final_names)}"
        )

    manifest = {
        "status": "MASKS_PREPARED_NO_PSB_SAVED",
        "source": source_receipt,
        "work11": work11_receipt,
        "frame": list(FRAME),
        "layers_bottom_to_top_tq": list(PROCESSED_IDS),
        "blur_ids_sigma48": list(BLUR_IDS),
        "no_blur_ids": list(NO_BLUR_IDS),
        "quarantine_hidden_ids": [QUARANTINE_ID],
        "directories": {
            "work": str(work_dir),
            "final_masks": str(final_mask_dir),
        },
        "final_mask_files": sorted(expected_final_names),
        "joint_transforms": {"P3": p3_stats, "P4": p4_stats},
        "layers": layers,
        "psb_saved": False,
    }
    manifest_path = output_dir / "mask_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest["manifest"] = {
        "path": str(manifest_path),
        "sha256": sha256_file(manifest_path),
    }
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prepara màscares u16 per a CapesTotalsV2; no desa cap PSB."
    )
    parser.add_argument(
        "--capes-totals-v1",
        type=Path,
        default=build.DEFAULT_CAPES_TOTALS_V1,
    )
    parser.add_argument("--work11", type=Path, default=DEFAULT_WORK11)
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="directori nou; el programa refusa sobreescriure'l",
    )
    args = parser.parse_args()
    manifest = prepare_masks(
        args.capes_totals_v1,
        args.work11,
        args.output_dir,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
