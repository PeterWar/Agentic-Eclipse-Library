"""Write cached filter layers with an independent Photoshop presentation recipe."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import time
import numpy as np
import tifffile

from .cancellation import check_cancelled
from .colour import set_luminosity
from .image_data import recipe_parameters, zero_missing
from .layer_engine import engine_for, requests, opacity, LABELS


def export_layered_package(worker, source, params, display, original_path, destination,
                           rgb=None, colour_report=None):
    from .layer_export import to_u16, photoshop_loader, write_edge_layer
    source = np.asarray(source)
    if source.ndim != 2 or not source.size:
        raise ValueError('Layer export requires a nonempty monochrome canvas')
    valid = np.isfinite(source)
    mask = params.get('valid_mask')
    if mask is not None:
        mask = np.asarray(mask, dtype=bool)
        if mask.shape != source.shape:
            raise ValueError('Layer validity must match the source canvas')
        valid &= mask
    if rgb is not None:
        rgb = np.asarray(rgb)
        if rgb.shape != (*source.shape, 3) or not np.isfinite(rgb[valid]).all():
            raise ValueError('RGB must match luminance and its observed-data mask')
    from .presentation import psb_presentation_settings, psb_base
    if display.get('mode') != 'ael_presentation':
        display = psb_presentation_settings(source, params.get('valid_mask'), rgb=rgb, params=params)
    params = {k:v for k,v in params.items() if k != 'layer_display'}
    destination=Path(destination)
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.layers-',dir=destination.parent))
    engine=engine_for(worker)
    records=[]
    started=time.perf_counter()
    def write(label,image,alpha,mode,amount,**metadata):
        check_cancelled()
        timer=time.perf_counter()
        order=len(records)+1
        filename=f'{order:02d}_{label}_{mode.replace(" ","")}.tif'
        rgba=np.dstack([image,image,image,alpha])
        tifffile.imwrite(stage/filename,rgba,photometric='rgb',extrasamples=['unassalpha'],
                         compression='zlib',metadata=None)
        records.append(dict(order=order,file=filename,mode=mode,opacity=amount,
                            opacity_255=round(amount*255),visible=amount>0,**metadata))
        print(f'[LAYER {label}: TIFF WRITE] Done in {time.perf_counter()-timer:.3f}s')
    try:
        reference = source if rgb is None else rgb
        finite = np.isfinite(reference) & (valid if reference.ndim == 2 else valid[..., None])
        reference_scale = float(np.max(reference, where=finite, initial=0.)) / .98 or 1.
        reference_file = '01_LINEAR_REFERENCE_Normal.tif'
        reference_rgb = to_u16(np.where(finite, reference / reference_scale, 0.))
        if reference_rgb.ndim == 2:
            reference_rgb = np.repeat(reference_rgb[..., None], 3, axis=-1)
        tifffile.imwrite(stage/reference_file,
                         np.dstack([reference_rgb, (finite if finite.ndim == 2 else finite.all(axis=-1)).astype(np.uint16)*65535]),
                         photometric='rgb', extrasamples=['unassalpha'], compression='zlib', metadata=None)
        records.append(dict(order=1, file=reference_file, name='Linear reference / receipt scale',
                            filter='linear_reference', mode='Normal', opacity=1., opacity_255=255,
                            visible=False, reference_scale=reference_scale,
                            negative_values='clipped in 16-bit reference; float source retains signed values',
                            colour_calibration=colour_report))
        base, color = psb_base(source,params,display,rgb)
        write('BASE',to_u16(base),valid.astype(np.uint16)*65535,
              'Normal',1.,filter='base',name='Display base')
        engine.prepare(worker,source,params)
        for name,variant,p,enabled in requests(params):
            layer=engine.layer(worker,source,p,name,variant)
            amount=round(opacity(name,p,enabled)*float(display.get('blend',1))*255)/255
            write(LABELS.get(variant,name.upper()),layer['image'],layer['alpha'],layer['mode'],amount,
                  filter=name,variant=variant,normalization=layer['mapping'],
                  operator_strength=p.get(name+'_str',100))
        timer=time.perf_counter()
        combined=engine.render(worker,source,params,display,base=base)
        if rgb is not None:
            order=len(records)+1
            filename=f'{order:02d}_RGB_Color.tif'
            tifffile.imwrite(stage/filename,np.dstack([to_u16(color),valid.astype(np.uint16)*65535]),
                             photometric='rgb',extrasamples=['unassalpha'],compression='zlib',metadata=None)
            records.append(dict(order=order,file=filename,filter='colour',mode='Color',
                                opacity=1.,opacity_255=255,visible=True))
            combined=set_luminosity(color,combined)
        from .presentation_edges import finish_presentation
        edge=engine.edge_alpha(source,params)
        write_edge_layer(stage,records,edge)
        combined=finish_presentation(combined,edge)
        if combined.ndim==2:
            combined=np.repeat(combined[...,None],3,axis=-1)
        combined_file='REFERENCE_COMBINED.tif'
        tifffile.imwrite(stage/combined_file,to_u16(combined),photometric='rgb',compression='zlib',metadata=None)
        tifffile.imwrite(stage/'SOURCE_float32.tif',zero_missing(source,valid).astype(np.float32),compression='zlib')
        tifffile.imwrite(stage/'VALID.tif',valid.astype(np.uint8)*255,compression='zlib')
        from .statistics_support import statistics_support
        tifffile.imwrite(stage/'STATISTICS_SUPPORT.tif',statistics_support(source,params,valid).astype(np.uint8)*255,compression='zlib')
        print(f'[LAYERS: COMPOSITE/SOURCE WRITE] Done in {time.perf_counter()-timer:.3f}s')
        for row in records:
            with (stage/row['file']).open('rb') as stream:
                row['sha256']=hashlib.file_digest(stream,'sha256').hexdigest()
        recipe=dict(shape=list(source.shape),layers=records,combined=combined_file,
                    parameters=recipe_parameters(params),display=display,source=original_path,
                    colour_calibration=colour_report,role='Independent linear-input layers; display composition',
                    alpha='Original validity retained separately; editable Edge Antialias adds display-only black fade',
                    missing_samples='Numerical files store zero; VALID marks unobserved samples')
        (stage/'recipe.json').write_text(json.dumps(recipe,indent=2),encoding='utf-8')
        background_file='00_BACKGROUND_Normal.tif'
        tifffile.imwrite(stage/background_file,np.zeros((*source.shape,3),np.uint16),
                         photometric='rgb',compression='zlib',metadata=None)
        loader_records=[dict(file=background_file,mode='Normal',opacity_255=255,visible=True),*records]
        (stage/'Load_layers_Photoshop.jsx').write_text(photoshop_loader(loader_records),encoding='utf-8')
        (stage/'Layers.md').write_text('# Independent filter layers\n\nLoad with File > Scripts > Browse > Load_layers_Photoshop.jsx.\n'
            'All filters start from the shared linear working input (including optional background equalization; see recipe parameters). Only Larson–Sekanina exposes Gain (0–200%); other filters have no Strength control. Opacity controls blending.\n'
            'The base uses the PSB Asinh-10 presentation with automatic scale plus manual EV exposure, regardless of the preview toggle. Main TIFF composition has no presentation stretch. A hidden linear reference carries its receipt scale.\n'
            'Edge Antialias is an editable display-only black overlay at lunar/missing boundaries.\n'
            'Numerical source files store missing samples as zero; VALID preserves their identity.\n',encoding='utf-8')
        check_cancelled()
        stage.rename(destination)
        print(f'[LAYERS PACKAGE: TOTAL] Done in {time.perf_counter()-started:.3f}s; {len(records)} layers')
        return destination
    except Exception:
        shutil.rmtree(stage)
        raise
