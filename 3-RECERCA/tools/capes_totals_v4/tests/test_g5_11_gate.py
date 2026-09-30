import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from g5_11_gate import (  # noqa: E402
    CHAIN_IDS,
    FOUNDATION_STATES,
    artifact_record,
    artifact_record_matches,
    candidate_pass,
    coverage_gate_snapshot,
    coverage_report_pass,
    coverage_snapshot_pass,
    foundation_gate,
    g5_10_snapshot,
    promotion_gate,
    seal_g5_10_reports,
    seal_pass,
    seal_reports,
)


SHA_A = "a" * 64


def artifact(name, sha=SHA_A):
    return {"path": f"/sealed/{name}.npy", "sha256": sha}


def coverage(state="S8", ok=True, n_bad=0, n_cells=100, min_cov=0.9):
    return {
        "state": state,
        "ok": ok,
        "zones": {
            "lunar_R+3_a_1.5Rsun": {"n_cells": n_cells, "n_bad": n_bad, "min_cobertura": min_cov},
            "solar_1.5_a_3.0Rsun": {"n_cells": n_cells, "n_bad": 0, "min_cobertura": min_cov},
        },
    }


def sectors(state="S8", n_sots=0, ok=True, n_cells=100):
    return {"state": state, "n_cells_tested": n_cells, "n_sots": n_sots, "ok": ok}


def foundation_summary():
    cov_reports = {state: coverage(state) for state in FOUNDATION_STATES}
    sector_reports = {state: sectors(state) for state in FOUNDATION_STATES}
    return {
        "4": {"porta": "ACCEPTADA"},
        "5": {"porta": "ACCEPTADA"},
        "7": {"porta": "ACCEPTADA"},
        "g5_11": seal_reports(cov_reports, FOUNDATION_STATES),
        "g5_10": seal_g5_10_reports(sector_reports, FOUNDATION_STATES),
        "artifacts": {
            "states": {state: artifact(state) for state in FOUNDATION_STATES},
            "masks": {str(layer_id): artifact(f"mask_{layer_id}") for layer_id in (4, 5, 7)},
        },
    }


def complete_chain():
    receipt = {
        "_contract": {
            "gate": "CHAIN_SEQUENCE",
            "status": "PASS",
            "start_state": "S7",
            "layer_ids": list(CHAIN_IDS),
            "final_state": f"S{CHAIN_IDS[-1]}",
        }
    }
    predecessor_state = "S7"
    predecessor_sha = SHA_A
    for offset, layer_id in enumerate(CHAIN_IDS, start=1):
        state = f"S{layer_id}"
        state_sha = f"{offset:064x}"
        receipt[str(layer_id)] = {
            "veredicte": "ACCEPTADA",
            "g5_11": coverage_gate_snapshot(coverage(state), state),
            "g5_10": g5_10_snapshot(sectors(state), state),
            "predecessor_state": predecessor_state,
            "predecessor_state_sha256": predecessor_sha,
            "mask_artifact": artifact(f"mask_{layer_id}", f"{offset + 20:064x}"),
            "state_artifact": artifact(state, state_sha),
        }
        predecessor_state = state
        predecessor_sha = state_sha
    return receipt


class CoverageReportTests(unittest.TestCase):
    def test_artifact_receipt_is_bound_to_live_path_and_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.npy"
            path.write_bytes(b"sealed-state")
            record = artifact_record(path)
            self.assertTrue(artifact_record_matches(record, path))
            path.write_bytes(b"changed-state")
            self.assertFalse(artifact_record_matches(record, path))
            self.assertFalse(artifact_record_matches(record, Path(tmp) / "other.npy"))

    def test_explicit_pass(self):
        self.assertTrue(coverage_report_pass(coverage(), "S8"))

    def test_bad_cell_or_false_ok_fails(self):
        self.assertFalse(coverage_report_pass(coverage(n_bad=1), "S8"))
        self.assertFalse(coverage_report_pass(coverage(ok=False), "S8"))

    def test_missing_real_zones_fails(self):
        report = coverage()
        report["zones"] = {"dummy": {"n_cells": 100, "n_bad": 0, "min_cobertura": 1.0}}
        self.assertFalse(coverage_report_pass(report, "S8"))

    def test_empty_cells_or_low_minimum_fails(self):
        self.assertFalse(coverage_report_pass(coverage(n_cells=0), "S8"))
        self.assertFalse(coverage_report_pass(coverage(min_cov=0.899), "S8"))

    def test_bool_is_not_a_valid_count(self):
        self.assertFalse(coverage_report_pass(coverage(n_bad=False), "S8"))

    def test_snapshot_gate_status_and_state_are_binding(self):
        snapshot = coverage_gate_snapshot(coverage("S8"), "S8")
        self.assertTrue(coverage_snapshot_pass(snapshot, "S8"))
        for key, value in (("gate", "NOT_G5_11"), ("status", "FAIL"), ("state", "S9")):
            broken = dict(snapshot)
            broken[key] = value
            with self.subTest(key=key):
                self.assertFalse(coverage_snapshot_pass(broken, "S8"))

    def test_porta_g5_10_and_g5_11_are_all_required(self):
        self.assertTrue(candidate_pass("ACCEPTADA", coverage(), sectors(), "S8"))
        self.assertFalse(candidate_pass("REBUTJADA", coverage(), sectors(), "S8"))
        self.assertFalse(candidate_pass("ACCEPTADA", coverage(n_bad=2), sectors(), "S8"))
        self.assertFalse(candidate_pass("ACCEPTADA", coverage(), sectors(n_sots=1), "S8"))
        self.assertFalse(candidate_pass("ACCEPTADA", coverage(), sectors(ok=False), "S8"))
        self.assertFalse(candidate_pass("ACCEPTADA", coverage(), sectors(n_cells=0), "S8"))


class SealAndPromotionTests(unittest.TestCase):
    def test_seal_requires_every_named_state_and_exact_contract(self):
        reports = {state: coverage(state) for state in FOUNDATION_STATES[:-1]}
        seal = seal_reports(reports, FOUNDATION_STATES)
        self.assertFalse(seal["ok"])
        self.assertFalse(seal_pass(seal, FOUNDATION_STATES))
        good = seal_reports({state: coverage(state) for state in FOUNDATION_STATES}, FOUNDATION_STATES)
        good["required_states"] = list(FOUNDATION_STATES[:-1])
        self.assertFalse(seal_pass(good, FOUNDATION_STATES))

    def test_foundation_requires_porta_gates_and_artifacts(self):
        summary = foundation_summary()
        self.assertTrue(foundation_gate(summary)["ok"])
        for mutation in ("porta", "g5_10", "artifacts"):
            broken = foundation_summary()
            if mutation == "porta":
                broken["5"]["porta"] = "REBUTJADA"
            elif mutation == "g5_10":
                broken["g5_10"]["status"] = "FAIL"
            else:
                del broken["artifacts"]["masks"]["5"]
            with self.subTest(mutation=mutation):
                self.assertFalse(foundation_gate(broken)["ok"])

    def test_historical_receipts_fail_closed(self):
        old_foundation = {"4": {"porta": "ACCEPTADA"}, "5": {"porta": "ACCEPTADA"}, "7": {"porta": "ACCEPTADA"}}
        old_chain = {"8": {"veredicte": "ACCEPTADA", "cobertura_bad": {"solar": 0}}}
        self.assertFalse(promotion_gate(old_foundation, old_chain)["ok"])

    def test_complete_canonical_receipts_pass(self):
        self.assertTrue(promotion_gate(foundation_summary(), complete_chain())["ok"])

    def test_hidden_or_partial_layer_list_cannot_reduce_gate(self):
        report = promotion_gate(foundation_summary(), complete_chain(), [3, 4, 5, 7, 8])
        self.assertFalse(report["ok"])
        self.assertIn("required_layers_not_canonical_complete_order", report["failures"])

    def test_permuted_chain_contract_fails(self):
        chain = complete_chain()
        chain["_contract"]["layer_ids"] = list(reversed(CHAIN_IDS))
        self.assertFalse(promotion_gate(foundation_summary(), chain)["ok"])
        chain = complete_chain()
        chain["_contract"]["final_state"] = "S8"
        self.assertFalse(promotion_gate(foundation_summary(), chain)["ok"])

    def test_extra_chain_receipt_entry_fails(self):
        chain = complete_chain()
        chain["99"] = chain["17"]
        report = promotion_gate(foundation_summary(), chain)
        self.assertFalse(report["ok"])
        self.assertIn("chain_receipt_entries_not_exactly_canonical", report["failures"])

    def test_snapshot_copied_to_another_state_fails(self):
        chain = complete_chain()
        chain["9"]["g5_11"] = chain["8"]["g5_11"]
        self.assertFalse(promotion_gate(foundation_summary(), chain)["ok"])

    def test_stale_predecessor_hash_fails(self):
        chain = complete_chain()
        chain["10"]["predecessor_state_sha256"] = "f" * 64
        report = promotion_gate(foundation_summary(), chain)
        self.assertFalse(report["ok"])
        self.assertIn("S10_predecessor_hash_mismatch", report["failures"])


if __name__ == "__main__":
    unittest.main()
