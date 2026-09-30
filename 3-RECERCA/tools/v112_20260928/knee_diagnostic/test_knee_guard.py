"""Scalar and tiny-array tests only; never constructs an image or a variant."""
import hashlib
import json
from pathlib import Path
import unittest

import numpy as np

from knee_guard import Config, G1, G1_SHA, OPS, OPS_SHA, literal_knee, wrap_knee, classify_model_capacity, audit_knee

DEST = Path(__file__).parent
SCALE = 'Smooth sigma6, VAL-normalized; effective masks unsmoothed; pre-output-clip'


def f(x):
    return np.asarray(x, dtype=np.float32)


class Tests(unittest.TestCase):
    def call(self, *, refs=((1, .8),), names=('HQ',), Fo=1, A=.2,
             B=1, gate=1, domain=True):
        config = Config(references=names)
        original = literal_knee(config)
        guarded = wrap_knee(original, config=config, model_scale=SCALE)
        args = (f(B), [(f(s), f(c)) for s, c in refs], f(A), f(A), f(Fo), 6)
        before = [x.tobytes() for x in (args[0], args[2], args[3], args[4])]
        expected = original(*args)
        returned, diagnostic = guarded(*args, active_domain=np.asarray(domain),
                                        gate=f(gate))
        for a, b in zip(expected, returned, strict=True):
            self.assertEqual(np.asarray(a).dtype, np.asarray(b).dtype)
            self.assertEqual(np.asarray(a).shape, np.asarray(b).shape)
            self.assertEqual(np.asarray(a).tobytes(), np.asarray(b).tobytes())
        self.assertEqual(before, [x.tobytes() for x in (args[0], args[2], args[3], args[4])])
        return returned, diagnostic

    def test_feasible_target(self):
        _, d = self.call(Fo=1)
        self.assertFalse(d['capacity']['infeasible_before_gate'])
        self.assertTrue(d['governing']['HQ'])
        self.assertLessEqual(abs(float(d['residual_before_limb_gate'])),
                             4 * float(np.spacing(np.float32(.8))))

    def test_infeasible_target_flag_does_not_change_output(self):
        old, d = self.call(Fo=.6)
        self.assertTrue(d['capacity']['infeasible_before_gate'])
        self.assertEqual(float(old[2]), 0)
        self.assertAlmostEqual(float(d['capacity']['excess_before_gate']), .2, places=6)
        self.assertEqual(d['achieved_before_limb_gate'], f(.6))

    def test_outside_domain_is_not_a_feasibility_failure(self):
        _, d = self.call(Fo=.6, domain=False)
        self.assertFalse(d['active'])
        self.assertFalse(d['capacity']['infeasible_before_gate'])
        self.assertEqual(float(d['capacity']['excess_before_gate']), 0)

    def test_zero_limb_gate_is_inactive(self):
        _, d = self.call(Fo=.6, gate=0)
        self.assertTrue(d['inactive_gate'])
        self.assertFalse(d['capacity']['infeasible_before_gate'])
        self.assertFalse(d['governing']['HQ'])

    def test_partial_limb_gate_residual_is_separate_from_feasibility(self):
        _, d = self.call(Fo=1, gate=.25)
        self.assertTrue(d['partial_gate'])
        self.assertFalse(d['capacity']['infeasible_before_gate'])
        self.assertGreater(float(d['residual_after_limb_gate']), 0)
        self.assertTrue(d['capacity']['infeasible_after_gate'])
        self.assertFalse(d['capacity']['floor_feasible_after_gate'])
        self.assertLess(float(d['capacity']['capacity_after_gate']), 1)

    def test_partial_gate_can_miss_a_still_attainable_floor(self):
        _, d = self.call(Fo=1, gate=.5)
        self.assertTrue(d['capacity']['floor_feasible_after_gate'])
        self.assertFalse(d['capacity']['infeasible_after_gate'])
        self.assertGreater(float(d['residual_after_limb_gate']), 0)

    def test_invalid_reference_is_domain_diagnostic(self):
        _, d = self.call(refs=((1, 0),))
        self.assertTrue(d['invalid_in_domain'])
        self.assertFalse(d['active'])
        self.assertFalse(d['capacity']['infeasible_before_gate'])

    def test_invalid_base_is_not_reported_as_capacity_failure(self):
        _, d = self.call(B=0)
        self.assertTrue(d['invalid_in_domain'])
        self.assertFalse(d['capacity']['infeasible_before_gate'])

    def test_black_other_layers_have_zero_capacity(self):
        _, d = self.call(Fo=0)
        self.assertTrue(d['active'])
        self.assertTrue(d['capacity']['infeasible_before_gate'])
        self.assertEqual(float(d['capacity']['capacity_before_gate']), 0)

    def test_max_hq_governs_but_legacy_bookkeeping_is_preserved(self):
        old, d = self.call(refs=((.5, .8), (.99, .8)), names=('SEC', 'HQ'),
                           A=.1, Fo=8/9)
        self.assertTrue(d['governing']['HQ'])
        self.assertFalse(d['governing']['SEC'])
        self.assertAlmostEqual(float(old[1]), .5, places=6)
        self.assertAlmostEqual(float(d['references'][1]['w']), .01, places=6)

    def test_max_sec_governs(self):
        _, d = self.call(refs=((.9, .8), (.5, .8)), names=('SEC', 'HQ'),
                          A=.1, Fo=8/9)
        self.assertTrue(d['governing']['SEC'])
        self.assertFalse(d['governing']['HQ'])

    def test_exact_tie_reports_both_references(self):
        _, d = self.call(refs=((.95, .8), (.95, .8)), names=('SEC', 'HQ'),
                          A=.1, Fo=8/9)
        self.assertTrue(d['governing']['SEC'])
        self.assertTrue(d['governing']['HQ'])

    def test_reversing_reference_order_preserves_correct_label(self):
        _, d = self.call(refs=((.99, .8), (.5, .8)), names=('HQ', 'SEC'),
                          A=.1, Fo=8/9)
        self.assertTrue(d['governing']['HQ'])
        self.assertFalse(d['governing']['SEC'])

    def test_tiny_mixed_array_keeps_every_original_bit(self):
        _, d = self.call(refs=((f([.5, .9, .95]), f([.8, .8, .8])),
                               (f([.99, .5, .95]), f([.8, .8, .8]))),
                          names=('SEC', 'HQ'), A=[.1, .1, .1], Fo=[8/9, 8/9, 8/9])
        np.testing.assert_array_equal(d['governing']['SEC'], [False, True, True])
        np.testing.assert_array_equal(d['governing']['HQ'], [True, False, True])

    def test_floor_below_current_is_met_without_target_equality(self):
        d = classify_model_capacity(f(.64), f(1), f(.2), f(.2), f(.5), f(1), True)
        self.assertTrue(d['floor_already_met'])
        self.assertTrue(d['floor_feasible_before_gate'])
        self.assertTrue(d['floor_feasible_after_gate'])
        self.assertFalse(d['equality_possible_before_gate'])
        self.assertFalse(d['equality_possible_after_gate'])

    def test_exact_capacity_boundary_is_feasible(self):
        d = classify_model_capacity(f(.64), f(1), f(.2), f(.2), f(1), f(1), True)
        self.assertFalse(d['infeasible_before_gate'])
        self.assertFalse(d['infeasible_after_gate'])
        self.assertTrue(d['equality_possible_after_gate'])

    def test_one_ulp_above_capacity_is_reported_without_hidden_tolerance(self):
        target = np.nextafter(f(1), f(2))
        d = classify_model_capacity(f(.64), f(1), f(.2), f(.2), target, f(1), True)
        self.assertTrue(d['infeasible_before_gate'])
        self.assertEqual(d['excess_before_gate'], target - f(1))

    def test_wrong_supplied_function_is_rejected(self):
        c = Config(references=('HQ',))
        original = literal_knee(c)
        def wrong(*args):
            result = list(original(*args))
            result[2] = f(0)
            return tuple(result)
        guarded = wrap_knee(wrong, config=c, model_scale=SCALE)
        with self.assertRaisesRegex(RuntimeError, 'differs'):
            guarded(f(1), [(f(1), f(.8))], f(.2), f(.2), f(1), 6,
                    active_domain=True, gate=f(1))

    def test_sidecar_records_config_iterations_sources_and_comparison_scope(self):
        _, d = self.call()
        self.assertEqual(d['n'], 6)
        self.assertEqual(d['config'], dict(references=('HQ',), beta=1., epsilon=.03,
            soft_gate_width=.01, sec_weight_on_w=True, hq_without_soft_gate=True,
            piecewise_h=True))
        self.assertEqual(d['g1_sha256'], G1_SHA)
        self.assertEqual(d['ops_sha256'], OPS_SHA)
        self.assertIs(d['output_tuple_matches_supplied_function'], True)
        self.assertNotIn('bound_to_supplied_function', d)
        _, unbound = audit_knee(f(1), [(f(1), f(.8))], f(.2), f(.2), f(1),
            active_domain=True, gate=f(1), model_scale=SCALE,
            config=Config(references=('HQ',)))
        self.assertIsNone(unbound['output_tuple_matches_supplied_function'])

    def test_scale_description_is_mandatory(self):
        c = Config(references=('HQ',))
        guarded = wrap_knee(literal_knee(c), config=c, model_scale='')
        with self.assertRaisesRegex(ValueError, 'scale'):
            guarded(f(1), [(f(1), f(.8))], f(.2), f(.2), f(1), 6,
                    active_domain=True, gate=f(1))


if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Tests))
    receipt = dict(
        scope='Scalar/tiny-array diagnostic tests only. No image or physical-sky PASS.',
        tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
        successful=result.wasSuccessful(),
        producer_unchanged=hashlib.sha256(G1.read_bytes()).hexdigest() == G1_SHA,
        helpers_unchanged=hashlib.sha256(OPS.read_bytes()).hexdigest() == OPS_SHA,
        files={p.name: hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (DEST/'knee_guard.py', Path(__file__))},
        failures_detail=[(str(case), detail) for case, detail in result.failures + result.errors],
        limitations=[
            'Only local frozen knee formula exercised, not smoothing, sky estimation or a full raster.',
            'Input model scale, domain and actual limb gate are caller declarations, not independently verified here.',
            'Infeasible means target exceeds this operator capacity; it does not prove the sky model is physical.',
            'Gate-aware capacity is distinguished from pre-gate capacity; partial gate can make a pre-gate attainable target unreachable by design.',
            'Floor below currentFp is already met: target equality is a separate predicate, never a requirement for floor satisfaction.',
            'Clipping of final raster, changing smooth gain and other Photoshop layers can alter actual retention/floor.',
            'Strict comparisons have no tuned tolerance; tiny positive floating excess remains visible as raw diagnostic.',
            'SEC/HQ ties are explicit. Original D/w return values are deliberately not corrected; use sidecar references.',
            'Use bounded scalar/stripe calls. This helper reads frozen code but never imports the full producer.',
        ],
    )
    (DEST/'TEST_RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')
    raise SystemExit(0 if result.wasSuccessful() else 1)
