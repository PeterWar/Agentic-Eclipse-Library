"""Validate the current layer pipeline on an opt-in image without modifying it.

Run in the project environment. The output must be a new directory; it receives
measurements, normalized layer compositions and an actual GUI TIFF/JPEG export.
Resolution differences are measurements, not scientific correctness thresholds.
"""
import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import warnings
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
for variable in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ.setdefault(variable,'1')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import cv2
import numpy as np
from PySide6.QtWidgets import QApplication
import tifffile

cv2.setNumThreads(min(2,os.cpu_count() or 4))
cv2.setUseOptimized(True)

from core.colour import set_luminosity
from core.filters import FilterWorker
from core.image_data import recipe_parameters, resize_observed
from core.layer_engine import ORDER, colour_display, engine_for
from core.layer_export import to_u16
from core.presentation_edges import finish_presentation
from gui.app import EclipseProcessorApp


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def wait_for_idle(app, window, timeout=300):
    deadline = time.monotonic() + timeout
    while True:
        app.processEvents()
        busy = (window.is_processing or window.recalculation_timer.isActive()
                or window.presentation_timer.isActive() or window.background.thread is not None
                or any(getattr(window, name) is not None for name in
                       ('_load_thread', '_geometry_thread', '_presentation_thread', '_presentation_request', '_export_thread')))
        if not busy:
            return
        if time.monotonic() >= deadline:
            raise TimeoutError(window.status_label.text())
        time.sleep(.01)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    before = digest(args.source)
    app = QApplication.instance() or QApplication([])
    window = EclipseProcessorApp()
    window.auto_calculate = False
    window.btn_auto_calc.setChecked(False)
    try:
        with patch('gui.app.QFileDialog.getOpenFileName', return_value=(str(args.source), '')):
            window.load_image_action()
        wait_for_idle(app, window)
        if window.full_raw_image is None:
            raise RuntimeError(window.status_label.text())
        full, preview = window.full_raw_image, window.preview_image
        full_before, preview_before = full.copy(), preview.copy()
        baseline = {name: window.collect_filter_parameters(image.shape) for name, image in
                    (('preview', preview), ('full', full))}
        report = dict(source=str(args.source), sha256=before, shape=list(full.shape),
                      input_state=window.combo_input_state.currentData(),
                      role='Normalized enhancement compositions, not photometric linear masters', cases=[])
        worker = FilterWorker()
        engine = engine_for(worker)
        display = window.collect_display_parameters()
        for family in (*ORDER, 'achf', 'combined'):
            results = {}
            row = dict(name=family, resolutions={})
            for resolution, image in (('preview', preview), ('full', full)):
                params = deepcopy(baseline[resolution])
                if family != 'combined':
                    for name in (*ORDER, 'achf'):
                        params[name + '_enabled'] = name == family
                    params[family + '_str'] = 100
                    params[family + '_opacity'] = 100
                    if family == 'achf':
                        for settings in params['achf_variants'].values():
                            settings.update(strength=100, opacity=100)
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always', RuntimeWarning)
                    started = time.perf_counter()
                    result = engine.render(worker, image, params, display)
                    seconds = time.perf_counter() - started
                assert np.isfinite(result).all() and result.shape == image.shape, (family, resolution)
                assert not [w for w in caught if issubclass(w.category, RuntimeWarning)], caught
                np.testing.assert_array_equal(engine.render(worker, image, params, display), result)
                disabled = dict(params)
                for name in (*ORDER, 'achf'):
                    disabled[name + '_enabled'] = False
                from core.layer_engine import display_base
                np.testing.assert_array_equal(engine.render(worker, image, disabled, display),
                    (display_base(image,disabled,display).astype(float)/65535).astype(np.float32))
                results[resolution] = result
                row['resolutions'][resolution] = dict(seconds=seconds,
                    percentiles=np.percentile(result, [0, 1, 50, 99, 100]).tolist(),
                    parameters=recipe_parameters(params))
                tifffile.imwrite(args.output/f'{family}_{resolution}_composition.tif', result,
                                 metadata={'role': report['role']}, compression='zlib')
            reduced = resize_observed(results['full'], (preview.shape[1], preview.shape[0]))
            row['preview_full_rmse'] = float(np.sqrt(np.mean((reduced-results['preview'])**2)))
            report['cases'].append(row)
            print(f'Validated {family}', flush=True)

        # Exercise the actual asynchronous GUI/export route, including native RGB calibration.
        window.chk_export_layers.setChecked(False)
        window.chk_verify_preview.setChecked(True)
        window.dispatch_pipeline_request()
        wait_for_idle(app, window)
        if window._full_cache is None:
            raise RuntimeError(window.status_label.text())
        window.render_matrix_to_screen()
        wait_for_idle(app, window)
        expected_jpeg = window.image_label._native_pixels.copy()
        destination = args.output/'actual_gui_export.tiff'
        with patch('gui.app.QFileDialog.getSaveFileName', return_value=(str(destination), '')):
            window.export_image_action()
        wait_for_idle(app, window)
        if not destination.is_file():
            raise RuntimeError(window.status_label.text())
        params = window.collect_filter_parameters(full.shape)
        active_engine = engine_for(window.filter_worker)
        expected = active_engine.render(window.filter_worker, full, params, display)
        if window.full_source_rgb is not None:
            expected = set_luminosity(colour_display(window._colour_cache[0], full, display), expected)
        expected = finish_presentation(expected, active_engine.edge_alpha(full, params))
        exported = tifffile.imread(destination)
        assert exported.dtype == np.uint16
        np.testing.assert_array_equal(exported, to_u16(expected))
        jpeg = cv2.imread(str(destination.with_name('actual_gui_export_preview.jpg')), cv2.IMREAD_UNCHANGED)
        if jpeg.ndim == 3:
            jpeg = cv2.cvtColor(jpeg, cv2.COLOR_BGR2RGB)
        assert jpeg.shape == expected_jpeg.shape
        report['export'] = dict(shape=list(exported.shape), dtype=str(exported.dtype),
            tiff_matches_unstretched_composition=True,
            jpeg_mae=float(np.mean(abs(jpeg.astype(float)-expected_jpeg))))
        assert report['export']['jpeg_mae'] < 8, report['export']
        np.testing.assert_array_equal(full, full_before)
        np.testing.assert_array_equal(preview, preview_before)
        assert digest(args.source) == before, 'The source changed during validation'
        (args.output/'measurements.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(f'Validation passed: {args.output}', flush=True)
    finally:
        window.close()
        deadline = time.monotonic() + 300
        while window.persistent_thread.isRunning() or any(getattr(window, name) is not None for name in
                ('_load_thread', '_geometry_thread', '_presentation_thread', '_export_thread')) or window.background.thread is not None:
            app.processEvents()
            if time.monotonic() >= deadline:
                raise TimeoutError('Workers did not finish closing')
            time.sleep(.01)


if __name__ == '__main__':
    main()
