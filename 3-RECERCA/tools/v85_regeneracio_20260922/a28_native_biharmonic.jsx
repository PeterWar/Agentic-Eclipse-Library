#target photoshop
var root=new File($.fileName).parent.parent.parent.parent;
var out=new Folder(root.fsName+'/4-RESULTATS/v85_regeneracio_20260922');
var prior=app.activeDocument,dialogs=app.displayDialogs,units=app.preferences.rulerUnits,d=null;
function log(s){var f=new File(out.fsName+'/NATIVE_BIHARMONIC_CANDIDATE.log');f.open('a');f.writeln(new Date().toUTCString()+' '+s);f.close();}
function layer(id){for(var i=0;i<d.layers.length;i++)if(d.layers[i].id==id)return d.layers[i];throw Error('Missing '+id);}
function view(name){
 app.activeDocument=d;app.refresh();var x=d.duplicate('V85_'+name,true),t=new TiffSaveOptions();t.imageCompression=TIFFEncoding.TIFFLZW;t.embedColorProfile=true;t.layers=false;
 try{x.crop([UnitValue(4600,'px'),UnitValue(3000,'px'),UnitValue(6150,'px'),UnitValue(4550,'px')]);x.saveAs(new File(out.fsName+'/'+name+'_roi.tif'),t,true,Extension.LOWERCASE);}finally{x.close(SaveOptions.DONOTSAVECHANGES);}
 app.activeDocument=d;x=d.duplicate('V85_full_'+name,true);
 try{x.resizeImage(UnitValue(1600,'px'),null,null,ResampleMethod.BICUBIC);x.saveAs(new File(out.fsName+'/'+name+'_full.tif'),t,true,Extension.LOWERCASE);}finally{x.close(SaveOptions.DONOTSAVECHANGES);}
 app.activeDocument=d;log('VIEW '+name);
}
try{
 app.displayDialogs=DialogModes.NO;app.preferences.rulerUnits=Units.PIXELS;
 d=app.open(new File(out.fsName+'/Biharmonic_candidate_stage.psb'));log('OPEN '+d.name);
 layer(3).visible=false;layer(3).visible=true;view('N_biharmonic_preplate');
 var beforeIds=[],src=null,owned=false,plate=null;
 for(var i=0;i<app.documents.length;i++)beforeIds.push(app.documents[i].id);
 try{
  src=app.open(new File(out.fsName+'/Moon_V84_preserved.tif'));owned=true;
  for(var i=0;i<beforeIds.length;i++)if(src.id===beforeIds[i])owned=false;
  if(!owned)throw Error('Source already open');
  if(src.mode!==DocumentMode.RGB||src.bitsPerChannel!==BitsPerChannelType.SIXTEEN||src.width.as('px')!==128||src.height.as('px')!==374)throw Error('Plate format');
  if(src.colorProfileName!==d.colorProfileName)throw Error('ICC mismatch');
  if(src.layers.length!==1||src.activeLayer.isBackgroundLayer||src.channels.length!==3)throw Error('TIFF alpha not imported as transparency');
  plate=src.activeLayer.duplicate(d,ElementPlacement.PLACEATBEGINNING);
 }finally{if(src&&owned)src.close(SaveOptions.DONOTSAVECHANGES);}
 app.activeDocument=d;plate.name='Aparença lunar V84 · compost natiu preservat';plate.blendMode=BlendMode.NORMAL;plate.opacity=100;plate.fillOpacity=100;plate.grouped=false;plate.visible=true;
 plate.move(layer(250),ElementPlacement.PLACEBEFORE);var b=plate.bounds;
 plate.translate(UnitValue(4908-b[0].as('px'),'px'),UnitValue(3493-b[1].as('px'),'px'));
 b=plate.bounds;var expected=[4908,3493,5036,3867];
 for(var j=0;j<4;j++)if(b[j].as('px')!==expected[j])throw Error('Plate bounds '+b);
 log('MOON_LAYER '+plate.id+' bounds '+b);view('P_biharmonic_preserved');
 var dst=new File(out.fsName+'/Biharmonic_candidate_native.psb');if(dst.exists)throw Error('No clobber');
 var sd=new ActionDescriptor(),so=new ActionDescriptor();so.putBoolean(stringIDToTypeID('maximizeCompatibility'),true);sd.putObject(charIDToTypeID('As  '),stringIDToTypeID('largeDocumentFormat'),so);sd.putPath(charIDToTypeID('In  '),dst);sd.putBoolean(charIDToTypeID('Cpy '),false);sd.putBoolean(charIDToTypeID('LwCs'),true);executeAction(charIDToTypeID('save'),sd,DialogModes.NO);log('NATIVE_SAVED');
 for(var id=41;id<=56;id++)layer(id).visible=false;layer(250).visible=false;view('P_biharmonic_unfiltered');log('COMPLETE');
}catch(e){log('ERROR '+e+' line '+e.line);throw e;}
finally{if(d)try{d.close(SaveOptions.DONOTSAVECHANGES);}catch(e){}app.activeDocument=prior;app.displayDialogs=dialogs;app.preferences.rulerUnits=units;}
'V85_NATIVE_CANDIDATE_DONE';
