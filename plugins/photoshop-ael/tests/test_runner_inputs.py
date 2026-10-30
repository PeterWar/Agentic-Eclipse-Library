#!/usr/bin/env python3
"""Runner input checks without Photoshop: a bad export must stop before AEL runs.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
import tifffile

from ael.geometry import EclipseGeometry
from ael.synthetic import SyntheticScene


def run_case(python: str, helper: Path, repo: Path, root: Path, name: str, image: np.ndarray,
             **tiff_options) -> dict:
    case = root / name
    case.mkdir()
    source = case / "source.tif"
    tifffile.imwrite(source, image, **tiff_options)
    out = case / "structure"
    cfg = {"operation": "structure", "input": str(source), "geometry": str(root / "geometry.json"),
           "out": str(out), "run_root": str(case),
           "source": {"width": image.shape[1], "height": image.shape[0], "channels": 3}}
    config, result = case / "config.json", case / "result.json"
    config.write_text(json.dumps(cfg), encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(repo), PYTHONDONTWRITEBYTECODE="1")
    subprocess.run([python, str(helper), str(config), str(result)], capture_output=True, text=True,
                   env=env, timeout=900, check=False)
    answer = json.loads(result.read_text()) if result.exists() else {"ok": False, "message": "no result"}
    return {"ok": bool(answer.get("ok")), "message": answer.get("message"), "ael_ran": out.exists()}


def probe(python: str, helper: Path, repo: Path, hidden: tuple = ()) -> dict:
    """The runner's probe, optionally in a Python where some modules cannot be imported."""
    code = ("import json, sys\n"
            f"sys.modules.update(dict.fromkeys({list(hidden)!r}))\n"
            f"sys.path.insert(0, {str(helper.parent)!r})\n"
            "import ael_photoshop\n"
            "print(json.dumps(ael_photoshop.execute({'operation': 'probe'})))\n")
    env = dict(os.environ, PYTHONPATH=str(repo), PYTHONDONTWRITEBYTECODE="1")
    completed = subprocess.run([python, "-c", code], capture_output=True, text=True, env=env, timeout=300,
                               check=False)
    try:
        answer = json.loads(completed.stdout.strip().splitlines()[-1])
    except Exception:
        answer = {"ok": False, "kind": "no_answer", "message": completed.stderr[-500:]}
    return {"ok": bool(answer.get("ok")), "kind": answer.get("kind"), "message": answer.get("message")}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--helper", type=Path, help="runner to test; default: this checkout's")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = args.repo.resolve()
    helper = (args.helper or repo / "plugins/photoshop-ael/python/ael_photoshop.py").resolve()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {"helper": str(helper)}
    with tempfile.TemporaryDirectory(prefix="ael-photoshop-inputs-") as temporary:
        root = Path(temporary)
        shape = (320, 400)
        geometry = EclipseGeometry(shape=shape, sun_xy=(198, 158), sun_radius_px=20,
                                   moon_xy=(198, 158), moon_radius_px=20.6, north_deg=17,
                                   arcsec_per_px=8, note="Synthetic runner input checks")
        geometry.to_json(root / "geometry.json")
        scene = SyntheticScene(sun_radius_px=20, seed=73, n_rays=120, psf_sigma_px=0.8)
        base = scene.radiance(shape, geometry.sun_xy, geometry.moon_xy).astype(np.float32) / 10
        rgb = np.stack([base * 1.03, base, base * 0.96], axis=-1).astype(np.float32)
        alpha = np.ones(shape, np.float32)
        alpha[:40, :] = 0  # what Photoshop writes when the top of the composite is empty
        rgba = np.concatenate([rgb * alpha[..., None], alpha[..., None]], axis=-1)
        report["control_rgb"] = run_case(args.python, helper, repo, root, "control", rgb, photometric="rgb")
        report["transparent_rgba"] = run_case(args.python, helper, repo, root, "transparent", rgba,
                                              photometric="rgb", extrasamples=["assocalpha"])
        report["planar_rgb"] = run_case(args.python, helper, repo, root, "planar", rgb,
                                        photometric="rgb", planarconfig="separate")
    report["probe"] = probe(args.python, helper, repo)
    report["probe_without_psd_tools"] = probe(args.python, helper, repo, hidden=("psd_tools",))
    # psd-tools installed but broken: one of its own dependencies cannot be imported.
    report["probe_without_attrs"] = probe(args.python, helper, repo, hidden=("attr", "attrs"))
    refused = {key: not report[key]["ok"] and report[key]["kind"] == "missing_dependency" and
               "psd_tools" in (report[key]["message"] or "") for key in ("probe_without_psd_tools", "probe_without_attrs")}
    report["gates"] = {
        "probe_ready": report["probe"]["ok"] and report["probe"]["kind"] == "ready",
        "probe_refuses_missing_psd_tools": refused["probe_without_psd_tools"],
        "probe_refuses_broken_psd_tools": refused["probe_without_attrs"],
        "control_runs": report["control_rgb"]["ok"] and report["control_rgb"]["ael_ran"],
        "transparent_refused_before_ael": not report["transparent_rgba"]["ok"] and
            "transparent" in (report["transparent_rgba"]["message"] or "") and
            not report["transparent_rgba"]["ael_ran"],
        "planar_refused_before_ael": not report["planar_rgb"]["ok"] and
            not report["planar_rgb"]["ael_ran"]}
    report["ok"] = all(report["gates"].values())
    (output / "RUNNER_INPUTS.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "gates": report["gates"]}, ensure_ascii=False))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
