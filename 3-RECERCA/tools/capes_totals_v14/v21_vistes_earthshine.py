"""Vistes de l'earthshine dels dos trens, i la comparació amb el mapa NASA."""
from __future__ import annotations
import json, os, sys
import numpy as np, cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
sys.path.insert(0, AQUI)
DEST = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/"
        "Capes Totals/CapesTotalsV21_vistes")


def norm(A, m, lo=1.0, hi=99.0):
    v = A[m]
    a, b = np.percentile(v, lo), np.percentile(v, hi)
    return np.clip((A - a) / max(b - a, 1e-9), 0, 1)


def main():
    os.makedirs(DEST, exist_ok=True)
    E = np.load(f"{CAU}/earthshine_producte.npy")
    dins = np.load(f"{CAU}/earthshine_producte_dins.npy")
    G = np.load(f"{CAU}/earthshine_lroc_render.npy")
    reb = json.load(open(f"{CAU}/earthshine_producte_rebut.json"))
    H, W = dins.shape
    m = cv2.erode(dins.astype(np.uint8), np.ones((25, 25), np.uint8)).astype(bool)
    nos = norm(cv2.GaussianBlur(E[..., 1], (0, 0), 6.0), m, 1.5, 98.5) * m
    lro = norm(cv2.GaussianBlur(G.astype(np.float32), (0, 0), 6.0), m, 1.5, 98.5) * m
    pan = np.zeros((H + 46, W * 2 + 12, 3), np.uint8)
    for i, (img, tit) in enumerate(((nos, "EARTHSHINE MESURAT · Vixen 3x10s + Sony >1s"),
                                    (lro, "MAPA LROC WAC (NASA) a l'orientacio de l'efemeride"))):
        z = (np.dstack([img] * 3) * 255).astype(np.uint8)
        pan[46:46 + H, i * (W + 12):i * (W + 12) + W] = z
        cv2.putText(pan, tit, (i * (W + 12) + 8, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.62, (255, 255, 255), 1, cv2.LINE_AA)
    r = reb["resultats"]["DOS TRENS · 8 fotogrames · producte"]
    cv2.putText(pan, f"r = {r['r']:+.3f}  (control nul {r['nul_mitjana']:+.3f} "
                     f"+/- {r['nul_sd']:.3f})  =  {r['z']:.1f} sigma",
                (8, H + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 1,
                cv2.LINE_AA)
    cv2.imwrite(f"{DEST}/V21_earthshine_dos_trens_vs_LROC.png", pan[..., ::-1])

    # cada component per separat
    md = json.load(open(f"{CAU}/lluna_sony_meta.json"))
    tires, tits = [], []
    for nom, fs, et in (("vixen", ["572A2982", "572A2983", "572A2984"], "VIXEN 3x10s"),
                        ("sony", ["DSC06987", "DSC06984"], "SONY apunt.1"),
                        ("sony", ["DSC06993", "DSC06996", "DSC06999"], "SONY apunt.2")):
        A = np.mean([np.nan_to_num(np.load(f"{CAU}/lluna_{nom}_{f}_lineal.npy"))[..., 1]
                     for f in fs], axis=0)
        tires.append(norm(cv2.GaussianBlur(A, (0, 0), 3.0), m, 0.5, 99.5) * m)
        tits.append(et)
    pan2 = np.zeros((H + 46, W * 3 + 24, 3), np.uint8)
    for i, (img, tit) in enumerate(zip(tires, tits)):
        z = (np.dstack([img] * 3) * 255).astype(np.uint8)
        pan2[46:46 + H, i * (W + 12):i * (W + 12) + W] = z
        cv2.putText(pan2, tit, (i * (W + 12) + 8, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.putText(pan2, "el disc tal com surt (vel de corona inclos) — el segon "
                      "apuntament de la Sony porta el vel gros",
                (8, H + 38), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 1,
                cv2.LINE_AA)
    cv2.imwrite(f"{DEST}/V21_earthshine_discs_per_tren.png", pan2[..., ::-1])
    print("vistes:", DEST)
    for f in sorted(os.listdir(DEST)):
        print("  ", f)


if __name__ == "__main__":
    main()
