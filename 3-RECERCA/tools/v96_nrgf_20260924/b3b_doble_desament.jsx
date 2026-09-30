#target photoshop
// b3b · Diagnosi del compost fusionat malmès: obre V96_stage.psb, força el compost, desa (1) a 4-RESULTATS/.../V96_d1.psb; espera 20 s, força i desa (2) a V96_d2.psb.
// No toca cap altre document. No sobreescriu res.
var ROOT = new File($.fileName).parent.parent.parent.parent; var OUT = new Folder(ROOT.fsName + '/4-RESULTATS/v96_nrgf_20260924');
var prior = (app.documents.length ? app.activeDocument : null), dialogs = app.displayDialogs, d = null;
function log(s) { var f = new File(OUT.fsName + '/B3B_DOBLE.log'); f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
function desa(nom) {
    var dst = new File(OUT.fsName + '/' + nom); if (dst.exists) throw Error('No clobber: ' + nom);
    var sd = new ActionDescriptor(), so = new ActionDescriptor(); so.putBoolean(stringIDToTypeID('maximizeCompatibility'), true);
    sd.putObject(charIDToTypeID('As  '), stringIDToTypeID('largeDocumentFormat'), so); sd.putPath(charIDToTypeID('In  '), dst); sd.putBoolean(charIDToTypeID('Cpy '), true); sd.putBoolean(charIDToTypeID('LwCs'), true);
    executeAction(charIDToTypeID('save'), sd, DialogModes.NO); log('DESAT ' + nom);
}
try {
    app.displayDialogs = DialogModes.NO; d = app.open(new File(OUT.fsName + '/V96_stage.psb')); log('OBRE ' + d.name);
    app.refresh(); var h = d.histogram; log('HIST1 ' + h.length); desa('V96_d1.psb');
    $.sleep(20000); app.refresh(); h = d.histogram; log('HIST2 ' + h.length); desa('V96_d2.psb'); log('COMPLET');
} catch (e) { log('ERROR ' + e + ' línia ' + e.line); throw e; }
finally { if (d) try { d.close(SaveOptions.DONOTSAVECHANGES); } catch (e) {} if (prior) try { app.activeDocument = prior; } catch (e) {} app.displayDialogs = dialogs; }
'B3B_FET';
