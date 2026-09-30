# Canon EOS 6D: coexistència amb l’A7III i backend inicial

Data de verificació: 29-07-2026.

## Veredicte

La Canon EOS 6D i la Sony A7III poden romandre connectades al mateix Mac
i el controlador les discrimina correctament per model, port USB i número
de sèrie PTP. La nova ruta Canon és, però, un
`CANDIDATE_NOT_PRODUCTION`: encara no està autoritzada per a l’eclipsi ni
per a un run `mission-first`.

No s’ha enviat cap trigger ni s’ha fet cap fotografia durant aquesta
verificació. Les dues preflights físiques només van executar ordres
`get-config`; `apply_safe_config` estava desactivat.

## Evidència física de coexistència

`ioreg -p IOUSB -l -w0` va mostrar els dos dispositius simultàniament i en
dos controladors XHCI diferents:

| Cos | Producte USB | `locationID` | Controlador pare |
|---|---|---:|---:|
| Sony A7III | `ILCE-7M3` | `18874368` | `16777216` |
| Canon 6D | `Canon Digital Camera` | `34603008` | `33554432` |

Després d’aturar el client PTP automàtic de macOS, un únic
`gphoto2 --auto-detect` va enumerar:

```text
Canon EOS 6D                         usb:002,001
Sony Alpha-A7 III (PC Control)       usb:001,001
```

El controlador va repetir aquest inventari en les dues direccions:

1. perfil Canon: va seleccionar `usb:002,001` i va validar
   `[SÈRIE]`;
2. perfil Sony: va seleccionar `usb:001,001` i va validar
   `[SÈRIE]`.

Per tant, connectar tots dos cossos no fa que el programa dispari «la
primera càmera USB»: cada procés resol exactament el model esperat i
verifica la sèrie abans d’admetre cap operació física.

## Contracte Canon implementat

El backend `canon_eos` no reutilitza el trigger Sony `capture=1/0`.
Empra el control EOS publicat pel cos:

```text
/main/actions/eosremoterelease
Press Full MF
Release Full
```

La 6D tampoc usa la cua Sony `/main/other/d215`. El perfil és
`card-only`: les captures es destinen a la SD i la verificació posterior
haurà de reconciliar els CR2 de la targeta.

La primera seqüència conté 23 captures de contacte:

- 11 al voltant de C2;
- 12 al voltant de C3;
- obturació prevista `1/4000`, ISO 100, RAW i drive `Single`;
- cap escala HDR de totalitat.

La interfície ofereix un selector de programa Sony/Canon. Mentre el perfil
Canon no estigui físicament qualificat, el botó de captura queda bloquejat;
la preflight i el dry-run continuen disponibles.

## Estat real observat de la 6D

La preflight va verificar model, sèrie i firmware `3-1.1.9` (1.1.9), RAW,
ISO 100, exposició Manual, focus Manual, AEB off i mirror lock off.
La bateria era al 50% i la càmera informava 42.579 captures disponibles.

Va fallar tancada per tres discrepàncies, sense corregir-les:

| Ajust | Observat | Exigit |
|---|---|---|
| Drive mode | `Timer 2 sec` | `Single` |
| Obturació | `1/2500` | `1/4000` |
| Destí de captura | `Internal RAM` | `Memory card` |

## Gates pendents

Abans de promoure la Canon a producció cal:

1. corregir manualment drive i obturació i confirmar SD/RAW;
2. fer un únic assaig físic acotat del parell press/release;
3. mesurar la cadència sostinguda de 23 captures;
4. extreure la SD i provar el delta exacte de CR2, mides i metadades;
5. definir l’òptica i l’escala HDR de totalitat;
6. repetir l’aïllament amb tots dos processos oberts si es pretén disparar
   les dues càmeres alhora.

Fins llavors, «coexistència confirmada» significa enumeració simultània,
selecció inequívoca i sessions PTP de lectura independents; no significa
encara captura simultània qualificada.
