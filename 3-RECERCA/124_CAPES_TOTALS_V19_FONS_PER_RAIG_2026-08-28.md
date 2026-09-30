# 124 · CapesTotalsV19: el fons per raig aplicat al llenç sencer

**28 d'agost de 2026, nit.** L'operador `fons_per_raig` del `research/123`
(la formalització del Desenfoque Radial ZOOM de Pere), aplicat al llenç sencer
de la seva V18 (12415×12095) i lliurat com a **`CapesTotalsV19.psb`** (4,35 GB,
16 capes, porta Photoshop «OBRE»). Ordre de Pere: «Endavant, monta la nova
versió».

## 1. L'estructura del lliurable

Les 12 capes Vixen + la Sony + el Pasalt del save de Pere **byte a byte**
(fora només la seva còpia de marques, que queda al seu V18), més dues capes
noves sobre la Sony:

- **`FONS_PER_RAIG`**: B = gaussiana en ln r (σ=0,2) per raig del compost
  des-premultiplicat, mediana-11, pesos de cobertura, zero suavitzat azimutal;
  polar 8160 rajos × 1750 mostres (r 1,5→20,7 R☉). Màscara **editable** = la
  rampa radial exacta de Pere (0→1 entre 2,36 i 3,12 R☉, mesurada del seu
  `V18-DesenfocRadialZoom`).
- **`ESTRELLES`**: reinjecció **additiva** (Linear Dodge) de 2.456 fonts amb
  discos suaus × rampa; contingut = clip(C − B_det, 0) amb B_det el fons fi
  (σ=0,05).

Fusionada RGBA RAW (4 plans, com mana la capçalera del save de Photoshop).
Blocs globals heretats fora (trampa 8BIM/8B64). Fidelitat verificada al
fitxer escrit (canal de capa vella byte a byte).

## 2. Portes (abans = la V18 de Pere; després = V19)

- **17/17 marques de les dues rondes**: 16 a bony **0,0000 exacte**; la verd
  gran de +98,4° passa de 0,142 a **0,019** — i el residu és el gradient
  propi del cel de la Sony canònica (§3.3), no un arc.
- 24 sectors: bony mediana **0,0100 → 0,0004**; variació total de croma
  millor a tots els sectors (mediana −0,19).
- **Cobertura 0,679 → 1,0000**: les cantonades més enllà de la vora de dada
  Sony (~9-15 R☉ segons azimut) s'omplen amb l'extensió de cel per raig
  (declarada cosmètica; la frontera només s'endevina a r>15).
- Estrelles: 2.456 reinjectades; al cru en són mesurables 1.390 i en
  sobreviuen 1.095 al llindar del 50 % de contrast (la resta són objectes
  d'~1σ que la mètrica no pot resoldre sobre el gra — l'excés hi és igualment).

## 3. Les tres troballes de la construcció

1. **La vora premultiplicada.** El compost duu la fosa de la màscara Sony
   premultiplicada (a la vora, valor = cel × màscara que cau, no cel): el
   primer fons se la va empassar i la porta va inflar un fals bony de 0,24.
   Cura: el fons menja **C/α** (des-premultiplicat) amb pes = cobertura.
   ⛔ Regla: un fons autoreferent ha de menjar valors de VERITAT, i a la vora
   d'una màscara la veritat és el valor des-premultiplicat.
2. **El gra correlacionat mata el filtre adaptat.** Al compost cru les
   estrelles febles són a ~1σ del gra local (pic 185, MAD 160 comptes), i el
   gra està correlacionat a l'escala de la PSF (drizzle 1,7×): el filtre
   adaptat NO hi guanya (343 → 143 deteccions). La reducció de soroll de la
   passada Camera Raw de Pere sí que les feia aflorar: **el seu catàleg del
   retall (2.117 fonts) és el detector** — es mapa al llenç (+2196, +4124),
   es dedupa a 4 px amb les 343 pròpies i es reinjecta l'excés cru de
   cadascuna. La corba final de Pere les tornarà a fer aflorar, sobre fons
   net.
3. **Un gradient de cel no és un arc.** Els sectors de dalt-esquerra pugen
   +1,5 %/R☉ (0,418 a 5,5 R☉ → 0,484 a 12,5): és el cel real del render, ja
   present a la V18, azimutalment suau. La porta de l'envolupant monòtona el
   compta com a «bony» (0,12) però cap fosa no l'ha de tocar: aplanar-lo és
   una decisió de TO (de Pere), no una cura de fusió. Queda declarat.

I una d'infraestructura: **macOS va retirar l'accés al Desktop a mig camí**
(TCC de l'app amfitriona `/Applications/Claude.app`); el flux es va partir en
`--nomes-calcul` (tot des dels caus del repositori) i `--nomes-psb` (només
obrir/escriure al Desktop), que és com l'script queda per a qualsevol represa.

## 4. Fitxers

- Lliurable: `CapesTotalsV19.psb` + `CapesTotalsV19_REBUT.md` +
  `CapesTotalsV19_vistes/` (6 vistes al llenç sencer), al costat dels seus.
- Eines: `research/tools/capes_totals_v14/{fes_v19_fons,vistes_v19_fons}.py`.
- Mesures: `cau_v19/fons/` (F, B, E, màscares, catàleg d'estrelles,
  `portes_v19.json`, `rebut_v19.json`).
- El save de Pere (`CapesTotalsV18.psb`, amb les seves marques) i el seu
  `V18-DesenfocRadialZoom.psb`: intactes, només lectura.
