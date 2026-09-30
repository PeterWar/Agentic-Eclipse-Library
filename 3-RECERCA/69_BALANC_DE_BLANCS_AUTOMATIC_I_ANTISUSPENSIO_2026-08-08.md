# El balanç de blancs passa a correcció d'arrencada, i el Mac ja no s'adorm

8 d'agost de 2026, nit. Dos encàrrecs de Pere, tots dos de la mateixa
família: coses que fins ara depenien que l'operador se'n recordés i que ara
les fa l'aplicació.

1. **Comprovar a l'arrencada si cada cos porta el balanç de blancs en
   automàtic i, si l'hi troba, corregir-l'hi.** Era el «que NO s'ha fet» de
   `research/68`.
2. **Impedir que el Mac s'adormi mentre hi ha un run en marxa, també amb
   bateria.**

Cap dels dos no toca geometria, cadència, exposicions ni contractes de
captura. Cap càmera no s'ha tocat per fer-los.

## 1. El balanç de blancs

### Què fa ara l'aplicació

`/main/imgsettings/whitebalance` entra a la convergència d'arrencada dels
**quatre** perfils de missió, amb la mateixa regla que la resta de
correccions: **un sol intent, readback exacte, i un fracàs net no atura el
canal**.

| Cos | Camí | Valor observat al bolcat | Valor de missió |
|---|---|---|---|
| A7RIIIA | `/main/imgsettings/whitebalance` | `Automatic` (`20260808T173224`) | `Daylight` |
| A7III | el mateix | manual, valor concret no bolcat | `Daylight` |
| R6 Mark III | el mateix | `Auto` (`20260803T195235`) | `Daylight` |
| Canon 6D | el mateix | `Manual` (`20260801T010919`) | `Daylight` |

Els quatre publiquen el camí com a escrivible (`Readonly: 0`) i els quatre
tenen `Daylight` al menú. Als dos Sony l'automàtic es diu `Automatic`; a les
dues Canon, `Auto`.

`Daylight` i no una temperatura fixa: als Sony `/main/imgsettings/colortemperature`
és **de només lectura** —només s'obre quan el balanç ja és
`Choose Color Temperature`—, o sigui que una temperatura numèrica exigiria dos
writes encadenats i un estat intermedi. `Daylight` és un sol write a totes
quatre i es llegeix igual a tots dos fabricants.

### Tres decisions de disseny que no són òbvies

**La correcció va sempre l'última de la llista.** Al worker Sony i al Canon
v2, un rebuig net d'una correcció d'arrencada **atura la cadena**: no
s'encadena cap altra escriptura declarativa després d'un setter ambigu. El
balanç de blancs és l'única correcció que no decideix si el programa es pot
executar —no és el mode M, ni el RAW, ni la targeta, ni el bràqueting—, o
sigui que ha d'anar darrere de totes. Al worker de la R6 la política és
`continue` i l'ordre no hi és crítica, però es manté per coherència.

**Sense `allowed_initial_values`.** Aquest camp converteix un valor inicial
inesperat en `ConfigWritePreconditionError`, i això sí que és un **hard stop
del canal**. Un cos que arrenqués a `Cloudy` o a `Tungsten` no ha de perdre la
missió per això: ha de convergir igualment. El camp queda per a l'AEB de la
6D, on la transició sí que està físicament qualificada des d'un conjunt
concret de valors.

**La línia de checklist es queda.** Ara diu que ho fa l'app, però no
desapareix: si la correcció no convergeix, el canal continua capturant amb el
valor real i llavors sí que cal anar al menú del cos.

### On és el contracte, fail-closed

- font: `preflight.required`, `preflight.required_choices` i
  `preflight.auto_configure` dels quatre perfils;
- R6: `r6m3_aeb3_operational_contract.startup_convergence.auto_configure_paths`
  també l'enumera, i el compilador de la GUI (`_r6m3_aeb3_auto_configure`) i el
  worker (`_is_r6m3_single_hdr_materialized_mission_candidate`) el comparen
  element a element. Treure'l del perfil materialitzat fa que el worker no
  reconegui el programa;
- 6D: `canon_fixed_aeb3_startup_auto_configure()` i el `fixed_required` de
  `validate_canon_fixed_aeb3_runtime_contract` al worker, més
  `expected_startup_writes` al compilador;
- Sony: la validació genèrica ja exigeix que tot valor autoconfigurable consti
  a `required` i a `required_choices`;
- l'A7III no s'edita a mà: surt de `controller/tools/build_short_profiles.py`.

### El que això no demostra

**No hi ha cap run físic amb la correcció posada.** Està verificat per
regressió i pels bolcats de capacitats, no al cos. El primer preflight que es
faci amb qualsevol dels quatre l'exercirà; l'A7RIIIA i la R6 haurien de
mostrar la transició `Automatic → Daylight` i `Auto → Daylight`
respectivament, perquè els bolcats els van trobar així.

## 2. L'antisuspensió del Mac

### El problema

Amb bateria, macOS no deixa posar la suspensió per inactivitat a «mai»: la
preferència d'energia només ho permet amb corrent. Un run de totalitat dura
minuts amb molt poca activitat visible per al sistema —una pulsació cada mig
segon i cap tecla ni ratolí—, o sigui que el Mac es pot adormir just al mig.

I adormir-lo no és un ensurt qualsevol: mata la sessió PTP, i per
`research/66` **una sessió morta amb imatges pendents deixa el cos inservible
fins que li treus la bateria**.

### Com es reté

Es demana a `caffeinate`, que és part de macOS i no demana cap autorització:

```
/usr/bin/caffeinate -i -m -w <pid>
```

- `-i` impedeix la suspensió del sistema per inactivitat. **És l'única
  bandera que actua amb bateria**;
- `-m` impedeix que el disc s'aturi per inactivitat;
- `-w <pid>` fa que l'ajudant es mori sol quan mor qui l'ha demanat, també si
  aquest cau de cop. Cap procés orfe no pot sobreviure un run, cosa que
  importa en un projecte on un `gphoto2` orfe reté una càmera com un ostatge.

Deliberadament **no** es fa servir `-s`: només val amb corrent, que és
exactament el cas contrari del que interessa. Tampoc `-d`: mantenir la
pantalla encesa no evita cap suspensió i gasta bateria.

### On es reté

A **tots dos hosts detached**, que són els processos que viuen exactament el
que dura la feina:

- `worker_host.py` la reté mentre té un controlador viu, i **per a qualsevol
  mode, no només `run`**: una suspensió durant un preflight mata la sessió
  PTP igual. L'estat queda escrit a `worker_state.json`;
- `mission_host.py` la reté durant tota la missió multicàmera, també als
  forats entre canals i durant l'agregació final. Queda a l'esdeveniment
  `mission_started`.

Les retencions són independents: el sistema les compta totes i només s'adorm
quan no en queda cap.

### Dues coses que s'han decidit i convé que constin

**Es reté sempre, no només amb bateria.** Pere ho va demanar per al cas de la
bateria, però decidir-ho una sola vegada a l'inici no veuria que algú
desendolli el cable enmig d'un run —que és justament el cas—, i amb corrent la
retenció no fa cap mal. La font d'energia observada sí que es llegeix i
s'anota (`pmset -g ps`, només lectura) perquè quedi al registre del run.

**No pot aturar res.** Si `caffeinate` no hi és o no arrenca, es registra el
motiu i es continua. Tapar la suspensió és una salvaguarda, no un
prerequisit: per `CLAUDE.md` §2, cap funcionalitat auxiliar nova pot
esdevenir un prerequisit de `Start mission`.

### El que això no cobreix

- **Tancar la tapa.** El clamshell adorm el Mac tot i la retenció.
- **La bateria esgotada.** La suspensió d'emergència passa per damunt.
- **Una suspensió demanada per l'operador** des del menú.
- **La finestra abans d'arrencar el run.** Mentre l'app espera amb el
  compte enrere a la pantalla i cap host viu, no hi ha cap retenció. Cobrir-ho
  voldria dir retenir des de la GUI, i s'ha deixat fora perquè l'encàrrec era
  «si hi ha un run en marxa».

## Regressió

- GUI **467/467** offscreen (446 abans, més 9 de `test_power.py`, 8 de
  `test_white_balance_convergence.py` i 4 als dos hosts);
- controlador **1.085/1.085** (1.079 abans, més 6 de
  `test_white_balance_startup_correction.py`);
- fuzz adaptatiu **67.392/67.392**;
- perfils curts, JSON i `git diff --check` verds.

Tres proves ancorades s'han hagut de reancorar, totes per la mateixa causa i
totes documentades al lloc: el recompte d'entrades de la llista de correccions
de la R6 (12 → 13), la de la 6D (1 → 2), el nombre de files de la taula de
Camera Settings (17 → 18) i el SHA del worker Canon v2, que ara inclou la
correcció nova. El manifest de runtime passa de 66 a 67 entrades per
`gui/eclipse_command/power.py`.

## Deute que això deixa obert

- **Cap run físic** amb cap de les dues coses. La correcció de blancs s'exercirà
  al primer preflight; l'antisuspensió, al primer run llarg amb bateria.
- **El bundle instal·lat queda enrere una altra vegada.** Els quatre perfils i
  els dos workers són inputs del manifest, i ara també hi ha un mòdul nou. Fins
  que no es refaci el bundle, l'app instal·lada **no fa cap de les dues coses**.
  Refer-lo demana tancar l'app de Pere i és decisió seva.
