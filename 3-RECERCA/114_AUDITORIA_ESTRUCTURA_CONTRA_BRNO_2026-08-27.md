# 114 · Auditoria d'estructura contra els composts de Brno (27-08-2026)

**Encàrrec de Pere**: comparar l'**estructura** de la nostra corona (no el color)
amb la de les imatges finals de l'equip Druckmüller del mateix eclipsi, i buscar
defectes nostres que se'ns hagin passat per alt, sobretot a la corona interior,
tocant el llimbe lunar. Eines a `research/tools/auditoria_estructura/`.

## 0. El resum

⏭️ **La nostra estructura resisteix la comparació.** Amb els quatre composts de
Brno com a jutge extern i el seu propi acord mutu com a control:

| escala angular | Brno×Brno (control) | el nostre PASSA_ALT | RADIAL | MGN | NRGF | compost cru |
|---|---|---|---|---|---|---|
| 12° (m 13–30) | 0,987 | 0,933 | 0,935 | **0,957** | 0,904 | 0,886 |
| 4,5° (m 31–80) | 0,976 | **0,943** | **0,945** | 0,929 | 0,878 | 0,843 |
| 1,8° (m 81–200) | 0,961 | 0,894 | 0,899 | 0,853 | 0,847 | 0,850 |
| 0,7° (m 201–500) | 0,761 | 0,647 | 0,692 | 0,561 | 0,626 | 0,718 |

De 1,15 a 2,40 R☉, contra el compost de 800 mm. ⏭️ **Les capes de detall NO
inventen res**: a 4,5° i 1,8° hi ha estructura real, i és el que Pere mira.
La forma de gran escala (m ≤ 2) va de **0,91 a 0,99** d'1,08 a 2,2 R☉.

⛔ **La major part del que semblava un defecte era MEU.** Sis errors de mètode,
tots documentats a §5; el gros és el §5.4, que sol feia baixar l'acord fi de
0,94 a 0,38 i em va portar a punt d'escriure que el nostre detall era inventat.

## 1. Com es compara estructura sense comparar color

Els quatre composts de Brno es registren al **nostre** llenç (Sol al centre per
efemèride, nord amunt) i cada anell es normalitza als dos costats restant-li la
mediana azimutal i dividint per la MAD. Amb això **qualsevol corba de to
monòtona i qualsevol guany desapareixen** i queda la forma. La mètrica és la
correlació de Pearson anell a anell, que a més és invariant a qualsevol
transformació afí local.

**El control mana**: cap nivell de correlació no vol dir res tot sol. El sostre
és **Brno contra Brno**, mesurat als **mateixos anells, el mateix arc i la
mateixa resolució**. ⚠️ És un sostre, no un terra just: els quatre surten del
mateix equip i del mateix pipeline, i part del seu 0,98 és pipeline compartit.

**Registre.** Quatre paràmetres (centre, escala, gir) per imatge. Surt:

| | gir | R_lluna/R☉ del seu disc | Sol − Lluna |
|---|---|---|---|
| 800 mm Trigaza | +5,36° | 1,007 | 0,064 R☉ |
| 200 mm DHS | +2,78° | 1,024 | 0,056 R☉ |
| 400 mm DHS | +3,14° | 1,028 | 0,050 R☉ |
| 530 mm DHS | −0,14° | 1,027 | 0,070 R☉ |

⏭️ El desplaçament Sol−Lluna surt **coherent als quatre mesurats per separat**
(0,050–0,070 R☉, sempre la mateixa direcció) i és menor que l'excursió lunar de
la totalitat (0,065 R☉): el seu disc lunar és d'**un instant** a prop d'un
extrem, com diu `research/105`. I el seu disc pintat és **més petit que la
Lluna de veritat** (1,007–1,028 contra 1,0338): per això ancorar-lo a la física
va sortir malament (§5.4).

## 2. El que PASSA

1. **Geometria.** El nostre centre, escala de placa i angle de posició són
   consistents amb quatre productes independents del mateix eclipsi.
2. **Forma de gran escala** (m ≤ 2, trets de 180° o més): 0,909 a 1,08 R☉,
   0,948 a 1,11, 0,97–0,99 d'1,2 a 1,9. Control 0,94–0,999.
3. **Detall fi**: taula del §0. A 4,5° el passa-alt fa **0,943** amb un control
   de 0,976.
4. **Tancament HDR píxel a píxel**: el quocient compost/fotograma solt és
   constant dins de **±1–3 %** de dalt a baix de la brillantor, als tres
   fotogrames provats i sobre 690.000–790.000 píxels. El compost **no**
   amplifica els trets brillants.
5. **El bony de θ ≈ 133°, r ≈ 1,07 R☉ és REAL.** Val ×4,0–5,8 els controls del
   mateix anell a **tots els 34 fotogrames no saturats**, dels dos extrems de la
   totalitat. És una protuberància, i cau justament on Brno hi té el disc lunar,
   o sigui que ells no la poden ni confirmar ni desmentir.
6. **La guarda de la màscara lunar (2 px) BASTA**, i ara està mesurada: amb la
   Lluna de sonda —llisca 28,5 px, o sigui que un mateix píxel del llenç és a
   distàncies molt diferents del limbe segons el fotograma—, el quocient
   compost/fotograma contra la distància al limbe és **pla dins del ±1,5 %**, i
   aquest ±1,5 % és sobretot la tendència radial.
7. **Pedestal residual −0,5 DN** sobre 512 restats. El −7…−10 % de l'asímptota
   entre parells d'exposicions és el desfasament conegut entre temps nominals i
   reals (`research/99`), que la coherència ja absorbeix com a guany.

## 3. El que queda obert

⏭️ **Per sota d'1,12 R☉ l'acord es degrada**, de ~0,12 de dèficit a fora fins a
~0,25 a 1,05–1,08 (a totes les escales; a m ≤ 2 el dèficit és 0,075–0,095).

**No és soroll nostre**: dos fotogrames independents separats 60 s es posen
d'acord al **0,99–0,998** allà mateix. És sistemàtic.

Hipòtesis provades i **descartades**, cadascuna amb la seva mesura:

| hipòtesi | prova | resultat |
|---|---|---|
| guarda de la màscara lunar curta | la Lluna de sonda, ±1,5 % | descartada |
| el compost amplifica els brillants | tancament píxel a píxel, ±1–3 % | descartada |
| un tret brillant fabricat | el bony a 34 fotogrames | és real |
| llum difusa de l'instrument | `ours − α·(ours ⊛ K_σ)`, jutge retingut | +0,006 sobre 0,25: refusada |
| soroll | dos fotogrames independents | 0,99 |
| pedestal residual | parells d'exposicions | −0,5 DN |

⚠️ Amb aquestes dades no es pot decidir si el que queda és nostre o és el
tractament de la seva corona interior (el seu disc lunar hi és a tocar).
**Ho desbloqueja el tren de la Sony**, exactament com deia `research/113` §5.

## 4. Una troballa nova sobre l'estriat del `research/113`

La muntura va derivar **27 px** durant la totalitat, o sigui que hi ha parelles
de fotogrames separades d'1,6 a 21,7 px **al sensor** però al mateix lloc del
cel. Els quatre fotogrames de 0,5 s donen sis parelles i és un experiment
complet amb la dada que ja hi ha:

| Δsensor | 12° | 4,5° | 1,8° | **0,7°** |
|---|---|---|---|---|
| 1,64 px | 0,998 | 0,991 | 0,916 | **0,530** |
| 5,09 px | 0,996 | 0,986 | 0,867 | **0,171** |
| 21,74 px | 0,997 | 0,984 | 0,850 | **0,293** |

⏭️ **De 12° a 1,8° la correlació NO depèn del desplaçament al sensor: aquella
estructura va enganxada al CEL i és real.** ⛔ **A 0,7° (8 px) sí que cau**, i
això és la família de λ ≈ 4,1 px que Pere va marcar: queda **mesurada com a
component fix al sensor**, que és el que el `113` no podia decidir. La família
de λ ≈ 51 px (≈ 4,5°) **no** és fixa al sensor.

## 5. Els sis errors de mètode que hi vaig cometre

Es documenten perquè tots sis produïen un «defecte» que no existia, i quatre
haurien passat qualsevol revisió interna.

**5.1 Correlacionar contra un disc negre.** A 1,04–1,09 R☉ l'anell de Brno és
mig **disc lunar pintat** (el seu no va centrat al Sol i arriba fins a 1,098
R☉). La dispersió azimutal se'n va a zero i en sortia una **anticorrelació de
−0,29** que no era cap mesura. Cura: `mascara_brno`.

**5.2 Un optimitzador aturat que sembla una mesura.** Nelder-Mead arrencat de
zeros fa passos de 0,00025: el centre del 800 mm «va sortir» desplaçat 0,00 px.
Un paràmetre que no s'ha mogut no és un resultat. Cura: símplex inicial explícit.

**5.3 FFT sobre un anell amb forats.** Omplir el forat de zeros i filtrar fa
**fuita de la vora**, i la fuita és **idèntica** entre dues imatges de Brno
—tenen el mateix contingut— i **diferent** entre les seves i la nostra: inflava
el control i desinflava el nostre alhora. El senyal d'alarma va ser que el radi
«dolent» **es movia quan movia la guarda**. Cura: mínims quadrats sobre l'arc
vàlid (`escales3.py`), i el dèficit es queda clavat al radi.

**5.4 Ajustar un paràmetre amb una dada que no el constreny.** El registre es va
fer maximitzant la correlació de l'estructura sencera, que la manen els
harmònics baixos; amb streamers radials **l'escala hi és gairebé lliure** i va
sortir amb un ±1,5 % de dispersió. El vaig ancorar a la física
(R_lluna/R☉ = 1,0338) creient que era prudent, però **el seu disc pintat no és
la Lluna de veritat** i l'ancoratge va arrossegar l'error. Jutjant amb la banda
m = 13–80 apareix un òptim net a **×1,06**, i l'acord fi puja de **0,383 a
0,589**; amb el registre refet del tot, de **0,38 a 0,94**. ⛔ **Amb el registre
dolent hauria escrit que el nostre detall fi és inventat.** Validació
fora-de-mostra: ajustat a 1,2–1,8 R☉ i jutjat a **1,8–2,4 R☉**, on la correlació
puja de 0,83 a 0,87–0,90 als quatre.

**5.5 Comparar obertures diferents.** El bony deia ×12 al compost i ×4,4 als
fotogrames: eren 4,5 px contra 9 px de radi.

**5.6 Encalaixar un quocient pel seu propi denominador.** Binar `llarg/curt`
per `curt` esbiaixa els calaixos fluixos cap amunt i fabrica una no-linealitat.

## 6. Què s'ha canviat al codi

1. **Porta nova F3.2, `tancament_hdr_brillantor`** (`comu.py`, connectada a
   `f3.py`). La porta de tancament que hi havia compara **medianes d'anell**, i
   una mediana no pot veure un error que depengui del **nivell** del píxel —que
   és exactament la forma d'un defecte de fusió HDR, perquè la frontera entre
   exposicions és una **isofota**, o sigui que viu a un nivell i no a un radi—.
   La nova compara els **percentils** del compost amb els del fotograma solt
   dins de cada anell. Calibrada amb la mesura píxel a píxel (±1–3 %), llindar
   al 8 % sobre el sistemàtic. Al run vigent: **sistemàtic 2,02 %, PASSA**.
2. **`GUARDA_LLUNA_PX` documentada amb la seva mesura** (`f2.py`): el 2,0 era
   una suposició escrita com si fos una mesura.

## 7. Reproduir-ho

```bash
cd "research/tools/auditoria_estructura"
~/.venvs/eines-ia-py312/bin/python registra.py      # registre gruixut
~/.venvs/eines-ia-py312/bin/python registra2.py     # el BO, jutjat a escala fina
~/.venvs/eines-ia-py312/bin/python detall3.py       # la taula del §0
~/.venvs/eines-ia-py312/bin/python escales3.py      # corona interior
~/.venvs/eines-ia-py312/bin/python fix_al_cel.py    # cel contra sensor (§4)
~/.venvs/eines-ia-py312/bin/python vistes_auditoria.py
```

Vistes a `~/Desktop/Eclipse determinista/2-OUTPUT/AUDITORIA_ESTRUCTURA/`.

## 8. «I si Brno s'equivoca, ho propaguem?» (pregunta de Pere, 27-08)

**A l'auditoria, no hi ha propagació possible.** Brno hi va fer de **jutge**,
no de font: cap píxel ni cap paràmetre seu no ha entrat al producte, i l'única
correcció que hauria pujat l'acord amb ells —el model de halo— es va **refusar**
(+0,006 sobre un dèficit de 0,25). Un jutge que et contradiu et pot dir **on
mirar**, mai **què escriure**.

**El que protegeix de debò és que l'estructura està verificada DUES vegades, i
una cama no els coneix:**

| ho diu | prova | a 4,5° |
|---|---|---|
| la nostra dada | dos fotogrames separats 60 s | **0,984** |
| Brno | quatre composts seus | **0,943** |

Si el seu ACHF fabriqués textura, la primera cama continuaria dempeus.

**On sí que en depenem** (grep exhaustiu al codi viu de la cadena):

- **número**: la corba de to (pendent 0,22/dècada, àncora 0,74) es va triar dins
  la banda mesurada als seus quatre composts (0,202–0,240; cim 0,72–0,76). És
  **presentació**, està **declarada** al rebut i està **acotada per la maqueta
  de Pere** (0,166) i per `estira_log` (0,524). Canviar-la és canviar un número.
- **convenció**: la capa **08 CORONA NEUTRA**. Viatja **al costat de la 07**,
  que surt del nostre model d'extinció: la diferència entre les dues és el
  residu que l'extinció no explica, i és **visible, no amagada**.
- **mètode**: LDIC, croma a baixa freqüència, cel al terra, màscara lunar per
  fotograma. Són mètodes, i cadascun té la seva porta sobre la **nostra** dada.

**No** en depenen: pedestal, saturació, flat, efemèride, registre, coherència,
cel per color, matriu de color, model d'extinció i totes les portes.

⚠️ **Tres cauteles:**

1. **Els seus quatre composts NO són quatre jutges independents**: mateix equip,
   mateix pipeline, i tres (les DHS) probablement la mateixa dada. «Brno×Brno»
   és un **sostre**, no un control independent.
2. Allà on discrepem —r < 1,12 R☉— **no ens hi hem acostat**: queda obert.
3. El jutge independent de veritat és **el tren de la Sony**.

⏭️ **Cura**: `comu.PROCEDENCIA` i una secció «D'on ve cada cosa» al rebut de
**cada run**, perquè la dependència quedi auditable sola.
