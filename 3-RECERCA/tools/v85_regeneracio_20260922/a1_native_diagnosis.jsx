#target photoshop
var scriptFile=new File($.fileName),root=scriptFile.parent.parent.parent.parent;
var out=new Folder(root.fsName+'/4-RESULTATS/v85_regeneracio_20260922');
var prior=app.activeDocument,dialogs=app.displayDialogs,units=app.preferences.rulerUnits,d=null;
function log(s){var f=new File(out.fsName+'/NATIVE_DIAG.log');f.open('a');f.writeln(new Date().toUTCString()+' '+s);f.close();}
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
 reset();saveview('A_current');
 reset();setvis(234,false);setvis(3,true);saveview('B_without_pix');
 reset();setvis(234,false);setvis(3,true);filters(false);saveview('C_unfiltered');
 reset();for(var i=0;i<d.layers.length;i++)d.layers[i].visible=false;setvis(234,true);saveview('D_pix_only');
 reset();for(var i=0;i<d.layers.length;i++)d.layers[i].visible=false;setvis(3,true);saveview('E_base_only');
 log('COMPLETE');
} catch(e){log('ERROR '+e+' line '+e.line);throw e;}
finally{if(d)try{d.close(SaveOptions.DONOTSAVECHANGES);}catch(e){}app.activeDocument=prior;app.displayDialogs=dialogs;app.preferences.rulerUnits=units;}
'V85_DIAG_DONE';
