"""CapesTotalsV14 — la maqueta de Pere refeta amb la dada calibrada.

## Què és

`CapesTotalsV13.psd` és **la maqueta**: el muntatge manual de Pere d'abans que
linealitzéssim, dotze capes planes —una per esglaó d'exposició— amb la seva
màscara, al llenç del sensor de la Vixen (7648×5353). `research/108` la va
mesurar i en va treure la corba de to que el projecte fa servir avui.

La V14 conserva **l'estructura i les màscares** de la V13 i en canvia la dada:

1. cada capa passa a ser la **imatge calibrada** del run vigent de la cadena
   determinista, al **llenç comú de 8096×8960** (el que encabeix la Sony);
2. les imatges ja hi arriben **alineades amb la corona** —les registra la
   cadena— i **cada màscara es porta amb el Sol del SEU fotograma**, que és el
   registre que la V13 no tenia (`geo_v13.py`);
3. la màscara es **retoca** perquè el limbe lunar surti net: es multiplica per
   la validesa de la seva pròpia capa.

## ⛔ La cura del limbe, i per què és aquesta

A la V13, el limbe embruta per una raó sola: **una màscara demana píxels que la
seva exposició no té**. Passa a dos llocs alhora.

- **Dins del disc lunar.** La capa de 10,3 s hi té la màscara a 0,33 i al limbe
  a 0,50 (`research/87` §1): és el vel que renta la Lluna. Allà no hi ha dada
  de cap exposició llarga —està tota saturada o tapada—, o sigui que el que
  entrava era desbordament i no imatge.
- **A la vora interior de cada exposició.** Cada esglaó deixa d'estar saturat a
  un radi propi (10,3 s a 2,00 R☉; 1/8 s a 1,18) i aquella vora, renderitzada,
  **és exactament un halo al voltant de la Lluna**. El 27-08 Pere va marcar la
  del 1/8 s creient que era un artefacte del producte.

La cura no pinta res: **`màscara_V14 = màscara_V13 · validesa_de_la_capa`**, amb
la validesa mesurada del pes de la composició —els tres canals amb dada i el
llindar comparat amb el que és assolible AL MATEIX RADI (`comu.mascara_dada`)—
i una vora suau. Amb això el disc lunar queda a zero a totes les capes menys la
que legítimament el mira (la de contacte de C2), la vora interior de cada
esglaó desapareix, i el marc blanc de la V13 —que era el marge del sensor— se'n
va sol.

## ⛔ La Lluna ha de ser RODONA, i per això va DECLARADA

El llenç va centrat al **Sol**, o sigui que **la Lluna hi llisca**: 28,5 px al
llarg de la totalitat, el 6,3 % del seu radi. Si cada capa es queda amb el forat
dels seus propis fotogrames, la silueta que en surt és la **intersecció** dels
discos —un *lune*— amb un tros de corona sobresortint per un costat i una
**mossegada** per l'altre. Mesurat a la primera V14: **16.643 px de corona dins
del disc de C2** i **8.293 px de negre fora**, fins a **23 px** enllà del limbe,
i la mossegada es menjava la protuberància.

⏭️ **La cura és la decisió que Pere ja havia pres el 27-08** («oblidem-nos de la
simetria amb els dos contactes, treballarem només en C2; no m'agrada el resultat
de deformar la Lluna»), aplicada també DINS de la totalitat:

1. es **declara un sol disc lunar**, el dels fotogrames de contacte de C2 —el
   mateix instant d'on surten les protuberàncies—, i totes les màscares hi van a
   zero: la Lluna surt rodona per construcció;
2. l'anell que queda entre aquell disc i on arriba cada capa el reomple la capa
   de **protuberàncies de C2** en mode **Aclarir**, que és exactament el que fa
   el producte de la cadena (`f4.psb_resultat`).

El preu, declarat: es perd la mica de corona que als fotogrames tardans es veia
dins del disc de C2. És el mateix preu que Pere ja va acceptar per tenir la
Lluna rodona.

⛔ Norma del rectangle: aquí no es retalla res a cap circumferència. L'única
cosa rodona és la Lluna, que **és** rodona. El que talla és la manca de dada,
mesurada.
⛔ El run és IMMUTABLE: d'ell només se'n llegeix.
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
sys.path.insert(0, os.path.join(os.path.dirname(AQUI), "encaix_sony"))   # psb_utils
sys.path.insert(0, AQUI)

import geo_v13

V13 = ("/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/"
       "Capes Totals/CapesTotalsV13.psd")
DEST_DIR = os.path.dirname(V13)

# ⏭️ La correspondència V13 → cadena. La clau NO és l'exposició nominal sinó el
#    FOTOGRAMA que el nom de la capa de la V13 declara: així el grup el resol la
#    cadena i no una taula escrita a mà que es pot desincronitzar.
CAPES = [   # de BAIX a DALT, com al fitxer
    ("12", "572A2956.CR3", "1/3200 s", "PERLES-DIAMANT (contacte de C2)"),
    ("11", "572A2968.CR3", "1/500 s",  "LIMBE-PROTUBERÀNCIES"),
    ("10", "572A2969.CR3", "1/125 s",  "CORONA INTERIOR"),
    ("09", "572A2975.CR3", "1/60 s",   "CORONA INTERIOR-MITJANA"),
    ("08", "572A2970.CR3", "1/30 s",   ""),
    ("07", "572A2976.CR3", "1/15 s",   ""),
    ("06", "572A2971.CR3", "1/8 s",    ""),
    ("05", "572A2977.CR3", "1/4 s",    ""),
    ("04", "572A2972.CR3", "1/2 s",    ""),
    ("03", "572A2978.CR3", "1 s",      ""),
    ("02", "572A2979.CR3", "2 s",      ""),
    ("01", "572A2982.CR3", "10,3 s",   ""),
]

FRAC_DADA = 0.02        # el mateix llindar que `comu.mascara_dada` fa servir
SIGMA_VORA = 1.6        # px, la vora suau de la validesa


# ------------------------------------------------------------------ V13

def extreu_v13(cau: str) -> dict:
    """Màscares (uint8, llenç sencer) i metadades de la V13. Només lectura."""
    fitxa = os.path.join(cau, "v13_info.json")
    if os.path.exists(fitxa):
        return json.load(open(fitxa))
    from psd_tools import PSDImage
    os.makedirs(cau, exist_ok=True)
    psd = PSDImage.open(V13)
    W, H = psd.width, psd.height
    info = {"W": W, "H": H, "fitxer": V13, "capes": {}}
    for i, l in enumerate(psd):
        num = l.name.split("_")[0]
        m = l.mask
        if m is None or m.size == (0, 0):
            raise SystemExit(f"la capa {num} de la V13 no té màscara")
        a = np.squeeze(np.asarray(m.topil()))
        a = (a.astype(np.float32) / 65535.0 if a.dtype == np.uint16
             else a.astype(np.float32) / 255.0)
        bg = float(getattr(m, "background_color", 0)) / 255.0
        full = np.full((H, W), bg, np.float32)
        x0, y0, x1, y1 = m.bbox
        sx0, sy0, sx1, sy1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
        full[sy0:sy1, sx0:sx1] = a[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0]
        np.save(os.path.join(cau, f"mask_{num}.npy"),
                (np.clip(full, 0, 1) * 255).round().astype(np.uint8))
        info["capes"][num] = {"i": i, "nom": l.name, "bbox": list(l.bbox),
                              "visible": bool(l.visible), "opacitat": int(l.opacity),
                              "fusio": str(l.blend_mode), "mask_bbox": list(m.bbox),
                              "mask_fons": bg,
                              "mask_mitjana": float(np.clip(full, 0, 1).mean())}
        print(f"    V13 {num}: màscara mitjana {full.mean():.3f} "
              f"(fons {bg:.2f}) · visible {l.visible}", flush=True)
        del full, a
    json.dump(info, open(fitxa, "w"), indent=1, ensure_ascii=False)
    return info


# ------------------------------------------------------------- la cadena

def carrega_cadena(run_dir: str):
    sys.path.insert(0, os.path.join(run_dir, "codi"))
    import comu, f2, f4                                   # noqa: E402
    run = comu.Run.obre(run_dir)
    return comu, f2, f4, run


def composa_contacte(comu, f2, ctx, run, S, frame, va, m, matriu, guany):
    """La capa de contacte de C2: perles i PRIMER ANELL DE DIAMANT.

    ⛔ **UN SOL fotograma**, el mateix que la capa de la V13 declara al seu nom.
    A les altres capes combinar els fotogrames del seu esglaó és estrictament
    millor —l'escena és la corona i no es mou—, però aquí l'escena SÍ que canvia:
    les perles són la fotosfera desapareixent darrere les muntanyes de la Lluna,
    i el `max` sobre la finestra de C2 que fa `f4.psb_contactes` en dibuixa la
    UNIÓ, un collaret que no va existir a cap instant. La V13 en tria un i aquí
    es tria el mateix.

    ⏭️ **Els píxels saturats es declaren COTA INFERIOR, no mesura.** A 1/3200 s
    la fotosfera de les perles satura i no hi ha cap exposició més curta que la
    rescati: si es deixen com a «sense dada» —que és el que la cadena fa— les
    perles surten clapejades de forats. S'omplen amb el sostre de la finestra,
    que és el que aquell píxel com a mínim val, i el rebut diu quants n'hi ha.
    """
    v = S[frame]; e = v["exp"]
    alt = f2.SOSTRE * (ctx.cfg["saturacio_dn"] - ctx.cfg["pedestal_dn"])
    cai = (0, ctx.H, 0, ctx.W)
    rx, ry = ctx.mapes(v["sol_x"], v["sol_y"], cai)
    num = np.zeros((ctx.H, ctx.W, 3), np.float32)
    den = np.zeros((ctx.H, ctx.W, 3), np.float32)
    nsat = np.zeros((ctx.H, ctx.W, 3), np.float32)
    sostre_cal = np.zeros(3, np.float64)
    import rawpy
    with rawpy.imread(ctx.ruta[frame]) as r:
        raw = r.raw_image.astype(np.float32)
    dk = ctx.dark(e)
    for i in range(4):
        oy, ox = ctx.orig[i]
        sub = raw[oy::2, ox::2]
        pl = comu.calibra_pla(sub, dk[oy::2, ox::2], ctx.flat[oy::2, ox::2],
                              e, ctx.wb, ctx.mc, i)
        w = f2.finestra(sub - ctx.cfg["pedestal_dn"], e,
                        ctx.cfg["saturacio_dn"], ctx.cfg["pedestal_dn"])
        w *= ctx.valid[oy::2, ox::2]
        sat = (((sub - ctx.cfg["pedestal_dn"]) >= alt).astype(np.float32)
               * ctx.valid[oy::2, ox::2])
        j = comu.IDX_CANAL[i]
        sostre_cal[j] = alt / e * ctx.wb[j]
        mx = ((rx - ox) * 0.5).astype(np.float32)
        my = ((ry - oy) * 0.5).astype(np.float32)
        ok = (w > 0).astype(np.float32)
        num[..., j] += cv2.remap(pl * ok, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
        den[..., j] += cv2.remap(ok, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
        nsat[..., j] += cv2.remap(sat, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
    del raw
    im = np.where(den > 0.5, num / np.maximum(den, 1e-9), np.nan).astype(np.float32)
    cota = (den <= 0.5) & (nsat > 0.5)
    for j in range(3):
        im[..., j] = np.where(cota[..., j], sostre_cal[j], im[..., j])
    dd = np.where(den > 0.5, 1.0, 0.0).astype(np.float32)
    dd = np.where(cota, 1.0, dd)
    mm = np.isfinite(im).all(axis=2) & m
    rgb, _ = comu.render_visual(im, mm, va, matriu, guany)
    n_cota = int(cota.any(axis=2).sum())
    return rgb, {c: dd[..., j] for j, c in enumerate(("R", "G", "B"))}, mm, [frame], n_cota


def disc_lluna(ctx, f2, S, noms) -> tuple[np.ndarray, dict]:
    """El disc lunar DECLARAT: 1 fora, 0 a dins, vora suau.

    El centre és la mitjana de la posició de la Lluna als fotogrames que fan les
    protuberàncies —dispersió 0,27 px, o sigui un sol disc—, i el radi i la vora
    són els mateixos que `f2.mascara_lluna` fa servir a tot arreu (radi
    d'efemèride + 2 px de guarda, vora de 2 px). Així el forat de les màscares i
    el de la capa de protuberàncies són el MATEIX cercle i no hi ha doble vora.
    """
    pos = []
    for n in noms:
        v = S[n]
        mlx = v["sol_x"] + float(v["lluna_dx"]); mly = v["sol_y"] + float(v["lluna_dy"])
        dx, dy = (mlx - v["sol_x"]) / ctx.k, (mly - v["sol_y"]) / ctx.k
        pos.append((ctx.CX + ctx.ca * dx - ctx.sa * dy, ctx.CY + ctx.sa * dx + ctx.ca * dy))
    P = np.array(pos, np.float64)
    cx, cy = P.mean(0)
    disp = float(np.hypot(*(P - P.mean(0)).T).max())
    d = np.hypot(np.arange(ctx.W, dtype=np.float32)[None, :] - cx,
                 np.arange(ctx.H, dtype=np.float32)[:, None] - cy)
    fora = np.clip((d - (ctx.RL + f2.GUARDA_LLUNA_PX)) / f2.VORA_LLUNA_PX, 0.0, 1.0)
    return fora.astype(np.float32), {
        "fotogrames": list(noms), "centre_px": [float(cx), float(cy)],
        "dispersio_px": disp, "R_lluna_px": float(ctx.RL),
        "guarda_px": f2.GUARDA_LLUNA_PX, "vora_px": f2.VORA_LLUNA_PX}


def validesa(comu, den, rad, m):
    """On la capa té dada de veritat, amb vora suau.

    ⛔ El llindar es compara amb el que és assolible AL MATEIX RADI: un llindar
    sobre el màxim global es menja la corona interior sencera, perquè prop del
    limbe només hi contribueixen les exposicions curtes i el pes hi cau dos
    ordres de magnitud de manera legítima (`comu.mascara_dada`).
    """
    tres = m.copy()
    for c in ("R", "G", "B"):
        tres &= den[c] > 0
    sup = comu.mascara_dada(den["G"], rad, frac=FRAC_DADA) & tres
    s = cv2.GaussianBlur(sup.astype(np.float32), (0, 0), SIGMA_VORA)
    return np.clip(2.0 * (s - 0.5), 0.0, 1.0), sup, tres


def comprova_obrible(ruta: str, W: int, H: int, n_capes: int) -> None:
    """⛔ Un fitxer escrit que ningú no ha tornat a obrir no està verificat.

    Es comprova amb DOS lectors independents:

    - `psd-tools`, que és qui l'ha escrit —diu si l'estructura de capes hi és—;
    - **`sips`**, que és ImageIO de macOS i **no comparteix ni una línia de codi
      amb psd-tools**: llegeix la imatge FUSIONADA, que és justament la secció
      que el 27-08 va deixar el fitxer sense obrir a Photoshop.

    Si el segon no en treu la mida, el fitxer no s'obrirà i s'ha de dir aquí,
    no d'aquí a una hora quan Pere hi faci doble clic.
    """
    import subprocess
    from psd_tools import PSDImage
    psd = PSDImage.open(ruta)
    capes = list(psd)
    if (psd.width, psd.height) != (W, H) or len(capes) != n_capes:
        raise SystemExit(f"PORTA: psd-tools rellegeix {psd.width}×{psd.height} amb "
                         f"{len(capes)} capes, i n'esperava {W}×{H} amb {n_capes}")
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", ruta],
                       capture_output=True, text=True)
    txt = r.stdout + r.stderr
    if f"pixelWidth: {W}" not in txt or f"pixelHeight: {H}" not in txt:
        raise SystemExit(
            "⛔ PORTA: ImageIO no llegeix la imatge fusionada del fitxer, o sigui "
            "que Photoshop tampoc l'obrirà («no és compatible amb aquesta versió»). "
            "Mira la compressió de `set_merged`: ha de ser RAW o RLE, mai ZIP.\n"
            + txt)
    print(f"    obrible ✓ · psd-tools {psd.width}×{psd.height} amb {len(capes)} capes "
          f"· ImageIO llegeix la fusionada")


def rang_radial(msk, rad, RS, llindar=None):
    """Fins on val una màscara, en R☉.

    ⛔ El llindar NO pot ser 0,5 fix: quatre de les dotze màscares de la V13
    no arriben a 0,5 enlloc (la del 1/8 s no passa de 0,345) i el rang sortia
    buit. Es pren la meitat del seu propi màxim, amb un terra de 0,02.
    """
    if llindar is None:
        llindar = max(0.02, 0.5 * float(np.nanmax(msk)))
    v = msk > llindar
    if not v.any():
        return None, None, llindar
    rr = rad[v] / RS
    return (float(np.percentile(rr, 0.5)), float(np.percentile(rr, 99.5)), llindar)


def _r(x):
    return "—" if x is None else f"{x:.2f}"


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default=None, help="carpeta del run (per defecte, el darrer VIXEN CIENCIA)")
    ap.add_argument("--cau", default=os.path.join(AQUI, "cau_v13"))
    ap.add_argument("--sortida", default=os.path.join(DEST_DIR, "CapesTotalsV14.psd"))
    ap.add_argument("--vistes", default=None)
    ap.add_argument("--sony", default=None, help="carpeta del run SONYTOT per a la capa afegida")
    a = ap.parse_args()

    ARREL = os.path.expanduser("~/Desktop/Eclipse determinista")
    if a.run is None:
        # ⛔ El darrer run pot estar EN MARXA: el 27-08 el `018` va aparèixer a
        #    mig fer i el selector se'l va endur, i la cadena va petar buscant
        #    un rebut que encara no existia. Es demana el darrer que tingui TOT
        #    el que aquesta eina llegeix.
        cal = ("4-rebuts/F1.2_sol_llenc.json", "4-rebuts/F1.3_registre.json",
               "4-rebuts/F2.2_coherencia.json", "4-rebuts/F3_filtres.json",
               "4-rebuts/F3b_protuberancies.json", "3-filtres/MASCARA.npy",
               "3-filtres/PROTUBERANCIES_rgb.npy", "3-filtres/PROTUBERANCIES_msk.npy")
        cands = []
        for d in sorted(os.listdir(os.path.join(ARREL, "1-RUNS"))):
            if "_VIXEN_CIENCIA_" not in d:
                continue
            r = os.path.join(ARREL, "1-RUNS", d)
            if all(os.path.exists(os.path.join(r, x)) for x in cal):
                cands.append(r)
        if not cands:
            raise SystemExit("cap run VIXEN CIENCIA acabat")
        a.run = cands[-1]
    vistes = a.vistes or os.path.join(os.path.dirname(a.sortida), "CapesTotalsV14_vistes")
    os.makedirs(vistes, exist_ok=True)
    print(f"run   : {os.path.basename(a.run)}")
    print(f"V13   : {V13}")
    print(f"sortida: {a.sortida}\n")

    print("[1/5] llegint la V13")
    v13 = extreu_v13(a.cau)

    print("\n[2/5] obrint el run (només lectura)")
    comu, f2, f4, run = carrega_cadena(a.run)
    from psd_tools import PSDImage
    from psd_tools.constants import BlendMode, Compression
    from psb_utils import add_pixel_layer, set_merged, finalize_lr16

    F12 = run.llegeix_rebut("F1.2_sol_llenc.json")
    F13 = run.llegeix_rebut("F1.3_registre.json")
    F3 = run.llegeix_rebut("F3_filtres.json")
    K = run.llegeix_rebut("F2.2_coherencia.json")["k"]
    S12, S13 = F12["fotogrames"], F13["fotogrames"]
    LL = F12["llenc"]; W, H = LL["W"], LL["H"]
    va = F3["corba_to"]["valor_ancora_L"]
    ctx = f2.Ctx(run)
    m = np.load(run.fase(3, "MASCARA.npy"))
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.hypot(yy - ctx.CY, xx - ctx.CX); del yy, xx
    matriu, guany = run.matriu, run.color["guany"]
    print(f"    llenç {W}×{H} · R☉ {ctx.RS:.2f} px · PA nord {LL['pa_north_deg']:.4f}° · "
          f"àncora {va:.4e}")

    grups = {}
    for n, v in S13.items():
        if v["coronal"]:
            grups.setdefault(round(v["exp"], 8), []).append(n)

    print("\n[3/5] mapes del transformat V13 → llenç comú")
    bx, by = geo_v13.mapes_base(W, H, LL["pa_north_deg"])

    # ⏭️ EL DISC LUNAR DECLARAT (mateix instant que les protuberàncies)
    prot = [n for n in run.cfg.get("prot_ingress", ()) if n in S12]
    if not prot:
        raise SystemExit("sense fotogrames de contacte de C2: no es pot declarar la Lluna")
    fora_lluna, info_lluna = disc_lluna(ctx, f2, S12, prot)
    print(f"    Lluna DECLARADA a ({info_lluna['centre_px'][0]:.2f}, "
          f"{info_lluna['centre_px'][1]:.2f}) R={ctx.RL:.2f}+{f2.GUARDA_LLUNA_PX:g} px · "
          f"{len(prot)} fotogrames de C2, dispersió {info_lluna['dispersio_px']:.2f} px")

    print("\n[4/5] capes")
    psd = PSDImage.new("RGB", (W, H), color=0, depth=16)     # PSD, versió 1
    compost = np.zeros((H, W, 3), np.float32)
    rebut = {"run": os.path.basename(a.run), "v13": V13, "llenc": LL,
             "ancora_L": va, "frac_dada": FRAC_DADA, "sigma_vora_px": SIGMA_VORA,
             "capes": []}
    rebut["lluna_declarada"] = info_lluna
    t0 = time.time()
    for num, frame, etiq, rol in CAPES:
        c13 = v13["capes"][num]
        v = S12[frame]
        n_cota = 0
        if num == "12":
            rgb, den, sup0, noms, n_cota = composa_contacte(
                comu, f2, ctx, run, S12, frame, va, m, matriu, guany)
            e = S12[frame]["exp"]
        else:
            e = round(S13[frame]["exp"], 8)
            noms = sorted(grups[e])
            pos = {n: S13[n] for n in noms}
            C, den = f2.compon(ctx, pos, {n: K[n] for n in noms}, f"{etiq}")
            tres = m.copy()
            for c in ("R", "G", "B"):
                tres &= (den[c] > 0) & np.isfinite(C[c])
            rgb, _ = comu.render_visual(
                np.dstack([C[c].astype(np.float32) for c in ("R", "G", "B")]),
                tres, va, matriu, guany)
            del C
        val, sup, tres = validesa(comu, den, rad, m)
        del den
        m13 = np.load(os.path.join(a.cau, f"mask_{num}.npy")).astype(np.float32) / 255.0
        m13w = geo_v13.warp_v13(m13, bx, by, v["sol_x"], v["sol_y"])
        del m13
        # ⛔ la Lluna DECLARADA mana sobre totes les capes: rodona per construcció
        msk = np.clip(m13w * val * fora_lluna, 0.0, 1.0)
        r_ab = rang_radial(m13w, rad, ctx.RS)
        r_de = rang_radial(msk, rad, ctx.RS, llindar=r_ab[2])
        r_va = rang_radial(val, rad, ctx.RS, llindar=0.5)
        nom = (f"{num}_{etiq}" + (f" · {rol}" if rol else "")
               + f" · {len(noms)} fot. · dada {_r(r_va[0])}-{_r(r_va[1])} R☉")
        add_pixel_layer(psd, np.clip(np.rint(rgb * 65535.0), 0, 65535).astype(np.uint16),
                        nom, mask8=(msk * 255).round().astype(np.uint8),
                        blend=BlendMode.NORMAL, opacity=c13["opacitat"],
                        visible=c13["visible"], compression=Compression.ZIP)
        if c13["visible"]:
            al = msk[..., None] * (c13["opacitat"] / 255.0)
            compost = compost * (1.0 - al) + rgb * al
        cv2.imwrite(os.path.join(vistes, f"capa_{num}_mascara_V13_portada.png"),
                    (np.clip(m13w, 0, 1) * 255).astype(np.uint8)[::8, ::8])
        cv2.imwrite(os.path.join(vistes, f"capa_{num}_mascara_V14.png"),
                    (msk * 255).astype(np.uint8)[::8, ::8])
        cv2.imwrite(os.path.join(vistes, f"capa_{num}_imatge.png"),
                    (np.clip(rgb, 0, 1) * 255).astype(np.uint8)[::8, ::8][..., ::-1])
        fora = int(((msk > 0.01) & (val <= 0.0)).sum())
        rebut["capes"].append({
            "px_saturats_declarats_cota": n_cota,
            "px_mascara_sobre_zona_sense_dada": fora,
            "num": num, "etiqueta": etiq, "rol": rol, "nom_V14": nom,
            "fotograma_V13": frame, "exposicio_s": e, "fotogrames": noms,
            "visible": c13["visible"], "opacitat": c13["opacitat"],
            "sol_del_fotograma_px": [v["sol_x"], v["sol_y"]],
            "mascara_V13_mitjana": c13["mask_mitjana"],
            "mascara_portada_mitjana": float(m13w.mean()),
            "mascara_V14_mitjana": float(msk.mean()),
            "llindar_del_rang": r_ab[2],
            "rang_mascara_V13_Rsol": r_ab[:2], "rang_validesa_Rsol": r_va[:2],
            "rang_mascara_V14_Rsol": r_de[:2],
            "px_demanats_V13": int((m13w > r_ab[2]).sum()),
            "px_conservats_V14": int((msk > r_ab[2]).sum())})
        print(f"    {nom}", flush=True)
        print(f"       màscara V13 {_r(r_ab[0])}-{_r(r_ab[1])} R☉ → V14 "
              f"{_r(r_de[0])}-{_r(r_de[1])} R☉ · mitjana "
              f"{c13['mask_mitjana']:.3f}→{msk.mean():.3f} · demanava "
              f"{fora/1e6:.2f} Mpx sense dada  [{time.time()-t0:.0f}s]", flush=True)
        del rgb, msk, m13w, val, sup, tres

    # ⏭️ EL SOL: la capa de protuberàncies de C2, en ACLARIR, a dalt de tot.
    #    És la que torna a tancar l'anell del limbe que el disc declarat i les
    #    vores de cada exposició deixen obert, i és la mateixa que la cadena
    #    posa al seu propi producte (`f4.psb_resultat`, capa 09).
    fprot = run.fase(3, "PROTUBERANCIES_rgb.npy")
    if not os.path.exists(fprot):
        raise SystemExit("el run no té PROTUBERANCIES_rgb.npy: no s'hi pot posar el Sol")
    prgb = np.load(fprot)
    pmsk = np.load(run.fase(3, "PROTUBERANCIES_msk.npy")).astype(np.float32) * fora_lluna
    F3b = run.llegeix_rebut("F3b_protuberancies.json")
    nomp = ("13_EL SOL · limbe i PROTUBERÀNCIES · C2 (ingress) · "
            f"{len(F3b['grups']['ingress']['fotogrames'])} fot. · Aclarir")
    add_pixel_layer(psd, np.clip(np.rint(prgb * 65535.0), 0, 65535).astype(np.uint16),
                    nomp, mask8=(pmsk * 255).round().astype(np.uint8),
                    blend=BlendMode.LIGHTEN, opacity=255, visible=True,
                    compression=Compression.ZIP)
    al = pmsk[..., None]
    compost = compost * (1.0 - al) + np.fmax(compost, prgb) * al
    cv2.imwrite(os.path.join(vistes, "capa_13_imatge.png"),
                (np.clip(prgb, 0, 1) * 255).astype(np.uint8)[::8, ::8][..., ::-1])
    cv2.imwrite(os.path.join(vistes, "capa_13_mascara_V14.png"),
                (pmsk * 255).astype(np.uint8)[::8, ::8])
    rebut["capes"].append({
        "num": "13", "etiqueta": "1/3200 s", "rol": "EL SOL · limbe i protuberàncies",
        "nom_V14": nomp, "fotograma_V13": None, "exposicio_s": None,
        "fotogrames": F3b["grups"]["ingress"]["fotogrames"], "visible": True,
        "opacitat": 255, "fusio": "Aclarir",
        "d_on_ve": "run · 3-filtres/PROTUBERANCIES_rgb.npy (f4.protuberancies)",
        "ancora_L": F3b.get("ancora_L"),
        "rang_validesa_Rsol": rang_radial(pmsk, rad, ctx.RS, llindar=0.5)[:2],
        "rang_mascara_V13_Rsol": [None, None], "rang_mascara_V14_Rsol":
            rang_radial(pmsk, rad, ctx.RS, llindar=0.5)[:2],
        "mascara_V14_mitjana": float(pmsk.mean()),
        "px_mascara_sobre_zona_sense_dada": 0, "px_saturats_declarats_cota": 0,
        "nota": ("no és cap capa de la V13: és el que Pere va demanar el 27-08 "
                 "—«el Sol i la Lluna que hi havia a la V13»—, i surt de la "
                 "cadena, no d'aquí")})
    print(f"    {nomp}")
    del prgb, pmsk

    print("\n[5/5] desant")
    finalize_lr16(psd)
    # ⛔ LA IMATGE FUSIONADA VA EN CRU. Mesurat el 27-08-2026 amb una matriu de
    #    2 formats × 4 compressions: amb `ZIP` o `ZIP_WITH_PREDICTION` a la
    #    secció d'`Image Data` **ni ImageIO ni Photoshop obren el fitxer** —
    #    Photoshop diu «no és compatible amb aquesta versió»— i passa igual a
    #    PSD i a PSB, o sigui que no és cosa del format. `RAW` i `RLE` van bé.
    #    Es fa servir `RAW`, que és el que `f4.set_merged` ja feia servir a tots
    #    els lliurables del projecte. Costa 435 MB.
    #    ⚠️ Les capes SÍ que van en ZIP: allà la compressió no és el problema.
    set_merged(psd, np.clip(np.rint(compost * 65535.0), 0, 65535).astype(np.uint16),
               compression=Compression.RAW)
    if getattr(psd, "_updated", False):
        psd._updated = False
    psd.save(a.sortida)
    n = os.path.getsize(a.sortida)
    comprova_obrible(a.sortida, W, H, len(CAPES) + 1)   # +1: la capa del Sol
    rebut["fitxer"] = a.sortida; rebut["bytes"] = n
    cv2.imwrite(os.path.join(vistes, "V14_compost.png"),
                (np.clip(compost, 0, 1) * 255).astype(np.uint8)[::8, ::8][..., ::-1])
    json.dump(rebut, open(os.path.join(vistes, "REBUT_V14.json"), "w"),
              indent=1, ensure_ascii=False)
    print(f"    {a.sortida} · {n/1e9:.2f} GB")
    if n > 2_000_000_000:
        print("    ⛔ PASSA DE 2 GB: el format PSD no hi arriba, cal PSB")
    return rebut


if __name__ == "__main__":
    main()
