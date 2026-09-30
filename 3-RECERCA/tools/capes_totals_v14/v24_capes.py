"""V24 · les dues capes noves (ordre de Pere, 01-09):

  · EARTHSHINE al TO del DSC06984.psb: la mateixa estructura validada, amb el
    disc a mediana ~0,10 (fosc, neutre-càlid com el seu revelat) — la Lluna
    s'insinua, no crida.
  · REFLEX de la flamarada: la llum vermella reflectida a la lent sobre el
    limbe NW, EXTRETA del PSB de Pere (revelat del RAW DSC06984) i portada al
    marc del disc amb la geometria disc→disc mesurada (escala pel quocient de
    radis fotogràfics, rotació sensor→llenç −44,0° mesurada a la V22).
    Additiva (Linear Dodge): llum sobre la Lluna fosca, res tapat.
"""
from __future__ import annotations
import json, math, os
import numpy as np, cv2

CAU = "cau_v21"
SCR = ("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/"
       "423091c7-0adc-498a-80f4-99666c4274fa/scratchpad")
CXT = CYT = 495.8                 # centre del disc dins la tessel·la (991×991)
R_MARC = 453.5
TO = (0.1036, 0.0983, 0.0981)     # mediana del disc al DSC06984.psb
ROT = math.radians(-44.0)          # sensor Sony → marc (mesurada, V22: 316°)


def main():
    # --- capa EARTHSHINE al to fosc ---
    E = np.load(f"{CAU}/capa_nat_px.npy").astype(np.float32) / 65535.0
    g = E[..., 0]
    yy, xx = np.mgrid[0:991, 0:991].astype(np.float32)
    rr = np.hypot(xx - CXT, yy - CYT)
    dins = rr < R_MARC * 0.9
    med = float(np.median(g[dins]))
    p10, p90 = np.percentile(g[dins], 10), np.percentile(g[dins], 90)
    # el rang p10-p90 del disc del PSB de Pere és ~0,09→0,13: contrast suau
    k = 0.045 / max(p90 - p10, 1e-9)
    out = np.zeros_like(E)
    for c in range(3):
        out[..., c] = np.clip(TO[c] + (g - med) * k, 0, 1)
    np.save(f"{CAU}/capa_fosca_px.npy",
            np.clip(np.rint(out * 65535), 0, 65535).astype(np.uint16))
    d2 = rr < R_MARC * 0.85
    print(f"earthshine fosca: mediana RGB "
          f"{[round(float(np.median(out[...,c][d2])),3) for c in range(3)]} "
          f"(objectiu {TO}) · k={k:.3f}")

    # --- capa REFLEX + GLOW del fotograma, amb la CADENA GEOMÈTRICA EXACTA ---
    #     (la mateixa que l'apilat: marc lunar → RAW del DSC06984; el PSB de
    #      Pere és el revelat del RAW amb un retall de (+8,5, +7,7) px mesurat)
    import sys
    sys.path.insert(0, ".")
    import fes_v15 as F15
    import fes_v17 as F17
    from v21_apilats import carrega_fits
    rgb = np.load(f"{SCR}/d84_rgb.npy")
    geo = json.load(open(f"{CAU}/d84_geo.json"))
    OFF = geo["off"]                       # PSB→RAW
    md = json.load(open(f"{CAU}/lluna_sony_meta.json"))
    x0, y0, x1, y1 = md["bbox_canvas"]
    MB = (6465.398680355321, 6752.632845814709)
    sv = F17.SV16(); geo15 = F15.Geo(padx=3387.0, pady=5109.0)
    comu, f2, run, ctx, S13, K, va = F15.carrega_sony()
    fits = carrega_fits()
    Xv, Yv = np.meshgrid(np.arange(x0, x1, dtype=np.float32),
                         np.arange(y0, y1, dtype=np.float32))
    x15, y15 = sv.enrere(Xv, Yv)
    vb = S13["DSC06993.ARW"]
    solb = np.array([vb["sol_x"], vb["sol_y"]])
    Mb = np.array([vb["sol_x"] + vb["lluna_dx"], vb["sol_y"] + vb["lluna_dy"]])
    dX, dY = geo15.v15_a_comu(x15, y15)
    rbx, rby = geo15.comu_a_raw_sony(dX, dY, solb)
    v84 = S13["DSC06984.ARW"]
    Mn = np.array([v84["sol_x"] + v84["lluna_dx"], v84["sol_y"] + v84["lluna_dy"]])
    th, _ = fits["DSC06984.ARW"]
    ca, sa = math.cos(th), math.sin(th)
    ux2 = rbx - Mb[0]; uy2 = rby - Mb[1]
    rxr = (ca * ux2 + sa * uy2 + Mn[0]).astype(np.float32)
    ryr = (-sa * ux2 + ca * uy2 + Mn[1]).astype(np.float32)
    # la tessel·la V22+ està reescalada ×0,9956 al voltant del centre: desfem-ho
    S22 = 453.5 / 455.5018189723177
    rxr = cv2.resize(rxr, None, fx=1, fy=1)      # (cap canvi de graella)
    ux3 = (xx - CXT) / S22 + (MB[0] - x0) - (MB[0] - x0)  # placeholder
    # mapa marc(tessel·la reescalada) → marc(original) → RAW:
    gx = (CXT + (xx - CXT) / S22).astype(np.float32)
    gy = (CYT + (yy - CYT) / S22).astype(np.float32)
    RXX = cv2.remap(rxr, gx + (496.3987 - CXT), gy + (495.6328 - CYT),
                    cv2.INTER_LINEAR, borderValue=-1)
    RYY = cv2.remap(ryr, gx + (496.3987 - CXT), gy + (495.6328 - CYT),
                    cv2.INTER_LINEAR, borderValue=-1)
    mx = (RXX - OFF[0]).astype(np.float32)       # RAW → PSB
    my = (RYY - OFF[1]).astype(np.float32)
    T = np.dstack([cv2.remap(rgb[..., c], mx, my, cv2.INTER_LINEAR,
                             borderValue=0) for c in range(3)])
    # additiu: TOT l'excés de llum del fotograma dins del disc (glow + reflex)
    fons = np.array([np.median(T[..., c][d2]) for c in range(3)], np.float32)
    dinsD = (rr < R_MARC * 1.001).astype(np.float32)
    vora = np.clip((R_MARC - rr) / 3.0, 0, 1)
    add = np.clip(T - fons[None, None, :], 0, 1) * (dinsD * vora)[..., None]
    croma = T[..., 0] - 0.5 * (T[..., 1] + T[..., 2])
    mrf = (croma > 0.05) & (rr < R_MARC)
    if mrf.sum() > 100:
        ys2, xs2 = np.where(mrf)
        print(f"reflex vermell: {int(mrf.sum())} px · centre tessel·la "
              f"({xs2.mean():.0f},{ys2.mean():.0f}) · azimut "
              f"{math.degrees(math.atan2(ys2.mean()-CYT, xs2.mean()-CXT)):+.0f}°")
    np.save(f"{CAU}/capa_reflex_px.npy",
            np.clip(np.rint(add * 65535), 0, 65535).astype(np.uint16))
    np.save(f"{CAU}/capa_reflex_msk.npy",
            np.full((991, 991), 65535, np.uint16))
    json.dump({"geometria": "cadena exacta del run (marc→RAW DSC06984) + "
                             "offset PSB (+8,5,+7,7)",
               "to_objectiu": TO, "k_contrast": float(k)},
              open(f"{CAU}/v24_meta.json", "w"), indent=1)
    # vista de control: la Lluna fosca + reflex additiu
    vis = out + add
    msk = np.load(f"{CAU}/capa_nat_msk.npy").astype(np.float32) / 65535.0
    v8 = np.clip(vis * msk[..., None] * 2.2, 0, 1)   # ×2,2 només per VEURE-la
    cv2.imwrite(f"{SCR}/v24_lluna_reflex.png",
                (v8 * 255).astype(np.uint8)[..., ::-1])
    print("vista de control escrita (aclarida ×2,2 només per inspecció)")


if __name__ == "__main__":
    main()
