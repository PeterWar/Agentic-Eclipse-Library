# 104 · La màscara de Pere, l'anomalia verda, i una decisió que no és meva

**25 d'agost de 2026, vespre-nit. Fable 5.** Pere ha dit «no estàs solucionant
absolutament res; el problema ha d'estar en una altra banda» i ha lliurat
**ARTEFACTE_PERE.psb**: una màscara pintada per ell que recull l'artefacte que
veu, aplicada a totes les capes, «on es veu millor és amb un passa-alt de 8 px».
Té raó en la primera part: cap cura aprovada fins ara no toca el que ell marca.
Aquest document diu què és el que marca —amb la seva màscara com a
veritat-terra—, què el mata i què costa matar-lo, i deixa la decisió on toca.

## 1 · Què hi ha exactament als píxels de Pere

La màscara: 49.278 px (0,31 %), traços a **1,42–2,15 R☉** (mediana 1,92), a
gairebé tots els azimuts (662/720). Mesures amb control aparellat (la mateixa
màscara desplaçada ±0,12 R☉ en radi):

| mesura (passa-alt σ8 en ln) | DINS | CONTROL |
|---|---:|---:|
| detall fusionat VIU | **−5,26·10⁻⁴** | −0,03·10⁻⁴ |
| detall fusionat amb la cura del cel (103) | −5,30·10⁻⁴ | −0,07·10⁻⁴ |
| compost natiu, canal **R** | −4,14 | −6,93 |
| compost natiu, canal **G** | **−20,19** | −5,49 |
| compost natiu, canal **B** | −6,88 | −6,17 |
| detall de la **SONY** al mateix lloc del cel | −0,66 | +0,14 |
| meitat A | −4,58 | −0,12 |
| meitat B | −4,67 | +0,04 |

⏭️ **El que Pere marca és una anomalia NOMÉS del canal verd (excés G −14,7·10⁻⁴
sobre control; R i B nuls), NOMÉS de la Vixen (la Sony hi és neta), present a
les dues meitats independents i als fotogrames individuals.** I la fila 2
confirma numèricament la seva queixa: la cura del cel del 103 no la toca
(−5,26 → −5,30).

## 2 · Les cures que han fallat, i per què

1. **Model de corba única** (r0(az) Fourier ajustada als seus traços): els
   traços NO són una corba (residu p90 = 59 px; és una família ramificada);
   l'excés només baixa de −14,5 a −14,2. Descartada.
2. **Arbitratge cromàtic lliure** (hpG ~ a·hpR + b·hpB): atenuació per soroll
   als regressors (a+b = 0,45); treu el 40 %.
3. **Arbitratge cromàtic amb restricció a+b = 1** (l'estructura compartida es
   cancel·la per a qualsevol a; l'ajust només tria el pes de soroll), dues
   bandes (σ8 i σ8→σ32), dues voltes: **excés −14,52 → +0,29·10⁻⁴** — l'artefacte
   de Pere, esborrat al seu propi criteri. El control simètric (R contra G,B)
   dona +9,30·10⁻⁴ = exactament la fuita del regressor (−a·anomalia = −0,66·(−14))
   — consistent amb anomalia només-G.
4. ⛔ **Però el jutge extern la REFUSA**: Δz aparellat **−0,0148 ± 0,0042**
   (la correlació amb la Sony cau, 0,9293 → 0,9138 a 1,10-1,30 R☉).

## 3 · Per què el jutge la refusa, i és física nova

La resta cromàtica de camp sencer no treu només l'anomalia: treu TOT el que és
«G que R i B no expliquen», i això inclou **estructura verda REAL**:

- **la corona E (Fe XIV 530,3 nm)** — som a màxim solar; la seva estructura és
  G-only i és COMPARTIDA amb la Sony (per això la correlació cau);
- **l'excés de nitidesa real de G**: la prova de les parcials ho ensenya
  directament — al G−R de la parcial `572A3090` hi ha un **halo fosc al voltant
  del creixent**: les ales de la PSF del canal R són més amples que les de G
  (focus cromàtic del tren). El detall fi real és més nítid a G que a R/B, i
  aquell excés és estructura real que la resta s'emporta.
- La contra-validació per la Sony no rescata la cura: κ ≈ 0 per banda (la part
  compartida no viu al residu cromàtic de la Sony, viu al seu detall pla).

⚠️ El que segueix SENSE explicar: el mecanisme físic exacte que fa que la
imatge G sola porti corbes fosques primes a 1,4–2,2 R☉ que cap altre canal ni
l'altre tren tenen. Els candidats vius: ghost/reflex intern en verd (la banda
de les parcials en va ensenyar un de fosc a l'oest del creixent), o un efecte
de sensor lligat a les files (G1/G2, dual-pixel) — la prova per plans verds ha
sortit no concloent per sistemàtics de saturació i queda pendent de fer bé.

## 4 · La decisió, i és de Pere

Hi ha DUES opcions netes i una de prohibida:

- **(A) Conservadora (estat actual)**: producte = Vixen amb la cura del cel
  (jutge +0,0031) + Sony viva. L'anomalia verda de Pere HI ÉS.
- **(B) Estètica**: aplicar l'arbitratge cromàtic. L'anomalia de Pere
  desapareix (+0,3·10⁻⁴) i el preu és perdre estructura fina verda real
  (corona E i nitidesa extra de G): Δz −0,0148 amb la Sony. Per a la via de la
  FOTO (D1: «el producte fusionat no és una mesura») és una opció LEGÍTIMA si
  Pere la tria conscientment mirant les dues imatges.
- ⛔ El que no es fa: cap versió local pintada sobre la màscara (frontera a mà)
  ni cap ajust que optimitzi el jutge.

Els dos productes són renderitzats i lliurats a Pere per a la tria visual.

## 5 · On és tot

```text
output/pilot_vixen_fable_20260825/mascara_pere/     la mascara extreta + control aparellat
output/pilot_vixen_fable_20260825_cura2/            compost amb l'arbitratge cromatic (opcio B)
    cura_gverd.json                                 rebut (kappes, exces final)
output/pilot_vixen_fable_20260825/ghost_parcials/   G-R de les parcials (l'halo cromatic)
research/103                                        la cura del cel (opcio A, jutge PASS)
```

⚠️ La porta H4 (jutge) es queda com a àrbitre del que és MESURA; per a la via
de la FOTO, el criteri final de l'estètica és de Pere — aquest document
existeix perquè aquella tria es faci amb tots els números davant.

## 6 · Afegit: els traços nous del MGN (màscara v2, 25-08 a la nit)

Pere ha ampliat ARTEFACTE_PERE.psb amb el MGN com a lupa: **12.089 px nous, set
arcs curts al nord, a 1,10-1,26 R☉** (els vells eren a 1,42-2,15). La bateria,
amb control aparellat AZIMUTAL (a aquest radi el control radial no val: la σ
canvia ×6,5 en ±0,10 R☉):

| mesura (excés DINS−CONTROL) | valor |
|---|---:|
| banda 16-64 px · Vixen viva | **+5,20·10⁻⁴** |
| banda 16-64 px · meitat A / meitat B | +3,37 / +7,86·10⁻⁴ |
| banda 16-64 px · **SONY** (tren independent) | **+5,18·10⁻⁴** |
| σ_ln teòrica (variància) | quocient 1,024 (res) |
| QUI_MANA als traços | 100 % Vixen (cap fuita de la Sony) |

⏭️ **Veredicte: NO són artefactes — són corona real.** Estructura tangencial
brillant (arcades de bucles sobre el limbe nord, on hi havia les
protuberàncies), present **als dos trens al mateix píxel amb el mateix signe i
la mateixa amplitud**, i a les dues meitats independents. És la mateixa regla
que ja va salvar les línies radials del limbe (research/76 §5 octies): el que
el segon tren reprodueix al mateix lloc és del cel, no de l'instrument. El MGN
fa la seva feina —blanqueja per anell i el que és regular sembla sospitós—,
però aquí el sospitós és bo. Vista: `mascara_pere/nous_vixen_vs_sony.png`.

⚠️ Per què a σ8 no es veien: són estructures de 16-64 px; la primera bateria
mesurava la banda equivocada — la lliçó de sempre, també per a l'amplada.

### 6 bis · La simetria del criteri (la pregunta de Pere: «i com sabem que els altres no són corona?»)

La mateixa bateria, a la banda pròpia de cada família, amb el control aparellat
que toca a cada radi:

| prova | traços NOUS (arcades, 1,10-1,26) | traços VELLS (corbes, 1,42-2,15) |
|---|---|---|
| color (compost, banda pròpia) | **R +600 · G +593 · B +593** ·10⁻⁴ — acromàtic a l'1 % | **G −14,7** · R +2,8 · B −0,7 ·10⁻⁴ — només verd |
| l'altre tren (Sony, mateix píxel) | **+5,18** vs Vixen +5,20 — ho reprodueix | **−0,8** vs Vixen −14,7 — un 5 %, res |
| meitats A/B | +3,4 / +7,9 — a les dues | −4,6 / −4,7 — a les dues |
| veredicte | **corona** | **instrument (tren Vixen)** |

Els forats de l'argument, tapats: (1) la resolució de la Sony (1,49× més
gruixuda) explicaria com a molt quedar-se al 50-70 % de l'amplitud, no al 5 % —
i les arcades en són el **control positiu**: a la mateixa zona i banda, quan la
cosa és real, la Sony la reprodueix sencera; (2) amb 49k px, l'error típic de
la mesura Sony és ~0,7·10⁻⁴: un senyal real atenuat s'hauria vist a >10 σ;
(3) l'única llum físicament només-verda és la corona E (Fe XIV), i aquella la
G de la Sony també l'hauria de veure — no la veu; (4) el punt cec compartit
del jutge (llenç/warp/màscara/filtre) no aplica: l'anomalia verda és als
fotogrames CRUS de la Vixen, abans de cap pas compartit. ⚠️ El que segueix
obert és el MECANISME de l'anomalia, no el seu origen instrumental.

## 7 · EL MECANISME, tancat — i el va destapar una observació de Pere

**Pere, mirant `anim_vixen_opcioB_zonaB.gif`: «aquestes mateixes línies es
desplacen significativament en direcció al contorn lunar».** Si l'opció B no
esborrava les línies sinó que les MOVIA, és que la resta cromàtica substituïa
la versió verda per la versió R/B **que és en una altra posició** — i això va
obrir la porta bona.

### 7.1 · Les mesures que ho claven

1. **G1 = G2 exactament** (fotogrames de 0,5 s, zona 100 % lineal: −11,8/−11,3,
   −9,4/−11,2, −6,7/−9,0·10⁻⁴; R i B a zero): l'anomalia entra ABANS del mosaic
   Bayer. No és el sensor.
2. **El contingut només-G és ortogonal a l'estructura real** (corr(Δ, Sony) =
   −0,03 mentre corr(hpG, Sony) = +0,68..+0,82; Δ16 ≈ 0,003·acromàtic): no és
   «G més nítid» (una funció parella correlacionaria); és **una funció senar**
   — un DESPLAÇAMENT.
3. **Desplaçament radial mesurat: +1,45 px a 1,15 R☉** (Δ ≈ δ·∂r hpRB, 24 % de
   variància explicada), zero més enfora com a camp global.
4. **Les finestres de retenció per canal** (G/R = 1,369, G/B = 2,615; el verd,
   més sensible, perd cada fotograma abans):

   | fotograma | G el perd a | R el reté fins | banda G≠RB |
   |---|---|---|---|
   | 0,5 s | r≈1,20 | r≈1,16 (B: 1,08) | **1,08-1,20** |
   | 1 s | r≈1,33 | r≈1,27 (B: 1,16) | **1,16-1,33** |
   | 2 s | r≈1,46 | r≈1,40 (B: 1,28) | **1,28-1,46** |
   | 10,08 s | r≈1,97 | r≈1,84 (B: 1,62) | **1,62-1,97** |

   Les marques NOVES de Pere (1,10-1,26) = les bandes de 0,5/1 s. Les VELLES
   (1,42-2,15) = les de 2/10 s. **L'anell de 1,85 = el mig de la banda del
   10,08 s.**

### 7.2 · El mecanisme, en una frase

> ⏭️ **El cel va canviar durant els 100 s (estries de transparència; la Lluna
> es mou 28,7 px) i cada CANAL compon cada radi amb un joc de fotogrames
> diferent — el verd, més sensible, perd cada fotograma abans. A cada banda de
> radi, la imatge verda és d'un «instant mitjà» DIFERENT que la vermella i la
> blava: les corbes «només-G» són les estries del cel de la barreja verda
> (que R/B no comparteixen perquè porten una altra realització temporal), i a
> la vora interior s'hi suma el desplaçament per l'ocultació lunar canviant
> (+1,45 px).** No és òptica espatllada ni sensor: és la interacció
> captura-HDR-atmosfera. El mateix fenomen de la família 1 (99-103), vist ara
> per l'eix del color.

I això **dissol la paradoxa del sostre** que el 102 deixava oberta: moure el
sostre mou les FRONTERES de les bandes, però dins de les zones d'exclusió
solapades els dos sostres expressen exactament la MATEIXA barreja de cel — per
això cap corba visible no es movia.

### 7.3 · Conseqüències per a la decisió A/B

- ⛔ **L'opció B queda DESQUALIFICADA pel mecanisme**: no treu cap artefacte —
  substitueix la realització de cel del verd per la de R/B (les línies es
  mouen, com Pere va veure) i desplaça estructura real a la vora interior
  (d'aquí el FAIL del jutge, concentrat a 1,10-1,30).
- ✅ **Recomanació: opció A** (cura del cel v4, jutge PASS) com a producte
  d'avui.
- ⏭️ La cura de fons ara té nom: **igualar la barreja temporal entre canals**
  — aplicar la cura del cel per fotograma també a R i B (i a escales més fines
  per estrat), de manera que els tres canals convergeixin a la mateixa mescla
  mitjana. I per al 2027, això reforça §1 quater de CLAUDE.md: més fotogrames
  per esglaó i monitor de transparència — el problema neix a la captura.

⚠️ Cua honesta: el solc exacte de 1.336 ADU/s del 102 §3.3 i la seva fondària
per fotograma individual queden per re-explicar fil per randa dins d'aquest
marc (la barreja per canal no viu dins d'UN fotograma); la hipòtesi de treball
és que la mesura per fotograma barrejava el senyal de les estries del cel
d'aquell instant amb el contorn triat sobre el compost.

### 7.4 · Quantificació del desplaçament de la zonaB (l'observació de Pere)

Mesurat directament entre els dos fotogrames de `anim_vixen_opcioB_zonaB.gif`
als traços de Pere (ajust `ΔD ≈ δ_r·∂r + δ_t·∂t`): **el moviment aparent NO és
un desplaçament rígid** (δ_radial +0,13 px, δ_tangencial −0,20 px, només l'1 %
del canvi explicat). El que l'ull llegeix com a moviment és **l'intercanvi de
realitzacions**: cada línia del cel de la barreja verda desapareix i al costat
n'apareix una altra de la barreja R/B — un parpelleig de patrons localment
desplaçats que el cervell integra com a translació cap al limbe (la direcció
d'organització radial de les bandes). El desplaçament COHERENT de debò viu a
la vora interior: **+1,45 px a 1,15 R☉** (§7.1, punt 3), on mana l'ocultació
lunar canviant. Totes dues coses són el mateix mecanisme de §7.2.
