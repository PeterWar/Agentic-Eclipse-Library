#!/usr/bin/env python3
"""LA CADENA. Un sol punt d'entrada, ordre fix, i falla tancat al primer error.

    python3 cadena.py VIXEN [CIENCIA] [--reusa [NNN]] [--igualment]

El segon argument és el **mode de color** (`comu.MODES_COLOR`). ⛔ Des del
27-08-2026 només n'hi ha un de viu, **CIENCIA** —blanc sobre el Sol de sobre
l'atmosfera (AM0)—, per decisió de Pere. El mode **MEMORIA** queda DEPRECAT:
es conserva a `comu.MODES_DEPRECATS` perquè el seu run vell es pugui continuar
llegint, però `Run.nou` refusa arrencar-ne un de nou.

Cada execució crea `1-RUNS/<TREN>_<segell>/`, que **no es toca mai més**:
- `MANIFEST.json` amb el SHA-256 del codi i de CADA fitxer d'entrada;
- `codi/` amb una còpia congelada dels scripts, perquè el run es pugui repetir
  tal com era encara que el codi viu hagi canviat;
- les cinc fases, els rebuts i els lliurables.

⏭️ **`--reusa`** (27-08, per Pere: «a cada run nou no fa falta que refacis les
primeres fases, el VIXEN ja fa LDIC molt bé»). Amb això, les fases **0
(calibració), 1 (registre) i 2 (composició LDIC)** no es tornen a calcular:
s'agafen d'un run anterior i es **munten per enllaç dur**, que no costa ni disc
ni temps. Es refan només la **3 (filtres)**, la **4 (PSB)** i la **5 (vistes)**.
El run nou continua sent un run sencer i immutable; el que canvia és d'on surt
la primera meitat, i queda escrit al manifest amb els SHA-256.

⛔ **Falla tancat si el codi de les fases reusades ha canviat.** Si `f0.py`,
`f1.py`, `f2.py` o qualsevol taula de constants no són byte a byte els del run
d'origen, es refusa: reusar productes fets amb un altre codi és mentir al
manifest. `--igualment` ho força, i llavors el manifest ho diu.

Al final es copia a `2-OUTPUT/<NNN>_<TREN>_<COLOR>/`, amb el NÚMERO del run al
davant: ordenar per nom és ordenar per temps, i el número més alt és l'últim.
Se'n conserven les dues últimes de cada tren+color; el run sempre queda sencer.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
import traceback
from datetime import datetime, timezone

import numpy as np
from astropy.io import fits

import comu

SCRIPTS = ("comu.py", "f0.py", "f1.py", "f2.py", "f3.py", "f4.py",
           "ajust.py", "vistes.py", "cadena.py",
           # taules de constants declarades: es congelen i es hashegen igual
           # que el codi, perquè decideixen el resultat.
           "flat_dither_SONY.json")


def manifest(run: comu.Run, segell_iso: str) -> dict:
    aqui = os.path.dirname(os.path.abspath(__file__))
    codi = {}
    for s in SCRIPTS:
        src = os.path.join(aqui, s)
        shutil.copy2(src, os.path.join(run.dir, "codi", s))
        codi[s] = comu.sha256(src)
    ent = {}
    cfg = run.cfg
    for quin in sorted(os.listdir(cfg["dir"])):
        d = os.path.join(cfg["dir"], quin)
        if not os.path.isdir(d):
            continue
        fs = comu.llista(d, cfg["ext"])
        ent[quin] = {"n": len(fs),
                     "fitxers": {os.path.basename(p): comu.sha256(p) for p in fs}}
    m = {"tren": run.tren, "mode_color": run.mode, "color": run.color,
         "corba_to": comu.CORBA, "extincio_declarada": comu.EXTINCIO,
         "segell": run.segell, "generat_utc": segell_iso,
         "config": {k: v for k, v in cfg.items()},
         "codi_sha256": codi,
         "entrades": ent,
         "entrades_total": sum(v["n"] for v in ent.values())}
    with open(os.path.join(run.dir, "MANIFEST.json"), "w") as fh:
        json.dump(m, fh, indent=1, ensure_ascii=False, sort_keys=True)
    return m


# fases que `--reusa` munta del run d'origen, i els rebuts que hi pertanyen
FASES_REUSABLES = ("0-calibracio", "1-registre", "2-ldic")
REBUTS_REUSABLES = ("F0.1_pedestal_blanc.json", "F0.2_masters_dark.json",
                    "F0.3_flat.json", "F1.1_limbe.json", "F1.2_sol_llenc.json",
                    "F1.3_registre.json", "F2.2_coherencia.json", "F2.4_cel.json")
# codi que decideix el que hi ha en aquelles fases: si canvia, no es pot reusar
CODI_CRITIC = ("comu.py", "f0.py", "f1.py", "f2.py", "flat_dither_SONY.json")


def _enllaça(origen: str, desti: str) -> tuple[int, int]:
    """Enllaç dur si es pot (mateix volum: no costa ni disc ni temps), còpia si no."""
    n_link = n_copia = 0
    for dp, _, fs in os.walk(origen):
        rel = os.path.relpath(dp, origen)
        dd = os.path.join(desti, rel) if rel != "." else desti
        os.makedirs(dd, exist_ok=True)
        for f in fs:
            a, b = os.path.join(dp, f), os.path.join(dd, f)
            if os.path.exists(b):
                continue
            try:
                os.link(a, b); n_link += 1
            except OSError:
                shutil.copy2(a, b); n_copia += 1
    return n_link, n_copia


def reusa_fases(run: comu.Run, font: str, igualment: bool) -> dict:
    """Munta les fases 0, 1 i 2 d'un run anterior dins del run nou."""
    mf = json.load(open(os.path.join(font, "MANIFEST.json")))
    if mf["tren"] != run.tren:
        raise SystemExit(f"⛔ el run d'origen és de {mf['tren']}, no de {run.tren}")
    # el codi de les fases reusades ha de ser el MATEIX
    aqui = os.path.dirname(os.path.abspath(__file__))
    dif = [c for c in CODI_CRITIC
           if os.path.exists(os.path.join(aqui, c))
           and mf["codi_sha256"].get(c) != comu.sha256(os.path.join(aqui, c))]
    # i les ENTRADES també: si han canviat els fotogrames, no val res
    ent = {q: v["fitxers"] for q, v in mf["entrades"].items()}
    ara = {}
    for quin in sorted(os.listdir(run.cfg["dir"])):
        dq = os.path.join(run.cfg["dir"], quin)
        if os.path.isdir(dq):
            ara[quin] = {os.path.basename(p): comu.sha256(p)
                         for p in comu.llista(dq, run.cfg["ext"])}
    if ent != ara:
        raise SystemExit("⛔ les ENTRADES han canviat des del run d'origen: "
                         "les fases 0-2 no es poden reusar.")
    if dif:
        msg = ("⛔ el codi de les fases reusades ha canviat des del run d'origen: "
               + ", ".join(dif))
        if not igualment:
            raise SystemExit(msg + "\n   (si de veritat ho vols, --igualment)")
        print("    ⚠️ " + msg + " · FORÇAT amb --igualment", flush=True)
    nl = nc = 0
    for f in FASES_REUSABLES:
        a = os.path.join(font, f)
        if os.path.isdir(a):
            x, y = _enllaça(a, os.path.join(run.dir, f)); nl += x; nc += y
    for r in REBUTS_REUSABLES:
        a = os.path.join(font, "4-rebuts", r)
        if os.path.exists(a):
            b = run.rebut(r)
            try:
                os.link(a, b); nl += 1
            except OSError:
                shutil.copy2(a, b); nc += 1
    info = {"font": os.path.basename(font), "fases": list(FASES_REUSABLES),
            "rebuts": [r for r in REBUTS_REUSABLES
                       if os.path.exists(os.path.join(font, "4-rebuts", r))],
            "fitxers_enllaçats": nl, "fitxers_copiats": nc,
            "codi_del_origen": {c: mf["codi_sha256"].get(c) for c in CODI_CRITIC},
            "codi_divergent": dif, "forçat": bool(dif and igualment),
            "per_que": ("Pere, 27-08-2026: «a cada run nou no fa falta que refacis "
                        "les primeres fases, el VIXEN ja fa LDIC molt bé»")}
    run.desa_rebut("F0-2_REUSADES.json", info)
    print(f"    de {info['font']} · {nl} fitxers enllaçats" +
          (f" i {nc} copiats" if nc else "") +
          " · fases 0, 1 i 2 NO es recalculen", flush=True)
    return info


def main() -> int:
    av = sys.argv[1:]
    igualment = "--igualment" in av
    av = [a for a in av if a != "--igualment"]
    reusa = None
    if "--reusa" in av:
        i = av.index("--reusa")
        reusa = av[i + 1] if len(av) > i + 1 and not av[i + 1].startswith("-") else "auto"
        av = av[:i] + av[i + (2 if reusa != "auto" else 1):]
    tren = (av[0] if av else "VIXEN").upper()
    if tren not in comu.TRENS:
        raise SystemExit(f"tren desconegut: {tren}")
    mode = (av[1] if len(av) > 1 else "CIENCIA").upper()
    # ⛔ El run d'origen es resol ABANS de crear res: un `--reusa` equivocat no
    #    ha de deixar cap carpeta orfe al darrere.
    font = None
    if reusa is not None:
        font = comu.darrer_run(tren, mode) if reusa == "auto" else comu.run_per_segell(reusa)
        if not os.path.exists(os.path.join(font, "2-ldic", "CORONA_G.fits")):
            raise SystemExit(f"⛔ el run d'origen no té la fase 2 acabada: {font}")
    ara = datetime.now(timezone.utc)
    segell = ara.strftime("%Y%m%dT%H%M%SZ")
    run = comu.Run.nou(tren, segell, mode)
    _MEU["dir"] = run.dir
    T0 = time.time()
    print(f"\n{'='*74}\nRUN {tren} · COLOR {mode} · {segell}\n{run.dir}\n"
          f"  {run.color['titol']}\n{'='*74}", flush=True)

    print("\n· MANIFEST (hash del codi i de cada entrada)", flush=True)
    m = manifest(run, ara.isoformat())
    print(f"    {len(m['codi_sha256'])} scripts congelats · "
          f"{m['entrades_total']} entrades hashejades", flush=True)

    import f0, f1, f2, f3, f4, vistes
    passos = []
    reus = None
    if font is not None:
        if os.path.abspath(font) == os.path.abspath(run.dir):
            raise SystemExit("⛔ el run d'origen no pot ser ell mateix")
        print(f"\n· F0-F2 REUSADES d'un run anterior (--reusa)", flush=True)
        t = time.time()
        reus = reusa_fases(run, font, igualment)
        passos.append({"pas": "F0-F2 reusades", "segons": round(time.time() - t, 1),
                       "font": reus["font"]})
        m["reusat"] = reus
        with open(os.path.join(run.dir, "MANIFEST.json"), "w") as fh:
            json.dump(m, fh, indent=1, ensure_ascii=False, sort_keys=True)

    def pas(nom, fn):
        t = time.time()
        print(f"\n· {nom}", flush=True)
        r = fn()
        passos.append({"pas": nom, "segons": round(time.time() - t, 1)})
        return r

    if reus is None:
        pas("F0.1 pedestal i nivell de blanc", lambda: f0.pedestal_i_blanc(run))
        pas("F0.2 màsters de dark", lambda: f0.masters_dark(run))
        pas("F0.3 flat radial + porta dels invertits", lambda: f0.flat_radial(run))
        pas("F1.1 limbe lunar", lambda: f1.limbe(run))
        pas("F1.2 Sol per efemèride i llenç", lambda: f1.sol_i_llenc(run))

    if reus is None:
        ctx = f2.Ctx(run)
        S = run.llegeix_rebut("F1.2_sol_llenc.json")
        pos0 = {n: v for n, v in S["fotogrames"].items() if v["coronal"]}
        # Aquesta porta vigila una cosa concreta: que el temps dels fotogrames i el
        # de C2/C3 estiguin a la MATEIXA referencia. Un error de referencia deixa
        # QUASI ZERO coronals, no dotze. Escrita com un minim absolut de 20 nomes
        # deia la mida del tren: la Vixen en porta 67 de 121 (55 %) i la Sony 12 de
        # 14 (86 %), i la Sony la fallava tenint la fraccio mes alta de les dues.
        # Ara demana una FRACCIO, mes un terra per sota del qual la LDIC no te res
        # a compondre.
        n_tot = len(S["fotogrames"])
        if len(pos0) < max(6, int(0.15 * n_tot)):
            raise SystemExit(f"PORTA F1.2: nomes {len(pos0)} fotogrames coronals de "
                             f"{n_tot} ({100*len(pos0)/max(n_tot,1):.0f} %). Comprova que "
                             "el temps dels fotogrames i el de C2/C3 estan a la MATEIXA "
                             "referencia.")
        if len(pos0) < 20:
            print(f"    ⚠️ només {len(pos0)} fotogrames coronals ({100*len(pos0)/n_tot:.0f} % "
                  f"de {n_tot}): el compost serà prim i el soroll ho dirà", flush=True)
        print(f"\n· F2.1 composició A (posicions del model)", flush=True)
        t = time.time()
        CA, _ = f2.compon(ctx, pos0, {}, "A")
        passos.append({"pas": "F2.1 composició A", "segons": round(time.time() - t, 1)})

        pos1 = pas("F1.3 registre fi per CORRELACIÓ", lambda: f2.refina(ctx, pos0, CA))
        run.desa_rebut("F1.3_registre.json",
                       {"metode": "correlacio de fase contra el compost A",
                        "n": len(pos1),
                        "n_refinats": sum(1 for v in pos1.values() if v["font"] == "correlacio"),
                        "fotogrames": pos1})

        K = pas("F2.2 coherència (guany per fotograma)",
                lambda: f2.coherencia(ctx, pos1, CA))
        ks = np.array([K[n] for n in sorted(K)])
        run.desa_rebut("F2.2_coherencia.json",
                       {"gauge": "mediana(ln k) = 0", "k": K,
                        "dispersio_pct": float(100 * ks.std()),
                        "p5": float(np.percentile(ks, 5)), "p95": float(np.percentile(ks, 95))})
        del CA

        print(f"\n· F2.3 composició B (registre fi + coherència)", flush=True)
        t = time.time()
        CB, den = f2.compon(ctx, pos1, K, "B")
        for c in comu.CANALS:
            fits.PrimaryHDU(CB[c]).writeto(run.fase(2, f"LDIC_{c}.fits"))
            fits.PrimaryHDU(den[c]).writeto(run.fase(2, f"PES_{c}.fits"))
        passos.append({"pas": "F2.3 composició B", "segons": round(time.time() - t, 1)})

        # ⛔ F2.3b · la cura del cel per fotograma (`research/103`) està
        #    IMPLEMENTADA a `f2.cura_cel_fotograma` però NO s'aplica. Mesurada el
        #    27-08 contra les marques de Pere: l'estriat de la zona marcada PUJA
        #    un 1,6 %, i el quocient zona/control va de 0,968 a 0,979 (+1,2 %).
        #    A sobre treu 1,4-2,9 % rms —el `research/103` parlava de 0,10-0,50 %—
        #    i el pitjor cas del tancament HDR passa de 5,3 a 9,0 %.
        #    Tres senyals en contra i cap a favor: norma zero.
        print(f"\n· F2.4 cel pel COLOR (dos vectors mesurats)", flush=True)
        t = time.time()
        COR, icel = f2.cel_per_color(ctx, CB, den)
        for c in comu.CANALS:
            fits.PrimaryHDU(COR[c]).writeto(run.fase(2, f"CORONA_{c}.fits"))
            fits.PrimaryHDU((CB[c] - COR[c]).astype(np.float32)).writeto(run.fase(2, f"CEL_{c}.fits"))
        yy, xx = np.mgrid[0:ctx.H, 0:ctx.W].astype(np.float32)
        rad = np.hypot(yy - ctx.CY, xx - ctx.CX); del yy, xx
        mm = den["G"] > 0
        icel["color_corona"] = comu.mesura_color(COR, rad, mm, ctx.RS)
        icel["veredicte_color"] = comu.veredicte_color(icel["color_corona"])
        fits.PrimaryHDU(((CB["G"] - COR["G"]) / max(icel["b_cel"][1], 1e-9)).astype(np.float32)
                        ).writeto(run.fase(2, "CEL_S.fits"))
        run.desa_rebut("F2.4_cel.json", icel)
        passos.append({"pas": "F2.4 cel", "segons": round(time.time() - t, 1)})
        del CB, COR, den

    pas("F3 filtres i corba de to", lambda: f3.filtres(run))
    pas(f"F3b protuberàncies · contactes al producte: "
        f"{', '.join(comu.CONTACTES_AL_PRODUCTE)}",
        lambda: f4.calcula_protuberancies(run))
    pas("F4.1 PSB del resultat", lambda: f4.psb_resultat(run))
    pas("F4.2 PSB de les capes LDIC", lambda: f4.psb_capes_ldic(run))
    pas("F4.3 PSB dels contactes", lambda: f4.psb_contactes(run))
    pas("F4.4 PSB SENCER (filtres + capes LDIC)", lambda: f4.psb_tot(run))
    pas("F5 vistes i rebut llegible", lambda: vistes.tot(run))

    # ⛔ Empremta de les PRÒPIES sortides. Sense això, una modificació posterior
    # (per exemple, desar el PSB des de Photoshop) no es pot detectar i el run
    # deixa de descriure el que hi ha al disc sense que ningú se n'assabenti.
    sortides = {}
    for dp, _, fs in os.walk(run.dir):
        for f in sorted(fs):
            if f in (".DS_Store", "MANIFEST_SORTIDES.json"):
                continue
            q = os.path.join(dp, f)
            sortides[os.path.relpath(q, run.dir)] = {"bytes": os.path.getsize(q),
                                                     "sha256": comu.sha256(q)}
    with open(os.path.join(run.dir, "MANIFEST_SORTIDES.json"), "w") as fh:
        json.dump({"n": len(sortides), "fitxers": sortides}, fh, indent=1, sort_keys=True)
    print(f"    {len(sortides)} sortides hashejades", flush=True)

    run.desa_rebut("CADENA.json", {"passos": passos,
                                   "segons_total": round(time.time() - T0, 1)})
    # ⛔ 2-OUTPUT és una CÒPIA, no un enllaç al run.
    # Amb un enllaç simbòlic, desar el PSB des de Photoshop escriu DINS del run
    # i li trenca la immutabilitat sense avisar. Va passar el 26-08: Pere va
    # desar les seves tries de capes i el run va deixar de ser el que la cadena
    # havia produït. Costa 4 GB i tanca la classe de problema sencera.
    os.makedirs(comu.OUTPUT, exist_ok=True)
    # ⏭️ La carpeta de sortida porta el NÚMERO DEL RUN: `NNN_TREN_COLOR`. Així
    #    ordenar per nom és ordenar per temps també aquí, i no cal cap sufix
    #    `_anterior`: la còpia de fa dos runs es queda amb el seu número.
    desti = os.path.join(comu.OUTPUT, comu.carpeta_sortida(run))
    if os.path.exists(desti):
        raise SystemExit(f"la sortida ja existeix i no es toca: {desti}")
    shutil.copytree(os.path.join(run.dir, "lliurables"), desti)
    # ⚠️ Es conserven les DUES últimes de cada tren+color. La tercera se'n va,
    #    i es diu, perquè si hi havies desat res ho perds: són 6-9 GB cada una.
    velles = comu.sortides_de(tren, mode)[:-2]
    for v in velles:
        shutil.rmtree(v)
        print(f"    retirada la sortida vella {os.path.basename(v)} "
              f"(el run {os.path.basename(v)[:3]} es conserva sencer)", flush=True)
    # ⏭️ 27-08: la carpeta de sortida diu DE QUIN RUN VE, amb el número. Sense
    #    això, `2-OUTPUT/VIXEN_CIENCIA` no diu quin dels catorze runs l'ha fet.
    with open(os.path.join(desti, "DE_QUIN_RUN_VE.txt"), "w") as fh:
        fh.write(f"{os.path.basename(run.dir)}\n\n"
                 f"run     : {run.dir}\n"
                 f"tren    : {tren}\n"
                 f"color   : {mode} · {run.color['titol']}\n"
                 f"generat : {ara.isoformat()}\n\n"
                 f"Aquesta carpeta és una CÒPIA dels lliurables d'aquell run. Pots\n"
                 f"desar-hi a sobre des de Photoshop: el run no es toca. La còpia\n"
                 f"anterior, amb els teus canvis, queda a "
                 f"{os.path.basename(desti)}_anterior.\n")
    print(f"\n{'='*74}")
    print(f"FET en {(time.time()-T0)/60:.1f} min")
    print(f"  run     : {run.dir}")
    print(f"  a mirar : {desti}")
    print(f"{'='*74}\n", flush=True)
    return 0


# El run que aquest proces ha creat. Nomes es marca aquest.
_MEU = {"dir": None}


def _marca_fallit():
    """Un run incomplet no es un run: es marca perque no es pugui confondre.

    Marca NOMES el run d'aquest proces. Escombrant tot `1-RUNS` i marcant
    qualsevol carpeta sense `CADENA.json`, una cadena que falla n'etiquetava
    d'altres que no eren seves: la d'una altra sessio que encara corre, o una
    ja marcada a ma, que es quedava amb un `_AVORTAT_FALLIT` absurd. Amb dues
    cadenes en paral.lel, la que peta declarava fallida la que anava be.
    """
    p = _MEU["dir"]
    if not p or not os.path.isdir(p) or p.endswith("_FALLIT"):
        return
    if os.path.exists(os.path.join(p, "4-rebuts", "CADENA.json")):
        return
    os.rename(p, p + "_FALLIT")
    print(f"⛔ run incomplet marcat: {os.path.basename(p)}_FALLIT", file=sys.stderr)


if __name__ == "__main__":
    try:
        c = main()
    except SystemExit as e:
        if e.code:
            _marca_fallit()
        raise
    except Exception:
        traceback.print_exc()
        _marca_fallit()
        raise SystemExit(1)
    raise SystemExit(c)
