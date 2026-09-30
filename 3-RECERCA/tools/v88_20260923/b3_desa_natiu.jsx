#target photoshop
// b3 · Desament natiu de la V88 (Claude, 23-09-2026): obre 4-RESULTATS/v88_20260923/V88_stage.psb, el desa com a
// 1-PHOTOSHOP/V88.psb (PSB, màxima compatibilitat: Photoshop recompon el compost fusionat) i en fa les vistes de revisió
// (llenç sencer, Lluna, cantonada) des de la composició de Photoshop, amb el seu ICC. No toca cap altre document obert.
var ROOT = new File($.fileName).parent.parent.parent.parent;
var OUT = new Folder(ROOT.fsName + '/4-RESULTATS/v88_20260923'), VIS = new Folder(OUT.fsName + '/vistes');
if (!VIS.exists) VIS.create();
var prior = (app.documents.length ? app.activeDocument : null), dialogs = app.displayDialogs, units = app.preferences.rulerUnits, d = null;
function log(s) { var f = new File(OUT.fsName + '/B3_NATIU.log'); f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
function tiff() { var t = new TiffSaveOptions(); t.imageCompression = TIFFEncoding.TIFFLZW; t.embedColorProfile = true; t.layers = false; t.alphaChannels = false; return t; }
function vista(nom, caixa, ample) {
    app.activeDocument = d; var x = d.duplicate('V88_' + nom, true);
    try {
        if (caixa) x.crop([UnitValue(caixa[0], 'px'), UnitValue(caixa[1], 'px'), UnitValue(caixa[2], 'px'), UnitValue(caixa[3], 'px')]);
        if (ample) x.resizeImage(UnitValue(ample, 'px'), null, null, ResampleMethod.BICUBIC);
        x.saveAs(new File(VIS.fsName + '/' + nom + '.tif'), tiff(), true, Extension.LOWERCASE);
    } finally { x.close(SaveOptions.DONOTSAVECHANGES); }
    app.activeDocument = d; log('VISTA ' + nom);
}
try {
    app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS;
    d = app.open(new File(OUT.fsName + '/V88_stage.psb')); log('OBRE ' + d.name + ' ' + d.width + 'x' + d.height + ' capes ' + d.layers.length);
    var dst = new File(ROOT.fsName + '/1-PHOTOSHOP/V88.psb'); if (dst.exists) throw Error('No clobber: ja existeix V88.psb');
    var sd = new ActionDescriptor(), so = new ActionDescriptor(); so.putBoolean(stringIDToTypeID('maximizeCompatibility'), true);
    sd.putObject(charIDToTypeID('As  '), stringIDToTypeID('largeDocumentFormat'), so); sd.putPath(charIDToTypeID('In  '), dst); sd.putBoolean(charIDToTypeID('Cpy '), false); sd.putBoolean(charIDToTypeID('LwCs'), true);
    executeAction(charIDToTypeID('save'), sd, DialogModes.NO); log('DESAT_NATIU ' + dst.fsName);
    vista('V88_llenc_sencer', null, 2400);
    vista('V88_lluna', [4600, 3000, 6150, 4550], null);
    vista('V88_cantonada', [7356, 4320, 9348, 6263], null);
    vista('V88_enquadrament_final', [1325, 1142, 9348, 6263], 2400);
    log('COMPLET');
} catch (e) { log('ERROR ' + e + ' línia ' + e.line); throw e; }
finally { if (d) try { d.close(SaveOptions.DONOTSAVECHANGES); } catch (e) {} if (prior) try { app.activeDocument = prior; } catch (e) {} app.displayDialogs = dialogs; app.preferences.rulerUnits = units; }
'A8_FET';
