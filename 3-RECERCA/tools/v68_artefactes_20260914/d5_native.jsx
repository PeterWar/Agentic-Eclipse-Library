var root='/Users/USUARI/Downloads/Eclipse 2026/output/v68_artefactes_20260914/',prior=app.activeDocument,old=app.displayDialogs,d=null,t=null;
function log(s){var f=new File(root+'D5_native.log');f.encoding='UTF8';f.open('a');f.writeln(s);f.close();}
function state(){for(var i=0;i<app.documents.length;i++){var q=app.documents[i];log('DOC '+q.id+' name='+q.name+' saved='+q.saved);}}
try{
 app.displayDialogs=DialogModes.NO;state();
 d=app.open(new File(root+'D4_V68_stage.psb'));if(d.layers.length!==31)throw Error('layer count');
 for(var i=0;i<d.layers.length;i++)if(d.layers[i].id===76){d.layers[i].visible=false;d.layers[i].visible=true;}
 app.refresh();log('RECOMPOSED '+d.id);
 t=d.duplicate('V68_FULL_NATIVE_QA',true);
 var opt=new TiffSaveOptions();opt.imageCompression=TIFFEncoding.TIFFZIP;opt.layers=false;opt.alphaChannels=true;opt.transparency=true;opt.embedColorProfile=true;
 var f=new File(root+'D5_full_native.tif');if(f.exists)throw new Error('no clobber TIFF');t.saveAs(f,opt,true,Extension.LOWERCASE);t.close(SaveOptions.DONOTSAVECHANGES);t=null;
 app.activeDocument=d;var dst=new File(root+'V68_native.psb');if(dst.exists)throw Error('no clobber PSB');
 var s=new ActionDescriptor(),o=new ActionDescriptor();o.putBoolean(stringIDToTypeID('maximizeCompatibility'),true);s.putObject(charIDToTypeID('As  '),stringIDToTypeID('largeDocumentFormat'),o);s.putPath(charIDToTypeID('In  '),dst);s.putBoolean(charIDToTypeID('Cpy '),false);s.putBoolean(charIDToTypeID('LwCs'),true);executeAction(charIDToTypeID('save'),s,DialogModes.NO);
 log('SAVED '+d.id+' '+d.name+' saved='+d.saved+' layers='+d.layers.length);d.close(SaveOptions.DONOTSAVECHANGES);d=null;state();log('COMPLETE');
}catch(e){log('ERROR '+e+' line '+e.line);throw e;}finally{if(t)t.close(SaveOptions.DONOTSAVECHANGES);if(d)d.close(SaveOptions.DONOTSAVECHANGES);app.activeDocument=prior;app.displayDialogs=old;}
