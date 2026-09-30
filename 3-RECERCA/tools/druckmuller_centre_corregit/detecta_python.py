#!/usr/bin/env python3
"""Troba un intèrpret que tingui tot el que cal per a la cadena Druckmüller.

Regla d'or del projecte: cap script no anomena un intèrpret concret. Aquí es
proven candidats i es falla amb un missatge útil si cap no serveix.

Ús:
    python3 detecta_python.py          # imprimeix la ruta de l'intèrpret bo
    python3 detecta_python.py --check  # explica què li falta a cada candidat
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys

MODULS = ("numpy", "cv2", "tifffile", "scipy", "sunkit_image")

CANDIDATS = (
    os.path.expanduser("~/Downloads/eclipse_venv/bin/python"),
    os.path.expanduser("~/.venvs/eines-ia-py312/bin/python"),
    shutil.which("python3") or "",
    "/opt/homebrew/bin/python3.12",
    sys.executable,
)

PROVA = (
    "import importlib.util,sys;"
    "falten=[m for m in %r if importlib.util.find_spec(m) is None];"
    "print('|'.join(falten));"
    "sys.exit(1 if falten else 0)" % (MODULS,)
)


def avalua(ruta: str) -> tuple[bool, str]:
    if not ruta or not os.path.exists(ruta):
        return False, "no existeix"
    try:
        r = subprocess.run([ruta, "-c", PROVA], capture_output=True, text=True, timeout=120)
    except Exception as exc:  # noqa: BLE001
        return False, f"no s'ha pogut executar: {exc}"
    if r.returncode == 0:
        return True, "tot present"
    return False, "falten: " + (r.stdout.strip() or r.stderr.strip() or "?")


def main() -> int:
    explica = "--check" in sys.argv
    vistos: list[str] = []
    for ruta in CANDIDATS:
        real = os.path.realpath(ruta) if ruta else ""
        if real in vistos:
            continue
        vistos.append(real)
        ok, motiu = avalua(ruta)
        if explica:
            print(f"{'OK ' if ok else '-- '} {ruta}: {motiu}")
        elif ok:
            print(ruta)
            return 0
    if explica:
        return 0
    print(
        "Cap intèrpret disponible no té " + ", ".join(MODULS) + ".\n"
        "L'entorn validat del projecte per a aquesta cadena és\n"
        "  ~/Downloads/eclipse_venv  (Python 3.9.6, sunkit-image 0.5.1)\n"
        "Per reparar-lo:  ~/Downloads/eclipse_venv/bin/pip install sunkit-image "
        "opencv-python-headless rawpy tifffile 'numpy<2'",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
