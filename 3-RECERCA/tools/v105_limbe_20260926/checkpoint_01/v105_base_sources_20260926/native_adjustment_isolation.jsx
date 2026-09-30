#target photoshop
// Diagnostic only. Reads the saved P01 native pilot; never saves a PSB.
// Export after FULL-CANVAS recomposition, then crop. Cropping the layered
// document first would change the context of nonlocal adjustment algorithms.
var SOURCE = new File('/private/tmp/v105_root_pilots_20260926/P01/native/V105_P01.psb');
var OUT = new Folder('/private/tmp/v105_base_sources_20260926/native_adjustment_isolation_01');
var BOX = [4600,3000,6150,4550];
var prior = app.documents.length ? app.activeDocument : null;
var dialogs = app.displayDialogs, units = app.preferences.rulerUnits;
var sourceDoc = null, sourceOwned = false, d = null;
function write(name, text) {
    var f = new File(OUT.fsName + '/' + name); f.encoding='UTF8';
    f.open('w'); f.write(text); f.close();
}
function log(text) {
    var f = new File(OUT.fsName + '/RUN.log'); f.encoding='UTF8';
    f.open('a'); f.writeln(new Date().toUTCString() + ' ' + text); f.close();
}
function findID(container, id) {
    for (var i=0;i<container.layers.length;i++) {
        var l=container.layers[i]; if (l.id===id) return l;
        if (l.typename==='LayerSet') { var x=findID(l,id); if (x) return x; }
    }
    return null;
}
function exportView(name) {
    app.activeDocument=d; app.refresh(); var forceHistogram=d.histogram;
    var flat=d.duplicate('V105_CONTEXT_QA_'+name,true);
    try {
        flat.crop([UnitValue(BOX[0],'px'),UnitValue(BOX[1],'px'),UnitValue(BOX[2],'px'),UnitValue(BOX[3],'px')]);
        var opts=new TiffSaveOptions(); opts.imageCompression=TIFFEncoding.TIFFLZW;
        opts.embedColorProfile=true; opts.layers=false; opts.alphaChannels=false;
        flat.saveAs(new File(OUT.fsName+'/'+name+'.tif'),opts,true,Extension.LOWERCASE);
    } finally { flat.close(SaveOptions.DONOTSAVECHANGES); }
    app.activeDocument=d; log('EXPORTED '+name+' histogramBins='+forceHistogram.length);
}
try {
    if (!SOURCE.exists) throw Error('Missing saved source');
    if (OUT.exists) throw Error('Diagnostic directory already exists; do not overwrite');
    if (!OUT.create()) throw Error('Cannot create diagnostic directory');
    app.displayDialogs=DialogModes.NO; app.preferences.rulerUnits=Units.PIXELS;
    // Preserve a pre-existing document, including any unsaved state.
    for (var i=0;i<app.documents.length;i++) {
        try { if (app.documents[i].fullName.fsName===SOURCE.fsName) sourceDoc=app.documents[i]; } catch(ignore) {}
    }
    if (sourceDoc) {
        // Unsaved changes would make this a different input from the saved file.
        if (!sourceDoc.saved) throw Error('P01 source is already open with unsaved changes; no state modified');
    } else { sourceDoc=app.open(SOURCE); sourceOwned=true; }
    app.activeDocument=sourceDoc;
    d=sourceDoc.duplicate('V105_CONTEXT_ISOLATION_WORKING_COPY',false);
    // Photoshop may assign fresh IDs on duplication; names are exact in this source.
    var base=d.artLayers.getByName('00 Base · fotografia observada V105');
    var old=d.artLayers.getByName('00 Base V104 original · referencia oculta');
    var reference=d.artLayers.getByName('09 1/60 x2');
    var luz=d.artLayers.getByName('Luz 1');
    var clarity=d.artLayers.getByName('Claridad y borrar neblina 1');
    var initial='source='+SOURCE.fsName+'\nsourceBytes='+SOURCE.length+'\nsourceModified='+SOURCE.modified.toUTCString()+
        '\nwidth='+d.width+'\nheight='+d.height+'\nprofile='+d.colorProfileName+'\nbaseMode='+base.blendMode+'\noldMode='+old.blendMode+
        '\nbaseOpacity='+base.opacity+'\noldOpacity='+old.opacity+'\ninitialLuzVisible='+luz.visible+'\ninitialClarityVisible='+clarity.visible+
        '\ncrop='+BOX.join(',')+'\nmethod=full-canvas merged duplicate first, unscaled crop second\n';
    write('INPUT.txt',initial); log('BEGIN work only on temporary document duplicate');
    reference.visible=false;
    var cases=[
        ['both_off',false,false],
        ['luz_off_clarity_on',false,true],
        ['luz_on_clarity_off',true,false],
        ['both_on',true,true]
    ];
    for (var k=0;k<cases.length;k++) {
        var c=cases[k]; luz.visible=c[1]; clarity.visible=c[2];
        base.visible=false; old.visible=true; exportView(c[0]+'_old');
        base.visible=true; old.visible=false; exportView(c[0]+'_new');
    }
    log('COMPLETE: eight crops; no PSB saved; original document untouched');
} catch(e) {
    if (OUT.exists) log('ERROR '+e+' line '+e.line);
    throw e;
} finally {
    if (d) try { d.close(SaveOptions.DONOTSAVECHANGES); } catch(ignore) {}
    if (sourceOwned && sourceDoc) try { sourceDoc.close(SaveOptions.DONOTSAVECHANGES); } catch(ignore) {}
    if (prior) try { app.activeDocument=prior; } catch(ignore) {}
    app.displayDialogs=dialogs; app.preferences.rulerUnits=units;
}
