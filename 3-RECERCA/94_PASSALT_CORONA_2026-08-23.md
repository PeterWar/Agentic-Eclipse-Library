# 94 — Pas alt de la corona: què s'ha resolt i què queda

23-08-2026. Pere: reapilar la Sony v3 i generar un pas alt de la corona **amb
totes les imatges apilades**, en **escala de grisos**, **sense Lluna ni
protuberàncies** i **sense artefactes de canvi de camp Canon/Sony**.

## 1. Reapilat Sony v3 — reprodueix el publicat

S'ha reconstruït el master dark de 1/4 s que faltava a l'arbre viu (35 darks,
mediana de `raw_image_visible`; validat contra l'1 s existent: mediana idèntica
i diferència 0,000 ADU) i s'ha tornat a executar `apila_sony_v3.py`.

Resultat: **correlació 1,000000** amb l'apilat publicat i p99 de la diferència
relativa **0,011 %**. Els offsets tornen a sortir iguals. La cobertura no
uniforme, doncs, **és de les dades** —els deu fotogrames van desplaçats— i no
un error d'apilat.

## 2. El pas alt

`research/tools/druckmuller_centre_corregit/passalt_corona.py`. Bandes
log-polars en **graus** (0,17°–4,9°), pesos de Wiener amb el soroll mesurat de
les **dues meitats independents** de l'apilat Sony, i tres proteccions contra
les costures:

1. **convolució normalitzada** `G(x·m)/G(m)`: la vora del camp no aporta zeros,
   no aporta res;
2. **finestra per distància a la vora, banda per banda** (3 σ);
3. **bandes en graus**: cap escala fixa en píxels que pugui dibuixar un anell.

Lluna i protuberàncies: mesurat, l'excés Hα s'acaba a **1,06–1,08 R_lluna**;
el filtre s'apaga amb rampa a 1,25–1,45 R_lluna i és neutre per dins.

Sortida: **`PASSALT_corona_gris_uint16.tif`**, un sol canal, gris 50 % neutre,
per posar en *Linear Light* o *Overlay* i dosar amb l'opacitat.

## 3. Dos errors propis, trobats mesurant

- **Doble emmascarament.** S'entrava `R = (P−F)·m` a una funció que ja fa
  `G(x·m)/G(m)`: la màscara s'aplicava dues vegades i **fabricava una vora dura
  al rim de la màscara**. Es reconeix perquè **es mou amb la màscara**.
- **Gate de cobertura llegint un pes suau.** `okf.mean(axis=0)` sobre un pes
  suau no és una fracció de cobertura: apagava tot el realçat d'1,2 a 2,7 R☉.
  Ha de ser `(okf > 0,5).mean(axis=0)`.

I un tercer, heretat de `research/93`: el **pedestal per zona de cobertura** és
una correcció de **cel** i les zones estan limitades per **isofotes de
saturació** dels 8 s; aplicat a la corona interior hi deixa un esglaó. Ara
s'esvaeix de 4 a 6 R☉ cap endins.

## 4. Què està mesurat i net

| Costura | Mesura al pas alt |
|---|---|
| vora del marc Vixen | **0,000 σ** |
| vora de cobertura Sony (la caixa) | **0,000 σ** |
| sigmoide de fusió a 2,8 R☉ | **0,105 σ** |

Les tres vores de camp que Pere volia no veure **no hi són**.

## 5. Què queda, i no es pinta a sobre

Queda **un contorn dentat a 2,475 R☉**, amb una osca a l'esquerra. Mesurat:
el màxim de |D| mitjà per radi hi cau **exactament al mateix radi i amb el
mateix valor (0,6511)** amb la màscara a 1,25 i amb la màscara a 1,72 R☉ →
**no es mou amb la màscara: és al compost**. La discontinuïtat radial més forta
de les dues capes font cau a 1,525 R☉ a totes dues, la qual cosa **no** explica
el contorn i deixa la causa oberta.

⛔ No s'ha tapat. Un pas alt és el millor detector d'esglaons que tenim; tapar
el que detecta és perdre l'única eina que els troba. La sospita és que és una
frontera de saturació/cobertura heretada d'aigües amunt, del mateix ordre que
l'artefacte F de `research/93`, i que es resol refent les fusions, no component.

## 6. Estat

`EXPERIMENTAL_NOT_CANONICAL`. Entrades: apilats històrics, no els paquets S6;
l'apilat Sony v3 ja fon `DSC06987` amb `DSC06993`. El gate S6 no canvia.
