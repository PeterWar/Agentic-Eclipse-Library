"""FASE 4 · Els projectes de Photoshop i les vistes.

⛔ La BASE és l'única capa amb sentit fotomètric. La resta són maneres de veure.
⛔ Norma del rectangle: cap capa retallada a cap circumferència.
⛔ Totes les capes surten de dada que JA porta el balanç de blancs (va a
   `calibra_pla`), i totes fan servir la MATEIXA àncora de to.
"""

from __future__ import annotations

import math
import os
import sys
import time
from collections import defaultdict

import numpy as np
import cv2
from astropy.io import fits

sys.path.insert(0, "/Users/USUARI/Downloads/Eclipse 2026/research/tools/encaix_sony")
import comu
import f2
import ajust


def u16(a):
    return np.clip(np.rint(np.asarray(a, np.float64) * 65535.0), 0, 65535).astype(np.uint16)


def gris(a):
    return np.dstack([a, a, a])


def nom_capa_ldic(e, n, msk, rad, RS):
    """El nom d'una capa LDIC diu FINS ON VAL.

    ⏭️ Cada exposicio te la seva vora interior —el radi on deixa d'estar
    saturada— i aquella vora, renderitzada, es EXACTAMENT un halo al voltant de
    la Lluna. El 27-08-2026 Pere va marcar la del 1/8 s (1,19 R☉) creient que
    era un artefacte del producte, i tenia tota la rao de marcar-la: el fitxer
    s'obre amb una capa visible i RES no li deia que aquella vora es el limit de
    l'exposicio i no un defecte. Amb el rang al nom, la vora s'explica sola.
    """
    vis = msk > 0.5
    if not vis.any():
        return f"LDIC {e:g}s ({n} fot.) · SENSE PES ENLLOC"
    rr = rad[vis] / RS
    return (f"LDIC {e:g}s ({n} fot.) · val "
            f"{float(np.percentile(rr, 0.5)):.2f}-{float(np.percentile(rr, 99.5)):.2f} R☉")


def _ctx_i_mapes(run):
    ctx = f2.Ctx(run)
    yy, xx = np.mgrid[0:ctx.H, 0:ctx.W].astype(np.float32)
    rad = np.hypot(yy - ctx.CY, xx - ctx.CX); del yy, xx
    m = np.load(run.fase(3, "MASCARA.npy"))
    va = run.llegeix_rebut("F3_filtres.json")["corba_to"]["valor_ancora_L"]
    return ctx, rad, m, va


# ------------------------------------------------------------- resultat


def psb_resultat(run: comu.Run) -> dict:
    from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16
    from psd_tools.constants import BlendMode
    ctx, rad, m, va = _ctx_i_mapes(run)
    base = np.load(run.fase(3, "BASE_rgb.npy"))
    P = fits.getdata(run.fase(2, "PES_G.fits")).astype(np.float32)
    pes = np.where(m, P / float(np.nanmax(P)), 0.0).astype(np.float32)
    S = fits.getdata(run.fase(2, "CEL_S.fits")).astype(np.float32)
    lo, hi = float(np.nanmin(S[m])), float(np.nanmax(S[m]))
    cel = np.where(m, (S - lo) / max(hi - lo, 1e-9), 0.0).astype(np.float32)

    extra = []
    if run.mode == "CIENCIA":
        # ⏭️ La MATEIXA dada dividida per l'extinció declarada: la corona tal com
        # es veuria SOBRE l'atmosfera, que és la que lliura Brno. La lluminància
        # es conserva, o sigui que només canvia el color.
        vec = np.asarray(comu.EXTINCIO["nomes_extincio"], np.float32)
        lin = comu.a_lineal(base)
        pes3 = np.array([0.25, 0.5, 0.25], np.float32)
        L0 = lin @ pes3
        u = lin / vec
        L1 = u @ pes3
        u *= np.where(L1 > 1e-9, L0 / np.maximum(L1, 1e-9), 0.0)[..., None]
        extra = [("07 SOBRE L'ATMOSFERA (÷ extinció DECLARADA)",
                  np.where(m[..., None], comu.a_srgb(u), 0.0).astype(np.float32),
                  "NORMAL", False)]
        del u
        # ⏭️ I la versió de Brno: blanquejar sobre la corona MESURADA. La
        # DIFERÈNCIA entre 07 i 08 és el residu que l'extinció NO explica —
        # corona F, línies E i model—, i per això van totes dues.
        cs = run.llegeix_rebut("F3_filtres.json").get("color_renderitzat_sRGB_lineal", {})
        k = "1.1Rsol" if "1.1Rsol" in cs else (sorted(cs)[0] if cs else None)
        if k:
            vc = np.array([cs[k]["R/G"], 1.0, cs[k]["B/G"]], np.float32)
            u2 = lin / vc
            L2 = u2 @ pes3
            u2 *= np.where(L2 > 1e-9, L0 / np.maximum(L2, 1e-9), 0.0)[..., None]
            extra.append((f"08 CORONA NEUTRA (÷ el color mesurat a {k} · com Brno)",
                          np.where(m[..., None], comu.a_srgb(u2), 0.0).astype(np.float32),
                          "NORMAL", False))
            del u2, L2
        del lin, L0, L1
    pr = _capa_protuberancies(run)
    if pr is not None:
        extra = extra + [(nom_capa_prot(run, "09"), pr[0], "LIGHTEN", True)]
    capes = [(f"00 BASE · {run.color['titol']} · cel POSAT", base, "NORMAL", True),
             ("01 DETALL passa-alt (mediana RGB)",
              gris(np.load(run.fase(3, "DETALL_PASSA_ALT.npy"))), "OVERLAY", True),
             ("02 DETALL radial · plomalls",
              gris(np.load(run.fase(3, "DETALL_RADIAL.npy"))), "OVERLAY", False),
             ("03 DETALL NRGF", gris(np.load(run.fase(3, "DETALL_NRGF.npy"))), "OVERLAY", False),
             ("04 DETALL MGN", gris(np.load(run.fase(3, "DETALL_MGN.npy"))), "OVERLAY", False),
             ("05 diagnòstic · CEL restat", gris(cel), "NORMAL", False),
             ("06 diagnòstic · MAPA DE PES", gris(pes), "NORMAL", False)] + extra
    psd = new_psb(ctx.W, ctx.H)
    mk = (m.astype(np.uint8) * 255)
    BM = {"NORMAL": BlendMode.NORMAL, "OVERLAY": BlendMode.OVERLAY,
          "LIGHTEN": BlendMode.LIGHTEN}
    t0 = time.time()
    for nom, arr, bl, vis in capes:
        mm = (pr[1].astype(np.uint8) * 255) if (pr is not None and nom.startswith("09")) else mk
        add_pixel_layer(psd, u16(arr), nom[:250], mask8=mm, blend=BM[bl], visible=vis)
        print(f"      {nom}  [{time.time()-t0:.0f}s]", flush=True)
    for nom, mena in (("AJUST · Exposició", "Exposició"), ("AJUST · Nivells", "Nivells"),
                      ("AJUST · Corbes", "Corbes")):
        ajust.afegeix(psd, nom, mena, visible=True)
    finalize_lr16(psd); set_merged(psd, u16(base))
    if getattr(psd, "_updated", False):
        psd._updated = False
    dst = run.lliurable(f"Eclipsi_2026_{run.tren}_{run.mode}.psb")
    psd.save(dst)
    info = {"fitxer": os.path.basename(dst), "bytes": os.path.getsize(dst),
            "llenc": [ctx.W, ctx.H],
            "capes": [c[0] for c in capes] + ["AJUST · Exposició", "AJUST · Nivells",
                                              "AJUST · Corbes"]}
    run.desa_rebut("F4.1_psb_resultat.json", info)
    print(f"    {os.path.basename(dst)} · {info['bytes']/1e9:.2f} GB · "
          f"{len(info['capes'])} capes", flush=True)
    return info


# ------------------------------------- protuberàncies dels contactes (C2/C3)

# ⏭️ Llibertat creativa DECLARADA, demanada per Pere el 27-08 i presa de
#    Druckmüller: ensenyar alhora les protuberàncies de just DESPRÉS de C2 i
#    de just ABANS de C3. No és un instant: és una unió de dos instants, i el
#    negre que en queda és la INTERSECCIÓ dels dos discos lunars, no un cercle.
#    L'egress surt de `572A3016.CR3`, que és el fotograma que va triar Pere.
PROT_INGRESS = ("572A2963.CR3", "572A2964.CR3", "572A2965.CR3", "572A2966.CR3")
PROT_EGRESS = ("572A3014.CR3", "572A3015.CR3", "572A3016.CR3",
               "572A3017.CR3", "572A3018.CR3")


def calcula_protuberancies(run: comu.Run) -> dict:
    """Pas de cadena: calcula-ho UNA vegada i desa-ho per als dos PSB."""
    rgb, msk, info = protuberancies(run)
    if rgb is None:
        info["porta"] = "SENSE DADA"
    else:
        np.save(run.fase(3, "PROTUBERANCIES_rgb.npy"), rgb)
        np.save(run.fase(3, "PROTUBERANCIES_msk.npy"), msk)
        info["porta"] = "PASSA"
        print("    " + " · ".join(f"{k}: {len(v['fotogrames'])} fotogrames t={v['t'][0]}-{v['t'][-1]}s"
                                  for k, v in info["grups"].items()), flush=True)
    run.desa_rebut("F3b_protuberancies.json", info)
    return info


def nom_capa_prot(run, num: str) -> str:
    """El nom diu quins contactes hi ha DE VERITAT, no quins n'hi podria haver."""
    q = {"ingress": "C2 (ingress)", "egress": "C3 (egress)"}
    try:
        g = list(run.llegeix_rebut("F3b_protuberancies.json")["grups"])
    except Exception:                                    # noqa: BLE001
        g = list(comu.CONTACTES_AL_PRODUCTE)
    return f"{num} PROTUBERÀNCIES · {' + '.join(q.get(k, k) for k in g)} · Aclarir"


def _capa_protuberancies(run):
    f = run.fase(3, "PROTUBERANCIES_rgb.npy")
    if not os.path.exists(f):
        return None
    return (np.load(f), np.load(run.fase(3, "PROTUBERANCIES_msk.npy")))


def protuberancies(run: comu.Run):
    """Composició dels contactes DECLARATS, cadascun amb la SEVA màscara lunar."""
    ctx = f2.Ctx(run)
    S = run.llegeix_rebut("F1.2_sol_llenc.json")["fotogrames"]
    K = run.llegeix_rebut("F2.2_coherencia.json")["k"]
    # ⛔ Els noms eren de la R6 III escrits a ma: amb un tren nou la fase es
    #    quedava muda tenint fotogrames de contacte. Ara son del TREN.
    cfgp = run.cfg
    tots = {"ingress": [n for n in cfgp.get("prot_ingress", PROT_INGRESS) if n in S],
            "egress": [n for n in cfgp.get("prot_egress", PROT_EGRESS) if n in S]}
    # ⛔ Només els contactes que Pere ha declarat (`comu.CONTACTES_AL_PRODUCTE`).
    #    Els altres es continuen anotant al rebut: que no surtin al producte no
    #    vol dir que no s'hagin vist.
    grups = {k: v for k, v in tots.items() if k in comu.CONTACTES_AL_PRODUCTE}
    acc = None; msk = np.zeros((ctx.H, ctx.W), bool)
    info = {"grups": {}, "contactes_al_producte": list(comu.CONTACTES_AL_PRODUCTE),
            "fora_del_producte": {k: v for k, v in tots.items()
                                  if k not in comu.CONTACTES_AL_PRODUCTE and v},
            "per_que": ("decisió de Pere del 27-08-2026: amb els dos extrems, el "
                        "negre que queda és la intersecció dels dos discos lunars "
                        "(la Lluna llisca ~28,5 px entre C2 i C3 sobre un llenç "
                        "centrat al Sol) i la Lluna surt deformada")}
    for etiq, noms in grups.items():
        if not noms:
            continue
        gacc = None; gmsk = np.zeros((ctx.H, ctx.W), bool)
        for n in noms:
            v = S[n]; e = v["exp"]; k = K.get(n, 1.0)
            cai = ctx.caixa(v["sol_x"], v["sol_y"]); y0, y1, x0, x1 = cai
            rx, ry = ctx.mapes(v["sol_x"], v["sol_y"], cai)
            fll = f2.mascara_lluna(ctx, v, rx, ry)
            num = np.zeros((ctx.H, ctx.W, 3), np.float32)
            den = np.zeros((ctx.H, ctx.W, 3), np.float32)
            for i, (pl, w) in ctx.plans(n, e).items():
                oy, ox = ctx.orig[i]
                mx = ((rx - ox) * 0.5).astype(np.float32); my = ((ry - oy) * 0.5).astype(np.float32)
                j = comu.IDX_CANAL[i]
                ok = (w > 0).astype(np.float32)
                num[y0:y1, x0:x1, j] += cv2.remap(pl * k * ok, mx, my, cv2.INTER_LINEAR,
                                                  borderValue=0.0) * fll
                den[y0:y1, x0:x1, j] += cv2.remap(ok, mx, my, cv2.INTER_LINEAR,
                                                  borderValue=0.0) * fll
            im = np.where(den > 0.5, num / np.maximum(den, 1e-9), np.nan).astype(np.float32)
            bo = np.isfinite(im).all(axis=2)
            # ⏭️ MÀXIM dins del grup: la Lluna es mou i cada fotograma en
            #    destapa un tros diferent; el màxim els uneix.
            gacc = np.where(bo[..., None], im, -np.inf) if gacc is None else \
                np.fmax(gacc, np.where(bo[..., None], im, -np.inf))
            gmsk |= bo
            del num, den, im
        info["grups"][etiq] = {"fotogrames": noms,
                               "t": [round(S[n]["t"], 2) for n in noms],
                               "px": int(gmsk.sum())}
        acc = gacc if acc is None else np.fmax(acc, gacc)
        msk |= gmsk
    if acc is None:
        return None, None, info
    acc = np.where(np.isfinite(acc) & msk[..., None], acc, np.nan).astype(np.float32)
    yy, xx = np.mgrid[0:ctx.H, 0:ctx.W].astype(np.float32)
    rad = np.hypot(yy - ctx.CY, xx - ctx.CX); del yy, xx
    L, _ = comu.lluminancia(np.nan_to_num(acc), run.matriu, run.color["guany"])
    an = msk & (rad > 1.00 * ctx.RS) & (rad < 1.20 * ctx.RS)
    va = float(np.nanpercentile(np.where(an, L, np.nan), 99.9)) if an.sum() > 1000 else \
        float(np.nanmedian(L[msk]))
    rgb, ren = comu.render_visual(np.nan_to_num(acc), msk, va, run.matriu,
                                  run.color["guany"], anc=1.0)
    info["ancora_L"] = va
    info["nota"] = ("unió de dos instants; el negre és la INTERSECCIÓ dels dos "
                    "discos lunars, no un cercle")
    return rgb, msk, info


# ------------------------------- EL PROJECTE SENCER: filtres + capes LDIC


def psb_tot(run: comu.Run) -> dict:
    """Un sol projecte amb la base, TOTS els filtres i TOTES les capes LDIC.

    Demanat per Pere el 26-08: «un cop tinguis tots els filtres modificats,
    posa-me'ls junt amb les capes LDIC en un projecte de photoshop».

    ⛔ Les capes LDIC apilades NO reprodueixen el compost (`Σ(wI)/Σw` no és una
    composició alfa i depèn de l'ordre): hi són per jutjar-les d'una en una.
    Per això surten totes apagades i la que mana és la BASE.
    """
    from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16
    from psd_tools.constants import BlendMode
    ctx, rad, m, va = _ctx_i_mapes(run)
    base = np.load(run.fase(3, "BASE_rgb.npy"))
    psd = new_psb(ctx.W, ctx.H)
    mk = (m.astype(np.uint8) * 255)
    t0 = time.time(); noms = []

    add_pixel_layer(psd, u16(base), f"00 BASE · {run.color['titol']}"[:250],
                    mask8=mk, blend=BlendMode.NORMAL, visible=True)
    noms.append("00 BASE")
    print(f"      00 BASE  [{time.time()-t0:.0f}s]", flush=True)
    for i, (k, et) in enumerate((("PASSA_ALT", "passa-alt"), ("RADIAL", "radial · plomalls"),
                                 ("NRGF", "NRGF"), ("MGN", "MGN")), start=1):
        f = run.fase(3, f"DETALL_{k}.npy")
        if not os.path.exists(f):
            continue
        nom = f"{i:02d} FILTRE · {et}"
        add_pixel_layer(psd, u16(gris(np.load(f))), nom[:250], mask8=mk,
                        blend=BlendMode.OVERLAY, visible=(k == "PASSA_ALT"))
        noms.append(nom)
        print(f"      {nom}  [{time.time()-t0:.0f}s]", flush=True)

    pr = _capa_protuberancies(run)
    if pr is not None:
        nom = nom_capa_prot(run, "05")
        add_pixel_layer(psd, u16(pr[0]), nom[:250],
                        mask8=(pr[1].astype(np.uint8) * 255),
                        blend=BlendMode.LIGHTEN, visible=True)
        noms.append(nom)
        print(f"      {nom}  [{time.time()-t0:.0f}s]", flush=True)

    S = run.llegeix_rebut("F1.3_registre.json")["fotogrames"]
    K = run.llegeix_rebut("F2.2_coherencia.json")["k"]
    grups = defaultdict(list)
    for n, v in sorted(S.items()):
        if v["coronal"]:
            grups[round(v["exp"], 8)].append(n)
    for e in sorted(grups):
        pos = {n: S[n] for n in grups[e]}
        C, den = f2.compon(ctx, pos, {n: K[n] for n in pos}, f"{e:g}s")
        tres = np.ones_like(m)
        for c in comu.CANALS:
            tres &= (den[c] > 0) & np.isfinite(C[c])
        rgb, _r = comu.render_visual(np.dstack([C[c].astype(np.float32) for c in comu.CANALS]),
                                     tres & m, va, run.matriu, run.color["guany"])
        msk = np.where(tres, np.clip(den["G"] / max(float(np.nanmax(den["G"])), 1e-9), 0, 1), 0.0)
        nom = nom_capa_ldic(e, len(grups[e]), msk, rad, ctx.RS)
        add_pixel_layer(psd, u16(rgb), nom[:250], mask8=(msk * 255).astype(np.uint8),
                        blend=BlendMode.NORMAL, visible=False)
        noms.append(nom)
        print(f"      {nom:36s} [{time.time()-t0:.0f}s]", flush=True)
        del C, den, rgb, msk, tres

    for nom, mena in (("AJUST · Exposició", "Exposició"), ("AJUST · Nivells", "Nivells"),
                      ("AJUST · Corbes", "Corbes")):
        ajust.afegeix(psd, nom, mena, visible=True)
        noms.append(nom)
    finalize_lr16(psd); set_merged(psd, u16(base))
    if getattr(psd, "_updated", False):
        psd._updated = False
    dst = run.lliurable(f"Eclipsi_2026_{run.tren}_{run.mode}_TOT.psb")
    psd.save(dst)
    info = {"fitxer": os.path.basename(dst), "bytes": os.path.getsize(dst),
            "llenc": [ctx.W, ctx.H], "capes": noms, "n_capes": len(noms),
            "nota": "les capes LDIC apilades NO reprodueixen el compost"}
    run.desa_rebut("F4.4_psb_tot.json", info)
    print(f"    {os.path.basename(dst)} · {info['bytes']/1e9:.2f} GB · {len(noms)} capes",
          flush=True)
    return info


# ----------------------------------------------------- capes LDIC (Pere)


def psb_capes_ldic(run: comu.Run) -> dict:
    """Una capa per esglaó d'exposició, amb la seva màscara de pes.

    ⛔ Apilades a Photoshop NO reprodueixen el compost: la composició alfa depèn
    de l'ordre i `Σ(wI)/Σw` no. Són per jutjar-les d'una en una, que és el que
    el contracte de fases demana.

    ⏭️ Cada capa duu al NOM el rang de radis on val. Sense això, la vora interior
    d'una exposició —el radi on deixa d'estar saturada— sembla un halo al
    voltant de la Lluna, i no hi ha manera de saber que és el límit de la capa
    i no un artefacte del producte (27-08-2026).
    """
    from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16
    from psd_tools.constants import BlendMode
    ctx, rad, m, va = _ctx_i_mapes(run)
    S = run.llegeix_rebut("F1.3_registre.json")["fotogrames"]
    K = run.llegeix_rebut("F2.2_coherencia.json")["k"]
    grups = defaultdict(list)
    for n, v in sorted(S.items()):
        if v["coronal"]:
            grups[round(v["exp"], 8)].append(n)
    psd = new_psb(ctx.W, ctx.H)
    t0 = time.time(); info = {"esglaons": {}}
    for e in sorted(grups):
        pos = {n: S[n] for n in grups[e]}
        C, den = f2.compon(ctx, pos, {n: K[n] for n in pos}, f"{e:g}s")
        # ⏭️ el cel NO es resta: la capa ha de viure al mateix renderitzat que
        # la base, o comparar-les no vol dir res.
        lin = {c: C[c].astype(np.float32) for c in comu.CANALS}
        # ⛔ La màscara exigeix ELS TRES CANALS. A 1/3200 s el blau de la corona
        # val 9 DN i el terra de soroll és 12: aquelles exposicions NO tenen
        # blau, i pintar-ho de terra opac per canal és el que feia les capes
        # verdes. Amb la màscara de tres canals, allà on falta un canal la capa
        # és TRANSPARENT, que és el que la dada diu de veritat.
        tres = np.ones_like(m)
        for c in comu.CANALS:
            tres &= (den[c] > 0) & np.isfinite(lin[c])
        rgb, _ren = comu.render_visual(np.dstack([lin[c] for c in comu.CANALS]),
                                       tres & m, va, run.matriu, run.color["guany"])
        msk = np.where(tres, np.clip(den["G"] / max(float(np.nanmax(den["G"])), 1e-9), 0, 1), 0.0)
        nom = nom_capa_ldic(e, len(grups[e]), msk, rad, ctx.RS)
        add_pixel_layer(psd, u16(rgb), nom, mask8=(msk * 255).astype(np.uint8),
                        blend=BlendMode.NORMAL, visible=(e == sorted(grups)[len(grups) // 2]))
        # ⏭️ el color es mesura sobre la dada LINEAL, no sobre la corba de to:
        # a l'espai de la corba, R/G no és el color, és un quocient de nivells.
        col = comu.mesura_color(lin, rad, tres & m, ctx.RS)
        cob3 = float(100 * (tres & m).mean())
        ver = comu.veredicte_color(col) if cob3 >= 5.0 else "capa d un sol canal (sense blau)"
        info["esglaons"][f"{e:g}"] = {
            "n": len(grups[e]),
            "cobertura_G_pct": float(100 * (den["G"] > 0).mean()),
            "cobertura_tres_canals_pct": cob3,
            "cobertura_per_canal_pct": {c: float(100 * (den[c] > 0).mean()) for c in comu.CANALS},
            "color_lineal": col, "veredicte_color": ver}
        print(f"      {nom:36s} cob G {100*(den['G']>0).mean():5.1f} % · RGB {cob3:5.1f} % · "
              f"{ver}  [{time.time()-t0:.0f}s]", flush=True)
    finalize_lr16(psd)
    set_merged(psd, u16(np.load(run.fase(3, "BASE_rgb.npy"))))
    if getattr(psd, "_updated", False):
        psd._updated = False
    dst = run.lliurable(f"Eclipsi_2026_{run.tren}_{run.mode}_capes_LDIC.psb")
    psd.save(dst)
    info["fitxer"] = os.path.basename(dst); info["bytes"] = os.path.getsize(dst)
    dolents = [k for k, v in info["esglaons"].items() if v["veredicte_color"].startswith("⛔")]
    if dolents:
        raise SystemExit(f"PORTA F4.2: capes VERDES: {dolents}")
    info["porta"] = "PASSA"
    run.desa_rebut("F4.2_capes_ldic.json", info)
    print(f"    {os.path.basename(dst)} · {info['bytes']/1e9:.2f} GB · "
          f"{len(grups)} capes · cap verda ✓", flush=True)
    return info


# --------------------------------------------------------- contactes


def psb_contactes(run: comu.Run) -> dict:
    from psb_utils import new_psb, add_pixel_layer, set_merged, finalize_lr16
    from psd_tools.constants import BlendMode
    ctx, rad, m_, va = _ctx_i_mapes(run)
    # ⛔ Els fotogrames de contacte NO són al rebut F1.3: aquell només porta els
    # coronals (són els únics que es refinen per correlació). Els de contacte
    # van amb la posició del MODEL, que és el que el contracte de fases diu.
    F12 = run.llegeix_rebut("F1.2_sol_llenc.json")
    S = F12["fotogrames"]
    CT = F12["contactes"]
    c2, c3 = CT["C2_t"], CT["C3_t"]
    grups = {"C2 · perles i PRIMER ANELL DE DIAMANT": [],
             "C3 · SEGON ANELL DE DIAMANT i perles": [],
             "parcial abans de C2 (documental)": [],
             "parcial després de C3 (documental)": []}
    for n, v in sorted(S.items()):
        t = v["t"]
        if v["coronal"]:
            continue
        if c2 - 4 <= t <= c2 + 2:
            grups["C2 · perles i PRIMER ANELL DE DIAMANT"].append(n)
        elif c3 - 2 <= t <= c3 + 4:
            grups["C3 · SEGON ANELL DE DIAMANT i perles"].append(n)
        elif t < c2:
            grups["parcial abans de C2 (documental)"].append(n)
        else:
            grups["parcial després de C3 (documental)"].append(n)

    def posa(n):
        v = S[n]; e = v["exp"]
        cai = (0, ctx.H, 0, ctx.W)
        rx, ry = ctx.mapes(v["sol_x"], v["sol_y"], cai)
        num = np.zeros((ctx.H, ctx.W, 3), np.float32); den = np.zeros((ctx.H, ctx.W, 3), np.float32)
        for i, (pl, w) in ctx.plans(n, e).items():
            oy, ox = ctx.orig[i]
            mx = ((rx - ox) * 0.5).astype(np.float32); my = ((ry - oy) * 0.5).astype(np.float32)
            ok = (w > 0).astype(np.float32)
            j = comu.IDX_CANAL[i]
            num[..., j] += cv2.remap(pl * ok, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
            den[..., j] += cv2.remap(ok, mx, my, cv2.INTER_LINEAR, borderValue=0.0)
        im = np.where(den > 0.5, num / np.maximum(den, 1e-9), np.nan).astype(np.float32)
        fo = (rad > 6.0 * ctx.RS) & np.isfinite(im).all(axis=2)
        if fo.sum() > 50000:
            for i in range(3):
                im[..., i] -= float(np.median(im[fo, i]))
        return im

    psd = new_psb(ctx.W, ctx.H); t0 = time.time(); info = {"capes": {}}; primera = None
    for nom in ("C2 · perles i PRIMER ANELL DE DIAMANT",
                "C3 · SEGON ANELL DE DIAMANT i perles",
                "parcial abans de C2 (documental)",
                "parcial després de C3 (documental)"):
        noms = sorted(grups[nom])
        if not noms:
            continue
        mode = "max" if nom.startswith(("C2", "C3")) else "mediana"
        if mode == "mediana":
            noms = noms[::3]
        acc = None
        for n in noms:
            im = posa(n)
            acc = im if acc is None else (np.fmax(acc, im) if mode == "max"
                                          else np.nanmean(np.stack([acc, im]), axis=0))
        mm = np.isfinite(acc).all(axis=2)
        # ⏭️ àncora COMUNA per capa (percentil alt del verd): un anell de diamant
        # no té anell d'àncora coronal, però el color ha de sobreviure igual.
        Lc, _ = comu.lluminancia(acc, run.matriu, run.color["guany"])
        vac = float(np.nanpercentile(np.where(mm, Lc, np.nan), 99.99))
        rgb, _ren = comu.render_visual(acc, mm, vac, run.matriu, run.color["guany"], anc=1.0)
        add_pixel_layer(psd, u16(rgb), nom, mask8=(mm.astype(np.uint8) * 255),
                        blend=BlendMode.NORMAL, visible=(primera is None))
        if primera is None:
            primera = u16(rgb)
        # ⛔ CADA CAPA ES JUTJA ON VIU. `mesura_color` mira els anells 1,1 · 2 ·
        #    3 · 5 R☉, que son CORONALS: una capa de CONTACTE —perles i anell de
        #    diamant— alla no hi te senyal, nomes soroll, i el veredicte «verda»
        #    mesurava el soroll. El 27-08 aixo va tombar el Run 2 de la Sony amb
        #    una capa de C2 perfectament bona. La proteccio de debo contra el
        #    verd la fa la porta F4.2 sobre les capes LDIC, que si que tenen
        #    corona; repetir-la aqui no protegia de res.
        C_ = {c: acc[..., i].astype(np.float64) for i, c in enumerate(comu.CANALS)}
        contacte = nom.startswith(("C2", "C3"))
        radis = (1.0, 1.05, 1.10) if contacte else (1.1, 2.0, 3.0, 5.0)
        col = comu.mesura_color(C_, rad, mm, ctx.RS, radis=radis)
        col_cor = comu.mesura_color(C_, rad, mm, ctx.RS) if contacte else col
        ver = comu.veredicte_color(col)
        info["capes"][nom] = {"n": len(noms), "mode": mode, "fotogrames": noms,
                              "jutjat_a_R☉": list(radis),
                              "color_lineal": col, "veredicte_color": ver}
        if contacte:
            info["capes"][nom]["color_als_anells_coronals"] = col_cor
            info["capes"][nom]["nota"] = ("una capa de contacte no te senyal als "
                                          "anells coronals: alla el color es soroll")
        print(f"      {nom:44s} {mode:8s} n={len(noms):2d} · {ver}"
              f"  [{time.time()-t0:.0f}s]", flush=True)
    if primera is None:
        raise SystemExit("PORTA F4.3: cap capa de contacte. Comprova la "
                         "classificació coronal/contacte contra C2 i C3.")
    finalize_lr16(psd); set_merged(psd, primera)
    if getattr(psd, "_updated", False):
        psd._updated = False
    dst = run.lliurable(f"Eclipsi_2026_{run.tren}_{run.mode}_contactes.psb")
    psd.save(dst)
    info["fitxer"] = os.path.basename(dst); info["bytes"] = os.path.getsize(dst)
    info["C2_t"] = c2; info["C3_t"] = c3; info["totalitat_s"] = CT["totalitat_s"]
    dolents = [k for k, v in info["capes"].items() if v["veredicte_color"].startswith("⛔")]
    if dolents:
        raise SystemExit(f"PORTA F4.3: capes VERDES: {dolents}")
    info["porta"] = "PASSA"
    run.desa_rebut("F4.3_contactes.json", info)
    return info
