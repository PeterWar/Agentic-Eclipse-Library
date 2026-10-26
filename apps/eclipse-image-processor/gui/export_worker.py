"""File export has no widgets and reports completion through QThread.finished."""
import traceback
from PySide6.QtCore import QThread, Signal
from core.export import export_images


class ExportThread(QThread):
    progress = Signal(int,str)

    def __init__(self, request, parent=None):
        super().__init__(parent)
        self.request = request
        self.message = None
        self.error = None

    def run(self):
        try:
            self.message = export_images(**self.request,progress=self.progress.emit)
        except Exception as error:
            self.error = str(error)
            traceback.print_exc()
