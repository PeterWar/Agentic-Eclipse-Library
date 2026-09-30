var root='/Users/USUARI/Downloads/Eclipse 2026/output/v62_prominencies_20260913/';
var old=app.displayDialogs,own=[];
function log(s){var f=new File(root+'A1_native.log');f.encoding='UTF8';f.open('a');f.writeln(s);f.close();}
function layer(d,id){for(var j=0;j<d.layers.length;j++)if(d.layers[j].id==id)return d.layers[j];throw new Error('layer '+id);}
function exp(d,n,crop){var f=new File(root+n+'.tif');if(f.exists)throw new Error('no-clobber '+n);var t=d.duplicate('V62_QA_'+n,true);own.push(t);if(crop)t.crop([UnitValue(4377,'px'),UnitValue(2777,'px'),UnitValue(6377,'px'),UnitValue(4777,'px')]);var o=new TiffSaveOptions();o.imageCompression=TIFFEncoding.TIFFZIP;o.layers=false;o.alphaChannels=true;o.transparency=true;o.embedColorProfile=true;t.saveAs(f,o,true,Extension.LOWERCASE);t.close(SaveOptions.DONOTSAVECHANGES);own.pop();log('EXPORTED '+n);}
function maskEnabled(l,on){app.activeDocument.activeLayer=l;var d=new ActionDescriptor(),r=new ActionReference();r.putIdentifier(stringIDToTypeID('layer'),l.id);d.putReference(charIDToTypeID('null'),r);var x=new ActionDescriptor();x.putBoolean(stringIDToTypeID('userMaskEnabled'),on);d.putObject(charIDToTypeID('T   '),charIDToTypeID('Lyr '),x);executeAction(charIDToTypeID('setd'),d,DialogModes.NO);}
try{app.displayDialogs=DialogModes.NO;var d=app.open(new File(root+'V61_Pere_input.psb'));own.push(d);if(d.layers.length!=24)throw new Error('24 layers expected');exp(d,'V61_marked',false);layer(d,78).visible=false;exp(d,'V61_clean',true);var ids=[],vis=[];for(var i=0;i<d.layers.length;i++){ids.push(d.layers[i].id);vis.push(d.layers[i].visible);}
layer(d,76).visible=false;exp(d,'V61_no_interiors',true);
for(var i=0;i<d.layers.length;i++)if(/^P0|^ACHF/.test(d.layers[i].name))d.layers[i].visible=false;exp(d,'V61_base_moon',true);
for(var i=0;i<d.layers.length;i++)d.layers[i].visible=false;layer(d,76).visible=true;exp(d,'V61_interiors_masked',true);maskEnabled(layer(d,76),false);exp(d,'V61_interiors_full',true);
for(var i=0;i<d.layers.length;i++)d.layers[i].visible=false;layer(d,3).visible=true;exp(d,'V61_base',true);
for(var i=0;i<d.layers.length;i++)d.layers[i].visible=false;layer(d,30).visible=true;exp(d,'V61_moon',true);
d.close(SaveOptions.DONOTSAVECHANGES);own.pop();log('COMPLETE');}catch(e){log('ERROR '+e+' line '+e.line);throw e;}finally{while(own.length){try{own.pop().close(SaveOptions.DONOTSAVECHANGES);}catch(e){}}app.displayDialogs=old;}
