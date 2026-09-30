# 122 · CapesTotalsV19: la segona ronda de halos — la referència enverinada i la fosa que pintava

> ⚠️ **Estat (28-08, vespre): el PSB de la V19 NO es va arribar a escriure** —
> la sessió va morir a mig construir-lo (cap fitxer parcial al disc). El
> diagnòstic (§2), el disseny (§3), les caçades (§4) i les portes a 1/4 (§5)
> són mesurats i vàlids; el §6 descriu el fitxer que S'HAVIA de fer. Abans que
> es reconstruís, **Pere va resoldre els halos a mà amb un desenfoc radial
> zoom + màscara** (`V18-DesenfocRadialZoom.psb`), un mètode més fort que
> aquest disseny; l'estudi i la formalització són al `research/123`.

**28 d'agost de 2026, tarda-vespre.** Pere ha re-desat `CapesTotalsV18.psb`
(17:07, 4,21 GB) amb una segona ronda de marques: **VERD = halos de
lluminància, TARONJA = halos de to de color**, pintades sobre una còpia de la
capa Sony (el seu save no té capa HALOS: té la capa Sony duplicada, i els
traços són la diferència entre les dues còpies — 3,38 M px, classificats per
la DIRECCIÓ del tint: 2,53 M verds i 0,85 M taronges, zero sense classificar).

## 1. On són les marques

| família | regions | on |
|---|---|---|
| VERD | 6 | dues grosses a **5,6-6,5 R☉** (az +98°, +113°), quatre a 3,5-5,4 |
| TARONJA | 2 | **5,3-6,6 R☉** (az −101°, +5°) |

⛔ **Totes les marques exteriors viuen exactament a la finestra de fosa de la
V18** (correcció plena ≤5,5 → res a 7,0). No és casualitat: són la fosa.

## 2. El diagnòstic, mesurat (les DUES famílies eren nostres, de la V18)

**2.1 Els verds grossos: la referència Vixen estava enverinada.** El fit del
ρ de la V18 anava fins a 9,7 R☉ amb un filtre que només exigia α>0,99 i
V>0,02. Però la vora del mosaic Vixen porta **px saturats a 1,0000, zeros i un
rolloff fosc** (a az +98°, V_G fa 0,35 → 0,296 → 0,272 → 1,0000 → 0,0000 entre
5,4 i 6,6 R☉). El fit se'ls va menjar i **ρG feia un bony fins a 1,165 a
6,1-6,4 R☉** — al compost, un arc de +16-25 % de lluminància en zona de Sony
pura. **El halo ERA la correcció.** Mesurat sector a sector: la referència
sana s'acaba a **r = 5,0 al pitjor sector** (az +97,5°; el quadrant
+67°..+127° i el −97°..−52° moren entre 5,0 i 5,7; la resta aguanta fins a
7,2-7,5).

**2.2 Els taronges: la fosa per canal pintava un viratge de to.** La finestra
declarada de la V18 fonia ρ→1 entre 5,5 i 7,0 **per canal**: ρR/ρG passa de
0,85 a 1,00 en 1,2 R☉ = **un viratge de R/G del 15 % (12 %/R☉)** que l'ull
llegeix com un arc taronja. Als dos sectors marcats, la variació total en
excés del perfil R/G (Σ|Δ| − |net|, que val 0 per a un perfil monòton) era
0,067-0,112. **La fosa ERA el halo.**

**2.3 Els verds interiors: residus que k≤2 no podia seguir** (mismatch ±2-6 %
amb estructura azimutal de ~25-60°).

**2.4 I dues marques són REALS (són al Vixen).** Contrast local amb control
aparellat per radi, al Vixen sol: az +161° (r 3,6-4,1) **G +3,2 %, R/G
+0,021** i az +113,5° (r 4,4-5,2) **G −3,1 %** — la taca brillant-vermella i
la fosca són **a la referència** (corona/cel reals). La cura NO les ha de
tocar, i no les toca: la V19 les segueix (+3,1 %/−2,2 %).

## 3. La cura de la V19 (tres decisions, totes per construcció)

1. **Referència robusta**: el fit només menja px amb α>0,995, tots els canals
   Vixen dins (0,01-0,85) i **r ≤ 4,9** (0,1 per sota del pitjor sector sa);
   **mediana** per cel·la (100→40 calaixos × 24 sectors), no mitjana.
2. **Cap fosa de la G: retenció.** Més enllà de l'últim calaix (4,86 R☉), ρ
   queda **radialment constant per azimut**. Cap gradient radial nou = cap
   arc possible. El camp llunyà canvia de nivell (declarat: mediana ×0,896,
   p1-p99 [0,86-1,10]) però hi canvia suau, i **hereta el patró azimutal del
   Vixen** (correlació 0,94 amb el Vixen a 4,4-4,8): «estèticament ha de
   quedar com la imatge del Vixen» (Pere, 28-08).
3. **El croma retingut es fon cap a un to uniforme en 1,5 R☉** (~1,6 %/R☉,
   set vegades més suau que la fosa que pintava els taronges): l'error
   azimutal de croma del fit no es queda imprès al cel llunyà.
   I **k≤4** (λ ≥ 90°): segueix els residus interiors sense poder perseguir
   la costura entre apuntaments.

## 4. Les dues caçades d'aquesta ronda (transparència)

1. **r_stop VARIABLE per azimut** (fit fins al radi sa de cada sector):
   semblava millor — més referència on n'hi ha — i les portes el van tombar:
   el radi de retenció variable **pinta esglaons azimutals nous** (el sector
   −101° passava a **−11,5 %** contra els veïns; +98° a −5,4 %). La retenció
   ha de ser **coherent en azimut**: global.
2. **La mètrica de contrast local mal pesada en radi**: comparava els px
   pintats amb un control d'anell sencer i part del «contrast azimutal» era
   perfil radial disfressat (+4,8 % en una zona on Vixen i Sony són plans).
   Control **aparellat per calaix de radi**, com mana la regla mare de les
   màscares (cada mètrica ha de mesurar allò que diu).

## 5. Els números finals (abans = el save de Pere; ara = V19)

Les 8 marques:

| marca | bony radial G | tv excés R/G | contrast local G |
|---|---|---|---|
| VERD +98° (5,6-6,5) | **0,111 → 0,006** | 0,042 → 0,000 | +3,3 % → **+0,1 %** |
| VERD +113° (4,4-5,2) | 0,032 → 0,000 | 0,034 → 0,000 | −3,0 → −2,2 % (REAL: Vixen −3,1) |
| VERD +45° (4,2-5,4) | 0,012 → 0,000 | 0,086 → 0,000 | +2,2 → +1,6 % |
| VERD −140° (4,8-5,4) | 0,000 → 0,000 | 0,149 → 0,000 | +4,0 → +2,7 % |
| VERD +161° (3,6-4,1) | 0,000 → 0,000 | — | +2,9 → +3,1 % (REAL: Vixen +3,2) |
| VERD +120° (3,5-4,0) | 0,004 → 0,000 | — | ~0 → ~0 |
| TARONJA −101° (5,3-6,3) | 0,000 → 0,000 | **0,067 → 0,000** | −2,4 → −1,9 % |
| TARONJA +5° (5,6-6,6) | 0,000 → 0,000 | **0,112 → 0,000** | R/G +0,002 → +0,011 (= el Vixen: +0,0109) |

I les portes globals: pitjor tv de croma dels 24 sectors **0,169 → 0,036**;
pitjor bony de sector 0,111 → 0,015 (el residu és el **cel propi de la Sony**,
que puja ~0,4 %/R☉ més enllà de 6,5 — estructura del format canònic, no un
arc); salts azimutals (costures radials) **intactes** abans/després (0,013-
0,014 a az +137° i −35°, pre-existents i no marcats).

## 6. El fitxer

`CapesTotalsV19.psb`: el save de Pere amb (a) la còpia de marques FORA (el
seu diagnòstic queda al seu V18 i a `cau_v19/`), (b) els canals RGB de la
capa Sony substituïts per Camera-Raw-de-Pere × ρ_v19 (la seva màscara i
transparència intactes, byte a byte), (c) blocs globals heretats fora (trampa
8BIM/8B64) i fusionada nova en RAW. Les 12 capes Vixen i el Pasalt: byte a
byte. **La capa Sony del save de Pere era exactament la nostra lliurada**
(dif màx 2 comptes de 65535: arrodoniment d'interpolació), o sigui que la
base torna a ser la seva Camera Raw canònica.

Eines: `research/tools/capes_totals_v14/{fes_v19,portes_v19,vistes_v19,
troba_marques_v19,regions_marques_v19,mesura_halos_v19,inspecciona_v18_pere}.py`
· mesures i rebut JSON a `cau_v19/`.

## 7. Lliçons que queden

- **Una referència també s'ha de qualificar**: el fit de la V18 va fallar
  perquè ningú no havia mesurat fins on el Vixen era de fiar. Ara està
  mesurat per sector i el fit s'atura 0,1 R☉ per sota del pitjor.
- **Tota fosa per canal és un pinzell de color**: si la correcció de croma
  s'ha d'apagar, s'apaga cap al TO UNIFORME i a ≲2 %/R☉, mai cap a 1 per
  canal a 12 %/R☉.
- **La retenció ha de ser coherent en azimut** (§4.1).
- **Abans de curar una taca, mira si és a la referència**: dues de les vuit
  marques eren corona/cel reals del Vixen.
