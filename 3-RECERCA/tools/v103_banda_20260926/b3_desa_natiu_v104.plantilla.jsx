#target photoshop
// b3 · Desament natiu de la V104 (Claude, 26-09-2026, matinada; a partir del de la V100): obre el PSB de pas __STAGE__, el desa COM A CÒPIA a __DST__
// (PSB, màxima compatibilitat: el Photoshop recompon el compost fusionat) i en fa les vistes de revisió a __VIS__. No toca cap altre document obert.
// La cantonada del logo NO es regenera: la capa nova és a la caixa lunar, lluny de la cantonada, i les capes de sota no hi canvien.
var ROOT = new File($.fileName).parent.parent.parent.parent;
var STAGE = new File(ROOT.fsName + '/__STAGE__'), DST = new File(ROOT.fsName + '/__DST__'), VIS = new Folder(ROOT.fsName + '/__VIS__');
if (!VIS.exists) VIS.create();
var prior = (app.documents.length ? app.activeDocument : null), dialogs = app.displayDialogs, units = app.preferences.rulerUnits, d = null;
function log(s) { var f = new File(VIS.fsName + '/B3_NATIU.log'); f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
function tiff() { var t = new TiffSaveOptions(); t.imageCompression = TIFFEncoding.TIFFLZW; t.embedColorProfile = true; t.layers = false; t.alphaChannels = false; return t; }
function vista(nom, caixa, ample) {
    app.activeDocument = d; var x = d.duplicate('V104_' + nom, true);
    try {
        if (caixa) x.crop([UnitValue(caixa[0], 'px'), UnitValue(caixa[1], 'px'), UnitValue(caixa[2], 'px'), UnitValue(caixa[3], 'px')]);
        if (ample) x.resizeImage(UnitValue(ample, 'px'), null, null, ResampleMethod.BICUBIC);
        x.saveAs(new File(VIS.fsName + '/' + nom + '.tif'), tiff(), true, Extension.LOWERCASE);
    } finally { x.close(SaveOptions.DONOTSAVECHANGES); }
    app.activeDocument = d; log('VISTA ' + nom);
}
try {
    app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS;
    if (DST.exists) throw Error('No clobber: ja existeix ' + DST.fsName);
    d = app.open(STAGE); log('OBRE ' + d.name + ' ' + d.width + 'x' + d.height + ' capes ' + d.layers.length);
    app.refresh(); var hist = d.histogram; log('COMPOST_FORCAT histograma ' + hist.length + ' nivells, suma ' + eval(hist.join('+')));
    var sd = new ActionDescriptor(), so = new ActionDescriptor(); so.putBoolean(stringIDToTypeID('maximizeCompatibility'), true);
    sd.putObject(charIDToTypeID('As  '), stringIDToTypeID('largeDocumentFormat'), so); sd.putPath(charIDToTypeID('In  '), DST); sd.putBoolean(charIDToTypeID('Cpy '), true);
    executeAction(charIDToTypeID('save'), sd, DialogModes.NO); log('DESAT_NATIU ' + DST.fsName);
    vista('V104_llenc_sencer', null, 2400);
    vista('V104_lluna', [4600, 3000, 6150, 4550], null);
    vista('V104_enquadrament_final', [1325, 1142, 9348, 6263], 2400);
    log('COMPLET');
} catch (e) { log('ERROR ' + e + ' línia ' + e.line); throw e; }
finally { if (d) try { d.close(SaveOptions.DONOTSAVECHANGES); } catch (e) {} if (prior) try { app.activeDocument = prior; } catch (e) {} app.displayDialogs = dialogs; app.preferences.rulerUnits = units; }
'B3_V104_FET';
