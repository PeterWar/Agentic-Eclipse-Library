"""Sky-sample controls and asynchronous source preparation before enhancement layers."""
import numpy as np
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QCheckBox,QLabel,QPushButton
from core.background import equalize_background,sample_grid,sample_allowed
from .background_tasks import TaskThread
from .components import CollapsibleSection
from .factories import create_slider,create_slider_float


class BackgroundExtraction(QObject):
    def __init__(self,window):
        super().__init__(window)
        self.w=window
        self.base=None;self.points=None;self.report=None
        self.dirty=False;self.thread=None;self.export_pending=False

    def build(self,layout):
        w=self.w
        w.sec_background=CollapsibleSection('BACKGROUND GRADIENT',has_checkbox=False,is_expanded=False)
        panel=w.sec_background.content_layout
        w.sec_background.toggle_btn.setToolTip('Fit a linear sky plane outside the corona. Removes slopes only, before all filters; original data remain available.')
        w.chk_background=QCheckBox('Equalize background gradient')
        w.chk_background.setToolTip('Subtract an independently fitted linear slope from each source channel. Preserve the mean fitted sky level. Requires linear input; review samples for faint corona.')
        panel.addWidget(w.chk_background)
        w.sl_background_radius,_=create_slider_float('Exclude corona (disk radii)',15,300,60,10.,panel,
            tooltip='No sample patch may touch this circle. Six disk radii is only a starting point: exclude all visible and faint coronal structures. Changing this regenerates samples.')
        w.sl_background_grid,_=create_slider('Samples per line',6,40,16,panel,
            tooltip='Candidate grid density. Patches inside the excluded circle, missing data and zero-filled areas are rejected. Changing density regenerates samples.')
        w.btn_background_generate=QPushButton('Regenerate samples')
        w.btn_background_generate.setToolTip('Replace manual edits with a fresh grid outside the coronal exclusion radius. Fit immediately when enabled.')
        panel.addWidget(w.btn_background_generate)
        w.btn_background_samples=QPushButton('Show / edit sky samples')
        w.btn_background_samples.setCheckable(True)
        w.btn_background_samples.setToolTip('Show the exclusion circle and samples. Left-click adds a sample; right-click removes a nearby sample. Middle-drag pans; Ctrl-click / Command-click still moves the lunar center.')
        panel.addWidget(w.btn_background_samples)
        w.lbl_background_fit=QLabel('Background equalization is off.')
        w.lbl_background_fit.setWordWrap(True)
        w.lbl_background_fit.setToolTip('Fit status. This is an additive preprocessing correction, not an enhancement layer. No absolute sky level is subtracted.')
        panel.addWidget(w.lbl_background_fit)
        w.chk_background.toggled.connect(lambda _:self.invalidate(False))
        w.sl_background_radius.valueChanged.connect(lambda _:self.invalidate(True))
        w.sl_background_grid.valueChanged.connect(lambda _:self.invalidate(True))
        w.btn_background_generate.clicked.connect(self.generate)
        w.btn_background_samples.toggled.connect(self.overlay)
        w.image_label.background_point_added.connect(self.add_point)
        w.image_label.background_point_removed.connect(self.remove_point)
        layout.addWidget(w.sec_background)

    def geometry(self):
        return tuple(float(getattr(self.w,'txt_'+key).text()) for key in ('x','y','r'))

    def invalidate(self,regenerate=True):
        w=self.w
        if getattr(w,'_restoring_settings',False):return
        if regenerate:self.points=None
        if self.base is not None or w.full_raw_image is not None:
            self.dirty=True
            w.lbl_background_fit.setText('Settings changed — recalculate background.' if w.chk_background.isChecked() else
                                        'Disabled — recalculate to restore original input.')
            w.dispatch_pipeline_request_if_auto()
        self.overlay()

    def generate(self):
        w=self.w
        if w.full_raw_image is None:return
        try:self.points=sample_grid(w.full_raw_image.shape,self.geometry(),w.sl_background_radius.value()/10,w.sl_background_grid.value())
        except ValueError as error:
            w.lbl_background_fit.setText(str(error));return
        w.btn_background_samples.setChecked(True)
        self.invalidate(False)
        if w.chk_background.isChecked():w.dispatch_pipeline_request()

    def overlay(self,*_):
        w=self.w
        try:radius=self.geometry()[2]*w.sl_background_radius.value()/10
        except ValueError:radius=0
        w.image_label.set_background_samples(self.points or [],radius,w.btn_background_samples.isChecked())

    def add_point(self,x,y):
        w=self.w
        point=(int(x),int(y))
        try:
            if not sample_allowed(point,w.full_raw_image.shape,self.geometry(),w.sl_background_radius.value()/10):
                w.lbl_background_fit.setText('Sample rejected: inside excluded corona or too close to the image edge.')
                return
            if self.points is None:
                self.points=sample_grid(w.full_raw_image.shape,self.geometry(),w.sl_background_radius.value()/10,w.sl_background_grid.value())
        except (ValueError,TypeError):return
        if len(self.points)>=5000:
            w.lbl_background_fit.setText('Maximum of 5000 sky samples reached.');return
        if point not in self.points:self.points.append(point)
        self.invalidate(False)

    def remove_point(self,x,y):
        if not self.points:return
        points=np.asarray(self.points)
        index=int(np.argmin(np.sum((points-[x,y])**2,axis=1)))
        rect=self.w.image_label.image_rect()
        scale=rect.width()/self.w.image_label.native_w
        if np.linalg.norm(points[index]-[x,y])*scale<=12:
            self.points.pop(index);self.invalidate(False)

    def reset_source(self,loaded,project):
        self.base=loaded;self.report=None
        if project is None:self.points=None
        self.dirty=self.w.chk_background.isChecked()
        self.w.lbl_background_fit.setText('Background fit pending.' if self.dirty else 'Background equalization is off.')
        self.overlay()

    def start(self):
        w=self.w
        if self.thread is not None:return
        if self.base is None:
            self.base=dict(full=w.full_raw_image,rgb=w.full_source_rgb,preview=w.preview_image)
        try:
            if w.chk_background.isChecked() and w.combo_input_state.currentData()!='linear':
                raise ValueError('Background equalization requires linear input')
            self.thread=TaskThread(equalize_background,self.base,self.geometry(),w.sl_background_radius.value()/10,
                                   w.sl_background_grid.value(),self.points,w.chk_background.isChecked(),parent=w)
            self.thread.finished.connect(self.finished)
            w.control_sidebar.setEnabled(False);w.zoom_toolbar.setEnabled(False)
            w.status_label.setText('Status: Fitting linear background…')
            self.thread.start()
        except Exception as error:
            self.thread=None;self.export_pending=False;w.lbl_background_fit.setText(str(error));w.status_label.setText(f'Status: Background failed — {error}');w.status_label.setToolTip(str(error))

    def finished(self):
        w=self.w;thread=self.thread;self.thread=None
        w.control_sidebar.setEnabled(True);w.zoom_toolbar.setEnabled(True)
        try:
            if w._closing:return
            if thread.error is not None:raise ValueError(thread.error)
            result=thread.result
            self.points=result['points'];self.report=result['report'];self.dirty=False
            w.full_raw_image=result['full'];w.full_source_rgb=result['rgb']
            w._display_reference_source=w.full_raw_image;w._display_bounds=result.get('display_bounds')
            w.raw_image=w.preview_image=result['preview'];w.processed_image=w.raw_image
            w._has_layer_result=False;w._full_cache=None
            w._colour_cache=w._preview_colour_cache=None;w._colour_revision+=1
            w._native_display_revision=w._native_filter_revision=None
            w.lbl_background_fit.setText(f"Plane fitted: {self.report['inliers']}/{self.report['samples']} sky samples; mean sky preserved." if self.report else 'Background equalization is off.')
            self.overlay();w.render_matrix_to_screen()
            if self.export_pending:
                self.export_pending=False;w.export_image_action()
            else:w.dispatch_pipeline_request()
        except Exception as error:
            self.export_pending=False
            w.lbl_background_fit.setText(str(error));w.status_label.setText(f'Status: Background failed — {error}');w.status_label.setToolTip(str(error))
        finally:
            thread.deleteLater();w._finish_close()
