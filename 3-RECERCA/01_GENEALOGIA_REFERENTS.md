# Genealogia dels referents de la fotografia coronal

## Idea central

L'escola Druckmüller és el punt de trobada de quatre tradicions diferents:

1. captura d'alt rang dinàmic;
2. registre i fusió quantitativa;
3. realçament de morfologia coronal;
4. física de la corona i del vent solar.

Cap persona domina sola les quatre. Per entendre «com s'ho fan» cal distingir qui ha aportat:

- instrumentació;
- ephemerides i campanya;
- fotometria;
- algoritmes;
- interpretació física;
- composició artística.

## 1. Genealogia de l'HDR

### Sectors mecànics i filtres òptics

Abans dels sensors digitals, el problema ja era el mateix: la corona interior és molt més brillant que l'exterior.

- Laffineur, Bloch i Bretz van emprar sectors rotatius prop del pla focal.
- Gordon Newkirk i Lee Lacey van construir una càmera amb filtre neutre radial: molta densitat a l'interior i menys a l'exterior.
- L'eclipsi de Bolívia de 1966 va produir una sola exposició que mostrava corona fins aproximadament 4,5 radis solars.

Fonts: [història HAO/NCAR de la càmera Newkirk](https://news.ucar.edu/123881/50-years-ago-ncar-camera-snaps-game-changing-eclipse-picture) i [arxiu fotogràfic HAO](https://www.hao.ucar.edu/hao/history/pictures.html).

### Cambra fosca i composició digital

- Unsharp masking, positiu-negatiu i efecte Sabattier reduïen el gradient i mostraven detall.
- Wendy Carlos i Fred Espenak van traslladar l'art de les màscares a la composició digital en Photoshop.
- L'objectiu de Carlos era perceptiu i artístic; en alguns treballs hi ha reconstrucció o aportacions d'altres fotografies. És una baula essencial de l'HDR, però no una plantilla de producte científic.

Font: [NASA, imatges d'eclipsi de Wendy Carlos i Fred Espenak](https://umbra.nascom.nasa.gov/eclipse/images/eclipse_images.html).

### Salt Druckmüller

Miloslav Druckmüller, Vojtech Rušin i Milan Minarovjech converteixen la composició en un problema explícit:

- calibratge;
- alineació sobre la corona;
- selecció de píxels segons SNR, linealitat i saturació;
- fusió ponderada;
- realçament separat.

El [paper de 2006](https://www.ta3.sk/caosp/Eedition/FullTexts/vol36no3/pp131-148.pdf) cita directament els sectors, Newkirk, la cambra fosca, Koutchmy, Espenak i Minarovjech. És la genealogia reconeguda pels autors, no una reconstrucció especulativa.

## 2. Genealogia del realçament morfològic

### Serge Koutchmy

Koutchmy és probablement el predecessor científic i metodològic més important:

- fotometria coronal des dels anys setanta;
- processament direccional de segon ordre el 1988;
- MadMax/OMC posterior;
- campanyes d'alta resolució;
- separació i models de corona K/F;
- treball amb Laurence November i el CFHT de 3,6 m.

El filtre de 1988 reduïa rang dinàmic i realçava estructures febles amb bona relació senyal-soroll. No s'ha de confondre aquell filtre amb totes les variants posteriors MadMax.

Fonts: [bibliografia Koutchmy](https://robrutten.nl/bibfiles/ads/abstracts/solabs_koutchmy.html) i [reconstrucció tridimensional de l'eclipsi de 1991](https://www.nature.com/articles/360717a0).

### De l'ACHF a MGN

- **ACHF/Corona, Druckmüller:** passa-alt circular adaptatiu, multiescala i no direccional; evita privilegiar els raigs radials.
- **NRGF, Morgan–Habbal–Woo, 2006:** a cada radi resta mitjana azimutal i divideix per desviació estàndard.
- **FNRGF, Hana Druckmüllerová–Morgan–Habbal, 2011:** la normalització passa a ser local en angle mitjançant sèries de Fourier.
- **NAFE, Miloslav Druckmüller, 2013:** equalització adaptativa fuzzy amb control de soroll, especialment aplicada a EUV.
- **MGN, Morgan–Miloslav Druckmüller, 2014:** normalització gaussiana local a diverses escales combinada amb context global.

Fonts primàries:

- [NRGF](https://arxiv.org/abs/astro-ph/0602174)
- [FNRGF](https://doi.org/10.1088/0004-637X/737/2/88)
- [NAFE](https://doi.org/10.1088/0067-0049/207/2/25)
- [MGN](https://arxiv.org/abs/1403.6613)

### Successors actuals

- **WOW — Wavelet-Optimized Whitening:** equalitza informació entre escales, amb tractament d'halos i soroll. [Paper](https://arxiv.org/abs/2212.10134).
- **RHEF — Radial Histogram Equalization Filter, 2025:** equalització per percentils dins d'anells radials, amb implementació oberta. [Paper](https://link.springer.com/article/10.1007/s11207-025-02578-x).
- **Craig DeForest i altres treballs de noise-gating:** recorden que el soroll s'ha de modelar abans d'amplificar estructures febles.

La funció dels mètodes moderns no és imitar un «look» únic, sinó proporcionar controls independents. Si una estructura desapareix quan canvia lleugerament el filtre, no és una detecció robusta.

## 3. Genealogia de la fotometria coronal

### Fonaments

- **Arthur Schuster:** llum polaritzada dispersada en la corona.
- **Marcel Minnaert:** geometria de dispersió Thomson, enfosquiment del limbe i secció eficaç.
- **Baumbach:** densitat electrònica a partir de brillantor d'eclipsi.
- **H. C. van de Hulst:** inversió de brillantor polaritzada a densitat electrònica i separació conceptual entre corona K i F.

Fonts: [van de Hulst, Nature 1949](https://www.nature.com/articles/163024a0) i [revisió NASA de fotometria coronal](https://ntrs.nasa.gov/api/citations/20230015141/downloads/paper1.pdf).

### Tradició moderna

- Koutchmy i Lamy: models de corona F i fotometria.
- Laurence November i Koutchmy: estructura fina calibrada amb l'eclipsi de 1991.
- Richard Woo: estructura de densitat a partir de ràdio i coautor del NRGF.
- Giuliana de Toma, Roberto Bemporad, Huw Morgan i altres: polarimetria i densitat amb sensors moderns.
- Benjamin Boe: topologia quantitativa, línies Fe i física del *freeze-in*.

Un exemple clar que una DSLR pot produir ciència real és el treball de Bemporad: quinze exposicions de 1/4000 a 4 s, selecció per píxel dins del tram lineal i polarimetria per derivar densitat entre aproximadament 1,1 i 3 R☉. [Paper](https://arxiv.org/abs/2010.15005).

## 4. Qui aporta què a la xarxa Druckmüller–Habbal

### Miloslav Druckmüller

Matemàtic aplicat i desenvolupador de:

- planificació experimental;
- control de càmeres;
- calibratge;
- PhaseCorr;
- LDIC;
- ACHF/Corona;
- NAFE;
- MGN, amb Huw Morgan.

La [biografia oficial de VUT](https://www.vut.cz/lide/miloslav-druckmuller-1591/zivotopis) confirma la seva formació matemàtica i el seu treball en processament numèric, gràfica, lògica multivaluada, conjunts difusos i transformacions ortogonals.

No és només un retocador: construeix la capa matemàtica i instrumental que permet que una campanya fotogràfica sigui una mesura.

### Hana Druckmüllerová

Contribucions pròpies:

- registre d'imatges coronals per correlació de fase;
- FNRGF;
- tesi doctoral que integra calibratge, registre i filtres adaptatius;
- desenvolupament de NAFE amb Miloslav;
- treball recent en modelatge de l'espectre de la K-corona.

Fonts:

- [tesi doctoral, 2014](https://www.vut.cz/www_base/zav_prace_soubor_verejne.php?file_id=81241)
- [treball de registre per correlació de fase](https://www.vut.cz/www_base/zav_prace_soubor_verejne.php?file_id=27760)

La seva genealogia directa de realçament és:

`NRGF de Morgan–Habbal–Woo → FNRGF`

### Shadia Habbal

És la gran responsable de la pregunta científica:

- origen i acceleració del vent solar;
- línies prohibides de Fe/Ni;
- distribució de temperatura;
- prominències i cavitats;
- CMEs;
- connexió entre corona baixa, coronògrafs i mesures in situ.

Lidera els **Solar Wind Sherpas** des de 1995. Miloslav aporta la matemàtica i el sistema; Habbal defineix què cal mesurar i per què.

Fonts: [Solar Wind Sherpas](https://project.ifa.hawaii.edu/solarwindsherpas/) i [biografia Habbal](https://people.ifa.hawaii.edu/faculty/bio/shadia-habbal/).

Els seus antecedents conceptuals inclouen:

- Eugene Parker per al vent solar;
- Grotrian i Edlén per identificar el «coronium» com ferro altament ionitzat;
- Minnaert i van de Hulst per a dispersió i densitat.

### Huw Morgan

És el pont directe entre Habbal i Druckmüller:

- doctorat sota Habbal;
- NRGF amb Habbal i Woo;
- FNRGF amb Hana i Habbal;
- MGN amb Miloslav.

No és un usuari secundari, sinó cocreador de dues de les famílies de realçament més influents.

### Benjamin Boe

Representa la fase quantitativa moderna:

- orientació de la corona entre 1 i 6 R☉ mitjançant Rolling Hough Transform;
- topologia magnètica projectada;
- brillantor absoluta de línies Fe;
- *freeze-in*;
- separació cromàtica K/F;
- validació contra coronògrafs i models MHD.

Fonts:

- [topologia de 14 eclipsis](https://arxiv.org/abs/2004.08970)
- [benchmark de models PFSS, 2024](https://arxiv.org/abs/2408.16149)

### Vojtech Rušin i Milan Minarovjech

- tradició observacional eslovaca;
- campanyes;
- morfologia al llarg del cicle solar;
- fotometria, prominències i automatització;
- coautoria del mètode fundacional de 2006.

No hi ha base per atribuir-los individualment PhaseCorr o ACHF, que són aportacions de Druckmüller.

### Fred Espenak

Dues funcions diferents:

- ephemerides, mapes, contactes i taules d'exposició;
- composicions digitals amb Wendy Carlos, citades per Druckmüller.

Font: [guia fotogràfica NASA](https://eclipse.gsfc.nasa.gov/SEhelp/SEphoto.html).

### Jay Pasachoff

- ciència d'escalfament coronal, espectroscòpia i dinàmica;
- campanyes i coordinació internacional;
- coautor amb Leon Golub de *The Solar Corona*;
- col·laborador de Rušin, Minarovjech i Druckmüller.

No és l'autor del pipeline matemàtic. Font: [recerca de Pasachoff a Williams College](https://web.williams.edu/Astronomy/people/jpasachoff/research.html).

### Peter Aniol, Adalbert Ding, Judd Johnson i equip

La qualitat de les campanyes no és només algoritme. Aquests col·laboradors aporten:

- òptica;
- mecànica;
- sistemes de dispar;
- integració;
- calibratge;
- redundància de camp.

L'equip de Brno va moure i reenfocar catorze òptiques durant la campanya mexicana de 2024. Aquesta capacitat operativa és part del resultat.

## 5. Fotògrafs de referència fora de l'escola

### Petr Horálek

Fortaleses:

- composició científica i paisatgística;
- múltiples focals simultànies;
- gran disciplina d'apilat, darks i flats;
- contactes i ambient separats del màster coronal.

Exemples documentats:

- 2024: 83 frames a 200 mm, 1/4000–2 s; 17 a 1100 mm, 1/500–4 s; 26 frames ambientals de 0,5 s a 12 mm. [Descripció](https://www.petrhoralek.com/?p=24033).
- 2023: 38 frames a 200 mm; dues sèries a 1100 mm; seqüència específica de prominències; 3 fps als contactes. [Descripció](https://www.petrhoralek.com/?p=23566).

No publica un pipeline completament reproduïble. És un referent de disseny de producte, disciplina i narrativa visual.

### Juan Carlos Casado

Fortaleses:

- composició multiescala;
- corona, Earthshine, paisatge i contacte;
- treball amb 300/2,8 i focal duplicada;
- seqüències dedicades i composicions visuals.

Exemples:

- 2001: 19 imatges a 300/2,8 + duplicador, 40 d'exterior i 30 d'Earthshine. [Solar Eclipse Newsletter](https://eclipse.gsfc.nasa.gov/SENL/SENL200107C.pdf).
- 2008: 25 frames, 1/1000–1/20, Canon 350D modificada i SCT; composite final de 67 imatges.
- 2019: 112 frames de 1/500 a 1 s i dues interpretacions de processament.

No hi ha un controlador ni una formulació matemàtica pública comparables als de Druckmüller. Cal seguir-lo com a referent visual i de camp, no atribuir-li un pipeline científic no documentat.

## 6. Cronologia essencial

| Any | Baula |
|---:|---|
| 1851 | Berkowski, primera fotografia útil d'un eclipsi total |
| 1860 | De la Rue i Secchi proven l'origen solar de les prominències |
| 1879–1950 | Schuster, Minnaert, Baumbach i van de Hulst: fotometria i densitat |
| 1931–1939 | Lyot: coronògraf |
| 1961 | sectors rotatius |
| 1966 | Newkirk–Lacey: filtre radial òptic |
| 1988 | processament direccional de Koutchmy |
| 1991–1996 | CFHT, November–Koutchmy, alta resolució i fotometria |
| 1995–2000 | Carlos–Espenak i Minarovjech: composició digital |
| 2002–2006 | mètode fundacional Druckmüller–Rušin–Minarovjech |
| 2006 | NRGF |
| 2009 | PhaseCorr generalitzat |
| 2011 | FNRGF i experiment multiespectral de set línies |
| 2013 | NAFE |
| 2014 | MGN |
| 2020 | IPC i topologia quantitativa amb Boe |
| 2023–2025 | WOW, RHEF i nous mètodes oberts |
| 2026 | línies Fe quantitatives fins a 6 R☉ i nova ciència eclipsi–Parker |

## 7. Què hem d'imitar i què no

### Imitar

- pensar la captura i el processament com un sol experiment;
- redundància;
- solapament d'exposicions;
- calibratge;
- registre coronal;
- màster lineal;
- diversos realçaments independents;
- prudència científica;
- publicació de fonts i metadades.

### No imitar cegament

- un aspecte final sense entendre la dada d'entrada;
- paràmetres d'un altre sensor;
- retoc manual impossible d'auditar;
- atribució d'una estructura a física només perquè sembla convincent;
- equip espectral on/off sense recursos per calibrar-lo;
- complexitat que posi en risc les dues cadenes principals.

## Síntesi

Els «referents dels referents» de Druckmüller són:

- Newkirk i la tradició de compressió de rang;
- Koutchmy i la morfologia/fotometria;
- Minnaert i van de Hulst en física de la corona;
- Habbal com a pregunta científica i arquitectura multibanda;
- Morgan com a pont algorítmic;
- Rušin/Minarovjech com a escola observacional;
- Parker, Grotrian i Edlén com a fonaments físics.

La millor síntesi per al projecte és:

> Capturar com un fotometrista, fusionar com Druckmüller, realçar amb diversos mètodes independents i jutjar els detalls com un científic escèptic.
