#target photoshop
var root=new File($.fileName).parent.parent.parent.parent;
var out=new Folder(root.fsName+'/4-RESULTATS/v85_regeneracio_20260922');
var prior=app.activeDocument,dialogs=app.displayDialogs,units=app.preferences.rulerUnits,d=null;
function log(s){var f=new File(out.fsName+'/NATIVE_DISPLAYFIX.log');f.open('a');f.writeln(new Date().toUTCString()+' '+s);f.close();}
function layer(id){for(var i=0;i<d.layers.length;i++)if(d.layers[i].id==id)return d.layers[i];throw Error('Missing '+id);}
function view(name){
 app.activeDocument=d;app.refresh();var x=d.duplicate('V85_'+name,true),t=new TiffSaveOptions();t.imageCompression=TIFFEncoding.TIFFLZW;t.embedColorProfile=true;t.layers=false;
 try{x.crop([UnitValue(4600,'px'),UnitValue(3000,'px'),UnitValue(6150,'px'),UnitValue(4550,'px')]);x.saveAs(new File(out.fsName+'/'+name+'_roi.tif'),t,true,Extension.LOWERCASE);}finally{x.close(SaveOptions.DONOTSAVECHANGES);}
 app.activeDocument=d;x=d.duplicate('V85_full_'+name,true);
 try{x.resizeImage(UnitValue(1600,'px'),null,null,ResampleMethod.BICUBIC);x.saveAs(new File(out.fsName+'/'+name+'_full.tif'),t,true,Extension.LOWERCASE);}finally{x.close(SaveOptions.DONOTSAVECHANGES);}
 app.activeDocument=d;log('VIEW '+name);
}
try{
 app.displayDialogs=DialogModes.NO;app.preferences.rulerUnits=Units.PIXELS;d=app.open(new File(out.fsName+'/DisplayFix2_stage.psb'));log('OPEN '+d.name);
 layer(3).visible=false;layer(3).visible=true;view('J_displayfix');
 for(var id=41;id<=56;id++)layer(id).visible=false;layer(250).visible=false;view('J_displayfix_unfiltered');log('COMPLETE');
}catch(e){log('ERROR '+e+' line '+e.line);throw e;}
finally{if(d)try{d.close(SaveOptions.DONOTSAVECHANGES);}catch(e){}app.activeDocument=prior;app.displayDialogs=dialogs;app.preferences.rulerUnits=units;}
'V85_NATIVE_DISPLAYFIX_DONE';
