import os

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget


class DropZone(QWidget):
    files_dropped = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        layout = QVBoxLayout()
        self.label = QLabel("SERET & LEPAS ARSIP DI SINI")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setStyleSheet("""
            QWidget { border: 2px dashed #aaa; border-radius: 8px; background-color: #f0f0f0; }
            QLabel { font-size: 14px; font-weight: bold; color: #555; border: none; background: transparent; }
        """)
        self.setMinimumHeight(100)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
            self.setStyleSheet(
                "border: 2px dashed #2196F3; background-color: #e3f2fd; border-radius: 8px;"
            )
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setStyleSheet(
            "border: 2px dashed #aaa; background-color: #f0f0f0; border-radius: 8px;"
        )

    def dropEvent(self, event):
        self.setStyleSheet(
            "border: 2px dashed #aaa; background-color: #f0f0f0; border-radius: 8px;"
        )
        files = [
            u.toLocalFile()
            for u in event.mimeData().urls()
            if os.path.isfile(u.toLocalFile())
        ]
        if files:
            self.files_dropped.emit(files)
