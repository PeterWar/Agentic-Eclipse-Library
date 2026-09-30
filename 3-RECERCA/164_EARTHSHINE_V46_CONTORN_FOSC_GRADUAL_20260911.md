# Earthshine V46 — contorn fosc gradual, 11-09-2026

Pere considera la millora V45 significativa i autoritza una V46 desatesa per enfosquir els últims píxels, amb degradats i protecció especial de les protuberàncies petites de dalt i de la dreta. La captura de referència és `Downloads/Captura de pantalla 2026-09-11 a las 3.12.25.png`.

## Lliurable i ús

`/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V46.psb`

SHA-256 `5a024e01ac47e703fb9d049868f923570188a265f3e722b4180c64dc8f836373`. 1,263,377,448 bytes; 10551 × 7506, RGB16, 25 capes. Mateix llenç, escala, contorn Vixen i màscara lunar. No retall ni remostreig del producte.

Capa superior **V46 · contorn fosc gradual · ajusta opacitat**, mode Restar, opacitat100%. Reduir-ne l'opacitat disminueix l'enfosquiment; apagar-la retorna a la composició V45 que Pere tenia oberta. Les 24 capes d'aquell estat es conserven amb els canals comprimits, màscares, geometria, modes i visibilitats exactes.

## Preservació de l'estat obert

Photoshop tenia `Earthshine_V45_Fonts.psb` amb canvis sense desar. La capa lunar visible tenia píxels diferents dels publicats; la capa09 RGB era exactament igual. La màscara només diferia1DN16 per quantització de Photoshop. No s'ha substituït l'estat obert pel fitxer de disc.

S'ha duplicat el document complet i desat exclusivament la còpia a `/Users/USUARI/Downloads/Eclipse 2026/research/tools/v46_earthshine_20260911/V45_live_source.psd`, SHA `a34931424b9239a357cad986e522015195ea44d7a7749076e1b4bce793d84737`. El document original ha continuat obert i sense desar abans i després. L'exportació TIFF prèvia i els canals de la còpia reprodueixen el mateix estat dins6DN16. La V46 parteix d'aquesta còpia completa.

## Ajust declarat

Aquesta és una **variant fotogràfica de to demanada expressament per Pere**, no una nova recuperació científica de relleu ni una correcció física de PSF. Aquesta instrucció concreta autoritza el degradat de pantalla; les exclusions anteriors de resta cosmètica continuen aplicant-se a les afirmacions científiques.

S'utilitza la distància interior al contorn Vixen existent. Un perfil robust de luminància de pantalla, en passos0,25px amb sigma0,5px només sobre la referència1D, defineix un camp positiu de guany. Cap píxel de la textura s'ha difuminat. Variant `h`: objectiu0,18 al contorn, transició smootherstep de8px fins0,22905; alliberament gradual complet als100px. Als60px el guany ja és0,94967, als80px0,99480 i a partir de100px és exactament1. Això evita el salt entre una línia fosca i el vel clar interior.

Si L és la capa lunar, B la capa09 i w la màscara existent, la composició anterior és B(1−w)+Lw. La capa nova conté S=L_G(1−g), igual als tres canals, i el pes w s'aplica a S abans de la fusió: **C46=C45−wS**. La capa Restar conté aquest producte ja calculat, per evitar que Photoshop retalli valors intermedis abans d'aplicar una màscara parcial. La contribució B(1−w) queda intacta, igual que les diferències cromàtiques que defineixen les protuberàncies. El contrast lunar absolut baixa amb el to; la textura fraccional de G es conserva dins la quantització. El perfil no es presenta com una estimació física del vel ni com terrain recuperat.

## Verificació real

- `porta_photoshop.sh`: OBRE10551×7506 ·25capes. Photoshop ha recomposat les capes després d'apagar i encendre l'ajust, i ha exportat TIFF RGB16 amb transparència.
- Diferència màxima sobre tot el llenç visible: **1DN16**; alfa: **0DN16**. No és una validació basada només en la miniatura incrustada.
- Les24capes de la còpia viva: canals comprimits exactes; nouRGB: descodificació exacta; màscares originals intactes. Segon lector ImageMagick correcte.
- Píxels de la ROI sense ajust: desviació màxima real **0DN16**; diferència cromàtica màxima **1DN16**.
- Verd mediana als últims píxels amb màscara>95%: **0.6412 → 0.1780** en escala0–1.
- Interior a100px: font exacta. Cap nou negre retallat en la font lunar dins la zona graduada; inversió del guany recupera G amb màxim1.964DN16 de quantització.
- Protuberàncies/zona dalt: màxim canviR−G 1DN16, desplaçament del centroide cromàtic 0.000024px.
- Protuberàncies/zona dreta: màxim canviR−G 1DN16, desplaçament del centroide cromàtic 0.000032px.
- Protuberàncies/zona oest: màxim canviR−G 1DN16, desplaçament del centroide cromàtic 0.000027px.
- Protuberàncies/zona baix: màxim canviR−G 1DN16, desplaçament del centroide cromàtic 0.000020px.

Inspecció visual feta al disc sencer, llenç complet i retalls de dalt, dreta, oest i baix a coordenades idèntiques. Les protuberàncies petites continuen visibles. La variació de contorn heretada no s'ha allisat ni substituït per un cercle.

## Proves descartades i límits

Els primers degradats directes exponencials de24–48px produïen una franja negra massa ampla; descartats. Les variants amb transicions24–32px també deixaven una vora massa marcada. La variant final usa8px i una correcció suau del vel de pantalla per enllaçar-la amb l'interior.

El primer PSB de prova va passar el lector independent però Photoshop el va refusar. Causa de format: la conversió del PSD de la còpia viva a PSB necessitava les signatures8B64 dels blocs globals FMsk/cinf, com al PSB nadiu. Es va corregir només la serialització; la prova rebutjada i el seu rebut queden a staging. Una segona prova es podia obrir però no reproduïa el càlcul: Photoshop retallava C−S abans d'interpolar la màscara parcial. La versió final incorpora w a S abans de Restar i evita aquest retall intermedi. El tercer PSB és el lliurat i ha passat obertura i comparació de tots els píxels.

La V46 no afegeix cap dada a la V45 ni torna a validar científicament les textures de l'últim limbe. La recuperació total no demostrada de research163 continua sent el límit de les fonts, compatible amb la valoració fotogràfica positiva de Pere. No es modifica Capes Totals ni cap RAW.

## Reproducció

Arrel de codi: `research/tools/v46_earthshine_20260911/`. Estat viu preservat a `V45_live_source.psd`; derivats exactes a `cau/`. Cadena `a2_grade_live.py` (variant h) → `b1_package.py build/verify/gate/readback` → `b2_protection.py` → `b1_package.py publish` → `d2_deliver.py`. El build/publish refusen sobreescriure fitxers; per repetir cal una destinació nova.

Rebuts a `output/v46_earthshine_20260911/4-rebuts/`. Vistes finals a `IA/output/v46_earthshine_20260911/vistes/`. Original V43, V43_detall, V44, TIFF anotat V44, V45 de disc i Capes TotalsV42 verificats perSHA i intactes. Manifest final `research/tools/v46_earthshine_20260911/delivery_manifest.json`.
