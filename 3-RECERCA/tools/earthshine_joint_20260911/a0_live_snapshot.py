"""Archive the unsaved V48 state through an own duplicate; never save the original."""
from joint_common import *
import subprocess
dst=OUT/'V48_live_before_joint.psd';assert not dst.exists()
js='''var prev=app.activeDocument;var ids=[];var src=null;for(var i=0;i<app.documents.length;i++){ids.push(app.documents[i].id);if(app.documents[i].id===1297)src=app.documents[i];}if(!src||src.saved)throw new Error("Reinspect original V48 state");var copy=null;try{copy=src.duplicate("CODEX_ARCHIVE_V48_LIVE");var opt=new PhotoshopSaveOptions();opt.layers=true;opt.alphaChannels=true;opt.embedColorProfile=true;copy.saveAs(new File(__DST__),opt,true,Extension.LOWERCASE);}finally{if(copy){var own=true;for(var j=0;j<ids.length;j++)if(copy.id===ids[j])own=false;if(own)copy.close(SaveOptions.DONOTSAVECHANGES);}app.activeDocument=prev;}src.id+"|"+src.name+"|"+src.saved+"|"+src.layers.length;'''.replace('__DST__',json.dumps(str(dst)))
sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js)+'\nend timeout\nend tell'
state=subprocess.check_output(['osascript','-e',sc],text=True).strip();assert state=='1297|Earthshine_V48.psb|false|25',state
with dst.open('rb') as f:h=hashlib.file_digest(f,'sha256').hexdigest()
save('A0_live_snapshot.json',dict(path=str(dst),sha256=h,bytes=dst.stat().st_size,source_state_after=state,purpose='Preserve live unsaved V48 in own archival duplicate; not a new photographic product.'))
print('SNAPSHOT',h,state,flush=True)
