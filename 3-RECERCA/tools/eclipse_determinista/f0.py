"""FASE 0 · Calibració — només l'instrument. Res del cel.

Ordre obligatori per fotograma: pedestal real mesurat → restar el dark de la
seva exposició → dividir pel flat. ⛔ El flat va ABANS de qualsevol warp.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from collections import Counter, defaultdict

import numpy as np
import rawpy
from astropy.io import fits

import comu

BANDA = 512
LLINDAR_ALT = 12000


def exposicions(carpeta: str) -> dict[str, float]:
    o = subprocess.run(["exiftool", "-q", "-n", "-T", "-FileName", "-ExposureTime",
                        carpeta], capture_output=True, text=True, timeout=1800).stdout
    d = {}
    for l in o.splitlines():
        p = l.split("\t")
        if len(p) >= 2:
            try:
                d[p[0]] = float(p[1])
            except ValueError:
                pass
    return dict(sorted(d.items()))


# --------------------------------------------------- 0.1 pedestal i blanc


def pedestal_i_blanc(run: comu.Run, n_llums: int = 121, n_darks_exp: int = 6) -> dict:
    cfg = run.cfg
    llums = comu.entrades(run.tren, "totalitat")[:n_llums]
    darks = comu.entrades(run.tren, "darks")
    exp_d = exposicions(os.path.join(cfg["dir"], "darks"))
    per_exp = defaultdict(list)
    for p in darks:
        per_exp[exp_d.get(os.path.basename(p), -1.0)].append(p)
    tria = [p for e in sorted(per_exp) for p in sorted(per_exp[e])[:n_darks_exp]]

    # ⏭️ D'ON SURT EL PEDESTAL. La R6 III té marge esquerre emmascarat i s'hi
    #    mesura fotograma a fotograma, que és millor perquè segueix la
    #    temperatura. ⛔ L'A7RIIIA NO TÉ CAP ZONA EMMASCARADA (`raw_width` 8000
    #    contra `width` 7968, i les 32 columnes que sobren veuen llum: a 8 s
    #    marquen 3436 DN), o sigui que allà el pedestal ha de sortir dels DARKS
    #    i és un número per run, no per fotograma.
    font = cfg.get("pedestal_font", "marge")
    if font not in ("marge", "darks"):
        raise SystemExit(f"pedestal_font desconegut: {font}")

    def mesura(ruta, amb_fosc=True):
        with rawpy.imread(ruta) as r:
            g = comu.geometria(r); mc = comu.mapa_colors(r); ri = r.raw_image
            negre = list(r.black_level_per_channel); blanc = int(r.white_level)
            vis = np.zeros((g.alt, g.ample), bool); vis[g.visible] = True
            fosc = comu.zona_fosca(g)[0] if amb_fosc else vis
            fila = {"negre_libraw": negre, "blanc_libraw": blanc, "canals": {}}
            for i in range(4):
                d = ri[fosc & (mc == i)].astype(np.float64)
                v = ri[vis & (mc == i)]
                alts = v[v >= LLINDAR_ALT]
                pic = max(Counter(alts.tolist()).items(), key=lambda kv: kv[1]) if alts.size else None
                fila["canals"][comu.nom_canal(i, g.desc)] = {
                    "pedestal_mediana": float(np.median(d)),
                    "pedestal_mitjana": float(d.mean()),
                    "sigma_lectura": float(d.std()),
                    "max_visible": int(v.max()),
                    "pic_alt": None if pic is None else [int(pic[0]), int(pic[1])],
                }
            return fila

    t0 = time.time()
    amb = (font == "marge")
    fl = {os.path.basename(p): mesura(p, amb) for p in llums}
    print(f"    llums {len(fl)}  [{time.time()-t0:.0f}s]", flush=True)
    fd = {os.path.basename(p): mesura(p, amb) for p in tria}
    print(f"    darks {len(fd)}  [{time.time()-t0:.0f}s]", flush=True)

    def resum(d):
        out = {}
        for nom in comu.NOMS:
            med = np.array([f["canals"][nom]["pedestal_mediana"] for f in d.values()])
            sig = np.array([f["canals"][nom]["sigma_lectura"] for f in d.values()])
            out[nom] = {"mediana": float(np.median(med)),
                        "min": float(med.min()), "max": float(med.max()),
                        "sigma_lectura": float(sig.mean())}
        return out

    pics = Counter()
    for f in fl.values():
        for nom in comu.NOMS:
            p = f["canals"][nom]["pic_alt"]
            if p and p[1] > 1000:
                pics[p[0]] += 1
    sat = max(pics.items(), key=lambda kv: kv[1])[0] if pics else None

    with rawpy.imread(llums[0]) as _r:
        _g = comu.geometria(_r)
    zona = (comu.zona_fosca(_g)[1] if amb
            else "ZONA ACTIVA dels DARKS (aquest cos no té marge emmascarat)")
    r = {"cos": cfg["cos"], "n_llums": len(fl), "n_darks": len(fd),
         "pedestal_font": font, "zona_mesura": zona,
         "resum_llums": resum(fl), "resum_darks": resum(fd),
         "negre_libraw": fl[list(fl)[0]]["negre_libraw"],
         "blanc_libraw": fl[list(fl)[0]]["blanc_libraw"],
         "saturacio_mesurada": sat,
         "saturacio_declarada": cfg["saturacio_dn"],
         "pedestal_declarat": cfg["pedestal_dn"],
         "per_fotograma": {"llums": fl, "darks": fd}}

    # ⛔ Sense marge emmascarat, la mediana dels LLUMS és corona, no pedestal:
    #    el número que mana és el dels DARKS.
    ped = r["resum_darks" if font == "darks" else "resum_llums"]["G1"]["mediana"]
    if abs(ped - cfg["pedestal_dn"]) > 1.0:
        raise SystemExit(f"PORTA F0.1: pedestal mesurat {ped} != declarat {cfg['pedestal_dn']}")
    if sat is not None and abs(sat - cfg["saturacio_dn"]) > 1.5:
        raise SystemExit(f"PORTA F0.1: saturació mesurada {sat} != declarada {cfg['saturacio_dn']}")
    r["porta"] = "PASSA"
    run.desa_rebut("F0.1_pedestal_blanc.json", r)
    print(f"    pedestal {ped:.2f} DN · saturació {sat} · PORTA PASSA", flush=True)
    return r


# ------------------------------------------------------- 0.2 màsters dark


def masters_dark(run: comu.Run, sostre: int = 128) -> dict:
    cfg = run.cfg
    ex = exposicions(os.path.join(cfg["dir"], "darks"))
    grups = defaultdict(list)
    for n, e in sorted(ex.items()):
        grups[round(e, 8)].append(os.path.join(cfg["dir"], "darks", n))
    sortida = run.fase(0, "masters_dark")
    os.makedirs(sortida, exist_ok=True)
    info = {"metode": "mediana per pixel, fotograma sencer amb marges",
            "sostre": sostre, "masters": {}}
    t0 = time.time()
    for e in sorted(grups):
        rutes = sorted(grups[e])
        fora = 0
        if len(rutes) > sostre:
            idx = np.linspace(0, len(rutes) - 1, sostre).round().astype(int)
            fora = len(rutes) - len(set(idx.tolist()))
            rutes = [rutes[i] for i in sorted(set(idx.tolist()))]
        with rawpy.imread(rutes[0]) as r:
            g = comu.geometria(r); mc = comu.mapa_colors(r)
        pila = np.empty((len(rutes), g.alt, g.ample), np.uint16)
        for i, p in enumerate(rutes):
            with rawpy.imread(p) as r:
                pila[i] = r.raw_image
        med = np.empty((g.alt, g.ample), np.float32)
        for y0 in range(0, g.alt, BANDA):
            y1 = min(y0 + BANDA, g.alt)
            med[y0:y1] = np.median(pila[:, y0:y1].astype(np.float32), axis=0)
        del pila
        # ⛔ No tots els cossos tenen zona emmascarada: l'A7RIIIA no en té cap
        #    (`raw_width` 8000 contra `width` 7968, i les 32 columnes que sobren
        #    veuen llum). Allà el dark ÉS la referència i no hi ha res a restar-li.
        vis = np.zeros((g.alt, g.ample), bool); vis[g.visible] = True
        te_fosc = g.marge_esq > 32
        fosc = comu.zona_fosca(g)[0] if te_fosc else None
        nom = f"MD_E{e:.8g}s.fits"
        h = fits.PrimaryHDU(med)
        h.header["EXPTIME"] = (e, "s, NOMINAL de l EXIF")
        h.header["NFRAMES"] = len(rutes)
        h.header["NDISPON"] = len(grups[e])
        h.writeto(os.path.join(sortida, nom))
        info["masters"][f"{e:.8g}"] = {
            "fitxer": nom, "n": len(rutes), "disponibles": len(grups[e]),
            "deixats_fora": fora,
            "pedestal_zona_fosca": ({comu.nom_canal(i, g.desc):
                                     float(np.median(med[fosc & (mc == i)])) for i in range(4)}
                                    if te_fosc else None),
            "pedestal_dark_actiu": {comu.nom_canal(i, g.desc):
                                    float(np.median(med[vis & (mc == i)])) for i in range(4)},
            "activa_menys_fosca_DN": ({comu.nom_canal(i, g.desc):
                                       float(med[vis & (mc == i)].mean()
                                             - med[fosc & (mc == i)].mean()) for i in range(4)}
                                      if te_fosc else None),
        }
        print(f"    {e:<12.8g} n={len(rutes):3d}"
              + (f" (fora {fora})" if fora else "") + f"  [{time.time()-t0:.0f}s]", flush=True)
    info["n_masters"] = len(info["masters"])
    run.desa_rebut("F0.2_masters_dark.json", info)
    return info


def dark_de(run: comu.Run, e: float) -> np.ndarray:
    d = run.llegeix_rebut("F0.2_masters_dark.json")["masters"]
    k = min(d, key=lambda q: abs(float(q) - e))
    return fits.getdata(os.path.join(run.fase(0, "masters_dark"), d[k]["fitxer"])).astype(np.float32)


# ------------------------------------------------------------- 0.3 flat


def _master_flat(rutes: list[str], dark: np.ndarray, sostre: int = 40) -> np.ndarray:
    rutes = sorted(rutes)
    if len(rutes) > sostre:
        idx = np.linspace(0, len(rutes) - 1, sostre).round().astype(int)
        rutes = [rutes[i] for i in sorted(set(idx.tolist()))]
    with rawpy.imread(rutes[0]) as r:
        h_, w_ = r.raw_image.shape
    pila = np.empty((len(rutes), h_, w_), np.uint16)
    for i, p in enumerate(rutes):
        with rawpy.imread(p) as r:
            pila[i] = r.raw_image
    med = np.empty((h_, w_), np.float32)
    for y0 in range(0, h_, BANDA):
        y1 = min(y0 + BANDA, h_)
        med[y0:y1] = np.median(pila[:, y0:y1].astype(np.float32), axis=0)
    return med - dark


def flat_radial(run: comu.Run, nb: int = 260) -> dict:
    """Flat RADIAL amb centre DECLARAT al centre del sensor.

    ⛔ El centre NO s'ajusta: amb centre lliure el residu del model radial baixa
    monòtonament cap enfora perquè un cercle molt gran és un PLA, i la cerca fuig.
    És la degeneració que `research/100` declara.

    Porta: el perfil dels 28 flats INVERTITS (cos girat 173,5°) ha de reproduir
    el dels normals. Si el flat és del sensor i radial, coincideixen.
    """
    cfg = run.cfg
    ex = exposicions(os.path.join(cfg["dir"], "flats"))
    grups = defaultdict(list)
    for n, e in sorted(ex.items()):
        grups[round(e, 8)].append(os.path.join(cfg["dir"], "flats", n))
    e_ref = max(grups, key=lambda k: (len(grups[k]), k))
    # ⛔ LA PORTA DELS INVERTITS NO EXISTEIX A TOTS ELS TRENS. La Vixen té 28
    #    flats amb el cos girat 173,5° i amb ells el perfil radial queda
    #    VALIDAT (`research/100`). L'A7RIIIA no en té cap: allà el millor
    #    control disponible és la REPETIBILITAT entre meitats, que comprova el
    #    soroll però NO la hipòtesi radial. Es fa, i es diu que és més fluix.
    #    ⏭️ El control de debò per a la Sony és el SALT DE MUNTURA: el mateix
    #    cel a dues posicions del sensor separades 749 px és exactament un
    #    dither. Arriba amb els fotogrames de la quarantena, no aquí.
    dinv = os.path.join(cfg["dir"], "flats-invertits")
    te_inv = os.path.isdir(dinv) and bool(exposicions(dinv))
    M = _master_flat(grups[e_ref], dark_de(run, e_ref))
    if te_inv:
        exi = exposicions(dinv)
        e_inv = sorted(set(exi.values()))[0]
        MI = _master_flat([os.path.join(dinv, n) for n in sorted(exi)],
                          dark_de(run, e_inv))
        control = "flats INVERTITS (cos girat 173,5°)"
    else:
        exi, e_inv = {}, None
        meitat = grups[e_ref][1::2]
        MI = _master_flat(meitat, dark_de(run, e_ref))
        M = _master_flat(grups[e_ref][0::2], dark_de(run, e_ref))
        control = ("MEITATS del mateix joc (no hi ha invertits): comprova "
                   "repetibilitat, NO la hipòtesi radial")
    with rawpy.imread(comu.entrades(run.tren, "totalitat")[0]) as r:
        g = comu.geometria(r); mc = comu.mapa_colors(r)
    CY, CX = g.alt / 2.0, g.ample / 2.0
    yy, xx = np.mgrid[0:g.alt, 0:g.ample].astype(np.float32)
    rad = np.hypot(yy - CY, xx - CX); del yy, xx
    vis = np.zeros((g.alt, g.ample), bool); vis[g.visible] = True
    RMAX = float(rad[vis].max())

    def perfil(v, r_):
        idx = np.clip((r_ / RMAX * nb).astype(np.int32), 0, nb - 1)
        s = np.bincount(idx, v, nb); c = np.bincount(idx, None, nb)
        p = np.where(c > 300, s / np.maximum(c, 1), np.nan)
        return p / np.nanmedian(p[:12]), c > 300

    # ⏭️ CORRECCIÓ DEL FLAT MESURADA PEL DITHER (27-08). Els flats de cel d'un
    #    cos sense flats invertits no tenen porta: a l'A7RIIIA el salt de
    #    muntura de 749 px fa de dither i mesura el residu que hi queda
    #    (`sony_entrada/flat_pel_salt.py`, `research/115` §11). Aquí només
    #    s'APLICA una taula declarada i congelada al manifest; no s'ajusta res.
    #    ⛔ Gauge lnF(0)=0: l'escala absoluta NO es toca, només la forma.
    corr = None
    if cfg.get("flat_dither"):
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               cfg["flat_dither"])) as fh:
            corr = json.load(fh)

    flat = np.ones((g.alt, g.ample), np.float32)
    info = {"centre_yx": [CY, CX], "centre": "CENTRE DEL SENSOR, declarat (no ajustat)",
            "exp_normal": e_ref, "exp_invertit": e_inv,
            "n_normal": min(len(grups[e_ref]), 40), "n_invertit": len(exi),
            "control": control, "te_invertits": te_inv, "canals": {}}
    pitjor = 0.0
    for i in range(4):
        cn = comu.nom_canal(i, g.desc); sel = vis & (mc == i)
        pn, bo = perfil(M[sel], rad[sel])
        pi, boi = perfil(MI[sel], rad[sel])
        both = bo & boi & np.isfinite(pn) & np.isfinite(pi)
        amp = float(1 - np.nanmin(pn[bo]))
        des = float(np.nanmedian(np.abs(pn[both] - pi[both])) / amp * 100)
        pitjor = max(pitjor, des)
        pr = np.where(np.isfinite(pn), pn, np.nanmedian(pn))
        idx = np.clip((rad / RMAX * nb).astype(np.int32), 0, nb - 1)
        flat[mc == i] = pr[idx][mc == i]
        dit = 0.0
        if corr is not None:
            if cn not in corr["lnF"]:
                raise SystemExit(f"la taula del dither no té el canal {cn}: "
                                 f"{list(corr['lnF'])}")
            f_ = np.exp(np.interp(rad[mc == i], corr["r_sensor_px"], corr["lnF"][cn]))
            flat[mc == i] *= f_.astype(np.float32)
            dit = float(100 * (f_.max() / f_.min() - 1))
        info["canals"][cn] = {"vinyetatge_pct": 100 * amp,
                              "desacord_invertits_pct": des,
                              "dither_amplitud_pct": dit,
                              "perfil": np.where(np.isfinite(pn), pn, -1).tolist()}
        print(f"    {cn:>2}  vinyetatge {100*amp:5.2f} %   desacord amb el control "
              f"{des:5.2f} %" + (f"   + dither {dit:5.2f} %" if corr else ""),
              flush=True)
    if pitjor > 8.0:
        raise SystemExit(f"PORTA F0.3: desacord amb el control {pitjor:.2f} % > 8 %")
    info["porta"] = ("PASSA" if te_inv else
                     ("PASSA (control del DITHER: el salt de muntura)" if corr
                      else "PASSA (control FLUIX: sense invertits)"))
    if corr is not None:
        info["dither"] = {"font": corr["font"], "metode": corr["metode"],
                          "gauge": corr["gauge"], "controls_pct": corr["controls_pct"]}
    info["desacord_pitjor_pct"] = pitjor
    fits.PrimaryHDU(flat).writeto(run.fase(0, "FLAT_RADIAL.fits"))
    run.desa_rebut("F0.3_flat.json", info)
    return info
