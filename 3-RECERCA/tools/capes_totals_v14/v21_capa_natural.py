"""V21 · la capa d'earthshine NATURAL (l'estil de DSC06987_cal, ordre de Pere).

Res de pedestal pintat ni fosca de limbe cosmètica: la capa és el DISC
LINEAL APILAT dels 11 fotogrames (vel de corona inclòs, gra real inclòs, la
mota del R6 emmascarada amb la Sony omplint), renderitzat amb la mateixa
cadena tonal que la capa Sony del muntatge, amb UN realç declarat:

    L' = L_lineal · (1 + A · E/nivell)

on E és l'estructura validada (r=0,887 amb LROC) i A l'amplificació de
contrast. El limbe és el de la dada; el gra és el de la dada.
"""
from __future__ import annotations
import json, math, os, sys
import numpy as np, cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v21")
CAU17 = os.path.join(AQUI, "cau_v17")
sys.path.insert(0, AQUI)
import fes_v15 as F15

MB = (6465.398680355321, 6752.632845814709)
RL = 455.5018189723177
A_REALC = 12.0          # amplificació de contrast de l'estructura, DECLARADA
COMPS = {
    "vixen10": (["572A2982", "572A2983", "572A2984"], [10., 10., 10.], "vixen"),
    "vixen2": (["572A2979", "572A2980", "572A2981"], [2., 2., 2.], "vixen"),
    "ap1": (["DSC06987", "DSC06984"], [8., 2.], "sony"),
    "ap2": (["DSC06993", "DSC06996", "DSC06999"], [8., 2., 2.], "sony"),
}


def main():
    md = json.load(open(f"{CAU}/lluna_sony_meta.json"))
    x0, y0, x1, y1 = md["bbox_canvas"]
    H, W = y1 - y0, x1 - x0
    yy = np.arange(y0, y1, dtype=np.float32)[:, None]
    xx = np.arange(x0, x1, dtype=np.float32)[None, :]
    rr = np.hypot(xx - MB[0], yy - MB[1]) / RL
    gs = np.array(json.load(open(f"{CAU}/lluna_parell.json"))["guany_sony_vixen"],
                  np.float32)
    reb = json.load(open(f"{CAU}/earthshine4_rebut.json"))
    Wc = reb["pesos"]

    # --- el disc LINEAL RGB apilat (pesos del rebut; mota emmascarada) ---
    P, T = {}, None
    for k, (fs, ts, tren) in COMPS.items():
        w = np.array(ts) / sum(ts)
        acc = None
        for f, wi in zip(fs, w):
            a = np.nan_to_num(np.load(f"{CAU}/lluna_{tren}_{f}_lineal.npy"))
            if tren == "vixen":
                a = a * gs[None, None, :]
            acc = a * wi if acc is None else acc + a * wi
        P[k] = acc
    yyq, xxq = np.mgrid[0:H, 0:W].astype(np.float32)
    dmota = np.hypot(xxq - 330.0, yyq - 528.0)
    Mmota = np.clip((dmota - 14.0) / 8.0, 0, 1).astype(np.float32)
    Wm = {k: (np.full((H, W), Wc[k], np.float32)
              * (Mmota if k.startswith("vixen") else 1.0)) for k in P}
    Tm = sum(Wm.values())
    L = (sum(P[k] * Wm[k][..., None] for k in P)
         / np.maximum(Tm, 1e-9)[..., None]).astype(np.float32)

    # --- el realç: multiplicar pel camp d'estructura validat ---
    # l'estructura del realç: la científica (r<0,85) + l'extensió de display
    # (0,85-0,975, mateix model del nucli, DECLARADA estètica)
    E = np.load(f"{CAU}/earthshine4_Gdisp.npy")
    niv = reb["nivell_disc"]
    # realç ple on hi ha ciència (r<0,85); a l'extensió de display el residu
    # de vel no és estructura lunar: realç reduït (×0,35) i fosa al limbe
    f_nucli = np.clip((0.88 - rr) / 0.03, 0, 1).astype(np.float32)
    f_vora = np.clip((0.965 - rr) / 0.02, 0, 1).astype(np.float32)
    fada = f_nucli + 0.35 * (1 - f_nucli) * f_vora
    realc = 1.0 + A_REALC * (E / niv) * fada
    Lr = L * realc[..., None]

    # --- render NATURAL: estirament lineal de finestra sobre el disc, en
    #     monocrom (G) — el mateix gest que fa Pere quan mira DSC06987_cal
    #     amb corbes; la cadena tonal de la corona aixafava el contrast del
    #     disc (pendent 0,17/dècada) i el tenyia amb la matriu
    G2 = Lr[..., 1]
    # el VEL DEL MODEL CIENTÍFIC (perfil radial + polinomi del nucli, que per
    # construcció NO absorbeix els mars) es comprimeix ×0,30 al display; el
    # residu — mars, cràters i gra — passa 1:1. DECLARAT (només display)
    from v21_earthshine_v4 import fes_neteja
    dnu4 = np.load(f"{CAU}/earthshine4_dnu.npy")
    tot4 = dnu4 | (rr >= 0)          # fes_neteja vol la cobertura: reconstruïm
    tot4 = np.load(f"{CAU}/earthshine4_dav.npy") | dnu4
    netd, dav = fes_neteja(tot4, rr, (H, W), r_aval=0.995)
    residu = netd(G2)
    vel_model = G2 - residu
    # ⛔ el walking noise (FPN del sensor caminat per la deriva lunar, 75-77°)
    #    viu a la banda fina del residu CRU: el display passa pel MATEIX
    #    filtre de Wiener mesurat que el producte científic (<4 px ×0,06 ·
    #    4-8 ×0,71 · ≥8 intacte) — el gra que quedi és el que té senyal
    fy = np.fft.fftfreq(H)[:, None]; fx = np.fft.rfftfreq(W)[None, :]
    lam = np.where(np.hypot(fy, fx) > 1e-9,
                   1.0 / np.maximum(np.hypot(fy, fx), 1e-9), 1e9)
    pl = np.log([2.0, 4.0, 8.0, 16.0, 32.0, 64.0])
    pg = np.array([0.06, 0.06, 0.71, 0.96, 0.995, 1.0])
    Gf = np.interp(np.log(np.clip(lam, 2.0, 64.0)), pl, pg).astype(np.float32)
    residu = np.fft.irfft2(np.fft.rfft2(residu) * Gf, s=residu.shape
                           ).astype(np.float32) * dav
    # el ringing del filtre al tall del disc s'esvaeix al limbe extrem
    residu *= np.clip((0.985 - rr) / 0.015, 0, 1).astype(np.float32)
    nivc = float(np.median(G2[rr < 0.5]))
    G2d = np.where(dav, nivc + 0.30 * (vel_model - nivc) + residu, G2)
    dins1 = rr < 0.85          # la finestra la mana el disc interior
    p1, p99 = np.percentile(G2d[dins1], 1), np.percentile(G2d[dins1], 99)
    lo = p1 - 0.30 * (p99 - p1)
    hi = p99 + 0.10 * (p99 - p1)
    g8 = ((G2d - lo) / max(hi - lo, 1e-9)).astype(np.float32)
    # compressió suau de llums i ombres (les vores del vel no cremen ni buiden)
    g8 = np.where(g8 > 0.80, 0.80 + 0.17 * np.tanh((g8 - 0.80) / 0.17), g8)
    g8 = np.where(g8 < 0.10, 0.10 - 0.09 * np.tanh((0.10 - g8) / 0.09), g8)
    g8 = np.clip(g8, 0, 1)
    rgb = np.dstack([g8, g8, g8])

    # --- màscara: el limbe de la DADA, fosa curta (com la capa del 28) ---
    m = np.clip(((0.9930) - rr) / 0.008, 0, 1).astype(np.float32)
    m = cv2.GaussianBlur(m, (0, 0), 1.2)
    px16 = np.clip(np.rint(rgb * 65535), 0, 65535).astype(np.uint16)
    msk = np.clip(np.rint(m * 65535), 0, 65535).astype(np.uint16)
    np.save(f"{CAU}/capa_nat_px.npy", px16)
    np.save(f"{CAU}/capa_nat_msk.npy", msk)
    dins = m > 0.5
    med = [float(np.median(rgb[..., c][dins])) for c in range(3)]
    json.dump({"pos": [int(y0), int(x0)], "amplificacio_contrast": A_REALC,
               "mediana_render_RGB": med,
               "render": "estirament lineal de finestra (monocrom G); "
                         "vel del model cientific (radial+poli del nucli) comprimit x0,30 (display, declarat); residu (mars, gra) 1:1",
               "contrast_estructura_final_pct":
                   float(100 * (1 + A_REALC) * reb["amplitud_pct"] / 100)},
              open(f"{CAU}/capa_nat_meta.json", "w"), indent=1)
    print(f"render: mediana RGB {['%.3f' % v for v in med]} · realç ×{A_REALC:g}"
          f" → contrast estructural ~{(1+A_REALC)*reb['amplitud_pct']:.1f} %")
    vis = rgb * m[..., None]
    cv2.imwrite("/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/"
                "423091c7-0adc-498a-80f4-99666c4274fa/scratchpad/capa_nat.png",
                (vis * 255).astype(np.uint8)[..., ::-1])


if __name__ == "__main__":
    main()
