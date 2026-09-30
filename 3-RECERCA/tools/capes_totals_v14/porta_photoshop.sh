#!/bin/zsh
# porta_photoshop.sh <fitxer.psd|psb> — la porta definitiva: l'obre el
# Photoshop DE VERITAT, sense diàlegs, i el tanca sense desar.
#
# ⛔ Lliçó del 28-08-2026 (research/119): psd-tools + sips + ImageMagick van
# donar el PSB per bo i Photoshop el refusava (signatures 8BIM/8B64 dels
# blocs globals de PSB). Cap lector independent no substitueix el de debò:
# si aquest script no diu OBRE, el fitxer NO es lliura.
#
# ⛔ Lliçó del 28-09-2026: app.open() d'un fitxer que Pere ja té obert NO l'obre de nou: retorna el SEU document, i el
# close(DONOTSAVECHANGES) del final el tanca i en perd els canvis no desats. Si el fitxer ja és obert, la porta no s'executa.
if [ -z "$1" ]; then echo "ús: porta_photoshop.sh <fitxer>"; exit 2; fi
if ! osascript -e 'tell application id "com.adobe.Photoshop" to get name' >/dev/null 2>&1; then
  echo "SENSE PHOTOSHOP (porta no executada)"; exit 3
fi
osascript <<AS
tell application id "com.adobe.Photoshop"
  -- ⛔ 29-08-2026: sense això, un PSB de 3+ GB peta amb AppleEvent -1712
  -- (caducitat de 120 s per defecte) i la porta sembla un rebuig quan no ho és.
  with timeout of 3600 seconds
  set jsx to "app.displayDialogs = DialogModes.NO; var r; var f0 = new File('$1'); var obert = false; for (var i = 0; i < app.documents.length; i++) { if (app.documents[i].name == f0.name) obert = true; } if (obert) { r = 'NO EXECUTADA: ' + f0.name + ' ja és obert al Photoshop (no es toca cap document de Pere)'; } else try { var d = app.open(f0); r = 'OBRE ' + d.width + ' x ' + d.height + ' · ' + d.artLayers.length + ' capes'; d.close(SaveOptions.DONOTSAVECHANGES); } catch (e) { r = 'REFUSA: ' + e.message; } r;"
  do javascript jsx
  end timeout
end tell
AS
