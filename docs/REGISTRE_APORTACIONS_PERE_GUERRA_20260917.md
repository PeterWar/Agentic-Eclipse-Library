# Registre d'aportacions de Pere Guerra al projecte Eclipse 2026

**Data del registre:** 17 de setembre de 2026 · **Redactat per:** Claude (Fable 5.1), a petició de Pere, a partir de
la memòria del projecte, dels 170 documents de `3-RECERCA/` i de l'índex de lliçons de la skill
`postprocessat-corona`. Cada línia porta la data i on és la prova. Les aportacions són de Pere; els mesuraments
que les van confirmar són dels agents (Claude i Codex).

**Per què existeix:** Pere vol que quedi constància del que ell ha aportat a un procés de cinc setmanes i milions
de tokens, per si és útil per millorar els models. Anthropic decidirà si val. Aquest registre acompanya
`IA/FEEDBACK_ANTHROPIC_20260917.md`.

---

## A. Normes de mètode que Pere va imposar

Cadascuna va néixer d'un error repetit dels agents i el va aturar. Són la part més transferible.

| Data | Norma de Pere | Què corregia | Prova |
|---|---|---|---|
| 07-09 | **Causa arrel, mai cosmètica.** Cap suavitzat, retall o pedaç que amagui un artefacte sense curar-ne la causa a l'origen; cap sacrifici de detall. La pregunta és sempre «què l'està causant?» | Versions senceres (V33) que tapaven anells i costures als filtres en lloc de curar la base | memòria `norma-causa-arrel-mai-cosmetica`; 3-RECERCA/149, 150 |
| 21-08 | **«Torre de Pisa»: es corregeix a la base, no a les capes de sobre.** Una capa del fonament desplaçada 1 px feia heretar la inclinació a totes les altres | Arreglar «en capes posteriors el que ja s'hereta de dins» | 3-RECERCA/87 §2; memòria `torre-de-pisa-corregir-a-la-base` |
| 23-08 | **Norma del rectangle.** Tot filtre s'aplica a tot el rectangle de la imatge, mai a una circumferència: les retallades circulars deixen halos i es mengen corona | Error recurrent del model (declarat com a tal a la memòria) | 3-RECERCA/93–95; memòria `norma-del-rectangle-cap-filtre-circular` |
| 26-08 | **Mai retalls: sempre el llenç sencer**, també a les vistes provisionals i de diagnòstic | Retalls que amagaven defectes fora de la zona triada i un llenç encongit 697 px sense dir-ho | memòria `mai-retalls-sempre-el-llenc-sencer` |
| 26-08 | **El mosaic RGGB i el balanç per canal es comproven a cada resultat** | Error recurrent d'interpretació del mosaic de Bayer | memòria `comprova-sempre-el-mosaic-rggb` |
| 26-08 | **Tot el que s'ha de mirar va a un sol lloc**, no escampat per carpetes internes | Lliurables perduts dins de l'estructura de l'agent | memòria `tot-el-que-pere-ha-de-veure-va-a-output` |
| 19-08 / 27-08 | **La Lluna, només de l'instant d'ancoratge** i **les protuberàncies, només del segon contacte**: barrejar instants deforma el disc | Discos lunars deformats per unir dos instants | memòries `lluna-nomes-de-linstant-dancoratge`, `nomes-c2-la-lluna-rodona` |
| 27-08 | **La resolució dels filtres ha de seguir el senyal/soroll**, no ser fixa | Fons de filtre amb estàtica | memòria `filtres-la-resolucio-segueix-el-sn`; 3-RECERCA/148 |
| 07-09 | **Versions lleugeres:** mentre quedin artefactes, s'itera sobre una sola base lineal i els filtres, no sobre el projecte sencer (9,6 GB per versió) | Temps, disc i tokens | memòria `versions-de-filtres-lleugeres` |
| 17-09 | **Cap filtre no pot veure la franja que la Lluna escombra mentre es mou** (28,5 px); els filtres són ràsters estàtics i s'han de recalcular si la base canvia | Correccions a la base que no podien arreglar res | 3-RECERCA/165; memòria `norma-cap-filtre-amb-la-franja-del-moviment-lunar` |
| 18-08 / 27-08 | **La ciència de Brno per sobre de l'estètica de tutorial**, i **Brno és jutge, mai font:** cap píxel seu al producte | Risc d'inventar detall o de copiar | memòries `postprocessat-druckmuller-sobre-astrofalls`, `brno-jutge-no-font` |
| 02-09 | **Cap flux massiu d'agents sense dir-ne el cost abans** | Una auditoria de 117 agents va gastar el 21 % del seu pressupost setmanal | memòria `cap-flux-massiu-dagents` |
| 06-08 / 03-08 | **Avança sol, informa una vegada, parla planer, sense manuals** | Interrupcions i documentació que ningú no havia demanat | memòries `avanca-sol-no-preguntis-tant`, `sense-manuals-estalvia-tokens`, `parla-planer-i-demana-la-camera` |
| 17-09 | **Les capes de Pere, byte a byte; les correccions, en una capa a part.** Noms de capa de nou paraules com a molt; la història va al rebut | Edicions no demanades al limbe lunar (V70, V74 i V75 refusades) | memòries `pere-refa-v77-des-de-v69-vora-lunar-refusada`, `noms-de-capa-maxim-9-paraules` |

## B. Defectes que Pere va veure a ull abans que cap control numèric

| Data | Què va veure | Què va resultar ser | Prova |
|---|---|---|---|
| 23-08 | Dos artefactes al passa-alt | Quatre causes mesurades i tres comprovacions noves «que saben fallar» | 3-RECERCA/95; memòria `passalt-artefactes-i-controls-falsos` |
| 27-08 | Ratlles diagonals al passa-alt | Eren anells: el perfil radial es restava per calaixos (900 graons) i cada graó és una vora dura. Cura: interpolar | 3-RECERCA/111; memòria `anells-de-calaix-del-perfil-radial` |
| 27-08 | Una taca a 3 radis solars del compost de la Sony | Un reflex intern de l'objectiu sobre l'eix òptic, que només veu el primer apuntament | memòria `ghost-de-leix-optic-sony` |
| 27-08 | Un estriat, marcat en lila | Dues coses diferents: una de real (del cel) i una del sensor de la Vixen | 3-RECERCA/113, 115; memòria `jutge-dos-trens-i-estriat-resolt` |
| 28-08 | «N'estàs detectant fora del camp» (87 «estrelles de catàleg») | 15 de 18 eren gra: la falsa alarma real sobre gra correlacionat és unes 100 vegades la gaussiana. D'aquí surt la norma del control nul aparellat | 3-RECERCA/125; memòria `control-nul-per-a-tota-llista-per-llindar` |
| 29-08 | Una capa d'earthshine lliurada que era pitjor que un sol fotograma | D'aquí surten la «mateixa vara» entre versions i la injecció cega | 3-RECERCA/127; memòria `portes-de-senyal-feble-injeccio-i-vara` |
| 31-08 | Un «cràter» que l'agent havia batejat Aristarc era fals | Una mota de pols del sensor: Aristarc cau a 350 px d'allà per l'efemèride, i els flats fets deu dies després ja no la portaven | 3-RECERCA/127 §7; memòria `mota-de-pols-i-flats-del-dia` |
| 04/05-09 | La geometria de la V25 i la V26 no li quadrava (dues vegades) | Anaven girades 138,5°; cap porta ho veia: les finestres i l'escaquer s'enganyen amb l'estructura radial | 3-RECERCA/132; memòria `v26-artefactes-i-cel-que-aplana` |
| 06/08-09 | 137 marques pintades sobre 19 capes (V31–V36) | Cinc famílies amb causa a l'origen: el camp pla de la Sony ondulat imprès invertit, la vora del camp de la Vixen dins de la Sony, la vora dels 8 s, els graons de gra a l'entrada de cada exposició | 3-RECERCA/145–153 |
| 09-09 | Marques verdes a la capa RHEF que semblaven núvols | No eren núvols: un patró fix del sensor que camina amb la deriva de la muntura | 3-RECERCA/158 |
| 16/17-09 | Vuit marques a la V69 i set a la V74 | El limbe dentat per un cercle booleà; la línia verda era una capa blanca sota la rampa lunar; la taca ampla és llum dispersada als RAW amplificada per la corba | `4-RESULTATS/v71…`, `v73…`, `v75…` |
| 17-09 | **Els negres de la corona interior no eren a la base: eren al ràster del filtre WOW bilateral.** Ho va provar ell a mà interpolant la capa, després que l'agent declarés arreglat el que no ho estava («no has arreglat res») | La troballa que dona peu a la norma de la franja lunar | 3-RECERCA/165; memòria `negres-corona-interior-son-al-raster-wow-bilateral` |

## C. Mètodes propis de Pere que els agents van formalitzar després

| Data | El que feia Pere a mà | En què s'ha convertit | Prova |
|---|---|---|---|
| 17-08 | Superposar l'apilat d'un segon damunt de l'HDR pla: l'«efecte 3D» | «Detall × envolupant»: com es dosa i què costa | memòria `efecte-3d-superponer-corona` |
| 28-08 | Matar els halos del camp exterior amb un Desenfocament radial de zoom i una rampa radial, després de dues rondes fallides dels agents | L'operador **fons per raig**: al camp exterior l'artefacte varia al llarg del raig i el senyal varia en azimut; un suavitzat només en ln r mata l'un i conserva l'altre, sense cap referència que es pugui enverinar (15 de 17 marques a zero) | 3-RECERCA/123; memòria `fons-per-raig-desenfoc-radial` |
| 25-08 | La seva màscara i la decisió sobre l'anell verd | Separació del cel per color, no per nivell | 3-RECERCA/104 |
| 28-08 | El revelat de la capa Sony amb Camera Raw, declarat canònic | Un format mesurat amb números (interior ~0,90, cel fosc i blau) | memòria `format-canonic-sony-de-pere` |
| 02-09 | La tria de la corba de to B entre dues vistes | Corba declarada (0,22 per dècada), mai derivada d'un percentil | 3-RECERCA/130 |
| 17-09 | Interpolar a mà els filtres a la franja 456–500 i pujar els negres del disc amb Camera Raw | El lliurament final (V77 → V80) | memòria `pere-interpola-els-filtres-i-camera-raw-al-disc` |
| tot | La pila del Photoshop: quines capes, en quin mode i a quina opacitat | La imatge final és una tria editorial seva sobre capes calculades | `4-RESULTATS/pdf_filtres_brno_20260917/` (apartat 6 del PDF) |

## D. Decisions de direcció

- **La captura** (juliol–agost): dos trens independents (Vixen VSD90SS amb Canon R6 III i Sony A7R IIIA amb 300 mm f/2,8), marge dinàmic per damunt de focal, escales d'exposició acceptades el 09-08, gphoto2 per a la missió i l'EDSDK només per preparar (07-08). Resultat: 377 fotos, zero divergents. 3-RECERCA/46–70.
- **Via de la foto** (23-08): el producte fusionat és una fotografia fidel, no una mesura; i l'ordre nou en quatre fases amb rebuts. Memòries `decisio-via-foto-i-pilot-vixen`, `ordre-nou-projecte-photoshop-quatre-fases`.
- **Tornar a començar amb un pilot d'un sol tren** (26-08) quan el projecte s'havia embolicat, amb el llenç declarat sencer des del primer dia. Memòria `represa-reagrupem-pilot-vixen-nomes`.
- **«Hi ha el que hi ha»** (09-09): refusar la reducció de soroll als filtres. 3-RECERCA/159.
- **Dos agents de cases diferents sobre el mateix projecte** (Claude i Codex), amb traspassos escrits, un sol escriptor alhora i contrastos amb altres models: setmanes de feina alterna sobre un fitxer de 7 GB sense cap corrupció.
- **Prioritats de tancament** (16-09): espai, després aprenentatges documentats, després skills; els scripts reproduïbles no són essencials.
- **Aquest registre i el feedback** (17-09): la decisió de fer arribar l'aprenentatge a qui fa els models.

## E. El que en surt, en una frase per a qui entrena models

L'usuari no va aportar només dades i encàrrecs: va aportar **el criteri que faltava**. Mirant cada imatge, va trobar defectes
que cap porta numèrica veia, va negar-se a acceptar pedaços, i va convertir cada error repetit en una norma curta que,
un cop escrita a la memòria i a les skills, va deixar de repetir-se.

---

*Constància:* aquest fitxer porta la data a dins i la seva empremta SHA-256 és a `IA/REGISTRE_APORTACIONS_REBUT.json`.
Un fitxer local no prova la data davant de tercers; la proven l'enviament pel canal oficial (queda lligat al compte i al
dia) i, si Pere ho autoritza, una publicació amb data pública.
