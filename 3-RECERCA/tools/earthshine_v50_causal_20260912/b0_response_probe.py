"""Falsify a photographic response-transfer explanation, not qualify D0 optics.
Keep V49 pre-CR and residual detail; transfer fixed D0 solar subtraction in a
single global response fitted on alternating sectors. Exact identity control.
"""
from common50 import *
import sys,subprocess,shutil,gc
from scipy.interpolate import PchipInterpolator
from scipy.optimize import isotonic_regression
from PIL import Image
sys.path.insert(0,str(ROOT/'research/tools/v45_earthshine_20260910'))
from c5_fonts_psb import C,PSDImage
NAME='V45 font G · dos trens · preferència temporal · vel present'
def jsx(js):
 sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js,ensure_ascii=False)+'\nend timeout\nend tell'
 v=subprocess.run(['osascript','-e',sc],capture_output=True,text=True);assert v.returncode==0,v.stderr;return v.stdout.strip()
tone=json.loads((ROOT/'output/v45_earthshine_20260910/4-rebuts/F7_fonts.json').read_text())['tone']
def display(g):return 65535*(tone['anchor']+tone['scale']*np.arcsinh((g-tone['mid'])/tone['soft']))
y,x=np.mgrid[:N,:N];r=np.hypot(x-CX,y-CY);sec=(np.arctan2(y-CY,x-CX)%(2*np.pi)*24/(2*np.pi)).astype(int)
U49=np.load(ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta/C0_pre_camera_raw_rgb.npy').astype(float)
G=np.load(ROOT/'output/earthshine_native_psf_20260911/B0_new_all.npz')['candidate']
G_old=np.load(ROOT/'output/earthshine_detail_20260911/B1_full_native_ensemble.npz')['candidate']
live=np.load(ROOT/'research/tools/v46_earthshine_20260911/cau/live_lunar_rgb_u16.npy').mean(-1)
mask=np.load(V49/'A0_inherited_mask_roi.npy').astype(float)/65535;valid=(r<470)&(mask>.1);train=valid&(sec%2==0);test=valid&(sec%2==1)
xv=np.load(ROOT/'research/tools/v45_earthshine_20260910/cau/combined_reference_display_u16.npy').mean(-1);knots=[]
for lo in np.arange(0,65535,250):
 w=train&(xv>=lo)&(xv<lo+250)
 if w.sum()>50:knots.append([float(np.mean(xv[w])),float(np.median(live[w])),int(w.sum())])
k=np.array(knots);ys=isotonic_regression(k[:,1],weights=k[:,2]).x;F=PchipInterpolator(np.r_[0,k[:,0],65535],np.r_[0,ys,65535],extrapolate=False)
def mapped(g):return F(np.clip(display(g),0,65535))
assert np.array_equal(U49+(mapped(G)-mapped(G))[...,None],U49)
D=np.load(PRIOR/'D0_pupil_all.npz');deep=r<350;xx=(x-CX)/455;yy=(y-CY)/455;A=np.c_[np.ones(deep.sum()),xx[deep],yy[deep]];cf=np.linalg.lstsq(A,D['spill'][deep],rcond=None)[0];corr=D['corrected']+cf[0]+cf[1]*xx+cf[2]*yy
trial=U49+(mapped(corr)-mapped(G))[...,None]
rep=dict(method=__doc__,knots=knots,isotonic_output=ys.tolist(),reserved_global_map_error_DN16=np.percentile(abs(F(np.clip(xv[test],0,65535))-live[test]),[50,95,99]).tolist(),identity_control_exact=True,gauge_plane=cf.tolist(),preCR_clips=int(((trial<0)|(trial>65535)).any(-1).sum()),qualification='D0 remains rejected; this probes response transfer only')
rep['visible_clips']=int((((trial<0)|(trial>65535)).any(-1)&(mask>.1)).sum());save('B0_response.json',rep)
if rep['visible_clips']:
 print('REJECTED before native Photoshop; visible out of range',rep['visible_clips'],flush=True);sys.exit(0)
trial=np.rint(np.clip(trial,0,65535)).astype(np.uint16);np.save(OUT/'B0_probe_preCR.npy',trial);save('B0_response.json',rep)
prefs=[];prefdir=Path.home()/'Library/Application Support/Adobe/CameraRaw/Defaults';snap=OUT/'B0_preferences_before';snap.mkdir()
for f in prefdir.glob('*.xmp'):shutil.copy2(f,snap/f.name);prefs.append(dict(path=str(f),sha256=sha(f)))
state=jsx('var a=[];for(var i=0;i<app.documents.length;i++)a.push(app.documents[i].id+"|"+app.documents[i].name+"|"+app.documents[i].saved);a.join("\\n");');save('B0_native_before.json',dict(state=state,preferences=prefs))
s=PSDImage.open(ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta/C0_pre_camera_raw_full.psd');l=next(l for l in s if l.name==NAME)
for info,ch in zip(l._record.channel_info,l._channels):
 if int(info.id) in [0,1,2]:ch.set_data(np.ascontiguousarray(trial[...,int(info.id)].astype('>u2')).tobytes(),N,N,16,1);info.length=len(ch.data)+2
C.finalize_lr16(s);s._updated=False;src=OUT/'B0_probe_input.psd';dst=OUT/'B1_probe_CR.psd'
with src.open('xb') as f:s.save(f)
del s,l;gc.collect()
js='''var orig=app.documents.length?app.activeDocument:null;var dialogs=app.displayDialogs;var ids=[];for(var i=0;i<app.documents.length;i++)ids.push(app.documents[i].id);var d=null;try{app.displayDialogs=DialogModes.NO;d=app.open(new File(__SRC__));for(var i=0;i<ids.length;i++)if(d.id===ids[i])throw new Error("Not own document");d.activeLayer=d.artLayers.getByName(__NAME__);var f=new File(__DESC__);f.encoding="BINARY";f.open("r");var b=f.read();f.close();var cr=new ActionDescriptor();cr.fromStream(b);executeAction(stringIDToTypeID("Adobe Camera Raw Filter"),cr,DialogModes.NO);var opt=new PhotoshopSaveOptions();opt.layers=true;opt.alphaChannels=true;opt.embedColorProfile=true;d.saveAs(new File(__DST__),opt,true,Extension.LOWERCASE);}finally{if(d){var own=true;for(var i=0;i<ids.length;i++)if(d.id===ids[i])own=false;if(own)d.close(SaveOptions.DONOTSAVECHANGES);}app.displayDialogs=dialogs;if(orig)app.activeDocument=orig;}"PROBE_DONE";'''
for key,val in [('__SRC__',src),('__DST__',dst),('__NAME__',NAME),('__DESC__',ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta/C1_input_descriptor.bin')]:js=js.replace(key,json.dumps(str(val),ensure_ascii=False))
print('NATIVE',jsx(js),flush=True)
s=PSDImage.open(dst);l=next(l for l in s if l.name==NAME);probe=np.stack([C.channel(l,c) for c in range(3)],-1);np.save(OUT/'B1_probe_RGB16.npy',probe);del s,l;gc.collect()
s=PSDImage.open(ROOT/'output/earthshine_native_psf_20260911/full_sampler_delta/C1_camera_raw.psd');l=next(l for l in s if l.name==NAME);baseline=np.stack([C.channel(l,c) for c in range(3)],-1).mean(-1);del s,l;gc.collect()
z=json.loads((PRIOR/'E2_appearance.json').read_text());kn=np.array(z['knots']);E=PchipInterpolator(np.r_[0,kn[:,0],65535],np.r_[0,z['isotonic_output'],65535]);pere=np.load(V49/'A0_Pere_moon_RGB16.npy').astype(float)
res=pere+(E(probe.mean(-1))-E(baseline))[...,None];rep['output_clips']=int(((res<0)|(res>65535)).any(-1).sum());res=np.rint(np.clip(res,0,65535)).astype(np.uint16);np.save(OUT/'B2_response_probe_RGB16.npy',res)
bg=np.load(V49/'A2_sense_font_lunar_RGB16.npy').astype(float);comp=np.rint(bg*(1-mask[...,None])+res*mask[...,None]).astype(np.uint16);np.save(OUT/'B2_response_probe_composite.npy',comp);Image.fromarray((comp>>8).astype('uint8')).save(OUT/'B2_response_probe.png')
rep['regions']={f'{lo}_{hi}':dict(delta=np.percentile((res.astype(float)-pere)[(r>=lo)&(r<hi)],[5,50,95]).tolist()) for lo,hi in [(0,350),(415,435),(435,449),(449,454),(454,460)]}
after=jsx('var a=[];for(var i=0;i<app.documents.length;i++)a.push(app.documents[i].id+"|"+app.documents[i].name+"|"+app.documents[i].saved);a.join("\\n");');assert after==state;assert all(sha(f['path'])==f['sha256'] for f in prefs)
rep.update(preferences_exact=True,native_documents_preserved=True);save('B2_response_result.json',rep);print(json.dumps(rep['regions']),flush=True)
