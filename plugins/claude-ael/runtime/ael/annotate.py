"""Drawing on products: anti-aliased arrows, labels and axes for polar views.

Lessons kept from the project's annotated images: geometry is drawn with OpenCV anti-aliasing and
sub-pixel precision (``shift=4``), arrowheads are filled triangles, text is drawn with PIL, and an
annotation is anchored on the *centre* of the feature it names.
"""
from __future__ import annotations

import numpy as np

__all__ = ["draw_arrow", "draw_arrows", "draw_text", "polar_axes", "to_rgb8"]

_SH = 4
_F = 1 << _SH


def to_rgb8(img01: np.ndarray) -> np.ndarray:
    x = np.clip(np.nan_to_num(np.asarray(img01, np.float32), nan=0.0), 0, 1)
    if x.ndim == 2:
        x = np.repeat(x[..., None], 3, axis=2)
    return np.ascontiguousarray(np.round(x * 255).astype(np.uint8))


def draw_arrow(img: np.ndarray, tail, head, color=(255, 255, 255), width: float = 3.0,
               head_len: float = 14.0, head_width: float = 11.0, outline: tuple | None = (0, 0, 0)) -> np.ndarray:
    """Arrow from ``tail`` to ``head`` (float pixel coordinates) with a filled triangular head."""
    import cv2

    t = np.asarray(tail, float)
    h = np.asarray(head, float)
    d = h - t
    L = float(np.hypot(*d))
    if L < 1e-6:
        return img
    u = d / L
    n = np.array([-u[1], u[0]])
    base = h - u * head_len
    tri = np.array([h, base + n * head_width / 2, base - n * head_width / 2])

    def P(p):
        return (int(round(p[0] * _F)), int(round(p[1] * _F)))

    for col, extra in ([(outline, 2.0)] if outline is not None else []) + [(color, 0.0)]:
        cv2.line(img, P(t), P(base), col, int(round(width + extra)), cv2.LINE_AA, _SH)
        tri_o = tri if extra == 0 else np.array([h + u * extra, base + n * (head_width / 2 + extra) - u * extra,
                                                 base - n * (head_width / 2 + extra) - u * extra])
        cv2.fillConvexPoly(img, np.array([P(p) for p in tri_o], np.int32), col, cv2.LINE_AA, _SH)
    return img


def draw_arrows(img: np.ndarray, arrows: list[dict], **kw) -> np.ndarray:
    """``arrows``: dicts with ``tail`` and ``head`` (and optional ``color``)."""
    for a in arrows:
        draw_arrow(img, a["tail"], a["head"], color=a.get("color", kw.get("color", (255, 255, 255))),
                   **{k: v for k, v in kw.items() if k != "color"})
    return img


def _font(size: int):
    from PIL import ImageFont
    for name in ("/System/Library/Fonts/Supplemental/Arial.ttf", "/System/Library/Fonts/Helvetica.ttc",
                 "/Library/Fonts/Arial.ttf", "DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_text(img: np.ndarray, text: str, xy, size: int = 24, color=(255, 255, 255), anchor: str = "la",
              shadow: tuple | None = (0, 0, 0)) -> np.ndarray:
    """Draw ``text`` with PIL (anchor as in PIL: 'la' left-ascender, 'mm' middle…)."""
    from PIL import Image, ImageDraw

    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    f = _font(size)
    if shadow is not None:
        for ox, oy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
            d.text((xy[0] + ox, xy[1] + oy), text, font=f, fill=shadow, anchor=anchor)
    d.text(xy, text, font=f, fill=color, anchor=anchor)
    img[...] = np.asarray(im)
    return img


def polar_axes(img: np.ndarray, polar, *, flipped: bool = True, pa_ticks=(0, 45, 90, 135, 180, 225, 270, 315),
               rsun_ticks=None, rsun_ref: str = "sun", size: int = 22, color=(235, 235, 235),
               margin_bottom: int = 0, margin_left: int = 0) -> np.ndarray:
    """Label a polar view drawn in ``img`` (which may include margins): PA ticks with N/E/S/W names
    along the bottom, and height ticks in solar radii along the left edge."""
    names = {0: "N", 90: "E", 180: "S", 270: "W"}
    n_r, n_pa = polar.data.shape[:2]
    R = polar.geometry.sun_radius_px
    for pa in pa_ticks:
        c = polar.column_of_pa(pa)
        if not (0 <= c <= n_pa - 1):
            continue
        x = margin_left + c
        lab = names.get(int(pa) % 360, f"{int(pa)}°")
        draw_text(img, lab, (x, img.shape[0] - margin_bottom + 6 if margin_bottom else img.shape[0] - 6),
                  size=size, color=color, anchor="mt" if margin_bottom else "mb")
    if rsun_ticks:
        for rr in rsun_ticks:
            row = polar.row_of_radius(rr * R)
            if not (0 <= row <= n_r - 1):
                continue
            y = (n_r - 1 - row) if flipped else row
            draw_text(img, f"{rr:g} R☉", (margin_left - 8 if margin_left else 8, y), size=size, color=color,
                      anchor="rm" if margin_left else "lm")
    return img
