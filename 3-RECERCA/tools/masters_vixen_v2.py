#!/usr/bin/env python3
"""Masters de fosc v2 per al tren Vixen (R6 III + VSD90SS).

Corregeix els dos defectes que `research/75` §1 va identificar als masters
del 15-08:

  1. **mitjana retallada, no mediana.** La mediana d'enters molt quantitzats
     deixa la imatge 0,132 ADU massa baixa. Aquí es descarta el mínim i el
     màxim per píxel (rebuig de còsmics) i es fa la mitjana de la resta, que
     no té biaix.
  2. **selecció per temperatura.** El dèficit de pedestal de l'esglaó de 10 s
     va a −0,0549 ADU/°C. Els fotogrames de la totalitat són a 41-42 °C, o
     sigui que el master s'ha de fer amb darks d'aquella temperatura i no amb
     el lot sencer (43-44 °C sobre-restaria 0,20 ADU i importaria el triple de
     píxels calents).

⛔ No es descarta cap fotograma per `frame_std`: `research/75` §1 demostra que
aquella mètrica mira el marge òpticament emmascarat i no la imatge.

Sortida: `<destí>/master_<exp>.npy` (float32, retall visible parell) i el seu
JSON amb la procedència. Idempotent: no refà el que ja hi és.
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import rawpy

DARKS = Path.home() / "Desktop/Eclipse 2026/Vixen R6III/Darks Canon R6III Eclipse"
DEST = Path.home() / "Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat/Masters_v2"

# Temperatura de treball: els 68 fotogrames de la totalitat són a 41-42 °C.
T_OBJECTIU = 41.5
N_MAX = 16
N_MIN = 6

# Les quinze exposicions del programa dins la totalitat.
EXPOSICIONS = [
    0.0003125, 0.0005, 0.001, 0.002, 0.004, 0.008,
    1 / 60, 1 / 30, 1 / 15, 0.125, 0.25, 0.5, 1.0, 2.0, 10.0,
]


def retall_parell(a: np.ndarray) -> np.ndarray:
    """Retall visible amb dimensions parelles, per poder partir el mosaic."""
    return a[: a.shape[0] // 2 * 2, : a.shape[1] // 2 * 2]


def inventari() -> dict[float, list[tuple[str, float]]]:
    out = subprocess.run(
        ["exiftool", "-q", "-n", "-T", "-FileName", "-ExposureTime",
         "-CameraTemperature", *sorted(str(p) for p in DARKS.glob("*.CR3"))],
        capture_output=True, text=True, check=True,
    ).stdout
    per_exp: dict[float, list[tuple[str, float]]] = defaultdict(list)
    for linia in out.splitlines():
        nom, exp, temp = linia.split("\t")
        per_exp[float(exp)].append((nom, float(temp)))
    return per_exp


def tria(candidats: list[tuple[str, float]]) -> list[tuple[str, float]]:
    """Els N_MAX darks més a prop de la temperatura de treball."""
    ordenats = sorted(candidats, key=lambda c: (abs(c[1] - T_OBJECTIU), c[0]))
    return sorted(ordenats[:N_MAX], key=lambda c: c[0])


def mitjana_retallada(fitxers: list[str]) -> tuple[np.ndarray, np.ndarray]:
    """Mitjana descartant mínim i màxim per píxel; retorna (mitjana, sigma)."""
    pila = None
    for i, nom in enumerate(fitxers):
        with rawpy.imread(str(DARKS / nom)) as raw:
            v = retall_parell(raw.raw_image_visible)
        if pila is None:
            pila = np.empty((len(fitxers), *v.shape), np.uint16)
        pila[i] = v
    n = pila.shape[0]
    mitjana = np.empty(pila.shape[1:], np.float32)
    sigma = np.empty(pila.shape[1:], np.float32)
    pas = 400
    for y in range(0, pila.shape[1], pas):
        bloc = pila[:, y:y + pas].astype(np.float32)
        bloc.sort(axis=0)
        centre = bloc[1:-1] if n >= 5 else bloc
        mitjana[y:y + pas] = centre.mean(axis=0)
        sigma[y:y + pas] = centre.std(axis=0)
    return mitjana, sigma


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    per_exp = inventari()
    for exp in EXPOSICIONS:
        clau = f"{exp:.10g}"
        desti = DEST / f"master_{clau}.npy"
        if desti.exists():
            print(f"  {clau:12s} ja hi és")
            continue
        candidats = next(
            (v for k, v in per_exp.items() if abs(k - exp) < 1e-9), None)
        if candidats is None or len(candidats) < N_MIN:
            print(f"  {clau:12s} ⛔ només {len(candidats or [])} darks")
            continue
        triats = tria(candidats)
        mitjana, sigma = mitjana_retallada([n for n, _ in triats])
        temps = [t for _, t in triats]
        meta = {
            "exposure_s": exp,
            "n_darks": len(triats),
            "darks": [n for n, _ in triats],
            "temperatures_C": temps,
            "T_mediana_C": float(np.median(temps)),
            "metode": "mitjana retallada (min i max descartats per pixel)",
            "pedestal_mitjana_ADU": float(mitjana.mean()),
            "pedestal_mediana_ADU": float(np.median(mitjana)),
            "soroll_master_ADU": float(np.median(sigma) / np.sqrt(len(triats) - 2)),
            "sigma_fotograma_ADU": float(np.median(sigma)),
            "forma": list(mitjana.shape),
        }
        np.save(desti, mitjana)
        desti.with_suffix(".json").write_text(
            json.dumps(meta, indent=1, ensure_ascii=False))
        print(f"  {clau:12s} n={len(triats):2d} T={meta['T_mediana_C']:.1f}°C "
              f"pedestal={meta['pedestal_mediana_ADU']:.3f} "
              f"sigma={meta['sigma_fotograma_ADU']:.3f} ADU")
    return 0


if __name__ == "__main__":
    sys.exit(main())
