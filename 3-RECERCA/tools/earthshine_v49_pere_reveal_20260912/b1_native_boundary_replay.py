"""Replay historical CR identically on original/auxiliary inputs; preserve prefs."""
from reveal_common import *
plan=json.loads((OUT/'B0_probe_plan.json').read_text());prefs_root=Path('/Users/USUARI/Library/Application Support/Adobe/CameraRaw/Defaults');prefnames=['Previous.xmp','Preferences.xmp','Clipboard.xmp'];prefdir=OUT/'CameraRaw_preferences_before';prefdir.mkdir();prefs=[]
for name in prefnames:
    p=prefs_root/name;b=p.read_bytes();(prefdir/name).write_bytes(b);prefs.append(dict(path=str(p),copy=str(prefdir/name),sha256=hashlib.sha256(b).hexdigest()))
save('B1_preferences_before.json',dict(files=prefs,meaning='These are session defaults, not proof of the exact sequence of CR filters baked into user V49. Previous.xmp currently says +0.40 exposure and zero blacks; user may have applied multiple filters. Preserve actual image and do not infer missing settings.'))
state=jsx('app.activeDocument.id+"|"+app.activeDocument.saved+"|"+app.documents.length+"|"+app.displayDialogs.toString();');results=[]
for key,path in [('baseline',plan['original_input']),('auxiliary',plan['modified_input'])]:
    dst=OUT/f'B1_{key}_camera_raw.psd';assert not dst.exists()
    js=r'''var original=app.activeDocument;var dialog=app.displayDialogs;var ids=[];for(var i=0;i<app.documents.length;i++)ids.push(app.documents[i].id);var d=null;try{app.displayDialogs=DialogModes.NO;d=app.open(new File(__SRC__));for(var i=0;i<ids.length;i++)if(d.id===ids[i])throw new Error("Expected own probe document");d.activeLayer=d.artLayers.getByName("V45 font G · dos trens · preferència temporal · vel present");var f=new File(__DESC__);f.encoding="BINARY";f.open("r");var b=f.read();f.close();var cr=new ActionDescriptor();cr.fromStream(b);var returned=executeAction(stringIDToTypeID("Adobe Camera Raw Filter"),cr,DialogModes.NO);var fo=new File(__RETURN__);fo.encoding="BINARY";fo.open("w");fo.write(returned.toStream());fo.close();var opt=new PhotoshopSaveOptions();opt.layers=true;opt.alphaChannels=true;opt.embedColorProfile=true;d.saveAs(new File(__DST__),opt,true,Extension.LOWERCASE);}finally{if(d){var own=true;for(var i=0;i<ids.length;i++)if(d.id===ids[i])own=false;if(own)d.close(SaveOptions.DONOTSAVECHANGES);}app.displayDialogs=dialog;app.activeDocument=original;}"HISTORICAL_REPLAY_DONE";'''
    for k,v in [('__SRC__',path),('__DESC__',plan['historical_descriptor']),('__RETURN__',OUT/f'B1_{key}_returned_descriptor.bin'),('__DST__',dst)]:js=js.replace(k,json.dumps(str(v),ensure_ascii=False))
    result=jsx(js);results.append(dict(key=key,input=path,output=str(dst),result=result));save('B1_native_replay.json',dict(method=__doc__,results=results,original_live_state=state));print(key,result,flush=True)
after=jsx('app.activeDocument.id+"|"+app.activeDocument.saved+"|"+app.documents.length+"|"+app.displayDialogs.toString();');assert after==state
prefchecks=[]
for r in prefs:
    current=sha(r['path']);prefchecks.append(dict(**r,after_sha256=current,unchanged=current==r['sha256']))
save('B1_preservation.json',dict(original_live_state_exact=after==state,original_live_state=after,preferences=prefchecks,all_preferences_unchanged=all(r['unchanged'] for r in prefchecks),source_sha256=sha(SOURCE)))
assert all(r['unchanged'] for r in prefchecks),'Preferences changed: inspect before any restoration or further action'
print('LIVE DOCUMENT AND CAMERA RAW PREFERENCES UNCHANGED',flush=True)
