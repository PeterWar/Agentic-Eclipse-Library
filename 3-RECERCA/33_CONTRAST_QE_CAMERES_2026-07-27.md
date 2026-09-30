# Contrast QE, soroll i càmera per a l'eclipsi i DSO

Data de tancament: 2026-07-27

## Abast

Contrast del model de càlcul de PeterWar per a exposicions DSO de 10–30 s,
òptiques ràpides, moltes preses RAW i sense guiatge. Es van consultar:

- Claude via el pont local del Mac;
- OpenAI GPT-5.4 via OpenRouter;
- Google Gemini 3.1 Pro Preview via OpenRouter;
- xAI Grok 4.5 via OpenRouter.

El model OpenAI GPT-5.6 Sol es va provar primer, però l'endpoint va retornar un
format no compatible amb el client; es va substituir per GPT-5.4. Aquesta
substitució va mantenir diversitat respecte de Google i xAI, però no respecte
del Codex que dirigia l'anàlisi, també d'OpenAI.

Claude es va identificar com a **Claude Opus 4.8 via Anthropic**, no com a
Claude Opus 5 ni com un model executat íntegrament en local. El pont és local,
però la inferència no ho és.

### Correcció metodològica del 2026-07-27

GPT-5.4 no es compta com una veu independent: Codex GPT-5.6 Sol ja representava
OpenAI en l'anàlisi. La seva consulta pot servir com a rèplica intrafamília,
per comprovar consistència o regressions entre versions, però no com a
triangulació per proveïdor o llinatge.

En aquesta ronda GPT-5.4 no va aportar cap conclusió exclusiva. Les conclusions
substantives també quedaven sostingudes per fonts primàries i pel contrast
independent d'Anthropic/Claude, Google/Gemini i xAI/Grok. Per tant, retirar
GPT-5.4 del recompte independent no altera la decisió provisional sobre les
càmeres, però sí corregeix la descripció del mètode. La consulta i el seu cost
es conserven a l'auditoria històrica.

## Consens tècnic

1. La fórmula és correcta:

   `P_càmera = P_A7S × àrea_relativa × eta_relativa`

   `t = C × RN² / P_càmera`

2. Perquè l'increment total de soroll sigui exactament del 5%, el coeficient és
   `C = 1 / (1,05² - 1) = 9,7561`. El valor arrodonit `C = 10` produeix un
   increment del 4,88%.

3. La QE útil no és una propietat única i universal del model. Per comparar
   càmeres fotogràfiques cal una resposta efectiva del sistema:

   `T × QE`, incloent microlents, CFA, filtres interns i resposta espectral.

4. La comparació mínima defensable per a banda ampla és una resposta RAW verda
   o un assaig amb font i òptica comunes. H-alfa a 656,3 nm necessita una
   columna separada i el resultat depèn decisivament de si la càmera és stock o
   modificada.

5. No hi ha una taula pública homogènia de QE directa per a tots els models
   candidats. Els percentatges de Photons to Photos/Sensorgen són estimacions
   derivades i s'han de marcar com a tals. Un sensor BSI o stacked no implica
   cap percentatge numèric concret.

6. `t+5%` no és un rànquing de qualitat DSO. Només estima la durada mínima de
   subexposició perquè el soroll de lectura afegeixi aproximadament un 5% al
   soroll de cel. Cal separar-lo de:

   - eficiència fotònica i temps per assolir el mateix SNR;
   - artefactes RAW, anells, filtratge d'estrelles, amp glow i banding;
   - dinàmica i saturació;
   - control físic real amb gphoto2.

7. El binning posterior no canvia per si sol la relació
   `variància de lectura / variància de cel` del mateix sensor: en sumar N
   píxels, totes dues variàncies escalen amb N. Tampoc converteix un sensor de
   molts píxels en un sensor amb una sola lectura per superpíxel.

## Lectura del nou post de Cloudy Nights

El post nou defensa que el read noise d'alta ISO i la QE de les càmeres FF
modernes han canviat poc des de la Canon 6D. La part qualitativa és raonable,
però no elimina la preocupació de PeterWar:

- el read noise per píxel és semblant entre molts models;
- el flux de cel per píxel disminueix amb l'àrea del píxel;
- amb el mateix full frame, la mateixa òptica i subs de 10–30 s, un sensor de
  45 MP fa moltes més lectures sobre la mateixa àrea angular que un de 20–24
  MP;
- per això `RN² / (P × t)` encara pot separar materialment una R5/R5 II d'una
  R6 II/R8, malgrat que els electrons de read noise siguin semblants.

Conclusió: el soroll sí que importa en aquest estil. La frase "tots són
essencialment iguals" només és aproximadament certa si s'ignoren l'àrea de
píxel, el temps unitari i els artefactes RAW.

## Decisió provisional

- **Primera opció per comprar i qualificar: Canon EOS R6 Mark II.**
  Té píxels grans, read noise baix a ISO alt, temps `t+5%` compatible amb
  10–30 s, RAW ben documentat en proves astro i apareix a libgphoto2 2.5.34
  com `Canon EOS R6m2`.
- **Segona opció: Canon EOS R5 original.**
  És la candidata d'alta resolució més documentada i no va mostrar anells en
  els flats citats per Mark Shelley. El seu cost és una subexposició mínima
  més llarga; a 30 s queda just al voltant del llindar del 5–6%.
- **No triar la R8 sense una prova pròpia d'anells.**
  El sensor és excel·lent en soroll i preu, però Mark Shelley documenta anells
  concèntrics al canal vermell fins i tot a ISO 3200.
- **No prioritzar Nikon Z per aquest ús concret.**
  Les dades de soroll són bones, però la correcció hardcoded i els anells
  documentats són contraris a la prioritat de RAW net i calibrable de PeterWar.
- **R5 II, R6 III, Z5 II i Z6 III: no comprar a cegues.**
  Falten dades homogènies de QE i/o proves astro suficients. A més, la R5 II i
  la Z5 II no apareixen amb nom propi a la llista local de libgphoto2 2.5.34.

## Cost i privacitat d'OpenRouter

- Ús acumulat abans de la ronda: 5,62755957 USD.
- Ús acumulat després de la ronda: 5,90110697 USD.
- Cost real de la ronda, inclosos intents no compatibles: **0,27354740 USD**.
- `data_collection=deny`.
- No es van enviar fitxers privats; només el prompt tècnic explícit de recerca.

## Fonts clau

- https://www.cloudynights.com/forums/topic/1006214-best-mirrorless-camera-for-dso/
- https://www.cloudynights.com/forums/topic/942671-an-argument-in-favour-of-300mm-f28-lenses/
- https://www.markshelley.co.uk/Astronomy/camera_summary.html
- https://www.photonstophotos.net/Charts/RN_e.htm
- https://www.photonstophotos.net/Charts/Sensor_Characteristics.htm
- https://clarkvision.com/articles/digital.photons.and.qe/
- https://www.webastro.net/forums/topic/236222-test-complet-canon-eos-r6-mark-ii/
