#target photoshop
// f2 · Vistes natives de la prova F (claredat amb màscara radial): obre V89_prova_F.psb, exporta la caixa de la Lluna (4600..6150 × 3000..4550)
// i el llenç sencer reduït a 2638 px d'amplada (com la vista de la V88), i la TANCA SENSE DESAR. No toca cap altre document.
var ROOT = new File($.fileName).parent.parent.parent.parent, DIR = ROOT.fsName + '/4-RESULTATS/v89_claredat_20260923', OUT = new Folder(DIR + '/vistes');
if (!OUT.exists) OUT.create();
function log(s) { var f = new File(OUT.fsName + '/F2.log'); f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
var dialogs = app.displayDialogs, units = app.preferences.rulerUnits, d = null;
function tif(doc, nom) { var t = new TiffSaveOptions(); t.imageCompression = TIFFEncoding.TIFFLZW; t.embedColorProfile = true; t.layers = false; t.alphaChannels = false; doc.saveAs(new File(OUT.fsName + '/' + nom + '.tif'), t, true, Extension.LOWERCASE); }
function vista(nom, caixa, amplada) {
    var x = d.duplicate(nom, true);
    try { if (caixa) x.crop([UnitValue(caixa[0], 'px'), UnitValue(caixa[1], 'px'), UnitValue(caixa[2], 'px'), UnitValue(caixa[3], 'px')]);
          if (amplada) x.resizeImage(UnitValue(amplada, 'px'), null, null, ResampleMethod.BICUBIC);
          tif(x, nom); } finally { x.close(SaveOptions.DONOTSAVECHANGES); }
    log('VISTA ' + nom);
}
try {
    app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS;
    d = app.open(new File(DIR + '/V89_prova_F.psb')); log('OBRE ' + d.name + ' ' + d.layers.length + ' capes');
    vista('prova_F_lluna', [4600, 3000, 6150, 4550], null);
    vista('prova_F_llenc', null, 2638);
    log('COMPLET');
} catch (e) { log('ERROR ' + e); } finally {
    if (d) d.close(SaveOptions.DONOTSAVECHANGES);
    app.displayDialogs = dialogs; app.preferences.rulerUnits = units;
}
'F2_FET';
