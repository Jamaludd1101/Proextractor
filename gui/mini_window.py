import os

from core.worker import WorkerThread
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MiniWindow(QWidget):
    def __init__(
        self,
        file_paths,
        dest_folder,
        mode="dialog",
        create_subfolder=True,
        delete_original=False,
        delete_method="",
    ):
        super().__init__()
        # Pastikan file_paths berupa list
        self.file_paths = file_paths if isinstance(file_paths, list) else [file_paths]
        self.dest_folder = dest_folder
        self.mode = mode
        self.worker = None

        self.setWindowTitle("Pro Extractor - Ekstraksi")
        self.setFixedSize(540, 480 if self.mode == "dialog" else 220)
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        self.layout = QVBoxLayout(self)

        if self.mode == "dialog":
            self.init_dialog_ui(create_subfolder, delete_original, delete_method)
        else:
            self.init_instant_ui(delete_original, delete_method)

    # ------------------ UI MODE DIALOG (Ekstrak ke folder...) ------------------
    def init_dialog_ui(self, create_subfolder, delete_original, delete_method):
        # 1. List File (Bisa Tambah & Hapus)
        group_files = QGroupBox("Daftar Berkas Terpilih")
        layout_files = QVBoxLayout(group_files)

        self.file_list = QListWidget()
        for f in self.file_paths:
            self.file_list.addItem(f)
        layout_files.addWidget(self.file_list)

        btn_files_layout = QHBoxLayout()
        self.btn_add_file = QPushButton("+ Tambah File")
        self.btn_add_file.clicked.connect(self.add_file)
        self.btn_remove_file = QPushButton("- Hapus File")
        self.btn_remove_file.clicked.connect(self.remove_file)

        btn_files_layout.addWidget(self.btn_add_file)
        btn_files_layout.addWidget(self.btn_remove_file)
        layout_files.addLayout(btn_files_layout)

        self.layout.addWidget(group_files)

        # 2. Lokasi Ekstraksi & Folder Favorit
        group_dest = QGroupBox("Lokasi Tujuan (Folder Favorit)")
        layout_dest = QHBoxLayout(group_dest)

        self.combo_dest = QComboBox()
        self.combo_dest.setEditable(True)
        self.combo_dest.addItem(self.dest_folder)

        # Daftar Folder Favorit Default
        favorites = [
            os.path.expanduser("~\\Downloads"),
            os.path.expanduser("~\\Desktop"),
            os.path.expanduser("~\\Documents"),
        ]
        for fav in favorites:
            if fav != self.dest_folder:
                self.combo_dest.addItem(fav)

        self.btn_browse = QPushButton("Browse...")
        self.btn_browse.clicked.connect(self.browse_folder)

        layout_dest.addWidget(self.combo_dest, 1)
        layout_dest.addWidget(self.btn_browse)
        self.layout.addWidget(group_dest)

        # 3. Pengaturan Ekstraksi
        group_settings = QGroupBox("Pengaturan")
        grid = QGridLayout(group_settings)

        self.chk_subfolder = QCheckBox("Buka folder baru (Subfolder)")
        self.chk_subfolder.setChecked(create_subfolder)
        grid.addWidget(self.chk_subfolder, 0, 0)

        self.chk_delete = QCheckBox("Hapus arsip setelah selesai")
        self.chk_delete.setChecked(delete_original)
        grid.addWidget(self.chk_delete, 1, 0)

        self.combo_del_method = QComboBox()
        self.combo_del_method.addItems(["Ke Recycle Bin", "Permanen"])
        if delete_method == "Permanen":
            self.combo_del_method.setCurrentText("Permanen")
        self.combo_del_method.setEnabled(delete_original)
        self.chk_delete.toggled.connect(self.combo_del_method.setEnabled)
        grid.addWidget(self.combo_del_method, 1, 1)

        grid.addWidget(QLabel("Overwrite mode:"), 2, 0)
        self.combo_conflict = QComboBox()
        self.combo_conflict.addItems(
            ["Ask before overwrite", "Overwrite all", "Skip existing files"]
        )
        grid.addWidget(self.combo_conflict, 2, 1)

        self.layout.addWidget(group_settings)

        # 4. Status, Progress Bar, & Tombol Kontrol
        self.lbl_status = QLabel("Siap mengekstrak...")
        self.layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        btn_action_layout = QHBoxLayout()
        btn_action_layout.addStretch()

        self.btn_extract = QPushButton("Ekstrak")
        self.btn_extract.setFixedWidth(100)
        self.btn_extract.clicked.connect(self.start_dialog_extraction)

        self.btn_close = QPushButton("Batal")
        self.btn_close.setFixedWidth(100)
        self.btn_close.clicked.connect(self.close_or_cancel)

        btn_action_layout.addWidget(self.btn_extract)
        btn_action_layout.addWidget(self.btn_close)
        self.layout.addLayout(btn_action_layout)

    # ------------------ UI MODE INSTANT (Ekstrak di sini) ------------------
    def init_instant_ui(self, delete_original, delete_method):
        self.lbl_status = QLabel("Memulai ekstraksi otomatis...")
        self.layout.addWidget(self.lbl_status)

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_close = QPushButton("Batal")
        self.btn_close.setFixedWidth(100)
        self.btn_close.clicked.connect(self.close_or_cancel)
        btn_layout.addWidget(self.btn_close)

        self.layout.addLayout(btn_layout)

        # Langsung eksekusi ekstraksi otomatis
        options = {
            "create_folder": False,
            "delete_original": delete_original,
            "delete_method": delete_method,
            "conflict": "Tanya",
        }
        self.run_worker(self.file_paths, self.dest_folder, options)

    # ------------------ FUNGSI KONTROL LIST FILE & FOLDER ------------------
    def add_file(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Tambah File Arsip",
            "",
            "Archive Files (*.zip *.rar *.7z *.tar *.gz *.bz2 *.xz)",
        )
        for f in files:
            f_norm = os.path.normpath(f)
            if f_norm not in [
                self.file_list.item(i).text() for i in range(self.file_list.count())
            ]:
                self.file_list.addItem(f_norm)

    def remove_file(self):
        current_item = self.file_list.currentItem()
        if current_item:
            self.file_list.takeItem(self.file_list.row(current_item))

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Pilih Folder Tujuan", self.combo_dest.currentText()
        )
        if folder:
            folder = os.path.normpath(folder)
            self.combo_dest.setCurrentText(folder)
            if self.combo_dest.findText(folder) == -1:
                self.combo_dest.addItem(folder)

    # ------------------ EKSEKUSI WORKER ------------------
    def start_dialog_extraction(self):
        # Ambil daftar file dari QListWidget
        current_files = [
            self.file_list.item(i).text() for i in range(self.file_list.count())
        ]
        if not current_files:
            QMessageBox.warning(self, "Peringatan", "Daftar file arsip kosong!")
            return

        dest = self.combo_dest.currentText()
        conflict_map = {
            "Ask before overwrite": "Tanya",
            "Overwrite all": "Timpa",
            "Skip existing files": "Lewati",
        }

        options = {
            "create_folder": self.chk_subfolder.isChecked(),
            "delete_original": self.chk_delete.isChecked(),
            "delete_method": self.combo_del_method.currentText(),
            "conflict": conflict_map.get(self.combo_conflict.currentText(), "Tanya"),
        }

        # Nonaktifkan komponen UI saat ekstraksi berjalan
        self.btn_extract.setEnabled(False)
        self.btn_add_file.setEnabled(False)
        self.btn_remove_file.setEnabled(False)
        self.combo_dest.setEnabled(False)
        self.btn_browse.setEnabled(False)

        self.run_worker(current_files, dest, options)

    def run_worker(self, files, dest, options):
        self.lbl_status.setText("Sedang mengekstrak...")
        self.worker = WorkerThread(files, dest, options)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.log.connect(self.lbl_status.setText)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def close_or_cancel(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.btn_close.setEnabled(False)
            self.lbl_status.setText("Membatalkan...")
        else:
            self.close()

    def on_finished(self, success, msg):
        # Setelah selesai, ubah tombol menjadi "Keluar" dan tampilkan status
        self.btn_close.setText("Keluar")
        self.btn_close.setEnabled(True)

        if success:
            self.lbl_status.setText("Ekstraksi Selesai!")
            self.progress_bar.setValue(100)
        else:
            self.lbl_status.setText(f"Dibatalkan / Error: {msg}")
