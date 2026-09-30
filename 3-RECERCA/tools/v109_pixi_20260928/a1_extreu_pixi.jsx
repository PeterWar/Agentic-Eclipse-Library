#target photoshop
var ROOT=new File($.fileName).parent.parent.parent.parent;
var OUT=new Folder(ROOT.fsName+'/4-RESULTATS/v109_pixi_20260928/entrades');
var SRC=File(Folder('~').fsName+'/Downloads/V108-Pixi.tif');
var prior=app.activeDocument, dialogs=app.displayDialogs, units=app.preferences.rulerUnits, dup=null;
function log(s){var f=new File(OUT.fsName+'/EXTRACCIO.log'); f.open('a');f.writeln(new Date().toUTCString()+' '+s);f.close();}
function savePsb(doc,path){if(path.exists)throw Error('Existeix '+path);app.activeDocument=doc;app.refresh();var h=doc.histogram;
 var sd=new ActionDescriptor(),so=new ActionDescriptor();so.putBoolean(stringIDToTypeID('maximizeCompatibility'),true);
 sd.putObject(charIDToTypeID('As  '),stringIDToTypeID('largeDocumentFormat'),so);sd.putPath(charIDToTypeID('In  '),path);sd.putBoolean(charIDToTypeID('Cpy '),true);executeAction(charIDToTypeID('save'),sd,DialogModes.NO);}
try{
 app.displayDialogs=DialogModes.NO;app.preferences.rulerUnits=Units.PIXELS;
 if(prior.fullName.fsName!=SRC.fsName||!prior.saved)throw Error('Font activa inesperada o no desada');
 dup=prior.duplicate('CODEX_V109_Pixi_COPIA',false);log('DUPLICADA; original intacte');
 savePsb(dup,new File(OUT.fsName+'/pixi_capes.psb'));log('PSB capes amb marques desat');
 var found=0;for(var i=0;i<dup.layers.length;i++)if(dup.layers[i].name=='Artefactes V108'){dup.layers[i].visible=false;found++;}
 if(found!=1)throw Error('No hi ha exactament una capa Artefactes V108');
 var clean=dup.duplicate('CODEX_V109_Pixi_SENSE_MARQUES',true);
 try{var t=new TiffSaveOptions();t.layers=false;t.alphaChannels=false;t.embedColorProfile=true;t.imageCompression=TIFFEncoding.NONE;
  var f=new File(OUT.fsName+'/pixi_sense_marques.tif');if(f.exists)throw Error('Existeix '+f);clean.saveAs(f,t,true,Extension.LOWERCASE);
 }finally{clean.close(SaveOptions.DONOTSAVECHANGES);}
 log('COMPLET');
}catch(e){log('ERROR '+e+' linea '+e.line);throw e;}
finally{if(dup)dup.close(SaveOptions.DONOTSAVECHANGES);app.activeDocument=prior;app.displayDialogs=dialogs;app.preferences.rulerUnits=units;}
'PIXI_EXTRET';
