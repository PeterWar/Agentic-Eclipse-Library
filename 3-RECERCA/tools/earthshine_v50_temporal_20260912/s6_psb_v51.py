"""S6: Earthshine_V51.psb (correcció A L'ORIGEN; substitueix la V50 refusada per Pere) = V49 de Pere (26 capes, canals comprimits copiats byte a byte) amb tres canvis declarats:
 (1) màscara d'usuari de «00 Base corba (total) · V42» oberta fins al limbe F4 a la ROI lunar (rampa 2 px);
 (2) capa NOVA «V50 · anell del limbe · Vixen 5,0–8,3 s · to de la base» (RGB16 + alfa) just damunt de la base;
 (3) màscara d'usuari de «V49 · graella verda nativa · Camera Raw de Pere» = cobertura geomètrica de F4 (rampa 2 px) a la vora,
     màscara de Pere exacta a més de 10 px endins. Píxels RGB de totes les capes: intactes.
Ús: build | verify | gate | readback | publish"""
import sys, json, hashlib, copy, gc, subprocess, shutil, os, datetime, numpy as np
from pathlib import Path
ROOT=Path('/Users/USUARI/Downloads/Eclipse 2026'); HERE=Path(__file__).resolve().parent; CAU=HERE/'cau'
OUT=ROOT/'output/earthshine_v50_temporal_20260912'; LLI=OUT/'lliurables'; LLI.mkdir(exist_ok=True)
V=ROOT/'output/earthshine_v49_pere_reveal_20260912'; SRC=V/'V49_Pere_referencia_20260912.psb'
SRC_SHA='fc22af4660c7ac7aeb10a1433f1c159a91968fed70646c4b9200bb5bf7748366'
CI=Path('/Users/USUARI/Desktop/Eclipse 2026/Projecte photoshop/1-Unint Capes/Capes interiors')
STAGING=HERE/'staging'; STAGING.mkdir(exist_ok=True); TARGET=STAGING/'Earthshine_V51.psb'; FINAL=CI/'Earthshine_V51.psb'
X0,Y0,N=4677,3077,1400; W,H=10551,7506; CLAIM='CLAUDE_EARTHSHINE_V51_ORIGEN_20260912'
BASE='00 Base corba (total) · V42'; LUN='V49 · graella verda nativa · Camera Raw de Pere'; L09='09 1/60 x2'
BOX=(3277,4273,4863,5859)  # Y0,Y1,X0,X1 de la caixa recomposta (S4)
sys.path.insert(0,str(ROOT/'research/tools/encaix_sony'))
from psd_tools import PSDImage
from psd_tools.constants import Compression, BlendMode, ChannelID, Tag, Resource
from psd_tools.psd.layer_and_mask import LayerRecord, ChannelInfo, ChannelData, ChannelDataList, MaskData, MaskFlags
from psd_tools.psd.tagged_blocks import TaggedBlocks
from psd_tools.psd.image_data import ImageData
from psd_tools.api.layers import PixelLayer
def claim():
    assert json.loads((ROOT/'.coordination/claim.lock/owner.json').read_text())['claim_id']==CLAIM
def sha(p):
    with open(p,'rb') as f: return hashlib.file_digest(f,'sha256').hexdigest()
def savejson(p,v): Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=1)+'\n')
def compressed(u,w,h):
    cd=ChannelData(Compression.ZIP); cd.set_data(np.ascontiguousarray(np.asarray(u).astype('>u2')).tobytes(),w,h,16,2); return cd
def chan(l,cid):
    ids=[int(c.id) for c in l._record.channel_info]; i=ids.index(cid); cd=l._channels[i]
    if cid==-2: md=l._record.mask_data; w,h=md.right-md.left,md.bottom-md.top
    else: w,h=l.width,l.height
    return np.frombuffer(cd.get_data(w,h,16,2),dtype='>u2').reshape(h,w).astype(np.uint16)
def replace_channel(l,cid,u):
    ids=[int(c.id) for c in l._record.channel_info]; i=ids.index(cid); h,w=u.shape
    cd=compressed(u,w,h); l._channels[i]=cd; l._record.channel_info[i]=ChannelInfo(ChannelID(cid),len(cd.data)+2)
def fingerprint(l):
    return dict(name=l.name,bbox=list(l.bbox),opacity=l.opacity,blend=str(l.blend_mode),visible=l.visible,
        channels=[dict(id=int(i.id),compression=int(c.compression),sha256=hashlib.sha256(c.data).hexdigest()) for i,c in zip(l._record.channel_info,l._channels)],
        mask=None if l._record.mask_data is None else dict(left=l._record.mask_data.left,top=l._record.mask_data.top,right=l._record.mask_data.right,bottom=l._record.mask_data.bottom,bg=l._record.mask_data.background_color))
def jsx(js):
    sc='tell application id "com.adobe.Photoshop"\nwith timeout of 3600 seconds\ndo javascript '+json.dumps(js)+'\nend timeout\nend tell'
    p=subprocess.run(['osascript','-e',sc],capture_output=True,text=True)
    if p.returncode: raise RuntimeError('Photoshop AppleEvent: '+p.stderr.strip())
    return p.stdout.strip()

def build():
    claim(); assert not TARGET.exists() and not FINAL.exists(); assert sha(SRC)==SRC_SHA
    s=PSDImage.open(SRC); assert s.size==(W,H) and s.depth==16 and len(s)==26
    before=[fingerprint(l) for l in s]
    L=list(s); base=L[1]; lun=L[25]; assert base.name==BASE and lun.name==LUN and L[7].name==L09
    s._record.header.version=2
    for tag in (Tag.FILTER_MASK,Tag.COMPOSITOR_INFO):
        if tag in s._record.layer_and_mask_information.tagged_blocks: s._record.layer_and_mask_information.tagged_blocks[tag].signature=b'8B64'
    bY0,bY1,bX0,bX1=BOX; newb=np.load(CAU/'base_rgb_new_roi_u16.npy')  # ROI 1400² amb la caixa recomposta
    for c in range(3):
        a=chan(base,c); roi=a[Y0:Y0+N,X0:X0+N]; assert np.array_equal(roi,np.load(CAU/f'base_ch{c}_roi.npy'))
        roi[:]=newb[...,c]; replace_channel(base,c,a); del a
    bm=chan(base,-2); md=base._record.mask_data; assert (md.left,md.top,md.right,md.bottom)==(0,0,W,H)
    old_roi=bm[Y0:Y0+N,X0:X0+N].copy(); assert np.array_equal(old_roi,np.load(CAU/'base_ch-2_roi.npy'))
    new=np.load(CAU/'base_mask51_u16.npy'); assert np.all(new.astype(int)>=old_roi.astype(int)),'la màscara de la base només s obre'
    bm[Y0:Y0+N,X0:X0+N]=new; replace_channel(base,-2,bm); del bm
    lm=chan(lun,-2); md=lun._record.mask_data; assert (md.left,md.top,md.right,md.bottom)==(0,0,W,H)
    assert np.array_equal(lm[Y0:Y0+N,X0:X0+N],np.load(CAU/'lun_ch-2_roi.npy'))
    lm[Y0:Y0+N,X0:X0+N]=np.load(CAU/'lun_mask51_u16.npy'); replace_channel(lun,-2,lm); del lm
    if Resource.THUMBNAIL_RESOURCE in s._record.image_resources: del s._record.image_resources[Resource.THUMBNAIL_RESOURCE]
    from psb_utils import finalize_lr16; finalize_lr16(s)
    # dades fusionades: exportació real de Photoshop de la V49 amb la ROI del candidat
    import tifffile
    comp=tifffile.imread(V/'A1_Pere_actual.tif'); assert comp.shape==(H,W,3) and comp.dtype==np.uint16
    cand=np.load(CAU/'cand51_roi_u16.npy'); comp[Y0:Y0+N,X0:X0+N]=cand
    data=[np.ascontiguousarray(comp[...,c].astype('>u2')).tobytes() for c in range(3)]
    merged=ImageData(compression=Compression.RAW); merged.set_data(data,s._record.header); s._record.image_data=merged; s._updated=False
    del comp,data; gc.collect()
    with open(TARGET,'xb') as f: s.save(f)
    savejson(OUT/'S6_build.json',dict(source=str(SRC),source_sha256=SRC_SHA,source_layers=before,target=str(TARGET),new_layer=None,box=BOX,
        changed=[dict(layer=BASE,channels=[0,1,2],what='fusió Vixen recomposta a la caixa lunar amb la màscara lunar per fotograma al limbe aparent (S4), recepta b4e exacta; només canvia on la lluminància canvia'),dict(layer=BASE,channel=-2,what='màscara oberta on hi ha dada nova (d ≥ −2 px); només s obre'),dict(layer=LUN,channel=-2,what='alfa geomètrica [−1,+1] on la base té dada, 1 on no en té; màscara de Pere exacta a > 10 px endins')],
        untouched='24 capes íntegres + RGB/alfa de les dues capes modificades: canals comprimits copiats byte a byte',canvas=[W,H],depth=16))
    print('BUILT',TARGET,flush=True)

def verify():
    claim(); b=json.loads((OUT/'S6_build.json').read_text()); s=PSDImage.open(TARGET)
    assert s.version==2 and len(s)==26 and s.size==(W,H) and s.depth==16
    L=list(s); old=b['source_layers']; rows=[]; others=L
    for o,l in zip(old,others):
        now=fingerprint(l)
        if l.name in (BASE,LUN):
            for k in ('name','bbox','opacity','blend','visible','mask'): assert now[k]==o[k],(l.name,k)
            for a,bb in zip(now['channels'],o['channels']):
                if a['id']==-1 or (l.name==LUN and a['id']>=0): assert a==bb,(l.name,a['id'])
            m=chan(l,-2)[Y0:Y0+N,X0:X0+N]; exp=np.load(CAU/('base_mask51_u16.npy' if l.name==BASE else 'lun_mask51_u16.npy')); assert np.array_equal(m,exp),l.name
            if l.name==BASE:
                newb=np.load(CAU/'base_rgb_new_roi_u16.npy'); src=PSDImage.open(SRC); sb=list(src)[1]; assert sb.name==BASE
                for c in range(3):
                    a=chan(l,c); a0=chan(sb,c); assert np.array_equal(a[Y0:Y0+N,X0:X0+N],newb[...,c]),('base roi',c)
                    a[Y0:Y0+N,X0:X0+N]=a0[Y0:Y0+N,X0:X0+N]; assert np.array_equal(a,a0),('base fora ROI',c); del a,a0
            rows.append(dict(name=l.name,changed_channels_decoded_exact=True,other_channels_exact=True))
        else:
            assert now==o,l.name; rows.append(dict(name=l.name,exact=True))
    r=subprocess.run(['/opt/homebrew/bin/magick','identify','-ping',str(TARGET)+'[0]'],capture_output=True,text=True,check=True)
    assert f'{W}x{H}' in r.stdout and '16-bit' in r.stdout,r.stdout
    savejson(OUT/'S6_verify.json',dict(PASS=True,sha256=sha(TARGET),bytes=TARGET.stat().st_size,layers=26,rows=rows,second_reader=r.stdout.strip()))
    print('VERIFIED',sha(TARGET),flush=True)

def gate():
    claim(); v=json.loads((OUT/'S6_verify.json').read_text()); assert v['PASS'] and sha(TARGET)==v['sha256']
    jsx('var candidate=new File('+json.dumps(str(TARGET))+').fsName;for(var i=0;i<app.documents.length;i++){var p="";try{p=app.documents[i].fullName.fsName;}catch(e){}if(p===candidate)throw new Error("Candidate already open");}"SAFE_NEW_CANDIDATE";')
    old=jsx('app.displayDialogs.toString();')
    try:
        p=subprocess.run(['/bin/zsh',str(ROOT/'research/tools/capes_totals_v14/porta_photoshop.sh'),str(TARGET)],check=True,capture_output=True,text=True)
        assert p.stdout.strip()==f'OBRE {W} px x {H} px · 26 capes',p.stdout
        tif=LLI/'Photoshop_V51_readback_RGBA.tif'; assert not tif.exists()
        js='app.displayDialogs=DialogModes.NO;var d=app.open(new File('+json.dumps(str(TARGET))+'));var t=null;var profile="";try{profile=d.colorProfileType.toString();if(d.colorProfileType!==ColorProfile.NONE)profile+="|"+d.colorProfileName;var l=d.artLayers.getByName('+json.dumps(LUN)+');l.visible=false;l.visible=true;app.refresh();t=d.duplicate("V51_QA_TEMP",true);var o=new TiffSaveOptions();o.imageCompression=TIFFEncoding.TIFFZIP;o.layers=false;o.alphaChannels=true;o.transparency=true;o.embedColorProfile=true;t.saveAs(new File('+json.dumps(str(tif))+'),o,true,Extension.LOWERCASE);}finally{if(t)t.close(SaveOptions.DONOTSAVECHANGES);d.close(SaveOptions.DONOTSAVECHANGES);}"RENDERED|"+profile;'
        rendered=jsx(js)
    finally: jsx('app.displayDialogs='+old+';app.displayDialogs.toString();')
    savejson(OUT/'S6_photoshop_gate.json',dict(result=p.stdout.strip(),rendered=rendered,sha256=v['sha256'],readback=str(tif)))
    print(p.stdout.strip(),rendered,flush=True)

def readback():
    claim(); import tifffile; from PIL import Image
    g=json.loads((OUT/'S6_photoshop_gate.json').read_text()); assert g['sha256']==sha(TARGET)
    with tifffile.TiffFile(g['readback']) as tf: a=tf.asarray(); extras=list(map(int,tf.pages[0].extrasamples))
    assert a.shape[:2]==(H,W) and a.dtype==np.uint16
    rgb=a[...,:3]; alpha=a[...,3] if a.shape[2]==4 else None
    s=PSDImage.open(TARGET); merged=s._record.image_data.get_data(s._record.header); ref=[np.frombuffer(x,dtype='>u2').reshape(H,W) for x in merged]
    mx=0; total=0; count=0
    for y in range(0,H,128):
        sl=slice(y,min(y+128,H)); valid=(alpha[sl]>0) if alpha is not None else np.ones((sl.stop-sl.start,W),bool)
        for c in range(3):
            r=ref[c][sl].astype(np.int32)
            if alpha is not None: r=np.rint(r*alpha[sl]/65535).astype(np.int32)
            d=abs(rgb[sl,:,c].astype(np.int32)-r)[valid]; mx=max(mx,int(d.max())); total+=int(d.sum()); count+=d.size
    roi=rgb[Y0:Y0+N,X0:X0+N].astype(np.int32); cand=np.load(CAU/'cand51_roi_u16.npy').astype(np.int32); diff=np.abs(roi-cand)
    rep=dict(PASS=bool(mx<=6),max_full_DN16=mx,mean_full_DN16=total/count,max_moon_DN16=int(diff.max()),p999_moon_DN16=float(np.percentile(diff,99.9)),extrasamples=extras,source_sha256=g['sha256'],readback_sha256=sha(g['readback']),profile=g['rendered'])
    savejson(OUT/'S6_photoshop_readback.json',rep); assert rep['PASS'],rep
    Image.fromarray((roi>>8).astype(np.uint8)).save(OUT/'vistes'/'S6_Photoshop_real_lluna_1a1.png')
    Image.fromarray((rgb[::4,::4]>>8).astype(np.uint8)).save(OUT/'vistes'/'S6_Photoshop_real_llenc_quart.png')
    np.save(CAU/'after_photoshop51_roi_u16.npy',roi.astype(np.uint16)); print('READBACK',rep,flush=True)

def publish():
    claim(); v=json.loads((OUT/'S6_verify.json').read_text()); p=json.loads((OUT/'S6_photoshop_readback.json').read_text())
    assert v['PASS'] and p['PASS'] and sha(TARGET)==v['sha256']==p['source_sha256'] and not FINAL.exists()
    assert sha(SRC)==SRC_SHA and sha(CI/'Earthshine_V49.psb')==SRC_SHA,'la V49 de Pere ha canviat'
    tmp=CI/'Earthshine_V51.tmp.psb'; assert not tmp.exists()
    with open(TARGET,'rb') as src,open(tmp,'xb') as dst: shutil.copyfileobj(src,dst,8<<20)
    assert sha(tmp)==v['sha256']; os.rename(tmp,FINAL)
    savejson(OUT/'S6_publish.json',dict(path=str(FINAL),sha256=v['sha256'],bytes=FINAL.stat().st_size,published_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),V49_sha256_unchanged=SRC_SHA))
    print('PUBLISHED',FINAL,v['sha256'],flush=True)

if __name__=='__main__': dict(build=build,verify=verify,gate=gate,readback=readback,publish=publish)[sys.argv[1]]()
