# V29 — diagnòstic dels pentàgons de la capa 03 (05-09-2026)

## Acceptació de Pere i abast

Pere accepta explícitament `01 ACHF fi 2-32 · V29` i `02 Passa-alt 24 · V29`:
«Estan perfectament bé». Es conserven sense canvis. La capa
`03 ACHF azimutal 8-128 · V29` queda **no acceptada visualment** pels
artefactes marcats a `/Users/USUARI/Downloads/pentagonals.tif`.

Aquest torn és una inspecció i un diagnòstic; no s'ha substituït cap capa,
no s'ha generat una nova versió del PSB ni s'ha aplicat una correcció als
apilats. No es declara resolt l'artefacte.

## Evidència localitzada

El TIFF té el mateix llenç, 10551 × 7506. SHA-256:
`e065557384187f0f69bb3ff3febbbf936f29a831bc696321283909d5aaa8fc9a`.
Les 16 components blaves detectades delimiten diversos contorns al voltant
de la corona interior. La codificació tonal del TIFF no és idèntica a la
del ràster de la capa; s'usa per localitzar les marques, no com a radiància.

Els contorns coincideixen amb canvis de contribució de les exposicions
llargues. Revisió independent, mostres radials a −40/0/+40 px de la marca:

| Punt del PSB | Pes G abans / sobre / després | Contribució identificada |
|---|---|---|
| (6198,3638), contorn mitjà | Vixen 22,564 / 22,542 / 64,279 | tres fotos de 10 s |
| (6142,4081), contorn mitjà | Vixen 22,559 / 24,656 / 72,892 | tres fotos de 10 s |
| (6376,4342), contorn exterior | Sony 11,391 / 12,267 / 16,764 | una foto de 8 s |

Els tres Vixen `572A2982/2983/2984.CR3` aporten 3 × 10 × 2 plans G = 60
de pes, coherent amb els plateaus observats aproximadament 22,55 → 82,3.
El Sony B `DSC06993.ARW`, de 8 s, aporta 16; el pes màxim teòric sense
aquesta foto és 11,406, coherent amb el plateau 11,391. Als dos punts Vixen,
el màxim gradient del pes és 12 i 7 px després de les marques blaves.

Un canvi de pes tot sol podria ser un canvi de soroll. Per distingir-lo,
s'han revelat quatre fotogrames Vixen individuals amb la calibració,
registre, balanç i k del run 019, sense fusionar exposicions. Es comparen
en una graella polar de diagnòstic, en zones vàlides comunes erosionades
per allunyar-se de la saturació i de la vora. No són píxels independents ni
una mesura d'error estadístic de milions de mostres.

| Banda | Mediana G(2 s)/G(1 s) | Mediana G(10 s)/G(2 s) |
|---|---:|---:|
| 1,5–2 R☉ | 1,0006 | 0,9602 |
| 2–2,5 R☉ | 1,0004 | 0,9582 |
| 2,5–3 R☉ | 0,9958 | 0,9455 |
| 3–3,8 R☉ | 0,9907 | 0,9338 |

Comparadors: `572A2978.CR3` (1 s), `572A2979.CR3` (2 s),
`572A2982.CR3` (10 s). El desnivell de radiància entre aquests 2 i 10 s
és mesurable, aproximadament 4–6% al voltant dels contorns estudiats;
no és només una diferència de variància. No s'ha comprovat encara si totes
les fotos dels grups mostren el mateix biaix ni el seu origen físic.

**Diagnòstic:** hi ha evidència forta de costures de fusió HDR amplificades
per la capa 03. La forma segueix les isòfotes de la corona i els límits de
validesa de les exposicions llargues, cosa que explica els contorns
poligonals en lloc d'un cercle solar perfecte. Al contorn Sony s'ha
identificat el canvi de contribució, però queda pendent la comparació
radiomètrica equivalent de 8 s contra exposicions més curtes.

## Hipòtesis contrastades i límits de la QA anterior

- Els contorns ja són visibles abans del suavitzat i d'H1. H1 els accentua:
  a la zona d'1,9–2,5 R☉ afegeix aproximadament 0,10 de nivell de gris;
  no és la causa única. La representació tanh també n'amplifica l'aparença.
- La resposta de l'operador angular amb escales físiques constants varia
  amb el radi. Una prova sintètica ho demostra, però substituir-lo per
  angles fixos **no elimina** els contorns observats. Aquesta variant es
  conserva com a ablació rebutjada, no com a correcció.
- La correlació entre trens i un control de senyal purament radial no
  detecten necessàriament costures que segueixen isòfotes no circulars.
  L'acceptació visual anterior de la capa 03 era insuficient: les marques
  de Pere constitueixen un cas de fallada que ha d'entrar a la verificació.
- La correcció s'ha d'investigar a la consistència radiomètrica dels grups
  d'exposicions usats per a la 03. Un ajust global, additiu o per intensitat
  encara no està justificat: cal separar els efectes i contrastar-los amb
  fotogrames reservats abans d'aplicar-lo.
- Les marques són localitzadors, mai màscares d'esborrat. No s'ha fet cap
  retall circular o poligonal, ni canvi de FOV, ni modificació d'01/02.

## Reproducció

Codi i rebuts: `research/tools/v29_pentagonals/`.

- `diagnose.py`: marques, comparació de fases i fonts Vixen/Sony.
- `ablate.py`: lineal/tanh/H1, escala angular i control sintètic.
- `frame_oracle.py`: quatre exposicions individuals, radiància i validesa.
- `single_frame_gain_check.json`: comparació quantitativa entre fotografies.

Vistes: `/Users/USUARI/Desktop/Eclipse 2026/IA/output/v29_pentagonals_20260905/`.
`MARQUES_llenc_sencer.png` i `DIAG_05_capa03_llenc_sencer.png` mostren el
llenç complet; els altres panells són ampliacions o controls addicionals.
El gris als controls de fotogrames indica manca de dada vàlida d'aquella
exposició; no és una proposta de màscara per al producte.

Fonts: run Vixen 019, run Sony 016, `research/tools/v29/cau_final/`,
`f2.finestra`, `prepare_final_grid.py` i el TIFF de Pere. Tot en lectura.
