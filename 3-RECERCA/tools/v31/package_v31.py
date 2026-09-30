"""Replace only RGB of five non-azimuthal layers in a new full-canvas V31."""
import os,sys,json,copy,gc
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
D=Path(__file__).parent;ROOT=D.parents[2];C=D/'cau'
sys.path.insert(0,str(ROOT/'research/tools/v29_c03_fix'))
from package_only03 import signature,global_signature,digest
from common import *
from inspect_inputs import sha,channel
from build_canvas import canvas_layer,over
from psd_tools import PSDImage
from psd_tools.constants import Compression,BlendMode
from psd_tools.psd.layer_and_mask import ChannelData
from psd_tools.psd.image_data import ImageData
from psb_utils import finalize_lr16
from PIL import Image,ImageDraw
TARGET=CT/'V31_verificacio.psb';FINAL=CT/'V31.psb'
EXPECTED='0d1f23fe5c56acf60bb35d3e24acea02fffaaf333d04d7a3aa17e0aac4f3f8c0'
TAGS=('01','02','04','05','06')
NAMES={'01':'01 ACHF fi 2-32 · V29','02':'02 Passa-alt 24 · V29','04':'04 ACHF micro 1-16 · V30','05':'05 ACHF fi 2-48 · V30','06':'06 ACHF estructura 4-64 · V30'}
OUT=Path('/Users/USUARI/Desktop/Eclipse 2026/IA/output/v31_20260905')

def compose(s):
    comp=np.zeros((FH,FW,3),np.float32)
    for i,l in enumerate(s):
        if not l.visible:continue
        a,m=canvas_layer(l);mode='overlay' if l.blend_mode==BlendMode.OVERLAY else 'add' if i>=28 else 'normal'
        comp=over(comp,a,m,l.opacity/255,mode);del a,m;log('recomposed '+l.name)
    return comp

def main():
    assert not TARGET.exists() and not FINAL.exists()
    assert json.loads((D/'candidate_qa.json').read_text())['status']=='CHECKS_PASS'
    src=C/'input_V30.psb';assert sha(src)==EXPECTED
    s=PSDImage.open(src);ls=list(s);assert len(ls)==30 and s.size==(FW,FH) and s.depth==16
    rep={'source':str(src),'source_sha256':EXPECTED,'original_layers':[signature(l) for l in ls],'original_global':global_signature(s),'changed':[]}
    m=np.load(CAU/'fusion_support.npy');w=m.astype('float32');changed_visible=np.zeros((FH,FW),bool)
    for tag in TAGS:
        matches=[(i,l) for i,l in enumerate(ls) if l.name==NAMES[tag]];assert len(matches)==1
        i,l=matches[0];name=l.name;old=rep['original_layers'][i];assert l.size==(FW,FH)
        # Use actual frozen PSB RGB to avoid any assumptions about old caches.
        u0=channel(l,0);assert all(np.array_equal(channel(l,c),u0) for c in (1,2))
        if l.visible:
            mask=channel(l,-2);alpha=channel(l,-1)
            changed_visible|=((mask>0) if mask is not None else True)&((alpha>0) if alpha is not None else True)
        sigma=1.5 if tag=='04' else 3;den=gauss(w,sigma)
        a=u0.astype('float32')/65535;b=.5+gauss((a-.5)*w,sigma)/np.maximum(den,1e-8);b[~m]=.5
        u=np.round(np.clip(b,0,1)*65535).astype('uint16');pilot=np.load(C/f'{tag}_s{sigma:g}_u16.npy',mmap_mode='r')
        err=int(np.max(np.abs(u.astype('int32')-pilot.astype('int32'))));assert err<=1,('pilot differs from actual source',tag,err)
        np.save(C/f'{tag}_final_u16.npy',u)
        cd=ChannelData(Compression.ZIP);cd.set_data(np.ascontiguousarray(u.astype('>u2')).tobytes(),FW,FH,16,2)
        for k,ci in enumerate(l._record.channel_info):
            if int(ci.id) in (0,1,2):l._channels[k]=copy.copy(cd);ci.length=len(cd.data)+2
        sig=signature(l);assert sig['record_without_color_lengths_sha256']==old['record_without_color_lengths_sha256']
        assert all(v==old['channels'][k] for k,v in sig['channels'].items() if k not in ('0','1','2'))
        l.name=name.rsplit(' · V',1)[0]+' · V31'
        rep['changed'].append({'index':i,'tag':tag,'sigma_px':sigma,'old_name':name,'new_name':l.name,'pilot_max_difference_DN16':err,'signature':signature(l)})
        log('smoothed RGB only '+l.name);del u0,a,b,u,cd;gc.collect()
    comp=compose(s);np.save(C/'composite.npy',comp)
    im=Image.fromarray(np.uint8(np.clip(comp,0,1)*255));im.thumbnail((1800,1800),Image.Resampling.LANCZOS);im.save(OUT/'V31_llenc_sencer.png')
    oldcomp=np.load(ROOT/'research/tools/v30/cau/composite_default_r4.npy',mmap_mode='r')
    for name,x,y in [('limbe_W',4921,3776),('limbe_N',5362,3335),('limbe_E',5802,3776),('limbe_S',5362,4216),('filaments',5960,3260),('marca_N',5715,2200),('marca_S',5130,5160),('exterior',6500,2520)]:
        sl=(slice(y-256,y+256),slice(x-256,x+256));panel=Image.new('RGB',(1024,542));dr=ImageDraw.Draw(panel)
        for j,(a,label) in enumerate([(oldcomp[sl],'V30'),(comp[sl],'V31 sigma3')]):
            panel.paste(Image.fromarray(np.uint8(np.clip(a,0,1)*255)),(j*512,30));dr.text((j*512+8,8),label,fill='white')
        panel.save(OUT/f'QA_100_{name}.png')
    finalize_lr16(s);merged_old=s._record.image_data.get_data(s._record.header)
    outside=~changed_visible;rep['outside_changed_visible_masks']={'pixels':int(outside.sum()),'max_DN16':[]}
    for c in range(3):
        before=np.frombuffer(merged_old[c],'>u2').reshape(FH,FW);after=np.round(np.clip(comp[...,c],0,1)*65535).astype('uint16')
        err=int(np.max(np.abs(before[outside].astype('int32')-after[outside].astype('int32'))));assert err<=1
        rep['outside_changed_visible_masks']['max_DN16'].append(err)
    data=[np.ascontiguousarray(np.round(np.clip(comp[...,c],0,1)*65535).astype('>u2')).tobytes() for c in range(3)]+list(merged_old[3:])
    merged=ImageData(compression=Compression.RAW);merged.set_data(data,s._record.header);s._record.image_data=merged;s._updated=False
    rep['expected_extra_merged_channels']=[digest(b) for b in merged_old[3:]]
    assert global_signature(s)==rep['original_global']
    changed={x['index'] for x in rep['changed']}
    for i,l in enumerate(s):
        if i not in changed:assert signature(l)==rep['original_layers'][i]
    with open(TARGET,'xb'):pass
    log('saving V31');s.save(TARGET);savejson(D/'packaging_receipt.json',rep);log('V31 saved')
if __name__=='__main__':main()
