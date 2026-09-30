from photoshop_api import *
out=OUT/'V46_Detall_live_source.psd';assert not out.exists()
source='/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V46_Detall.psb'
js='''var wanted=new File(__SOURCE__).fsName;var d=null;for(var i=0;i<app.documents.length;i++){var p="";try{p=app.documents[i].fullName.fsName;}catch(e){}if(p===wanted)d=app.documents[i];}if(!d)throw new Error("Expected current V46_Detall not open");var originalActive=app.activeDocument;var before=d.saved;var originalID=d.id;var tmp=null;try{tmp=d.duplicate("EARTHSHINE_RECONSTRUCTION_SOURCE_SNAPSHOT",false);var opt=new PhotoshopSaveOptions();opt.layers=true;opt.alphaChannels=true;opt.embedColorProfile=true;tmp.saveAs(new File(__TARGET__),opt,true,Extension.LOWERCASE);}finally{if(tmp)tmp.close(SaveOptions.DONOTSAVECHANGES);app.activeDocument=originalActive;}"SOURCE_ID|"+originalID+"|SAVED_BEFORE|"+before+"|AFTER|"+d.saved;'''
js=js.replace('__SOURCE__',json.dumps(source)).replace('__TARGET__',json.dumps(str(out)))
# Replace only placeholders; document names deliberately use no source token.
print(jsx(js),flush=True)
