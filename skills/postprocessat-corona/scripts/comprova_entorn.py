#!/usr/bin/env python3
"""Comprova l'entorn de calibratge i apilatge de la corona. Només lectura.

Es pot executar amb qualsevol python3 (no importa res del que comprova):
detecta un intèrpret que tingui les biblioteques, mira els binaris externs,
l'efemèride, les carpetes de dades i de productes, i diu què hi falta.

Ús:
    python3 comprova_entorn.py            # informe humà
    python3 comprova_entorn.py --python   # només imprimeix l'intèrpret bo (o surt 1)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()


def troba_repo() -> Path:
    """Resol el worktree canònic tant des de la skill local com la global."""
    candidats = []
    if valor := os.environ.get("ECLIPSE2026_REPO"):
        candidats.append(Path(valor))
    candidats.extend((
        Path.cwd(),
        HOME / "Downloads/Eclipse 2026",
        # scripts/ → skill/ → skills/ → .claude/ → arrel, per la còpia local.
        Path(__file__).resolve().parents[4],
    ))
    vistos: set[Path] = set()
    for candidat in candidats:
        resolt = candidat.expanduser().resolve()
        if resolt in vistos:
            continue
        vistos.add(resolt)
        if (
            (resolt / "AGENTS.md").is_file()
            and (resolt / "research/tools/masters_vixen_v2.py").is_file()
        ):
            return resolt
    return Path.cwd().resolve()


REPO = troba_repo()
REQUISITS = Path(__file__).resolve().parents[1] / "requirements_validated.txt"

CANDIDATS_PYTHON = [
    HOME / ".venvs/eines-ia-py312/bin/python",
    REPO / "gui/.venv312/bin/python",
    Path("/opt/homebrew/bin/python3.12"),
    Path("/opt/homebrew/bin/python3"),
]
MODULS = ["numpy", "scipy", "rawpy", "tifffile", "skimage", "cv2", "skyfield",
          "astropy", "photutils", "PIL"]

DADES = {
    "Vixen totalitat (124 CR3)": HOME / "Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat",
    "Masters_v2 del Vixen": HOME / "Desktop/Eclipse 2026/Vixen R6III/Vixen Fase totalitat/Masters_v2",
    "Vixen sencer (247 CR3)": HOME / "Desktop/Eclipse 2026/Vixen R6III",
    "Sony 300 mm (194 ARW)": HOME / "Desktop/Eclipse 2026/300mm A7RIIIA",
    "Sony calibrated": HOME / "Desktop/Eclipse 2026/300mm A7RIIIA/calibrated",
    "Darks R6 III": HOME / "Desktop/Eclipse 2026/Vixen R6III/Darks Canon R6III Eclipse",
    "Darks A7RIIIA": HOME / "Desktop/Eclipse 2026/300mm A7RIIIA/Darks A7RIIIA Eclipse",
    "Estrelles (placa)": HOME / "Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles",
    "Earthshine_FINAL": HOME / "Desktop/Eclipse 2026/Derivats/Earthshine/Earthshine_FINAL",
}
PRODUCTES = {
    "Corona_HDR_Vixen": HOME / "Desktop/Eclipse 2026/Derivats/Vixen/Corona_HDR_Vixen",
    "HDR4": HOME / "Desktop/Eclipse 2026/Derivats/Vixen/HDR4",
}
EINES_REPO = [
    "research/tools/masters_vixen_v2.py",
    "research/tools/prnu_vixen.py",
    "research/tools/hdr_corona_vixen.py",
    "research/tools/apila_hdr4_vixen.py",
    "research/tools/lot_calibratge_300mm.py",
]


def prova_python(p: Path) -> tuple[bool, list[str]]:
    if not p.exists():
        return False, ["no existeix"]
    codi = "import importlib.util\nfalten=[m for m in %r if importlib.util.find_spec(m) is None]\nprint(' '.join(falten))" % MODULS
    try:
        r = subprocess.run([str(p), "-c", codi], capture_output=True, text=True, timeout=60)
    except Exception as e:  # noqa: BLE001
        return False, [f"no arrenca: {e}"]
    if r.returncode != 0:
        return False, [r.stderr.strip()[-200:]]
    falten = r.stdout.split()
    return (not falten), falten


def troba_python() -> tuple[Path | None, list[str]]:
    notes = []
    for p in CANDIDATS_PYTHON:
        ok, falten = prova_python(p)
        if ok:
            return p, notes
        notes.append(f"  {p}: falten {', '.join(falten) if falten else '?'}")
    return None, notes


def versio_dng_converter() -> str | None:
    app = Path("/Applications/Adobe DNG Converter.app/Contents/Info.plist")
    if not app.exists():
        return None
    r = subprocess.run(["/usr/libexec/PlistBuddy", "-c", "Print CFBundleShortVersionString", str(app)],
                       capture_output=True, text=True)
    return r.stdout.strip() or "?"


def compta(p: Path, sufixos: tuple[str, ...]) -> int:
    if not p.is_dir():
        return 0
    return sum(1 for f in p.iterdir() if f.suffix.upper() in sufixos)


def main() -> int:
    nomes_python = "--python" in sys.argv
    py, notes = troba_python()
    if nomes_python:
        if py is None:
            print("CAP INTÈRPRET amb les biblioteques del postprocessat.", file=sys.stderr)
            print("\n".join(notes), file=sys.stderr)
            return 1
        print(py)
        return 0

    problemes = 0
    print("== Intèrpret Python")
    if py is None:
        print("  ✗ cap intèrpret amb", ", ".join(MODULS))
        print("\n".join(notes))
        print("  → repara:")
        print("    /opt/homebrew/bin/python3.12 -m venv ~/.venvs/eines-ia-py312")
        print(f"    ~/.venvs/eines-ia-py312/bin/python -m pip install -r {REQUISITS}")
        problemes += 1
    else:
        print(f"  ✓ {py}")

    print("== Binaris externs")
    for nom in ("exiftool",):
        w = shutil.which(nom)
        print(f"  {'✓' if w else '✗'} {nom}: {w or 'no trobat (brew install exiftool)'}")
        problemes += 0 if w else 1
    v = versio_dng_converter()
    print(f"  {'✓' if v else '✗'} Adobe DNG Converter: {v or 'no instal·lat'} (18.5 va donar el blanc 13995 de la R6 III)")
    problemes += 0 if v else 1

    print("== Efemèride")
    eph = HOME / ".cache/skyfield/de440s.bsp"
    print(f"  {'✓' if eph.exists() else '✗'} {eph}")
    orfe = REPO / "de440s.bsp"
    if orfe.exists():
        print(f"  ⚠ hi ha un de440s.bsp orfe a l'arrel del repositori ({orfe.stat().st_size // 1_000_000} MB): un load() relatiu l'ha baixat; no s'ha de commitar")

    print("== Eines del repositori")
    print(f"  {'✓' if REQUISITS.is_file() else '✗'} {REQUISITS}")
    problemes += 0 if REQUISITS.is_file() else 1
    for e in EINES_REPO:
        ok = (REPO / e).exists()
        print(f"  {'✓' if ok else '✗'} {e}")
        problemes += 0 if ok else 1

    print("== Dades (només lectura)")
    for nom, p in DADES.items():
        n = compta(p, (".CR3", ".ARW", ".CR2", ".TIF", ".TIFF", ".NPY", ".CSV"))
        print(f"  {'✓' if p.exists() else '✗'} {nom}: {p}  ({n} fitxers)")
        problemes += 0 if p.exists() else 1

    print("== Productes")
    for nom, p in PRODUCTES.items():
        if p.exists():
            n = sum(1 for _ in p.iterdir())
            print(f"  ✓ {nom}: {p}  ({n} entrades) — no sobreescriure a cegues: fes servir SUFIX/HDR_SUFIX/FOTO_SUFIX o carpeta nova")
        else:
            print(f"  · {nom}: {p} encara no existeix (es crea a la primera execució)")

    print("== Processos que no hi haurien de ser mentre s'apila")
    r = subprocess.run(
        ["pgrep", "-fl", "[E]clipse Command|[m]ission_host|[e]clipse_capture|[g]photo2"],
        capture_output=True,
        text=True,
    )
    if r.stdout.strip():
        print("  ⚠ hi ha processos de captura vius:\n" + r.stdout)
    else:
        print("  ✓ cap procés de captura viu")

    print()
    print("Tot a punt." if problemes == 0 else f"{problemes} coses a arreglar abans d'apilar.")
    return 0 if problemes == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
