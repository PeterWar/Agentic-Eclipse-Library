"""Additional numerical controls with explicit physical units and conversions."""
from PySide6.QtWidgets import QCheckBox, QLabel
from .components import ScrollSafeComboBox
from .factories import create_slider_float, create_slider, update_slider_display, set_parameter_title

# attribute, recipe key, title, min, max, default, divisor, help
CONTROLS = {
    'nrgf': [
        ('nrgf_min_count', 'nrgf_min_count', 'Minimum samples per ring', 2, 128, 12, 1., 'Annuli with fewer observed samples remain undefined; at least four consecutive usable annuli are needed.'),
        ('nrgf_smooth_bins', 'nrgf_smooth_bins', 'Profile smoothing (rings)', 0, 100, 0, 10., 'Optional local quadratic smoothing of radial model nodes, never image pixels. AEL default is zero; smoothing may bias curved profiles.')],
    'fnrgf': [
        ('fnrgf_smooth', 'fnrgf_smooth', 'Model smoothing (preview px)', 0, 640, 80, 10., 'Radial Gaussian sigma of the continuous background model, not the final image. Zero disables smoothing.'),
        ('fnrgf_fade', 'fnrgf_fade', 'Boundary fade (preview px)', 0, 1280, 80, 10., 'Continuous mode: smooth application at the inner and outer radii without changing observed-data validity.'),
        ('fnrgf_ridge', 'fnrgf_ridge', 'Harmonic regularization', 0, 1000, 10, 1000., 'Dimensionless penalty on higher angular harmonics. Increased automatically for partial coverage; zero disables it.'),
        ('fnrgf_floor', 'fnrgf_floor', 'Minimum width fraction', 0, 100, 5, 100., 'Floor relative to typical annular spread. Continuous mode also keeps its divisor positive.'),
        ('fnrgf_robust', 'fnrgf_robust', 'Robust fit iterations', 0, 5, 2, 1., 'Continuous-model reweighting passes; zero selects ordinary regularized least squares.'),
        ('fnrgf_min_pixels', 'fnrgf_min_pixels', 'Minimum samples per sector', 1, 32, 1, 1., 'Sectors with fewer observed pixels do not constrain the model. Widths always need at least two samples; rings without three measured sector widths retain the input.'),
        ('fnrgf_mean_tail', 'fnrgf_mean_tail', 'Highest-harmonic mean weight', 0, 100, 0, 100., 'Final weight of the linearly attenuated brightness harmonics. Continuous mode preserves the DC mean unless all coefficients are removed.'),
        ('fnrgf_width_tail', 'fnrgf_width_tail', 'Highest-harmonic width weight', 0, 100, 0, 100., 'Final weight of the width harmonics. Continuous mode fits log-width and always retains its DC scale.')],
    'rhef': [
        ('rhef_upsilon_high', 'rhef_upsilon_high', 'Upper-tail exponent', 1, 500, 35, 100., 'Exponent for the upper half of the rank curve. One leaves this tail unchanged.'),
        ('rhef_min_count', 'rhef_min_count', 'Minimum samples per ring', 2, 128, 12, 1., 'Continuous mode: fewer positive samples leave the ring unprocessed.'),
        ('rhef_quantiles', 'rhef_quantiles', 'Quantile samples', 17, 1025, 257, 1., 'Continuous mode: integer number of quantile nodes, including both endpoints. Any count from 17 to 1025 is valid; powers of two are not required. Odd counts include the median node. Default 257 gives 256 intervals. More nodes increase cost.'),
        ('rhef_noise_confidence', 'rhef_noise_confidence', 'Noise confidence (0 = off)', 0, 100, 0, 10., 'Optional blend attenuation where angular spread is near estimated noise. Adjacent-pixel noise is approximate, particularly on correlated stacks.')],
    'larson_sekanina': [
        ('larson_sekanina_angular', 'larson_sekanina_angular', 'Angular increment (degrees)', 0, 1800, 30, 10., 'Symmetric rotations by plus/minus this angle. The radial increment is fixed at zero; zero angular increment bypasses the operator.')],
    'tangential': [
        ('tangential_arc', 'tangential_arc', 'Angular Gaussian sigma (degrees)', 1, 300, 30, 10., 'Angular blur sigma, 0.1 to 30 degrees. The corresponding arc length increases with radius.'),
        ('tangential_gain', 'tangential_gain', 'Detail gain', 0, 50, 10, 10., 'Multiplier of the signed angular residual before layer encoding and opacity blending.'),
        ('tangential_denoise', 'tangential_denoise', 'Noise threshold (sigma)', 0, 100, 0, 10., 'Soft threshold on signed detail, using a robust adjacent-pixel noise estimate. Zero bypasses it; not calibrated detector noise.'),
        ('tangential_inner', 'tangential_inner', 'Inner radius (disk radii)', 0, 40, 10, 10., 'Start of tangential processing in reference disk radii.'),
        ('tangential_outer', 'tangential_outer', 'Outer radius (disk radii)', 11, 200, 40, 10., 'Outer processing radius in reference disk radii, used only when Limit outer radius is checked.'),
        ('tangential_fade', 'tangential_fade', 'Boundary fade (preview px)', 0, 1280, 80, 10., 'Smooth radial blend width at the application boundaries; scaled on export.')],
}


def add_controls(window):
    for family, specs in CONTROLS.items():
        section = getattr(window, 'sec_'+family)
        for attr, key, label, minimum, maximum, default, divisor, help_text in specs:
            if divisor == 1:
                slider, _ = create_slider(label, minimum, maximum, default,
                                           section.content_layout, tooltip=help_text,
                                           on_release_callback=window.dispatch_pipeline_request_if_auto)
            else:
                slider, _ = create_slider_float(label, minimum, maximum, default, divisor,
                                                section.content_layout, tooltip=help_text,
                                                on_release_callback=window.dispatch_pipeline_request_if_auto)
            slider.setObjectName('sl_'+attr)
            setattr(window, 'sl_'+attr, slider)
    window.combo_fnrgf_mode = ScrollSafeComboBox()
    window.combo_fnrgf_mode.addItem('Continuous · observed support', 'continuous')
    window.combo_fnrgf_mode.addItem('Reference-compatible', 'legacy')
    window.combo_fnrgf_mode.setToolTip('Continuous fits use observed angular support and interpolated radial models. Compatible mode retains the original reference conventions.')
    window.sec_fnrgf.content_layout.insertWidget(0, window.combo_fnrgf_mode)
    window.combo_fnrgf_mode.currentIndexChanged.connect(window.dispatch_pipeline_request_if_auto)
    def mode_changed():
        continuous = window.combo_fnrgf_mode.currentData() == 'continuous'
        for name in ('smooth', 'fade', 'ridge', 'robust'):
            slider = getattr(window, 'sl_fnrgf_'+name)
            slider.parameter_row.setEnabled(continuous)
    window.combo_fnrgf_mode.currentIndexChanged.connect(mode_changed)
    mode_changed()
    window.chk_rhef_symmetric = QCheckBox('Use the same exponent for both tails')
    window.chk_rhef_symmetric.setChecked(True)
    window.chk_rhef_symmetric.setToolTip('Link the upper-tail exponent to the main Upsilon exponent. Uncheck for independent tail control.')
    window.chk_rhef_symmetric.toggled.connect(window.dispatch_pipeline_request_if_auto)
    window.sec_rhef.content_layout.addWidget(window.chk_rhef_symmetric)
    def update_rhef_controls():
        continuous = window.combo_rhef_mode.currentData() == 'continuous'
        for name in ('min_count', 'quantiles'):
            getattr(window, 'sl_rhef_'+name).setEnabled(continuous)
        window.sl_rhef_upsilon_high.setEnabled(not window.chk_rhef_symmetric.isChecked())
    window.chk_rhef_symmetric.toggled.connect(update_rhef_controls)
    window.combo_rhef_mode.currentIndexChanged.connect(update_rhef_controls)
    update_rhef_controls()
    window.chk_tangential_outer = QCheckBox('Limit outer radius')
    window.chk_tangential_outer.setToolTip('Enable an outer processing boundary; otherwise process to the observed image edges.')
    window.sec_tangential.content_layout.addWidget(window.chk_tangential_outer)
    def sync_tangential():
        window.sl_tangential_outer.setMinimum(window.sl_tangential_inner.value()+1)
        window.sl_tangential_outer.setEnabled(window.chk_tangential_outer.isChecked())
    window.chk_tangential_outer.toggled.connect(sync_tangential)
    window.chk_tangential_outer.toggled.connect(window.dispatch_pipeline_request_if_auto)
    window.sl_tangential_inner.valueChanged.connect(sync_tangential)
    sync_tangential()
    window.sl_mgn_sigmas, window.sl_mgn_weights = [], []
    for index, sigma in enumerate((1.25, 2.5, 5, 10, 20, 40)):
        for collection, title, maximum, default, help_text in (
            (window.sl_mgn_sigmas, 'sigma (native px)', 12800, round(sigma*100), 'Gaussian scale in original-image pixels. Reduced proportionally for fast preview; used directly at full resolution.'),
            (window.sl_mgn_weights, 'weight', 200, 100, 'Nonnegative weight of this local MGN scale. Zero disables its contribution; normalization still divides by six scales.')):
            slider, _ = create_slider_float(f'Scale {index+1} {title}', 25 if collection is window.sl_mgn_sigmas else 0,
                                            maximum, default, 100., window.sec_mgn.content_layout,
                                            tooltip=help_text, on_release_callback=window.dispatch_pipeline_request_if_auto)
            collection.append(slider)
    window.sl_wow_bilateral, _ = create_slider_float('Bilateral intensity scale', 1, 50, 10, 10.,
        window.sec_wow.content_layout, tooltip='Positive intensity sensitivity for the bilateral WOW backend (0.1 to 5); enabled only in edge-aware mode.',
        on_release_callback=window.dispatch_pipeline_request_if_auto)
    window.sl_wow_noise_floor, _ = create_slider_float('AEL noise floor', 0, 100, 30, 10.,
        window.sec_wow.content_layout, tooltip='AEL regularization multiplier of measured noise in the whitening denominator. This is not a significance threshold.',
        on_release_callback=window.dispatch_pipeline_request_if_auto)


def collect_controls(window):
    params = {'larson_sekanina_radial': 0.}
    for specs in CONTROLS.values():
        for attr, key, label, minimum, maximum, default, divisor, help_text in specs:
            value = getattr(window, 'sl_'+attr).value()/divisor
            params[key] = int(value) if divisor == 1 else value
    params['rhef_upsilon_high'] = window.sl_rhef_upsilon_high.value()
    if window.chk_rhef_symmetric.isChecked():
        params['rhef_upsilon_high'] = window.sl_rhef_upsilon.value()
    if not window.chk_tangential_outer.isChecked():
        params['tangential_outer'] = 0.
    params['fnrgf_mode'] = window.combo_fnrgf_mode.currentData()
    params['mgn_sigmas'] = tuple(sl.value()/100 for sl in window.sl_mgn_sigmas)
    params['mgn_weights'] = tuple(sl.value()/100 for sl in window.sl_mgn_weights)
    params['wow_bilateral'] = window.sl_wow_bilateral.value()/10 if window.combo_wow_bilateral.currentIndex() else None
    params['wow_mode'] = 'ael_bilateral' if window.combo_wow_bilateral.currentIndex() == 2 else 'native'
    params['wow_noise_floor'] = window.sl_wow_noise_floor.value()/10
    return params


def set_control_visible(control, visible):
    """Keep each factory slider's title and displayed value with its track."""
    if hasattr(control, "parameter_row"):
        control.parameter_row.setVisible(visible)
    control.setVisible(visible)
    if hasattr(control, 'title_label'):
        control.title_label.setVisible(visible)
        control.value_label.setVisible(visible)


def add_advanced_mode(window, header_layout):
    window.chk_advanced = QCheckBox('Advanced mode')
    window.chk_advanced.setToolTip('Show all filter parameters. Hidden settings remain active. Basic WOW noise edits apply to every scale; basic Upsilon edits link both tails.')
    header_layout.addWidget(window.chk_advanced)
    window.sl_wow_noise, _ = create_slider_float(
        'Noise threshold (all scales, sigma)', 0, 100, 0, 10.,
        window.sec_wow.content_layout,
        tooltip='Apply this noise threshold to every native wavelet scale. Zero disables noise suppression. Editing replaces individual advanced thresholds.',
        on_release_callback=window.dispatch_pipeline_request_if_auto)
    window.lbl_advanced_values = QLabel('Individual WOW thresholds or separate RHEF tails remain active. Edit the basic control to link them again.')
    window.lbl_advanced_values.setWordWrap(True)
    window.lbl_advanced_values.setStyleSheet('color: #aaaaaa; font-size: 10px;')
    window.lbl_advanced_values.setToolTip('Switching modes preserves parameters. Advanced WOW and RHEF values remain active until their basic control is edited.')
    header_layout.addWidget(window.lbl_advanced_values)
    advanced = [window.sl_mgn_trunc, *window.sl_mgn_sigmas, *window.sl_mgn_weights,
                window.sl_wow_scales, *window.sl_wow_denoise,
                window.sl_wow_bilateral,
                window.combo_rhef_mode, window.sl_rhef_rad, window.sl_rhef_bin,
                window.chk_rhef_symmetric, window.chk_tangential_outer,
                window.sl_achf_boost, window.sl_achf_background,
                window.chk_statistics_lunar, window.chk_statistics_bright,
                window.sl_statistics_guard, window.sl_statistics_percentile,
                window.sl_statistics_outer]
    for family, specs in CONTROLS.items():
        for attr, *_ in specs:
            if attr not in ('tangential_arc', 'tangential_denoise', 'larson_sekanina_angular'):
                advanced.append(getattr(window, 'sl_' + attr))

    def update_visibility(checked):
        for control in advanced:
            set_control_visible(control, checked)
        set_control_visible(window.sl_wow_noise, not checked)
        set_parameter_title(window.sl_rhef_upsilon.title_label, 'Lower-tail Upsilon' if checked else 'Upsilon (both tails)')
        update_custom_values()

    def update_custom_values():
        mixed_noise = any(slider.value() != window.sl_wow_noise.value()
                          for slider in window.sl_wow_denoise if slider.isEnabled())
        window.lbl_advanced_values.setVisible(
            not window.chk_advanced.isChecked() and
            (mixed_noise or not window.chk_rhef_symmetric.isChecked()))

    def apply_noise(value):
        for slider in window.sl_wow_denoise:
            blocked = slider.blockSignals(True)
            slider.setValue(value)
            slider.blockSignals(blocked)
            update_slider_display(slider)
        window.on_filter_slider_released(window.sec_wow)
        update_custom_values()

    def apply_upsilon(_):
        if not window.chk_advanced.isChecked():
            window.sl_rhef_upsilon_high.setValue(window.sl_rhef_upsilon.value())
            window.chk_rhef_symmetric.setChecked(True)

    window.sl_wow_noise.valueChanged.connect(apply_noise)
    window.sl_rhef_upsilon.valueChanged.connect(apply_upsilon)
    for slider in window.sl_wow_denoise:
        slider.valueChanged.connect(update_custom_values)
    window.sl_wow_scales.valueChanged.connect(update_custom_values)
    window.chk_rhef_symmetric.toggled.connect(update_custom_values)
    window.chk_advanced.toggled.connect(update_visibility)
    update_visibility(False)


def add_achf_variants(window):
    """One persistent panel per AEL variant; switching never overwrites edits."""
    from PySide6.QtWidgets import QWidget, QVBoxLayout
    from core.ael_achf import AEL_PRESETS
    window.achf_ael_controls = {}
    for variant, preset in AEL_PRESETS.items():
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0,0,0,0)
        controls = dict(panel=panel)
        controls['enabled']=QCheckBox('Include in composition')
        controls['enabled'].setToolTip('Enable this variant independently of the other ACHF layers; cached results are retained when disabled.')
        controls['enabled'].toggled.connect(window.on_filter_toggled)
        layout.addWidget(controls['enabled'])
        controls['opacity'], _=create_slider('Opacity (%)',0,100,50,layout,
            tooltip='Overlay opacity; changing this only recomposes cached layers.')
        controls['opacity'].setProperty('mix_only',True)
        controls['opacity'].valueChanged.connect(window.on_layer_mix_changed)
        if 'sigmas' in preset:
            controls['sigmas'] = []
            for i, value in enumerate(preset['sigmas']):
                slider, _ = create_slider_float(f'Scale {i+1} sigma (native px)',1,1280,round(10*value),10.,layout,
                    tooltip='Gaussian sigma at full source resolution. Fast preview adapts the footprint.',
                    on_release_callback=window.dispatch_pipeline_request_if_auto)
                controls['sigmas'].append(slider)
        else:
            controls['angular_sigma'], _ = create_slider_float('Angular sigma (degrees)',1,300,10,10.,layout,
                tooltip='Gaussian angular width along circles around the reference center, in degrees.',
                on_release_callback=window.dispatch_pipeline_request_if_auto)
        controls['outer_sigma'], _ = create_slider_float('Final smoothing (native px)',0,640,
            round(10*preset['outer_sigma']),10.,layout,
            tooltip='Gaussian sigma after detail extraction; zero disables it.',
            on_release_callback=window.dispatch_pipeline_request_if_auto)
        window.achf_ael_controls[variant] = controls
        window.sec_achf.content_layout.addWidget(panel)


def collect_achf_variants(window):
    result = {}
    for variant, controls in window.achf_ael_controls.items():
        settings = dict(strength=100,outer_sigma=controls['outer_sigma'].value()/10.,
                        opacity=controls['opacity'].value(),enabled=controls['enabled'].isChecked())
        if 'sigmas' in controls:
            settings['sigmas'] = [slider.value()/10. for slider in controls['sigmas']]
        else:
            settings['angular_sigma'] = controls['angular_sigma'].value()/10.
        result[variant] = settings
    return result


def add_layer_opacities(window):
    """Opacity controls composition; only Linear Light retains a separate Gain."""
    from .factories import create_slider
    for name in ('nrgf','fnrgf','rhef','mgn','wow','tangential','larson_sekanina','achf'):
        layout=(window.achf_adaptive_panel.layout() if name == 'achf'
                else getattr(window,'sec_'+name).content_layout)
        if name == 'larson_sekanina':
            gain=window.sl_larson_sekanina_str
            help_text='Gain scales the signed residual before Linear Light clipping; opacity controls the mixture after clipping.'
            for control in (gain,gain.title_label,gain.value_label):
                control.setToolTip(help_text)
        mode='Multiply' if name in ('nrgf', 'fnrgf') else 'Linear Light' if name == 'larson_sekanina' else 'Overlay'
        slider,_=create_slider('Opacity (%)',0,100,40 if name == 'nrgf' else 50,layout,
            tooltip=f'{mode} layer opacity. Changes only the composition; preserves calculated filters.')
        slider.setProperty('mix_only',True)
        slider.valueChanged.connect(window.on_layer_mix_changed)
        row=slider.parameter_row
        layout.removeWidget(row)
        layout.insertWidget(0,row)
        setattr(window,'sl_'+name+'_opacity',slider)
    window.chk_achf_adaptive=QCheckBox('Include Adaptive in composition')
    window.chk_achf_adaptive.setToolTip('Include the adaptive ACHF layer; the other variants can be enabled independently.')
    window.chk_achf_adaptive.setChecked(True)
    window.chk_achf_adaptive.toggled.connect(window.on_filter_toggled)
    window.achf_adaptive_panel.layout().insertWidget(0,window.chk_achf_adaptive)
