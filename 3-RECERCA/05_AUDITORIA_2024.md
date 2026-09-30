# Auditoria de la captura de 2024

> **Estat del document:** primera auditoria. La reconstrucció exhaustiva dels
> 260 RAW és a
> [`12_FORENSICA_RAW_2024.md`](12_FORENSICA_RAW_2024.md), i la síntesi causal
> de scripts, logs i metadades és a
> [`13_AUTOPSIA_CAUSAL_2024.md`](13_AUTOPSIA_CAUSAL_2024.md). Aquests dos
> documents posteriors prevalen quan afinen o resolen una hipòtesi d'aquest
> informe.

## Abast

Auditoria de lectura, sense modificar els originals, sobre:

- `/Users/USUARI/Dropbox/Astrofotografia/Eclipse Solar 2024/Script/Versió final que es va fer servir`
- `/Users/USUARI/Dropbox/Astrofotografia/Eclipse Solar 2024/Eclipse (short)`

Nota de traçabilitat: el directori real de Dropbox és `Script`, en singular, encara que en la descripció inicial apareixia `Scripts`.

La seqüència curta conté:

- `Canon 6D Nikon 300mm AFS-II 300mm f2.8`
- `Sony A7III AP130GTS QUADTCC 590mm f4.5`
- `Sony A7S Questar 3.5 1280mm f14`

Les xifres següents provenen de metadades EXIF i, en una mostra de la A7III, de lectura directa dels valors RAW de 14 bits. Són una auditoria preliminar; no substitueixen un revelat científic amb black level, white level, defectes i linealitat caracteritzats.

## Resultat de les tres seqüències

| Sistema | RAW | Interval EXIF | Durada | Cadència mediana | Buits remarcables |
|---|---:|---|---:|---:|---|
| A7III + AP/QUADTCC | 56 ARW | 19:07:54–19:12:45 | 291 s | 2 s | 30 s i **125 s** |
| Canon 6D + 300/2,8 | 146 CR2 | 20:15:43–20:20:33 | 290 s | 2 s | cap superior a 4 s |
| A7S + Questar | 58 ARW | noms 11:08:25–11:13:50; EXIF de 2014 | 325 s | 6 s | diversos de 3–9 s |

### A7III + AP: el problema principal

El buit crític és:

- `DSC06631`: 19:10:21, exposició 2 s;
- `DSC06632`: 19:12:26, exposició 0,8 s;
- diferència: **125 s**.

També hi ha un buit de 30 s:

- `DSC06613`: 19:09:05;
- `DSC06614`: 19:09:35.

Un buit de 125 s dins una totalitat de pocs minuts costa:

- repeticions HDR;
- redundància contra vibració o núvol;
- resolució temporal de prominències i Lluna;
- marge al voltant de C3;
- possibilitat d'escollir només els frames de millor seeing.

No es pot afirmar que gphoto2 fos l'única causa. Els possibles contribuents són bloqueig de procés, espera d'esdeveniment, estat USB, càmera ocupada, búfer/targeta, branca temporal errònia o script diferent del conservat.

### Canon 6D + 300 mm: el patró que va funcionar

La Canon va obtenir una successió d'aproximadament cinc escales:

`1/4000 → 1/2500 → 1/1000 → 1/500 → 1/200 → 1/80 → 1/30 → 1/15 → 1/8 → 1/4 → 0,4 → 0,6 → 1 s`

La majoria de valors tenen dues repeticions; les exposicions d'1 s, sovint una. Aquesta seqüència és molt més semblant a la filosofia Druckmüller:

- passos pròxims;
- solapament dinàmic;
- repetició;
- escales curtes repetides;
- cap gran buit temporal.

La lliçó és important fins i tot si la 6D no viatja el 2026: **la cadena més simple va ser temporalment la més robusta**.

### A7S + Questar: penalització de la descàrrega

`A7SFinal.sh` utilitza `--capture-image-and-download` i afegeix `sleep 0.8` a cada fotografia, a més d'altres esperes. La cadència observada d'uns 6 s és coherent amb una captura serialitzada amb transferència USB.

Per als moments crítics, transferir cada RAW abans de continuar és una arquitectura inadequada.

## Escala d'exposicions de la A7III

La seqüència observada comença a ISO 200:

- `1/400` × 3;
- `1/8000` × 6;
- primera escala HDR: `1/500, 1/250, 1/100, 1/30, 1/15, 1/8, 0,4, 1, 2, 0,8 s`, en general dues preses;
- segona escala fins a 2 s;
- després del buit de 125 s: ISO 100, `0,8 s` × 2, `1/8000` × 6 i `1/400`.

Problemes:

- salts superiors a 1 EV en diversos punts;
- ordre temporal poc net;
- només dues escales completes;
- canvi d'ISO;
- massa dependència d'un nombre petit d'exposicions llargues;
- manca de repetició homogènia abans i després del buit.

## Saturació RAW preliminar de la A7III

En una mostra de RAW sense comprimir de 14 bits, el valor màxim és 16.383:

| Fitxer/exposició | Píxels a 16.383 | Lectura |
|---|---:|---|
| `DSC06590`, 1/8000 s | 1.416 | clipping local, compatible amb zones molt brillants |
| `DSC06598`, 1/100 s | 45.202 | ja hi ha una regió saturada apreciable |
| `DSC06606`, 0,4 s | 1.798.962 | aproximadament 7,4% del sensor |
| `DSC06610`, 2 s | 4.956.621 | aproximadament 20,4% del sensor |
| presa pròxima a C3, 0,8 s | 1.806.687 | clipping extens |

Cap dels frames de mostra tenia saturació tocant la vora de la imatge. Això indica que les exposicions llargues encara poden aportar corona exterior, però no poden representar corona interior ni prominències sense capes curtes.

No s'ha d'interpretar el recompte brut com una mesura fotomètrica completa. Sí que prova una cosa: els valors a 16.383 són irrecuperables i la fusió els ha d'excloure.

## Auditoria dels scripts guardats

La sintaxi s'ha comprovat amb `bash -n`:

- `A7IIIFINAL.sh`: passa;
- `A7SFinal.sh`: passa;
- `EclipseV6.sh`: passa;
- `assaig.sh`: passa;
- `A7III.sh`: falla a la condició de la línia 36;
- `Canon6DFinal.sh`: falla al `fi` de la línia 26.

### `A7IIIFINAL.sh`

Troballes:

- en detectar la càmera, `capture_image` dispara dues fotografies reals abans d'establir `i=0`;
- data `2024-03-21` i contactes de prova, no la data real del 8 d'abril;
- ISO configurat sense `--port`, encara que els dispars sí utilitzen port;
- cada parella crea dos processos independents `gphoto2`;
- espera `CAPTURECOMPLETE` després de cada tret;
- `--filename` no té efecte pràctic si no es descarrega la imatge;
- cap comprovació del codi de retorn;
- cap lectura posterior per verificar que ISO/velocitat han canviat;
- cap reintent, watchdog ni límit de temps;
- cap log estructurat;
- la primera part de totalitat ordena 10, 5 i 3 s, mentre els RAW auditats arriben només a 2 s;
- l'extracció de port amb una columna fixa d'`awk` depèn del text exacte del model;
- la lògica de C2/C3 canvia de fase segons l'hora d'entrada i pot consumir tota la finestra en una branca.

Conclusió: el fitxer etiquetat `FINAL` no descriu de manera exacta la seqüència RAW observada.

### `A7III.sh`

La seva escala s'assembla més als RAW observats, però:

- conté condicions `[[ ...]]` sense l'espai obligatori abans de `]]`;
- usa una data de prova, `2024-03-19`;
- no fixa el port;
- continua obrint dos processos per parella;
- no registra ni valida operacions.

És possible que hi hagués una versió corregida en execució o canvis posteriors, però els fitxers conservats no permeten demostrar-ho.

### `Canon6DFinal.sh`

Conté:

```bash
while true; do
    capture_image
fi
done
```

El `fi` no té cap `if` corresponent. El fitxer, tal com està guardat, no és sintàcticament executable. A més, la seva única velocitat no pot explicar l'escala completa observada als CR2.

La bona seqüència Canon prové, per tant, d'una altra versió o d'un altre mecanisme que no ha quedat identificat.

### `A7SFinal.sh`

- usa `--capture-image-and-download` a cada presa;
- imposa una espera addicional de 0,8 s;
- afegeix `sleep 1` en fases crítiques;
- usa `date -d`, sintaxi GNU/Linux, mentre altres scripts usen `date -j` de macOS/BSD;
- la càmera conserva un any EXIF 2014;
- no verifica canvis de configuració ni captura.

## Rellotges i reconstrucció temporal

Els cossos no compartien una referència fiable:

- A7III: EXIF del 2024, hora 19:xx;
- Canon 6D: EXIF del 2024, hora 20:xx;
- A7S: EXIF del 2014, mentre els noms de fitxer indiquen el 2024 i un interval
  de 11:08:25–11:13:50. Aquest interval prové dels noms generats pel
  controlador, no d'una hora de captura EXIF fiable.

Això impedeix:

- comparar exactament el mateix instant entre focals;
- saber amb certesa la distància de cada frame a C2/C3;
- separar error de càmera, controlador o calendari;
- mesurar retard real de dispar;
- reconstruir una cronologia comuna.

## Requisits que se'n deriven per a 2026

1. Sincronitzar controlador i tres cossos abans de cada assaig i el dia de l'eclipsi.
2. Registrar hora civil, UTC i rellotge monotònic del controlador.
3. Guardar inici i final de cada ordre, resultat, configuració sol·licitada i configuració llegida.
4. Comptar els esdeveniments de captura i, després, els fitxers reals a la targeta.
5. Fixar ports/cossos de manera inequívoca.
6. Fer una sola inicialització explícita que **no dispari**.
7. Evitar una invocació nova del programa per tret.
8. Aplicar timeout, reintent acotat i degradació segura.
9. Deixar la descàrrega per després de la finestra crítica.
10. Guardar el commit/fitxer exacte que s'ha executat, amb hash.
11. Fer un assaig complet a durada real amb targetes reals, bateria, cables i temperatura.
12. Comparar llista prevista versus EXIF real automàticament després de cada assaig.

## Què va anar bé

L'auditoria no és només negativa:

- l'AP130 + QUADTCC + A7III va donar enquadrament i qualitat òptica útils;
- les exposicions curtes van conservar prominències i contactes;
- les llargues no van saturar fins a la vora i aporten corona exterior;
- la Canon va demostrar que una escala densa i repetida era possible;
- es van conservar RAW i una seqüència crítica, cosa que permet aprendre de manera objectiva;
- el projecte ja disposava de divisió funcional entre focals.

La prioritat de 2026 és conservar aquestes fortaleses i eliminar els punts únics de fallada.
