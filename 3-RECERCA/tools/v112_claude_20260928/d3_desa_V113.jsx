#target photoshop
// d3 · V113 (Claude, 28-09-2026): obre el PSB de pas de la V113 (variant v113b: V112 + base i filtres refets des de la Sony A corregida contra la B als arcs i a tota la franja de la vora d'A; 301 regenerada)
// i el desa COM A CÒPIA a 1-PHOTOSHOP/V113.psb (PSB, màxima compatibilitat). Els noms ja porten «V113» (m1_munta_v113.py).
// No toca cap altre document obert, mai no sobreescriu i no canvia res del PSB de pas.
// Vista de revisió a 4-RESULTATS/v112_claude_20260928/V113_natiu/.
var ROOT = new File($.fileName).parent.parent.parent.parent;
var SRC = new File(ROOT.fsName + '/4-RESULTATS/v112_claude_20260928/V113b_stage.psb');
var DST = new File(ROOT.fsName + '/1-PHOTOSHOP/V113.psb');
var VIS = new Folder(ROOT.fsName + '/4-RESULTATS/v112_claude_20260928/V113_natiu'); if (!VIS.exists) VIS.create();
var NOMS = {};
var prior = (app.documents.length ? app.activeDocument : null), dialogs = app.displayDialogs, units = app.preferences.rulerUnits, d = null;
function log(s) { var f = new File(VIS.fsName + '/D3_NATIU.log'); f.encoding = 'UTF-8'; f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
function vista(nom, ample) {
    app.activeDocument = d; var x = d.duplicate('V113_' + nom, true);
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
    d = app.open(SRC); log('OBRE ' + d.name + ' ' + d.width + 'x' + d.height + ' capes ' + d.layers.length);
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
'D3_V113_FET';
