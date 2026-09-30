from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np

from contracts import (
    CFA4_SHAPE,
    DARK_LEGACY_SHAPE,
    MOSAIC_SHAPE,
    PHYSICAL_LONG_EXPOSURE_S,
    ContractError,
    affine_frame_to_canvas,
    assert_exclusive_output,
    calibrate_cfa,
    cfa4_to_mosaic,
    common_canvas_from_perimeters,
    flat_regression_gate,
    frame_order_sha256,
    ldic_payload_hashes,
    ldic_sum,
    max_relative_deviation,
    pad_dark_to_mosaic,
    physical_exposure_s,
    project_points,
    quadratic_axis_plane_degeneracy_error,
    registration_gate,
)


class CalibrationContracts(unittest.TestCase):
    def test_physical_long_exposure_authority(self) -> None:
        self.assertEqual(physical_exposure_s(10.0, 10.3), PHYSICAL_LONG_EXPOSURE_S)
        self.assertEqual(physical_exposure_s(2.0, 2.0), 2.0)

    def test_dark_padding_is_only_bottom_and_right_edge(self) -> None:
        dark = np.arange(np.prod(DARK_LEGACY_SHAPE), dtype=np.float32).reshape(DARK_LEGACY_SHAPE)
        full = pad_dark_to_mosaic(dark)
        self.assertEqual(full.shape, MOSAIC_SHAPE)
        np.testing.assert_array_equal(full[:-2, :-2], dark)
        self.assertTrue(np.all(np.isnan(full[-2:, :])))
        self.assertTrue(np.all(np.isnan(full[:, -2:])))

    def test_cfa_order_rggb(self) -> None:
        flat = np.empty(CFA4_SHAPE, np.float32)
        for channel, value in enumerate((1.0, 2.0, 3.0, 4.0)):
            flat[channel].fill(value)
        mosaic = cfa4_to_mosaic(flat)
        self.assertTrue(np.all(mosaic[0::2, 0::2] == 1.0))
        self.assertTrue(np.all(mosaic[0::2, 1::2] == 2.0))
        self.assertTrue(np.all(mosaic[1::2, 0::2] == 3.0))
        self.assertTrue(np.all(mosaic[1::2, 1::2] == 4.0))

    def test_dark_already_contains_pedestal(self) -> None:
        raw = np.full(MOSAIC_SHAPE, 612.0, np.float32)
        dark = np.full(DARK_LEGACY_SHAPE, 512.0, np.float32)
        flat = np.full(CFA4_SHAPE, 2.0, np.float32)
        calibrated = calibrate_cfa(raw, dark, flat)
        self.assertTrue(np.all(calibrated[:-2, :-2] == 50.0))
        self.assertTrue(np.all(np.isnan(calibrated[-2:, :])))
        self.assertTrue(np.all(np.isnan(calibrated[:, -2:])))
        self.assertTrue(
            np.any(
                calibrated[:-2, :-2]
                != (raw - 512.0 - pad_dark_to_mosaic(dark))[:-2, :-2] / 2.0
            )
        )

    def test_padding_then_calibration_cannot_revalidate_missing_dark_border(self) -> None:
        raw = np.full(MOSAIC_SHAPE, 612.0, np.float32)
        legacy = np.full(DARK_LEGACY_SHAPE, 512.0, np.float32)
        padded = pad_dark_to_mosaic(legacy)
        flat = np.ones(CFA4_SHAPE, np.float32)
        calibrated = calibrate_cfa(raw, padded, flat)
        self.assertTrue(np.all(np.isnan(calibrated[-2:, :])))
        self.assertTrue(np.all(np.isnan(calibrated[:, -2:])))
        with self.assertRaises(ContractError):
            calibrate_cfa(raw, np.full(MOSAIC_SHAPE, 512.0, np.float32), flat)

    def test_flat_before_warp_is_not_flat_after_warp(self) -> None:
        # Valor al mig d'una interpolació lineal de dos píxels.
        raw = np.array([2.0, 8.0])
        flat = np.array([1.0, 2.0])
        correct = np.mean(raw / flat)
        forbidden = np.mean(raw) / np.mean(flat)
        self.assertNotAlmostEqual(correct, forbidden)


class GeometryContracts(unittest.TestCase):
    @staticmethod
    def field_points() -> np.ndarray:
        angles = np.linspace(0, 2 * np.pi, 8, endpoint=False)
        return np.vstack(
            [
                np.column_stack((radius * np.cos(angles), radius * np.sin(angles)))
                for radius in (1000.0, 3000.0)
            ]
        )

    def test_affine_places_sun_at_requested_center(self) -> None:
        matrix = affine_frame_to_canvas((123.25, 456.75), 57.195, 2.1494813525884373, (500, 600))
        projected = project_points(matrix, np.array([[123.25, 456.75]]))[0]
        np.testing.assert_allclose(projected, [500, 600], atol=1e-12)

    def test_canvas_is_derived_and_contains_every_corner(self) -> None:
        frames = [
            {"width": 100, "height": 60, "sun_x": 30, "sun_y": 20, "pa_north_deg": 0, "scale_arcsec_px": 2.1494813525884373},
            {"width": 100, "height": 60, "sun_x": 70, "sun_y": 40, "pa_north_deg": 90, "scale_arcsec_px": 2.1494813525884373},
        ]
        canvas = common_canvas_from_perimeters(frames, kernel_support_px=4)
        self.assertEqual(canvas["width"] % 2, 1)
        self.assertEqual(canvas["height"] % 2, 1)
        self.assertGreaterEqual(canvas["width"], 2 * 4)
        self.assertGreaterEqual(canvas["height"], 2 * 4)

    def test_canvas_positive_edge_and_kernel_support_are_inside(self) -> None:
        frame = {
            "width": 100,
            "height": 60,
            "sun_x": 0,
            "sun_y": 0,
            "pa_north_deg": 0,
            "scale_arcsec_px": 2.1494813525884373,
        }
        canvas = common_canvas_from_perimeters([frame], kernel_support_px=4)
        cx, cy = canvas["center_xy"]
        self.assertLessEqual(cx + 99 + 4, canvas["width"] - 1)
        self.assertLessEqual(cy + 59 + 4, canvas["height"] - 1)
        for invalid in (-1, 1.5, True):
            with self.assertRaises(ContractError):
                common_canvas_from_perimeters([frame], kernel_support_px=invalid)

    def test_registration_threshold_controls(self) -> None:
        points = self.field_points()
        r299 = np.tile([0.299, 0.0], (len(points), 1))
        r301 = np.tile([0.301, 0.0], (len(points), 1))
        expected = ["a"]
        order_hash = frame_order_sha256(expected)
        self.assertEqual(registration_gate(
            {"a": r299}, {"a": points}, held_out=True,
            expected_frame_ids=expected, expected_order_sha256=order_hash,
        )["status"], "PASS")
        self.assertEqual(registration_gate(
            {"a": r301}, {"a": points}, held_out=True,
            expected_frame_ids=expected, expected_order_sha256=order_hash,
        )["status"], "FAIL")
        for override in (
            {"limit_px": True},
            {"min_radial_span_px": True},
            {"held_out": "false"},
            {"held_out": 1},
        ):
            with self.subTest(override=override):
                kwargs = {
                    "held_out": True,
                    "expected_frame_ids": expected,
                    "expected_order_sha256": order_hash,
                }
                kwargs.update(override)
                with self.assertRaises(ContractError):
                    registration_gate({"a": r299}, {"a": points}, **kwargs)

    def test_registration_needs_held_out_field_coverage(self) -> None:
        result = registration_gate(
            {"a": np.array([[0.0, 0.0]])},
            {"a": np.array([[0.0, 0.0]])},
            held_out=True,
            expected_frame_ids=["a"],
            expected_order_sha256=frame_order_sha256(["a"]),
        )
        self.assertEqual(result["status"], "UNDECIDABLE_INSUFFICIENT_FIELD_COVERAGE")
        result = registration_gate(
            {"a": np.zeros((8, 2))},
            {"a": np.zeros((8, 2))},
            held_out=False,
        )
        self.assertEqual(result["status"], "UNDECIDABLE_NOT_HELD_OUT")

    def test_global_rms_cannot_hide_one_bad_frame(self) -> None:
        points = self.field_points()
        residuals = {f"ok{i}": np.zeros_like(points) for i in range(67)}
        residuals["bad"] = np.tile([2.0, 0.0], (len(points), 1))
        validation = {name: points for name in residuals}
        ids = list(residuals)
        result = registration_gate(
            residuals,
            validation,
            held_out=True,
            expected_frame_ids=ids,
            expected_order_sha256=frame_order_sha256(ids),
        )
        self.assertLess(result["global_rms_px"], 0.3)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["failed_frames"], ["bad"])


class GateAndLdicContracts(unittest.TestCase):
    def test_axis_plane_degeneracy_is_exact(self) -> None:
        self.assertLess(quadratic_axis_plane_degeneracy_error(), 1e-12)

    def test_flat_gate_positive_and_bad_controls(self) -> None:
        x = np.linspace(-0.03, 0.03, 1000)
        blocks = np.arange(x.size) % 20
        expected_blocks = np.arange(20)
        domain = np.ones_like(x, dtype=bool)
        good = flat_regression_gate(
            x, x, block_ids=blocks, expected_block_ids=expected_blocks, domain_mask=domain
        )
        inverse = flat_regression_gate(
            -x, x, block_ids=blocks, expected_block_ids=expected_blocks, domain_mask=domain
        )
        no_flat = flat_regression_gate(
            np.zeros_like(x), x, block_ids=blocks,
            expected_block_ids=expected_blocks, domain_mask=domain
        )
        self.assertEqual(good["status"], "PASS")
        self.assertEqual(inverse["status"], "FAIL")
        self.assertEqual(no_flat["status"], "UNDECIDABLE_INSUFFICIENT_LEVERAGE")

    def test_flat_gate_cannot_pass_without_independent_blocks(self) -> None:
        x = np.linspace(-0.03, 0.03, 1000)
        result = flat_regression_gate(x, x, domain_mask=np.ones_like(x, dtype=bool))
        self.assertEqual(result["status"], "UNDECIDABLE_MISSING_INDEPENDENT_BLOCKS")

    def test_flat_gate_uses_student_t_and_rejects_nonfinite_domain(self) -> None:
        x0 = np.linspace(-0.03, 0.03, 100)
        slopes = 1 + 0.06 * np.array([-1.5, -1, -0.5, -0.2, 0.2, 0.5, 1, 1.5])
        x = np.tile(x0, 8)
        blocks = np.repeat(np.arange(8), 100)
        y = x * slopes[blocks]
        domain = np.ones_like(x, dtype=bool)
        result = flat_regression_gate(
            x, y, block_ids=blocks, expected_block_ids=np.arange(8), domain_mask=domain
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertGreater(result["ci_critical"], 1.96)
        y[0] = np.nan
        result = flat_regression_gate(
            x, y, block_ids=blocks, expected_block_ids=np.arange(8), domain_mask=domain
        )
        self.assertEqual(result["status"], "FAIL_NONFINITE_INSIDE_DOMAIN")

    def test_flat_gate_rejects_nan_block_id_false_pass_fixture(self) -> None:
        x0 = np.linspace(-0.03, 0.03, 100)
        x = np.tile(x0, 8)
        true_blocks = np.repeat(np.arange(8), 100)
        slopes = np.array([1 - 0.15 / 7] * 7 + [1 + 0.15])
        y = x * slopes[true_blocks]
        invalid_blocks = true_blocks.astype(float)
        invalid_blocks[invalid_blocks == 7] = np.nan
        with self.assertRaises(ContractError):
            flat_regression_gate(
                x,
                y,
                block_ids=invalid_blocks,
                expected_block_ids=np.arange(8),
                domain_mask=np.ones_like(x, dtype=bool),
            )

    def test_flat_gate_rejects_nonfinite_or_untyped_threshold_bypasses(self) -> None:
        x = np.linspace(-0.03, 0.03, 1000)
        blocks = np.arange(x.size) % 20
        kwargs = {
            "block_ids": blocks,
            "expected_block_ids": np.arange(20),
            "domain_mask": np.ones_like(x, dtype=bool),
        }
        for override in (
            {"min_p95_p05": np.nan},
            {"min_p95_p05": True},
            {"min_n": np.nan},
            {"min_blocks": np.nan},
            {"min_n": True},
            {"min_blocks": 2.0},
            {"min_r2": False},
            {"beta_interval": (False, 1.05)},
        ):
            with self.subTest(override=override):
                with self.assertRaises(ContractError):
                    flat_regression_gate(x, x, **kwargs, **override)

    def test_single_ldic_sum_is_order_invariant(self) -> None:
        images = np.array([[1.0, 10.0], [3.0, 6.0], [8.0, 2.0]])
        weights = np.array([[1.0, 0.5], [2.0, 1.0], [0.25, 4.0]])
        ids = ["a", "b", "c"]
        order_hash = frame_order_sha256(ids)
        payload_hashes = ldic_payload_hashes(images, weights, ids)
        n1, d1, g1 = ldic_sum(
            images, weights, frame_ids=ids, expected_order_sha256=order_hash,
            expected_payload_sha256_by_frame=payload_hashes,
        )
        n2, d2, g2 = ldic_sum(
            images, weights, frame_ids=ids, expected_order_sha256=order_hash,
            expected_payload_sha256_by_frame=payload_hashes,
        )
        np.testing.assert_allclose(n1, n2)
        np.testing.assert_allclose(d1, d2)
        np.testing.assert_allclose(g1, g2)
        with self.assertRaises(ContractError):
            ldic_sum(
                images[::-1],
                weights[::-1],
                frame_ids=ids[::-1],
                expected_order_sha256=order_hash,
                expected_payload_sha256_by_frame=payload_hashes,
            )
        with self.assertRaises(ContractError):
            ldic_sum(
                images[::-1],
                weights[::-1],
                frame_ids=ids,
                expected_order_sha256=order_hash,
                expected_payload_sha256_by_frame=payload_hashes,
            )

    def test_compensated_ldic_sum_handles_cancellation_in_frozen_order(self) -> None:
        images = np.array([[1e16], [-1e16], [1.0]])
        weights = np.ones_like(images)
        ids = ["large-positive", "large-negative", "unit"]
        payload_hashes = ldic_payload_hashes(images, weights, ids)
        numerator, _, _ = ldic_sum(
            images,
            weights,
            frame_ids=ids,
            expected_order_sha256=frame_order_sha256(ids),
            expected_payload_sha256_by_frame=payload_hashes,
        )
        self.assertEqual(numerator[0], 1.0)

    def test_zero_weight_nan_is_neutral_but_positive_weight_nan_fails(self) -> None:
        images = np.array([[np.nan, 2.0], [4.0, 6.0]])
        weights = np.array([[0.0, 1.0], [1.0, 1.0]])
        ids = ["a", "b"]
        payload_hashes = ldic_payload_hashes(images, weights, ids)
        numerator, denominator, composite = ldic_sum(
            images,
            weights,
            frame_ids=ids,
            expected_order_sha256=frame_order_sha256(ids),
            expected_payload_sha256_by_frame=payload_hashes,
        )
        np.testing.assert_allclose(numerator, [4.0, 8.0])
        np.testing.assert_allclose(denominator, [1.0, 2.0])
        np.testing.assert_allclose(composite, [4.0, 4.0])
        weights[0, 0] = 0.1
        with self.assertRaises(ContractError):
            ldic_sum(
                images,
                weights,
                frame_ids=ids,
                expected_order_sha256=frame_order_sha256(ids),
                expected_payload_sha256_by_frame=ldic_payload_hashes(images, weights, ids),
            )

    def test_ldic_overflow_fails_closed(self) -> None:
        images = np.array([[1e308], [1e308]])
        weights = np.ones_like(images)
        ids = ["a", "b"]
        with self.assertRaises(ContractError):
            ldic_sum(
                images,
                weights,
                frame_ids=ids,
                expected_order_sha256=frame_order_sha256(ids),
                expected_payload_sha256_by_frame=ldic_payload_hashes(images, weights, ids),
            )

    def test_double_mask_control_fails_relative_gate(self) -> None:
        images = np.array([[2.0, 5.0], [4.0, 9.0]])
        weights = np.array([[0.25, 0.75], [0.80, 0.40]])
        ids = ["a", "b"]
        order_hash = frame_order_sha256(ids)
        payload_hashes = ldic_payload_hashes(images, weights, ids)
        _, _, expected = ldic_sum(
            images, weights, frame_ids=ids, expected_order_sha256=order_hash,
            expected_payload_sha256_by_frame=payload_hashes,
        )
        double_images = images * weights
        _, _, double_masked = ldic_sum(
            double_images,
            weights,
            frame_ids=ids,
            expected_order_sha256=order_hash,
            expected_payload_sha256_by_frame=ldic_payload_hashes(double_images, weights, ids),
        )
        self.assertGreater(max_relative_deviation(double_masked, expected, 1e-9), 1e-3)

    def test_relative_gate_not_absolute(self) -> None:
        expected = np.array([1e-8, 1e2])
        actual = expected * 1.0005
        self.assertLess(max_relative_deviation(actual, expected, 1e-12), 1e-3)

    def test_relative_gate_rejects_nan_instead_of_passing_vacuously(self) -> None:
        with self.assertRaises(ContractError):
            max_relative_deviation(np.array([np.nan]), np.array([1.0]), 1e-12)
        with self.assertRaises(ContractError):
            max_relative_deviation(np.array([999.0]), np.array([1.0]), np.inf)
        with self.assertRaises(ContractError):
            max_relative_deviation(np.array([0.0015]), np.array([0.001]), True)

    def test_no_clobber(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "build"
            assert_exclusive_output(path)
            path.mkdir()
            with self.assertRaises(ContractError):
                assert_exclusive_output(path)


if __name__ == "__main__":
    unittest.main()
