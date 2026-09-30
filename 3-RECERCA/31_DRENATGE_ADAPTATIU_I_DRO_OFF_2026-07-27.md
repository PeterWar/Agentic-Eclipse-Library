# Drenatge adaptatiu i requisit DRO Off — 2026-07-27

> **Nota de vigència, 28-07-2026.** Aquest document conserva la hipòtesi i
> els assajos previs. La política `2 s / 1 s / 500 ms`, el gate `<4,70 s`,
> l'inici `C2+4,90` i el headroom fix de 300 ms han estat substituïts pel
> protocol v0.3.4 qualificat: drenatge a `C2+4,80`, tail i purga de `50 ms`,
> màxim modelat de `5,28 s` i handoff HDR real dins de 100 ms. Vegeu
> [Qualificació del drenatge i handoff HDR](34_QUALIFICACIO_DRENATGE_I_HANDOFF_HDR_2026-07-28.md).

## Estat de partida

El cribratge físic ISO 100 del run
`20260727T221254_candidate_a7m3_ap130_short_hybrid_5x3_then_9x1_mid_drain_screen_qualification`
va preservar íntegrament el contracte de captura:

- 11 presses i 11 releases per mostra;
- 11 JPEG rebuts al Mac i 0 ARW per USB;
- cua final `d215=0`;
- `capturemode` final writable;
- cap sessió contaminada ni error de cleanup.

Cap finestra fixa va superar, però, el gate temporal estricte `<4,70 s`:

| Finestra | mediana | pitjor mostra |
|---|---:|---:|
| 2 s | 4,838518 s | 4,856762 s |
| 1 s | 4,899785 s | 4,992259 s |
| 500 ms | 4,861488 s | 4,963105 s |

Els 11 JPEG sumaven només uns 2,77 MB per mostra. El bus USB no és el
coll d'ampolla dominant.

## Troballa de telemetria

En una mostra de 500 ms els onze JPEG ja eren al directori local després
del cinquè intent, però `d215` encara publicava `1`. El bucle antic exigia
simultàniament ledger complet i cua zero i, per tant, gastava una sisena
finestra sencera de 500 ms només per consumir l'esdeveniment final de Sony.

La cua `d215` és telemetria necessària, però pot anar endarrerida. El ledger
local —imatges compromeses menys fitxers descarregats— és la font correcta
per decidir la durada de la següent espera.

## Política implementada, encara pendent de prova física

La política queda opt-in al perfil amb:

`wait_policy = adaptive_ledger_2s_1s_500ms_50ms_purge`

Escull la següent finestra així:

- deute de 6 o més JPEG: 2 s;
- deute de 3 a 5 JPEG: 1 s;
- deute d'1 o 2 JPEG: 500 ms;
- deute zero però `d215>0`: purga de 50 ms;
- deute zero i `d215=0`: deixa de fer esperes.

Després continua exigint `capturemode` writable, ara amb polling cada
50 ms. No s'ha relaxat cap gate: payload exacte, cua zero, cap ARW per USB,
deadline dur de 5,0 s, almenys 300 ms abans del canvi HDR i temps total
estrictament inferior a 4,70 s.

La qualificació s'ha de fer amb un únic protocol adaptatiu:

1. warm-up no comptat + 3 repeticions, totes 3/3;
2. warm-up no comptat + 10 repeticions consecutives, totes 10/10;
3. resultat de la segona fase lligat pels hashes al `result.json` de la
   primera.

No s'han de tornar a etiquetar com 2 s, 1 s i 500 ms tres execucions que,
amb la política adaptativa activa, serien idèntiques.

## DRO Off

La Sony A7III publica la propietat PTP `0xd201` com `dro = DRO Auto`.
El path de libgphoto2 és `/main/capturesettings/dro`; el perfil requereix
ara el valor `Off`.

Amb mode M, ISO i obturació fixos, desactivar DRO no canvia l'exposició
captada pel sensor. Evita una transformació adaptativa del JPEG i dona una
telemetria més consistent. Un possible guany de temps continua sent una
hipòtesi: no s'atribuirà cap millora a DRO sense A/B físic.

Fins demostrar `Readonly: 0` i un setter+readback correcte en aquesta
càmera, el controlador **no** el canvia automàticament. Si el preflight
llegeix un valor diferent:

1. desconnectar temporalment l'USB;
2. `MENU > Camera Settings1 > DRO/Auto HDR > Off`;
3. reconnectar amb `USB Connection = PC Remote`;
4. repetir el preflight fins que llegeixi `DRange Optimizer = Off`.

Font primària Sony:
[ILCE-7M3 Help Guide, D-Range Optimizer](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001653147.html)
i
[ILCE-7M3 Help Guide, Auto HDR](https://helpguide.sony.net/ilc/1720/v1/en/contents/TP0001653148.html).

## Decisió de seguretat

No s'avança el drenatge per sota de `C2+4,90 s`: el marge contractual
respecte del readiness de l'últim trigger és només de 30 ms. Avançar-lo de
manera segura aportaria 20–30 ms, insuficient per resoldre el problema.
Tampoc es desplaça encara el bloc HDR ni es relaxa el límit de 4,70 s.
Primer s'ha de mesurar la política adaptativa amb la càmera real.
