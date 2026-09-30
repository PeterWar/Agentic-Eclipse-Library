var root='/Users/USUARI/Downloads/Eclipse 2026/output/v57_integracio_20260913/';
var oldDialogs=app.displayDialogs;
var owned=[];
function log(s){var f=new File(root+'C0_native_render.log');f.open('a');f.writeln(s);f.close();}
function render(path,name,refresh) {
 log('OPEN '+name);
 var d=app.open(new File(path));owned.push(d);
 if(refresh){var l=d.layers[0],v=l.visible;l.visible=!v;l.visible=v;app.refresh();}
 log('LAYERS '+name+' '+d.artLayers.length);
 var t=d.duplicate('V57_QA_'+name,true);owned.push(t);
 var o=new TiffSaveOptions();o.imageCompression=TIFFEncoding.TIFFZIP;o.layers=false;o.alphaChannels=true;o.transparency=true;o.embedColorProfile=true;
 var file=new File(root+name+'_native.tif');if(file.exists)throw new Error('No-clobber '+file.fsName);
 t.saveAs(file,o,true,Extension.LOWERCASE);
 t.close(SaveOptions.DONOTSAVECHANGES);owned.pop();
 log('RENDERED '+name);
 d.close(SaveOptions.DONOTSAVECHANGES);owned.pop();
}
try {
 if(app.documents.length!==0)throw new Error('Unexpected open user document; inspect first');
 app.displayDialogs=DialogModes.NO;
 render('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V42.psb','V42',true);
 render(root+'V57_work.psb','V57',true);
 log('COMPLETE');
} finally {
 while(owned.length){try{owned.pop().close(SaveOptions.DONOTSAVECHANGES);}catch(e){}}
 app.displayDialogs=oldDialogs;
}
'RENDERED V42 AND V57';
