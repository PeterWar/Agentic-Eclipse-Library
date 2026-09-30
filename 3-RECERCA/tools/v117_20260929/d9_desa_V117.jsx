#target photoshop
function jaObert(f) { for (var i = 0; i < app.documents.length; i++) { if (app.documents[i].name == f.name) return true; } return false; }  // ⛔ 28-09: mai reutilitzar ni tancar un document que Pere tingui obert
// d9 · V117 (Claude, 29-09): desa COM A CÒPIA el pas final de la V117 (la V115 de Pere de les 04:25 + la capa nova 415 del filtre A·B corregit, al 25 %, i la 301 regenerada) a 1-PHOTOSHOP/V117.psb.
// PSB, màxima compatibilitat. La capa nova ja porta el nom «· V117» (m6_munta_v117.py).
// No toca cap altre document obert, mai no sobreescriu i no canvia res del PSB de pas.
// Vista de revisió a 4-RESULTATS/v117_20260929/V117_natiu/.
var ROOT = new File($.fileName).parent.parent.parent.parent;
var SRC = new File(ROOT.fsName + '/4-RESULTATS/v117_20260929/stage_final.psb');
var DST = new File(ROOT.fsName + '/1-PHOTOSHOP/V117.psb');
var VIS = new Folder(ROOT.fsName + '/4-RESULTATS/v117_20260929/V117_natiu'); if (!VIS.exists) VIS.create();
var NOMS = {};
var prior = (app.documents.length ? app.activeDocument : null), dialogs = app.displayDialogs, units = app.preferences.rulerUnits, d = null;
function log(s) { var f = new File(VIS.fsName + '/D9_NATIU.log'); f.encoding = 'UTF-8'; f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
function vista(nom, ample) {
    app.activeDocument = d; var x = d.duplicate('V117_' + nom, true);
    try {
        if (ample) x.resizeImage(UnitValue(ample, 'px'), null, null, ResampleMethod.BICUBIC);
        var t = new TiffSaveOptions(); t.imageCompression = TIFFEncoding.NONE; t.embedColorProfile = true; t.layers = false; t.alphaChannels = false;
        var f = new File(VIS.fsName + '/' + nom + '.tif'); if (f.exists) throw Error('Existeix ' + f.fsName);
        x.saveAs(f, t, true, Extension.LOWERCASE);
    } finally { x.close(SaveOptions.DONOTSAVECHANGES); }
    app.activeDocument = d; log('VISTA ' + nom);
}
try {
    app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS;
    if (!SRC.exists) throw Error('No trobo ' + SRC.fsName);
    if (DST.exists) throw Error('No clobber: ja existeix ' + DST.fsName);
    if (jaObert(SRC)) throw Error('OBERT_PER_PERE: ' + SRC.name + ' ja és obert al Photoshop; no el toco'); d = app.open(SRC); log('OBRE ' + d.name + ' ' + d.width + 'x' + d.height + ' capes ' + d.layers.length);
    var fets = 0;
    for (var i = 0; i < d.layers.length; i++) {
        var L = d.layers[i];
        if (NOMS.hasOwnProperty(L.id)) { var v = L.visible; log('NOM ' + L.id + ': «' + L.name + '» → «' + NOMS[L.id] + '»'); L.name = NOMS[L.id]; L.visible = v; fets++; }
    }
    if (fets != 0) throw Error('no s\'havia de reanomenar res');
    app.refresh(); var hist = d.histogram; log('COMPOST_FORCAT ' + hist.length);
    var sd = new ActionDescriptor(), so = new ActionDescriptor(); so.putBoolean(stringIDToTypeID('maximizeCompatibility'), true);
    sd.putObject(charIDToTypeID('As  '), stringIDToTypeID('largeDocumentFormat'), so); sd.putPath(charIDToTypeID('In  '), DST); sd.putBoolean(charIDToTypeID('Cpy '), true);
    executeAction(charIDToTypeID('save'), sd, DialogModes.NO); log('DESAT_NATIU ' + DST.fsName);
    vista('visible_complet', null);
    vista('llenc_sencer', 2400);
    log('COMPLET');
} catch (e) { log('ERROR ' + e + ' línia ' + e.line); throw e; }
finally { if (d) try { d.close(SaveOptions.DONOTSAVECHANGES); } catch (e) {} if (prior) try { app.activeDocument = prior; } catch (e) {} app.displayDialogs = dialogs; app.preferences.rulerUnits = units; }
'D9_V117_FET';
