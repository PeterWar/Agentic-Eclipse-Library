#target photoshop
var root='/Users/USUARI/Downloads/Eclipse 2026/output/v57_integracio_20260913/';
var d=null,t=null,result;var old=app.displayDialogs;
try{
 app.displayDialogs=DialogModes.NO;d=app.open(new File(root+'V57.psb'));
 if(d.artLayers.length!=35)throw Error('Expected 35 layers');
 var solar=d.artLayers.getByName('09 Compost de perles i protuberàncies · V56');if(solar.visible)throw Error('Expected V56 solar alternative hidden');
 var moon=d.artLayers.getByName('Earthshine V56 · detall i revelat de Pere');moon.visible=false;moon.visible=true;app.refresh();
 t=d.duplicate('V57 final native readback',true);
 var op=new TiffSaveOptions();op.imageCompression=TIFFEncoding.TIFFZIP;op.layers=false;op.embedColorProfile=true;
 var file=new File(root+'V57_final_readback.tif');if(file.exists)throw Error('EXISTS');
 t.saveAs(file,op,true,Extension.LOWERCASE);result='V57_FINAL_NATIVE_RENDERED_35_LAYERS';
}finally{if(t)t.close(SaveOptions.DONOTSAVECHANGES);if(d)d.close(SaveOptions.DONOTSAVECHANGES);app.displayDialogs=DialogModes.ERROR;}
result;
