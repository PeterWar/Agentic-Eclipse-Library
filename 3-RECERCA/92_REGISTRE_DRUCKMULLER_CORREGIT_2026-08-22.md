# 92 — La branca Druckmüller amb el registre corregit, i la rectificació de `research/91` §2.4

Data: 22 d'agost de 2026, nit. Ordre expressa de Pere després de l'auditoria:
refer les proves que li han agradat amb la geometria correcta, sobre un build
ID nou i sense tocar el workspace congelat.

## 1. Rectificació: el centre no era l'error

`research/91` §2.4 deia que la branca Gemini ancorava la geometria radial a un
centre solar escrit a mà —`sun_v = [3479.0, 2319.0]`— i que aquest valor era
«el centre geomètric de la matriu, no cap mesura», 71,2 px fora de
l'astrometria del projecte.

**Aquella conclusió era falsa.** El fitxer
`Derivats/Vixen/Corona_HDR_Vixen/LLEGEIX-ME.md` ho diu literalment:

> `hdr_vixen_countss.npy` … float32, 6958×4638×3 (R,G,B), en **ADU/s**.
> **El Sol al centre exacte (3479, 2319)**.

La matriu HDR **està construïda amb el Sol al centre**, i per això el centre
del Sol i el centre geomètric coincideixen. El valor de Gemini és correcte
**per a aquella matriu**. Vaig confondre una coincidència de disseny amb un
farciment perquè vaig comparar contra `final_solution.json`, que és
l'astrometria d'un **fotograma cru** (`572A2983`) i no de la matriu HDR.

## 2. El defecte real, i és pitjor

La matriu `M` de Gemini està ajustada amb sis estrelles les coordenades Vixen
de les quals són a la **graella del sensor**, no a la de la matriu HDR. I
després s'aplica a la matriu HDR. Les dues graelles estan desplaçades.

**Translació mesurada, HDR → graella del sensor: (+89,775, −48,647) px**, amb
σ = (0,254, 0,128) px sobre **19 estrelles** de `final_match_r6.csv`
centroidades dins la mateixa matriu HDR. Concorda amb el que ja constava a
`Corona_HDR_Vixen/alineacio_llenc_Pere.json` per a un altre fotograma
(+84,891, −44,340; la diferència de 6,6 px és la deriva de muntura entre
fotogrames).

Conseqüència: **la capa Vixen queda desregistrada 68,8 px = 0,230 R☉ respecte
de la base Sony**, i les màscares radials segueixen la Vixen desplaçada en
lloc del Sol de la Sony. El número de `research/91` era correcte; el que era
incorrecte era la causa i, per tant, la reparació.

⚠️ La primera variant que vaig construir (`build 20260822T2100Z_ab`, variant
`centre_astrometric`) movia **només la màscara** i deixava el warp desplaçat.
No arregla res i queda marcada `SUPERSEDED.md`.

## 3. La correcció

En comptes d'ajustar sis estrelles amb residus de fins a 1,27 px, la matriu
nova surt de **les dues solucions de placa del projecte**, compostes pel pla
tangent al Sol:

```text
M_lineal = A_sony · A_vixen⁻¹
```

amb `r6_radial` (22 estrelles, rms 0,424 px) i `sony_radial` (38 estrelles,
rms 0,713 px). La translació HDR → sensor es mesura amb el catàleg, dins la
mateixa matriu HDR.

**Escala i rotació no canvien**: 0,67125 i 33,089° contra els 0,671927 i
33,075° de Gemini. L'única cosa que canvia és la **translació**. La matriu
`M` de Gemini era bona com a transformació lineal; el que estava malament era
a quina graella s'aplicava.

## 4. Validació independent: el disc lunar

No es valida amb la mateixa astrometria que s'ha fet servir per corregir.
S'ajusta un cercle al limbe del disc lunar de la Vixen **ja deformada**,
mirant el gradient a 144 azimuts, i es compara amb el Sol astromètric de la
Sony:

| Warp | Centre del disc lunar | Radi | Residu de l'ajust | Distància al Sol Sony |
|---|---|---:|---:|---:|
| original (Gemini) | (3825,16, 2763,34) | 305,58 px | 2,59 px | **69,06 px** |
| corregit | (3893,74, 2768,76) | 305,24 px | 2,57 px | **0,28 px** |

El radi del disc surt 1,019–1,020 R☉ als dos casos, coherent amb una magnitud
local d'1,03. **0,28 px** és el número que tanca la correcció.

## 5. Què es veu

A la comparativa de la corona interior, amb el warp original:

- el disc lunar no és concèntric amb la corona interior: hi ha un **creixent
  brillant** gruixut per un costat i prim per l'altre;
- apareixen **esglaons i arcs** que travessen les serpentines a mig radi, del
  costat on les dues capes no es toquen;
- les plomes polars surten desalineades entre la capa Vixen i la Sony.

Amb el registre corregit, el disc queda concèntric, el creixent desapareix,
les serpentines són contínues i les plomes polars s'alineen.

⚠️ Queda un artefacte que **no és d'aquesta correcció** sinó de la recepta
original: la màscara de limbe talla a 0,985 R☉ mentre el disc lunar en fa
1,02, i el Sol i la Lluna no són exactament concèntrics. Això deixa un anell
prim entre les dues vores. Es corregeix pujant el tall a la vora mesurada del
disc, i és una decisió a part.

## 6. Els productes

Build `20260822T2130Z_registre`, a
`output/druckmuller_centre_corregit_20260822/`. Dues variants amb **el mateix
codi i les mateixes entrades**, perquè l'A/B sigui honest:

- `warp_original/` — reproducció exacta de la branca Gemini;
- `warp_corregit/` — la correcció.

Cadascuna porta els quatre màsters de la recepta original —base Sony, overlay
Vixen apoditzat, màscara de transició i capa de detall MGN a sis escales—, més
un extra: **`EXTRA_Compost_LINEAL_float32_ADUs.tif`**, el compost sense corba
de to ni quantització. Aquest respon al que el mateix handoff de Gemini demana
a §7.3 i que el seu codi no feia: els 38 TIFF que va lliurar són `uint16` amb
`percentil 99,8 → clip → log1p`, o sigui display-referred.

Previsualitzacions i comparatives a
`IA/output/druckmuller_centre_corregit_20260822/20260822T2130Z_registre/`.

Eines: `research/tools/druckmuller_centre_corregit/`
(`build_masters_registre_corregit.py` i `detecta_python.py`, que compleix la
regla d'or de no fixar cap intèrpret). Entorn: `~/Downloads/eclipse_venv`,
Python 3.9.6, `sunkit-image` 0.5.1.

## 7. Què continua sent `EXPERIMENTAL_NOT_CANONICAL`

Tot això. El registre és correcte, però les **entrades no ho són**:

- parteix de `Sony300_apilat_v3_10fotogrames` i de `hdr_vixen_countss.npy`,
  que són **apilats històrics**, no els paquets S6 acceptats;
- l'apilat Sony v3 **ja fon `DSC06987` amb `DSC06993`** i vuit fotogrames més,
  o sigui que les dues 8 s **no** hi són com a contribucions independents, i
  això és el que `NORMES_I_AUTORITAT.md` exigeix;
- no hi ha G5.10, G5.11 ni G7.07;
- el `FOV` continua pendent de decisió de Pere.

El gate següent no canvia: pilot 1:1 sobre S6 amb les dues 8 s separades. El
que aquesta ronda aporta és que **la geometria ja no és el problema**, i que
la matriu bona i la seva validació estan escrites i són reproduïbles.

## 8. Estat

La pausa visual continua. Aquesta ronda no promociona res, no obre earthshine,
no toca cap PSB, cap RAW, cap màster S6 ni cap rebut, i no ha executat res del
workspace congelat.
