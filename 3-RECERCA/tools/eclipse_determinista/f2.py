"""FASE 2 · Composició LDIC — UNA SOLA suma ponderada. Res d'estètica.

    g = Sum_i w(f_i) * k_i * f_i  /  Sum_i w(f_i)

⛔ Aquí dins no hi ha cap fusió entre exposicions: no hi ha fronteres i per tant
no hi pot haver cap graó de fusió.

⛔ **La zona EMMASCARADA del sensor no entra al llenç.** Es porta una màscara de
validesa al costat de la dada: mesurat el 26-08, sense ella 384.970 px del llenç
(l'1,19 % de la dada, a 5,15-10 R☉) rebien el gruix del seu pes de l'overscan.
"""

from __future__ import annotations

import math
import os
import time

import numpy as np
import cv2
import rawpy
from astropy.io import fits

import comu
import f0

SOSTRE = 0.85       # research/101: baixar-lo costa senyal/soroll
TERRA_DN = 12.0     # ~4 sigma de soroll de lectura


def finestra(f: np.ndarray, t: float, sat: float, ped: float) -> np.ndarray:
    alt = SOSTRE * (sat - ped)
    w = np.clip((f - TERRA_DN) / (3.0 * TERRA_DN), 0.0, 1.0)
    w *= np.clip((alt - f) / (0.18 * alt), 0.0, 1.0)
    return (w * t).astype(np.float32)


class Ctx:
    """Tot el que la composició necessita, carregat una sola vegada."""

    def __init__(s, run: comu.Run):
        s.run = run; s.cfg = run.cfg
        S = run.llegeix_rebut("F1.2_sol_llenc.json")
        s.LL = S["llenc"]; s.W = s.LL["W"]; s.H = s.LL["H"]
        s.CX = s.W / 2.0; s.CY = s.H / 2.0; s.RS = s.LL["R_sol_px"]
        # ⛔ RS és en píxels del LLENÇ i RL en píxels del SENSOR: amb un llenç
        #    heretat les dues escales NO són la mateixa. La màscara lunar
        #    treballa al marc del sensor i per això vol RL del sensor.
        s.RL = float(S["contactes"]["R_lluna_px"])
        # ⏭️ Factor llenç → sensor. Val 1 quan el llenç és el del propi tren
        #    (Vixen) i 0,6713 per a la Sony, que hi entra remostrejada ×1,49.
        s.k = s.LL["escala_arcsec_px"] / s.LL.get(
            "escala_sensor_arcsec_px", s.LL["escala_arcsec_px"])
        th = math.radians(-s.LL["pa_north_deg"])
        s.ca, s.sa = math.cos(th), math.sin(th)
        with rawpy.imread(comu.entrades(run.tren, "totalitat")[0]) as r:
            s.g = comu.geometria(r); s.mc = comu.mapa_colors(r)
        s.flat = fits.getdata(run.fase(0, "FLAT_RADIAL.fits")).astype(np.float32)
        s.wb = comu.balanc_dia(comu.entrades(run.tren, "totalitat")[0])
        s.orig = {i: tuple(int(v.min()) for v in np.where(s.mc == i)) for i in range(4)}
        # validesa: zona activa erosionada 2 px, en coordenades de subpla
        s.valid = np.zeros((s.g.alt, s.g.ample), np.float32)
        s.valid[s.g.marge_dalt + 2:s.g.alt - s.g.marge_baix - 2,
                s.g.marge_esq + 2:s.g.ample - s.g.marge_dreta - 2] = 1.0
        s._dk = {}
        s.ruta = {os.path.basename(p): p for p in comu.llums(run.tren)}

    def dark(s, e):
        if e not in s._dk:
            s._dk[e] = f0.dark_de(s.run, e)
        return s._dk[e]

    def caixa(s, sx, sy):
        cs = []
        for (yy, xx) in ((0, 0), (0, s.g.ample), (s.g.alt, 0), (s.g.alt, s.g.ample)):
            dx, dy = (xx - sx) / s.k, (yy - sy) / s.k
            cs.append((s.CX + s.ca * dx - s.sa * dy, s.CY + s.sa * dx + s.ca * dy))
        cs = np.array(cs)
        x0 = max(0, int(np.floor(cs[:, 0].min())) - 2); x1 = min(s.W, int(np.ceil(cs[:, 0].max())) + 2)
        y0 = max(0, int(np.floor(cs[:, 1].min())) - 2); y1 = min(s.H, int(np.ceil(cs[:, 1].max())) + 2)
        return y0, y1, x0, x1

    def mapes(s, sx, sy, caixa):
        y0, y1, x0, x1 = caixa
        XX, YY = np.meshgrid(np.arange(x0, x1, dtype=np.float32),
                             np.arange(y0, y1, dtype=np.float32))
        dX = (XX - s.CX) * s.k; dY = (YY - s.CY) * s.k
        return (s.ca * dX + s.sa * dY) + sx, (-s.sa * dX + s.ca * dY) + sy

    def plans(s, nom, e):
        """(subpla calibrat i balancejat, pes) per als quatre índexs CFA."""
        with rawpy.imread(s.ruta[nom]) as r:
            raw = r.raw_image.astype(np.float32)
        dk = s.dark(e)
        out = {}
        for i in range(4):
            oy, ox = s.orig[i]
            pl = comu.calibra_pla(raw[oy::2, ox::2], dk[oy::2, ox::2],
                                  s.flat[oy::2, ox::2], e, s.wb, s.mc, i)
            w = finestra(raw[oy::2, ox::2] - s.cfg["pedestal_dn"], e,
                         s.cfg["saturacio_dn"], s.cfg["pedestal_dn"])
            w *= s.valid[oy::2, ox::2]        # ⛔ fora l'overscan
            out[i] = (pl, w)
        return out


# ⛔ MÀSCARA LUNAR PER FOTOGRAMA (Druckmüller: w = −1 al seu disc lunar).
#    El llenç està centrat al SOL, o sigui que la Lluna hi LLISCA: 61,5″ =
#    28,6 px = 0,0650 R☉ al llarg de la totalitat. Sense aquesta màscara, el
#    compost fa la mitjana de píxels que a uns fotogrames eren corona i a
#    altres eren Lluna fosca, i el biaix cau justament on la corona és més
#    brillant. La regió realment tapada NO és un cercle sinó la INTERSECCIÓ
#    dels discos; tot el que hi ha entre la intersecció i la unió és
#    recuperable fotograma a fotograma.
# ⏭️ MESURAT el 27-08 (auditoria contra Brno, `research/114`), que fins llavors
#    aquest 2,0 era una suposició escrita com si fos una mesura. Amb la Lluna de
#    sonda —llisca 28,5 px, o sigui que un mateix píxel del llenç és a
#    distàncies molt diferents del limbe segons el fotograma—, el quocient
#    compost/fotograma contra la distància al limbe és PLA dins del ±1,5 %, i
#    aquest ±1,5 % és sobretot la tendència radial. La contaminació del limbe és
#    negligible i 2,0 px BASTA. Pujar la guarda costaria corona interior a canvi
#    de res.
GUARDA_LLUNA_PX = 2.0      # PSF del limbe + error d'ajust (contaminació ≲1,5 %)
VORA_LLUNA_PX = 2.0        # vora suau: una màscara dura fa dents de serra


def mascara_lluna(ctx: "Ctx", v: dict, rx, ry):
    """1 fora del disc lunar d'AQUEST fotograma, 0 a dins, vora suau.

    ⛔ L'han de fer servir TOTS els llocs que comparen un fotograma amb el
    compost. Si `compon` emmascara la Lluna i `coherencia` no, el quocient
    `compost/fotograma` es dispara justament als píxels que en aquell
    fotograma eren Lluna: mesurat el 27-08, k arribava a **206** i el compost
    sortia **49 vegades** massa brillant a partir de 2 R☉.
    """
    if "lluna_dx" not in v or "lluna_dy" not in v:
        raise SystemExit("falta el vector Lluna−Sol (lluna_dx/dy): sense ell no es "
                         "pot emmascarar la Lluna per fotograma.")
    mlx = v["sol_x"] + float(v["lluna_dx"]); mly = v["sol_y"] + float(v["lluna_dy"])
    return np.clip((np.hypot(rx - mlx, ry - mly) - (ctx.RL + GUARDA_LLUNA_PX))
                   / VORA_LLUNA_PX, 0.0, 1.0).astype(np.float32)


def compon(ctx: Ctx, pos: dict, kq: dict, etiqueta: str) -> tuple[dict, dict]:
    num = {c: np.zeros((ctx.H, ctx.W), np.float32) for c in comu.CANALS}
    den = {c: np.zeros((ctx.H, ctx.W), np.float32) for c in comu.CANALS}
    t0 = time.time(); noms = sorted(pos)
    for j, n in enumerate(noms, 1):
        v = pos[n]; e = v["exp"]; k = kq.get(n, 1.0)
        cx_, cy_ = v["sol_x"], v["sol_y"]
        cai = ctx.caixa(cx_, cy_); y0, y1, x0, x1 = cai
        rx, ry = ctx.mapes(cx_, cy_, cai)
        fll = mascara_lluna(ctx, v, rx, ry)
        for i, (pl, w) in ctx.plans(n, e).items():
            oy, ox = ctx.orig[i]
            mx = ((rx - ox) * 0.5).astype(np.float32); my = ((ry - oy) * 0.5).astype(np.float32)
            c = comu.CANALS[comu.IDX_CANAL[i]]
            num[c][y0:y1, x0:x1] += cv2.remap(pl * w * k, mx, my, cv2.INTER_LINEAR,
                                              borderValue=0.0, borderMode=cv2.BORDER_CONSTANT) * fll
            den[c][y0:y1, x0:x1] += cv2.remap(w, mx, my, cv2.INTER_LINEAR,
                                              borderValue=0.0, borderMode=cv2.BORDER_CONSTANT) * fll
        if j % 15 == 0 or j == len(noms):
            print(f"      [{etiqueta}] {j}/{len(noms)} ({time.time()-t0:.0f}s)", flush=True)
    C = {c: np.where(den[c] > 0, num[c] / np.maximum(den[c], 1e-20), np.nan).astype(np.float32)
         for c in comu.CANALS}
    return C, den


def refina(ctx: Ctx, pos: dict, C: dict, r_min=1.3, r_max=8.0) -> dict:
    """Registre fi per CORRELACIÓ DE FASE contra el compost.

    ⏭️ És la mesura bona: 0,095 px, contra 0,4-0,7 px de l'ajust del limbe.
    El punt de partida és el model; si la correlació no convenç, s'hi queda.
    """
    yy, xx = np.mgrid[0:ctx.H, 0:ctx.W].astype(np.float32)
    rad = np.hypot(yy - ctx.CY, xx - ctx.CX); del yy, xx
    banda = (rad > r_min * ctx.RS) & (rad < r_max * ctx.RS) & np.isfinite(C["G"]) & (C["G"] > 0)
    ref = np.zeros((ctx.H, ctx.W), np.float32)
    ref[banda] = np.log10(np.maximum(C["G"][banda], 1e-6))
    ref[banda] -= ref[banda].mean()
    win = cv2.createHanningWindow((ctx.W, ctx.H), cv2.CV_32F)
    refw = (ref * win).astype(np.float64)
    out = {}; t0 = time.time(); noms = sorted(pos); n_ref = 0
    for j, n in enumerate(noms, 1):
        v = dict(pos[n]); e = v["exp"]
        cai = (0, ctx.H, 0, ctx.W)
        rx, ry = ctx.mapes(v["sol_x"], v["sol_y"], cai)
        pl, w = ctx.plans(n, e)[1]
        oy, ox = ctx.orig[1]
        mx = ((rx - ox) * 0.5).astype(np.float32); my = ((ry - oy) * 0.5).astype(np.float32)
        im = cv2.remap(pl, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
        wm = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
        ok = banda & (wm > 0.25 * float(w.max())) & (im > 0)
        if ok.sum() > 150000:
            cur = np.zeros((ctx.H, ctx.W), np.float32)
            cur[ok] = np.log10(np.maximum(im[ok], 1e-6)); cur[ok] -= cur[ok].mean()
            (dx, dy), resp = cv2.phaseCorrelate(refw, (cur * win).astype(np.float64))
            if resp >= 0.02 and abs(dx) < 20 and abs(dy) < 20:
                v["sol_x"] += ctx.ca * dx - ctx.sa * dy
                v["sol_y"] += ctx.sa * dx + ctx.ca * dy
                v["font"] = "correlacio"; v["desplacament_px"] = [float(dx), float(dy)]
                v["resposta"] = float(resp); n_ref += 1
            else:
                v["font"] = "model (correlacio refusada)"; v["resposta"] = float(resp)
        else:
            v["font"] = "model (banda insuficient)"; v["n_banda"] = int(ok.sum())
        out[n] = v
        if j % 15 == 0 or j == len(noms):
            print(f"      [refina] {j}/{len(noms)} ({time.time()-t0:.0f}s)", flush=True)
    d = np.array([math.hypot(*out[n]["desplacament_px"]) for n in out
                  if "desplacament_px" in out[n]])
    print(f"    refinats {n_ref}/{len(noms)} · desplaçament mediana "
          f"{np.median(d) if d.size else float('nan'):.3f} px màx "
          f"{d.max() if d.size else float('nan'):.3f} px", flush=True)
    return out


def coherencia(ctx: Ctx, pos: dict, C: dict) -> dict:
    """Guany k_i per fotograma, mediana píxel a píxel. Gauge mediana(ln k)=0.

    ⛔ Sense terme additiu `q`: ajustar k i q alhora és DEGENERAT quan el perfil
    és pla (els fotogrames d'1 s demanaven k=2,5 amb q=−1.700). El cel es treu
    una sola vegada al final.
    """
    cg = C["G"]
    fin = np.isfinite(cg)
    llind = 5.0 * float(np.nanmedian(cg[fin]))
    out = {}; lnk = []
    for n in sorted(pos):
        v = pos[n]; e = v["exp"]
        cai = ctx.caixa(v["sol_x"], v["sol_y"]); y0, y1, x0, x1 = cai
        rx, ry = ctx.mapes(v["sol_x"], v["sol_y"], cai)
        pl, w = ctx.plans(n, e)[1]
        oy, ox = ctx.orig[1]
        mx = ((rx - ox) * 0.5).astype(np.float32); my = ((ry - oy) * 0.5).astype(np.float32)
        a = cv2.remap(pl, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
        b = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
        ref = cg[y0:y1, x0:x1]
        # ⛔ la MATEIXA màscara lunar que `compon`, o el quocient es dispara
        fll = mascara_lluna(ctx, v, rx, ry)
        bo = ((b > 0.35 * float(w.max())) & np.isfinite(ref) & (ref > llind)
              & (a > 0) & (fll > 0.99))
        k = float(np.median(ref[bo] / a[bo])) if bo.sum() >= 5000 else 1.0
        if not np.isfinite(k) or k <= 0:
            k = 1.0
        out[n] = k
        if bo.sum() >= 5000:
            lnk.append(math.log(k))
    med = float(np.median(lnk)) if lnk else 0.0
    out = {n: out[n] / math.exp(med) for n in out}
    ks = np.array([out[n] for n in sorted(out)])
    if ks.size == 0:
        raise SystemExit("PORTA F2.2: cap fotograma per ajustar el guany")
    print(f"    k: mediana {np.median(ks):.4f} · p5-p95 {np.percentile(ks,5):.4f}-"
          f"{np.percentile(ks,95):.4f} · dispersió {100*ks.std():.2f} %", flush=True)
    # ⏭️ PORTA: la transparència va caure un 8 % durant la totalitat, o sigui
    #    que cap fotograma no pot demanar un guany d'un factor 2. Un k
    #    disparat vol dir que el fotograma i la referència no es comparen sobre
    #    els mateixos píxels, i el compost en surt destrossat sense avisar.
    pit = float(np.max(np.abs(np.log(ks))))
    if pit > math.log(2.0):
        dolents = {n: round(out[n], 3) for n in sorted(out)
                   if abs(math.log(out[n])) > math.log(2.0)}
        raise SystemExit(f"PORTA F2.2: guany fora de rang (factor "
                         f"{math.exp(pit):.2f} > 2). Fotogrames: {dolents}")
    return out


def cura_cel_fotograma(ctx: Ctx, pos: dict, kq: dict, C: dict, den: dict,
                       sig_soroll=24.0, lam_max=500.0) -> tuple[dict, dict]:
    """`research/103` · la transparència del cel té ESTRUCTURA per fotograma.

    La coherència (`k`) només corregeix el guany GLOBAL de cada fotograma. El
    que queda són **bandes i estries** de 0,10-0,50 % rms que es mouen amb el
    vent (`research/102`): la «malla de rectes». Al compost hi sobreviuen com
    a arcs i bandes suaus, i són el que Pere va marcar en lila el 27-08.

        ΔC = Σ(w_i · S_i) / Σ w_i

    amb `S_i` el residu relatiu de cada fotograma contra el compost, suavitzat
    per matar el soroll i **acotat a la banda [σ, λ_max]**.

    ⏭️ La corona REAL s'hi cancel·la sola: és al fotograma i al compost alhora,
    o sigui que surt del quocient. El que queda és el que el compost ha heretat
    de la transparència.
    ⛔ L'acotament per dalt (λ_max) és el que impedeix que la cura es mengi
    estructura coronal gran; la σ de baix, que es mengi soroll.
    ⚠️ Aprovada pel jutge extern NOMÉS per a la Vixen (`research/103`): a la
    Sony la va refusar.
    """
    # ⏭️ Tot el càlcul va a 1/8 de resolució: les bandes de transparència fan
    #    centenars de píxels i el desenfoc de λmax a mida completa demanaria un
    #    nucli de 1501 px sobre caixes de 25 Mpx. A 1/8 és 64 vegades més barat
    #    i la banda que ens interessa hi cap sencera.
    Q = 8
    hs, ws = ctx.H // Q, ctx.W // Q
    num = {c: np.zeros((hs, ws), np.float32) for c in comu.CANALS}
    dnm = {c: np.zeros((hs, ws), np.float32) for c in comu.CANALS}
    k1 = int(6 * (sig_soroll / Q)) | 1
    k2 = int(6 * (lam_max / 2.0 / Q)) | 1
    t0 = time.time(); noms = sorted(pos)
    for j, n in enumerate(noms, 1):
        v = pos[n]; e = v["exp"]; kk = kq.get(n, 1.0)
        cai = ctx.caixa(v["sol_x"], v["sol_y"]); y0, y1, x0, x1 = cai
        rx, ry = ctx.mapes(v["sol_x"], v["sol_y"], cai)
        fll = mascara_lluna(ctx, v, rx, ry)
        for i, (pl, w) in ctx.plans(n, e).items():
            oy, ox = ctx.orig[i]
            mx = ((rx - ox) * 0.5).astype(np.float32); my = ((ry - oy) * 0.5).astype(np.float32)
            c = comu.CANALS[comu.IDX_CANAL[i]]
            a = cv2.remap(pl * kk, mx, my, cv2.INTER_LINEAR, borderValue=0.0) * fll
            b = cv2.remap(w, mx, my, cv2.INTER_LINEAR, borderValue=0.0) * fll
            ref = C[c][y0:y1, x0:x1]
            bo = (b > 0) & np.isfinite(ref) & (ref > 0)
            q = np.where(bo, a / np.maximum(ref, 1e-12) - 1.0, 0.0).astype(np.float32)
            wb = np.where(bo, b, 0.0).astype(np.float32)
            # a 1/8, damunt d'un llenç sencer perquè les vores de caixa no comptin
            QN = np.zeros((hs, ws), np.float32); QD = np.zeros((hs, ws), np.float32)
            hh = ((y1 - y0) // Q) * Q; ww = ((x1 - x0) // Q) * Q
            if hh < Q or ww < Q:
                continue
            sq = cv2.resize((q * wb)[:hh, :ww], (ww // Q, hh // Q), interpolation=cv2.INTER_AREA)
            sw = cv2.resize(wb[:hh, :ww], (ww // Q, hh // Q), interpolation=cv2.INTER_AREA)
            ys, xs = y0 // Q, x0 // Q
            ye, xe = min(hs, ys + sq.shape[0]), min(ws, xs + sq.shape[1])
            QN[ys:ye, xs:xe] = sq[:ye - ys, :xe - xs]
            QD[ys:ye, xs:xe] = sw[:ye - ys, :xe - xs]
            sn = cv2.GaussianBlur(QN, (k1, k1), sig_soroll / Q)
            sd = cv2.GaussianBlur(QD, (k1, k1), sig_soroll / Q)
            fi = np.where(sd > 1e-9, sn / np.maximum(sd, 1e-12), 0.0).astype(np.float32)
            va = (sd > 1e-9).astype(np.float32)
            gn = cv2.GaussianBlur(fi * va, (k2, k2), lam_max / 2.0 / Q)
            gd = cv2.GaussianBlur(va, (k2, k2), lam_max / 2.0 / Q)
            fi -= np.where(gd > 1e-9, gn / np.maximum(gd, 1e-12), 0.0)   # fora l'escala gran
            num[c] += fi * QD
            dnm[c] += QD
        if j % 15 == 0 or j == len(noms):
            print(f"      [cura cel] {j}/{len(noms)} ({time.time()-t0:.0f}s)", flush=True)
    info = {"metode": "research/103 · ΔC = Σ(w·S)/Σw, banda [σ, λmax]",
            "sigma_soroll_px": sig_soroll, "lambda_max_px": lam_max,
            "validacio": "jutge extern de research/103, NOMÉS per a la Vixen",
            "resolucio_calcul": "1/8 del llenç",
            "amplitud_pct": {}}
    out = {}
    for c in comu.CANALS:
        ds = np.where(dnm[c] > 0, num[c] / np.maximum(dnm[c], 1e-12), 0.0).astype(np.float32)
        d = cv2.resize(ds, (ctx.W, ctx.H), interpolation=cv2.INTER_CUBIC)
        s_ = cv2.resize((dnm[c] > 0).astype(np.float32), (ctx.W, ctx.H),
                        interpolation=cv2.INTER_NEAREST) > 0.5
        info["amplitud_pct"][c] = {
            "rms": float(100 * np.sqrt(np.mean(d[s_] ** 2))) if s_.any() else 0.0,
            "p99": float(100 * np.percentile(np.abs(d[s_]), 99)) if s_.any() else 0.0}
        out[c] = np.where(np.isfinite(C[c]), C[c] * (1.0 - d), np.nan).astype(np.float32)
    print("    amplitud treta: " + " · ".join(
        f"{c} rms {info['amplitud_pct'][c]['rms']:.3f} % p99 {info['amplitud_pct'][c]['p99']:.3f} %"
        for c in comu.CANALS), flush=True)
    return out, info


# ------------------------------------------------------------------- cel


def cel_per_color(ctx: Ctx, C: dict, den: dict, sigma=220.0,
                  r_corona=(1.05, 1.30), r_cel=6.0) -> tuple[dict, dict]:
    """Separació cel/corona pel COLOR, amb els DOS vectors MESURATS.

    ⛔ Rectificació del 26-08: el mètode NO falla per extinció. Els dos vectors
    se separen 22,6° i la condició és 5,15. El que fallava era suposar la corona
    NEUTRA, i no ho és (R/G=1,76 · B/G=0,50 per l'extinció cromàtica a X~6).

    Tres equacions i dues incògnites: queda **un grau de llibertat per fallar**,
    i aquest és el control honest que `research/100` §D demana.
    """
    yy, xx = np.mgrid[0:ctx.H, 0:ctx.W].astype(np.float32)
    rad = np.hypot(yy - ctx.CY, xx - ctx.CX); del yy, xx
    m = comu.mascara_dada(den["G"], rad)
    for c in comu.CANALS:
        m &= np.isfinite(C[c]) & (C[c] > 0)
    din = m & (rad > r_corona[0] * ctx.RS) & (rad < r_corona[1] * ctx.RS)
    fora = m & (rad > r_cel * ctx.RS)
    s = np.array([float(np.median(C[c][din] / C["G"][din])) for c in comu.CANALS])
    b = np.array([float(np.median(C[c][fora] / C["G"][fora])) for c in comu.CANALS])
    A = np.c_[s, b]; cond = float(np.linalg.cond(A))
    ang = float(np.degrees(np.arccos(s @ b / (np.linalg.norm(s) * np.linalg.norm(b)))))
    pinv = np.linalg.pinv(A)
    I = np.stack([C[c] for c in comu.CANALS], axis=0)
    for _ in range(3):
        Cc = sum(pinv[0, i] * I[i] for i in range(3))
        Ss = sum(pinv[1, i] * I[i] for i in range(3))
        net = fora & (Cc < 0.15 * np.nanmedian(Cc[fora]) + abs(np.nanmedian(Cc[fora])))
        if net.sum() < 100000:
            break
        bn = np.array([float(np.median((C[c][net] - Cc[net] * s[i]) /
                                       np.maximum(Ss[net], 1e-6)))
                       for i, c in enumerate(comu.CANALS)])
        bn = bn / bn[1]
        d = float(np.max(np.abs(bn - b))); b = bn; A = np.c_[s, b]; pinv = np.linalg.pinv(A)
        if d < 2e-3:
            break
    Cc = sum(pinv[0, i] * I[i] for i in range(3))
    Ss = sum(pinv[1, i] * I[i] for i in range(3))
    rec = np.stack([Cc * s[i] + Ss * b[i] for i in range(3)], axis=0)
    resid = np.abs(I - rec).sum(axis=0) / np.maximum(np.abs(I).sum(axis=0), 1e-6)
    ctrl = float(100 * np.median(resid[m])); ctrl90 = float(100 * np.percentile(resid[m], 90))
    del I, rec
    k = int(6 * sigma) | 1
    mf = m.astype(np.float32)
    num = cv2.GaussianBlur(np.where(m, Ss, 0.0).astype(np.float32), (k, k), sigma)
    dd = cv2.GaussianBlur(mf, (k, k), sigma)
    Sf = np.where(dd > 1e-4, num / np.maximum(dd, 1e-9), 0.0).astype(np.float32)
    out = {c: np.where(m, C[c] - Sf * b[i], np.nan).astype(np.float32)
           for i, c in enumerate(comu.CANALS)}
    info = {"s_corona": s.tolist(), "b_cel": b.tolist(), "angle_graus": ang,
            "condicio": cond, "control_residu_mediana_pct": ctrl,
            "control_residu_p90_pct": ctrl90, "sigma_suavitzat_px": sigma,
            "perfil_G": {}}
    for r0 in (1.1, 1.5, 2.0, 3.0, 5.0, 7.0, 9.0):
        s2 = m & (rad > r0 * ctx.RS) & (rad < (r0 + 0.06) * ctx.RS)
        if s2.sum() < 200:
            continue
        a_ = float(np.nanmedian(C["G"][s2])); c_ = float(np.nanmedian(out["G"][s2]))
        info["perfil_G"][f"{r0:g}"] = {"abans": a_, "despres": c_,
                                       "cel_sobre_corona": (a_ - c_) / max(c_, 1e-9)}
    print(f"    s={np.round(s,4).tolist()} b={np.round(b,4).tolist()} · angle {ang:.2f}° "
          f"· condició {cond:.2f}", flush=True)
    print(f"    CONTROL (grau de llibertat que sobra): mediana {ctrl:.3f} % p90 {ctrl90:.3f} % "
          f"[research/100: 0,01-1,26 %]", flush=True)
    if ctrl > 3.0:
        raise SystemExit(f"PORTA F2.4: el control del color dona {ctrl:.2f} % > 3 %")
    info["porta"] = "PASSA"
    return out, info
