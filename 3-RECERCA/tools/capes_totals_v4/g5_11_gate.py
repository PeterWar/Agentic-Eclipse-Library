"""Contractes fail-closed G5.10/G5.11 per a CapesTotals V4.

La semàntica és deliberadament pura, tret dels helpers explícits de hash. Això
permet provar els rebuts sense carregar ni executar el workspace V4/V4b.
"""
import hashlib
import math
import re
from collections.abc import Mapping


FOUNDATION_STATES = ("S3", "S4", "S5", "S7")
FOUNDATION_LAYER_IDS = (4, 5, 7)
CHAIN_IDS = (8, 9, 10, 11, 12, 13, 16, 17)
ALL_LAYER_IDS = (3, 4, 5, 7, *CHAIN_IDS)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def sha256_file(path, chunk_size=8 * 1024 * 1024):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def artifact_record(path):
    return {"path": str(path), "sha256": sha256_file(path)}


def artifact_record_pass(record):
    return (
        isinstance(record, Mapping)
        and isinstance(record.get("path"), str)
        and bool(record["path"])
        and isinstance(record.get("sha256"), str)
        and _SHA256_RE.fullmatch(record["sha256"]) is not None
    )


def artifact_record_matches(record, path):
    """Comprova que el rebut identifica exactament el fitxer viu i el seu hash."""
    if not artifact_record_pass(record) or record["path"] != str(path):
        return False
    try:
        return record["sha256"] == sha256_file(path)
    except OSError:
        return False


def _finite_number_at_least(value, minimum):
    return type(value) in (int, float) and math.isfinite(value) and value >= minimum


def coverage_report_pass(report, expected_state=None):
    """PASS cru: estat correcte, dues zones reals, cobertura ≥0,9 i zero bad."""
    if not isinstance(report, Mapping) or report.get("ok") is not True:
        return False
    if expected_state is not None and report.get("state") != expected_state:
        return False
    zones = report.get("zones")
    if not isinstance(zones, Mapping) or len(zones) != 2:
        return False
    names = tuple(str(name) for name in zones)
    if sum(name.startswith("lunar_") for name in names) != 1:
        return False
    if sum(name.startswith("solar_") for name in names) != 1:
        return False
    for zone in zones.values():
        if not isinstance(zone, Mapping):
            return False
        if type(zone.get("n_cells")) is not int or zone["n_cells"] <= 0:
            return False
        if type(zone.get("n_bad")) is not int or zone["n_bad"] != 0:
            return False
        if not _finite_number_at_least(zone.get("min_cobertura"), 0.9):
            return False
    return True


def coverage_gate_snapshot(report, expected_state):
    zones = report.get("zones") if isinstance(report, Mapping) else None
    zone_values = {}
    if isinstance(zones, Mapping):
        for name, zone in zones.items():
            zone_values[str(name)] = {
                "n_cells": zone.get("n_cells") if isinstance(zone, Mapping) else None,
                "n_bad": zone.get("n_bad") if isinstance(zone, Mapping) else None,
                "min_cobertura": zone.get("min_cobertura") if isinstance(zone, Mapping) else None,
            }
    ok = coverage_report_pass(report, expected_state)
    return {
        "gate": "G5.11",
        "state": expected_state,
        "status": "PASS" if ok else "FAIL",
        "ok": ok,
        "zones": zone_values,
    }


def coverage_snapshot_pass(snapshot, expected_state):
    return (
        isinstance(snapshot, Mapping)
        and snapshot.get("gate") == "G5.11"
        and snapshot.get("state") == expected_state
        and snapshot.get("status") == "PASS"
        and coverage_report_pass(snapshot, expected_state)
    )


def g5_10_report_pass(report, expected_state=None):
    if not isinstance(report, Mapping):
        return False
    if expected_state is not None and report.get("state") != expected_state:
        return False
    return (report.get("ok") is True
            and type(report.get("n_cells_tested")) is int
            and report["n_cells_tested"] > 0
            and type(report.get("n_sots")) is int
            and report["n_sots"] == 0)


def g5_10_snapshot(report, expected_state):
    ok = g5_10_report_pass(report, expected_state)
    return {
        "gate": "G5.10",
        "state": expected_state,
        "status": "PASS" if ok else "FAIL",
        "ok": ok,
        "n_cells_tested": report.get("n_cells_tested") if isinstance(report, Mapping) else None,
        "n_sots": report.get("n_sots") if isinstance(report, Mapping) else None,
    }


def g5_10_snapshot_pass(snapshot, expected_state):
    return (
        isinstance(snapshot, Mapping)
        and snapshot.get("gate") == "G5.10"
        and snapshot.get("state") == expected_state
        and snapshot.get("status") == "PASS"
        and snapshot.get("ok") is True
        and g5_10_report_pass(snapshot, expected_state)
    )


def candidate_pass(porta_verdict, coverage_report, sectors_report, expected_state):
    return (
        porta_verdict == "ACCEPTADA"
        and coverage_report_pass(coverage_report, expected_state)
        and g5_10_report_pass(sectors_report, expected_state)
    )


def seal_reports(reports, required_states):
    required = tuple(required_states)
    states = {
        state: coverage_gate_snapshot(
            reports.get(state) if isinstance(reports, Mapping) else None,
            state,
        )
        for state in required
    }
    ok = bool(required) and all(coverage_snapshot_pass(states[state], state) for state in required)
    return {
        "gate": "G5.11",
        "status": "PASS" if ok else "FAIL",
        "ok": ok,
        "required_states": list(required),
        "states": states,
    }


def seal_pass(seal, required_states):
    required = tuple(required_states)
    if not isinstance(seal, Mapping):
        return False
    if seal.get("gate") != "G5.11" or seal.get("status") != "PASS" or seal.get("ok") is not True:
        return False
    if seal.get("required_states") != list(required):
        return False
    states = seal.get("states")
    if not isinstance(states, Mapping) or set(states) != set(required):
        return False
    return all(coverage_snapshot_pass(states[state], state) for state in required)


def seal_g5_10_reports(reports, required_states):
    required = tuple(required_states)
    states = {
        state: g5_10_snapshot(
            reports.get(state) if isinstance(reports, Mapping) else None,
            state,
        )
        for state in required
    }
    ok = bool(required) and all(g5_10_snapshot_pass(states[state], state) for state in required)
    return {
        "gate": "G5.10",
        "status": "PASS" if ok else "FAIL",
        "ok": ok,
        "required_states": list(required),
        "states": states,
    }


def seal_g5_10_pass(seal, required_states):
    required = tuple(required_states)
    if not isinstance(seal, Mapping):
        return False
    if seal.get("gate") != "G5.10" or seal.get("status") != "PASS" or seal.get("ok") is not True:
        return False
    if seal.get("required_states") != list(required):
        return False
    states = seal.get("states")
    if not isinstance(states, Mapping) or set(states) != set(required):
        return False
    return all(g5_10_snapshot_pass(states[state], state) for state in required)


def _entry(mapping, key):
    if not isinstance(mapping, Mapping):
        return None
    return mapping.get(str(key), mapping.get(key))


def _foundation_artifacts_pass(artifacts):
    if not isinstance(artifacts, Mapping):
        return False
    states = artifacts.get("states")
    masks = artifacts.get("masks")
    if not isinstance(states, Mapping) or set(states) != set(FOUNDATION_STATES):
        return False
    if not isinstance(masks, Mapping) or set(masks) != {str(i) for i in FOUNDATION_LAYER_IDS}:
        return False
    return all(artifact_record_pass(states[state]) for state in FOUNDATION_STATES) and all(
        artifact_record_pass(masks[str(layer_id)]) for layer_id in FOUNDATION_LAYER_IDS
    )


def foundation_gate(summary):
    failures = []
    if not isinstance(summary, Mapping):
        return {
            "gate": "FOUNDATION_PROMOTION",
            "status": "FAIL",
            "ok": False,
            "failures": ["foundation_receipt_missing_or_malformed"],
        }
    if not seal_pass(summary.get("g5_11"), FOUNDATION_STATES):
        failures.append("g5_11_foundation_not_explicit_pass")
    if not seal_g5_10_pass(summary.get("g5_10"), FOUNDATION_STATES):
        failures.append("g5_10_foundation_not_explicit_pass")
    if not _foundation_artifacts_pass(summary.get("artifacts")):
        failures.append("foundation_artifacts_not_explicitly_sealed")
    for layer_id in FOUNDATION_LAYER_IDS:
        entry = _entry(summary, layer_id)
        if not isinstance(entry, Mapping) or entry.get("porta") != "ACCEPTADA":
            failures.append(f"S{layer_id}_porta_not_accepted")
    return {
        "gate": "FOUNDATION_PROMOTION",
        "status": "PASS" if not failures else "FAIL",
        "ok": not failures,
        "failures": failures,
    }


def promotion_gate(foundation_summary, chain_receipt, required_layer_ids=ALL_LAYER_IDS):
    """Antibypass: cadena completa, ordre canònic, gates i artefactes segellats."""
    failures = []
    if tuple(required_layer_ids) != ALL_LAYER_IDS:
        failures.append("required_layers_not_canonical_complete_order")
    foundation = foundation_gate(foundation_summary)
    if not foundation["ok"]:
        failures.extend(foundation["failures"])
    if not isinstance(chain_receipt, Mapping):
        failures.append("chain_receipt_missing_or_malformed")
        chain_receipt = {}
    receipt_layer_keys = {str(key) for key in chain_receipt if str(key) != "_contract"}
    if receipt_layer_keys != {str(layer_id) for layer_id in CHAIN_IDS}:
        failures.append("chain_receipt_entries_not_exactly_canonical")
    contract = chain_receipt.get("_contract")
    if not (
        isinstance(contract, Mapping)
        and contract.get("gate") == "CHAIN_SEQUENCE"
        and contract.get("status") == "PASS"
        and contract.get("start_state") == "S7"
        and contract.get("layer_ids") == list(CHAIN_IDS)
        and contract.get("final_state") == f"S{CHAIN_IDS[-1]}"
    ):
        failures.append("chain_sequence_contract_not_explicit_pass")

    predecessor_state = "S7"
    predecessor_sha = None
    artifacts = foundation_summary.get("artifacts") if isinstance(foundation_summary, Mapping) else None
    if isinstance(artifacts, Mapping) and isinstance(artifacts.get("states"), Mapping):
        record = artifacts["states"].get("S7")
        if artifact_record_pass(record):
            predecessor_sha = record["sha256"]

    for layer_id in CHAIN_IDS:
        state = f"S{layer_id}"
        entry = _entry(chain_receipt, layer_id)
        if not isinstance(entry, Mapping):
            failures.append(f"{state}_receipt_missing")
            predecessor_state = state
            predecessor_sha = None
            continue
        if entry.get("veredicte") != "ACCEPTADA":
            failures.append(f"{state}_porta_not_accepted")
        if not coverage_snapshot_pass(entry.get("g5_11"), state):
            failures.append(f"{state}_g5_11_not_explicit_pass")
        if not g5_10_snapshot_pass(entry.get("g5_10"), state):
            failures.append(f"{state}_g5_10_not_explicit_pass")
        if entry.get("predecessor_state") != predecessor_state:
            failures.append(f"{state}_predecessor_state_mismatch")
        if predecessor_sha is None or entry.get("predecessor_state_sha256") != predecessor_sha:
            failures.append(f"{state}_predecessor_hash_mismatch")
        if not artifact_record_pass(entry.get("mask_artifact")):
            failures.append(f"{state}_mask_artifact_not_sealed")
        if not artifact_record_pass(entry.get("state_artifact")):
            failures.append(f"{state}_state_artifact_not_sealed")
            predecessor_sha = None
        else:
            predecessor_sha = entry["state_artifact"]["sha256"]
        predecessor_state = state

    return {
        "gate": "CAPESTOTALS_V4_PROMOTION",
        "status": "PASS" if not failures else "FAIL",
        "ok": not failures,
        "required_layer_ids": list(ALL_LAYER_IDS),
        "failures": failures,
    }
