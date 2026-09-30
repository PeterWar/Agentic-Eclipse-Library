#target photoshop
var ROOT=new File($.fileName).parent.parent.parent.parent;
var f=new File(ROOT.fsName+'/1-PHOTOSHOP/V109.psb');
var d=app.open(f);app.activeDocument=d;app.bringToFront();
var report='V109_OBERTA '+d.width+' x '+d.height+' · '+d.layers.length+' capes · saved='+d.saved;
for(var i=0;i<app.documents.length;i++)report+='\nDOC '+app.documents[i].name+' saved='+app.documents[i].saved;
report;
