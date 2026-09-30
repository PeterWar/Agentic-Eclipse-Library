"""Independent decoded-channel and Photoshop-recomposition checks for comparison PSB.
This validates delivery and original preservation, not scientific all-limb recovery.
"""
from full_delta_common import *
from photoshop_full_api import jsx
import sys,subprocess,tifffile,gc
from PIL import Image
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from c5_fonts_psb import C,PSDImage,fingerprint
prefix=sys.argv[1];b=json.loads((OUT/(prefix+'_build.json')).read_text());target=Path(b['target']);name=b['new_layer'];tif=OUT/(prefix+'_Photoshop_RGBA.tif');assert not tif.exists()
s=PSDImage.open(target);assert s.version==2 and s.depth==16 and s.size==(10551,7506) and len(s)==26
for old,l in zip(b['source_layers'],list(s)[:25]):
 e=old.copy()
 if e['name'] in b['hidden_in_candidate']:e['visible']=False
 assert fingerprint(l)==e,l.name
new=list(s)[-1];rgb=np.load(OUT/'C3_candidate_rgb.npy');assert all(np.array_equal(C.channel(new,c),rgb[...,c]) for c in range(3))
old=next(l for l in s if l.name==b['old_source_layer'])
for cid in [-1,-2]:
 i=next(i for i,c in enumerate(new._record.channel_info) if int(c.id)==cid);j=next(i for i,c in enumerate(old._record.channel_info) if int(c.id)==cid);assert new._channels[i].data==old._channels[j].data
sha=hashlib.file_digest(target.open('rb'),'sha256').hexdigest();p=subprocess.run(['/opt/homebrew/bin/magick','identify','-ping',str(target)+'[0]'],capture_output=True,text=True,check=True);assert '10551x7506' in p.stdout and '16-bit' in p.stdout
save(prefix+'_verify.json',dict(PASS=True,target_sha256=sha,source_layers_exact=25,visibility_changes=b['hidden_in_candidate'],source_mask_and_alpha_bytes_exact=True,new_rgb_decoded_exact=True,reader2=p.stdout.strip()))
print('VERIFIED',prefix,flush=True);del s;gc.collect()
jsx('var p=new File('+json.dumps(str(target))+').fsName;for(var i=0;i<app.documents.length;i++){var f="";try{f=app.documents[i].fullName.fsName;}catch(e){}if(f===p)throw new Error("Candidate already open");}"SAFE";')
state=jsx('app.activeDocument.id+"|"+app.displayDialogs.toString();');original_id,dialog=state.split('|')
try:
 p=subprocess.run(['/bin/zsh',str(ROOT/'research/tools/capes_totals_v14/porta_photoshop.sh'),str(target)],capture_output=True,text=True,check=True);assert p.stdout.strip()=='OBRE 10551 px x 7506 px · 26 capes',p.stdout
 js='''var ids=[];for(var i=0;i<app.documents.length;i++)ids.push(app.documents[i].id);var d=null,t=null;try{d=app.open(new File(__SRC__));for(var i=0;i<ids.length;i++)if(d.id===ids[i])throw new Error("Expected new candidate");var l=d.artLayers.getByName(__NAME__);l.visible=false;l.visible=true;app.refresh();t=d.duplicate("V49_RECOMPOSITION_QA",true);var o=new TiffSaveOptions();o.imageCompression=TIFFEncoding.TIFFZIP;o.layers=false;o.alphaChannels=true;o.transparency=true;o.embedColorProfile=true;t.saveAs(new File(__DST__),o,true,Extension.LOWERCASE);}finally{if(t)t.close(SaveOptions.DONOTSAVECHANGES);if(d){var own=true;for(var j=0;j<ids.length;j++)if(d.id===ids[j])own=false;if(own)d.close(SaveOptions.DONOTSAVECHANGES);}}"RENDERED";'''
 for k,v in [('__SRC__',str(target)),('__NAME__',name),('__DST__',str(tif))]:js=js.replace(k,json.dumps(v))
 render=jsx(js)
finally:jsx('app.displayDialogs='+dialog+';for(var i=0;i<app.documents.length;i++)if(app.documents[i].id==='+original_id+')app.activeDocument=app.documents[i];"RESTORED";')
save(prefix+'_gate.json',dict(result=p.stdout.strip(),render=render,target_sha256=sha,readback=str(tif)));print('GATE',p.stdout.strip(),flush=True)
with tifffile.TiffFile(tif) as tf:a=tf.asarray();extras=list(map(int,tf.pages[0].extrasamples))
assert a.shape==(7506,10551,4) and a.dtype==np.uint16 and extras==[1]
s=PSDImage.open(target);merged=s._record.image_data.get_data(s._record.header);ref=[np.frombuffer(x,dtype='>u2').reshape(7506,10551) for x in merged];mx=0;ma=0;total=0;n=0
for y in range(0,7506,128):
 sl=slice(y,min(y+128,7506));valid=ref[3][sl]>0
 for c in range(3):
  rr=np.rint(ref[c][sl].astype(float)*ref[3][sl]/65535).astype(int);d=abs(a[sl,:,c].astype(int)-rr)[valid]
  if d.size:mx=max(mx,int(d.max()));total+=float(d.sum());n+=d.size
 ma=max(ma,int(abs(a[sl,:,3].astype(int)-ref[3][sl].astype(int)).max()))
roi=a[3077:4477,4677:6077,:3];expect=np.load(OUT/(prefix+'_expected_moon.npy'));dr=abs(roi.astype(int)-expect.astype(int));report=dict(PASS=mx<=6 and ma<=6,full_max_DN16=mx,alpha_max_DN16=ma,full_mean_DN16=total/n,moon_max_DN16=int(dr.max()),target_sha256=sha,readback_sha256=hashlib.file_digest(tif.open('rb'),'sha256').hexdigest())
save(prefix+'_readback.json',report);assert report['PASS'],report
Image.fromarray((roi>>8).astype(np.uint8)).save(OUT/'vistes'/(prefix+'_Photoshop_moon.png'))
print('READBACK',report,flush=True)
