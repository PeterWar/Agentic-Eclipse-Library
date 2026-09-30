# 56 — El menú col·lapsat és del cos, no de libgphoto2

6 d'agost de 2026, nit. Prova física executada amb autorització de Pere.
Aquest document substitueix el manual d'execució que hi havia abans: la
pregunta ja té resposta.

## La pregunta

Quan el menú d'obturació de la R6 es col·lapsa de 58 opcions a dues, ¿la
llista morta és una còpia degenerada del costat de l'amfitrió, o el cos ha
deixat de publicar-la de veritat? Discrimina-ho una sessió nova.

## La resposta: el cos

Seqüència real, tota amb el mateix cos i el mateix cable, sense tocar res
entremig:

1. `20260806T234631`, escala de setters a 0,75 s. El menú es col·lapsa a la
   **pulsació 12**. Sentinella `Unknown value 1900`, valor actual `1/320`.
   El gate s'atura al primer setter, com toca.
2. `20260806T234809`, **procés nou, sessió de gphoto2 nova**. El preflight
   refusa abans de cap mutació: el perfil planifica `1/160` i el menú viu no
   el té. Zero captures.
3. `20260806T234843`, preflight de només lectura, **una tercera sessió
   independent**: `obturació 1/320, opcions publicades: 2`. Bateria 76 %.

Tres processos diferents, tres sessions PTP diferents, el mateix menú mort.
**Tancar i reobrir no el cura.** La hipòtesi de la còpia degenerada de
libgphoto2 queda descartada: si la llista fos de l'amfitrió, un procés nou
l'hauria reconstruït.

### Conseqüència per a l'EDSDK

Tanca la porta. L'EDSDK va pel mateix protocol PTP i al mateix cos —§2.1 i
§2.2 de la seva documentació—, o sigui que rebria la mateixa descripció de
propietat degenerada. Canviar de biblioteca no arregla un cos que ha deixat
de publicar el menú. L'SDK continua tenint sentit per al sostre de transport
de 0,55 s, però ja no per a això, i no abans de l'eclipsi.

## I el llindar no és fix

| Run | Cadència | Es col·lapsa a la pulsació |
|---|---|---:|
| `20260806T184228` (missió) | 0,75 s | 82 |
| `20260806T204045` (missió) | 0,75 s | 82 |
| `20260806T234631` (banc) | 0,75 s | **12** |

Els dos runs de missió són idèntics entre ells, i el de banc cau set vegades
abans amb la mateixa cadència de grup. O sigui que **no és un comptador de
pulsacions**. El que canvia entre els dos casos:

- el `hold` és 0,25 s al banc i ~0,15 s a la missió;
- el banc va córrer **després** de la sonda d'earthshine, amb tres
  exposicions de 8 s i 26 CR3 més, o sigui amb el cos ja calent i amb feina
  acumulada;
- la bateria era del 100 % a les missions i del 76 % ara.

No es pot triar entre aquestes tres amb les dades que hi ha. El que sí que
queda establert és el pitjor cas conegut: **el menú pot morir a la dotzena
pulsació**, i llavors no hi ha cap canvi de base fins que el cos es reiniciï.

## El que això obliga a decidir

El nucli dens actual confia sis canvis de base repartits per la totalitat.
Amb un llindar que pot caure a la pulsació 12, aquesta confiança no se
sosté. Les opcions, sense triar-ne cap encara:

1. **Menys canvis de base, i els importants al principi.** Si només se'n
   poden garantir els primers, que siguin els que més valen.
2. **Àncora d'earthshine primerenca.** Ja sabem que costa 9,2 s i que el
   canvi de base són 0,42 s; posar-la aviat la treu de la zona de risc.
3. **Acceptar la base fixa** i renunciar a l'escala HDR dinàmica a canvi de
   no dependre de cap setter enmig de la ràfega.

La mesura que falta per decidir-ho és quina de les tres variables mou el
llindar. És una tarda de banc, no un run de missió.

## Estat físic en tancar

El cos ha quedat amb el menú col·lapsat i l'obturació a **1/320**, que és la
correcta. **Cal un cicle d'alimentació abans de qualsevol altra prova**: fins
llavors cap perfil que necessiti una obturació diferent de 1/320 passarà el
preflight.
