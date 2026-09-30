"""Contractes purs del pilot Vixen LDIC.

No hi ha I/O de càmera ni escriptura de productes en aquest mòdul. Les
funcions existeixen perquè els ordres de calibratge, registre i suma es puguin
provar amb fixtures petites abans de llegir cap RAW.
"""

from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
from scipy.stats import t as student_t


RAW_CROP_Y_X_H_W = (108, 172, 4640, 6960)
CFA4_SHAPE = (4, 2320, 3480)
DARK_LEGACY_SHAPE = (4638, 6958)
MOSAIC_SHAPE = (4640, 6960)
CFA_ORDER = ("R", "G1", "G2", "B")
PHYSICAL_LONG_EXPOSURE_S = 10.079368399159
CANVAS_SCALE_ARCSEC_PX = 2.1494813525884373
REGISTRATION_LIMIT_PX = 0.3


class ContractError(RuntimeError):
    """Una precondició física o d'auditoria no es compleix."""


def is_finite_real(value: object) -> bool:
    return (
        not isinstance(value, (bool, np.bool_))
        and isinstance(value, (int, float, np.integer, np.floating))
        and math.isfinite(float(value))
    )


def physical_exposure_s(exp_nominal: float, manifest_exp_s: float) -> float:
    """Aplica l'autoritat MakerNote S6 sense mutar el manifest històric."""
    if math.isclose(exp_nominal, 10.0, rel_tol=0.0, abs_tol=1e-9):
        return PHYSICAL_LONG_EXPOSURE_S
    return float(manifest_exp_s)


def pad_dark_to_mosaic(dark: np.ndarray) -> np.ndarray:
    """Porta el dark històric a forma completa sense inventar la vora absent."""
    if dark.shape == MOSAIC_SHAPE:
        full = np.asarray(dark)
        if (
            not np.all(np.isfinite(full[:-2, :-2]))
            or not np.all(np.isnan(full[-2:, :]))
            or not np.all(np.isnan(full[:, -2:]))
        ):
            raise ContractError(
                "dark full-grid no autoritzat: el contracte actual exigeix interior finit i vora absent NaN"
            )
        return full
    if dark.shape != DARK_LEGACY_SHAPE:
        raise ContractError(
            f"dark amb forma {dark.shape}; esperada {DARK_LEGACY_SHAPE} o {MOSAIC_SHAPE}"
        )
    if not np.all(np.isfinite(dark)):
        raise ContractError("dark legacy conté valors no finits")
    out = np.full(MOSAIC_SHAPE, np.nan, dtype=np.result_type(dark.dtype, np.float32))
    out[:-2, :-2] = dark
    return out


def cfa4_to_mosaic(flat_cfa4: np.ndarray) -> np.ndarray:
    """Expandeix R,G1,G2,B a un mosaic RGGB 4640x6960 sense interpolar."""
    if flat_cfa4.shape != CFA4_SHAPE:
        raise ContractError(f"flat CFA4 amb forma {flat_cfa4.shape}; esperada {CFA4_SHAPE}")
    if not np.all(np.isfinite(flat_cfa4)) or np.any(flat_cfa4 <= 0):
        raise ContractError("flat CFA4 no finit o no positiu")
    out = np.empty(MOSAIC_SHAPE, dtype=np.float32)
    out[0::2, 0::2] = flat_cfa4[0]
    out[0::2, 1::2] = flat_cfa4[1]
    out[1::2, 0::2] = flat_cfa4[2]
    out[1::2, 1::2] = flat_cfa4[3]
    return out


def calibrate_cfa(
    raw_crop: np.ndarray, dark: np.ndarray, flat_cfa4: np.ndarray
) -> np.ndarray:
    """Calibratge lineal obligatori: (RAW - dark_amb_pedestal) / flat.

    No resta 511,5 una segona vegada, no retalla negatius i no desbayera.
    """
    if raw_crop.shape != MOSAIC_SHAPE:
        raise ContractError(f"RAW amb forma {raw_crop.shape}; esperada {MOSAIC_SHAPE}")
    dark_full = pad_dark_to_mosaic(dark)
    flat = cfa4_to_mosaic(flat_cfa4)
    return (raw_crop.astype(np.float32) - dark_full.astype(np.float32)) / flat


def affine_frame_to_canvas(
    sun_xy: Sequence[float],
    pa_north_deg: float,
    frame_scale_arcsec_px: float,
    canvas_center_xy: Sequence[float] = (0.0, 0.0),
    canvas_scale_arcsec_px: float = CANVAS_SCALE_ARCSEC_PX,
) -> np.ndarray:
    """Transformació `afi`: fotograma -> nord amunt, Sol al centre."""
    numeric = np.asarray(
        [*sun_xy, pa_north_deg, frame_scale_arcsec_px, *canvas_center_xy, canvas_scale_arcsec_px],
        dtype=np.float64,
    )
    if numeric.size != 7 or not np.all(np.isfinite(numeric)):
        raise ContractError("paràmetres afins no finits o amb longitud invàlida")
    if float(frame_scale_arcsec_px) <= 0 or float(canvas_scale_arcsec_px) <= 0:
        raise ContractError("escala afí no positiva")
    pa = math.radians(float(pa_north_deg))
    rotation = np.array(
        [[math.cos(pa), math.sin(pa)], [-math.sin(pa), math.cos(pa)]],
        dtype=np.float64,
    )
    linear = (float(frame_scale_arcsec_px) / float(canvas_scale_arcsec_px)) * rotation
    translation = np.asarray(canvas_center_xy, dtype=np.float64) - linear @ np.asarray(
        sun_xy, dtype=np.float64
    )
    return np.hstack((linear, translation[:, None]))


def project_points(matrix_2x3: np.ndarray, xy: np.ndarray) -> np.ndarray:
    matrix = np.asarray(matrix_2x3, dtype=np.float64)
    points = np.asarray(xy, dtype=np.float64)
    if matrix.shape != (2, 3) or points.ndim != 2 or points.shape[1] != 2:
        raise ContractError("matriu o punts amb forma invàlida")
    return (matrix[:, :2] @ points.T).T + matrix[:, 2]


def common_canvas_from_perimeters(
    frames: Sequence[Mapping[str, float]], kernel_support_px: int = 0
) -> dict[str, object]:
    """Deriva un rectangle simètric de la unió de tots els perímetres.

    `kernel_support_px` és explícit; no hi ha una mida de llenç escrita a mà.
    """
    if not frames:
        raise ContractError("cal almenys un fotograma")
    if (
        isinstance(kernel_support_px, (bool, np.bool_))
        or not isinstance(kernel_support_px, (int, np.integer))
        or int(kernel_support_px) < 0
    ):
        raise ContractError("kernel_support_px ha de ser un enter no negatiu")
    all_points = []
    for frame in frames:
        try:
            width_value = float(frame["width"])
            height_value = float(frame["height"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ContractError("amplada/alçada de fotograma invàlida") from exc
        if not np.isfinite(width_value) or not np.isfinite(height_value):
            raise ContractError("amplada/alçada de fotograma no finita")
        width, height = int(width_value), int(height_value)
        if (
            isinstance(frame["width"], (bool, np.bool_))
            or isinstance(frame["height"], (bool, np.bool_))
            or width_value != width
            or height_value != height
            or width <= 0
            or height <= 0
        ):
            raise ContractError("amplada/alçada de fotograma no positiva")
        matrix = affine_frame_to_canvas(
            (float(frame["sun_x"]), float(frame["sun_y"])),
            float(frame["pa_north_deg"]),
            float(frame["scale_arcsec_px"]),
        )
        # Per a l'afí verificat, els quatre vèrtexs són tot el perímetre convex.
        corners = np.array(
            [
                [0.0, 0.0],
                [width - 1.0, 0.0],
                [width - 1.0, height - 1.0],
                [0.0, height - 1.0],
            ],
            dtype=np.float64,
        )
        all_points.append(project_points(matrix, corners))
    points = np.vstack(all_points)
    support = int(kernel_support_px)
    min_x, max_x = float(points[:, 0].min()) - support, float(points[:, 0].max()) + support
    min_y, max_y = float(points[:, 1].min()) - support, float(points[:, 1].max()) + support
    half_width = int(math.ceil(max(abs(min_x), abs(max_x))))
    half_height = int(math.ceil(max(abs(min_y), abs(max_y))))
    # Convenció explícita de centres de píxel: índexs 0..W-1 i Sol a l'índex
    # enter half_width. Per això cal el +1; sense ell el vèrtex positiu cau fora.
    width, height = 2 * half_width + 1, 2 * half_height + 1
    return {
        "width": width,
        "height": height,
        "center_xy": [float(half_width), float(half_height)],
        "kernel_support_px": support,
        "coordinate_convention": "pixel centres 0..W-1/0..H-1; input corners 0..w-1/0..h-1; Sun at integer centre",
        "bounds_about_sun_xy": [
            min_x,
            min_y,
            max_x,
            max_y,
        ],
    }


def registration_gate(
    residuals_by_frame: Mapping[str, np.ndarray],
    validation_points_by_frame: Mapping[str, np.ndarray] | None = None,
    *,
    expected_frame_ids: Sequence[str] | None = None,
    expected_order_sha256: str | None = None,
    held_out: bool = False,
    limit_px: float = REGISTRATION_LIMIT_PX,
    min_points_per_frame: int = 8,
    min_radial_span_px: float = 1000.0,
    min_azimuth_quadrants: int = 4,
) -> dict[str, object]:
    """Porta held-out per fotograma i global, amb cobertura de camp.

    Els punts de validació s'expressen respecte del Sol del llenç. Un punt al
    centre no pot provar gir, escala o distorsió i per tant és UNDECIDABLE.
    """
    if not residuals_by_frame:
        raise ContractError("porta de registre sense residus")
    if not isinstance(held_out, (bool, np.bool_)):
        raise ContractError("held_out ha de ser booleà explícit")
    if (
        not is_finite_real(limit_px)
        or limit_px <= 0
        or isinstance(min_points_per_frame, (bool, np.bool_))
        or not isinstance(min_points_per_frame, (int, np.integer))
        or min_points_per_frame < 1
        or not is_finite_real(min_radial_span_px)
        or min_radial_span_px < 0
        or isinstance(min_azimuth_quadrants, (bool, np.bool_))
        or not isinstance(min_azimuth_quadrants, (int, np.integer))
        or not 1 <= min_azimuth_quadrants <= 4
    ):
        raise ContractError("llindars de registre invàlids")
    if not held_out:
        return {"status": "UNDECIDABLE_NOT_HELD_OUT", "limit_px": float(limit_px)}
    if expected_frame_ids is None or expected_order_sha256 is None:
        return {
            "status": "UNDECIDABLE_MISSING_FROZEN_FRAME_SET",
            "limit_px": float(limit_px),
        }
    expected_ids = [str(value) for value in expected_frame_ids]
    actual_ids = list(residuals_by_frame)
    if (
        frame_order_sha256(expected_ids) != expected_order_sha256
        or actual_ids != expected_ids
    ):
        return {
            "status": "FAIL_FRAME_SET_OR_ORDER_DIVERGENCE",
            "limit_px": float(limit_px),
            "expected_count": len(expected_ids),
            "actual_count": len(actual_ids),
        }
    if validation_points_by_frame is None:
        return {
            "status": "UNDECIDABLE_MISSING_VALIDATION_GEOMETRY",
            "limit_px": float(limit_px),
        }
    if list(validation_points_by_frame) != expected_ids:
        raise ContractError("ordre/conjunt de geometria de validació divergent")
    per_frame: dict[str, float] = {}
    coverage: dict[str, object] = {}
    insufficient_coverage = []
    concatenated_distances = []
    for name, values in residuals_by_frame.items():
        residuals = np.asarray(values, dtype=np.float64)
        if residuals.ndim != 2 or residuals.shape[1] != 2 or residuals.size == 0:
            raise ContractError(f"residus invàlids per {name}")
        if not np.all(np.isfinite(residuals)):
            raise ContractError(f"residus no finits per {name}")
        if name not in validation_points_by_frame:
            raise ContractError(f"falten punts de validació per {name}")
        points = np.asarray(validation_points_by_frame[name], dtype=np.float64)
        if points.shape != residuals.shape or not np.all(np.isfinite(points)):
            raise ContractError(f"punts de validació invàlids per {name}")
        radii = np.hypot(points[:, 0], points[:, 1])
        radial_span = float(np.max(radii) - np.min(radii))
        angles = np.mod(np.arctan2(points[:, 1], points[:, 0]), 2 * np.pi)
        quadrants = int(np.unique(np.floor(angles / (0.5 * np.pi)).astype(int)).size)
        enough = (
            points.shape[0] >= min_points_per_frame
            and radial_span >= min_radial_span_px
            and quadrants >= min_azimuth_quadrants
        )
        coverage[name] = {
            "points": int(points.shape[0]),
            "radial_span_px": radial_span,
            "azimuth_quadrants": quadrants,
            "status": "PASS" if enough else "INSUFFICIENT",
        }
        if not enough:
            insufficient_coverage.append(name)
        distances = np.hypot(residuals[:, 0], residuals[:, 1])
        scale = float(np.max(distances))
        per_frame[name] = (
            0.0
            if scale == 0.0
            else float(scale * np.sqrt(np.mean((distances / scale) ** 2)))
        )
        concatenated_distances.append(distances)
    joined_distances = np.concatenate(concatenated_distances)
    global_scale = float(np.max(joined_distances))
    global_rms = (
        0.0
        if global_scale == 0.0
        else float(
            global_scale
            * np.sqrt(np.mean((joined_distances / global_scale) ** 2))
        )
    )
    if not np.isfinite(global_rms) or any(not np.isfinite(value) for value in per_frame.values()):
        raise ContractError("overflow al càlcul RMS de registre")
    failed = sorted(name for name, value in per_frame.items() if value > limit_px)
    if failed or global_rms > limit_px:
        status = "FAIL"
    elif insufficient_coverage:
        status = "UNDECIDABLE_INSUFFICIENT_FIELD_COVERAGE"
    else:
        status = "PASS"
    return {
        "status": status,
        "limit_px": float(limit_px),
        "global_rms_px": global_rms,
        "per_frame_rms_px": per_frame,
        "failed_frames": failed,
        "coverage_by_frame": coverage,
        "insufficient_coverage_frames": sorted(insufficient_coverage),
        "held_out": True,
    }


def flat_regression_gate(
    predictor_log_flat_ratio: np.ndarray,
    observed_log_signal_ratio: np.ndarray,
    *,
    block_ids: np.ndarray | None = None,
    expected_block_ids: Sequence[int] | None = None,
    domain_mask: np.ndarray | None = None,
    min_n: int = 100,
    min_blocks: int = 8,
    min_p95_p05: float = 0.01,
    beta_interval: tuple[float, float] = (0.95, 1.05),
    min_r2: float = 0.95,
) -> dict[str, object]:
    """Porta Vixen proposada; la manca de palanca és UNDECIDABLE, mai PASS."""
    x = np.asarray(predictor_log_flat_ratio, dtype=np.float64).ravel()
    y = np.asarray(observed_log_signal_ratio, dtype=np.float64).ravel()
    if domain_mask is None:
        return {"status": "UNDECIDABLE_MISSING_EXPLICIT_DOMAIN", "n": int(x.size)}
    raw_domain = np.asarray(domain_mask)
    if raw_domain.dtype != np.dtype(bool):
        raise ContractError("domain_mask ha de ser booleà")
    domain = raw_domain.ravel()
    if domain.shape != x.shape or y.shape != x.shape:
        raise ContractError("domini/x/y no tenen la mateixa forma al gate del flat")
    if not np.any(domain):
        return {"status": "UNDECIDABLE_EMPTY_DOMAIN", "n": 0}
    if np.any(~np.isfinite(x[domain])) or np.any(~np.isfinite(y[domain])):
        return {"status": "FAIL_NONFINITE_INSIDE_DOMAIN", "n": int(np.count_nonzero(domain))}
    if block_ids is None:
        return {
            "status": "UNDECIDABLE_MISSING_INDEPENDENT_BLOCKS",
            "n": int(np.count_nonzero(domain)),
        }
    if (
        isinstance(min_n, (bool, np.bool_))
        or not isinstance(min_n, (int, np.integer))
        or min_n < 3
        or isinstance(min_blocks, (bool, np.bool_))
        or not isinstance(min_blocks, (int, np.integer))
        or min_blocks < 2
        or not is_finite_real(min_p95_p05)
        or min_p95_p05 <= 0
        or len(beta_interval) != 2
        or any(not is_finite_real(value) for value in beta_interval)
        or beta_interval[0] >= beta_interval[1]
        or not is_finite_real(min_r2)
        or not 0 <= min_r2 <= 1
    ):
        raise ContractError("llindars del gate del flat invàlids")
    blocks = np.asarray(block_ids).ravel()
    if blocks.shape != x.shape:
        raise ContractError("block_ids no coincideix amb les mostres del flat")
    if not np.issubdtype(blocks.dtype, np.integer) or np.any(blocks < 0):
        raise ContractError("block_ids ha de contenir només enters no negatius")
    if expected_block_ids is None:
        return {
            "status": "UNDECIDABLE_MISSING_PREDECLARED_BLOCK_SET",
            "n": int(np.count_nonzero(domain)),
        }
    expected_blocks = np.asarray(expected_block_ids)
    if (
        expected_blocks.ndim != 1
        or expected_blocks.size == 0
        or not np.issubdtype(expected_blocks.dtype, np.integer)
        or np.any(expected_blocks < 0)
        or np.unique(expected_blocks).size != expected_blocks.size
    ):
        raise ContractError("expected_block_ids invàlid")
    x, y, blocks = x[domain], y[domain], blocks[domain]
    unique_blocks = np.unique(blocks)
    if not np.array_equal(unique_blocks, np.sort(expected_blocks)):
        return {
            "status": "UNDECIDABLE_PREDECLARED_BLOCK_COVERAGE",
            "n": int(x.size),
            "expected_blocks": int(expected_blocks.size),
            "observed_blocks": int(unique_blocks.size),
        }
    block_counts = np.asarray([np.count_nonzero(blocks == block) for block in unique_blocks])
    leverage = float(np.percentile(x, 95) - np.percentile(x, 5)) if x.size else 0.0
    base = {
        "n": int(x.size),
        "independent_blocks": int(unique_blocks.size),
        "minimum_samples_per_block": int(block_counts.min()) if block_counts.size else 0,
        "p95_minus_p05": leverage,
    }
    if (
        x.size < min_n
        or unique_blocks.size < min_blocks
        or np.any(block_counts < 2)
        or leverage < min_p95_p05
        or float(np.var(x)) <= 0.0
    ):
        return {**base, "status": "UNDECIDABLE_INSUFFICIENT_LEVERAGE"}
    design = np.column_stack((np.ones_like(x), x))
    with np.errstate(over="ignore", invalid="ignore"):
        coefficients, *_ = np.linalg.lstsq(design, y, rcond=None)
        fitted = design @ coefficients
        residual = y - fitted
        ss_res = float(np.sum(residual * residual))
        ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    if (
        not np.all(np.isfinite(coefficients))
        or not np.all(np.isfinite(residual))
        or not np.isfinite(ss_res)
        or not np.isfinite(ss_tot)
    ):
        raise ContractError("overflow o regressió no finita al gate del flat")
    if ss_tot <= 0:
        return {**base, "status": "UNDECIDABLE_NO_OBSERVED_VARIANCE"}
    r2 = 1.0 - ss_res / ss_tot
    # Covariància sandwich agrupada: els píxels d'un mateix tile no compten
    # com observacions independents. Els block_ids s'han de predeclarar.
    bread = np.linalg.inv(design.T @ design)
    meat = np.zeros((2, 2), dtype=np.float64)
    for block in unique_blocks:
        score = design[blocks == block].T @ residual[blocks == block]
        meat += np.outer(score, score)
    correction = (unique_blocks.size / (unique_blocks.size - 1)) * (
        (x.size - 1) / (x.size - 2)
    )
    covariance = correction * bread @ meat @ bread
    if not np.all(np.isfinite(covariance)):
        raise ContractError("covariància no finita al gate del flat")
    beta = float(coefficients[1])
    beta_se = float(math.sqrt(max(covariance[1, 1], 0.0)))
    critical = float(student_t.ppf(0.975, unique_blocks.size - 1))
    ci95 = [beta - critical * beta_se, beta + critical * beta_se]
    passed = (
        beta_interval[0] <= beta <= beta_interval[1]
        and ci95[0] >= beta_interval[0]
        and ci95[1] <= beta_interval[1]
        and r2 >= min_r2
    )
    return {
        **base,
        "status": "PASS" if passed else "FAIL",
        "intercept": float(coefficients[0]),
        "beta": beta,
        "beta_ci95": ci95,
        "ci_distribution": f"Student t with {unique_blocks.size - 1} df",
        "ci_critical": critical,
        "r2": r2,
        "requirements": {
            "beta_interval": list(beta_interval),
            "ci95_inside_interval": True,
            "min_r2": min_r2,
            "min_n": min_n,
            "min_independent_blocks": min_blocks,
            "min_p95_minus_p05": min_p95_p05,
        },
    }


def frame_order_sha256(frame_ids: Sequence[str]) -> str:
    ids = [str(value) for value in frame_ids]
    if not ids or any(not value or "\n" in value for value in ids) or len(set(ids)) != len(ids):
        raise ContractError("ordre de frames buit, duplicat o invàlid")
    return hashlib.sha256(("\n".join(ids) + "\n").encode("utf-8")).hexdigest()


def ldic_payload_sha256(image: np.ndarray, weight: np.ndarray) -> str:
    """Hash canònic del parell J_i/w_i d'un fotograma de la suma LDIC."""
    value = np.ascontiguousarray(np.asarray(image, dtype="<f8"))
    w = np.ascontiguousarray(np.asarray(weight, dtype="<f8"))
    if value.shape != w.shape:
        raise ContractError("J_i i w_i no tenen la mateixa forma")
    digest = hashlib.sha256()
    digest.update(b"PILOT_VIXEN_LDIC_J_W_V1\0")
    digest.update(json_shape(value.shape))
    digest.update(value.tobytes(order="C"))
    digest.update(w.tobytes(order="C"))
    return digest.hexdigest()


def json_shape(shape: Sequence[int]) -> bytes:
    """Codificació mínima i inequívoca d'una shape per a hashes de payload."""
    return (",".join(str(int(value)) for value in shape) + "\0").encode("ascii")


def ldic_payload_hashes(
    images: np.ndarray, weights: np.ndarray, frame_ids: Sequence[str]
) -> dict[str, str]:
    values = np.asarray(images)
    w = np.asarray(weights)
    ids = [str(value) for value in frame_ids]
    frame_order_sha256(ids)
    if values.shape != w.shape or values.ndim < 2 or values.shape[0] != len(ids):
        raise ContractError("payload LDIC incompatible amb els frame_ids")
    return {
        frame_id: ldic_payload_sha256(values[index], w[index])
        for index, frame_id in enumerate(ids)
    }


def ldic_sum(
    images: np.ndarray,
    weights: np.ndarray,
    *,
    frame_ids: Sequence[str],
    expected_order_sha256: str,
    expected_payload_sha256_by_frame: Mapping[str, str],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Una única suma additiva en un ordre congelat i hashejat.

    `images` ja conté J_i = k_i f_i + q_i. S'usa suma compensada de Neumaier
    per al numerador; l'ordre continua essent part explícita del rebut.
    """
    values = np.asarray(images, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64)
    if values.shape != w.shape:
        raise ContractError("imatges i pesos han de tenir la mateixa forma")
    if values.ndim < 2 or values.shape[0] == 0 or np.any(~np.isfinite(w)) or np.any(w < 0):
        raise ContractError("pesos invàlids")
    ids = [str(value) for value in frame_ids]
    actual_order_sha256 = frame_order_sha256(ids)
    if len(ids) != values.shape[0] or actual_order_sha256 != expected_order_sha256:
        raise ContractError("ordre de frames divergent del hash congelat")
    actual_payload_hashes = ldic_payload_hashes(values, w, ids)
    if (
        list(expected_payload_sha256_by_frame) != ids
        or actual_payload_hashes != dict(expected_payload_sha256_by_frame)
    ):
        raise ContractError("payload J_i/w_i divergent dels hashes congelats")
    if np.any((w > 0) & ~np.isfinite(values)):
        raise ContractError("valor no finit amb pes positiu a la suma LDIC")
    # Fora de cobertura J_i pot ser NaN, però només és neutral si w_i és zero.
    safe_values = np.where(w > 0, values, 0.0)
    numerator = np.zeros(values.shape[1:], dtype=np.float64)
    compensation = np.zeros_like(numerator)
    denominator = np.zeros_like(numerator)
    with np.errstate(over="ignore", invalid="ignore"):
        for index in range(values.shape[0]):
            contribution = w[index] * safe_values[index]
            total = numerator + contribution
            compensation += np.where(
                np.abs(numerator) >= np.abs(contribution),
                (numerator - total) + contribution,
                (contribution - total) + numerator,
            )
            numerator = total
            denominator += w[index]
        numerator += compensation
    if (
        np.any(~np.isfinite(numerator))
        or np.any(~np.isfinite(denominator))
        or np.any(~np.isfinite(compensation))
    ):
        raise ContractError("overflow o estat no finit a l'acumulador LDIC")
    composite = np.full_like(numerator, np.nan, dtype=np.float64)
    np.divide(numerator, denominator, out=composite, where=denominator > 0)
    return numerator, denominator, composite


def max_relative_deviation(
    actual: np.ndarray, expected: np.ndarray, relative_floor: float
) -> float:
    """Desviació F relativa amb un floor declarat, mai un error absolut."""
    a = np.asarray(actual, dtype=np.float64)
    e = np.asarray(expected, dtype=np.float64)
    if a.shape != e.shape or not is_finite_real(relative_floor) or relative_floor <= 0:
        raise ContractError("forma o floor invàlid a la porta F")
    if a.size == 0 or np.any(~np.isfinite(a)) or np.any(~np.isfinite(e)):
        raise ContractError("porta F sense domini finit i no buit")
    denominator = np.maximum(np.abs(e), float(relative_floor))
    return float(np.max(np.abs(a - e) / denominator))


def quadratic_axis_plane_degeneracy_error(
    center_a_xy: Sequence[float] = (0.0, 0.0),
    center_b_xy: Sequence[float] = (137.0, -83.0),
) -> float:
    """Demostra la degeneració exacta eix/pla d'un flat radial quadràtic."""
    cx, cy = map(float, center_a_xy)
    nx, ny = map(float, center_b_xy)
    constant, radial, plane_x, plane_y = 0.17, -2.1e-8, 7.0e-6, -4.0e-6
    new_plane_x = plane_x + 2.0 * radial * (nx - cx)
    new_plane_y = plane_y + 2.0 * radial * (ny - cy)
    new_constant = constant + radial * (cx * cx + cy * cy - nx * nx - ny * ny)
    yy, xx = np.mgrid[-500:501:23, -700:701:29]
    a = constant + radial * ((xx - cx) ** 2 + (yy - cy) ** 2) + plane_x * xx + plane_y * yy
    b = (
        new_constant
        + radial * ((xx - nx) ** 2 + (yy - ny) ** 2)
        + new_plane_x * xx
        + new_plane_y * yy
    )
    return float(np.max(np.abs(a - b)))


def assert_exclusive_output(path: Path) -> None:
    """Falla abans d'escriure si un build ID ja existeix."""
    if path.exists() or path.is_symlink():
        raise ContractError(f"output preexistent: {path}")
