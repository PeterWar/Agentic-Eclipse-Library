"""⛔ EL JUTGE EXTERN: cap correcció es declara bona sense passar per aquí.

## Per què existeix aquest fitxer

El 24-08-2026 vaig declarar quatre vegades que un artefacte estava arreglat, i
quatre vegades **Pere el va veure a la imatge** quan el meu número deia que no
hi era. L'error no era de cap mesura concreta: era **de mètode**. Cada estadístic
que em vaig inventar tenia un punt cec que no havia comprovat:

| el que deia el número | el punt cec |
|---|---|
| «la costura es veu a 60 σ» | cap control: el mètode sol ja dona 3-8 σ |
| «a 1,25-1,51 R☉ no es pot mesurar» | les costures són **més juntes** que la finestra |
| «el residu per nivell baixa del 88,6 % al 4,6 %» | la mediana **per azimut** dilueix el que és local |
| «la resta per sector millora la costura ×8» | ⛔ **treia CORONA**, i el número no ho podia saber |

⛔ **La cura no és una porta més sobre el mateix estadístic.** És un jutge que
no comparteixi els punts cecs: **l'altre tren**. La Sony i la Vixen veuen la
mateixa corona amb **una altra òptica, un altre sensor, un altre fosc, un altre
flat, una altra escala d'exposicions i unes altres fronteres de fusió**. Per tant:

> **Una correcció que treu ARTEFACTE d'un tren fa PUJAR la seva correlació amb
> l'altre. Una que treu CORONA la fa BAIXAR.**

Això no es pot autoenganyar amb un estadístic mal triat, perquè el segon tren no
sap res del primer. Mesurat el mateix dia: les dues passades globals fan pujar
l'acord de 0,894 a 0,952 —bones— i la resta per sector el fa baixar de 0,930 a
0,849 —**dolenta, i el seu propi número deia que era vuit vegades millor**—.

⚠️ **El límit del jutge**: els dos trens comparteixen llenç, warp, màscara lunar
i filtre de fase 3. Un artefacte introduït per **aquelles** etapes també
correlacionaria i el jutge no el veuria. El que sí que exclou del tot és tot el
que NO comparteixen, que és on viuen les costures de fusió i els anells.

## Ús

    jutge_creuat.py --sony <dir filtres_sony> --candidat <dir> [--candidat <dir> ...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402
import portes as P  # noqa: E402

BANDES = ((1.10, 1.30), (1.30, 1.50), (1.50, 1.75), (1.75, 2.10), (2.10, 2.60))


def correlacions(dir_vixen: Path, ds: np.ndarray, ws: np.ndarray,
                 escala_sony: float = 3.2019914, escala_vixen: float = 2.1494814):
    import cv2
    from scipy.ndimage import gaussian_filter
    Hc, Wc = ds.shape
    d = np.load(dir_vixen / "DETALL_ln.npy")
    w = np.load(dir_vixen / "PES.npy")
    H, W = d.shape
    A = C.afi((W / 2.0, H / 2.0), (Wc / 2.0, Hc / 2.0))
    dc = cv2.warpAffine(np.nan_to_num(d * w), A, (Wc, Hc),
                        flags=cv2.INTER_LANCZOS4, borderValue=0.0)
    wc = cv2.warpAffine(np.nan_to_num(w), A, (Wc, Hc),
                        flags=cv2.INTER_LINEAR, borderValue=0.0)
    bo = wc > 0.5
    dc = np.where(bo, dc / np.maximum(wc, 1e-6), 0.0)
    # ⛔ a resolució comuna: la Sony mostreja 1,49× més gruixut i sense
    # igualar-ho la correlació surt baixa per MOSTREIG, no per la dada
    sig = float(np.sqrt(max((escala_sony / escala_vixen) ** 2 - 1.0, 0.0)))
    dc = gaussian_filter(dc * bo, sig)
    yy = np.arange(Hc, dtype=np.float32)[:, None] - Hc / 2
    xx = np.arange(Wc, dtype=np.float32)[None, :] - Wc / 2
    rr = np.hypot(xx, yy) / C.R_SOL_PX
    ang = (np.degrees(np.arctan2(xx, -yy)) + 360.0) % 360.0
    out, inc = {}, {}
    for a, b in BANDES:
        m = bo & (ws > 0) & (rr >= a) & (rr < b)
        if m.sum() <= 20000:
            out[f"{a:.2f}-{b:.2f}"] = float("nan")
            inc[f"{a:.2f}-{b:.2f}"] = (np.full(36, np.nan), np.zeros(36))
            continue
        out[f"{a:.2f}-{b:.2f}"] = float(np.corrcoef(dc[m], ds[m])[0, 1])
        # ⛔ La correlació PER BLOC ANGULAR, desada sencera. La incertesa del Δ
        # es calcula després **APARELLADA**: referència i candidat es mesuren
        # als MATEIXOS sectors, o sigui que el seu error és comú i es cancel·la
        # a la diferència. Combinar-los com si fossin independents dona
        # σ(Δ) = ±0,032, que s'empassa tots els efectes i deixa la porta sense
        # dents —mesurat el 25-08-2026, i és un error meu que va durar deu
        # minuts perquè el número era absurd—.
        sec = (ang[m] / 10.0).astype(int) % 36
        # ⛔ En escala de FISHER, i amb el nombre de píxels de cada bloc. És la
        # manera estàndard de combinar correlacions, i cal: amb la mitjana crua
        # de les r el mateix candidat sortia +0,00057 per sectors i −0,00078 per
        # bandes, **signe contrari**. Una porta el veredicte de la qual depèn de
        # com s'agrega no és una porta.
        z_sec = np.full(36, np.nan); n_sec = np.zeros(36)
        for k in range(36):
            q = sec == k
            if q.sum() > 500:
                rk = np.corrcoef(dc[m][q], ds[m][q])[0, 1]
                z_sec[k] = np.arctanh(np.clip(rk, -0.999999, 0.999999))
                n_sec[k] = q.sum()
        inc[f"{a:.2f}-{b:.2f}"] = (z_sec, n_sec)
    return out, inc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sony", type=Path, required=True)
    ap.add_argument("--referencia", type=Path, required=True,
                    help="el producte SENSE la correcció que es vol jutjar")
    ap.add_argument("--candidat", type=Path, nargs="+", required=True)
    a = ap.parse_args()
    ds = np.load(a.sony / "DETALL_ln.npy")
    ws = np.load(a.sony / "PES.npy")
    ref, ref_inc = correlacions(a.referencia, ds, ws)
    print(f"{'':34s} " + "".join(f"{k:>13s}" for k in ref))
    print(f"  {'REFERÈNCIA':32s} " + "".join(f"{ref[k]:+13.4f}" for k in ref))
    for c in a.candidat:
        cor, c_inc = correlacions(c, ds, ws)
        g = P.porta_h4_jutge_creuat(ref, cor)
        # ⛔ Δ APARELLAT per sector: la diferència es fa DINS de cada bloc
        # angular, on l'error comú es cancel·la, i la incertesa surt de la
        # dispersió d'aquelles diferències.
        dz, pes_ = [], []
        for k in ref:
            zc, nc = c_inc[k]; zr, nr = ref_inc[k]
            q = np.isfinite(zc) & np.isfinite(zr) & (nc > 0)
            if q.sum() > 3:
                dz.append(zc[q] - zr[q]); pes_.append(np.minimum(nc[q], nr[q]))
        if dz:
            v = np.concatenate(dz); pw = np.concatenate(pes_)
            dm = float(np.sum(pw * v) / np.sum(pw))
            # error de la mitjana ponderada, des de la dispersió dels blocs
            var = float(np.sum(pw * (v - dm) ** 2) / np.sum(pw))
            n_ef = float(np.sum(pw) ** 2 / np.sum(pw ** 2))
            sig = float(np.sqrt(var / max(n_ef - 1, 1)))
        else:
            dm, sig = g["delta_mitja"], float("nan")
        ver = ("EMPAT" if not (abs(dm) > 2 * sig) else
               ("PASS" if dm > 0 else "FAIL"))
        print(f"  {c.name[:32]:32s} " + "".join(f"{cor[k]:+13.4f}" for k in cor)
              + f"   → {ver}  (Δz aparellat {dm:+.5f} ± {sig:.5f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
