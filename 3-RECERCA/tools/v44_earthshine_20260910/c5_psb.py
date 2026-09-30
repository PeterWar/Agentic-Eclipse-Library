"""Non-clobber V44 package: append to Pere's marked PSB without recoding its
15 source layers. Verify compressed channel identity and new uint16 channels.
"""
from comu44 import *
import hashlib, gc, subprocess, datetime, shutil, os
sys.path.insert(0,str(HERE44.parent/'v39_20260909'))
import c4_projecte_v39 as C
from psd_tools import PSDImage
from psd_tools.constants import BlendMode, Resource
from PIL import Image
CI=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors')
SOURCE=CI/'Earthshine_V43_detall.psb'
STAGING=HERE44/'staging';TARGET=STAGING/'Earthshine_V44.psb';FINAL=CI/TARGET.name
NATURAL='Earthshine V44 · natural 12 % · contorn Vixen · aportació'
VARIANT='Earthshine V44 · relleu 24 % · alternativa (activar sola)'
HDR='Earthshine V44 · HDR mesurat · rellotge comú (diagnòstic)'
LAYERS=[(HDR,'earthshine_HDR_u16.npy','HDR_mask_u16.npy',BlendMode.NORMAL,False),
        (VARIANT,'earthshine_relleu24_delta_u16.npy',None,BlendMode.LINEAR_DODGE,False),
        (NATURAL,'earthshine_natural_delta_u16.npy',None,BlendMode.LINEAR_DODGE,True)]

def fingerprint(l):
    return dict(name=l.name,bbox=list(l.bbox),opacity=l.opacity,blend=str(l.blend_mode),visible=l.visible,
        channels=[dict(id=int(i.id),compression=int(c.compression),sha256=hashlib.sha256(c.data).hexdigest()) for i,c in zip(l._record.channel_info,l._channels)],
        mask=None if l._record.mask_data is None else dict(left=l._record.mask_data.left,top=l._record.mask_data.top,right=l._record.mask_data.right,bottom=l._record.mask_data.bottom,bg=l._record.mask_data.background_color))

def build():
    prepare();STAGING.mkdir(exist_ok=True);assert not TARGET.exists() and not FINAL.exists()
    expected=json.loads((REB44/'A0_inventari_psb.json').read_text())['Earthshine_V43_detall.psb']['sha256']
    assert sha(SOURCE)==expected,'marked source changed during work'
    s=PSDImage.open(SOURCE);assert s.size==(W,H) and s.depth==16 and len(s)==15
    before=[fingerprint(l) for l in s]
    for l in s:
        if l.visible and l.name!='09 1/60 x2':l.visible=False
    box=(X0,Y0,X0+N,Y0+N)
    for name,src,mask,mode,vis in LAYERS:
        u=np.load(CAU44/src);m=None if mask is None else np.load(CAU44/mask)
        C.add_layer(s,u,name,None,m,box if m is not None else None,0,mode,255,vis,box)
    # Preserve all original image resources, including the untagged color state.
    # The obsolete thumbnail is removed so readers use the newly rendered composite.
    if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
    C.finalize_lr16(s)
    base=next(l for l in s if l.name=='09 1/60 x2');b=np.stack([C.channel(base,c) for c in range(3)],-1)
    comp=np.zeros((H,W,3),np.uint16);comp[base.top:base.bottom,base.left:base.right]=b;del b
    a=C.channel(base,-1);alpha=np.zeros((H,W),np.uint16)
    alpha[base.top:base.bottom,base.left:base.right]=65535 if a is None else a;del a
    du=np.load(CAU44/'earthshine_natural_delta_u16.npy')
    roi=comp[Y0:Y0+N,X0:X0+N];roi[:]=np.minimum(roi.astype(np.uint32)+du,65535).astype(np.uint16)
    alpha[Y0:Y0+N,X0:X0+N]=65535
    assert np.array_equal(roi,np.load(CAU44/'expected_moon_u16.npy'))
    rgba=np.dstack([comp[::4,::4]>>8,alpha[::4,::4]>>8]).astype(np.uint8)
    Image.fromarray(rgba).save(VIS44/'C5_Earthshine_V44_llenc_quart.png')
    Image.fromarray((roi>>8).astype(np.uint8)).save(VIS44/'C5_Earthshine_V44_lluna_1a1.png')
    data=[np.ascontiguousarray(comp[...,c].astype('>u2')).tobytes() for c in range(3)]+[np.ascontiguousarray(alpha.astype('>u2')).tobytes()]
    merged=C.ImageData(compression=C.Compression.RAW);merged.set_data(data,s._record.header);s._record.image_data=merged;s._updated=False
    del comp,alpha,data;gc.collect()
    with open(TARGET,'xb') as f:s.save(f)
    savejson(REB44/'C5_build.json',dict(source=str(SOURCE),source_sha256=expected,source_layers=before,target=str(TARGET),new_layers=[x[0] for x in LAYERS],original_channels='kept compressed byte for byte; no re-encoding',canvas=[W,H],depth=16))
    print('BUILT',TARGET,flush=True)

def verify():
    claim();b=json.loads((REB44/'C5_build.json').read_text());s=PSDImage.open(TARGET);assert len(s)==18 and s.size==(W,H) and s.depth==16
    rows=[]
    for old,l in zip(b['source_layers'],list(s)[:15]):
        now=fingerprint(l);expected=dict(old)
        if expected['visible'] and expected['name']!='09 1/60 x2':expected['visible']=False
        assert now==expected,l.name
        rows.append(dict(name=l.name,original_channel_bytes_exact=True))
    for l,(name,src,mask,mode,vis) in zip(list(s)[15:],LAYERS):
        u=np.load(CAU44/src);assert l.name==name and l.visible==vis and l.blend_mode==mode
        assert all(np.array_equal(C.channel(l,c),u[...,c]) for c in range(3)),name
        assert np.all(C.channel(l,-1)==65535)
        if mask:assert np.array_equal(C.channel(l,-2),np.load(CAU44/mask))
        rows.append(dict(name=name,decoded_uint16_exact=True))
    # Independent system reader, plus actual Photoshop in the next gate.
    r=subprocess.run(['/opt/homebrew/bin/magick','identify','-ping',str(TARGET)+'[0]'],capture_output=True,text=True,check=True)
    assert f'{W}x{H}' in r.stdout and '16-bit' in r.stdout,r.stdout
    savejson(REB44/'C5_verify.json',dict(PASS=True,sha256=sha(TARGET),bytes=TARGET.stat().st_size,layers=18,rows=rows,second_reader=r.stdout))
    print('VERIFIED',sha(TARGET),flush=True)

def jsx(js):
    sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js)+'\nend timeout\nend tell'
    p=subprocess.run(['osascript','-e',sc],capture_output=True,text=True)
    if p.returncode:raise RuntimeError('Photoshop AppleEvent: '+p.stderr.strip())
    return p.stdout.strip()

def gate():
    claim();v=json.loads((REB44/'C5_verify.json').read_text());assert v['PASS'] and sha(TARGET)==v['sha256']
    # Never let the gate close a candidate the user has already opened.
    jsx('var candidate=new File('+json.dumps(str(TARGET))+').fsName; for(var i=0;i<app.documents.length;i++){var p=""; try{p=app.documents[i].fullName.fsName;}catch(e){} if(p===candidate)throw new Error("V44 candidate already open: preserve user document");} "SAFE_NEW_CANDIDATE";')
    old=jsx('app.displayDialogs.toString();')
    try:
        p=subprocess.run(['/bin/zsh',str(ROOT/'research/tools/capes_totals_v14/porta_photoshop.sh'),str(TARGET)],check=True,capture_output=True,text=True)
        assert p.stdout.strip()==f'OBRE {W} px x {H} px · 18 capes',p.stdout
        tif=OUT44/'lliurables/Photoshop_V44_readback_RGBA.tif'
        assert not tif.exists()
        js='app.displayDialogs=DialogModes.NO; var d=app.open(new File('+json.dumps(str(TARGET))+')); var t=null; var profile=""; try { profile=d.colorProfileType.toString(); if(d.colorProfileType!==ColorProfile.NONE)profile+="|"+d.colorProfileName; var l=d.artLayers.getByName('+json.dumps(NATURAL)+'); l.visible=false; l.visible=true; app.refresh(); t=d.duplicate("V44_QA_TEMP",true); var o=new TiffSaveOptions(); o.imageCompression=TIFFEncoding.TIFFZIP; o.layers=false; o.alphaChannels=true; o.transparency=true; o.embedColorProfile=true; t.saveAs(new File('+json.dumps(str(tif))+'),o,true,Extension.LOWERCASE); } finally { if(t)t.close(SaveOptions.DONOTSAVECHANGES); d.close(SaveOptions.DONOTSAVECHANGES); } "RENDERED|"+profile;'
        rendered=jsx(js)
    finally:jsx('app.displayDialogs='+old+'; app.displayDialogs.toString();')
    savejson(REB44/'C5_photoshop_gate.json',dict(result=p.stdout.strip(),rendered=rendered,sha256=v['sha256'],readback=str(tif)))
    print(p.stdout.strip(),rendered,flush=True)

def readback():
    import tifffile
    g=json.loads((REB44/'C5_photoshop_gate.json').read_text());v=json.loads((REB44/'C5_verify.json').read_text())
    assert g['sha256']==v['sha256']==sha(TARGET)
    with tifffile.TiffFile(g['readback']) as tf:
        extras=[int(x) for x in tf.pages[0].extrasamples];a=tf.asarray()
    assert a.dtype==np.uint16 and a.shape==(H,W,4) and extras in ([1],[2])
    associated=extras==[1]
    roi=a[Y0:Y0+N,X0:X0+N,:3];expected=np.load(CAU44/'expected_moon_u16.npy');dif=abs(roi.astype(np.int32)-expected.astype(np.int32))
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
    savejson(REB44/'C5_photoshop_readback.json',rep)
    assert rep['PASS'],rep
    Image.fromarray((roi>>8).astype(np.uint8)).save(VIS44/'C5_Photoshop_real_lluna_1a1.png')
    preview=a[::4,::4].astype(np.float32)
    if associated:preview[...,:3]*=65535/np.maximum(preview[...,3:4],1)
    Image.fromarray((np.clip(preview,0,65535).astype(np.uint16)>>8).astype(np.uint8)).save(VIS44/'C5_Photoshop_real_llenc_quart.png')
    print('PHOTOSHOP PIXELS',rep,flush=True)

def publish():
    claim();v=json.loads((REB44/'C5_verify.json').read_text());p=json.loads((REB44/'C5_photoshop_readback.json').read_text())
    g=json.loads((REB44/'C5_photoshop_gate.json').read_text())
    assert v['PASS'] and p['PASS'] and sha(TARGET)==v['sha256']==g['sha256']==p['source_sha256'] and not FINAL.exists()
    tmp=CI/'Earthshine_V44_verificat.tmp.psb';assert not tmp.exists()
    with open(TARGET,'rb') as src,open(tmp,'xb') as dst:shutil.copyfileobj(src,dst,8<<20)
    assert sha(tmp)==v['sha256'];os.rename(tmp,FINAL)
    savejson(REB44/'C5_publish.json',dict(path=str(FINAL),sha256=v['sha256'],bytes=FINAL.stat().st_size,published_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    print('PUBLISHED',FINAL,flush=True)

if __name__=='__main__':{'build':build,'verify':verify,'gate':gate,'readback':readback,'publish':publish}[sys.argv[1]]()
