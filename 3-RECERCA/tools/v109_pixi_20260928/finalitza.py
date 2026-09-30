from pathlib import Path
import json,datetime
ROOT=Path(__file__).resolve().parents[3];O=ROOT/'4-RESULTATS/v109_pixi_20260928'
r=json.loads((O/'VERIFICACIO_FINAL.json').read_text());assert r['status']=='PASS'
assert len(r['sources'])==4 and sum(x['exact_channels'] for x in r['original_layers'])==194
porta=(O/'PORTA.log').read_text();assert 'OBRE' in porta and 'REFUSA' not in porta
p6=(O/'P6.log').read_text();assert 'PASSA' in p6
owner=ROOT/'.coordination/claim.lock/owner.json';assert json.loads(owner.read_text())['claim_id']=='CODEX_V109_PIXI_I_ARTEFACTES_20260928'
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
body=f'''# V109 — retocs de Pere i correcció del cel

Desada el 28-09-2026. Font manual: `Downloads/V108-Pixi.tif`, llegida amb la capa 307 de marques apagada. Base: `1-PHOTOSHOP/V108.psb`, SHA 23be3edc… Font manual SHA ac93336f… Originals comprovats intactes.

## Lliurable

`1-PHOTOSHOP/V109.psb` — 10551 × 7506, RGB de 16 bits, AdobeRGB, 43 capes. SHA256: `{r['sha256']}`.

- Les 41 capes de V108 conserven tots els canals i les propietats visuals exactes.
- **Retocs de Pere · V109** (400, Normal 100%): només els 71.587.313 píxels que difereixen del visible V108. RGB exactes de Pixi sense marques; alfa 65535 dins el delta i zero fora, sense llindar. Inclou el canvi global de Levels ja present a la font de Pere, a més del retoc local del limbe.
- **Cel · correcció NRGF V109** (401, Normal 100%): 69.931.899 píxels canviats; correcció derivada de retirar el terme CEL de NRGF 41/42, mantenint el genoll. La contribució de Light 239 i Claridad 241 queda fixada dins el residual de Pere perquè reavaluar aquests ajustos alterava la Lluna. No és una recomposició íntegra de la cadena ni un nou calibratge físic.

Per comparar: apagar només 401 recupera exactament el visible V108-Pixi net; apagar 400 i 401 recupera V108. Els dos originals continuen intactes.

## Marques i límits

La depressió del cel nord exterior baixa d'aproximadament3–4% a0,5–1,2%. Es redueix; no es declara eliminació completa. Les dues marques petites, prop(6025,4504) i(6518,4534), segueixen valls coronals confirmades per quatre imatgesBrno: es conserven. No s'ha respost a l'opció de suavitzar-ne la presentació; s'ha mantingut el detall real.

El disc lunar(644.610píxels), la franja exterior0–40px(118.851) i el retoc local dePere(74.241) queden exactes respectePixi. Frontera del retoc: pas màximL4,5DN/0,0161%, davant192,5DN/1,509% de la variant descartada. Cap clipping nou.

Transferència Fourier relativa0,940–1,021; absoluta0,963–1,099 excepte el camp superior senseBrno(1,104–1,109). Aquesta excepció supera la porta absoluta1,10 i es declara, sense PASS global. MorfologiaBrno conservada, pitjor canvi de correlació−0,0011. No s'afirma absència de tots els artefactes.

## Verificació

Desada nativa com a còpia i nova obertura real: `{porta.strip()}`. `{p6.strip()}`.
Comprovació independent: ImageData = TIFF natiu = target calculat, zero diferències; 194 canals antics exactes, propietats visuals exactes, alfa i RGB de 400 i 401 exactes. Photoshop ha actualitzat les hores de modificació de les capes (layerTime); és l'única diferència de les metadades originals, a més de les longituds de compressió. SHA dels quatre fitxers d'entrada intactes.
El perfil ICC és idèntic entre V108, V109, Pixi i el TIFF natiu (PERFIL_ICC.json).

Evidència: `4-RESULTATS/v109_pixi_20260928/VERIFICACIO_FINAL.json`, `QA_CIENTIFICA_FROZEN.json`, `FACTORIAL_AJUSTOS.json`, `TRANSPORT_FROZEN.json`, `DIAGNOSI.md` i els renders natius. Els negatius es conserven: primera desada amb ImageData incorrecte i candidata amb tall dur a la màscara manual. No s'han tocat RAW, calibradors, ajustos manuals originals ni la investigació de perles aturada.
'''
(ROOT/'1-PHOTOSHOP/V109_REBUT.md').write_text(body)
(O/'RESULTAT.md').write_text(body)
handoff=f'''# V109 — traspàs verificat

{now}. Encàrrec dePere: ferV109 des deV108-Pixi, capa de delta exacta i corregir les marques fosques.

Lliurable: `1-PHOTOSHOP/V109.psb`, SHA `{r['sha256']}`. Rebut: `1-PHOTOSHOP/V109_REBUT.md`.
43capes:41originalsV108 exactes,400Retocs dePere,401Cel/correccióNRGF. Apagar401 tornaPixi net; apagar400+401 tornaV108. Originals iRAW intactes. Font correcta `Downloads/V108-Pixi.tif`;V108_Artefactes és suport diagnòstic, no la font manual final.

Decisió: transport de la contribucióNRGF noCEL ambLight239/Claridad241 congelats al residual dePixi per preservar laLluna. Disc,40px de limbe i74241píxels de retoc exactes. La depressió nord es redueix a0,5–1,2%, no es declara acabada globalment. Les dues valls petites són reals segonsBrno i es conserven. Contrast relatiu preservat0,940–1,021; amplitud absoluta al camp superior senseBrno1,104–1,109, excepció declarada. No reobrir perles ni promoure calibratge nou.

Portes: desada nativa, p6 PASSA, porta OBRE, canals i propietats visuals antics exactes, compost i target exactes, fonts SHA intactes. Photoshop només renova layerTime a les metadades de les capes. El primer desament i el transport directe amb tall H són negatius preservats; no reutilitzar-los com a resultat.

Entrada curta per continuar: `4-RESULTATS/v109_pixi_20260928/RESULTAT.md`, `DIAGNOSI.md`, `QA_CIENTIFICA_FROZEN.json`. Eines a `3-RECERCA/tools/v109_pixi_20260928/`.

RELEASED. serial_writes: RELEASED. owner: null. released_utc: {now}. Zero processos propis pendents i agents acabats. Cap missatge enviat aClaude, cap publicació ni actualització de memòria.
'''
(ROOT/'.coordination/HANDOFF_2026-09-28_V109.md').write_text(handoff)
with (ROOT/'.coordination/CODEX_STATUS.md').open('a') as f:
 f.write(f'\n{now} · V109 RELEASED; serial_writes: RELEASED; owner: null; released_utc: {now}. V109.psb43capes, SHA{r["sha256"]}, portaOBRE i p6PASSA, compost/target exactes, fonts intactes. DeltaPixi exacte400 + correccióNRGF401 amb presentació congelada. Lluna/40px/retoclocal exactes; depressió nord reduïda a0,5–1,2%; duesvallsreals conservades. SensePASSglobal. Rebut1-PHOTOSHOP/V109_REBUT.md; handoff.coordination/HANDOFF_2026-09-28_V109.md. Zero processos propis i agents acabats.\n')
(O/'TANCAMENT.json').write_text(json.dumps(dict(status='RELEASED',serial_writes='RELEASED',owner=None,released_utc=now,claim_id='CODEX_V109_PIXI_I_ARTEFACTES_20260928',product=r['file'],sha256=r['sha256']),indent=2)+'\n')
owner.unlink();owner.parent.rmdir();print('RELEASED',now)
