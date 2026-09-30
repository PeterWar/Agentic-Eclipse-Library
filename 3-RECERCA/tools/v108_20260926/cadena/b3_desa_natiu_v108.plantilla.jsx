#target photoshop
function jaObert(f) { for (var i = 0; i < app.documents.length; i++) { if (app.documents[i].name == f.name) return true; } return false; }  // ⛔ 28-09: mai reutilitzar ni tancar un document que Pere tingui obert
// b3 · Desament natiu de la V108 (Claude, 26-09-2026, nit; còpia de la plantilla de la V106): obre el PSB de pas __STAGE__, el desa COM A CÒPIA a
// __DST__ (PSB, màxima compatibilitat: el Photoshop recompon el compost fusionat, que al PSB de pas encara és el de la V107) i en fa les vistes de
// revisió a __VIS__. No toca cap altre document obert (Pere pot tenir-hi la V107 oberta) i mai no sobreescriu.
// La cantonada del logo (301) NO es regenera: a la V107 és oculta.
// Aquest fitxer és a 3-RECERCA/tools/v108_20260926/cadena/: l'arrel del projecte és 5 carpetes amunt del JSX generat.
var ROOT = new File($.fileName).parent.parent.parent.parent.parent;
var STAGE = new File(ROOT.fsName + '/__STAGE__'), DST = new File(ROOT.fsName + '/__DST__'), VIS = new Folder(ROOT.fsName + '/__VIS__');
if (!VIS.exists) VIS.create();
var prior = (app.documents.length ? app.activeDocument : null), dialogs = app.displayDialogs, units = app.preferences.rulerUnits, d = null;
function log(s) { var f = new File(VIS.fsName + '/B3_NATIU.log'); f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
function tiff() { var t = new TiffSaveOptions(); t.imageCompression = TIFFEncoding.TIFFLZW; t.embedColorProfile = true; t.layers = false; t.alphaChannels = false; return t; }
function vista(nom, caixa, ample) {
    app.activeDocument = d; var x = d.duplicate('V108_' + nom, true);
    try {
        if (caixa) x.crop([UnitValue(caixa[0], 'px'), UnitValue(caixa[1], 'px'), UnitValue(caixa[2], 'px'), UnitValue(caixa[3], 'px')]);
        if (ample) x.resizeImage(UnitValue(ample, 'px'), null, null, ResampleMethod.BICUBIC);
        x.saveAs(new File(VIS.fsName + '/' + nom + '.tif'), tiff(), true, Extension.LOWERCASE);
    } finally { x.close(SaveOptions.DONOTSAVECHANGES); }
    app.activeDocument = d; log('VISTA ' + nom);
}
try {
    app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS;
    if (!STAGE.exists) throw Error('No trobo el PSB de pas ' + STAGE.fsName);
    if (DST.exists) throw Error('No clobber: ja existeix ' + DST.fsName);
    if (jaObert(STAGE)) throw Error('OBERT_PER_PERE: ' + STAGE.name + ' ja és obert al Photoshop; no el toco'); d = app.open(STAGE); log('OBRE ' + d.name + ' ' + d.width + 'x' + d.height + ' capes ' + d.layers.length);
    app.refresh(); var hist = d.histogram; log('COMPOST_FORCAT histograma ' + hist.length + ' nivells, suma ' + eval(hist.join('+')));
    var sd = new ActionDescriptor(), so = new ActionDescriptor(); so.putBoolean(stringIDToTypeID('maximizeCompatibility'), true);
    sd.putObject(charIDToTypeID('As  '), stringIDToTypeID('largeDocumentFormat'), so); sd.putPath(charIDToTypeID('In  '), DST); sd.putBoolean(charIDToTypeID('Cpy '), true);
    executeAction(charIDToTypeID('save'), sd, DialogModes.NO); log('DESAT_NATIU ' + DST.fsName);
    vista('V108_llenc_sencer', null, 2400);
    vista('V108_lluna', [4600, 3000, 6150, 4550], null);
    vista('V108_enquadrament_final', [1325, 1142, 9348, 6263], 2400);
    log('COMPLET');
} catch (e) { log('ERROR ' + e + ' línia ' + e.line); throw e; }
finally { if (d) try { d.close(SaveOptions.DONOTSAVECHANGES); } catch (e) {} if (prior) try { app.activeDocument = prior; } catch (e) {} app.displayDialogs = dialogs; app.preferences.rulerUnits = units; }
'B3_V108_FET';
