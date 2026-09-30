FORATS DE SUBSTÀNCIA, per ordre de risc

1. Ja hi ha un model de halo fet, i cap dels dos documents no el cita (VERIFICAT al disc)
Què falta: `~/Desktop/Eclipse 2026/Earthshine_FINAL/` conté un producte tancat del 15-08 a les 20:26 amb `earthshine_FINAL_halo_params.json` (dos nuclis d'ales de PSF amb índexs 1,5 i 2,5 i escales 6/12 i 320 px, amplituds per canal, rms per canal) i un `LLEGEIX-ME.txt` que diu literalment que el model és «dos nuclis d'ales de PSF sobre la corona real + pla de cel», validat fora de mostra contra el mapa d'albedo LROC WAC amb r=0,68 (escala completa) i 0,73 (mitja escala). El dossier afirma que la separació halo/earthshine «no està feta» i el pla la torna a plantejar de zero.
Per què importa: el pla duplicaria una jornada de feina i, pitjor, amb un mètode inferior (punt 2). I el fitxer ja diu que les capes Sony de 2 s i 1 s i el Vixen empitjoraven la validació fora de mostra: és informació que el pla ignora quan proposa ajustar sobre dotze fotogrames profunds dels dos cossos.
Com tancar-lo: llegir aquell directori i el `research/72` §5-6 abans de reobrir G3, i redefinir G3 com «reajustar el model existent sobre dades no retallades», no com «mesurar un halo».

2. El model de halo del pla és físicament dolent: assumeix simetria respecte del limbe (INFERIT, però directe)
Què falta: el pla ajusta `I_dins(r) = E + A·(R_lluna − r + r0)^−α`, o sigui llum difusa que depèn només de la distància al limbe. El halo dins del disc el genera la corona, que és fortament asimètrica (bagues d'un costat, forats polars de l'altre). El model ja existent no ho fa així: convoluciona la corona real mesurada amb les ales i n'ajusta només les amplituds. Aquesta és la manera correcta.
Per què importa: un ajust radial sobre un halo asimètric absorbeix l'asimetria dins de `E`, i llavors `E` no és earthshine.
Com tancar-lo: model directe (corona mesurada ⊗ nucli d'ales) + constant + pla de cel, ajustant només amplituds i índexs, exactament com el que ja hi ha.

3. `E` és degenerat amb el pedestal de cel, i la Fita 2 del pla no es pot complir (VERIFICAT al LLEGEIX-ME)
Què falta: el fitxer diu «Fotometria absoluta: NO (pedestal de halo/cel degenerat amb una constant)». El pla fa dependre tota la decisió D3 d'una Fita 2 que exigeix que l'earthshine dels dos trens coincideixi dins de 0,3 EV. Si la constant és degenerada, aquella comparació no mesura res: compara dues constants no identificables.
Com tancar-lo: substituir la Fita 2 per un criteri d'estructura, no de nivell. Concretament, la correlació espacial amb el mapa LROC WAC (que ja dona r=0,68/0,73) sobre cada tren per separat, i exigir que els dos trens donin el mateix mapa relatiu, no el mateix zero. El nivell absolut només es pot recuperar amb una àncora externa (punts 5 i 6).

4. Demosaic AHD dins d'un flux fotomètric (VERIFICAT al pla, §G2-bis)
Què falta: el pla especifica `demosaic_algorithm=AHD`. Interpolar el mosaic correlaciona píxels veïns i barreja canals. Això trenca tres coses del mateix pla: el criteri 3 de G2-bis (comptar píxels al sostre del TIFF i comparar-los amb les fotolocalitats saturades del RAW dins d'un factor 1,3 — amb AHD la saturació s'escampa als veïns i el factor no pot sortir), el llindar de 5σ (la σ per píxel deixa de ser la del sensor) i la màscara de saturació per canal.
Com tancar-lo: no desbayerar. Treballar amb els quatre plans R, G1, G2, B a mitja resolució (superpíxel 2×2), que a més et deixa els G1/G2 com a estimador de soroll gratuït. El mostreig ja és el coll d'ampolla a la visualització; la fotometria no perd res.

5. Ningú no ha mirat si hi ha estrelles als fotogrames, i és el pont a la calibració absoluta (INFERIT)
Què falta: a 8 s i f/2,8 amb 300 mm, i a 10,3 s amb el VSD90SS, hi ha d'haver estrelles al camp durant la totalitat. Bemporad (2020), que el dossier declara «la referència directa per a DSLR», calibra exactament així: dues estrelles de magnitud coneguda i la magnitud aparent del Sol. Cap dels dos documents no proposa buscar-les.
Per què importa: resol el problema 3 del dossier («no sabem la densitat òptica del filtre») sense mesurar el filtre, dona l'ala de la PSF per la via d'`elderflower` que el dossier cita i no fa servir, i de passada permet resoldre el camp (plate solve) i tenir orientació nord real, que ara no es té (el LLEGEIX-ME diu que l'orientació és la del sensor).
Com tancar-lo: mitja hora. Apilar les tres àncores i els tres fotogrames de 10,3 s, córrer un resolutor astromètric, identificar les estrelles del catàleg dins del camp i fer-ne fotometria d'obertura.

6. Cap dada externa del mateix dia (INFERIT, oportunitat gran)
Què falta: el 12 d'agost de 2026 SOHO/LASCO C2 i C3 estaven observant, i probablement el K-Cor de Mauna Loa (18:30 UT = 08:30 al matí a Hawaii). LASCO C2 cobreix 2–6 R☉, que és exactament la teva banda de solapament; K-Cor cobreix 1,05–3 R☉ i és el que Bemporad fa servir per a la intercalibració. Cap dels dos documents no ho esmenta. Tampoc no esmenta la predicció MHD que Predictive Science publica per a cada eclipsi total.
Per què importa: és calibració absoluta gratuïta, i és l'única validació externa real de «aquesta estructura existeix». La prova de coherència entre trens del pla és bona però comparteix atmosfera, lloc i operador; LASCO no.
Com tancar-lo: baixar les imatges de nivell 1 de LASCO C2/C3 i de K-Cor per a la finestra 12-08-2026 17:00–20:00 UT i la predicció de Predictive Science per a aquest eclipsi, i afegir-les com a G7 de validació.

7. El camp pla es pot fer encara, i ningú no ho proposa (INFERIT)
Què falta: els dos documents tracten l'absència de flat com un fet consumat. Els dos trens existeixen. Un flat de panell o de cel crepuscular a la mateixa obertura i focus tret aquesta setmana no és perfecte, però el vinyetatge d'un refractor i d'un teleobjectiu és estable si no es toca el diafragma.
Per què importa: sense flat, el vinyetatge queda dins del terme de halo i el resultat deixa de ser un model físic. Amb un flat aproximat, el terme empíric es redueix molt.
Com tancar-lo: dir-ho a Pere ara, mentre encara pot reproduir el muntatge. Documentar que és un flat posterior.

8. El guany en electrons per compte no es coneix, i els pesos de G5 no són òptims (VERIFICAT al pla)
Què falta: la funció de pes del pla és un trapezi (rampa d'entrada, pla, rampa de sortida). El problema obert que el paper de 2006 declara és trobar els pesos que minimitzen el soroll, i aquests són inversa de la variància: variància = senyal/guany + soroll de lectura². Sense guany no hi ha pesos òptims.
Com tancar-lo: corba de transferència de fotons amb les dades que ja hi ha. Mitjana i variància d'un mateix pegat de corona als setze esglaons d'exposició del R6; el pendent és 1/guany. No calen flats.

9. No hi ha mapa d'incertesa (INFERIT)
Què falta: tots els criteris del pla són percentatges (3 %, 5 %, 8 %, 25 %) sobre una imatge sense pla de variància. No es pot dir si un 3 % és significatiu.
Com tancar-lo: propagar la variància per píxel al llarg de G5 i lliurar `hdr_var_*.tif` al costat de `hdr_*.tif`. Sense això, cap de les fites és una porta.

10. El 6D no existeix per a cap dels dos documents (VERIFICAT: 3.063 CR2)
Què falta: hi ha 3.063 fitxers del 6D del 12 d'agost, a 35 mm f/2,5, majoritàriament 1/4000 però amb 163 a 1/30. És camp ampli, no corona, però durant la totalitat una exposició d'1/30 a 35 mm capta planetes i estrelles brillants.
Per què importa: és una tercera referència astromètrica i fotomètrica independent i és el registre de com era el cel (llum difusa atmosfèrica, punt 2 del G3 del dossier), que és justament la component que no sabeu separar. També hi ha 249 CR3 a `Vixen/` i vuit fitxers a `HDR/` que cap dels dos documents no inventaria.
Com tancar-lo: inventariar les set carpetes del disc abans de tancar G0. G0 està declarat FET i no cobreix la meitat de les dades.

11. Estètica confosa amb ciència: no hi ha cap pregunta científica declarada
Què falta: el pla acaba a `vis_final.png`. Les fites decideixen si la imatge és «defensable», no si respon res. El dossier té tota la maquinària de van de Hulst i Baumbach i el pla no la fa servir enlloc.
Com tancar-lo: escollir abans de G5 quina magnitud es publica: perfil de brillantor radial per sector amb la llei de tres termes, mapa d'earthshine contra LROC, o posició de plomalls contra PFSS. La resta és postproducció.

12. Contactes que no s'han intentat (INFERIT)
El dossier dona `[adreça]` i no proposa escriure-hi. Val la pena demanar-li a ell el LDIC o que passi el teu compost per Corona 4.1, i a Hrazdíra el codi de correlació de fase iterativa. També Auchère per al WOW *edge-aware* i Boe per a la separació K/F. Cost: quatre correus. I quan hi hagi producte, dipositar-lo amb DOI a Zenodo, que és el que fa que la sèrie sigui citable.