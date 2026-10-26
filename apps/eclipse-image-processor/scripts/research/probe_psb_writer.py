"""Opt-in PSB16 feasibility probe; no changes to application export/dependencies.

Run with psd-tools==1.26.0 available on PYTHONPATH and --ael-runtime pointing to
AEL 1.3.3's runtime directory. Writes only a NEW output directory. AEL's low-level
writer supplies the 16-bit Lr16 records; this probe adds Color and Linear Light
using psd-tools' public blend-mode property, without modifying AEL itself.
"""
import argparse
import hashlib
import importlib.metadata
import io
import json
from pathlib import Path
import struct
import sys
import zlib

import numpy as np
from PIL import Image

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from core.layer_export import overlay, linear_light, to_u16
from core.colour import set_luminosity


def independent_read(path):
    """Small spec-based PSB16 reader; no psd-tools/AEL parsing or decompression.

    Deliberately limited to this probe's full-canvas RGB+A layers, ZIP prediction,
    Unicode names, Lr16 section and RAW merged RGB. Not a general PSD parser.
    """
    f=io.BytesIO(path.read_bytes())
    def unpack(fmt):
        return struct.unpack('>'+fmt,f.read(struct.calcsize('>'+fmt)))
    signature,version,reserved,channels,h,w,depth,mode=unpack('4sH6sHIIHH')
    assert (signature,version,reserved,depth,mode)==(b'8BPS',2,b'\0'*6,16,3)
    for _ in range(2):
        size,=unpack('I'); f.seek(size,1)
    size,=unpack('Q');section_end=f.tell()+size
    primary_size,=unpack('Q');assert primary_size==0
    global_mask_size,=unpack('I');f.seek(global_mask_size,1)
    lr16=None
    while f.tell()+12<=section_end:
        sig,key=unpack('4s4s')
        assert sig in (b'8BIM',b'8B64')
        length,=unpack('Q' if key in (b'Lr16',b'Mt16',b'Mt32',b'Mtrn') else 'I')
        payload=f.read(length)
        if key==b'Lr16':lr16=payload
        f.seek((-length)%4,1)
    assert lr16 is not None
    merged_offset=section_end
    f=io.BytesIO(lr16)
    count,=unpack('h');records=[]
    for _ in range(abs(count)):
        top,left,bottom,right,nchannels=unpack('iiiiH')
        assert (top,left,bottom,right)==(0,0,h,w)
        planes=[unpack('hQ') for _ in range(nchannels)]
        sig,blend,opacity,clipping,flags,filler,extra_length=unpack('4s4sBBBBI')
        assert sig==b'8BIM'
        extra_start=f.tell();mask_size,=unpack('I');f.seek(mask_size,1)
        ranges,=unpack('I');f.seek(ranges,1)
        namelen,=unpack('B');pascal=f.read(namelen);f.seek((-(namelen+1))%4,1)
        name=pascal.decode('mac_roman')
        while f.tell()+12<=extra_start+extra_length:
            sig,key,length=unpack('4s4sI');payload=f.read(length);f.seek((-length)%4,1)
            if key==b'luni':
                units=struct.unpack('>I',payload[:4])[0];name=payload[4:4+2*units].decode('utf-16-be')
        f.seek(extra_start+extra_length)
        records.append(dict(name=name,mode=blend.decode('ascii'),opacity=opacity,
                            visible=not bool(flags&2),planes=planes))
    for record in records:
        data={}
        for cid,length in record.pop('planes'):
            payload=f.read(length);compression=struct.unpack('>H',payload[:2])[0]
            assert compression==3
            encoded=zlib.decompress(payload[2:])
            assert len(encoded)==h*w*2
            delta=np.frombuffer(encoded,dtype='>u2').reshape(h,w)
            data[cid]=(np.cumsum(delta,axis=1,dtype=np.uint64)&65535).astype(np.uint16)
        record['rgb16']=np.stack([data[i] for i in range(3)],axis=-1)
        record['alpha16']=data[-1]
    raw=path.read_bytes()[merged_offset:]
    assert struct.unpack('>H',raw[:2])[0]==0
    merged=np.frombuffer(raw[2:],dtype='>u2').reshape(channels,h,w).transpose(1,2,0).astype(np.uint16)
    return dict(size=[w,h],depth=depth,version=version,records=records,merged=merged)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ael-runtime',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    sys.path.insert(0,str(args.ael_runtime.resolve()))
    from ael import photoshop as writer
    from psd_tools import PSDImage
    from psd_tools.constants import BlendMode
    h,w=64,96;y,x=np.indices((h,w))
    rng=np.random.default_rng(783)
    base=to_u16(np.stack([.08+.5*x/(w-1),.12+.5*y/(h-1),.15+.4*(x+y)/(w+h-2)],axis=-1))
    opaque=np.full((h,w),65535,np.uint16)
    alpha=to_u16(np.clip((x-10)/60,0,1));alpha[20:30,30:45]=0
    layers=[dict(name='01 Base · RGB 16 bits',mode='normal',opacity=1.,visible=True,rgb16=base,alpha16=opaque),
            dict(name='02 Detalle fino — Overlay',mode='overlay',opacity=37/255,visible=True,
                 rgb16=rng.integers(29000,37000,(h,w,3),dtype=np.uint16),alpha16=alpha),
            dict(name='03 Larson–Sekanina · Linear Light',mode='linear_light',opacity=19/255,visible=True,
                 rgb16=rng.integers(31000,34500,(h,w,3),dtype=np.uint16),alpha16=np.flip(alpha,axis=1).copy()),
            dict(name='04 Color · RGB',mode='color',opacity=131/255,visible=True,
                 rgb16=rng.integers(4000,60000,(h,w,3),dtype=np.uint16),alpha16=alpha),
            dict(name='05 Oculta · 精度',mode='normal',opacity=53/255,visible=False,
                 rgb16=rng.integers(0,65536,(h,w,3),dtype=np.uint16),alpha16=alpha)]
    composite=base.astype(float)/65535
    for row in layers[1:]:
        if not row['visible']:continue
        rgb=row['rgb16'].astype(float)/65535;mask=row['alpha16'].astype(float)/65535
        if row['mode']=='overlay':composite=overlay(composite,rgb,mask[...,None],row['opacity'])
        elif row['mode']=='linear_light':composite=linear_light(composite,rgb,mask[...,None],row['opacity'])
        elif row['mode']=='color':
            coloured=set_luminosity(rgb,composite@np.array([.30,.59,.11]))
            a=mask[...,None]*row['opacity'];composite=composite*(1-a)+coloured*a
    merged=to_u16(composite)
    doc=writer.new_document(w,h,psb=True)
    for row in layers:
        layer=writer.add_layer(doc,row['name'],row['rgb16'],row['alpha16'],
                               mode='normal',opacity=row['opacity'],visible=row['visible'])
        layer.blend_mode=getattr(BlendMode,row['mode'].upper())
    destination=args.out/'probe_rgb16_layers.psb'
    writer.save(doc,destination,merged)
    api=writer.verify(destination,layers)
    assert api['ok'],api
    raw=independent_read(destination)
    assert raw['depth']==16 and raw['version']==2 and len(raw['records'])==len(layers)
    mode_keys=dict(normal='norm',overlay='over',color='colr',linear_light='lLit')
    checks=[]
    for actual,expected in zip(raw['records'],layers):
        assert actual['name']==expected['name']
        assert actual['mode']==mode_keys[expected['mode']]
        assert actual['opacity']==round(expected['opacity']*255)
        assert actual['visible']==expected['visible']
        np.testing.assert_array_equal(actual['rgb16'],expected['rgb16'])
        np.testing.assert_array_equal(actual['alpha16'],expected['alpha16'])
        # Precision witness: data contains values beyond an 8-bit ×257 lattice.
        off_grid=int(np.count_nonzero(actual['rgb16']%257))
        assert off_grid>0
        checks.append(dict(name=actual['name'],mode=actual['mode'],opacity=actual['opacity'],
                           visible=actual['visible'],exact_rgb=True,exact_alpha=True,
                           non_8bit_samples=off_grid))
    np.testing.assert_array_equal(raw['merged'],merged)
    # Negative control: an 8-bit roundtrip must be detected by the pixel check.
    quantized=(np.rint(layers[0]['rgb16']/257)*257).astype(np.uint16)
    assert not np.array_equal(raw['records'][0]['rgb16'],quantized)
    reopened=PSDImage.open(destination)
    np.testing.assert_allclose(reopened.numpy('color')*65535,merged,atol=.01)
    np.savez_compressed(args.out/'expected.npz',merged=merged,
        **{f'layer_{i}_rgb':r['rgb16'] for i,r in enumerate(layers)},
        **{f'layer_{i}_alpha':r['alpha16'] for i,r in enumerate(layers)})
    Image.fromarray(np.uint8(np.round(merged/257))).resize((768,512)).save(args.out/'expected_composite.png')
    report=dict(candidate='AEL 1.3.3 low-level writer + psd-tools',
                psd_tools=importlib.metadata.version('psd-tools'),attrs=importlib.metadata.version('attrs'),
                file=str(destination),sha256=hashlib.sha256(destination.read_bytes()).hexdigest(),
                bytes=destination.stat().st_size,size=[w,h],depth=16,version=2,
                api_roundtrip=api,independent_checks=checks,exact_cached_composite=True,
                quantization_negative_control=True,native_photoshop='not checked',
                limitations=['Small synthetic document only; no >2 GB stress test',
                             'Layer alpha verified; cached composite is opaque RGB',
                             'Cached composite uses application blend equations; native re-render not yet verified',
                             'Uses psd-tools private record APIs; pin and regression-test before integration'])
    (args.out/'report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
    print(json.dumps(report,indent=2,ensure_ascii=False))


if __name__=='__main__':main()
