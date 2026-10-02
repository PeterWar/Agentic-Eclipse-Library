"""Agentic Eclipse Library (``ael``): runnable tools for total-solar-eclipse corona images.

The rest of the repository is a record of one project (the 12 August 2026 eclipse). This package is
the general part of it, rewritten so that an agent — or a person — can run it on *their own* data:

* :mod:`ael.geometry`  – Sun/Moon geometry, position angles, lunar-limb fitting.
* :mod:`ael.polar`     – polar "unrolled corona" views and their exact inverse, with anti-aliasing.
* :mod:`ael.filters`   – detail filters that only ever read observed pixels: normalised convolution,
  NRGF, MGN, WOW (starlet whitening), tangential high-pass.
* :mod:`ael.render`    – sky model, radial normalisation, structure images, chromosphere colour.
* :mod:`ael.motion`    – coronal-motion animations: epochs, Sun-frame merging, displacement vectors
  with null tests that reject sensor-fixed and Moon-fixed motion.
* :mod:`ael.calibrate` – minimal RAW calibration (dark, flat, saturation, Bayer handling).
* :mod:`ael.photoshop` – layered 16-bit Photoshop files (PSD/PSB), verified by reopening; needs psd-tools.
* :mod:`ael.annotate`, :mod:`ael.io`, :mod:`ael.synthetic`, :mod:`ael.gates` – drawing, files and
  receipts, synthetic coronae for tests, and the gates every product must pass.
* :mod:`ael.pipelines` – the three products end to end (also ``python -m ael <command>``).

Rule that shapes every function: **nothing invented, nothing mirrored**. Where there is no data the
result is ``NaN`` (or transparent), never a fill, a continuation or a reflection.
"""

__version__ = "1.1.1"

CREDIT = ("Processed with Agentic Eclipse Library by Pere Guerra — "
          "https://github.com/PeterWar/Agentic-Eclipse-Library")

from . import geometry, polar, filters, render, motion, calibrate, photoshop, annotate, io, synthetic, gates, pipelines  # noqa: E402,F401
from .geometry import EclipseGeometry  # noqa: E402,F401
