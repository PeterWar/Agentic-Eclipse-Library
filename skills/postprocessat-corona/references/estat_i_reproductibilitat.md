# Estat, reconstrucció i neteja — 16-09-2026

## 16-09 (tarda): reorientació de Pere i neteja profunda

Pere: «no és essencial disposar dels scripts de Python; l'essencial és la neteja profunda per
alliberar espai sense perdre aprenentatges». La reconstrucció determinista RAW→PSB queda SUSPESA.
Els replays exactes fets (F0 → filtres V58) queden com a rebuts `raw_replay/SUMMARY_*.json`; les
seves rondes s'han retirat com a duplicats exactes. Cinc lots a `~/.Trash/Eclipse_neteja_20260916/`
(1,5 TiB lògics): duplicats per SHA-256, pipelines d'agost, carpetes de treball de setembre,
caches de 3-RECERCA/tools, PSB supersedits del Desktop i Derivats. Manifests, restauració i rebuts:
`2-ARXIU/reconstruccio_compactacio_20260915/neteja_20260916/`. Es conserven RAW, calibradors,
V69 (de Pere, tal qual), V68, V56, CapesTotalsV13_Pere, l'arxiu PSB de Codex, rebuts, notes, codi i
vistes. Encàrrec posterior del mateix dia: retirats també els 176 RAW duplicats interns i la carpeta `Desktop/Eclipse
determinista` sencera (runs 019/016; documents a `neteja_20260916/eclipse_determinista_docs/`).
La secció següent i la resta del document són història vigent fins al 16-09 al matí.

## Estat previ — 15-09-2026

## Autoritat i abast

Resol sempre els fitxers vius amb `IA/ACTIVE.json`.
Pere ha confirmat V68 general i Earthshine V56 independent com a referències
definitives. Preserva les decisions manuals; no reapliquis matrius a V67/V68.
La taca ampla V68 continua sense correcció validada. No reprendre la prova
d'ales estel·lars pausada per manca del contrast Claude Fable 5.1 xHigh.

Arrels: (arrel) = codi; (arrel) = fotografia;
2-ARXIU/reconstruccio_compactacio_20260915/neteja_20260916/eclipse_determinista_docs = entrades/runs. Sense Git; SERIAL_WRITES retirat el 30-09-2026 (AGENTS §5).
L'auditoria és a `2-ARXIU/auditoria_reproductibilitat_20260915/README.md`.
L'autorització de neteja del 15-09 abasta aquestes tres arrels, no el 4TB.
No és una autorització permanent per buidar la Paperera o netejar altres tasques.

## Què vol dir determinista

Declara punt d'inici, hashes, paràmetres, codi, dependències, precisió/fils i
abast de comparació. Dues execucions en carpetes/processos nous han de comparar
els píxels, màscares i geometries pertinents. Separa bytes del PSB i píxels.
No anomenis RAW→PSB una còpia del final o un replay que llegeix arrays desats.
Cap import exploratori de mòduls històrics amb `mkdir`, publicació o claims.
Les sortides s'han de crear exclusivament en una carpeta nova, sense `-O`.

Prova del 15-09: V56 R5→R8 i V68 B4/B10 coincideixen en dues execucions
noves. Els canals finals també coincideixen: V68 requereix reproduir la
quantització Adobe `rint(rint(x*32768/65535)*65535/32768)`; abans d'aquesta
conversió hi ha fins a 1 DN16, ja previst al D6 original. No és un nou llindar.
El runner i els rebuts són a `2-ARXIU/auditoria_reproductibilitat_20260915/replay/`.
**Aquesta prova no reconstrueix RAW, màsters, R4/B9, Camera Raw, capes heretades
ni el contenidor PSB complet.** Photoshop OBRE/readback és integritat, no nova
resolució ni validació física del senyal.

### Ampliació: calibratge RAW real

F0.1–F0.3 s’han reconstruït en quatre processos nous: dues rondes per tren,
56/56 FITS SHA exactes contra l’històric i 28/28 entre rondes; també rebuts,
píxels i capçaleres exactes. Runner immutable i ordre per repetir en una
carpeta nova a `2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/README_RESULTAT.md`.
Sony aplica la taula `flat_dither_SONY.json` congelada: no se n’ha reestimat
l’origen. F1/F2 també passen en quatre processos nous: 52/52 FITS exactes
als històrics i 26/26 entre rondes; 20 JSON amb dades completes exactes i
10 fitxers JSON exactes entre rondes. Els JSON històrics tenen serialització
diferent. `raw_replay/RESULTAT_F12.md` i `F12_OUTPUT_INDEX.json`, dins
`2-ARXIU/reconstruccio_compactacio_20260915/`, fixen els 72 inputs resultants.
BLAS/OMP/VECLIB sol·licitats a 6; OpenCV en reporta 16 amb GCD, però no s’ha mesurat la concurrència efectiva. Pic RAM 21,46 GiB.
RAW→PSB complet continua pendent. Provar l’IO real de FITS
i temporals dins el confinament abans d’un càlcul llarg; fixar cwd/scratch
abans d’imports que poden crear fitxers. Refusar Python optimitzat al launcher.


V29 mostres/confiança i ajustos additius també repetits des de RAW amb els F0/F12 nous: 8/8 NPY exactes als històrics, 4/4 entre rondes; tots els JSON exactes en dades. Matriu V27 declarada, no reestimada. OpenCV sol·licita 6 i en reporta 16 amb GCD; concurrència efectiva no mesurada. Prova: `2-ARXIU/reconstruccio_compactacio_20260915/raw_replay/RESULTAT_OFFSETS.md`.

## Mapa de producció acceptada

1. RAW + darks/flats/invertits → `eclipse_determinista/cadena.py` fases 0–2,
   runs 019 Vixen i 016 Sony. La cadena base conserva deutes documentats.
2. Registre/correccions V25–V42 → corona, filtres i fonts lunars. El mapa
   V35 és `3-RECERCA/152_REPLICACIO_DETERMINISTA_RAW_A_V35_20260908.md`.
3. V56: `earthshine_max_detail_20260913/a1_native_rgb.py --all` + detector
   V55 → `earthshine_v56_three_routes_20260913/r4`, `r5`, `r8`, `e0_package`.
4. V68: PSB manual V67 → `v68_artefactes_20260914/b2`, `b4`, `b9`, `b10`
   → B11–B13/D3 → d4 → d5 Adobe → d6/e4. B5/B7 rebutjats no són producció.

Les abreviacions anteriors són scripts dins `3-RECERCA/tools/`; consulta el
nom complet i les dependències al mapa de l'auditoria. El revelat de Pere és
una entrada editorial, no uns controls Camera Raw recuperats. Conserva
anchors manuals exactes fins que una alternativa sense pèrdua tingui replay.
Una referència absent a RUN017 dins RUN018 no prova dades perdudes: comprova
els bytes reusats/hardlinks dels runs 018/019, no només els noms de ruta.

## Validació que no es pot substituir

- Congela el jutge i les dades reservades abans d'ajustar. Un segon tren
  compartit amb el compost és retenció en aquell domini, no independència.
- LROC/CGI és morfologia orientativa; no fotometria veraç per restar una taca.
- Les injeccions condicionals mesuren el seu operador; no tota la cadena.
- Mateix detector i mateix llindar a referència/candidat; registra també els
  controls nuls que invaliden una aparent millora. No promoguis un negatiu.
- Una millor aparença no acredita detall nou; en V56 el reforç és fotogràfic.

## Neteja que preserva reproducció i estalvia tokens

Primer manifest de dependències, després classificació: original/calibrador,
decisió manual, producte, intermedi reproduït o negatiu. `cau`, `old` i
`rebutjat` no impliquen prescindible: poden contenir inputs compartits.
Conserva scripts i paràmetres acceptats; per via negativa, protocol, causa,
mètriques, hashes i la mínima vista que expliqui l'error. Treu payloads només
si la reconstrucció o una còpia independent verificada els substitueix.

Duplicats: SHA-256 complet i identitat estable, moviment exclusiu a Paperera,
journal durable i restauració provada. No facis symlink/hardlink d'un stage
que pot rebre `save()` cap a un PSB editable de Pere. Usa un manifest de
redirecció amb hash i materialitza una còpia independent en una carpeta nova.
Mantenir el mateix nom no compensa perdre un snapshot manual irreproduïble.
L'estalvi lògic no és espai físic lliure: APFS comparteix blocs i la Paperera
ocupa fins que Pere la buidi. No buidar-la sense autorització específica.

Clons APFS poden mantenir rutes i edicions independents compartint blocs:
primer SHA complet, prova COW en ambdues direccions, metadata funcional,
ctime abans/després de hash, journal d’inode temporal i rename exclusiu.
No forçar macl/quarantine per passar el gate; conservar originals dels casos
exclosos. Birthtime/provenance poden canviar per identitat OS: registrar-les.
Lot verificat i recuperació: `2-ARXIU/reconstruccio_compactacio_20260915/array_clones/README_RESULTAT.md`.

Prioritat de Pere: reconstrucció correcta; després menys tokens; després
menys espai. Una entrada curta amb mapa i límits estalvia més que rellegir
tota la cronologia. Conserva la història exacta en arxiu i llegeix-la per tema.

## Arxiu i precisió dels rebuts

15-09: 84 PSB s’han recuperat exactes des d’un arxiu de 78,30 GiB, amb dues restauracions físiques i 51 rutes antigues verificades. Això conserva els checkpoints; no prova RAW→PSB. Vegeu `2-ARXIU/reconstruccio_compactacio_20260915/psb_archive/RESULTAT_ARXIU_REAL.md` i `INPUTS_EDITORIALS.json` de la carpeta mare.

Les dates de fitxer en nanosegons superen el límit enter exacte de JavaScript (2^53−1). Capturar-les i escriure-les amb Python directament a JSON, o transportar-les com a cadenes; no passar-les per nombres JavaScript. Si un manifest perd precisió, conservar la fallada i recapturar la metadata sense afluixar la comparació ni moure payloads. El cas concret és a `psb_retirement/PRECISION_REPAIR.json` del mateix paquet.

### Verificació posterior del15-09

V32G/R33 repetits dues rondes des deRAW ambF0/F12/offsets nous:26NPY històrics exactes,13entre rondes;12JSON complets sota el contracte de paths/canalG. GeometriaV27 i taula Sony encara declarades. RESULTAT_V32G_R33.md.

Neteja de106negatius verificada. En un trasllat ha aparegut una com.apple.provenance nova: preservar-la i registrar l'addició; cap canvi als valors antics ni al contingut. La mida base64 no és la mida descodificada: el primer supòsit12bytes era erroni, el valor real en tenia11; V2 es va aturar i V3 es va provar amb el valor observat. No generalitzar aquesta excepció a altres atributs ni forçar MACL/quarantine. Evidència a negative_retirement/RESULTAT_FINAL.json.

### V36 i fils de càlcul

V36 RGB també reproduïda en dues rondes: 78 NPY exactes als històrics, 39 entre rondes; 10 JSON amb dades completes exactes, normalitzant només meta.run. Resum a raw_replay/SUMMARY_V36_RGB.json. No és RAW→PSB complet.

No confondre fils demanats amb fils efectius. OpenCV 5.0.0 d’aquest Mac usa GCD: setNumThreads(6) deixa getNumThreads()=16, però això no mesura la concurrència activa. La docstring encara parla de512. Fixar la compilació i registrar petició, retorn i límit; no inferir sis ni setze treballadors efectius. Això qualifica també offsets/V32 i el futur A1 (petició original2). El closer inicial fallit queda conservat; la correcció és del registre d’entorn, cap comparador científic ni tolerància s’ha canviat.

### Arxiu Photoshop i metadades del lot82

82 històrics retirats amb snapshots exactes recuperables; V68/V56 normals.
El gestor `2-ARXIU/auditoria_reproductibilitat_20260915/gestiona_fitxers.py`
resol 133 rutes i materialitza inputs independents. Proves i ordres a
`2-ARXIU/reconstruccio_compactacio_20260915/psb_retirement/RESULTAT_FINAL82.md`.
No prometre igualtat de totes les metadades:22 substitucions de provenance
i25 addicions registrades amb abans/després; contingut i resta exactes.
L’excepció és local, cap atribut s’ha reescrit i DONE torna a ser estricte.
Els descriptors nous poden rebre atributs durant la primera lectura: només
reprendre un inode propi amb hash exacte i metadades estabilitzades.


### Fonts natives i recepta del catàleg estel·lar

A1 natiu també repetit en dues rondes de88RAW:352NPZ/5.280arrays històrics exactes,176NPZ entre rondes; JSON complets i352plansG exactes. Rebut: raw_replay/SUMMARY_NATIVE88.json. V27/V45/V42/dither continuen inputs fixos declarats; no prova RAW→PSB completa.

Recepta estrelles2.py recuperada de l’historial a raw_replay/recovered_v39_stars/:37estrelles declarades,8registres originals disponibles. El catàleg complet encara no s’ha regenerat. Conservar el productor; no substituir decimals absents per coordenades arrodonides d’E1d ni executar-ne directament les rutes temporals històriques.


B2V36 completa també repetida:6NPY+6JSON històrics exactes,3+3creuats; raw_replay/RESULTAT_B2_V36.md. No reutilitzar-ne el denominador com a pesosV29: són diferents. La V68 actual ja s’ha comparat: 134/149 canals comuns tenen píxels exactes, 15 difereixen en cinc capes, canvien tres visibilitats i se substitueix una capa oculta. E07 conserva aquest estat editorial com a PSB extern protegit; el delta suficient i el compost final continuen pendents. Prova: v68_editorial_delta/RESULTAT.md del paquet. No aplicar les conclusions del snapshot antic a aquesta desada sense incorporar els canvis.


### Replay V38 A1/A2

Dues rondes dels 67 RAW Vixen reprodueixen 3 NPZ/22 arrays i 4 JSON per ronda, inclosa la taula del limbe recalculada. Vegeu raw_replay/RESULTAT_V38_LIMB.md. En extreure només càlculs numèrics, conservar la selecció A1 que s’escriu DESPRÉS dels gràfics i el NaN històric; només les imatges són prescindibles. Els diagnòstics històrics A1 contra B2 i nul A2 són diferents de zero: reproduir-los no els converteix en validació nova. B2 V38 Vixen també reconstruïda: dos RGB complets i dos JSON exactes; raw_replay/RESULTAT_B2_V38.md. B2 interpola d_px i B_ln en float32: conservar aquesta expressió, diferent del pilot ROI A2. Verificar que el SHA del rebut de producció A2 està encadenat al VERIFIED abans de consumir-ne la taula. Les capes posteriors continuen pendents; per als pesos V29, vegeu la prova següent.


### Replay V29: cel, graella i resolució

Dues rondes amb F0/F12 de la mateixa ronda reprodueixen 38 NPY històrics i sis JSON; 19 NPY i tres JSON coincideixen entre rondes. Prova: `raw_replay/RESULTAT_V29_SOURCES.md`. F2 ha de ser original en un procés nou: no heretar plans/finestra/LUT de V36. L'índex F12 → MANIFEST → f0_inputs fixa els FITS i JSON nous; verificar també LDIC/PES/CEL de tots tres canals abans de produir. Només vuit rutes operatives JSON es normalitzen. Els 30 NaN del rebut de resolució es preserven per posició i bytes; no són una validació nova. Geometria V27 i dither Sony encara declarats; RAW→PSB complet pendent.


### V29: preservar la versió de cada pas

Dues rondes reprodueixen 48 NPY i deu JSON històrics exactes; 24 NPY, cinc JSON i 35 versions d’etapa coincideixen entre rondes. Recepta: merge → fusió source-only → refine amb helper antic de quatre passades → recentrat PCHIP recuperat sobre els tres smoothed per regenerar els u16 → gran angular final. El rebut refine i els rasters finals provenen de versions diferents del helper: congelar la versió per etapa, no substituir-les totes pel codi més recent. Les dates i els logs serveixen per recuperar la seqüència; els hashes i el replay complet la comproven. Rebut: raw_replay/RESULTAT_V29_PROFILES.md.

Conservar hashes dels intermedis abans de sobreescriure’ls estalvia duplicar payloads. La via rebutjada gran_independent no alimenta el resultat final, que es deriva de nou de les fonts per tren. L’exactitud de reconstrucció no valida de nou la ciència ni demostra RAW→PSB complet. V27/dither i les edicions de Pere continuen dependències declarades.


Retirada addicional del16-09: tres sortides descartades,10,49GiB lògics, amb set entrades protegides intactes; negative_extra3/RESULTAT_FINAL.md. Els homònims full_sampler_delta alimenten V54/V56 i es conserven. Una prova de restauració sintètica de57bytes comprova el mecanisme, però no equival a restaurar els tres payloads grans: declarar l’abast. El Python del Mac no exposa os.setxattr; la fixture usa l’ABI ctypes ja provat, sense canviar les guardes del lot real.


### Sony B V42: arguments efectius

Dues rondes reprodueixen quatre NPY i dos JSON històrics exactes, amb normalització només de sortida; dos NPY i un JSON coincideixen entre rondes. Rebut: raw_replay/RESULTAT_B2_V42.md. Cal passar delta_arcmin=8.10 explícitament: el default real és zero malgrat la docstring. Les tres correccions estel·lars i la rotació són inputs fixos declarats, no una reestimació. Segellar total, pesos i JSON abans de llegir oracles; preservar els helpers exactes de cada productor. B3 i RAW→PSB complet continuen pendents.


### B3 V42 i dependències que sobreviuen

Fusió B3 repetida en dues rondes:22NPY i dosJSON històrics exactes; onzeNPY i unJSON creuats, sense normalització. Rebut: raw_replay/RESULTAT_B3_V42.md. REP_CANVIS s’hereta de V34→V37; congelar també la versió del rebut. Conservar la branca de replegament i executar el jutge original, sense anticipar-ne el resultat. B3b és substituïda per V58 en els ràsters sense estrelles, però el seu catàleg encara és una entrada de D0b/D4: dependència per producte, no per carpeta. Mapa: raw_replay/NEXT_V58_DEPENDENCIES.md. Cap reconstrucció completa RAW→PSB declarada.


### Catàlegs intermedis i controls nuls

B3b (catàleg), D0b i D1 repetits en dues rondes: vuit JSON i dos CSV històrics exactes, quatre JSON i un CSV creuats. Rebut: raw_replay/RESULTAT_STAR_CATALOG.md. El prefix de detecció B3b i les seves escriptures JSON no depenen dels grans ràsters de pegats que V58 substitueix; es poden reproduir sense generar-los. D0b sobreescriu la projecció D0: fixar el productor efectiu, no el primer. Preservar també els tres controls nuls que passen D1; 54 candidats no són 54 estrelles confirmades. E1d i el catàleg/solució astromètrica continuen entrades fixes declarades.


### D2/D3: una prova descartada pot conservar dependències

D2/D3 repetits en dues rondes: quatre JSON i quatre NPZ/vuit arrays històrics exactes; dos JSON i dos NPZ/quatre arrays creuats. Rebut: raw_replay/RESULTAT_STAR_MODELS.md. D2 és el model PSF anterior, però la seva llista ordenada i desduplicada alimenta D3; no eliminar tot el productor pel veredicte del model. D3 estima components empírics, usats posteriorment a D4. Conservar 53 candidats i 43 repeat_AB segons el criteri històric, sense presentar-los com una validació astronòmica nova. Es poden ometre galeries després de comprovar que no alimenten el càlcul. Els dos NPZ before/after i JSON complets només ocupen uns 4 MB per ronda; el detall pedagògic no exigeix grans còpies de les imatges globals.


### S4: un manifest conjunt no prova la relació productor–output

S4 V51 recuperat i repetit en dues rondes:14arrays històrics exactes,7creuats; raw_replay/RESULTAT_S4_V51.md. El script conservat inclou revisions posteriors (suport només finit i medianes V52), però els arrays que consumeixen D4/E4 provenen de la suma ponderada V51 amb suport RGB positiu. Recuperar la versió dels logs i comprovar-la amb replay; no ajustar fórmules ni comparadors per encaixar. El manifest V53 reunia codi i arrays de moments diferents. Preservar versions per producte i derivacions de les rutes; els imports antics canviaven CAU. Guardarail històric rel_max0,0250842124 reproduït, no nova validació física. Els dos ràsters de l'intent fallit retirats a Paperera; codi i rebuts pedagògics conservats.


### D4/D4b: un fitxer pot tenir dos productors successius

D4→D4b repetit en dues rondes,132binaris i dosJSON per ronda exactes sota el contracte de set rutes D4; rebut raw_replay/RESULTAT_D4_D4B.md. La Vixen produïda per D4 coincidia amb el seu rebut, però la referència conservada ja incloïa D4b: nou pegats originals retornats perquè no superaven la detecció Vixen. Abans de culpar la numeració o canviar toleràncies, reconstruir les escriptures successives. Segellar SHA i capçalera de l'intermedi abans de sobreescriure'l; verificar també que el rebut anterior no canvia. Conservar una sola còpia de l'intermedi significatiu i retirar només duplicats amb substitut exacte. E6 substitueix els locals E1/E5 al muntatge sense sobreescriure'ls: l'ordre i el consumidor decideixen quina versió cal reconstruir. Mapa NEXT_FILTERS_R17.md. Exactitud numèrica no és nova validació física ni prova RAW→PSB completa.


### Derivacions petites i binaris reconstruïbles

V58 E3 necessita tres scale_tanh deV30: extreure el prefix literal que els calcula, no tota la presentació posterior. Duesrondes des deV29 nou reprodueixen els tres arrays subjacents (payload/forma/dtype) i els tres floats exactes; només1652bytes deJSON científic conservats. Els nou temporals de cada ronda es retiren després de consumir-los. No confondre el hash d'un array en memòria amb el hash del fitxerNPY complet. Prova raw_replay/RESULTAT_V30_SCALES.md.

La biblioteca sparse_conv.dylib també es reconstrueix byte a byte en dos arbres nous amb l'ordre original, mateix camí relatiu i entorn declarat; raw_replay/sparse_conv_rebuild/RESULTAT.md. Conservar argv, versió de compilador/SDK i hashes; la coincidència no prova portabilitat universal. Els workspaces futurs han de connectar explícitament les escales i la biblioteca noves: no reescriure una congelació mentre hi ha una execució viva.


### Filtres V58: operador i consumidor exactes

E1/E2/E3/E4/E6 reconstruïts en dues rondes:82NPY i10JSON històrics exactes,41NPY i5JSON creuats; cap normalització JSON. Rebut raw_replay/RESULTAT_FILTERS_V58.md. E6 local60/local30 substitueix els locals E1 al muntatge; conservar aquesta distinció. Només galeries omeses, no càlculs ni rebuts. Els cinc displays V42 encara són inputs fixos; no recalcular-los sobre V58. G9/I0 protegeixen màscares amb anchors V57; V60 C2 també modifica sis RGB, V61/V63 canvien màscares. Mapa NEXT_MASKS_R19.md. Identitat de filtres no demostra identitat dels encaixos manuals ni RAW→PSB complet.
