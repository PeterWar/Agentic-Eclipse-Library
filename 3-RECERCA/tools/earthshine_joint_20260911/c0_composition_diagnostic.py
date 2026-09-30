"""Native Photoshop visibility-only diagnostic from saved V48, on an own copy.
No masks, pixels, CameraRaw parameters, originals or saved product are edited.
Four full-canvas TIFF comparisons separate alternative lunar sources and LROC.
"""
from joint_common import *
import shutil,subprocess
src=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors/Earthshine_V48.psb')
tmp=OUT/'C0_V48_disk_test.psb';assert not tmp.exists()
with src.open('rb') as f,tmp.open('xb') as g:shutil.copyfileobj(f,g,8*1024*1024)
with tmp.open('rb') as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
assert sha=='48715be427ebd5ea654eeea746e0a295201f9f0a354e4f5e37fbf40df47443a5'
paths={k:str(OUT/f'C0_{k}_RGBA.tif') for k in ['baseline','without_all_epochs','single_lunar_source','solar_background']}
assert not any(Path(p).exists() for p in paths.values())
js='''var prev=app.activeDocument;var ids=[];for(var i=0;i<app.documents.length;i++)ids.push(app.documents[i].id);var priorDialogs=app.displayDialogs;var doc=null;var result=[];
function layer(d,n){for(var i=0;i<d.layers.length;i++)if(d.layers[i].name===n)return d.layers[i];throw new Error("Missing layer "+n);}
function exportTiff(d,p){var o=new TiffSaveOptions();o.imageCompression=TIFFEncoding.TIFFZIP;o.layers=false;o.alphaChannels=true;o.embedColorProfile=true;o.saveTransparency=true;d.saveAs(new File(p),o,true,Extension.LOWERCASE);result.push(p);}
try{app.displayDialogs=DialogModes.NO;doc=app.open(new File(__SRC__));for(var i=0;i<ids.length;i++)if(doc.id===ids[i])throw new Error("Original returned instead of own copy");if(doc.width.as('px')!==10551||doc.height.as('px')!==7506||doc.layers.length!==25)throw new Error("Unexpected document");
var top=layer(doc,"V48 · fonts CFA completes · Camera Raw de Pere"),all=layer(doc,"V45 font G · dos trens · tots els epochs"),lroc=layer(doc,"Compara LROC");if(!top.visible||!all.visible||!lroc.visible)throw new Error("Disk state changed; inspect before editing");
exportTiff(doc,__BASE__);all.visible=false;exportTiff(doc,__NOALL__);lroc.visible=false;exportTiff(doc,__SINGLE__);top.visible=false;exportTiff(doc,__SOLAR__);
}finally{if(doc){var own=true;for(var i=0;i<ids.length;i++)if(doc.id===ids[i])own=false;if(own)doc.close(SaveOptions.DONOTSAVECHANGES);}app.displayDialogs=priorDialogs;app.activeDocument=prev;}result.join("\\n");'''
for tag,value in [('__SRC__',str(tmp)),('__BASE__',paths['baseline']),('__NOALL__',paths['without_all_epochs']),('__SINGLE__',paths['single_lunar_source']),('__SOLAR__',paths['solar_background'])]:js=js.replace(tag,json.dumps(value))
sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js,ensure_ascii=False)+'\nend timeout\nend tell'
res=subprocess.run(['osascript','-e',sc],capture_output=True,text=True)
if res.returncode:raise RuntimeError(res.stderr)
assert all(Path(p).exists() for p in paths.values())
save('C0_composition_diagnostic.json',dict(method=__doc__,saved_V48_sha256=sha,own_byte_exact_copy=str(tmp),exports=paths,native_result=res.stdout.strip(),source_of_truth='Saved V48; user clarified live inspection changes need not be adopted',product_changed=False,original_saved_or_closed=False))
print('NATIVE COMPOSITION EXPORTS',res.stdout,flush=True)
