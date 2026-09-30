#target photoshop
// b1 · Vistes natives de la V87 de Pere SENSE la capa de marques (Artefactes V87): obre, amaga la capa, exporta i TANCA SENSE DESAR.
var ROOT = new File($.fileName).parent.parent.parent.parent, OUT = new Folder(ROOT.fsName + '/4-RESULTATS/v88_20260923/vistes_v87');
if (!OUT.exists) OUT.create();
function log(s) { var f = new File(OUT.fsName + '/B1.log'); f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
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
    d = app.open(new File(ROOT.fsName + '/1-PHOTOSHOP/V87.psb')); log('OBRE ' + d.layers.length + ' capes');
    var marques = null; for (var i = 0; i < d.layers.length; i++) if (d.layers[i].name === 'Artefactes V87') marques = d.layers[i];
    if (!marques) throw Error('No trobo la capa Artefactes V87');
    vista('V87_amb_marques_lluna', [4600, 3000, 6150, 4550], null);
    marques.visible = false;
    vista('V87_lluna', [4600, 3000, 6150, 4550], null);
    vista('V87_llenc_sencer', null, 3000);
    // la Lluna sola (capa 225) i la pila de sota de la Lluna, per separar què ve dels filtres i què de la Lluna
    var lluna = null; for (var i = 0; i < d.layers.length; i++) if (d.layers[i].name === 'Earthshine V86') lluna = d.layers[i];
    lluna.visible = false; vista('V87_sense_lluna_lluna', [4600, 3000, 6150, 4550], null); lluna.visible = true;
    log('COMPLET');
} catch (e) { log('ERROR ' + e); } finally {
    if (d) d.close(SaveOptions.DONOTSAVECHANGES);
    app.displayDialogs = dialogs; app.preferences.rulerUnits = units;
}
'B1_FET';
