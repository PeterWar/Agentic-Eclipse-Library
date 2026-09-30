# 88 — CapesTotals V4: la normalització de l'escala d'exposició desencalla la cadena sencera (12→01)

Execució de `PROPOSTA_Normalitzacio_Exposicio_CapesTotalsV4.md` (Escriptori), decisions §8
signades per Pere el 21-08-2026. Agent: Kimi (claim `FC0611A4-D243-402E-ACCF-112C3EA9FC4A`;
diari a `.coordination/KIMI_STATUS.md`). Resultat: **`CapesTotalsV4.psb`** (1.901.837.970 B,
SHA-256 `2a75cc695fa9c731a18d27e73af72cc80e02eae17df35fdfe77d81815eb12d97`), les **12 capes
acceptades a pes 1,0** amb totes les portes verdes, de la 1/3200 a la 10,3 s. La V3c queda
congelada com a checkpoint (12→08 a 2,6 R☉); no s'hi ha tornat.

## 1. La via de revelat: ACR scriptat no existeix (PS 27.9.1) → renderer offline

L'Opció A (re-revelat ACR amb compensació EV) és impossible de scriptar a 16 bits: l'obertura
scriptada d'un raw a Photoshop 27.9.1 ignora el flux de treball d'ACR i obre sempre a 8 bits
Display P3. Provat i descartat: workflow a 16 bits via GUI (escriu `Workflow/DNG.xmp`), reinici
complet de Photoshop, obertura com a smart object, i descriptors `cameraRawOptions` (error 8800
en totes les variants; no hi ha `CameraRawOpenOptions` al DOM ni diccionari AppleScript).
Amb l'aprovació de Pere, **Opció B+**: `research/tools/revelat_normalitzat/render_lineal.py`:

- els 3 CR3 del fonament es converteixen a DNG lineal amb el **mateix DNG Converter 18.5** que
  va reescriure els 9 apilats (`-c -l -p1`; verificat: mateixes matrius i neutral);
- lectura LinearRaw amb **rawpy** (el motor de `apila_hdr4_vixen.py`), `(x−negre)/(blanc−negre)`,
  WB As Shot (idèntic als 12 fitxers: neutral 0,514573 1 0,602707, Dia 5200 K — verificat tant a
  l'EXIF com a LibRaw), escala exacta t_ref/t, ForwardMatrix2 (D65) → Bradford → Display P3 →
  TRC sRGB → u16. BaselineExposure (0,26 als 12 DNG) **no aplicat**: escala pura declarada.
- temps de l'EXIF APEX rellegit per fitxer; capa 01 = **10,08 s fotomètric** (decisió §8.3,
  research/76). Escales resultants: +7,72/+5,09/+3,09/+2,00/+1,00/0,00/−0,91/−1,91/−2,91/−3,91/
  −4,91/−7,24 EV.
- Cada capa porta `RENDER_RECEIPT` (`HDR4/revelat_v4/receipts/`). El test d'escala (07 a ×1 i ×2)
  dona raó 2,0000 (p1 1,9939, p99 2,0002). Contracte amb el revelat ACR vell (ID9): el vell
  pujava ×2,5 el to mig i comprimia el to fluix ×0,5 — la patologia que la V4 elimina.

## 2. Re-calibratge de la validesa (proposta §4.2)

Amb revelats lineals normalitzats, el plateau de saturació seu a nivell scale_i (fosc per a les
capes llargues) i els llindars antics p50/p95 del codificat —que mesuraven la compressió de la
corba ACR— no el detecten. Validesa V4: **fora del plateau** (raw ≥ blanc a la font; màscara
`sat_i` per capa) **i SNR ≥ 5**. P3 = clip blanc de la 1/3200 (9.094 px, 16 components: perles i
diamant — allò que clippa a totes les capes); P4 = clip blanc de la 1/500 (R+64) ∪ excés vermell
∪ limbe R→R+4 (16.108 px). Les màscares de la cadena porten el factor per píxels (1 − sat_i)
amb ploma 1+2 px: una capa mai contribueix on ella mateixa és saturada. El·lipses lunars
re-mesurades a les 12 capes; la del 10,3 s per gradient màxim (R_eq 445,3 px: el bloom de la
corona saturada esmena el limbe ~7 px; el mig nivell hi fallava, contrast 0,028).

## 3. Resultats de la cadena

- **§5.2 (q entre veïnes): 1,00 ± 0,05** a tots els anells 1,3–4 R☉ per a 09…02 (V3c: 2,0–3,9).
  11/10 i 12/11 divergeixen cap enfora (pedestal del CR3 únic sense cel anivellat) — fora del seu
  domini de contribució (1,0–1,55 R☉, on q = 1,01–1,07).
- Fonament (11/10/09): màscares a pes 1,0, 0 defectes, empremta 0,003–0,005 %.
- Cadena 08→01: **totes ACCEPTADES a w = 1,0 a la primera combinació provada**, 0 defectes de
  costura, empremta ≤ 0,003 %, 0 sots sectorials, nuclis P3/P4 byte-idèntics, cobertura neta llevat
  de la reserva documentada (6 cel·les al streamer 230–250°, 0,80–0,90; 5 cel·les a 2,3–2,8 R☉,
  mínim 0,67 — la SNR per cel·la subestima on hi ha estructura fina real).
- Entrades per saturació de la precedent: 06 a 1,03 · 05 a 1,11 · 04 a 1,21 · 03 a 1,33 ·
  02 a 1,47 · 01 a 2,01 R☉ (Δ = 0,3 R☉, w = 1,0). Estratificació HDR tal com preveia la proposta.
- Verificació reoberta 12/12: ràsters == revelats V4 (marges d'ID4/ID5 byte a byte), alfa ==
  fonts, màscares == declarades, merged == compost offline (0 DN) i == cadena (≤1 DN).

## 4. §5.3: FORA del ±10 %, amb la descomposició

Primer contrast de la cadena de Photoshop contra l'autoritat fotomètrica
(`hdr_vixen_countss.npy`, 22 estrelles, B/B☉ = 2,772×10⁻¹¹ ×ADU/s), fet a l'espai de càmera
(matrius invertides; sense això la raó surt inflada pel guany WB del R barrejat al G de P3):
**V4/mestre = 1,23 (1,3–1,6 R☉) → 1,14 (4,2–5,0 R☉)**. Descomposició:

1. **~+11 % preexistents**: l'apilat 07 cru (sense cap processat V4) ja llegeix 1,09–1,15 sobre el
   màster als mateixos anells — divergència d'escala absoluta ENTRE els dos pipelines d'apilatge
   (els factors `escala` ~0,89–0,96 de research/76 que el màster va aplicar i els apilats HDR4 no;
   1/0,893 = 1,12). No és un defecte de la V4.
2. **~70 ADU/s de cel**: la V4 no resta el cel (els apilats l'anivellen); el màster sí. Restat,
   els anells externs queden a +3…+15 %.
3. **L'excés intern (1,3–2,0 R☉) queda per investigar** (vignetatge/flat de camp, o ponderació dels
   frames interns al màster).

Decisió pendent de Pere: ancorar l'escala absoluta a la BASE (els apilats; mai al compost — torre
de Pisa) o revisar els factors del màster. La porta §5.3 ha fet exactament la seva feina: és la
primera mesura d'aquesta divergència.

## 5. Notes per a la presentació

- El disc lunar mostra la 1/3200 amplificada ×210 (soroll visible; a la V3c quedava sota el
  llindar visual). És el contingut honest de la base; disc d'earthshine o corba radial són
  decisions posteriors a la cadena (research/84 §5).
- El gradient d'extinció dins del camp (research/75 §4) continua sense corregir a cap pipeline.

## 6. Eines i rebuts

- `research/tools/revelat_normalitzat/`: `render_lineal.py` (renderer), `revelat.py` (via ACR
  descartada, conservada com a registre), `valida_render.py`, README.
- `research/tools/capes_totals_v4/`: cadena autocontinguda (cap dependència de /private/tmp;
  el deute de research/87 §8 per a aquesta cadena): `v4_lib.py`, `v4_tests.py`, scripts
  01–12, `build_capes_totals_v4.py` (substitució de ràsters RGB amb alfa i marges byte-idèntics),
  `verify_capes_totals_v4.py`.
- QA: `1-Unint Capes/CapesTotalsV4_QA/`; manifests `CapesTotalsV4.manifest.json` +
  `.manifest_v4.json`; LLEGEIX-ME propi.
- Skill `postprocessat-corona` v3: pas obligatori de revelat normalitzat amb `RENDER_RECEIPT`
  (còpia projecte/global byte-idèntiques, SHA `8fb6db65…`). Tanca research/87 §10.4.
