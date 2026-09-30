# 103 · La cura del cel per fotograma: la Vixen passa el jutge, la Sony el falla

**25 d'agost de 2026, tarda-vespre. Fable 5. Continuació executiva de
`research/102`** (el diagnòstic: el que Pere veu no és la fusió HDR, sinó cel
per fotograma + un anell verd instrumental).

Resum en tres línies:

> ⏭️ **La cura del cel per fotograma al tren VIXEN queda APROVADA pel jutge
> extern** (Δz aparellat **+0,00305 ± 0,00070** contra la Sony viva; totes les
> portes de la fase 3 PASS) i **el producte fusionat canònic candidat passa a
> ser Vixen curada + Sony viva**, a `output/pilot_vixen_fable_20260825_cura/`.
> ⛔ **La mateixa cura a la SONY queda REFUSADA pel jutge** (−0,00513 ±
> 0,00084): treu corona, i s'entén per què. ⛔ **La cura de l'anell verd NO
> s'ha aplicat**: el model no supera els seus propis controls i la norma zero
> mana.

---

## 1 · L'arquitectura de la cura, i el truc que la fa exacta

El pes de la composició LDIC (fase 2) **només depèn del valor CRU i de t**
—mai del valor compost—, o sigui que compondre fotogrames corregits
`J_i' = J_i − S_i` equival **exactament** a restar del compost viu:

```
ΔC(x) = Σ_i w_i(x)·S_i(x) / Σ_i w_i(x)
```

sense refer cap drizzle. `S_i` és l'estructura suau (σ = 24 px natius) del
residu de cada fotograma contra una **referència de mescla llisa** `A`, amb la
fuita de registre treta per regressió (`a·Gx + b·Gy + c` per fotograma).

**El disseny va necessitar quatre voltes, i les tres primeres van caure per
números propis** (que és com ha de ser):

| versió | referència | resultat | per què cau |
|---|---|---|---|
| v1 | el compost | volta 1: 0,141 % → volta 2: **0,240 %** | ⛔ un no-op que DIVERGEIX: la mitjana ponderada de desviacions respecte de la mitjana ponderada és zero, i iterar-ho acumula linealment |
| v2 | mitjana equiponderada | rms **1,25 %** | ⛔ el soroll dels fotogrames curts entra sencer a la referència (grumolls) i ±2 % de gradient ampli entre mescles |
| v3 | t² per fotograma | rms 0,128 % però anell intern ±0,5-1 % | ⛔ la referència inclou fotogrames dins la seva rampa de saturació i n'hereta el biaix de vora de pou |
| **v4** | **t², només zones de pes PLE** (cru < 0,2·sostre), **banda limitada** (λ < ~500 px), rampa d'arrencada 1,15→1,22 R☉ | **rms 0,110 %**, el mapa són les estries | ✓ |

El mapa de correcció final és, visiblement, **el camp d'estries diagonals del
cel** (compareu-lo amb els parells de fotogrames de `research/102` §3.2) més
les bandes de barreja per estrat a la corona interior.

## 2 · Els veredictes del jutge extern (H4)

| candidat | àrbitre | Δz aparellat | veredicte |
|---|---|---:|---|
| **Vixen curada (σ24)** | Sony viva | **+0,00305 ± 0,00070** | **PASS** |
| Vixen curada (σ24) | Sony curada | +0,00250 ± 0,00073 | PASS |
| Vixen curada variant fina (σ12) | Sony viva | +0,00106 ± 0,00086 | EMPAT → **descartada** (comença a menjar estructura compartida) |
| **Sony curada** | Vixen viva | **−0,00513 ± 0,00084** | **REFUSADA** |
| Sony curada | Vixen **curada** | −0,00569 ± 0,00088 | REFUSADA (el confusor del cel compartit queda exclòs) |

Les correlacions Vixen-Sony per banda pugen amb la cura Vixen a totes les
bandes on hi ha res a guanyar (1,10-1,30: 0,9233 → 0,9293; 1,30-1,50: 0,9387 →
0,9485; 1,50-1,75: 0,9401 → 0,9454; 1,75-2,10: 0,9252 → 0,9276).

**Per què la Sony falla el jutge i la Vixen no.** El mecanisme probable és del
tren, no del mètode: la Sony té **dos apuntaments** i el seu registre porta
residus de **rotació i compressió alt/az** (research/96); la meva regressió de
fuita només treu un desplaçament GLOBAL per fotograma, o sigui que els residus
LOCALS de registre deixen dipols d'escena dins de `S_i` — i restar-los treu
corona. Amb 14 fotogrames (contra 68) la referència tampoc no esmorteix el cel
(√11 ≈ 3), o sigui que el guany possible era petit i el dany va guanyar.
⏭️ Si algú la vol reprendre: cal una fuita de registre **per grup d'apuntament
i amb rotació** (sis paràmetres, no tres), i encara llavors el jutge mana.

⚠️ **Confusor nou documentat al jutge**: els dos trens **comparteixen el
cel** (mateixa atmosfera, instants solapats), o sigui que «el que és compartit»
no és només corona. Per això la cura Sony s'ha jutjat DUES vegades: contra la
Vixen viva i contra la Vixen ja curada de cel. Surt negativa a les dues: el
veredicte no és el confusor.

## 3 · Les portes i les mesures del producte curat (Vixen)

- Fase 3: **H1 PASS** (anells 0,4 %), costures per nivell **2,9 %** (el viu:
  4,6 %), **G PASS**, **rectangle PASS**, entrada llisa 0,02 %, soroll 0,40 σ.
- Amplituds al llarg del contorn (`mesura_fronteres`, els quatre grossos):
  1,241 R☉ **0,715 → 0,572 %** · 1,251 **0,561 → 0,500 %** · 1,969
  **0,0500 → 0,0472 %** · 1,971 **0,0474 → 0,0447 %**. El que se'n va és la
  part de mescla/fusió; el que queda és el que el sostre no mou (l'anell i
  companyia, research/102 §3.1c).
- Residu creuat a λ ≤ 31 px: **sense canvi** (correlació 0,237 → 0,239).
  ⚠️ Declarat i esperat: la cura talla a λ ≳ 50 px; la variant que baixava
  l'escala (σ12) l'ha refusada el jutge. **El gra fi de les estries queda.**
- La fusió refeta (Vixen curada + Sony viva): G PASS, rectangle PASS,
  cobertura 80,8 %, frontera Vixen/Sony 0,46 %.

## 4 · L'anell verd: intentat, i NO aplicat

S'ha provat un model d'artefacte ajustat —`A(az)·S(r − r0(az))`, r0 per
Fourier ≤ 8— i **no supera els seus propis controls**: la forma apilada surt
plana (el seguiment de la corba es perd entre les estries, que per azimut
tenen la mateixa amplitud que l'anell) i els controls R/B disparen tant com G.
⛔ **Per la NORMA ZERO, una correcció que falla els seus controls no s'aplica.**
L'intent queda a `output/pilot_vixen_fable_20260825/cura_anell_vixen.py` i el
producte es va esborrar. El camí honest continua sent el de `research/102`
§5.1: **confirmar el mecanisme** (parcials: un ghost es mou amb la geometria
de la font) i llavors modelar-lo amb dents. ⚠️ Conseqüència visible: **la
corba tancada de ~1,97 R☉ que Pere va marcar encara hi és** al producte curat.

## 5 · On és tot

```text
output/pilot_vixen_fable_20260825_cura/
    fisiques_flat-si_coh/            compost Vixen CURAT (G; R/B i VAR del viu)
        CURA_CEL_DELTA_G.npy         el camp de correcció (ADU/s)
    filtres_fisiques_flat-si_coh/    detall Vixen curat (fase 3)
    sony_llenc_comu_coh -> (viu)     la Sony es queda VIVA (cura refusada)
    filtres_sony_coh -> (viu)
    dos_trens_filtrats/              fusió: Vixen curada + Sony viva
    cura_cel_vixen.json              rebut de la cura (v4, amb la historia v1-v3)
output/pilot_vixen_fable_20260825/
    cura_cel_vixen.py, cura_cel_sony.py, cura_anell_vixen.py, despres_sony.sh
    sony_cura_refusada/              rebuts i delta de la cura Sony refusada
    entrega/                         vistes per a la inspecció de Pere
        dos_trens_CURA_r4.0.png      mateix format que la vista que Pere va marcar
        dos_trens_CURA_r2.6.png
        vixen_*_abans_despres.png    parelles abans/després per zones
    residu_cura/                     residu creuat amb la Vixen curada
```

## 6 · Què queda obert

1. **L'anell verd** (§4): mecanisme amb les parcials, després model, després
   jutge. És l'artefacte marcat per Pere que segueix al producte.
2. **El gra fi (λ < 31 px) de les estries**: fora de la banda curable sense
   perdre estructura compartida (el jutge ho ha dit amb la variant σ12). Les
   opcions de fons són les de research/102 §5.2 (estimadors temporals robustos
   per píxel), totes amb el jutge al davant.
3. **La Sony**: la seva cura demana fuita de registre per apuntament amb
   rotació (§2) — o acceptar que amb 14 fotogrames el marge és petit.
4. La **base de Photoshop** (00_BASE al llenç) encara surt del compost viu;
   si Pere valida el detall curat, cal refer `llenc` + `munta_photoshop` amb
   el compost curat perquè el PSB sencer sigui coherent.
