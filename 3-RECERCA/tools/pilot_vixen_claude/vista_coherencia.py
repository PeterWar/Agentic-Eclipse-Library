"""Dibuix de l'ajust de coherència: transparència i cel contra el temps.

Dos panells. A dalt, la **transparència** de cada fotograma contra l'instant,
amb el color per exposició: si el que hi ha és aire, tots els esglaons han de
caure sobre la MATEIXA corba. A baix, la **desviació de cel**, que ha de fer la
V que el projecte ja coneix (mínim a mig eclipsi).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("json_coherencia", type=Path)
    ap.add_argument("-o", "--sortida", type=Path, required=True)
    ap.add_argument("--titol", default="")
    a = ap.parse_args()
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = json.loads(a.json_coherencia.read_text())
    pf = sorted(d["per_fotograma"], key=lambda x: x["t_rel_c2"])
    t = np.array([x["t_rel_c2"] for x in pf])
    c = np.array([0.5 * (x["transparencia"]["G1"] + x["transparencia"]["G2"]) for x in pf])
    s = np.array([0.5 * (x["cel_adu_s"]["G1"] + x["cel_adu_s"]["G2"]) for x in pf])
    e = np.array([x["exposicio_s"] for x in pf])
    aj = set(d["per_pla"]["G1"].get("interpolats", []))
    es_int = np.array([x["nom"] in aj for x in pf])

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True,
                                 gridspec_kw={"height_ratios": [3, 2]})
    exps = sorted(set(e))
    cm = plt.get_cmap("viridis")
    for i, ex in enumerate(exps):
        m = (e == ex) & ~es_int
        if m.any():
            a1.plot(t[m], c[m], "o", ms=7, color=cm(i / max(len(exps) - 1, 1)),
                    label=f"{ex:.5g} s", zorder=3)
    if es_int.any():
        a1.plot(t[es_int], c[es_int], "x", ms=6, color="0.6", zorder=2,
                label="interpolat de la corba")
    a1.axhline(1.0, color="0.7", lw=0.8, ls="--")
    a1.set_ylabel("transparència  $c_i$")
    a1.set_title(a.titol or "Coherència per fotograma  ·  "
                 "si el que hi ha és aire, tots els esglaons cauen sobre la mateixa corba")
    a1.legend(fontsize=7, ncol=4, loc="upper right")
    a1.grid(alpha=0.25)

    a2.plot(t[~es_int], s[~es_int], "o-", ms=5, color="#b1552b", lw=1.2)
    a2.axhline(0.0, color="0.7", lw=0.8, ls="--")
    a2.set_ylabel("desviació de cel  $s_i$  (ADU/s)")
    a2.set_xlabel("t des de C2 (s)")
    a2.grid(alpha=0.25)
    a2.set_title("el mínim a mig eclipsi és la V del cel que el projecte ja coneixia "
                 "— no se li ha dit, surt de l'ajust", fontsize=9)
    fig.tight_layout()
    a.sortida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.sortida, dpi=130)
    print(f"→ {a.sortida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
