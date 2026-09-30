"""Construeix Corretgint2.psb sense modificar els píxels font.

Aplicació executable de la porta Photoshop de ``postprocessat-corona`` per al
subconjunt concret de Corretgint.psb.  La geometria, els perfils i les portes
de protecció són deliberadament explícits: si canvia l'entrada, el programa
s'atura en lloc d'improvisar una nova compensació.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, ChannelID, Compression, Tag
from psd_tools.psd.layer_and_mask import MaskFlags
from scipy import ndimage as ndi
from scipy import sparse
from scipy.sparse import linalg as spla


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "capes_interiors_v4"))
from psb_utils import add_mask16, finalize_lr16, set_merged  # noqa: E402


WIDTH = 7648
HEIGHT = 5353
FRAME = (457, 463, 7417, 5103)  # left, top, right, bottom
FRAME_W = FRAME[2] - FRAME[0]
FRAME_H = FRAME[3] - FRAME[1]
SUN = (4020.89, 2737.66)
R_SUN = 446.15
BIN_RSUN = 0.002
PROFILE_SIGMA_BINS = 10.0

# La capa curta inferior és l'única autoritat per a les perles/diamant que
# conté.  El suport es congela ABANS de construir cap màscara superior.  Els
# llindars són deliberadament específics d'aquesta font validada i queden
# protegits pel SHA de l'entrada: no es reutilitzen a cegues en una altra foto.
PROTECTED_SOURCE_LAYER_ID = 3
PROTECTED_ANNULUS_PX = (400.0, 600.0)
PROTECTED_SEED_MIN_RGB = 0.99
PROTECTED_CORE_MIN_RGB = 0.20
PROTECTED_FEATHER_MIN_RGB = 0.10
PROTECTED_MIN_SEED_PIXELS = 3
PROTECTED_BEAD_MIN_RGB = 0.99
EXPECTED_PROTECTED_CORE_PIXELS = 1676
EXPECTED_BEAD_COMPONENTS = 4
EXPECTED_BEAD_PIXELS = 263
OWN_LUNAR_FEATHER_OUTSIDE_PX = 4.0
ID5_LUNAR_CORE_OUTSIDE_PX = 3.0
ID5_LUNAR_FEATHER_END_OUTSIDE_PX = 18.0
ID7_LUNAR_CORE_OUTSIDE_PX = 3.0
ID7_LUNAR_FEATHER_WIDTH_PX = 18.0

PROTECTED_PROM_SOURCE_LAYER_ID = 4
PROTECTED_LIMB_CORE_OUTSIDE_PX = 4.0
PROTECTED_PROM_REFERENCE_OFFSETS_PX = (35.0, 100.0)
PROTECTED_PROM_REFERENCE_GREEN_MIN = 0.01
PROTECTED_PROM_REFERENCE_PERCENTILE = 45.0
PROTECTED_PROM_ZONE_OUTSIDE_PX = 64.0
PROTECTED_PROM_SEED_EXCESS = 0.040
PROTECTED_PROM_SEED_RED = 0.060
PROTECTED_PROM_ALLOWED_EXCESS = 0.012
PROTECTED_PROM_ALLOWED_RED = 0.020
PROTECTED_PROM_MIN_SEED_PIXELS = 3
PROTECTED_RADIAL_FEATHER_END_OUTSIDE_PX = 10.0
PROTECTED_COMPATIBILITY_WIDTH_PX = 40
PROTECTED_COMPATIBILITY_GAMMA = 1.0 / 2.2
PROTECTED_COMPATIBILITY_SCALE = 0.10
PROTECTED_COMPATIBILITY_SOLVER_RESIDUAL_MAX = 1.0e-10
EXPECTED_LIMB_CORE_PIXELS = 11_414
EXPECTED_PROM_CORE_PIXELS = 6_481
EXPECTED_PROM_COMPONENTS = 6
EXPECTED_PROM_COMPONENTS_DESCRIPTOR = (
    (5889, (3545, 2566, 3616, 2881)),
    (208, (3648, 2471, 3669, 2499)),
    (195, (4021, 2262, 4031, 2287)),
    (144, (4404, 2986, 4426, 3005)),
    (38, (4063, 3189, 4078, 3194)),
    (7, (3626, 2538, 3629, 2541)),
)
EXPECTED_STRONG_PROM_PIXELS = 4_978
EXPECTED_STRONG_PROM_GROUP_AREAS = (4651, 159, 118, 41, 6, 3)
EXPECTED_STRONG_PROM_COMPONENTS_DESCRIPTOR = (
    (4651, (3548, 2566, 3614, 2876)),
    (159, (3648, 2471, 3669, 2498)),
    (118, (4023, 2263, 4030, 2286)),
    (41, (4413, 2990, 4424, 2997)),
    (6, (4065, 3191, 4068, 3193)),
    (3, (3627, 2538, 3629, 2540)),
)
EXPECTED_RADIAL_CORE_PIXELS = 652_689
EXPECTED_RADIAL_GATE_NONZERO_PIXELS = 670_024
EXPECTED_PHOTOMETRIC_GATE_NONZERO_PIXELS = 6_481
EXPECTED_PROTECTED_4_UNION_PIXELS = 657_192
EXPECTED_PROTECTED_4_GATE_NONZERO_PIXELS = 673_652
EXPECTED_PROTECTED_4_EFFECTIVE_GATE_PIXELS = 673_445
EXPECTED_PROTECTED_4_EFFECTIVE_PLUME_PIXELS = 16_253
EXPECTED_PROM_RED_GREEN_SCALE = 1.6335238218307495
EXPECTED_ALLOWED_PROM_SHA256 = "3c4f8f477d642aa0ba4ad88b1a04d8ee2f6719f1a6a6363b74c7210cb3c68f8e"
EXPECTED_STRONG_PROM_SHA256 = "1bf6bb3defeb53b0c60f97657d25f51acd8faff2361fe38feadf57e6520c2fd3"
EXPECTED_PHOTOMETRIC_GATE_SHA256 = "bd556c1d84362ad443b93a18fef521d08ed19cdbb0cf4c3e84019682ef363386"
EXPECTED_RADIAL_CORE_SHA256 = "d3c758f324063678bea97c5b3a2d8dadfe9fa57af2b945988d4d08efc1cd6dec"
EXPECTED_RADIAL_GATE_SHA256 = "a4c1ca5a101473f301136552d300c3c5c7160fb8baf66ee3180a952085e155e2"
EXPECTED_PROTECTED_4_CORE_SHA256 = "1647bd9fbedd5789239c590d56a0456c3a10e98bfab309e569c42a95269cab7c"
EXPECTED_PROTECTED_4_GATE_SHA256 = "0c69d9a124ef4a27895559ad91f82bcd9aea7045dc2788c9b031d5ebd56d0f89"
EXPECTED_PROTECTED_4_Q16_SHA256 = "e214a72c94089592b1eefd436fb82d9621a12887e9d79d557b025c91627c3914"
EXPECTED_H40_DOMAIN_PIXELS = 69_296
EXPECTED_H40_DOMAIN_OVERLAP_PIXELS = 4_352
EXPECTED_H40_COMBINED_EFFECTIVE_PIXELS = 704_856
EXPECTED_H40_PHOTO_U16_SHA256 = "b9a206f923f3ac323c83104c51058b851183772efd8af444a512ea01bb876d2f"
EXPECTED_H40_GATE_U16_SHA256 = "72f128ecb06937028d1c1e58962820796e89d679cfbe73f900d61e6c0d0e13e6"
EXPECTED_H40_Q_U16_SHA256 = "4a35befd1f7174facb1baaf1933586002d0112d9270808a437ccae27dc496148"
EXPECTED_H40_DOMAIN_SHA256 = "04148e8fed9bf14c77acedc74de50a89821f35ba7d1cbf0b4b413aa25e9859a9"

# Control de regressió del contacte principal. Ja no governa la màscara: ha
# d'estar completament inclòs dins el selector Hα de sis components.
CONTACT_ROI_ELLIPSE = (3578.0, 2653.0, 140.0, 160.0)
CONTACT_ROI_REFERENCE_RADII = (480.0, 560.0)
CONTACT_ROI_REFERENCE_EXCLUDED_ANGLES = (130.0, 220.0)
CONTACT_ROI_SIGMA_MULTIPLIER = 8.0
CONTACT_ROI_SEED_EXCESS = 0.20
EXPECTED_CONTACT_ROI_PIXELS = 4_365
EXPECTED_CONTACT_ROI_COMPONENT_AREAS = (4031, 334)

SOURCE_SHA256 = "d8afed2a997f8a449180be804561e6ed17eeaee30146970364a5daeba911730b"
SOURCE_SIZE = 708_214_002

EXPECTED_LAYERS = (
    (3, "12_1-3200s_572A2956.CR3", (457, 463, 7417, 5103)),
    (4, "Capa 1", (0, 0, 7648, 5353)),
    (5, "Capa 2", (0, 0, 7648, 5353)),
    (6, "09_1-60s_572A2975_apilat2.dng", (458, 464, 7418, 5104)),
    (7, "09_1-60s_572A2975_apilat2.dng", (457, 463, 7417, 5103)),
)

FINAL_NAMES = {
    3: "12_1-3200s_572A2956.CR3 · FONT_PROTEGIDA · PERLES-DIAMANT",
    4: "11_1-500s_572A2968.CR3 · FONT_PROTEGIDA · LIMBE-PROTUBERÀNCIES",
    5: "10_1-125s_572A2969.CR3 · FONT_HDR · CORONA INTERIOR",
    7: "09_1-60s_572A2975+572A2993_apilat2.dng · FONT_HDR · CORONA INTERIOR-MITJANA",
}

MOON = {
    3: (4036.27, 2740.24, 451.83),
    4: (4036.494, 2738.531, 451.800),
    5: (4037.03, 2738.18, 451.71),
    7: (4033.62, 2735.62, 451.34),
}

PROFILE_RADII = (1.0, 1.1, 1.5, 2.0)
EXPECTED_PROFILE_VALUES = {
    4: (0.868, 0.996, 1.000, 0.924),
    5: (0.729, 0.831, 0.425, 0.051),
    7: (0.148, 0.533, 0.796, 0.313),
}


def log(start: float, *parts: object) -> None:
    print(f"[{time.monotonic() - start:6.1f}s]", *parts, flush=True)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def channel_map(layer):
    return {ci.id: (ci, cd) for ci, cd in zip(layer._record.channel_info, layer._channels)}


def channel_bytes(layer, channel_id: ChannelID, header) -> bytes:
    channels = channel_map(layer)
    if channel_id not in channels:
        raise AssertionError(f"falta canal {channel_id} a layer_id={layer.layer_id}")
    return channels[channel_id][1].get_data(layer.width, layer.height, header.depth, header.version)


def source_channel_hashes(layer, header) -> dict[str, str]:
    result = {}
    for channel_id in (
        ChannelID.TRANSPARENCY_MASK,
        ChannelID.CHANNEL_0,
        ChannelID.CHANNEL_1,
        ChannelID.CHANNEL_2,
    ):
        result[str(int(channel_id))] = hashlib.sha256(channel_bytes(layer, channel_id, header)).hexdigest()
    return result


def channel_u16(layer, channel_id: ChannelID, header) -> np.ndarray:
    raw = channel_bytes(layer, channel_id, header)
    expected = layer.width * layer.height * 2
    if len(raw) != expected:
        raise AssertionError(
            f"canal no és 16-bit: layer_id={layer.layer_id}, canal={int(channel_id)}, "
            f"bytes={len(raw)}, esperat={expected}"
        )
    return np.frombuffer(raw, dtype=">u2").reshape(layer.height, layer.width)


def layer_rect_u16(layer, channel_id: ChannelID, header, rect=FRAME) -> np.ndarray:
    left, top, right, bottom = rect
    out = np.zeros((bottom - top, right - left), dtype=np.uint16)
    x0 = max(left, layer.left)
    y0 = max(top, layer.top)
    x1 = min(right, layer.right)
    y1 = min(bottom, layer.bottom)
    if x0 >= x1 or y0 >= y1:
        return out
    data = channel_u16(layer, channel_id, header)
    out[y0 - top : y1 - top, x0 - left : x1 - left] = data[
        y0 - layer.top : y1 - layer.top,
        x0 - layer.left : x1 - layer.left,
    ]
    return out


def mask_rect_float(layer, header, rect) -> np.ndarray:
    """Llegeix només dades explícites de màscara; fora bbox sempre és zero.

    Això evita heretar el background=255 invàlid de la còpia antiga d'1/60.
    """
    md = layer._record.mask_data
    if md is None:
        raise AssertionError(f"layer_id={layer.layer_id} no té màscara")
    channels = channel_map(layer)
    if ChannelID.USER_LAYER_MASK not in channels:
        raise AssertionError(f"layer_id={layer.layer_id} no té canal de màscara")
    mw = md.right - md.left
    mh = md.bottom - md.top
    raw = channels[ChannelID.USER_LAYER_MASK][1].get_data(mw, mh, header.depth, header.version)
    if len(raw) != mw * mh * 2:
        raise AssertionError(f"màscara layer_id={layer.layer_id} no és 16-bit")
    data = np.frombuffer(raw, dtype=">u2").reshape(mh, mw)
    left, top, right, bottom = rect
    out = np.zeros((bottom - top, right - left), dtype=np.float32)
    x0 = max(left, md.left)
    y0 = max(top, md.top)
    x1 = min(right, md.right)
    y1 = min(bottom, md.bottom)
    if x0 < x1 and y0 < y1:
        out[y0 - top : y1 - top, x0 - left : x1 - left] = (
            data[y0 - md.top : y1 - md.top, x0 - md.left : x1 - md.left].astype(np.float32)
            / 65535.0
        )
    return out


def smootherstep(value: np.ndarray) -> np.ndarray:
    value = np.clip(value, 0.0, 1.0)
    return value * value * value * (value * (value * 6.0 - 15.0) + 10.0)


def radial_profile(mask: np.ndarray, bins: np.ndarray, nbins: int) -> np.ndarray:
    sums = np.bincount(bins.ravel(), weights=mask.ravel(), minlength=nbins)
    counts = np.bincount(bins.ravel(), minlength=nbins).astype(np.float64)
    profile = np.full(nbins, np.nan, dtype=np.float64)
    valid = counts > 0
    profile[valid] = sums[valid] / counts[valid]
    finite = np.isfinite(profile)
    if not finite.any():
        raise AssertionError("perfil radial buit")
    profile[~finite] = np.interp(np.flatnonzero(~finite), np.flatnonzero(finite), profile[finite])
    profile = ndi.gaussian_filter1d(profile, PROFILE_SIGMA_BINS, mode="nearest")
    return np.clip(profile, 0.0, 1.0).astype(np.float32)


def radial_image(profile: np.ndarray, r_sun: np.ndarray) -> np.ndarray:
    radii = np.arange(profile.size, dtype=np.float32) * BIN_RSUN
    out = np.empty(r_sun.shape, dtype=np.float32)
    for y0 in range(0, r_sun.shape[0], 192):
        y1 = min(y0 + 192, r_sun.shape[0])
        out[y0:y1] = np.interp(r_sun[y0:y1], radii, profile).astype(np.float32)
    return out


def profile_controls(profile: np.ndarray) -> list[float]:
    return [float(profile[int(round(radius / BIN_RSUN))]) for radius in PROFILE_RADII]


def max_rgb_frame(layer, header) -> np.ndarray:
    maximum = np.zeros((FRAME_H, FRAME_W), dtype=np.float32)
    for channel_id in (ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2):
        channel = layer_rect_u16(layer, channel_id, header).astype(np.float32)
        channel *= 1.0 / 65535.0
        np.maximum(maximum, channel, out=maximum)
        del channel
    return maximum


def min_rgb_frame(layer, header) -> np.ndarray:
    minimum = np.ones((FRAME_H, FRAME_W), dtype=np.float32)
    for channel_id in (ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2):
        channel = layer_rect_u16(layer, channel_id, header).astype(np.float32)
        channel *= 1.0 / 65535.0
        np.minimum(minimum, channel, out=minimum)
        del channel
    return minimum


def saturation_gate(maximum: np.ndarray, r_sun: np.ndarray) -> np.ndarray:
    gate = smootherstep((maximum - 0.60) / 0.25)
    gate *= ((r_sun > 0.95) & (r_sun < 1.15)).astype(np.float32)
    return ndi.gaussian_filter(gate, 1.5, mode="nearest").astype(np.float32)


def protected_contact_support(minimum: np.ndarray, xx: np.ndarray, yy: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict]:
    """Congela el suport de perles/diamant/protuberància de la capa inferior.

    La detecció és per histèresi sobre LA FONT PROTEGIDA: una capa superior no
    pot definir aquesta regió amb la seva pròpia saturació perquè el fenomen
    temporal ja hi pot haver desaparegut. El mínim dels tres canals separa el
    fotosfèric blanc de la protuberància vermella, que en aquest document té la
    seva font inferior dedicada a l'1/500. El nucli queda binari i exacte; la
    ploma fotomètrica només ocupa el senyal entre 0,10 i 0,20, mai el fons fosc.
    """
    cx, cy, _radius = MOON[PROTECTED_SOURCE_LAYER_ID]
    distance = np.hypot(xx - cx, yy - cy)
    annulus = (distance >= PROTECTED_ANNULUS_PX[0]) & (distance <= PROTECTED_ANNULUS_PX[1])
    seed = annulus & (minimum >= PROTECTED_SEED_MIN_RGB)
    allowed = annulus & (minimum >= PROTECTED_FEATHER_MIN_RGB)
    labels, _count = ndi.label(allowed)
    seed_labels = np.unique(labels[seed])
    keep = [
        int(label)
        for label in seed_labels
        if label > 0 and np.count_nonzero(seed & (labels == label)) >= PROTECTED_MIN_SEED_PIXELS
    ]
    connected = np.isin(labels, keep)
    core = connected & (minimum >= PROTECTED_CORE_MIN_RGB)
    del labels, seed, allowed, annulus, distance
    if np.count_nonzero(core) != EXPECTED_PROTECTED_CORE_PIXELS:
        raise AssertionError(
            f"suport protegit inesperat: {np.count_nonzero(core)} px, "
            f"esperat={EXPECTED_PROTECTED_CORE_PIXELS}"
        )

    ys, xs = np.nonzero(core)
    if not len(xs):
        raise AssertionError("suport protegit buit")
    gate = smootherstep(
        (minimum - PROTECTED_FEATHER_MIN_RGB)
        / (PROTECTED_CORE_MIN_RGB - PROTECTED_FEATHER_MIN_RGB)
    )
    gate *= connected.astype(np.float32)
    gate[core] = 1.0
    del connected
    stats = {
        "source_layer_id": PROTECTED_SOURCE_LAYER_ID,
        "annulus_px": list(PROTECTED_ANNULUS_PX),
        "seed_min_rgb": PROTECTED_SEED_MIN_RGB,
        "core_min_rgb": PROTECTED_CORE_MIN_RGB,
        "feather_min_rgb": PROTECTED_FEATHER_MIN_RGB,
        "core_pixels": int(core.sum()),
        "core_bbox_document": [
            int(xs.min() + FRAME[0]),
            int(ys.min() + FRAME[1]),
            int(xs.max() + FRAME[0] + 1),
            int(ys.max() + FRAME[1] + 1),
        ],
        "feather_nonzero_pixels": int(np.count_nonzero(gate)),
    }
    return core, gate, stats


def protected_prominence_support(
    layer,
    header,
    xx: np.ndarray,
    yy: np.ndarray,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    dict,
]:
    """Congela limbe i protuberàncies de la font inferior 1/500.

    El limbe es protegeix fins a tres sigma del residu del seu ajust circular.
    Les sis estructures Hα es detecten exclusivament al raster de l'1/500, per
    histèresi sobre l'excés R-rho*G. Cap saturació de l'1/125 pot definir o
    ampliar el suport. El selector antic de dues estructures del contacte queda
    només com a regressió inclosa dins aquesta porta completa de sis components.
    """
    red = layer_rect_u16(layer, ChannelID.CHANNEL_0, header).astype(np.float32)
    green = layer_rect_u16(layer, ChannelID.CHANNEL_1, header).astype(np.float32)
    red *= 1.0 / 65535.0
    green *= 1.0 / 65535.0

    cx, cy, radius = MOON[PROTECTED_PROM_SOURCE_LAYER_ID]
    distance = np.hypot(xx - cx, yy - cy).astype(np.float32)
    offset = distance - np.float32(radius)
    reference = (
        (offset >= PROTECTED_PROM_REFERENCE_OFFSETS_PX[0])
        & (offset <= PROTECTED_PROM_REFERENCE_OFFSETS_PX[1])
        & (green > PROTECTED_PROM_REFERENCE_GREEN_MIN)
    )
    if not np.any(reference):
        raise AssertionError("referència cromàtica 1/500 buida")
    ratios = red[reference] / np.maximum(green[reference], 1.0 / 65535.0)
    rho = float(np.percentile(ratios, PROTECTED_PROM_REFERENCE_PERCENTILE))
    del ratios, reference
    if abs(rho - EXPECTED_PROM_RED_GREEN_SCALE) > 1.0e-9:
        raise AssertionError(
            f"escala R/G inesperada: {rho}, esperada={EXPECTED_PROM_RED_GREEN_SCALE}"
        )
    excess = red - np.float32(rho) * green
    zone = (offset > 0.0) & (offset <= PROTECTED_PROM_ZONE_OUTSIDE_PX)
    seed = zone & (excess >= PROTECTED_PROM_SEED_EXCESS) & (red >= PROTECTED_PROM_SEED_RED)
    allowed = (
        zone
        & (excess >= PROTECTED_PROM_ALLOWED_EXCESS)
        & (red >= PROTECTED_PROM_ALLOWED_RED)
    )
    del zone
    structure = np.ones((3, 3), dtype=np.uint8)
    labels, count = ndi.label(allowed, structure=structure)
    del allowed
    seed_counts = np.bincount(labels[seed].ravel(), minlength=count + 1)
    keep_ids = np.flatnonzero(seed_counts >= PROTECTED_PROM_MIN_SEED_PIXELS)
    keep_ids = keep_ids[keep_ids > 0]
    del seed_counts

    allowed_kept = np.isin(labels, keep_ids)
    strong_core = seed & allowed_kept
    prominence_descriptors = []
    strong_descriptors = []
    for label_id in keep_ids:
        selected = labels == label_id
        comp_y, comp_x = np.nonzero(selected)
        prominence_descriptors.append(
            (
                int(comp_x.size),
                (
                    int(comp_x.min() + FRAME[0]),
                    int(comp_y.min() + FRAME[1]),
                    int(comp_x.max() + FRAME[0] + 1),
                    int(comp_y.max() + FRAME[1] + 1),
                ),
            )
        )
        selected_strong = selected & strong_core
        strong_y, strong_x = np.nonzero(selected_strong)
        strong_descriptors.append(
            (
                int(strong_x.size),
                (
                    int(strong_x.min() + FRAME[0]),
                    int(strong_y.min() + FRAME[1]),
                    int(strong_x.max() + FRAME[0] + 1),
                    int(strong_y.max() + FRAME[1] + 1),
                ),
            )
        )
        del selected, selected_strong, comp_x, comp_y, strong_x, strong_y
    del labels, seed
    prominence_descriptors = sorted(prominence_descriptors, reverse=True)
    strong_descriptors = sorted(strong_descriptors, reverse=True)
    prominence_pixels = int(np.count_nonzero(allowed_kept))
    strong_pixels = int(np.count_nonzero(strong_core))
    if (
        prominence_pixels != EXPECTED_PROM_CORE_PIXELS
        or len(prominence_descriptors) != EXPECTED_PROM_COMPONENTS
        or tuple(prominence_descriptors) != EXPECTED_PROM_COMPONENTS_DESCRIPTOR
        or strong_pixels != EXPECTED_STRONG_PROM_PIXELS
        or tuple(strong_descriptors) != EXPECTED_STRONG_PROM_COMPONENTS_DESCRIPTOR
    ):
        raise AssertionError(
            "suport protegit 1/500 inesperat: "
            f"allowed={prominence_pixels}, strong={strong_pixels}, "
            f"components={prominence_descriptors}, forts={strong_descriptors}"
        )

    # Ploma exclusivament fotomètrica: mai surt dels sis CC Hα retinguts.
    photo_gate = (
        smootherstep(
            (excess - PROTECTED_PROM_ALLOWED_EXCESS)
            / (PROTECTED_PROM_SEED_EXCESS - PROTECTED_PROM_ALLOWED_EXCESS)
        )
        * smootherstep(
            (red - PROTECTED_PROM_ALLOWED_RED)
            / (PROTECTED_PROM_SEED_RED - PROTECTED_PROM_ALLOWED_RED)
        )
        * allowed_kept.astype(np.float32)
    ).astype(np.float32)
    photo_gate[strong_core] = 1.0
    del excess

    # Regressió del contacte principal: 2 components (4031+334 px). Aquest
    # selector no governa l'alfa; només demostra que el gate complet no n'omet
    # cap píxel.
    ellipse_x, ellipse_y, ellipse_rx, ellipse_ry = CONTACT_ROI_ELLIPSE
    ellipse = (
        ((xx - ellipse_x) / ellipse_rx) ** 2
        + ((yy - ellipse_y) / ellipse_ry) ** 2
        < 1.0
    )
    angle = np.arctan2(-(yy - cy), xx - cx).astype(np.float32)
    angle *= np.float32(180.0 / np.pi)
    angle %= np.float32(360.0)
    excluded_start, excluded_end = CONTACT_ROI_REFERENCE_EXCLUDED_ANGLES
    roi_reference = (
        (distance >= CONTACT_ROI_REFERENCE_RADII[0])
        & (distance < CONTACT_ROI_REFERENCE_RADII[1])
        & ~ellipse
        & ~((angle >= excluded_start) & (angle <= excluded_end))
    )
    del angle
    roi_rho = float(
        np.median(red[roi_reference] / np.maximum(green[roi_reference], 1.0e-6))
    )
    roi_excess = red - np.float32(roi_rho) * green
    roi_median = float(np.median(roi_excess[roi_reference]))
    roi_sigma = float(
        1.4826 * np.median(np.abs(roi_excess[roi_reference] - roi_median))
    )
    roi_threshold = roi_median + CONTACT_ROI_SIGMA_MULTIPLIER * roi_sigma
    del roi_reference, red, green
    roi_raw = ellipse & (roi_excess >= roi_threshold)
    roi_seed = ellipse & (roi_excess >= CONTACT_ROI_SEED_EXCESS)
    del ellipse, roi_excess
    roi_labels, roi_count = ndi.label(roi_raw, structure=structure)
    del roi_raw
    roi_seed_counts = np.bincount(
        roi_labels[roi_seed].ravel(), minlength=roi_count + 1
    )
    roi_keep_ids = np.flatnonzero(roi_seed_counts >= PROTECTED_PROM_MIN_SEED_PIXELS)
    roi_keep_ids = roi_keep_ids[roi_keep_ids > 0]
    del roi_seed, roi_seed_counts
    roi_core = np.zeros(roi_labels.shape, dtype=bool)
    roi_areas = []
    for label_id in roi_keep_ids:
        component = ndi.binary_fill_holes(roi_labels == label_id)
        roi_areas.append(int(np.count_nonzero(component)))
        roi_core |= component
        del component
    del roi_labels
    roi_areas = tuple(sorted(roi_areas, reverse=True))
    if (
        int(np.count_nonzero(roi_core)) != EXPECTED_CONTACT_ROI_PIXELS
        or roi_areas != EXPECTED_CONTACT_ROI_COMPONENT_AREAS
    ):
        raise AssertionError(
            "regressió ROI-2 inesperada: "
            f"pixels={np.count_nonzero(roi_core)}, àrees={roi_areas}"
        )

    limb_core = (offset > 0.0) & (offset <= PROTECTED_LIMB_CORE_OUTSIDE_PX)
    limb_pixels = int(np.count_nonzero(limb_core))
    if limb_pixels != EXPECTED_LIMB_CORE_PIXELS:
        raise AssertionError(
            f"anell de limbe inesperat: {limb_pixels}, esperat={EXPECTED_LIMB_CORE_PIXELS}"
        )
    radial_core = offset <= PROTECTED_LIMB_CORE_OUTSIDE_PX
    radial_core_pixels = int(np.count_nonzero(radial_core))
    # Forma literal congelada: és algebraicament equivalent a 1-S((d-4)/6),
    # però no byte-idèntica en float32 als sis píxels de frontera.
    radial_gate = smootherstep(
        (PROTECTED_RADIAL_FEATHER_END_OUTSIDE_PX - offset)
        / (
            PROTECTED_RADIAL_FEATHER_END_OUTSIDE_PX
            - PROTECTED_LIMB_CORE_OUTSIDE_PX
        )
    )
    radial_gate = radial_gate.astype(np.float32)
    radial_gate[radial_core] = 1.0
    radial_gate[offset >= PROTECTED_RADIAL_FEATHER_END_OUTSIDE_PX] = 0.0
    radial_gate_nonzero = int(np.count_nonzero(radial_gate))
    if (
        radial_core_pixels != EXPECTED_RADIAL_CORE_PIXELS
        or radial_gate_nonzero != EXPECTED_RADIAL_GATE_NONZERO_PIXELS
    ):
        raise AssertionError(
            "porta radial inesperada: "
            f"core={radial_core_pixels}, suport={radial_gate_nonzero}"
        )

    core = radial_core | strong_core
    union_pixels = int(np.count_nonzero(core))
    gate = np.maximum(radial_gate, photo_gate)
    gate[core] = 1.0
    gate_nonzero_pixels = int(np.count_nonzero(gate))
    q16 = np.clip(np.rint((1.0 - gate) * 65535.0), 0, 65535).astype(np.uint16)
    effective_gate = q16 < 65535
    effective_gate_pixels = int(np.count_nonzero(effective_gate))
    effective_plume_pixels = int(np.count_nonzero(effective_gate & ~core))
    photo_gate_nonzero = int(np.count_nonzero(photo_gate))
    if (
        union_pixels != EXPECTED_PROTECTED_4_UNION_PIXELS
        or gate_nonzero_pixels != EXPECTED_PROTECTED_4_GATE_NONZERO_PIXELS
        or effective_gate_pixels != EXPECTED_PROTECTED_4_EFFECTIVE_GATE_PIXELS
        or effective_plume_pixels != EXPECTED_PROTECTED_4_EFFECTIVE_PLUME_PIXELS
        or photo_gate_nonzero != EXPECTED_PHOTOMETRIC_GATE_NONZERO_PIXELS
    ):
        raise AssertionError(
            "suport/ploma ID4 inesperats: "
            f"nucli={union_pixels}, foto={photo_gate_nonzero}, "
            f"total={gate_nonzero_pixels}, efectiu={effective_gate_pixels}, "
            f"ploma_efectiva={effective_plume_pixels}"
        )
    if np.any((photo_gate > 0.0) & ~allowed_kept):
        raise AssertionError("la ploma Hα ha sortit del senyal allowed")
    roi_outside = roi_core & (offset > 0.0)
    roi_inside = roi_core & (offset <= 0.0)
    if not np.all(gate[roi_core] > 0.0):
        raise AssertionError("el gate complet omet part del control ROI-2")
    roi_outside_pixels = int(np.count_nonzero(roi_outside))
    roi_inside_pixels = int(np.count_nonzero(roi_inside))
    if (roi_outside_pixels, roi_inside_pixels) != (4343, 22):
        raise AssertionError(
            f"partició ROI-2 inesperada: fora={roi_outside_pixels}, dins={roi_inside_pixels}"
        )
    del roi_outside, roi_inside
    core_sha256 = hashlib.sha256(np.ascontiguousarray(core).tobytes()).hexdigest()
    allowed_sha256 = hashlib.sha256(np.ascontiguousarray(allowed_kept).tobytes()).hexdigest()
    strong_sha256 = hashlib.sha256(np.ascontiguousarray(strong_core).tobytes()).hexdigest()
    photo_gate_sha256 = hashlib.sha256(np.ascontiguousarray(photo_gate).tobytes()).hexdigest()
    radial_core_sha256 = hashlib.sha256(np.ascontiguousarray(radial_core).tobytes()).hexdigest()
    radial_gate_sha256 = hashlib.sha256(np.ascontiguousarray(radial_gate).tobytes()).hexdigest()
    gate_sha256 = hashlib.sha256(np.ascontiguousarray(gate).tobytes()).hexdigest()
    q16_sha256 = hashlib.sha256(np.ascontiguousarray(q16).tobytes()).hexdigest()
    if (
        core_sha256 != EXPECTED_PROTECTED_4_CORE_SHA256
        or allowed_sha256 != EXPECTED_ALLOWED_PROM_SHA256
        or strong_sha256 != EXPECTED_STRONG_PROM_SHA256
        or photo_gate_sha256 != EXPECTED_PHOTOMETRIC_GATE_SHA256
        or radial_core_sha256 != EXPECTED_RADIAL_CORE_SHA256
        or radial_gate_sha256 != EXPECTED_RADIAL_GATE_SHA256
        or gate_sha256 != EXPECTED_PROTECTED_4_GATE_SHA256
        or q16_sha256 != EXPECTED_PROTECTED_4_Q16_SHA256
    ):
        raise AssertionError(
            "hash geomètric inesperat a P4: "
            f"core={core_sha256}, allowed={allowed_sha256}, strong={strong_sha256}, "
            f"foto={photo_gate_sha256}, radial={radial_gate_sha256}, "
            f"gate={gate_sha256}, q16={q16_sha256}"
        )
    del limb_core, radial_core, effective_gate, q16, distance, offset

    stats = {
        "source_layer_id": PROTECTED_PROM_SOURCE_LAYER_ID,
        "reference_offsets_px": list(PROTECTED_PROM_REFERENCE_OFFSETS_PX),
        "reference_green_min": PROTECTED_PROM_REFERENCE_GREEN_MIN,
        "reference_percentile": PROTECTED_PROM_REFERENCE_PERCENTILE,
        "red_green_scale": rho,
        "seed_thresholds": {
            "excess": PROTECTED_PROM_SEED_EXCESS,
            "red": PROTECTED_PROM_SEED_RED,
        },
        "allowed_thresholds": {
            "excess": PROTECTED_PROM_ALLOWED_EXCESS,
            "red": PROTECTED_PROM_ALLOWED_RED,
        },
        "prominence_allowed_pixels": prominence_pixels,
        "prominence_allowed_components": [
            {"area_px": area, "bbox_document": list(bbox)}
            for area, bbox in prominence_descriptors
        ],
        "prominence_strong_pixels": strong_pixels,
        "prominence_strong_groups": [
            {"area_px": area, "bbox_document": list(bbox)}
            for area, bbox in strong_descriptors
        ],
        "prominence_gate": "photometric product, no EDT",
        "prominence_gate_nonzero_pixels": photo_gate_nonzero,
        "limb_fit": {"center": [cx, cy], "radius_px": radius, "rms_px": 1.316},
        "limb_core_outside_px": PROTECTED_LIMB_CORE_OUTSIDE_PX,
        "limb_core_pixels": limb_pixels,
        "radial_core_pixels_including_disc": radial_core_pixels,
        "radial_feather_end_outside_px": PROTECTED_RADIAL_FEATHER_END_OUTSIDE_PX,
        "radial_gate_nonzero_pixels": radial_gate_nonzero,
        "union_core_pixels": union_pixels,
        "combined_gate_nonzero_pixels": gate_nonzero_pixels,
        "combined_gate_effective_u16_pixels": effective_gate_pixels,
        "effective_plume_outside_core_pixels": effective_plume_pixels,
        "union_core_sha256": core_sha256,
        "allowed_sha256": allowed_sha256,
        "strong_sha256": strong_sha256,
        "photometric_gate_float32_sha256": photo_gate_sha256,
        "radial_core_sha256": radial_core_sha256,
        "radial_gate_float32_sha256": radial_gate_sha256,
        "gate_float32_sha256": gate_sha256,
        "q16_sha256": q16_sha256,
        "contact_roi_regression": {
            "red_green_scale": roi_rho,
            "excess_median": roi_median,
            "excess_sigma_robust": roi_sigma,
            "excess_threshold": roi_threshold,
            "core_pixels": int(np.count_nonzero(roi_core)),
            "component_areas": list(roi_areas),
            "outside_disc_included_in_gate_pixels": roi_outside_pixels,
            "inside_disc_included_in_radial_gate_pixels": roi_inside_pixels,
        },
    }
    del roi_core
    return core, gate, strong_core, allowed_kept, photo_gate, radial_gate, stats


def quantize_half_up_u16(value: np.ndarray) -> np.ndarray:
    """Quantització canònica: mig LSB sempre cap amunt."""
    return np.clip(np.floor(np.asarray(value, dtype=np.float64) * 65535.0 + 0.5), 0, 65535).astype(
        np.uint16
    )


def compose_p3_upper_reference(
    layers_by_id: dict[int, object],
    header,
    frozen_lower_path: Path,
    mask5_path: Path,
    mask7_path: Path,
) -> tuple[np.ndarray, np.ndarray]:
    """Retorna L4 congelat i el compost superior original després de P3."""
    lower = np.load(frozen_lower_path, mmap_mode="r").astype(np.float32)
    if lower.shape != (FRAME_H, FRAME_W, 3):
        raise AssertionError("referència L4 inesperada")
    lower *= 1.0 / 65535.0
    alpha5 = np.load(mask5_path, mmap_mode="r").astype(np.float32)
    alpha7 = np.load(mask7_path, mmap_mode="r").astype(np.float32)
    if alpha5.shape != (FRAME_H, FRAME_W) or alpha7.shape != alpha5.shape:
        raise AssertionError("màscares P3 inesperades")
    alpha5 *= 1.0 / 65535.0
    alpha7 *= 1.0 / 65535.0
    upper = lower.copy()
    for layer_id, alpha in ((5, alpha5), (7, alpha7)):
        source = np.stack(
            [
                layer_rect_u16(layers_by_id[layer_id], channel_id, header)
                for channel_id in (
                    ChannelID.CHANNEL_0,
                    ChannelID.CHANNEL_1,
                    ChannelID.CHANNEL_2,
                )
            ],
            axis=-1,
        ).astype(np.float32)
        source *= 1.0 / 65535.0
        upper += (source - upper) * alpha[..., None]
        del source
    del alpha5, alpha7
    return lower, upper


def harmonic_compatibility_gate(
    lower: np.ndarray,
    upper: np.ndarray,
    allowed_kept: np.ndarray,
    strong_core: np.ndarray,
    radial_gate: np.ndarray,
    core: np.ndarray,
    width_px: int = PROTECTED_COMPATIBILITY_WIDTH_PX,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    """Ploma mínima guiada per compatibilitat, no per geometria del fenomen.

    Per cada un dels sis grups Hα, el nucli fort queda a 1 i la frontera del
    domini a 0. Entre tots dos es resol una extensió harmònica ponderada per la
    diferència gamma-RGB entre L4 congelat i el compost superior original.
    Aquesta ploma és només una zona de barreja; ``allowed_kept`` continua sent
    l'únic suport científic del fenomen.
    """
    expected_rgb = (FRAME_H, FRAME_W, 3)
    expected_mask = (FRAME_H, FRAME_W)
    if lower.shape != expected_rgb or upper.shape != expected_rgb:
        raise AssertionError("compositors inesperats per a la ploma harmònica")
    for name, mask in (
        ("allowed", allowed_kept),
        ("strong", strong_core),
        ("radial", radial_gate),
        ("core", core),
    ):
        if mask.shape != expected_mask:
            raise AssertionError(f"geometria inesperada a {name}")
    if width_px <= 0:
        raise AssertionError("amplada harmònica no positiva")
    if np.any(strong_core & ~allowed_kept):
        raise AssertionError("el nucli fort Halpha no és subconjunt d'allowed")

    lower_gamma = np.power(
        np.clip(lower, 0.0, 1.0), np.float32(PROTECTED_COMPATIBILITY_GAMMA)
    )
    upper_gamma = np.power(
        np.clip(upper, 0.0, 1.0), np.float32(PROTECTED_COMPATIBILITY_GAMMA)
    )
    compatibility = np.linalg.norm(lower_gamma - upper_gamma, axis=2).astype(np.float32)
    del lower_gamma, upper_gamma

    labels, count = ndi.label(
        allowed_kept, structure=np.ones((3, 3), dtype=np.uint8)
    )
    if count != EXPECTED_PROM_COMPONENTS:
        raise AssertionError(f"components Halpha inesperats per H{width_px}: {count}")
    photo = np.zeros(expected_mask, dtype=np.float64)
    declared_domain = np.zeros(expected_mask, dtype=bool)
    overlap_count = np.zeros(expected_mask, dtype=np.uint8)
    component_stats = []
    for label_id in range(1, count + 1):
        component = labels == label_id
        fixed_one_full = component & strong_core
        if np.count_nonzero(fixed_one_full) < PROTECTED_PROM_MIN_SEED_PIXELS:
            raise AssertionError(f"component Halpha {label_id} sense nucli fort")
        ys, xs = np.nonzero(component)
        y0 = max(0, int(ys.min()) - width_px - 2)
        y1 = min(FRAME_H, int(ys.max()) + width_px + 3)
        x0 = max(0, int(xs.min()) - width_px - 2)
        x1 = min(FRAME_W, int(xs.max()) + width_px + 3)
        comp = component[y0:y1, x0:x1]
        fixed_one = fixed_one_full[y0:y1, x0:x1]
        distance = ndi.distance_transform_edt(~comp)
        domain = distance < float(width_px)
        variable = domain & ~fixed_one
        index = np.full(variable.shape, -1, dtype=np.int32)
        index[variable] = np.arange(np.count_nonzero(variable), dtype=np.int32)
        compdiff = compatibility[y0:y1, x0:x1].astype(np.float64)
        conductance = 1.0 + (compdiff / PROTECTED_COMPATIBILITY_SCALE) ** 2
        rows: list[np.ndarray] = []
        cols: list[np.ndarray] = []
        data: list[np.ndarray] = []
        rhs = np.zeros(np.count_nonzero(variable), dtype=np.float64)
        vy, vx = np.nonzero(variable)
        for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            ny = vy + dy
            nx = vx + dx
            valid = (
                (ny >= 0)
                & (ny < variable.shape[0])
                & (nx >= 0)
                & (nx < variable.shape[1])
            )
            src_y = vy[valid]
            src_x = vx[valid]
            dst_y = ny[valid]
            dst_x = nx[valid]
            src_i = index[src_y, src_x]
            weight = 0.5 * (
                conductance[src_y, src_x] + conductance[dst_y, dst_x]
            )
            rows.append(src_i)
            cols.append(src_i)
            data.append(weight)
            dst_i = index[dst_y, dst_x]
            dst_variable = dst_i >= 0
            rows.append(src_i[dst_variable])
            cols.append(dst_i[dst_variable])
            data.append(-weight[dst_variable])
            dst_one = fixed_one[dst_y, dst_x]
            np.add.at(rhs, src_i[dst_one], weight[dst_one])
        matrix = sparse.coo_matrix(
            (np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
            shape=(rhs.size, rhs.size),
            dtype=np.float64,
        ).tocsr()
        solution = spla.spsolve(matrix, rhs, permc_spec="NATURAL")
        residual_abs = float(np.max(np.abs(matrix @ solution - rhs), initial=0.0))
        residual_relative = residual_abs / max(1.0, float(np.max(np.abs(rhs), initial=0.0)))
        if not np.all(np.isfinite(solution)) or residual_relative > PROTECTED_COMPATIBILITY_SOLVER_RESIDUAL_MAX:
            raise AssertionError(
                f"solver H{width_px} no convergent al component {label_id}: "
                f"residu_rel={residual_relative}"
            )
        local = np.zeros(variable.shape, dtype=np.float64)
        local[variable] = np.clip(solution, 0.0, 1.0)
        local[fixed_one] = 1.0
        current = photo[y0:y1, x0:x1]
        np.maximum(current, local, out=current)
        declared_domain[y0:y1, x0:x1] |= domain
        overlap_count[y0:y1, x0:x1] += domain.astype(np.uint8)
        component_stats.append(
            {
                "component": label_id,
                "allowed_pixels": int(np.count_nonzero(component)),
                "strong_pixels": int(np.count_nonzero(fixed_one_full)),
                "domain_pixels": int(np.count_nonzero(domain)),
                "variable_pixels": int(rhs.size),
                "solver_residual_abs": residual_abs,
                "solver_residual_relative": residual_relative,
            }
        )
        del (
            component,
            fixed_one_full,
            ys,
            xs,
            comp,
            fixed_one,
            distance,
            domain,
            variable,
            index,
            compdiff,
            conductance,
            rows,
            cols,
            data,
            rhs,
            vy,
            vx,
            matrix,
            solution,
            local,
        )
    del labels, compatibility

    photo_u16 = quantize_half_up_u16(photo)
    photo_u16[strong_core] = 65535
    photo_u16[~declared_domain] = 0
    radial_u16 = quantize_half_up_u16(radial_gate)
    gate_u16 = np.maximum(radial_u16, photo_u16)
    gate_u16[core] = 65535
    if np.any(photo_u16[strong_core] != 65535):
        raise AssertionError("H40 no congela tots els nuclis forts")
    if np.any(photo_u16[~declared_domain]):
        raise AssertionError("H40 surt del domini declarat")
    gate = gate_u16.astype(np.float32) * (1.0 / 65535.0)
    photo_float = photo_u16.astype(np.float32) * (1.0 / 65535.0)
    stats = {
        "method": "weighted harmonic compatibility plume",
        "scientific_support": "six Halpha allowed components from frozen ID4",
        "blend_zone": "per-component EDT domain only; geometry does not set weights",
        "width_px": width_px,
        "gamma": PROTECTED_COMPATIBILITY_GAMMA,
        "compatibility_scale": PROTECTED_COMPATIBILITY_SCALE,
        "solver": "scipy.spsolve float64, NATURAL permutation, 4-neighbour mean conductance",
        "quantization": "uint16 half-up; uint16 gate is authoritative",
        "components": component_stats,
        "declared_domain_pixels": int(np.count_nonzero(declared_domain)),
        "domain_overlap_pixels": int(np.count_nonzero(overlap_count > 1)),
        "photo_effective_pixels": int(np.count_nonzero(photo_u16)),
        "combined_effective_pixels": int(np.count_nonzero(gate_u16)),
        "combined_core_pixels": int(np.count_nonzero(gate_u16 == 65535)),
        "photo_u16_sha256": hashlib.sha256(np.ascontiguousarray(photo_u16).tobytes()).hexdigest(),
        "gate_u16_sha256": hashlib.sha256(np.ascontiguousarray(gate_u16).tobytes()).hexdigest(),
        "q_u16_sha256": hashlib.sha256(
            np.ascontiguousarray(np.uint16(65535) - gate_u16).tobytes()
        ).hexdigest(),
        "declared_domain_sha256": hashlib.sha256(
            np.ascontiguousarray(declared_domain).tobytes()
        ).hexdigest(),
    }
    if (
        stats["declared_domain_pixels"] != EXPECTED_H40_DOMAIN_PIXELS
        or stats["domain_overlap_pixels"] != EXPECTED_H40_DOMAIN_OVERLAP_PIXELS
        or stats["photo_effective_pixels"] != EXPECTED_H40_DOMAIN_PIXELS
        or stats["combined_effective_pixels"] != EXPECTED_H40_COMBINED_EFFECTIVE_PIXELS
        or stats["photo_u16_sha256"] != EXPECTED_H40_PHOTO_U16_SHA256
        or stats["gate_u16_sha256"] != EXPECTED_H40_GATE_U16_SHA256
        or stats["q_u16_sha256"] != EXPECTED_H40_Q_U16_SHA256
        or stats["declared_domain_sha256"] != EXPECTED_H40_DOMAIN_SHA256
    ):
        raise AssertionError(f"reproducció H40 inesperada: {stats}")
    del photo, radial_u16, overlap_count
    return photo_float, gate, gate_u16, declared_domain, stats


def moon_distance(layer_id: int, xx: np.ndarray, yy: np.ndarray) -> np.ndarray:
    cx, cy, _radius = MOON[layer_id]
    return np.hypot(xx - cx, yy - cy).astype(np.float32)


def write_full_mask(path: Path, frame_mask: np.ndarray) -> None:
    quantized = np.clip(np.rint(frame_mask * 65535.0), 0, 65535).astype(np.uint16)
    write_full_mask_u16(path, quantized)
    del quantized


def write_full_mask_u16(path: Path, frame_mask: np.ndarray) -> None:
    if frame_mask.shape != (FRAME_H, FRAME_W) or frame_mask.dtype != np.uint16:
        raise AssertionError("màscara de frame inesperada")
    target = np.lib.format.open_memmap(path, mode="w+", dtype=np.uint16, shape=(HEIGHT, WIDTH))
    target[:] = 0
    target[FRAME[1] : FRAME[3], FRAME[0] : FRAME[2]] = frame_mask
    target.flush()
    del target


def save_frame_mask_u16(path: Path, frame_mask: np.ndarray) -> None:
    target = np.lib.format.open_memmap(
        path, mode="w+", dtype=np.uint16, shape=(FRAME_H, FRAME_W)
    )
    target[:] = np.clip(np.rint(frame_mask * 65535.0), 0, 65535).astype(np.uint16)
    target.flush()
    del target


def joint_protect_stack_u16(
    base_paths: list[Path],
    gate: np.ndarray,
    core: np.ndarray,
    output_paths: list[Path],
    layer_ids: list[int],
    gate_name: str,
    gate_u16_authority: np.ndarray | None = None,
) -> dict:
    """Atenua conjuntament una pila Normal preservant tots els seus pesos.

    Per q=1-g, la transformació es resol de dalt cap avall. El coeficient
    objectiu de cada font és q pel seu coeficient original; l'alfa nova és
    aquest coeficient dividit per la supervivència ja quantitzada de les capes
    superiors. Això generalitza exactament, entre d'altres, el parell:

      a7' = q*a7
      a5' = q*(1-a7)*a5/(1-a7')

    La branca g=0 copia bytes; g=1 dona zero literal. Si la supervivència nova
    ja és zero, l'alfa inferior és render-irrellevant i es copia per estabilitat.
    """
    if not base_paths or len(base_paths) != len(output_paths) or len(base_paths) != len(layer_ids):
        raise AssertionError("pila conjunta mal definida")
    if gate.shape != (FRAME_H, FRAME_W) or core.shape != gate.shape:
        raise AssertionError("geometria inesperada a la protecció conjunta")
    if gate_u16_authority is not None and (
        gate_u16_authority.shape != gate.shape
        or gate_u16_authority.dtype != np.uint16
    ):
        raise AssertionError("autoritat u16 de gate inesperada")
    bases = [np.load(path, mmap_mode="r") for path in base_paths]
    if any(base.shape != gate.shape or base.dtype != np.uint16 for base in bases):
        raise AssertionError("màscares base inesperades a la protecció conjunta")
    outputs = [
        np.lib.format.open_memmap(path, mode="w+", dtype=np.uint16, shape=gate.shape)
        for path in output_paths
    ]

    max_coefficient_error = {str(layer_id): 0.0 for layer_id in layer_ids}
    max_lower_coefficient_error = 0.0
    outside_changes = {str(layer_id): 0 for layer_id in layer_ids}
    core_nonzero = {str(layer_id): 0 for layer_id in layer_ids}
    for y0 in range(0, FRAME_H, 192):
        y1 = min(FRAME_H, y0 + 192)
        gate_block = gate[y0:y1]
        core_block = core[y0:y1]
        base_u16 = [np.asarray(base[y0:y1], dtype=np.uint16) for base in bases]
        base_alpha = [block.astype(np.float64) / 65535.0 for block in base_u16]
        if gate_u16_authority is None:
            q_u16 = np.clip(
                np.rint((1.0 - gate_block) * 65535.0), 0, 65535
            ).astype(np.uint16)
        else:
            q_u16 = np.uint16(65535) - np.asarray(
                gate_u16_authority[y0:y1], dtype=np.uint16
            )
        q = q_u16.astype(np.float64) / 65535.0
        unchanged = q_u16 == 65535
        q_zero = q_u16 == 0
        survival_base = np.ones(q.shape, dtype=np.float64)
        survival_new = np.ones(q.shape, dtype=np.float64)
        new_u16: list[np.ndarray | None] = [None] * len(base_u16)

        for index in range(len(base_u16) - 1, -1, -1):
            target_coefficient = q * survival_base * base_alpha[index]
            alpha_new = np.zeros(q.shape, dtype=np.float64)
            np.divide(
                target_coefficient,
                survival_new,
                out=alpha_new,
                where=survival_new > 0.0,
            )
            alpha_new_u16 = np.clip(
                np.rint(alpha_new * 65535.0), 0, 65535
            ).astype(np.uint16)
            degenerate = (survival_new <= 0.0) & ~q_zero & ~unchanged
            alpha_new_u16[degenerate] = base_u16[index][degenerate]
            alpha_new_u16[unchanged] = base_u16[index][unchanged]
            alpha_new_u16[q_zero] = 0
            alpha_new_u16[core_block] = 0
            alpha_new_q = alpha_new_u16.astype(np.float64) / 65535.0
            actual_coefficient = survival_new * alpha_new_q
            layer_key = str(layer_ids[index])
            max_coefficient_error[layer_key] = max(
                max_coefficient_error[layer_key],
                float(
                    np.max(
                        np.abs(actual_coefficient - target_coefficient), initial=0.0
                    )
                ),
            )
            outside_changes[layer_key] += int(
                np.count_nonzero(
                    alpha_new_u16[unchanged] != base_u16[index][unchanged]
                )
            )
            core_nonzero[layer_key] += int(
                np.count_nonzero(alpha_new_u16[core_block])
            )
            survival_base *= 1.0 - base_alpha[index]
            survival_new *= 1.0 - alpha_new_q
            new_u16[index] = alpha_new_u16
            del target_coefficient, alpha_new, alpha_new_q, actual_coefficient, degenerate

        target_lower = 1.0 - q * (1.0 - survival_base)
        max_lower_coefficient_error = max(
            max_lower_coefficient_error,
            float(np.max(np.abs(survival_new - target_lower), initial=0.0)),
        )
        for index, output in enumerate(outputs):
            if new_u16[index] is None:
                raise AssertionError("transformació conjunta incompleta")
            output[y0:y1] = new_u16[index]
        del (
            base_u16,
            base_alpha,
            q_u16,
            q,
            unchanged,
            q_zero,
            survival_base,
            survival_new,
            new_u16,
            target_lower,
        )

    for output in outputs:
        output.flush()
    del outputs, bases
    if any(outside_changes.values()) or any(core_nonzero.values()):
        raise AssertionError(
            f"protecció conjunta {gate_name} no exacta: "
            f"fora={outside_changes}, core={core_nonzero}"
        )
    return {
        "gate": gate_name,
        "formula": "top-down Normal coefficient preservation T_q",
        "layers_bottom_to_top": layer_ids,
        "quantization": "u16 bases, q and each upper alpha before lower denominator",
        "gate_u16_authority": gate_u16_authority is not None,
        "outside_gate_changed_values": outside_changes,
        "core_nonzero_pixels": core_nonzero,
        "max_source_coefficient_error": max_coefficient_error,
        "max_lower_coefficient_error": max_lower_coefficient_error,
    }


def freeze_lower_reference4(
    layers_by_id: dict[int, object],
    header,
    mask4_frame_path: Path,
    output_path: Path,
) -> dict:
    """Materialitza el compost immutable ID3→ID4 abans de construir P4."""
    alpha4 = np.load(mask4_frame_path, mmap_mode="r").astype(np.float32)
    alpha4 *= 1.0 / 65535.0
    frozen = np.lib.format.open_memmap(
        output_path, mode="w+", dtype=np.uint16, shape=(FRAME_H, FRAME_W, 3)
    )
    channel_hashes = []
    channel_sums = []
    for channel_index, channel_id in enumerate(
        (ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2)
    ):
        source3 = layer_rect_u16(layers_by_id[3], channel_id, header).astype(np.float32)
        source4 = layer_rect_u16(layers_by_id[4], channel_id, header).astype(np.float32)
        source3 *= 1.0 / 65535.0
        source4 *= 1.0 / 65535.0
        lower = source3 + (source4 - source3) * alpha4
        lower_u16 = np.clip(np.rint(lower * 65535.0), 0, 65535).astype(np.uint16)
        frozen[..., channel_index] = lower_u16
        channel_sums.append(int(lower_u16.astype(np.uint64).sum()))
        channel_hashes.append(
            hashlib.sha256(np.ascontiguousarray(lower_u16).astype(">u2").tobytes()).hexdigest()
        )
        del source3, source4, lower, lower_u16
    frozen.flush()
    del frozen, alpha4
    return {
        "path": str(output_path),
        "sha256_npy": sha256_file(output_path),
        "channel_sha256_be_u16": channel_hashes,
        "channel_sums_u16": channel_sums,
    }


def replace_mask16(layer, mask16: np.ndarray, header) -> None:
    md = layer._record.mask_data
    if md is None:
        raise AssertionError(f"layer_id={layer.layer_id} sense màscara per substituir")
    height, width = mask16.shape
    if (width, height) != (WIDTH, HEIGHT):
        raise AssertionError("la màscara superior ha de cobrir exactament el llenç")
    md.top = 0
    md.left = 0
    md.bottom = HEIGHT
    md.right = WIDTH
    md.background_color = 0
    md.flags = MaskFlags()
    for ci, cd in zip(layer._record.channel_info, layer._channels):
        if ci.id == ChannelID.USER_LAYER_MASK:
            cd.compression = Compression.ZIP_WITH_PREDICTION
            cd.set_data(np.ascontiguousarray(mask16).astype(">u2").tobytes(), WIDTH, HEIGHT, 16, header.version)
            ci.length = len(cd.data) + 2
            if hasattr(layer, "_mask"):
                del layer._mask
            layer._psd._mark_updated()
            return
    raise AssertionError(f"falta canal de màscara a layer_id={layer.layer_id}")


def compose_merged(layers, header, mask_paths: dict[int, Path], merged_path: Path, start: float) -> np.memmap:
    merged = np.lib.format.open_memmap(
        merged_path, mode="w+", dtype=np.uint16, shape=(HEIGHT, WIDTH, 3)
    )
    merged[:] = 0
    mask_views = {}
    for layer in layers:
        mask = np.load(mask_paths[layer.layer_id], mmap_mode="r")
        if layer.layer_id == 3:
            mask_views[layer.layer_id] = mask
        else:
            mask_views[layer.layer_id] = mask[FRAME[1] : FRAME[3], FRAME[0] : FRAME[2]]

    for channel_index, channel_id in enumerate(
        (ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2)
    ):
        composite = np.zeros((FRAME_H, FRAME_W), dtype=np.float32)
        for layer in layers:
            alpha_u16 = layer_rect_u16(layer, ChannelID.TRANSPARENCY_MASK, header)
            if not np.all(alpha_u16 == 65535):
                raise AssertionError(f"alpha font no opaca dins frame: layer_id={layer.layer_id}")
            del alpha_u16
            alpha = np.asarray(mask_views[layer.layer_id], dtype=np.float32) * (1.0 / 65535.0)
            source = layer_rect_u16(layer, channel_id, header).astype(np.float32)
            source *= 1.0 / 65535.0
            composite += (source - composite) * alpha
            del alpha, source
        merged[FRAME[1] : FRAME[3], FRAME[0] : FRAME[2], channel_index] = np.clip(
            np.rint(composite * 65535.0), 0, 65535
        ).astype(np.uint16)
        del composite
        log(start, f"merged canal {channel_index + 1}/3")
    merged.flush()
    return merged


def merged_hashes(merged: np.ndarray) -> list[str]:
    result = []
    for channel in range(3):
        raw = np.ascontiguousarray(merged[..., channel]).astype(">u2").tobytes()
        result.append(hashlib.sha256(raw).hexdigest())
    return result


def transition_qa(merged: np.ndarray) -> dict:
    """Rebutja un fossat radial nou a la unió HDR de l'1/60.

    La mitjana azimutal es mesura al voltant del limbe propi de la capa 1/60
    i se suavitza 3 px, igual que a l'auditoria que va detectar el mínim fals
    a r=499 px de la primera passada.
    """
    cx, cy, _radius = MOON[7]
    pad = 650
    left = int(np.floor(cx - pad))
    right = int(np.ceil(cx + pad)) + 1
    top = int(np.floor(cy - pad))
    bottom = int(np.ceil(cy + pad)) + 1
    crop = np.asarray(merged[top:bottom, left:right], dtype=np.float32)
    luminance = (crop[..., 0] + crop[..., 1] + crop[..., 2]) / 3.0
    yy = np.arange(top, bottom, dtype=np.float32)[:, None]
    xx = np.arange(left, right, dtype=np.float32)[None, :]
    distance = np.hypot(xx - cx, yy - cy)
    selected = (distance >= 440.0) & (distance < 621.0)
    annulus = np.floor(distance[selected]).astype(np.int32)
    values = luminance[selected]
    sums = np.bincount(annulus, weights=values, minlength=621)
    counts = np.bincount(annulus, minlength=621)
    radial = sums / np.maximum(counts, 1)
    smooth = ndi.gaussian_filter1d(radial, 3.0, mode="nearest")
    minima = [
        radius
        for radius in range(452, 620)
        if smooth[radius] <= smooth[radius - 1] and smooth[radius] < smooth[radius + 1]
    ]
    if minima:
        raise AssertionError(f"mínim radial nou entre 452–620 px: {minima}")
    return {
        "local_minima_452_620": minima,
        "mean_u16": {
            str(radius): float(smooth[radius])
            for radius in (452, 464, 470, 480, 500, 520, 540, 620)
        },
    }


def _bright_components(
    mask: np.ndarray,
    left: int,
    top: int,
    *,
    connectivity8: bool = False,
) -> list[dict]:
    structure = np.ones((3, 3), dtype=np.uint8) if connectivity8 else None
    labels, count = ndi.label(mask, structure=structure)
    components = []
    for label in range(1, count + 1):
        selected = labels == label
        area = int(np.count_nonzero(selected))
        if area < 2:
            continue
        ys, xs = np.nonzero(selected)
        components.append(
            {
                "area_px": area,
                "bbox_document": [
                    int(xs.min() + left),
                    int(ys.min() + top),
                    int(xs.max() + left + 1),
                    int(ys.max() + top + 1),
                ],
            }
        )
    return sorted(components, key=lambda component: (-component["area_px"], component["bbox_document"]))


def protected_contact_qa(
    merged: np.ndarray,
    protected_layer,
    header,
    core: np.ndarray,
    mask_paths: dict[int, Path],
    support_stats: dict,
) -> dict:
    """Gate dur: cap capa superior pot alterar el nucli temporal protegit."""
    source = np.stack(
        [
            layer_rect_u16(protected_layer, channel_id, header)
            for channel_id in (ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2)
        ],
        axis=-1,
    )
    final = np.asarray(merged[FRAME[1] : FRAME[3], FRAME[0] : FRAME[2]], dtype=np.uint16)
    difference = np.abs(final.astype(np.int32) - source.astype(np.int32))
    mismatch_values = difference[core]
    mismatch_count = int(np.count_nonzero(mismatch_values))
    max_abs = int(mismatch_values.max(initial=0))
    if mismatch_count or max_abs:
        raise AssertionError(
            f"s'ha alterat la font protegida dins el nucli: "
            f"valors_diferents={mismatch_count}, max_abs={max_abs}"
        )

    threshold = int(np.ceil(PROTECTED_BEAD_MIN_RGB * 65535.0))
    source_bright = core & (np.min(source, axis=2) >= threshold)
    final_bright = core & (np.min(final, axis=2) >= threshold)
    source_components = _bright_components(source_bright, FRAME[0], FRAME[1])
    final_components = _bright_components(final_bright, FRAME[0], FRAME[1])
    if (
        len(source_components) != EXPECTED_BEAD_COMPONENTS
        or int(np.count_nonzero(source_bright)) != EXPECTED_BEAD_PIXELS
    ):
        raise AssertionError(
            "morfologia protegida de la font inesperada: "
            f"components={len(source_components)}, pixels={np.count_nonzero(source_bright)}"
        )
    if not np.array_equal(source_bright, final_bright) or source_components != final_components:
        raise AssertionError("ha desaparegut o canviat una perla/diamant al compost final")

    upper_masks = {}
    for layer_id in (4, 5, 7):
        mask = np.load(mask_paths[layer_id], mmap_mode="r")[
            FRAME[1] : FRAME[3], FRAME[0] : FRAME[2]
        ]
        nonzero = int(np.count_nonzero(mask[core]))
        upper_masks[str(layer_id)] = {
            "nonzero_core_pixels": nonzero,
            "max_core_u16": int(mask[core].max(initial=0)),
        }
        if nonzero:
            raise AssertionError(f"layer_id={layer_id} encara contribueix dins el nucli protegit")

    source_core = source[core].astype(np.uint64)
    final_core = final[core].astype(np.uint64)
    support_stats = dict(support_stats)
    support_stats["core_sha256"] = hashlib.sha256(np.ascontiguousarray(core).tobytes()).hexdigest()
    return {
        "status": "PASS",
        "source_layer_id": protected_layer.layer_id,
        "support": support_stats,
        "upper_layer_effective_masks": upper_masks,
        "core_exactness": {
            "different_channel_values": mismatch_count,
            "max_abs_u16": max_abs,
            "source_sum_rgb_u16": [int(value) for value in source_core.sum(axis=0)],
            "final_sum_rgb_u16": [int(value) for value in final_core.sum(axis=0)],
        },
        "baily_diamond_gate": {
            "min_rgb_threshold": PROTECTED_BEAD_MIN_RGB,
            "source_pixels": int(np.count_nonzero(source_bright)),
            "final_pixels": int(np.count_nonzero(final_bright)),
            "source_components": source_components,
            "final_components": final_components,
        },
    }


def protected_prominence_qa(
    merged: np.ndarray,
    layers_by_id: dict[int, object],
    header,
    core: np.ndarray,
    strong_core: np.ndarray,
    allowed_kept: np.ndarray,
    photo_gate: np.ndarray,
    photo_domain: np.ndarray,
    radial_gate: np.ndarray,
    mask_paths: dict[int, Path],
    base_upper_mask_paths: dict[int, Path],
    protection_gate: np.ndarray,
    protection_gate_u16: np.ndarray,
    frozen_lower_path: Path,
    support_stats: dict,
) -> dict:
    """Gate dur jeràrquic per a limbe/cromosfera/protuberàncies de l'1/500."""
    expected_shape = (FRAME_H, FRAME_W)
    for name, value in (
        ("core", core),
        ("strong", strong_core),
        ("allowed", allowed_kept),
        ("photo", photo_gate),
        ("photo_domain", photo_domain),
        ("radial", radial_gate),
        ("combined", protection_gate),
        ("combined_u16", protection_gate_u16),
    ):
        if value.shape != expected_shape:
            raise AssertionError(f"geometria inesperada al gate {name}")
    if np.any(strong_core & ~allowed_kept):
        raise AssertionError("un nucli Halpha fort ha sortit del senyal allowed")
    if np.any((photo_gate > 0.0) & ~photo_domain):
        raise AssertionError("la ploma harmònica ha sortit del domini declarat")
    if not np.all(photo_gate[strong_core] == 1.0):
        raise AssertionError("el nucli Halpha fort no queda congelat")
    expected_combined_u16 = np.maximum(
        quantize_half_up_u16(radial_gate), quantize_half_up_u16(photo_gate)
    )
    expected_combined_u16[core] = 65535
    if not np.array_equal(protection_gate_u16, expected_combined_u16):
        raise AssertionError("P4 u16 no és el màxim canònic radial+H40")
    expected_combined = expected_combined_u16.astype(np.float32) * (1.0 / 65535.0)
    if not np.array_equal(protection_gate, expected_combined):
        raise AssertionError("la vista float de P4 no correspon a l'autoritat u16")
    del expected_combined, expected_combined_u16

    alpha4 = np.load(mask_paths[4], mmap_mode="r")[
        FRAME[1] : FRAME[3], FRAME[0] : FRAME[2]
    ].astype(np.float32)
    alpha4 *= 1.0 / 65535.0
    alpha5_base = np.load(base_upper_mask_paths[5], mmap_mode="r").astype(np.float32)
    alpha7_base = np.load(base_upper_mask_paths[7], mmap_mode="r").astype(np.float32)
    alpha5_base *= 1.0 / 65535.0
    alpha7_base *= 1.0 / 65535.0
    q_u16 = np.uint16(65535) - protection_gate_u16
    q = q_u16.astype(np.float32) * (1.0 / 65535.0)
    frozen_lower = np.load(frozen_lower_path, mmap_mode="r")
    if frozen_lower.shape != (FRAME_H, FRAME_W, 3) or frozen_lower.dtype != np.uint16:
        raise AssertionError("referència ID3→ID4 congelada inesperada")
    final = np.asarray(merged[FRAME[1] : FRAME[3], FRAME[0] : FRAME[2]], dtype=np.uint16)
    mismatch_count = 0
    max_abs = 0
    ideal_different_values = 0
    ideal_max_abs = 0
    outside_gate_different_values = 0
    outside_gate_max_abs = 0
    lower_sums = []
    final_sums = []
    lower_channels = []
    support = protection_gate_u16 > 0
    effective_support = q_u16 < 65535
    outside = ~support
    for channel_index, channel_id in enumerate(
        (ChannelID.CHANNEL_0, ChannelID.CHANNEL_1, ChannelID.CHANNEL_2)
    ):
        source3 = layer_rect_u16(layers_by_id[3], channel_id, header).astype(np.float32)
        source4 = layer_rect_u16(layers_by_id[4], channel_id, header).astype(np.float32)
        source3 *= 1.0 / 65535.0
        source4 *= 1.0 / 65535.0
        lower = source3 + (source4 - source3) * alpha4
        lower_u16 = np.clip(np.rint(lower * 65535.0), 0, 65535).astype(np.uint16)
        if not np.array_equal(lower_u16, frozen_lower[..., channel_index]):
            raise AssertionError("ha canviat la referència ID3→ID4 després de congelar-la")
        difference = np.abs(
            final[..., channel_index].astype(np.int32) - lower_u16.astype(np.int32)
        )
        selected = difference[core]
        mismatch_count += int(np.count_nonzero(selected))
        max_abs = max(max_abs, int(selected.max(initial=0)))
        lower_sums.append(int(lower_u16[core].astype(np.uint64).sum()))
        final_sums.append(int(final[..., channel_index][core].astype(np.uint64).sum()))

        source5 = layer_rect_u16(layers_by_id[5], channel_id, header).astype(np.float32)
        source7 = layer_rect_u16(layers_by_id[7], channel_id, header).astype(np.float32)
        source5 *= 1.0 / 65535.0
        source7 *= 1.0 / 65535.0
        upper_base = lower + (source5 - lower) * alpha5_base
        upper_base += (source7 - upper_base) * alpha7_base
        ideal = lower + (upper_base - lower) * q
        ideal_u16 = np.clip(np.rint(ideal * 65535.0), 0, 65535).astype(np.uint16)
        ideal_difference = np.abs(
            final[..., channel_index].astype(np.int32) - ideal_u16.astype(np.int32)
        )
        ideal_different_values += int(np.count_nonzero(ideal_difference[support]))
        ideal_max_abs = max(
            ideal_max_abs, int(ideal_difference[support].max(initial=0))
        )
        upper_base_u16 = np.clip(
            np.rint(upper_base * 65535.0), 0, 65535
        ).astype(np.uint16)
        outside_difference = np.abs(
            final[..., channel_index].astype(np.int32)
            - upper_base_u16.astype(np.int32)
        )
        outside_gate_different_values += int(
            np.count_nonzero(outside_difference[outside])
        )
        outside_gate_max_abs = max(
            outside_gate_max_abs, int(outside_difference[outside].max(initial=0))
        )
        lower_channels.append(lower_u16)
        del (
            source3,
            source4,
            source5,
            source7,
            lower,
            difference,
            selected,
            upper_base,
            ideal,
            ideal_u16,
            ideal_difference,
            upper_base_u16,
            outside_difference,
        )
    del alpha4, alpha5_base, alpha7_base, q, q_u16, frozen_lower
    if mismatch_count or max_abs:
        raise AssertionError(
            "s'ha alterat la referència acumulada 1/3200+1/500 dins "
            f"limbe/protuberàncies: diferents={mismatch_count}, max_abs={max_abs}"
        )
    if ideal_max_abs > 1:
        raise AssertionError(
            "la ploma conjunta no reprodueix la interpolació ideal: "
            f"diferents={ideal_different_values}, max_abs={ideal_max_abs}"
        )
    if outside_gate_different_values or outside_gate_max_abs:
        raise AssertionError(
            "la protecció ID4 ha alterat píxels fora del seu suport: "
            f"diferents={outside_gate_different_values}, max_abs={outside_gate_max_abs}"
        )

    # G5/G6: el gate no pot convertir la incompatibilitat entre els dos
    # compostos en un ribet propi. Es mesura sobre el render gamma a 100 %.
    lower_float, upper_float = compose_p3_upper_reference(
        layers_by_id,
        header,
        frozen_lower_path,
        base_upper_mask_paths[5],
        base_upper_mask_paths[7],
    )
    final_float = final.astype(np.float32)
    final_float *= 1.0 / 65535.0

    def _luminance8(rgb: np.ndarray) -> np.ndarray:
        shown = np.power(np.clip(rgb, 0.0, 1.0), 1.0 / 2.2) * 255.0
        return (
            shown[..., 0] * 0.2126
            + shown[..., 1] * 0.7152
            + shown[..., 2] * 0.0722
        ).astype(np.float32)

    def _gradient(value: np.ndarray) -> np.ndarray:
        gy, gx = np.gradient(value)
        return np.hypot(gx, gy).astype(np.float32)

    lower_luma = _luminance8(lower_float)
    upper_luma = _luminance8(upper_float)
    final_luma = _luminance8(final_float)
    lower_gradient = _gradient(lower_luma)
    upper_gradient = _gradient(upper_luma)
    final_gradient = _gradient(final_luma)
    gate_gradient = _gradient(protection_gate)
    radial_u16 = quantize_half_up_u16(radial_gate)
    partial = (
        (protection_gate_u16 > 0)
        & (protection_gate_u16 < 65535)
        & (radial_u16 == 0)
    )
    parent_gradient = np.maximum(lower_gradient, upper_gradient)
    gradient_excess = final_gradient - parent_gradient
    gate_correlation = float(
        np.corrcoef(final_gradient[partial], gate_gradient[partial])[0, 1]
    )
    mask_term = np.abs(lower_luma - upper_luma) * gate_gradient
    physical_term = (
        protection_gate * lower_gradient
        + (1.0 - protection_gate) * upper_gradient
    )
    imprint_metrics = {
        "partial_pixels_outside_radial": int(np.count_nonzero(partial)),
        "final_gradient_median": float(np.median(final_gradient[partial])),
        "parent_gradient_median": float(np.median(parent_gradient[partial])),
        "gradient_excess_gt_2_pixels": int(
            np.count_nonzero(gradient_excess[partial] > 2.0)
        ),
        "gradient_gate_correlation": gate_correlation,
        "mask_term_dominant_pixels": int(
            np.count_nonzero(mask_term[partial] > physical_term[partial])
        ),
        "limits": {
            "final_gradient_median_le_parent": True,
            "gradient_excess_gt_2_pixels_max": 100,
            "gradient_gate_correlation_max": 0.40,
        },
    }
    if (
        imprint_metrics["final_gradient_median"]
        > imprint_metrics["parent_gradient_median"]
        or imprint_metrics["gradient_excess_gt_2_pixels"] > 100
        or imprint_metrics["gradient_gate_correlation"] > 0.40
    ):
        raise AssertionError(f"la ploma H40 imprimeix un contorn: {imprint_metrics}")
    del (
        lower_float,
        upper_float,
        final_float,
        lower_luma,
        upper_luma,
        final_luma,
        lower_gradient,
        upper_gradient,
        final_gradient,
        gate_gradient,
        radial_u16,
        partial,
        parent_gradient,
        gradient_excess,
        mask_term,
        physical_term,
    )

    # G10 fail-closed: la pròpia ID4 i totes les capes que hi ha per damunt
    # han de donar alfa literalment zero dins el disc canònic de la font ID4.
    local_y = np.arange(FRAME[1], FRAME[3], dtype=np.float32)[:, None]
    local_x = np.arange(FRAME[0], FRAME[2], dtype=np.float32)[None, :]
    cx4, cy4, radius4 = MOON[PROTECTED_PROM_SOURCE_LAYER_ID]
    disc4 = np.hypot(local_x - cx4, local_y - cy4) <= radius4
    alpha4_u16 = np.load(mask_paths[4], mmap_mode="r")[
        FRAME[1] : FRAME[3], FRAME[0] : FRAME[2]
    ]
    disc_stats = {
        "4": {
            "nonzero_pixels": int(np.count_nonzero(alpha4_u16[disc4])),
            "max_u16": int(alpha4_u16[disc4].max(initial=0)),
        }
    }
    if disc_stats["4"]["nonzero_pixels"] or disc_stats["4"]["max_u16"]:
        raise AssertionError("la font ID4 encara contribueix dins el seu disc lunar")

    upper_masks = {}
    for layer_id in (5, 7):
        mask = np.load(mask_paths[layer_id], mmap_mode="r")[
            FRAME[1] : FRAME[3], FRAME[0] : FRAME[2]
        ]
        nonzero = int(np.count_nonzero(mask[core]))
        upper_masks[str(layer_id)] = {
            "nonzero_core_pixels": nonzero,
            "max_core_u16": int(mask[core].max(initial=0)),
        }
        if nonzero:
            raise AssertionError(
                f"layer_id={layer_id} contribueix al nucli 1/500 de limbe/protuberàncies"
            )
        disc_stats[str(layer_id)] = {
            "nonzero_pixels": int(np.count_nonzero(mask[disc4])),
            "max_u16": int(mask[disc4].max(initial=0)),
        }
        if (
            disc_stats[str(layer_id)]["nonzero_pixels"]
            or disc_stats[str(layer_id)]["max_u16"]
        ):
            raise AssertionError(
                f"layer_id={layer_id} encara contribueix dins el disc canònic ID4"
            )

    components = _bright_components(
        allowed_kept, FRAME[0], FRAME[1], connectivity8=True
    )
    expected_components = [
        {"area_px": area, "bbox_document": list(bbox)}
        for area, bbox in EXPECTED_PROM_COMPONENTS_DESCRIPTOR
    ]
    if components != expected_components:
        raise AssertionError(
            "components protegits 1/500 inesperats: "
            f"components={components}"
        )

    lower_stack = np.stack(lower_channels, axis=-1)
    del lower_channels
    labels, label_count = ndi.label(
        allowed_kept, structure=np.ones((3, 3), dtype=np.uint8)
    )
    component_photometry = []
    for label_id in range(1, label_count + 1):
        selected_allowed = labels == label_id
        allowed_area = int(np.count_nonzero(selected_allowed))
        if allowed_area < 2:
            continue
        selected_strong = selected_allowed & strong_core
        strong_area = int(np.count_nonzero(selected_strong))
        if strong_area < PROTECTED_PROM_MIN_SEED_PIXELS:
            raise AssertionError("un grup Halpha retingut no conserva prou llavor forta")
        allowed_y, allowed_x = np.nonzero(selected_allowed)
        ys, xs = np.nonzero(selected_strong)
        lower_values = lower_stack[selected_strong].astype(np.uint64)
        final_values = final[selected_strong].astype(np.uint64)
        if not np.array_equal(lower_values, final_values):
            raise AssertionError("fotometria del nucli fort d'una protuberància no és exacta")
        weights = lower_values.sum(axis=1).astype(np.float64)
        weight_sum = float(weights.sum())
        centroid = [
            float(np.dot(xs.astype(np.float64) + FRAME[0], weights) / weight_sum),
            float(np.dot(ys.astype(np.float64) + FRAME[1], weights) / weight_sum),
        ]
        component_photometry.append(
            {
                "allowed_area_px": allowed_area,
                "allowed_bbox_document": [
                    int(allowed_x.min() + FRAME[0]),
                    int(allowed_y.min() + FRAME[1]),
                    int(allowed_x.max() + FRAME[0] + 1),
                    int(allowed_y.max() + FRAME[1] + 1),
                ],
                "strong_area_px": strong_area,
                "strong_bbox_document": [
                    int(xs.min() + FRAME[0]),
                    int(ys.min() + FRAME[1]),
                    int(xs.max() + FRAME[0] + 1),
                    int(ys.max() + FRAME[1] + 1),
                ],
                "centroid_flux_document": centroid,
                "sum_rgb_u16": [int(value) for value in lower_values.sum(axis=0)],
                "peak_rgb_u16": [int(value) for value in lower_values.max(axis=0)],
                "integrated_flux_rgb_u16": int(lower_values.sum()),
                "reference_final_exact": True,
            }
        )
        del (
            selected_allowed,
            selected_strong,
            allowed_y,
            allowed_x,
            ys,
            xs,
            lower_values,
            final_values,
            weights,
        )
    del labels, lower_stack
    component_photometry = sorted(
        component_photometry,
        key=lambda item: (-item["allowed_area_px"], item["allowed_bbox_document"]),
    )
    actual_strong_descriptors = tuple(
        (
            item["strong_area_px"],
            tuple(item["strong_bbox_document"]),
        )
        for item in component_photometry
    )
    if actual_strong_descriptors != EXPECTED_STRONG_PROM_COMPONENTS_DESCRIPTOR:
        raise AssertionError(
            "els sis nuclis forts Halpha han canviat: "
            f"actual={actual_strong_descriptors}"
        )

    photo_outside_allowed = int(np.count_nonzero((photo_gate > 0.0) & ~allowed_kept))
    photo_outside_domain = int(np.count_nonzero((photo_gate > 0.0) & ~photo_domain))
    effective_photo = quantize_half_up_u16(photo_gate)
    support_stats = dict(support_stats)
    support_stats["union_core_sha256"] = hashlib.sha256(
        np.ascontiguousarray(core).tobytes()
    ).hexdigest()
    support_stats["strong_core_sha256"] = hashlib.sha256(
        np.ascontiguousarray(strong_core).tobytes()
    ).hexdigest()
    support_stats["allowed_sha256"] = hashlib.sha256(
        np.ascontiguousarray(allowed_kept).tobytes()
    ).hexdigest()
    support_stats["photometric_gate_sha256"] = hashlib.sha256(
        np.ascontiguousarray(photo_gate).tobytes()
    ).hexdigest()
    support_stats["radial_gate_sha256"] = hashlib.sha256(
        np.ascontiguousarray(radial_gate).tobytes()
    ).hexdigest()
    support_stats["gate_u16_sha256"] = hashlib.sha256(
        np.ascontiguousarray(protection_gate_u16).tobytes()
    ).hexdigest()
    return {
        "status": "PASS",
        "source_layer_id": PROTECTED_PROM_SOURCE_LAYER_ID,
        "support": support_stats,
        "components": components,
        "component_photometry": component_photometry,
        "upper_layer_effective_masks": upper_masks,
        "canonical_id4_disc": disc_stats,
        "gate_provenance": {
            "photometric_gate_outside_allowed_pixels": photo_outside_allowed,
            "photometric_gate_outside_declared_domain_pixels": photo_outside_domain,
            "photometric_gate_float_nonzero_pixels": int(
                np.count_nonzero(photo_gate)
            ),
            "photometric_gate_effective_u16_pixels": int(
                np.count_nonzero(effective_photo)
            ),
            "combined_gate_float_nonzero_pixels": int(
                np.count_nonzero(protection_gate)
            ),
            "combined_gate_effective_u16_pixels": int(
                np.count_nonzero(effective_support)
            ),
            "formula": "max(radial fail-closed, H40 weighted harmonic compatibility plume)",
            "scientific_support": "allowed Halpha only; H40 is a declared blend zone",
        },
        "mask_imprint_qa": imprint_metrics,
        "core_exactness": {
            "different_channel_values": mismatch_count,
            "max_abs_u16": max_abs,
            "allowed_u16": 0,
            "lower_composite_sum_rgb_u16": lower_sums,
            "final_sum_rgb_u16": final_sums,
        },
        "joint_feather_interpolation": {
            "different_channel_values": ideal_different_values,
            "max_abs_u16": ideal_max_abs,
            "allowed_quantization_u16": 1,
            "outside_gate_different_channel_values": outside_gate_different_values,
            "outside_gate_max_abs_u16": outside_gate_max_abs,
            "base_mask_sha256": {
                str(layer_id): sha256_file(path)
                for layer_id, path in base_upper_mask_paths.items()
            },
            "frozen_lower_npy_sha256": sha256_file(frozen_lower_path),
        },
    }


def validate_source(psd: PSDImage, source: Path) -> tuple[dict[int, object], dict[int, dict[str, str]]]:
    header = psd._record.header
    if source.stat().st_size != SOURCE_SIZE:
        raise AssertionError("ha canviat la mida de Corretgint.psb")
    if (header.version, header.depth, header.channels, psd.width, psd.height) != (2, 16, 4, WIDTH, HEIGHT):
        raise AssertionError("capçalera font inesperada")
    layers = list(psd)
    if len(layers) != len(EXPECTED_LAYERS):
        raise AssertionError(f"s'esperaven 5 capes i n'hi ha {len(layers)}")
    by_id = {layer.layer_id: layer for layer in layers}
    for layer, (expected_id, expected_name, expected_bbox) in zip(layers, EXPECTED_LAYERS):
        if (layer.layer_id, layer.name, tuple(layer.bbox)) != (expected_id, expected_name, expected_bbox):
            raise AssertionError(
                f"capa font inesperada: {(layer.layer_id, layer.name, tuple(layer.bbox))!r}"
            )
        if not layer.visible or layer.blend_mode != BlendMode.NORMAL or layer.opacity != 255 or layer.fill_opacity != 255:
            raise AssertionError(f"estat de capa no canònic a layer_id={layer.layer_id}")
    hashes = {layer.layer_id: source_channel_hashes(layer, header) for layer in layers}
    if hashes[6] != hashes[7]:
        raise AssertionError("les dues còpies d'1/60 ja no són el mateix raster")
    return by_id, hashes


def validate_output(
    output: Path,
    source_hashes: dict[int, dict[str, str]],
    mask_paths: dict[int, Path],
    expected_merged_hashes: list[str],
) -> dict:
    psd = PSDImage.open(output)
    header = psd._record.header
    if (header.version, header.depth, header.channels, psd.width, psd.height) != (2, 16, 3, WIDTH, HEIGHT):
        raise AssertionError("capçalera final incorrecta")
    lm = psd._record.layer_and_mask_information
    if lm.tagged_blocks is None or Tag.LAYER_16 not in lm.tagged_blocks:
        raise AssertionError("falta Lr16 al PSB final")
    if Tag.SAVING_MERGED_TRANSPARENCY16 in lm.tagged_blocks:
        raise AssertionError("Mt16 antic encara és present")
    layers = list(psd)
    if [layer.layer_id for layer in layers] != [3, 4, 5, 7]:
        raise AssertionError(f"ordre/IDs finals incorrectes: {[layer.layer_id for layer in layers]}")
    seen_rgb = set()
    mask_stats = {}
    for layer in layers:
        if layer.name != FINAL_NAMES[layer.layer_id]:
            raise AssertionError(f"nom final incorrecte a layer_id={layer.layer_id}")
        if not layer.visible or layer.blend_mode != BlendMode.NORMAL or layer.opacity != 255 or layer.fill_opacity != 255:
            raise AssertionError(f"estat final incorrecte a layer_id={layer.layer_id}")
        if source_channel_hashes(layer, header) != source_hashes[layer.layer_id]:
            raise AssertionError(f"s'han alterat píxels font a layer_id={layer.layer_id}")
        rgb_key = tuple(source_hashes[layer.layer_id][str(index)] for index in (0, 1, 2))
        if rgb_key in seen_rgb:
            raise AssertionError("queda un raster RGB duplicat")
        seen_rgb.add(rgb_key)
        md = layer._record.mask_data
        channels = channel_map(layer)
        if md is None or ChannelID.USER_LAYER_MASK not in channels:
            raise AssertionError(f"falta màscara final a layer_id={layer.layer_id}")
        if md.background_color != 0 or layer.mask.disabled:
            raise AssertionError(f"màscara no canònica a layer_id={layer.layer_id}")
        mw = md.right - md.left
        mh = md.bottom - md.top
        raw = channels[ChannelID.USER_LAYER_MASK][1].get_data(mw, mh, 16, 2)
        if len(raw) != mw * mh * 2:
            raise AssertionError(f"màscara no 16-bit a layer_id={layer.layer_id}")
        actual = np.frombuffer(raw, dtype=">u2").reshape(mh, mw)
        expected = np.load(mask_paths[layer.layer_id], mmap_mode="r")
        if actual.shape != expected.shape or not np.array_equal(actual, expected):
            raise AssertionError(f"màscara round-trip diferent a layer_id={layer.layer_id}")
        if layer.layer_id != 3:
            outside_nonzero = (
                np.count_nonzero(actual[: FRAME[1]])
                + np.count_nonzero(actual[FRAME[3] :])
                + np.count_nonzero(actual[FRAME[1] : FRAME[3], : FRAME[0]])
                + np.count_nonzero(actual[FRAME[1] : FRAME[3], FRAME[2] :])
            )
            if outside_nonzero:
                raise AssertionError(f"màscara no negra fora frame a layer_id={layer.layer_id}")
        if layer.layer_id in (4, 5):
            if np.any(actual[FRAME[1], FRAME[0] : FRAME[2]]) or np.any(
                actual[FRAME[1] : FRAME[3], FRAME[0]]
            ):
                raise AssertionError(f"vora blanca invàlida encara oberta a layer_id={layer.layer_id}")
        lunar_disc = {"nonzero_pixels": None, "max_u16": None}
        if layer.layer_id in (4, 5, 7):
            cx, cy, radius = MOON[layer.layer_id]
            x0 = max(0, int(np.floor(cx - radius - 1.0)))
            x1 = min(WIDTH, int(np.ceil(cx + radius + 1.0)) + 1)
            y0 = max(0, int(np.floor(cy - radius - 1.0)))
            y1 = min(HEIGHT, int(np.ceil(cy + radius + 1.0)) + 1)
            local_y = np.arange(y0, y1, dtype=np.float32)[:, None]
            local_x = np.arange(x0, x1, dtype=np.float32)[None, :]
            inside = np.hypot(local_x - cx, local_y - cy) <= radius
            values = actual[y0:y1, x0:x1][inside]
            lunar_disc = {
                "nonzero_pixels": int(np.count_nonzero(values)),
                "max_u16": int(values.max(initial=0)),
            }
            if lunar_disc["nonzero_pixels"] or lunar_disc["max_u16"]:
                raise AssertionError(
                    f"layer_id={layer.layer_id} contribueix dins el disc lunar: {lunar_disc}"
                )
        mask_stats[str(layer.layer_id)] = {
            "bbox": [md.left, md.top, md.right, md.bottom],
            "min": int(actual.min()),
            "max": int(actual.max()),
            "nonzero": int(np.count_nonzero(actual)),
            "lunar_disc": lunar_disc,
        }
    image_channels = psd._record.image_data.get_data(header, split=True)
    actual_merged_hashes = [hashlib.sha256(channel).hexdigest() for channel in image_channels]
    if actual_merged_hashes != expected_merged_hashes:
        raise AssertionError("la previsualització merged no ha sobreviscut el round-trip")
    return {
        "header": {"version": header.version, "depth": header.depth, "channels": header.channels},
        "layer_ids_bottom_to_top": [layer.layer_id for layer in layers],
        "names": [layer.name for layer in layers],
        "masks": mask_stats,
        "merged_channel_sha256": actual_merged_hashes,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("work", type=Path)
    args = parser.parse_args()
    start = time.monotonic()
    source = args.source.resolve()
    output = args.output.resolve()
    work = args.work.resolve()
    if output.exists():
        raise SystemExit(f"no sobreescric: {output}")
    work.mkdir(parents=True, exist_ok=True)

    source_sha = sha256_file(source)
    if source_sha != SOURCE_SHA256:
        raise AssertionError(f"SHA-256 font inesperat: {source_sha}")
    log(start, "font immutable verificada")

    psd = PSDImage.open(source)
    by_id, source_hashes = validate_source(psd, source)
    header = psd._record.header
    log(start, "estructura i canals font verificats")

    # Les transparències font són opaques dins el marc; tota la selecció efectiva
    # queda així continguda en les màscares noves.
    for layer in by_id.values():
        alpha = layer_rect_u16(layer, ChannelID.TRANSPARENCY_MASK, header)
        if layer.layer_id == 6:
            # La còpia desplaçada no cobreix la primera fila/columna del marc.
            alpha = alpha[1:, 1:]
        if not np.all(alpha == 65535):
            raise AssertionError(f"alpha font no opaca a layer_id={layer.layer_id}")
        del alpha

    yy = np.arange(FRAME[1], FRAME[3], dtype=np.float32)[:, None]
    xx = np.arange(FRAME[0], FRAME[2], dtype=np.float32)[None, :]
    r_sun = np.hypot(xx - SUN[0], yy - SUN[1]).astype(np.float32)
    r_sun *= 1.0 / R_SUN
    bins = np.rint(r_sun / BIN_RSUN).astype(np.int32)
    nbins = int(bins.max()) + 2

    m500_old = mask_rect_float(by_id[4], header, FRAME)
    m125_old = mask_rect_float(by_id[5], header, FRAME)
    m60_can = mask_rect_float(by_id[7], header, FRAME)
    shifted_rect = (FRAME[0] + 1, FRAME[1] + 1, FRAME[2] + 1, FRAME[3] + 1)
    m60_old_to_can = mask_rect_float(by_id[6], header, shifted_rect)
    m60_union = m60_can + m60_old_to_can - m60_can * m60_old_to_can
    del m60_can, m60_old_to_can

    profiles = {
        4: radial_profile(m500_old, bins, nbins),
        5: radial_profile(m125_old, bins, nbins),
        7: radial_profile(m60_union, bins, nbins),
    }
    del m500_old, m125_old, m60_union, bins
    controls = {str(layer_id): profile_controls(profile) for layer_id, profile in profiles.items()}
    for layer_id, expected in EXPECTED_PROFILE_VALUES.items():
        actual = controls[str(layer_id)]
        if max(abs(a - b) for a, b in zip(actual, expected)) > 0.035:
            raise AssertionError(
                f"perfil radial inesperat a layer_id={layer_id}: actual={actual}, esperat≈{expected}"
            )
    log(start, "perfils radialitzats validats", controls)

    min_protected = min_rgb_frame(by_id[PROTECTED_SOURCE_LAYER_ID], header)
    protected_core, protected_gate, protected_support_stats = protected_contact_support(
        min_protected, xx, yy
    )
    del min_protected
    protected_core_path = work / "protected_core_layer_3.npy"
    protected_gate_path = work / "protected_gate_layer_3.npy"
    np.save(protected_core_path, protected_core)
    np.save(protected_gate_path, protected_gate.astype(np.float32))
    protected_support_stats["source_channel_sha256"] = source_hashes[PROTECTED_SOURCE_LAYER_ID]
    log(start, "font temporal protegida congelada", protected_support_stats)

    max500 = max_rgb_frame(by_id[4], header)
    h500 = saturation_gate(max500, r_sun)
    del max500
    max125 = max_rgb_frame(by_id[5], header)
    hot125 = max125 >= 0.85
    h125 = saturation_gate(max125, r_sun)
    del max125
    h_counts = {"500": int(np.count_nonzero(h500 > 0.5)), "125": int(np.count_nonzero(h125 > 0.5))}
    if abs(h_counts["500"] - 2219) > 180 or abs(h_counts["125"] - 4722) > 300:
        raise AssertionError(f"porta de saturació inesperada: {h_counts}")
    log(start, "portes de saturació validades", h_counts)

    mask_paths: dict[int, Path] = {}
    base_path = work / "mask_3_base.npy"
    base = np.lib.format.open_memmap(base_path, mode="w+", dtype=np.uint16, shape=(FRAME_H, FRAME_W))
    base[:] = 65535
    base.flush()
    del base
    mask_paths[3] = base_path

    dist500 = moon_distance(4, xx, yy)
    radius500 = MOON[4][2]
    # Disc lunar fail-closed: zero literal fins al radi mesurat; tota la ploma
    # queda a l'exterior, mai dins l'últim anell de píxels lunars.
    d500 = smootherstep((dist500 - radius500) / OWN_LUNAR_FEATHER_OUTSIDE_PX)
    d500[dist500 <= radius500] = 0.0
    m500 = radial_image(profiles[4], r_sun)
    m500 *= d500
    m500 *= 1.0 - h500
    # Capa 1/2 duen blanc invàlid a la primera fila/columna del marc; la font
    # fotogràfica real comença a (458, 464). La base i l'1/60 sí que són vàlides
    # des de (457, 463).
    m500[0, :] = 0.0
    m500[:, 0] = 0.0
    base500_path = work / "mask_4_500_before_protection3_u16.npy"
    save_frame_mask_u16(base500_path, m500)
    del dist500, d500, m500, h500

    (
        protected_prom_core,
        protected_prom_gate,
        protected_prom_strong_core,
        protected_prom_allowed,
        protected_prom_photo_gate,
        protected_prom_radial_gate,
        protected_prom_stats,
    ) = (
        protected_prominence_support(by_id[PROTECTED_PROM_SOURCE_LAYER_ID], header, xx, yy)
    )
    protected_prom_core_path = work / "protected_core_layer_4.npy"
    protected_prom_gate_path = work / "protected_gate_layer_4.npy"
    protected_prom_strong_path = work / "protected_strong_layer_4.npy"
    protected_prom_allowed_path = work / "protected_allowed_layer_4.npy"
    protected_prom_photo_gate_path = work / "protected_photo_gate_layer_4.npy"
    protected_prom_radial_gate_path = work / "protected_radial_gate_layer_4.npy"
    protected_prom_gate_u16_path = work / "protected_gate_layer_4_u16.npy"
    protected_prom_domain_path = work / "protected_domain_layer_4.npy"
    np.save(protected_prom_core_path, protected_prom_core)
    np.save(protected_prom_strong_path, protected_prom_strong_core)
    np.save(protected_prom_allowed_path, protected_prom_allowed)
    np.save(protected_prom_radial_gate_path, protected_prom_radial_gate.astype(np.float32))
    protected_prom_stats["source_channel_sha256"] = source_hashes[
        PROTECTED_PROM_SOURCE_LAYER_ID
    ]
    log(start, "font 1/500 de limbe/protuberàncies congelada", protected_prom_stats)

    dist125 = moon_distance(5, xx, yy)
    radius125 = MOON[5][2]
    d125 = smootherstep(
        (dist125 - (radius125 + ID5_LUNAR_CORE_OUTSIDE_PX))
        / (ID5_LUNAR_FEATHER_END_OUTSIDE_PX - ID5_LUNAR_CORE_OUTSIDE_PX)
    )
    d125[dist125 <= radius125 + ID5_LUNAR_CORE_OUTSIDE_PX] = 0.0
    m125 = radial_image(profiles[5], r_sun)
    m125 *= d125
    m125 *= 1.0 - h125
    m125[0, :] = 0.0
    m125[:, 0] = 0.0
    base125_path = work / "mask_5_125_before_protection3_u16.npy"
    save_frame_mask_u16(base125_path, m125)
    del dist125, d125, m125

    dist60 = moon_distance(7, xx, yy)
    # La porta ampla 470→540 i l'el·lipse de protuberància eren correctes per
    # a la cadena exterior completa (que contenia VORA), però en aquest PSB de
    # quatre fonts creaven un mínim a r=499 px i una bombolla fosca. Ací la
    # porta queda resolta A LA MÀSCARA: zero fins R_lluna+3, plena a +21.
    gate60 = smootherstep(
        (dist60 - (MOON[7][2] + ID7_LUNAR_CORE_OUTSIDE_PX))
        / ID7_LUNAR_FEATHER_WIDTH_PX
    )
    m60 = radial_image(profiles[7], r_sun)
    m60 *= gate60
    m60 *= 1.0 - h125
    # El H125 feathered protegeix cromosfera/protuberància; els nuclis
    # saturats queden literalment a zero, sense cap empremta el·líptica.
    m60[hot125] = 0.0
    base60_path = work / "mask_7_60_before_protection3_u16.npy"
    save_frame_mask_u16(base60_path, m60)

    # P3 s'aplica a tota la pila superior alhora. Multiplicar cada màscara per
    # (1-P3) canviaria els pesos Normal i podria crear un halo al diamant.
    p3_500_path = work / "mask_4_500_after_protection3_u16.npy"
    p3_125_path = work / "mask_5_125_after_protection3_u16.npy"
    p3_60_path = work / "mask_7_60_after_protection3_u16.npy"
    joint_contact_stats = joint_protect_stack_u16(
        [base500_path, base125_path, base60_path],
        protected_gate,
        protected_core,
        [p3_500_path, p3_125_path, p3_60_path],
        [4, 5, 7],
        "P3_PERLES_DIAMANT",
    )
    path500 = work / "mask_4_500.npy"
    write_full_mask_u16(path500, np.load(p3_500_path, mmap_mode="r"))
    mask_paths[4] = path500
    frozen_lower4_path = work / "frozen_L4_ID3_to_ID4_rgb16.npy"
    frozen_lower4_stats = freeze_lower_reference4(
        by_id, header, p3_500_path, frozen_lower4_path
    )
    log(start, "referència acumulada ID3→ID4 congelada", frozen_lower4_stats)

    # La ploma P4 es decideix només ara, entre els dos compostos reals que ha
    # d'interpolar. El suport científic continua sent l'allowed Hα congelat;
    # H40 és una zona de barreja de compatibilitat i no una dilatació del
    # fenomen. El gate u16 half-up és l'autoritat de totes les alfas posteriors.
    lower_p3, upper_p3 = compose_p3_upper_reference(
        by_id, header, frozen_lower4_path, p3_125_path, p3_60_path
    )
    (
        protected_prom_photo_gate,
        protected_prom_gate,
        protected_prom_gate_u16,
        protected_prom_domain,
        harmonic_stats,
    ) = harmonic_compatibility_gate(
        lower_p3,
        upper_p3,
        protected_prom_allowed,
        protected_prom_strong_core,
        protected_prom_radial_gate,
        protected_prom_core,
    )
    upper_p3_path = work / "upper_O_after_P3_rgb16.npy"
    np.save(upper_p3_path, quantize_half_up_u16(upper_p3))
    np.save(protected_prom_gate_path, protected_prom_gate)
    np.save(protected_prom_gate_u16_path, protected_prom_gate_u16)
    np.save(protected_prom_domain_path, protected_prom_domain)
    np.save(protected_prom_photo_gate_path, protected_prom_photo_gate)
    for stale_key in (
        "prominence_gate",
        "prominence_gate_nonzero_pixels",
        "combined_gate_nonzero_pixels",
        "combined_gate_effective_u16_pixels",
        "effective_plume_outside_core_pixels",
        "photometric_gate_float32_sha256",
        "gate_float32_sha256",
        "q16_sha256",
    ):
        protected_prom_stats.pop(stale_key, None)
    protected_prom_stats["compatibility_plume"] = harmonic_stats
    del lower_p3, upper_p3
    log(
        start,
        "pilot H40 reproduït dins el builder",
        {
            "gate_u16": harmonic_stats["gate_u16_sha256"],
            "domain_pixels": harmonic_stats["declared_domain_pixels"],
        },
    )

    # P4 només governa ID5/ID7 i congela el compost acumulat ID3→ID4.
    final125_frame_path = work / "mask_5_125_after_protection4_u16.npy"
    final60_frame_path = work / "mask_7_60_after_protection4_u16.npy"
    joint_prominence_stats = joint_protect_stack_u16(
        [p3_125_path, p3_60_path],
        protected_prom_gate,
        protected_prom_core,
        [final125_frame_path, final60_frame_path],
        [5, 7],
        "P4_LIMBE_PROTUBERANCIES",
        gate_u16_authority=protected_prom_gate_u16,
    )
    path125 = work / "mask_5_125.npy"
    path60 = work / "mask_7_60.npy"
    write_full_mask_u16(path125, np.load(final125_frame_path, mmap_mode="r"))
    write_full_mask_u16(path60, np.load(final60_frame_path, mmap_mode="r"))
    mask_paths[5] = path125
    mask_paths[7] = path60
    del dist60, gate60, m60, h125, hot125, protected_gate
    log(
        start,
        "màscares canòniques construïdes",
        {"P3": joint_contact_stats, "P4": joint_prominence_stats},
    )

    # Mutació controlada del round-trip: es retira només la còpia PSD redundant.
    psd.remove(by_id[6])
    remaining = list(psd)
    if [layer.layer_id for layer in remaining] != [3, 4, 5, 7]:
        raise AssertionError("eliminació de duplicat no determinista")
    add_mask16(
        by_id[3],
        np.load(mask_paths[3], mmap_mode="r"),
        top=FRAME[1],
        left=FRAME[0],
        compression=Compression.ZIP_WITH_PREDICTION,
    )
    for layer_id in (4, 5, 7):
        replace_mask16(by_id[layer_id], np.load(mask_paths[layer_id], mmap_mode="r"), header)
    for layer in remaining:
        layer.name = FINAL_NAMES[layer.layer_id]
        layer.blend_mode = BlendMode.NORMAL
        layer.opacity = 255
        layer.fill_opacity = 255
        layer.visible = True

    merged_path = work / "merged_rgb16.npy"
    merged = compose_merged(remaining, header, mask_paths, merged_path, start)
    protected_metrics = protected_contact_qa(
        merged,
        by_id[PROTECTED_SOURCE_LAYER_ID],
        header,
        protected_core,
        mask_paths,
        protected_support_stats,
    )
    log(
        start,
        "perles/diamant preservats exactament",
        protected_metrics["baily_diamond_gate"],
    )
    del protected_core
    protected_prom_metrics = protected_prominence_qa(
        merged,
        by_id,
        header,
        protected_prom_core,
        protected_prom_strong_core,
        protected_prom_allowed,
        protected_prom_photo_gate,
        protected_prom_domain,
        protected_prom_radial_gate,
        mask_paths,
        {5: p3_125_path, 7: p3_60_path},
        protected_prom_gate,
        protected_prom_gate_u16,
        frozen_lower4_path,
        protected_prom_stats,
    )
    log(
        start,
        "limbe/protuberàncies 1/500 preservats exactament",
        protected_prom_metrics["core_exactness"],
    )
    del (
        protected_prom_core,
        protected_prom_strong_core,
        protected_prom_allowed,
        protected_prom_photo_gate,
        protected_prom_domain,
        protected_prom_radial_gate,
        protected_prom_gate,
        protected_prom_gate_u16,
    )
    transition_metrics = transition_qa(merged)
    log(start, "transició radial sense mínims locals", transition_metrics["mean_u16"])
    expected_merged_hashes = merged_hashes(merged)

    finalize_lr16(psd)
    set_merged(psd, merged, compression=Compression.RAW)
    lm = psd._record.layer_and_mask_information
    if lm.tagged_blocks is not None and Tag.SAVING_MERGED_TRANSPARENCY16 in lm.tagged_blocks:
        del lm.tagged_blocks[Tag.SAVING_MERGED_TRANSPARENCY16]
    psd._record.header.channels = 3
    psd._updated = False
    psd.save(output)
    del merged
    log(start, "PSB temporal desat", output, output.stat().st_size)

    validation = validate_output(output, source_hashes, mask_paths, expected_merged_hashes)
    output_sha = sha256_file(output)
    if sha256_file(source) != SOURCE_SHA256:
        raise AssertionError("Corretgint.psb ha canviat durant la construcció")
    qa = {
        "status": "PASS",
        "source": {"path": str(source), "size": SOURCE_SIZE, "sha256": SOURCE_SHA256},
        "output": {"path": str(output), "size": output.stat().st_size, "sha256": output_sha},
        "removed_redundant_layer_id": 6,
        "preserved_source_layer_ids": [3, 4, 5, 7],
        "profile_controls": controls,
        "saturation_gate_counts_gt_0_5": h_counts,
        "protected_contact_qa": protected_metrics,
        "protected_prominence_qa": protected_prom_metrics,
        "joint_alpha_transforms": {
            "P3_PERLES_DIAMANT": joint_contact_stats,
            "P4_LIMBE_PROTUBERANCIES": joint_prominence_stats,
        },
        "frozen_lower_reference4": frozen_lower4_stats,
        "transition_qa": transition_metrics,
        "validation": validation,
    }
    qa_path = work / "qa.json"
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log(start, "QA PASS", output_sha)


if __name__ == "__main__":
    main()
