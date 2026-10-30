#!/usr/bin/env python3
"""Synthetic validation for the Adobe Photoshop AEL bridge.

MIT License — Copyright (c) 2026 Pere Guerra Serra.
Processed with Agentic Eclipse Library by Pere Guerra —
https://github.com/PeterWar/Agentic-Eclipse-Library
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback

import cv2
import numpy as np
import tifffile

from ael.geometry import EclipseGeometry
from ael.synthetic import SyntheticScene


def detect_python(repo: Path) -> str:
    """A Python 3.10+ that imports this checkout's AEL, found the way the bridge finds one, never named: AEL_PYTHON,
    this interpreter, python3 and python3.N (newest first) in /opt/homebrew/bin and /usr/local/bin, virtual
    environments, pyenv, conda and /usr/bin/python3."""
    home = Path.home()

    def minor(path: Path) -> int:
        return int(path.name.split(".")[1]) if "." in path.name else 1000

    candidates = [os.environ.get("AEL_PYTHON"), sys.executable]
    for folder in ("/opt/homebrew/bin", "/usr/local/bin"):
        found = [path for path in Path(folder).glob("python3*") if re.fullmatch(r"python3(\.\d+)?", path.name)]
        candidates += [str(path) for path in sorted(found, key=minor, reverse=True)]
    for folder in (".venvs", ".virtualenvs", "venvs"):
        candidates += [str(path / "bin/python") for path in sorted((home / folder).glob("*")) if path.is_dir()]
    candidates += [str(home / name) for name in ("venv/bin/python", ".venv/bin/python", ".pyenv/shims/python",
                   "miniconda3/bin/python", "anaconda3/bin/python", "miniforge3/bin/python", "mambaforge/bin/python")]
    candidates.append("/usr/bin/python3")
    tried = []
    for candidate in candidates:
        if not candidate or not Path(candidate).exists() or candidate in tried:
            continue
        run = subprocess.run([candidate, "-c", "import sys, ael; assert sys.version_info >= (3, 10)"],
                             capture_output=True, check=False,
                             env=dict(os.environ, PYTHONPATH=str(repo), PYTHONDONTWRITEBYTECODE="1"))
        if run.returncode == 0:
            return candidate
        tried.append(candidate)
    raise RuntimeError(f"No Python 3.10+ that imports AEL was found (tried {', '.join(tried) or 'none'}); "
                       "select one with --python or AEL_PYTHON")


def photoshop_running() -> bool:
    return subprocess.run(["pgrep", "-f", "Adobe Photoshop 2026.app/Contents/MacOS"],
                          capture_output=True, check=False).returncode == 0


def do_javascript(code: str, timeout: int = 1800) -> subprocess.CompletedProcess:
    script = ('tell application id "com.adobe.Photoshop"\n'
              f'with timeout of {timeout} seconds\n'
              f'do javascript {json.dumps(code, ensure_ascii=False)}\n'
              'end timeout\nend tell')
    return subprocess.run(["osascript", "-e", script], text=True, capture_output=True,
                          timeout=timeout + 30, check=False)


def direct(repo: Path, python: str, operation: str, source: Path, geometry: Path,
           parent: Path, rmax: float = 4.0) -> dict:
    root = parent / f"direct_{operation}"
    root.mkdir()
    cfg = {"operation": operation, "input": str(source), "geometry": str(geometry),
           "out": str(root / operation), "run_root": str(root), "rmax": rmax,
           "source": {"width": 400, "height": 320, "channels": 3}}
    config, result = root / "config.json", root / "result.json"
    config.write_text(json.dumps(cfg), encoding="utf-8")
    env = dict(os.environ, PYTHONPATH=str(repo), PYTHONDONTWRITEBYTECODE="1")
    run = subprocess.run([python, str(repo / "plugins/photoshop-ael/python/ael_photoshop.py"),
                          str(config), str(result)], text=True, capture_output=True, env=env,
                         timeout=900, check=False)
    if run.returncode or not result.exists():
        raise RuntimeError(f"Direct {operation} failed: {run.stdout}\n{run.stderr}")
    answer = json.loads(result.read_text())
    if not answer.get("ok"):
        raise RuntimeError(answer.get("message"))
    return answer


def compare_products(direct_result: dict, bridge_root: Path, operation: str) -> dict:
    comparisons = {}
    for image in direct_result["images"]:
        expected = tifffile.imread(image["path"]) if image["path"].endswith(".tif") else None
        produced_path = bridge_root / operation / Path(image["path"]).name
        if expected is None:
            import imageio.v3 as iio
            expected = iio.imread(image["path"])
            produced = iio.imread(produced_path)
        else:
            produced = tifffile.imread(produced_path)
        difference = float(np.max(np.abs(expected.astype(np.float64) - produced.astype(np.float64))))
        comparisons[Path(image["path"]).name] = {"max_abs_difference": difference,
                                                 "same_shape": expected.shape == produced.shape}
    return comparisons


def psb_layers_u16(psb: Path) -> list:
    """The layers of AEL's PSB as psd-tools reads them: 16-bit colour and alpha (None when opaque)."""
    from psd_tools import PSDImage

    layers = []
    for layer in PSDImage.open(str(psb)):
        shape_channel = layer.numpy("shape")
        layers.append({"name": layer.name, "visible": bool(layer.visible), "opacity": int(layer.opacity),
                       "mode": str(layer.blend_mode).split(".")[-1].lower(),
                       "rgb16": np.round(np.asarray(layer.numpy("color"), np.float64) * 65535).astype(np.int64),
                       "alpha16": None if shape_channel is None else
                       np.round(np.asarray(shape_channel, np.float64)[..., 0] * 65535).astype(np.int64)})
    return layers


def photoshop_15bit_model(psb: Path, shape) -> np.ndarray:
    """The visible layers of AEL's PSB composited as Photoshop holds 16-bit images: layers and alphas on the
    15-bit grid (0–32768), the blend and the opacity mix rounded to it after every layer, exported to 16 bits.
    The blends are AEL's (develop.py, add()); the opacity is the stored byte."""
    def q15(value):
        return np.round(np.asarray(value, np.float64) * 32768) / 32768

    comp = np.zeros(shape, np.float64)
    for layer in psb_layers_u16(psb):
        if not layer["visible"]:
            continue
        x = q15(layer["rgb16"] / 65535)
        alpha = q15((np.full(shape[:2], 65535) if layer["alpha16"] is None else layer["alpha16"]) / 65535)
        mode = layer["mode"]
        blend = x if mode == "normal" else comp * x if mode == "multiply" else \
            np.where(comp <= .5, 2 * comp * x, 1 - 2 * (1 - comp) * (1 - x))
        weight = alpha[..., None] * (layer["opacity"] / 255)
        comp = q15(comp * (1 - weight) + q15(blend) * weight)
    return np.round(np.clip(comp, 0, 1) * 65535).astype(np.int64)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    parser.add_argument("--python")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--skip-photoshop", action="store_true")
    args = parser.parse_args()
    # Photoshop resolves relative paths from its own working directory, not from this shell.
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    repo = args.repo.resolve()
    python = args.python or detect_python(repo)
    helper = repo / "plugins/photoshop-ael/python/ael_photoshop.py"
    core = repo / "plugins/photoshop-ael/AELPhotoshopCore.jsx"
    report = {"ok": False, "synthetic": True, "python": python, "repo": str(repo),
              "photoshop_tested": not args.skip_photoshop}
    was_running = photoshop_running()
    report["photoshop_was_running"] = was_running
    try:
        with tempfile.TemporaryDirectory(prefix="ael-photoshop-") as temporary:
            root = Path(temporary) / "prova pont àè"
            root.mkdir()
            shape = (320, 400)
            geometry = EclipseGeometry(shape=shape, sun_xy=(198, 158), sun_radius_px=20,
                                       moon_xy=(198, 158), moon_radius_px=20.6,
                                       north_deg=17, arcsec_per_px=8, note="Synthetic Photoshop validation")
            geometry_path = root / "geometry.json"
            geometry.to_json(geometry_path)
            scene = SyntheticScene(sun_radius_px=20, seed=73, n_rays=120, psf_sigma_px=0.8)
            base = scene.radiance(shape, geometry.sun_xy, geometry.moon_xy).astype(np.float32) / 10
            base = np.stack([base * 1.03, base, base * 0.96], axis=-1).astype(np.float32)
            source = root / "source.tif"
            tifffile.imwrite(source, base, photometric="rgb")
            direct_structure = direct(repo, python, "structure", source, geometry_path, root)
            direct_polar = direct(repo, python, "polar", source, geometry_path, root)
            report["direct"] = {"structure": direct_structure["out"], "polar": direct_polar["out"]}

            matrices = [np.array([[1, 0, 0], [0, 1, 0]], np.float32),
                        np.array([[1, 0, 2.0], [0, 1, -1.5]], np.float32),
                        np.array([[1, 0, -2.5], [0, 1, 2.0]], np.float32)]
            exposures = [0.01, 0.02, 0.04]
            exiftool = shutil.which("exiftool") or "/opt/homebrew/bin/exiftool"
            frames = []
            for index, (matrix, exposure) in enumerate(zip(matrices, exposures)):
                moving = cv2.warpAffine(base, matrix, (shape[1], shape[0]),
                                        flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                                        borderMode=cv2.BORDER_CONSTANT, borderValue=0).astype(np.float32)
                path = root / f"frame_{index}.tif"
                tifffile.imwrite(path, moving * exposure, photometric="rgb")
                subprocess.run([exiftool, "-overwrite_original", f"-ExposureTime={exposure}",
                                "-ISO=100", "-Make=Synthetic", "-Model=WorkflowCamera", str(path)],
                               text=True, capture_output=True, check=True)
                frames.append(path)
            camera = root / "camera.json"
            camera.write_text(json.dumps({"black": 0, "white": 1000000,
                                          "linearity_fraction": 0.95, "train": "synthetic"}), encoding="utf-8")

            if not args.skip_photoshop:
                jsx_report = args.output / "JSX_PROGRESS.json"
                after_structure = root / "after_structure.tif"
                after_polar = root / "after_polar.tif"
                after_untagged = root / "after_untagged.tif"
                (root / "photoshop_layers").mkdir()
                for name in ("fake python one", "fake python two"):  # candidates that never answer the probe
                    (root / name).write_text("#!/bin/sh\nexit 3\n", encoding="utf-8")
                    (root / name).chmod(0o755)
                jsx = f'''#include {json.dumps(str(core))}
var REPORT = {{ok:false}};
var OWNED = {{}};
function remember(id) {{ OWNED[String(id)] = true; }}
function rememberResults(result) {{
    for (var i=0; i<result.opened_documents.length; i++) remember(result.opened_documents[i].id);
}}
function closeOwned() {{
    for (var i=app.documents.length-1; i>=0; i--) {{
        var doc=app.documents[i];
        if (OWNED[String(doc.id)]) doc.close(SaveOptions.DONOTSAVECHANGES);
    }}
    OWNED={{}};
}}
function documentByID(id) {{
    for (var i=0; i<app.documents.length; i++) if (app.documents[i].id === id) return app.documents[i];
    return null;
}}
function openedBits(result) {{
    var bits=[];
    for (var i=0; i<result.opened_documents.length; i++) {{
        var doc=documentByID(result.opened_documents[i].id);
        bits.push(doc ? String(doc.bitsPerChannel) : 'missing');
    }}
    return bits;
}}
// Photoshop's own composite of the PSB it opened: a merged copy of the visible layers, saved as a 16-bit TIFF.
function exportComposite(result, target) {{
    for (var i=0; i<result.opened_documents.length; i++) {{
        if (result.opened_documents[i].kind !== 'psb') continue;
        var doc=documentByID(result.opened_documents[i].id);
        app.activeDocument=doc;
        var copy=doc.duplicate('AEL composite test', true);
        remember(copy.id);
        copy.flatten();
        var options=new TiffSaveOptions(); options.embedColorProfile=false; options.imageCompression=TIFFEncoding.NONE;
        options.layers=false; options.alphaChannels=false; options.transparency=false;
        copy.saveAs(new File(target), options, true, Extension.LOWERCASE);
        return {{bits:String(copy.bitsPerChannel), source_layers:doc.layers.length}};
    }}
    return null;
}}
// Each layer of the PSB alone on its black Background, in normal mode at full opacity, as Photoshop holds it. The
// other layers are removed, not hidden: flattening hidden layers would ask in a dialog.
function exportLayers(result, folder) {{
    var done=[];
    for (var i=0; i<result.opened_documents.length; i++) {{
        if (result.opened_documents[i].kind !== 'psb') continue;
        var doc=documentByID(result.opened_documents[i].id);
        for (var k=0; k<doc.layers.length; k++) {{
            var name=doc.layers[k].name;
            if (name === 'Background') continue;
            app.activeDocument=doc;
            var copy=doc.duplicate('AEL layer test', false);
            remember(copy.id);
            for (var j=copy.layers.length-1; j>=0; j--) {{
                var layer=copy.layers[j];
                if (layer.name !== name && layer.name !== 'Background') layer.remove();
            }}
            for (j=0; j<copy.layers.length; j++) {{
                copy.layers[j].visible=true;
                if (copy.layers[j].name === name) {{ copy.layers[j].blendMode=BlendMode.NORMAL; copy.layers[j].opacity=100; }}
            }}
            copy.flatten();
            var options=new TiffSaveOptions(); options.embedColorProfile=false; options.imageCompression=TIFFEncoding.NONE;
            options.layers=false; options.alphaChannels=false; options.transparency=false;
            var file=new File(folder+'/layer_'+k+'.tif');
            copy.saveAs(file, options, true, Extension.LOWERCASE);
            copy.close(SaveOptions.DONOTSAVECHANGES);
            done.push({{name:name, path:file.fsName}});
        }}
    }}
    return done;
}}
function imageOperation(operation, afterPath) {{
    REPORT.stage=operation+'_open'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    if (AELPhotoshop.isOpen({json.dumps(str(source))})) throw new Error('Already open, not touched');
    var oldDialogs=app.displayDialogs; app.displayDialogs=DialogModes.NO;
    var source;
    try {{ source=app.open(new File({json.dumps(str(source))})); }}
    finally {{ app.displayDialogs=oldDialogs; }}
    remember(source.id);
    REPORT.stage=operation+'_run'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    var saved=source.saved;
    var result=AELPhotoshop.run({{operation:operation,outputParent:{json.dumps(str(root))},
        geometry:{json.dumps(str(geometry_path))},python:{json.dumps(python)},aelFolder:{json.dumps(str(repo))},
        rmax:4.0}});
    rememberResults(result);
    AELPhotoshop.exportDocument(source,new File(afterPath));
    var answer={{run_root:result.run_root,opened:result.opened_documents.length,
        receipt:result.bridge_receipt,source_saved_before:saved,source_saved_after:source.saved}};
    closeOwned();
    return answer;
}}
function newOwned(name, fill, bits) {{
    var oldUnits=app.preferences.rulerUnits; app.preferences.rulerUnits=Units.PIXELS;
    try {{ var d=app.documents.add(400,320,72,name,NewDocumentMode.RGB,fill,1,bits); remember(d.id); return d; }}
    finally {{ app.preferences.rulerUnits=oldUnits; }}
}}
function runFolders() {{
    var names=[], files=new Folder({json.dumps(str(root))}).getFiles("AEL_*");
    for (var i=0; i<files.length; i++) if (files[i] instanceof Folder) names.push(files[i].name);
    return names;
}}
function transparentRefusal() {{
    var d=newOwned('AEL test transparent',DocumentFill.TRANSPARENT,BitsPerChannelType.THIRTYTWO);
    d.selection.select([[100,80],[300,80],[300,240],[100,240]]);
    var c=new SolidColor(); c.rgb.red=128; c.rgb.green=128; c.rgb.blue=128;
    d.selection.fill(c); d.selection.deselect();
    var before=runFolders(), answer={{refused:false}}, seen={{}};
    try {{
        var result=AELPhotoshop.run({{operation:'structure',outputParent:{json.dumps(str(root))},
            geometry:{json.dumps(str(geometry_path))},python:{json.dumps(python)},aelFolder:{json.dumps(str(repo))}}});
        rememberResults(result); answer.opened=result.opened_documents.length;
    }} catch(e) {{ answer.refused=true; answer.error=String(e.message); }}
    for (var i=0; i<before.length; i++) seen[before[i]]=true;
    var after=runFolders(); answer.new_run_folders=[];
    for (var j=0; j<after.length; j++) if (!seen[after[j]]) answer.new_run_folders.push(after[j]);
    closeOwned();
    return answer;
}}
function untaggedExport() {{
    var d=newOwned('AEL test untagged',DocumentFill.WHITE,BitsPerChannelType.SIXTEEN);
    d.colorProfileType=ColorProfile.NONE;
    var answer={{}};
    try {{
        var info=AELPhotoshop.exportDocument(d,new File({json.dumps(str(after_untagged))}));
        answer.ok=true; answer.color_profile=info.color_profile; answer.color_profile_type=info.color_profile_type;
    }} catch(e) {{ answer.ok=false; answer.error=String(e.message); }}
    closeOwned();
    return answer;
}}
try {{
    REPORT.stage='bad_path'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    try {{ AELPhotoshop.probe('/path/that/does/not/exist',{json.dumps(str(repo))}); }}
    catch(e) {{ REPORT.bad_path_error=String(e.message); }}
    REPORT.stage='read_json'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    var hostile=new File({json.dumps(str(root / "not_json_result.json"))});
    hostile.encoding='UTF8'; hostile.open('w');
    hostile.write('(function(){{ REPORT.json_code_ran=true; return {{ok:true}}; }})()'); hostile.close();
    try {{ AELPhotoshop.readJSON(hostile); REPORT.json_refused=false; }} catch(e) {{ REPORT.json_refused=true; }}
    REPORT.stage='structure'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    REPORT.structure=imageOperation('structure',{json.dumps(str(after_structure))});
    REPORT.stage='polar'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    REPORT.polar=imageOperation('polar',{json.dumps(str(after_polar))});
    REPORT.stage='master'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    var master=AELPhotoshop.run({{operation:'master',outputParent:{json.dumps(str(root))},
        geometry:{json.dumps(str(geometry_path))},camera:{json.dumps(str(camera))},
        frames:{json.dumps([str(p) for p in frames])},python:{json.dumps(python)},
        aelFolder:{json.dumps(str(repo))},run_filters:true,filter_options:{{filters:'all'}}}});
    rememberResults(master);
    REPORT.master={{run_root:master.run_root,opened:master.opened_documents.length,
        registrations:master.registrations,linear:master.images[0].path,receipt:master.bridge_receipt,
        native_check:master.native_check,ael_version:master.ael_version}};
    closeOwned();
    REPORT.stage='filters'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    var filters=AELPhotoshop.run({{operation:'filters',outputParent:{json.dumps(str(root))},
        input:REPORT.master.linear,python:{json.dumps(python)},aelFolder:{json.dumps(str(repo))},filters:'all'}});
    rememberResults(filters);
    REPORT.filters={{run_root:filters.run_root,opened:filters.opened_documents.length,
        images:filters.images.length,receipt:filters.bridge_receipt,native_check:filters.native_check}};
    REPORT.filters.composite=exportComposite(filters,{json.dumps(str(root / "photoshop_composite.tif"))});
    REPORT.filters.psb=filters.psb;
    REPORT.filters.layers=exportLayers(filters,{json.dumps(str(root / "photoshop_layers"))});
    closeOwned();
    REPORT.stage='filters_documents'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    var separate=AELPhotoshop.run({{operation:'filters',outputParent:{json.dumps(str(root))},open_mode:'documents',
        input:REPORT.master.linear,python:{json.dumps(python)},aelFolder:{json.dumps(str(repo))},filters:'all'}});
    rememberResults(separate);
    REPORT.filters_documents={{opened:separate.opened_documents.length,native_check:separate.native_check||null,
        bits:openedBits(separate)}};
    closeOwned();
    REPORT.stage='default_ael'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    REPORT.default_ael={{folder:AELPhotoshop.defaultAELFolder(),
        runtime:AELPhotoshop.probe({json.dumps(python)},'').runtime}};
    REPORT.stage='automatic_python'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    // The automatic search from scratch: the Python kept from earlier runs is set aside and put back afterwards.
    var keptPython=AELPhotoshop.savedPython();
    try {{ app.eraseCustomOptions(AELPhotoshop.settingsKey); }} catch(e) {{}}
    try {{
        var automatic=AELPhotoshop.probe('',{json.dumps(str(repo))});
        REPORT.automatic_python={{python:automatic.selected_python, ael_version:automatic.runtime.ael_version,
            tried:automatic.tried, saved_after:AELPhotoshop.savedPython()}};
    }} catch(e) {{ REPORT.automatic_python={{error:String(e.message)}}; }}
    finally {{ if (keptPython) AELPhotoshop.savePython(keptPython); }}
    REPORT.stage='no_python'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    try {{ AELPhotoshop.firstWorking({json.dumps([str(root / "fake python one"), str(root / "fake python two")])},
        {json.dumps(str(repo))}); REPORT.no_python={{refused:false}}; }}
    catch(e) {{ REPORT.no_python={{refused:true, message:String(e.message)}}; }}
    REPORT.stage='transparent'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    REPORT.transparent=transparentRefusal();
    REPORT.stage='untagged'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    REPORT.untagged=untaggedExport();
    REPORT.stage='check_layers'; AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT);
    // checkLayers on a stand-in document (no document opened): one byte of opacity off, or another mode, fails.
    function standIn(opacityByte, mode) {{
        return {{bitsPerChannel:'BitsPerChannelType.SIXTEEN', layers:[{{name:'01a NRGF', blendMode:'BlendMode.'+mode,
            opacity:opacityByte/255*100, visible:true, typename:'ArtLayer'}}]}};
    }}
    var wanted=[{{name:'01a NRGF', mode:'overlay', opacity:0.2, opacity_byte:51, visible:true}}];
    REPORT.check_layers={{exact:AELPhotoshop.checkLayers(standIn(51,'OVERLAY'),wanted).ok,
        byte_below:AELPhotoshop.checkLayers(standIn(50,'OVERLAY'),wanted).ok,
        byte_above:AELPhotoshop.checkLayers(standIn(52,'OVERLAY'),wanted).ok,
        other_mode:AELPhotoshop.checkLayers(standIn(51,'MULTIPLY'),wanted).ok}};
    REPORT.stage='done'; REPORT.ok=true;
}} catch(e) {{ REPORT.error=String(e.message); REPORT.stack=String(e.stack); }}
finally {{ closeOwned(); AELPhotoshop.writeJSON(new File({json.dumps(str(jsx_report))}),REPORT); }}
'PHOTOSHOP_AEL_TEST_DONE';'''
                completed = do_javascript(jsx, timeout=600)
                report["photoshop_command"] = "osascript: tell com.adobe.Photoshop to do javascript <generated synthetic test>"
                report["photoshop_stdout"] = completed.stdout
                report["photoshop_stderr"] = completed.stderr
                if completed.returncode or not jsx_report.exists():
                    raise RuntimeError(f"Photoshop test failed: {completed.stdout}\n{completed.stderr}")
                jsx_result = json.loads(jsx_report.read_text())
                report["jsx"] = jsx_result
                if not jsx_result.get("ok"):
                    raise RuntimeError(jsx_result.get("error"))

                report["structure_products"] = compare_products(direct_structure,
                    Path(jsx_result["structure"]["run_root"]), "structure")
                report["polar_products"] = compare_products(direct_polar,
                    Path(jsx_result["polar"]["run_root"]), "polar")
                report["source_roundtrip"] = {}
                for name, after in (("structure", after_structure), ("polar", after_polar)):
                    restored = tifffile.imread(after)
                    difference = float(np.max(np.abs(restored - base)))
                    negative = float(np.max(np.abs(np.flipud(restored) - base)))
                    report["source_roundtrip"][name] = {"shape": list(restored.shape),
                        "dtype": str(restored.dtype), "max_abs_difference": difference,
                        "negative_orientation_difference": negative}
                report["source_saved_unchanged"] = all(
                    jsx_result[name]["source_saved_before"] == jsx_result[name]["source_saved_after"]
                    for name in ("structure", "polar"))

                master_out = Path(jsx_result["master"]["run_root"]) / "master"
                linear = np.load(master_out / "master/linear.npy")
                valid = np.load(master_out / "master/valid.npy")
                difference = np.abs(linear - base)
                finite = valid & np.isfinite(difference).all(axis=-1)
                relative = difference / np.maximum(np.abs(base), 1.0)
                measured_frames = json.loads((master_out / "stack_recipe.json").read_text())["frames"]
                truth = [np.linalg.inv(np.vstack([matrix, [0, 0, 1]]))[:2] for matrix in matrices]
                report["translation_errors_px"] = [float(np.linalg.norm(
                    np.asarray(frame["reference_to_input"])[:, 2] - expected[:, 2]))
                    for frame, expected in zip(measured_frames, truth)]
                report["master"] = {"median_relative_difference": float(np.median(relative[finite])),
                    "median_abs_difference": float(np.median(difference[finite])),
                    "p99_abs_difference": float(np.percentile(difference[finite], 99))}
                filters_out = Path(jsx_result["filters"]["run_root"]) / "filters"
                report["filter_counts"] = {"layers": len(list((filters_out / "tiff").glob("*_layer.tif"))),
                    "alphas": len(list((filters_out / "tiff").glob("*_alpha.tif")))}
                transparent = jsx_result["transparent"]
                transparent["ael_outputs"] = [name for name in transparent["new_run_folders"]
                                              if (root / name / "structure").exists()]
                report["transparent"] = transparent
                report["untagged"] = dict(jsx_result["untagged"], exported=after_untagged.exists())
                # Photoshop's composite of the PSB against AEL's own composite (ael/display.tif), in 16-bit steps.
                # Photoshop holds 16-bit images as 15-bit (one 15-bit step = two 16-bit steps) and rounds at each
                # of the four visible blends: up to 8 steps. Declared with it before the first run, a 99.9th
                # percentile of 3 failed (4.0, run of 30-10). A model of that arithmetic (15-bit layers and alphas,
                # rounding after every blend) gave the same distance to AEL on another image and matched Photoshop
                # exactly at 95.8 % of its pixels (mean 0.09 steps, 0.18 % beyond 2), so the percentile was an
                # estimate of mine, not Photoshop's behaviour. The gate is now that model, declared from that image.
                composite = root / "photoshop_composite.tif"
                ael_display = Path(jsx_result["filters"]["run_root"]) / "filters" / "ael" / "display.tif"
                seen = tifffile.imread(composite).astype(np.int64) if composite.exists() else np.zeros(0)
                wanted = tifffile.imread(ael_display).astype(np.int64)
                report["photoshop_composite"] = {"photoshop": jsx_result["filters"].get("composite"),
                    "shape": list(seen.shape), "ael_shape": list(wanted.shape), "dtype": "uint16" if
                    composite.exists() and tifffile.imread(composite).dtype == np.uint16 else "other"}
                if seen.shape == wanted.shape:
                    model = photoshop_15bit_model(Path(jsx_result["filters"]["psb"]), seen.shape)
                    for name, other in (("vs_ael", wanted), ("vs_15bit_model", model)):
                        steps = np.abs(seen - other)
                        report["photoshop_composite"][name] = {"max_steps": int(steps.max()),
                            "p999_steps": float(np.percentile(steps, 99.9)), "mean_steps": float(steps.mean()),
                            "exact": float(np.mean(steps == 0)), "over_2_steps": float(np.mean(steps > 2))}
                # Each layer as Photoshop holds it, against the layer AEL wrote, where AEL's alpha is opaque. Declared
                # before the first run: at most one 16-bit step, the round trip through Photoshop's 15-bit grid.
                written = {layer["name"]: layer for layer in psb_layers_u16(Path(jsx_result["filters"]["psb"]))}
                report["photoshop_layers"] = {}
                for item in jsx_result["filters"].get("layers") or []:
                    layer = written[item["name"]]
                    opaque = np.ones(layer["rgb16"].shape[:2], bool) if layer["alpha16"] is None else layer["alpha16"] == 65535
                    held = tifffile.imread(item["path"]).astype(np.int64)
                    steps = np.abs(held - layer["rgb16"])[opaque] if held.shape == layer["rgb16"].shape else np.array([99])
                    report["photoshop_layers"][item["name"]] = {"opaque_pixels": int(opaque.sum()),
                        "max_steps": int(steps.max()) if steps.size else None, "exact": float(np.mean(steps == 0)) if steps.size else None}

            # AGENTS §7: no script names an interpreter; the private environment name never reaches the code.
            plugin = repo / "plugins/photoshop-ael"
            report["named_interpreter_in"] = sorted(
                str(path.relative_to(plugin)) for path in plugin.rglob("*")
                if path.suffix in (".jsx", ".py") and "__pycache__" not in path.parts and
                re.search("eines" + "-ia|python3\\.1[0-9]", path.read_text(encoding="utf-8")))
            report["gates"] = {
                "direct_structure": bool(direct_structure.get("ok")),
                "direct_polar": bool(direct_polar.get("ok")),
                "no_named_interpreter": not report["named_interpreter_in"]}
            if not args.skip_photoshop:
                report["gates"].update({
                    "bad_path_clear": "bad_path" in report["jsx"].get("bad_path_error", ""),
                    "non_json_not_evaluated": bool(report["jsx"].get("json_refused")) and
                                              not report["jsx"].get("json_code_ran"),
                    # bool(...) first: all() of an empty product list would pass silently.
                    "structure_matches_direct": bool(report["structure_products"]) and all(
                        x["same_shape"] and x["max_abs_difference"] == 0
                        for x in report["structure_products"].values()),
                    "polar_matches_direct": bool(report["polar_products"]) and all(
                        x["same_shape"] and x["max_abs_difference"] == 0
                        for x in report["polar_products"].values()),
                    "transparent_refused": report["transparent"]["refused"] and
                                           "transparent" in report["transparent"].get("error", "") and
                                           len(report["transparent"]["new_run_folders"]) == 1 and
                                           not report["transparent"]["ael_outputs"],
                    "untagged_exported": bool(report["untagged"].get("ok")) and report["untagged"]["exported"],
                    "source_exact": all(x["max_abs_difference"] == 0 and x["negative_orientation_difference"] > 0
                                        for x in report["source_roundtrip"].values()),
                    "source_saved_unchanged": report["source_saved_unchanged"],
                    "master_translation": max(report["translation_errors_px"]) < 0.1,
                    "master_pixels": report["master"]["median_relative_difference"] < 0.001,
                    "sixteen_filters": report["filter_counts"] == {"layers": 16, "alphas": 16},
                    # Layered by default: the linear master and one PSB; "documents" opens every TIFF.
                    "results_opened": report["jsx"]["structure"]["opened"] == 3 and
                                      report["jsx"]["polar"]["opened"] == 8 and
                                      report["jsx"]["master"]["opened"] == 2 and
                                      report["jsx"]["filters"]["opened"] == 1 and
                                      report["jsx"]["filters_documents"]["opened"] == 33,
                    # The PSB as Photoshop itself reads it: every layer, mode, opacity and visibility.
                    "psb_native": all((report["jsx"][key].get("native_check") or {}).get("ok") and
                                      report["jsx"][key]["native_check"]["layers"] == 19 for key in ("master", "filters")),
                    "check_layers_exact": report["jsx"]["check_layers"] == {"exact": True, "byte_below": False,
                                                                            "byte_above": False, "other_mode": False},
                    "photoshop_composite_within_8_steps": report["photoshop_composite"]["dtype"] == "uint16" and
                        report["photoshop_composite"].get("vs_ael", {}).get("max_steps", 99) <= 8,
                    "photoshop_composite_is_15bit_arithmetic":
                        report["photoshop_composite"].get("vs_15bit_model", {}).get("mean_steps", 99) <= 0.2 and
                        report["photoshop_composite"].get("vs_15bit_model", {}).get("over_2_steps", 1) <= 0.005,
                    "photoshop_layers_within_1_step": len(report["photoshop_layers"]) == 18 and all(
                        value["opaque_pixels"] > 0 and value["max_steps"] is not None and value["max_steps"] <= 1
                        for value in report["photoshop_layers"].values()),
                    # Separate documents: Photoshop has no Overlay at 32 bits, so every one must be 16-bit.
                    "documents_16bit": report["jsx"]["filters_documents"]["bits"] ==
                        ["BitsPerChannelType.SIXTEEN"] * 33,
                    "default_ael_is_this_checkout": str(report["jsx"]["default_ael"]["runtime"].get("ael_file", ""))
                                                    .startswith(str(repo)),
                    # Python field empty and nothing kept from earlier runs: the search finds one by itself.
                    "automatic_python_found": bool(report["jsx"]["automatic_python"].get("python")) and
                                              report["jsx"]["automatic_python"].get("ael_version") == "1.3.6",
                    "no_python_error_lists_tried": report["jsx"]["no_python"].get("refused") is True and
                        "Tried:" in report["jsx"]["no_python"].get("message", "") and
                        all(name in report["jsx"]["no_python"]["message"] for name in ("fake python one", "fake python two"))})
            report["ok"] = all(report["gates"].values())
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
        report["traceback"] = traceback.format_exc()
    finally:
        if not was_running and not args.skip_photoshop:
            quit_run = subprocess.run(["osascript", "-e",
                'tell application id "com.adobe.Photoshop" to quit'],
                text=True, capture_output=True, check=False)
            report["photoshop_quit_by_test"] = quit_run.returncode == 0
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "VALIDATION.json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"ok": report["ok"], "output": str(args.output), "gates": report.get("gates")}, ensure_ascii=False))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
