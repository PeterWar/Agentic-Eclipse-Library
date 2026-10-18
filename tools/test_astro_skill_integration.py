"""Bounded ASTRO skill/package checks; no AEL numerical command is executed."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

REPO = Path(__file__).resolve().parents[1]
BASE = None
FILES = ("SKILL.md", "agents/openai.yaml", "references/acquisition-and-authority.md",
         "references/examples-and-receipts.md")
SKILL = Path("skills/eclipse-astrophotography")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("Missing YAML frontmatter")
    front = text.split("---", 2)[1]
    fields = dict(line.split(":", 1) for line in front.strip().splitlines())
    name, description = fields["name"].strip(), fields["description"].strip()
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name) or not description:
        raise ValueError("Invalid skill name/description")
    return name, description


def catalog(root):
    found = {}
    for path in sorted((root / "skills").glob("*/SKILL.md")):
        name, description = metadata(path)
        if name in found:
            raise ValueError("Duplicate skill name: " + name)
        found[name] = (path, description)
    return found


class SkillIntegration(unittest.TestCase):
    def test_seventh_skill_discovery(self):
        skills = catalog(REPO / "plugins/codex-ael")
        self.assertEqual(len(skills), 7)
        self.assertIn("eclipse-astrophotography", skills)

    def test_onboarding_preserved(self):
        plugin = REPO / "plugins/codex-ael"
        data = json.loads((plugin / "plugin.json").read_text(encoding="utf-8"))
        entry = data["extensions"]["com.openai"]["onboardingSkill"]
        self.assertEqual(entry, "./skills/eclipse-first-steps/SKILL.md")
        self.assertTrue((plugin / entry).is_file())
        if BASE:
            for old in (BASE / "plugins/codex-ael/skills").glob("*/SKILL.md"):
                self.assertEqual(sha(old), sha(plugin / old.relative_to(BASE / "plugins/codex-ael")))

    def test_canonical_and_plugin_skill_equal(self):
        for name in FILES:
            self.assertEqual(sha(REPO / SKILL / name), sha(REPO / "plugins/codex-ael" / SKILL / name))

    def test_local_supporting_references_resolve(self):
        for prefix in (REPO, REPO / "plugins/codex-ael"):
            root = prefix / SKILL
            for source in root.rglob("*.md"):
                for link in re.findall(r"\]\(([^)]+)\)", source.read_text(encoding="utf-8")):
                    if "://" in link or link.startswith("#"):
                        continue
                    self.assertTrue((source.parent / link.split("#")[0]).is_file(), (source, link))
        self.assertTrue((REPO / "plugins/codex-ael/docs/USAGE.md").is_file())

    def test_ui_metadata(self):
        text = (REPO / SKILL / "agents/openai.yaml").read_text(encoding="utf-8")
        short = re.search(r'short_description: "([^"]+)"', text).group(1)
        self.assertGreaterEqual(len(short), 25)
        self.assertLessEqual(len(short), 64)
        self.assertIn("$eclipse-astrophotography", text)
        self.assertNotIn("allow_implicit_invocation: false", text)

    def test_builder_explicitly_syncs_four_skill_files(self):
        spec = importlib.util.spec_from_file_location("ael_package_builder", REPO / "tools/build_codex_plugin_20261016.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        pairs = module.sources()
        actual = {dst.relative_to(module.PLUGIN).as_posix(): src for src, dst in pairs if dst.is_relative_to(module.PLUGIN / SKILL)}
        expected = {(SKILL / name).as_posix(): REPO / SKILL / name for name in FILES}
        self.assertEqual(actual, expected)

    def test_engine_unchanged(self):
        if BASE is None:
            self.skipTest("No pre-change base supplied; engine comparison untested")
        # A release changes only the version line; every other line of the engine must match the base.
        def body(path):
            lines = path.read_text(encoding="utf-8").splitlines()
            return [l for l in lines if not re.match(r'\s*(__version__|version)\s*=\s*"', l)]
        old = {p.relative_to(BASE / "ael").as_posix(): body(p) for p in (BASE / "ael").rglob("*.py")}
        new = {p.relative_to(REPO / "ael").as_posix(): body(p) for p in (REPO / "ael").rglob("*.py")}
        self.assertEqual(old, new)
        self.assertEqual(body(BASE / "pyproject.toml"), body(REPO / "pyproject.toml"))

    def test_duplicate_catalog_rejected(self):
        with tempfile.TemporaryDirectory(prefix="astro-duplicate-") as tmp:
            p = Path(tmp)
            for name in ("one", "two"):
                dest = p / "skills" / name / "SKILL.md"
                dest.parent.mkdir(parents=True)
                dest.write_text("---\nname: duplicate\ndescription: Test only\n---\n", encoding="utf-8")
            with self.assertRaises(ValueError):
                catalog(p)


class BuilderIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="astro-build-")
        cls.path = Path(cls.tmp.name)
        cls.repo = cls.path / "source"
        shutil.copytree(REPO, cls.repo, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        cls.env = dict(os.environ, PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
        if "GIT_DIR" not in cls.env:
            git_dir = subprocess.check_output(["git", "rev-parse", "--absolute-git-dir"], cwd=REPO, text=True).strip()
            cls.env["GIT_DIR"] = git_dir
        cls.env["GIT_WORK_TREE"] = str(cls.repo)
        cls.z1, cls.z2 = cls.path / "first.zip", cls.path / "second.zip"
        cls.first = cls.build(cls.z1, sync=True)
        cls.second = cls.build(cls.z2)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    @classmethod
    def build(cls, out, sync=False):
        args = [sys.executable, str(cls.repo / "tools/build_codex_plugin_20261016.py"), "--out", str(out)]
        if sync:
            args.append("--sync")
        return subprocess.run(args, cwd=cls.repo, env=cls.env, text=True, capture_output=True)

    def test_actual_builder_and_determinism(self):
        self.assertEqual(self.first.returncode, 0, self.first.stderr)
        self.assertEqual(self.second.returncode, 0, self.second.stderr)
        self.assertEqual(sha(self.z1), sha(self.z2))

    def test_zip_has_portable_discoverable_paths(self):
        self.assertEqual(self.first.returncode, 0, self.first.stderr)
        with zipfile.ZipFile(self.z1) as z:
            names = z.namelist()
            self.assertTrue(all("\\" not in n for n in names), "ZIP must use POSIX path separators on every build host")
            self.assertIn("agentic-eclipse-library/skills/eclipse-astrophotography/SKILL.md", names)
            self.assertEqual(len([n for n in names if n.startswith("agentic-eclipse-library/skills/") and n.endswith("/SKILL.md")]), 7)
            receipt = json.loads(z.read("agentic-eclipse-library/BUNDLE_CONTENTS.json"))
            for name, digest in receipt["files"].items():
                self.assertEqual(hashlib.sha256(z.read("agentic-eclipse-library/" + name)).hexdigest(), digest)

    def test_existing_archive_refused(self):
        before = sha(self.z1)
        result = self.build(self.z1)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ZIP already exists", result.stderr)
        self.assertEqual(sha(self.z1), before)

    def test_missing_entrypoint_blocks_packaging(self):
        path = self.repo / "plugins/codex-ael/skills/eclipse-astrophotography/SKILL.md"
        original = path.read_bytes()
        try:
            path.unlink()
            target = self.path / "invalid.zip"
            result = self.build(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(target.exists())
        finally:
            path.write_bytes(original)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--base", type=Path)
    options, rest = parser.parse_known_args()
    REPO, BASE = options.repo.resolve(), options.base.resolve() if options.base else None
    unittest.main(argv=[sys.argv[0], *rest])
