#target photoshop
var scriptFile=new File($.fileName),root=scriptFile.parent.parent.parent.parent;
var out=new Folder(root.fsName+'/4-RESULTATS/v85_regeneracio_20260922');
var prior=app.activeDocument,dialogs=app.displayDialogs,units=app.preferences.rulerUnits,d=null;
function log(s){var f=new File(out.fsName+'/NATIVE_DIAG_3.log');f.open('a');f.writeln(new Date().toUTCString()+' '+s);f.close();}
function setvis(id,v){for(var i=0;i<d.layers.length;i++)if(d.layers[i].id==id){d.layers[i].visible=v;return;}throw Error('Missing layer '+id);}
var saved=[];
function reset(){for(var i=0;i<d.layers.length;i++)d.layers[i].visible=saved[i];setvis(251,false);setvis(246,false);}
function filters(v){for(var id=41;id<=56;id++)setvis(id,v);setvis(250,v);}
function saveview(name){
 app.activeDocument=d;app.refresh();log('RENDER '+name);
 var x=d.duplicate('V85_diag_'+name,true);
 var t=new TiffSaveOptions();t.imageCompression=TIFFEncoding.TIFFLZW;t.embedColorProfile=true;t.layers=false;
 try{
  x.crop([UnitValue(4600,'px'),UnitValue(3000,'px'),UnitValue(6150,'px'),UnitValue(4550,'px')]);
  x.saveAs(new File(out.fsName+'/'+name+'_roi.tif'),t,true,Extension.LOWERCASE);
 }finally{x.close(SaveOptions.DONOTSAVECHANGES);}
 app.activeDocument=d;x=d.duplicate('V85_diag_full_'+name,true);
 try{
  x.resizeImage(UnitValue(1600,'px'),null,null,ResampleMethod.BICUBIC);
  x.saveAs(new File(out.fsName+'/'+name+'_full.tif'),t,true,Extension.LOWERCASE);
 }finally{x.close(SaveOptions.DONOTSAVECHANGES);}
 app.activeDocument=d;log('DONE '+name);
}
try{
 app.displayDialogs=DialogModes.NO;app.preferences.rulerUnits=Units.PIXELS;
 d=app.open(new File(out.fsName+'/V84_Pere_input.psb'));log('OPEN '+d.name);
 for(var i=0;i<d.layers.length;i++)saved.push(d.layers[i].visible);
 reset();for(var i=0;i<d.layers.length;i++)d.layers[i].visible=false;setvis(3,true);for(var id=240;id<=244;id++)setvis(id,true);saveview('H_base_no239');
 var candidates=['s75c90','s70c87'];
 for(var k=0;k<candidates.length;k++){
  reset();setvis(234,false);setvis(3,true);filters(false);setvis(225,false);
  var src=app.open(new File(out.fsName+'/base_'+candidates[k]+'.tif'));
  var lay=src.activeLayer.duplicate(d,ElementPlacement.PLACEATBEGINNING);src.close(SaveOptions.DONOTSAVECHANGES);app.activeDocument=d;
  var baseLayer=null;for(var i=0;i<d.layers.length;i++)if(d.layers[i].id==3)baseLayer=d.layers[i];
  lay.move(baseLayer,ElementPlacement.PLACEBEFORE);lay.name='Diagnostic base shoulder '+candidates[k];var bounds=lay.bounds;lay.translate(UnitValue(4600-bounds[0].as('px'),'px'),UnitValue(3000-bounds[1].as('px'),'px'));
  saveview('I_'+candidates[k]);lay.remove();
 }
 log('COMPLETE');
} catch(e){log('ERROR '+e+' line '+e.line);throw e;}
finally{if(d)try{d.close(SaveOptions.DONOTSAVECHANGES);}catch(e){}app.activeDocument=prior;app.displayDialogs=dialogs;app.preferences.rulerUnits=units;}
'V85_DIAG_DONE';
