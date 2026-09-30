# 97 · Les dues decisions del 23-08: la via de la foto, i el pilot amb la Vixen

**23 d'agost de 2026, tarda.** Document canònic. Recull les **dues decisions que
Pere ha pres** i el raonament que hi porta, incloent-hi el contrast amb Codex i
amb cinc llinatges externs. Substitueix qualsevol lectura anterior sobre com
s'ha de reestructurar el projecte.

Companys: `research/96` (el salt de muntura i la lectura dels papers de Brno),
`research/95` (artefactes del pas alt i la norma del rectangle), i el contracte
de fases a `.coordination/HANDOFF_2026-08-23_REESTRUCTURACIO_PER_FASES.md`.

---

## 1 · LES DUES DECISIONS

### D1 · Es va per la via de la **FOTO**, ajuntant els dos telescopis

Es clona el flux de Druckmüller tal com el fa per a una **imatge**: calibrar →
registrar → **compondre (LDIC)** → realçar, amb els dos trens dins d'una sola
composició i `k(φ), q(φ)` amb tota la llibertat.

⚠️ **I això té un preu que s'accepta conscientment.** Fusionar els dos trens amb
60 segments angulars **gasta l'única prova externa que teníem**. Mesurat: passar
de 4 a 120 paràmetres millora el residu **dins** del domini d'ajust (0,444 →
0,297 %) i l'**empitjora fora** (1,33 → 1,76 % a 6–8 R☉). Això no és calibratge,
és absorció, i és exactament el que fa que la foto surti bé.

⛔ **Conseqüència que ha de constar sempre: el producte fusionat NO és una
mesura.** Cap número fotomètric que en surti no es pot presentar com a validat
per l'acord entre trens, perquè l'acord s'hi ha imposat. Si algun dia es vol la
mesura, es fa **a part**, amb dos mestres independents (§3).

**Per què és una decisió defensable i no una rendició.** El propi grup de Brno
fa exactament això per a les seves imatges —1994 amb dues expedicions, 1995 amb
focals 6×, 2023 amb 199 fotogrames de 200 mm més el de 1000 mm— i **no** ho fa
quan publica ciència: Boe, Habbal i Druckmüller 2020 **eliminen tot el camp ample
per sota de 2 R☉**, i a Boe et al. 2021 els dos instruments ni es fusionen.
**Seguir Druckmüller bé vol dir tenir dos productes, i avui es tria fer-ne un.**

### D2 · Es fa un **pilot d'una sola tirada, des de zero, amb la Vixen**

No es comença per la fase 0 amb tot el material. Es fa una passada **d'extrem a
extrem amb un sol tren**, la Vixen, al **llenç comú**, amb tots els rebuts.

**Motiu, i és aritmètic:** només el 23-08 es van trobar **cinc coses** que
haurien obligat a refer feina —l'orientació del llenç, la contaminació de
`.apparent()`, que la porta E es podia falsejar, que Photoshop no calcula
`Σ(wI)/Σw`, i el «0,662″ al limbe» mal etiquetat. A aquest ritme, comprometre's
amb una passada sencera surt car; un pilot destapa els mateixos problemes a una
fracció del cost.

---

## 2 · QUÈ QUEDA VIU I QUÈ QUEDA AJORNAT AMB LA VIA DE LA FOTO

| | estat amb D1 |
|---|---|
| ordre de fases 0→1→2→3 + rebuts | **viu**, tal com el contracte el descriu |
| llenç comú nord amunt, escala fina | **viu** |
| LDIC com a una sola suma ponderada | **viu**, i és el nucli |
| mapes de pes editables per Pere a Photoshop | **viu**, i és ortodox (Brno els pinta a mà) |
| norma del rectangle als filtres | **viva** |
| comprovacions E, F i G | **vives**, amb la salvetat de §4 |
| **camp d'extinció sense calibrar** | **ajornat**: amb `k(φ), q(φ)` lliures, s'absorbeix. ⛔ Però continua invalidant qualsevol número fotomètric absolut |
| **dispersió cromàtica, equació de magnitud, mapa de distorsió** | **ajornats**: són sistemàtics de la mesura, no de la foto |
| **polarització de la corona K** (~50 %, trens girats 33°) | **ajornada** però ⚠️ **`k(φ)` se l'empassarà**: és part del que farà que la foto lligui, i per tant part del que impedeix presentar-la com a mesura |
| **la deflexió gravitatòria** | **fora d'aquest camí.** El pla de detecció és el 2027 (`research/77`) |

---

## 3 · SI ALGUN DIA ES VOL LA MESURA, AIXÒ ÉS EL QUE CAL

No s'hi treballa ara, però es deixa escrit perquè no es perdi:

1. **catàleg SENSE deflexió.** ⛔⛔ `.apparent()` de Skyfield **ja aplica la
   deflexió del Sol** —mesurat: el 99,5 % a 1,5 R☉ i el 99,9 % a 15 R☉— i
   `cat2.py` el fa servir. **El residu de placa no la pot contenir per
   construcció.** És una línia de codi i invalida qualsevol número anterior.
2. **pla tangent aparent a λ declarada** i **color per estrella**.
3. ⛔ **cap terme radial a la placa**: el radial i el senyal 1/r són tots dos
   funcions suaus del radi i es confonen.
4. **fotograma a fotograma**, mai sobre l'apilat: un registre per semblança sobre
   fotogrames separats 100 s deixa **0,561″ rms**, que és **2,67× el senyal a
   l'estrella mediana** (0,210″ a 8,33 R☉).
5. **dos mestres independents** i que concordin.
6. **pressupost d'error mesurat**: traça de 2,92 px als 10,3 s, equació de
   magnitud, mapa de distorsió, i T/P/H **mesurades** (avui `cat2.py` les té com
   a hipòtesi).

⚠️ **I una expectativa honesta**: amb σ(ε) = **0,845** al model que es fa servir
de veritat (`radial=True`; el 0,53 que s'ha citat correspon al model de
similitud), el 2026 **no arribarà a ser una detecció**. El que sí que pot fer, i
és el que val, és **mesurar el pressupost d'error** perquè el 2027 es dissenyi
amb números.

---

## 4 · EL QUE EL CONTRAST DEL 23-08 VA CANVIAR

Contrastat amb **Codex** (pel pont) i amb **cinc llinatges externs** via
OpenRouter —xAI, Moonshot, DeepSeek, Google i Meta, tots distints d'Anthropic i
OpenAI. Cost 0,244 USD. Cap protecció no es va rebaixar: `data_collection=deny`
es va mantenir i el ZDR que Pere autoritzava no va caldre.

**Grok 4.6** va donar el contrast útil; Kimi i DeepSeek van abocar el raonament
sense arribar a resposta, Gemini flash es va tallar i Llama va fer una revisió
genèrica. Dues aportacions es van salvar igualment: **Kimi va derivar pel seu
compte el mateix resultat del quincunx** i va marcar la mateixa incoherència de
la taula R/B, i **Llama va convergir independentment** cap a la validació
creuada.

Quatre coses que en van sortir i que ja són al contracte:

1. ⛔ **El «0,662″ al limbe» era fals.** És HIP 46345 a **2,646 R☉**; al limbe
   val **1,752″**. La comparació que decideix és amb l'estrella **mediana**, i
   allà el residu és **2,67×** el senyal, no 0,85×.
2. ⛔⛔ **La porta E es podia falsejar.** Uns `k(φ), q(φ)` lliures, amb 60
   segments, **poden fabricar** el perfil monòton que E comprova. E s'ha
   d'avaluar **abans** d'aplicar `k, q`, o sobre un producte on estiguin
   **congelats i declarats**, mai sobre el mateix ajust que els ha produït.
3. **El «< 10⁻³» no estava definit**: cal declarar-lo **relatiu** (la corona té
   10⁶ de rang dinàmic) i congelar **l'ordre** i **les iteracions**, perquè
   `k, q` s'ajusten contra el que ja s'ha compost.
4. **Sis sistemàtics que faltaven**, llistats a §1 bis del contracte.

I dues coses de Codex que també hi són: **apuntament i temps estaven
perfectament confosos** (el grup desplaçat és l'anterior, 42 s abans) i **el
llenç era massa petit** — encara que la causa que ni ell ni jo havíem vist és que
**amb el nord amunt el camp és vertical**.

---

## 5 · L'ESTAT DEL CONEIXEMENT QUE EL PILOT HEREDA

Tot això està mesurat i no s'ha de tornar a discutir:

- **el camp de la Sony va caure 750 px** a mig de la totalitat i són **dos
  apuntaments** (`research/96`)
- **el flat de la Sony està validat per tres vies**: prediu el quocient entre
  apuntaments amb coeficient **+1,019** i R² **0,981**; només el **component
  radial** (el 2D porta la pols i un pla que falsificaria −0,0145 mag/X)
- **el pedestal real és 511–512 pla**; el negre de metadada de libraw és fals
- **cap dels dos trens no està submostrejat en luminància** (2,59 i 2,70 px de
  FWHM); el drizzle és per al **color**, i el verd va en **quincunx**
- **el «submostrejat 1,7×» de `research/75` §2.3 no es reprodueix**
- **la Lluna es mou 61,24″ = 28,5 px respecte del Sol** en la totalitat: la
  corona i l'earthshine **no comparteixen alineació**
- **la deriva de muntura+refracció** val 0,610 ″/s i deixa **2,92 px de traça**
  dins d'una pose de 10,3 s
