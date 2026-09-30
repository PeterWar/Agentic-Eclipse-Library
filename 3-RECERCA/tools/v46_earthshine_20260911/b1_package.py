"""V46: one editable SUBTRACT grade above the complete live V45 snapshot.
Source channels are copied in their original ZIP-with-prediction encoding.
The original open document and published V45 are never saved or closed.
"""
from comu46 import *
from c5_fonts_psb import C,PSDImage,fingerprint,jsx,CI
from psd_tools.constants import BlendMode,Resource,Tag
import gc,subprocess,shutil,os,datetime,tifffile
from PIL import Image

SOURCE=HERE46/'V45_live_source.psd'
STAGING=HERE46/'staging';TARGET=STAGING/'Earthshine_V46.psb';FINAL=CI/TARGET.name
NAME='V46 · contorn fosc gradual · ajusta opacitat'

def build():
    claim46();STAGING.mkdir(exist_ok=True);assert not TARGET.exists() and not FINAL.exists()
    receipt=json.loads((REB46/'A0_snapshot.json').read_text());assert sha(SOURCE)==receipt['sha256']
    s=PSDImage.open(SOURCE);assert s.size==(W,H) and s.depth==16 and len(s)==24
    before=[fingerprint(l) for l in s]
    assert all(c.compression in (C.Compression.ZIP,C.Compression.ZIP_WITH_PREDICTION) for l in s for c in l._channels)
    s._record.header.version=2
    # Photoshop's native PSB uses extended-block signatures for these two
    # global blocks. A PSD snapshot carries 8BIM; changing only the main
    # header is insufficient for Photoshop's strict reader.
    for tag in (Tag.FILTER_MASK,Tag.COMPOSITOR_INFO):
        if tag in s._record.layer_and_mask_information.tagged_blocks:
            s._record.layer_and_mask_information.tagged_blocks[tag].signature=b'8B64'
    old=np.load(CAU46/'live_lunar_rgb_u16.npy');new=np.load(CAU46/'h_display_u16.npy')
    sub=old.astype(np.int32)-new.astype(np.int32);assert sub.min()>=0 and np.max(np.ptp(sub,axis=2))==0
    m=np.load(CAU46/'live_lunar_mask_u16.npy');box=(X0,Y0,X0+N,Y0+N)
    # Premultiply before SUBTRACT: Photoshop clips C-S before interpolating
    # a partial layer mask. Baking w into S instead guarantees C-wS>=0,
    # avoids that intermediate clipping, and retains the solar RGB signal.
    u=np.rint(sub.astype(float)*m[...,None]/65535).astype(np.uint16)
    np.save(CAU46/'grade_subtract_u16.npy',u)
    C.add_layer(s,u,NAME,None,None,None,0,BlendMode.SUBTRACT,255,True,box)
    if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
    C.finalize_lr16(s)
    # Independent expected composite from actual before TIFF, unassociated.
    a=tifffile.imread(OUT46/'lliurables/V45_live_before_RGBA.tif');assert a.shape==(H,W,4)
    alpha=a[...,3].copy();comp=np.empty((H,W,3),np.uint16)
    for y in range(0,H,128):
        sl=slice(y,min(y+128,H));v=a[sl,:,:3].astype(float)*65535/np.maximum(alpha[sl,:,None],1)
        comp[sl]=np.rint(np.clip(v,0,65535)).astype(np.uint16)
    del a
    roi=comp[Y0:Y0+N,X0:X0+N];assert np.all(alpha[Y0:Y0+N,X0:X0+N]==65535)
    assert np.all(roi.astype(np.int32)>=u.astype(np.int32))
    roi[:]=(roi.astype(np.int32)-u.astype(np.int32)).astype(np.uint16)
    np.save(CAU46/'expected_moon_u16.npy',roi)
    png46('B1_expected_lluna_1a1.png',roi/65535)
    data=[np.ascontiguousarray(comp[...,c].astype('>u2')).tobytes() for c in range(3)]+[np.ascontiguousarray(alpha.astype('>u2')).tobytes()]
    merged=C.ImageData(compression=C.Compression.RAW);merged.set_data(data,s._record.header);s._record.image_data=merged;s._updated=False
    del comp,alpha,data;gc.collect()
    with open(TARGET,'xb') as f:s.save(f)
    savejson(REB46/'B1_build.json',dict(source=str(SOURCE),source_sha256=receipt['sha256'],source_layers=before,target=str(TARGET),new_layer=NAME,canvas=[W,H],depth=16,selected_variant='h',source_channels='24 live layers copied compressed byte for byte; same visibility, geometry and masks',operation='One neutral-gray SUBTRACT layer; original lunar mask premultiplied into RGB before blend; opacity controls strength',scope='PHOTOGRAPHIC_TONE_ONLY'))
    print('BUILT',TARGET,flush=True)

def verify():
    claim46();b=json.loads((REB46/'B1_build.json').read_text());s=PSDImage.open(TARGET)
    assert s.version==2 and len(s)==25 and s.size==(W,H) and s.depth==16
    for old,l in zip(b['source_layers'],list(s)[:24]):assert fingerprint(l)==old,l.name
    l=list(s)[-1];u=np.load(CAU46/'grade_subtract_u16.npy');m=np.load(CAU46/'live_lunar_mask_u16.npy')
    assert l.name==NAME and l.visible and l.blend_mode==BlendMode.SUBTRACT
    assert all(np.array_equal(C.channel(l,c),u[...,c]) for c in range(3))
    assert l._record.mask_data is None and np.all(C.channel(l,-1)==65535)
    r=subprocess.run(['/opt/homebrew/bin/magick','identify','-ping',str(TARGET)+'[0]'],capture_output=True,text=True,check=True)
    assert f'{W}x{H}' in r.stdout and '16-bit' in r.stdout,r.stdout
    savejson(REB46/'B1_verify.json',dict(PASS=True,sha256=sha(TARGET),bytes=TARGET.stat().st_size,layers=25,source_layers_exact=24,grade_channels_exact=True,original_mask_used_in_premultiplication=True,second_reader=r.stdout))
    print('VERIFIED',sha(TARGET),flush=True)

def gate():
    claim46();v=json.loads((REB46/'B1_verify.json').read_text());assert v['PASS'] and sha(TARGET)==v['sha256']
    jsx('var candidate=new File('+json.dumps(str(TARGET))+').fsName;for(var i=0;i<app.documents.length;i++){var p="";try{p=app.documents[i].fullName.fsName;}catch(e){}if(p===candidate)throw new Error("Candidate already open");}"SAFE_NEW_CANDIDATE";')
    old=jsx('app.displayDialogs.toString();')
    try:
        p=subprocess.run(['/bin/zsh',str(ROOT/'research/tools/capes_totals_v14/porta_photoshop.sh'),str(TARGET)],check=True,capture_output=True,text=True)
        assert p.stdout.strip()==f'OBRE {W} px x {H} px · 25 capes',p.stdout
        tif=OUT46/'lliurables/Photoshop_V46_readback_RGBA.tif';assert not tif.exists()
        js='app.displayDialogs=DialogModes.NO;var d=app.open(new File('+json.dumps(str(TARGET))+'));var t=null;var profile="";try{profile=d.colorProfileType.toString();if(d.colorProfileType!==ColorProfile.NONE)profile+="|"+d.colorProfileName;var l=d.artLayers.getByName('+json.dumps(NAME)+');l.visible=false;l.visible=true;app.refresh();t=d.duplicate("V46_QA_TEMP",true);var o=new TiffSaveOptions();o.imageCompression=TIFFEncoding.TIFFZIP;o.layers=false;o.alphaChannels=true;o.transparency=true;o.embedColorProfile=true;t.saveAs(new File('+json.dumps(str(tif))+'),o,true,Extension.LOWERCASE);}finally{if(t)t.close(SaveOptions.DONOTSAVECHANGES);d.close(SaveOptions.DONOTSAVECHANGES);}"RENDERED|"+profile;'
        rendered=jsx(js)
    finally:jsx('app.displayDialogs='+old+';app.displayDialogs.toString();')
    savejson(REB46/'B1_photoshop_gate.json',dict(result=p.stdout.strip(),rendered=rendered,sha256=v['sha256'],readback=str(tif)))
    print(p.stdout.strip(),rendered,flush=True)

def readback():
    claim46();g=json.loads((REB46/'B1_photoshop_gate.json').read_text())
    assert g['sha256']==sha(TARGET)
    with tifffile.TiffFile(g['readback']) as tf:a=tf.asarray();extras=list(map(int,tf.pages[0].extrasamples))
    assert a.shape==(H,W,4) and a.dtype==np.uint16 and extras==[1]
    s=PSDImage.open(TARGET);merged=s._record.image_data.get_data(s._record.header)
    ref=[np.frombuffer(x,dtype='>u2').reshape(H,W) for x in merged]
    mx=0;total=0;count=0;ma=0
    for y in range(0,H,128):
        sl=slice(y,min(y+128,H));valid=ref[3][sl]>0
        for c in range(3):
            r=np.rint(ref[c][sl].astype(float)*ref[3][sl]/65535).astype(np.int32)
            d=abs(a[sl,:,c].astype(np.int32)-r)[valid]
            if d.size:mx=max(mx,int(d.max()));total+=int(d.sum());count+=d.size
        ma=max(ma,int(abs(a[sl,:,3].astype(np.int32)-ref[3][sl].astype(np.int32)).max()))
    roi=a[Y0:Y0+N,X0:X0+N,:3];expected=np.load(CAU46/'expected_moon_u16.npy')
    diff=abs(roi.astype(int)-expected.astype(int))
    rep=dict(PASS=mx<=6 and ma<=6,max_full_DN16=mx,max_alpha_DN16=ma,mean_full_DN16=total/count,max_moon_DN16=int(diff.max()),source_sha256=g['sha256'],readback_sha256=sha(Path(g['readback'])),profile=g['rendered'])
    savejson(REB46/'B1_photoshop_readback.json',rep);assert rep['PASS'],rep
    png46('B1_Photoshop_real_lluna_1a1.png',roi/65535)
    z=a[::4,::4].astype(float);z[...,:3]*=65535/np.maximum(z[...,3:4],1);png46('B1_Photoshop_real_llenc_quart.png',z/65535)
    np.save(CAU46/'after_photoshop_rgb_u16.npy',roi)
    print('READBACK',rep,flush=True)

def publish():
    claim46();v=json.loads((REB46/'B1_verify.json').read_text());p=json.loads((REB46/'B1_photoshop_readback.json').read_text())
    q=json.loads((REB46/'B2_protection.json').read_text());assert v['PASS'] and p['PASS'] and q['PASS'] and sha(TARGET)==v['sha256']==p['source_sha256'] and not FINAL.exists()
    tmp=CI/'Earthshine_V46_verificat.tmp.psb';assert not tmp.exists()
    with open(TARGET,'rb') as src,open(tmp,'xb') as dst:shutil.copyfileobj(src,dst,8<<20)
    assert sha(tmp)==v['sha256'];os.rename(tmp,FINAL)
    savejson(REB46/'B1_publish.json',dict(path=str(FINAL),sha256=v['sha256'],bytes=FINAL.stat().st_size,published_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    print('PUBLISHED',FINAL,flush=True)

if __name__=='__main__':dict(build=build,verify=verify,gate=gate,readback=readback,publish=publish)[sys.argv[1]]()
