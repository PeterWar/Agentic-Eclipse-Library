# 163 — V44: cremallera confirmada; V45: fonts temporals, sense recuperació acreditada de tot el limbe

Petició de Pere: revisar `Earthshine_V44_artefactes.tif`, corregir la cremallera marcada en blau clar i el residu lila prop de les perles/protuberància, i prioritzar detall real de tot el limbe aprofitant els dos telescopis i els instants tardans. Autorització desatesa i de Photoshop vigent. Codi a Downloads; actius a Desktop; mateix llenç 10551 × 7506. Cap RAW ni PSB anterior sobreescrit.

**Resultat científic: el problema complet no queda resolt.** S'ha identificat l'error de V44, refet la font verda nadiua de 88 fotogrames, millorat la selecció temporal i corregit el desequilibri dels pesos. Però no hi ha una candidata de disc net que alhora conservi les textures radials i superi el jutge independent de l'últim limbe. Es lliuren **fonts editables**, no una V45 fotogràfica certificada ni un nou Capes Totals. La V44 queda preservada i explícitament qüestionada per aquestes proves.

## 1. Fitxer de Pere i causa de la cremallera

Entrada exacta: `/Users/USUARI/Downloads/Earthshine_V44_artefactes.tif`, RGB16, 10551 × 7506, 3.695.828 bytes, SHA-256 `2e73cd404f760ed894ad9805e812a828ebf357e55a98ce49317d491d1159bd4a`.

La imatge correspon essencialment a la capa d'aportació natural de V44 aïllada, no a tota la composició amb la capa09. Això explica part de la forma de la protecció de perles, **però no invalida les marques**: la cremallera es reprodueix en el càlcul i no és una aparença inventada pel TIFF.

- Les tres marques cian principals ocupen r≈401–428 px; mediana≈414,5. La marca lila ocupa l'oest, prop del limbe físic; les comparacions quantitatives utilitzen sectors geomètrics fixos, no les pinzellades com a màscara de correcció.
- `v44/f3b_detall_log.py`: FFT en finestres64 amb pas8. Una font purament radial, sense textura lunar, produeix RMS angular1,895 DN a r410–420; a r419 la correlació artefacte real/nul és0,904. Traslladar1/2/4px altera el resultat0,190/0,347/0,483 DN; a8px es repeteix exactament. És empremta del mosaic de finestres.
- `v44/f5_render.py`: la suma de pesos del detall isotròpic i tangencial arriba a1,69848 a r412,034. Amplifica la zona defectuosa; normalitzar aquesta suma no cura la causa del mosaic.
- `v44/f3c_tangencial.py`: el filtratge només angular altera el soroll, amb quocient de potències de gradients radial/tangencial0,993→2,962 aσ1. No és un tractament isotròpic.
- El detall V44 s'esvaeix entre435,00 i439,56px. La franja sense textura visual no és una demostració que el RAW no contingui cap senyal.

Rebut causal: `output/v45_earthshine_20260910/4-rebuts/A1_causal_audits.json`. L'obertura i la coincidència de píxels a Photoshop de V44 continuen sent certes; **no acreditaven absència d'artefactes ni recuperació de tot el limbe**. La conclusió anterior «detall fins0,96R» s'ha d'interpretar amb aquestes rectificacions, no reutilitzar-la com a acceptació global.

## 2. Què aporta l'instant tardà a la zona lila

Comparació nadiua de dues exposicions iguals, Vixen1/2s, ja en coordenades lunars comunes:

| Mesura fixa, sector180–195° | 572A2972, C2+11,4s | 572A2990, C2+73,1s |
|---|---:|---:|
| MedianaG a r440–449, amb mostra vàlida | 1458,73 | 1032,68 |
| Fracció amb alguna mostra verda vàlida, r449 fins al limbe observat | 74,47% | 92,67% |

L'instant tardà té menys llum contaminant i més superfície mesurable en aquest sector. **Pere tenia raó a reclamar aquesta informació temporal.** No s'ha substituït tota la perifèria pel fotograma més tardà: en altres sectors el primerenc és millor, i la Sony tardana té saturació/ghost prop d'algunes zones. «Més tard» no és sempre «més net».

El perfil comparat i els retalls amb exactament la mateixa escala són a `F8_comparacio_temporal_lila.png`; dades i hashes a `F8_temporal_comparison.json`. Les dues medianes tenen els seus respectius suports vàlids; no són una estimació aïllada de llum lunar ni una resta de PSF.

## 3. Nova font i pesos

Cadena publicada de fonts: `b1_native.py`/`b1_run.py` → `f2w_noise.py` → `f2_temporal.py` → `f6_reference_transfer.py` → `f7_fonts.py` → `c5_fonts_psb.py`. Tots aquests scripts són a `research/tools/v45_earthshine_20260910/`. Els scriptsF3/F5 d'aquesta carpeta són pilots rebutjats, no formen part del producte de fonts.

### Mostres dels RAW

Els88 fotogrames registrats dels dos trens es regeneren a partir dels dos verds del CFA. Una sola interpolació incorpora geometria solar/lunar, rellotge comú, apuntament i correccions acceptades. Es conserven dark/flat/LUT Sony i coherència de la cadena; no s'ha fet drizzle ni canviat el camp.

Cada pla verd exigeix que els quatre píxels CFA que contribueixen estiguin per sota del85% de saturació i siguin vàlids. No s'exigeix que el canal vermell sigui vàlid: així no es llença G útil perquè R satura en una protuberància. La font és monocroma G1+G2, sense matriu RGB.

S'elimina el llindar de brillantor12→48DN heretat: condicionar el pes a una lectura positiva seleccionava soroll positiu en exposicions curtes. Les lectures febles/negatives continuen existint i la variància dona poc pes a les curtes quan toca. La font final seleccionada té zero píxels lunars sense dada i zero valors no positius; això és **cobertura**, no detecció de textura.

Només una nova correcció de registre addicional s'aplica: SonyDSC06982(+0,63747,−1,83705)px, integrada al remapatge CFA. Guany modest en meitats reservades i en24–48px; no millora totes les bandes. Candidats per2972/2977/2990/2995/3002/3008 no s'apliquen perquè els jutges reservats empitjoren o discrepen. Les correccions acceptades de V44 es conserven. Rebut `A2_native_registration.json`.

### Els cinc RAW addicionals prop dels contactes

No s'ha equiparat «88 registrats» amb «tots els RAW nominalment dins la totalitat». S'han revisat també2958/3026/3027 deVixen(1/3200s) i7003/7004 deSony(1/800 i1/6400s). F1.2 els situa a C2+0,415s o a menys d'1s abans deC3; la guarda temporal d'1s els exclou deF1.3. La cronologiaSony només té precisió de segon: aquests temps són nominals.

Auditoria dels RAW sense demosaic i geometriaF1.2 provisional: els quatre contribuents de cadascun dels dos verds són vàlids al100% a la zona lila r420–454, igual que els curts veïns ja inclosos. No s'hi demostra nova cobertura. Els Vixen3026/3027 tenen informació condicional semblant a3025; Sony7003/7004 tenen més llum de fons que7000/7001 a igual exposició. En particular, a r440–449 el G menys pedestal passa3,93→12,27DN entre7000 i7003. No són referències netes millors en aquesta prova.

Assignant als cinc el pes dels veïns equivalents, la projecció d'aportació addicional és0,000629% interior,0,001102% a r420–450 i0,004390% a r449–454. **És una projecció, no una cota matemàtica per a cada píxel.** No inclou una nova calibració de camp ni registre refinat. Es mantenen88 entrades; els cinc poden servir per estudiar anatomia/contacte al seu instant, amb nova verificació de rellotge/geometria. Rebut i hashes dels cinc RAW: `A3_extra_contact_RAW_audit.json`.

### Soroll fix i pes entre components

La variància fotònica/de lectura no representava tot el patró fix del sensor. Es mesura potència8–64px en una apertura interior fixa amb exclusió del ghostB, pla quadràtic únic i Fourier; s'estima el senyal compartit amb creuades Vixen×Sony. No s'utilitza LROC per triar pesos.

| Component | Factor efectiuα que divideix el pes | Fracció abans | Fracció després |
|---|---:|---:|---:|
| Vixen10s | 35,54865 | 46,48% | 32,27% |
| Vixen2s | 32,94040 | 8,54% | 6,40% |
| Vixen≤1s | 14,82631 | 5,62% | 9,35% |
| SonyA | 18,86459 | 17,56% | 22,98% |
| SonyB | 18,55317 | 21,80% | 29,00% |

Aquestes fraccions són globals, dins l'apertura d'auditoria i **abans de la preferència temporal**, no els pesos de la zona lila. S'aplica `w=q/(α·NG4(v))`. El Vixen conserva48,02% del pes total. Reproducció numèrica exacta del revisor a `F2w_empirical_weights.json` i `f2w_noise.py`.

α és una calibració efectiva d'aquesta banda, no una variància física completa: diferències de MTF poden comptar senyal no compartit com a residu. Queda covariància entre componentsVixen i no s'ha identificat tota la incertesa de flat/dark/camp ni la covariància espacial Sony. La variància de sortida continua sent **condicional**; no s'ha inflat silenciosament perα.

### Selecció temporal

Quinze grups temporals (9Vixen,6Sony), cadascun amb HDR nadiu. La preferència utilitza mitjanes cartesianes8px només sobre la superfície lunar observada, cobertura contínua elevada a4 i percentil20 suau mitjançant CDF logística. El terme de2% cobreix de manera declarada petites discrepàncies de nivell entre trens; no és una precisió fotomètrica mesurada.

El resultat és una **suma convexa de mostres observades**, amb pesos segons soroll/cobertura/excés de llum. No hi ha selecció del mínim de cada píxel. A l'exterior diagnòstic només s'estén la preferència, mai la radiància; s'hi combinen les mostres exteriors reals. El ghost SonyB conegut queda exclòs gradualment amb el guard heretat.

La resta diferencial de vel calculada també perF2 es conserva com a experiment, però es rebutja: produïa valors negatius i sobrecorreccions. **Els fitxers `*_corrected.npy` no són el producte.** La font és `combined_reference.npy`.

## 4. Controls de conservació i recuperació

### Transferència de senyal feble

Dotze injeccions de0,05DN després del registreCFA, abans de recalcular preferències temporals: paquetsσ20, longituds16/24px, orientació radial/tangencial, r414nord, r440lila i r451nord. Guany coherent final0,999790–1,000648; totes dins0,9–1,1. Error relatiu màxim5,35%. Rebut `F6_reference_transfer.json`, vinculat alF2final.

És un control **condicional posterior al CFA**. No és una injecció òptica/RAW, una mesura de resolució ni una detecció de cràters reals. La corba global deF7 és monòtona/invertible abans de quantitzar; no té filtre espacial. El TIFFfloat32 conserva la font lineal perquè la visualitzacióRGB16 no garanteix conservar amplituds subquantificació al limbe molt brillant.

### Jutge independent de l'últim limbe

Font directaG, únic pla cartesià, anell435–449, vuit sectors fixos45°, tres bandes, onze girs de control30–330°. LROC es manté alineada/fixada com a jutge; cap píxel LROC entra al producte. Cada cel·la indica correlació/màxim absolut de girs:

| Banda | Vixen×Sony | Combinat×LROC |
|---|---:|---:|
| 16–24px | 0,05730 /0,14649 | 0,00408 /0,00592 |
| 24–40px | 0,07853 /0,10192 | 0,01059 /0,01406 |
| 40–64px | 0,13653 /0,12717 | 0,01280 /0,01690 |

**0/24 combinacions sector×banda passen alhora Vixen×Sony, Vixen×LROC i Sony×LROC**, tant en flux lineal com logarítmic. No hi ha millora nova corroborada de tot aquest últim anell respecte deV44. L'absència de passada no demostra absència física de senyal. La mesura angular és sobretot tangencial;14px d'amplada no resolen per si sols transferència radial40–64px.

Fonts definitives: Vixen `87be75c6e14017eec7d050e1f4604f2da330b29035a2dc2f0b80492d749de5d3`; Sony `9561ae6a9b285d21b16abfec68cec6792720def8d9f4fc1d5aa0a32549e7ae7f`; combinat `faeec8deff41d2092b866a1e7aa146ceb22daad35d14a268268f21a818f60fb7`.

La reproducció de Codex de l'script del revisor coincideix: `f9_fixed_judge.py` → `F9_fixed_last_limb_judge.json`;40.320/40.320 mostres comunes vàlides,0/24 tant lineal com logarítmic. La finestra cosinus pondera la correlació després de la FFT angular completa; no és apodització prèvia al filtratge.

## 5. Tractaments descartats i per què no es lliura un disc artificialment net

| Prova | Resultat i decisió |
|---|---|
| Canviar només FFT local per passa-alt cartesià | El fons sectorial continua absorbint textures radials. Rebutjat. |
| Perfil per sector + interpolació cúbica | A r451 paquets radials16/24px poden donar guany pròxim a0 o negatiu, mentre els tangencials passen. Neteja visual no equival a conservació. |
| Fons de poques bases radials | Millor transferència de paquets locals, però queden bandes fosques/clares amples al limbe. No promogut. |
| Harmònics angulars baixos m≤1…6 | Alguns jutges cian milloren, però es retiren modes lunars reals i persisteix una vora falsa. PrecedentG-AZI de research/127; no promogut. |
| Coordenada de fons centrada a la vora | Augmenta el residu anular i empitjora transferència. Rebutjat. |
| PSF comuna ajustada a diferències temporals | Millora parelles primerenca/tardana però empitjora una parella tardana/tardana: RMS29,79→61,93. No valida una resta absoluta. |
| Coeficient local del vel temporal | Redueix discrepàncies reservades; la resta absoluta crea negatius. La versió diferencial conserva injeccions però no recupera detallLROC de435–449. Diagnòstic, no producte. |
| Ales de PSF mesurades amb estrelles | S/N nominal≈1,5–2 als radis9–26px, sense incloure fons de corona. No prou precís per restar earthshine feble. |

Els perfils estel·lars vius són a `Desktop/Eclipse 2026/Derivats/Astrometria/Estrelles/Work_2026-08-17/xmatch/wings_r6.npz` i `wings_sony.npz`; executables `astrometria/xmatch/wings.py`/`wings2.py`. La integralR6=0,963 a30px no prova la precisió de les ales. A130px arriba a1,72 vegades el flux estel·lar; Sony11,77: fons residual. `fitpsf.py` mesura el nucli en19×19, no aquestes ales. El model `halo_sony2_full.py` ajusta dins la Lluna ambLROC i no és una mesura independent.

Les diferències entre instants identifiquen canvis del vel, però no determinen per si soles la component comuna que tots els fotogrames comparteixen amb la superfície lunar. No s'ha importat texturaLROC, omplert la franja amb terreny artificial ni aplicat un esvaïment per amagar el problema.

Els experiments anteriors a la correcció de pesos són preservats a `cau/pre_FPN/` amb manifest. Els valors negatius i les previsualitzacionsF3/F5 continuen al cau de recerca com a negatius; no són variants que es recomanin activar.

## 6. Lliurables i ús

- `Capes interiors/Earthshine_V45_Fonts.psb`:24capes, RGB16, mateix10551×7506. Les18capes deV44 es conserven amb canals comprimits byte a byte; només visibilitats adaptades. Sis capes noves de fonts, Normal100%, màscares editables; activar-les d'una en una. La visible és la combinada amb preferència temporal, explícitament «vel present». Capa09 de context conservada.
- `Earthshine_V45_HDR_G_lineal.tif`: mateix llenç, RGBfloat32 amb alfa no associada; els tres canals són G/65535. Font monocroma, sense resta de fons ni filtre espacial. No representa radiància absoluta.
- `Earthshine_V45_font_i_pesos.npz`: fontG, Vixen/Sony separats, combinat sense preferència, pesos de cada grup temporal, geometria/alfa/unió i origen de la tessel·la. Conserva totes les mostres observades, inclòs context exterior que la màscara Photoshop amaga.
- `F8_comparacio_temporal_lila.png`: comparació diagnòstica primerenca/tardana. Les vistes de recerca rebutjades no es barregen amb la selecció publicada.

Corba única de visualització de les sis capes: `0,20 + 0,045·asinh((G−528,312744140625)/20)`, sense filtratge espacial i amb zero retalls de valors vàlids dins la Lluna. La màscara d'unió amb09 és exactament laV44, desactivable; és una protecció geomètrica/fotomètrica, no una màscara nova de «qualitat de detall». El TIFF32 porta la geometria del limbe observat, sense aquesta protecció de09.

**L'aspecte de vora lluminosa es conserva en aquestes fonts perquè hi ha llum dispersada observada.** No s'ha de confondre amb una neteja acabada de l'earthshine. El PSB és una font de treball reversible; no substitueix Capes TotalsV42 ni acredita el resultat fotogràfic sol·licitat per a tot el limbe.

Porta real, readback, hashes de publicació, integritat d'originals i instruccions de represa: `output/v45_earthshine_20260910/4-rebuts/C5_*.json`, manifest de lliurament i handoff d'aquesta ronda. La passada Photoshop només acredita contenidor/composició, separada del resultat científic negatiu anterior.

## 7. Verificació del paquet de fonts

PSB publicat: SHA-256 `d8bfd4cfc39346b025dd8f071d8b9acd235ae879b62dd576cbf2a25c9199adbc`,1.266.007.766bytes. Les18capes prèvies es comproven amb hashes dels canals comprimits; els nous RGB i màscares es descodifiquen i coincideixen exactament. Segon lector ImageMagick i porta real `porta_photoshop.sh`: **OBRE10551×7506,24capes**.

Photoshop recompon la capa nova apagant-la/encenent-la, duplica el document i exportaTIFFRGBA16. Comparació amb composició independent: màxim3DN16 a la Lluna i a102.935.013valors de canal visibles; alfa exacte. TIFFde readback SHA `a0fcf473ad3d75dfcda1cedadefe707bbeaef77fe1afd931cb69d6a76998b6ec`. Les vistes reals s'han inspeccionat tant a la Lluna1:1 com al llenç complet: el vel lluminós continua visible i per això el paquet es declara font, no neteja fotogràfica.

La lectura numèrica del TIFFfloat32 és exacta respecteG/65535 i la seva alfa. La visualitzacióRGB16 té zero clipping lunar; l'exportaciófloat32 evita perdre les amplituds petites que la corba de pantalla podria quantificar. La comprovació del fitxer32bits en Photoshop es registra separadament a `F7_HDR_photoshop.json`.
