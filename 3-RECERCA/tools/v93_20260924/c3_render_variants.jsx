#target photoshop
// c3 · Renders natius per a la diagnosi de la V93 (Claude, 24-09-2026): obre una CÒPIA (clon APFS) de la V92 de Pere, amaga la capa de marques
// «Artefactes V92» i exporta el compost amb variants de visibilitat (llenç a 1/4 i la caixa de la Lluna a 1:1). Tanca sense desar. No toca cap altre document.
var ROOT = new File($.fileName).parent.parent.parent.parent;
var OUT = new Folder(ROOT.fsName + '/4-RESULTATS/v93_20260924/renders'); if (!OUT.exists) OUT.create();
function log(s) { var f = new File(OUT.fsName + '/C3_RENDERS.log'); f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
function tiff() { var t = new TiffSaveOptions(); t.imageCompression = TIFFEncoding.TIFFLZW; t.embedColorProfile = true; t.layers = false; t.alphaChannels = false; return t; }
var prior = (app.documents.length ? app.activeDocument : null), dialogs = app.displayDialogs, units = app.preferences.rulerUnits, d = null;
function nomes(fn) { var out = []; for (var i = 0; i < d.layers.length; i++) if (fn(d.layers[i].name)) out.push(d.layers[i]); return out; }
function exporta(nom, lluna) {
    app.activeDocument = d; var x = d.duplicate('R_' + nom, true);
    try { x.resizeImage(UnitValue(2638, 'px'), null, null, ResampleMethod.BICUBIC); x.saveAs(new File(OUT.fsName + '/' + nom + '_quart.tif'), tiff(), true, Extension.LOWERCASE); }
    finally { x.close(SaveOptions.DONOTSAVECHANGES); }
    if (lluna) { app.activeDocument = d; var y = d.duplicate('L_' + nom, true);
        try { y.crop([UnitValue(4600, 'px'), UnitValue(3000, 'px'), UnitValue(6150, 'px'), UnitValue(4550, 'px')]); y.saveAs(new File(OUT.fsName + '/' + nom + '_lluna.tif'), tiff(), true, Extension.LOWERCASE); }
        finally { y.close(SaveOptions.DONOTSAVECHANGES); } }
    app.activeDocument = d; log('EXPORTA ' + nom);
}
try {
    app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS;
    d = app.open(new File(ROOT.fsName + '/4-RESULTATS/v93_20260924/V92_copia_render.psb')); log('OBRE ' + d.name + ' capes ' + d.layers.length);
    var marques = nomes(function (n) { return n.indexOf('Artefactes V92') == 0; }); for (var i = 0; i < marques.length; i++) marques[i].visible = false;
    exporta('V0_tal_com_esta', true);
    var grups = [['V1_sense_claredat', function (n) { return n.indexOf('Claridad') == 0; }],
                 ['V2_sense_capes_ajust', function (n) { return /^(Luz|Color e int|Claridad|Niveles|Exposici|Tono)/.test(n); }],
                 ['V3_sense_76', function (n) { return n.indexOf('Interiors 06') == 0; }],
                 ['V4_sense_96', function (n) { return n.indexOf('07 1/15') == 0; }],
                 ['V5_sense_cantonada', function (n) { return n.indexOf('Cantonada') == 0; }],
                 ['V6_sense_filtres', function (n) { return /V92/.test(n) && n.indexOf('Artefactes') != 0; }],
                 ['V7_sense_earthshine', function (n) { return n.indexOf('Earthshine V88') == 0; }]];
    for (var g = 0; g < grups.length; g++) {
        var ls = nomes(grups[g][1]), prev = [];
        for (var i = 0; i < ls.length; i++) { prev.push(ls[i].visible); ls[i].visible = false; }
        log(grups[g][0] + ': ' + ls.length + ' capes amagades');
        exporta(grups[g][0], grups[g][0] == 'V7_sense_earthshine' || grups[g][0] == 'V2_sense_capes_ajust');
        for (var i = 0; i < ls.length; i++) ls[i].visible = prev[i];
    }
    log('COMPLET');
} catch (e) { log('ERROR ' + e + ' línia ' + e.line); throw e; }
finally { if (d) try { d.close(SaveOptions.DONOTSAVECHANGES); } catch (e) {} if (prior) try { app.activeDocument = prior; } catch (e) {} app.displayDialogs = dialogs; app.preferences.rulerUnits = units; }
'C3_FET';
