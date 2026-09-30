# Contrast extern i tancament tècnic v0.2.9

Data: 27-07-2026  
Àmbit: captura A7III + AP130GTX + QUADCC, gphoto2 persistent, totalitat de
98,8 s per als assajos.

## Decisió

Es manté l'arquitectura `PC+càmera` amb RAW sense comprimir a SD i només
JPEG Small/Standard al Mac. El perfil continua sent
`CANDIDATE_NOT_PRODUCTION`.

No s'han acceptat canvis de coreografia basats només en opinions de models.
Sí que s'han implementat tres millores que queden justificades pel codi i
els logs locals:

1. `wait-event-and-download` usa `2s`, `1s` o `500ms` segons la gramàtica
   documentada de gphoto2; ja no s'emet `0.5s`.
2. El timeout del pare ja no afegeix dos segons al pressupost del drenatge.
   L'ordre no es pot enviar després del deadline monotònic.
3. Si el drenatge expira i contamina el prompt, el controlador prova una
   resincronització de fins a 10 s, sempre abans de `C3−25 s`. Si recupera
   la sessió, anul·la l'HDR per dependència i conserva C3 als targets
   absoluts. Si no recupera, falla explícitament.

La tercera millora és una degradació lògica, no encara una garantia física.
Cal provar que l'A7III accepta els 12 triggers C3 amb els onze JPEG de C2
encara pendents. El run JPEG-only de 23 captures és evidència favorable,
però no va injectar un timeout real al checkpoint.

## Evidència local que governava la consulta

- El run RAW+JPEG va drenar 11 captures / 22 fitxers en aproximadament
  6,18 s.
- El run JPEG-only va drenar 23 JPEG en aproximadament 8,68 s, però va
  començar 2,875 s després de l'últim release.
- El checkpoint nou comença a `C2+4,90`, aproximadament 1,15 s després de
  l'últim release C2.
- Per tant, l'extrapolació d'11 JPEG en 4,23–4,45 s no qualifica encara el
  pressupost de 5 s.
- El checkpoint exigeix exactament 11 JPEG nous, cap ARW, cua final zero,
  recompte total coherent i `capturemode` writable.
- `sensorcrop=Off` correlaciona amb ARW full-frame `6048×4024`, però encara
  falta la prova inversa amb APS-C activat.
- `3008×2000` no identifica tot sol el mode full-frame: també pot aparèixer
  amb una combinació APS-C/M. Per això es mantenen simultàniament el gate
  directe `sensorcrop=Off` i la sonda funcional `3008×2000`.

## Claude local

La primera ronda va arribar al màxim de 12 iteracions mentre inspeccionava
el projecte i no va emetre veredicte. La segona va rebre el dossier
verificat i la instrucció de no usar eines.

Conclusió útil de Claude:

- l'estructura general se sosté;
- el pressupost de 5 s encara és una hipòtesi;
- el `+2 s` del timeout i la unitat `0.5s` eren defectes demostrats;
- l'HDR ha de dependre del checkpoint, però C3 ha de quedar independent;
- tres repeticions serveixen per cribrar, no per defensar una probabilitat
  d'èxit pròxima al 95%; la finestra escollida necessita almenys deu runs;
- s'ha de reproduir exactament l'offset d'1,15 s, no un drenatge manual més
  madur.

Punt descartat: Claude va atribuir massa directament els 6,18 s a onze RAW
escrits a SD. Aquell run transferia RAW+JPEG al Mac i no és equivalent a la
ruta vigent JPEG-only. L'escriptura RAW a SD pot influir el buffer, però la
causa i la magnitud s'han de mesurar, no inferir d'aquella xifra.

## OpenRouter

No es va enviar cap fitxer del projecte. El prompt contenia només un resum
tècnic no sensible i la política de dades va ser `deny`.

### Respostes utilitzables

| Model demanat | Model resolt | Tokens entrada | Tokens sortida | Cost |
|---|---|---:|---:|---:|
| `nvidia/nemotron-3-ultra-550b-a55b` | el mateix | 1.454 | 4.000 | 0,01340875 USD |
| `google/gemini-3.1-pro-preview` | el mateix | 1.470 | 4.465 | 0,05652 USD |

Consum acumulat abans de la ronda: `4,95978336 USD`.  
Consum acumulat després de la ronda: `5,179346907 USD`.  
Increment total, inclosos intents sense text utilitzable:
**0,219563547 USD**.

També es van intentar Gemini Pro latest, Grok 4.5 i Kimi K3. El client va
rebre respostes en un format no textual compatible —probablement contingut
de raonament sense `message.content` final dins el límit— i no en va poder
extreure cap dictamen. No s'inventa ni es resumeix una resposta absent.

### Consens útil

Gemini i Nemotron coincideixen en:

- mantenir la separació RAW a SD / JPEG petit al PC;
- no considerar qualificat el límit de 5 s;
- mesurar separadament cua zero i instant en què `capturemode` deixa de ser
  readonly;
- provar finestres més curtes en lloc d'assumir que `2s` és òptim;
- conservar C3 per sobre de l'HDR;
- validar `3:2`, mida JPEG i sensor crop amb un test funcional.

### Suggeriments descartats o posposats

- **Canviar a `capturetarget=card`: descartat.** Contradiu la ruta Sony
  verificada `PC+càmera` / `card+sdram` que permet JPEG-only al PC i RAW a
  SD.
- **Pujar directament el drenatge a 6,0 o 6,5 s: posposat.** És una xifra
  arbitrària abans de mesurar. A més, el perfil té marge temporal suficient
  per degradar a C3-only sense regalar temps HDR per intuïció.
- **Eliminar el tercer 9×1: descartat ara.** Ja és opcional, es decideix
  abans d'obrir PTP i no desplaça C3 si no hi cap.
- **Fer `pull` amb `--get-all-files`: posposat.** No hi ha evidència que
  sigui més ràpid que els esdeveniments Sony, i podria reintroduir RAW al
  bus.
- **Carregar el Mac amb `stress-ng`: descartat.** No és una càrrega
  representativa del Mac de camp i l'eina no forma part del contracte
  offline.
- **Tractar cua zero com a fals positiu demostrat: descartat.** És una
  hipòtesi; el controlador ja exigeix addicionalment payload exacte i
  `capturemode` writable.
- **Afirmacions genèriques de 12/14 bits en Silent Shooting: no
  autoritatives.** Els ARW locals i els dos bits baixos són l'evidència que
  governa aquest projecte.

## Auditoria específica de C3

El perfil ja tenia la topologia correcta:

- una fallada neta del drenatge marca `drain_c2_contacts=skipped`;
- `set_hdr_5ev3` i tota la branca HDR se salten per dependència;
- `set_c3_single` i `set_c3_1_8000` tenen `requires=[]`;
- les 12 captures C3 només depenen d'aquests dos setters i mantenen targets
  absoluts.

El forat era un timeout que deixava la sessió `tainted`: abans de v0.2.9
abortava tota la timeline. Ara s'intenta `recover_prompt()` amb cutoff. Les
proves unitàries cobreixen tant recuperació correcta amb C3 preservat com
recuperació fallida i fatal.

No es promet una interrupció física dura. `gphoto2 --shell` és persistent:
el pare pot deixar d'esperar, però no pot matar només l'operació PTP sense
matar tota la sessió. Reobrir gphoto i reprendre C3 és un segon esglaó que
només s'implementarà després d'un assaig explícit.

## Protocol físic següent

### Sensor Crop

1. APS-C manual `Activar` + JPEG `M`.
2. Reconnectar: el preflight ha de bloquejar amb `sensorcrop=On`, fins i tot
   si la mida resultant és `3008×2000`.
3. APS-C manual `Desactivar` + JPEG `S`.
4. Reconnectar: `sensorcrop=Off` i sonda `3008×2000`.
5. Verificar a la SD un ARW `6048×4024`.

### Drenatge

1. Un warm-up no comptabilitzat.
2. Finestres `2s`, `1s`, `500ms`.
3. Tres repeticions intercalades per finestra.
4. Onze triggers amb els offsets C2 reals i inici exacte a `C2+4,90`.
5. Guanyadora provisional: 3/3, 11 JPEG, zero ARW, cua zero,
   `capturemode` writable i pitjor cas `<4,70 s`.
6. Qualificació: deu repeticions consecutives de la finestra guanyadora.
7. Una ronda d'injecció de timeout amb recuperació i C3-only; no habilitar
   aquest fallback com a qualificat fins que les 12 captures C3 passin.

Aquest protocol ja està codificat a
`controller/tools/qualify_mid_drain_windows.py`. Sense `--arm` només
imprimeix el pla; en mode físic manté una sola sessió persistent, una sola
sonda de ruta, ledger acumulat i atura tota la campanya a la primera mostra
físicament insegura. Els onze offsets s'esperen activament —no s'envien
abans d'hora— i es reconcilien 22 ordres, 11 presses i 11 releases. La fase
de deu runs només accepta el `result.json` del cribratge si coincideixen els
hashes de perfil, eina i controlador; també recalcula el resum a partir de
les mostres, en lloc de confiar en una guanyadora desada. Un firewall limita
el vocabulari PTP del camí calent i rebutja abans de l'enviament qualsevol
ordre aliena al gate. La càmera no era visible a
`gphoto2 --auto-detect` en tancar la ronda, per tant no hi ha encara cap
resultat físic d'aquest gate.

## Estat verificat

- controlador: `v0.2.9-candidate`;
- generador determinista: `--check` correcte;
- validació: 56 imatges obligatòries, 65 màximes, mínim C2–C3 de 84,67 s;
- dry-run de 98,8 s: 65 imatges i `hdr_9ev1_03` inclòs;
- proves de programari: 344/344 correctes;
- pendent decisiu: càmera real, checkpoint d'11 JPEG i prova A/B de
  `sensorcrop`.
