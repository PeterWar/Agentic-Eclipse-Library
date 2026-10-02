"""Command line: ``python -m ael <command> ...`` (run ``python -m ael -h``)."""
import argparse
import json
import sys

import numpy as np

from . import CREDIT, __version__
from .geometry import EclipseGeometry


def main(argv=None):
    ap = argparse.ArgumentParser(prog="ael", description=f"Agentic Eclipse Library {__version__}. {CREDIT}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for command, help_text in (("stack", "RAW/Bayer/linear RGB + frozen registration -> linear HDR stack"),
                               ("filters", "linear stack -> corona filter layers and optional 16-bit PSB")):
        parser = sub.add_parser(command, help=help_text)
        parser.add_argument("--config", required=True, help="JSON recipe; paths relative to this file")
        parser.add_argument("--out", required=True, help="new output directory (must not exist)")
    s = sub.add_parser("structure", help="linear composite -> structure images (mono, cool, measured colour)")
    s.add_argument("--input", required=True, help=".npy/.fits/.tif linear composite, (H,W) or (H,W,3)")
    s.add_argument("--geometry", required=True, help="geometry JSON (see ael.geometry.EclipseGeometry)")
    s.add_argument("--valid", help="optional boolean mask (.npy) of observed pixels")
    s.add_argument("--out", required=True)
    s.add_argument("--name", default="structure")
    p = sub.add_parser("polar", help="image in [0,1] (.npy/.tif/.png) -> unrolled views around Sun and Moon")
    p.add_argument("--input", required=True)
    p.add_argument("--geometry", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--rmax", type=float, default=4.0)
    m = sub.add_parser("motion", help="RAW frames + JSON config -> motion analysis and animation")
    m.add_argument("--config", required=True)
    m.add_argument("--out", required=True)
    d = sub.add_parser("demo-motion", help="synthetic demonstration with known truth")
    d.add_argument("--out", required=True)
    t = sub.add_parser("selftest", help="run the tests with known truth")
    a = ap.parse_args(argv)

    from . import io as aio, pipelines
    if a.cmd in ("stack", "filters"):
        from .stack import stack_from_config
        from .develop import filters_from_config
        run = stack_from_config if a.cmd == "stack" else filters_from_config
        try:
            print(json.dumps(run(a.config, a.out), indent=1))
        except (ValueError, FileExistsError, KeyError) as exc:
            ap.error(str(exc))
    elif a.cmd == "structure":
        data = aio.load_array(a.input)
        geo = EclipseGeometry.from_json(a.geometry)
        valid = np.load(a.valid).astype(bool) if a.valid else None
        r = pipelines.structure_from_linear(np.asarray(data, np.float32), geo, a.out, valid=valid, name=a.name)
        print(json.dumps(dict(files=r["files"], receipt=r["receipt"], gate=r["gate"]), indent=1))
    elif a.cmd == "polar":
        img = aio.load_array(a.input).astype(np.float32)
        if img.max() > 1.0:
            img = img / (65535.0 if img.max() > 255 else 255.0)
        r = pipelines.polar_views(img, EclipseGeometry.from_json(a.geometry), a.out, r_max_rsun=a.rmax)
        print(json.dumps(r, indent=1))
    elif a.cmd == "motion":
        r = pipelines.motion_from_config(a.config, a.out)
        print(json.dumps({k: r[k] for k in ("classes", "confirmation", "detection_limit_km_s")}, indent=1, default=float))
        print(f"{len(r['candidates'])} candidates: check them by eye in candidates_visual_check.png")
    elif a.cmd == "demo-motion":
        print(json.dumps(pipelines.demo_motion_synthetic(a.out), indent=1, default=float))
    elif a.cmd == "selftest":
        from ._tests.runner import run
        return run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
