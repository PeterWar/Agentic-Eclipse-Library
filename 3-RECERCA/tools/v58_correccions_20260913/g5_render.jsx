var root='/Users/USUARI/Downloads/Eclipse 2026/output/v58_correccions_20260913/';
var oldDialogs=app.displayDialogs;var owned=[];
function log(s){var f=new File(root+'G5_native.log');f.open('a');f.writeln(s);f.close();}
function exportVisible(d,name){
 var f=new File(root+name+'.tif');if(f.exists)throw new Error('No-clobber '+name);
 var t=d.duplicate('V58_QA_'+name,true);owned.push(t);var o=new TiffSaveOptions();o.imageCompression=TIFFEncoding.TIFFZIP;o.layers=false;o.alphaChannels=true;o.transparency=true;o.embedColorProfile=true;t.saveAs(f,o,true,Extension.LOWERCASE);t.close(SaveOptions.DONOTSAVECHANGES);owned.pop();log('EXPORTED '+name);
}
try{
 app.displayDialogs=DialogModes.NO;log('EXISTING_DOCUMENTS '+app.documents.length);
 var d=app.open(new File(root+'V58_overlap_work.psb'));owned.push(d);log('OPEN '+d.name+' '+d.layers.length+' layers');
 var n=d.layers.length;var vis=[];for(var i=0;i<n;i++)vis.push(d.layers[i].visible);
 d.layers[0].visible=false;d.layers[0].visible=true;app.refresh();exportVisible(d,'V58O_default_native');
 for(var i=0;i<n;i++)d.layers[i].visible=(i>=n-4);app.refresh();exportVisible(d,'V58O_solar_composite_native');
 for(var i=0;i<n;i++)d.layers[i].visible=(i===0||i>=n-2);app.refresh();exportVisible(d,'V58O_11_12_moon_native');
 for(var i=0;i<n;i++)d.layers[i].visible=vis[i];
 for(var fidx=13;fidx<=16;fidx++){
  for(var kk=11;kk<=26;kk++)d.layers[n-1-kk].visible=false;
  var fl=d.layers[n-1-fidx];var oo=fl.opacity;fl.opacity=100;fl.visible=true;app.refresh();exportVisible(d,'V58O_RHEF_'+fidx+'_native');fl.opacity=oo;
 }
 for(var i=0;i<n;i++)d.layers[i].visible=vis[i];d.close(SaveOptions.DONOTSAVECHANGES);owned.pop();log('COMPLETE');
}finally{while(owned.length){try{owned.pop().close(SaveOptions.DONOTSAVECHANGES);}catch(e){}}app.displayDialogs=oldDialogs;}
'V58_NATIVE_EXPORTED';
