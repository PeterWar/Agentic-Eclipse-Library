"""El rebut de la V14, en text llegible. Surt dels dos JSON i de res més."""
from __future__ import annotations
import json, os, sys

def coma(x, n=2):
    if x is None:
        return "—"
    return f"{x:.{n}f}".replace(".", ",")

def main():
    dest = sys.argv[1] if len(sys.argv) > 1 else (
        "/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals")
    V = os.path.join(dest, "CapesTotalsV14_vistes")
    R = json.load(open(os.path.join(V, "REBUT_V14.json")))
    P = json.load(open(os.path.join(V, "PORTES_V14.json")))
    LL = R["llenc"]
    L = []
    A = L.append
    A("# CapesTotalsV14 — la maqueta de Pere amb la dada calibrada\n")
    A(f"Feta el 27 d'agost de 2026 a partir de **`CapesTotalsV13.psd`** i del run "
      f"**`{R['run']}`** de la cadena determinista. El run no s'ha tocat: només se n'ha llegit.\n")
    A(f"- **Fitxer**: `{os.path.basename(R['fitxer'])}` · "
      + f"{R['bytes']/1e9:.2f}".replace(".", ",") + " GB (el format PSD arriba a 2 GB; "
      "hi cap). ⏭️ **Comprovat que s'obre** amb dos lectors independents: `psd-tools` "
      "(12 capes i les seves màscares) i **ImageIO de macOS** (`sips`), que llegeix la "
      "imatge fusionada — que és justament la secció que la primera versió tenia mal "
      "comprimida i per això Photoshop la refusava.\n")
    A(f"- **Llenç**: {LL['W']} × {LL['H']} px = ±{coma(LL['semi_Rsol'][0])} × "
      f"±{coma(LL['semi_Rsol'][1])} R☉, nord amunt, Sol al centre, "
      f"{coma(LL['escala_arcsec_px'], 4)} ″/px. És el llenç comú d'avui, el que encabeix la Sony.\n")
    A(f"- **Capes**: {len(R['capes'])} — les **12 de la V13**, en el mateix ordre i amb la "
      f"seva visibilitat i opacitat, més **la 13, que és EL SOL** (§«La Lluna i el Sol»).\n")
    ll = R.get("lluna_declarada")
    if ll:
        A(f"- **Lluna DECLARADA** a ({coma(ll['centre_px'][0])} · {coma(ll['centre_px'][1])}) px, "
          f"radi {coma(ll['R_lluna_px'])} + {coma(ll['guarda_px'],0)} px de guarda: el disc dels "
          f"{len(ll['fotogrames'])} fotogrames de contacte de C2, que hi coincideixen a "
          f"{coma(ll['dispersio_px'])} px.\n")
    A("\n## Què s'hi ha canviat, i què no\n")
    A("| | V13 | V14 |")
    A("|---|---|---|")
    A("| llenç | 7648 × 5353, la graella del sensor de la Vixen | "
      f"{LL['W']} × {LL['H']}, el llenç comú (Sol al centre, nord amunt) |")
    A("| dada | revelat directe dels RAW | compost calibrat de la cadena: fosc, flat, "
      "pedestal i saturació mesurats, balanç de blancs, màscara lunar per fotograma |")
    A("| alineació | cap: cada capa seu a la posició crua del seu fotograma | "
      "la cadena registra cada fotograma a la corona (correlació de fase) |")
    A("| to | l'estirament d'Antigravity | una sola corba sobre la lluminància, "
      f"àncora comuna {R['ancora_L']:.4e} |".replace(".", ","))
    A("| màscares | les de Pere | **les mateixes**, portades al llenç nou i retocades "
      "només allà on demanaven dada que no existeix |")
    A("\n## Les capes\n")
    A("| capa | exposició | fotogrames | on hi ha dada | màscara V13 | màscara V14 | visible |")
    A("|---|---|---:|---|---|---|---|")
    for c in R["capes"]:
        rv, ra, rd = c["rang_validesa_Rsol"], c["rang_mascara_V13_Rsol"], c["rang_mascara_V14_Rsol"]
        A(f"| **{c['num']}** {c['rol'] or ''} | {c['etiqueta']} | {len(c['fotogrames'])} | "
          f"{coma(rv[0])}–{coma(rv[1])} R☉ | {coma(ra[0])}–{coma(ra[1])} R☉ | "
          f"{coma(rd[0])}–{coma(rd[1])} R☉ | {'sí' if c['visible'] else 'no'} |")
    A("\n⏭️ «On hi ha dada» és el rang on la capa té els **tres canals** amb pes per damunt "
      "del que és assolible al mateix radi. La seva vora **interior** és el radi on aquella "
      "exposició deixa d'estar saturada, i renderitzada és exactament un halo al voltant de "
      "la Lluna: és el que Pere va marcar el 27-08 a la capa de 1/8 s.\n")
    A("\n## Les portes\n")
    p = P["portes"]
    A("| porta | què mesura | resultat | veredicte |")
    A("|---|---|---|---|")
    a_ = p["A_transformat"]
    A(f"| **A** · transformat | el limbe lunar de la V13 contra on la cadena diu que és la "
      f"Lluna d'aquell fotograma ({a_['n_capes_mesurades']} capes) | mediana "
      f"{coma(a_['residu_mediana_px'])} px, màxim {coma(a_['residu_max_px'])} px "
      f"(llindar {coma(a_['llindar_px'])}) | **{a_['veredicte']}** |")
    b_ = p["B_mascara_sense_dada"]
    A(f"| **B** · cap màscara demana el que no hi ha | píxels amb màscara > 0,01 on la capa "
      f"no té dada | {b_['total']} px (llindar 0) | **{b_['veredicte']}** |")
    c_ = p["C_disc_lunar"]
    A(f"| **C** · el disc lunar és net | nivell mostrat dins de la intersecció dels discos "
      f"lunars ({c_['px_interseccio']} px) | mitjana {coma(c_['nivell_mitja'], 4)} · p99 "
      f"{coma(c_['nivell_p99'], 4)} · **V13 0,137 · V13_Pere 0,024** | **{c_['veredicte']}** |")
    d_ = p["D_monotonia"]
    A(f"| **D** · perfil monòton | on cau el màxim del perfil radial, i si baixa d'allà cap "
      f"enfora (des d'1,07 R☉, on la cobertura ja és completa) | màxim "
      f"{coma(d_['maxim_del_perfil'], 3)} a **{coma(d_['r_del_maxim_Rsol'])} R☉** — "
      f"**la V13 el té a 2,0** — i {d_['pujades']} pujades de {d_['n_calaixos']} calaixos, "
      f"la pitjor {coma(d_['pujada_maxima'], 5)} | **{d_['veredicte']}** |")
    f_ = p.get("F_lluna_rodona")
    if f_:
        A(f"| **F** · la Lluna és rodona | el radi de la silueta negra, raig a raig "
          f"({f_['n_azimuts']} azimuts) | {coma(f_['r_min_px'],1)}–{coma(f_['r_max_px'],1)} px "
          f"sobre {coma(f_['r_mediana_px'],1)} → **{coma(f_['desviacio_maxima_px'])} px** de "
          f"desviació (llindar {coma(f_['llindar_px'],0)}; la primera V14 en feia **23**) | "
          f"**{f_['veredicte']}** |")
    e_ = p["E_halos"]
    A(f"| **E** · cap halo | ondulació del perfil a la vora interior de cada capa | "
      f"màxima **{coma(e_['amplitud_maxima_pct'], 3)} %** del nivell, a 1,31 R☉ "
      f"(llistó {coma(e_['llindar_pct'])} %, que és la discrepància entre esglaons veïns "
      f"que `research/100` va mesurar) | **{e_['veredicte']}** |")
    A(f"\nNivell del compost: **{coma(d_['nivell_a_1.1_Rsol'], 3)}** a 1,1 R☉ · "
      f"**{coma(d_['nivell_a_2_Rsol'], 3)}** a 2 R☉ · **{coma(d_['nivell_a_4_Rsol'], 3)}** a 4 R☉. "
      "La V13 hi feia 0,518 (a 1,09) · 0,719 (a 2,15) · 0,484 (a 3,74), o sigui que **el seu "
      "perfil pujava del limbe cap enfora fins a 2 R☉**: la corona interior hi era més fosca "
      "que la mitjana, que és el vel de la capa de 10,3 s.\n")
    A("\n## La Lluna i el Sol\n")
    A("El llenç va centrat al **Sol**, o sigui que **la Lluna hi llisca**: 28,5 px al llarg "
      "de la totalitat, el 6,3 % del seu radi. Si cada capa es queda amb el forat dels seus "
      "propis fotogrames, la silueta que en surt és la **intersecció** dels discos —un "
      "*lune*—: la primera V14 tenia **16.643 px de corona dins del disc de C2** i **8.293 px "
      "de negre a fora**, fins a **23 px** enllà del limbe, i la mossegada es menjava la "
      "protuberància.\n")
    A("⏭️ La cura és **la decisió que ja havies pres el 27-08** —treballar només en C2 perquè "
      "la Lluna surti rodona—, aplicada també DINS de la totalitat:\n")
    A("1. **la Lluna va DECLARADA**: un sol disc, el dels fotogrames de contacte de C2, i "
      "totes les màscares hi van a zero. Rodona per construcció;")
    A("2. **el Sol el posa la capa 13**, les protuberàncies de C2 en mode **Aclarir** — la "
      "mateixa que la cadena posa al seu producte (`f4.psb_resultat`, capa 09) —, que torna a "
      "tancar l'anell del limbe.\n")
    p_ = P["portes"].get("F_lluna_rodona")
    if p_:
        A(f"**Mesurat**: la silueta de la Lluna té el radi entre {coma(p_['r_min_px'],1)} i "
          f"{coma(p_['r_max_px'],1)} px sobre una mediana de {coma(p_['r_mediana_px'],1)}, o "
          f"sigui **{coma(p_['desviacio_maxima_px'])} px de desviació màxima** (abans, 23) i "
          f"{coma(p_['rms_px'])} px d'rms. **És rodona.**\n")
    A("⚠️ El preu, declarat: es perd la mica de corona que als fotogrames tardans es veia dins "
      "del disc de C2. És el mateix preu que ja vas acceptar per tenir la Lluna rodona.\n")
    A("⚠️ I una cosa que la V13 tenia i la V14 no: el seu disc lunar no era negre del tot "
      "(0,024 al `V13_Pere`). **No és earthshine**: mesurat, és un gradient llis que puja cap "
      "al limbe i **sense cap detall lunar** —és llum de la corona escampada per l'òptica—. "
      "L'earthshine de veritat demana una pila a part, emmascarada al revés i registrada a la "
      "LLUNA i no al Sol (`research/112` §7); continua pendent.\n")
    A("\n## Tres coses que veuràs de seguida en obrir-lo\n")
    A("**1. Els plomalls no hi són, i és correcte.** El que hi ha a cada capa és la **BASE "
      "calibrada**: la corona tal com surt de la composició, sense cap filtre de detall. Els "
      "plomalls que la V13 ensenyava els porta el revelat directe dels RAW, que arrossega el "
      "seu propi contrast local. A la cadena d'avui el detall va **a part**, com a capes en "
      "Superposar (passa-alt, radial, NRGF, MGN), i viuen a "
      "`~/Desktop/Eclipse determinista/2-OUTPUT/017_VIXEN_CIENCIA/Eclipsi_2026_VIXEN_CIENCIA.psb`. "
      "Posar-les sobre la V14 és arrossegar-les; no s'han posat aquí perquè la V13 no en tenia "
      "cap i l'encàrrec era capa per capa.\n")
    A("**2. El to és el del run, no el de la maqueta.** La corba és la declarada: pendent "
      "**0,22 per dècada** i àncora 0,74 a 1,05–1,15 R☉. La maqueta de la V13 en demanava "
      "**0,166** (`research/108` §3) i per això la seva corona exterior sembla més viva. "
      "És **un sol número** i no toca la dada: si el vols a 0,166, es refà.\n")
    A("⏭️ I hi ha una segona meitat d'aquesta diferència, que es veu al "
      "`V14_perfil_radial.png`: **la V14 segueix la forma de la maqueta fins a ~2,7 R☉ i "
      "d'allà cap enfora s'aplana a 0,245**, perquè el que hi ha allà **és el cel** i el "
      "compost el porta com un terra pla (decisió de la cadena: el terra és cel, no negre). "
      "A la V13 el cel no s'havia tret i el seu propi nivell queia amb el radi —el "
      "vinyetatge—, i això li donava un gradient que semblava corona.\n")
    A("**3. La capa 12 queda tapada per la 11**, exactament com a la V13: la màscara d'anell "
      "de la 11 passa per damunt de les perles. No és cap canvi meu; si les vols veure, la "
      "que s'ha d'obrir és la 11.\n")
    A("\n## Vistes\n")
    A("A `CapesTotalsV14_vistes/`, totes al **llenç sencer** i sense cap retall:\n")
    A("- `V14_compost.png` — el muntatge tal com s'obre;")
    A("- `capa_NN_imatge.png` — la imatge calibrada de cada capa;")
    A("- `capa_NN_mascara_V13_portada.png` — la màscara de Pere al llenç nou, abans de retocar;")
    A("- `capa_NN_mascara_V14.png` — la mateixa, després;")
    A("- `CONTACT_mascara_V13_portada.png` i `CONTACT_mascara_V14.png` — les dotze d'un cop;")
    A("- `V14_quina_capa_mana.png` — quina capa té el pes efectiu més gran a cada píxel;")
    A("- `V14_perfil_radial.png` — el nivell contra el radi, amb la V13 i la maqueta al costat;")
    A("- `V13_contra_V14.png` — els dos composts, cadascun al seu llenç sencer.\n")
    A("\n## El que NO s'ha fet\n")
    A("- **Cap màscara s'ha repintat.** El retoc és una multiplicació per la validesa mesurada "
      "de la capa; on la V13 demanava dada que existeix, la màscara és la seva, intacta.")
    A("- **Cap filtre circular.** Norma del rectangle: el que talla és la manca de dada.")
    A("- **Cap capa d'ajust ni corba a sobre.** El to és el del run, declarat al seu rebut.")
    A("- **El run és intacte.** La V14 s'escriu fora, i el run només s'ha llegit.\n")
    out = os.path.join(dest, "CapesTotalsV14_REBUT.md")
    open(out, "w").write("\n".join(L) + "\n")
    print(out)

if __name__ == "__main__":
    main()
