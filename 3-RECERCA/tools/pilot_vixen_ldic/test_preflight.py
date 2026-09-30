from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

import preflight


class PreflightSerializationContracts(unittest.TestCase):
    @staticmethod
    def valid_claim() -> dict[str, str]:
        return {
            "claim_id": "fixture",
            "owner": "Codex",
            "task": "Pilot Vixen fixture",
            "scope": "research/tools/pilot_vixen_ldic output/pilot_vixen_ldic_20260823",
        }

    def test_strict_json_reader_rejects_nonstandard_nan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            path.write_text('{"value": NaN}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                preflight.json_load(path)

    def test_strict_json_writer_rejects_nan_before_creating_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "bad.json"
            with self.assertRaises(ValueError):
                preflight.write_json_exclusive(path, {"value": np.nan})
            self.assertFalse(path.exists())

    def test_payload_manifest_detects_post_commit_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "A").write_text("one\n", encoding="ascii")
            sums = preflight.write_payload_sha256sums(root)
            self.assertEqual(preflight.verify_payload_sha256sums(root, sums), 1)
            (root / "A").write_text("two\n", encoding="ascii")
            with self.assertRaises(preflight.ContractError):
                preflight.verify_payload_sha256sums(root, sums)

    def test_closed_stdout_after_status_cannot_append_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            preflight.write_json_exclusive(root / "STATUS.json", {"status": "BLOCKED"})
            with mock.patch("builtins.print", side_effect=BrokenPipeError):
                with self.assertRaises(BrokenPipeError):
                    preflight.report_terminal_build(root)
            self.assertTrue((root / "STATUS.json").is_file())
            self.assertFalse((root / "ERROR.json").exists())
            self.assertEqual(json.loads((root / "STATUS.json").read_text())["status"], "BLOCKED")

    def test_terminal_short_write_never_publishes_partial_status(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build = root / "build"
            build.mkdir()
            status = build / "STATUS.json"

            def short_write(path: Path, payload: str) -> None:
                path.write_text(payload[:1], encoding="utf-8")
                raise OSError("fixture short write")

            with mock.patch.object(
                preflight, "_write_all_and_fsync", side_effect=short_write
            ):
                with self.assertRaises(OSError):
                    preflight.write_terminal_json_atomic(status, {"status": "BLOCKED"})
            self.assertFalse(status.exists())
            self.assertFalse((root / ".build.STATUS.json.tmp").exists())

    def test_terminal_publish_is_complete_and_no_clobber(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            build = root / "build"
            build.mkdir()
            status = build / "STATUS.json"
            preflight.write_terminal_json_atomic(status, {"status": "BLOCKED"})
            self.assertEqual(preflight.json_load(status)["status"], "BLOCKED")
            self.assertFalse((root / ".build.STATUS.json.tmp").exists())
            with self.assertRaises(preflight.ContractError):
                preflight.write_terminal_json_atomic(status, {"status": "OTHER"})

    def test_claim_owner_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lock = root / "claim.lock"
            lock.mkdir()
            real_owner = root / "real-owner.json"
            real_owner.write_text(json.dumps(self.valid_claim()), encoding="utf-8")
            (lock / "owner.json").symlink_to(real_owner)
            with mock.patch.object(preflight, "CLAIM", lock / "owner.json"):
                with self.assertRaises(preflight.ContractError):
                    preflight.require_codex_claim()

    def test_claim_lock_directory_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            real_lock = root / "real-lock"
            real_lock.mkdir()
            (real_lock / "owner.json").write_text(
                json.dumps(self.valid_claim()), encoding="utf-8"
            )
            linked_lock = root / "claim.lock"
            linked_lock.symlink_to(real_lock, target_is_directory=True)
            with mock.patch.object(preflight, "CLAIM", linked_lock / "owner.json"):
                with self.assertRaises(preflight.ContractError):
                    preflight.require_codex_claim()

    def test_output_ancestor_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            worktree = root / "worktree"
            worktree.mkdir()
            external = root / "external"
            (external / "pilot_vixen_ldic_20260823").mkdir(parents=True)
            (worktree / "output").symlink_to(external, target_is_directory=True)
            with mock.patch.object(preflight, "WORKTREE", worktree):
                with self.assertRaises(preflight.ContractError):
                    preflight.canonical_output_root()

    def test_manifest_hash_and_parse_use_the_same_frozen_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            raw_root = root / "raw"
            raw_root.mkdir()
            manifest = root / "manifest.csv"
            names = [f"572A{index:04d}.CR3" for index in range(1000, 1068)]
            for name in names:
                (raw_root / name).write_bytes(b"")
            header = "nom,t_rel_c2,exp_nominal,exp_s,temp_C,sol_x,sol_y,n_sat,usat\n"

            def csv_bytes(temperature: int) -> bytes:
                rows = [
                    f"{name},{index + 1},0.001,0.001,{temperature},3500,2300,0,True"
                    for index, name in enumerate(names)
                ]
                return (header + "\n".join(rows) + "\n").encode("utf-8")

            original = csv_bytes(20)
            manifest.write_bytes(original)
            expected_hash = hashlib.sha256(original).hexdigest()
            real_reader = preflight.read_frozen_bytes

            def swap_after_read(path: Path):
                payload, row = real_reader(path)
                manifest.write_bytes(csv_bytes(99))
                return payload, row

            with (
                mock.patch.object(preflight, "MANIFEST", manifest),
                mock.patch.object(preflight, "RAW_ROOT", raw_root),
                mock.patch.object(
                    preflight,
                    "EXPECTED_MANIFEST_ORDER_SHA256",
                    preflight.frame_order_sha256(names),
                ),
                mock.patch.dict(
                    preflight.FROZEN_AUTHORITY_SHA256,
                    {str(manifest): expected_hash},
                    clear=True,
                ),
                mock.patch.object(
                    preflight, "read_frozen_bytes", side_effect=swap_after_read
                ),
            ):
                rows, anchor = preflight.load_manifest()
            self.assertEqual(rows[0]["temp_C"], 20.0)
            self.assertEqual(anchor["sha256"], expected_hash)
            self.assertIn(",99,", manifest.read_text(encoding="utf-8"))

    def test_terminal_input_revalidation_detects_changed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input.bin"
            path.write_bytes(b"authority")
            document = preflight.hash_one(path)
            path.write_bytes(b"changed")
            with self.assertRaises(preflight.ContractError):
                preflight.revalidate_consumed_inputs(document)


if __name__ == "__main__":
    unittest.main()
