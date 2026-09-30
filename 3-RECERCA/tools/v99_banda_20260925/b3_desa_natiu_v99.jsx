#target photoshop
// b3 · Desament natiu de la V99 (Claude, 25-09-2026, vespre; còpia del de la V98): obre 4-RESULTATS/v99_banda_20260925/B/V99_stage.psb, el desa com a
// 1-PHOTOSHOP/V99.psb (PSB, màxima compatibilitat: Photoshop recompon el compost fusionat) i en fa les vistes de revisió
// (llenç sencer, Lluna, cantonada) des de la composició de Photoshop, amb el seu ICC. No toca cap altre document obert.
var ROOT = new File($.fileName).parent.parent.parent.parent;
var OUT = new Folder(ROOT.fsName + '/4-RESULTATS/v99_banda_20260925/B'), VIS = new Folder(OUT.fsName + '/vistes');
if (!VIS.exists) VIS.create();
var prior = (app.documents.length ? app.activeDocument : null), dialogs = app.displayDialogs, units = app.preferences.rulerUnits, d = null;
function log(s) { var f = new File(OUT.fsName + '/B3_NATIU.log'); f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
function tiff() { var t = new TiffSaveOptions(); t.imageCompression = TIFFEncoding.TIFFLZW; t.embedColorProfile = true; t.layers = false; t.alphaChannels = false; return t; }
function vista(nom, caixa, ample) {
    app.activeDocument = d; var x = d.duplicate('V99_' + nom, true);
    try {
        if (caixa) x.crop([UnitValue(caixa[0], 'px'), UnitValue(caixa[1], 'px'), UnitValue(caixa[2], 'px'), UnitValue(caixa[3], 'px')]);
        if (ample) x.resizeImage(UnitValue(ample, 'px'), null, null, ResampleMethod.BICUBIC);
        x.saveAs(new File(VIS.fsName + '/' + nom + '.tif'), tiff(), true, Extension.LOWERCASE);
    } finally { x.close(SaveOptions.DONOTSAVECHANGES); }
    app.activeDocument = d; log('VISTA ' + nom);
}
try {
    app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS;
    d = app.open(new File(OUT.fsName + '/V99_stage.psb')); log('OBRE ' + d.name + ' ' + d.width + 'x' + d.height + ' capes ' + d.layers.length);
    // ⛔ 24-09: dos desaments (V95 16:43, V96 20:0x) van sortir amb el COMPOST FUSIONAT malmès (capes bones). Es força el càlcul del compost abans de desar:
    // V98: la cantonada del logo (255) és una capa DERIVADA de les de sota (norma de Pere del 23-09): la base ha canviat (fusió sense el residu
    // local A→B) i al voltant de la cantonada la imatge de sota ha variat fins a un 1,9 % (p95). Es regenera amb el seu script (recepta V79/V86).
    $.evalFile(new File(ROOT.fsName + '/3-RECERCA/tools/v86_neta_20260923/regenera_cantonada.jsx')); app.activeDocument = d; log('CANTONADA_REGENERADA');
    app.refresh(); var hist = d.histogram; log('COMPOST_FORCAT histograma ' + hist.length + ' nivells, suma ' + eval(hist.join('+')));
    var dst = new File(ROOT.fsName + '/1-PHOTOSHOP/V99.psb'); if (dst.exists) throw Error('No clobber: ja existeix V99.psb');
    var sd = new ActionDescriptor(), so = new ActionDescriptor(); so.putBoolean(stringIDToTypeID('maximizeCompatibility'), true);
    sd.putObject(charIDToTypeID('As  '), stringIDToTypeID('largeDocumentFormat'), so); sd.putPath(charIDToTypeID('In  '), dst); sd.putBoolean(charIDToTypeID('Cpy '), true)   // ⛔ 24-09: amb Cpy false el compost fusionat va sortir malmès 4 cops; com a còpia, bé; sd.putBoolean(charIDToTypeID('LwCs'), true);
    executeAction(charIDToTypeID('save'), sd, DialogModes.NO); log('DESAT_NATIU ' + dst.fsName);
    vista('V99_llenc_sencer', null, 2400);
    vista('V99_lluna', [4600, 3000, 6150, 4550], null);
    vista('V99_cantonada', [7356, 4320, 9348, 6263], null);
    vista('V99_enquadrament_final', [1325, 1142, 9348, 6263], 2400);
    for (var i = 0; i < d.layers.length; i++) if (d.layers[i].name.indexOf('Earthshine V88') == 0) { var es = d.layers[i]; var prev = es.visible; es.visible = false;
        try { vista('V99_lluna_sense_earthshine', [4600, 3000, 6150, 4550], null); } finally { es.visible = prev; } }
    log('COMPLET');
} catch (e) { log('ERROR ' + e + ' línia ' + e.line); throw e; }
finally { if (d) try { d.close(SaveOptions.DONOTSAVECHANGES); } catch (e) {} if (prior) try { app.activeDocument = prior; } catch (e) {} app.displayDialogs = dialogs; app.preferences.rulerUnits = units; }
'B3_V99_FET';
