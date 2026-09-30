"""Peces compartides de la cadena REAGRUPEM (pilot Vixen + Canon R6 III).

Convencions que manen aquí i que no es poden canviar sense dir-ho al rebut:

- **El pedestal es MESURA a la zona emmascarada**, mai es llegeix de la
  metadada de libraw, que a la R6 III és falsa (`research/71`).
- **Tot es fa sobre `raw_image` sencer**, marges inclosos. No es retalla res
  «per comoditat»: la norma de Pere del 26-08 és que cap sortida no és un
  retall.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

import numpy as np
import rawpy

# ---------------------------------------------------------------- rutes

ARREL = os.path.expanduser("~/Desktop/REAGRUPEM")
VIXEN = os.path.join(ARREL, "Vixen R6III")
VIXEN_DARKS = os.path.join(VIXEN, "Darks Canon R6III Eclipse")
VIXEN_FLATS = os.path.join(VIXEN, "Flats R6III")
VIXEN_FLATS_INV = os.path.join(VIXEN, "Flats invertits Vixen")
SONY = os.path.join(ARREL, "300mm A7RIIIA")
SONY_QUAR = os.path.join(SONY, "En cuarantena")

PROJ_CANON = os.path.join(ARREL, "Projecte CANON")
F0 = os.path.join(PROJ_CANON, "0-CALIBRACIÓ")
F1 = os.path.join(PROJ_CANON, "1-REGISTRE")
F2 = os.path.join(PROJ_CANON, "2-LDIC")
F3 = os.path.join(PROJ_CANON, "3-FILTRES")
REBUTS = os.path.join(PROJ_CANON, "4-REBUTS")

# ⛔ NORMA DE PERE (26-08-2026): TOT el que ell ha de veure va a `Output/`,
# no a les carpetes de fase. Les carpetes de fase són feina interna —màsters,
# compostos, .npy, rebuts—; `Output/` és on hi ha els lliurables i les vistes.
OUTPUT = os.path.join(ARREL, "Output")
OUT_CANON = os.path.join(OUTPUT, "CANON")
OUT_VISTES = os.path.join(OUT_CANON, "vistes")


def vista(nom: str) -> str:
    """Ruta d'una vista, a `Output/`. Crea la carpeta si cal."""
    os.makedirs(OUT_VISTES, exist_ok=True)
    return os.path.join(OUT_VISTES, nom)


def lliurable(nom: str) -> str:
    """Ruta d'un lliurable (PSB, informe), a `Output/`."""
    os.makedirs(OUT_CANON, exist_ok=True)
    return os.path.join(OUT_CANON, nom)


def llista(carpeta: str, ext: str) -> list[str]:
    """Fitxers d'una extensió, ordenats, ruta completa."""
    if not os.path.isdir(carpeta):
        raise SystemExit(f"no hi ha la carpeta: {carpeta}")
    noms = sorted(n for n in os.listdir(carpeta) if n.upper().endswith(ext.upper()))
    return [os.path.join(carpeta, n) for n in noms]


# ------------------------------------------------------- geometria RAW


@dataclass(frozen=True)
class Geo:
    """Geometria d'un RAW, en índexs de `raw_image` (marges inclosos)."""

    alt: int
    ample: int
    marge_dalt: int
    marge_esq: int
    marge_dreta: int
    marge_baix: int
    patro: tuple[tuple[int, int], int]  # ((fila%2, col%2) -> índex de color)
    desc: str

    @property
    def visible(self) -> tuple[slice, slice]:
        return (
            slice(self.marge_dalt, self.alt - self.marge_baix),
            slice(self.marge_esq, self.ample - self.marge_dreta),
        )


def geometria(r: rawpy.RawPy) -> Geo:
    s = r.sizes
    h, w = r.raw_image.shape
    return Geo(
        alt=h,
        ample=w,
        marge_dalt=s.top_margin,
        marge_esq=s.left_margin,
        marge_dreta=w - s.left_margin - s.width,
        marge_baix=h - s.top_margin - s.height,
        patro=tuple(map(tuple, r.raw_pattern.tolist())),  # type: ignore[arg-type]
        desc=r.color_desc.decode() if isinstance(r.color_desc, bytes) else str(r.color_desc),
    )


def mapa_colors(r: rawpy.RawPy) -> np.ndarray:
    """Índex de color CFA per a CADA píxel de `raw_image` (marges inclosos).

    No s'assumeix la paritat dels marges: es reconstrueix el patró amb la
    mateixa fase que `raw_colors_visible` i s'estén als marges.
    """
    h, w = r.raw_image.shape
    s = r.sizes
    pat = np.asarray(r.raw_pattern)  # 2x2, fase de la zona VISIBLE
    fil = (np.arange(h) - s.top_margin) % 2
    col = (np.arange(w) - s.left_margin) % 2
    return pat[fil[:, None], col[None, :]]


NOMS_CFA = ("R", "G1", "B", "G2")  # índexs 0..3 de libraw amb color_desc RGBG


def nom_canal(idx: int, desc: str = "RGBG") -> str:
    lletra = desc[idx] if idx < len(desc) else "?"
    if lletra == "G":
        return "G1" if idx == 1 else "G2"
    return lletra


# --------------------------------------------------------- zona fosca


def zona_fosca(g: Geo, guarda: int = 16) -> tuple[np.ndarray, str]:
    """Màscara booleana de la zona emmascarada FIABLE de `raw_image`.

    ⛔ **Només el marge ESQUERRE.** El marge SUPERIOR queda EXCLÒS: mesurat el
    26-08 sobre els 16 màsters, les files 0-40 porten **lluïssor
    d'amplificador** que no depèn de l'exposició sinó de la TEMPERATURA del
    sensor — als darks de 0,5 s la banda va de 514 DN a 39 °C fins a 617 DN a
    44 °C, amb píxels de fins a 6.684. La zona activa no se n'assabenta
    (512,23-512,25 als setze fotogrames, sigma 0,006), o sigui que el defecte
    és de la referència, no de la imatge.

    També es deixen `guarda` píxels a cada costat: la vora física del sensor i
    la transició cap a la zona il·luminada no són fiables (la transició
    comença ~8 px abans del marge nominal).
    """
    m = np.zeros((g.alt, g.ample), dtype=bool)
    if g.marge_esq <= 2 * guarda:
        raise ValueError("marge esquerre massa prim per mesurar el pedestal")
    y0, y1 = 48, g.alt - 48
    x0, x1 = guarda, g.marge_esq - guarda
    m[y0:y1, x0:x1] = True
    return m, f"esq col[{x0}:{x1}] fila[{y0}:{y1}]  (marge superior EXCLOS: llumissor)"
