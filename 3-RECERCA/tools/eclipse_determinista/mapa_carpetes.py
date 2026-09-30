#!/usr/bin/env python3
"""El mapa de carpetes del projecte, generat des del disc.

⏭️ 27-08-2026, per Pere: «torno a tenir lio en l'estructura de carpetes».
Aquest mapa **no s'escriu a mà**: es genera del que hi ha de veritat, o sigui
que no pot quedar desfasat. Es desa a `2-OUTPUT/MAPA_DE_CARPETES.md`.

    python3 mapa_carpetes.py
"""
from __future__ import annotations

import json
import os
import subprocess

import comu


def mida(p):
    try:
        out = subprocess.run(["du", "-sh", p], capture_output=True, text=True).stdout
        return out.split("\t")[0].strip()
    except Exception:                                    # noqa: BLE001
        return "?"


def n_fitxers(p):
    return sum(len(f) for _, _, f in os.walk(p))


def main():
    L = []
    w = L.append
    w("# Mapa de carpetes · Eclipse determinista\n")
    w("*Generat des del disc per `research/tools/eclipse_determinista/"
      "mapa_carpetes.py`. No s'escriu a mà: si el torna a executar, es refà.*\n")
    w("## La regla, en tres línies\n")
    w("- **`0-ENTRADES/`** és l'autoritat: els RAW. Només s'hi llegeix.")
    w("- **`1-RUNS/`** és la història: cada execució de la cadena, **immutable**.")
    w("- **`2-OUTPUT/`** és el que mires tu: una **còpia** dels lliurables del "
      "run vigent. Pots desar-hi a sobre; el run no es toca.\n")
    w("**El número mana als dos llocs.** Un run es diu "
      "`NNN_TREN_COLOR_segell` i la seva sortida `NNN_TREN_COLOR`, amb el "
      "**mateix** `NNN`: cronològic i comú a tots els trens. O sigui que "
      "**ordenar per nom és ordenar per temps** i el número més alt és sempre "
      "l'últim — i `2-OUTPUT/014_SONYTOT_CIENCIA/` ve del run "
      "`1-RUNS/014_SONYTOT_CIENCIA_.../` sense haver de mirar res.\n")
    w("De cada tren+color s'hi conserven les **dues últimes** sortides. La "
      "tercera se'n va quan n'arriba una de nova, i la cadena ho diu; el run, "
      "en canvi, no s'esborra mai sol.\n")

    # ---------------------------------------------------------- 0-ENTRADES
    w("---\n\n## `0-ENTRADES/` · els RAW\n")
    w("| carpeta | fitxers | mida | què és |")
    w("|---|---:|---:|---|")
    QUE = {
        "totalitat": "fotogrames de la totalitat",
        "descentrats": "**primer apuntament** de la Sony (abans del salt de muntura). Estan bé",
        "inservibles": "moguts durant el salt. **Ningú els llegeix**; el manifest els hasheja",
        "darks": "foscos per exposició",
        "flats": "camp pla",
        "flats-invertits": "camp pla amb el cos girat 173,5° (la porta del flat)",
    }
    for tren in sorted(os.listdir(comu.ENTRADES)):
        d = os.path.join(comu.ENTRADES, tren)
        if not os.path.isdir(d):
            continue
        w(f"| **`{tren}/`** | | {mida(d)} | |")
        for c in sorted(os.listdir(d)):
            p = os.path.join(d, c)
            if os.path.isdir(p):
                w(f"| &nbsp;&nbsp;`{c}/` | {n_fitxers(p)} | {mida(p)} | "
                  f"{QUE.get(c, '')} |")
    w("")

    # ------------------------------------------------------------- 1-RUNS
    w("---\n\n## `1-RUNS/` · un per execució, immutables\n")
    w("| # | tren | color | segell | mida | |")
    w("|---:|---|---|---|---:|---|")
    vigents = {}
    for c in sorted(os.listdir(comu.OUTPUT)):
        f = os.path.join(comu.OUTPUT, c, "DE_QUIN_RUN_VE.txt")
        if os.path.exists(f):
            vigents[open(f).readline().strip()] = c
    for p in comu.runs_llista(acabats=False):
        b = os.path.basename(p)
        r = comu.Run.obre(p)
        tren, mode, seg = r.tren, r.mode, r.segell
        if not seg:                      # runs d'abans que hi hagués mode
            tren, mode, seg = r.tren, "—", r.mode
        marca = f"⏭️ **vigent a `2-OUTPUT/{vigents[b]}/`**" if b in vigents else ""
        if b.endswith(("_FALLIT", "_AVORTAT")):
            marca = "⛔ incomplet"
        w(f"| {comu.numero_de(p):03d} | {tren} | {mode} | `{seg}` | "
          f"{mida(p)} | {marca} |")
    w("")
    w("Dins de cada run:\n")
    w("```text")
    w("NNN_TREN_COLOR_segell/")
    for c, q in (("MANIFEST.json", "SHA-256 del codi i de CADA fitxer d'entrada"),
                 ("codi/", "còpia congelada dels scripts d'aquell moment"),
                 ("0-calibracio/", "pedestal, màsters de fosc, flat"),
                 ("1-registre/", "limbe, Sol per efemèride, registre fi"),
                 ("2-ldic/", "el compost: LDIC, CEL, CORONA, PES (per canal)"),
                 ("3-filtres/", "passa-alt, radial, NRGF, MGN"),
                 ("4-rebuts/", "un JSON per fase, amb totes les portes"),
                 ("lliurables/", "els PSB, el REBUT.md i les vistes ← això és el que es copia")):
        w(f"  {c:<18s} {q}")
    w("```\n")

    # ------------------------------------------------------------ 2-OUTPUT
    w("---\n\n## `2-OUTPUT/` · el que has de mirar\n")
    w("| carpeta o fitxer | ve de | mida | què és |")
    w("|---|---|---:|---|")
    NOTA = {
        "DOS_TRENS": "la Vixen contra la Sony: el jutge independent. **No va per "
                     "runs**: es refà a sobre",
        "AUDITORIA_ESTRUCTURA": "la nostra estructura contra la de Brno. **No va "
                                "per runs**",
        "ESTUDI_DRUCKMULLER": "mesures sobre els composts de Brno. **No va per runs**",
        "MARQUES_DE_PERE": "el que has marcat tu, i què n'ha sortit. **No va per runs**",
    }
    ultims = {}
    for c in sorted(os.listdir(comu.OUTPUT)):
        if comu._PREFIX.match(c) and os.path.isdir(os.path.join(comu.OUTPUT, c)):
            ultims[c[4:]] = c          # l'ordre alfabètic ja deixa l'últim
    for c in sorted(os.listdir(comu.OUTPUT)):
        p = os.path.join(comu.OUTPUT, c)
        if os.path.isdir(p):
            f = os.path.join(p, "DE_QUIN_RUN_VE.txt")
            ve = f"run **{open(f).readline().strip()[:3]}**" if os.path.exists(f) else "—"
            nota = NOTA.get(c, "")
            if c == "VIXEN_MEMORIA":
                nota = "⛔ mode DEPRECAT el 27-08. Història"
            if not nota and ve != "—":
                nota = ("⏭️ **l'últim** d'aquest tren" if c == ultims.get(c[4:])
                        else "una còpia anterior; si hi has desat res, és aquí")
            w(f"| **`{c}/`** | {ve} | {mida(p)} | {nota} |")
    SOLTS = {
        "MAPA_DE_CARPETES.md": "aquest fitxer",
        "LLEGEIX-ME.md": "els dos modes de color i per què n'hi ha un de deprecat",
        "TRIES_DE_PERE.md": "què deixes encès i què n'has dit",
        "COM_S_HA_FET.md": "com s'ha fet el que hi ha, pas per pas",
        "COM_S_HA_FET_els_anells.md": "els anells dels filtres",
        "COM_S_HA_FET_la_mascara_lunar.md": "la màscara lunar per fotograma",
        "COM_S_HA_FET_les_marques_i_les_protuberancies.md":
            "les teves marques i les protuberàncies",
        "COMPARATIVA_DELS_DOS_MODES.png": "MEMORIA contra CIENCIA (històric)",
    }
    for c in sorted(os.listdir(comu.OUTPUT)):
        p = os.path.join(comu.OUTPUT, c)
        if not os.path.isdir(p) and not c.startswith("."):
            w(f"| `{c}` | — | {mida(p)} | {SOLTS.get(c, '')} |")
    w("")
    w("Dins de cada carpeta de tren hi ha sempre el mateix:\n")
    w("```text")
    for c, q in (("Eclipsi_2026_..._TOT.psb", "el projecte SENCER (filtres + capes LDIC)"),
                 ("Eclipsi_2026_....psb", "el resultat: base + detall + diagnòstics"),
                 ("..._capes_LDIC.psb", "una capa per esglaó d'exposició"),
                 ("..._contactes.psb", "perles, anells de diamant i parcials"),
                 ("REBUT.md", "tots els números del run, en text llegible"),
                 ("DE_QUIN_RUN_VE.txt", "quin run l'ha fet ← comença per aquí"),
                 ("vistes/", "PNG per mirar sense obrir Photoshop")):
        w(f"  {c:<26s} {q}")
    w("```")

    p = os.path.join(comu.OUTPUT, "MAPA_DE_CARPETES.md")
    open(p, "w").write("\n".join(L) + "\n")
    print("\n".join(L))
    print(f"\n→ desat a {p}")


if __name__ == "__main__":
    main()
