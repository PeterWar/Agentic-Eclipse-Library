# 161 · Com fa Brno l'earthshine i el limbe net; i la V43: l'apilat lunar amb totes les exposicions dels dos trens

10-09-2026 (tarda–vespre). Ordre de Pere: «ara treballarem earthshine només. M'impressiona lo ben treballada que està l'earthshine a TSE_2026_530mm_DHS de Druckmüller; el limbe està completament net. Repassa els seus papers a veure si podem entendre què fan.» Després: «mira `Earthshine_V42.psb`… valora un apilat sumant exposicions curtes dels dos telescopis, que comptin més que les llargues vora el limbe… si té sentit, fes-ho, desatès.»

Fonts: els papers locals a `Papers Druckmuller/` (CAOSP 2006, ApJ 2009, tesi Druckmüllerová 2013/14, FNRGF 2011, MGN 2014, Hrazdira 2021, Habbal 2010/2011/2014, Boe 2021), les 667 pàgines de la web de Brno (`zam.fme.vutbr.cz/~druck/eclipse`, rastrejades en text), cerca externa, i la nostra cadena (research/125–127, 155, 160; `f1_earthshine_v42.py`, `b2_lluna_v42.py`). Els §1–6 són el document d'un flux de 6 lectors + síntesi + 3 verificadors adversaris (fidelitat a les fonts, física, normes) + revisió (11 agents); el §7 és el que s'ha FET després, amb els números. Les línies («l. 2286») són del text extret amb `pdftotext -layout`.


## 1. Resposta curta

Brno no «neteja» el limbe: l'evita, i la nostra cadena ja fa la part principal. (1) La corona es compon amb la Lluna de cada fotograma exclosa (pes −1) i un fotograma de referència que mana al disc: una sola vora, cap anell. La base V38→V42 ja fa el mateix (màscara lunar per fotograma, forat = intersecció, disc d'un sol instant, t 15 s): la diferència amb Brno és de nom, no de mètode. (2) La Lluna il·luminada s'alinea A PART i s'insereix com a capa (documentat 1994–2010; el 2026 no en diu res); l'únic «com» descrit és del 2001: per formacions de la superfície, perquè el limbe és saturat als llargs. (3) Els filtres de Corona (tangencial/ACHF, NRGF/FNRGF) no miren dins del disc; el MGN sí. (4) El disc és molt fosc respecte de la corona (0,18 en sRGB): el glow del limbe hi és igual que al nostre (×1,3 en lineal a 0,95 R), però no es veu. (5) Centenars de fotogrames ≤ 1 s, no cinc de 8–10 s. El nostre limbe brut no és la composició: és una franja de 452–457,5 px sense dada a cap producte, un disc a 0,49 de la corona que ensenya el glow, i una corona amb el R retallat que embruta per fora.

## 2. El que està DOCUMENTAT

### Captura

- 2026, 530 mm: «Exposure 1/250 s - 1 s, ISO 100 Processing Composition of 225 eclipse images» (pàgina web de Brno, `Ecl2026s/Trigaza/TSE_2026_530mm_DHS/0-info.htm`). Sol a 7°. Cap paraula sobre la Lluna.
- 2024 Sims: 487 fotogrames 1/250–1 s (web de Brno (`Ecl2024u__Sims__WL-300mm__0-info.htm.txt`)).
- L'earthshine no exigeix 8 s: 2006 Egipte, 58 fotogrames amb màxim 1/2 s: «The perfect display of the lunar surface... beyond the abilities of human vision» (web de Brno (`Ecl2006em__Tse2006em_mo1__0-info.htm.txt`)). 2015 Svalbard, Sol a 11°, 1/1600–4 s: superfície lunar «surprisingly well» (web de Brno (`Ecl2015s__800mm__0-info.htm.txt`)).
- Seqüència: «ending with an image where a large part of the corona is overexposed» (tesi 2013, l. 1518-1521).

### Alineació

- «Neither the edge of the Moon nor stars are suitable for the high precision alignment» (CAOSP 2006, l. 88-90).
- 2009: filtre tangencial + màscara anular amb «r1 is a constant greater than the lunar radius» (ApJ 2009, l. 109-134); es treu «all parts of the image which move... such as the Moon, bright stars, dust particles» (l. 109-116). Precisió simulada < 0,01 px (l. 182-186).
- Tesi: «the window function has to vanish both at the edge of the Moon / saturated part» (l. 2286-2288).
- La Lluna a part: «it was necessary to align the solar corona and the Moon separately» (2001, web de Brno (`Ecl2001z__Ecl2001_dd_mo__0-info.htm.txt`)); la correlació de fase no servia perquè «the edge of the Moon was missing on the images with long exposure times», i va alinear «identifying formations on the lunar surface» (ACC Match II). Les pàgines 1994, 2006 Turquia i 2008 només diuen «separately». Tolerància: «about 5 seconds difference... would cause noticeable blurring of the Moon» (2006 Turquia).

### Composició (LDIC)

- Pes: «wik,l = −1 in the Moon covered part» (CAOSP 2006, l. 191-192). Referència: «with a correctly-exposed innermost part of the corona» (l. 196-197). Eq. 3: f = 0 si i ≠ j i algun dels dos és Lluna; |w| si i = j (l. 200-202). Resultat: «a proper view of the eclipsed Sun at the moment when the image Am was taken» (l. 216-218).
- Tesi 2013, eq. 4.15 (l. 2352-2363), que descriu l'LDIC «implemented by Miloslav Druckmüller... in 2006» (l. 2360-2361): pes per valor de píxel (0 «from about 85 % of the dynamic range», l. 2364-2374); k, q per 60 segments angulars; «The composition starts from the longest exposure times» (l. 2375-2388); permet «compose images with different distribution of diffuse light» (l. 2414-2419).
- La Lluna: «It has to follow the moving position of the Moon, possibly even making a sharp composition of the Earth-lit Moon» (l. 2412-2414). Model lineal «hx = hx,0 + t · hdx» (l. 2456-2462), mesurat als curts; «A minimum is one image after C2 and one before C3» (l. 2442-2500).
- Web: un instant declarat, «The position of the Moon represents the situation 54 seconds after the second contact» (2008, web de Brno (`Ecl2008m__Tse2008_1000_mo1__0-info.htm.txt`)); també 15, 61, 62, 120, 139, 157 s. 1995: «This single image was used for reconstruction of the nearest neighborhood of the Moon» (`Ecl1995i__Outcor`). 1999: «the exact sharp image of the Moon» (`Ecl1999n__23cor`). 2006 Líbia: «the lunar edge is correctly recorded on a single image only».
- Quan volen tota la corona: «the black area occulted by the Moon is not a circle, but the intersection of two circles» (2026 800 mm, pàgina `TSE_2026_800mm_DHS`; igual al 2010 Fe X).
- Habbal 2010: «the third one is an overlay inset for the Moon» (l. 101-102); peu de la Fig. 1: «the lunar disk that is normally underexposured» (l. 124).
- Versions a la web: LDIC 1.0 (2001), 4.0 (2006), 5.0 (2008–2015), 6.0 (2026). El paper del 2006 no anomena l'LDIC (només «version 3.0» de PhaseCorr/Corona, l. 145 i 378).

### Filtres

- Convolució parcial: mitjana normalitzada per Σ C·w, w ∈ {0,1} (tesi, Def. 3.27-3.28, l. 1264-1300). «They have w set to zero inside the Moon» (l. 1305-1308). «The filters are applied out of the Moon... the interior of the Moon is irrelevant» (l. 727-728).
- ACHF: «Cx,y(i,j) = 0... if pixels lie in two significantly different parts of the image» (l. 3199-3205). NRGF: «applied only to circles... that lie completely in the corona» (l. 3371); FNRGF: «Only pixels on Sun-centered circles that lie completely in the corona are processed» (l. 3582-3583).
- MGN (Morgan & Druckmüller 2014): cap màscara w; convoluciona tot el domini (l. 306-320).

### Cel i earthshine

- «The sky brightness is removed by measuring and subtracting the intensity observed at the center of the Moon» (Boe 2021, l. 164-172); earthshine de càlcul, 2,5·10⁻¹⁰ I☉.
- El glow dins del disc, reconegut: «The extreme brightness gradient near the lunar edge caused by diffuse light was necessary to be removed» i «I had to write a dedicated program» (2001). 2006 Líbia: detall bo «in the center of the lunar disc where the images do not suffer from diffuse light». Tesi §5.3: el costat on la fotosfera acaba de quedar oculta és més brillant (l. 3330-3335).
- Cap dels papers ni la tesi descriu la composició lunar, el vel dins del disc ni la inserció (grep «earthshine»: 0 a la majoria; 1 a Habbal 2010; 2 a Boe 2021).
- Font externa a Brno: Vuorinen, tse-tools 2026 (https://www.othercomputer.com/blog/2026-08-20-solar-eclipse-tools/): «replaced with a stack of long-exposure images aligned according to the Moon».

### Mesura del PNG web (lector 6, `output/v43_earthshine_20260910/lliurables/vistes/mesura_limbe_lector6/`)

530 mm: transició 10–90 % 1,49 px web ≈ 6 px de sensor (límit del re-mostreig); anell rms 1,3 %; zona no monòtona 0 px; disc a 0,18 de la corona (sRGB); gradient del disc 0,95 R / 0,5 R = 1,18 en codis sRGB (sectors 1,10–1,31), ≈ 1,32 descodificat a lineal; corona neutra (R/G 1,01, B/G 1,00), disc blavós (0,78 / 1,34); contrast dels mars 33 % (400 mm: 62 %). Al 800 mm la Lluna és negre pur.

## 3. El que és INFERIT

**La discrepància entre el paper 2006 i la tesi.** El paper descriu un fotograma de referència curt amb w = −1 i normalització; la tesi, que diu descriure el mateix LDIC de 2006, dona l'eq. 4.15 sense −1 ni divisió i una cadena que comença per les llargues. Ho llegim com dues descripcions de dues parts de l'operador (la tesi, l'ordre de la regressió k/q entre fotogrames; el paper, la tria de la referència lunar): que el −1 no surti a l'eq. 4.15 és silenci, no canvi de versió. Els números de versió de la web no es poden lligar a cap de les dues fórmules; LDIC 6.0 no està documentat.

**Per què pes −1 + referència no fa ni anell ni doble limbe.** Als píxels que a A_j són Lluna, tots els i ≠ j tenen f = 0: el disc és A_j tal qual (o la capa inserida). Als píxels que a j són corona però a i són Lluna, i queda exclòs. Cap valor fosc de Lluna aliena a la corona ni corona aliena dins del disc. Preu: prop del limbe de j hi ha menys fotogrames (més gra, cap biaix). El cas «corona a j amb w_j = 0 i Lluna a tots els altres» deixa el denominador a zero: el paper no ho tracta. El disc de referència, curt, és fosc però NO pla: porta el mateix glow relatiu que qualsevol altre (vegeu §4).

**Per què la convolució parcial no fa halo, i què no cura.** Amb w = 1 dins del disc, la mitjana local barreja corona amb disc ≈ 0 i f − m fabrica un anell clar fora i fosc dins, d'amplada ~σ per escala. Amb w = 0 i divisió per Σ C·w l'anell no es fabrica. El que la tesi NO tracta és el biaix d'un sol costat que queda igualment: el veïnat només exterior contra un gradient radial fort. La nostra cadena ho va mesurar (research/154 l. 7: mitjana d'un sol costat «contra un gradient de ×2 cada 44 px», |d/escala| +27 a 1,00 R☉, banda sense estructura fins a 1,08–1,16). Que a Brno es noti menys s'explicaria pel nucli anisòtrop (tesi eq. 5.1, radial × tangencial) i per una corona interior més suau a 1/250 s; no ho podem quantificar.

**Com deu ser la composició lunar dins de l'LDIC.** Cada fotograma es desplaça per −h(t_i), s'apila el disc amb pesos per valor i s'insereix al compost de corona a l'instant declarat. Alternatives que no podem excloure: alineació per formacions (2001) en lloc del model; un programa a part per al gradient del limbe (2001); inserció i fosa manual a ACC 6.1 («final processing»). Vuorinen descriu el mateix esquema (apilat llarg registrat a la Lluna que substitueix el disc de la referència), sense dir res del vel ni de la fosa.

**Per què amb 1 s a f/5 i el Sol a 7° els surten les maria.** No sabem quants dels 225 fotogrames són d'1 s. El que sí: (a) amb 1 s la Lluna es mou 0,6″ ≈ 0,25 px al seu sensor: cap desenfoc dins de l'exposició (nosaltres 2,2–2,7 px); (b) el registre lunar segueix la Lluna; (c) el contrast final del 33 % contra un earthshine real del 0,36 % del disc (`research/126`) diu que hi ha un realç local fort, no documentat; (d) el disc fosc amaga glow i gra alhora. Que el 400 mm tregui 62 % i el 530 mm 33 % diu que el contrast és una tria.

**Intersecció i earthshine no conviuen ni a Brno.** Al 800 mm (forat = intersecció) el disc és negre pur; al 530 i 400 mm hi ha earthshine.

## 4. Nosaltres avui (V42 F1)

`b2_lluna_v42.py` registra 8 tessel·les sobre la Lluna per efemèride (sol′ = sol + Δlluna − Rm·d(M_c); B amb rotació +8,10′), disc fins a RL + 14 px amb vora de 3 px. `f1_earthshine_v42.py` apila 5 (Sony A 8 s + 2 s, Vixen 10 s; els tres Sony B exclosos per un excés compacte de llum del +30–35 %, 16 σ, origen no identificat) amb pesos per variància inversa, resta un vel (perfil radial fins a 0,975 R + polinomi 2D grau 4 a r ≤ 0,85), relleu ×K només a r ≤ 0,85, disc pla al nivell POWAAAH3 (×2,58 el vel), màscara 1 fins a 453,5 i 0 a 457,5. Instants de la pila: t 18–69 s (corona desplaçada fins a 13,8 px entre el primer i l'últim) sobre un forat de t 15 s. La base té forat = intersecció amb guarda de 2 px per fotograma (research/155 l. 9) i màscara «fora del disc a l'inici». Al PSB les quatre capes F1 són ocultes; el que Pere veu és el POWAAAH3. Jutge LROC +0,540 / +0,681 amb nuls ≤ 0,012 (tres girs de 90°, no una distribució).

⛔ **Deute de registre**: el «< 0,2 px» als mars surt de `fase(z, ref, okm)`, correlació de fase amb la MATEIXA màscara als dos costats, sense control amb desplaçament conegut: la trampa de research/160 §7 (l'E3 «≤ 0,05 px» amb 12 px reals). No és un fet verificat.

| Mesura (lector 6) | Brno 530 | F1 relleu12 (oculta) | POWAAAH3 (visible) |
|---|---|---|---|
| Transició 10–90 % | ≈ 6 px sensor (límit web) | graó de la base 0,6–2,1 px | saturat 446–452 |
| Anell rms (0,96–1,07 R) | 1,3 % | 14,2 % (base sola 2,5 %) | — |
| Zona no monòtona | 0 px | 18 px | — |
| Solc a zero | cap | 4–5 px (452,3–456,3) | màscara R+6, ploma 8 |
| Bony de glow | — | +15–19 % a 0,985 R | vessa 8 px dins del limbe |
| Disc / corona (sRGB) | 0,18 | 0,49 | 0,49 |
| Gradient 0,95/0,5 (lineal) | ≈ 1,32 (sectors 1,10–1,31 sRGB) | 1,01 (pla per construcció); dada 1,31 (sectors 1,23–1,57) | 1,06 / 1,26 |
| Corona R/G · B/G | 1,01 · 1,00 | 1,32 · 0,52 | id. |
| R retallat a 1,00–1,05 R | 1,3 % | 58 % | id. |
| Contrast mars (passa-alt 0,25 R) | 33 % | 11 % (relleu24: 23 %) | — |

**El glow, mesurat a les tessel·les del cau.** El perfil relatiu és el mateix a totes les exposicions i als dos trens: Sony 2 s (f/2,8) i Vixen 10 s (f/5,5) donen 1,23–1,26 a 0,95 R, 1,44–1,58 a 0,97, 1,95–2,15 a 0,985 i 2,1–2,3 a 0,99 R; els 8 s Sony només semblen plans (1,22 a 0,985) perquè la saturació els treu els píxels brillants (r50 431–437). INFERIT: dues òptiques amb el mateix perfil → ala de PSF/difusió, no saturació. L'asimetria és comuna i DERIVA amb l'instant: DSC06984 (t 18) W 1,40 / E 1,25; 572A2984 (t 69) W 1,34 / E 1,35; DSC06996 (t 82, B) W 1,34 / E 1,33, coherent amb la tesi §5.3 (a t 15 l'oest és l'últim cobert). L'apilat E a 0,94–0,985 R és una barreja seleccionada per saturació (DSC06987 hi pesa el 24 % però només hi sobreviuen els seus píxels foscos).

**Cobertura per classe** (radi on la validesa cau sota 50 % / 5 %): Sony 8 s 431–437 / 446–447; Vixen 10 s 449–450 / 452–453; Sony 2 s 452 / 454–456. La fusió (`base_G_v42.npy`) a l'oest té 0 % de dada a 452–456 i 99 % a 458.

Els defectes, per causa:

1. **El solc no és comptabilitat: és una franja sense dada a cap producte.** L'apilat s'acaba a 452–454 per saturació dels llargs (no per cap màscara); la base no entra fins a 457,5 (= 455,5 astromètric + 2 px de guarda). Entre 452,4 i 457,5 no hi ha res. A més, el RL = 453,5 del F1 (limbe fotogràfic de les capes de Pere) va 2 px curt: el limbe mesurat és 455,5 (+0,6 px per fotograma, 155 l. 34); «0,975 R», el taper del relleu i la màscara van 2 px cap endins.
2. **El bony** és la franja 0,975–1,0 R (glow a 2,2× el disc) passada a la dada lineal ×2,58, visible perquè el disc és a 0,49 (Brno 0,18).
3. **El glow asimètric és real i deriva amb l'instant**: la pila (t 18–69) i la corona de la base (t 15) difereixen al limbe un ±5 % del glow segons el sector: un desencaix dins/fora que cap radi no cura.
4. **La corona taronja amb R retallat** és de la BASE (corba/color), no de l'earthshine.
5. Si l'anell negre és al PSB real amb les capes 12/07/06 de Pere a sota: no comprovat.

## 5. Propostes per a la V43

Tres són decisions de Pere, no propostes tècniques: la guarda de la base (0 o 2 px), el nivell disc/corona (0,18 o 0,49) i l'instant del forat (t 15 o el centre de gravetat de la pila d'earthshine).

**0. La franja 452–457,5 px.** Primer, R = 455,5 a tot arreu (F1 inclòs). Després, una de tres, cadascuna una decisió: (a) la màscara de la capa passa a ser la VALIDESA per píxel (no radial) perquè la franja deixi veure la capa de sota (POWAAAH3 o la 12 de Pere), mesurat al PSB real; (b) dada fins a 455,5 amb fotogrames curts (proposta ii); (c) treure la guarda de 2 px de la base (recomposició des d'E2; defensable perquè el dèficit de vora ja és corregit a l'origen i el limbe modelat coincideix a +0,6 px). Sense (c) i sense (b), els 2 px 455,5–457,5 de l'oest només els pot omplir la base. Mesura: perfil al limbe amb zero píxels a 0, anell rms, al PSB.

**(i) La base: no cal refer-la.** La V38 ja equival a l'eq. 3 de CAOSP 2006 (Lluna de cada fotograma exclosa, corona on ho és, disc d'un instant). El que queda per decidir és què omple el disc (la capa apilada) i la guarda. L'opció D de research/155 §5 (Lluna a l'INICI, amb earthshine, i la corona de la franja SE dibuixada per sobre de la vora del disc) continua lícita si es declara; no és la intersecció del 800 mm.

**(ii) Apilat lunar amb més fotogrames — amplia l'inventari ordenat: decisió de Pere.** Primer els Vixen 3×2 s (ja registrats i amb pes mesurat del 14,8 % a la V4, research/127 §8; fora de la V42 per l'ordre «Vixen de 4 o més segons») i els Sony A 3×1 s; els 1 s i 1/2 s només per efemèride (la correlació als mars no passa: σ per píxel ≥ senyal). Els curts són els únics amb dada a 452–456 i sense desenfoc de moviment. Pas previ obligat: refer la mesura de registre als mars amb finestra lliure a totes dues imatges (o Pearson dins del solapament, com `e3f_translacio_sectors.py`) i control: tessel·la desplaçada 5–10 px que retorni 5–10. Pesos per variància mesurada (estimador del walking noise). ⚠️ (ii) no s'avalua sola: a 0,99–1,0 R el que hi ha és glow a 2,2–2,3× el disc, no earthshine (el relleu és a r ≤ 0,85); a la capa F1 la franja va com E × 2,58 i l'anell pujaria a ≈ 5,9× el vel. Només amb el disc a 0,18 (2,3 × 0,18 = 0,41) queda sota la corona amb perfil monòton. Porta del limbe: perfil monòton ±2,5 % per sectors; LROC per bandes només com a guarda que l'interior no empitjora (treballa a r < 0,85 i no veu el limbe); injecció cega a 2–16 px (transferència 0,90–1,10); nul per escombrada d'orientació com al 126; taula V4/V21/V42/V43 amb la mateixa vara. Risc: els curts dilueixen si els pesos no són per S/N; l'excés dels B continua sense causa.

**(iii) El glow dins del disc.** Ja és mesurat (§4). Vel: ajustar-lo al limbe per CLASSE (2 s, 10 s) amb anells de validesa ≥ 95 %, no sobre E (hereta la selecció per sectors); perfil radial fins al radi de cobertura real, polinomi només a ≤ 0,85 R (research/127: ajustar fins al limbe contamina el disc). Declarar el desencaix azimutal dins/fora amb el número i mesurar el glow per fotograma en funció del seu t i apuntament (Sony A / Sony B / Vixen). El nivell disc/corona és decisió de pantalla, DECLARADA, no una cura: amagar per nivell no és curar. El retall en R s'ataca a la base. Mesura: gradient 0,95/0,5 per sector en lineal, anell rms, LROC (no ha de canviar més que els nuls).

**(iv) Filtres: retirada.** La convolució parcial normalitzada amb el forat com a suport absent ERA l'ACHF de cadena de la V29 a la V36, i és el que va saturar les capes al limbe (154 l. 7); la V37 la va substituir pel farcit B / condició de contorn (l'ACHF de cadena farceix a l'entrada i convoluciona sense màscara, 154 l. 25). Tornar a w = 0 no cura res que Brno no pateixi també. Si es prova alguna cosa, és l'extensió RADIAL del nucli al limbe mantenint la condició de contorn de la V37, amb la mètrica del 154 (d/escala per anell), com a capa alternativa oculta i el P05 V38 intacte.

## 6. Preguntes obertes i el que NO sabem

- Què fa el «dedicated program» del 2001 pel gradient del limbe: cap font.
- Com s'insereix i es fon la Lluna (radi, ploma, instant) i què fa ACC 6.1 amb el disc: cap font.
- LDIC 6.0 / Corona 6.0 (2026) no són a la tesi; si hi ha un terme radial de llum difusa o només k/q azimutals, no ho sabem.
- Al 530 mm: quin instant té la Lluna, quants dels 225 fotogrames són d'1 s i quants entren a l'earthshine.
- Si Brno resta un model de vel o només aprofita el disc fosc: el ×1,32 del PNG no ho distingeix.
- L'amplada real del limbe de Brno al sensor (el web acota ≤ 6 px).
- Per què el 400 mm té el doble de contrast de mars que el 530 mm.
- Si l'anell negre és al PSB real amb les capes de Pere a sota.
- L'origen de l'excés compacte de llum dels tres B.
- Cap mesura publicada de Brno amb el Sol a 7–9° i vel gran: els números de precisió del 2009 són simulats i del 2008 (Sol a 22°).

## Objeccions no acceptades

- **fidelitat-fonts, LLEU sobre (iv)** («la convolució parcial amb Σ C·w s'ha d'implementar tant als isotròpics com a l'ACHF»): no s'adopta perquè research/154 l. 7 mesura que aquesta convolució és justament el mecanisme de la saturació al limbe (V29–V36); s'accepta la GREU de fisica-metode, que la retira. El fet (l'ACHF de cadena farceix a l'entrada, 154 l. 25) sí que s'incorpora.
- Cap altra: fisica-metode GREU 2 («màscara on acaba la dada») i normes-projecte MITJÀ («acabar-la a la dada reobre l'anell negre») no es contradiuen: la màscara de validesa per píxel només serveix si a sota hi ha una capa que ompli la franja, i així queda escrit a la proposta 0.
## 7. FET el mateix dia (10-09, tarda–vespre): l'apilat lunar V43 amb TOTES les exposicions dels dos trens, i el limbe net

Ordre de Pere: «mira `Earthshine_V42.psb` a Capes interiors: m'és molt difícil ajuntar l'earthshine amb el limbe per culpa de la brillantor. Valora un apilat d'earthshine sumant exposicions curtes dels dos telescopis, que haurien de comptar més que les llargues vora el limbe, on la càmera saturava. Si té sentit, fes-ho, desatès.» Té sentit i és exactament el principi del LDIC (§2): pes per píxel segons validesa. Eines a `research/tools/v43_earthshine_20260910/`, rebuts a `output/v43_earthshine_20260910/4-rebuts/`, vistes a `…/lliurables/vistes/`.

**Què tenia Pere (`Earthshine_V42.psb`, 9 capes, 17:10):** el POWAAAH3 (Lighten) i la seva `09 1/60 x2` (Lighten) visibles, les nostres quatre capes F1 ocultes. Mesurat al voltant del limbe: el POWAAAH3 puja de 26 a 255 (saturat) entre 0,92 i 1,0 R —un anell blanc gruixut dins del disc—, la `09` comença a 452–456 px a nivell 61–78, la base a 457,5 px entra a 182, i la nostra `V42 lineal` s'acaba a 96 amb la màscara a 453,5: tres nivells diferents al mateix radi. No hi havia res a «ajuntar»: cap capa tenia dada al limbe sense saturar.

**B2-Lluna V43 (`b2_lluna_v43.py`, 88 tessel·les):** la B2-Lluna de la V42 per a TOTS els fotogrames dels dos runs (Sony 21, dels quals 9 A i 12 B; Vixen 67), marge de 40 px fora del limbe (per al glow i la unió amb la base), geometria viva (rotació +8,10′ i correccions a la B). ~3 s per fotograma.

**F2 (`f2_apilat_lunar_v43.py`): l'apilat.** Cada píxel = Σ w·valor / Σ w amb w = validesa del run (0 on satura) × t_exp × g_sensor × pes d'instant, en unitats Vixen (Sony × guany per canal de la F1: 0,311/0,328/0,318). g_sensor = 1/(σ²_ln·t) mesurat a la F1: per segon d'exposició la Sony pesa ×1.88 la Vixen. Apuntament B exclòs (declarat: el fantasma de +30 % de research/160). **Instant declarat T0 = 15 s** (la Lluna de la base): a l'anell (r ≥ 0,93 R, dins i fora) només compten els fotogrames propers (exp(−((t−15)/10)²)), perquè el glow dins del limbe i la corona de fora canvien amb el temps; a l'interior (≤ 0,85 R) compten tots; entremig, fosa. Resultat: **0 píxels del disc sense dada** (a la V42, una franja de 4–5 px). Qui mana on: interior DSC06987 19.0 % · 572A2983 17.1 % · 572A2984 17.1 % · 572A2982 17.1 %; **anell 0,93–1,0 R: DSC06984 69.2 % · DSC06982 10.6 % · DSC06985 7.3 % · 572A2972 4.2 %**; fora del limbe (1,0–1,09 R): DSC06983 36.2 % · 572A2971 21.5 % · 572A2970 12.8 % · DSC06981 6.3 %. N_eff interior 7.5, anell 1.9, fora 3.7; pes de les exposicions < 1 s: interior 7 %, anell 17 %, fora 100 %. Les curtes manen al limbe SOLES, per validesa: no cal cap pes a mà.

⛔ **Registre (lliçó, i rectifica la V42):** la correlació de fase de la F1 («< 0,2 px») amb la MATEIXA màscara als dos costats és CEGA: un control amb DSC06987 desplaçat (+5, −3) px tornava (−0,05, −0,03). I entre dos fotogrames del mateix sensor la Pearson troba el PATRÓ FIX que camina amb la Lluna (research/127 §8), no els mars (Vixen–Vixen donava desplaçaments de 6–10 px, el que la Lluna es mou entre fotogrames). Cura: Pearson per força bruta (±10 px, paràbola subpíxel) del passa-alt 6–24 px dels mars en finestra lliure (r < 0,80 R), **cada fotograma contra l'ALTRE sensor** (Vixen contra DSC06987, Sony contra 572A2983) i tot al marc de 572A2983 pel vector creuat (+1.16, -0.97) px. Controls al rebut: DSC06987 (+5, −3) → recuperat (-4.20, +2.73); 572A2982 (+4, +2) → (-3.35, -1.56) (el 80–90 % de l'amplitud: la resta és el re-mostreig bilineal del control). Aplicat a 8 fotogrames llargs (r ≥ 0,30, |d| > 0,5 px): DSC06984 (+2.5, -1.3), DSC06985 (+1.3, -0.7), DSC06987 (+1.2, -1.0), 572A2978 (+1.1, -0.9), 572A2980 (+0.8, -1.3), 572A2981 (+1.0, -1.1), 572A2984 (-0.2, +0.5), 572A2996 (+0.4, -1.0). Els curts no es toquen: el seu limbe fotogràfic (ajust de cercle, 9 fotogrames) és a (−1,5 ± 1,2, −0,7 ± 1,1) px del model d'efemèride, dR −0,9 ± 0,6: un desplaçament SISTEMÀTIC petit, igual a tots, declarat i no corregit (la base i les capes de Pere van amb el model).

**Jutge LROC (r < 0,85 R, orientació d'efemèride, nuls per 11 girs de 45°/90°):** banda 2–12 px r +0.578 (nuls ≤ 0.017), banda 4–16 r +0.685 (nuls ≤ 0.033); la F1 de la V42 feia +0,540 / +0,681. Ni millor ni pitjor de manera significativa: l'interior ja el tenien els llargs; el que hi guanya és el limbe.

**F2b (`f2b_glow_per_sensor.py`): el glow dins del limbe és el mateix als dos trens.** A l'instant declarat, (G − interior)/corona: Vixen 0,95 R 0.14 %, 0,975 R 0.37 %, 0,99 R 2.89 %, 0,995 R 14.40 %; Sony-A 0.14 / 0.35 / 2.45 / 15.60 %. Dues òptiques (300 mm f/2,8 i VSD90SS f/5,5) amb el mateix perfil: no és la lent, és l'ALA DE LA PSF del limbe (seeing amb el Sol a 9° + difracció) de la cromosfera/corona de just fora, 100× més brillant que el disc. Per això Pere no podia «ajuntar-ho»: sota la corba de to logarítmica de la base (0,22/dècada) un 2,7 % de la corona a 0,99 R surt a 0,42 sRGB quan el disc és a 0,29: un anell clar de 10 px. Brno té el mateix glow (§4, ×1,3 en lineal) i el seu disc puja només un 1 %: el seu disc és a 0,18 de la corona i la seva corba no és la nostra.

**F2c (`f2c_disc_pla_limbe_net.py`): el limbe net.** El glow es modela com a VEL (research/127) fins a 0,995 R —radial + polinomi a ≤ 0,85 R, i de 0,92 R enfora mediana per anell d'1 px i SECTOR de ±10° (l'ala depèn de l'azimut: on fora hi ha la cromosfera és més alta), suavitzat en log— i es substitueix per un NIVELL PLA declarat; el relleu (E − vel)/vel × K només a r ≤ 0,85 R (a 0,85–0,97 R el residu × LROC dona +0.066 amb nul 0.064: no és earthshine demostrat i no s'amplifica), fos a 0 fins a 0,95 R; de 0,95 a 0,995 R disc pla; 0,995–1,0 R fosa a la dada (la vora de la PSF, 2 px); fora, la corona de l'instant. Dos nivells: FOSC (×0,30 el vel → sRGB 0.163, com el disc de Brno, 0,14) i POWAAAH3 (×2.58 → 0.373); K 16.1 / 36.4 per a un contrast sRGB del 12 % (σ 3 px). Cap píxel pintat: el pla és un nivell i un color (mesurat: R/G/B 1.038/1.055/0.852) constants declarats en lloc del vel; relleu, vora i corona són dada.

**F3 (`f3_perfil_limbe_v43.py`): el limbe, amb la mateixa vara (mediana azimutal de la luminància sRGB; el compost = base corba + capa amb la seva màscara):**

| Compost | disc/corona | transició 10–90 % | vora clara fora | solc fosc fora | glow dins | L(0,95)/L(0,5) | contrast mars |
|---|---|---|---|---|---|---|---|
| Brno 530 mm (PNG web, R 106 px; 1 px web ≈ 4 del sensor) | 0.19 | 0.5 px (0.005 R) | +2.1 % | +6.8 % | +1.0 % | 1.17 | 12.8 % |
| V42: base + `Earthshine V42 lineal (corba)` | 0.41 | 13.6 px (0.030 R) | +7.5 % | +26.6 % | +13.4 % | 1.09 | 0.2 % |
| POWAAAH3 de Pere sobre la base | 0.58 | 11.3 px (0.025 R) | +33.0 % | -3.9 % | +84.6 % | 1.21 | 1.2 % |
| V43: base + `HDR lineal (corba)` | 0.40 | 11.3 px (0.025 R) | +7.5 % | -0.6 % | +22.8 % | 1.08 | 0.2 % |
| V43: base + `vel ×0,3 + relleu` (glow ×1 al limbe) | 0.36 | 18.1 px (0.040 R) | +7.5 % | -0.6 % | +30.5 % | 1.83 | 3.3 % |
| **V43: base + `disc pla fosc + relleu · limbe net`** (visible al PSB) | 0.22 | 4.5 px (0.010 R) | +7.5 % | -0.6 % | +0.1 % | 1.01 | 3.5 % |
| V43: base + `disc pla POWAAAH3 + relleu · limbe net` | 0.51 | 4.5 px (0.010 R) | +7.5 % | -0.6 % | +0.2 % | 1.01 | 3.5 % |

La «vora clara fora» del 7,5 % és de la BASE (la cromosfera a 1,0–1,06 R, igual a tots els nostres composts); el «solc fosc» de la V42 (26,6 %) era la franja sense dada; el «glow dins» passa del 13–23 % (V42, HDR lineal) i del 85 % (POWAAAH3) a 0,1 %; la transició de 13,6 a 4,5 px. Brno (web) fa 0,005 R de transició i 1 % de glow: hi som (0,010 R, 0,1 %) dins del que el seu PNG deixa mesurar. El contrast dels mars és decisió de pantalla (Brno 13 % amb aquesta mètrica; nosaltres 3,5 % amb K per al 12 % de l'altra): el K es pot pujar.

**Unió amb la base, mesurada (sRGB G):** capa V43 a 457–462 px 0,770 contra base 0,765; a 462–470, 0,761 contra 0,754; per sectors de 45° al mateix radi (458–461): sis de vuit dins de ±0,01, els dos de l'est (cromosfera) −0,04 i −0,025: la corona de l'instant declarat i la de la base són la mateixa a la vora del forat.

**Lliurat: `Capes interiors/Earthshine_V43.psb`** (fitxer NOU; l'`Earthshine_V42.psb` de Pere no es toca): les seves 9 capes byte a byte (píxels, màscares, modes Lighten, visibilitats) + 6 capes noves a dalt (màscara 1 fins a R 457,5 = vora del forat de la base, 0 a 461,5; dada de píxel fins a R+40): `disc pla fosc + relleu 12 % · limbe net` (VISIBLE), `disc pla POWAAAH3 + relleu`, `vel ×0,3 + relleu` i `nivell POWAAAH3 + relleu` (glow mesurat ×1 al limbe), `HDR lineal (corba)` (el disc tal com el van veure els sensors, limbe sense saturar) i la visible amb `màscara àmplia (R+40)` (la corona de l'instant fora del limbe, per si Pere vol). Publicat el 10-09-2026 a les 18:13: SHA-256 `52ac5cfd90d7b1434eec49274b694b72c19e3159a490a2b3e2f27119b8d025b1`, 1,258,023,582 bytes, Photoshop real `OBRE 10551 px x 7506 px · 15 capes` (15 de 15 capes verificades exactes). Rebut `Earthshine_V43_REBUT.md` al costat del PSB.

**Límits declarats.** (1) El disc de l'apilat és a (−1,6, −0,3) px del centre d'efemèride (ajust de cercle al limbe, rms 1,5 px, 358 azimuts): dins de la màscara (4 px de marge) i de la incertesa del model; no corregit. (2) A 0,95–0,995 R el disc és PLA: el relleu real de les vores del disc (mars vora el limbe) no hi és perquè no el podem separar de l'ala. (3) La corona fora del limbe a la capa és de l'instant T0 ± 10 s (28 fotogrames, N_eff 3.7): més gra que la base. (4) L'apuntament B queda fora sense causa del seu excés de llum. (5) Els controls de registre recuperen el 80–90 % de l'amplitud imposada: el registre val a ±0,5 px, no millor. (6) Cap reducció de soroll; el gra del disc és el que hi ha (variant «gra tal qual» no refeta: el relleu porta σ 3 px, declarat).

**Següent (decisió de Pere):** nivell del disc (fosc com Brno o POWAAAH3), contrast (K) i si la màscara àmplia li serveix per a la unió; si vol l'earthshine de les vores del disc, cal deconvolució de l'ala (fora d'abast avui). Les propostes 0/(i)/(iv) del §5 queden resoltes o retirades per aquest lliurament; la (ii) és feta; la (iii) és la F2c.


## Correcció del mateix vespre (19 h): la vora del disc pla segueix el limbe mesurat per azimut

Pere (crop amb marques verdes al limbe est): «per què es produeixen aquests desajustos?». Mesurat: cap píxel negre ni sense dada; el que hi havia era la RAMPA de la PSF entre el disc pla i la cromosfera allà on la vora fotogràfica de l'apilat cau més enfora del cercle nominal (R 453,5 al centre d'efemèride): el 50 % de la rampa és a 456,3–456,4 px a l'est (a la cromosfera), 452,9 al nord, 453,6 a l'oest; mediana 453.6, de 451.0 a 457.9 px (720 azimuts). Amb la vora al cercle nominal, a l'est quedaven 2–3 px de rampa visibles entre el disc i la cromosfera (la franja verda). Cura (`f2c`): r_limbe(φ) = el 50 % de la rampa mesurat azimut a azimut (suavitzat ±3°), disc pla fins a r_limbe(φ) − 1 px i fosa d'1 px a la dada. (Un primer intent amb la mitjana geomètrica com a llindar queia 1–3 px massa endins i deixava la rampa vista: refusat per la mesura.) Perfil del limbe amb la mateixa vara: transició 2.3 px (0.005 R; Brno 0,005 R), glow dins 0.1 %.

La primera publicació (vora al cercle nominal; SHA-256 `14fc1b75c134405269c85bc517009116c836fd2ae6abfc464a60581ccfec3a1b`) és a `research/tools/v43_earthshine_20260910/staging/Earthshine_V43_vora_cercle_nominal_18h13_20260910.psb` (rebuts a `4-rebuts/primera_publicacio_18h13/`). Fitxer vigent: SHA-256 `52ac5cfd90d7b1434eec49274b694b72c19e3159a490a2b3e2f27119b8d025b1`, 1,258,023,582 bytes, `OBRE 10551 px x 7506 px · 15 capes`, publicat el 2026-09-10T17:19:45.306635+00:00.
