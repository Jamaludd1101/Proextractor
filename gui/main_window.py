import os

from config.manager import ConfigManager
from core.extractor import ArchiveExtractor
from core.worker import WorkerThread
from gui.drop_zone import DropZone
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pro Extractor")
        self.resize(600, 700)
        self.config_manager = ConfigManager()
        self.files_to_extract = []
        self.worker = None
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        layout = QVBoxLayout(main_widget)

        self.drop_zone = DropZone()
        self.drop_zone.files_dropped.connect(self.add_files)
        layout.addWidget(self.drop_zone)

        file_btn_layout = QHBoxLayout()
        self.btn_add_files = QPushButton("➕ Tambah Manual")
        self.btn_add_files.clicked.connect(self.browse_files_manual)

        self.btn_remove_file = QPushButton("❌ Hapus Pilihan")
        self.btn_remove_file.clicked.connect(self.remove_selected_files)

        file_btn_layout.addWidget(self.btn_add_files)
        file_btn_layout.addWidget(self.btn_remove_file)
        file_btn_layout.addStretch()
        layout.addLayout(file_btn_layout)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Nama File", "Ukuran"])
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        layout.addWidget(QLabel("Lokasi Ekstraksi:"))
        dest_layout = QHBoxLayout()
        self.dest_combo = QComboBox()
        self.dest_combo.setEditable(True)
        self.dest_combo.addItems(self.config_manager.data["favorites"])
        self.dest_combo.currentTextChanged.connect(self.check_favorite_status)
        dest_layout.addWidget(self.dest_combo, stretch=1)

        self.btn_browse = QPushButton("Telusuri...")
        self.btn_browse.clicked.connect(self.browse_dest)
        dest_layout.addWidget(self.btn_browse)

        self.btn_fav = QPushButton("☆")
        self.btn_fav.setToolTip("Tambah ke Favorit")
        self.btn_fav.clicked.connect(self.toggle_favorite)
        dest_layout.addWidget(self.btn_fav)
        layout.addLayout(dest_layout)

        opt_layout = QVBoxLayout()
        conflict_layout = QHBoxLayout()
        conflict_layout.addWidget(QLabel("Bila ada konflik:"))
        self.conflict_combo = QComboBox()
        self.conflict_combo.addItems(["Tanya", "Lewati", "Ubah Nama", "Timpa"])
        conflict_layout.addWidget(self.conflict_combo)
        conflict_layout.addStretch()
        opt_layout.addLayout(conflict_layout)

        self.cb_folder = QCheckBox("Buat folder baru untuk setiap arsip")
        self.cb_folder.setChecked(True)
        opt_layout.addWidget(self.cb_folder)

        del_layout = QHBoxLayout()
        self.cb_delete = QCheckBox("Hapus arsip asli setelah selesai")
        self.cb_delete.toggled.connect(self.toggle_delete_method)

        self.delete_method_combo = QComboBox()
        self.delete_method_combo.addItems(["Ke Recycle Bin", "Permanen"])
        self.delete_method_combo.setEnabled(False)

        del_layout.addWidget(self.cb_delete)
        del_layout.addWidget(self.delete_method_combo)
        del_layout.addStretch()
        opt_layout.addLayout(del_layout)
        layout.addLayout(opt_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.lbl_status = QLabel("Siap digunakan")
        layout.addWidget(self.lbl_status)

        btn_layout = QHBoxLayout()
        self.btn_test = QPushButton("UJI ARSIP")
        self.btn_test.clicked.connect(self.test_archives)
        btn_layout.addWidget(self.btn_test)

        self.btn_extract = QPushButton("EKSTRAK")
        self.btn_extract.clicked.connect(self.start_extraction)
        btn_layout.addWidget(self.btn_extract)

        self.btn_cancel = QPushButton("BATAL")
        self.btn_cancel.setEnabled(False)
        self.btn_cancel.clicked.connect(self.cancel_extraction)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setCentralWidget(main_widget)
        if self.config_manager.data["history"]:
            self.dest_combo.setCurrentText(self.config_manager.data["history"][0])

    def add_files(self, files):
        for f in files:
            if f not in self.files_to_extract:
                try:
                    size_mb = os.path.getsize(f) / (1024 * 1024)
                    self.files_to_extract.append(f)
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    item_name = QTableWidgetItem(os.path.basename(f))
                    item_name.setData(Qt.ItemDataRole.UserRole, f)
                    self.table.setItem(row, 0, item_name)
                    self.table.setItem(row, 1, QTableWidgetItem(f"{size_mb:.2f} MB"))
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Kesalahan",
                        f"Gagal memuat file: {os.path.basename(f)}\n{e}",
                    )

    def browse_files_manual(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Pilih Arsip",
            "",
            "Arsip (*.zip *.7z *.rar *.tar *.gz *.bz2 *.xz);;Semua File (*)",
        )
        if files:
            self.add_files(files)

    def remove_selected_files(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        rows_to_remove = sorted(
            list(set(item.row() for item in selected_items)), reverse=True
        )
        for row in rows_to_remove:
            file_path = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
            if file_path in self.files_to_extract:
                self.files_to_extract.remove(file_path)
            self.table.removeRow(row)

    def toggle_delete_method(self):
        self.delete_method_combo.setEnabled(self.cb_delete.isChecked())

    def browse_dest(self):
        folder = QFileDialog.getExistingDirectory(self, "Pilih Lokasi Ekstraksi")
        if folder:
            self.dest_combo.setCurrentText(folder)
            self.config_manager.add_history(folder)

    def check_favorite_status(self, text):
        if self.config_manager.is_favorite(text):
            self.btn_fav.setText("⭐")
        else:
            self.btn_fav.setText("☆")

    def toggle_favorite(self):
        current = self.dest_combo.currentText()
        if current:
            self.config_manager.toggle_favorite(current)
            self.check_favorite_status(current)
            self.dest_combo.clear()
            self.dest_combo.addItems(self.config_manager.data["favorites"])
            self.dest_combo.setCurrentText(current)

    def test_archives(self):
        if not self.files_to_extract:
            return
        self.lbl_status.setText("Menguji arsip...")
        for f in self.files_to_extract:
            try:
                handler = ArchiveExtractor.get_extractor(f)
                if handler:
                    handler.test_archive()
            except Exception as e:
                QMessageBox.critical(
                    self, "Uji Gagal", f"Arsip {os.path.basename(f)} rusak!\nError: {e}"
                )
                self.lbl_status.setText("Ujian gagal.")
                return
        QMessageBox.information(self, "Uji Sukses", "Semua arsip dalam kondisi baik.")
        self.lbl_status.setText("Ujian sukses.")

    def start_extraction(self):
        if not self.files_to_extract:
            QMessageBox.warning(self, "Kosong", "Tidak ada file yang dipilih!")
            return

        dest = self.dest_combo.currentText()
        if not dest or not os.path.exists(dest):
            QMessageBox.warning(
                self, "Lokasi Tidak Valid", "Folder tujuan tidak ditemukan!"
            )
            return

        options = {
            "create_folder": self.cb_folder.isChecked(),
            "delete_original": self.cb_delete.isChecked(),
            "delete_method": self.delete_method_combo.currentText(),
            "conflict": self.conflict_combo.currentText(),
        }

        self.worker = WorkerThread(self.files_to_extract, dest, options)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self.lbl_status.setText)
        self.worker.finished.connect(self.on_extraction_finished)

        self.btn_extract.setEnabled(False)
        self.btn_test.setEnabled(False)
        self.btn_add_files.setEnabled(False)
        self.btn_remove_file.setEnabled(False)
        self.btn_cancel.setEnabled(True)
        self.progress_bar.setValue(0)
        self.worker.start()

    def cancel_extraction(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.lbl_status.setText("Membatalkan...")
            self.btn_cancel.setEnabled(False)

    def on_extraction_finished(self, success, msg):
        self.btn_extract.setEnabled(True)
        self.btn_test.setEnabled(True)
        self.btn_add_files.setEnabled(True)
        self.btn_remove_file.setEnabled(True)
        self.btn_cancel.setEnabled(False)

        if success:
            QMessageBox.information(self, "Selesai", msg)
            self.table.setRowCount(0)
            self.files_to_extract.clear()
        else:
            QMessageBox.warning(self, "Informasi", msg)
