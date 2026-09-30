"""Package an accepted V29 candidate, preserving every retained source channel.

No-clobber output. This script is only invoked after scientific and visual
checks have selected exact strengths in delivery_config.json.
"""
from common import *
import hashlib,io
from psd_tools import PSDImage
from psd_tools.constants import BlendMode,Compression
from psd_tools.psd.image_data import ImageData
sys.path.insert(0,str(ROOT/'research/tools/encaix_sony'))
from psb_utils import add_pixel_layer,add_mask16,finalize_lr16

def layer_signature(l):
    md=l._record.mask_data;b=io.BytesIO()
    if md is not None:md.write(b)
    return {'name':l.name,'bbox':list(l.bbox),'opacity':l.opacity,'blend':str(l.blend_mode),'mask_sha256':hashlib.sha256(b.getvalue()).hexdigest(),'channels':{str(int(i.id)):{'compression':int(c.compression),'bytes':len(c.data),'sha256':hashlib.sha256(c.data).hexdigest()} for i,c in zip(l._record.channel_info,l._channels)}}

def main():
    assert FINAL_GRID
    cfg=json.loads((CAU/'delivery_config.json').read_text());target=CT/'V29.psb'
    assert cfg['accepted_for_packaging'] is True
    assert not target.exists(),'V29.psb already exists; do not overwrite'
    s=PSDImage.open(HERE/'cau/input_V28.psb');ls=list(s);original={str(i):layer_signature(l) for i,l in enumerate(ls)}
    # Keep original objects (channels, alpha, masks, blend metadata) intact.
    stars,reflex=ls[24],ls[25]
    for i in range(25,17,-1):ls[i].delete_layer()
    for i,l in enumerate(list(s)):l.visible=i in (0,1,17)
    tb=s._record.layer_and_mask_information.tagged_blocks
    for kk in list(tb.keys()):
        kb=kk.value if hasattr(kk,'value') else kk
        if kb not in (b'Lr16',b'Mt16'):del tb[kk]
    bm=np.round(np.clip(np.load(CAU/'base_mask_final.npy'),0,1)*65535).astype(np.uint16)
    for source,name,vis in [('base_amb_cel','00 Base amb cel',False),('base_cel4','00 Base (cel/4)',True)]:
        a=np.load(CAU/f'{source}_final.npy',mmap_mode='r');rgb=np.round(np.clip(a,0,1)*65535).astype(np.uint16)
        l=add_pixel_layer(s,rgb,name,visible=vis,compression=Compression.ZIP);add_mask16(l,bm,0,0);del a,rgb;log('packed '+name)
    detail_names={'gran':'03 ACHF azimutal 8-128 · V29','achf':'01 ACHF fi 2-32 · V29','passalt24':'02 Passa-alt 24 · V29'}
    for source in ('gran','achf','passalt24'):
        v=cfg['layers'][source];a=np.load(CAU/f'{source}_final.npy',mmap_mode='r');a=.5+(a-.5)*v['strength']
        u=np.round(np.clip(a,0,1)*65535).astype(np.uint16);rgb=np.repeat(u[...,None],3,axis=2)
        dm=np.round(np.clip(np.load(CAU/f'{source}_mask_final.npy'),0,1)*65535).astype(np.uint16)
        l=add_pixel_layer(s,rgb,detail_names[source],blend=BlendMode.OVERLAY,opacity=v['opacity_u8'],compression=Compression.ZIP);add_mask16(l,dm,0,0);del a,u,rgb;log('packed '+source)
    for l in (stars,reflex):s.append(l);l.visible=True
    finalize_lr16(s)
    original_merged=s._record.image_data.get_data(s._record.header)
    comp=np.load(CAU/'composite_delivery.npy',mmap_mode='r')
    data=[np.ascontiguousarray(np.round(np.clip(comp[...,i],0,1)*65535).astype('>u2')).tobytes() for i in range(3)]+list(original_merged[3:])
    merged=ImageData(compression=Compression.RAW);merged.set_data(data,s._record.header);s._record.image_data=merged;s._updated=False
    expected={'input_snapshot':str(HERE/'cau/input_V28.psb'),'output':str(target),'preserved_original_indices':list(range(18))+[24,25],'original_layers':original,'output_layers':[layer_signature(l) for l in s],'delivery_config':cfg}
    # Exclusive reservation makes accidental reruns fail before saving.
    with open(target,'xb'):pass
    log('saving V29 PSB');s.save(target);savejson(CAU/'packaging_receipt.json',expected);log('PSB saved')

if __name__=='__main__':main()
