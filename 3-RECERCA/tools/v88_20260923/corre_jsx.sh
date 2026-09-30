#!/bin/zsh
# corre_jsx.sh <fitxer.jsx> — executa un script al Photoshop obert amb $.evalFile (així $.fileName hi és i les rutes són relatives).
if [ -z "$1" ]; then echo "ús: corre_jsx.sh <fitxer.jsx>"; exit 2; fi
F="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
osascript <<AS
tell application id "com.adobe.Photoshop"
  with timeout of 7200 seconds
    do javascript "\$.evalFile(new File('$F'));"
  end timeout
end tell
AS
