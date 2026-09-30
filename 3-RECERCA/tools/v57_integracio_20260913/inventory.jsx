var z=[];
z.push('ACTIVE='+ (app.documents.length?app.activeDocument.id:'NONE')+';DIALOGS='+app.displayDialogs.toString());
for(var i=0;i<app.documents.length;i++) {
 var d=app.documents[i], p=''; try {p=d.fullName.fsName;} catch(e){}
 z.push([d.id,d.name,p,d.saved,d.width.as('px'),d.height.as('px'),String(d.bitsPerChannel),d.layers.length].join('|'));
 for(var j=0;j<d.layers.length;j++) {
  var l=d.layers[j]; z.push(['L',d.id,j,l.id,l.name,l.visible,l.opacity,String(l.blendMode),l.bounds].join('|'));
 }
}
z.join('\n');
