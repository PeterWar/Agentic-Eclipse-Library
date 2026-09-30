# Normes de Pere i portes de la cadena

Estat: 05-09-2026. Aquest fitxer es llegeix sencer abans de tocar cap
producte. Cada norma porta data, literal quan n'hi ha, i on viu al codi.
Les trampes concretes són a `trampes.md` (índex a `trampes_INDEX.md`).

## A. Normes DECLARADES per Pere

| data | norma | literal o font | on viu |
|---|---|---|---|
| 06-08 | Avança sol i informa una vegada; para només per destructiu, físic o disseny del lliurable | «em pares massa sovint per preguntar i això resta eficiència» | memòria avanca-sol |
| 06-08 | Parla planer, sense anglicismes; sense manuals ni documentació d'operador | memòries parla-planer, sense-manuals | |
| 19-08 | Disc lunar, earthshine i limbe de presentació només de l'instant d'ancoratge (C2 − 0,5 s); això no retalla la corona vàlida descoberta en altres instants | memòria lluna-nomes-de-linstant-dancoratge; precisió de suport temporal 05-09 | `f2.mascara_lluna` |
| 21-08 | Soroll i denoise: recerca futura, no ara | «PER FUTURS PROJECTES D'ECLIPSE SI QUE VAL LA PENA... ARA NO ES EL MOMENT» research/87:346 | skill d'apilatge com a PROPOSTA |
| 23-08 | Norma del rectangle | «El filtre ha d'aplicar a TOT el rectangle de la imatge, no només a una circumferència, sinó quedaran HALOS» | trampes.md:332; `filtres_druckmuller.py`; `f3.py` |
| 05-09 | Les retallades circulars probablement fan més mal que bé: eliminen detall de corona i poden crear halos | Precaució expressa de Pere; desenvolupada a «Retallades circulars» més avall | contracte de postprocessat i skill `corregeix-artefactes` |
| 23-08 | D1: via de la FOTO amb els dos trens; el fusionat NO és una mesura. D2: pilot des de zero amb la Vixen | research/97 §1 | tota la cadena |
| 24-08 | Vistes de diagnòstic a cada etapa | «a cada etapa, fase o bloc rellevant que facis, genera imatges si és possible, que seguiré buscant artefactes» | `vistes.py`, `vistes_diagnostic.py` |
| 26-08 | RGGB a cada resultat (error recurrent) | R/G i B/G d'una zona coneguda al rebut; balanç de dia R 2,1678 · B 1,3555 a cada producte des dels RAW | `comu.calibra_pla`, `comu.mesura_color`, porta «cap capa verda» |
| 26-08 | Llenç sencer, mai retalls | «MAI li ensenyis només el retall» | `vistes.py` docstring |
| 26-08 | Tot el que Pere ha de veure va a Output | `comu.Run.vista()` i `comu.Run.lliurable()`; cap ruta de sortida a mà | `comu.py:311-315` |
| 26-08 | La corba de to és un paràmetre declarat, mai d'un percentil; el sostre és el màxim de la dada | research/108 §3 i §7 | `comu.CORBA` (comu.py:573) |
| 27-08 | Mode de color CIENCIA; MEMORIA deprecat | «depreca el mode de color MEMORIA, seguim amb ciència» | `cadena.py`, `2-OUTPUT/LLEGEIX-ME.md` |
| 27-08 | Només C2 | «oblidem-nos del requisit de fer la simetria amb els dos contactes, treballarem només en C2» | `comu.CONTACTES_AL_PRODUCTE` (comu.py:160) |
| 27-08 | El fons dels filtres no pot ser estàtica: la resolució segueix el S/N | «tots els filtres tenen encara un fons molt sorollós» | `f3.suavitza_sn` t = 0,18 |
| 27-08 | Brno és jutge, no font | pregunta «què passa si ells cometen errors? els propaguem?» | `comu.PROCEDENCIA`, `es_corona.py` |
| 27-08 | Cada foto compta: DSC06991 i 06993 tornen a entrar | «pensa que cada foto compta» | `comu.TRENS["SONYTOT"]` |
| 28-08 | Format canònic de la capa Sony | «aquest és el format que vull que guardis com a canònicament bo» | `FORMAT_CANONIC_SONY_PERE.json` |
| 25-08 | El requisit del protocol 2027 està acceptat; la solució (escala monòtona amunt-avall) no està decidida | CLAUDE.md §1 quater, reserva de Pere | recordatori actiu per a la tardor 2026 |

### Retallades circulars: precaució prioritària (05-09-2026)

**Probablement les retallades circulars fan més mal que bé:** poden esborrar
detall real de corona i introduir halos o anells. És el criteri de precaució
de Pere, no una demostració que tota operació radial sigui perjudicial.
Una ploma suavitza la frontera però no garanteix preservar el senyal ni
evitar l'halo; declarar el radi al rebut tampoc no valida la correcció.

- No prescriguis per defecte discs a zero o a gris neutre, forats lunars
  engrandits, pedaços circulars ni esvaïments del detall cap a zero a un radi
  fix. Les receptes històriques de 3,5→5, 5→6,5 o 5→7 R☉ no són normes
  generals: el radi, l'aspecte net o la millora d'un detector no demostren
  absència de corona. Ajusta la resolució segons el senyal i el soroll
  mesurats per escala i zona, sense amputar tot un anell.
- Distingeix el retall de la **validesa física per fotograma**: ocultació
  lunar real, saturació, defectes mesurats i cobertura del sensor. A la
  corona, compon la unió temporal de les observacions vàlides; un píxel
  ocult en una foto pot tenir dada en una altra. La zona sempre ocultada
  queda exclosa; no facis la unió dels discs ocultats per engrandir el forat
  del compost. El disc lunar i l'earthshine conserven el seu ancoratge C2.
- Tracta les vores segons la cobertura real i el suport del nucli del
  filtre, sense inventar radiància ni convertir una vora en un tall circular.
  Les ponderacions HDR basades en validesa radiomètrica poden variar amb el
  radi, però no han d'esborrar dada vàlida del compost. Els perfils per
  anells, el càlcul polar i la correlació circular azimutal són eines de
  càlcul o diagnòstic; no autoritzen a retallar el camp. Un llindar de pes
  com el 2 % és un criteri de qualitat, no la definició de cobertura física;
  cap porta d'independència azimutal no exigeix circularitzar aquesta cobertura.
- Davant d'un halo, resol la causa a la geometria, calibració, cobertura,
  fusió o filtre. Abans d'acceptar una atenuació circular excepcional,
  justifica-la amb dades i comprova què elimina: comparació abans/després i
  diferència al llenç sencer i a 1:1, incloent limbe i sectors exteriors,
  jutge independent i transferència de detall a les bandes afectades
  (porta d'injecció 0,90–1,10 quan correspon). Cap millora del detector
  compensa pèrdua de corona o un halo nou. Si no queda validada, es conserva
  la versió anterior i es registra el deute; no es tapa la zona.

## B. Regles de mètode MESURADES (cada una amb el dia que va costar)

| data | regla | número que la sosté | eina |
|---|---|---|---|
| 24-08 | NORMA ZERO: cap correcció d'artefacte sense el jutge extern (l'altre tren) | passades globals 0,894 → 0,952 (bones); resta per sector 0,930 → 0,849 amb el seu propi número ×8 millor | `jutge_creuat.py`, porta H4 |
| 25-08 | Una coincidència de posició no és una causa: mou el paràmetre | amb el sostre 0,85 → 0,60 cap corba visible no es mou | `mesura_fronteres.py --sostre` |
| 25-08 | Un rebut sense paràmetres no és un rebut | sis sortides amb sostres diferents tenien JSON indistingibles | `desa()` estampa els PILOT_* |
| 27-08 | Una màscara nova va a TOTS els llocs que comparen; una sola funció | k fins a 206, dispersió 2488 % amb la màscara només a `compon` | `f2.mascara_lluna`; porta F2.2 |
| 27-08 | La vara del pes és el que és assolible al mateix radi, no el màxim global | el màxim global era dins de la Lluna | `comu.mascara_dada` |
| 27-08 | Tota correcció per calaixos s'aplica interpolada | potència ×937 → ×1,97 al passa-alt | `f3.perfil_azimutal`, H1b |
| 27-08 | Un lliurable escrit no està verificat fins que un altre lector l'obre; fusionada mai en ZIP | matriu 2 formats × 4 compressions | `comprova_obrible()` de `fes_v14.py` |
| 27-08 | Jutja cada capa on viu | R/G 0,048 a 5 R☉ en una capa de contacte que hi té zero senyal | porta del color per capa |
| 27-08 | Un salt de muntura és un dither i mesura el flat | error del flat 7 a 9 % pel camp, meitats 0,04 a 0,54 % | `sony_entrada/flat_pel_salt.py` |
| 28-08 | L'acord entre trens no distingeix corona d'atmosfera local | línia r 2,52: Brno −0,3 a −1,7 % on una corona real faria −9 a −18 % | `es_corona.py` |
| 28-08 | `topil()` torna màscares de 16 bits a 8; cada canal editat es re-descodifica | 40,9 MB per 81,9 | `psb_utils.py` |
| 28-08 | PSB: fora els blocs globals heretats menys Lr16/Mt16; la porta és el Photoshop real | signatures 8B64 contra 8BIM | `porta_photoshop.sh` |
| 28-08 | Al camp exterior l'artefacte varia al llarg del raig i el senyal en azimut: fons per raig només en ln r, autoreferent | 16/17 marques a bony 0,0000; 2.097 de 2.102 estrelles recuperades | `operador_prototip.py` |
| 28-08 | Tota fosa per canal és un pinzell de color; la referència es qualifica per sector | viratge R/G 12 %/R☉; ρG fins a 1,165 a la vora | research/122 §2 |
| 29-08 | Un error de transport de la porta no és un veredicte | AppleEvent −1712 als 120 s | `with timeout of 3600 seconds` |
| 29-08 | Control nul aparellat per a tota llista per llindar | falsa alarma 2,8 % per posició; 15 de 18 eren gra; puresa 95,8 % | `v21_estrelles_purga.py` |
| 29-08 | El criteri creuat entre trens no tria el model de vel (part del vel és comuna) | research/126 §103-107 | `v21_earthshine_v4.py` |
| 30-08 | Vara única: tota versió es compara amb totes les anteriors mesurades igual | la capa del 29 feia 0,777 quan un fotograma sol fa 0,857 | taula research/127 §2 |
| 30-08 | Porta d'injecció cega 0,90 a 1,10; filtres per bandes en Fourier, mai DoG | el Wiener DoG menjava el 17 % | `v21_earthshine_v4.py` |
| 31-08 | Cap tret puntual sense posició predita; cap tret lunar si els dos trens no el veuen igual | mota a (3579, 2374): +33,4 Vixen contra +5,0 Sony | efemèride de421 |
| 31-08 | Flats del mateix dia o dither | correlació 0,00 de la mota amb els flats del 22-08 | checklist 2027 |
| 31-08 | El soroll d'un component mai només per diferències entre germans | r fina 0,44 a Δt 3 s, 0,03 a Δt 13 s | pesos de l'earthshine |
| 01-09 | El limbe fotogràfic amb llum asimètrica menteix; ancora al costat fosc o a un contacte real | 3,6 px de biaix al DSC06984 | research/128 §6 |
| 01-09 | El limbe de display es compon del fotograma sencer; les tessel·les de ciència no serveixen | guarda 8 px i sostre LDIC buiden el trànsit | `v24_perimetre_e.py` |
| 02-09 | Tota línia de base feta d'un apilat amb guarda s'estén llisa des de dins abans de restar | guionets a les vores de guarda desplaçades | research/128 §8 |

## C. Taula de portes

| porta | on | què mesura | llindar | què passa si falla |
|---|---|---|---|---|
| F0.1 | `f0.pedestal_i_blanc` | pedestal i saturació mesurats contra els declarats a `comu.TRENS` | ±1 / ±1,5 DN | atura |
| F0.3 | `f0.flat_radial` | desacord del flat amb els flats invertits (Vixen) o amb el dither (Sony) | ≤ 8 % | atura |
| F1.2 | `f1.contactes_i_offsets`, `cadena.py` | dos contactes trobats i fracció de fotogrames coronals | ≥ max(6, 15 %) | atura |
| F2.2 | `f2.coherencia` | guany de coherència per fotograma | dins de [1/2, 2] | atura i diu quins |
| F2.4 | `f2.cel_per_color` | residu del control de la separació cel/corona pel color | ≤ 3 % | atura |
| tancament HDR | `comu.tancament_hdr` | compost contra un fotograma solt repartit en el temps, per color | ≤ 5 % | atura |
| brillantor | `comu.tancament_hdr_brillantor` | el mateix, per brillantor, amb dispersió | ≤ 8 % | atura |
| croma | `f3.filtres` | p1 a p99 de R − G de la base | ≥ 0,02 | atura (monocroma) |
| H1 | `f3.filtres` | max |nivell de l'anell − 0,5| als filtres 0,5-neutres | ≤ 0,05 | atura |
| H1b | `f3.anells_de_calaix` | potència a la freqüència dels calaixos contra veïnes | < 2 | avisa |
| cap capa verda | `f4.py` | R/G i B/G de cada capa on la capa té senyal | plausibles | atura |
| mascara_dada | `comu.mascara_dada` | qualitat del pes contra l'assolible al mateix radi; no defineix la cobertura física | 2 % | vara |
| E, E2, F, G, rectangle | `pilot_vixen_claude/portes.py` | monotonia, graons de fusió, mescla, envolupant i frontera de la dada; sense imposar simetria circular a la cobertura física | vegeu docstrings; 100 proves | |
| H2 | `portes.porta_h_costures` | costures per nivell | deute: refer amb control aparellat pel sostre (research/102 §5.3) | |
| H3 | `portes.porta_h_esglaons_px` | desacord entre esglaons píxel a píxel | | |
| H4 | `portes.porta_h4_jutge_creuat`, `jutge_creuat.py` | correlació amb l'altre tren puja o baixa | puja = PASS | refusa la correcció |
| control nul | `v21_estrelles_purga.py` | puresa d'una llista per llindar amb posicions girades | el tall el tria el control | no es lliura |
| injecció cega | `v21_earthshine_v4.py` | transferència de textura sintètica a la banda del senyal | 0,90 a 1,10 | no es lliura |
| és corona | `auditoria_estructura/es_corona.py` | dos trens + nul honest + observador d'un altre lloc | tres columnes | INDECÍS o NO ÉS CORONA |
| Photoshop | `capes_totals_v14/porta_photoshop.sh` | el Photoshop real obre el fitxer | literal OBRE | no es lliura |
| dos lectors | `comprova_obrible()` a `fes_v14.py` | psd-tools i `sips -g pixelWidth` | cap nil | no es lliura |

Una porta que no pot fallar no és una porta: cada porta nova porta una prova
amb entrada dolenta coneguda (model: `pilot_vixen_claude/test_portes.py`).
Un número al rebut sense porta és documentació, no control.


## Prova azimutal d'alineació (05-09-2026, research/132)

Tota geometria entre llenços (cadena → graella de Pere, tren ↔ tren) passa la
**correlació circular en azimut** del perfil polar en ln (r × θ, mitjana per
anell restada) entre la capa nova i una capa de referència: pic a **0 ± 0,5°** i
**control nul** (referència girada 180°: la correlació a 0° ha de caure). Les
finestres de correlació de fase i els escaquers **no són prova d'alineació**:
el gradient radial, els raigs, els anells HDR i el forat lunar són invariants a
la rotació, i amb ells la V25/V26 van sortir girades 138,5° amb «1,5 px» de
residu. El centre solar és el de l'efemèride; la geometria lunar de cada
fotograma i el disc C2 es contrasten separadament. El forat de la unió
temporal no és el disc C2 ni fixa el centre solar. L'escala es declara
(1,0 quan la de píxel és la mateixa).
