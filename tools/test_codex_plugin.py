"""Exercise a released ZIP outside its source tree, without creating a Python environment."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys
import zipfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("zip", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(args.zip) as z:
        assert z.testzip() is None
        for name in z.namelist():
            assert not Path(name).is_absolute() and ".." not in Path(name).parts
        z.extractall(out / "unpacked")
    plugin = out / "unpacked" / "agentic-eclipse-library"
    launcher = plugin / "scripts" / "run_ael.py"
    manifest = json.loads((plugin / "BUNDLE_CONTENTS.json").read_text())
    for rel, expected in manifest["files"].items():
        assert sha(plugin / rel) == expected, rel
    results = {"zip_sha256": sha(args.zip), "file_hashes_verified": len(manifest["files"]), "checks": {}}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    env.pop("PYTHONPATH", None)

    def run(label, argv, expected=0):
        r = subprocess.run([sys.executable, *map(str, argv)], cwd=out, env=env,
                           text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out / (label + ".log")).write_text(r.stdout)
        ok = r.returncode == expected if expected == 0 else r.returncode != 0
        results["checks"][label] = {"passed": ok, "exit_code": r.returncode, "log": label + ".log"}
        print(f"{label}: {'PASS' if ok else 'FAIL'}", flush=True)
        assert ok, r.stdout[-3000:]
        return r.stdout

    check = json.loads(run("dependencies", [launcher, "--check"]))
    assert Path(check["ael_source"]).is_relative_to(plugin)
    assert all(check["dependencies"].values()), "This validation requires all optional dependencies"
    bare = json.loads(run("no_site_dependency_check", ["-S", launcher, "--check"]))
    assert not any(bare["dependencies"].values())
    run("missing_dependencies_message", ["-S", launcher, "--help"], expected=1)
    existing = out / "protected-output"
    existing.mkdir()
    sentinel = existing / "original.txt"
    sentinel.write_text("user-original-must-stay\n")
    before = sha(sentinel)
    for command in ("stack", "extinction", "filters", "coronagraph", "structure", "polar", "motion", "demo-motion"):
        run("refuse_existing_" + command, [launcher, command, "--out", existing], expected=1)
    run("refuse_abbreviation", [launcher, "demo-motion", "--o", existing], expected=1)
    assert sha(sentinel) == before
    core = run("ael_selftest", [launcher, "selftest"])
    assert "0 skipped" in core, "A skipped test is not validated"
    run("synthetic_demo", [launcher, "demo-motion", "--out", out / "synthetic-demo"])

    sys.path.insert(0, str(plugin / "runtime"))
    import numpy as np
    import tifffile
    from ael.synthetic import SyntheticScene
    from ael.geometry import EclipseGeometry
    data_dir = out / "synthetic-input"
    data_dir.mkdir()
    shape = (256, 320)
    scene = SyntheticScene(20, seed=63, n_rays=100, sky_level=40)
    image = scene.radiance(shape, (160, 128), (161, 128))
    geo = EclipseGeometry(shape=shape, sun_xy=(160, 128), sun_radius_px=20,
                          moon_xy=(161, 128), moon_radius_px=20.6)
    valid = np.hypot(*np.meshgrid(np.arange(320)-161, np.arange(256)-128)) > 23
    image[~valid] = np.nan
    np.save(data_dir / "linear.npy", image)
    np.save(data_dir / "valid.npy", valid)
    geo.to_json(data_dir / "geometry.json")
    paths = [data_dir / "linear.npy", data_dir / "valid.npy", data_dir / "geometry.json"]
    input_hashes = [sha(x) for x in paths]
    run("structure_full_canvas", [launcher, "structure", "--input", paths[0], "--valid", paths[1],
                                  "--geometry", paths[2], "--out", out / "structure"])
    display = tifffile.imread(out / "structure" / "structure_mono.tif")
    assert display.shape[:2] == shape
    assert not (out / "structure" / "structure_cool.tif").exists()
    assert input_hashes == [sha(x) for x in paths]
    run("reject_colour_on_mono", [launcher, "structure", "--input", paths[0], "--geometry", paths[2],
                                  "--style", "measured", "--out", out / "invalid-colour"], expected=1)
    assert not (out / "invalid-colour").exists()
    run("reject_name_escape", [launcher, "structure", "--input", paths[0], "--geometry", paths[2],
                              "--name", "../escape", "--out", out / "invalid-name"], expected=1)
    assert not (out / "invalid-name").exists()
    results.update({"full_canvas_shape": list(shape), "inputs_unchanged": True,
                    "scientific_validation": "Synthetic software checks only; no new astronomical observation validated.",
                    "python": sys.version.split()[0], "all_passed": True})
    (out / "RESULT.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps({"all_passed": True, "checks": len(results["checks"]), "report": str(out / "RESULT.json")}), flush=True)


if __name__ == "__main__":
    main()
