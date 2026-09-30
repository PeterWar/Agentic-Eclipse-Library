"""V56 package: only lunar RGB and its descriptive name change from BASE."""
from common import *
from psb_support import *
from psd_tools import PSDImage
from psd_tools.constants import Compression,ChannelID,Tag,Resource
from psd_tools.psd.layer_and_mask import ChannelInfo,ChannelData
from psd_tools.psd.image_data import ImageData
import sys,subprocess,gc,shutil,os
sys.path.insert(0,str(ROOT/'research/tools/encaix_sony'))
from psb_utils import finalize_lr16
TARGET=OUT/'staging/Earthshine_V56.psb';FINAL=CI/'Earthshine_V56.psb';W,H=10551,7506
NAME='V56 · detall 24–40 corroborat amb R i G · revelat preservat'
def replace(l,c,u):
    i=[int(x.id) for x in l._record.channel_info].index(c);cd=ChannelData(Compression.ZIP)
    cd.set_data(np.ascontiguousarray(u.astype('>u2')).tobytes(),l.width,l.height,16,2);l._channels[i]=cd;l._record.channel_info[i]=ChannelInfo(ChannelID(c),len(cd.data)+2)
def roi(l,c):
    a=channel(l,c)
    if c==-2:m=l._record.mask_data;left,top=m.left,m.top
    else:left,top=l.left,l.top
    return a[Y0-top:Y0-top+N,X0-left:X0-left+N]
def recomposition(s,rgb):
    B=np.stack([roi(s[1],c) for c in range(3)],-1)/65535.;Ba=roi(s[1],-1)/65535.*roi(s[1],-2)/65535.
    S=np.stack([roi(s[7],c) for c in range(3)],-1)/65535.;Sa=roi(s[7],-1)/65535.
    La=roi(s[25],-1)/65535.*roi(s[25],-2)/65535.
    Cc=B*Ba[...,None];Ca=Ba;Cb=np.where(Ca[...,None]>0,Cc/np.maximum(Ca[...,None],1e-9),0)
    mix=(1-Ca[...,None])*S+Ca[...,None]*np.maximum(S,Cb);Cc=Sa[...,None]*mix+(1-Sa[...,None])*Cc;Ca=Sa+Ca-Sa*Ca
    Cc=La[...,None]*rgb/65535.+(1-La[...,None])*Cc;Ca=La+Ca-La*Ca
    return np.rint(np.where(Ca[...,None]>0,Cc/np.maximum(Ca[...,None],1e-9),0)*65535).astype('uint16')
def build():
    claim();assert not TARGET.exists() and not FINAL.exists();assert sha(BASE)==BASE_SHA
    assert json.loads((OUT/'R11_photo_injections.json').read_text())['all_pass']
    inj=json.loads((OUT/'R9_repeatable_injections.json').read_text());assert inj['all_scene_pass'] and inj['all_detector_no_amplification']
    assert json.loads((OUT/'R13_qualification.json').read_text())['photographic_candidate_qualified']
    assert not json.loads((OUT/'R8_exact_retention.json').read_text())['lost_triples']
    s=PSDImage.open(BASE);before=[fingerprint(l) for l in s];rgb=np.load(OUT/'arrays/R8_candidate_rgb.npy');comp=recomposition(s,rgb)
    np.save(OUT/'arrays/E0_exact_composite.npy',comp)
    assert np.max(abs(comp.astype(int)-np.load(OUT/'arrays/R10_candidate_composite.npy').astype(int)))<=1
    for c in range(3):replace(s[25],c,rgb[...,c])
    s[25].name=NAME
    for tag in (Tag.FILTER_MASK,Tag.COMPOSITOR_INFO):
        if tag in s._record.layer_and_mask_information.tagged_blocks:s._record.layer_and_mask_information.tagged_blocks[tag].signature=b'8B64'
    if Resource.THUMBNAIL_RESOURCE in s._record.image_resources:del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
    finalize_lr16(s)
    merged=s._record.image_data.get_data(s._record.header);data=[]
    for c,raw in enumerate(merged):
        a=np.frombuffer(raw,dtype='>u2').reshape(H,W).copy()
        if c<3:a[Y0:Y0+N,X0:X0+N]=comp[...,c]
        data.append(a.tobytes());del a
    im=ImageData(compression=Compression.RAW);im.set_data(data,s._record.header);s._record.image_data=im;s._updated=False;del data,merged;gc.collect()
    with TARGET.open('xb') as f:s.save(f)
    save('E0_build.json',dict(source=str(BASE),source_sha256=BASE_SHA,target=str(TARGET),before=before,changed_layer=25,changed_channels=[0,1,2],name=NAME,canvas=[W,H],depth=16,layers=26,merged_compression='RAW'))
    print('BUILT',flush=True)
def verify():
    claim();s=PSDImage.open(TARGET);assert s.size==(W,H) and s.depth==16 and s.version==2 and len(s)==26
    before=json.loads((OUT/'E0_build.json').read_text())['before'];rows=[];rgb=np.load(OUT/'arrays/R8_candidate_rgb.npy')
    for i,l in enumerate(s):
        fp=fingerprint(l)
        if i!=25:assert fp==before[i],i;rows.append(dict(layer=i,all_exact=True))
        else:
            for k in ['bbox','opacity','blend','visible','mask']:assert fp[k]==before[i][k]
            for a,b in zip(fp['channels'],before[i]['channels']):
                if a['id'] not in [0,1,2]:assert a==b
            for c in range(3):assert np.array_equal(channel(l,c),rgb[...,c])
            rows.append(dict(layer=i,RGB_decoded_exact=True,mask_alpha_exact=True,geometry_exact=True,name=NAME))
    p=subprocess.run(['/opt/homebrew/bin/magick','identify','-ping',str(TARGET)+'[0]'],capture_output=True,text=True,check=True);assert '10551x7506' in p.stdout and '16-bit' in p.stdout
    save('E1_verify.json',dict(PASS=True,rows=rows,sha256=sha(TARGET),bytes=TARGET.stat().st_size,second_reader=p.stdout.strip(),source_still_exact=sha(BASE)==BASE_SHA))
    print('VERIFIED',flush=True)
def gate():
    claim();v=json.loads((OUT/'E1_verify.json').read_text());assert v['PASS'] and sha(TARGET)==v['sha256']
    before=inventory();assert str(TARGET) not in before;old=jsx('app.displayDialogs.toString();');active=jsx('app.documents.length?app.activeDocument.id:0;')
    tif=OUT/'staging/Photoshop_V56_readback_RGBA.tif';assert not tif.exists()
    try:
        p=subprocess.run(['/bin/zsh',str(ROOT/'research/tools/capes_totals_v14/porta_photoshop.sh'),str(TARGET)],capture_output=True,text=True,check=True)
        assert p.stdout.strip()=='OBRE 10551 px x 7506 px · 26 capes',p.stdout
        js='app.displayDialogs=DialogModes.NO;var d=app.open(new File('+json.dumps(str(TARGET))+'));var t=null;try{var l=d.artLayers.getByName('+json.dumps(NAME)+');l.visible=false;l.visible=true;app.refresh();t=d.duplicate("V56_QA_OWN",true);var o=new TiffSaveOptions();o.imageCompression=TIFFEncoding.TIFFZIP;o.layers=false;o.alphaChannels=true;o.transparency=true;o.embedColorProfile=true;t.saveAs(new File('+json.dumps(str(tif))+'),o,true,Extension.LOWERCASE);}finally{if(t)t.close(SaveOptions.DONOTSAVECHANGES);d.close(SaveOptions.DONOTSAVECHANGES);}"V56_RENDERED";'
        result=jsx(js)
    finally:
        jsx('app.displayDialogs='+old+';for(var i=0;i<app.documents.length;i++){if(app.documents[i].id==='+active+')app.activeDocument=app.documents[i];} "RESTORED";')
    after=inventory();assert before==after
    save('E2_photoshop_gate.json',dict(result=p.stdout.strip(),rendered=result,sha256=v['sha256'],readback=str(tif),before=before,after=after,documents_preserved=True))
    print(p.stdout.strip(),flush=True)
def readback():
    import tifffile
    from PIL import Image
    claim();g=json.loads((OUT/'E2_photoshop_gate.json').read_text());assert sha(TARGET)==g['sha256']
    with tifffile.TiffFile(g['readback']) as tf:a=tf.asarray();extras=list(map(int,tf.pages[0].extrasamples))
    assert a.shape[:2]==(H,W) and a.dtype==np.uint16
    rgb=a[...,:3];alpha=a[...,3] if a.shape[2]==4 else None;s=PSDImage.open(TARGET);raw=s._record.image_data.get_data(s._record.header)
    mx=0;total=0;count=0
    for c in range(3):
        ref=np.frombuffer(raw[c],dtype='>u2').reshape(H,W)
        for y in range(0,H,128):
            sl=slice(y,min(y+128,H));v=ref[sl].astype('int32');valid=np.ones(v.shape,bool)
            if alpha is not None:v=np.rint(v.astype(float)*alpha[sl]/65535.).astype('int32');valid=alpha[sl]>0
            dd=abs(rgb[sl,:,c].astype('int32')-v)[valid];mx=max(mx,int(dd.max()));total+=int(dd.sum());count+=dd.size
    moon=rgb[Y0:Y0+N,X0:X0+N];exact=np.load(OUT/'arrays/E0_exact_composite.npy');md=abs(moon.astype('int32')-exact.astype('int32'))
    rep=dict(PASS=bool(mx<=6 and md.max()<=3),max_full_DN16=mx,mean_full_DN16=total/count,max_moon_DN16=int(md.max()),p999_moon=float(np.percentile(md,99.9)),extrasamples=extras,target_sha256=g['sha256'],readback_sha256=sha(g['readback']))
    save('E3_readback.json',rep);assert rep['PASS'],rep
    np.save(OUT/'arrays/E3_native_moon.npy',moon)
    Image.fromarray((moon>>8).astype('uint8')).save(OUT/'vistes/E3_Photoshop_V56_moon_1a1.png')
    Image.fromarray((rgb[::4,::4]>>8).astype('uint8')).save(OUT/'vistes/E3_Photoshop_V56_full.png')
    Image.fromarray(np.clip(moon.astype(float)*2/256,0,255).astype('uint8')).save(OUT/'vistes/E3_Photoshop_V56_moon_x2.png')
    print('READBACK',rep,flush=True)
def publish():
    claim();v=json.loads((OUT/'E1_verify.json').read_text());q=json.loads((OUT/'E3_readback.json').read_text());assert v['PASS'] and q['PASS'] and sha(TARGET)==v['sha256']==q['target_sha256']
    assert json.loads((OUT/'E3_visual_review.json').read_text())['PASS']
    assert not FINAL.exists() and sha(BASE)==BASE_SHA;tmp=CI/'Earthshine_V56.tmp.psb';assert not tmp.exists()
    with TARGET.open('rb') as src,tmp.open('xb') as dst:shutil.copyfileobj(src,dst,8<<20)
    assert sha(tmp)==v['sha256'];os.rename(tmp,FINAL)
    save('E4_publish.json',dict(path=str(FINAL),sha256=sha(FINAL),bytes=FINAL.stat().st_size,time=datetime.datetime.now(datetime.timezone.utc).isoformat(),BASE_exact=True))
    print('PUBLISHED',FINAL,flush=True)
if __name__=='__main__':dict(build=build,verify=verify,gate=gate,readback=readback,publish=publish)[sys.argv[1]]()
