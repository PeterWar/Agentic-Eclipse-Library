"""Two diagnostic source renderings, no V50 promotion.
A: re-render physical complete Vixen stack (remove inherited pre-CR photographic
basis). B: same, with unqualified pupil solar subtraction. Both pass through
the same archived native Camera Raw descriptor, then a global appearance test.
"""
from common50 import *
import sys,subprocess,shutil,gc
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from c5_fonts_psb import C,PSDImage
NAME='V45 font G · dos trens · preferència temporal · vel present'
def jsx(js):
 sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js,ensure_ascii=False)+'\nend timeout\nend tell'
 v=subprocess.run(['osascript','-e',sc],capture_output=True,text=True);assert v.returncode==0,v.stderr;return v.stdout.strip()
tone=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F7_fonts.json').read_text())['tone'];G=np.load(ROOT/'output/earthshine_native_psf_20260911/B0_new_all.npz')['candidate'];D=np.load(OUT/'D0_pupil_all.npz');YY,XX=np.mgrid[:N,:N];r=np.hypot(XX-CX,YY-CY);deep=r<350;x=(XX-CX)/455;y=(YY-CY)/455;A=np.c_[np.ones(deep.sum()),x[deep],y[deep]];cf=np.linalg.lstsq(A,D['spill'][deep],rcond=None)[0];corr=D['corrected']+cf[0]+cf[1]*x+cf[2]*y
prefdir=Path.home()/'Library/Application Support/Adobe/CameraRaw/Defaults';snap=OUT/'E0_preferences_before';snap.mkdir(exist_ok=False);prefs=[]
for f in prefdir.glob('*.xmp'):
 shutil.copy2(f,snap/f.name);prefs.append(dict(path=str(f),sha256=sha(f)))
save('E0_plan.json',dict(method=__doc__,tone=tone,pupil_gauge_plane=cf.tolist(),preferences=prefs,originals='Unchanged; probes are own archived input copies. No current CR slider reconstruction claimed.'))
state=jsx('var a=[];for(var i=0;i<app.documents.length;i++)a.push(app.documents[i].id+"|"+app.documents[i].name+"|"+app.documents[i].saved);a.join("\\n");');save('E0_native_before.json',dict(state=state))
for tag,g in [('physical',G),('pupil',corr)]:
 display=tone['anchor']+tone['scale']*np.arcsinh((g-tone['mid'])/tone['soft']);rgb=np.repeat(np.rint(np.clip(display*65535,0,65535)).astype(np.uint16)[...,None],3,axis=2);np.save(OUT/f'E0_{tag}_preCR.npy',rgb)
 s=PSDImage.open(ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta/C0_pre_camera_raw_full.psd');l=next(l for l in s if l.name==NAME)
 for info,ch in zip(l._record.channel_info,l._channels):
  if int(info.id) in [0,1,2]:ch.set_data(np.ascontiguousarray(rgb[...,int(info.id)].astype('>u2')).tobytes(),N,N,16,1);info.length=len(ch.data)+2
 C.finalize_lr16(s);s._updated=False;src=OUT/f'E0_{tag}_input.psd';dst=OUT/f'E1_{tag}_CR.psd';assert not src.exists() and not dst.exists()
 with src.open('xb') as f:s.save(f)
 del s,l;gc.collect()
 js='''var orig=app.documents.length?app.activeDocument:null;var dialogs=app.displayDialogs;var ids=[];for(var i=0;i<app.documents.length;i++)ids.push(app.documents[i].id);var d=null;try{app.displayDialogs=DialogModes.NO;d=app.open(new File(__SRC__));for(var i=0;i<ids.length;i++)if(d.id===ids[i])throw new Error("Not own document");d.activeLayer=d.artLayers.getByName(__NAME__);var f=new File(__DESC__);f.encoding="BINARY";f.open("r");var b=f.read();f.close();var cr=new ActionDescriptor();cr.fromStream(b);executeAction(stringIDToTypeID("Adobe Camera Raw Filter"),cr,DialogModes.NO);var opt=new PhotoshopSaveOptions();opt.layers=true;opt.alphaChannels=true;opt.embedColorProfile=true;d.saveAs(new File(__DST__),opt,true,Extension.LOWERCASE);}finally{if(d){var own=true;for(var i=0;i<ids.length;i++)if(d.id===ids[i])own=false;if(own)d.close(SaveOptions.DONOTSAVECHANGES);}app.displayDialogs=dialogs;if(orig)app.activeDocument=orig;}"PROBE_DONE";'''
 for k,v in [('__SRC__',src),('__DST__',dst),('__NAME__',NAME),('__DESC__',ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta/C1_input_descriptor.bin')]:js=js.replace(k,json.dumps(str(v),ensure_ascii=False))
 print(tag,jsx(js),flush=True);s=PSDImage.open(dst);l=next(l for l in s if l.name==NAME);np.save(OUT/f'E1_{tag}_RGB16.npy',np.stack([C.channel(l,c) for c in range(3)],-1));del s,l;gc.collect()
assert all(sha(f['path'])==f['sha256'] for f in prefs)
after=jsx('var a=[];for(var i=0;i<app.documents.length;i++)a.push(app.documents[i].id+"|"+app.documents[i].name+"|"+app.documents[i].saved);a.join("\\n");');assert after==state;save('E1_native_after.json',dict(state=after,preferences_exact=True,probes_only=True));print('ALL PROBES DONE',flush=True)
