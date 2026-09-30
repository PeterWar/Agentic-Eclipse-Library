"""Diagnostic ablation of historical CR Texture/Clarity, all other fields fixed."""
from reveal_common import *
plan=json.loads((OUT/'B0_probe_plan.json').read_text())
prefs=json.loads((OUT/'B1_preferences_before.json').read_text())['files']
state=jsx('app.activeDocument.id+"|"+app.activeDocument.saved+"|"+app.documents.length+"|"+app.displayDialogs.toString();')
dst=OUT/'C0_no_local_detail_camera_raw.psd';assert not dst.exists()
js=r'''var original=app.activeDocument;var dialog=app.displayDialogs;var ids=[];for(var i=0;i<app.documents.length;i++)ids.push(app.documents[i].id);var d=null;try{app.displayDialogs=DialogModes.NO;d=app.open(new File(__SRC__));for(var i=0;i<ids.length;i++)if(d.id===ids[i])throw new Error("Expected own diagnostic document");d.activeLayer=d.artLayers.getByName("V45 font G · dos trens · preferència temporal · vel present");var f=new File(__DESC__);f.encoding="BINARY";f.open("r");var b=f.read();f.close();var cr=new ActionDescriptor();cr.fromStream(b);if(cr.getInteger(charIDToTypeID("CrTx"))!==100||cr.getInteger(charIDToTypeID("Cl12"))!==40)throw new Error("Unexpected historical controls");cr.putInteger(charIDToTypeID("CrTx"),0);cr.putInteger(charIDToTypeID("Cl12"),0);var fi=new File(__INPUT__);fi.encoding="BINARY";fi.open("w");fi.write(cr.toStream());fi.close();var returned=executeAction(stringIDToTypeID("Adobe Camera Raw Filter"),cr,DialogModes.NO);var fo=new File(__RETURN__);fo.encoding="BINARY";fo.open("w");fo.write(returned.toStream());fo.close();var opt=new PhotoshopSaveOptions();opt.layers=true;opt.alphaChannels=true;opt.embedColorProfile=true;d.saveAs(new File(__DST__),opt,true,Extension.LOWERCASE);}finally{if(d){var own=true;for(var i=0;i<ids.length;i++)if(d.id===ids[i])own=false;if(own)d.close(SaveOptions.DONOTSAVECHANGES);}app.displayDialogs=dialog;app.activeDocument=original;}"LOCAL_DETAIL_ABLATION_DONE";'''
for k,v in [('__SRC__',plan['original_input']),('__DESC__',plan['historical_descriptor']),('__INPUT__',OUT/'C0_input_descriptor.bin'),('__RETURN__',OUT/'C0_returned_descriptor.bin'),('__DST__',dst)]:js=js.replace(k,json.dumps(str(v),ensure_ascii=False))
result=jsx(js)
after=jsx('app.activeDocument.id+"|"+app.activeDocument.saved+"|"+app.documents.length+"|"+app.displayDialogs.toString();')
checks=[dict(path=p['path'],before=p['sha256'],after=sha(p['path'])) for p in prefs]
save('C0_ablation.json',dict(method=__doc__,changes={'CrTx':[100,0],'Cl12':[40,0]},result=result,original_live_before=state,original_live_after=after,preferences=checks,source_sha256=sha(SOURCE),scope='Diagnostic only. Removing lunar detail is not an accepted repair. No mask or source input was modified.'))
assert after==state and all(p['before']==p['after'] for p in checks)
print(result,'LIVE AND PREFERENCES UNCHANGED',flush=True)
