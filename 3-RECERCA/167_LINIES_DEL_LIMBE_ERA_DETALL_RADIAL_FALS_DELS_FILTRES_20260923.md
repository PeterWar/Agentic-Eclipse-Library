# 167 · Les línies paral·leles al limbe de la vora esquerra: detall radial fals dels filtres (23-09-2026)

**Ordre de Pere:** «anota-ho a la recerca». Això va ser després de confirmar a la V90: «ho has tret! felicitats!».

**Autors:**
- **Pere Guerra:** marques, decisions i validació visual.
- **Claude (Opus 5.5):** diagnosi, proves i cura.

Continua la 165 (el moviment del limbe lunar contamina els filtres).

## 1. El símptoma
Marques de Pere a la vora **esquerra** de la Lluna, en tres versions seguides:
- **V87** (capa «Artefactes V87»): marró, «l'NRGF introdueix artefactes a la corona més interior»; blau clar, «origen desconegut».
- **V88** (capa «Artefactes V88»): blau cel a 104–119°; lila a 121–152°, 211° i 216–229°. Són línies fines paral·leles al limbe a 2–7 px (una de fosca i una de clara, «un limbe doble»), grans foscos i un arc clar.

Pere: «són els últims artefactes de llimb que queden. No en sé trobar una sola capa com a causa».

La V88 (23-09, tarda) havia tret les dents esglaonades de la franja d'un instant (el «cosit de cremallera»), però **aquestes línies no**. Es va dir que estaven corregides i no ho estaven.

## 2. La causa
**Els 16 filtres dibuixaven, als primers ~10 px fora de la Lluna, un detall radial que no existeix a la corona.**

1. **Què hi ha de debò en aquella franja.** No hi ha estructura de corona resoluble. Hi ha:
   - la vora de la Lluna difuminada per l'òptica i per l'atmosfera (el Sol era a 5° d'altura);
   - la vora del domini de dades dels filtres (DMIN ≈ 1–1,8 px), més enllà de la qual els operadors s'han d'inventar la continuació;
   - la continuació de la fosa a4 (un tram pla fins a DMIN + 4 px).

   A la dada d'un instant, el perfil radial de la corona a l'esquerra **puja durant els primers 5–7 px** des del limbe (una vall i després una cresta). Passa a cada fotograma per separat, en el verd matricial i també en la lluminància Y (làmines `M10`, `M11` i `M13` de `4-RESULTATS/v88_marques_pere_20260923/`).
2. **Per què a l'esquerra.** És el costat de C2: el limbe lunar hi és gairebé a sobre del solar, i la corona i la cromosfera hi són més brillants i amb més pendent. Per això la vall i la cresta hi surten més marcades. A dalt, el màxim és a tocar del limbe; a baix i a la dreta, la pujada és curta i queda dins de la fosa.
3. **Per què línies.** Els filtres exageren qualsevol variació de brillantor amb el radi (per això fan sortir l'estructura). Una vall i una cresta paral·leles al limbe esdevenen una línia fosca i una de clara. Allà on variaven al llarg del limbe, en sortien grans.
4. **Per què «cap capa sola».** Els 16 filtres ho feien alhora i als mateixos radis (`LAMINA_M4`, `M5`: la línia és a l'NRGF 41 i 42, l'ACHF 51, la WOW 55 i 56 i el RHEF local 45 i 46). Amagant-ne un, els altres quinze la mantenien.
5. **La claredat** (capa d'ajust de Pere, «Claridad y borrar neblina») la feia més visible, però no n'era la causa.
   - L'efecte de la claredat és un halo de vora de contrast fort: aclareix la Lluna per dins (+0,003..+0,012 de lluminància) i fa un anell fosc (−0,005..−0,008 a 3–20 px).
   - Sense la capa, Pere hi continuava veient les línies (`4-RESULTATS/v89_claredat_20260923`).

## 3. La cura (V90)
**Menys resolució radial dels filtres prop del limbe.** Els filtres es suavitzen només al llarg del radi:
- **Mida:** gaussiana amb σ_r = 4 px fins a 4 px del limbe, que s'apaga amb un smoothstep fins a 0 a 14 px.
- **Com:** en polars (0,05° × 0,25 px) i aplicat com a **diferència** (tornada del suavitzat menys tornada sense suavitzar). Més enllà de 14 px, cada ràster és bit a bit el d'abans (comprovat, 0 DN16).
- **Què desapareix:** les línies paral·leles al limbe, que són detall radial.
- **Què es conserva:** els raigs, que van en la direcció del radi i són estructura real.
- **Què no es toca:** ni la Lluna, ni les màscares, ni cap capa de Pere.

És l'equivalent del que fa Brno, on els filtres no tenen pes arran del limbe (vegeu research/161).

- **Codi:** `3-RECERCA/tools/v90_20260923/a5_radial.py`.
- **Producte:** `1-PHOTOSHOP/V90.psb` (SHA `66311f17…`, 38 capes, porta OBRE).
- **Proves:** P2 (capes de Pere a 0 de diferència), P3 (filtres = càlcul, alfa i màscara de la V88) i P4 (canvis a d ≤ 13,94 px).
- **Resultat** (`4-RESULTATS/v90_20260923/LAMINA_V90_1_marques.png`, compost de Photoshop):
  - desapareixen la línia doble de 136° i les ratlletes de 223°;
  - a 211° marxen els grans (hi queden els punts vermells de la cromosfera de les fotos de Pere);
  - a 112° el ribet clar és molt més suau.

**D'ara endavant, aquest pas va a la recepta dels filtres, després de la fosa a4.**

## 4. El que no era (i es va haver de rectificar)
Totes les hipòtesis es van posar a prova amb una mesura. Dues es van explicar a Pere abans de mesurar-les i es van haver de rectificar: **mesura abans d'explicar.**

1. **«La matriu de color forada el verd de l'Hα».** Era falsa.
   - L'excés de color de la protuberància respecte de la corona del costat té G/R = −0,02 ± 0,07: l'Hα gairebé no toca el verd matricial.
   - Als sectors marcats, la lluminància Y i el verd tenen el mateix perfil.
   - Y/G_m és alt (1,4–2,8) perquè l'Hα és vermella, no perquè el verd baixi.
   - Les proves «lluminància Y» i «només corona» no s'han fet.
2. **«La barreja de temps de la franja d'un instant».** Era falsa: cada fotograma sol ja té la vall, i la combinació amb pes temporal centrat a 18,4 s dona el mateix.
3. **«L'alfa de la Lluna de Pere»** (la 225/258, la Lluna sumada al llarg del temps, que sobresurt fins a 8 px a l'esquerra). Hi contribueix, però **no és un error**: quadra amb la línia vermella de la cromosfera de les seves fotos (+2..+3,5 px).
   - Una alfa «de l'instant» hi obria una franja clara (prova A, pitjor).
   - Confirma la norma de Pere de no tocar mai el limbe.
4. **Qualsevol unió arran del limbe fa una línia nova.** L'ull veu una línia allà on canvia el pendent de la brillantor (bandes de Mach). No van funcionar:
   - l'entrada continuada des de la cresta (prova B);
   - el domini dels filtres des de la Lluna de Pere (prova C);
   - una continuació amb valor i pendent continus;
   - una vora nítida nova de la Lluna a la cromosfera.

   La recomanació «A + B» es va muntar com a V90 i es va descartar abans de lliurar-la (`4-RESULTATS/v90_20260923/descartat_intent1_A_B`).
5. **La claredat.** L'amplia, però no la crea (prova D i prova F amb màscara radial).

## 5. Trampes de mètode
- **Mesura de la curvatura.** L'energia de curvatura (derivada segona radial) a la franja de la vora la domina el mateix salt de la Lluna, i no va veure la millora del suavitzat radial. **Cal jutjar amb vistes a 4:1 a les marques**: primer al compost emulat i després al natiu de Photoshop.
- **Les capes d'ajust.** Si «no és cap capa», s'han de provar també amagant les capes d'ajust, en una còpia renderitzada per Photoshop.
- **Photoshop amb documents de Pere oberts.** Les proves amb Photoshop es fan sobre còpies (obrir, exportar la caixa i tancar sense desar). Si Pere hi té documents sense desar, cal preguntar-li-ho abans.

## 6. Troballes de passada
- **La capa 262 de Pere** («Ajust cua protuberància esquerra», Lluminositat al 96 %) té una màscara de **14/255 a tot el camp Vixen**, segurament una selecció per lluminositat d'una foto curta.
  - Efecte: enfosqueix el camp un 5 % i en marca el rectangle.
  - Cura: Nivells a la màscara, amb el negre a ~20. És de Pere, i està pendent.
- **La cua de la protuberància.** El detall fi (filaments carmesí) hi és als filtres, però la foto 76, en «Aclarir», el substitueix per la seva versió rosa difuminada. Pere la vol resoldre ell.

## 7. Preguntes obertes
- **Quant és instrumental i quant és real** a la pujada dels primers 5–7 px de l'esquerra? Hi entren la PSF i el seeing a 5° d'altura, la topografia lunar i la cromosfera tapada. Una PSF mesurada amb les estrelles de la mateixa sessió en diria el σ.
- **Per al 2027:** a Cadis, el Sol serà a 37° d'altura, i caldria comprovar si la vall arran del limbe hi desapareix.

## Evidència
- **Diagnosi:** `4-RESULTATS/v88_marques_pere_20260923/DIAGNOSI.md`, amb les làmines M1–M17 i els rebuts JSON.
- **Proves:**
  - A–E: `4-RESULTATS/v89_proves_20260923/PROVES.md`. Els PSB són retirats: el lot9 el va buidar Pere i el lot9b és a la Paperera.
  - F: `4-RESULTATS/v89_claredat_20260923/RESULTAT.md`.
  - V90: `4-RESULTATS/v90_20260923/RESULTAT.md`, i l'intent A+B descartat.
- **Lliçons:**
  - skill: `.claude/skills/corregeix-artefactes/references/v90_linies_limbe_suavitzat_radial.md`;
  - traspàs: `.coordination/HANDOFF_2026-09-23_V90.md`.

## 8. Addenda (23-09, nit): la «lent» de la V90 i la V91
**Símptoma:** Pere va marcar en rosa, a la V90 (capa «Artefactes V90»), una «deformació de la corona interior, molt a prop del llimb … com si fos una lent gravitatòria». Era a dalt, a la dreta i a baix (0–32°, 45–98° i 230,5–305°). Mai a l'esquerra.

**Causa:** el suavitzat radial de la V90 anava a tot el voltant. On no hi havia detall radial fals (línies), no en treia: estirava radialment la **textura real** dels primers 14 px, i l'ull hi veu un efecte lupa. La cura d'un defecte, aplicada on no hi ha el defecte, és un defecte nou.

**Cura (V91):** el suavitzat només on hi havia les línies. Les marques de la V88 eren a 104–229° i la lent comença a 230,5°:
- S(θ) = 4 px × smoothstep(θ, 99°, 104°) × (1 − smoothstep(θ, 228°, 232°));
- fora d'aquesta finestra, els filtres són els de la V88 bit a bit;
- codi: `3-RECERCA/tools/v91_20260923/a5c_radial_on_hi_havia_linies.py`;
- producte: `1-PHOTOSHOP/V91.psb`;
- evidència: `4-RESULTATS/v91_20260923/LAMINA_V91_1_lent.png` i `LAMINA_V91_2_linies.png`, del compost de Photoshop a 4:1. La lent marxa a totes les marques roses i les línies no tornen.

**Criteris que no van servir:**
- **L'alçada del limbe lunar sobre el solar.** La idea era que les línies surten on la Lluna tapa just el limbe solar. Però les línies acaben a 229° amb una alçada de ~4 px, i a dalt arriben a 104° amb ~9 px. Aquest criteri encara suavitzava a 230–258°, on hi ha la lent.
- **Un índex d'estructura paral·lela al limbe:** el detall radial fi mitjanat en 3° d'azimut, dividit pel mateix detall sense mitjanar. Val 0,8–1,0 a tot arreu, perquè el domina el salt de la Lluna (és la trampa de la §5).

**Pregunta oberta, que s'afegeix a la §7:** per què les línies es van quedar a 104–229°. Aquesta és la zona més pròxima a C2, on la corona i la cromosfera arran del limbe són més brillants i amb més pendent. Però el límit exacte no el dona cap mesura simple. Una PSF mesurada amb les estrelles hi ajudaria.

## 9. Addenda (24-09, matinada): la lent que quedava a la V91 i la V92
**Símptoma:** Pere, sobre la V91: «encara veig una mica d'efecte lent … més o menys en el mateix lloc que la marca d'Artefactes V90, però més subtil».

**La mesura:** un índex d'estirament radial de la textura, E_d/E_s a 16–30 px dividit pel mateix arran del limbe.
- Es calcula amb pas alt **només en azimut**, i així el salt de la Lluna no el confon (la trampa de la §5).
- Al compost de Photoshop de la V91, a 1–5 px, donava 4,8 a baix i 1,6 a dalt, contra 1 de la corona de més enfora.

**La causa:** la continuació d'a4 (V88), que als ~4–6 px sense dada plena tocant la Lluna copiava el valor al llarg del radi, a tots els filtres. La 56 WOW bilateral, amb més opacitat, n'era la portadora principal.

**La cura (V92):** mirall de la textura a través de la vora de la dada, amb el nivell continuat al llarg de l'arc.
- El nivell no canvia (< 0,0001), i per tant no hi surt cap línia.
- L'estirament a 1–5 px passa de 4,79 a 1,28 a baix i de 1,62 a 0,63 a dalt.
- Les línies de l'esquerra no tornen.
- Codi: `3-RECERCA/tools/v92_20260924/a4m_continuacio_mirall.py`. Diagnosi: `4-RESULTATS/v91_lent_residual_20260923/`.

**Pregunta oberta:** a baix i a la dreta hi queda un estirament suau a 5–14 px (1,6), que ja era a la V88. No el fa la continuació de l'entrada de la WOW (prova c6, B). Pot ser estructura real, com plomalls d'un pol. Per saber-ho, caldria l'angle del nord solar a la imatge.

## 10. Addenda (24-09, nit): la V93
- **El mirall.** Pere va veure el mirall de la continuació de la V92. Qualsevol textura al buit sense dada (els ~4–6 px tocant la Lluna) és inventada i es veu: estirada si és copiada, i com un mirall si és reflectida. **Al buit, només el nivell** (a4v).
- **La textura.** El suavitzat radial de la V90–V92, que curava les línies, s'enduia la textura: la de la WOW bilateral a 2–14 px baixava del 78 % (V88) al 36 %. Les línies són el detall radial **coherent al llarg del limbe**. Traient només aquesta part, amb un arc de 6 px, les línies marxen igual (vist a 8:1) i la textura torna al 46 % (a5d).
- **Pregunta oberta:** més enllà de 9 px, la textura de la WOW ja és baixa a la V88. És el blanqueig de la WOW arran del limbe brillant.

Codi: `3-RECERCA/tools/v93_20260924/`. Informe: `4-RESULTATS/v93_20260924/RESULTAT.md`.
