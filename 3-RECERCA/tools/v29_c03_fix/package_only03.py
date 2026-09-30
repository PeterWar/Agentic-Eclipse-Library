"""Replace only the three grayscale color channels of layer03 in a new PSB.

The original remains untouched until the separate validation and Photoshop gate.
"""
import os,sys,json,hashlib,copy
from pathlib import Path
os.environ['V29_FINAL_GRID']='1'
D=Path(__file__).parent;ROOT=D.parents[2]
sys.path.insert(0,str(ROOT/'research/tools/v29'))
from common import *
from inspect_inputs import sha,channel
from psd_tools import PSDImage
from psd_tools.constants import Compression,Tag
from psd_tools.psd.layer_and_mask import ChannelData
from psd_tools.psd.image_data import ImageData
sys.path.insert(0,str(ROOT/'research/tools/encaix_sony'))
from psb_utils import finalize_lr16

TARGET=CT/'V29_c03_verificacio.psb'
NAME='03 ACHF azimutal 8-128 · V29'

def digest(b):return hashlib.sha256(b).hexdigest()
def signature(l):
    rec=copy.deepcopy(l._record)
    # Color-channel lengths are data-dependent; keep the complete original
    # record hash too, and a second hash excluding ONLY those three lengths.
    full=digest(rec.tobytes(version=2))
    for ci in rec.channel_info:
        if int(ci.id) in (0,1,2):ci.length=0
    return {'name':l.name,'bbox':list(l.bbox),'visible':l.visible,'opacity':l.opacity,'blend':str(l.blend_mode),'record_sha256':full,'record_without_color_lengths_sha256':digest(rec.tobytes(version=2)),
      'channels':{str(int(ci.id)):{'compression':int(cd.compression),'bytes':len(cd.data),'sha256':digest(cd.data)} for ci,cd in zip(l._record.channel_info,l._channels)}}

def global_signature(s):
    lm=s._record.layer_and_mask_information
    blocks={str(k):digest(v.tobytes(version=2)) for k,v in lm.tagged_blocks.items() if k!=Tag.LAYER_16}
    return {'header':digest(s._record.header.tobytes()),'color_mode':digest(s._record.color_mode_data.tobytes()),'image_resources':digest(s._record.image_resources.tobytes()),'other_global_tagged_blocks':blocks}

def main():
    manifest=json.loads((D/'input_manifest.json').read_text());src=Path(manifest['backup'])
    assert not TARGET.exists(),'staging PSB exists'
    assert sha(src)==manifest['sha256'],'backup has changed'
    assert json.loads((D/'candidate_qa.json').read_text())['PASS']
    assert json.loads((D/'independent_judge.json').read_text())['accepted_for_layer03'], 'independent review not accepted'
    s=PSDImage.open(src);ls=list(s);assert len(ls)==25 and s.depth==16 and s.size==(FW,FH)
    matches=[i for i,l in enumerate(ls) if l.name==NAME];assert matches==[20]
    rep={'input_manifest':manifest,'target':str(TARGET),'original_layers':[signature(l) for l in ls],'original_global':global_signature(s)}
    l=ls[20];u=np.load(D/'gran_u16.npy',mmap_mode='r');assert u.shape==(FH,FW) and u.dtype==np.uint16
    raw=np.ascontiguousarray(u.astype('>u2')).tobytes();cd=ChannelData(Compression.ZIP);cd.set_data(raw,FW,FH,16,2)
    for j,ci in enumerate(l._record.channel_info):
        if int(ci.id) in (0,1,2):l._channels[j]=copy.copy(cd);ci.length=len(cd.data)+2
    del raw,cd;log('only03 RGB replaced in memory')
    finalize_lr16(s)
    merged_old=s._record.image_data.get_data(s._record.header);comp=np.load(D/'composite.npy',mmap_mode='r')
    data=[np.ascontiguousarray(np.round(np.clip(comp[...,c],0,1)*65535).astype('>u2')).tobytes() for c in range(3)]+list(merged_old[3:])
    merged=ImageData(compression=Compression.RAW);merged.set_data(data,s._record.header);s._record.image_data=merged;s._updated=False
    rep['expected_extra_merged_channels']=[digest(b) for b in merged_old[3:]]
    assert global_signature(s)==rep['original_global']
    for i,ll in enumerate(s):
        sig=signature(ll);old=rep['original_layers'][i]
        if i!=20:assert sig==old,('unintended layer change',i)
        else:
            assert sig['record_without_color_lengths_sha256']==old['record_without_color_lengths_sha256']
            assert all(v==old['channels'][k] for k,v in sig['channels'].items() if k not in ('0','1','2'))
    with open(TARGET,'xb'):pass
    log('saving staging PSB');s.save(TARGET);savejson(D/'packaging_receipt.json',rep);log('staging PSB saved')
if __name__=='__main__':main()
