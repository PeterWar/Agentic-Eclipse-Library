# 106 · La lluminància de Brno i la cura RGB: el producte final del pilot

**Data:** 25 d'agost de 2026, nit. **Agent:** Fable 5.
**Mandat de Pere:** «avança com creguis tu més convenient per finalitzar el
projecte» — executat sota la norma zero (cap adopció sense jutge extern) i
amb totes les mesures als rebuts.

Aquesta ronda executa les dues conseqüències pràctiques del mecanisme tancat
del `104` §7 (cada canal compon cada radi amb un joc de fotogrames diferent i
el cel canviava) i del contrast amb Brno del `105`: **(1) el detall de la
fase 3 passa de G sol a una LLUMINÀNCIA**, i **(2) la cura del cel per
fotograma s'estén a R i B**. La primera queda **APROVADA pel jutge extern**;
la segona surt **EMPAT als dos jutges** i s'adopta com a *compleció* de la
cura G ja aprovada, no com a cura nova. El producte final és a
`output/pilot_vixen_fable_20260825_lliurament/`.

---

## §1. El detall sobre lluminància: PASS del jutge i mig camí de l'anomalia

**El canvi.** La fase 3 de la Vixen filtrava `hdr[...,1]` — el canal G sol.
És exactament la porta que l'escola de Brno té tancada («els filtres
s'apliquen només al component de brillantor», tesi 2014 §3.1.1; `105` §4) i
per on entren les estries de la barreja verda. Ara el detall es computa sobre

    ln L = (ln R + 2·ln G + ln B) / 4

(mitjana geomètrica amb el verd a pes doble — el mostreig Bayer el dona dues
vegades, i és la tria de Brno), amb la variància propagada exacta
`var(ln L) = (vR/R² + 4·vG/G² + vB/B²)/16` (plans Bayer independents). Els
guanys de color són constants additives en ln i el NRGF/ACHF les ignora.
Codi: `output/pilot_vixen_fable_20260825/fase3_lluminancia.py`.

**El cost és nul i el guany és mesurat:**

| mesura | G sol (fins ara) | LLUMINÀNCIA |
|---|---:|---:|
| cobertura amb dada | 95,89 % | **95,84 %** (−0,05 punts) |
| detall declarat (contrast) | 0,225 % | **0,229 %** |
| portes H1 / G / rectangle / llisa / soroll | PASS totes | **PASS totes** (soroll 0,40 σ) |
| **jutge extern (Δz aparellat, Sony d'àrbitre)** | referència | **+0,00686 ± 0,00221 → PASS (3,1 σ)** |
| **mètrica de Pere** (excés del detall als seus traços) | −8,54·10⁻⁴ | **−4,04·10⁻⁴ (−53 %)** |

El PASS és **més gran que el de la cura del cel mateixa** (+0,00305) i el
guany es concentra a 1,10-1,30 R☉ —justament on l'opció B fallava— i a
2,10-2,60, on el cel domina i les estries del G pesen més.

⏭️ **Aquest és el contrari exacte de l'opció B del `104`**: l'arbitratge
cromàtic esborrava l'anomalia del tot (−14,5 → +0,3) però **pagant detall
real** (jutge −0,0148, FAIL); la lluminància en treu la meitat **guanyant**
acord entre trens (+0,0069, PASS). No esborra: **dilueix** l'anomalia només-G
amb el pes que G té dins L, i alhora suma la informació real de R i B. La
tria A/B queda superada per una tercera via que domina les dues en el criteri
del jutge.

⚠️ **El que la lluminància NO fa**: l'anomalia fina continua sencera **dins
del canal G del compost** (−14,7·10⁻⁴ al hp8, intacta); el que canvia és el
producte de detall que es mira. I l'estructura només-G real (corona E,
Fe XIV) queda diluïda amb el mateix factor — el jutge diu que el balanç
global és clarament positiu, però qui vulgui la corona E pura ha de mirar el
detall G, que es conserva al costat.

## §2. La cura del cel a R i B: EMPAT als dos jutges, adoptada com a compleció

**El canvi.** La mateixa arquitectura v4 aprovada a G (`103`): referència t²
de zones a pes ple, S_i suau amb la fuita de registre treta, ΔC = Σ(w·S)/Σw
amb els pesos de la fase 2, banda λ<500 px, rampa 1,15→1,22 R☉. Codi:
`output/pilot_vixen_fable_20260825/cura_cel_rgb.py`; compost amb els tres
canals curats a `output/pilot_vixen_fable_20260825_curargb/`.

**Les amplituds segueixen el mecanisme**: correcció del 0,11 % (G, la
d'abans), **0,18 % (R)** i **0,34 % (B)** — el blau és el pitjor, coherent
amb G/B = 2,62 de diferència de retenció (el B és el canal amb la barreja
temporal més allunyada).

**Els dos jutges surten EMPAT:**

- **Jutge cromàtic** (nou, `jutge_cromatic.py`: correlació entre trens dels
  camps ln R−ln G i ln B−ln G, banda 12-125 px q, Δz aparellat per sector):
  **EMPAT −0,004 ± 0,012**. ⚠️ I amb una lliçó: les correlacions cromàtiques
  entre trens valen **0,55-0,98** — els dos trens comparteixen el cel I són
  càmeres Bayer amb patrons de retenció semblants, o sigui que **part de
  l'artefacte mateix està correlacionat entre trens** i aquest jutge hi és
  parcialment cec. Confusor nou, documentat aquí.
- **Jutge del detall en lluminància** (la cura R/B hi entra per L):
  **EMPAT exacte +0,00007 ± 0,00017**. Coherent per construcció: la banda de
  la cura (160-500 px) i la del detall ACHF (σ 2-32) gairebé no se solapen.

**La decisió, i per què no viola la norma zero.** La cura R/B **no es declara
bona pel jutge** — es declara **inofensiva pels dos jutges i mecànicament
fundada**, i s'adopta pel motiu següent: la cura G aprovada, tota sola,
deixava el camp cromàtic pitjor que abans (G sense estries, R/B amb les
seves: un desequilibri cromàtic **fabricat per la nostra pròpia cura**).
Estendre-la als tres canals és **completar una correcció ja aprovada**, que
és exactament la «cura de fons» que el `104` §7 va deixar recomanada i que
`CLAUDE.md` recull. És reversible: `_cura` (G sol) queda intacta i les deltes
són al disc per separat.

## §3. El producte final

`output/pilot_vixen_fable_20260825_lliurament/` (enllaços simbòlics a les
peces adoptades — cap còpia):

- **compost Vixen**: `curargb` (cel per fotograma curat als 3 canals, sostre
  0,85, coherència, efemèrides) — l'**opció A** del `104` executada fins al
  final;
- **detall Vixen**: lluminància (§1); el detall G es conserva al costat;
- **Sony**: compost i detall **vius** (la cura Sony continua refusada, `103`);
- **fusionat** `dos_trens_filtrats/`: cobertura 80,8 % del rectangle, mana la
  Vixen al 21,3 % i la Sony al 59,5 %, **G PASS** (excés 1,06), **rectangle
  PASS**, frontera Vixen/Sony al 0,46 % del rectangle;
- **projecte Photoshop** `photoshop/Eclipsi_2026_dos_trens_LLUM.psb`: base
  calibrada + detall fusionat + un filtre per capa (passa-alt, desenfoc
  radial i azimutal, NRGF, FNRGF, MGN, WOW, NAFE), capes en Superposar i
  apagades, com Pere treballa.

Vistes d'inspecció a `output/pilot_vixen_fable_20260825/entrega/`:
`anim_vixen_detall_G_vs_LLUM.gif` (el canvi de §1),
`anim_vixen_cura_RB.gif` (§2 vist al detall),
`anim_vixen_color_cura.gif` + `color_abans/despres_curaRB.png` (§2 en color).

## §4. Cues obertes, per ordre de valor

1. **La Sony en lluminància**: pendent perquè el seu llenç només guarda la
   variància del G (`SONY_D_verd`); cal refer la composició Sony desant D per
   canal. El fusionat actual aparella Vixen-L amb Sony-G — asimetria
   documentada, jutjada PASS igualment.
2. **L'anell verd de ~1,97 R☉**: encara al canal G del compost (cap model no
   ha passat els seus controls); al detall en lluminància queda diluït ×~0,5.
   La cura de veritat és de captura (2027, §1 quater).
3. El solc de 1336 ADU/s per fotograma individual: re-explicar-lo dins del
   marc de finestres de retenció (`104` §7, cua honesta).
4. La regressió Sony a r = 1,263/1,266 (deute del traspàs de Codex).

## §5. Rebuts

- `output/pilot_vixen_fable_20260825_curargb/cura_cel_rgb.json` (deltes,
  stats per fotograma, paràmetres del pilot);
- `output/pilot_vixen_fable_20260825_cura/fase3_fisiques_flat-si_coh_llum.json`
  i `..._curargb/fase3_fisiques_flat-si_coh_llum.json` (portes, SHA);
- `output/pilot_vixen_fable_20260825_lliurament/fase3_dos_trens.json`;
- registres d'execució a `output/pilot_vixen_fable_20260825/*.log`.

Tots els jutges d'aquesta ronda s'han corregut amb el mateix àrbitre
(`filtres_sony_coh` viu) i la mateixa referència declarada al rebut de cada
ordre; cap paràmetre del pilot no s'ha tocat (`PILOT_SOSTRE` 0,85, voltes,
sigmes ACHF idèntics).
