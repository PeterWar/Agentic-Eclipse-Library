"""Main application window: EclipseProcessorApp."""

import os
from typing import Optional, Tuple

import cv2
import numpy as np
from PySide6.QtCore import QThread, QTimer, Signal, Qt, QSignalBlocker
from PySide6.QtGui import QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListView,
    QStyledItemDelegate,
    QMainWindow,
    QPushButton,
    QProgressBar,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config import APP_VERSION, CPU_CORES
from core.filters import FilterWorker
from core.pipeline import prepare_parameters
from core.presentation import composition_settings
from core.layer_engine import engine_for
from gui.background_tasks import TaskThread, load_source, render_snapshot
from gui.export_worker import ExportThread
from gui.image_view import ImageView
from gui.background_controls import BackgroundExtraction
from core.colour import neutralize_tse, set_luminosity
from core.result_cache import parameter_signature
from core.project_settings import read_settings, write_settings
from gui.project_settings import capture_settings, restore_settings, validate_settings, initialize_filter_defaults, reset_filter_defaults
from gui.filter_controls import add_controls, collect_controls, add_advanced_mode, add_achf_variants, collect_achf_variants, add_layer_opacities
from gui.components import BUTTON_STYLE, CHECKBOX_STYLE, CollapsibleSection, FullRowCheckBox, InWindowTooltips, ScrollSafeComboBox
from gui.factories import (
    create_filter_group,
    create_slider,
    update_slider_display,
    create_slider_float,
    create_stepper_input,
    create_dyadic_slider,
)
from utils.helpers import application_icon_path, recommended_radial_bins


class EclipseProcessorApp(QMainWindow):
    """Main application window for solar eclipse processing."""

    request_processing_signal = Signal(np.ndarray, dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Eclipse Image Processor v{APP_VERSION}")
        self.resize(1180, 780)
        self.setMinimumSize(960, 600)

        self.setWindowIcon(QIcon(application_icon_path()))

        self.raw_image: Optional[np.ndarray] = None
        self.processed_image: Optional[np.ndarray] = None
        self.full_raw_image: Optional[np.ndarray] = None
        self.preview_image: Optional[np.ndarray] = None
        self.source_path: Optional[str] = None
        self.full_source_rgb: Optional[np.ndarray] = None
        self.source_rgb_white = 1.
        self._display_reference_source = None
        self._display_bounds = None
        self._colour_cache = None
        self._preview_colour_cache = None
        self._colour_revision = 0
        self._full_cache = None
        self._export_thread = None
        self._load_thread = None
        self._geometry_thread = None
        self._presentation_thread = None
        self._presentation_request = None
        self._native_display_revision = None
        self._native_filter_revision = None
        self._presentation_revision = 0
        self._closing = False
        self._running_full_job = False
        self._running_signature = None
        self._running_full_source = None
        self.preview_scale: float = 1.0
        self.show_original_mode: bool = False
        self.auto_calculate: bool = True
        self.is_processing: bool = False
        self.has_pending_request: bool = False
        # Only one worker job runs at a time; revisions reject obsolete results
        # while cooperative cancellation stops superseded work at safe checkpoints.
        self._preview_revision = 0
        self._running_revision = None
        self._running_image = None
        self._pending_manual = False
        self.recalculation_timer = QTimer(self)
        self.recalculation_timer.setSingleShot(True)
        self.recalculation_timer.setInterval(650)
        self.recalculation_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.recalculation_timer.timeout.connect(self.dispatch_pipeline_request)
        self.presentation_timer = QTimer(self)
        self.presentation_timer.setSingleShot(True)
        self.presentation_timer.setInterval(100)
        self.presentation_timer.timeout.connect(self.render_matrix_to_screen)

        self.persistent_thread = QThread()
        self.filter_worker = FilterWorker()
        self.filter_worker.moveToThread(self.persistent_thread)
        self.request_processing_signal.connect(self.filter_worker.process_pipeline)
        self.filter_worker.finished.connect(self.on_processing_finished)
        self.filter_worker.failed.connect(self.on_processing_failed)
        self.filter_worker.cancelled.connect(self.on_processing_cancelled)
        self.persistent_thread.finished.connect(self._finish_close)
        self.persistent_thread.start()

        self.background=BackgroundExtraction(self)
        self._build_ui()
        initialize_filter_defaults(self)
        for checkbox in self.findChildren(QCheckBox):
            checkbox.setStyleSheet(CHECKBOX_STYLE)
            checkbox.setCursor(Qt.CursorShape.PointingHandCursor)
        for button in self.findChildren(QPushButton):
            if not button.isFlat():
                button.setStyleSheet(BUTTON_STYLE)
        self.in_window_tooltips = InWindowTooltips(self)

    def _build_ui(self):
        """Build the main user interface."""
        main_widget = QWidget()
        main_widget.setObjectName("centralWidget")
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        viewer_panel=QWidget()
        viewer_layout=QVBoxLayout(viewer_panel)
        viewer_layout.setContentsMargins(0,0,0,0)
        viewer_layout.setSpacing(6)
        zoom_row=QHBoxLayout()
        view_label=QLabel('View:')
        view_label.setToolTip('Preview magnification: Fit, 100% or 200% of native pixels.')
        zoom_row.addWidget(view_label)
        self.zoom_buttons=QButtonGroup(self)
        self.zoom_buttons.setExclusive(True)
        for label,zoom in (('Fit',None),('100%',1),('200%',2)):
            button=QPushButton(label)
            button.setCheckable(True)
            button.setEnabled(False)
            button.setToolTip('Fit the complete image; subsequent edits use fast processing unless native verification is checked.' if zoom is None else
                              f'{label}: native image pixels relative to physical screen pixels. Drag to pan; native filters are calculated only when needed.')
            button.clicked.connect(lambda checked,zoom=zoom:self.set_preview_zoom(zoom))
            self.zoom_buttons.addButton(button,0 if zoom is None else zoom)
            zoom_row.addWidget(button)
        self.zoom_buttons.button(0).setChecked(True)
        zoom_row.addStretch()
        self.lbl_view_state=QLabel('Open an image')
        self.lbl_view_state.setToolTip('Current preview magnification and native-resolution availability.')
        zoom_row.addWidget(self.lbl_view_state)
        self.zoom_toolbar=QWidget()
        self.zoom_toolbar.setLayout(zoom_row)
        viewer_layout.addWidget(self.zoom_toolbar)
        self.image_label=ImageView()
        self.image_label.circle_center_requested.connect(self.on_circle_center_requested)
        self.image_label.view_changed.connect(self._update_view_scale_label)
        self.image_label.setToolTip('Fit shows the complete image. 100% and 200% inspect native pixels: drag, scroll or use arrow keys to pan. Ctrl-click (Command-click on macOS) moves the disk center.')
        viewer_layout.addWidget(self.image_label,stretch=1)
        main_layout.addWidget(viewer_panel,stretch=3)

        right_container = QWidget()
        self.control_sidebar = right_container
        right_container.setFixedWidth(380)
        right_container.setStyleSheet("background-color: #2b2b2b; border-radius: 6px;")
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(6, 6, 6, 6)
        right_layout.setSpacing(6)

        top_header_panel = QFrame()
        top_header_panel.setStyleSheet("QFrame { background-color: #303030; border: 1px solid #3c3c3c; border-radius: 4px; }")
        top_header_layout = QVBoxLayout(top_header_panel)
        top_header_layout.setContentsMargins(10, 8, 10, 8)
        top_header_layout.setSpacing(6)

        self.status_label = QLabel(f"Status: Ready ({CPU_CORES} CPU cores available)")
        self.status_label.setToolTip("Processing, pending changes and export status. Ready means the latest requested preview has completed.")
        self.status_label.setStyleSheet("color: #9cdcfe; font-weight: bold; font-size: 11px;")
        top_header_layout.addWidget(self.status_label)

        btn_row = QHBoxLayout()
        self.btn_load = QPushButton("Open Image / Settings")
        self.btn_load.setToolTip("Open a settings JSON to restore its original image and all adjustments, or open TIFF, FITS, XISF, PNG, JPEG or BMP. Filters use monochrome intensity; source RGB is retained for preview and export. Missing samples remain excluded.")
        self.btn_load.clicked.connect(self.load_image_action)
        btn_row.addWidget(self.btn_load)

        self.btn_compare = QPushButton("View Original")
        self.btn_compare.setCheckable(True)
        self.btn_compare.setToolTip("Temporarily bypass detail filters to inspect the working input with the selected PSB presentation or un-stretched view. Enabled background equalization and Calibrate color apply to both views. This comparison does not change filter settings or the export.")
        self.btn_compare.clicked.connect(self.toggle_compare_mode)
        btn_row.addWidget(self.btn_compare)

        self.btn_auto_calc = QPushButton("Auto Calculate")
        self.btn_auto_calc.setCheckable(True)
        self.btn_auto_calc.setChecked(True)
        self.btn_auto_calc.setToolTip("Recalculate automatically after a 650 ms pause in geometry or filter adjustments")
        self.btn_auto_calc.clicked.connect(self.toggle_auto_calc_mode)
        btn_row.addWidget(self.btn_auto_calc)

        self.btn_recalc = QPushButton("🔄")
        self.btn_recalc.setFixedSize(32, 26)
        self.btn_recalc.setToolTip("Update the preview with the current settings. Reuse cached layers and calculate only missing or changed filters. If busy, queue the latest settings.")
        self.btn_recalc.clicked.connect(self.dispatch_pipeline_request)
        self.btn_recalc.setVisible(False)
        btn_row.addWidget(self.btn_recalc)

        top_header_layout.addLayout(btn_row)
        self.chk_verify_preview = QCheckBox('Full-resolution verification preview')
        self.chk_verify_preview.setChecked(False)
        self.chk_verify_preview.setToolTip('Use native filter calculations even in Fit view. 100% and 200% request native resolution automatically. Export reuses native layers when settings match. Disable and use Fit for fast approximate editing.')
        self.chk_verify_preview.toggled.connect(self.dispatch_pipeline_request_if_auto)
        top_header_layout.addWidget(self.chk_verify_preview)
        right_layout.addWidget(top_header_panel)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        control_panel = QWidget()
        control_panel.setStyleSheet("background-color: transparent;")
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(2, 2, 6, 2)
        control_layout.setSpacing(6)

        scroll_area.setWidget(control_panel)
        right_layout.addWidget(scroll_area, stretch=1)
        main_layout.addWidget(right_container)

        self.lbl_input_linearity = QLabel()
        self.lbl_input_linearity.setToolTip("Input transfer-function declaration; linearity is assumed unless confirmed by the source. This does not undo a previous stretch.")
        self.lbl_input_linearity.setWordWrap(False)
        self.lbl_input_linearity.setStyleSheet("color: #e5a00d; font-size: 11px;")
        self.lbl_input_linearity.setVisible(False)
        self._build_geometry_section(control_layout)
        self.background.build(control_layout)
        self._build_filters_section(control_layout)
        add_layer_opacities(self)
        for section in (self.sec_nrgf, self.sec_fnrgf, self.sec_mgn, self.sec_wow, self.sec_rhef,
                        self.sec_tangential, self.sec_larson_sekanina, self.sec_achf):
            for slider in section.findChildren(QSlider):
                if slider.property("mix_only"):
                    continue
                slider.valueChanged.connect(
                    lambda value, section=section: self.on_filter_slider_released(section))
        self._build_presentation_section(control_layout)
        top_header_layout.insertWidget(2, self.combo_input_state)
        top_header_layout.insertWidget(3, self.lbl_input_linearity)
        top_header_layout.addWidget(self.chk_calibrate_colour)
        add_advanced_mode(self, top_header_layout)
        top_header_layout.addWidget(self.lbl_colour_hint)
        self.sl_wow_scales.valueChanged.connect(lambda _: self.update_wow_controls())
        self.update_wow_controls()
        section_help = {
            self.sec_geo: "Set the disk center and reference radius in native image pixels for radial filtering and the circle overlay.",
            self.sec_nrgf: "Normalizing Radial Graded Filter (AEL): continuous annular brightness and spread on linear input; independent Multiply layer. Undefined annuli stay transparent.",
            self.sec_fnrgf: "Fourier Normalizing Radial Gradient Filter: model annular brightness and spread as functions of angle.",
            self.sec_mgn: "Multi-scale Gaussian Normalization: combine local contrast at several scales with a global gamma image.",
            self.sec_wow: "Wavelets Optimized Whitening: normalize multiscale contrast with optional noise suppression.",
            self.sec_rhef: "Radial Histogram Equalization: map intensities to ranks within radial distributions.",
            self.sec_tangential: "Tangential detail: subtract an angular blur with observed support and retain the Cartesian base.",
            self.sec_larson_sekanina: "Larson-Sekanina: extract signed rotational detail from the shared working input using the reference disk center. Radial increment is fixed at zero; the layer uses Linear Light.",
            self.sec_achf: "ACHF detail layers: Adaptive uses accepted opposite neighbor pairs; AEL ISO 01, ISO 04 and Angular use log-luminance residuals. Enable variants independently.",
        }
        for section, description in section_help.items():
            section.toggle_btn.setToolTip(description + " Click to expand or collapse controls; this does not enable the stage.")
            if section.chk_active is not None:
                section.chk_active.setToolTip(description + " Enable or bypass this stage without resetting its controls.")

    def _build_geometry_section(self, layout: QVBoxLayout):
        """Build the solar disk geometry section."""
        self.sec_geo = CollapsibleSection("SOLAR DISK GEOMETRY", has_checkbox=False, is_expanded=True)
        coord_layout = QHBoxLayout()
        self.txt_x = create_stepper_input(
            "Center X:", "0", coord_layout, "Horizontal (X) position of the lunar disk center in FULL-RESOLUTION pixels",
            on_change_callback=self.dispatch_pipeline_request_if_auto
        )
        self.txt_y = create_stepper_input(
            "Center Y:", "0", coord_layout, "Vertical (Y) position of the lunar disk center in FULL-RESOLUTION pixels",
            on_change_callback=self.dispatch_pipeline_request_if_auto
        )
        self.txt_r = create_stepper_input(
            "Radius R:", "300", coord_layout, "Radius of the lunar/solar disk in FULL-RESOLUTION pixels",
            on_change_callback=self.dispatch_pipeline_request_if_auto
        )
        self.sec_geo.content_layout.addLayout(coord_layout)

        self.lbl_scale_info = QLabel("Scale: 1.0x (100% resolution)")
        self.lbl_scale_info.setToolTip("Pipeline scale compares native image pixels with preview pixels; display scale compares native pixels with the fitted on-screen image. Geometry is entered in native pixels.")
        self.lbl_scale_info.setStyleSheet("color: #aaaaaa; font-size: 10px;")
        self.sec_geo.content_layout.addWidget(self.lbl_scale_info)

        self.txt_x.textChanged.connect(self.trigger_circle_redraw)
        self.txt_y.textChanged.connect(self.trigger_circle_redraw)
        self.txt_r.textChanged.connect(self.trigger_circle_redraw)
        for field in (self.txt_x, self.txt_y, self.txt_r):
            field.textChanged.connect(self._on_geometry_changed)

        self.btn_auto_moon = QPushButton("Auto-detect Lunar Disk")
        self.btn_auto_moon.setToolTip("Enclose a closed, nearly circular missing-data region, or use robust contrast normalization, Hough detection and limb refinement. The enclosing radius protects the data gap and is not necessarily the physical lunar radius.")
        self.btn_auto_moon.clicked.connect(self.auto_detect_moon_action)
        detection_row = QHBoxLayout()
        detection_row.addWidget(self.btn_auto_moon, 1)
        self.btn_disk_overlay = QPushButton('Disk overlay')
        self.btn_disk_overlay.setCheckable(True)
        self.btn_disk_overlay.setChecked(True)
        self.btn_disk_overlay.setToolTip('Show or hide the red lunar circle and center cross. Visible by default when opening an image. This changes only the overlay, not the processing or export.')
        self.btn_disk_overlay.toggled.connect(self.image_label.set_disk_overlay_visible)
        detection_row.addWidget(self.btn_disk_overlay)
        self.sec_geo.content_layout.addLayout(detection_row)
        self.chk_statistics_lunar = QCheckBox('Exclude lunar disk from filter statistics')
        self.chk_statistics_lunar.setChecked(True)
        self.chk_statistics_lunar.setToolTip('Keep finite lunar pixels unchanged while excluding them from enhancement statistics. This is separate from missing-data validity. Masked WOW uses the observed-support starlet variant.')
        self.chk_statistics_bright = QCheckBox('Exclude bright limb samples from statistics')
        self.chk_statistics_bright.setToolTip('Exclude the brightest samples in a selected limb annulus from statistics and leave those input pixels unchanged. This brightness heuristic does not identify prominences scientifically.')
        for checkbox in (self.chk_statistics_lunar, self.chk_statistics_bright):
            checkbox.toggled.connect(self.dispatch_pipeline_request_if_auto)
            self.sec_geo.content_layout.addWidget(checkbox)
        self.sl_statistics_guard, _ = create_slider_float('Lunar guard (preview px)', 0, 640, 0, 10., self.sec_geo.content_layout,
            tooltip='Extra statistical exclusion beyond the reference lunar radius, scaled on export.', on_release_callback=self.dispatch_pipeline_request_if_auto)
        self.sl_statistics_percentile, _ = create_slider_float('Bright-limb percentile', 900, 1000, 995, 10., self.sec_geo.content_layout,
            tooltip='Exclude samples above this percentile within the selected limb annulus. 100 excludes none.', on_release_callback=self.dispatch_pipeline_request_if_auto)
        self.sl_statistics_outer, _ = create_slider_float('Limb annulus outer radius', 11, 30, 15, 10., self.sec_geo.content_layout,
            tooltip='Outer radius of the bright-sample statistics annulus in reference disk radii; its inner radius is one.', on_release_callback=self.dispatch_pipeline_request_if_auto)
        for slider in (self.sl_statistics_guard, self.sl_statistics_percentile, self.sl_statistics_outer):
            slider.valueChanged.connect(self.dispatch_pipeline_request_if_auto)
        self.chk_statistics_lunar.toggled.connect(self.sl_statistics_guard.setEnabled)
        self.sl_statistics_guard.setEnabled(self.chk_statistics_lunar.isChecked())
        for slider in (self.sl_statistics_percentile, self.sl_statistics_outer):
            self.chk_statistics_bright.toggled.connect(slider.setEnabled)
            slider.setEnabled(self.chk_statistics_bright.isChecked())
        layout.addWidget(self.sec_geo)

    def _build_filters_section(self, layout: QVBoxLayout):
        """Build radial, multiscale and sharpening filter sections."""
        radial_group = create_filter_group("RADIAL ENHANCEMENT", layout)
        self.sec_nrgf = CollapsibleSection("NRGF", has_checkbox=True, is_expanded=False, is_active=False)
        self.sl_nrgf_rad, _ = create_slider_float(
            'Inner radius (R)', 10, 25, 10, 10., self.sec_nrgf.content_layout,
            tooltip='Exclude samples at or inside this reference disk radius from NRGF statistics and output. The whole observed rectangle beyond it is processed.',
            on_release_callback=self.dispatch_pipeline_request_if_auto)
        self.sl_nrgf_bin_px, _ = create_slider_float(
            'Ring width (native px)', 5, 320, 20, 10., self.sec_nrgf.content_layout,
            tooltip='Annular measurement width at original resolution. Fast preview scales it to the same physical footprint; no image smoothing.',
            on_release_callback=self.dispatch_pipeline_request_if_auto)
        self.combo_nrgf_statistics = ScrollSafeComboBox()
        self.combo_nrgf_statistics.addItems(['Median / MAD (AEL)', 'Mean / STD'])
        self.combo_nrgf_statistics.setToolTip('Robust AEL statistics or mean/standard deviation. Both use the continuous radial profile; only observed samples contribute.')
        self.combo_nrgf_statistics.currentIndexChanged.connect(self.dispatch_pipeline_request_if_auto)
        self.sec_nrgf.content_layout.addWidget(self.combo_nrgf_statistics)
        self.sec_nrgf.toggled_active.connect(self.on_filter_toggled)
        radial_group.addWidget(self.sec_nrgf)
        self.sec_fnrgf = CollapsibleSection("FNRGF", has_checkbox=True, is_expanded=False, is_active=False)
        self.sl_fnrgf_ord, _ = create_slider(
            "Fourier order", 1, 24, 6, self.sec_fnrgf.content_layout,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_fnrgf),
            tooltip="Highest angular Fourier harmonic in the annular brightness and spread models. Higher orders follow finer angular variations; they do not guarantee additional real detail."
        )
        self.sl_fnrgf_seg, _ = create_dyadic_slider(
            "Angular segments", 4, 10, 4, self.sec_fnrgf.content_layout,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_fnrgf),
            tooltip="At least the smallest power of two >= 2*Fourier Order+1. Higher manually chosen values are retained when the order changes."
        )
        self.sl_fnrgf_cut, _ = create_slider(
            "Remove coefficients", 0, 7, 0, self.sec_fnrgf.content_layout,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_fnrgf),
            tooltip="Remove this many highest-order model coefficients. Zero retains them all; the maximum is Fourier order + 1."
        )
        def sync_fnrgf_limits(_=None):
            order = self.sl_fnrgf_ord.value()
            self.sl_fnrgf_cut.setMaximum(order + 1)
            exponent = (2 * order).bit_length()
            self.sl_fnrgf_seg.setMinimum(exponent)
            if self.sl_fnrgf_seg.value() < exponent:
                self.sl_fnrgf_seg.setValue(exponent)

        self.sl_fnrgf_ord.valueChanged.connect(sync_fnrgf_limits)
        sync_fnrgf_limits()
        self.sl_fnrgf_rad, _ = create_slider(
            "Inner radius (R)", 5, 25, 10, self.sec_fnrgf.content_layout,
            divisor=10,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_fnrgf),
            tooltip="Process only above this radius, in disk radii"
        )
        self.sl_fnrgf_rmax, _ = create_slider(
            "Outer radius (R)", 15, 60, 30, self.sec_fnrgf.content_layout,
            divisor=10,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_fnrgf),
            tooltip="Outer boundary in disk radii. The upper limit follows the farthest image corner; verify coverage when the disk is off-center."
        )
        self.sl_fnrgf_rmax.setMinimum(self.sl_fnrgf_rad.value() + 1)
        self.sl_fnrgf_rad.valueChanged.connect(
            lambda value: self.sl_fnrgf_rmax.setMinimum(value + 1))
        self.sl_fnrgf_bin_px, _ = create_slider(
            "Ring width (px)", 1, 32, 4, self.sec_fnrgf.content_layout,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_fnrgf),
            tooltip="Ring width in pixels at each processing resolution (default 4). Export increases the ring count to retain this width. For logarithmic spacing this is the inner-ring width; outer rings are wider."
        )

        w_row = QHBoxLayout()
        w_lbl = QLabel("Spread estimator")
        w_lbl.setFixedWidth(126)
        w_lbl.setStyleSheet("color: #aaa; font-size: 11px;")
        self.combo_fnrgf_width = ScrollSafeComboBox()
        self.combo_fnrgf_width.addItems(["STD", "MAD"])
        self.combo_fnrgf_width.setCurrentIndex(1)
        self.combo_fnrgf_width.setToolTip("Estimate sector spread using standard deviation or 1.4826 times median absolute deviation. MAD makes the spread less sensitive to outliers; the brightness model still uses sector means.")
        self.combo_fnrgf_width.currentIndexChanged.connect(lambda _: self.dispatch_pipeline_request_if_auto())
        w_lbl.setToolTip(self.combo_fnrgf_width.toolTip())
        w_row.addWidget(w_lbl)
        w_row.addWidget(self.combo_fnrgf_width)
        self.sec_fnrgf.content_layout.addLayout(w_row)

        b_row = QHBoxLayout()
        b_lbl = QLabel("Radial spacing")
        b_lbl.setFixedWidth(126)
        b_lbl.setStyleSheet("color: #aaa; font-size: 11px;")
        self.combo_fnrgf_binning = ScrollSafeComboBox()
        self.combo_fnrgf_binning.addItems(["Linear", "Log"])
        self.combo_fnrgf_binning.setCurrentIndex(1)
        self.combo_fnrgf_binning.setToolTip("Linear bins have equal radial widths. Log-spaced bins are finer near the inner boundary and wider farther out.")
        self.combo_fnrgf_binning.currentIndexChanged.connect(lambda _: self.dispatch_pipeline_request_if_auto())
        b_lbl.setToolTip(self.combo_fnrgf_binning.toolTip())
        b_row.addWidget(b_lbl)
        b_row.addWidget(self.combo_fnrgf_binning)
        self.sec_fnrgf.content_layout.addLayout(b_row)

        self.sl_fnrgf_mask, _ = create_slider(
            "Limb protection (%)", 0, 100, 0, self.sec_fnrgf.content_layout,
            on_release_callback=self.dispatch_pipeline_request_if_auto,
            tooltip="Protect the working input near r/R = 1 with a triangular band from 0.95 to 1.05. Zero disables protection; 100 removes FNRGF at the band center. This is not the missing-data mask."
        )
        self.sec_fnrgf.toggled_active.connect(self.on_filter_toggled)
        radial_group.addWidget(self.sec_fnrgf)

        histogram_group = create_filter_group("RADIAL HISTOGRAM EQUALIZATION", layout)
        self.sec_rhef = CollapsibleSection("RHEF", has_checkbox=True, is_expanded=False, is_active=False)
        self.combo_rhef_mode = ScrollSafeComboBox()
        self.combo_rhef_mode.addItem("Legacy / compatible", "legacy")
        self.combo_rhef_mode.addItem("Continuous global", "continuous")
        self.combo_rhef_mode.setCurrentIndex(1)
        self.combo_rhef_mode.setToolTip("Legacy ranks samples independently within rings. Continuous global interpolates positive log-intensity quantiles across populated neighboring rings; nonpositive and sparse samples retain their input values.")
        self.combo_rhef_mode.currentIndexChanged.connect(lambda _: self.dispatch_pipeline_request_if_auto())
        self.sec_rhef.content_layout.addWidget(self.combo_rhef_mode)
        self.sl_rhef_rad, _ = create_slider(
            "Application Radius (disk radii)", 0, 100, 10, self.sec_rhef.content_layout,
            divisor=10,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_rhef),
            tooltip="Application radius in disk radii"
        )
        self.sl_rhef_upsilon, _ = create_slider(
            "Lower-tail Upsilon", 1, 500, 35, self.sec_rhef.content_layout,
            divisor=100,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_rhef),
            tooltip="Exponent from 0.01 to 5, applied to both rank-distribution tails. Values below 1 compress the tail toward mid-grey; 1 leaves the curve unchanged; values above 1 expand it. Upper-tail linking is controlled below."
        )
        self.sl_rhef_bin, _ = create_slider(
            "Ring Width (preview px)", 5, 100, 10, self.sec_rhef.content_layout,
            divisor=10,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_rhef),
            tooltip="Annular width in preview pixels; scaled to full resolution on export"
        )
        self.sec_rhef.toggled_active.connect(self.on_filter_toggled)
        histogram_group.addWidget(self.sec_rhef)

        multiscale_group = create_filter_group("MULTI-SCALE / WAVELETS", layout)
        self.sec_mgn = CollapsibleSection("MGN", has_checkbox=True, is_expanded=False, is_active=False)
        self.sl_mgn_gam, _ = create_slider(
            "Gamma", 1, 100, 32, self.sec_mgn.content_layout,
            divisor=10,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_mgn),
            tooltip="Global gamma exponent, from 0.1 to 10"
        )
        self.sl_mgn_k, _ = create_slider(
            "Factor k", 0, 500, 70, self.sec_mgn.content_layout,
            divisor=100,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_mgn),
            tooltip="Arctangent factor k, from 0 to 5"
        )
        self.sl_mgn_h, _ = create_slider(
            "Global Weight h", 0, 100, 70, self.sec_mgn.content_layout,
            divisor=100,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_mgn),
            tooltip="Global gamma-image weight, from 0 to 1. At 0, use local multiscale normalization; at 1, use the global gamma image. Layer opacity controls its contribution."
        )
        self.sl_mgn_trunc, _ = create_slider(
            "Kernel Truncation (Sigmas)", 1, 6, 3, self.sec_mgn.content_layout,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_mgn),
            tooltip="Gaussian truncation in standard deviations; all values 1–6 are honored"
        )
        self.sec_mgn.toggled_active.connect(self.on_filter_toggled)
        multiscale_group.addWidget(self.sec_mgn)

        self.sec_wow = CollapsibleSection("WOW", has_checkbox=True, is_expanded=False, is_active=False)
        self.sl_wow_scales, _ = create_slider(
            "Native wavelet scales", 0, 10, 0, self.sec_wow.content_layout,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_wow),
            tooltip="Integer number of native-resolution wavelet scales, not a power of two. Auto uses six for AEL and the largest supported count for native WOW (up to 10). The internal dilation doubles at each scale. Fast preview adapts physical bands approximately."
        )
        self.sl_wow_scales.setProperty("zero_label", "Auto")
        update_slider_display(self.sl_wow_scales)
        self.sl_wow_denoise = []
        for scale in range(10):
            slider, _ = create_slider(
                f"Denoise Scale {scale+1} (sigma)", 0, 100, 0,
                self.sec_wow.content_layout,
                divisor=10,
                on_release_callback=lambda: self.on_filter_slider_released(self.sec_wow),
                tooltip="Noise-significance threshold in sigma units for this native-resolution band. Fast preview shifts thresholds with its spatial bands. Zero disables thresholding; higher values suppress more weak detail. Noise is estimated from the current input, with approximate thresholds on masked inputs."
            )
            self.sl_wow_denoise.append(slider)
        self.combo_wow_bilateral = ScrollSafeComboBox()
        self.combo_wow_bilateral.addItems(["Standard WOW", "Edge-aware WOW (adjustable bilateral)", "AEL bilateral"])
        self.combo_wow_bilateral.setToolTip("Standard and adjustable edge-aware WOW use the existing backend. AEL bilateral uses a log-luminance radial residual, symmetric observed starlet pairs and its own noise floor. No mode fills missing data.")
        self.combo_wow_bilateral.setCurrentIndex(1)
        self.combo_wow_bilateral.currentIndexChanged.connect(self.dispatch_pipeline_request_if_auto)
        self.combo_wow_bilateral.currentIndexChanged.connect(lambda _: self.update_wow_controls())
        self.sec_wow.content_layout.addWidget(self.combo_wow_bilateral)
        self.sec_wow.toggled_active.connect(self.on_filter_toggled)
        multiscale_group.addWidget(self.sec_wow)

        sharpening_group = create_filter_group("SHARPENING", layout)
        self.sec_tangential = CollapsibleSection("TANGENTIAL DETAIL", has_checkbox=True, is_expanded=False, is_active=False)
        self.sec_tangential.toggled_active.connect(self.on_filter_toggled)
        sharpening_group.addWidget(self.sec_tangential)

        self.sec_larson_sekanina = CollapsibleSection("LARSON-SEKANINA", has_checkbox=True, is_expanded=False, is_active=False)
        self.sl_larson_sekanina_str, _ = create_slider(
            "Gain (%)", 0, 200, 10, self.sec_larson_sekanina.content_layout,
            on_release_callback=self.dispatch_pipeline_request_if_auto,
            tooltip="Gain scales the signed residual before Linear Light clipping; opacity controls the mixture after clipping.")
        self.sec_larson_sekanina.toggled_active.connect(self.on_filter_toggled)
        sharpening_group.addWidget(self.sec_larson_sekanina)

        self.sec_achf = CollapsibleSection("ACHF", has_checkbox=True, is_expanded=False, is_active=False)
        self.combo_achf_variant = ScrollSafeComboBox()
        self.combo_achf_variant.addItem("Adaptive circular", "adaptive")
        self.combo_achf_variant.addItem("AEL · ISO 01", "ael_iso_01")
        self.combo_achf_variant.addItem("AEL · ISO 04", "ael_iso_04")
        self.combo_achf_variant.addItem("AEL · Angular", "ael_angular_4")
        self.combo_achf_variant.setToolTip("Choose which variant to edit. Include checkboxes independently enable multiple variants; each retains its opacity and parameters. AEL uses positive log-luminance and Overlay; best used on linear input. Boundary bands can remain.")
        self.sec_achf.content_layout.addWidget(self.combo_achf_variant)
        self.achf_adaptive_panel = QWidget()
        adaptive_layout = QVBoxLayout(self.achf_adaptive_panel)
        adaptive_layout.setContentsMargins(0,0,0,0)
        self.sec_achf.content_layout.addWidget(self.achf_adaptive_panel)
        self.sl_achf_kernel, _ = create_slider(
            "Support Radius (preview px)", 10, 200, 20, adaptive_layout,
            divisor=10,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_achf),
            tooltip="Circular kernel radius in preview pixels, scaled for full-resolution export. Larger supports increase processing cost."
        )
        self.sl_achf_boost, _ = create_slider(
            "Contrast Gain", 0, 50, 20, adaptive_layout,
            divisor=10,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_achf),
            tooltip="Signed high-pass gain from 0 to 5. Opacity controls its contribution to the composition."
        )
        self.sl_achf_threshold, _ = create_slider(
            "Intensity Threshold (%)", 0, 100, 10, adaptive_layout,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_achf),
            tooltip="Maximum neighbor difference as a percentage of the working input intensity range; both opposite neighbors must pass."
        )
        self.sl_achf_background, _ = create_slider(
            "Background Retention (%)", 0, 100, 100, adaptive_layout,
            on_release_callback=lambda: self.on_filter_slider_released(self.sec_achf),
            tooltip="Percentage of the input image retained by the numerical ACHF filter. The Photoshop ACHF detail layer removes this base component before normalization."
        )
        add_achf_variants(self)
        def update_achf_controls():
            selected = self.combo_achf_variant.currentData()
            self.achf_adaptive_panel.setVisible(selected == 'adaptive')
            self.achf_adaptive_panel.setEnabled(selected == 'adaptive')
            for variant, controls in self.achf_ael_controls.items():
                controls['panel'].setVisible(selected == variant)
        self.combo_achf_variant.currentIndexChanged.connect(update_achf_controls)
        update_achf_controls()
        self.sec_achf.toggled_active.connect(self.on_filter_toggled)
        sharpening_group.addWidget(self.sec_achf)
        add_controls(self)

    def _build_presentation_section(self, layout: QVBoxLayout):
        """Build the shared PSB/JPEG presentation controls above export options."""
        psb_group = create_filter_group('PHOTOSHOP PRESENTATION', layout)
        self.sl_psb_exposure, self.lbl_psb_exposure = create_slider(
            'PSB Exposure (EV)', -600, 600, 0, psb_group,
            divisor=100, formatter=None,
            tooltip='Automatic native-image scale plus exposure compensation: +1 EV doubles exposure; -1 EV halves it. Always affects Photoshop layer presentation. Affects the screen and JPEG only when Preview PSB presentation is on; never changes the main TIFF. Double-click to restore 0 EV.')
        self.sl_psb_exposure.valueChanged.connect(self._on_psb_exposure_changed)
        self.btn_psb_preview = QPushButton('Preview PSB presentation')
        self.btn_psb_preview.setCheckable(True)
        self.btn_psb_preview.setChecked(True)
        self.btn_psb_preview.setToolTip('Show the Photoshop presentation (default). Turn off to inspect the un-stretched TIFF composition. Native verification matches the exported presentation; fast view is approximate. The optional Color Correction group is rendered only in Photoshop.')
        self.btn_psb_preview.toggled.connect(self.render_matrix_to_screen)
        psb_group.addWidget(self.btn_psb_preview)
        self.lbl_psb_presentation = QLabel('Auto scale + exposure compensation · Asinh 10')
        self.lbl_psb_presentation.setWordWrap(True)
        self.lbl_psb_presentation.setToolTip('P99.5 of positive native luminance outside 1.2 lunar radii. This automatic estimate is our heuristic; the Asinh curve and shared highlight shoulder follow AEL.')
        psb_group.addWidget(self.lbl_psb_presentation)
        layout.addSpacing(8)

        self.chk_export_layers = QCheckBox("Also export editable Photoshop layers")
        self.chk_export_layers.setChecked(True)
        self.chk_export_layers.setStyleSheet("QCheckBox { color: #dddddd; font-size: 11px; }")
        self.chk_export_layers.setToolTip("Export a 16-bit PSB or TIFF layer package with a stretched base, independent filter layers and optional RGB Color layer. Uses AEL-style presentation with automatic scale and adjustable exposure even when Preview PSB presentation is off. Includes a hidden working linear reference with its storage scale.")
        layout.addWidget(self.chk_export_layers)
        self.combo_layers_format = ScrollSafeComboBox()
        self.combo_layers_format.addItem("Photoshop · PSB (16-bit layers)", "psb")
        self.combo_layers_format.addItem("TIFF layers + Photoshop script", "tiff")
        self.combo_layers_format.setToolTip("PSB writes a verified layered file directly. TIFF keeps the individual layers and JSX import script as an alternative. Includes all active ACHF variants.")
        self.chk_color_correction = QCheckBox('Add Color Correction to PSB (sRGB)')
        self.chk_color_correction.setToolTip('PSB only: editable gradient map, color balance and sky saturation in a Normal 50% group. Photoshop renders the correction; preview and TIFF/JPEG stay unchanged. Initial masks need review.')
        layout.addWidget(self.chk_color_correction)
        layout.addWidget(self.combo_layers_format)
        def update_correction_option():
            self.chk_color_correction.setEnabled(self.chk_export_layers.isChecked() and self.combo_layers_format.currentData()=='psb')
        self.chk_export_layers.toggled.connect(update_correction_option)
        self.combo_layers_format.currentIndexChanged.connect(update_correction_option)
        update_correction_option()
        self.combo_input_state = ScrollSafeComboBox()
        # Use a Qt list rather than the native macOS popup, whose light item
        # background can conflict with our inherited dark-theme text colours.
        self.combo_input_state.setStyleSheet("""
            QComboBox {
                combobox-popup: 0;
                color: #eeeeee;
                background-color: #333333;
                border: 1px solid #555555;
                border-radius: 3px;
                padding: 5px 8px;
            }
        """)
        input_view = QListView(self.combo_input_state)
        input_view.setItemDelegate(QStyledItemDelegate(input_view))
        input_view.setUniformItemSizes(True)
        input_view.setStyleSheet("""
            QListView {
                background-color: #282828;
                color: #eeeeee;
                border: 1px solid #606060;
                border-radius: 0;
                outline: 0;
                selection-background-color: #505050;
                selection-color: #ffffff;
            }
            QListView::item {
                background-color: #282828;
                color: #eeeeee;
                padding: 7px 10px;
                border: none;
            }
            QListView::item:selected, QListView::item:hover {
                background-color: #505050;
                color: #ffffff;
            }
        """)
        input_view.viewport().setStyleSheet("background-color: #282828; border-radius: 0;")
        self.combo_input_state.setView(input_view)
        self.combo_input_state.addItem("Input: linearity unspecified", "unknown")
        self.combo_input_state.addItem("Input: linear", "linear")
        self.combo_input_state.addItem("Input: already stretched / nonlinear", "nonlinear")
        self.combo_input_state.setCurrentIndex(self.combo_input_state.findData("linear"))
        self.combo_input_state.setToolTip("Linear is assumed by default, not automatically confirmed. Change this if the source was already stretched. This declaration also controls color calibration; it does not undo stretching.")
        self.combo_input_state.setVisible(False)
        self.chk_calibrate_colour = FullRowCheckBox("Calibrate color")
        self.chk_calibrate_colour.setToolTip("Requires linear RGB. Assumes neutral channel spans: balances P99 minus P1 using gains only, without subtracting backgrounds. A common highlight scale preserves channel ratios. This is not photometric or ICC calibration. Applies to fast preview, verification and export. Preserves the original sources.")
        self.chk_calibrate_colour.setEnabled(False)
        self.chk_calibrate_colour.setChecked(True)
        self.chk_calibrate_colour.toggled.connect(self.on_colour_changed)
        self.combo_input_state.currentIndexChanged.connect(self.on_input_state_changed)
        self.lbl_colour_hint = QLabel("Color calibration requires an RGB image.")
        self.lbl_colour_hint.setToolTip("Color calibration is available only for RGB input explicitly declared linear. Native-image calibration is shared by fast preview, verification and export; it does not change numerical luminance filters.")
        self.lbl_colour_hint.setWordWrap(True)
        self.lbl_colour_hint.setStyleSheet("color: #aaaaaa; font-size: 10px;")
        self.btn_export = QPushButton("Export Final Image")
        self.btn_export.setToolTip("Save the full-resolution filter composition without visual stretch. JPEG follows the PSB presentation preview. Photoshop layers use their own exposure-controlled presentation base and hidden linear reference.")
        self.btn_export.clicked.connect(self.export_image_action)
        self.btn_save_settings = QPushButton("Save Settings Only")
        self.btn_save_settings.setToolTip("Save current adjustments to JSON without calculating filters or exporting images. The original image is required when reopening the JSON.")
        self.btn_save_settings.clicked.connect(self.save_settings_action)
        layout.addWidget(self.btn_save_settings)
        layout.addWidget(self.btn_export)
        self.export_progress = QProgressBar()
        self.export_progress.setRange(0,100)
        self.export_progress.setToolTip("Completed export stages, not an estimate of elapsed or remaining time.")
        self.export_progress.hide()
        layout.addWidget(self.export_progress)

    def on_input_state_changed(self, *_):
        warning = getattr(self, '_input_linearity_warning', '')
        state = self.combo_input_state.currentData()
        self.lbl_input_linearity.setText(
            'Assumed linear; not confirmed.' if state == 'linear' else
            'Input already stretched.' if state == 'nonlinear' else
            'Input linearity unknown.')
        self.lbl_input_linearity.setToolTip(warning)
        self.lbl_input_linearity.setVisible(bool(warning))
        allowed = self.full_source_rgb is not None and self.combo_input_state.currentData() == "linear"
        self.chk_background.setEnabled(self.full_raw_image is not None and state == 'linear')
        if state != 'linear' and self.chk_background.isChecked():
            self.chk_background.setChecked(False)
        self.chk_calibrate_colour.setEnabled(allowed)
        self.lbl_colour_hint.setText(
            "Color calibration requires an RGB image." if self.full_source_rgb is None else
            "Color calibration is shown in preview and export." if allowed else
            "Select 'Input: linear' below to enable color calibration.")
        if not allowed:
            self.chk_calibrate_colour.setChecked(False)

    def on_colour_changed(self, *_):
        """Update presentation colour without invalidating the numerical cache."""
        self._colour_cache = None
        self._preview_colour_cache = None
        self._colour_revision += 1
        self.render_matrix_to_screen()

    def collect_display_parameters(self):
        """Native normalization for the un-stretched composition; no GUI tone curve."""
        settings=dict(blend=1.)
        if self._display_reference_source is self.full_raw_image and self._display_bounds is not None:
            settings['normalization_range']=list(self._display_bounds)
        return settings

    def on_circle_center_requested(self, x: int, y: int):
        """Only modified canvas clicks move the lunar center."""
        self.txt_x.setText(str(x))
        self.txt_y.setText(str(y))
        self.dispatch_pipeline_request_if_auto()

    def _on_geometry_changed(self, *_):
        if self.full_raw_image is not None and not getattr(self,'_restoring_settings',False):
            try:
                cx, cy, radius = (float(getattr(self,'txt_'+key).text()) for key in ('x','y','r'))
                h, w = self.full_raw_image.shape[:2]
                if radius > 0 and all(np.isfinite(v) for v in (cx,cy,radius)):
                    maximum = int(np.ceil(10*max(np.hypot(x-cx,y-cy) for x in (0,w-1) for y in (0,h-1))/radius))
                    self.sl_fnrgf_rmax.setMaximum(max(self.sl_fnrgf_rmax.maximum(),maximum))
            except (ValueError,OverflowError):
                pass
        if self.background.base is not None and self.chk_background.isChecked() and not getattr(self,'_restoring_settings',False):
            self.background.points=None;self.background.dirty=True
        self.background.overlay()
        self.dispatch_pipeline_request_if_auto()

    def trigger_circle_redraw(self):
        """Redraw the solar disk circle on the canvas."""
        if self.raw_image is None or self.full_raw_image is None:
            return
        try:
            cx_full = int(self.txt_x.text())
            cy_full = int(self.txt_y.text())
            r_full = int(self.txt_r.text())
            h_full, w_full = self.full_raw_image.shape[:2]
            self.image_label.set_circle_parameters(cx_full, cy_full, r_full, native_w=w_full, native_h=h_full)
        except ValueError:
            pass

    def toggle_compare_mode(self, checked: bool):
        """Toggle between original and processed image display."""
        if self.raw_image is None:
            self.btn_compare.setChecked(False)
            return
        self.show_original_mode = checked
        if checked:
            self.btn_compare.setText("View Processed")
            self.status_label.setText("Status: Showing Original")
            self.status_label.setStyleSheet("color: #cc3335; font-weight: bold;")
        else:
            self.btn_compare.setText("View Original")
            self.status_label.setText("Status: Showing Processed")
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        self.render_matrix_to_screen()

    def toggle_auto_calc_mode(self, checked: bool):
        """Toggle automatic calculation mode."""
        self.auto_calculate = checked
        self.recalculation_timer.stop()
        self.has_pending_request = False
        self._pending_manual = False
        self.btn_auto_calc.setText("Auto Calculate" if checked else "Man Calc")
        self.btn_recalc.setVisible(not checked)
        self.status_label.setText("Status: Auto Calculate" if checked else "Status: Manual Calculate")
        if checked:
            self.dispatch_pipeline_request()

    def on_layer_mix_changed(self, *_):
        """Wait for a short pause in opacity edits, then recompose cached layers."""
        self.presentation_timer.start(250)

    def on_filter_toggled(self, is_active: bool):
        """Enable or bypass a layer without changing its opacity."""
        self.dispatch_pipeline_request_if_auto()

    def on_filter_slider_released(self, section):
        # Parameter edits require this enabled layer to be recalculated.
        if section.is_filter_active():
            self.dispatch_pipeline_request_if_auto()

    def dispatch_pipeline_request_if_auto(self):
        """Record edits immediately, dispatch only after the user pauses."""
        if self._closing or getattr(self, '_restoring_settings', False):
            return
        self._preview_revision += 1
        if self.image_label.zoom is not None:
            self.image_label.set_pending(True,None if self.auto_calculate else 'Settings changed · press Calculate')
        if self.is_processing:
            self.filter_worker.cancel()
            self.status_label.setText('Status: Cancelling outdated calculation...')
        if self.auto_calculate and self.raw_image is not None:
            self.has_pending_request = True
            self.recalculation_timer.start()
        elif self.raw_image is not None:
            self.status_label.setText('Status: Settings changed — recalculate')

    def dispatch_pipeline_request(self):
        """Run the latest complete recipe; snapshot errors never lock the worker."""
        self.recalculation_timer.stop()
        if self.raw_image is None or self.full_raw_image is None:
            return
        if self._closing or self._load_thread is not None or self._export_thread is not None:
            return
        if self.is_processing:
            self.filter_worker.cancel()
            self.has_pending_request = True
            self._pending_manual = not self.auto_calculate
            return
        self.has_pending_request = False
        self._pending_manual = False
        if self.background.thread is not None:return
        if self.background.dirty:
            self.background.start()
            return
        self._running_full_job = self.chk_verify_preview.isChecked() or self.image_label.zoom is not None
        job_image = self.full_raw_image if self._running_full_job else self.raw_image
        try:
            params = self.collect_filter_parameters(job_image.shape[:2])
            if not np.isfinite([params['sx'], params['sy'], params['sr']]).all() or params['sr'] <= 0:
                raise ValueError("Sun center must be finite and radius must be positive")
        except (ValueError, TypeError, OverflowError) as error:
            self.status_label.setText(f"Status: Invalid parameters — {error}")
            if self.image_label.zoom is not None:
                self.image_label.set_pending(True,"Check geometry · see status")
            self.status_label.setStyleSheet("color: #ff3333; font-weight: bold;")
            return
        if self.btn_compare.isChecked() and self.image_label.zoom is None:
            self.btn_compare.setChecked(False)
            self.show_original_mode = False
        self._running_revision = self._preview_revision
        self._running_image = self.raw_image
        self._running_full_source = self.full_raw_image
        self._running_signature = parameter_signature(params)
        self.is_processing = True
        self.btn_export.setEnabled(False)
        self.status_label.setText("Status: Processing Filters...")
        self.status_label.setStyleSheet("color: #e5a00d; font-weight: bold;")
        self.filter_worker.prepare_job()
        self.request_processing_signal.emit(job_image, params)

    def collect_filter_parameters(self, target_shape, *, include_mask=True):
        """Snapshot UI once; prepare the same recipe for preview or export."""
        params = {
            "nrgf_enabled": self.sec_nrgf.is_filter_active(),
            "nrgf_str": 100,
            "nrgf_rad": self.sl_nrgf_rad.value(),
            "nrgf_bin_px": self.sl_nrgf_bin_px.value()/10.,
            "nrgf_robust": self.combo_nrgf_statistics.currentIndex() == 0,
            "fnrgf_enabled": self.sec_fnrgf.is_filter_active(),
            "fnrgf_str": 100,
            "fnrgf_ord": self.sl_fnrgf_ord.value(),
            "fnrgf_seg": 2 ** self.sl_fnrgf_seg.value(),
            "fnrgf_cut": self.sl_fnrgf_cut.value(),
            "fnrgf_rad": self.sl_fnrgf_rad.value(),
            "fnrgf_rmax": self.sl_fnrgf_rmax.value(),
            "fnrgf_bin_px": self.sl_fnrgf_bin_px.value(),
            "fnrgf_width_func": "mad" if self.combo_fnrgf_width.currentIndex() == 1 else "std",
            "fnrgf_radial_binning": "log" if self.combo_fnrgf_binning.currentIndex() == 1 else "linear",
            "fnrgf_apply_mask": self.sl_fnrgf_mask.value(),
            "mgn_enabled": self.sec_mgn.is_filter_active(),
            "mgn_str": 100,
            "mgn_gam": self.sl_mgn_gam.value(),
            "mgn_k": self.sl_mgn_k.value(),
            "mgn_h": self.sl_mgn_h.value(),
            "mgn_trunc": self.sl_mgn_trunc.value(),
            "rhef_mode": self.combo_rhef_mode.currentData(),
            "rhef_enabled": self.sec_rhef.is_filter_active(),
            "rhef_str": 100,
            "rhef_rad": self.sl_rhef_rad.value(),
            "rhef_upsilon": self.sl_rhef_upsilon.value(),
            "rhef_bin_px": self.sl_rhef_bin.value()/10.0,
            "wow_enabled": self.sec_wow.is_filter_active(),
            "wow_str": 100,
            "wow_scales": self.sl_wow_scales.value() or (6 if self.combo_wow_bilateral.currentIndex() == 2 else self.sl_wow_scales.maximum()),
            "wow_native_scales": True,
            "wow_denoise": [slider.value()/10 for slider in self.sl_wow_denoise if slider.isEnabled()],
            "wow_bilateral": 1 if self.combo_wow_bilateral.currentIndex() else None,
            "tangential_enabled": self.sec_tangential.is_filter_active(),
            "tangential_str": 100,
            "larson_sekanina_enabled": self.sec_larson_sekanina.is_filter_active(),
            "larson_sekanina_str": self.sl_larson_sekanina_str.value(),
            "achf_variant": self.combo_achf_variant.currentData(),
            "achf_enabled": self.sec_achf.is_filter_active(),
            "achf_str": 100,
            "achf_kernel": self.sl_achf_kernel.value(),
            "achf_boost": self.sl_achf_boost.value(),
            "achf_threshold": self.sl_achf_threshold.value(),
            "achf_background": self.sl_achf_background.value(),
            "sx": float(self.txt_x.text()),
            "sy": float(self.txt_y.text()),
            "sr": float(self.txt_r.text()),
        }
        variants = collect_achf_variants(self)
        params['layer_display'] = composition_settings(self.collect_display_parameters())
        for name in ('nrgf','fnrgf','rhef','mgn','wow','tangential','larson_sekanina','achf'):
            params[name+'_opacity'] = getattr(self,'sl_'+name+'_opacity').value()
        variants['adaptive'] = dict(enabled=self.chk_achf_adaptive.isChecked(),
                                    opacity=self.sl_achf_opacity.value(),strength=100)
        params['achf_variants'] = variants
        params['achf_adaptive_strength'] = 100
        selected = params['achf_variant']
        if selected in variants and selected != 'adaptive':
            params['achf_str'] = variants[selected]['strength']
            params['achf_ael_parameters'] = variants[selected]
        params.update(collect_controls(self))
        params.update(statistics_exclude_lunar=self.chk_statistics_lunar.isChecked(),
                      statistics_exclude_bright=self.chk_statistics_bright.isChecked(),
                      statistics_guard_px=self.sl_statistics_guard.value()/10,
                      statistics_bright_percentile=self.sl_statistics_percentile.value()/10,
                      statistics_limb_outer=self.sl_statistics_outer.value()/10)
        if params['tangential_outer'] and params['tangential_outer'] <= params['tangential_inner']:
            raise ValueError('Tangential outer radius must exceed inner radius or be zero')
        params['background_extraction']=self.background.report
        params = prepare_parameters(params, self.full_raw_image.shape[:2],
                                    self.preview_image.shape[:2], target_shape)
        data = self.full_raw_image if tuple(target_shape) == self.full_raw_image.shape[:2] else self.preview_image
        if include_mask:
            params["valid_mask"] = np.isfinite(data)
        return params

    def _dispatch_pending_preview(self):
        # An edit restarted the debounce timer: don't execute early or lose it.
        if self.recalculation_timer.isActive():
            return
        if self.has_pending_request and (self.auto_calculate or self._pending_manual):
            self.dispatch_pipeline_request()

    def _log_processing_end(self, process, outcome):
        pending=(self.recalculation_timer.isActive() or self.presentation_timer.isActive()
                 or (self.has_pending_request and (self.auto_calculate or self._pending_manual)))
        if self.is_processing or self._export_thread is not None:
            state="Another process is running"
        elif pending:
            state="Waiting for pending update"
        else:
            state="Idle — no processing running or queued"
        print(f"[{process}] {outcome}. {state}.",flush=True)

    def on_processing_cancelled(self):
        """Keep the last accepted preview and start only the latest paused edit."""
        self.is_processing = False
        self.btn_export.setEnabled(True)
        self._running_revision = None
        self._running_image = None
        self.status_label.setText('Status: Waiting for slider adjustments...' if self.auto_calculate
                                  else 'Status: Settings changed — recalculate')
        self.status_label.setStyleSheet('color: #e5a00d; font-weight: bold;')
        self._dispatch_pending_preview()
        self._log_processing_end("PIPELINE", "Cancelled")

    def on_processing_failed(self, message: str):
        self.is_processing = False
        self.btn_export.setEnabled(True)
        self._running_revision = None
        self._running_image = None
        self.status_label.setText(f"Status: Processing failed — {message}")
        if self.image_label.zoom is not None:
            self.image_label.set_pending(True,"Native calculation failed · see status")
        self.status_label.setStyleSheet("color: #ff3333; font-weight: bold;")
        self._dispatch_pending_preview()
        self._log_processing_end("PIPELINE", "Failed")

    def on_processing_finished(self, output_matrix: np.ndarray):
        """Never publish an obsolete image or recipe as the finished preview."""
        current = (self._running_revision is None or
                   (self._running_revision == self._preview_revision
                    and self._running_image is self.raw_image
                    and self._running_full_source is self.full_raw_image))
        self.is_processing = False
        self.btn_export.setEnabled(True)
        self._running_revision = None
        self._running_image = None
        if current and not self.recalculation_timer.isActive():
            self._has_layer_result = True
            if self._running_full_job:
                self._full_cache = (self.full_raw_image, self._running_signature, output_matrix, self._preview_revision)
            self.processed_image = output_matrix
            self.status_label.setText('Status: Full-resolution verification ready' if self._running_full_job else 'Status: Fast preview ready (approximate)')
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
            self.render_matrix_to_screen()
        else:
            self.status_label.setText("Status: Updated settings pending..." if
                                      (self.auto_calculate or self._pending_manual) else
                                      "Status: Settings changed — recalculate")
            self.status_label.setStyleSheet("color: #e5a00d; font-weight: bold;")
        self._dispatch_pending_preview()
        self._log_processing_end("PIPELINE", "Complete")

    def update_wow_controls(self, *, preserve_settings=False):
        shape = self.full_raw_image.shape if self.full_raw_image is not None else (5120, 5120)
        maximum = max(1, min(10, int(np.round(np.log2(min(shape)/5.)))))
        ael = self.combo_wow_bilateral.currentIndex() == 2
        if ael:
            maximum = 10
        if preserve_settings:
            maximum = max(maximum, self.sl_wow_scales.value())
        previous = self.sl_wow_scales.blockSignals(True)
        self.sl_wow_scales.setMaximum(maximum)
        self.sl_wow_scales.blockSignals(previous)
        update_slider_display(self.sl_wow_scales)
        self.sec_wow.chk_active.setEnabled(min(shape) >= 10)
        if min(shape) < 10 and not preserve_settings:
            self.sec_wow.chk_active.setChecked(False)
        count = self.sl_wow_scales.value() or (6 if ael else maximum)
        for index, slider in enumerate(self.sl_wow_denoise):
            slider.setEnabled(not ael and index < count)
        self.sl_wow_noise.setEnabled(not ael)
        self.sl_wow_noise_floor.setEnabled(ael)
        self.sl_wow_bilateral.setEnabled(self.combo_wow_bilateral.currentIndex() == 1)

    def apply_recommended_parameters_to_gui(self, r_full: float, w_full: int, h_full: int):
        """Auto-populate sliders based on image resolution."""
        if r_full <= 5:
            return

        preview_radius = r_full*np.sqrt(self.preview_image.shape[0]/h_full*self.preview_image.shape[1]/w_full)
        rec_achf_kernel_px = max(1.5, preview_radius * 0.025)

        rec_fnrgf_ord = int(np.clip(r_full * 0.015 + 4, 6, 24))
        # Half-diagonal reaches the corners for a disk at the frame center.
        # Round upwards to the slider's 0.1 R_sun step to include corner pixels.
        cx_full, cy_full = float(self.txt_x.text()), float(self.txt_y.text())
        rmax_slider = int(np.ceil(10 * max(np.hypot(x-cx_full, y-cy_full) for x in (0, w_full-1) for y in (0, h_full-1)) / r_full))
        self.sl_fnrgf_rmax.setMaximum(max(self.sl_fnrgf_rmax.minimum(), rmax_slider))
        rec_fnrgf_rmax = self.sl_fnrgf_rmax.maximum() / 10.0
        rec_fnrgf_nbins = recommended_radial_bins(
            self.sl_fnrgf_rad.value() / 10.0 * r_full,
            rec_fnrgf_rmax * r_full,
            logarithmic=self.combo_fnrgf_binning.currentIndex() == 1,
            width_px=4,
        )
        adaptive_defaults = (
            (self.sl_fnrgf_ord, rec_fnrgf_ord),
            (self.sl_fnrgf_seg, (2 * rec_fnrgf_ord).bit_length()),
            (self.sl_fnrgf_bin_px, 4),
            (self.sl_fnrgf_rmax, int(round(rec_fnrgf_rmax * 10.0))),
            (self.sl_wow_scales, 6 if self.combo_wow_bilateral.currentIndex() == 2 else 0),
            (self.sl_achf_kernel, int(round(rec_achf_kernel_px * 10.0))),
        )
        for slider, value in adaptive_defaults:
            slider.setValue(value)
        for slider, _ in adaptive_defaults:
            slider.setProperty("reset_value", slider.value())
        self.update_wow_controls()

        print(f"\n{'='*80}")
        print(f"INITIAL FILTER HEURISTICS (Reference disk radius = {r_full:.1f} native px)")
        print(f"{'='*80}")
        print(f"   • Full image: {w_full} × {h_full} px")
        print("   • Reference disk geometry may enclose missing data; no astrometric scale inferred.")
        print(f"   • FNRGF: order = {self.sl_fnrgf_ord.value()} | sectors = {2**self.sl_fnrgf_seg.value()} | rings = {rec_fnrgf_nbins} (full resolution) | outer radius = {rec_fnrgf_rmax:.1f} reference radii")
        print(f"   • WOW: {self.sl_wow_scales.value() or 'Auto'} native scales; fast preview adapts the bands")
        print(f"   • ACHF: support radius = {self.sl_achf_kernel.value()/10:.1f} preview px")
        print(f"{'='*80}\n")

    def auto_detect_moon_action(self):
        """Detect geometry in the background, just as when opening an image."""
        if self.full_raw_image is None or self._geometry_thread is not None or self._closing:
            return
        self.status_label.setText('Status: Detecting lunar disk...')
        self.control_sidebar.setEnabled(False)
        self.zoom_toolbar.setEnabled(False)
        self._geometry_thread = TaskThread(self.detect_lunar_limb, self.full_raw_image, parent=self)
        self._geometry_thread.finished.connect(self._on_geometry_detected)
        self._geometry_thread.start()

    def _on_geometry_detected(self):
        thread = self._geometry_thread
        self._geometry_thread = None
        self.control_sidebar.setEnabled(True)
        self.zoom_toolbar.setEnabled(True)
        if not self._closing and thread.args[0] is self.full_raw_image:
            if thread.error is not None:
                self.status_label.setText(f'Status: Lunar detection failed — {thread.error}')
            else:
                cx, cy, radius = thread.result
                for key,value in zip(('x','y','r'),(cx,cy,radius)):
                    getattr(self,'txt_'+key).setText(str(value))
                self.status_label.setText(f'Status: Moon detected (Full-res X:{cx}, Y:{cy}, R:{radius})')
        thread.deleteLater()
        self._finish_close()

    @staticmethod
    def detect_lunar_limb(raw_img: np.ndarray) -> Tuple[int, int, int]:
        """Estimate a circular data boundary or a contrast-normalized lunar limb.

        The robust stretch below is a detection-only working image: it never
        modifies the linear source, filter input or presentation settings.
        """
        if raw_img is None:
            return 0, 0, 100

        if raw_img.ndim == 3:
            if raw_img.shape[2] in (3, 4):
                img_gray = 0.299 * raw_img[:, :, 0] + 0.587 * raw_img[:, :, 1] + 0.114 * raw_img[:, :, 2]
            elif raw_img.shape[0] in (3, 4):
                img_gray = 0.299 * raw_img[0, :, :] + 0.587 * raw_img[1, :, :] + 0.114 * raw_img[2, :, :]
            else:
                img_gray = raw_img[:, :, 0]
        else:
            img_gray = raw_img

        h, w = img_gray.shape
        # A calibrated stack can have an unobserved lunar disc instead of a
        # black disc. Fit only a closed, nearly circular missing-data boundary;
        # edge gaps and isolated defective pixels are not lunar candidates.
        missing = (~np.isfinite(img_gray)).astype(np.uint8)
        if missing.any():
            contours, _ = cv2.findContours(missing, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            for contour in sorted(contours, key=cv2.contourArea, reverse=True):
                if cv2.contourArea(contour) < np.pi * (min(h, w) * .02)**2:
                    break
                points = contour[:, 0].astype(float)
                if (points[:, 0].min() <= 0 or points[:, 0].max() >= w-1
                        or points[:, 1].min() <= 0 or points[:, 1].max() >= h-1):
                    continue
                origin = points.mean(axis=0)
                offsets = points-origin
                matrix = np.column_stack([2*offsets, np.ones(len(points))])
                solution = np.linalg.lstsq(matrix, np.sum(offsets**2, axis=1), rcond=None)[0]
                center = origin+solution[:2]
                distances = np.linalg.norm(points-center, axis=1)
                radius = float(np.mean(distances))
                if radius > 0 and np.sqrt(np.mean((distances-radius)**2))/radius < .03:
                    cx, cy = int(round(center[0])), int(round(center[1]))
                    # Enclose the whole boundary around the integer center used by filters.
                    enclosing_radius = int(np.ceil(np.linalg.norm(points-(cx, cy), axis=1).max()))
                    print("Disk protection geometry estimated from missing-data boundary; radius encloses the data gap, not necessarily the physical lunar limb")
                    return cx, cy, enclosing_radius
        clean_img = np.nan_to_num(img_gray, nan=0.0, posinf=0.0, neginf=0.0)
        # A saturated star or prominence can dominate min/max scaling and leave
        # the actual limb below Hough's edge threshold. Ignore extreme tails and
        # compress the detection image before quantizing it to eight bits.
        observed = clean_img[np.isfinite(img_gray)]
        if not observed.size:
            return w // 2, h // 2, min(w, h) // 4
        lower, upper = np.percentile(observed, [1, 99.8])
        if upper <= lower:
            return w // 2, h // 2, min(w, h) // 4
        contrast = np.clip((clean_img.astype(np.float64)-lower)/(upper-lower), 0, 1)
        # Retain floating-point samples for full-resolution radial refinement.
        norm = (255*np.arcsinh(10*contrast)/np.arcsinh(10)).astype(np.float32)

        scale = min(1.0, 800.0 / max(h, w))
        sw, sh = max(1, int(w * scale)), max(1, int(h * scale))
        small = cv2.resize(norm, (sw, sh), interpolation=cv2.INTER_AREA).astype(np.uint8)
        filtered = cv2.bilateralFilter(small, 9, 75, 75)

        circles = cv2.HoughCircles(
            filtered,
            cv2.HOUGH_GRADIENT,
            dp=1.2,
            minDist=min(sw, sh) // 4,
            param1=100,
            param2=30,
            minRadius=int(min(sw, sh) * 0.04),
            maxRadius=int(min(sw, sh) * 0.48),
        )

        best_candidate = None
        if circles is not None:
            circles = np.round(circles[0, :]).astype(int)
            best_contrast = -1.0
            for cx, cy, r in circles:
                if cx - r < 0 or cx + r >= sw or cy - r < 0 or cy + r >= sh:
                    continue
                mask_in = np.zeros((sh, sw), dtype=np.uint8)
                mask_out = np.zeros((sh, sw), dtype=np.uint8)
                cv2.circle(mask_in, (cx, cy), int(r * 0.8), 255, -1)
                cv2.circle(mask_out, (cx, cy), int(r * 1.25), 255, -1)
                cv2.circle(mask_out, (cx, cy), int(r * 1.05), 0, -1)

                contrast = cv2.mean(small, mask=mask_out)[0] - cv2.mean(small, mask=mask_in)[0]
                if contrast > best_contrast and contrast > 5:
                    best_contrast = contrast
                    best_candidate = ((cx + 0.5) * w / sw - 0.5,
                                      (cy + 0.5) * h / sh - 0.5,
                                      float(r) / scale)

        if best_candidate is None:
            return w // 2, h // 2, min(w, h) // 4

        init_cx, init_cy, init_r = best_candidate
        r_search = int(init_r * 0.15)
        radii = np.arange(max(1, init_r - r_search), min(min(w, h) / 2, init_r + r_search), 0.5)
        angles = np.linspace(0, 2 * np.pi, 360, endpoint=False)

        edge_pts = []
        for ang in angles:
            xs = (init_cx + radii * np.cos(ang)).astype(np.float32)
            ys = (init_cy + radii * np.sin(ang)).astype(np.float32)
            if not len(radii) or xs.min() < 0 or xs.max() > w - 1 or ys.min() < 0 or ys.max() > h - 1:
                continue
            profile = cv2.remap(norm, xs[None, :], ys[None, :], cv2.INTER_LINEAR)[0]
            grad = np.diff(profile)
            if len(grad) > 0 and grad.max() > 2.5:
                index = np.argmax(grad)
                best_r = (radii[index] + radii[index + 1]) / 2
                edge_pts.append((init_cx + best_r * np.cos(ang), init_cy + best_r * np.sin(ang)))

        if len(edge_pts) >= 12:
            pts = np.array(edge_pts)
            x_pts, y_pts = pts[:, 0], pts[:, 1]
            A = np.column_stack([x_pts, y_pts, np.ones_like(x_pts)])
            B = -(x_pts**2 + y_pts**2)
            try:
                from scipy.optimize import least_squares
                sol, _, _, _ = np.linalg.lstsq(A, B, rcond=None)
                cx, cy = -sol[0]/2.0, -sol[1]/2.0
                radius = np.sqrt(max(1.0, cx**2 + cy**2 - sol[2]))
                # Limit the pull of prominences and bright arcs outside the limb.
                fit = least_squares(
                    lambda circle: np.hypot(x_pts-circle[0], y_pts-circle[1])-circle[2],
                    (cx, cy, radius), loss='soft_l1', f_scale=0.5,
                )
                final_cx, final_cy, final_r = fit.x
                if abs(final_cx - init_cx) < init_r * 0.2 and abs(final_cy - init_cy) < init_r * 0.2:
                    return int(round(final_cx)), int(round(final_cy)), int(round(final_r))
            except Exception:
                pass

        return int(round(init_cx)), int(round(init_cy)), int(round(init_r))

    def load_image_action(self):
        """Load an astronomical image (FITS, XISF, TIFF, etc)."""
        file_filter = (
            "Images and Settings (*.json *.tiff *.tif *.fits *.fit *.fts *.xisf *.png *.jpg *.jpeg *.bmp);;"
            "Processing Settings (*.json);;"
            "Astronomical FITS (*.fits *.fit *.fts);;"
            "PixInsight XISF (*.xisf);;"
            "TIFF Images (*.tiff *.tif);;"
            "PNG Images (*.png);;"
            "All Files (*)"
        )
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Image / Settings", "", file_filter)
        if not file_path:
            return

        if self._load_thread is not None or self._closing:
            return
        try:
            project = None
            if file_path.lower().endswith('.json'):
                image_path, project = read_settings(file_path)
                validate_settings(self, project)
                file_path = str(image_path)
            geometry = None if project is None else tuple(int(project['geometry'][k]) for k in ('x','y','r'))
            self._load_thread = TaskThread(load_source, file_path, geometry, self.detect_lunar_limb, parent=self)
            self._load_thread.file_path = file_path
            self._load_thread.project = project
            self._load_thread.finished.connect(self._on_source_loaded)
            self.control_sidebar.setEnabled(False)
            self.zoom_toolbar.setEnabled(False)
            self.status_label.setText('Status: Loading image...')
            self.recalculation_timer.stop()
            self.has_pending_request = False
            self._preview_revision += 1
            self.filter_worker.cancel()
            self._load_thread.start()
        except Exception as error:
            self._show_load_error(error)

    def _show_load_error(self, error):
        self.status_label.setText(f'Error loading file: {error}')
        self.status_label.setToolTip(str(error))
        self.status_label.setStyleSheet('color: #ff3333; font-weight: bold;')

    def _on_source_loaded(self):
        thread = self._load_thread
        self._load_thread = None
        self.control_sidebar.setEnabled(True)
        self.zoom_toolbar.setEnabled(True)
        try:
            if self._closing:
                return
            if thread.error is not None:
                raise ValueError(thread.error)
            loaded, file_path, project = thread.result, thread.file_path, thread.project
            first_image = self.full_raw_image is None
            lower_path = file_path.lower()
            # Reject incompatible recipes before replacing the current source.
            if project is not None:
                restore_settings(self, project)
            self.background.reset_source(loaded,project)
            self._has_layer_result = False
            engine_for(self.filter_worker).clear()
            self.image_label.clear()
            self.btn_disk_overlay.setChecked(True)
            self.zoom_buttons.button(0).setChecked(True)
            self._native_display_revision=self._native_filter_revision=None
            self.full_raw_image = loaded['full']
            self._display_reference_source=self.full_raw_image
            self._display_bounds=loaded['display_bounds']
            self.full_source_rgb = loaded['rgb']
            self.source_rgb_white = loaded['white']
            self._colour_cache = None
            self._preview_colour_cache = None
            # Restore the requested defaults without rendering the previous image
            # or scheduling a worker until the new source and geometry are ready.
            for control in (() if project is not None else (self.combo_input_state, self.chk_calibrate_colour, self.chk_verify_preview)):
                blocked = control.blockSignals(True)
                if control is self.combo_input_state:
                    control.setCurrentIndex(control.findData("linear"))
                else:
                    control.setChecked(loaded['rgb'] is not None if control is self.chk_calibrate_colour else False)
                control.blockSignals(blocked)
            self._input_linearity_warning = (
                "Input assumed linear. This format commonly contains display-encoded images; "
                "if already stretched, select 'Input: already stretched / nonlinear'."
                if lower_path.endswith(('.jpg', '.jpeg', '.png', '.bmp')) else
                "Input assumed linear; linearity has not been confirmed. "
                "If the source was stretched before saving, select 'Input: already stretched / nonlinear'.")
            self.on_input_state_changed()
            self.combo_input_state.setVisible(True)
            self.source_path = file_path
            self._full_cache = None
            h_full, w_full = self.full_raw_image.shape[:2]

            self.preview_scale = loaded['scale']
            self.preview_image = loaded['preview']
            self.raw_image = self.preview_image

            self.processed_image = self.raw_image.copy()
            scale_ratio = h_full / float(self.preview_image.shape[0])
            self.lbl_scale_info.setText(f"Scale: {scale_ratio:.1f}x (100% = {w_full}×{h_full}px)")

            cx_full, cy_full, r_full = loaded['circle']

            self.txt_x.setText(str(cx_full))
            self.txt_y.setText(str(cy_full))
            self.txt_r.setText(str(r_full))

            if project is None and first_image:
                reset_filter_defaults(self, ael=True)
                self.apply_recommended_parameters_to_gui(r_full, w_full, h_full)
            if project is not None:
                cx_full,cy_full,r_full=(int(getattr(self,"txt_"+key).text()) for key in ("x","y","r"))
            if project is not None:
                self.background.points=([tuple(p) for p in project.get('background_samples',[])] if project.get('background_samples') is not None else None)
            self.background.overlay()
            self.update_wow_controls(preserve_settings=project is None and not first_image)

            # Invalidate the filter revision before snapshotting the first preview.
            self.dispatch_pipeline_request_if_auto()
            self.render_matrix_to_screen()
            missing = loaded['missing']
            self.status_label.setText(f"Status: Loaded {os.path.basename(file_path)} (X:{cx_full}, Y:{cy_full}, R:{r_full}); {missing} missing pixels")
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        except Exception as error:
            self._show_load_error(error)
        finally:
            thread.deleteLater()
            self._finish_close()

    def save_settings_action(self):
        """Save a reloadable recipe without running the processing/export pipeline."""
        if self.full_raw_image is None or not self.source_path:
            self.status_label.setText("Status: Load an image before saving settings")
            return
        file_path,_=QFileDialog.getSaveFileName(self,"Save Settings Only",
            os.path.splitext(self.source_path)[0]+'.json',"Processing Settings (*.json)")
        if not file_path:
            return
        if not file_path.lower().endswith('.json'):
            file_path+='.json'
        try:
            parameters=self.collect_filter_parameters(self.full_raw_image.shape[:2])
            destination=write_settings(file_path,self.source_path,capture_settings(self),
                                       parameters,self.collect_display_parameters())
            message=f"Status: Settings saved — {destination}"
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        except Exception as error:
            message=f"Status: Settings save failed — {error}"
            self.status_label.setStyleSheet("color: #ff3333; font-weight: bold;")
        self.status_label.setText(message)
        self.status_label.setToolTip(message)

    def export_image_action(self):
        """Snapshot settings on the GUI thread, calculate/write on an export thread."""
        if self.background.dirty or self.background.thread is not None:
            self.background.export_pending=True
            self.dispatch_pipeline_request()
            return
        if self.raw_image is None or self.full_raw_image is None:
            self.status_label.setText("Status: No image loaded")
            return
        if self.is_processing or self._export_thread is not None:
            return
        pending_preview = self.recalculation_timer.isActive()
        self.recalculation_timer.stop()
        file_path, _ = QFileDialog.getSaveFileName(self, "Export Filtered Image", "", "TIFF Files (*.tiff *.tif)")
        if not file_path:
            if pending_preview:
                self.dispatch_pipeline_request_if_auto()
            return
        if not file_path.lower().endswith((".tiff", ".tif")):
            file_path += ".tiff"
        try:
            parameters = self.collect_filter_parameters(self.full_raw_image.shape[:2])
            cached = self._full_cache
            processed = (cached[2] if cached is not None and cached[0] is self.full_raw_image
                         and cached[1] == parameter_signature(parameters) else None)
            request = dict(source=self.full_raw_image.copy(), parameters=parameters,
                display=self.collect_display_parameters(), file_path=file_path,
                original_path=self.source_path or file_path,
                scale_factor=self.full_raw_image.shape[0]/float(self.preview_image.shape[0]),
                source_rgb=self.full_source_rgb,
                calibrate_colour=self.chk_calibrate_colour.isChecked(), white=self.source_rgb_white,
                export_layers=self.chk_export_layers.isChecked(), layers_format=self.combo_layers_format.currentData(),
                color_correction=self.chk_color_correction.isEnabled() and self.chk_color_correction.isChecked(),
                psb_exposure_ev=self.sl_psb_exposure.value()/100 if hasattr(self,'sl_psb_exposure') else 0.,
                psb_preview_jpeg=self.btn_psb_preview.isChecked() if hasattr(self,'btn_psb_preview') else False,
                input_state=self.combo_input_state.currentData(), processed=processed,
                project_settings=capture_settings(self))
            request["layer_cache"] = engine_for(self.filter_worker).snapshot(self.full_raw_image,request["source"])
        except (ValueError, TypeError, OverflowError) as error:
            self.status_label.setText(f"Status: Export failed - {error}")
            return
        self.recalculation_timer.stop()
        self.presentation_timer.stop()
        self.control_sidebar.setEnabled(False)
        self.zoom_toolbar.setEnabled(False)
        self.status_label.setText("Status: Exporting full resolution...")
        self._export_thread = ExportThread(request, self)
        self._export_thread.source_identity = self.full_raw_image
        self._export_thread.finished.connect(self._on_export_finished)
        self.export_progress.setValue(0)
        self.export_progress.setFormat("Preparing export — %p%")
        self.export_progress.show()
        self._export_thread.progress.connect(self._on_export_progress)
        self._export_thread.start()

    def _on_export_progress(self, value, label):
        self.export_progress.setValue(value)
        self.export_progress.setFormat(label+" — %p%")

    def _on_export_finished(self):
        thread = self._export_thread
        self._export_thread = None
        if (getattr(thread,'source_identity',None) is self.full_raw_image
                and thread.request.get('layer_cache') is not None):
            engine_for(self.filter_worker).absorb(thread.request['layer_cache'],
                thread.request['source'],self.full_raw_image)
        self.control_sidebar.setEnabled(True)
        self.zoom_toolbar.setEnabled(True)
        if thread.error is None:
            self.status_label.setText(thread.message)
            self.status_label.setToolTip(thread.message)
            self.status_label.setStyleSheet("color: #00ff00; font-weight: bold;")
        else:
            self.status_label.setText(f"Status: Export failed - {thread.error}")
            self.status_label.setToolTip(f"Export failed: {thread.error}\nFull traceback is available in the application console.")
            self.status_label.setStyleSheet("color: #ff3333; font-weight: bold;")
        self.export_progress.setValue(100 if thread.error is None else self.export_progress.value())
        self.export_progress.setFormat("Export complete" if thread.error is None else "Export failed")
        thread.deleteLater()
        self._log_processing_end("EXPORT", "Complete" if thread.error is None else "Failed")
        self._finish_close()

    def render_matrix_to_screen(self):
        """Snapshot widgets now; compose pixels without blocking Qt's event loop."""
        self.presentation_timer.stop()
        if self.raw_image is None or self.full_raw_image is None or self._closing or getattr(self,'_restoring_settings',False):
            return
        self._presentation_revision += 1
        if self.image_label.zoom is not None:
            self.image_label.set_pending(True)
        try:
            cache = self._full_cache
            native = (cache is not None
                      and cache[0] is self.full_raw_image and cache[3] == self._preview_revision)
            source = self.full_raw_image if native else self.raw_image
            params = self.collect_filter_parameters(source.shape, include_mask=False)
            display = self.collect_display_parameters()
            if self.show_original_mode:
                display = dict(display, blend=0.)
            self._presentation_request = dict(
                revision=self._presentation_revision, filter_revision=self._preview_revision,
                colour_revision=self._colour_revision,
                source_identity=self.full_raw_image,
                source=source, params=params, display=display, native=native,
                fallback=cache[2] if native else (self.processed_image if self.processed_image is not None else source),
                has_layers=native or getattr(self,'_has_layer_result',False),
                engine=engine_for(self.filter_worker), worker=self.filter_worker,
                rgb=self.full_source_rgb, white=self.source_rgb_white,
                calibrate=self.chk_calibrate_colour.isChecked(),
                colour_cache=self._colour_cache, preview_cache=self._preview_colour_cache,
                neutralize=neutralize_tse, set_luminosity=set_luminosity,
                psb_preview=self.btn_psb_preview.isChecked(), psb_exposure_ev=self.sl_psb_exposure.value()/100,
                psb_params=(self.collect_filter_parameters(self.full_raw_image.shape,include_mask=False)
                            if self.btn_psb_preview.isChecked() else None),
                preview_size=(self.raw_image.shape[1],self.raw_image.shape[0]))
        except (ValueError, TypeError, OverflowError):
            self._presentation_request = None
            return  # Keep the last valid view while geometry is being edited.
        self._start_presentation()

    def _on_psb_exposure_changed(self):
        if self.btn_psb_preview.isChecked():
            self.presentation_timer.start(100)
        else:
            self.lbl_psb_presentation.setText(f'Auto scale + {self.sl_psb_exposure.value()/100:+.2f} EV · Asinh 10')

    def _start_presentation(self):
        if self._presentation_thread is not None or self._presentation_request is None or self._closing:
            return
        job = self._presentation_request
        # An obsolete display job may still have computed reusable colour data.
        if job['colour_revision'] == self._colour_revision and job['source_identity'] is self.full_raw_image:
            job.update(colour_cache=self._colour_cache, preview_cache=self._preview_colour_cache)
        self._presentation_request = None
        self._presentation_thread = TaskThread(render_snapshot, job, parent=self)
        self._presentation_thread.finished.connect(self._on_presentation_finished)
        self._presentation_thread.start()

    def _on_presentation_finished(self):
        thread = self._presentation_thread
        self._presentation_thread = None
        job = thread.args[0]
        if (thread.error is None and thread.result[4] is None and not self._closing
                and job['colour_revision'] == self._colour_revision
                and job['source_identity'] is self.full_raw_image):
            self._colour_cache, self._preview_colour_cache = thread.result[2:4]
        if (not self._closing and job['revision'] == self._presentation_revision
                and job['source_identity'] is self.full_raw_image
                and job['filter_revision'] == self._preview_revision):
            if thread.error is not None:
                self.status_label.setText(f'Status: Presentation failed — {thread.error}')
                self.image_label.set_pending(True,'Native rendering failed · see status')
            else:
                final, pixels, self._colour_cache, self._preview_colour_cache, colour_error, native_pixels, psb_settings = thread.result
                self.last_preview_presentation = final
                if psb_settings is not None:
                    pending = ' · filters pending calculation' if psb_settings.get('pending_filters') else ''
                    self.lbl_psb_presentation.setText(f"Auto scale: {psb_settings['automatic_scale']:.5g} · Exposure: {psb_settings['exposure_ev']:+.2f} EV\nPSB preview{pending} · Color Correction excluded")
                else:
                    self.lbl_psb_presentation.setText(f'Auto scale + {self.sl_psb_exposure.value()/100:+.2f} EV · Asinh 10')
                if colour_error:
                    with QSignalBlocker(self.chk_calibrate_colour):
                        self.chk_calibrate_colour.setChecked(False)
                    self.status_label.setText(f'Status: Colour neutralization disabled — {colour_error}')
                if native_pixels is not None:
                    self._native_display_revision=self._presentation_revision
                    self._native_filter_revision=self._preview_revision
                self._install_display_pixels(pixels,native_pixels)
        thread.result = None
        thread.args = ()
        thread.deleteLater()
        self._start_presentation()
        self._finish_close()

    def _install_display_pixels(self, display_img, native_pixels=None):
        self._display_pixels=display_img
        h,w=self.full_raw_image.shape[:2]
        self.image_label.set_images(display_img,native_pixels,w,h)
        self.image_label.set_pending(self.image_label.zoom is not None and native_pixels is None)
        for button in self.zoom_buttons.buttons():
            button.setEnabled(True)
        self.trigger_circle_redraw()
        self._update_view_scale_label()

    def _update_view_scale_label(self):
        if not hasattr(self,'lbl_scale_info') or self.full_raw_image is None:
            return
        h,w=self.full_raw_image.shape[:2]
        rect=self.image_label.image_rect()
        physical_width=rect.width()*self.image_label.devicePixelRatioF()
        zoom=physical_width/w if physical_width>0 else 0
        buffer_scale=(1. if self.image_label._native is not None else
                      h/float(self.preview_image.shape[0]) if self.preview_image is not None else 1.)
        self.lbl_scale_info.setText(f'Pipeline: {buffer_scale:.2f}x | Display: {100*zoom:.1f}% ({w}×{h}px native)')
        self.lbl_view_state.setText('Fit' if self.image_label.zoom is None else
                                   f'{100*self.image_label.zoom}% · native' if self.image_label._native is not None else
                                   'Preparing native view…')
        if self.btn_psb_preview.isChecked():
            self.lbl_view_state.setText(self.lbl_view_state.text()+' · PSB preview')

    def set_preview_zoom(self, zoom):
        if self.full_raw_image is None or self._closing:
            return
        self.zoom_buttons.button(0 if zoom is None else zoom).setChecked(True)
        self.image_label.set_zoom(zoom)
        if zoom is None:
            return
        ready=(self.image_label._native is not None
               and self._native_filter_revision == self._preview_revision
               and self._native_display_revision == self._presentation_revision
               and not self.presentation_timer.isActive())
        if ready:
            return
        self.image_label.set_pending(True)
        cache=self._full_cache
        if cache is not None and cache[0] is self.full_raw_image and cache[3] == self._preview_revision:
            scheduled=self._presentation_request or (self._presentation_thread.args[0] if self._presentation_thread is not None else None)
            if (scheduled is None or not scheduled['native']
                    or scheduled['revision'] != self._presentation_revision
                    or scheduled['filter_revision'] != self._preview_revision
                    or self.presentation_timer.isActive()):
                self.render_matrix_to_screen()
            return
        # A second zoom click must not cancel the same native job already running.
        if (self.is_processing and self._running_full_job
                and self._running_revision == self._preview_revision
                and self._running_full_source is self.full_raw_image):
            return
        self.dispatch_pipeline_request()

    def _finish_close(self):
        if self._closing:
            self.close()

    def closeEvent(self, event: QCloseEvent):
        """Defer closing until background tasks finish; keep Qt responsive."""
        self._closing = True
        self.recalculation_timer.stop()
        self.presentation_timer.stop()
        self._presentation_request = None
        self.in_window_tooltips.detach()
        self.filter_worker.cancel()
        self.persistent_thread.quit()
        busy = (self._export_thread is not None or self._load_thread is not None
                or self._geometry_thread is not None or self._presentation_thread is not None
                or self.background.thread is not None
                or self.persistent_thread.isRunning())
        if busy:
            self.control_sidebar.setEnabled(False)
            self.zoom_toolbar.setEnabled(False)
            self.status_label.setText('Status: Finishing background tasks before closing...')
            event.ignore()
        else:
            event.accept()
