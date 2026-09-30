"""Comú per aplicar la llibreria ael a les dades de l'eclipsi del 12-08-2026 (Pere Guerra).

Rutes relatives a l'arrel del projecte (la carpeta que conté CLAUDE.md). Sortides:
- 4-RESULTATS/ael_20260930/  (dades intermèdies i rebuts)
- IA/output/ael_20260930/    (vistes per a Pere: PNG, JPG, GIF, MP4, TIF)
"""
from __future__ import annotations
import os, sys
from pathlib import Path

ARREL = Path(__file__).resolve().parents[3]
assert (ARREL / 'CLAUDE.md').exists(), ARREL
sys.path.insert(0, str(ARREL / '3-RECERCA/tools/ael'))
import ael  # noqa: E402
from ael.geometry import EclipseGeometry  # noqa: E402

RES = ARREL / '4-RESULTATS/ael_20260930'
OUT = ARREL / 'IA/output/ael_20260930'
RES.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)

LINEAL = ARREL / '4-RESULTATS/v120_20260929/cadena/v120/lineal'
# Llenç de la V120 (geometria de la Vixen): centre del Sol i radi solar de la cadena (b1_filtre_coherent_AB.py);
# nord 45,253° a la dreta de la vertical (doc. 174; anotada de l'APOD); imatge no invertida (E a l'esquerra del N).
H, W = 7506, 10551
SOL = (5361.768, 3775.748)
RS = 440.603
NORD = 45.253
ESCALA = 2.1504   # ″/px (placa de l'APOD sobre 39 HIP)

def geometria_llenc(lluna=None, r_lluna=None) -> EclipseGeometry:
    return EclipseGeometry(shape=(H, W), sun_xy=SOL, sun_radius_px=RS, moon_xy=lluna, moon_radius_px=r_lluna,
                           north_deg=NORD, mirrored=False, arcsec_per_px=ESCALA,
                           note='Llenç V120 (Vixen), Eclipse 2026-08-12, Pere Guerra')
