"""16-bit layered Photoshop files (PSD/PSB) with psd-tools: full-canvas RGBA layers with a Unicode name, blend
mode, opacity and visibility.

psd-tools only builds layers from PIL images (8 bits), so the layer records are built by hand here.  At 16 bits
Photoshop keeps the layers in the "Lr16" block and leaves the main layer section empty; psd-tools reads them from
there but writes them to the main section, so :func:`save` moves them (otherwise the layers come out wrong in
Photoshop).  The flattened composite is written uncompressed, never with ZIP.  Always reopen the file and compare
(:func:`verify`) before handing it over.

Tested with psd-tools 1.18 and 1.23 (it uses its record classes directly).  Install with ``pip install -e ".[photoshop]"``.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np

MODES = ("normal", "multiply", "overlay", "difference", "screen", "soft_light")


def _psd():
    try:
        import psd_tools  # noqa: F401
    except ImportError as e:  # pragma: no cover
        raise ImportError('Photoshop files need psd-tools: pip install -e ".[photoshop]"') from e
    from psd_tools import PSDImage
    from psd_tools.api.layers import PixelLayer
    from psd_tools.constants import BlendMode, ChannelID, Compression, Resource, Tag
    from psd_tools.psd.image_resources import ImageResource
    from psd_tools.psd.layer_and_mask import ChannelData, ChannelDataList, ChannelInfo, LayerInfo, LayerRecord
    from psd_tools.psd.tagged_blocks import TaggedBlocks
    return dict(PSDImage=PSDImage, PixelLayer=PixelLayer, BlendMode=BlendMode, ChannelID=ChannelID,
                Compression=Compression, Resource=Resource, Tag=Tag, ImageResource=ImageResource,
                ChannelData=ChannelData, ChannelDataList=ChannelDataList, ChannelInfo=ChannelInfo,
                LayerInfo=LayerInfo, LayerRecord=LayerRecord, TaggedBlocks=TaggedBlocks)


def to_u16(x: np.ndarray) -> np.ndarray:
    """0–1 floats to uint16 (NaN → 0); pair it with an alpha that is 0 where there is no data."""
    a = np.nan_to_num(np.asarray(x, np.float64), nan=0.0)
    return np.round(np.clip(a, 0.0, 1.0) * 65535.0).astype(np.uint16)


def new_document(width: int, height: int, *, psb: bool = True):
    """An empty 16-bit RGB document.  ``psb=True`` (large document format) is needed beyond 30,000 px or 2 GB."""
    P = _psd()
    doc = P["PSDImage"].new("RGB", (int(width), int(height)), depth=16)
    if psb:
        doc._record.header.version = 2
    doc._next_layer_id = 1
    return doc


def add_layer(doc, name: str, rgb16: np.ndarray, alpha16: np.ndarray | None = None, *, mode: str = "normal",
              opacity: float = 1.0, visible: bool = True, rle: bool = False):
    """Append a full-canvas layer on top.  ``rgb16``: (H, W, 3) or (H, W) grey, uint16; ``alpha16``: (H, W)
    uint16 or None (opaque).  ``opacity`` 0–1."""
    P = _psd()
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    rgb16 = np.asarray(rgb16)
    if rgb16.ndim == 2:
        rgb16 = np.repeat(rgb16[..., None], 3, axis=2)
    if rgb16.dtype != np.uint16 or rgb16.shape[2] != 3:
        raise ValueError("rgb16 must be uint16, (H, W, 3) or (H, W)")
    h, w = rgb16.shape[:2]
    if (h, w) != (doc.height, doc.width):
        raise ValueError(f"layer is {w}×{h}, document is {doc.width}×{doc.height}: layers are full canvas")
    if alpha16 is None:
        alpha16 = np.full((h, w), 65535, np.uint16)
    elif alpha16.dtype != np.uint16 or alpha16.shape != (h, w):
        raise ValueError("alpha16 must be uint16 (H, W)")
    rec = P["LayerRecord"](top=0, left=0, bottom=h, right=w, channel_info=[])
    rec.name = name.encode("mac_roman", "replace").decode("mac_roman")[:31]
    rec.tagged_blocks.set_data(P["Tag"].UNICODE_LAYER_NAME, name)
    rec.tagged_blocks.set_data(P["Tag"].LAYER_ID, doc._next_layer_id)
    doc._next_layer_id += 1
    rec.blend_mode = getattr(P["BlendMode"], mode.upper())
    rec.opacity = int(round(float(opacity) * 255))
    rec.flags.visible = bool(visible)
    comp = P["Compression"].RLE if rle else P["Compression"].ZIP_WITH_PREDICTION
    cdl = P["ChannelDataList"]()
    ver = doc._record.header.version
    planes = ((P["ChannelID"].TRANSPARENCY_MASK, alpha16), (P["ChannelID"](0), rgb16[..., 0]),
              (P["ChannelID"](1), rgb16[..., 1]), (P["ChannelID"](2), rgb16[..., 2]))
    for cid, plane in planes:
        cd = P["ChannelData"](comp)
        cd.set_data(np.ascontiguousarray(plane).astype(">u2").tobytes(), w, h, 16, ver)
        rec.channel_info.append(P["ChannelInfo"](cid, len(cd.data) + 2))
        cdl.append(cd)
    layer = P["PixelLayer"](doc, rec, cdl)
    doc.append(layer)
    return layer


def _to_lr16(doc) -> None:
    P = _psd()
    lmi = doc._record.layer_and_mask_information
    li = lmi.layer_info
    if li is None or not li.layer_records:
        return
    if lmi.tagged_blocks is None:
        lmi.tagged_blocks = P["TaggedBlocks"]()
    lmi.tagged_blocks.set_data(P["Tag"].LAYER_16, layer_count=li.layer_count, layer_records=li.layer_records,
                               channel_image_data=li.channel_image_data)
    lmi.layer_info = P["LayerInfo"]()


def save(doc, path: str | Path, composite16: np.ndarray, *, icc: bytes | None = None) -> Path:
    """Write the file.  ``composite16`` (H, W, 3) uint16 is the flattened image other programs show (usually the
    visible layers flattened); ``icc`` the colour profile to embed (say which one in the receipt).  Never call
    ``doc.save()``: psd-tools would recompose the composite at 8 bits."""
    P = _psd()
    composite16 = np.asarray(composite16)
    if composite16.dtype != np.uint16 or composite16.shape != (doc.height, doc.width, 3):
        raise ValueError("composite16 must be uint16 (H, W, 3) with the document size")
    rec = doc._record
    rec.image_data.compression = P["Compression"].RAW
    rec.image_data.set_data([np.ascontiguousarray(composite16[..., k]).astype(">u2").tobytes() for k in range(3)],
                            rec.header)
    if icc:
        rec.image_resources[P["Resource"].ICC_PROFILE] = P["ImageResource"](
            signature=b"8BIM", key=P["Resource"].ICC_PROFILE, name="", data=icc)
    _to_lr16(doc)
    path = Path(path)
    if path.exists():
        raise FileExistsError(f"{path} exists: write a new file, never overwrite the user's work")
    with open(path, "wb") as f:
        rec.write(f)
    return path


def verify(path: str | Path, expected: list[dict]) -> dict:
    """Reopen ``path`` and compare every layer with ``expected`` (dicts with name, mode, opacity, visible and,
    optionally, rgb16 / alpha16 to compare pixel by pixel).  Returns a report; ``ok`` is False on any mismatch."""
    P = _psd()
    doc = P["PSDImage"].open(str(path))
    layers = list(doc)
    rep = dict(file=str(path), depth=int(doc.depth), size=[doc.width, doc.height], layers=len(layers),
               mismatches=[])
    if len(layers) != len(expected):
        rep["mismatches"].append(f"{len(layers)} layers, expected {len(expected)}")
    for lay, exp in zip(layers, expected):
        tag = exp["name"]
        if lay.name != exp["name"]:
            rep["mismatches"].append(f"name {lay.name!r} != {exp['name']!r}")
        if "mode" in exp and lay.blend_mode != getattr(P["BlendMode"], exp["mode"].upper()):
            rep["mismatches"].append(f"{tag}: mode {lay.blend_mode}")
        if "opacity" in exp and lay.opacity != int(round(exp["opacity"] * 255)):
            rep["mismatches"].append(f"{tag}: opacity {lay.opacity}")
        if "visible" in exp and bool(lay.visible) != bool(exp["visible"]):
            rep["mismatches"].append(f"{tag}: visibility {lay.visible}")
        if "rgb16" in exp:
            got = np.asarray(lay.numpy("color"), np.float64)
            want = np.asarray(exp["rgb16"], np.float64)
            if want.ndim == 2:
                want = np.repeat(want[..., None], 3, axis=2)
            err = float(np.max(np.abs(got * 65535.0 - want))) if got.shape == want.shape else float("inf")
            if err > 0.5:
                rep["mismatches"].append(f"{tag}: colour differs by up to {err:.1f} DN16")
        if "alpha16" in exp and exp["alpha16"] is not None:
            got = np.asarray(lay.numpy("shape"), np.float64)
            got = got[..., 0] if got.ndim == 3 else got
            err = float(np.max(np.abs(got * 65535.0 - exp["alpha16"].astype(np.float64))))
            if err > 0.5:
                rep["mismatches"].append(f"{tag}: alpha differs by up to {err:.1f} DN16")
    rep["ok"] = not rep["mismatches"]
    return rep
