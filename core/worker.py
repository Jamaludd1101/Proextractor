import os
import shutil

from PyQt6.QtCore import QThread, pyqtSignal
from send2trash import send2trash

from .extractor import ArchiveExtractor


class WorkerThread(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, files, dest, options):
        super().__init__()
        self.files = files
        self.dest = dest
        self.options = options
        self.is_cancelled = False
        self.extracted_paths = []

    def cancel(self):
        self.is_cancelled = True

    def run(self):
        total_files = len(self.files)
        success_count = 0

        for i, file_path in enumerate(self.files):
            if self.is_cancelled:
                break

            self.log.emit(f"Mengekstrak: {os.path.basename(file_path)}...")
            handler = ArchiveExtractor.get_extractor(file_path)

            if not handler:
                self.log.emit(f"Format tidak didukung: {file_path}")
                continue

            target_dir = self.dest
            if self.options.get("create_folder"):
                folder_name = os.path.splitext(os.path.basename(file_path))[0]
                target_dir = os.path.join(self.dest, folder_name)
                os.makedirs(target_dir, exist_ok=True)
                self.extracted_paths.append(target_dir)

            try:
                handler.extract_all(target_dir)
                success_count += 1
            except Exception as e:
                err_str = str(e).lower()
                if "password" in err_str or "encrypted" in err_str:
                    self.log.emit(f"Gagal: Arsip dikunci sandi ({file_path})")
                elif "unrar" in err_str:
                    self.log.emit("Gagal: Mesin RAR (unrar.exe) tidak ditemukan!")
                elif "space" in err_str:
                    self.log.emit("Gagal: Penyimpanan Penuh!")
                elif "permission" in err_str or "access is denied" in err_str:
                    self.log.emit("Gagal: Izin Ditolak atau file sedang digunakan!")
                else:
                    self.log.emit(f"Gagal/Rusak: {e!s}")

                self.is_cancelled = True
                break

            persentase = int(((i + 1) / total_files) * 100)
            self.progress.emit(persentase)

        if self.is_cancelled:
            self.log.emit("Dibatalkan! Memulihkan sistem...")
            self._rollback()
            self.finished.emit(
                False, "Proses dibatalkan. Berkas setengah jadi telah dihapus."
            )
        else:
            if success_count == total_files and self.options.get("delete_original"):
                del_method = self.options.get("delete_method", "Ke Recycle Bin")
                self.log.emit(f"Menghapus arsip asli ({del_method})...")
                for f in self.files:
                    try:
                        if del_method == "Permanen":
                            os.remove(f)
                        else:
                            send2trash(f)
                    except Exception:
                        pass

            self.progress.emit(100)
            self.finished.emit(True, "Seluruh berkas berhasil diekstrak!")

    def _rollback(self):
        for path in self.extracted_paths:
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)
