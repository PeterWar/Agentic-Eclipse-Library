# Metodologia DXOMark, SNR, ISO i normalització per al rànquing de càmeres

Data: 2026-07-28

Estat: **incorporat al body of knowledge; font històrica contrastada**

## Abast i procedència

Aquesta nota incorpora l'article de Guillermo Luijk
*DXOMARK para fotógrafos. Fujifilm X100*, creat el 24 d'abril de 2011.
L'URL facilitada actualment retorna 404 i el certificat del domini està mal
configurat. S'ha recuperat la captura de Wayback Machine del
26 de setembre de 2020.

La còpia arxivada acaba literalment a mitja frase en la secció de rang
dinàmic. Per tant:

- és una bona introducció conceptual;
- no és una especificació completa del protocol DXOMark;
- les seves regles històriques sobre ISO no es traslladen automàticament a
  sensors moderns;
- els punts operatius s'han contrastat amb DXOMark i Photons to Photos
  actuals.

## Què aporta Luijk i es conserva

### 1. RAW és preferible a JPEG per caracteritzar el sensor

Mesurar abans del demosaic i del processament JPEG evita barrejar nitidesa,
reducció de soroll, corbes tonals i estil de revelat. També permet provar el
cos sense que l'objectiu domini el resultat.

**Matís necessari:** això no converteix el RAW en dades necessàriament
verges. Les correccions internes, l'escalat de canals, els anells, el
filtratge d'estrelles, el black clipping o el banding poden estar baked-in.
DXOMark caracteritza la cadena sensor-electrònica-RAW, no el silici nu ni la
integritat astrofotogràfica completa.

### 2. ISO nominal i ISO mesurat no són el mateix

L'ISO nominal és l'etiqueta del fabricant. L'ISO mesurat relaciona
l'exposició al pla focal amb la proximitat del RAW a saturació. Un ISO mesurat
més baix que el nominal no és per si sol un sensor pitjor: sovint representa
més headroom de llums.

Però en el nostre projecte la diferència **no és irrellevant operacionalment**:
amb temps d'obturació fixats, bràqueting d'eclipsi o automatització sense
feedback, el headroom, el clipping i el mode de lectura continuen important.

Guardrail:

> Les taules del projecte diran «ISO 3200 nominal/configurat» o «ISO setting
> 3200». No assumiran que dues marques reben exactament la mateixa exposició
> RAW perquè comparteixen el mateix número ISO.

### 3. El guany ISO no crea fotons

Una multiplicació digital posterior a l'ADC no millora l'SNR de captura i pot
malbaratar headroom. El guany analògic previ a l'ADC sí que pot reduir el pes
relatiu del soroll electrònic posterior i de quantificació.

La divisió de 2011 entre ISO «real» i «forçat» és pedagògicament útil, però
avui és massa binària. Un canvi d'ISO pot combinar:

- guany analògic;
- canvi de conversion gain;
- canvi de cadena ADC o de mode de lectura;
- profunditat de bits diferent;
- multiplicació digital;
- metadades o preprocessament intern.

Per tant, no s'adopta com a regla general que tot ISO superior a
1600 o 3200 sigui digital. Es consultarà la corba específica de gain, read
noise, saturació i mode RAW de cada cos.

### 4. Full SNR, SNR 18% i rang dinàmic responen preguntes diferents

La corba Full SNR descriu l'SNR aleatori al llarg del nivell de senyal.
SNR 18% descriu una zona ben exposada. El rang dinàmic redueix la corba a la
distància entre saturació i un llindar inferior d'SNR.

DXOMark usa per al rang dinàmic d'enginyeria un llindar `SNR = 1`
(`0 dB`). Photons to Photos diferencia aquest criteri del seu Photographic
Dynamic Range, que usa un llindar perceptual i una normalització de cercle de
confusió.

Conseqüències:

- SNR 18% no és inútil, però diu poc sobre subs curtes limitades per read
  noise o sobre l'aixecament extrem del fons.
- El rang dinàmic és útil per a headroom i ombres, però **no és sinònim de
  l'SNR d'un objecte DSO feble**.
- Una sola xifra de rang dinàmic no inclou QE espectral, flux de cel,
  dark current, artefactes espacials, duty cycle ni calibratge.

### 5. El millor sensor DXOMark no implica la millor càmera

El resultat real també depèn de l'òptica, muntura, vinyetatge, resposta
espectral, RAW baked-in, temperatura, obturador, búfer, targetes, potència i
automatització. En el nostre cas també depèn de `gphoto2`.

Aquesta separació queda formalitzada en tres capes:

1. **Física aleatòria:** fotons, QE estimada, read noise, dark current,
   quantificació, saturació i escala espacial.
2. **Integritat RAW:** anells, filtratge, banding, amp glow, black clipping i
   calibrabilitat.
3. **Sistema de camp:** gola de muntura, fiabilitat gPhoto2, targetes,
   alimentació, buffer, recuperació de fallades i paisatge.

Un bon valor a la primera capa no pot compensar un veto a la segona o tercera.

## Screen, Print i la normalització correcta

La interfície actual de DXOMark defineix:

- **Screen:** mesura per píxel natiu, vista al 100%;
- **Print:** RAW normalitzat a una sortida comuna de 8 MP.

La normalització Print evita castigar injustament un sensor de més resolució
quan la fotografia final es compara a la mateixa mida. En reduir una imatge,
el soroll aleatori de píxels independents es promedia.

En el cas ideal de soroll aleatori no correlacionat, si es redueix de `N`
píxels natius a `N0` píxels finals:

```text
SNR_normalitzat = SNR_píxel × sqrt(N / N0)
SNR_normalitzat_dB = SNR_píxel_dB + 10 × log10(N / N0)
ΔDR_EV = 0,5 × log2(N / N0)
```

Per exemple, reduir de 40 MP a 10 MP duplica idealment l'SNR: `+6,02 dB`,
equivalents aproximadament a `+1 EV`. Aquesta millora no es pot presumir per
a banding, anells, quatre sectors, amp glow, filtratge d'estrelles ni altres
artefactes correlacionats.

Però Print continua responent al problema DXOMark de sortida a 8 MP. No
reprodueix automàticament:

- el mateix SQM;
- el mateix f-ratio;
- la mateixa exposició de 10, 15 o 30 segons;
- la mateixa escala angular i PSF;
- el mateix espectre OSC;
- la mateixa temperatura;
- el mateix temps mort.

Per això el gràfic Print Dynamic Range de la conversa de Cloudy Nights és un
**control extern útil**, no la mètrica principal del nostre rànquing DSO.

## Aplicació al model DSO de Pere

### Llindar natiu de subexposició

Per al model `Temps +5%` a igual f-ratio i SQM:

```text
P_i = P_A7S
      × (pitch_i / pitch_A7S)^2
      × (eta_i / eta_A7S)

t_+5% = RN_i^2 / [(1.05^2 - 1) × P_i]
       = 9.7561 × RN_i^2 / P_i
```

Usar `10 × RN²/P` és una aproximació transparent: produeix un increment de
soroll d'aproximadament el 4,88%.

El flux `P_A7S = 2,86 e-/s/píxel` ja està ancorat empíricament a l'A7S.
Per tant, l'eficiència entra com a **quocient relatiu**. No s'ha de tornar a
multiplicar per una QE absoluta i comptar-la dues vegades.

Limitacions:

- les QE de Photons to Photos són ajustos broadband derivats, no mesures
  espectrals directes;
- per H-alfa o càmeres modificades cal una resposta separada;
- un proxy de família s'ha d'etiquetar i portar interval;
- si no hi ha QE específica, el temps ajustat serà `N/A` o es mostrarà
  explícitament com a escenari proxy, mai com a mesura.

### Comparació a sortida angular comuna

`Temps +5%` respon al píxel natiu. La comparació final entre resolucions ha de
portar cada cos a la mateixa escala angular/PSF i calcular:

```text
SNR = senyal / sqrt(
    shot objecte
  + shot cel
  + dark current
  + lectures × RN^2
  + quantificació
  + variància de calibratge
  + variància sistemàtica
)
```

La mètrica física primària continua sent `SNR² per segon de rellotge` —o el
seu recíproc, temps fins a un SNR objectiu— a sortida comuna. Això incorpora
l'avantatge de reduir una imatge de molts megapíxels sense fingir que cada
superpíxel només ha patit una lectura.

### Rang dinàmic

El rang dinàmic d'enginyeria continua a la taula com a diagnòstic:

```text
DR_eng = log2(saturació_electrons / read_noise_electrons)
```

No s'usarà com a substitut de l'SNR DSO ni es tornarà a sumar al score físic
si aquest ja incorpora read noise i saturació. Per a paisatge, el DR
normalitzat a sortida comuna sí que conserva valor directe.

## Efecte sobre la decisió de compra

L'article **no inverteix** la recomanació condicional de la Canon R6 Mark II.
Sí que reforça quatre guardrails:

1. la diferència R8–R6 II en read noise natiu no és decisiva sense
   normalització espacial i incertesa de QE;
2. el gràfic DXOMark Print no prova l'SNR d'una sub DSO de 10–30 segons;
3. ISO 3200 i 6400 s'han d'avaluar amb el mode RAW i la corba específica de
   cada cos, no amb una regla genèrica d'ISO;
4. artefactes RAW i qualificació gPhoto2 continuen sent gates separats.

## Fonts clau

- [URL original facilitada](http://www.guillermoluijk.com/article/dxomark/)
  — actualment 404 i amb certificat mal configurat.
- [Còpia arxivada de l'article de Luijk](https://web.archive.org/web/20200926211649/http://www.guillermoluijk.com/article/dxomark/index.htm)
  — pàgina de l'autor, 2011; incompleta.
- [Luijk: corbes de relació senyal/soroll](http://www.guillermoluijk.com/article/snr/index.htm)
  — desenvolupament conceptual enllaçat per l'autor.
- [Luijk: millora en soroll pujant l'ISO](http://www.guillermoluijk.com/article/iso/index.htm)
  — guany analògic, soroll de lectura i límits del guany digital.
- [Luijk: mesura de soroll i rang dinàmic](http://www.guillermoluijk.com/tutorial/noisedr/index.htm)
  — metodologia històrica complementària.
- [Protocol actual de sensors DXOMark](https://www.dxomark.com/dxomark-camera-sensor-testing-protocol-and-scores/)
  — RAW, SNR, DR, ISO i normalització.
- [Definició actual d'ISO de DXOMark](https://www.dxomark.com/glossary/iso-speed/)
  — ISO al pla focal, guany i headroom.
- [Exemple DXOMark de Screen i Print](https://www.dxomark.com/Cameras/Nikon/D850---Measurements)
  — píxel natiu versus sortida normalitzada a 8 MP.
- [Photons to Photos: read noise en electrons](https://www.photonstophotos.net/Charts/RN_e.htm)
  — adverteix que els valors no estan ajustats per àrea.
- [Photons to Photos: engineering i photographic DR](https://www.photonstophotos.net/GeneralTopics/Sensors_%26_Raw/Sensor_Analysis_Primer/Engineering_and_Photographic_Dynamic_Range.htm)
  — llindars d'SNR diferents.
