"""Utility helper functions."""

import os
import sys
import math


def recommended_radial_bins(inner_px: float, outer_px: float, logarithmic=False, width_px=4.0) -> int:
    """Choose rings no wider than width_px (inner ring for log spacing)."""
    if not math.isfinite(width_px) or width_px <= 0:
        raise ValueError("Ring width must be positive and finite")
    if not 0 < inner_px < outer_px:
        raise ValueError("Radial bounds must satisfy 0 < inner < outer")
    if logarithmic:
        return max(1, math.ceil(math.log(outer_px / inner_px) / math.log1p(width_px / inner_px)))
    return max(1, math.ceil((outer_px - inner_px) / width_px))


def resource_path(relative_path: str) -> str:
    """Resolves absolute resource path compatible with dev and frozen executables."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(base_path, relative_path)


def application_icon_path() -> str:
    """Use ICO on Windows and PNG elsewhere, avoiding Qt's ICNS decoder."""
    extension = "ico" if sys.platform == "win32" else "png"
    base = "assets/Eclipse_Image_Processor"
    native_path = resource_path(f"{base}.{extension}")
    return native_path if os.path.isfile(native_path) else resource_path(f"{base}.png")
