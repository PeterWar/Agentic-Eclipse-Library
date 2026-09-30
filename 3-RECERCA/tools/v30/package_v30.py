"""Preserve all V29 pixels; add five reversible alternatives to a new PSB."""
import os,sys,json,copy,gc
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
D=Path(__file__).parent;ROOT=D.parents[2];C=D/'cau'
sys.path.insert(0,str(ROOT/'research/tools/v29_c03_fix'))
from package_only03 import signature,global_signature,digest
from common import *
from inspect_inputs import sha,channel
from psd_tools import PSDImage
from psd_tools.api.layers import PixelLayer
from psd_tools.constants import Compression,BlendMode,Tag
from psd_tools.psd.layer_and_mask import ChannelData
from psd_tools.psd.image_data import ImageData
from psb_utils import add_pixel_layer,add_mask16,finalize_lr16
TARGET=CT/'V30_verificacio.psb'
FINAL=CT/'V30.psb'
EXPECTED='67169f0345c8abdf3fb9c3fd940d5b9f13d260864954d776c5d9277e15630676'
NEW=[('03 ACHF azimutal 8-128 · V30','gran_r4',38,True),
     ('07 ACHF azimutal suau r8 · V30','gran_r8',38,False),
     ('04 ACHF micro 1-16 · V30','micro1_16',36,False),
     ('05 ACHF fi 2-48 · V30','fi2_48',36,False),
     ('06 ACHF estructura 4-64 · V30','estructura4_64',36,False)]

def main():
    assert not TARGET.exists() and not FINAL.exists(),'new output must not exist'
    assert sha(C/'input_V29.psb')==EXPECTED
    assert json.loads((C/'injection_receipt.json').read_text())['default_r4_PASS']
    s=PSDImage.open(C/'input_V29.psb');ls=list(s);assert len(ls)==25
    rep={'source_sha256':EXPECTED,'target':str(TARGET),'original_layers':[signature(l) for l in ls],'original_global':global_signature(s),'new':[]}
    original03=ls[20];assert original03.name=='03 ACHF azimutal 8-128 · V29'
    original03.visible=False
    rep['expected_preserved_layers']=[signature(l) for l in ls]
    for j,(name,tag,opacity,visible) in enumerate(NEW):
        u=np.load(C/f'{tag}_u16.npy',mmap_mode='r');assert u.shape==(FH,FW) and u.dtype==np.uint16
        if j<2:
            # Copy the exact original alpha, physical mask and layer settings.
            rec=copy.deepcopy(original03._record);chans=copy.deepcopy(original03._channels)
            if Tag.LAYER_ID in rec.tagged_blocks:del rec.tagged_blocks[Tag.LAYER_ID]
            l=PixelLayer(s,rec,chans);s.append(l);l.name=name;l.visible=visible
            cd=ChannelData(Compression.ZIP);cd.set_data(np.ascontiguousarray(u.astype('>u2')).tobytes(),FW,FH,16,2)
            for k,ci in enumerate(l._record.channel_info):
                if int(ci.id) in (0,1,2):l._channels[k]=copy.copy(cd);ci.length=len(cd.data)+2
            s.remove(l);s.insert(21+j,l)
        else:
            l=add_pixel_layer(s,np.broadcast_to(u[...,None],(FH,FW,3)),name,blend=BlendMode.OVERLAY,opacity=opacity,visible=visible)
            mask=np.load(C/f'{tag}_mask_u16.npy',mmap_mode='r');add_mask16(l,mask,0,0)
            s.remove(l);idx=list(s).index(ls[23]);s.insert(idx,l)
        assert l.opacity==opacity and l.visible==visible
        rep['new'].append({'name':name,'tag':tag,'opacity':opacity,'visible':visible,'signature':signature(l)})
        log('added '+name);gc.collect()
    assert len(list(s))==30
    finalize_lr16(s)
    merged_old=s._record.image_data.get_data(s._record.header);comp=np.load(C/'composite_default_r4.npy',mmap_mode='r')
    data=[np.ascontiguousarray(np.round(np.clip(comp[...,c],0,1)*65535).astype('>u2')).tobytes() for c in range(3)]+list(merged_old[3:])
    merged=ImageData(compression=Compression.RAW);merged.set_data(data,s._record.header);s._record.image_data=merged;s._updated=False
    rep['expected_extra_merged_channels']=[digest(b) for b in merged_old[3:]]
    assert global_signature(s)==rep['original_global']
    assert [signature(l) for l in s if l.name not in [n[0] for n in NEW]]==rep['expected_preserved_layers']
    with open(TARGET,'xb'):pass
    log('saving V30 staging');s.save(TARGET);savejson(D/'packaging_receipt.json',rep);log('V30 saved')
if __name__=='__main__':main()
