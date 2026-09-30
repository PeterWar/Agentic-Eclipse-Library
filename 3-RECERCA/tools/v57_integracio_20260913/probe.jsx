#target photoshop
var root='/Users/USUARI/Downloads/Eclipse 2026/output/v57_integracio_20260913/';
var old=app.displayDialogs, d=null,t=null;var result;
try {
 app.displayDialogs=DialogModes.NO;
 d=app.open(new File(root+'V57_work.psb'));
 d.artLayers.getByName('09 Compost de perles i protuberàncies · V56').visible=false;
 app.refresh();t=d.duplicate('V57 no solar QA',true);
 var op=new TiffSaveOptions();op.imageCompression=TIFFEncoding.TIFFZIP;op.layers=false;op.embedColorProfile=true;
 var file=new File(root+'V57_noSolar_native.tif');if(file.exists)throw Error('EXISTS');
 t.saveAs(file,op,true,Extension.LOWERCASE);result='RENDERED noSolar';
}finally{if(t)t.close(SaveOptions.DONOTSAVECHANGES);if(d)d.close(SaveOptions.DONOTSAVECHANGES);app.displayDialogs=old;}
result;
