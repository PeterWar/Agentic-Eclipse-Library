#target photoshop
// Opens only our new stage; preserves every pre-existing document and preference.
var STAGE = new File('/private/tmp/v105_root_pilots_20260926/P01/V105_P01_stage.psb'), DST = new File('/private/tmp/v105_root_pilots_20260926/P01/native/V105_P01.psb'), VIS = new Folder('/private/tmp/v105_root_pilots_20260926/P01/native');
if (!VIS.exists) VIS.create();
var prior = app.documents.length ? app.activeDocument : null;
var dialogs = app.displayDialogs, units = app.preferences.rulerUnits, d = null;
function log(s) { var f = new File(VIS.fsName + '/NATIVE.log'); f.open('a'); f.writeln(new Date().toUTCString() + ' ' + s); f.close(); }
function tiff() { var t = new TiffSaveOptions(); t.imageCompression = TIFFEncoding.TIFFLZW; t.embedColorProfile = true; t.layers = false; t.alphaChannels = false; return t; }
function vista(name, box, width) {
    app.activeDocument = d; var x = d.duplicate('V105_QA_' + name, true);
    try {
        if (box) x.crop([UnitValue(box[0],'px'),UnitValue(box[1],'px'),UnitValue(box[2],'px'),UnitValue(box[3],'px')]);
        if (width) x.resizeImage(UnitValue(width,'px'),null,null,ResampleMethod.BICUBIC);
        x.saveAs(new File(VIS.fsName + '/' + name + '.tif'),tiff(),true,Extension.LOWERCASE);
    } finally { x.close(SaveOptions.DONOTSAVECHANGES); }
    app.activeDocument=d; log('VISTA ' + name);
}
try {
    app.displayDialogs=DialogModes.NO; app.preferences.rulerUnits=Units.PIXELS;
    if (DST.exists) throw Error('No overwrite: '+DST.fsName);
    d=app.open(STAGE); log('STAGE OBRE '+d.width+' x '+d.height+' capes '+d.layers.length);
    var base=d.artLayers.getByName('00 Base · fotografia observada V105');
    var old=d.artLayers.getByName('00 Base V104 original · referencia oculta');
    base.visible=false; old.visible=true;
    vista('baseline_lluna',[4600,3000,6150,4550],null);
    vista('baseline_llenc',null,2400);
    base.visible=true;old.visible=false;app.refresh();var hist=d.histogram;
    log('RECOMPOST histograma '+hist.length);
    var sd=new ActionDescriptor(),so=new ActionDescriptor();so.putBoolean(stringIDToTypeID('maximizeCompatibility'),true);
    sd.putObject(charIDToTypeID('As  '),stringIDToTypeID('largeDocumentFormat'),so);sd.putPath(charIDToTypeID('In  '),DST);sd.putBoolean(charIDToTypeID('Cpy '),true);
    executeAction(charIDToTypeID('save'),sd,DialogModes.NO);log('DESAT_NATIU '+DST.fsName);
    vista('V105_lluna',[4600,3000,6150,4550],null);
    vista('V105_llenc_sencer',null,2400);
    vista('V105_enquadrament_final',[1325,1142,9348,6263],2400);
    d.close(SaveOptions.DONOTSAVECHANGES);d=null;
    d=app.open(DST);log('PORTA OBRE '+d.width+' x '+d.height+' · '+d.artLayers.length+' capes');
    vista('V105_reobert_lluna',[4600,3000,6150,4550],null);log('COMPLET');
} catch(e) {log('ERROR '+e+' line '+e.line);throw e;}
finally {if(d)try{d.close(SaveOptions.DONOTSAVECHANGES);}catch(e){}if(prior)try{app.activeDocument=prior;}catch(e){}app.displayDialogs=dialogs;app.preferences.rulerUnits=units;}
