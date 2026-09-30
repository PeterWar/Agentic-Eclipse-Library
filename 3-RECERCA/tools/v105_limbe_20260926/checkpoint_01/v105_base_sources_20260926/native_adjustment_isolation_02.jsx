#target photoshop
// ASCII-only diagnostic; source and every original are read only.
// Full-canvas merged duplication precedes the crop, preserving context.
var SOURCE=new File('/private/tmp/v105_root_pilots_20260926/P01/native/V105_P01.psb');
var OUT=new Folder('/private/tmp/v105_base_sources_20260926/native_adjustment_isolation_02');
var BOX=[4600,3000,6150,4550];
var prior=app.documents.length ? app.activeDocument : null;
var dialogs=app.displayDialogs, units=app.preferences.rulerUnits;
var sourceDoc=null, sourceOwned=false, d=null;
function write(name,text) {var f=new File(OUT.fsName+'/'+name);f.encoding='UTF8';if(!f.open('w'))throw Error('Cannot write '+name);f.write(text);f.close();}
function log(text) {var f=new File(OUT.fsName+'/RUN.log');f.encoding='UTF8';f.open('a');f.writeln(new Date().toUTCString()+' '+text);f.close();}
function inventory(c,path,out) {
    for(var i=0;i<c.layers.length;i++) {
        var l=c.layers[i],p=path.concat([i]);
        out.push({path:p,id:l.id,name:l.name,type:l.typename});
        if(l.typename==='LayerSet')inventory(l,p,out);
    }
}
function at(c,path) {for(var j=0;j<path.length;j++)c=c.layers[path[j]];return c;}
function locate(items,id,name) {
    var byID=[],byName=[];
    for(var i=0;i<items.length;i++){if(items[i].id===id)byID.push(items[i]);if(items[i].name===name)byName.push(items[i]);}
    if(byID.length===1) {
        if(byID[0].name!==name)throw Error('ID/name disagreement for '+id+': '+byID[0].name);
        return byID[0];
    }
    if(byID.length===0 && byName.length===1) {log('ID absent; unique exact-name fallback for '+id);return byName[0];}
    throw Error('Ambiguous or missing source layer '+id+' IDmatches='+byID.length+' nameMatches='+byName.length);
}
function mapped(rec) {
    var l=at(d,rec.path);
    if(l.name!==rec.name || l.typename!==rec.type)throw Error('Duplicate topology/name differs at '+rec.path.join('/'));
    return l;
}
function exportView(name) {
    app.activeDocument=d;app.refresh();var forceHistogram=d.histogram;
    var flat=d.duplicate('V105_CONTEXT_QA_'+name,true);
    try {
        flat.crop([UnitValue(BOX[0],'px'),UnitValue(BOX[1],'px'),UnitValue(BOX[2],'px'),UnitValue(BOX[3],'px')]);
        var opts=new TiffSaveOptions();opts.imageCompression=TIFFEncoding.TIFFLZW;opts.embedColorProfile=true;opts.layers=false;opts.alphaChannels=false;
        flat.saveAs(new File(OUT.fsName+'/'+name+'.tif'),opts,true,Extension.LOWERCASE);
    } finally {flat.close(SaveOptions.DONOTSAVECHANGES);}
    app.activeDocument=d;log('EXPORTED '+name+' histogramBins='+forceHistogram.length);
}
try {
    if(!SOURCE.exists)throw Error('Missing saved source');
    if(OUT.exists)throw Error('Output directory already exists; do not overwrite');
    if(!OUT.create())throw Error('Cannot create output directory');
    app.displayDialogs=DialogModes.NO;app.preferences.rulerUnits=Units.PIXELS;
    for(var i=0;i<app.documents.length;i++) {
        try{if(app.documents[i].fullName.fsName===SOURCE.fsName)sourceDoc=app.documents[i];}catch(ignore){}
    }
    if(sourceDoc){if(!sourceDoc.saved)throw Error('Source already open with unsaved changes; no state modified');}
    else{sourceDoc=app.open(SOURCE);sourceOwned=true;}
    app.activeDocument=sourceDoc;
    var items=[];inventory(sourceDoc,[],items);var lines=[];
    for(var j=0;j<items.length;j++)lines.push('path='+items[j].path.join('/')+' id='+items[j].id+' type='+items[j].type+' name='+items[j].name);
    write('SOURCE_LAYERS.txt',lines.join('\n'));log('SOURCE inventory written; '+items.length+' layers');
    var bRec=locate(items,3,'00 Base \u00b7 fotografia observada V105');
    var oRec=locate(items,304,'00 Base V104 original \u00b7 referencia oculta');
    var rRec=locate(items,303,'09 1/60 x2');
    var lRec=locate(items,239,'Luz 1');
    var cRec=locate(items,241,'Claridad y borrar neblina 1');
    d=sourceDoc.duplicate('V105_CONTEXT_ISOLATION_02_WORKING_COPY',false);
    var base=mapped(bRec),old=mapped(oRec),reference=mapped(rRec),luz=mapped(lRec),clarity=mapped(cRec);
    write('INPUT.txt','source='+SOURCE.fsName+'\nsourceBytes='+SOURCE.length+'\nsourceModified='+SOURCE.modified.toUTCString()+
      '\nwidth='+d.width+'\nheight='+d.height+'\nprofile='+d.colorProfileName+'\nbaseMode='+base.blendMode+'\noldMode='+old.blendMode+
      '\nbaseOpacity='+base.opacity+'\noldOpacity='+old.opacity+'\ninitialLuzVisible='+luz.visible+'\ninitialClarityVisible='+clarity.visible+
      '\ncrop='+BOX.join(',')+'\nmethod=source ID lookup; duplicate topology map; full-canvas merged duplicate; unscaled crop\n');
    log('BEGIN work only on temporary duplicate');reference.visible=false;
    var cases=[['both_off',false,false],['luz_off_clarity_on',false,true],['luz_on_clarity_off',true,false],['both_on',true,true]];
    for(var k=0;k<cases.length;k++) {
        var c=cases[k];luz.visible=c[1];clarity.visible=c[2];
        base.visible=false;old.visible=true;exportView(c[0]+'_old');
        base.visible=true;old.visible=false;exportView(c[0]+'_new');
    }
    log('COMPLETE: eight crops; no PSB saved; original source untouched');
} catch(e) {if(OUT.exists)log('ERROR '+e+' line '+e.line);throw e;}
finally {
    if(d)try{d.close(SaveOptions.DONOTSAVECHANGES);}catch(ignore){}
    if(sourceOwned && sourceDoc)try{sourceDoc.close(SaveOptions.DONOTSAVECHANGES);}catch(ignore){}
    if(prior)try{app.activeDocument=prior;}catch(ignore){}
    app.displayDialogs=dialogs;app.preferences.rulerUnits=units;
}
