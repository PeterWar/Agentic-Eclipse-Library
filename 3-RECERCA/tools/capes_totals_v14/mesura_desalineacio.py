"""Mesura la desalineació de la CORONA entre capes de la V13_Pere, parell a parell.

## Per què es mesura, si `research/78` ja declara la geometria

Hi ha dues hipòtesis sobre on seu cada capa, i decideixen coses diferents:

- **H_comuna**: els nou apilats DNG comparteixen la geometria de 572A2969
  («el Sol al lloc on era a 572A2969 […] sense que el merge hagi d'alinear
  res», `research/78` §1) → només les capes 12 i 11 (CR3 solts) estan fora.
- **H_propia**: cada capa seu a la posició crua del seu fotograma declarat
  (la lectura de `research/117` §1) → onze capes s'han de moure, fins a 4 px.

La correlació de fase sobre l'estructura de la corona (plomalls) en l'anell
comú de cada parella distingeix les dues: H_propia prediu salts alternats de
±1,0-1,2 px entre capes veïnes (els fotogrames declarats alternen entre les
dues mitges escales del cos) i H_comuna prediu zero exacte entre apilats.

## ⛔ La trampa del patró fix

`research/78` §2: a 2-4 R☉ les exposicions llargues queden dominades per pols
i vinyetatge, que són FIXOS al sensor, i la correlació s'hi enganxa a
desplaçament zero. Un zero mesurat en una banda dominada pel patró fix
FINGEIX la H_comuna. Per això: (1) les bandes de mesura són interiors
(corona dominant), (2) cada parella es mesura també en dues mitges bandes
radials per veure la dispersió, i (3) hi ha una banda de CONTROL llunyana
(3,6-4,4 R☉) que ensenya el zero del patró fix explícitament.
"""
from __future__ import annotations

import json
import os

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v13pere")

# centre = el Sol de la geometria de referència (572A2969) en coordenades V13
SENSOR_A_V13 = (285.0, 355.0)          # X13 = sensor_x + 285 ; Y13 = sensor_y + 355
RS = 455.5                             # px, radi solar d'efemèride
SENSOR_RECT = (458, 464, 7417, 5103)   # zona amb dada real (marges blancs fora)

# vores interiors de la dada (saturació) per capa, en R☉ (research/117 §2)
VORA_INT = {"12": 1.02, "11": 1.03, "10": 1.03, "09": 1.04, "08": 1.09,
            "07": 1.15, "06": 1.17, "05": 1.23, "04": 1.31, "03": 1.41,
            "02": 1.53, "01": 1.96}
VORA_EXT = {"12": 1.14, "11": 1.55, "10": 1.96, "09": 2.31}   # la resta, el llenç

PARELLES = [("12", "11"), ("11", "10"), ("10", "09"), ("09", "08"),
            ("08", "07"), ("07", "06"), ("06", "05"), ("05", "04"),
            ("04", "03"), ("03", "02"), ("02", "01"),
            # redundància creuada
            ("10", "08"), ("09", "07"), ("08", "06"), ("06", "04"), ("04", "02"),
            # ⏭️ reforç per a les capes llargues: la 01 i la 02 tenen la banda
            #    fora de 2 R☉, on la resposta cau; més parelles independents
            ("05", "02"), ("06", "02"), ("03", "01"), ("04", "01"), ("05", "01")]


def _centre():
    pos = json.load(open(os.path.join(CAU, "posicions.json")))
    ref = pos["fotogrames"][pos["referencia"]]
    return (ref["sol_x"] + SENSOR_A_V13[0], ref["sol_y"] + SENSOR_A_V13[1]), pos


def _g(num: str) -> np.ndarray:
    f = os.path.join(CAU, f"g_{num}.npy")
    if os.path.exists(f):
        return np.load(f)
    rgb = np.load(os.path.join(CAU, f"rgb_{num}.npy"), mmap_mode="r")
    info = json.load(open(os.path.join(CAU, "info.json")))
    c = next(x for x in info["capes"] if x["num"] == num)
    W, H = info["W"], info["H"]
    full = np.zeros((H, W), np.float32)
    x0, y0, x1, y1 = c["bbox"]
    full[y0:y1, x0:x1] = rgb[..., 1].astype(np.float32) / 65535.0
    np.save(f, full)
    return full


def _banda(a: str, b: str) -> tuple[float, float]:
    rin = max(VORA_INT[a], VORA_INT[b]) + 0.05
    rout = min(VORA_EXT.get(a, 3.2), VORA_EXT.get(b, 3.2)) - 0.03
    if a == "12" or b == "12":     # la banda de la 12 és fina: marges mínims
        rin = max(VORA_INT[a], VORA_INT[b]) + 0.015
        rout = 1.145
    if b == "01" or (a == "01"):   # la 01 comença a 1,96: banda pròpia, curta
        rin, rout = 2.02, 2.90     # els plomalls encara hi són; la pols mana més enllà
    return rin, rout


def _prepara(g: np.ndarray, cx: float, cy: float, rin_px: float, rout_px: float,
             sigma: float, taper: float, rad: np.ndarray, valid: np.ndarray):
    hp = g - cv2.GaussianBlur(g, (0, 0), sigma)
    w = (np.clip((rad - rin_px) / taper, 0, 1)
         * np.clip((rout_px - rad) / taper, 0, 1) * valid)
    return hp * w


def mesura_parella(a: str, b: str, cx: float, cy: float,
                   rin: float, rout: float) -> dict:
    ga, gb = _g(a), _g(b)
    H, W = ga.shape
    rout_px, rin_px = rout * RS, rin * RS
    # retall quadrat al voltant del centre, dins del llenç
    m = int(rout_px + 80)
    x0, x1 = max(0, int(cx) - m), min(W, int(cx) + m)
    y0, y1 = max(0, int(cy) - m), min(H, int(cy) + m)
    ca, cb = ga[y0:y1, x0:x1], gb[y0:y1, x0:x1]
    ccx, ccy = cx - x0, cy - y0
    yy, xx = np.mgrid[0:ca.shape[0], 0:ca.shape[1]].astype(np.float32)
    rad = np.hypot(xx - ccx, yy - ccy)
    valid = np.zeros_like(ca)
    vx0, vy0, vx1, vy1 = SENSOR_RECT
    valid[max(0, vy0 - y0):max(0, vy1 - y0), max(0, vx0 - x0):max(0, vx1 - x0)] = 1.0
    valid *= (ca < 0.995) * (cb < 0.995)
    prim = rout - rin < 0.2
    sigma = 8.0 if prim else 20.0
    taper = 8.0 if prim else 24.0
    res = {}
    talls = [("tot", rin_px, rout_px)]
    if not prim:
        mig = 0.5 * (rin_px + rout_px)
        talls += [("int", rin_px, mig), ("ext", mig, rout_px)]
    for nom, r0, r1 in talls:
        pa = _prepara(ca, ccx, ccy, r0, r1, sigma, taper, rad, valid)
        pb = _prepara(cb, ccx, ccy, r0, r1, sigma, taper, rad, valid)
        (dx, dy), resp = cv2.phaseCorrelate(pa.astype(np.float64), pb.astype(np.float64))
        res[nom] = {"dx": float(dx), "dy": float(dy), "resposta": float(resp)}
    return res


def _autocalibra(cx: float, cy: float) -> int:
    """El signe de cv2.phaseCorrelate, comprovat i no recordat: es desplaça la
    capa 10 (+3, +2) px amb np.roll i la convenció s'ajusta perquè el resultat
    surti (+3, +2) = «contingut de B respecte del d'A»."""
    g = _g("10")
    m = 900
    x0, y0 = int(cx) - m, int(cy) - m
    ca = g[y0:y0 + 2 * m, x0:x0 + 2 * m].copy()
    cb = np.roll(np.roll(ca, 2, axis=0), 3, axis=1)
    yy, xx = np.mgrid[0:2 * m, 0:2 * m].astype(np.float32)
    rad = np.hypot(xx - m, yy - m)
    v = ((ca < 0.995) * (cb < 0.995)).astype(np.float32)
    pa = _prepara(ca, m, m, 500, 850, 20, 24, rad, v)
    pb = _prepara(cb, m, m, 500, 850, 20, 24, rad, v)
    (dx, dy), _ = cv2.phaseCorrelate(pa.astype(np.float64), pb.astype(np.float64))
    s = 1 if abs(dx - 3) < 0.3 and abs(dy - 2) < 0.3 else -1
    if s == -1 and not (abs(dx + 3) < 0.3 and abs(dy + 2) < 0.3):
        raise SystemExit(f"autocalibratge del signe impossible: ({dx:.2f}, {dy:.2f})")
    print(f"  signe de phaseCorrelate: {'directe' if s == 1 else 'invertit'} "
          f"(sintètic (+3, +2) → ({dx:+.2f}, {dy:+.2f}))")
    return s


def main():
    (cx, cy), pos = _centre()
    print(f"centre V13 = ({cx:.2f}, {cy:.2f}) · RS {RS} px")
    s = _autocalibra(cx, cy)
    F = pos["fotogrames"]
    decl = {c["num"]: c["declarat"] for c in pos["capes"]}
    ref = pos["referencia"]

    def sol(n):
        return np.array([F[n]["sol_x"], F[n]["sol_y"]])

    out = {"centre_v13": [cx, cy], "signe": s, "parelles": []}
    print(f"\n{'parella':9s} {'banda R☉':12s} {'mesurat (dx, dy)':22s} "
          f"{'H_propia':18s} {'H_comuna':14s} resp  dispersió")
    for a, b in PARELLES:
        rin, rout = _banda(a, b)
        r = mesura_parella(a, b, cx, cy, rin, rout)
        dx, dy = s * r["tot"]["dx"], s * r["tot"]["dy"]
        hp = sol(decl[b]) - sol(decl[a])
        singles = {"12", "11", "10"}
        pa_ = sol(decl[a]) if a in singles else sol(ref)
        pb_ = sol(decl[b]) if b in singles else sol(ref)
        hc = pb_ - pa_
        disp = ""
        if "int" in r:
            ddx = s * (r["int"]["dx"] - r["ext"]["dx"])
            ddy = s * (r["int"]["dy"] - r["ext"]["dy"])
            disp = f"({ddx:+.2f}, {ddy:+.2f})"
        print(f"{a}→{b:6s} {rin:.2f}-{rout:.2f}    "
              f"({dx:+6.2f}, {dy:+6.2f})      "
              f"({hp[0]:+5.2f}, {hp[1]:+5.2f})   ({hc[0]:+5.2f}, {hc[1]:+5.2f})"
              f"  {r['tot']['resposta']:.2f}  {disp}")
        out["parelles"].append({
            "a": a, "b": b, "banda_Rsol": [rin, rout],
            "mesurat": [dx, dy], "H_propia": list(map(float, hp)),
            "H_comuna": list(map(float, hc)),
            "resposta": r["tot"]["resposta"],
            "mitges_bandes": {k: {"dx": s * v["dx"], "dy": s * v["dy"],
                                  "resposta": v["resposta"]}
                              for k, v in r.items() if k != "tot"}})

    # banda de CONTROL del patró fix: una parella llarga, lluny
    print("\ncontrol del patró fix (banda 3,6-4,4 R☉, on mana la pols):")
    r = mesura_parella("02", "01", cx, cy, 3.6, 4.4)
    print(f"  02→01 llunyà: ({s*r['tot']['dx']:+.2f}, {s*r['tot']['dy']:+.2f}) "
          f"resp {r['tot']['resposta']:.2f}   ← si això és ~zero amb resposta alta, "
          f"és el sensor, no la corona")
    out["control_patro_fix"] = {k: {"dx": s * v["dx"], "dy": s * v["dy"],
                                    "resposta": v["resposta"]} for k, v in r.items()}
    json.dump(out, open(os.path.join(CAU, "desalineacio.json"), "w"),
              indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
