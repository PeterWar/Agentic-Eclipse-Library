"""Self-contained Catalan receipts, results and restart for all three routes."""
from common import *
claim();pub=json.loads((OUT/'E4_publish.json').read_text());native=json.loads((OUT/'E3_readback.json').read_text());ret=json.loads((OUT/'R8_exact_retention.json').read_text());inj=json.loads((OUT/'R11_photo_injections.json').read_text());assert native['PASS'] and sha(pub['path'])==pub['sha256'];report=OUT/'RESULTAT.md';handoff=ROOT/'.coordination/HANDOFF_2026-09-13_CODEX_EARTHSHINE_V56.md';manifest=HERE/'delivery_manifest.json'
measure=[a for a in ret['rows'] if a['mode']=='linear' and a['band']==[24,40] and 'heldout' in a['region']];table='\n'.join(f"| {a['region']} | {(a['relative_amplitude']-1)*100:.3f}% | {a['old']['Sony']['r']:.6f} → {a['new']['Sony']['r']:.6f} |" for a in measure)
text=f"""# Earthshine V56 · resultat de les tres propostes · 13-09-2026

La V56 reforça aproximadament un **2,4–2,9% l'amplitud fotogràfica de la textura de 24–40 píxels** dins del disc fins a r435. Les tres vies demanades s'han provat. El resultat útil ve del vermell: neteja del patró repetible del sensor i corroboració R/G per reforçar moderadament la font fotogràfica existent. La fusió per nitidesa i la reconstrucció CFA assajades no superen la V55.

Aquest percentatge descriu contrast de textura; **no** és un percentatge de nova informació, resolució o cràters recuperats. L'increment és petit. La concordança fotogràfica amb Sony canvia molt poc; la base fotogràfica ja conté Sony i aquesta comparació és retenció, no independència. No es reclama detall nou de tot l'últim limbe ni equivalència DHS.

## Producte i preservació

- [Earthshine_V56.psb]({pub['path']}), SHA256 `{pub['sha256']}`, {pub['bytes']} bytes; 10551 × 7506, RGB16, 26 capes.
- V55, V54, V53 i 88 RAW exactes; 271 entrades verificades a `F0_integrity.json`. CLAUDE_STATUS intacte.
- Només RGB i nom de la capa lunar 25 canvien. Les altres 25 capes, alfa, màscares, geometria, visibilitat i modes són exactes. R−G i B−G es conserven en enters; els quocients cromàtics es documenten a `R13_qualification.json`.
- Sense nou enquadrament, remostreig del producte, màscara de marques, contorn pintat o nou revelat Camera Raw. Els pilots de mostreig natiu es limiten a dades de diagnòstic i no entren al PSB.
- Dos lectors i Photoshop real: `OBRE 10551 px x 7506 px · 26 capes`; lectura de retorn màxim {native['max_full_DN16']} DN16 al llenç i {native['max_moon_DN16']} a la Lluna. Documents oberts de Pere preservats.

## Resultat fotogràfic mesurat igual que la V55

| Regió reservada | Increment d'amplitud 24–40 | Correlació amb Sony, abans → després |
|---|---:|---:|
{table}

93/93 coincidències triples de la V55 es conserven, en les mateixes regions verdes, anells, modes lineal/log i controls girats. Els 37 requadres 2D passen els controls de retenció en les bandes 16–64. No són mostres independents: se superposen i comparteixen calibració. La correlació mitjana 2D fotogràfica 24–40 amb Sony passa aproximadament de 0,8708 a 0,8714; LROC baixa lleument de 0,7276 a 0,7274. No s'amaga aquest resultat mixt ni s'interpreta l'increment de contrast com un guany equivalent de senyal.

## Les tres vies i les proves descartades

| Via | Prova concreta | Resultat |
|---|---|---|
| 1. Fusió per nitidesa | B0: 12 captures de ≥0,5 s, 384², quatre bandes i vuit direccions; coherència amb dues referències que exclouen la captura. B1: incertesa de sis sectors parells per limitar pesos sorollosos. | B0 empitjora 16–24, 40–64 i 64–96; B1 no dona millora conjunta Sony/LROC. Cap mosaic ni PSB. |
| 1. Control de fase | B2: desplaçament petit estimat contra dues meitats, sectors senars per predir i nul girat. | Només 1/12 captura passa acord ≤0,25 px, límit 2 px i millora reservada. No hi ha graf complet ni geometria nova. |
| 2. Vermell addicional | R0 emparella R/G de la mateixa captura amb els mateixos pesos; R1 ajusta resposta fotogràfica espacial. | Font 16–64 millor, però 149 píxels fotogràfics fora de rang a r448,97–456,45: **rebutjada**. No es retallen aquests píxels. |
| 2. Incertesa cromàtica | R2/R3: covariància i variació temporal, amb/sense component polinòmic lent. | Pes vermell central aproximadament 2,7–2,9%, molt menor prop del limbe; aquests pesos no es promouen a la foto. La llum solar variable continua limitant la mescla directa. |
| 2. Patró vermell repetible | R4: 67 Vixen, dues meitats separades per exposició/temps, operador global 1400², mateixa covariància segura que V55 i guanys Fourier de potència creuada. | Font útil; R5 retira la seva contribució estimada a la foto, només ±7 DN16. Aquesta correcció sola és massa petita per explicar la millora visual final. |
| 2. Detall corroborat | R8: acord R/G net per donar confiança a la font pre-CameraRaw existent, banda 24–40 amb faldilles 20–48, reforç màxim 4%; beta=0,707351 ajustada només als sectors parells. | **Productor fotogràfic escollit: R4 → R5 + R8**. Mateixa aparença desada; increment total màxim ±53 DN16. |
| 3. CFA natiu | C0: cobertura de fase. C1: G1/G2 sense interpolar la radiància, 12 captures; integració del píxel natiu amb quadratura positiva GL8 i contrast GL12. | Rang de fases 4, condició 1,218 a les captures llargues; operadors de constant, pla i adjunt passen. Això no prova resolució òptica. |
| 3. Reconstrucció | C2: mínims quadrats natius amb regularització triada per predicció Vixen. C3: mateix problema restringit a 16–64, faldilles 12–96. | C2 conserva només 0,49–0,50 de la injecció: rebutjada. C3 passa 0,905–0,926 però empitjora Sony/LROC a 16–40. No es promou ni s'amplia un pilot negatiu a tot el disc. |

Els fracassos són d'aquestes implementacions i d'aquest conjunt de dades, no una demostració que els mètodes generals siguin impossibles. El primer intent C1 va topar amb el límit OpenCV de 32767 files; es va corregir dividint les consultes en blocs de 16384, sense canviar la interpolació de calibració. C3 va necessitar un precondicionador espectral per convergir; el model i els llindars van quedar iguals.

## Evidència de la font vermella

Correlació 2D mitjana del **vermell sol** amb Sony: 16–24, 0,2777 → 0,3096; 24–40, 0,4140 → 0,4864; 40–64, 0,7080 → 0,7540. La combinació GR neta dona 0,3681 / 0,5250 / 0,7740 davant del verd net V55 0,3463 / 0,5032 / 0,7541. Són coeficients de correlació, no percentatges de resolució. Sony és aquí una font separada i no entra al productor Vixen. LROC és un patró històric de contrast, no aporta píxels. R/G i les meitats temporals comparteixen sensor, calibració i una part del patró fix.

## Injecció i contorn

- R9: 360 injeccions de senyal comú en fonts R, transferència 1; sis controls de detector pur deixen un residu 0,359–0,682, sense amplificació. Operador, covariància i guany de repetibilitat congelats. La invariància del senyal comú és pròpia del model d'escena lliure; no basta com a prova independent.
- R11: 288 proves condicionals 24–40, transferència {inj['new_range'][0]:.6f}–{inj['new_range'][1]:.6f}; 48 controls de solapament acumulat 40–64 contra la resposta nativa CameraRaw antiga, {inj['cumulative_range'][0]:.6f}–{inj['cumulative_range'][1]:.6f}. Tots dins 0,90–1,10. A 24–40 el transport és empíric i condicionat a beta; **no** és una nova prova absoluta RAW → CameraRaw.
- Mateixos detectors de limbe: arcs RMS 68,5831 → 68,5888 DN16; màxim local 241,483 → 241,863; canvi màxim d'un bin del perfil compost 31 DN16. Els llindars absoluts antics de monotonia estricta, graó 2% i arc local <100 ja fallaven a V53/V54/V55. Es conserven i es declaren; no s'han canviat per obtenir PASS.
- Llenç complet i Lluna nativa de 1400² inspeccionats, aquesta darrera amb llum de diagnòstic ×2 i resolució original: cap costura nova visible respecte de V55. La foto lliurada conserva la llum desada. Judici estètic de Pere pendent.

## Represa i reproducció

Arrel canònica `{ROOT}` sense Git. Codi `{HERE}`; dades i rebuts `{OUT}`. Llegir AGENTS, CLAUDE sencer, estats i IA README → ESTAT → MAPA abans de mutar; adquirir un claim nou. Els scripts exigeixen el claim d'aquesta campanya i diverses sortides exclusives: **no** importar-los ni rellançar-los amb el claim alliberat o sobre els fitxers existents.

Ordre productor: `a0_freeze.py`, `a1_clean_frames.py`; exploració B0/B1/B2 i C0/C1/C2/C3; R0/R1/R2/R3 negatius; `r4_red_repeatability.py`, `r5_red_detector_photo.py`, `r7_red_external.py`, `r8_supported_photo_band.py`, `r8_exact_retention.py`, `r9_red_injections.py`, `r10_profiles.py`, `r11_photo_injections.py`, `r12_photo_external.py`; qualificació R13; `e0_package.py build`, `verify`, `gate`, `readback`, `publish`. La congelació de R13, F0 i QA visual està als seus rebuts; són passos d'orquestració explícits, no subcomandes amagades. Runtime `/Users/USUARI/.venvs/eines-ia-py312/bin/python`, `PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=2 OMP_NUM_THREADS=2`.

Pròxima recerca útil: resposta òptica/temporal o calibració que permeti distingir senyal lunar de llum solar en el vermell, amb un nou contrast independent. No repetir l'augment de vermell R1, els pesos Fourier sorollosos o l'ajust natiu negatiu com si fossin solucions. Cap claim de màxim matemàtic ni promesa d'un altre 4–5%.

Les idees generals provenen de [Fourier Burst Accumulation, autors](https://dev.ipol.im/~mdelbra/fba/), [Local Fourier Burst Accumulation, IPOL](https://www.ipol.im/pub/art/2017/197/) i [reconstrucció multiframe RAW, Google Research](https://research.google/pubs/handheld-multi-frame-super-resolution/). Els pilots locals no són una reproducció d'aquests sistemes i les xifres d'aquest informe provenen exclusivament dels rebuts locals.
"""
with report.open('x') as f:f.write(text)
ht=f"""# Represa Codex · Earthshine V56 · 13-09-2026

Objectiu de Pere «millora el detall de earthshine provant les 3 sudgerències»: les tres vies s'han executat; V56 fotogràfica lliurada. Increment d'amplitud 24–40 d'aproximadament2,4–2,9% dinsr435; no percentatge de nova informació/resolució. Judici visual de Pere pendent.

- Producte `{pub['path']}`, SHA `{pub['sha256']}`, {pub['bytes']}bytes,10551×7506RGB16,26capes. V55/V54/V53 i88RAW exactes.25capes, màscara/alfa/geometria exactes; nomésRGB25 i nom canvien. Diferències R−G/B−G exactes; cap nou CameraRaw.
- Informe complet `{report}`; manifest `{manifest}`. Codi `{HERE}`; output `{OUT}`. Llegir l'informe abans de reprendre: inclou tots els negatius i els límits de validació.
- Productor **R4 → R5 + R8**. R4: patró vermell de67Vixen repetible en dues meitats, mateix operador global deV55. R5: petita retirada del detector vermell a la foto (±7DN16). R8: acord R/G net com a confiança per reforçar4%màxim la font preCR24–40 ja existent, beta0,707351 als sectors parells; resultat fotogràfic2,4–2,9%. No substituir la foto per la font vermella més sorollosa.
-93/93 coincidències deV55 preservades. Sony fotogràfica és retenció; la base ja contéSony. Fonts R independents deSony: correlació2D24–40 0,4140→0,4864. Cap píxel Sony/LROC al productor Vixen.
- R9:360injeccions de font comunes ambtransferència1 i6controlsdetectorresidu0,359–0,682. R11:288novabandacondicionals1,02066–1,03905 i48controls acumulats40–64 amb respostaCameraRaw nativa anterior1,00434–1,06322. A24–40 la resposta és empírica; no és una prova absoluta RAW→CameraRaw.
- **Negatius**: B0/B1Fourier empitjoren diversesbandes; B2fase només1/12passa,no canvi geomètric. C1CFAverd natiu téoperadorpixel positiu correcte; C2transferència0,49falla; C3banda limitada passa0,905–0,926 però empitjoraSony/LROC16–40. R1mescla vermella millora fonts però149píxelsfora de rang al limbe: rebutjada. R2/R3covariància no promoguda. R5sol molt petit.
- Contorn: mateix detector; arcs68,5831→68,5888 i màximlocal241,483→241,863; bin de perfilcompost canvia31DN16 màxim. Llindars absoluts antics ja fallenV53/V54/V55; no redefinits ni declaratsPASS. No nova cura de totl'últimlimbe niDHS.
- Photoshop real26capes, doslectors, readback{native['max_full_DN16']}DN16al llenç i{native['max_moon_DN16']}a la Lluna; documentsdePere preservats. Llenç i1400²natiusinspeccionats, sense costura nova visible. Vistes `vistes/E3_Photoshop_V56_*`.

Arrencada: AGENTS, CLAUDE sencer, estats, IA README→ESTAT→MAPA. Codi Downloads senseGit, actiusDesktop; originals/RAW/runs preservats. Claim d'aquesta campanya `{CLAIM}`; alliberament efectiu aCODEX_STATUS iF3_release.json. Aquest handoff no substitueix el lock. Nouclaim/output per qualsevol represa, capimport executable ambclaim vell. Només el propi diari; capmissatge aClaude ni agent auxiliar s'ha utilitzat.
"""
with handoff.open('x') as f:f.write(ht)
artifacts=[]
for p in sorted(OUT.glob('*.json')):artifacts.append(dict(path=str(p),sha256=sha(p)))
for p in sorted(HERE.glob('*.py')):artifacts.append(dict(path=str(p),sha256=sha(p)))
data=dict(product=pub,report=str(report),report_sha256=sha(report),handoff=str(handoff),handoff_sha256=sha(handoff),artifacts=artifacts,scope='Three routes investigated, best qualified photographicV56 delivered, no new resolution/full-limb/DHS claim',visuals=[str(OUT/'vistes/E3_Photoshop_V56_full.png'),str(OUT/'vistes/E3_Photoshop_V56_moon_x2.png')])
with manifest.open('x') as f:json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')
save('F1_documentation.json',dict(report=str(report),report_sha256=sha(report),handoff=str(handoff),handoff_sha256=sha(handoff),manifest=str(manifest),manifest_sha256=sha(manifest)));print('DOCUMENTED',flush=True)
