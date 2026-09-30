"""Separa CORONA i CEL pel COLOR, no pel temps.

⛔ Per què això és una via nova. El model de cel de `research/99` §13 ajusta
`total(t) = corona + S·f(t)` fotograma a fotograma: veu el cel **variable**, i
el seu propi avís ho diu —«la part constant queda dins C i aquesta via no la
veu»—. El color no té aquest problema: **la corona és de color solar i el cel és
blau**, i això separa els dos components sense mirar el temps.

La descomposició és `I_canal = a·k_corona[canal] + b·k_cel[canal]`: **tres
equacions i dues incògnites**, o sigui que li queda **un grau de llibertat per
fallar**. Mesurat al pilot, el residu és de 0,02 a 1,26 % a tots els anells i
als dos trens: la passa.

I la prova que NO pot ser circular: els dos trens tenen sensors, filtres i
calibratges diferents, i les seves fraccions de cel **coincideixen a 1-2 punts a
tots els radis**. El cel iguala la corona a **~2,4 R☉**, que és el 2,41 R☉ que
`research/99` va treure per la via temporal.

⚠️ Els vectors de color s'han de mesurar **al mateix espai** que les dades. El
color del cel de `research/99` §13 és instrumental (ADU/s per pla CFA) i aquí
les dades són calibrades (B/B☉ per canal): posar-hi aquell dona un 26 % menys de
cel, i no és cap contradicció, són espais diferents.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402


def _med(arr, m):
    return np.array([float(np.nanmedian(np.where(m, np.asarray(arr[..., i], np.float32), np.nan)))
                     for i in range(3)])


def vectors(arr, rr, r_corona=(1.10, 1.35), r_cel=(7.0, 10.0)):
    """Els dos colors: la corona on el cel encara no mana, i el cel on mana ell."""
    kc = _med(arr, (rr >= r_corona[0]) & (rr < r_corona[1]))
    ks = _med(arr, (rr >= r_cel[0]) & (rr < r_cel[1]))
    return kc / kc[1], ks / ks[1]


def separa(arr, rr, kc, ks, sigma_px: float = 120.0):
    """El CEL sobre una versió suavitzada, i la corona per diferència.

    ⛔ **Per píxel no es pot.** La separació entre els dos colors és petita
    —ΔB/G = 0,113— i la descomposició amplifica el soroll **×2,8 a ×3,1**
    (número de condició 7,4): a 3 R☉, un 1 % de soroll per canal es converteix
    en un **11,8 %** sobre la corona. Resolt així, el mapa de corona surt ple
    d'una lluïssor difusa que és soroll amplificat i no corona.

    El que sí que es pot, i és físic: **el cel no té estructura fina**
    —`research/99` §13 l'ajusta amb una quàdrica—, o sigui que es resol sobre
    una versió molt suavitzada, i el mapa de cel que en surt es resta a
    **resolució sencera**. La corona conserva tot el seu detall i el cel no n'hi
    posa cap.

    La convolució és **incompleta i normalitzada pel pes** (`(I·w)⊗G / (w⊗G)`),
    que és la norma del rectangle ben feta: el que la para és no tenir dada.
    """
    import cv2
    M = np.stack([kc, ks], 1)
    Mp = np.linalg.pinv(M)
    H, W = arr.shape[:2]
    llis = np.empty((H, W, 3), np.float32)
    val = None
    for i in range(3):
        b = np.asarray(arr[..., i], np.float32)
        m = np.isfinite(b).astype(np.float32)
        val = m if val is None else val * m
        num = cv2.GaussianBlur(np.nan_to_num(b) * m, (0, 0), sigma_px)
        den = cv2.GaussianBlur(m, (0, 0), sigma_px)
        llis[..., i] = np.where(den > 1e-6, num / np.maximum(den, 1e-6), np.nan)
    cel = (llis[..., 0] * Mp[1, 0] + llis[..., 1] * Mp[1, 1]
           + llis[..., 2] * Mp[1, 2]).astype(np.float32)
    cel = np.where(val > 0, cel, np.nan)
    # ⛔ A dins de ~2 R☉ la descomposició és DEGENERADA —allà el cel és del 0,1
    # al 4 % del senyal— i el que en sortia era soroll, que retallat a zero
    # deixava un **forat al mapa de cel molt més gran que la Lluna**. I un forat
    # és físicament fals: el cel és un gradient de gran escala i no té cap motiu
    # per desaparèixer al limbe. El que es fa és el que `research/99` §13 ja
    # feia amb la via temporal: **ajustar una quàdrica on el cel SÍ que està
    # determinat** —r ≥ 2 R☉— i avaluar-la a tot el rectangle.
    bo = np.isfinite(cel) & (rr >= 2.0) & (val > 0)
    if bo.sum() > 10000:
        sub = (slice(None, None, 8), slice(None, None, 8))
        u = ((np.arange(W, dtype=np.float64) - W / 2) / (W / 2))[None, :]
        v2 = ((np.arange(H, dtype=np.float64) - H / 2) / (H / 2))[:, None]
        U = np.broadcast_to(u, (H, W)); V = np.broadcast_to(v2, (H, W))
        base = [np.ones((H, W)), U, V, U * U, U * V, V * V]
        A = np.stack([b[sub][bo[sub]].ravel() for b in base], 1)
        y = cel[sub][bo[sub]].ravel().astype(np.float64)
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        quad = sum(c * b for c, b in zip(coef, base)).astype(np.float32)
        residu = float(np.std(cel[bo] - quad[bo]) / max(np.mean(cel[bo]), 1e-30))
        cel = np.where(val > 0, quad, np.nan)
    else:
        residu = float("nan")
    # ⛔ I les dues fites físiques: ni negatiu, ni per damunt del total.
    verd = np.where(val > 0, np.asarray(arr[..., 1], np.float32), np.nan)
    cel = np.clip(cel, 0.0, np.nan_to_num(verd, nan=0.0))
    cor = (verd - cel).astype(np.float32)
    return cor, np.where(val > 0, cel, np.nan).astype(np.float32), residu


def perfil(arr, rr, kc, ks, anells):
    M = np.stack([kc, ks], 1)
    files = []
    for a, b in anells:
        m = (rr >= a) & (rr < b)
        if m.sum() < 5000:
            continue
        y = _med(arr, m)
        if not np.isfinite(y).all():
            continue
        x, *_ = np.linalg.lstsq(M, y, rcond=None)
        res = float(np.max(np.abs(M @ x - y) / np.maximum(np.abs(y), 1e-30)))
        files.append({"r_rsol": round(0.5 * (a + b), 3),
                      "corona_BBsol": float(f"{x[0]:.5g}"),
                      "cel_BBsol": float(f"{x[1]:.5g}"),
                      "cel_sobre_total": round(float(x[1] / max(x[0] + x[1], 1e-30)), 4),
                      "residu_maxim_percent": round(100 * res, 3)})
    return files


def resta_a_la_reixa(dirc: Path, dst: Path, r_asimptota=(6.5, 7.5),
                     r_corona=(1.10, 1.35), sigma_px: float = 120.0) -> dict:
    """Escriu una variant del compost amb el CEL DEL COLOR restat, a la reixa
    pròpia del tren, perquè la fase 3 la pugui consumir tal qual.

    ⛔ Per què cal, i no n'hi ha prou amb el model temporal: amb el color
    corregit, el producte `cel-model` deixa de tenir blaus negatius —de 64,5 % a
    **0,0 %** a 4,4-5,1 R☉— però el **verd** hi queda al 55 % de negatius. La
    causa és l'amplitud: el cel temporal val 1,318·10⁻⁸ i el del color
    1,209·10⁻⁸, un **9 % més**, i aquell 9 % és més gran que la corona que hi
    queda (7 % del total a 5 R☉). O sigui que el que sobre-resta no és el color
    sinó el nivell, i el nivell bo és el que el color mesura.
    """
    hdr = np.load(dirc / "HDR_adu_s.npy")
    var = np.load(dirc / "VAR_adu_s2.npy", mmap_mode="r")
    H, W = hdr.shape[:2]
    yy = np.arange(H, dtype=np.float32)[:, None] - H / 2
    xx = np.arange(W, dtype=np.float32)[None, :] - W / 2
    rr = np.hypot(yy, xx) / C.R_SOL_PX
    kc, ks = vectors(hdr, rr, r_corona=r_corona, r_cel=r_asimptota)
    _, cel_g, res_quad = separa(hdr, rr, kc, ks, sigma_px=sigma_px)
    out = np.empty_like(hdr, np.float32)
    for i in range(3):
        out[..., i] = np.asarray(hdr[..., i], np.float32) - cel_g * float(ks[i])
    dst.mkdir(parents=True, exist_ok=True)
    np.save(dst / "HDR_adu_s.npy", out)
    # ⛔ La variància NO baixa en restar el cel: el cel restat és un model, i el
    # soroll dels fotons que el van fer hi continua. Es copia tal qual.
    np.save(dst / "VAR_adu_s2.npy", np.asarray(var, np.float32))
    for n in ("COBERTURA.npy", "ESGLAO_DOMINANT.npy"):
        if (dirc / n).exists():
            np.save(dst / n, np.load(dirc / n, mmap_mode="r"))
    neg = {}
    for a, b in ((2.2, 2.6), (3.0, 3.6), (4.4, 5.1)):
        m = (rr >= a) & (rr < b)
        neg[f"{a}-{b}"] = [round(100 * float(np.nanmean(out[..., i][m] < 0)), 2)
                           for i in range(3)]
    return {"origen": str(dirc), "desti": str(dst),
            "color_cel_RGB": [round(float(v), 4) for v in ks],
            "residu_de_la_quadrica": round(res_quad, 5),
            "cel_verd_median_adu_s": float(f"{np.nanmedian(cel_g):.6g}"),
            "percent_negatius_RGB_per_anell": neg}


def resta_sony(dirc: Path, dst: Path, r_asimptota=(6.5, 7.5),
               r_corona=(1.10, 1.35), sigma_px: float = 120.0) -> dict:
    """El mateix per al compost Sony, que ja viu al llenç comú.

    ⛔ El seu `k_cel` es mesura al SEU compost, no al de la Vixen: els dos
    cossos tenen resposta espectral diferent i el color del cel hi surt diferent
    —Sony R/G 0,365 · B/G 0,647 contra Vixen 0,458 · 0,472—. Fer servir un sol
    vector deixaria una costura de color justament on es toquen.
    """
    hdr = np.load(dirc / "SONY_LLENC_BBsol.npy")
    H, W = hdr.shape[:2]
    yy = np.arange(H, dtype=np.float32)[:, None] - H / 2
    xx = np.arange(W, dtype=np.float32)[None, :] - W / 2
    rr = np.hypot(yy, xx) / C.R_SOL_PX
    kc, ks = vectors(hdr, rr, r_corona=r_corona, r_cel=r_asimptota)
    _, cel_g, res_quad = separa(hdr, rr, kc, ks, sigma_px=sigma_px)
    out = np.empty_like(hdr, np.float32)
    for i in range(3):
        out[..., i] = np.asarray(hdr[..., i], np.float32) - cel_g * float(ks[i])
    dst.mkdir(parents=True, exist_ok=True)
    np.save(dst / "SONY_LLENC_BBsol.npy", out)
    for n in ("SONY_D_verd.npy", "SONY_COBERTURA.npy"):
        if (dirc / n).exists() and not (dst / n).exists():
            os.symlink(os.path.relpath(dirc / n, dst), dst / n)
    neg = {}
    for a, b in ((2.2, 2.6), (3.0, 3.6), (4.4, 5.1)):
        m = (rr >= a) & (rr < b)
        neg[f"{a}-{b}"] = [round(100 * float(np.nanmean(out[..., i][m] < 0)), 2)
                           for i in range(3)]
    return {"origen": str(dirc), "desti": str(dst),
            "color_cel_RGB": [round(float(v), 4) for v in ks],
            "residu_de_la_quadrica": round(res_quad, 5),
            "cel_verd_median_BBsol": float(f"{np.nanmedian(cel_g):.6g}"),
            "percent_negatius_RGB_per_anell": neg}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vixen", type=Path,
                    default=Path("output/pilot_vixen_claude_20260824/dos_trens/"
                                 "VIXEN_al_llenc_BBsol_float32.tif"))
    ap.add_argument("--sony", type=Path,
                    default=Path("output/pilot_vixen_claude_20260824/sony_llenc_comu/"
                                 "SONY_LLENC_BBsol.npy"))
    ap.add_argument("--dst", type=Path,
                    default=Path("output/pilot_vixen_claude_20260824/cel_per_color"))
    ap.add_argument("--resta-sony", type=Path, default=None,
                    help="directori sony_llenc_comu; n'escriu la variant _cel-color")
    ap.add_argument("--resta-a", type=Path, default=None,
                    help="directori d'una fase 2; n'escriu la variant amb el cel del color restat")
    a = ap.parse_args()
    if a.resta_sony is not None:
        d = a.resta_sony
        print(json.dumps(resta_sony(d, d.parent / (d.name + "_cel-color")),
                         indent=1, ensure_ascii=False))
        return 0
    if a.resta_a is not None:
        d = a.resta_a
        r = resta_a_la_reixa(d, d.parent / (d.name + "_cel-color"))
        print(json.dumps(r, indent=1, ensure_ascii=False))
        return 0
    import tifffile
    trens = {"vixen": tifffile.memmap(str(a.vixen)),
             "sony": np.load(a.sony, mmap_mode="r")}
    H, W = trens["vixen"].shape[:2]
    yy = np.arange(H, dtype=np.float32)[:, None] - H / 2
    xx = np.arange(W, dtype=np.float32)[None, :] - W / 2
    rr = np.hypot(yy, xx) / C.R_SOL_PX
    ANELLS = [(1.2, 1.4), (1.4, 1.6), (1.6, 1.9), (1.9, 2.2), (2.2, 2.6),
              (2.6, 3.0), (3.0, 3.6), (3.6, 4.5), (4.5, 5.5), (5.5, 7.0), (7.0, 9.0)]
    a.dst.mkdir(parents=True, exist_ok=True)
    out = {"metode": "descomposicio de color, 3 canals i 2 amplituds",
           "graus_de_llibertat": 1, "trens": {}}
    for nom, arr in trens.items():
        kc, ks = vectors(arr, rr)
        files = perfil(arr, rr, kc, ks, ANELLS)
        cor, cel, res_quad = separa(arr, rr, kc, ks)
        np.save(a.dst / f"{nom}_CORONA_verd_BBsol.npy", cor)
        np.save(a.dst / f"{nom}_CEL_verd_BBsol.npy", cel)
        out["trens"][nom] = {"residu_de_la_quadrica_de_cel": round(res_quad, 5),
                             "color_corona_RGB_respecte_del_verd": [round(float(v), 4) for v in kc],
                             "color_cel_RGB_respecte_del_verd": [round(float(v), 4) for v in ks],
                             "per_anell": files}
        print(f"{nom}: corona R/G {kc[0]:.3f} B/G {kc[2]:.3f} · cel R/G {ks[0]:.3f} B/G {ks[2]:.3f}")
        for f in files:
            print(f"   {f['r_rsol']:5.2f} R☉  corona {f['corona_BBsol']:9.4g}  "
                  f"cel {f['cel_BBsol']:9.4g}  cel/total {f['cel_sobre_total']:.3f}  "
                  f"residu {f['residu_maxim_percent']:.2f} %")
    # acord entre trens
    v = {f["r_rsol"]: f["cel_sobre_total"] for f in out["trens"]["vixen"]["per_anell"]}
    s = {f["r_rsol"]: f["cel_sobre_total"] for f in out["trens"]["sony"]["per_anell"]}
    com = sorted(set(v) & set(s))
    dif = [abs(v[r] - s[r]) for r in com]
    out["acord_entre_trens"] = {"n_anells": len(com),
                                "diferencia_maxima_de_la_fraccio": round(max(dif), 4),
                                "diferencia_mediana": round(float(np.median(dif)), 4)}
    print(f"\nacord entre trens sobre cel/total: mediana {np.median(dif):.4f}, màxim {max(dif):.4f}")
    (a.dst / "CEL_PER_COLOR.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
