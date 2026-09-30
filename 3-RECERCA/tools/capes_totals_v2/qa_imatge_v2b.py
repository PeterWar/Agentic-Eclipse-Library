"""QA d'imatge de ``CapesTotalsV2b`` (només lectura): estrelles i limbe lunar.

Llegeix el canal G de les capes directament del candidat i el col·loca al llenç
amb la bbox del fitxer, o sigui que jutja la reixa tal com la veurà Photoshop.

(d) estrelles (DoG sobre el log, centroide gaussià 2D, r = 2,3–6,5 R☉):
    01−03 i 01−02 han de ser ≈ 0 ± 0,5 px; 02−03 és el control.
(e) limbe lunar: ajust de cercle als mateixos azimuts del costat fosc de la
    1/3200 per a ID3, ID4, ID5 i ID8; es compara el DIFERENCIAL contra ID8
    (apilat 572A2970, reixa comuna coneguda) amb el model d'efemèride del
    manifest de Corona_HDR_Vixen, perquè el mètode del limbe té un biaix
    absolut que depèn de l'exposició (~1 px) i el diferencial l'anul·la.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from psd_tools import PSDImage
from psd_tools.constants import ChannelID
from scipy import ndimage as ndi, optimize

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_capes_totals_v2 as base  # noqa: E402

W, H = base.WIDTH, base.HEIGHT
# Sol de la geometria comuna (HDR4/qa/*.json: 572A2969) + reixa dels apilats (457,463)
SOL = (3563.8912793889317 + 457, 2274.660453669 + 463)
RS = 446.2
# Efemèride (manifest Corona_HDR_Vixen, còpia _prova_skill): centres lunars mesurats al limbe, en coords del propi fotograma,
# i desplaçament sol_2969 − sol_f de HDR4 (comuna). 2956 no és al manifest: model lineal (v_lluna, v_sol).
LLUNA_MES = {"2968": (3578.9792793722536, 2275.1136009635943), "2969": (3579.451411692386, 2274.8008292658233), "2970": (3578.8528024425596, 2274.5295826810748)}
DESP = {"2968": (0.163, -0.180), "2969": (0.0, 0.0), "2970": (-0.1689, 0.1851)}
T = {"2956": -0.750, "2968": 7.541, "2969": 8.444, "2970": 9.3767}
V_LLUNA = (-0.06484116141466612, -0.3283337107276059)   # px/s, geometria.json
V_SOL = (0.18442215936052028, -0.1965783259797699)      # px/s, deriva_corona.json
LAYER_FRAME = {3: "2956", 4: "2968", 5: "2969", 8: "2970"}


def canvas_G(psd, lid):
    layer = next(l for l in psd if l.layer_id == lid)
    g = base._decoded_channel_u16(layer, ChannelID.CHANNEL_1, psd._record.header)
    out = np.full((H, W), np.nan, np.float32)
    l0, t0 = layer.left, layer.top; h, w = g.shape
    x0, y0 = max(0, l0), max(0, t0); x1, y1 = min(W, l0 + w), min(H, t0 + h)
    out[y0:y1, x0:x1] = g[y0 - t0:y1 - t0, x0 - l0:x1 - l0].astype(np.float32) / 65535.0
    return out


def detect(img, rmin=2.3, rmax=6.5, k=8.0):
    yy, xx = np.mgrid[0:H, 0:W]; r = np.hypot(xx - SOL[0], yy - SOL[1]) / RS
    L = np.log(np.maximum(np.nan_to_num(img, nan=0), 1e-4))
    d = ndi.gaussian_filter(L, 1.0) - ndi.gaussian_filter(L, 4.0)
    m = (r > rmin) & (r < rmax) & np.isfinite(img)
    sig = 1.4826 * np.median(np.abs(d[m] - np.median(d[m])))
    pk = (d == ndi.maximum_filter(d, 11)) & m & (d > k * sig)
    ys, xs = np.nonzero(pk)
    return list(zip(xs, ys, d[ys, xs] / sig))


def centroid(img, x, y, R=5):
    y0, x0 = int(y), int(x)
    sub = img[y0 - R:y0 + R + 1, x0 - R:x0 + R + 1]
    if sub.shape != (2 * R + 1, 2 * R + 1) or not np.isfinite(sub).all():
        return None
    yy, xx = np.mgrid[-R:R + 1, -R:R + 1]
    bg = np.median(np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]]))
    def model(p):
        A, cx, cy, sx, sy, b = p
        return b + A * np.exp(-((xx - cx) ** 2 / (2 * sx ** 2) + (yy - cy) ** 2 / (2 * sy ** 2)))
    try:
        p, _ = optimize.leastsq(lambda p: (model(p) - sub).ravel(), [sub.max() - bg, 0, 0, 1.5, 1.5, bg], maxfev=400)
    except Exception:
        return None
    A, cx, cy, sx, sy, b = p
    if A <= 0 or abs(cx) > 3 or abs(cy) > 3 or not (0.5 < abs(sx) < 6 and 0.5 < abs(sy) < 6):
        return None
    return x0 + cx, y0 + cy, A, sub.max()


def estrelles(A, B, AMP=0.003):
    rows = []
    for x, y, snr in detect(A):
        ca = centroid(A, x, y); cb = centroid(B, x, y)
        if ca is None or cb is None or ca[3] > 0.97 or cb[3] > 0.97:
            continue
        rows.append((ca[0], ca[1], cb[0] - ca[0], cb[1] - ca[1], snr, ca[2], cb[2]))
    good = [r for r in rows if r[5] > AMP and r[6] > AMP]
    gx = np.array([r[2] for r in good]); gy = np.array([r[3] for r in good])
    return dict(n=len(good), dx=float(np.median(gx)) if good else None, dy=float(np.median(gy)) if good else None,
                mad=[float(1.4826 * np.median(np.abs(gx - np.median(gx)))), float(1.4826 * np.median(np.abs(gy - np.median(gy))))] if good else None,
                parelles=[list(map(float, r)) for r in good])


def edges(img, c0, r0=430, r1=475, sigma=1.5, pas_az=0.5):
    cx0, cy0 = c0; x0, y0 = int(cx0 - 520), int(cy0 - 520); S = 1040
    sub = np.nan_to_num(img[y0:y0 + S, x0:x0 + S], nan=0.0)
    L = ndi.gaussian_filter(np.log(np.maximum(sub, 2e-4)), sigma)
    az = np.radians(np.arange(0, 360, pas_az)); rr = np.arange(r0, r1, 0.25)
    cx, cy = cx0 - x0, cy0 - y0
    X = cx + rr[None, :] * np.cos(az[:, None]); Y = cy - rr[None, :] * np.sin(az[:, None])
    prof = ndi.map_coordinates(L, [Y.ravel(), X.ravel()], order=1).reshape(len(az), len(rr))
    g = np.gradient(prof, axis=1); k = np.argmax(g, axis=1)
    fora = np.array([np.exp(prof[j, min(len(rr) - 1, k[j] + 24):min(len(rr), k[j] + 48)]).mean() for j in range(len(az))])
    rad = np.full(len(az), np.nan)
    for j in range(len(az)):
        jj = k[j]
        if jj <= 0 or jj >= len(rr) - 1:
            continue
        m, z, p = g[j, jj - 1], g[j, jj], g[j, jj + 1]; den = m - 2 * z + p
        rad[j] = rr[jj] + ((m - p) / (2 * den) if den != 0 else 0.0) * 0.25
    return az, rad, fora, (cx0, cy0)


def cercle(az, rad, sel, c0):
    ok = sel & np.isfinite(rad)
    px = c0[0] + rad[ok] * np.cos(az[ok]); py = c0[1] - rad[ok] * np.sin(az[ok])
    keep = np.ones(len(px), bool)
    for _ in range(10):
        A = np.c_[2 * px[keep], 2 * py[keep], np.ones(keep.sum())]; b = px[keep] ** 2 + py[keep] ** 2
        a_, b_, c_ = np.linalg.lstsq(A, b, rcond=None)[0]; R = np.sqrt(c_ + a_ ** 2 + b_ ** 2)
        res = np.hypot(px - a_, py - b_) - R; s = 1.4826 * np.median(np.abs(res[keep]))
        nk = np.abs(res) < 2.5 * max(s, 0.25)
        if (nk == keep).all():
            break
        keep = nk
    return dict(cx=float(a_), cy=float(b_), R=float(R), rms=float(res[keep].std()), n=int(keep.sum()))


def moon_canvas_model(frame):
    """Centre lunar previst al llenç (reixa comuna 457,463) per a un fotograma del manifest."""
    lx, ly = LLUNA_MES[frame]; dx, dy = DESP[frame]
    return (lx + dx + 457, ly + dy + 463)


def main() -> None:
    parser = argparse.ArgumentParser(description="QA d'imatge (estrelles i limbe) de CapesTotalsV2b")
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--P", type=int, default=30, help="percentil del costat fosc (azimuts de la 1/3200)")
    args = parser.parse_args()
    psd = PSDImage.open(args.candidate.resolve())
    out: dict[str, object] = {"candidate": str(args.candidate.resolve())}
    bbox = {l.layer_id: list(l.bbox) for l in psd}
    out["bbox"] = {str(k): v for k, v in bbox.items()}
    # (d) estrelles
    G = {lid: canvas_G(psd, lid) for lid in (13, 16, 17)}
    out["estrelles"] = {
        "01-03": estrelles(G[13], G[17]), "01-02": estrelles(G[16], G[17]), "02-03_control": estrelles(G[13], G[16]),
    }
    for key in ("01-03", "01-02"):
        e = out["estrelles"][key]
        print(f"estrelles {key}: n={e['n']} mediana=({e['dx']:+.2f}, {e['dy']:+.2f}) MAD={e['mad']}")
    ok_d = all(abs(out["estrelles"][k]["dx"]) <= 0.5 and abs(out["estrelles"][k]["dy"]) <= 0.5 for k in ("01-03", "01-02"))
    print(f"estrelles 02-03 (control): {out['estrelles']['02-03_control']['dx']:+.2f}, {out['estrelles']['02-03_control']['dy']:+.2f}")
    del G
    # (e) limbe
    G = {lid: canvas_G(psd, lid) for lid in (3, 4, 5, 8)}
    c0 = {3: (moon_canvas_model("2969")[0] + 0.2, moon_canvas_model("2969")[1] + 3.1), 4: moon_canvas_model("2968"), 5: moon_canvas_model("2969"), 8: moon_canvas_model("2970")}
    E = {lid: edges(G[lid], c0[lid]) for lid in G}
    az, rad, fora, _ = E[3]
    sel = fora <= np.percentile(fora, args.P)
    fits = {lid: cercle(*E[lid][:2], sel, E[lid][3]) for lid in G}
    out["limbe"] = {"P": args.P, "fits_llenc": {str(k): v for k, v in fits.items()}, "diferencials": {}}
    for lid in (4, 5):
        f = LAYER_FRAME[lid]
        mes = (fits[lid]["cx"] - fits[8]["cx"], fits[lid]["cy"] - fits[8]["cy"])
        exp = (moon_canvas_model(f)[0] - moon_canvas_model("2970")[0], moon_canvas_model(f)[1] - moon_canvas_model("2970")[1])
        absol = (fits[lid]["cx"] - moon_canvas_model(f)[0], fits[lid]["cy"] - moon_canvas_model(f)[1])
        out["limbe"]["diferencials"][str(lid)] = {"mesurat_vs_ID8": mes, "esperat_vs_ID8": exp, "residu": (mes[0] - exp[0], mes[1] - exp[1]), "absolut_vs_efemeride": absol}
        print(f"limbe ID{lid}−ID8: mesurat ({mes[0]:+.2f},{mes[1]:+.2f}) esperat ({exp[0]:+.2f},{exp[1]:+.2f}) residu ({mes[0]-exp[0]:+.2f},{mes[1]-exp[1]:+.2f}); absolut vs efemèride ({absol[0]:+.2f},{absol[1]:+.2f})")
    # ID3: el seu disc al llenç ha de ser a lluna_2968 − v_lluna·Δt (propi) + (sol_2969 − sol_2956) ... expressat via ID4:
    dt = T["2968"] - T["2956"]
    exp3 = (fits[4]["cx"] - (V_LLUNA[0] - V_SOL[0]) * dt, fits[4]["cy"] - (V_LLUNA[1] - V_SOL[1]) * dt)  # a la reixa comuna, la Lluna relativa al Sol
    res3 = (fits[3]["cx"] - exp3[0], fits[3]["cy"] - exp3[1])
    out["limbe"]["diferencials"]["3"] = {"esperat_des_de_ID4": exp3, "mesurat": (fits[3]["cx"], fits[3]["cy"]), "residu": res3}
    print(f"limbe ID3 (via ID4, Δt={dt:.3f} s): residu ({res3[0]:+.2f},{res3[1]:+.2f})")
    ok_e = all(abs(v) <= 0.5 for lid in ("4", "5") for v in out["limbe"]["diferencials"][lid]["residu"])
    out["resultat"] = {"d_estrelles_0.5px": ok_d, "e_limbe_diferencial_0.5px": ok_e}
    print(json.dumps(out["resultat"]))
    if args.out is not None:
        base.write_json_no_clobber(args.out, out)


if __name__ == "__main__":
    main()
