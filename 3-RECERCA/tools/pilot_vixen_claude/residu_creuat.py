"""El que NO comparteixen els dos trens: per construcció, això no pot ser cel.

## ⛔ Per què aquesta mesura mana sobre totes les altres

Els dos trens miren la mateixa corona amb una altra òptica, un altre sensor, un
altre fosc, un altre flat, una altra escala d'exposicions i unes altres fronteres
de fusió. **Tot el que coincideix als dos és cel**; tot el que no, és d'un dels
dos instruments o de la cadena que l'ha processat.

O sigui que el residu creuat **és el jutge de la NORMA ZERO sense cap model
nostre pel mig**: el criteri —«ho comparteixen els dos trens?»— no depèn de cap
llindar ni de cap suposició.

Mesurat el 25-08-2026: els dos trens coincideixen amb coherència **0,977-0,999**
per damunt de λ ≈ 100 px i **deixen de coincidir per sota de λ ≈ 31 px** (0,04 a
0,70 a λ = 14-24 px). Aquell desacord val el **8,34 %** de la potència del
detall, i és l'única cosa mesurable que no és cel.

## ⚠️ El que aquesta mesura NO pot dir

Que una cosa no la comparteixin els dos trens **no vol dir que sigui un
artefacte**: també hi cau el soroll, que per definició no es comparteix. Per això
el producte porta al costat el **mapa de soroll esperat** de cada tren: el que
importa és el residu que **passa del soroll**.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import comu as C  # noqa: E402
import filtres_druckmuller as FD  # noqa: E402


def al_llenc_comu(x: np.ndarray, w: np.ndarray, forma) -> tuple[np.ndarray, np.ndarray]:
    """Porta un producte de la Vixen al llenç comú, ponderat.

    ⛔ Exactament la mateixa afí que fa servir `fase_dos_trens_filtrats`: si se'n
    fes servir una altra, el residu creuat mesuraria el desregistre i no la dada.
    """
    import cv2
    H, W = x.shape
    Hc, Wc = forma
    A = C.afi((W / 2.0, H / 2.0), (Wc / 2.0, Hc / 2.0))
    xw = cv2.warpAffine(np.nan_to_num(x).astype(np.float32) * w, A, (Wc, Hc),
                        flags=cv2.INTER_LANCZOS4, borderValue=0.0)
    ww = cv2.warpAffine(w.astype(np.float32), A, (Wc, Hc),
                        flags=cv2.INTER_LINEAR, borderValue=0.0)
    bo = ww > 0.5
    return np.where(bo, xw / np.maximum(ww, 1e-6), 0.0).astype(np.float32), bo


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vixen", type=Path, required=True, help="dir amb DETALL_ln.npy i PES.npy")
    ap.add_argument("--sony", type=Path, required=True)
    ap.add_argument("--sortida", type=Path, required=True)
    ap.add_argument("--lambda-max", type=float, default=31.0,
                    help="només les escales per sota d'aquesta λ, en px de llenç")
    ap.add_argument("--radi-max", type=float, default=4.5)
    a = ap.parse_args()

    ds = np.load(a.sony / "DETALL_ln.npy", mmap_mode="r")
    ws = np.load(a.sony / "PES.npy", mmap_mode="r")
    Hc, Wc = ds.shape
    dv_p = np.load(a.vixen / "DETALL_ln.npy")
    wv_p = np.load(a.vixen / "PES.npy")
    print(f"Sony {Wc}×{Hc}  ·  Vixen {dv_p.shape[1]}×{dv_p.shape[0]} → llenç comú")
    dvc, bo_v = al_llenc_comu(dv_p, (wv_p > 0).astype(np.float32), (Hc, Wc))
    del dv_p, wv_p

    m = int(round(a.radi_max * C.R_SOL_PX))
    cy, cx = Hc // 2, Wc // 2
    sl = (slice(max(0, cy - m), min(Hc, cy + m)), slice(max(0, cx - m), min(Wc, cx + m)))
    V = dvc[sl].astype(np.float32)
    S = np.asarray(ds[sl], np.float32)
    bo = bo_v[sl] & (np.asarray(ws[sl]) > 0) & np.isfinite(V) & np.isfinite(S)
    del dvc, bo_v
    h, w = V.shape
    yy = (np.arange(h, dtype=np.float32)[:, None] + sl[0].start - cy)
    xx = (np.arange(w, dtype=np.float32)[None, :] + sl[1].start - cx)
    rr = (np.hypot(xx, yy) / C.R_SOL_PX).astype(np.float32)
    pes = bo.astype(np.float32)
    print(f"  retall {w}×{h}  ·  {100*bo.mean():.1f} % amb dada als DOS trens")

    # ⛔ passa-alt amb pes: σ = λ/2π és el que deixa passar per sota de λ
    sig = a.lambda_max / (2.0 * np.pi)
    Vh, _ = FD.passa_alt(V, pes, sig)
    Sh, _ = FD.passa_alt(S, pes, sig)
    Vh = np.where(bo, Vh, 0.0); Sh = np.where(bo, Sh, 0.0)

    # ⛔ UN sol escalar de guany, global. Res angular ni radial: amb graus de
    # llibertat espacials l'acord entre trens se l'imposa un mateix (mesurat el
    # 23-08: de 4 a 120 paràmetres el residu millora dins i empitjora fora).
    vv, ss = Vh[bo], Sh[bo]
    g = float(np.dot(vv, ss) / max(np.dot(ss, ss), 1e-30))
    R = np.where(bo, Vh - np.float32(g) * Sh, 0.0).astype(np.float32)
    r_v = float(np.std(vv)); r_s = float(np.std(ss)); r_r = float(np.std(R[bo]))
    coh = float(np.dot(vv, ss) / max(np.sqrt(np.dot(vv, vv) * np.dot(ss, ss)), 1e-30))
    print(f"  λ ≤ {a.lambda_max:.0f} px  ·  guany Sony→Vixen {g:.4f}  ·  correlació {coh:.4f}")
    print(f"  rms  Vixen {r_v:.6f}   Sony {r_s:.6f}   RESIDU {r_r:.6f} "
          f"({100*r_r/max(r_v,1e-30):.1f} % del de la Vixen)")

    # quant del residu és circular, i quant per anell
    import filtres as F
    circ = F.rms_circular(R, pes, rr, r0=1.05, r1=a.radi_max, pas_r=0.01)
    print(f"  component circular del residu: {100*circ['rms_circular']/max(circ['rms_detall'],1e-30):.2f} %")

    perfil = []
    for r0 in np.arange(1.1, a.radi_max, 0.2):
        sel = bo & (rr >= r0) & (rr < r0 + 0.2)
        if sel.sum() > 5000:
            perfil.append({"r": round(float(r0 + 0.1), 2),
                           "rms_residu": float(np.std(R[sel])),
                           "rms_vixen": float(np.std(Vh[sel])),
                           "fraccio": float(np.std(R[sel]) / max(np.std(Vh[sel]), 1e-30))})
    print("\n   r (R☉)   rms residu   rms Vixen   residu/Vixen")
    for p in perfil:
        print(f"    {p['r']:5.2f}    {p['rms_residu']:.6f}    {p['rms_vixen']:.6f}    {p['fraccio']:6.2f}")

    a.sortida.mkdir(parents=True, exist_ok=True)
    np.save(a.sortida / "RESIDU_CREUAT.npy", R)
    np.save(a.sortida / "PES.npy", pes)
    import cv2
    for nom, img in (("residu", R), ("vixen", Vh), ("sony", Sh)):
        v = img[bo]
        lo, hi = np.percentile(v, [0.5, 99.5])
        q = np.clip((img - lo) / max(hi - lo, 1e-30), 0, 1)
        q = np.where(bo, q, 0.5)
        cv2.imwrite(str(a.sortida / f"{nom}.png"),
                    (cv2.resize(q, (1400, 1400), interpolation=cv2.INTER_AREA) * 255).astype(np.uint8))
    C.desa_json(a.sortida / "residu_creuat.json",
                {"lambda_max_px": a.lambda_max, "sigma_px": sig, "guany": g,
                 "correlacio": coh, "rms_vixen": r_v, "rms_sony": r_s,
                 "rms_residu": r_r, "fraccio_no_compartida": r_r / max(r_v, 1e-30),
                 "component_circular_del_residu": circ, "perfil": perfil,
                 "retall": [int(w), int(h)], "radi_max_rsol": a.radi_max})
    print(f"\n  → {a.sortida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
