"""Non-clobber V45_Fonts package: append to Pere's marked PSB without recoding its
18 source layers. Verify compressed channel identity and new uint16 channels.
"""
from comu45 import *
from f7_fonts import SOURCES
claim=claim45
prepare=claim45
import hashlib, gc, subprocess, datetime, shutil, os
sys.path.insert(0,str(HERE45.parent/'v39_20260909'))
import c4_projecte_v39 as C
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, Resource
from PIL import Image
CI=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors')
SOURCE=CI/'Earthshine_V44.psb'
STAGING=HERE45/'staging';TARGET=STAGING/'Earthshine_V45_Fonts.psb';FINAL=CI/TARGET.name
NATURAL=SOURCES[-1][1]
LAYERS=[(label,key+'_display_u16.npy',key+'_mask_u16.npy',BlendMode.NORMAL,key=='combined_reference') for key,label in SOURCES]

def fingerprint(l):
    return dict(name=l.name,bbox=list(l.bbox),opacity=l.opacity,blend=str(l.blend_mode),visible=l.visible,
        channels=[dict(id=int(i.id),compression=int(c.compression),sha256=hashlib.sha256(c.data).hexdigest()) for i,c in zip(l._record.channel_info,l._channels)],
        mask=None if l._record.mask_data is None else dict(left=l._record.mask_data.left,top=l._record.mask_data.top,right=l._record.mask_data.right,bottom=l._record.mask_data.bottom,bg=l._record.mask_data.background_color))

def build():
    prepare();STAGING.mkdir(exist_ok=True);assert not TARGET.exists() and not FINAL.exists()
    expected='49fe61696845014160278d431969972ea59d1566b33ed0250bdcc4d9d8e33220'
    assert sha(SOURCE)==expected,'marked source changed during work'
    s=PSDImage.open(SOURCE);assert s.size==(W,H) and s.depth==16 and len(s)==18
    before=[fingerprint(l) for l in s]
    for l in s:
        if l.visible and l.name!='09 1/60 x2':l.visible=False
    box=(X0,Y0,X0+N,Y0+N)
    for name,src,mask,mode,vis in LAYERS:
        u=np.load(CAU45/src);m=None if mask is None else np.load(CAU45/mask)
        C.add_layer(s,u,name,None,m,box if m is not None else None,0,mode,255,vis,box)
    # Preserve all original image resources, including the untagged color state.
    # The obsolete thumbnail is removed so readers use the newly rendered composite.
    if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
    C.finalize_lr16(s)
    base=next(l for l in s if l.name=='09 1/60 x2');b=np.stack([C.channel(base,c) for c in range(3)],-1)
    comp=np.zeros((H,W,3),np.uint16);comp[base.top:base.bottom,base.left:base.right]=b;del b
    a=C.channel(base,-1);alpha=np.zeros((H,W),np.uint16)
    alpha[base.top:base.bottom,base.left:base.right]=65535 if a is None else a;del a
    u=np.load(CAU45/'combined_reference_display_u16.npy')
    m=np.load(CAU45/'combined_reference_mask_u16.npy').astype(float)/65535
    roi=comp[Y0:Y0+N,X0:X0+N]
    assert np.all(alpha[Y0:Y0+N,X0:X0+N]==65535),'09 alpha must be opaque in source ROI'
    roi[:]=np.rint(roi.astype(float)*(1-m[...,None])+u.astype(float)*m[...,None]).astype(np.uint16)
    np.save(CAU45/'expected_fonts_moon_u16.npy',roi)
    rgba=np.dstack([comp[::4,::4]>>8,alpha[::4,::4]>>8]).astype(np.uint8)
    Image.fromarray(rgba).save(VIS45/'C5_Earthshine_V45_Fonts_llenc_quart.png')
    Image.fromarray((roi>>8).astype(np.uint8)).save(VIS45/'C5_Earthshine_V45_Fonts_lluna_1a1.png')
    data=[np.ascontiguousarray(comp[...,c].astype('>u2')).tobytes() for c in range(3)]+[np.ascontiguousarray(alpha.astype('>u2')).tobytes()]
    merged=C.ImageData(compression=C.Compression.RAW);merged.set_data(data,s._record.header);s._record.image_data=merged;s._updated=False
    del comp,alpha,data;gc.collect()
    with open(TARGET,'xb') as f:s.save(f)
    savejson(REB45/'C5_build.json',dict(source=str(SOURCE),source_sha256=expected,source_layers=before,target=str(TARGET),new_layers=[x[0] for x in LAYERS],F7_sha256=sha(REB45/'F7_fonts.json'),scope='OBSERVED_SOURCE_ONLY; no all-limb detail recovery claim',original_channels='kept compressed byte for byte; no re-encoding',canvas=[W,H],depth=16))
    print('BUILT',TARGET,flush=True)

def verify():
    claim();b=json.loads((REB45/'C5_build.json').read_text());s=PSDImage.open(TARGET);assert len(s)==24 and s.size==(W,H) and s.depth==16
    rows=[]
    for old,l in zip(b['source_layers'],list(s)[:18]):
        now=fingerprint(l);expected=dict(old)
        if expected['visible'] and expected['name']!='09 1/60 x2':expected['visible']=False
        assert now==expected,l.name
        rows.append(dict(name=l.name,original_channel_bytes_exact=True))
    for l,(name,src,mask,mode,vis) in zip(list(s)[18:],LAYERS):
        u=np.load(CAU45/src);assert l.name==name and l.visible==vis and l.blend_mode==mode
        assert all(np.array_equal(C.channel(l,c),u[...,c]) for c in range(3)),name
        assert np.all(C.channel(l,-1)==65535)
        if mask:assert np.array_equal(C.channel(l,-2),np.load(CAU45/mask))
        rows.append(dict(name=name,decoded_uint16_exact=True))
    # Independent system reader, plus actual Photoshop in the next gate.
    r=subprocess.run(['/opt/homebrew/bin/magick','identify','-ping',str(TARGET)+'[0]'],capture_output=True,text=True,check=True)
    assert f'{W}x{H}' in r.stdout and '16-bit' in r.stdout,r.stdout
    savejson(REB45/'C5_verify.json',dict(PASS=True,sha256=sha(TARGET),bytes=TARGET.stat().st_size,layers=24,rows=rows,second_reader=r.stdout))
    print('VERIFIED',sha(TARGET),flush=True)

def jsx(js):
    sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js)+'\nend timeout\nend tell'
    p=subprocess.run(['osascript','-e',sc],capture_output=True,text=True)
    if p.returncode:raise RuntimeError('Photoshop AppleEvent: '+p.stderr.strip())
    return p.stdout.strip()

def gate():
    claim();v=json.loads((REB45/'C5_verify.json').read_text());assert v['PASS'] and sha(TARGET)==v['sha256']
    # Never let the gate close a candidate the user has already opened.
    jsx('var candidate=new File('+json.dumps(str(TARGET))+').fsName; for(var i=0;i<app.documents.length;i++){var p=""; try{p=app.documents[i].fullName.fsName;}catch(e){} if(p===candidate)throw new Error("V45_Fonts candidate already open: preserve user document");} "SAFE_NEW_CANDIDATE";')
    old=jsx('app.displayDialogs.toString();')
    try:
        p=subprocess.run(['/bin/zsh',str(ROOT/'research/tools/capes_totals_v14/porta_photoshop.sh'),str(TARGET)],check=True,capture_output=True,text=True)
        assert p.stdout.strip()==f'OBRE {W} px x {H} px · 24 capes',p.stdout
        tif=OUT45/'lliurables/Photoshop_V45_Fonts_readback_RGBA.tif'
        assert not tif.exists()
        js='app.displayDialogs=DialogModes.NO; var d=app.open(new File('+json.dumps(str(TARGET))+')); var t=null; var profile=""; try { profile=d.colorProfileType.toString(); if(d.colorProfileType!==ColorProfile.NONE)profile+="|"+d.colorProfileName; var l=d.artLayers.getByName('+json.dumps(NATURAL)+'); l.visible=false; l.visible=true; app.refresh(); t=d.duplicate("V45_Fonts_QA_TEMP",true); var o=new TiffSaveOptions(); o.imageCompression=TIFFEncoding.TIFFZIP; o.layers=false; o.alphaChannels=true; o.transparency=true; o.embedColorProfile=true; t.saveAs(new File('+json.dumps(str(tif))+'),o,true,Extension.LOWERCASE); } finally { if(t)t.close(SaveOptions.DONOTSAVECHANGES); d.close(SaveOptions.DONOTSAVECHANGES); } "RENDERED|"+profile;'
        rendered=jsx(js)
    finally:jsx('app.displayDialogs='+old+'; app.displayDialogs.toString();')
    savejson(REB45/'C5_photoshop_gate.json',dict(result=p.stdout.strip(),rendered=rendered,sha256=v['sha256'],readback=str(tif)))
    print(p.stdout.strip(),rendered,flush=True)

def readback():
    import tifffile
    g=json.loads((REB45/'C5_photoshop_gate.json').read_text());v=json.loads((REB45/'C5_verify.json').read_text())
    assert g['sha256']==v['sha256']==sha(TARGET)
    with tifffile.TiffFile(g['readback']) as tf:
        extras=[int(x) for x in tf.pages[0].extrasamples];a=tf.asarray()
    assert a.dtype==np.uint16 and a.shape==(H,W,4) and extras in ([1],[2])
    associated=extras==[1]
    roi=a[Y0:Y0+N,X0:X0+N,:3];expected=np.load(CAU45/'expected_fonts_moon_u16.npy');dif=abs(roi.astype(np.int32)-expected.astype(np.int32))
    rep=dict(source_sha256=g['sha256'],readback_sha256=sha(Path(g['readback'])),max_abs_DN16=int(dif.max()),mean_abs_DN16=float(dif.mean()),p999_abs_DN16=float(np.percentile(dif,99.9)),shape=list(a.shape),profile=g['rendered'],tiff_alpha='associated' if associated else 'unassociated')
    # Compare every visible canvas pixel against the independently assembled
    # merged channels, not only the lunar ROI. Ignore invisible RGB values.
    s=PSDImage.open(TARGET);merged=s._record.image_data.get_data(s._record.header)
    ref=[np.frombuffer(x,dtype='>u2').reshape(H,W) for x in merged]
    max_full=0;sum_full=0;count_full=0;max_alpha=0
    for y in range(0,H,128):
        sl=slice(y,min(H,y+128));valid=ref[3][sl]>0
        for c in range(3):
            reference=ref[c][sl].astype(np.int32)
            if associated:reference=np.rint(reference.astype(np.float64)*(ref[3][sl].astype(np.float64)/65535)).astype(np.int32)
            delta=np.abs(a[sl,:,c].astype(np.int32)-reference)[valid]
            if delta.size:max_full=max(max_full,int(delta.max()));sum_full+=int(delta.sum());count_full+=int(delta.size)
        if a.shape[-1]==4:max_alpha=max(max_alpha,int(np.abs(a[sl,:,3].astype(np.int32)-ref[3][sl].astype(np.int32)).max()))
    rep['full_visible_canvas']=dict(max_abs_DN16=max_full,mean_abs_DN16=sum_full/max(count_full,1),n_channel_values=count_full,alpha_max_abs_DN16=max_alpha,comparison='premultiplied stored RGB + alpha' if associated else 'unassociated RGB + alpha')
    rep['PASS']=rep['max_abs_DN16']<=6 and max_full<=6 and max_alpha<=6
    savejson(REB45/'C5_photoshop_readback.json',rep)
    assert rep['PASS'],rep
    Image.fromarray((roi>>8).astype(np.uint8)).save(VIS45/'C5_Photoshop_real_lluna_1a1.png')
    preview=a[::4,::4].astype(np.float32)
    if associated:preview[...,:3]*=65535/np.maximum(preview[...,3:4],1)
    Image.fromarray((np.clip(preview,0,65535).astype(np.uint16)>>8).astype(np.uint8)).save(VIS45/'C5_Photoshop_real_llenc_quart.png')
    print('PHOTOSHOP PIXELS',rep,flush=True)

def publish():
    claim();v=json.loads((REB45/'C5_verify.json').read_text());p=json.loads((REB45/'C5_photoshop_readback.json').read_text())
    g=json.loads((REB45/'C5_photoshop_gate.json').read_text())
    assert v['PASS'] and p['PASS'] and sha(TARGET)==v['sha256']==g['sha256']==p['source_sha256'] and not FINAL.exists()
    tmp=CI/'Earthshine_V45_Fonts_verificat.tmp.psb';assert not tmp.exists()
    with open(TARGET,'rb') as src,open(tmp,'xb') as dst:shutil.copyfileobj(src,dst,8<<20)
    assert sha(tmp)==v['sha256'];os.rename(tmp,FINAL)
    savejson(REB45/'C5_publish.json',dict(path=str(FINAL),sha256=v['sha256'],bytes=FINAL.stat().st_size,published_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    print('PUBLISHED',FINAL,flush=True)

if __name__=='__main__':{'build':build,'verify':verify,'gate':gate,'readback':readback,'publish':publish}[sys.argv[1]]()
