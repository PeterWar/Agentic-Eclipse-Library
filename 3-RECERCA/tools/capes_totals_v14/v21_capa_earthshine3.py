"""V21 · la capa d'earthshine: monocroma, disc sencer, amplificació declarada."""
from __future__ import annotations
import json, os, sys
import numpy as np, cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
MB = (6465.398680355321, 6752.632845814709)
RL = 455.5018189723177
PEDESTAL = 0.42
SIG_VIS = 0.11         # desviació visual objectiu de l'estructura
SUAU = 2.5


def main():
    E = np.load(f"{CAU}/earthshine2_G.npy")
    fit = np.load(f"{CAU}/earthshine2_fit.npy")
    reb = json.load(open(f"{CAU}/earthshine2_rebut.json"))
    md = json.load(open(f"{CAU}/lluna_sony_meta.json"))
    x0, y0, x1, y1 = md["bbox_canvas"]
    h, w = fit.shape
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    rr = np.hypot(xx - MB[0], yy - MB[1]) / RL

    Es = cv2.GaussianBlur(E, (0, 0), SUAU)
    mer = cv2.erode((fit & (rr < 0.88)).astype(np.uint8),
                    np.ones((17, 17), np.uint8)).astype(bool)
    sg = float(Es[mer].std())
    # l'amplificació de contrast real que això implica, DECLARADA
    ampl = SIG_VIS / (sg / reb["nivell_disc"]) / PEDESTAL
    print(f"σ estructura {sg:.2f} comptes · contrast real "
          f"{100*sg/reb['nivell_disc']:.3f} % · amplificació de contrast "
          f"×{ampl:.0f}")
    # l'estructura amplificada s'esvaeix on el vel residual mana (0,92→0,96),
    # i els extrems es comprimeixen suaument (tanh a ±2,5σ): els arcs de
    # residu del limbe no cremen i cap mar real no es toca (són ≤2σ)
    fada = np.clip((0.96 - rr) / 0.04, 0, 1).astype(np.float32)
    x = Es / sg
    xc = 2.5 * np.tanh(x / 2.5)
    # fosca de limbe suau del PEDESTAL (display, declarada): l'anell exterior
    # deixa de ser un cèrcol pla
    limb = 1.0 - 0.22 * np.clip((rr - 0.85) / 0.15, 0, 1) ** 1.5
    v = PEDESTAL * limb * (1.0 + (SIG_VIS / PEDESTAL) * xc * fada)
    px16 = np.clip(np.rint(np.clip(v, 0, 1) * 65535), 0, 65535).astype(np.uint16)
    px = np.dstack([px16, px16, px16])            # MONOCROM: cap color fabricat
    # màscara: el disc sencer fins al limbe (fosa 0,985 → 1,0)
    m = np.clip((0.9975 - rr) / 0.0125, 0, 1).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 1.5)
    msk = np.clip(np.rint(m * 65535), 0, 65535).astype(np.uint16)
    ys, xs = np.where(m > 0.5)
    print(f"radi visible: {np.hypot(xs-(MB[0]-x0), ys-(MB[1]-y0)).max():.0f} px "
          f"(el disc del muntatge: {RL:.0f})")
    np.save(f"{CAU}/capa_es3_px.npy", px)
    np.save(f"{CAU}/capa_es3_msk.npy", msk)
    json.dump({"pos": [int(y0), int(x0)], "pedestal": PEDESTAL,
               "compressio": "tanh ±2,5σ", "fosca_limbe_display": 0.22,
               "sig_vis": SIG_VIS, "suau_px": SUAU,
               "amplificacio_contrast": float(ampl),
               "contrast_real_pct": 100 * sg / reb["nivell_disc"]},
              open(f"{CAU}/capa_es3_meta.json", "w"), indent=1)
    vis = (px.astype(np.float32) / 65535.0) * (msk.astype(np.float32) / 65535.0)[..., None]
    cv2.imwrite("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/"
                "423091c7-0adc-498a-80f4-99666c4274fa/scratchpad/capa3_vista.png",
                (np.clip(vis, 0, 1) * 255).astype(np.uint8)[..., ::-1])
    zx, zy = int(MB[0] - x0), int(MB[1] - y0)
    z = vis[zy - 180:zy + 180, zx - 180:zx + 180]
    cv2.imwrite("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/"
                "423091c7-0adc-498a-80f4-99666c4274fa/scratchpad/capa3_zoom.png",
                (np.clip(z, 0, 1) * 255).astype(np.uint8)[..., ::-1])


if __name__ == "__main__":
    main()
