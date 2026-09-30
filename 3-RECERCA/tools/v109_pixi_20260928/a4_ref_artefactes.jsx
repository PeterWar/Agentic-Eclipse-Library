#target photoshop
var ROOT=new File($.fileName).parent.parent.parent.parent,O=new Folder(ROOT.fsName+'/4-RESULTATS/v109_pixi_20260928/entrades');
var prior=app.activeDocument,dialogs=app.displayDialogs,units=app.preferences.rulerUnits,d=null,x=null;
try{app.displayDialogs=DialogModes.NO;app.preferences.rulerUnits=Units.PIXELS;
 d=app.open(new File(O.fsName+'/V108_Artefactes_base.psb'));var n=0;for(var i=0;i<d.layers.length;i++)if(d.layers[i].id==307){d.layers[i].visible=false;n++;}if(n!=1)throw Error('Capa307 absent');
 app.refresh();var h=d.histogram;x=d.duplicate('CODEX_V109_ARTEFACTES_SENSE307',true);
 var t=new TiffSaveOptions();t.layers=false;t.alphaChannels=false;t.embedColorProfile=true;t.imageCompression=TIFFEncoding.NONE;
 var f=new File(O.fsName+'/Artefactes_sense307_natiu.tif');if(f.exists)throw Error('Existeix '+f);x.saveAs(f,t,true,Extension.LOWERCASE);
}finally{if(x)x.close(SaveOptions.DONOTSAVECHANGES);if(d)d.close(SaveOptions.DONOTSAVECHANGES);app.activeDocument=prior;app.displayDialogs=dialogs;app.preferences.rulerUnits=units;}
'ARTEFACTES_REFERENCIA_FETA';
