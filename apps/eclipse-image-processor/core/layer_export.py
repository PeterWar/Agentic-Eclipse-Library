"""Independent mono detail and optional RGB Color layer for Photoshop.

Every branch shares one prepared input, with no preceding enhancement branch.
Detail layers are uint16 equal-channel RGB; the optional top RGB layer uses Color.
Both support unassociated alpha. Numerical
input/preparation files retain float32 input units; they are not PS display layers.
"""
import json

import numpy as np
import tifffile

from .image_data import zero_missing


def photoshop_loader(records):
    """Import into a new unsaved document; never close an owner's document."""
    return '''#target photoshop
(function () {
    var layers = RECORDS;
    var folder = File($.fileName).parent;
    // Snapshot the enum name: do not retain a host enum object across imports.
    var dialogName = String(app.displayDialogs);
    var dialogMode = dialogName === String(DialogModes.NO) ? 'NO' :
        (dialogName === String(DialogModes.ERROR) ? 'ERROR' : 'ALL');
    var importError = null;
    var result = null;
    function ownedCopy(file) {
        for (var i = 0; i < app.documents.length; i++) {
            try {
                if (app.documents[i].fullName.fsName === file.fsName) {
                    app.activeDocument = app.documents[i];
                    return app.activeDocument.duplicate();
                }
            } catch (ignored) {}
        }
        return app.open(file);
    }
    try {
        app.displayDialogs = DialogModes.NO;
        for (var j = 0; j < layers.length; j++) {
            var entry = layers[j];
            var input = ownedCopy(File(folder.fsName + '/' + entry.file));
            try {
                if (j === 0) {
                    result = input.duplicate('Independent corona layers');
                    app.activeDocument = result;
                    if (result.activeLayer.isBackgroundLayer) {
                        result.activeLayer.isBackgroundLayer = false;
                    }
                } else {
                    app.activeDocument = input;
                    input.activeLayer.duplicate(result, ElementPlacement.PLACEATBEGINNING);
                    app.activeDocument = result;
                    result.activeLayer = result.layers[0];
                }
                result.activeLayer.name = entry.file.replace(/\\.tif$/i, '');
                result.activeLayer.blendMode = entry.mode === 'Color' ? BlendMode.COLORBLEND : (entry.mode === 'Normal' ? BlendMode.NORMAL : (entry.mode === 'Linear Light' ? BlendMode.LINEARLIGHT : (entry.mode === 'Multiply' ? BlendMode.MULTIPLY : BlendMode.OVERLAY)));
                result.activeLayer.opacity = entry.opacity_255 * 100 / 255;
                result.activeLayer.visible = entry.visible;
            } finally {
                app.activeDocument = input;
                input.close(SaveOptions.DONOTSAVECHANGES);
            }
        }
        app.activeDocument = result;
    } catch (error) {
        importError = error;
        throw new Error('Layer import failed at line ' + error.line + ': ' + error.message);
    } finally {
        try {
            app.displayDialogs = DialogModes[dialogMode];
        } catch (restoreError) {
            // A cleanup failure must not hide the actual import error.
            if (importError === null) throw restoreError;
        }
    }
})();
'''.replace('RECORDS', json.dumps(records, ensure_ascii=True))


def to_u16(a):
    return np.rint(np.clip(zero_missing(a), 0, 1) * 65535).astype(np.uint16)


def write_edge_layer(stage, records, alpha):
    """Editable black Normal overlay above detail and source colour layers."""
    if alpha is None:
        return
    from .presentation_edges import EDGE_WIDTH_NATIVE_PX
    filename=f'{len(records)+1:02d}_EDGE_ANTIALIAS_Normal.tif'
    rgba=np.zeros((*alpha.shape,4),np.uint16)
    rgba[...,3]=alpha
    tifffile.imwrite(stage/filename,rgba,photometric='rgb',extrasamples=['unassalpha'],compression='zlib',metadata=None)
    records.append(dict(order=len(records)+1,file=filename,name='Edge Antialias',filter='edge_antialias',
                        mode='Normal',opacity=1.,opacity_255=255,visible=True,
                        width_native_px=EDGE_WIDTH_NATIVE_PX,role='Display-only lunar/missing boundary fade to opaque black'))


def neutral_layer(values, valid):
    """Median-centred tanh display; S is 1.4826 MAD, in branch units.

    No absolute epsilon: near-constant residuals use a relative numerical floor.
    Excluded pixels have neutral grey and zero alpha, never invented structure.
    """
    a = np.asarray(values, dtype=np.float64)
    mask = np.asarray(valid, dtype=bool)
    if a.ndim != 2 or not a.size or mask.shape != a.shape:
        raise ValueError('Layer validity must match image')
    result = np.full(a.shape, .5, dtype=np.float64)
    if not mask.any():
        return result, dict(center=0., scale=0., constant=True)
    selected = a[mask]
    if not np.isfinite(selected).all():
        raise ValueError("Observed layer samples must be finite")
    center = float(np.median(selected))
    residual = selected - center
    mad = float(1.4826 * np.median(np.abs(residual)))
    floor = max(float(np.max(np.abs(selected))) * 1e-6, np.finfo(float).tiny)
    constant = bool(np.ptp(selected) <= floor)
    scale = max(mad, floor)
    if not constant:
        result[mask] = .5 + .5 * np.tanh(residual / (2.5 * scale))
    return result, dict(center=center, scale=scale, mad=mad,
                        relative_floor=floor, constant=constant,
                        formula='0.5 + 0.5*tanh((q-center)/(2.5*scale))')


def overlay(base, layer, alpha, opacity):
    """Photoshop Overlay in declared display numbers, with straight alpha."""
    mixed = np.where(base <= .5, 2 * base * layer,
                     1 - 2 * (1 - base) * (1 - layer))
    weight = alpha * opacity
    return base * (1 - weight) + mixed * weight


def linear_light(base, layer, alpha, opacity):
    """Signed addition: clip(base + 2*layer - 1), then layer opacity/alpha."""
    mixed = np.clip(base + 2*layer - 1, 0, 1)
    weight = alpha*opacity
    return base*(1-weight) + mixed*weight


def linear_detail_layer(values, valid, input_span):
    """Zero-centred linear encoding; one shared scale, no median or tanh.

    L=0.5+D/(2S), so Linear Light adds D/S before gamut clipping.
    S is at least the prepared input span and the largest absolute residual.
    """
    selected = np.asarray(values, dtype=float)[valid]
    if not np.isfinite(selected).all():
        raise ValueError('Observed detail must be finite')
    peak = float(np.max(np.abs(selected))) if selected.size else 0.
    scale = max(float(input_span), peak)
    layer = np.full(values.shape, .5)
    if scale > 0:
        layer[valid] += selected/(2*scale)
    return layer, dict(center=0., scale=scale, constant=peak == 0,
                       formula='0.5 + D/(2*scale)',
                       blend='clip(base + D/scale, 0, 1) before opacity')


def branch_domain(shape, params, name):
    yy, xx = np.ogrid[:shape[0], :shape[1]]
    radius = np.hypot(xx - params['sx'], yy - params['sy'])
    sr = float(params['sr'])
    if not np.isfinite(sr) or sr <= 0:
        raise ValueError('Layer export needs a positive disk radius')
    domain = radius > sr
    if name == 'nrgf':
        domain &= radius > float(params.get('nrgf_rad', 10)) / 10 * sr
    if name in ('fnrgf', 'rhef'):
        domain &= radius >= float(params[name + '_rad']) / 10 * sr
    if name == 'tangential':
        domain &= radius >= float(params.get('tangential_inner', 1.))*sr
        if params.get('tangential_outer', 0.):
            domain &= radius < float(params['tangential_outer'])*sr
    if name == 'fnrgf':
        domain &= radius < float(params.get('fnrgf_rmax', 30)) / 10 * sr
    return domain


from .layer_package import export_layered_package as export_layer_package
