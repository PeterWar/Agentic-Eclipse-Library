"""Verified PSB16 export of existing independent layer packages.

Low-level new_document/add_layer/_to_lr16 and imports adapted from AEL 1.3.3,
Copyright (c) 2026 Pere Guerra Serra, MIT (docs/third-party/AEL-MIT.txt).
Local additions: required blend modes, merged RGBA, recipe metadata, atomic
publication and exact channel verification. No upstream AEL install is needed.
"""
from pathlib import Path
import gc
import hashlib
import importlib.metadata
import json
import os
import tempfile
import time
from xml.sax.saxutils import escape

import numpy as np
import tifffile
from .cancellation import check_cancelled

MODES = ('normal','overlay','multiply','color','linear_light')
BLEND_KEYS = {'Multiply':'multiply','Normal':'normal','Overlay':'overlay','Color':'color','Linear Light':'linear_light'}

def _psd():
    try:
        from psd_tools import PSDImage
    except ImportError as e:  # pragma: no cover
        raise ImportError('PSB export requires psd-tools==1.26.0; install the project requirements') from e
    from psd_tools.api.layers import PixelLayer
    from psd_tools.constants import BlendMode, ChannelID, Compression, Resource, Tag
    from psd_tools.psd.image_resources import ImageResource
    from psd_tools.psd.layer_and_mask import ChannelData, ChannelDataList, ChannelInfo, LayerInfo, LayerRecord
    from psd_tools.psd.tagged_blocks import TaggedBlocks
    return dict(PSDImage=PSDImage, PixelLayer=PixelLayer, BlendMode=BlendMode, ChannelID=ChannelID,
                Compression=Compression, Resource=Resource, Tag=Tag, ImageResource=ImageResource,
                ChannelData=ChannelData, ChannelDataList=ChannelDataList, ChannelInfo=ChannelInfo,
                LayerInfo=LayerInfo, LayerRecord=LayerRecord, TaggedBlocks=TaggedBlocks)


def new_document(width: int, height: int):
    """An empty 16-bit RGB document in PSB large document format."""
    P = _psd()
    doc = P["PSDImage"].new("RGB", (int(width), int(height)), depth=16)
    doc._record.header.version = 2
    doc._next_layer_id = 1
    return doc


def add_layer(doc, name: str, rgb16: np.ndarray, alpha16: np.ndarray | None = None, *, mode: str = "normal",
              opacity: float = 1.0, visible: bool = True, rle: bool = False):
    """Append a full-canvas layer on top.  ``rgb16``: (H, W, 3) or (H, W) grey, uint16; ``alpha16``: (H, W)
    uint16 or None (opaque).  ``opacity`` 0–1."""
    P = _psd()
    if mode not in MODES:
        raise ValueError(f"mode must be one of {MODES}")
    rgb16 = np.asarray(rgb16)
    if rgb16.ndim == 2:
        rgb16 = np.repeat(rgb16[..., None], 3, axis=2)
    if rgb16.dtype != np.uint16 or rgb16.shape[2] != 3:
        raise ValueError("rgb16 must be uint16, (H, W, 3) or (H, W)")
    h, w = rgb16.shape[:2]
    if (h, w) != (doc.height, doc.width):
        raise ValueError(f"layer is {w}×{h}, document is {doc.width}×{doc.height}: layers are full canvas")
    if alpha16 is None:
        alpha16 = np.full((h, w), 65535, np.uint16)
    elif alpha16.dtype != np.uint16 or alpha16.shape != (h, w):
        raise ValueError("alpha16 must be uint16 (H, W)")
    rec = P["LayerRecord"](top=0, left=0, bottom=h, right=w, channel_info=[])
    rec.name = name.encode("mac_roman", "replace").decode("mac_roman")[:31]
    rec.tagged_blocks.set_data(P["Tag"].UNICODE_LAYER_NAME, name)
    rec.tagged_blocks.set_data(P["Tag"].LAYER_ID, doc._next_layer_id)
    doc._next_layer_id += 1
    rec.blend_mode = getattr(P["BlendMode"], mode.upper())
    rec.opacity = int(round(float(opacity) * 255))
    rec.flags.visible = bool(visible)
    comp = P["Compression"].RLE if rle else P["Compression"].ZIP_WITH_PREDICTION
    cdl = P["ChannelDataList"]()
    ver = doc._record.header.version
    planes = ((P["ChannelID"].TRANSPARENCY_MASK, alpha16), (P["ChannelID"](0), rgb16[..., 0]),
              (P["ChannelID"](1), rgb16[..., 1]), (P["ChannelID"](2), rgb16[..., 2]))
    for cid, plane in planes:
        cd = P["ChannelData"](comp)
        cd.set_data(np.ascontiguousarray(plane).astype(">u2").tobytes(), w, h, 16, ver)
        rec.channel_info.append(P["ChannelInfo"](cid, len(cd.data) + 2))
        cdl.append(cd)
    layer = P["PixelLayer"](doc, rec, cdl)
    doc.append(layer)
    return layer


def _to_lr16(doc) -> None:
    P = _psd()
    lmi = doc._record.layer_and_mask_information
    li = lmi.layer_info
    if li is None or not li.layer_records:
        return
    if lmi.tagged_blocks is None:
        lmi.tagged_blocks = P["TaggedBlocks"]()
    lmi.tagged_blocks.set_data(P["Tag"].LAYER_16, layer_count=li.layer_count, layer_records=li.layer_records,
                               channel_image_data=li.channel_image_data)
    lmi.layer_info = P["LayerInfo"]()


def _package(package):
    package = Path(package).resolve()
    recipe = json.loads((package/'recipe.json').read_text())
    shape = tuple(recipe['shape'])
    if len(shape) != 2 or not all(isinstance(v,int) and 0 < v <= 300000 for v in shape):
        raise ValueError('PSB needs two positive image dimensions, at most 300000 pixels')
    if not recipe.get('layers') or len(recipe['layers']) > 32766:
        raise ValueError('PSB needs 1 to 32766 image layers plus background')
    for row in recipe['layers']:
        if row.get('mode') not in BLEND_KEYS or not 0 <= row.get('opacity_255',-1) <= 255:
            raise ValueError('Unsupported layer mode or opacity')
        _package_path(package,row['file'])
    return package,recipe,shape


def _package_path(package,name):
    path = (package/name).resolve()
    if not path.is_relative_to(package) or not path.is_file():
        raise ValueError('Layer package paths must reference files inside the package')
    return path


def _pixels(path,shape):
    a = tifffile.imread(path)
    if a.dtype != np.uint16 or a.shape not in ((*shape,3),(*shape,4)):
        raise ValueError(f'PSB layer must be full-canvas uint16 RGB/RGBA: {path.name}')
    return a


def _name(row):
    return row.get('name') or Path(row['file']).stem


def _black_composite(composite):
    """Composite straight uint16 RGBA onto black; preserve RGB input exactly."""
    if composite.shape[-1] == 3:
        return composite
    return np.rint(composite[...,:3].astype(np.float64) *
                   (composite[...,3:4].astype(np.float64)/65535)).astype(np.uint16)


def _correction_input(package,recipe,shape):
    composite=_black_composite(_pixels(_package_path(package,recipe['combined']),shape))
    mask_file=recipe.get('validity_file','VALID.tif')
    valid=tifffile.imread(_package_path(package,mask_file))
    if valid.shape!=shape:
        raise ValueError('Color Correction validity must match PSB canvas')
    return composite,valid>0,recipe.get('parameters',{})


def verify_psb_package(path,package,*,color_correction=False):
    """Reopen PSB; check original channels, opaque black background and cached RGB exactly."""
    from psd_tools import PSDImage
    from psd_tools.constants import BlendMode,Resource
    package,recipe,shape = _package(package)
    doc = PSDImage.open(path)
    if (doc._record.header.version,doc.depth,doc.height,doc.width) != (2,16,*shape):
        raise ValueError('PSB header does not match the package')
    if len(doc) != len(recipe['layers']) + 1 + bool(color_correction):
        raise ValueError('PSB layer count does not match the package')
    background=doc[0]
    if (background.name,background.blend_mode,background.opacity,bool(background.visible)) != (
            '00_BACKGROUND_Black',BlendMode.NORMAL,255,True):
        raise ValueError('PSB black background metadata mismatch')
    if {int(info.id) for info in background._record.channel_info} != {-1,0,1,2}:
        raise ValueError('PSB black background channels mismatch')
    for info,channel in zip(background._record.channel_info,background._channels):
        expected=(b'\xff\xff' if int(info.id) == -1 else b'\x00\x00') * (shape[0]*shape[1])
        if channel.get_data(shape[1],shape[0],16,2) != expected:
            raise ValueError('PSB black background pixel mismatch')
    report=[]
    for layer,row in zip(list(doc)[1:],recipe['layers']):
        layer_start = time.perf_counter()
        check_cancelled()
        if (layer.name,layer.blend_mode,layer.opacity,bool(layer.visible)) != (
                _name(row),getattr(BlendMode,BLEND_KEYS[row['mode']].upper()),
                row['opacity_255'],row.get('visible',True)):
            raise ValueError(f'PSB layer metadata mismatch: {_name(row)}')
        a = _pixels(_package_path(package,row['file']),shape)
        for info,channel in zip(layer._record.channel_info,layer._channels):
            cid = int(info.id)
            expected = (a[...,3] if a.shape[-1] == 4 else np.full(shape,65535,np.uint16)) if cid == -1 else a[...,cid]
            actual = channel.get_data(shape[1],shape[0],16,2)
            if actual != np.ascontiguousarray(expected).astype('>u2').tobytes():
                raise ValueError(f'PSB pixel mismatch: {_name(row)}, channel {cid}')
        if {int(info.id) for info in layer._record.channel_info} != {-1,0,1,2}:
            raise ValueError('PSB must retain exactly RGB and layer transparency')
        report.append(dict(name=layer.name,mode=row['mode'],opacity_255=layer.opacity,
                           visible=bool(layer.visible),exact_rgb=True,exact_alpha=True))
        del a,actual,expected
        print(f"[PSB VERIFY: {_name(row)}] Done in {time.perf_counter()-layer_start:.3f}s")
    composite = _pixels(_package_path(package,recipe['combined']),shape)
    composite = _black_composite(composite)
    if doc._record.header.channels != 3:
        raise ValueError('PSB black-backed merged image must be RGB')
    for k,plane in enumerate(doc._record.image_data.get_data(doc._record.header)):
        if plane != np.ascontiguousarray(composite[...,k]).astype('>u2').tobytes():
            raise ValueError(f'PSB merged channel mismatch: {k}')
    if Resource.XMP_METADATA not in doc._record.image_resources:
        raise ValueError('PSB recipe metadata is missing')
    correction_report=None
    if color_correction:
        from .color_correction import verify_color_correction
        correction_report=verify_color_correction(doc,*_correction_input(package,recipe,shape))
    return dict(version=2,depth=16,shape=list(shape),layers=report,
                exact_composite=not color_correction,exact_base_reference=True,
                color_correction=correction_report,merged_transparency=False,black_background=True,
                psd_tools=importlib.metadata.version('psd-tools'))


def export_psb_package(package,destination,*,color_correction=False):
    """Convert a layer package; publish only after verified writing, never overwrite."""
    total_start = time.perf_counter()
    package,recipe,shape = _package(package)
    if color_correction and len(recipe['layers'])>32760:
        raise ValueError('Color Correction exceeds the PSB layer-record limit')
    destination = Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    if destination.suffix.lower() != '.psb':
        raise ValueError('The layered Photoshop destination must end in .psb')
    doc = new_document(shape[1],shape[0])
    layer_start = time.perf_counter()
    add_layer(doc,'00_BACKGROUND_Black',np.zeros((*shape,3),np.uint16))
    print(f"[PSB: BACKGROUND ENCODE] Done in {time.perf_counter()-layer_start:.3f}s")
    for row in recipe['layers']:
        layer_start = time.perf_counter()
        check_cancelled()
        path = _package_path(package,row['file'])
        if row.get('sha256'):
            with path.open('rb') as stream:
                if hashlib.file_digest(stream,'sha256').hexdigest() != row['sha256']:
                    raise ValueError(f'Layer file changed since package creation: {path.name}')
        a = _pixels(path,shape)
        add_layer(doc,_name(row),a[...,:3],a[...,3] if a.shape[-1] == 4 else None,
                  mode=BLEND_KEYS[row['mode']],opacity=row['opacity_255']/255.,
                  visible=row.get('visible',True))
        del a
        print(f"[PSB: {_name(row)} READ/HASH/ENCODE] Done in {time.perf_counter()-layer_start:.3f}s")
    composite_start = time.perf_counter()
    from psd_tools.constants import Compression,Resource
    from psd_tools.psd.image_resources import ImageResource
    rec=doc._record
    composite = _pixels(_package_path(package,recipe['combined']),shape)
    composite = _black_composite(composite)
    correction=None
    if color_correction:
        from .color_correction import add_color_correction
        correction=add_color_correction(doc,*_correction_input(package,recipe,shape))
    rec.header.channels=3
    rec.image_data.compression=Compression.RAW
    rec.image_data.set_data([np.ascontiguousarray(composite[...,k]).astype('>u2').tobytes()
                             for k in range(composite.shape[-1])],rec.header)
    _to_lr16(doc)
    provenance = dict(recipe=recipe,writer='AEL-derived PSB16 writer; Eclipse Image Processor',
                      psd_tools=importlib.metadata.version('psd-tools'),black_background=True)
    if correction is not None:
        provenance['color_correction']=correction
    xmp = ('<x:xmpmeta xmlns:x="adobe:ns:meta/"><rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">'
           '<rdf:Description rdf:about="" xmlns:eip="https://eclipse-image-processor/metadata/1/">'
           '<eip:recipe>'+escape(json.dumps(provenance,ensure_ascii=False))+'</eip:recipe>'
           '</rdf:Description></rdf:RDF></x:xmpmeta>')
    rec.image_resources[Resource.XMP_METADATA]=ImageResource(
        signature=b'8BIM',key=Resource.XMP_METADATA,name='',data=xmp.encode('utf-8'))
    del composite
    print(f"[PSB: CACHED COMPOSITE/METADATA] Done in {time.perf_counter()-composite_start:.3f}s")
    temporary=None
    write_start = time.perf_counter()
    try:
        with tempfile.NamedTemporaryFile(prefix='.'+destination.stem+'-',suffix='.psb.tmp',
                                         dir=destination.parent,delete=False) as stream:
            temporary=Path(stream.name)
            rec.write(stream)
            stream.flush()
            os.fsync(stream.fileno())
        print(f"[PSB: DISK WRITE] Done in {time.perf_counter()-write_start:.3f}s")
        del doc,rec
        gc.collect()
        verify_start = time.perf_counter()
        report=verify_psb_package(temporary,package,color_correction=color_correction)
        print(f"[PSB: VERIFY] Done in {time.perf_counter()-verify_start:.3f}s")
        check_cancelled()
        # Same-directory hard link publishes atomically and refuses a name collision.
        os.link(temporary,destination)
        print(f"[PSB: TOTAL] Done in {time.perf_counter()-total_start:.3f}s")
        return report
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
