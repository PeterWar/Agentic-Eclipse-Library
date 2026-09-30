#target photoshop
var old=app.displayDialogs;var result;
try {
 app.displayDialogs=DialogModes.NO;
 var d=app.open(new File('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes Totals/V57.psb'));
 app.activeDocument=d;d.activeLayer=d.artLayers.getByName('Earthshine V56 · detall i revelat de Pere');
 try{app.runMenuItem(charIDToTypeID('FtOn'));}catch(e){}
 app.bringToFront();result='ACTIVE '+d.fullName.fsName+' | '+d.artLayers.length+' layers | saved='+d.saved+' | '+d.width+' x '+d.height;
}finally{app.displayDialogs=old;}
result;
