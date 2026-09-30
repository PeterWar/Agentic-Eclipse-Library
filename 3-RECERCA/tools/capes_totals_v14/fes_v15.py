"""CapesTotalsV15 — la V14 amb el llenç estès i la capa dels 8 s de la Sony.

Encàrrec de Pere (28-08-2026): «fes la V15 basant-te en la V14 [amb la capa que
ell hi ha modificat], augmentant el tamany del llenç i afegint les imatges
stackejades per temps d'exposició de la Sony — les de 8 segons».

## Què s'hi fa, i què no

- **La V14 es conserva sencera i intacta**: els canals de píxels de les 12
  capes van byte a byte (inclosa la capa 01 que Pere ha modificat); l'únic que
  canvia és el rectangle de cada capa (+pad del llenç nou).
- **El llenç s'estén fins on arriba LA DADA dels dos fotogrames de 8 s**, no
  fins al llenç comú de la cadena: composem directament del RAW, o sigui que
  el retall del llenç comú no ens obliga. És la filosofia declarada del
  projecte («el llenç es declara sencer i generós, perquè la decisió quedi
  reversible»).
- **La capa nova és la recepta EXACTA de les capes LDIC del run**
  (`f4.psb_capes_ldic` del run 016_SONYTOT_CIENCIA): composició amb finestra
  de pes, màscara lunar PER FOTOGRAMA, coherència k, màscara de tres canals i
  el render declarat del run (pendent 0,22 · àncora 0,74 · terra 0,045 ·
  àncora L del seu F3). El cel NO es resta, com a les capes germanes.
- **Un sol re-mostreig**: del RAW de la Sony directament a la graella de la
  V15, amb la geometria composta dels dos runs (el llenç comú només és un marc
  intermedi de coordenades).

## La geometria, mesurada i no suposada

⛔ Els dos runs comparteixen el llenç comú (8096×8960, nord amunt, Sol al
centre, 2,1495 ″/px) però **cada tren hi entra amb la SEVA rotació**:
pa_north(VIXEN) = 57,195° i pa_north(SONY) = 90,27°. La diferència, 33,08°,
és la rotació Vixen↔Sony que la calibració del 17-08 ja donava (−33,2°).
El primer esbós d'aquest script suposava que compartien pa i la rotació «es
cancel·lava»: FALS, i és el motiu que la transformació es faci sempre en dos
passos amb els números de cada run.

    V15 → sensor Vixen:  sx = X − padx − 285 ; sy = Y − pady − 355
    sensor → llenç comú: d = A_vᵀ·(s − sol_vixen(572A2969))     [k_v = 1]
    llenç comú → RAW Sony: raw = A_s·(k_s·d) + sol_sony(fotograma)
    amb A = [[cos θ, sin θ], [−sin θ, cos θ]], θ = −pa_north de cada run,
    k_s = 2,1495/3,202 = 0,6713 (llenç → sensor Sony).

## Els dos fotogrames de 8 s

`DSC06987` (t = 37 s) i `DSC06993` (t = 70 s) — **un per apuntament** (el salt
de muntura de research/96 és entre ells). La DSC06990 (àncora 2, moguda) és
als inservibles i no entra. El registre dels dos és del MODEL de la cadena (la
correlació els refusa, normal a 8 s), o sigui que l'alineació amb la corona de
la V14 ES MESURA aquí (correlació al solapament 3-4,2 R☉) i, si cal, es
corregeix i es recompon. La Lluna s'emmascara per fotograma (w=0 al seu disc):
el forat lunar de la capa és TRANSPARENT i el disc de la V14 es veu a sota.
L'earthshine de veritat demana una pila registrada a la LLUNA (research/112
§7) i NO és aquesta capa.
"""
from __future__ import annotations

import json
import math
import os
import sys
import time

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v15")
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "encaix_sony"))   # psb_utils

V14 = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/"
       "Capes Totals/CapesTotalsV14.psd")
DST = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/"
       "Capes Totals/CapesTotalsV15.psb")
ARREL = os.path.expanduser("~/Desktop/Eclipse determinista/1-RUNS")
RUN_SONY = os.path.join(ARREL, "016_SONYTOT_CIENCIA_20260827T183356Z")
RUN_VIXEN = os.path.join(ARREL, "017_VIXEN_CIENCIA_20260827T193426Z")

SENSOR_A_V13 = (285.0, 355.0)
FRAMES_8S = ["DSC06987.ARW", "DSC06993.ARW"]
MARGE_PX = 8


class Geo:
    """La transformació V15 ↔ RAW Sony, amb els números dels DOS runs."""

    def __init__(g, padx: float = 0.0, pady: float = 0.0):
        Fv = json.load(open(os.path.join(RUN_VIXEN, "4-rebuts", "F1.2_sol_llenc.json")))
        F13v = json.load(open(os.path.join(RUN_VIXEN, "4-rebuts", "F1.3_registre.json")))
        Fs = json.load(open(os.path.join(RUN_SONY, "4-rebuts", "F1.2_sol_llenc.json")))
        g.LLv, g.LLs = Fv["llenc"], Fs["llenc"]
        assert (g.LLv["W"], g.LLv["H"]) == (g.LLs["W"], g.LLs["H"])
        g.CX, g.CY = g.LLv["W"] / 2.0, g.LLv["H"] / 2.0
        v = F13v["fotogrames"]["572A2969.CR3"]
        g.solv = (v["sol_x"], v["sol_y"])              # l'àncora del llenç V13/V14
        tv = math.radians(-g.LLv["pa_north_deg"])
        g.cav, g.sav = math.cos(tv), math.sin(tv)
        ts = math.radians(-g.LLs["pa_north_deg"])
        g.cas, g.sas = math.cos(ts), math.sin(ts)
        g.ks = g.LLs["escala_arcsec_px"] / g.LLs["escala_sensor_arcsec_px"]
        g.padx, g.pady = padx, pady

    def v15_a_comu(g, Xv, Yv):
        ux = Xv - g.padx - SENSOR_A_V13[0] - g.solv[0]
        uy = Yv - g.pady - SENSOR_A_V13[1] - g.solv[1]
        return (g.cav * ux - g.sav * uy), (g.sav * ux + g.cav * uy)   # dX, dY

    def comu_a_raw_sony(g, dX, dY, sol_f):
        dXs, dYs = dX * g.ks, dY * g.ks
        return (g.cas * dXs + g.sas * dYs + sol_f[0],
                -g.sas * dXs + g.cas * dYs + sol_f[1])

    def raw_sony_a_v15(g, rx, ry, sol_f):
        usx, usy = rx - sol_f[0], ry - sol_f[1]
        dX = (g.cas * usx - g.sas * usy) / g.ks
        dY = (g.sas * usx + g.cas * usy) / g.ks
        sx = g.cav * dX + g.sav * dY + g.solv[0]
        sy = -g.sav * dX + g.cav * dY + g.solv[1]
        return (sx + SENSOR_A_V13[0] + g.padx, sy + SENSOR_A_V13[1] + g.pady)

    def sol_v15(g):
        return (g.solv[0] + SENSOR_A_V13[0] + g.padx,
                g.solv[1] + SENSOR_A_V13[1] + g.pady)


def carrega_sony():
    sys.path.insert(0, os.path.join(RUN_SONY, "codi"))
    import comu, f2                                    # noqa: E402
    run = comu.Run.obre(RUN_SONY)
    ctx = f2.Ctx(run)
    S13 = run.llegeix_rebut("F1.3_registre.json")["fotogrames"]
    K = run.llegeix_rebut("F2.2_coherencia.json")["k"]
    va = run.llegeix_rebut("F3_filtres.json")["corba_to"]["valor_ancora_L"]
    return comu, f2, run, ctx, S13, K, va


def llenc_nou(geo: Geo, ctx, S13) -> tuple[int, int, int, int]:
    """El llenç que conté la V14 sencera i TOTA la dada dels dos 8 s."""
    xs, ys = [0.0, 7648.0], [0.0, 5353.0]
    g = ctx.g
    cantons = [(g.marge_esq + 2, g.marge_dalt + 2),
               (g.ample - g.marge_dreta - 2, g.marge_dalt + 2),
               (g.marge_esq + 2, g.alt - g.marge_baix - 2),
               (g.ample - g.marge_dreta - 2, g.alt - g.marge_baix - 2)]
    for n in FRAMES_8S:
        sol = (S13[n]["sol_x"], S13[n]["sol_y"])
        for (rx, ry) in cantons:
            x, y = geo.raw_sony_a_v15(rx, ry, sol)
            xs.append(x); ys.append(y)
    x0 = int(math.floor(min(xs))) - MARGE_PX
    y0 = int(math.floor(min(ys))) - MARGE_PX
    x1 = int(math.ceil(max(xs))) + MARGE_PX
    y1 = int(math.ceil(max(ys))) + MARGE_PX
    padx, pady = -x0, -y0
    W = x1 - x0; H = y1 - y0
    W += (-W) % 4; H += (-H) % 4
    return W, H, padx, pady


def compon_8s(geo: Geo, comu, f2, ctx, S13, K, W: int, H: int,
              correccio=(0.0, 0.0), banda_files: int = 1024):
    """El compost LDIC dels 8 s a la graella V15, un sol re-mostreig.

    Rèplica de `f2.compon` amb les graelles pròpies. `correccio` (px del llenç
    comú) s'aplica al sol dels DOS fotogrames si la mesura contra la V14 en
    troba (comparteixen el biaix del model)."""
    num = {c: np.zeros((H, W), np.float32) for c in comu.CANALS}
    den = {c: np.zeros((H, W), np.float32) for c in comu.CANALS}
    t0 = time.time()
    for n in FRAMES_8S:
        v = S13[n]
        sol = (v["sol_x"] + correccio[0], v["sol_y"] + correccio[1])
        mlx = sol[0] + float(v["lluna_dx"]); mly = sol[1] + float(v["lluna_dy"])
        k = K.get(n, 1.0)
        plans = ctx.plans(n, v["exp"])
        for y0 in range(0, H, banda_files):
            y1 = min(H, y0 + banda_files)
            Xv, Yv = np.meshgrid(np.arange(W, dtype=np.float32),
                                 np.arange(y0, y1, dtype=np.float32))
            dX, dY = geo.v15_a_comu(Xv, Yv)
            del Xv, Yv
            rx, ry = geo.comu_a_raw_sony(dX, dY, sol)
            del dX, dY
            fll = np.clip((np.hypot(rx - mlx, ry - mly)
                           - (ctx.RL + f2.GUARDA_LLUNA_PX)) / f2.VORA_LLUNA_PX,
                          0.0, 1.0).astype(np.float32)
            for i, (pl, w) in plans.items():
                oy, ox = ctx.orig[i]
                mx = ((rx - ox) * 0.5).astype(np.float32)
                my = ((ry - oy) * 0.5).astype(np.float32)
                c = comu.CANALS[comu.IDX_CANAL[i]]
                num[c][y0:y1] += cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR,
                                           borderValue=0.0) * fll
                den[c][y0:y1] += cv2.remap(w, mx, my, cv2.INTER_LINEAR,
                                           borderValue=0.0) * fll
                del mx, my
            del rx, ry, fll
        print(f"    {n} compost  [{time.time()-t0:.0f}s]", flush=True)
    C = {c: np.where(den[c] > 0, num[c] / np.maximum(den[c], 1e-20),
                     np.nan).astype(np.float32) for c in comu.CANALS}
    del num
    return C, den


def mesura_contra_v14(C, geo: Geo, W: int, H: int, padx: int, pady: int):
    """El desplaçament del compost Sony contra la corona de la V14 (fusionada
    actual del fitxer, amb l'edició de Pere inclosa), al solapament 3,0-4,2 R☉.

    Retorna (dx, dy) en px del llenç V15 i la resposta."""
    from psd_tools import PSDImage
    st = PSDImage.open(V14).numpy()
    g14 = np.zeros((H, W), np.float32)
    g14[pady:pady + 5353, padx:padx + 7648] = st[..., 1]
    del st
    gs = np.where(np.isfinite(C["G"]), C["G"], 0.0)
    cx, cy = geo.sol_v15()
    RS = 455.5
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(xx - cx, yy - cy); del yy, xx
    zona = ((rad > 3.0 * RS) & (rad < 4.2 * RS)
            & (g14 > 0) & (gs > 0)).astype(np.float32)
    # log del lineal Sony perquè l'estructura pesi com a la V14 tonificada
    gl = np.where(gs > 0, np.log10(np.maximum(gs, 1e-9)), 0.0).astype(np.float32)
    a = (g14 - cv2.GaussianBlur(g14, (0, 0), 20)) * zona
    b = (gl - cv2.GaussianBlur(gl, (0, 0), 20)) * zona
    m = int(4.2 * RS) + 40
    x0, x1 = max(0, int(cx) - m), min(W, int(cx) + m)
    y0, y1 = max(0, int(cy) - m), min(H, int(cy) + m)
    (dx, dy), resp = cv2.phaseCorrelate(a[y0:y1, x0:x1].astype(np.float64),
                                        b[y0:y1, x0:x1].astype(np.float64))
    return (float(dx), float(dy)), float(resp)


def main():
    os.makedirs(CAU, exist_ok=True)
    print("[1/6] geometria dels dos runs")
    geo = Geo()
    print(f"    pa VIXEN {geo.LLv['pa_north_deg']:.3f}° · pa SONY "
          f"{geo.LLs['pa_north_deg']:.2f}° · k_s {geo.ks:.5f} · "
          f"sol(2969)=({geo.solv[0]:.2f}, {geo.solv[1]:.2f})")
    comu, f2, run, ctx, S13, K, va = carrega_sony()
    W, H, padx, pady = llenc_nou(geo, ctx, S13)
    geo.padx, geo.pady = float(padx), float(pady)
    print(f"    llenç nou {W}×{H} · pad ({padx}, {pady}) · "
          f"Sol a ({geo.sol_v15()[0]:.1f}, {geo.sol_v15()[1]:.1f})")

    print("[2/6] compost dels 8 s (primera passada)")
    C, den = compon_8s(geo, comu, f2, ctx, S13, K, W, H)

    print("[3/6] alineació contra la corona de la V14")
    (dx, dy), resp = mesura_contra_v14(C, geo, W, H, padx, pady)
    print(f"    desplaçament mesurat ({dx:+.2f}, {dy:+.2f}) px · resposta {resp:.3f}")
    correccio = (0.0, 0.0)
    if resp >= 0.03 and 0.3 < math.hypot(dx, dy) < 12.0:
        # el biaix és del MODEL dels dos fotogrames: es passa al marc del llenç
        # comú i s'aplica al sol dels dos. V15: la Sony s'ha de moure (+dx,+dy);
        # el sol al llenç comú es mou amb A_vᵀ (rotació V15→comú) i k_s·A_s
        # (comú→raw): tot dins de comu_a_raw via el sol del fotograma.
        ddX = geo.cav * dx - geo.sav * dy
        ddY = geo.sav * dx + geo.cav * dy
        ddx_raw = geo.cas * (ddX * geo.ks) + geo.sas * (ddY * geo.ks)
        ddy_raw = -geo.sas * (ddX * geo.ks) + geo.cas * (ddY * geo.ks)
        correccio = (ddx_raw, ddy_raw)
        print(f"    correcció aplicada al sol dels dos fotogrames: "
              f"({correccio[0]:+.2f}, {correccio[1]:+.2f}) px RAW Sony")
        C, den = compon_8s(geo, comu, f2, ctx, S13, K, W, H, correccio)
        (dx2, dy2), resp2 = mesura_contra_v14(C, geo, W, H, padx, pady)
        print(f"    residual ({dx2:+.2f}, {dy2:+.2f}) px · resposta {resp2:.3f}")
        residual = (dx2, dy2)
    else:
        residual = (dx, dy)
        print("    (per sota del llindar o resposta insuficient: no es corregeix)")

    print("[4/6] render i màscara (la recepta de les capes LDIC del run)")
    tres = np.ones((H, W), bool)
    for c in comu.CANALS:
        tres &= (den[c] > 0) & np.isfinite(C[c])
    rgb, ren = comu.render_visual(np.dstack([C[c] for c in comu.CANALS]),
                                  tres, va, run.matriu, run.color["guany"])
    dmax = max(float(np.nanmax(den["G"])), 1e-9)
    msk = np.where(tres, np.clip(den["G"] / dmax, 0.0, 1.0), 0.0).astype(np.float32)
    cx, cy = geo.sol_v15()
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(xx - cx, yy - cy); del yy, xx
    RS = 455.5
    col = comu.mesura_color(C, rad, tres, RS, radis=(3.0, 5.0, 8.0))
    rr = rad[msk > 0.5] / RS
    rang = (float(np.percentile(rr, 0.5)), float(np.percentile(rr, 99.5)))
    del rr
    nom = (f"13_8s_DSC06987+DSC06993_apilat2_SONY300 · LDIC run 016 · "
           f"dada {rang[0]:.2f}-{rang[1]:.2f} R☉")
    print(f"    «{nom}» · color: " + "; ".join(
        f"{k} R/G {v['R/G']:.2f} B/G {v['B/G']:.2f}" for k, v in col.items()))
    np.save(os.path.join(CAU, "sony8s_G_lineal.npy"), C["G"])
    np.save(os.path.join(CAU, "sony8s_den_G.npy"), den["G"])
    for c in comu.CANALS:
        del C[c]

    print("[5/6] el PSB: la V14 sencera + pad + la capa Sony a baix de tot")
    from psd_tools import PSDImage
    from psd_tools.constants import BlendMode, Compression
    from psd_tools.psd.image_data import ImageData
    from psb_utils import add_pixel_layer, finalize_lr16
    psd = PSDImage.open(V14)
    assert psd._record.header.channels == 4
    psd._record.header.version = 2          # PSB: el fitxer passarà de 2 GB
    psd._record.header.width = W
    psd._record.header.height = H
    # ⛔ LA TRAMPA DEL «NO COMPATIBLE» DE PSB (mesurada el 28-08 amb la V15
    #    refusada i bisecció amb el Photoshop de debò via ExtendScript):
    #    Photoshop escriu els blocs globals `cinf` i `FMsk` amb signatura
    #    `8B64` (longitud de 8 bytes) i `CAI `/`OCIO`/`GenI`/`Pat2` amb
    #    `8BIM` + 4 bytes; psd-tools els re-serialitza TOTS amb `8BIM`, i als
    #    que posa longitud de 8 bytes (cinf, FMsk) Photoshop hi llegeix 4 →
    #    es desalinea i refusa el fitxer sencer. A PSD v1 tot és de 4 bytes i
    #    per això la V14 s'obria. La cura: en re-serialitzar un document
    #    LLEGIT com a PSB, fora tots els blocs globals menys Lr16 i Mt16
    #    (són metadades de sessió que Photoshop regenera; comprovat que
    #    l'X2 sense ells obre amb les 12 capes senceres).
    tb = psd._record.layer_and_mask_information.tagged_blocks
    for k in list(tb.keys()):
        kb = k.value if hasattr(k, "value") else k
        if kb not in (b"Lr16", b"Mt16"):
            del tb[k]
            print(f"    fora el bloc global heretat {kb.decode(errors='replace')!r} "
                  "(vegeu la trampa de PSB al docstring)")
    for layer in psd:
        rec = layer._record
        rec.top += pady; rec.bottom += pady
        rec.left += padx; rec.right += padx
        md = rec.mask_data
        md.top += pady; md.bottom += pady
        md.left += padx; md.right += padx
    # la capa Sony, retallada a la seva dada, INSERIDA A BAIX DE TOT
    on = np.argwhere(msk > 0.002)
    by0, bx0 = np.maximum(on.min(axis=0) - 4, 0)
    by1, bx1 = np.minimum(on.max(axis=0) + 5, (H, W))
    del on
    rgb16 = np.clip(np.rint(rgb[by0:by1, bx0:bx1] * 65535.0), 0,
                    65535).astype(np.uint16)
    m8 = np.clip(np.rint(msk[by0:by1, bx0:bx1] * 255.0), 0, 255).astype(np.uint8)
    capa = add_pixel_layer(psd, rgb16, nom, top=int(by0), left=int(bx0),
                           mask8=m8, blend=BlendMode.NORMAL, opacity=255,
                           visible=True, compression=Compression.ZIP)
    psd.remove(capa)
    psd.insert(0, capa)
    finalize_lr16(psd)

    print("    fusionada nova (RGBA, matte blanc, RAW)…", flush=True)
    compost = np.zeros((H, W, 3), np.float32)
    alfa = np.zeros((H, W), np.float32)
    al = msk * 1.0
    compost = rgb * al[..., None]
    alfa = al.copy()
    del rgb, msk, al
    info14 = []
    src14 = PSDImage.open(V14)
    for layer in src14:
        arr = layer.numpy("color")
        import fes_v14_pere as FP
        mfull, _, _ = FP._decodifica_mascara(layer, 7648, 5353)
        x0, y0v, x1, y1v = layer.bbox
        pix = np.zeros((H, W, 3), np.float32)
        cob = np.zeros((H, W), np.float32)
        pix[y0v + pady:y1v + pady, x0 + padx:x1 + padx] = arr
        cob[y0v + pady:y1v + pady, x0 + padx:x1 + padx] = 1.0
        mm = np.zeros((H, W), np.float32)
        mm[pady:pady + 5353, padx:padx + 7648] = mfull
        a2 = mm * cob * (layer.opacity / 255.0)
        if layer.visible:
            compost = compost * (1.0 - a2[..., None]) + pix * a2[..., None]
            alfa = alfa + a2 * (1.0 - alfa)
        info14.append((layer.name, layer.bbox))
        del arr, mfull, pix, cob, mm, a2
    del src14
    rgbW = compost + (1.0 - alfa[..., None])
    plans = [np.clip(np.rint(rgbW[..., j] * 65535.0), 0, 65535)
             .astype(">u2").tobytes() for j in range(3)]
    plans.append(np.clip(np.rint(alfa * 65535.0), 0, 65535).astype(">u2").tobytes())
    idata = ImageData(compression=Compression.RAW)
    idata.set_data(plans, psd._record.header)
    psd._record.image_data = idata
    if getattr(psd, "_updated", False):
        psd._updated = False
    np.save(os.path.join(CAU, "compost_v15.npy"),
            np.clip(np.rint(compost * 65535.0), 0, 65535).astype(np.uint16))
    np.save(os.path.join(CAU, "alfa_v15.npy"),
            np.clip(np.rint(alfa * 255.0), 0, 255).astype(np.uint8))
    del compost, rgbW, plans

    print("    desant…", flush=True)
    t0 = time.time()
    psd.save(DST)
    print(f"    {DST} · {os.path.getsize(DST)/1e9:.2f} GB · {time.time()-t0:.0f} s")

    print("[6/6] obrible amb dos lectors + rebut de construcció")
    import subprocess
    p2 = PSDImage.open(DST)
    assert (p2.width, p2.height) == (W, H) and len(list(p2)) == 13, \
        f"reobre {p2.width}×{p2.height} amb {len(list(p2))} capes"
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", DST],
                       capture_output=True, text=True)
    txt = r.stdout + r.stderr
    if f"pixelWidth: {W}" not in txt or f"pixelHeight: {H}" not in txt:
        raise SystemExit("⛔ ImageIO no llegeix la fusionada del PSB:\n" + txt)
    print("    obrible ✓ (psd-tools + ImageIO)")
    rebut = {"v14": V14, "desti": DST, "llenc": [W, H], "pad": [padx, pady],
             "sol_v15": list(geo.sol_v15()), "fotogrames_8s": FRAMES_8S,
             "k_coherencia": {n: K.get(n, 1.0) for n in FRAMES_8S},
             "correccio_raw_sony_px": list(correccio),
             "residual_v14_px": list(residual),
             "render": ren, "color_lineal": col,
             "rang_dada_Rsol": rang, "nom_capa": nom,
             "capes_v14": [{"nom": n, "bbox_v14": list(b)} for n, b in info14],
             "bytes": os.path.getsize(DST)}
    json.dump(rebut, open(os.path.join(CAU, "rebut_v15.json"), "w"),
              indent=1, ensure_ascii=False)
    return rebut


if __name__ == "__main__":
    main()
