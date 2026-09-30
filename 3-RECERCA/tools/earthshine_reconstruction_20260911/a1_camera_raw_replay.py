"""Replay candidate XMP via Adobe's documented native CameraRaw-open route.
Temporary TIFF only. Capture the returned ActionDescriptor for exact future
filter replay. Never save or close any user document.
"""
from photoshop_api import *
src=OUT/'A1_before_camera_raw_bbox.tif';dst=OUT/'A1_camera_raw_open_result.tif';stream=OUT/'A1_camera_raw_descriptor.bin'
assert src.exists() and not dst.exists()
js='''var prev=app.activeDocument;var ids=[];for(var i=0;i<app.documents.length;i++)ids.push(app.documents[i].id);var temp=null;var oldDialogs=app.displayDialogs;var msg="";try{app.displayDialogs=DialogModes.NO;var d=new ActionDescriptor();d.putPath(charIDToTypeID("null"),new File(__SRC__));d.putObject(charIDToTypeID("As  "),stringIDToTypeID("Adobe Camera Raw"),new ActionDescriptor());var ret=executeAction(charIDToTypeID("Opn "),d,DialogModes.NO);temp=app.activeDocument;for(var j=0;j<ids.length;j++)if(temp.id===ids[j])throw new Error("Refuse to alter existing user document");if(ret.hasKey(charIDToTypeID("As  "))){var cr=ret.getObjectValue(charIDToTypeID("As  "));var f=new File(__STREAM__);f.encoding="BINARY";f.open("w");f.write(cr.toStream());f.close();msg="DESCRIPTOR|"+cr.count;}var opt=new TiffSaveOptions();opt.layers=false;opt.alphaChannels=true;opt.transparency=true;opt.imageCompression=TIFFEncoding.TIFFZIP;opt.embedColorProfile=true;temp.saveAs(new File(__DST__),opt,true,Extension.LOWERCASE);msg+="|SIZE|"+temp.width+"|"+temp.height+"|DEPTH|"+temp.bitsPerChannel;}finally{if(temp){var ours=true;for(var j=0;j<ids.length;j++)if(temp.id===ids[j])ours=false;if(ours)temp.close(SaveOptions.DONOTSAVECHANGES);}app.displayDialogs=oldDialogs;app.activeDocument=prev;}msg;'''
for key,path in [('__SRC__',src),('__DST__',dst),('__STREAM__',stream)]:js=js.replace(key,json.dumps(str(path)))
result=jsx(js);(OUT/'A1_camera_raw_open_status.txt').write_text(result+'\n');print(result,flush=True)
