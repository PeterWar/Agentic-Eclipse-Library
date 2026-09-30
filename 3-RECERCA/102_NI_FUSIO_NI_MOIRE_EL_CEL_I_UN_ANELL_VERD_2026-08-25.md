# 102 · Ni fusió ni moiré: el cel per fotograma i un anell verd instrumental

**25 d'agost de 2026, tarda. Fable 5, com a tercera opinió demanada pel traspàs
`.coordination/HANDOFF_2026-08-25_FABLE5_ARTEFACTE_RESIDUAL.md`.**

Aquest document respon la pregunta del traspàs §9.2 —«una de les dues coses és
falsa: o les mesures són cegues o el que Pere veu no és el que perseguim.
Digues quina»— i la resposta és la segona, amb una precisió que canvia el marc:

> ⏭️ **El que Pere veu NO és la fusió HDR.** Són DUES coses diferents, cap de
> les dues perseguida fins avui: **(1) estructura de transparència del cel,
> variable en el temps, que cada fotograma porta amb un patró diferent** —la
> «malla de rectes»— i **(2) un anell fosc quasi circular a ~1,85 R☉ que és
> NOMÉS del canal verd, NOMÉS del tren Vixen, i és a CADA fotograma cru**
> —les corbes tancades—. La fusió, després de la coherència i les dues
> passades, deixa un residu real però **petit**: com a molt un terç de
> l'amplitud que el contorn li atribuïa, i a la majoria de fronteres una
> desena part.

L'instrument que ho decideix és nou i és barat: **el control aparellat pel
SOSTRE** (§2). La resta del document són les mesures, per orde d'execució, i al
final les respostes una a una a les preguntes del traspàs i el que queda obert.

Tots els productes i scripts d'aquesta ronda són a
`output/pilot_vixen_fable_20260825/` (scripts inclosos, un per mesura). No s'ha
tocat cap producte viu i no s'ha declarat cap cura: això és **diagnòstic**.

---

## 1 · El punt de partida, i el que ja deia una porta

El traspàs arribava amb: tres corbes tancades marcades per Pere sobre el tren
Vixen (~1,25 · 1,51 · 1,97 R☉), un arc groc a la Sony (~1,18), la coincidència
de les corbes amb nivells de frontera de fusió mesurada al llarg del contorn
(0,05–0,72 % a 2,9–4,1 σ), i una malla de rectes a ±45° al residu creuat amb
una hipòtesi d'escaquer CFA per confirmar o trencar.

⚠️ Una dada del mateix traspàs ja apuntava la resposta: **la porta H2 donava
PASS amb un terra de control de 4,32 σ i la pitjor frontera a 4,14 σ**. Un
control que dispara diu que l'estadístic no distingeix la frontera del que
l'envolta — i efectivament: el que hi havia als contorns no era (majoritàriament)
la frontera.

## 2 · El mètode que decideix: el control aparellat pel SOSTRE

Amb quinze esglaons d'1 EV **no existeix cap contorn de control lliure a
l'espai ni al nivell** (trampes del 24-08). Però hi ha un eix net que ningú no
havia fet servir per a controlar les mesures de contorn: **`PILOT_SOSTRE` mou
TOTES les fronteres de fusió alhora** —en nivell, un factor exacte; en radi,
desenes de píxels— **sense tocar ni la corona ni el cel ni el filtre**.

El control aparellat és: *mesura el MATEIX contorn (mateixa forma, mateixa
corona a sota) al producte amb el sostre mogut*. El que és de la fusió segueix
el sostre; el que no ho és, s'hi queda. La corona es cancel·la exactament
perquè el contorn és idèntic.

Existien els escombrats `_e080`, `_e075`, `_e060` (i les meitats `_mA`/`_mB` i
el `_flatno`), o sigui que el control **no ha costat cap composició nova**.

⚠️ Els rebuts d'aquells escombrats són d'abans de l'estampat de paràmetres i no
declaren el sostre; la validació és empírica i és al §3.1: la variància puja
×1,88 sota la frontera nova, la cobertura hi perd 12 mostres, i el compost és
idèntic bit a bit enlloc i al 0,000 % on el sostre no toca. Els directoris són
el que diuen ser.

## 3 · Les mesures

### 3.1 · Res del que es veu no es mou amb el sostre

**(a) Perfils condicionats al nivell.** Mitjana i σ del detall per calaix fi de
`ln(nivell)` (700 calaixos, 1,05–3,2 R☉, mateix mapa de nivell de referència
per a tots), als productes 0,85 / 0,80 / 0,75 / 0,60:

| desplaçament | esperat (ln) | mesurat |
|---|---:|---:|
| 0,85 → 0,80 | −0,061 | **0,000** (r = 0,90) |
| 0,85 → 0,75 | −0,125 | **0,000** (r = 0,90) |
| 0,85 → 0,60 | −0,348 | **0,000** (r = 0,87; σ: r = 1,000) |

Cap estructura del perfil —ni de mitjana ni de textura— no es desplaça, quan
les fronteres s'han mogut fins a 0,35 en ln.

**(b) La imatge.** Superposició R/G del detall 0,85 (vermell) contra 0,60
(verd) a les zones de les marques: **tot surt groc o blau marí** (comú); ni un
sol serrell de color. Les bandes granulars, els arcs i la malla són al mateix
lloc, amb el mateix gra, als dos productes.
(`output/pilot_vixen_fable_20260825/blink/nord151_rg_085_060.png`)

**(c) El contorn, aparellat pel sostre.** `mesura_fronteres` als MATEIXOS
nivells absoluts (els del sostre 0,85) sobre el producte 0,85 (frontera
present) i sobre el 0,60 (cap frontera a aquells nivells):

| contorn (R☉) | frontera | producte 0,85 | producte 0,60 | persisteix |
|---:|---|---:|---:|---:|
| 1,251 | t=1/16 pes→1 | 0,5605 % (3,56 σ) | 0,5075 % (3,15 σ) | **91 %** |
| 1,241 | t=1/4 pes→0 | 0,7151 % (2,86 σ) | 0,5648 % (2,28 σ) | **79 %** |
| 1,969 | t=2 pes→1 | 0,0500 % (4,14 σ) | 0,0385 % (3,15 σ) | **77 %** |
| 1,971 | t=10,08 pes→0 | 0,0474 % (3,93 σ) | 0,0352 % (2,88 σ) | **74 %** |

⏭️ **Del 74 al 91 % de l'amplitud «de frontera» NO és la frontera.** El residu
genuí de fusió (la diferència) queda acotat: ~0,15 % al pitjor contorn interior,
~0,05 % a 1,251, ~0,011–0,012 % a 1,97. Aquesta és la resposta a «per què les
dues fronteres de 1,24–1,25 són deu vegades més grosses»: perquè el que s'hi
mesura és una altra cosa, que viu allà i no es mou.

**(d) Validació de l'eix.** On el sostre SÍ que toca, els productes divergeixen
com toca: sota la frontera nova del 0,60, el compost canvia un **+0,53 %** de
mediana (el desacord sistemàtic del fotograma de 10,08 s amb els altres),
**VAR ×1,88**, cobertura −12 mostres; a 1.340–2.700 ADU/s, on cap sostre no
talla res, els dos compostos coincideixen al **0,0003 %**.

### 3.2 · La «malla de rectes» és el CEL, variable en el temps

**La prova d'un sol paràmetre que faltava (traspàs §10.5), amb el disseny
afinat: parells de fotogrames de la MATEIXA exposició a instants diferents.**
Quocient en ln dels plans G1 calibrats, alineats pel model de centres, treta la
part llisa (σ 160 px natius):

| parell | Δt | rms de la banda |
|---|---:|---:|
| 10,08 s · #0 vs #1 | 13,1 s | 0,195 % |
| 10,08 s · #1 vs #2 | 13,4 s | 0,104 % |
| 10,08 s · #0 vs #2 | 26,5 s | 0,238 % |
| 2 s · #0 vs #1 | 2,9 s | 0,138 % |
| 1 s · #0 vs #1 | 61,7 s | 0,422 % |
| 0,5 s · #0 vs #1 | 61,7 s | 0,504 % |

I a les imatges (`output/pilot_vixen_fable_20260825/transparencia/`) s'hi veu
exactament la morfologia de la malla: **línies primes llargues i ondulades
—estries— i bandes amples onejades**, que **canvien de posició d'un parell a
l'altre** i creixen amb Δt. És estructura de transparència atmosfèrica (cirrus
prims i ones), escombrada pel vent: dins d'una exposició el patró es corre
centenars de píxels i queda **allargat en la direcció del vent**, que és el que
fa les «rectes»; dues capes de núvol amb vents diferents donen les dues
famílies de direccions.

Això explica d'una sola causa el que el traspàs §7.2–7.4 havia mesurat:

- els dos trens **no** hi coincideixen (correlació 0,24 a λ ≤ 31 px): mostregen
  el cel a instants i pesos diferents;
- les meitats A/B porten cadascuna el seu patró (mesurat aquí: les corbes fines
  surten a la diferència mA − mB);
- no es mou amb el sostre: no és de la fusió;
- és al compost ABANS de la fase 3, i als fotogrames crus.

⛔ **La hipòtesi de l'escaquer CFA (traspàs §7.5) queda REFUTADA per tres vies
independents**: (1) la línia `out[oy::2, ox::2] = cv2.resize(...)` és del model
de CEL (`cel_del_fotograma`), que el producte viu no executa (etiqueta sense
`_cel-model`); el drizzle de la fase 2 posa cada pla CFA a la seva posició
absoluta amb gota de 2,0 px i partició de la unitat; (2) la malla és present al
detall en graella NATIVA, abans del warp de 57,2°; (3) la malla és als
fotogrames individuals calibrats, abans de compondre res.

### 3.3 · Les corbes tancades: un anell fosc VERD, instrumental, a cada fotograma

El passa-alt (σ 6 px, convolució incompleta) del compost natiu ensenya una
corba tancada fosca de ~10–20 px d'ample al voltant de la corona. Mesurada amb
el mínim del perfil per nivell (calaixos fins, coordenada comuna):

| producte | mínim | fondària |
|---|---:|---:|
| viu 0,85 | 1.336 ADU/s | −0,183 % |
| e080 | 1.336 | −0,177 % |
| e060 | 1.336 | −0,177 % |
| meitat A | 1.336 | −0,199 % |
| meitat B | 1.336 | −0,138 % |
| **flat=no** | 1.336 | −0,180 % |

**Idèntica a tot arreu**: sostre, meitats i flat exculpats d'un sol cop. I les
mesures que la caracteritzen:

- **És a CADA fotograma cru calibrat**, també als curts: mediana del passa-alt
  per fotograma sobre el contorn, contra dos contorns de control veïns:
  2 s → −0,11/−0,15 %; 1 s → −0,10; 0,5 s → −0,03/−0,07; 0,25 s → −0,05/−0,09;
  els de 1/8 s arriben a **−0,4/−0,7 %** (controls: ±0,01–0,03 %). Els
  fotogrames amb el solc més fondo són els **pròxims als contactes**.
- **És NOMÉS del canal verd**: al compost, G −0,098 % contra controls −0,02;
  R −0,025 i B −0,028, indistingibles dels seus controls. ⛔ Un dèficit de llum
  real (cel o corona) sortiria als tres canals; això és **instrumental**.
- **La Sony NO el té**: al mateix lloc del cel, −0,031 % contra controls
  −0,025/−0,036. Instrumental **del tren Vixen**.
- **Està clavat en RADI, no en nivell**: seguint el mínim a 72 azimuts, el radi
  té cv 12,9 % (mediana 1,845 R☉, IQR 1,73–2,01) i el nivell cv 47,8 %. És un
  **anell quasi circular centrat prop de l'eix òptic**, no una isofota — i per
  això la coincidència amb els nivells de frontera era només aproximada, i per
  això va enganyar.
- **PRNU i màsters de fosc exculpats**: mostrejats sobre el contorn, cap
  signatura (PRNU ±0,01–0,05 % sense coherència; foscos plans a <0,01 ADU).

⏭️ **Hipòtesi de mecanisme (NO confirmada)**: la vora d'un **reflex intern
(ghost) desenfocat de la corona interior** al tren VSD90SS + R6 —un altiplà
ample de llum verda que s'acaba a ~1,85 R☉; el passa-alt en pinta la vora com
un solc fosc—. Hi encaixen el color (revestiments), el centrat a l'eix, la
presència a tots els fotogrames i la fondària més gran prop dels contactes
(quan la cromosfera i les perles disparen la font del reflex). Es pot
confirmar o refutar mirant **fotogrames de parcial** (geometria de font
diferent) o girant el cos (el ghost segueix l'òptica, la corona no).

⚠️ **Sobre les marques interiors de Pere (1,24–1,25 R☉)**: el mateix contorn
al compost té una signatura **BLAVA** —B +0,22/+0,27 % amb controls −0,25/−0,18,
G −0,05, R −0,02— o sigui **color de cel**: allà el que domina és la família
del cel per fotograma (§3.2), no l'anell verd. Les dues famílies conviuen i cap
de les dues és la fusió (persistència 79–91 % al control de sostre).

⚠️ El detall de la fase 3 es calcula **sobre el canal G** (`_filtra` rep
`hdr[..., 1]`): l'anell verd hi entra sencer, sense la dilució que tindria en
una luminància RGB.

## 4 · Respostes a les preguntes del traspàs

**§9.2 (quina de les dues coses és falsa).** La identificació, no les mesures
ni els ulls de Pere: el que es veu és real, però **no és la fusió**. La mesura
per contorn deia la veritat («hi ha alguna cosa a aquests contorns») i la seva
pròpia paradoxa —el control que dispara— deia la resta.

**§6 bis 1 (com es mesura un bony que el control no s'empassi).** Amb el
control aparellat pel SOSTRE (§2): mateix contorn, producte amb les fronteres
mogudes. La corona es cancel·la per construcció i cap densitat de fronteres no
el contamina. La porta H2 s'hauria de refer amb aquest control.

**§6 bis 2 (per què un bony i no un graó).** Per a la part genuïna de fusió
(petita), la resposta d'Opus és bona: resposta del passa-alt a la curvatura de
la rampa. Però el bony GROS no era de la fusió, i per això pujar l'ordre de la
rampa no el matava.

**§6 bis 3 (què tenen d'especial 1,241 i 1,251).** Que el que s'hi mesura és
una altra cosa: cel per fotograma (blau) més el gra amplificat, amb un residu
de fusió de només ~0,05–0,15 %.

**§9.3 (el marc).** El marc era el problema, i de la manera que el traspàs
temia: l'artefacte dominant **neix a la fase 0** (és als fotogrames: cel
variable i anell òptic), no a la composició ni als filtres. La fase 2 el
BARREJA (cada píxel, un cistell de fotogrames diferent) i la fase 3
l'AMPLIFICA, però cap dels dos el crea.

**§9.4 (el jutge).** El forat del jutge (llenç, warp, màscara, filtre
compartits) no ha estat el problema aquí; l'eix de sostre és un segon jutge
extern per a tot el que sigui de fusió, i és gratuït amb els escombrats fets.

**§9.5 (la prova més barata).** Les dues que han decidit: parells de
fotogrames de la mateixa exposició (§3.2) i el contorn aparellat pel sostre
(§3.1c). Cap de les dues no necessita compondre res de nou.

**§10 (el que Opus hauria fet).** El §10.2 i el §10.5 eren les bones —el patró
és al compost i als fotogrames— i el §10.1 (la porta de l'ACHF) era secundari:
la porta modula el GRA amb què es veu, però no crea les corbes (les zones de
transició de la porta són taques que segueixen l'estructura, no la malla;
mesurat, `output/pilot_vixen_fable_20260825/porta/`).

## 5 · El que queda obert, i per on continuar

1. **El mecanisme de l'anell verd.** Provar el ghost amb els fotogrames de
   PARCIAL (font puntual filtrada: el ghost es mou amb la geometria) o amb els
   flats girats del 24-08 (si és del tren, gira amb el cos). Si es confirma,
   la reparació honesta és **aigües amunt**: model òptic del reflex, mai cap
   màscara (norma del rectangle).
2. **El cel per fotograma.** L'anivellament i la coherència són ESCALARS per
   fotograma i el cel real té ESTRUCTURA (0,1–0,5 % rms). Les opcions, totes
   amb el jutge extern al davant: (a) acceptar-ho i documentar-ho —per a la via
   de la FOTO pot ser el cost més honest—; (b) model 2-D suau per fotograma
   restringit on el cel mana (r > 2,4 R☉), amb el perill conegut de menjar-se
   corona; (c) estimadors temporals robustos per píxel (mediana temporal
   ponderada), que maten el que no és compartit entre fotogrames — més
   agressiu i més perillós.
3. **La porta H2** s'ha de refer amb el control de sostre; la seva versió
   actual no és específica (el seu control ho deia).
4. **El residu genuí de fusió** (~0,01–0,15 %) queda acotat i és més petit que
   les altres dues famílies: no és la prioritat.
5. ⚠️ El producte `_ordre` (rampa d'ordre 7) queda a mig fer (`pas1` sol);
   després d'això, la prova perd urgència: la rampa no era el coll d'ampolla.

## 6 · On és tot

```text
output/pilot_vixen_fable_20260825/
    mira_superposar.py, vistes/          la composicio Superposar que Pere veu, al 100 %
    malla.py, malla/                     espectres i vistes de la malla als 4 productes
    bony_nivell.py, bony/                perfils per nivell + imatges de diferencia entre sostres
    blink/                               mateixa zona als 4 sostres + superposicions R/G
    meitats/                             meitats A/B, diferencia, i passa-alt del compost per zones
    porta_achf.py, porta/                mapes de la porta de soroll de l'ACHF
    transparencia_fotogrames.py,
    transparencia/                       parells de fotogrames: les bandes del cel
    compost_hp6_sencer_bin3.png          el passa-alt del compost natiu sencer (l'anell s'hi veu)
    corba_rg_*.png, solc_*.png           l'anell: superposicions entre sostres i perfils
```

Les mesures puntuals (canals, Sony, PRNU, foscos, geometria de l'anell,
fotogrames individuals, marques interiors) són reproduïbles amb
`output/pilot_vixen_fable_20260825/mesures_puntuals.py`, una ordre per mesura;
les xifres d'aquest document en són el contracte. El contorn aparellat pel
sostre és `mesura_fronteres.py` tal qual, amb `--sostre 13490.775` sobre el
producte `_e060` (§3.1c).
