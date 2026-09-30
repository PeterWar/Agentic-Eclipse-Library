var eclipse63TargetPath='/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V63.psb',root='/Users/USUARI/Downloads/Eclipse 2026/output/v63_encaix_contorn_20260913/',own=[],d=null;
function log(s){var f=new File(root+'E2_final_open.log');f.encoding='UTF8';f.open('a');f.writeln(s);f.close();}
function find(d,id){for(var i=0;i<d.layers.length;i++)if(d.layers[i].id===id)return d.layers[i];throw new Error('Missing layer '+id);}
try{
app.displayDialogs=DialogModes.NO;
for(var i=app.documents.length-1;i>=0;i--){var z=app.documents[i];if(z.name==='V63_pilot.psb'&&z.saved&&z.fullName.fsName===root+'V63_pilot.psb')z.close(SaveOptions.DONOTSAVECHANGES);}
d=app.open(new File(eclipse63TargetPath));
if(d.width.as('px')!==10551||d.height.as('px')!==7506||d.layers.length!==24)throw new Error('Final geometry');
var t=d.duplicate('V63_FINAL_QA_COPY',false);own.push(t);var so=find(t,76);so.visible=false;so.visible=true;app.refresh();
var f=t.duplicate('V63_FINAL_READBACK',true);own.push(f);var dest=new File(root+'V63_final_readback.tif');if(dest.exists)throw new Error('no-clobber');
var o=new TiffSaveOptions();o.imageCompression=TIFFEncoding.TIFFZIP;o.layers=false;o.alphaChannels=true;o.transparency=true;o.embedColorProfile=true;
f.saveAs(dest,o,true,Extension.LOWERCASE);f.close(SaveOptions.DONOTSAVECHANGES);own.pop();t.close(SaveOptions.DONOTSAVECHANGES);own.pop();
app.activeDocument=d;so=find(d,76);d.activeLayer=so;app.runMenuItem(stringIDToTypeID('actualPixels'));
if(!so.visible||find(d,78).visible||!d.saved)throw new Error('Final presentation');
var soIndex=-1,moonIndex=-1;for(var j=0;j<d.layers.length;j++){if(d.layers[j].id===76)soIndex=j;if(d.layers[j].id===30)moonIndex=j;}if(soIndex>=moonIndex)throw new Error('Foreground order');
log(d.name+' | saved='+d.saved+' | 24 top-level items | interiors visible='+so.visible+' | interiors above Moon=true | annotations hidden=true | profile='+d.colorProfileName);
log('FINAL_OPEN_COMPLETE');
}catch(e){log('ERROR '+e+' line '+e.line);throw e;}finally{while(own.length){try{own.pop().close(SaveOptions.DONOTSAVECHANGES);}catch(e){}}app.displayDialogs=DialogModes.ERROR;}
'V63_FINAL_OPEN';
