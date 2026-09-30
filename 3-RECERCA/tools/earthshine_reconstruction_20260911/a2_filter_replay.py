"""Candidate CameraRaw recipe on a temporary, source-exact TIFF via native API."""
from photoshop_api import *
import numpy as np,tifffile,xml.etree.ElementTree as ET
before=OUT/'A2_before_filter.tif';after=OUT/'A2_filter_result.tif';assert not after.exists()
a=np.load(ROOT/'research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy');icc=(ROOT/'research/tools/v46_earthshine_20260911/cau/source_icc.bin').read_bytes()
tifffile.imwrite(before,a,photometric='rgb',compression='deflate',metadata=None,extratags=[(34675,'B',len(icc),icc,False)])
attrs=next(x for x in ET.fromstring((OUT/'settings_before/Previous.xmp').read_text()).iter() if x.tag.endswith('Description')).attrib
v={k.split('}')[-1]:x for k,x in attrs.items()}
mapping={'Exposure2012':('Ex12','Double'),'Contrast2012':('Cr12','Integer'),'Highlights2012':('Hi12','Integer'),'Shadows2012':('Sh12','Integer'),'Whites2012':('Wh12','Integer'),'Blacks2012':('Bk12','Integer'),'Texture':('CrTx','Integer'),'Clarity2012':('Cl12','Integer'),'Dehaze':('Dhze','Integer'),'Sharpness':('Shrp','Integer'),'LuminanceSmoothing':('LNR ','Integer')}
puts=''.join('cr.put'+typ+'(charIDToTypeID('+json.dumps(key)+'),'+str(float(v[name]) if typ=='Double' else int(v[name]))+');' for name,(key,typ) in mapping.items())
puts+='cr.putBoolean(charIDToTypeID("CtoG"),true);cr.putString(charIDToTypeID("CamP"),"Default Monochrome");cr.putString(charIDToTypeID("CMod"),"Filter");'
js='''var previous=app.activeDocument;var ids=[];for(var i=0;i<app.documents.length;i++)ids.push(app.documents[i].id);var temp=null;try{temp=app.open(new File(__BEFORE__));for(var j=0;j<ids.length;j++)if(temp.id===ids[j])throw new Error("Refuse original document");var f=new File(__STREAM__);f.encoding="BINARY";f.open("r");var data=f.read();f.close();var cr=new ActionDescriptor();cr.fromStream(data);__PUTS__var ret=executeAction(stringIDToTypeID("Adobe Camera Raw Filter"),cr,DialogModes.NO);var r=new File(__OUTSTREAM__);r.encoding="BINARY";r.open("w");r.write(ret.toStream());r.close();var opt=new TiffSaveOptions();opt.layers=false;opt.imageCompression=TIFFEncoding.TIFFZIP;opt.embedColorProfile=true;temp.saveAs(new File(__AFTER__),opt,true,Extension.LOWERCASE);}finally{if(temp){var ours=true;for(var j=0;j<ids.length;j++)if(temp.id===ids[j])ours=false;if(ours)temp.close(SaveOptions.DONOTSAVECHANGES);}app.activeDocument=previous;}"FILTER_REPLAY_DONE";'''
for key,value in [('__BEFORE__',before),('__STREAM__',OUT/'A1_camera_raw_descriptor.bin'),('__OUTSTREAM__',OUT/'A2_filter_descriptor.bin'),('__AFTER__',after)]:js=js.replace(key,json.dumps(str(value)))
js=js.replace('__PUTS__',puts);(OUT/'A2_filter_recipe.json').write_text(json.dumps(dict(xmp_values=v,descriptor_assignments=mapping),indent=2))
print(jsx(js),flush=True)
new=tifffile.imread(after);ref=np.load(OUT/'A0_live_layer21_rgb.npy');dif=abs(new.astype(int)-ref.astype(int));rep=dict(scope='BBox replay, candidate recipe only',max_difference_DN16=int(dif.max()),difference_percentiles=np.percentile(dif,[50,95,99]).tolist(),means=new.mean((0,1)).tolist(),target_means=ref.mean((0,1)).tolist())
(OUT/'A2_filter_comparison.json').write_text(json.dumps(rep,indent=2));print(json.dumps(rep),flush=True)
