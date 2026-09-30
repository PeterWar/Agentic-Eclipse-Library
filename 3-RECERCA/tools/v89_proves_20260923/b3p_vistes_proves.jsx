#target photoshop
// b3p · Vistes natives (Photoshop, amb les capes d'ajust de Pere) de les proves de la vora esquerra: obre V89_prova_A.psb i V89_prova_B.psb
// d'una en una, exporta la caixa de la Lluna (4600..6150 × 3000..4550) i les TANCA SENSE DESAR. No toca cap altre document obert.
var ROOT = new File($.fileName).parent.parent.parent.parent, DIR = ROOT.fsName + '/4-RESULTATS/v89_proves_20260923', OUT = new Folder(DIR + '/vistes');
if (!OUT.exists) OUT.create();
function log(s) { var f = new File(OUT.fsName + '/B3P.log'); f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
var dialogs = app.displayDialogs, units = app.preferences.rulerUnits;
function tif(doc, nom) { var t = new TiffSaveOptions(); t.imageCompression = TIFFEncoding.TIFFLZW; t.embedColorProfile = true; t.layers = false; t.alphaChannels = false; doc.saveAs(new File(OUT.fsName + '/' + nom + '.tif'), t, true, Extension.LOWERCASE); }
function vista(d, nom, caixa) {
    var x = d.duplicate(nom, true);
    try { x.crop([UnitValue(caixa[0], 'px'), UnitValue(caixa[1], 'px'), UnitValue(caixa[2], 'px'), UnitValue(caixa[3], 'px')]); tif(x, nom); } finally { x.close(SaveOptions.DONOTSAVECHANGES); }
    log('VISTA ' + nom);
}
var noms = ['A', 'B', 'C', 'D', 'E'];
try {
    app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS;
    for (var k = 0; k < noms.length; k++) {
        var f = new File(DIR + '/V89_prova_' + noms[k] + '.psb'); if (!f.exists) { log('NO HI ES ' + f.fsName); continue; }
        if (new File(OUT.fsName + '/prova_' + noms[k] + '_lluna.tif').exists) { log('JA FETA ' + noms[k]); continue; }
        var d = null;
        try { d = app.open(f); log('OBRE ' + d.name + ' ' + d.layers.length + ' capes'); vista(d, 'prova_' + noms[k] + '_lluna', [4600, 3000, 6150, 4550]); }
        catch (e) { log('ERROR ' + noms[k] + ' ' + e); }
        finally { if (d) d.close(SaveOptions.DONOTSAVECHANGES); }
    }
    log('COMPLET');
} catch (e) { log('ERROR ' + e); } finally { app.displayDialogs = dialogs; app.preferences.rulerUnits = units; }
'B3P_FET';
