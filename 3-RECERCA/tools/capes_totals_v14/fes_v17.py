"""CapesTotalsV17 — la V16 de Pere amb l'apilat Sony >1 s, WB ajustat i el limbe de la 09 net.

Encàrrec de Pere (28-08-2026, migdia), sobre la SEVA V16 (re-escenificació completa:
llenç 12415×12095, capes Vixen rotades ~10,9°, Lluna prop del mig, la capa Sony a
DALT de les Vixen i les capes 08-01 apagades):

1. **capa 09** (1/60 s): repassar el limbe lunar a la màscara («hi estic introduint
   artefactes») — mesurat: la seva màscara entra 2-10 % dins del disc i el seu
   contingut hi és bloom → el mateix vel de sempre. Cura de la V14: màscara ×
   fora(disc PROPI mesurat al contingut de la 09 a la V16: centre (6480,13,
   6756,00), R 452,39, rampa [R+0,5, R+3,5]);
2. **capa 13**: substituir l'apilat de 8 s per **TOTS els fotogrames de més d'1 s**
   del run 016 (2 s: DSC06984/06996/06999 · 8 s: DSC06987/06993 — els dos
   apuntaments), per «rascar» més corona externa. Es compon del RAW directament a
   la graella de la V16 (UN re-mostreig; la capa que Pere havia transformat a mà en
   duia dos) i **alineat per construcció amb la SEVA corona Vixen**: la
   transformació V15→V16 s'ha mesurat sobre les capes Vixen (θ=10,880°, translació
   mesurada, resposta 1,04) i es compon a través d'ella;
3. **balanç de blancs i nivell** ajustats PER MESURA contra la fusionada de la V16
   (el compost visible de Pere: capes 12+11+10+09) a l'anell de solapament, iterant
   guanys lineals per canal i l'àncora del render; i **màscara de desenfoc gaussià**:
   rampa radial centrada al Sol entre on la Vixen visible s'acaba i on l'apilat és
   sòlid, desenfocada σ=120 px (la lliçó d'Astrofalls: tot anell és subblur).

⛔ Les regles apreses que s'hi apliquen: blocs globals heretats FORA en re-serialitzar
(la trampa 8BIM/8B64 de PSB), màscares a 16 bits pel canal cru (mai topil), round-trip
de cada canal editat, i CAP lliurament sense `porta_photoshop.sh`.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
import time

import numpy as np
import cv2

AQUI = os.path.dirname(os.path.abspath(__file__))
CAU = os.path.join(AQUI, "cau_v17")
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "encaix_sony"))
sys.path.insert(0, AQUI)

import fes_v15 as F15
import fes_v14_pere as FP

B = "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/"
V16 = B + "CapesTotalsV16.psb"
DST = B + "CapesTotalsV17.psb"

FRAMES_MES1S = ["DSC06984.ARW", "DSC06996.ARW", "DSC06999.ARW",
                "DSC06987.ARW", "DSC06993.ARW"]
RS = 455.5
RAMPA_BLEND_RSOL = (1.75, 2.15)     # on la Vixen visible (09, dada fins a 2,31) cedeix
SIGMA_BLEND_PX = 120.0
RAMPA_LIMBE = (0.5, 3.5)            # px fora del limbe, com a la V14


class SV16:
    """La transformació mesurada V15 → V16 (rotació + translació, escala 1)."""

    def __init__(s):
        mes = json.load(open(os.path.join(CAU, "mesures_v16.json")))
        S = mes["S_v15_a_v16"]
        th = math.radians(S["theta_deg"])
        # convenció de cv2.getRotationMatrix2D: p' = Rcv·(p−c) + c + t,
        # Rcv = [[cos, sin], [−sin, cos]]
        s.ca, s.sa = math.cos(th), math.sin(th)
        s.c = np.array(S["centre_rotacio_v15"], float)
        s.t = np.array(S["translacio"], float)
        s.lluna09 = mes["lluna_09_v16"]
        s.W16, s.H16 = mes["W16"], mes["H16"]

    def endavant(s, x15, y15):
        dx, dy = x15 - s.c[0], y15 - s.c[1]
        return (s.ca * dx + s.sa * dy + s.c[0] + s.t[0],
                -s.sa * dx + s.ca * dy + s.c[1] + s.t[1])

    def enrere(s, x16, y16):
        ux, uy = x16 - s.c[0] - s.t[0], y16 - s.c[1] - s.t[1]
        return (s.ca * ux - s.sa * uy + s.c[0],
                s.sa * ux + s.ca * uy + s.c[1])


def compon_mes1s(sv: SV16, geo15, comu, f2, ctx, S13, K,
                 correccio=(0.0, 0.0), banda_files=1024):
    """Tots els >1 s, del RAW a la graella V16, un re-mostreig, recepta LDIC."""
    W, H = sv.W16, sv.H16
    num = {c: np.zeros((H, W), np.float32) for c in comu.CANALS}
    den = {c: np.zeros((H, W), np.float32) for c in comu.CANALS}
    t0 = time.time()
    for n in FRAMES_MES1S:
        v = S13[n]
        sol = (v["sol_x"] + correccio[0], v["sol_y"] + correccio[1])
        mlx = sol[0] + float(v["lluna_dx"]); mly = sol[1] + float(v["lluna_dy"])
        k = K.get(n, 1.0)
        plans = ctx.plans(n, v["exp"])
        for y0 in range(0, H, banda_files):
            y1 = min(H, y0 + banda_files)
            Xv, Yv = np.meshgrid(np.arange(W, dtype=np.float32),
                                 np.arange(y0, y1, dtype=np.float32))
            x15, y15 = sv.enrere(Xv, Yv)
            del Xv, Yv
            dX, dY = geo15.v15_a_comu(x15, y15)
            del x15, y15
            rx, ry = geo15.comu_a_raw_sony(dX, dY, sol)
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
        print(f"    {n} ({S13[n]['exp']:g} s) compost  [{time.time()-t0:.0f}s]",
              flush=True)
    C = {c: np.where(den[c] > 0, num[c] / np.maximum(den[c], 1e-20),
                     np.nan).astype(np.float32) for c in comu.CANALS}
    del num
    return C, den


def mesura_seam(rgb_meu, rgb09, sol16, rin=2.15, rout=2.60):
    """Nivell i color (medianes per canal) del CONTINGUT de la capa 01 de Pere
    (10,3 s: la seva corona externa) i del meu render, al mateix anell."""
    H, W = rgb_meu.shape[:2]
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    rad = np.hypot(xx - sol16[0], yy - sol16[1])
    z = ((rad > rin * RS) & (rad < rout * RS)
         & (rgb09[..., 1] > 0.02) & (rgb_meu[..., 1] > 0))
    seu = [float(np.median(rgb09[..., j][z])) for j in range(3)]
    meu = [float(np.median(rgb_meu[..., j][z])) for j in range(3)]
    return seu, meu, int(z.sum())


def main():
    os.makedirs(CAU, exist_ok=True)
    sv = SV16()
    W, H = sv.W16, sv.H16
    print(f"[1/7] geometria: V16 {W}×{H} · θ {math.degrees(math.atan2(sv.sa, sv.ca)):.3f}° · "
          f"t ({sv.t[0]:.1f}, {sv.t[1]:.1f})")
    geo15 = F15.Geo(padx=3387.0, pady=5109.0)
    sol16 = sv.endavant(7410.63, 7844.42)     # el Sol de la V15, portat a la V16
    print(f"    Sol a la V16: ({sol16[0]:.2f}, {sol16[1]:.2f}) · "
          f"Lluna(09) ({sv.lluna09['cx']:.2f}, {sv.lluna09['cy']:.2f})")
    comu, f2, run, ctx, S13, K, va = F15.carrega_sony()
    for n in FRAMES_MES1S:
        assert n in S13, f"{n} no és al run"
    print("    k coherència:", {n.split('.')[0]: round(K.get(n, 1.0), 3)
                                for n in FRAMES_MES1S})

    print("[2/7] compost >1 s (5 fotogrames, dos apuntaments)")
    C, den = compon_mes1s(sv, geo15, comu, f2, ctx, S13, K)

    print("[3/7] alineació contra la corona Vixen de la V16")
    from psd_tools import PSDImage
    p16v = PSDImage.open(V16)
    merged16 = p16v.numpy()                   # RGBA float32 (per als informes)
    # ⛔ el compost VISIBLE de Pere (12+11+10+09) s'esvaeix a negre més enllà
    #    d'~1,5 R☉ (les capes 08-01 són apagades): la referència d'alineació i
    #    de WB ha de ser EL CONTINGUT de la capa 09 (sense màscara), no la
    #    fusionada — el primer intent hi va perseguir el negre (àncora ×94) i
    #    la zona d'alineació va quedar BUIDA (resposta 1,000 falsa).
    # ⏭️ la referència de color, nivell i alineació és la CAPA 01 (10,3 s): la
    #    corona externa del muntatge de Pere (ara apagada), la capa el paper de
    #    la qual assumeix la Sony. El seu contingut és sòlid i estructurat
    #    (plomalls) a 2,1-2,9 R☉, on el meu apilat també ho és. La capa 09
    #    (segon intent) hi era quasi negra —1/60 s no grava corona a 2,2 R☉—
    #    i la fusionada (primer intent) també, amb les capes 08-01 apagades.
    l01v = next(l for l in p16v if l.name.startswith("01_"))
    x0b, y0b, x1b, y1b = l01v.bbox
    arr01 = l01v.numpy("color")
    rgb09 = np.zeros((H, W, 3), np.float32)
    rgb09[max(0,y0b):min(H,y1b), max(0,x0b):min(W,x1b)] = arr01[
        max(0,y0b)-y0b:min(H,y1b)-y0b, max(0,x0b)-x0b:min(W,x1b)-x0b]
    del arr01
    g16m = rgb09[..., 1]
    gl = np.where(np.isfinite(C["G"]) & (C["G"] > 0),
                  np.log10(np.maximum(np.nan_to_num(C["G"]), 1e-9)), 0.0
                  ).astype(np.float32)
    yy = np.arange(H, dtype=np.float32)[:, None]
    xx = np.arange(W, dtype=np.float32)[None, :]
    rad = np.hypot(xx - sol16[0], yy - sol16[1])
    zona = ((rad > 2.1 * RS) & (rad < 2.9 * RS) & (g16m > 0.02)
            & (gl != 0)).astype(np.float32)
    print(f"    zona de solapament amb el contingut de la capa 01: {zona.sum()/1e3:.0f} kpx")
    a = (g16m - cv2.GaussianBlur(g16m, (0, 0), 12)) * zona
    b = (gl - cv2.GaussianBlur(gl, (0, 0), 12)) * zona
    m = int(2.9 * RS) + 40
    x0, x1 = max(0, int(sol16[0]) - m), min(W, int(sol16[0]) + m)
    y0, y1 = max(0, int(sol16[1]) - m), min(H, int(sol16[1]) + m)
    if zona.sum() < 5e4:
        dx = dy = 0.0; resp = 0.0
        print("    ⚠️ zona insuficient: l'alineació queda per la cadena geomètrica")
    else:
        (dx, dy), resp = cv2.phaseCorrelate(a[y0:y1, x0:x1].astype(np.float64),
                                            b[y0:y1, x0:x1].astype(np.float64))
    print(f"    desplaçament ({dx:+.2f}, {dy:+.2f}) px · resposta {resp:.3f}")
    residual = (float(dx), float(dy))
    if resp >= 0.03 and 0.35 < math.hypot(dx, dy) < 12.0:
        # correcció al sol dels fotogrames: J = A_s·k_s·A_vᵀ·R_v16→15
        ux, uy = sv.ca * dx - sv.sa * (-dy) , 0  # (no: fem el camí complet)
        # vector V16 → V15
        vx = sv.ca * dx + sv.sa * dy
        vy = -sv.sa * dx + sv.ca * dy
        # wait: enrere() del vector és Rᵀ
        vx = sv.ca * dx - (-sv.sa) * dy
        # per claredat: Rcvᵀ = [[ca, -sa],[sa, ca]]
        vx = sv.ca * dx - sv.sa * dy
        vy = sv.sa * dx + sv.ca * dy
        ddX = geo15.cav * vx - geo15.sav * vy
        ddY = geo15.sav * vx + geo15.cav * vy
        rx = geo15.cas * (ddX * geo15.ks) + geo15.sas * (ddY * geo15.ks)
        ry = -geo15.sas * (ddX * geo15.ks) + geo15.cas * (ddY * geo15.ks)
        print(f"    correcció al RAW: ({rx:+.2f}, {ry:+.2f}) px — es recompon")
        C, den = compon_mes1s(sv, geo15, comu, f2, ctx, S13, K, (rx, ry))
        a2 = gl  # re-mesura
        gl = np.where(np.isfinite(C["G"]) & (C["G"] > 0),
                      np.log10(np.maximum(np.nan_to_num(C["G"]), 1e-9)), 0.0
                      ).astype(np.float32)
        b = (gl - cv2.GaussianBlur(gl, (0, 0), 12)) * zona
        (dx2, dy2), resp2 = cv2.phaseCorrelate(a[y0:y1, x0:x1].astype(np.float64),
                                               b[y0:y1, x0:x1].astype(np.float64))
        print(f"    residual ({dx2:+.2f}, {dy2:+.2f}) px · resposta {resp2:.3f}")
        residual = (float(dx2), float(dy2))
    del a, b, gl, zona, g16m

    print("[4/7] render + balanç de blancs i nivell iterats contra la V16")
    tres = np.ones((H, W), bool)
    for c in comu.CANALS:
        tres &= (den[c] > 0) & np.isfinite(C[c])
    guanys = np.array([1.0, 1.0, 1.0])
    va_fit = va
    seu = meu = None
    for it in range(3):
        Cg = {c: C[c] * guanys[j] for j, c in enumerate(comu.CANALS)}
        rgb, ren = comu.render_visual(np.dstack([Cg[c] for c in comu.CANALS]),
                                      tres, va_fit, run.matriu, run.color["guany"])
        seu, meu, npx = mesura_seam(rgb, rgb09, sol16)
        # color: iguala les raons c/G en lineal; nivell: mou l'àncora amb el pendent
        rG = (seu[0] / seu[1]) / max(meu[0] / meu[1], 1e-6)
        bG = (seu[2] / seu[1]) / max(meu[2] / meu[1], 1e-6)
        guanys[0] *= np.clip(rG, 0.5, 2.0)
        guanys[2] *= np.clip(bG, 0.5, 2.0)
        pend = ren["pendent"]
        va_fit *= 10 ** ((meu[1] - seu[1]) / max(pend, 0.05))
        print(f"    it{it}: seu RGB {[round(x,3) for x in seu]} · meu "
              f"{[round(x,3) for x in meu]} · guanys ({guanys[0]:.3f}, 1, "
              f"{guanys[2]:.3f}) · àncora ×{va_fit/va:.3f} · {npx/1e3:.0f} kpx")
    Cg = {c: C[c] * guanys[j] for j, c in enumerate(comu.CANALS)}
    rgb, ren = comu.render_visual(np.dstack([Cg[c] for c in comu.CANALS]),
                                  tres, va_fit, run.matriu, run.color["guany"])
    seu, meu, npx = mesura_seam(rgb, rgb09, sol16)
    print(f"    final: seu {[round(x,3) for x in seu]} · meu {[round(x,3) for x in meu]}")
    col = comu.mesura_color(Cg, rad, tres, RS, radis=(2.0, 3.0, 5.0, 8.0))
    del Cg

    print("[5/7] màscara de mescla (rampa radial + desenfoc gaussià σ=120)")
    # la vora interior de la dada (saturació), azimut a azimut: la rampa HA
    # d'arrencar per fora d'ella o la vora renderitzada és un halo (117)
    vores = []
    for az in np.linspace(0, 2 * np.pi, 360, endpoint=False):
        rr = np.arange(1.4 * RS, 3.0 * RS, 2.0)
        px = np.clip((sol16[0] + rr * np.cos(az)).astype(int), 0, W - 1)
        py = np.clip((sol16[1] + rr * np.sin(az)).astype(int), 0, H - 1)
        t = tres[py, px]
        i = np.argmax(t)
        if t[i]:
            vores.append(rr[i] / RS)
    r_sat = float(np.percentile(vores, 99)) if vores else 2.2
    r_a = r_sat + 0.05
    r_b = r_a + 0.65
    print(f"    vora de saturació p99: {r_sat:.2f} R☉ → rampa suau [{r_a:.2f}, {r_b:.2f}]")
    tt = np.clip((rad - r_a * RS) / ((r_b - r_a) * RS), 0.0, 1.0).astype(np.float32)
    rampa = tt * tt * (3.0 - 2.0 * tt)          # smoothstep: 0 exacte per dins
    del tt
    dmax = max(float(np.nanmax(den["G"])), 1e-9)
    solidesa = np.clip(den["G"] / (0.5 * dmax), 0.0, 1.0) * tres
    msk = np.clip(rampa * solidesa, 0.0, 1.0)
    rr = rad[msk > 0.5] / RS
    rang = (float(np.percentile(rr, 0.5)), float(np.percentile(rr, 99.5))) if rr.size else (0, 0)
    del rr, rampa, solidesa
    nom = (f"13_mes1s_2sx3+8sx2_SONY300 · LDIC run 016 · WB i nivell ajustats a la "
           f"V16 · dada {rang[0]:.2f}-{rang[1]:.2f} R☉")
    print(f"    «{nom}»")
    np.save(os.path.join(CAU, "sony_mes1s_G_lineal.npy"), C["G"])
    np.save(os.path.join(CAU, "sony_mes1s_den_G.npy"), den["G"])
    for c in list(C):
        del C[c]

    print("[6/7] construcció del PSB")
    from psd_tools.constants import ChannelID, Compression
    from psd_tools.compression import decompress
    from psd_tools.psd.image_data import ImageData
    psd = PSDImage.open(V16)
    ver = psd._record.header.version
    # ⛔ la trampa 8BIM/8B64: fora els blocs globals heretats (menys Lr16/Mt16)
    tb = psd._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb = kk.value if hasattr(kk, "value") else kk
        if kb not in (b"Lr16", b"Mt16"):
            del tb[kk]
            print(f"    fora el bloc global heretat {kb!r}")

    def canal(layer, cid):
        for j, ci in enumerate(layer._record.channel_info):
            if int(ci.id) == cid:
                return j, layer._channels[j]
        raise KeyError(cid)

    def reencoda(layer, cid, arr, depth=16):
        j, cd = canal(layer, cid)
        raw = (arr.astype(">u2") if depth == 16 else arr.astype(np.uint8)).tobytes()
        h_, w_ = arr.shape
        cd.set_data(raw, w_, h_, depth, ver)
        rec = layer._record
        rec.channel_info[j] = type(rec.channel_info[j])(rec.channel_info[j].id,
                                                        len(cd.data) + 2)
        assert decompress(cd.data, cd.compression, w_, h_, depth, ver) == raw, \
            "el canal no fa round-trip"

    capes = {l.name.split("_")[0].strip(): l for l in psd}
    # --- capa 09: màscara × fora(disc propi mesurat)
    l09 = capes["09"]
    m09, cru09, mb09 = FP._decodifica_mascara(l09, W, H)
    Lm = sv.lluna09
    d09 = np.hypot(xx - Lm["cx"], yy - Lm["cy"])
    fora = np.clip((d09 - Lm["R"] - RAMPA_LIMBE[0])
                   / (RAMPA_LIMBE[1] - RAMPA_LIMBE[0]), 0.0, 1.0).astype(np.float32)
    nou09 = m09 * fora
    canv = int((np.abs(nou09 - m09) > 1e-6).sum())
    x0m, y0m, x1m, y1m = mb09
    a09 = cru09.copy()
    sx0, sy0 = max(0, x0m), max(0, y0m); sx1, sy1 = min(W, x1m), min(H, y1m)
    a09[sy0 - y0m:sy1 - y0m, sx0 - x0m:sx1 - x0m] = np.clip(
        np.rint(nou09[sy0:sy1, sx0:sx1] * 65535.0), 0, 65535).astype(np.uint16)
    reencoda(l09, int(ChannelID.USER_LAYER_MASK), a09)
    print(f"    09: màscara neta al limbe ({canv/1e3:.0f} kpx dins del disc)")

    # --- capa 13: substitució de contingut, màscara i nom
    l13 = capes["13"]
    assert l13.bbox == (0, 0, W, H), l13.bbox
    rgb16 = np.clip(np.rint(rgb * 65535.0), 0, 65535).astype(np.uint16)
    for j in range(3):
        reencoda(l13, j, rgb16[..., j])
    reencoda(l13, int(ChannelID.TRANSPARENCY_MASK),
             np.full((H, W), 65535, np.uint16))
    m13, cru13, mb13 = FP._decodifica_mascara(l13, W, H)
    assert cru13.shape == (H, W), cru13.shape
    reencoda(l13, int(ChannelID.USER_LAYER_MASK),
             np.clip(np.rint(msk * 65535.0), 0, 65535).astype(np.uint16))
    l13.name = nom
    l13.visible = True
    print("    13: contingut, màscara i nom substituïts · visible")

    print("    fusionada nova…", flush=True)
    compost = np.zeros((H, W, 3), np.float32)
    alfa = np.zeros((H, W), np.float32)
    for layer in psd:      # de BAIX a DALT
        if not layer.visible:
            continue
        numc = layer.name.split("_")[0].strip()
        if layer is l13:
            pix, al = rgb, msk * (layer.opacity / 255.0)
        else:
            x0b, y0b, x1b, y1b = layer.bbox
            arr = layer.numpy("color")
            pix = np.zeros((H, W, 3), np.float32)
            cob = np.zeros((H, W), np.float32)
            pix[max(0,y0b):min(H,y1b), max(0,x0b):min(W,x1b)] = arr[
                max(0,y0b)-y0b:min(H,y1b)-y0b, max(0,x0b)-x0b:min(W,x1b)-x0b]
            cob[max(0,y0b):min(H,y1b), max(0,x0b):min(W,x1b)] = 1.0
            if numc == "09":
                mm = nou09
            else:
                mm, _, _ = FP._decodifica_mascara(layer, W, H)
            al = mm * cob * (layer.opacity / 255.0)
            del arr, cob
        compost = compost * (1.0 - al[..., None]) + pix * al[..., None]
        alfa = alfa + al * (1.0 - alfa)
        del pix, al
    rgbW = compost + (1.0 - alfa[..., None])
    plans = [np.clip(np.rint(rgbW[..., j] * 65535.0), 0, 65535)
             .astype(">u2").tobytes() for j in range(3)]
    plans.append(np.clip(np.rint(alfa * 65535.0), 0, 65535).astype(">u2").tobytes())
    idata = ImageData(compression=Compression.RAW)
    idata.set_data(plans, psd._record.header)
    psd._record.image_data = idata
    if getattr(psd, "_updated", False):
        psd._updated = False
    np.save(os.path.join(CAU, "compost_v17.npy"),
            np.clip(np.rint(compost * 65535.0), 0, 65535).astype(np.uint16))
    np.save(os.path.join(CAU, "alfa_v17.npy"),
            np.clip(np.rint(alfa * 255.0), 0, 255).astype(np.uint8))
    del compost, rgbW, plans, rgb, msk

    print("    desant…", flush=True)
    psd.save(DST)
    print(f"    {DST} · {os.path.getsize(DST)/1e9:.2f} GB")

    print("[7/7] portes ràpides de construcció")
    p2 = PSDImage.open(DST)
    assert (p2.width, p2.height) == (W, H) and len(list(p2)) == 14
    r = subprocess.run(["sips", "-g", "pixelWidth", DST], capture_output=True, text=True)
    assert f"pixelWidth: {W}" in r.stdout + r.stderr, "sips no llegeix la fusionada"
    r = subprocess.run([os.path.join(AQUI, "porta_photoshop.sh"), DST],
                       capture_output=True, text=True, timeout=900)
    print("    Photoshop diu:", (r.stdout + r.stderr).strip())
    rebut = {"v16": V16, "desti": DST, "llenc": [W, H],
             "S_v15_a_v16": json.load(open(os.path.join(CAU, "mesures_v16.json")))["S_v15_a_v16"],
             "sol_v16": [float(sol16[0]), float(sol16[1])],
             "fotogrames": FRAMES_MES1S,
             "k": {n: K.get(n, 1.0) for n in FRAMES_MES1S},
             "residual_px": residual,
             "wb_guanys_lineals_RGB": [float(guanys[0]), 1.0, float(guanys[2])],
             "ancora_factor": float(va_fit / va), "render": ren,
             "seam_seu_RGB": seu, "seam_meu_RGB": meu,
             "color_lineal": col, "rang_dada_Rsol": rang, "nom_capa": nom,
             "mascara_blend": {"rampa_Rsol": [float(r_a), float(r_b)],
                                "forma": "smoothstep (0 exacte per dins de la vora de saturació)"},
             "lluna_09": Lm, "px_mascara_09_canviats": canv,
             "bytes": os.path.getsize(DST)}
    json.dump(rebut, open(os.path.join(CAU, "rebut_v17.json"), "w"),
              indent=1, ensure_ascii=False)
    return rebut


if __name__ == "__main__":
    main()
