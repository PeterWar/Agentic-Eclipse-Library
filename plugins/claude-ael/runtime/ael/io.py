"""Files and receipts.

Every product written by the library can carry a receipt: inputs with SHA-256, parameters, library
version and the courtesy credit line.  A receipt without parameters is not a receipt.
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import platform
from pathlib import Path

import numpy as np

from . import CREDIT, __version__

__all__ = ["sha256", "load_array", "save_tiff", "save_png", "save_jpeg", "write_receipt", "save_gif", "save_mp4"]


def sha256(path: str | Path, chunk: int = 1 << 22) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def load_array(path: str | Path, mmap: bool = False) -> np.ndarray:
    p = Path(path)
    s = p.suffix.lower()
    if s == ".npy":
        return np.load(p, mmap_mode="r" if mmap else None)
    if s == ".npz":
        z = np.load(p)
        return z[list(z.keys())[0]]
    if s in (".fits", ".fit", ".fts"):
        from astropy.io import fits
        return np.asarray(fits.getdata(p))
    import tifffile
    return tifffile.imread(p)


def _meta_text(extra: str = "", ascii_only: bool = False) -> str:
    s = (CREDIT + (" | " + extra if extra else "")).strip()
    if ascii_only:
        import unicodedata
        s = s.replace("\u2014", "-").replace("\u2013", "-").replace("\u2609", "Rsun").replace("\u00b0", " deg")
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")
    return s


def save_tiff(path: str | Path, img: np.ndarray, *, description: str = "", icc: bytes | None = None) -> Path:
    """16-bit (or float) TIFF with the credit line in ImageDescription and Software."""
    import tifffile
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    extratags = []
    if icc is not None:
        extratags.append((34675, "B", len(icc), icc, True))
    tifffile.imwrite(p, img, photometric="rgb" if (img.ndim == 3 and img.shape[2] in (3, 4)) else "minisblack",
                     description=_meta_text(description, ascii_only=True), software=f"ael {__version__}", extratags=extratags,
                     compression="zlib")
    return p


def save_png(path: str | Path, img: np.ndarray, *, description: str = "") -> Path:
    """8- or 16-bit PNG with the credit line in a tEXt chunk (16-bit via OpenCV-free writer: PIL/imageio)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    a = np.asarray(img)
    if a.dtype == np.uint16:
        import imageio.v3 as iio
        iio.imwrite(p, a)
    else:
        from PIL import Image, PngImagePlugin
        info = PngImagePlugin.PngInfo()
        info.add_text("Description", _meta_text(description))
        info.add_text("Software", f"ael {__version__}")
        Image.fromarray(a).save(p, pnginfo=info, optimize=True)
    return p


def save_jpeg(path: str | Path, img8: np.ndarray, *, quality: int = 92, description: str = "") -> Path:
    from PIL import Image
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    im = Image.fromarray(np.asarray(img8, np.uint8))
    exif = im.getexif()
    exif[0x010E] = _meta_text(description, ascii_only=True)   # ImageDescription (EXIF strings are ASCII)
    exif[0x0131] = f"ael {__version__}"      # Software
    im.save(p, quality=quality, subsampling=0, exif=exif)
    return p


def save_gif(path: str | Path, frames8: list[np.ndarray], durations_ms: list[int] | int, loop: int = 0) -> Path:
    """Animated GIF from uint8 frames (gray or RGB).  One global palette keeps greys stable."""
    from PIL import Image
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    ims = [Image.fromarray(np.asarray(f, np.uint8)) for f in frames8]
    if isinstance(durations_ms, int):
        durations_ms = [durations_ms] * len(ims)
    if ims[0].mode == "L":
        ims = [im.convert("P") for im in ims]
    else:
        pal = ims[0].quantize(colors=256, method=Image.Quantize.MEDIANCUT)
        ims = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in ims]
    ims[0].save(p, save_all=True, append_images=ims[1:], duration=durations_ms, loop=loop, optimize=False,
                comment=_meta_text().encode("utf-8"))
    return p


def save_mp4(path: str | Path, frames8: list[np.ndarray], durations_ms: list[int] | int, fps: int = 30,
             crf: int = 16) -> Path | None:
    """H.264 MP4 via ffmpeg (frames repeated to honour the durations).  Returns None without ffmpeg."""
    import shutil
    import subprocess
    import tempfile
    from PIL import Image
    if shutil.which("ffmpeg") is None:
        return None
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(durations_ms, int):
        durations_ms = [durations_ms] * len(frames8)
    with tempfile.TemporaryDirectory() as td:
        k = 0
        for f, d in zip(frames8, durations_ms):
            n = max(1, int(round(d / 1000 * fps)))
            im = Image.fromarray(np.asarray(f, np.uint8)).convert("RGB")
            w, h = im.size
            im = im.crop((0, 0, w - w % 2, h - h % 2))
            for _ in range(n):
                im.save(Path(td) / f"f{k:06d}.png")
                k += 1
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(Path(td) / "f%06d.png"),
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", str(crf), "-movflags", "+faststart",
               "-metadata", f"comment={_meta_text()}", str(p)]
        subprocess.run(cmd, check=True)
    return p


def write_receipt(path: str | Path, *, product: str, inputs: dict | None = None, outputs: dict | None = None,
                  parameters: dict | None = None, gates: dict | None = None, notes: str = "",
                  hash_inputs: bool = True) -> Path:
    """JSON receipt next to a product.  ``inputs``/``outputs`` map a label to a path; files are hashed."""
    def desc(d):
        out = {}
        for k, v in (d or {}).items():
            if not isinstance(v, (str, Path)):
                out[k] = v
                continue
            p = Path(v)
            e = {"path": str(v)}
            if p.exists() and p.is_file() and hash_inputs:
                e["sha256"] = sha256(p)
                e["bytes"] = p.stat().st_size
            out[k] = e
        return out
    rec = dict(product=product, created=_dt.datetime.now().astimezone().isoformat(timespec="seconds"),
               library=f"ael {__version__}", python=platform.python_version(), inputs=desc(inputs),
               outputs=desc(outputs), parameters=parameters or {}, gates=gates or {}, notes=notes, credit=CREDIT)
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(rec, indent=1, ensure_ascii=False, default=str), encoding="utf-8")
    return p
