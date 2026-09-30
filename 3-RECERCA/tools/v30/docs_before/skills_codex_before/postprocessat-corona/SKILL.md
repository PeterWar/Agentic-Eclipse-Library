---
name: postprocessat-corona
description: >-
  Postprocessat de la corona de l'eclipsi del 12-08-2026 (i del 2027) amb la cadena determinista `cadena.py`: calibració dels RAW (CR3, ARW, darks, flats, pedestal, flats invertits, dither), registre per efemèride, composició LDIC en una sola suma ponderada, filtres de detall (passa-alt, NRGF, MGN, ACHF, fons per raig), color CIENCIA i corba de to declarada, PSB per a Photoshop, earthshine, estrelles i astrometria, jutge extern entre trens, portes i rebuts. Usa-la per a qualsevol feina sobre Vixen R6 III, Sony 300 mm, LDIC, artefactes, anells, costures, halos, CapesTotals, limbe lunar, perles, protuberàncies, earthshine, LROC, estrelles, control nul, injecció cega, porta Photoshop, Druckmüller o Brno. Cap PSB no es lliura sense `porta_photoshop.sh`; cap correcció d'artefacte no es declara bona sense el jutge extern.
---

# Postprocessat de la corona

Estat del contracte: 05-09-2026. Substitueix el SKILL.md del 21-08, que
descrivia el revelat de DNG i la composició per capes de CapesTotalsV4.
Aquell mètode és història (vegeu §6). Llegeix abans de res
`references/normes_i_portes.md`: són les normes de Pere i les portes que manen.

## 0. Arrels i punt d'entrada

- Repositori i codi: `/Users/USUARI/Downloads/Eclipse 2026`.
- Actius fotogràfics i Photoshop de Pere:
  `/Users/USUARI/Desktop/Eclipse 2026` (`Projecte photoshop/1-Unint Capes/Capes Totals/` és on viuen els CapesTotals; el viu és `CapesTotalsV24.psb`).
- Cadena determinista i dades: `/Users/USUARI/Desktop/Eclipse determinista/`
  amb `0-ENTRADES/` (només lectura, per tren i rol), `1-RUNS/` (un run
  immutable per execució) i `2-OUTPUT/` (còpia dels lliurables del run vigent,
  amb `MAPA_DE_CARPETES.md`, `LLEGEIX-ME.md`, `TRIES_DE_PERE.md` i els
  `COM_S_HA_FET*.md`).
- Punt d'entrada únic: `research/tools/eclipse_determinista/cadena.py`.

```bash
cd research/tools/eclipse_determinista
<python detectat> cadena.py VIXEN CIENCIA            # run sencer, ~17 min
<python detectat> cadena.py VIXEN CIENCIA --reusa 019 # fases 0-2 del run 019, refà 3-5
<python detectat> cadena.py SONYTOT CIENCIA
```

Regla d'or: cap intèrpret escrit a pèl. Detecta'l amb
`.claude/skills/apilatge-imatges-eclipsi/scripts/comprova_entorn.py --python`
(l'entorn viu és `~/.venvs/eines-ia-py312`). Mode de color: només `CIENCIA`
(blanc sobre el Sol AM0, guany 0,9302 · 1 · 1,1261); `MEMORIA` és deprecat
des del 27-08 i la cadena refusa arrencar-lo.

Cada run escriu `MANIFEST.json` amb el SHA-256 del codi i de cada entrada,
una còpia congelada del codi a `codi/`, les fases `0-calibracio 1-registre
2-ldic 3-filtres 4-rebuts` i `lliurables/` amb els PSB, `REBUT.md` i
`vistes/`. `--reusa` falla tancat si `f0.py`, `f1.py`, `f2.py` o una taula de
constants no són byte a byte els del run d'origen. Els runs no es toquen mai;
el que Pere mira és `2-OUTPUT/NNN_TREN_COLOR/`.

## 1. Les normes que manen a tot (una línia cadascuna)

Detall, data i literal a `references/normes_i_portes.md`.

1. Norma zero (24-08): cap correcció d'artefacte es declara bona sense el
   jutge extern, que és l'altre tren. `research/tools/pilot_vixen_claude/jutge_creuat.py`, porta H4.
2. Norma del rectangle (23-08): tot filtre a tot el rectangle, mai a una
   circumferència. **Precaució de Pere (05-09): probablement les retallades
   circulars fan més mal que bé: poden eliminar detall real de corona i
   crear halos, també amb ploma.** Cap tall o esvaïment a radi fix com a
   correcció per defecte; el radi sol no demostra manca de senyal. Conserva
   el suport real de la dada; criteris a `references/normes_i_portes.md`,
   «Retallades circulars».
3. Vara única (30-08): tota versió nova es compara amb totes les anteriors
   mesurades idènticament abans de lliurar.
4. Injecció cega (30-08): tota cadena de senyal feble injecta textura
   sintètica i mesura la transferència a la banda del senyal: 0,90 a 1,10.
   Els filtres per bandes es fan en Fourier, mai amb diferències de gaussianes.
5. Control nul aparellat (29-08): cap llista triada per llindar sense la
   puresa mesurada amb posicions girades al voltant del Sol.
6. RGGB a cada resultat (26-08, error recurrent): R/G i B/G d'una zona
   coneguda al rebut de cada producte reconstruït des dels RAW.
7. Llenç sencer (26-08): cap vista retallada, ni de diagnòstic. El detall va
   a més de la vista sencera, mai en lloc seu.
8. Tot a Output (26-08): el que Pere ha de veure surt per `comu.Run.vista()`
   i `comu.Run.lliurable()`, mai per una ruta escrita a mà.
9. Vistes de diagnòstic a cada etapa (24-08) i mira-te-les tu abans
   d'enviar-les: Pere hi troba defectes que cap porta no veu.
10. La imatge localitza, el número decideix, el jutge valida. Una coincidència
    de posició no és una causa: mou el paràmetre abans d'atribuir.
11. Centre absolut = Sol per efemèride, mai el limbe (llisca 28,5 px).
12. Només C2 (27-08): les protuberàncies del producte surten de l'ingress;
    `comu.CONTACTES_AL_PRODUCTE = ("ingress",)`.
13. Disc lunar, earthshine i limbe de presentació només de l'instant
    d'ancoratge (19-08); màscara lunar per fotograma per a la corona (27-08):
    `w = 0` al disc de CADA fotograma, una sola funció
    `f2.mascara_lluna`, aplicada a tots els llocs que comparen. Per a la
    corona, conserva la unió temporal de les observacions vàlides, sense
    imposar al compost un forat circular més gran. Això no canvia l'instant
    d'ancoratge del disc lunar i l'earthshine.
14. Perímetre lunar de display amb el fotograma sencer (01-09): les tessel·les
    de ciència buiden el trànsit disc-glow per construcció.
15. Cap tret puntual es bateja sense la posició predita per l'efemèride, i cap
    tret és lunar si els dos trens no el veuen amb la mateixa amplitud (31-08).
16. Flats del mateix dia o dither (31-08): la pols del sensor es mou.
17. El soroll d'un component mai només per diferències entre germans (31-08):
    el patró fix es cancel·la; estimador = potència total menys senyal creuat.
18. Jutja cada capa on viu (27-08): una porta hereta radis i llindars d'on va
    néixer; comprova que el producte nou hi té senyal.
19. Un rebut que no diu amb quins paràmetres s'ha fet no és un rebut (25-08).
20. Cap PSD/PSB es lliura sense `porta_photoshop.sh` amb el literal OBRE
    (28-08); dos lectors independents; fusionada mai en ZIP; canals editats
    re-descodificats a la profunditat del document.
21. Brno és jutge, no font (27-08): cap píxel ni correcció seva al producte;
    «és corona real» exigeix un observador d'un altre lloc (`es_corona.py`).
22. El fons dels filtres segueix el S/N (27-08): `f3.suavitza_sn`, t = 0,18.
23. La corba de to és un paràmetre declarat, mai d'un percentil (26-08).
24. D1 (23-08): la via és la FOTO amb els dos trens; el fusionat NO és una
    mesura. La fotometria es declara sobre els FITS lineals del run.
25. Avança sol i informa una vegada (06-08); parla planer; sense manuals.

## 2. Les fases de la cadena i la porta de sortida de cadascuna

| fase | fitxer | què fa | porta que atura |
|---|---|---|---|
| 0 calibració | `f0.py` | pedestal mesurat (marge a la Vixen, darks a la Sony), màsters de dark per exposició, flat radial; el flat abans de qualsevol warp | F0.1 pedestal/saturació = declarat; F0.3 desacord amb els flats invertits ≤ 8 % (Sony: control del dither, `flat_dither_SONY.json`) |
| 1 registre | `f1.py` | Sol per efemèride, llenç comú declarat `comu.LLENC_COMU` (8096×8960, 2,1495 ″/px, nord amunt), segments d'apuntament, registre fi per correlació de fase | F1.2 dos contactes i fracció de coronals |
| 2 LDIC | `f2.py` | una sola suma ponderada g = Σ w k f / Σ w, sostre 0,85, terra 12 DN, màscara lunar per fotograma (guarda 2 px), coherència k amb gauge mediana ln k = 0, cel separat pel color; N i D desats per canal | F2.2 guany dins de [1/2, 2]; F2.4 control del color ≤ 3 % |
| 3 filtres | `f3.py` | base amb la cadena de color sencera i una corba escalar sobre la lluminància (`comu.CORBA`); detall per la MEDIANA de les tres realitzacions de canal; passa-alt, radial, NRGF, MGN; `suavitza_sn`; perfils per calaix interpolats; anivellament per anell | tancament HDR ≤ 5 %, brillantor ≤ 8 %, croma ≥ 0,02, H1 max |nivell − 0,5| ≤ 0,05, H1b anells de calaix, cap capa verda |
| 4 PSB | `f4.py`, `ajust.py`, `research/tools/encaix_sony/psb_utils.py` | PSB del resultat, capes LDIC amb el rang de validesa al nom, contactes, capes d'ajust a identitat | cap capa verda; `porta_photoshop.sh` diu OBRE; `sips -g pixelWidth` no torna nil |
| 5 vistes | `vistes.py`, `vistes_filtres.py`, `mapa_carpetes.py` | vistes al llenç sencer, `REBUT.md`, mapa generat del disc | R/G i B/G al rebut |

Deutes de la cadena que has de tenir presents abans de mesurar-hi res:
els temps d'exposició són els nominals de l'EXIF (research/99 §2: fins a
−6,25 %), els darks van per mediana sense selecció de temperatura, la
variància per canal no es desa (només `PES_c`), i la cura del cel per
fotograma (`f2.cura_cel_fotograma`) és desactivada perquè a la cadena
empitjora l'estriat (research/113).

## 3. El que avui viu fora de la cadena (scripts d'un sol ús, sense manifest)

Són les peces que el pla del 2027 ha de portar a dins com a fases 6 i 7.

- Fusió dels dos trens al llenç de Pere: igualació en baixa freqüència ρ
  (`research/tools/capes_totals_v14/fes_v18.py`, research/121) dins del radi
  de detall; fons per raig al camp exterior (`fes_v19_fons.py` i
  `cau_v19/desenfoc/scripts/operador_prototip.py`, research/123 i 124):
  suavitzat només en ln r, σ 0,2, autoreferent, re-injecció d'estrelles.
  Cap fosa per canal, cap retenció que no sigui coherent en azimut.
- Jutge extern: `research/tools/pilot_vixen_claude/jutge_creuat.py` (H4) i
  `research/tools/dos_trens_jutge/nucli.py`; contra un altre lloc,
  `research/tools/auditoria_estructura/es_corona.py`.
- Filtres del pilot: `research/tools/pilot_vixen_claude/filtres_druckmuller.py`
  (passa-alt, desenfoc radial i azimutal, NRGF, FNRGF, MGN, WOW, NAFE, tots al
  rectangle amb convolució incompleta) i `filtres.py` (ACHF multi-σ sobre ln I
  amb NRGF davant). Muntatge a Photoshop: `munta_photoshop.py`. Portes pures i
  100 proves: `portes.py` i `test_portes.py`.
- Earthshine: pila registrada a la Lluna per tren (`v21_lluna_tren.py`),
  producte V4 amb model de vel només a r < 0,85, pesos per component amb
  l'estimador de soroll corregit, Wiener en Fourier, injecció cega i validació
  amb el mapa LROC (`v21_earthshine_v4.py`, `v21_lroc.py`; research/126 i 127).
  La significança citable és la del 126 (7σ); el r del producte és producte.
- Estrelles: del catàleg cap a la imatge, fotometria forçada i control nul
  aparellat (`v21_estrelles_purga.py`, research/125 §3 ter). Astrometria i
  calibratge absolut: `research/tools/astrometria/pipeline_estrelles.sh` i
  `test_acceptacio.py` (22 números), `references/astrometria_i_deflexio.md`.
- Perímetre lunar de display: `v24_perimetre_e.py` (research/128 §8).

## 4. Producte i to

- D1: el producte és la foto dels dos trens. Cap número fotomètric no surt
  del fusionat; surt dels FITS `CORONA_*` i `LDIC_*` del run.
- Format canònic de la capa Sony: el de Pere, mesurat a
  `research/tools/capes_totals_v14/FORMAT_CANONIC_SONY_PERE.json`. Cap render
  pla de la cadena es lliura com a capa Sony estètica.
- Corba de to: paràmetre declarat al rebut. La cadena porta `comu.CORBA`
  (pendent 0,22, àncora 0,74, terra 0,045); la maqueta de Pere en fa 0,166 i
  research/108 proposa 0,17 i 0,68. El número és de Pere; el sostre surt del
  màxim de la dada, mai d'un percentil.
- Procedència al rebut (`comu.PROCEDENCIA`): què és mesurat aquí, què és
  tria de Pere, què és número, convenció o mètode de Brno.
- Les decisions manuals de Pere (corba, re-escenificació del llenç, Camera
  Raw de la Sony, màscares, retall 3:2, perles, reflex) no s'automatitzen: es
  mesuren i es desen com a paràmetres.

## 5. Rebut i lliurament

Tot lliurable porta `REBUT.md` amb: paràmetres efectius, procedència, SHA i
mida del fitxer, R/G i B/G d'una zona coneguda, veredicte literal de cada
porta, la taula comparativa amb totes les versions anteriors amb la mateixa
vara, i el literal de `porta_photoshop.sh`. Un rebut escrit abans del save no
cobreix el fitxer. Informa curt: `DEMOSTRAT`, `FALTA`, següent porta.

Per a un PSB de Pere (CapesTotals): les seves capes byte a byte, cap
re-mostreig dels seus píxels, capes noves a sobre amb el nom que digui què són
i fins on valen, i `references/acceptacio_capes_photoshop.md` per a les
portes de capa.

## 6. Què és història i on és

- Revelat «protocol v3» de DNG amb t_ref 1/15 s i
  `research/tools/revelat_normalitzat/render_lineal.py`: CapesTotalsV2b a V4
  del 21-08 (research/87 §11 i research/88). La cadena compon LDIC des dels
  RAW i no revela cap DNG.
- `.claude/skills/apilatge-imatges-eclipsi/scripts/pipeline_vixen.sh`
  (masters_vixen_v2, prnu_vixen, hdr_corona_vixen, apila_hdr4_vixen): la
  cadena del 17-08 amb R☉ 959 ″ i drizzle; els seus productes queden desmentits
  per research/99 §21. Conserva tres peces que la cadena no té: darks per
  temperatura amb mitjana retallada, PRNU amb estrelles emmascarades i drizzle.
- Regla de llenç W = max(W_i): substituïda pel llenç comú declarat.
- Retall 1:1 com a lliurable: substituït per la norma del llenç sencer.
- Pilot del 23 al 25-08: `output/pilot_vixen_fable_20260825_lliurament/` i
  `~/Desktop/Eclipse 2026/Projecte photoshop/3-Dos trens amb filtres 2026-08-25/`.

## 7. Referències i scripts

- ⛔ Skill germana `corregeix-artefactes` (04-09-2026): s'executa ABANS de
  calcular o inserir qualsevol capa de detall i DESPRÉS de cada muntatge
  (ghosts, ratllat, vores rectes, limbe, monotonia, H1, marques de Pere).
- `references/normes_i_portes.md`: normes de Pere amb data i literal, regles
  de mètode mesurades, taula de portes. Llegeix-lo sempre.
- `references/trampes_INDEX.md`: índex per fase de `references/trampes.md`.
- `references/trampes.md`: el diari de les lliçons pagades; consulta per tema.
- `references/acceptacio_capes_photoshop.md`: portes G0-G7 per a capes de Pere.
- `references/astrometria_i_deflexio.md`: estrelles, placa, B/B☉, deflexió.
- `references/constants.md`: constants mesurades; a refer amb data per fila.
- `research/README.md` i `research/97` a `research/128`: l'evidència.
- `research/tools/capes_totals_v14/porta_photoshop.sh`: la porta final de tot PSD/PSB.
