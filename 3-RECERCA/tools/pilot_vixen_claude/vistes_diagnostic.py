"""Vistes de diagnòstic d'un compost, per caçar artefactes a ull.

⛔ Cap d'aquestes imatges NO és el producte: el producte és el float lineal. Són
miralls, i cadascun ensenya una família d'artefacte diferent. Ordre de Pere del
24-08-2026: «a cada etapa genera imatges, que seguiré buscant artefactes».

Norma del rectangle: totes es pinten a **tot el rectangle**; l'única cosa que
les atura és que no hi hagi dada, i això entra pel pes i mai per una
circumferència.

Les set vistes, i què caça cadascuna:

| vista | què hi busques |
|---|---|
| `lineal` | com queda de veritat; cremats i color |
| `radial` | anells de fusió i costures — el fons queda pla |
| `passalt` | detall fi, i qualsevol textura que no sigui corona |
| `esglao` | **quina exposició mana a cada píxel**: les fronteres de fusió, dibuixades |
| `cobertura` | quants fotogrames hi contribueixen: petjades i saturació |
| `color` | R/G i B/G contra el seu perfil radial: franges de color |
| `soroll` | senyal sobre soroll del compost |
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402

CMAP = cv2.COLORMAP_TURBO


def _radis(h: int, w: int) -> np.ndarray:
    yy = np.arange(h, dtype=np.float32)[:, None] - h / 2
    xx = np.arange(w, dtype=np.float32)[None, :] - w / 2
    return np.hypot(yy, xx) / C.R_SOL_PX


def _perfil(v: np.ndarray, rr: np.ndarray, m: np.ndarray, nb: int = 700):
    """Perfil radial per calaix però RETORNAT amb interpolació contínua.
    ⛔ Mai `med[ib]`: això és el que feia 700 anells amb dents de serra."""
    rmax = float(rr[m].max())
    ib = np.clip((rr / rmax * nb).astype(np.int32), 0, nb - 1)
    med = np.full(nb, np.nan)
    o = np.argsort(ib[m]); ii = ib[m][o]; vv = v[m][o]
    talls = np.searchsorted(ii, np.arange(nb + 1))
    for a in range(nb):
        seg = vv[talls[a]:talls[a + 1]]
        if seg.size > 200:
            med[a] = np.median(seg)
    bons = np.isfinite(med)
    if bons.sum() < 8:
        return np.ones_like(rr)
    med = np.interp(np.arange(nb), np.flatnonzero(bons), med[bons])
    centres = (np.arange(nb) + 0.5) * rmax / nb
    return np.interp(rr, centres, med)


def _desa(dst: Path, nom: str, img: np.ndarray, etiqueta: str) -> str:
    f = dst / f"{etiqueta}__{nom}.png"
    cv2.imwrite(str(f), img)
    return f.name


def _gris(x: np.ndarray, lo: float, hi: float) -> np.ndarray:
    return (np.clip(np.nan_to_num((x - lo) / max(hi - lo, 1e-12)), 0, 1) * 65535).astype(np.uint16)


def vistes(dirc: Path, dst: Path, etiqueta: str) -> dict:
    hdr = np.load(dirc / "HDR_adu_s.npy")
    H, W = hdr.shape[:2]
    rr = _radis(H, W)
    g = hdr[..., 1].astype(np.float32)
    m = np.isfinite(g) & (g > 0)
    dst.mkdir(parents=True, exist_ok=True)
    fets = {}

    # --- balanç de blancs només per mirar
    an = (rr > 2.0) & (rr < 3.0) & m
    wb = [float(np.nanmedian(hdr[..., 1][an]) / np.nanmedian(hdr[..., i][an])) for i in range(3)]
    neutre = hdr.astype(np.float32) * np.array(wb, np.float32)

    # 1 · lineal
    ref = float(np.nanpercentile(neutre[..., 1], 99.9))
    lin = np.log1p(np.clip(np.nan_to_num(neutre) / ref, 0, 1) * 2000.0) / math.log1p(2000.0)
    fets["lineal"] = _desa(dst, "lineal", cv2.cvtColor(
        (np.clip(lin, 0, 1) * 65535).astype(np.uint16), cv2.COLOR_RGB2BGR), etiqueta)

    # 2 · normalitzat radialment
    vis = np.empty_like(neutre)
    for ch in range(3):
        v = neutre[..., ch]
        mm = np.isfinite(v) & (v > 0)
        vis[..., ch] = v / np.maximum(_perfil(v, rr, mm), 1e-30)
    lo, hi = np.nanpercentile(vis[..., 1][m], [1, 99.5])
    fets["radial"] = _desa(dst, "radial", cv2.cvtColor(
        _gris(vis, lo, hi), cv2.COLOR_RGB2BGR), etiqueta)

    # 3 · passa-alt sobre ln, a tot el rectangle
    ln = np.log(np.maximum(g, 1e-30), dtype=np.float32)
    ln = np.where(m, ln, np.nan)
    pes = m.astype(np.float32)
    llis = cv2.GaussianBlur(np.nan_to_num(ln) * pes, (0, 0), 12.0)
    nrm = cv2.GaussianBlur(pes, (0, 0), 12.0)
    hp = np.where(nrm > 1e-6, np.nan_to_num(ln) - llis / np.maximum(nrm, 1e-6), 0.0)
    s = float(np.nanstd(hp[m]))
    fets["passalt"] = _desa(dst, "passalt", _gris(np.where(m, hp, 0.0), -3 * s, 3 * s), etiqueta)

    # 4 · quina exposició mana: la frontera de fusió, dibuixada
    if (dirc / "ESGLAO_DOMINANT.npy").exists():
        dom = np.load(dirc / "ESGLAO_DOMINANT.npy")
        d = dom[..., 1] if dom.ndim == 3 else dom
        d = d.astype(np.float32)
        nn = float(np.nanmax(d))
        col = cv2.applyColorMap(
            (np.clip(d / max(nn, 1) * 255, 0, 255)).astype(np.uint8), CMAP)
        col[~m] = 0
        fets["esglao"] = _desa(dst, "esglao_dominant", col, etiqueta)

    # 5 · cobertura
    if (dirc / "COBERTURA.npy").exists():
        cob = np.load(dirc / "COBERTURA.npy")
        c = cob[..., 1] if cob.ndim == 3 else cob
        c = c.astype(np.float32)
        lo2, hi2 = np.nanpercentile(c[m], [1, 99])
        col = cv2.applyColorMap(
            (np.clip((c - lo2) / max(hi2 - lo2, 1e-9), 0, 1) * 255).astype(np.uint8), CMAP)
        col[~m] = 0
        fets["cobertura"] = _desa(dst, "cobertura", col, etiqueta)

    # 6 · color: R/G i B/G contra el seu propi perfil radial
    rg = np.where(m, hdr[..., 0] / np.maximum(g, 1e-30), np.nan)
    bg = np.where(m, hdr[..., 2] / np.maximum(g, 1e-30), np.nan)
    out = np.zeros((H, W, 3), np.uint16)
    for k, (v, canal) in enumerate(((rg, 2), (bg, 0))):
        mm = np.isfinite(v)
        d = v / np.maximum(_perfil(np.nan_to_num(v), rr, mm), 1e-30)
        lo3, hi3 = np.nanpercentile(d[mm], [1, 99])
        out[..., canal] = _gris(np.where(mm, d, 1.0), lo3, hi3)
    out[..., 1] = (out[..., 0].astype(np.int32) + out[..., 2]) // 2
    fets["color"] = _desa(dst, "color_RG_BG", out, etiqueta)

    # 7 · senyal sobre soroll
    if (dirc / "VAR_adu_s2.npy").exists():
        var = np.load(dirc / "VAR_adu_s2.npy")
        snr = np.where(m, g / np.sqrt(np.maximum(var[..., 1], 1e-30)), 0.0)
        col = cv2.applyColorMap(
            (np.clip(np.log10(np.maximum(snr, 0.1)) / 3.0, 0, 1) * 255).astype(np.uint8), CMAP)
        col[~m] = 0
        fets["soroll"] = _desa(dst, "senyal_soroll", col, etiqueta)

    return {"font": str(dirc), "llenc": [W, H], "balanc_per_mirar_rgb": wb,
            "vistes": fets,
            "nota": "cap d'aquestes imatges no és el producte; el producte és el float lineal"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("dir", type=Path, help="directori d'una fase 2")
    ap.add_argument("etiqueta")
    ap.add_argument("--dst", type=Path,
                    default=C.DESK / "IA" / "output" / "pilot_vixen_claude_20260824")
    a = ap.parse_args()
    print(json.dumps(vistes(a.dir, a.dst, a.etiqueta), indent=1, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
