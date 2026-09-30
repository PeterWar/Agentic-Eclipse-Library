"""Vista de caça d'arcs: detall amb realçat local fort i les fronteres dibuixades.

⛔ El propòsit és que un arc que quedi es vegi, no que la imatge quedi bonica.
El realçat és **per anell**: es divideix per la desviació local, de manera que
la corona interior i l'exterior tenen el mateix contrast a la pantalla i un arc
feble de fora no queda amagat pel detall fort de dins.

Damunt s'hi dibuixen, en color, les **isofotes de frontera de fusió** que el
programa d'exposicions prediu. Si un arc hi cau a sobre, és de la fusió; si no,
és una altra cosa i s'ha de buscar per una altra banda.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("detall", type=Path)
    ap.add_argument("--comp", type=Path, required=True)
    ap.add_argument("--sostre", type=float, required=True)
    ap.add_argument("--exposicions", type=float, nargs="+", required=True)
    ap.add_argument("--fb", type=float, default=None)
    ap.add_argument("-o", "--sortida", type=Path, required=True)
    ap.add_argument("--r-max", type=float, default=2.8)
    ap.add_argument("--titol", default="")
    a = ap.parse_args()
    import cv2

    d = np.load(a.detall / "DETALL_ln.npy")
    w = np.load(a.detall / "PES.npy")
    comp = np.load(a.comp, mmap_mode="r")
    g = np.asarray(comp[..., 1] if comp.ndim == 3 else comp, np.float32)
    if a.fb:
        g = g / np.float32(a.fb)
    H, W = d.shape
    yy = np.arange(H, dtype=np.float32)[:, None] - H / 2
    xx = np.arange(W, dtype=np.float32)[None, :] - W / 2
    rr = np.hypot(xx, yy) / C.R_SOL_PX

    # realçat PER ANELL: cada radi es divideix per la seva pròpia dispersió
    vores = np.arange(1.0, a.r_max + 0.02, 0.02)
    sd = np.ones_like(rr)
    idx = np.digitize(rr, vores) - 1
    for i in range(len(vores) - 1):
        m = (idx == i) & (w > 0)
        if m.sum() > 500:
            sd[m] = max(float(np.std(d[m])), 1e-9)
    q = np.where(w > 0, d / sd, 0.0)

    r = int(min(a.r_max * C.R_SOL_PX, H / 2 - 4, W / 2 - 4))
    sl = (slice(H // 2 - r, H // 2 + r), slice(W // 2 - r, W // 2 + r))
    esc = 1400.0 / (2 * r)
    img = cv2.resize(np.clip((q[sl] + 3.0) / 6.0, 0, 1), None, fx=esc, fy=esc,
                     interpolation=cv2.INTER_AREA)
    vis = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)

    # les isofotes de frontera, dibuixades
    gs = cv2.resize(g[sl], None, fx=esc, fy=esc, interpolation=cv2.INTER_AREA)
    for t in sorted(a.exposicions):
        for quin, niv, col in (("pes 0", a.sostre / t, (60, 60, 255)),
                               ("pes 1", 0.2 * a.sostre / t, (255, 200, 60))):
            m = (gs > niv).astype(np.uint8)
            if not (0.001 < m.mean() < 0.999):
                continue
            cnt, _ = cv2.findContours(m, cv2.RETR_LIST, cv2.CHAIN_APPROX_NONE)
            cv2.drawContours(vis, [c for c in cnt if len(c) > 200], -1, col, 1, cv2.LINE_AA)
    cv2.putText(vis, a.titol or a.detall.name, (12, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.75, (0, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(vis, "vermell = on una exposicio se satura   ·   groc = on entra a pes ple",
                (12, vis.shape[0] - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                (0, 255, 255), 1, cv2.LINE_AA)
    a.sortida.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(a.sortida), vis)
    print(f"→ {a.sortida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
