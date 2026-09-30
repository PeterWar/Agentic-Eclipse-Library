var root='/Users/USUARI/Downloads/Eclipse 2026/output/v68_artefactes_20260914/',old=app.displayDialogs,d=null,t=null;
function log(s){var f=new File(root+'E3_final_open.log');f.encoding='UTF8';f.open('a');f.writeln(s);f.close();}
try{
 app.displayDialogs=DialogModes.NO;
 var finalFile=new File('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V68.psb');
 d=app.open(finalFile);if(d.layers.length!==31||!d.saved)throw Error('final file state');
 // Force recomposition on an owned duplicate so the deliverable remains open and saved.
 t=d.duplicate('V68_REOPEN_FORCED_QA',false);
 for(var i=0;i<t.layers.length;i++)if(t.layers[i].name.indexOf('Interiors 06')===0){t.layers[i].visible=false;t.layers[i].visible=true;}
 app.refresh();t.mergeVisibleLayers();
 var opt=new TiffSaveOptions();opt.imageCompression=TIFFEncoding.TIFFZIP;opt.layers=false;opt.alphaChannels=true;opt.transparency=true;opt.embedColorProfile=true;
 var f=new File(root+'E3_final_readback.tif');if(f.exists)throw new Error('no clobber');t.saveAs(f,opt,true,Extension.LOWERCASE);t.close(SaveOptions.DONOTSAVECHANGES);t=null;
 app.activeDocument=d;
 for(var i=0;i<app.documents.length;i++){var q=app.documents[i];log('DOC '+q.id+' name='+q.name+' saved='+q.saved+' layers='+q.layers.length);}
 log('FINAL_OPEN_COMPLETE');
}catch(e){log('ERROR '+e+' line '+e.line);throw e;}finally{if(t)t.close(SaveOptions.DONOTSAVECHANGES);app.displayDialogs=old;}
