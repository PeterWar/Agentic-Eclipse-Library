# 129 · Auditoria general del projecte, balanç i pla per al 2027

**2 de setembre de 2026.** Ordre de Pere: «una auditoria general i completa
del projecte», resumir en quin punt som, què ha funcionat i què no,
actualitzar la skill si té sentit, i que l'exercici serveixi per a quatre
esperances: (1) treure més detall de la imatge final, «cada fotó de llum
importa»; (2) millorar la captura del 2027 amb Eclipse Command; (3)
millorar-la amb la web d'ubicacions i meteorologia; (4) automatitzar molt més
el postprocessat.

**Mètode.** Deu lectors en paral·lel (un per subsistema), sis síntesis (estat,
les quatre esperances i la skill) i verificació adversària de cada afirmació
clau contra els fitxers. ⚠️ **La verificació va quedar a mitges**: 76 agents
de 117 van acabar; els 41 que van caure eren refutadors de les síntesis 2, 3 i
5, els revisors dels esborranys de la skill i el crític de completesa, tots
pel límit de sessió. La cobertura exacta és a §14. ⛔ **Cost: 16,8 milions de
tokens de subagents, el 21 % del pressupost setmanal de Pere en una sola
consulta.** Regla nova, de Pere: cap flux massiu d'agents més sense
pressupost explícit; auditories amb pocs agents o cap.

Els fitxers del flux (mapes dels deu lectors, síntesis, veredictes) són a
`/private/tmp/claude-501/-Users-USUARI-Downloads-Eclipse-2026/fa2a9ec7-ecad-44a9-be36-0188281c6910/tasks/wpuxpfrep.output`
i al `journal.jsonl` del mateix flux; són volàtils. Pàgina publicada:
https://claude.ai/code/artifact/4687853c-9ffb-414f-9f6c-c3703c1f2ee3

---

## 0. El punt exacte, en deu línies

1. **Captura feta i auditada.** El run `20260812T202219` va lliurar el nucli
   científic sencer: Sony 33/33, R6 67/67, 377 de 391 captures reconciliades,
   retard màxim 1,230 ms (informe PDF del run, l.20 i 56; CONFIRMAT).
   Contactes reals: C2 a −1,0 s i C3 a +102,7 s del predit, totalitat
   103,7 s (`research/71` l.24).
2. **Calibratge i composició lineal** viuen a la cadena determinista
   (`research/tools/eclipse_determinista/cadena.py`), runs vigents 019 Vixen i
   016 SONYTOT. ⛔ Cap fitxer de la cadena és a git (CONFIRMAT).
3. **Photoshop.** El fitxer viu és `CapesTotalsV24.psb` (V24e, 20 capes, 31-08
   22:05). És un muntatge **no lineal de cap a peus**: 12 capes ACR de Pere,
   la capa Sony pel seu Camera Raw, fons per raig, earthshine, estrelles,
   reflex i perímetre lunar. El seu rebut és de les 21:10, anterior al fitxer.
4. **Earthshine detectat**: r = +0,792 amb el mapa LROC, control nul −0,070 ±
   0,123, **7,0σ**, sense cap paràmetre ajustat (`research/126` l.79;
   CONFIRMAT). Producte vigent: r = +0,885, injecció 0,957 PASS, pesos Sony
   ap1 51,2 % · Vixen10 33,9 % · Vixen2 14,8 % (`research/127` §8).
5. **Estrelles**: 85 de catàleg, puresa 95,8 % mesurada amb control nul, límit
   V ≈ 9,5 (`research/125`).
6. **Frontera de dada mesurada**: el cel iguala la corona a 2,41 R☉, a 5 R☉ el
   cel n'és 9,2×, i la fotometria es declara fins a 3,2 R☉ (`research/99`;
   CONFIRMAT). Més enllà de ~3,25 R☉ el compost és cosmètica declarada.
7. **Publicació**: l'APOD és un esborrany, no consta cap enviament. La
   deflexió no és mesurable amb aquestes dades.
8. **2027**: Eclipse Command V1.02 no serveix tal qual. La porta de durades
   exigeix 60-110 s (`gui/tools/qa_totality_duration_gate.py:57-58`) i el
   disseny de blocs dels Sony acaba a 200 s (`adaptive_profiles.py:756`);
   Zahara fa 271 s. El requisit d'escala monòtona està acceptat; la solució,
   no decidida (CLAUDE.md §1 quater).
9. **Dades**: tot el produït des del 22-08 viu en un sol disc. `/Volumes`
   només té Macintosh HD i Time Machine no té destinació. El `.git` porta
   ~156 GiB d'objectes solts més 17 GiB de brossa d'un `git add` avortat.
   És **el risc més gran del projecte** (§10).
10. **Skills**: eren una foto del 21-08 d'un mètode abandonat. Avui s'han
    reescrit (§9).

---

## 1. Què ha funcionat, per importància per a la foto

| # | Què | Prova | Estat de verificació |
|---|---|---|---|
| 1 | El nucli de captura: 100/100 fotogrames científics, jitter 1,2 ms, contactes travessats | informe PDF del run | CONFIRMAT |
| 2 | Coherència de transparència per fotograma + dues passades de resta: anells Vixen **27,5 % → 0,4 %**, costures **88,6 % → 4,6 %** | `research/100` l.1096-1139 | CONFIRMAT |
| 3 | El diagnòstic del que Pere veia: no era la fusió sinó el **cel per fotograma** i un **anell verd instrumental**; la cura final és la **mediana de canals**: mètrica de Pere −8,54 → −2,93·10⁻⁴, jutge extern +0,00347 ± 0,00178 | `research/102`, `107` l.85-88 | CONFIRMAT |
| 4 | **Fons per raig**, formalització del desenfoc radial de Pere: a la V19 al llenç sencer, 17/17 marques passen, 16 a bony 0,0000 i la 17a a 0,019 (gradient real del cel); al prototip sobre el retall recupera 2.097 de 2.102 estrelles | `research/123` §6, `124` §2 | MATISAT: el 2.097 és del prototip, no d'un lliurable vigent |
| 5 | **Igualació ρ en baixa freqüència** de la Sony: pitjor bony 0,0024 als 9 arcs marcats | `research/121` l.20 | MATISAT: només a la banda 3,6-4,6 R☉; fora la V18 fabricava halos nous (0,111) i el lliurable final fa servir el fons per raig |
| 6 | **L'estructura passa contra Brno**: passa-alt 0,943 a 4,5° amb sostre Brno×Brno 0,976; Vixen×Sony 0,989 | `research/114` l.16, `115` l.185 | CONFIRMAT |
| 7 | **La corba de to identificada**: la maqueta de Pere fa 0,166 per dècada, `estira_log` en feia 0,503 i cremava 1,67 dècades (329.659 px a 0,998 fins a 1,45 R☉) | `research/108` l.21-26 | CONFIRMAT |
| 8 | **Earthshine i estrelles amb portes que saben fallar**: vara única, control nul aparellat, injecció cega | `research/125`, `126`, `127` | CONFIRMAT |
| 9 | **La norma del rectangle i la porta Photoshop real**, que han tancat dues famílies d'errors recurrents | `trampes.md`, `porta_photoshop.sh` | CONFIRMAT |
| 10 | **La cadena determinista**: un run immutable per execució, manifest de SHA-256, codi congelat; determinisme demostrat el 26-08 (60 de 64 fitxers bit a bit, els 4 amb només el segell) | `1-RUNS/PROVA_DETERMINACIO_20260826.md` | MATISAT: avui dona 59/5 perquè el PSB del run 002 es va re-desar a posteriori |

---

## 2. Què no ha funcionat

| Què | Causa mesurada | Estat |
|---|---|---|
| **Arcs entre esglaons veïns** de la R6 | Dues mitges escales de 2 EV a instants diferents i la transparència caient: el mateix 1/128 s val **1,0598 a t=8 s i 0,9779 a t=89 s** (`research/100` l.1009; CONFIRMAT); veïns discrepen 1,1-1,3 % amb signe alternat | IRREDUCTIBLE al postprocessat; és captura 2027 |
| **Terç residual de l'anomalia verda** | Barreja temporal dins de cada esglaó més un anell instrumental fix a l'eix òptic (`research/107`) | «defensablement irreductible»: la cura seria un flat espectral amb llum solar |
| **Salts de la Skywatcher** (+223 px, −715 px) | En treure el filtre es va moure la lent de 300 mm; la pertorbació es va alliberar a C2+30 i C2+50 (`research/72`) | IRREDUCTIBLE: àncora DSC06990 perduda, rotació de camp +7,86′, segon apuntament amb vel de 40,2 comptes |
| **Mota de pols del R6** disfressada de cràter | Fixa al sensor a (3579, 2374), +33,4 comptes als Vixen i +5 a la Sony; absent dels flats de 10 dies després (r = 0,00) | CURAT al postprocessat (pes Vixen 0 en 22 px); lliçó 2027: flats del dia o dither |
| **Franja a 2,52 R☉** | Extinció local, no corona (`research/116` l.876) | IRREDUCTIBLE |
| **Cura del cel a la Sony** | Refusada pel jutge extern (dos apuntaments) | OBERT |
| **Capa d'earthshine del 29-08 pitjor que un fotograma sol** (0,777 contra 0,857) | Model de vel ajustat fins a r<0,975 contaminava el disc; es va lliurar sense comparar amb la mateixa vara (`research/127` l.27; CONFIRMAT) | CURAT amb la vara única |
| **Sense drizzle a la cadena** | `f2.py:158-161` remostreja els subplans CFA amb `cv2.remap INTER_LINEAR` (CONFIRMAT); l'antic pipeline en feia amb gota 2,0 i es va abandonar sense rebut | OBERT |
| **Temps d'exposició nominals** a `f0.py:26` i `f1.py:51` (CONFIRMAT); els 1/60, 1/30, 1/15 són 1/64, 1/32, 1/16, −6,25 % (CONFIRMAT) | La cura ja existeix al pilot (`pilot_vixen_claude/comu.py` l.106-124, taula `EXP_FISICA`) i no s'ha portat a la cadena | OBERT |
| **Cap còpia física des del 22-08, `.git` inflat, codi sense commitar** | Vegeu §10 | OBERT i és el risc més gran |

---

## 3. Taula per fase

| Fase | DEMOSTRAT | FALTA | IRREDUCTIBLE amb aquestes dades |
|---|---|---|---|
| Captura | nucli 100/100, jitter 1,2 ms, contactes travessats | rellotge R6, cua 3152-3177, causa del USB −52, inventari de la 6D | arcs entre esglaons, salts de muntura, 16 s d'earthshine útils de 24 |
| Calibratge | pedestal 512 mesurat, flat Vixen validat amb invertits, flat Sony pel dither | darks per temperatura, exposició física a la cadena, variància per canal | mota sense flat del dia, anell verd de l'eix |
| Registre | centre per efemèride, dos trens a 0,21 px | model de punteria als contactes | cap |
| LDIC | una sola suma, coherència, màscara lunar per fotograma, cel pel color | cura del cel Sony, drizzle, H2 amb control de sostre | terç de l'anomalia G, franja 2,52 R☉ |
| Filtres | mediana de canals, H1/H1b, suavitzat pel S/N, estructura contra Brno | veredicte de Pere sobre WOW/NAFE/FNRGF; mesura de Claridad i Neblina | gra a 7 R☉ |
| Photoshop | V24e amb rebuts i fidelitat byte a byte | rebut posterior al PSB; compost lineal a la graella de Pere; decisió de corba | costures de vora interior d'esglaó |
| Earthshine i estrelles | 7σ; 85 estrelles amb puresa mesurada | variància propagada, cobertura per unió | color de l'earthshine, deflexió |
| Dades | originals íntegres (fingerprint reproduït) | còpia externa, neteja del `.git`, `.gitignore`, commit | Paperera no auditable |

---

## 4. Les deu lliçons més cares

1. **La corba de to per percentils** va tenir el projecte encallat del 23 al
   26-08 (`research/108`).
2. **Les dues mitges escales entrellaçades** són l'arrel dels arcs i no tenen
   cura (`research/100` §E).
3. **Un jutge intern no basta**: la meitat dels candidats del 25-08 passaven
   els seus controls i el jutge extern els va tombar (`research/107`; norma
   zero).
4. **`distanceTransform` sobre cobertura amb el forat lunar**, tres cops en dos
   dies (`research/93`, `100`).
5. **El perfil radial per calaixos** fabricava el 54 % del detall
   (`research/100` l.424).
6. **La referència enverinada i la fosa per canal** de la V19 dissenyada, que
   mai no es va escriure (`research/122`).
7. **El model de vel ajustat massa endins** feia la capa d'earthshine pitjor
   que un fotograma (`research/127`).
8. **El Wiener amb diferències de gaussianes menjava el 17 % del senyal**, i
   només la injecció cega ho va veure (`research/127` l.129).
9. **Les trampes de PSB**: ZIP a la fusionada, `topil()` a 8 bits, `8B64`. Tres
   lliuraments refusats per Photoshop (`research/117`, `118`, `119`).
10. **Un `git add` massiu avortat** el 23-08 ha deixat ~163 GiB inaccessibles
    al `.git`.

---

## 5. Esperança 1: més detall a la imatge final

### 5.1 On és el detall que falta

La resposta curta: **no és a cap fotograma nou, és a la base**. La V24e és no
lineal de cap a peus i hereta el desacord entre esglaons veïns del muntatge
per capes (ondulació 0,208 % a la capa 04, `research/117` §4). La cadena
determinista ja té la composició LDIC en una sola suma ponderada de 67
fotogrames Vixen i 21 Sony, amb màscara lunar per fotograma i coherència. El
primer guany, i el més gros, és posar aquesta base sota les capes de Pere.

Vies, ordenades per guany contra cost, amb la porta que les jutja:

| Via | Què hi ha | Guany | Risc | Cost | Porta |
|---|---|---|---|---|---|
| a) Compost lineal a la graella de Pere | LDIC 019 + 016 existeixen a 8096×8960; `fes_v17.py` ja compon la Sony >1 s a la graella V16 en un sol re-mostreig | el més gros: base sense costures ni ondulació | cap si es fa amb PES per canal | 1-2 dies | alineació ≤0,3 px amb la capa 01; R/G i B/G al rebut |
| b) Drizzle gota 2,0 a `f2.compon` | avui bilineal a mitja resolució (CONFIRMAT). ⚠️ El submostreig no és 1,7× uniforme: per canal Vixen R 1,95×, G 1,08×, B 1,30×; en luminància cap tren no està submostrejat (MATISAT pel contracte del 23-08) | escales de 2-4 px al R i al B | escaquer si la gota baixa de 2,0; gra correlacionat (va enganyar la detecció d'estrelles) | 2 dies | H4, meitats A/B, H1b, injecció cega a 2-8 px |
| c) Temps d'exposició físics a la cadena | taula `EXP_FISICA` ja al pilot | −6,25 % d'escala als esglaons curts absorbit avui només com a escalar | cap | mig dia + un run | dispersió de k baixa; F0 per anells |
| d) Darks per temperatura, mitjana retallada | `masters_vixen_v2.py` ho fa fora de la cadena; el màster de 10 s torna a 511,0 a la zona activa | 0,5 DN = 5 % del fons de l'earthshine | cap | mitja jornada | F0.2 pedestal actiu = zona fosca |
| e) Variància per canal | només `PES_c` avui | permet porta de soroll a WOW/NAFE i barra d'error a l'earthshine | cap | 1 dia | meitats A/B |
| f) Corona interior sota 1,12 R☉ | radi mínim amb corona ja a 1,0133 R☉; dèficit ~0,25 amb Brno | petit però visible al limbe | mitjà | una tarda | Sony com a jutge |
| g) Earthshine | r +0,885; queden variància, cobertura per unió (94 → 100 %) i halo per component | petit al display; la significança citable continua 7σ | baix | 2-3 dies | vara única, injecció |
| h) Sony segon apuntament | ja entra a la corona; paga escala fina | baix | | | |
| i) Estrelles | límit V ≈ 9,5 amb aquest cel | cap més | | | |
| j) Camp exterior >3,25 R☉ | cosmètica declarada; el fons per raig ja fa el màxim | només la 6D, mai inventariada | | | |

### 5.2 El pla no lineal → lineal: convé invertir-lo

**El projecte de Photoshop no es pot linealitzar**: les capes ACR ja porten la
corba i no hi ha camí de tornada. La versió lineal no surt del PSB, surt dels
RAW, i ja existeix als runs 019 i 016, però a un altre llenç.

L'ordre bo és l'invers, i **no atura Pere**: la V24e és la maqueta d'aspecte i
la referència de geometria (V23: 10551×7506, disc de C2 a (5361,9 · 3774,7),
R 453,5 px, `research/128`). La cadena lineal es compon **a la seva graella**
en un sol re-mostreig del RAW; sobre aquest lineal van els filtres, la ρ per
canal dins del radi de detall, el fons per raig a fora, i la corba declarada
com a última passa. Photoshop rep el compost acabat més les capes artístiques
de Pere byte a byte: perles, reflex, earthshine, retall.

Què falta: (1) el compost Vixen+Sony a la graella V23 amb PES per canal; (2)
**la decisió de corba**, perquè n'hi ha dues de declarades: 0,166 de la
maqueta i 0,17/0,68 de `research/108`, contra 0,22/0,74/0,045 de
`comu.py:573` (CONFIRMAT); (3) la re-injecció de les capes de Pere; (4) la
vara única per comparar V24e i lineal abans de lliurar.

### 5.3 Els halos de Camera Raw (Claridad i Borrar neblina)

⛔ **Cap document del projecte mesura Claridad ni Borrar neblina**: el grep
només toca el tutorial d'Astrofalls (`research/81`). El que segueix és
SUPOSAT sobre els mecanismes i MESURAT en el que ha passat amb operadors
germans dins del projecte.

**Què fan.** Claridad és un contrast local de tons mitjos amb radi gran: un
passa-alt ample sumat a la imatge ja tonificada. Borrar neblina estima un vel
i una transmissió locals per mínims i els treu. Sobre una corona el «vel» és
la corona K+F i el cel: treure'l buida el voltant del disc i realça tota vora.

**Per què tornen els halos**, amb el que el projecte ha mesurat:

1. **Radi gran sobre un gradient de 3,92 dècades.** Un passa-alt sense el
   perfil radial tret davant llegeix la curvatura del perfil com a estructura.
   (La xifra «6,6 % de detall inventat» del 23-08 surt d'un control defectuós i
   rectificat pel `research/100` §G3; el principi es manté i Brno el prescriu.)
   Camera Raw no treu cap perfil.
2. **Vores de màscara i costures.** Tota capa que s'apaga dins de la dada deixa
   un halo (norma del rectangle, `research/95`). A la V24e hi ha la màscara
   Sony 2,00-2,65 R☉, la rampa 2,45-3,25 del fons per raig, la rampa del
   reflex i el limbe. Un halo de fusió és una diferència de baixa freqüència
   als dos costats d'una màscara, invisible fins que un operador de radi gran
   la dibuixa.
3. **El limbe.** Un desenfoc calculat amb el forat de la Lluna a dins mostra
   d'un sol costat i fabrica un anell saturat (`research/111` l.49-55); la
   cura va ser la màscara lunar per fotograma i la guarda a 1,010 R☉, amb el
   passa-alt de 0,468 a 0,008 (`research/112` §6).
4. **Per canal.** Tota fosa o realç per canal és un pinzell de to: la fosa per
   canal de la V18 pintava un viratge R/G del 12 %/R☉ (`research/122`).

**La pila del projecte que dona el mateix efecte sense halos**, en aquest
ordre i sobre el **compost lineal**, mai sobre la imatge tonificada:

1. Fusió lineal dels dos trens: ρ per canal dins del radi de detall, fons per
   raig fora, tot al rectangle sencer.
2. NRGF en log r amb Savitzky-Golay davant.
3. ACHF multi-σ (2/4/8/16/32 px) sobre ln I amb convolució incompleta
   G(w·I)/G(w) i porta erf (`filtres.py`).
4. Mediana de les tres realitzacions de canal; mai detall per canal.
5. Suavitzat pel S/N (t = 0,18) i anivellat per anell |nivell − 0,5| ≤ 0,05.
6. Passa-alt σ 24 px i MGN a cinc escales com a capes Superposar apagades: el
   pes el posa Pere amb l'opacitat, que és exactament el dial de Claridad
   però sense halos.
7. Corba de to declarada com a última passa; sostre del màxim de la dada.

L'estructura d'aquesta pila passa contra Brno (0,943 a 4,5°; CONFIRMAT). Brno
fa l'ACHF sobre la brillantor del compost lineal amb corba log-lineal de
0,20-0,24 per dècada i zero píxels cremats (`research/109`); que no passi per
Camera Raw és inferit del seu programari declarat, no demostrat. ⚠️ I **Pere
encara no ha validat aquesta pila com a imatge impressionant**: el 26-08 va
apagar tot menys el passa-alt (`TRIES_DE_PERE.md`).

**Prova barata per decidir-ho amb Pere mirant.** A: la V24e amb la seva
passada de Claridad i Borrar neblina, exportada a TIFF 16 bits. B: el compost
lineal a la graella V23 amb la pila de dalt i la corba 0,17. Mateix llenç,
mateix retall 3:2, mateixa corba, i tres finestres 1:1 a 1,3, 2,5 i 4 R☉ al
costat del llenç sencer. Mateixa vara: bony per sector sobre envolupant
monòtona (`mesura_halos_v19.py`), H1 de nivell per anell, H4 contra la Sony,
`es_corona.py` per a les línies. Cost: mig dia; Pere només ha d'exportar A.

### 5.4 Pla de treball

1. Vara única sobre la V24e del disc (desatès): SHA, porta Photoshop, bony, H1,
   H4 sobre l'exportació.
2. Compost lineal Vixen+Sony a la graella V23 (desatès, 1-2 dies).
3. Temps físics i darks per temperatura a la cadena (desatès, un dia + un run).
4. La prova A/B dels halos (requereix Pere: exportar A i mirar).
5. Decisió de corba i radi de detall (requereix Pere).
6. Drizzle gota 2,0 (desatès, dos dies), amb les quatre portes.
7. Variància per canal i WOW/NAFE amb porta calculada (desatès, un dia).
8. Muntatge final: lineal + filtres + corba + capes de Pere byte a byte.
9. Commitar la cadena i les eines; regenerar el mapa de carpetes.

---

## 6. Esperança 2: la captura del 2027 amb Eclipse Command

### 6.1 Per què la V1.02 no serveix tal qual

- Porta de durades: exigeix 60,0-110,0 s i escombra una banda informativa de
  40-125 s (`qa_totality_duration_gate.py:57-63`; MATISAT).
- Disseny de blocs dels Sony: `A7R3A_BLOCS_MAX_TOTALITY_S = 200.0`
  (`adaptive_profiles.py:756`); per damunt cau a l'envolupant genèrica. ⚠️
  `research/70` no diu 200 s: parla d'«uns 120 s», i la frase de les 36
  imatges descriu el que s'EVITA amb el forat màxim de 76 s (MATISAT).
- Sostres de cua 33 i 27, unitats de mig eclipsi = (sostre − 15) // 3, sis i
  quatre (CONFIRMAT): amb 271 s no mana el temps, mana la cua.
- Zahara: 271,4 s, Sol a 37,9°, azimut 95,1°, C2 08:45:00 UTC;
  Tarifa 282 s (`Eclipse 2027/meteo_simple/dades_2027.json`; geomètric, 2-3 s
  optimista).
- Extinció: el ×11 del 2026 és una estimació (X 6,02-6,20 i k = 0,402 mesurat
  donen ×9,5-10); el 2027 amb X ≈ 1,6-1,7 surt ~×1,8-1,9 (MATISAT).

### 6.2 Requisits ja acceptats (CLAUDE.md §1 quater)

Escala monòtona d'1 EV amb veïns en el temps; cada esglaó a ≥2 instants
separats (el postprocessat hi posa número: >30-60 s, perquè el cel fi es
decorrelaciona ~85 % a 3 s i zero a 60-80 s, `research/107`); monitor de
transparència cada ~10 s; val als dos trens; validar per canal (G/R 1,369,
G/B 2,615); variància per canal; prou fotogrames per barreja. Brno: 8-50
aparicions per esglaó contra les nostres 1-2. Reserva de Pere: **el requisit
està acceptat, la solució no**.

### 6.3 Requisits nous d'aquesta auditoria

**R6 III + VSD90SS**: flats del mateix dia a l'orientació de l'eclipsi o
dither deliberat (la mota no és al flat de 10 dies després; aplicar-lo puja el
gra 4,96 → 7,20); rellotge mesurat abans de volar (0,27 px per segon a
l'alineació absoluta); CFexpress formatada de fresc; run de banc amb calor
real (sensor a 41-43 °C el 2026; a la costa a les 10:45 d'agost pot ser
pitjor); flat espectral amb llum solar per a l'anell verd de l'eix.

**A7RIIIA + 300 GM**: extracció del filtre sense contacte, o re-tensar i
verificar (3,6 kg de tren); comprovar el focus cada deu minuts durant la
parcial (nitidesa de 4,7-5,4″ a 7,57″ en onze minuts, `research/75`); més
integració d'earthshine i no més llarga: el cos filtra el RAW als 8 s
(autocorrelació +0,42 a lag 1), i amb el Sol a 38° l'àncora de 8 s queda a
menys d'1 EV del cremat (SUPOSAT: pintar àncores de 2-4 s més nombroses i
mesurar al banc on comença el filtrat); sostre de cua 33 sense mode
només-targeta: les opcions són drenar dins la totalitat (18-24 s cada
drenatge), partir l'escala entre trens com Mamalluca 2019, o la doble
targeta (`research/89`, sense cap prova).

**A7III**: sostre 30 (27 operatius), ràfega −3/0/+3; si fa vídeo, ISO
manual (el 2026 l'ISO automàtic va fabricar falsos shadow bands); és el
candidat natural a partir l'escala amb l'A7RIIIA.

**6D**: 3.062 CR2 fora de tot ledger, 163 fotogrames a 1/30 durant la
totalitat; cap inventari des del 15-08. O entra a l'app amb el perfil v2
card_only, o queda fora amb rellotge sincronitzat i protocol propi.

**Tots**: variància per canal, noms de fitxer o manifest amb el rol de cada
fotograma, exposició física registrada al run (els «10,3 s» reals són
10,079 s), no tocar cap cos durant el run, monitor de transparència com a
exposició pròpia.

### 6.4 Canvis al programari

- Porta de durades a 250-290 s; `KNOWN_TIER_EDGES_S` refets; la R6 al fuzz
  (avui zero ocurrències).
- Tram nou per damunt de 200 s als Sony, no el genèric.
- `render_hdr_coverage.py`: bandes de fenomen i `EARTHSHINE_S = 8.0` són
  transferències a Medina; parametritzar per altura del Sol i afegir les
  finestres de retenció per canal.
- `report_run.py`: llegir els CR3 de la targeta d'un cos card_only i
  aparellar-los amb `mission_events.jsonl`; mesura automàtica del rellotge.
- Generador del dibuix de dos panells (norma de Pere: pintar abans de
  discutir), amb els quatre números i normalitzat a f/2,8 ISO 100.
- Checklists físiques: cap perfil diu flats del dia, targeta formatada ni
  filtre sense contacte; canviar-ho canvia el SHA i obliga a un build.
- Marge de C3 dels Sony: amb 271 s hi ha lloc per a +2,5 s en lloc de +1,45.

### 6.5 Què s'hauria de pintar, amb quins números d'entrada

Totalitat 268-282 s; Sol a 38°; extinció ~×1,8; sostres 33 i 27; drenatge
0,573 s/imatge i 33 → 0 en 18,3 s; àncora de 8 s 11,21 s d'acció i 12,0 de
cadència; canvi de base 5,3 s; tríada 1/4 pressupostada a 5,0 s sense mesura;
R6 a 0,65 s entre fotogrames, 0,35 s de guarda, els llargs paguen 2,20 s més.
SUPOSAT: una passada monòtona de la R6 de 1/3200 a 1 s costa ~12 s, ~28 s amb
2 s i 10,3 s; a 271 s hi caben 8-10 passades, que és l'ordre de Brno. Això és
el que el dibuix ha d'ensenyar, no el que afirmo.

### 6.6 Banc abans del 2027

1. Tardor 2026: tríada 1/4 com a distribució i dispersió del canvi de base
   (perfils `lab_a7r3a_*` existents).
2. Tardor 2026: sostre de cua i drenatge dins de totalitat a 271 s als dos
   Sony (`lab_a7r3a_sostre_cua_48.json`, `lab_a7m3_sostre_cua.json`).
3. Tardor 2026: filtrat del RAW de l'A7RIIIA a 2, 4, 6 i 8 s.
4. Hivern: rellotge de la R6 per EXIF dels CR3 contra pulsacions conegudes;
   run de més d'una hora amb el cable i el cos per reproduir el −52.
5. Primavera 2027: gate A/B/C de la doble targeta, només si Pere l'autoritza.
6. Juny-juliol 2027: run sencer de la flota a 271 s amb la calor real; porta i
   bundle qualificats abans.

---

## 7. Esperança 3: la web d'ubicacions i meteorologia

### 7.1 Balanç del 2026

- La web viu a `~/Desktop/Altres/Eclipse meteo/Eclipse meteo/` (la memòria
  deia una altra ruta; corregida avui).
- **El cel el va encertar**: al FINAL 2 el cache de les 17:12 UTC dona ECMWF,
  ICON i GFS al 100 % de membres sota el 30 % de núvol; les capes de les 18 UTC
  0/0/0. La durada predita 103,8 s contra 103,7 mesurats.
- **El veredicte va sortir JUST, no NET** (MATISAT): a la falca de 25 km l'UKMO
  (18 membres) dona 14 de 18 ≤ 30 % (78 %), mediana 11,0 tal com la calcula el
  codi, i el punt falla tres criteris alhora (minP30 78 < 85, mediana 11 > 10,
  rang 22 > 20). `PROTOCOL_METEO.md:368-370` diu que <15 punts és el mateix
  número i <30 no és desacord (CONFIRMAT): la regla del codi és més estricta
  que el terra del protocol. Ho ha de decidir Pere.
- **El llindar «net» de R (55) era inabastable**: màxim 47,5 sobre 45 punts. El
  2027 està recalibrat a 40/25.
- **El que la web no mesurava i va manar**: la transparència que cau un 8 % en
  100 s (irreductible des de la web: requisit 3 del §1 quater); l'extinció i el
  groc atmosfèric (la web treballa en magnituds a 550 nm i no publica cap
  vector per canal); el vent (cap variable de vent al codi); aerosol CAMS i
  cirrus EUMETSAT tenien clau al Clauer i script, i no consta cap ús el dia 12.

### 7.2 Estat del 2027

Fet: motor Skyfield + DE421 validat; Zahara 270,2 s (C1 07:40:50, C2
08:45:00, C3 08:49:30, C4 10:00:21 UTC); climatologia ERA5; accés OSRM als 20
punts; escala de R refeta; cadena provada el 24-08 en mode proves.

Mort o no calibrat (tot CONFIRMAT llevat que es digui): `MODE_PROVES = True` i
`DIES = [demà]` (`fes_web_local.py:49-52`); el bloc AEMET busca «Eclipse del
12 de agosto» i l'IGN apunta al 2026 (l.372, 382); `nuvols_aemet.py` llegeix
`FINAL2026.kmz`, que no existeix; `mobilitat_punts.json` i `cota_casella.json`
no s'han generat, tot i pesar 0,15 i 0,46 a R; la llegenda diu 90 s, 9°, 25 km
i 18:30; el mode satèl·lit té 'MIRADOR FINAL 2' com a punt; l'azimut de la
falca es calcula a les 08:30 (100,1°) i C2 és a 95,1°; els noms del KMZ porten
una puntuació disfressada de durada («Los Reales — 4m23s» quan la durada és
206,2 s); cap variable de vent, humitat ni estratus marí; cap protocol de
portes; cap alerta; cap regeneració programada; la carpeta no té git; el
repositori meteo del 2026 té 34 entrades sense commitar des del 08-08.

### 7.3 Millores, per valor

**Dades**: vent a 10 m i ràfegues, humitat i punt de rosada (mateixa crida
d'Open-Meteo); estratus marí per HARMONIE-AROME de l'AEMET amb la clau del
Clauer; aerosol CAMS directe amb `cams.py` adaptat; cirrus OCA només si es
decideix baixar-lo a les portes; **vector d'extinció previst per punt i hora**
(X, AOD, k, R/G, B/G) en JSON per a la cadena de postprocessat.

**Portes per a un eclipsi a les 08:45 UTC** (les del 2026 eren per a les 18:30
i no serveixen): T−7 climatologia i deriva dels conjunts, només llegir; T−2
vespre, decisió de base (Zahara, Marbella, Granada) amb l'ECMWF 12z i el
pitjor centre; T−1 18:00 UTC, llista curta de miradors a <60 min i sortida
límit; matí T−3 h (05:45 UTC), passada 00z més satèl·lit infraroig, mana
l'observació, go/no-go.

**Automatització**: `--dia` als dos scripts i `MODE_PROVES` fora; launchd cada
6 h des del 15-07-2027 amb registre i SHA del cache; arxiu diari dels cinc
conjunts; alerta quan canvia el guanyador o el veredicte de la base; QA de la
pàgina que falla si troba «12 de agosto», «18:30», «90 s», «25 km»; un botó
«on vaig demà».

**Integració amb la captura**: exportar C1-C4 per punt en JSON UTC perquè
Eclipse Command els llegeixi; altura del Sol i X per punt cap a les bandes de
fenomen; contrastar el KMZ del 2027 per quatre vies amb les eines de
`Eclipse meteo/eines/` (no copiades al 2027) abans d'entrar res a l'app.

**Esforç total**: quatre o cinc dies abans del juny del 2027, més les proves
del juliol quan els conjunts arribin (fins cap al 17-07-2027 cap conjunt no
arriba al 2 d'agost).

---

## 8. Esperança 4: automatitzar el postprocessat

### 8.1 D'on partim

Quatre generacions d'eines i només una cadena de cap a cap:
`eclipse_determinista/cadena.py`, un sol punt d'entrada amb manifest i codi
congelat; `--reusa` falla tancat si canvien `comu.py`, `f0-f2.py` o
`flat_dither_SONY.json` (i es pot forçar amb `--igualment`, que ho deixa
escrit). Tot el que s'ha fet del 27-08 al 02-09 és **fora** de la cadena:
`capes_totals_v14/` (85 scripts, 47 amb rutes absolutes, cap prova). Hi viuen
les peces bones que la cadena no té: ρ (`fes_v18.py`), fons per raig
(`operador_prototip.py`), earthshine V4, estrelles amb control nul, porta
Photoshop. Les portes amb proves són al pilot (`portes.py`, 100 proves); la
cadena en té **zero** (CONFIRMAT). `cadena.py` no crida ni `porta_photoshop.sh`,
ni `jutge_creuat`, ni `mapa_carpetes` (CONFIRMAT). Lloc, dia, ofset i
efemèride són escrits a mà a `comu.py:162-165` (CONFIRMAT), i `de421.bsp` és
una ruta absoluta a l'arrel del repositori, sense seguir a git.

### 8.2 El pipeline desatès del 2027, per fases

| Fase | Entrada → sortida | Portes | Eina i estat | Esforç | Decisió humana |
|---|---|---|---|---|---|
| F0 calibració | RAW per rol + `tren_<COS>.json` → pedestal, darks, flat | F0.1, F0.3 | `f0.py`, amb paràmetres; afegir darks per temperatura i exposició física | 1 dia | cap |
| F1 registre | `eclipsi_<ANY>.json` → limbe, Sol per efemèride, llenç comú | F1.2 | `f1.py` un cop les constants surtin de `comu.py` | mig dia | cap |
| F2 LDIC | una suma, màscara lunar per fotograma, coherència, cel pel color | F2.2, F2.4 | `f2.py` tal qual; afegir VAR per canal, drizzle, meitats A/B | 2-3 dies | cap |
| F3 filtres | base amb corba, mediana de canals, `suavitza_sn`, anivella | tancament ≤5 %, brillantor ≤8 %, H1, H1b | `f3.py` + `filtres_druckmuller.py` (WOW, NAFE, FNRGF no integrats) | | **la corba** |
| F5 earthshine i estrelles (nova) | àncores dels dos trens, LROC, catàleg → pila lunar, capa, llista | injecció 0,90-1,10, vara única, control nul | `v21_*` d'un sol ús: treure caus i rutes | 3-4 dies | realç de display |
| F6 fusió dels dos trens (nova) | dos runs al mateix llenç → compost, ρ, fons per raig | bony per marca i sector, croma, estrelles | `fes_v18.py`, `operador_prototip.py` d'un sol ús | 4-5 dies | **radi de detall** (JSON) |
| F7 jutge i lliurament (nova) | H4 entre trens, `es_corona.py`, `porta_photoshop.sh` amb OBRE al rebut | | existeixen, cap cridada | 1-2 dies | cap |
| F4 PSB + tries | `f4.py`, `ajust.py`; `tries.json` (retall, to del disc, reflex, capes visibles, format Sony) | cap capa verda; OBRE | | mig dia | totes les de Pere, aïllades |

### 8.3 Portabilitat i captura

Codi: treure de `comu.py` el lloc, dia, ofset, efemèride, `TRENS`, `LLENC_COMU`
i `CORBA` cap a `eclipsi_<ANY>.json` i `tren_<COS>.json`, afegits a `SCRIPTS`
de `cadena.py` perquè quedin al manifest (el patró ja existeix amb
`flat_dither_SONY.json`); `de421.bsp` a la cau de skyfield; fora el `sys.path`
absolut de `f4.py:21`; rols dels fotogrames d'un manifest de captura i no
d'heurístiques d'EXIF (al run del 12-08 la Sony té 156 `capt_*` lligats a
accions i la R6 cap).

Captura, perquè el pipeline sigui més senzill: (1) Eclipse Command escriu per
canal un `frames_manifest.json` (`action_id`, `phase`, `target_utc`,
`expected_shutter`) i el postflight aparella els CR3 per EXIF i mesura el
rellotge; (2) flats del dia als dos trens; (3) darks a la temperatura de
treball just després de C4; (4) escala monòtona i monitor de transparència;
(5) exposició física al run; (6) no moure la lent en treure el filtre.

### 8.4 Ordre d'integració i criteri de «fet»

Regla única: **cap fase nova toca res del 2027 fins que reprodueix el 2026 amb
la mateixa vara** (portes i números iguals als rebuts del 019, del 016 i de
`cau_v21/earthshine4_rebut.json`).

1. Commit del text i `.gitignore` (`output/`, `cau_*`, `*.npy`, `*.psb`,
   `*.tif`, `/de421.bsp`); `mapa_carpetes.py` al final de cada run (el mapa diu
   017 vigent i al disc hi ha 018 i 019). 1 h.
2. Configuració externa i efemèride a la cau. Fet: un `--reusa` del 019 dona
   els mateixos SHA de sortida (cal una eina de comparació de rebuts, que no
   existeix). 1 dia.
3. Proves: les 100 del pilot a un mòdul comú, més determinisme amb entrades
   sintètiques. 2-3 dies.
4. F0/F2 amb exposició física, darks per temperatura, VAR. 2 dies.
5. F7 dins de `cadena.py`. 1-2 dies.
6. F6 fusió (ja planificada al `research/123` §7, no executada). Fet: bony
   ≤ 0,0024 a la zona de dada i 16/17 marques a 0,000 sobre el 2026. 4-5 dies.
7. F5 earthshine i estrelles. Fet: r +0,885, injecció 0,957, puresa 95,8 %.
   3-4 dies.
8. Drizzle i meitats A/B, amb porta d'injecció.

Contracte de tot rebut: paràmetres efectius, procedència per número, SHA de
codi i entrades, veredicte literal de cada porta amb llindar, R/G i B/G per
zona, taula amb la mateixa vara contra totes les versions anteriors,
transferència d'injecció a les cadenes de senyal feble, vistes al llenç sencer.

---

## 9. Les skills: què s'ha fet avui

Diagnòstic: els dos `SKILL.md` eren una foto del 21 i 22-08. El de
postprocessat descrivia el «protocol v3» de revelat de DNG cap a 1/15 s i el
muntatge per capes de CapesTotalsV4, abandonats el 23-08 amb D1 i D2; el
d'apilatge manava «un màster per banda, no fusionis», que és el contrari de la
suma única de la cadena, i el seu orquestrador `pipeline_vixen.sh` és la
cadena del 17-08 amb R☉ 959″. Cap dels dos deia LDIC, `cadena.py`, jutge
extern, norma zero, control nul, injecció, vara única, porta Photoshop, fons
per raig, mediana de canals ni RGGB. I nou normes de Pere vivien només a la
memòria de Claude, invisibles per a Codex o un Claude nou.

Fet avui, sota el bloqueig d'escriptura, amb els esborranys de la síntesi
revisats per mi (les rutes citades comprovades una a una; els revisors
adversaris no van córrer):

- `.claude/skills/postprocessat-corona/SKILL.md` reescrit des del punt
  d'entrada `cadena.py`: arrels, 25 normes en una línia, fases i portes,
  què viu fora de la cadena, producte i to, rebut, història.
- `references/normes_i_portes.md` (nou): normes declarades de Pere amb data
  i literal, regles de mètode mesurades, taula de portes.
- `references/trampes_INDEX.md` (nou): índex per fase de `trampes.md` (1.902
  línies), que no es toca.
- `.claude/skills/apilatge-imatges-eclipsi/SKILL.md` reduït a redireccionament:
  fases 0-2 = `cadena.py`; `pipeline_vixen.sh` històric; soroll i denoise
  com a proposta, tal com Pere va ordenar el 21-08.
- `scripts/comprova_entorn.py` copiat a la skill de postprocessat (la carpeta
  era buida i dues eines d'astrometria hi apuntaven).
- Còpia de Codex a `~/.codex/skills/` sincronitzada (llegia un `trampes.md`
  de 449 línies) i `IA/Skills/README.md` amb els SHA nous.

Els `SKILL.md` anteriors queden a git (`git show HEAD:...`) i no s'han
esborrat d'enlloc més. Pendent i seu: `constants.md` amb data i font per fila,
i la decisió de la corba.

---

## 10. Dades i risc: la còpia és el primer pas de qualsevol pla

⏭️ **Fet el mateix dia a la tarda** (rebut: `output/cleanup/20260902_neteja/REBUT.md`): còpia verificada al 4TB de tot l'insubstituïble posterior al 22-08 (229 GB, 15/15 PSB amb SHA igual), tres lots reversibles a la Paperera (256 GB) i `.gitignore`. ⛔ **Rectificació**: els 173 GiB del `.git` no són un `git add` avortat sinó nou `refs/codex/turn-diffs/checkpoints/*` de Codex (23-08) que instantanien tot l'arbre; cap branca els conté. La cura (`update-ref -d` + `gc`) és irreversible i queda pendent de Pere.

- `/Volumes` només conté Macintosh HD; `tmutil destinationinfo` diu «No
  destinations configured». El 4TB no s'ha muntat des del 22-08. Tot el produït
  des de llavors (cadena determinista ~350 GB, Projecte photoshop, Derivats,
  màsters S6, research/97-129, el run canònic, els STATUS, la memòria) és en
  un sol disc.
- El `.git` porta ~156 GiB d'objectes solts i 17 GiB de brossa que no són a
  cap commit (`git count-objects -vH`); l'últim commit és del 23-08 i
  `output/` (449 GB) no és al `.gitignore`. Un `git clean` s'ho enduria tot.
- Dins del worktree hi ha 26 GB (`capes_totals_v14`) i 12 GB (`corretgint2`)
  de caus sense seguir.
- Gates de procedència oberts: cua Vixen 3152-3177 absent; R6 amb 247 CR3 per
  238 esperats (i sis 572A3170-3175 de 15 s a ISO 6400 a les 23:41 que semblen
  proves nocturnes); 6D sense inventari; `BACKUP.psb` (3,98 GB, 28-08) i
  `CapesTotalsV20.psb` sense cap nota.

Ordre proposat, i és el que mana abans de cap filtre nou: (1) muntar un disc i
copiar-ho tot amb hashes (Pere; cap agent hi pot accedir); (2) `.gitignore` i
commit del text; (3) amb autorització, `git gc --prune=now` (irreversible
sobre objectes que no són a cap commit); (4) política de retenció dels runs
vells de la cadena i dels PSB supersedits, en lots reversibles a la Paperera.

---

## 11. Coordinació i higiene

- `IA/ESTAT_ACTUAL.md` (23-08) i `ACTIVE.json` (25-08) diuen «pilot bloquejat»
  i «earthshine fora d'abast»: fals des del `research/99` i del `126`.
- El bloc de represa de CLAUDE.md creix un paràgraf llarg per dia; té dues
  seccions «1 bis» i la capçalera diu «22 d'agost» amb contingut del 31.
- Els traspassos formals de `.coordination/` s'aturen el 25-08; des de llavors
  27 rondes seguides de Claude sense Codex.
- El mapa de carpetes de la cadena diu 017 vigent i al disc hi ha 018 i 019.
- Rutina de tancament de sessió proposada: `date` del Mac a cada bloc; una
  línia a `normes_i_portes.md` per cada norma nova de Pere el mateix dia; una
  entrada a `trampes_INDEX.md` per cada trampa; `mapa_carpetes.py`; el rebut
  sempre **després** del save; i el bloc de CLAUDE.md §1 reduït a ≤25 línies
  d'estat més una taula de sessions.

---

## 12. Honestedat

**El que hem fet malament els agents**: lliurar versions pitjors sense
comparar-les amb la mateixa vara; batejar Aristarc una mota de pols sense
efemèride; dissenyar la V19 sense escriure-la; enverinar la referència a la
vora del mosaic; escriure PSB que Photoshop refusava i validar-los amb el
mateix lector que els havia escrit; menjar-nos el sufix `_coh`; sobreescriure
la V21; declarar una costura a «60σ» sense control; concloure que les maria no
hi eren amb el segon apuntament barrejat; mantenir quatre fitxers d'autoritat
aturats deu dies mentre el mètode canviava tres vegades; i avui, gastar el
21 % del pressupost setmanal en una sola auditoria.

**El que Pere ha resolt a mà i nosaltres no vèiem**: el desenfoc radial zoom
com a cura estructural dels halos (després, el fons per raig); la corba de to
de la maqueta del 21-08, que ja arreglava el rentat de la Lluna; les perles i
el contorn de la V23 contra el limbe; el Camera Raw de la capa Sony, ara
format canònic; els retocs enters de la V13; i totes les rondes de marques de
defectes, l'única manera de trobar els halos, els arcs i els guionets que cap
porta veia (`research/128` §8).

---

## 13. Preguntes a Pere (les que bloquegen)

1. **Corba de to**: 0,17/0,68 (la teva maqueta fa 0,166; `research/108`) o
   0,22/0,74/0,045 (la cadena, `comu.py:573`)? Sense això el compost lineal no
   es tanca.
2. **Còpia física**: pots muntar el 4TB o un disc nou? Cap agent hi pot accedir
   i avui tot viu en un sol disc.
3. **Git**: autoritzes el `.gitignore`, el commit del text (skills, research,
   CLAUDE.md, cadena determinista) i, després de la còpia, el `git gc`?
4. **El pla invertit**: acceptes que el lineal es compongui a la graella de la
   teva V23 i que les teves capes s'hi posin a sobre byte a byte, en lloc de
   linealitzar el PSB, que no és possible?
5. **Prova A/B dels halos**: pots exportar la V24e en dos TIFF de 16 bits, amb
   i sense Claridad i Borrar neblina, i dir-ne els valors?
6. **Escala 2027**: vols que es pintin les tres variants (monòtona amunt-avall;
   partida entre A7RIIIA i A7III; monòtona només a la R6) abans de decidir? I
   el sostre de cua: drenar dins la totalitat, doble targeta o partir l'escala?
7. **6D i A7III**: dins d'Eclipse Command el 2027 o fora amb protocol propi?
8. **Banc de tardor**: autoritzes els runs (tríada 1/4, canvi de base, sostre a
   271 s, filtrat a 2-8 s, rellotge R6, run llarg per al −52)?
9. **Web**: regla NET (un centre de 18 membres pot vetar sol?), portes del 2027
   i launchd cada 6 h?
10. **Fitxers**: `BACKUP.psb` i `CapesTotalsV20.psb`, conservar o brossa? Els
    572A3170-3175 són proves teves? La CFexpress conserva els 3152-3169?
11. **Codex** torna a l'alternança, o seguim només amb Claude i ho deixem
    escrit?

---

## 14. Cobertura i límits d'aquesta auditoria

| Síntesi | Afirmacions verificades | Recomanacions jutjades | Esborranys revisats |
|---|---:|---:|---:|
| S0 estat i balanç | 10 (7 CONFIRMADES, 1 MATISADA, 2 no acabades) | 5 | — |
| S1 més detall | 10 (5 CONFIRMADES, 5 MATISADES) | 4 | — |
| S2 Eclipse Command | 3 (1 CONFIRMADA, 2 MATISADES) | 0 | — |
| S3 web meteo | 10 (7 CONFIRMADES, 3 MATISADES) | 1 | — |
| S4 automatització | 10 (7 CONFIRMADES, 3 MATISADES) | 7 | — |
| S5 skills | 0 | 0 | 0 (revisat per mi) |

Cap afirmació verificada va sortir REFUTADA; les MATISADES estan incorporades
al text amb la correcció. Les afirmacions de prioritat mitjana i baixa no es
van verificar. El crític de completesa no va córrer: el que falta per llegir
no està enumerat per cap agent. Els números de §6 (2027) i §7 (web) surten
dels lectors i de les síntesis, amb només 13 verificacions entre les dues.
Els deu mapes dels lectors (433 KB) no s'han incorporat sencers a aquest
document; el que hi ha aquí és el que les síntesis en van treure.
