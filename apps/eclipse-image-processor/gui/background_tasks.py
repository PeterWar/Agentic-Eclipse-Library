"""Background I/O and display computations; these functions never touch widgets."""
import cv2
import numpy as np
import tifffile
from PySide6.QtCore import QThread
from core.linear_export import split_source_channels
from core.image_data import resize_observed, observed_bounds
from core.layer_engine import colour_display
from core.presentation import (normalized_base, composition_settings,
                               psb_presentation_settings, psb_base)
from core.presentation_edges import finish_presentation


class TaskThread(QThread):
    def __init__(self, function, *args, parent=None):
        super().__init__(parent)
        self.function, self.args = function, args
        self.result = None
        self.error = None

    def run(self):
        try:
            self.result = self.function(*self.args)
        except Exception as error:
            self.error = str(error)


def load_source(file_path, geometry, detect_limb):
    img = None
    lower_path = file_path.lower()

    if lower_path.endswith(".xisf"):
        try:
            import xisf
            xisf_file = xisf.XISF(file_path)
            img = xisf_file.read_image(0)
        except Exception as e:
            print(f"XISF reader warning: {e}")

    if img is None and lower_path.endswith((".fits", ".fit", ".fts")):
        try:
            from astropy.io import fits
            with fits.open(file_path) as hdul:
                for hdu in hdul:
                    if hdu.data is not None and isinstance(hdu.data, np.ndarray) and hdu.data.ndim >= 2:
                        img = np.squeeze(hdu.data)
                        break
        except Exception as e:
            print(f"FITS reader warning: {e}")

    if img is None:
        try:
            with tifffile.TiffFile(file_path) as tif:
                img = tif.pages[0].asarray()
        except Exception:
            pass

    if img is None:
        img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)
        if img is not None and img.ndim == 3 and img.shape[-1] in (3, 4):
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2RGBA if img.shape[-1] == 4 else cv2.COLOR_BGR2RGB)

    if img is None:
        from PIL import Image
        with Image.open(file_path) as pil_img:
            img = np.array(pil_img)

    if img is None:
        raise ValueError("Could not decode image with any available decoder.")

    white = float(np.iinfo(img.dtype).max) if np.issubdtype(img.dtype, np.integer) else None
    mono, source_rgb = split_source_channels(img)
    full = np.ascontiguousarray(mono, dtype=np.float32)
    h, w = full.shape
    scale = min(1., 1500 / max(h, w))
    preview = resize_observed(full, (int(w*scale), int(h*scale))) if scale < 1 else full.copy()
    circle = detect_limb(full) if geometry is None else geometry
    return dict(full=full, rgb=source_rgb, white=white, preview=preview,
                scale=scale, circle=circle, display_bounds=observed_bounds(full), missing=np.count_nonzero(~np.isfinite(full)))


def display_pixels(image):
    """Convert in row tiles: avoid full-size float RGB temporaries for native views."""
    result=np.empty(image.shape,np.uint8)
    for first in range(0,image.shape[0],128):
        stop=first+128
        scaled=image[first:stop]*255.
        np.clip(scaled,0,255,out=scaled)
        result[first:stop]=scaled
    return result


def render_snapshot(job):
    source = job['source']
    params = dict(job['params'], valid_mask=np.isfinite(source))
    display = job['display']
    engine = job['engine']
    colour_cache, preview_cache = job['colour_cache'], job['preview_cache']
    rgb = job['rgb']
    colour_error = None
    psb_settings = None
    if rgb is not None:
        if colour_cache is None:
            report = dict(method='none')
            if job['calibrate']:
                try:
                    rgb, report = job['neutralize'](rgb, job['white'])
                except ValueError as error:
                    colour_error = str(error)
            colour_cache = (rgb, None, report)
        rgb = colour_cache[0]
        if job.get('psb_preview'):
            psb_settings=psb_presentation_settings(job['source_identity'], rgb=rgb,
                params=job['psb_params'], exposure_ev=job['psb_exposure_ev'])
        if source.shape != rgb.shape[:2]:
            if preview_cache is None or preview_cache[0] is not rgb or preview_cache[1] != source.shape:
                reduced = np.stack([resize_observed(rgb[...,c], (source.shape[1],source.shape[0])) for c in range(3)],axis=-1)
                preview_cache = (rgb,source.shape,reduced)
            rgb = preview_cache[2]
    if job.get('psb_preview'):
        if psb_settings is None:
            psb_settings=psb_presentation_settings(job['source_identity'],
                params=job['psb_params'], exposure_ev=job['psb_exposure_ev'])
        base,colour=psb_base(source,params,psb_settings,rgb)
        settings=dict(psb_settings,blend=display.get('blend',1.))
        final=engine.render(job['worker'],source,params,settings,calculate=False,base=base)
        if final is None:
            final=base
            psb_settings['pending_filters']=True
        if colour is not None:
            final=job['set_luminosity'](colour,final)
    else:
        final=engine.render(job['worker'],source,params,display,calculate=False)
        if final is None:
            final=job['fallback'] if job['has_layers'] else normalized_base(source,display)
            if final.shape != source.shape:
                final=resize_observed(final,(source.shape[1],source.shape[0]))
        if rgb is not None:
            final=job['set_luminosity'](colour_display(rgb,source,composition_settings(display)),final)
    final = finish_presentation(final, engine.edge_alpha(source, params))
    native_pixels=display_pixels(final) if job['native'] else None
    if job['native']:
        size = job['preview_size']
        final = (np.stack([resize_observed(final[...,c],size) for c in range(3)],axis=-1)
                 if rgb is not None else resize_observed(final,size))
    pixels = display_pixels(final)
    return final, pixels, colour_cache, preview_cache, colour_error, native_pixels, psb_settings
