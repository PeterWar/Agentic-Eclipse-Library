---
name: corregeix-artefactes
description: >-
  Detecta i corregeix els artefactes recurrents del postprocessat de la corona (eclipsi 12-08-2026 i futurs) ABANS d'aplicar cap filtre nou i DESPRÉS de cada muntatge: ghosts del Sol a la lent (Sony, Sol descentrat), ratllat del patró fix del sensor, vores rectes de cobertura o d'extensions inventades, franja fosca o clara al limbe, anells del perfil radial, nivell per anell de les capes de detall (H1), i les marques que Pere pinta sobre un TIF (Artefactes.tif). Usa-la sempre que es parli d'artefactes, halos, anells, ghosts, ratlles, costures, seams, vores, marques de Pere, abans de filtrar, o quan un filtre de detall (ACHF, passa-alt, MGN, NRGF, Claridad, Textura) hagi d'entrar a un PSB.
---

# Corregeix artefactes (abans de filtrar, després de muntar)

Norma de Pere (04-09-2026), després de la V25: «els filtres són magnífics
però estan plens d'artefactes; fes una skill per corregir-los que s'executi
sempre abans de fer un filtre nou». Aquesta skill és aquesta rutina. Mòdul:
`scripts/artefactes.py` (detectors i correccions); ingestió de marques:
`scripts/marques_pere.py`. Exemple històric: `research/tools/v25_lineal/etapa4_munta_v26.py`.

**Precaució de Pere (05-09-2026): probablement les retallades circulars fan
més mal que bé: poden eliminar detall real de corona i crear halos, també
amb ploma.** No són una correcció per defecte. Aquesta norma substitueix les
receptes històriques de pedaços i esvaïments a radis fixos; conservar-ne el
codi o declarar-les al rebut no les valida. Llegeix «Retallades circulars» a
`../postprocessat-corona/references/normes_i_portes.md` per distingir un
retall arbitrari de la validesa lunar temporal i la cobertura física.

## Quan

1. **Abans** de calcular o d'inserir qualsevol capa de detall: la base ha de
   passar els detectors G, R, V, L i M; si no els passa, es corregeix la base,
   no la capa de detall (un passa-alt és un detector d'artefactes: tot el que
   la base té de dolent, el detall ho amplifica).
2. **Després** de cada muntatge, sobre la fusionada: M, L, H i, si Pere ha
   pintat marques, P. Res es lliura amb un detector en vermell sense una
   correcció DECLARADA al rebut.

## Les famílies, per ordre d'execució

| codi | artefacte | causa mesurada | detector (`artefactes.py`) | correcció | on s'ha vist |
|---|---|---|---|---|---|
| **G** ghosts | taques rodones febles (100-500 px) al camp exterior; també a 3,0 R☉ | reflex del Sol a la lent de la Sony amb el Sol descentrat (primer apuntament): un ghost per apuntament a la posició simètrica respecte de l'eix òptic; ~8 R☉ el 2026 | `blobs_rodons` sobre la CAPA DE DETALL (a la base són <4σ) i sobre la base; DoG 40-140 px, >3,5σ, rodonesa >0,55 | identificar la font contaminada i aprofitar observacions netes de la mateixa zona celeste amb geometria validada; qualsevol exclusió es justifica per fotograma i conserva la dada vàlida alternativa. `tapa_blob` i els discs a 0,5 són recursos històrics, no una correcció automàtica | research/116; V25 (3,0 R☉); V26 (sis marques de Pere a ~8 R☉) |
| **R** ratllat | ratlles diagonals al camp exterior, molt visibles al passa-alt | patró fix del sensor (Sony: −45° a la graella V23; Vixen: diagonal del sensor) | `ratllat`: pic espectral d'una finestra de 1024 px del detall; alarma si pic/anell > 30 | diagnosticar les famílies del sensor i validar la retenció de corona abans d'acceptar un `notch_direccional`; ni rampa radial ni esvaïment a 5→7 R☉ per defecte. El radi no demostra que només hi hagi cel | research/113/116 (estriat); V26: 240× abans |
| **V** vores rectes | línies rectes, escales de to o de gra | fi de la cobertura d'un tren, extensió INVENTADA (per raig, constant), rectangle d'una capa | `arestes_rectes` (Canny + Hough ≥400 px) sobre el detall; i mirar-ho a l'ull | mai extensió sintètica: fora de cobertura hi va DADA (l'altre tren, o la capa de Pere) igualada en to en baixa freqüència (ρ radial × k≤2, finestra declarada) amb ploma ≥100 px; o llenç transparent | V25 (extensió per raig: refusada per Pere); V19 (cantonades) |
| **L** limbe | franja fosca o clara entre les perles i la corona | forat lunar de la cadena més gran que el disc de C2 (fins a 22 px); banda exterior d'una capa d'earthshine tonificada a un altre nivell; màscara de la base massa oberta | `limbe`: perfil per anells de 0,01 R☉ de 0,98 a 1,16; alarma si hi ha caiguda >0,03 seguida de pujada | màscara lunar real per fotograma i unió temporal de corona vàlida; disc i earthshine ancorats a C2. Ni forat fix engrandit, ni llindar opac universal a 1,012 R☉, ni ompliment per raig de píxels no observats | research/128 §8; V25 (5 rondes) |
| **M** monotonia | anell clar o fosc a qualsevol radi | igualació entre trens amb finestra que no cobreix el traspàs; capes a nivells diferents | `perfil_radial` + `monotonia` (cap pujada >0,005 per 0,1 R☉ d'1,2 a 12 R☉) | igualar a la base tot el que va fora, no la base a fora; finestra de ρ que inclogui la vora | V25 (anell fosc 2,5-4 R☉) |
| **H** nivell del detall | anell sencer aclarit o enfosquit per una capa Superposar | nivell per anell ≠ 0,5 | `h1_nivell` ≤ 0,05 | `f3.anivella` (interpolat, mai per calaix) | research/111 |
| **C** cel que aplana | de ~2,7 R☉ enfora la base és PLANA i la corona «s'acaba»; els streamers no s'hi veuen | el cel (CEL_c de la cadena) iguala la corona a 2,5 R☉ i la supera ×2 a 3, ×5 a 4, ×10 a 5, ×21 a 6 R☉ (runs 019/016, luminància): amb el cel dins, la corba B compressa la modulació azimutal (13-27 % real fins a 5 R☉) a ±0,005 | taula cel/corona per anell (`etapa1b`, rebut) i amplitud p99 per anell de cada capa de detall | (1) el detall GRAN (ACHF 32-256 px) sobre ln(corona SOLA) amb NRGF complet (mediana i MAD per anell en ln r interpolat): els streamers hi són; (2) base alternativa corona + k·cel amb k DECLARAT (0,25) i la mateixa corba i àncora; mai «dehaze» de Camera Raw com a substitut | V25/V26 (04-09) |
| **A** alineació | les capes noves surten GIRADES respecte de les de Pere (V25/V26: 138,5°) | geometria entre llenços «validada» amb proves rotació-invariants (finestres de fase dominades pel gradient radial, escaquer de raigs radials, forat lunar, anells) | `prova_azimutal`: correlació circular en azimut del perfil polar en ln; PASSA si el pic és a 0 ± 0,5° i el control nul (ref girada 180°) no correla | refer la geometria amb l'angle azimutal com a pas gros (`etapa2d`), centre solar per efemèride i escala declarada; contrastar a part la geometria lunar temporal, sense confondre el seu forat amb el disc C2. Cap PSB amb capes noves sense aquesta prova al rebut | V27 (05-09) |
| **P** marques de Pere | el que ell pinta sobre un TIF de la fusionada | localitza el problema observat; la causa s'ha de comprovar | `marques_tif` → components amb color, mida, r, azimut; `marques_pere.py` fa el panell TIF ↔ fusionada | classificar cada marca en una família i corregir-la a l'origen; el rebut diu marca per marca què s'ha fet | V18, V19, V24, V26 |

## Lliçons de la V26 (rondes 2 i 3, 04-09-2026)

- **La ploma d'un camp exterior es mesura a la vora EXTERIOR**: la distància a
  «fora de cobertura» compta també el forat lunar; sense omplir-lo, la base es
  barreja amb la capa exterior (zero dins de 2,6 R☉) fins a 120 px del limbe →
  franja fosca 1,0-1,27 R☉. `binary_fill_holes` només sobre la màscara auxiliar
  per calcular aquesta distància: mai sobre la validesa física ni la radiància.
- **El tall del detall FI a 3,5→5 R☉ era una recepta d'aquell pilot, ara
  retirada com a norma general (05-09)**. Research/82 situava l'estructura
  real a 30-45 px a 4 R☉, però això no justifica esborrar tot el detall d'un
  anell. Mesura senyal i soroll per escala i zona, amb jutge independent;
  els blobs del detector poden ser gra, i el radi sol no els classifica.
- **Una vora de fotograma de la Sony és a ±45° a la V23** (la capa 13 de Pere
  la té igual): on un apuntament s'acaba, el soroll del compost canvia de cop i
  el detall fi hi dibuixa una RECTA (3.200 px a 4,7 R☉). No es tapa: el detall
  s'ha de revisar a la cobertura i als pesos del compost. Que la banda gran
  no la mostri no justifica eliminar circularment la banda fina.
- **Ratllat: famílies a finestres d'azimuts diferents** (`families_ratllat`):
  un patró del sensor surt al mateix angle a totes; una estructura real, no.
  Dues famílies al mateix període 27,5 px (−45° i −36°) a la V26. I l'angle és
  el del PIC ESPECTRAL (el que torna `ratllat`), no el de les ratlles.
- **Res es lliura sense mirar les vistes**: les portes numèriques de la ronda 2
  van passar (H1, fidelitat, OBRE) amb una franja fosca al limbe i el detall
  saturat de gra; ho van dir `limbe`, `monotonia` i els ulls.

## Regles
- **Prova azimutal obligatòria** a tota capa nova que vagi a un PSB amb capes de
  Pere (`prova_azimutal`, pic a 0 ± 0,5°, control nul). Les finestres de fase i
  els escaquers NO valen com a prova d'alineació: s'enganyen amb el que és
  radial. I mira les vistes en POLAR (r × azimut): un gir hi és evident.
- **Ghosts a l'ORIGEN**: identifica l'apuntament contaminat i busca dada
  neta de la mateixa zona celeste; comprova geometria, suport i transició.
  La recepta històrica `corregeix_bol` + `tapa_inpaint` + `clona_textura`
  no és una correcció per defecte: una textura clonada no recupera la corona
  observada. Mesura el residu i la retenció de detall CAPA PER CAPA. Una
  moneda plana (V26) o un anellet a la ploma (V27) també són artefactes.

- Tot detector torna un número i un veredicte; tot el que es corregeix queda
  al rebut amb la coordenada, el radi i el mètode. Un pedaç no declarat és un
  frau; un pedaç declarat és cosmètica.
- **Cap retall circular per defecte**, encara que estigui declarat: ni
  discs neutres ni esvaïments a radis fixos per ocultar un artefacte. Els
  filtres treballen sobre tot el rectangle amb dada; els perfils radials i
  les màscares de validesa física no són una autorització per amputar corona.
- La base es corregeix ABANS del detall; el detall es recalcula des de la
  font i la validesa verificades, sense heretar pedaços a 0,5 ni esvaïments
  històrics. Mai corregir només la capa de detall per tapar un error de base.
- Un pic espectral, una vora recta o un blob que apareix DESPRÉS d'un filtre i
  no era a la base és del filtre: es canvia el filtre, no es tapa.
- Cada marca de Pere s'atribueix a una família o s'obre una família nova; la
  taula conserva l'evidència històrica, però les receptes superades es marquen
  i deixen de ser instruccions actives. Una marca localitza el problema;
  no autoritza a esborrar tota la zona marcada.

## Ordre d'una passada

```text
base (lineal, fusionada)  →  C (cel/corona per anell: on és la dada)  →  G (blobs a la base
  i al detall on hi ha senyal)  →  V (vores, extensions, ploma a la vora exterior)  →  L (limbe)
  →  M (perfil monòton)  →  [detall fi 2-32 · gran 32-256]  →  R (famílies a diverses
  finestres; correcció només validada)  →  suport real i retenció del detall, sense tall
  circular per defecte  →  H (H1)
  →  muntatge  →  M, L a la fusionada  →  P (marques de Pere)  →  VISTES  →  rebut
```

## Fitxers

- `scripts/artefactes.py`: `blobs_rodons`, `tapa_blob`, `ratllat`,
  `pics_espectrals`, `families_ratllat`, `notch_direccional`, `arestes_rectes`,
  `perfil_radial`, `monotonia`, `limbe`, `h1_nivell`, `marques_tif`.
- Exemples històrics, no receptes vigents de retall: `research/tools/v25_lineal/etapa1b_corona_gran_i_base_k.py`
  (corona sola, detall gran, base k) i `etapa4_munta_v26.py` (muntatge amb G, V,
  L, R, E, H i vistes).
- `scripts/marques_pere.py <Artefactes.tif> <fusionada.psb|.tif> <sortida/>`:
  llista de marques (JSON) i panell de finestres TIF ↔ fusionada.
- Evidència: `research/116` (ghost), `121` (halos de fusió), `123` (fons per
  raig), `128` (limbe), `130` (V25), `131` (V26 i aquesta skill).
