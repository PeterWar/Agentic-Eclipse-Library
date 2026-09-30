#target photoshop
// a10 · Prova de regenera_cantonada.jsx sobre la V86 desada: obre 1-PHOTOSHOP/V86.psb, regenera la cantonada amb el compost de
// Photoshop, en desa la vista de la caixa i TANCA SENSE DESAR (la V86 no es toca). Compara't amb vistes/V86_cantonada.tif.
var ROOT = new File($.fileName).parent.parent.parent.parent, EINES = new File($.fileName).parent;
var OUT = new Folder(ROOT.fsName + '/4-RESULTATS/v86_neta_20260923/vistes'), d = null, t0 = new Date().getTime();
var dialogs = app.displayDialogs, units = app.preferences.rulerUnits;
function log(s) { var f = new File(ROOT.fsName + '/4-RESULTATS/v86_neta_20260923/A10_PROVA_CANTONADA.log'); f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
try {
    app.displayDialogs = DialogModes.NO; app.preferences.rulerUnits = Units.PIXELS;
    d = app.open(new File(ROOT.fsName + '/1-PHOTOSHOP/V86.psb')); log('OBRE ' + d.layers.length + ' capes');
    var t1 = new Date().getTime(); $.evalFile(new File(EINES.fsName + '/regenera_cantonada.jsx')); log('REGENERADA en ' + ((new Date().getTime() - t1) / 1000) + ' s');
    var x = d.duplicate('prova', true);
    try { x.crop([UnitValue(7356, 'px'), UnitValue(4320, 'px'), UnitValue(9348, 'px'), UnitValue(6263, 'px')]); var t = new TiffSaveOptions(); t.imageCompression = TIFFEncoding.TIFFLZW; t.embedColorProfile = true; t.layers = false; t.alphaChannels = false;
          x.saveAs(new File(OUT.fsName + '/V86_cantonada_regenerada_photoshop.tif'), t, true, Extension.LOWERCASE); } finally { x.close(SaveOptions.DONOTSAVECHANGES); }
    log('VISTA desada; total ' + ((new Date().getTime() - t0) / 1000) + ' s');
} catch (e) { log('ERROR ' + e + ' línia ' + e.line); throw e; }
finally { if (d) d.close(SaveOptions.DONOTSAVECHANGES); app.displayDialogs = dialogs; app.preferences.rulerUnits = units; }
'A10_FET';
