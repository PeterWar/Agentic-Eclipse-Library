#target photoshop
function jaObert(f) { for (var i = 0; i < app.documents.length; i++) { if (app.documents[i].name == f.name) return true; } return false; }  // ⛔ 28-09: mai reutilitzar ni tancar un document que Pere tingui obert
// l0 · llista les capes tal com les veu el Photoshop (índex DOM, id, nom, visible) d'un PSB, sense desar res. Ús: $.evalFile amb SRC definit a sota.
var ROOT = new File($.fileName).parent.parent.parent.parent;
var SRC = new File(ROOT.fsName + '/1-PHOTOSHOP/V113.psb');
var OUT = new File(ROOT.fsName + '/4-RESULTATS/v114_estrelles_20260928/L0_capes_photoshop_V113.txt');
var prior = app.documents.length ? app.activeDocument : null, dialogs = app.displayDialogs, d = null;
try { app.displayDialogs = DialogModes.NO; if (jaObert(SRC)) throw Error('OBERT_PER_PERE: ' + SRC.name + ' ja és obert al Photoshop; no el toco'); d = app.open(SRC); OUT.encoding = 'UTF-8'; OUT.open('w');
  for (var i = 0; i < d.layers.length; i++) { var L = d.layers[i]; OUT.writeln(i + '\t' + L.id + '\t' + L.visible + '\t' + L.name); }
  OUT.close();
} finally { if (d) d.close(SaveOptions.DONOTSAVECHANGES); if (prior) app.activeDocument = prior; app.displayDialogs = dialogs; }
'L0_FET';
