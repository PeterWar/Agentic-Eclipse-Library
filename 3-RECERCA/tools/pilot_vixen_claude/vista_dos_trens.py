"""Els DOS trens un al costat de l'altre, al mateix llenç i amb el mateix realçat.

⛔ La comparació només vol dir alguna cosa si les dues imatges han passat
exactament pel mateix camí: mateix llenç comú (la Vixen s'hi porta amb l'afí de
`comu.afi`, la mateixa que fa servir `dos_trens_filtrats`), mateix retall,
mateix realçat per anell i el mateix rang de to. Qualsevol diferència que es
vegi és de la dada, no de com s'ha pintat.

Els dos trens tenen jocs d'exposicions **diferents**, o sigui **fronteres de
fusió a radis diferents**. Un patró que surti als dos al mateix lloc no pot ser
de la fusió; un que segueixi les fronteres de cada tren, sí.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402


def realca_per_anell(d, w, rr, r_max, pas=0.02):
    vores = np.arange(1.0, r_max + pas, pas)
    sd = np.ones_like(rr)
    idx = np.digitize(rr, vores) - 1
    for i in range(len(vores) - 1):
        m = (idx == i) & (w > 0)
        if m.sum() > 500:
            sd[m] = max(float(np.std(d[m])), 1e-9)
    return np.where(w > 0, d / sd, 0.0)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vixen", type=Path, required=True)
    ap.add_argument("--sony", type=Path, required=True)
    ap.add_argument("-o", "--sortida", type=Path, required=True)
    ap.add_argument("--r-max", type=float, default=2.6)
    ap.add_argument("--etiquetes", nargs=2, default=["VIXEN + R6 III", "SONY A7RIIIA"])
    a = ap.parse_args()
    import cv2

    ds = np.load(a.sony / "DETALL_ln.npy")
    ws = np.load(a.sony / "PES.npy")
    Hc, Wc = ds.shape
    dv = np.load(a.vixen / "DETALL_ln.npy")
    wv = np.load(a.vixen / "PES.npy")
    H, W = dv.shape
    A = C.afi((W / 2.0, H / 2.0), (Wc / 2.0, Hc / 2.0))
    dvc = cv2.warpAffine(np.nan_to_num(dv * wv), A, (Wc, Hc),
                         flags=cv2.INTER_LANCZOS4, borderValue=0.0)
    wvc = cv2.warpAffine(np.nan_to_num(wv), A, (Wc, Hc),
                         flags=cv2.INTER_LINEAR, borderValue=0.0)
    bo = wvc > 0.5
    dvc = np.where(bo, dvc / np.maximum(wvc, 1e-6), 0.0)

    yy = np.arange(Hc, dtype=np.float32)[:, None] - Hc / 2
    xx = np.arange(Wc, dtype=np.float32)[None, :] - Wc / 2
    rr = np.hypot(xx, yy) / C.R_SOL_PX
    qv = realca_per_anell(dvc, bo.astype(np.float32), rr, a.r_max)
    qs = realca_per_anell(ds, ws, rr, a.r_max)

    r = int(min(a.r_max * C.R_SOL_PX, Hc / 2 - 4, Wc / 2 - 4))
    sl = (slice(Hc // 2 - r, Hc // 2 + r), slice(Wc // 2 - r, Wc // 2 + r))
    esc = 1000.0 / (2 * r)
    pans = []
    for q, m, et in ((qv, bo, a.etiquetes[0]), (qs, ws > 0, a.etiquetes[1])):
        img = np.clip((q[sl] + 3.0) / 6.0, 0, 1) * (m[sl] > 0)
        img = cv2.resize(img, None, fx=esc, fy=esc, interpolation=cv2.INTER_AREA)
        v = cv2.cvtColor((img * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)
        cv2.putText(v, et, (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                    (0, 255, 255), 2, cv2.LINE_AA)
        pans.append(v)
    sep = np.full((pans[0].shape[0], 6, 3), 90, np.uint8)
    out = np.hstack([pans[0], sep, pans[1]])
    cv2.putText(out, "mateix llenc, mateix retall, mateix realcat per anell  ·  "
                     "exposicions i fronteres de fusio DIFERENTS a cada tren",
                (12, out.shape[0] - 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                (0, 255, 255), 1, cv2.LINE_AA)
    a.sortida.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(a.sortida), out)
    print(f"→ {a.sortida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
