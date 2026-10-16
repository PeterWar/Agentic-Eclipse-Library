"""Run the bundled AEL without modifying inputs or an existing output directory."""
from pathlib import Path
import argparse
import importlib.util
import json
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if sys.version_info < (3, 10):
        raise SystemExit("AEL requires Python 3.10 or later. Choose the user's supported Python environment.")
    if args == ["--check"]:
        modules = ("numpy", "scipy", "cv2", "PIL", "tifffile", "imageio", "rawpy", "astropy", "psd_tools")
        source = ROOT / "runtime" / "ael" / "__init__.py"
        version = re.search(r'^__version__ = "([^"]+)"', source.read_text(), re.MULTILINE).group(1)
        print(json.dumps({"python": sys.version.split()[0], "ael_version": version,
                          "ael_source": str(source),
                          "dependencies": {m: importlib.util.find_spec(m) is not None for m in modules}}, indent=2))
        return 0
    allowed = {"--input", "--geometry", "--valid", "--out", "--name", "--style", "--sky-r-min-rsun",
               "--config", "--rmax", "--help"}
    for i, arg in enumerate(args):
        if arg.startswith("--") and arg.split("=", 1)[0] not in allowed:
            raise SystemExit(f"Use a complete supported option, not an abbreviation: {arg}")
        out = args[i + 1] if arg == "--out" and i + 1 < len(args) else (
            arg.split("=", 1)[1] if arg.startswith("--out=") else None)
        if out is not None and (Path(out).exists() or Path(out).is_symlink()):
            raise SystemExit(f"Output already exists; choose a new directory: {out}")
    try:
        if args and args[0] == "structure":
            return structure(args[1:])
        from ael.__main__ import main as run
        return run(args)
    except ModuleNotFoundError as exc:
        raise SystemExit(f"Missing Python dependency: {exc.name}. See the plugin's docs/USAGE.md; nothing was installed.") from exc


def structure(args):
    p = argparse.ArgumentParser(description="Full-canvas AEL structure display; mono by default.", allow_abbrev=False)
    p.add_argument("--input", required=True)
    p.add_argument("--geometry", required=True)
    p.add_argument("--valid")
    p.add_argument("--out", required=True)
    p.add_argument("--name", default="structure")
    p.add_argument("--style", choices=("mono", "measured", "cool"), default="mono")
    p.add_argument("--sky-r-min-rsun", type=float, default=7.0)
    a = p.parse_args(args)
    if not a.name or Path(a.name).name != a.name or a.name in (".", ".."):
        p.error("Name must be a filename stem within the new output directory.")
    import numpy as np
    from ael import io, pipelines
    from ael.geometry import EclipseGeometry
    data = io.load_array(a.input)
    if a.style != "mono" and (data.ndim != 3 or data.shape[-1] != 3):
        p.error("Colour styles require RGB input; use mono for a scalar image.")
    result = pipelines.structure_from_linear(
        data, EclipseGeometry.from_json(a.geometry), a.out,
        valid=np.load(a.valid).astype(bool) if a.valid else None,
        name=a.name, styles=(a.style,), crop_height_rsun=None,
        sky_r_min_rsun=a.sky_r_min_rsun)
    print(json.dumps({k: result[k] for k in ("files", "receipt", "gate")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
