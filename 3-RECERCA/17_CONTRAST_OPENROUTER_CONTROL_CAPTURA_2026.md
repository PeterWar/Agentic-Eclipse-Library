> **AVÍS HISTÒRIC (27-07-2026):** document superat operativament per
> `controller v0.2.3 candidate`, F3/F3B/F3M i el disseny HDR nadiu. Es
> conserva com a evidència i no és autoritat operativa.

# Contrast OpenRouter — control de captura 2026

Data: 26 de juliol de 2026  
Estat: **cinc opinions externes amb material útil; decisió depurada contra evidència pròpia**

## Objectiu i privacitat

Es va demanar una segona opinió independent sobre la ruta de producció
C2–C3:

- `gphoto2`/PTP persistent;
- RP2040/Pico + Sony Multi Terminal;
- intervalòmetre cablejat com a possible tercera via.

El text enviat descrivia els cossos i trens òptics, les mesures de latència,
les mides dels RAW, els gates superats, els errors de 2024 i el termini
operatiu de tretze dies.

No es van enviar RAW, números de sèrie, ubicacions, dades personals,
directoris ni fitxers de context del projecte. Les peticions van exigir:

- `zdr=true`;
- `data_collection=deny`;
- funcionament exclusivament a la zona de recerca, mai al camí offline de
  captura.

## Models útils

| Model sol·licitat | Model resolt | Entrada | Sortida facturada | Cost |
|---|---|---:|---:|---:|
| `x-ai/grok-4.5` | `x-ai/grok-4.5` | 1.374 | 1.270 | 0,0101504 USD |
| `z-ai/glm-5.2` | `z-ai/glm-5.2` | 1.174 | 1.001 | 0,0054432 USD |
| `deepseek/deepseek-v4-pro` | `deepseek/deepseek-v4-pro` | 1.267 | 5.821 | 0,02015138754 USD |
| `moonshotai/kimi-k3` | `moonshotai/kimi-k3` | 1.266 | 1.200 | 0,021798 USD |
| `nvidia/nemotron-3-ultra-550b-a55b` | mateix | 1.271 | 1.000 | 0,0028099 USD |

DeepSeek va facturar 5.821 tokens de sortida tot i haver rebut
`max_tokens=600`; la diferència sembla correspondre a raonament intern
facturable no limitat pel paràmetre de text final.

Intents sense una resposta final completa:

- `moonshotai/kimi-k3`: els primers intents amb raonament per defecte `max`
  no van retornar un bloc de text compatible. Una nova consulta autoritzada
  amb `reasoning.effort=low` va retornar una decisió útil però truncada;
- `google/gemini-3.1-pro-preview`: va consumir el límit i només va deixar un
  fragment final, insuficient per comptar-lo com a opinió.
- `nvidia/nemotron-3-ultra-550b-a55b`: un primer intent va fallar per un
  format de contingut no reconegut. El segon, amb extractor corregit i
  `reasoning.max_tokens=128`, va retornar text útil.

El cost acumulat final indicat per `GET /api/v1/key` va ser:

`0,13489119 USD`

Aquest total inclou els intents sense resposta recuperable i és superior a
l'estimació inicial. No s'han ocultat ni arrodonit aquests intents.

## Opinió 1 — Grok 4.5

Veredicte:

- RP2040/Pico + Multi Terminal com a ruta principal;
- dos controladors independents;
- intervalòmetres cablejats comercials com a fallback físic;
- `gphoto2` només per preparar i verificar abans de la finestra crítica.

Confiança declarada: moderada-alta, condicionada a superar en 72 hores:

- outputs inactius a boot, reset i brownout;
- límit dur de pulsació i watchdog;
- tres seqüències completes de 90 s;
- Mac desconnectat;
- recompte exacte de RAW i zero shutter encallat.

Risc principal atribuït a gphoto: un bloqueig PTP impedeix també el release
perquè control i watchdog comparteixen canal.

Risc principal atribuït al Pico: contacte encallat, rebot o hold incorrecte
sense telemetria de fitxer durant la totalitat.

## Opinió 2 — GLM 5.2

Veredicte:

- Pico + Multi Terminal com a principal;
- gphoto degradat com a fallback si la ruta física no passa el gate;
- intervalòmetre comercial acceptat com a substitut més simple del Pico.

Confiança declarada: moderada-baixa, precisament perquè el hardware físic
encara no s'ha construït.

Gates proposats:

1. 24 h: estat elèctric segur a boot/reset/brownout;
2. 48 h: un bracket físic correcte a cada cos;
3. 72 h: 90 s per cos, Mac desconnectat, recompte i EXIF posteriors.

GLM recomana congelar hardware i firmware a T−7 dies i la taula de temps a
T−3 dies.

## Opinió 3 — DeepSeek V4 Pro

Veredicte:

- trigger físic independent com a principal;
- gphoto per configuració i postflight;
- gphoto degradat com a fallback si el físic falla.

DeepSeek també proposa un gate 24/48/72 h i prohibeix:

- drenatge durant totalitat;
- firmware nou després del freeze;
- targetes o cables no qualificats;
- dispar simultani per Pico i gphoto;
- excedir la cadència demostrada.

### Errors que no s'adopten

DeepSeek afirma que un bracket cada 8 s —uns 60 RAW en 90 s— quedaria
“dins” els mínims demostrats de 5 RAW a l'A7RIIIA i 15 a l'A7III. És
aritmèticament fals: 60 continua molt per sobre de tots dos mínims. Aquests
mínims tampoc són límits de búfer; només són el màxim assajat sense drenatge.

També suggereix reduir cadència si es perd fins a un 10% de fotogrames.
Aquesta tolerància no és acceptable per qualificar la ruta final. El gate
de producció exigeix zero brackets perduts, extres o parcials en repeticions
completes.

L'afirmació que PC Remote queda limitat a 5–15 RAW mentre standalone donarà
“probablement 30+” és especulativa. Sony publica xifres de ràfega nativa,
però no equivalen a la cua PTP ni garanteixen la cadència d'eclipsi.

## Opinió 4 — Kimi K3

OpenRouter no oferia cap identificador `Kimi V3`; el model frontier
disponible era `moonshotai/kimi-k3`.

La part recuperable del memoràndum escull:

- Pico/Multi Terminal com a ruta principal;
- un controlador físicament independent per càmera;
- RAW només a SD i Mac fora del camí crític;
- gphoto degradat com a fallback.

Kimi presenta la combinació com una arquitectura híbrida: el trigger físic
és l'actuador i gphoto queda com a monitor o fallback. Aquesta formulació
només és acceptable amb un guardrail més estricte que el del model:

> durant C2–C3 no hi haurà sessió PC Remote ni monitoratge PTP a la ruta
> card-only, encara que sembli “silenciós”.

També afirma que tots els errors forenses de 2024 vivien al domini de
software, sessió o transferència. És una simplificació excessiva: el codi
i la transferència síncrona expliquen una part forta, però targeta, búfer i
estat del cos no van quedar completament discriminats.

## Opinió 5 — NVIDIA Nemotron 3 Ultra

Nemotron també escull:

- Pico/Multi Terminal com a principal;
- gphoto `PC+Camera` degradat com a fallback;
- desenvolupament físic en paral·lel i decisió en 72 h.

El seu valor diferencial és explicitar que gphoto pot ser més madur avui i
alhora tenir pitjor risc residual, mentre el trigger físic té més risc de
desenvolupament però elimina el punt comú PTP/USB.

### Errors i recomanacions perilloses que no s'adopten

Nemotron proposa verificar un “pols de 5 V” al Multi Terminal. Aquesta
recomanació és inadequada i potencialment perillosa. La interfície de
producció ha de presentar un **contacte sec/aïllat normalment obert** o una
emulació elèctrica validada del comandament; no s'injectarà cap tensió a la
càmera a partir d'una resposta d'IA.

També fixa sense prova:

- hold d'aproximadament 1 s;
- màxim de hold d'1,2 s;
- sincronització obligatòria inferior a 3 ms;
- tolerància d'una captura perduda.

Cap d'aquests valors queda autoritzat. El hold es mesurarà físicament; la
sincronització exigida serà la necessària fotogràficament; i qualsevol
bracket perdut, parcial o doble farà fallar la qualificació.

La seva regla de “si falla el Pico, promoure gphoto” també necessita una
condició absent al text del model: gphoto només pot ser promogut si Gate 8
ha superat abans les proves físiques completes.

## Consens extern útil

Els cinc models amb material útil convergeixen en cinc punts:

1. eliminar PTP, USB i transport d'imatges del camí crític és més important
   que conservar flexibilitat de configuració;
2. el Pico només és justificable com un MVP mínim de pols/release;
3. una via física comercial pot ser millor que fabricar més del necessari;
4. gphoto continua sent valuós per preflight, laboratori i fallback;
5. la decisió s'ha de tancar amb un gate dur de 72 h, no per preferència.

El consens no demostra que el Pico funcioni ni que sigui més ràpid. Només
confirma que, si supera els assajos, elimina classes de fallada que el
software PTP no pot eliminar.

## Decisió depurada del projecte

No es torna a gphoto com a única ruta principal.

Ordre de preferència:

1. **Trigger físic doble qualificat**: intervalòmetre cablejat o
   Pico/Multi Terminal, segons quin superi abans els gates.
2. **Ruta asimètrica** si només passa un canal físic:
   A7RIIIA + AP130GTX/QUADCC per trigger físic; A7III + 300 mm per gphoto
   degradat i qualificat.
3. **gphoto doble** només si Gate 8 `PC+Camera` supera físicament 20 s, 40 s,
   90 s, repeticions i fallades amb les SD definitives.

El valor específic del Pico no és augmentar necessàriament les fotos per
minut. És garantir que:

- el Mac pot morir sense aturar la taula;
- no hi ha cua d'imatges al canal de control;
- el release no depèn de libgphoto;
- cada cos pot fallar sense bloquejar l'altre.

## Gate dur de les pròximes 72 hores

### 0–24 h

- obtenir dos cables/comandaments Multi Terminal;
- confirmar manualment cinc RAW exactes per pressió a cada cos;
- validar contacte normalment obert i cap trigger a boot/reset/pèrdua de
  corrent;
- decidir si un intervalòmetre comercial ja resol la cadència sense Pico.

### 24–48 h

- implementar només `{offset, hold}` si cal Pico;
- un canal per cos, sense GPIO directe a càmera;
- límit dur de hold i release fail-open;
- seqüències de 20 s i 40 s amb recompte i EXIF exactes.

### 48–72 h

- tres seqüències duals de 90 s amb SD, alimentació i RAW finals;
- Mac desconnectat o procés mort;
- exactament cinc RAW per acció;
- zero brackets perduts, parcials o dobles;
- cap contacte premut després de reset, brownout o final de taula.

Si falla qualsevol criteri estructural, la ruta Pico s'atura i no consumeix
la setmana final. En paral·lel, el Gate 8 gphoto continua la mateixa
progressió perquè existeixi un fallback real, no teòric.

## Conclusió

La consulta externa reforça, però no substitueix, l'evidència pròpia:

> la ruta física és el millor candidat de producció si passa el gate en 72 h;
> gphoto és el millor fallback disponible, però encara no és un backend
> card-only ni té release físicament independent.
