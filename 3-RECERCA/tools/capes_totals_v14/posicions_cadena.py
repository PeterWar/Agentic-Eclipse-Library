"""Posicions del Sol i de la Lluna de la cadena per als fotogrames de la V13.

Només lectura del run. Escriu `cau_v13pere/posicions.json` amb, per fotograma:
sol_x/sol_y (coordenades de raw_image, marges inclosos), t, exp, lluna_dx/dy.

⏭️ Serveix per decidir QUÈ s'ha de moure: `research/78` declara que els nou
apilats DNG comparteixen la geometria de 572A2969 («el Sol al lloc on era a
572A2969 […] sense que el merge hagi d'alinear res»), o sigui que la
desalineació esperada de la V13 és NOMÉS a les capes 12 (572A2956) i 11
(572A2968), que són CR3 solts. La mesura directa (mesura_desalineacio.py) ho
contrasta abans de moure res.
"""
from __future__ import annotations

import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
ARREL = os.path.expanduser("~/Desktop/Eclipse determinista")

# les capes de la V13_Pere, de BAIX a DALT, amb el fotograma/apilat que el nom declara
# i els membres de cada apilat segons `research/78` §1
CAPES_V13 = [
    ("12", "572A2956.CR3", ["572A2956.CR3"]),
    ("11", "572A2968.CR3", ["572A2968.CR3"]),
    ("10", "572A2969.CR3", ["572A2969.CR3"]),
    ("09", "572A2975.CR3", ["572A2975.CR3", "572A2993.CR3"]),
    ("08", "572A2970.CR3", ["572A2970.CR3", "572A2988.CR3", "572A3000.CR3", "572A3006.CR3"]),
    ("07", "572A2976.CR3", ["572A2976.CR3", "572A2994.CR3"]),
    ("06", "572A2971.CR3", ["572A2971.CR3", "572A2989.CR3", "572A3001.CR3", "572A3007.CR3"]),
    ("05", "572A2977.CR3", ["572A2977.CR3", "572A2995.CR3"]),
    ("04", "572A2972.CR3", ["572A2972.CR3", "572A2990.CR3", "572A3002.CR3", "572A3008.CR3"]),
    ("03", "572A2978.CR3", ["572A2978.CR3", "572A2996.CR3"]),
    ("02", "572A2979.CR3", ["572A2979.CR3", "572A2980.CR3", "572A2981.CR3"]),
    ("01", "572A2982.CR3", ["572A2982.CR3", "572A2983.CR3", "572A2984.CR3"]),
]
REFERENCIA = "572A2969.CR3"      # la geometria comuna dels apilats (research/78)


def tria_run(run: str | None) -> str:
    if run:
        return run
    cal = ("4-rebuts/F1.2_sol_llenc.json", "4-rebuts/F1.3_registre.json")
    cands = [os.path.join(ARREL, "1-RUNS", d)
             for d in sorted(os.listdir(os.path.join(ARREL, "1-RUNS")))
             if "_VIXEN_CIENCIA_" in d]
    cands = [r for r in cands
             if all(os.path.exists(os.path.join(r, x)) for x in cal)]
    if not cands:
        raise SystemExit("cap run VIXEN CIENCIA amb F1.2 i F1.3")
    return cands[-1]


def main(run: str | None = None) -> dict:
    run = tria_run(run)
    F12 = json.load(open(os.path.join(run, "4-rebuts", "F1.2_sol_llenc.json")))
    F13 = json.load(open(os.path.join(run, "4-rebuts", "F1.3_registre.json")))
    S = dict(F12["fotogrames"])
    for n, v in F13["fotogrames"].items():
        S.setdefault(n, {}).update(v)
    tots = {m for _, _, mm in CAPES_V13 for m in mm}
    fora = sorted(tots - set(S))
    if fora:
        raise SystemExit(f"fotogrames sense posició a la cadena: {fora}")
    poss = {n: {k: S[n][k] for k in ("sol_x", "sol_y", "t", "exp", "lluna_dx", "lluna_dy")
                if k in S[n]} for n in sorted(tots)}
    sortida = {"run": os.path.basename(run), "llenc": F12.get("llenc"),
               "referencia": REFERENCIA, "fotogrames": poss,
               "capes": [{"num": n, "declarat": d, "membres": m} for n, d, m in CAPES_V13]}
    os.makedirs(os.path.join(AQUI, "cau_v13pere"), exist_ok=True)
    dst = os.path.join(AQUI, "cau_v13pere", "posicions.json")
    json.dump(sortida, open(dst, "w"), indent=1, ensure_ascii=False)
    ref = poss[REFERENCIA]
    print(f"run {os.path.basename(run)} · {len(poss)} fotogrames · "
          f"referència {REFERENCIA} sol=({ref['sol_x']:.2f}, {ref['sol_y']:.2f})")
    for num, decl, membres in CAPES_V13:
        v = poss[decl]
        dx, dy = ref["sol_x"] - v["sol_x"], ref["sol_y"] - v["sol_y"]
        print(f"  capa {num} · {decl} t={v.get('t', float('nan')):6.2f}s · "
              f"sol=({v['sol_x']:.2f}, {v['sol_y']:.2f}) · "
              f"Δ cap a ref=({dx:+.2f}, {dy:+.2f}) px · {len(membres)} membres")
    return sortida


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
