import os
import sys

# Impor antarmuka asli Anda
from gui.main_window import MainWindow
from gui.mini_window import MiniWindow
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtNetwork import QLocalServer, QLocalSocket
from PyQt6.QtWidgets import QApplication


class SingleApplication(QApplication):
    messageReceived = pyqtSignal(str)

    def __init__(self, argv, unique_key):
        super().__init__(argv)
        self._unique_key = unique_key
        self.is_running = False

        # 1. Cek apakah Pro Extractor sudah terbuka
        socket = QLocalSocket()
        socket.connectToServer(self._unique_key)

        if socket.waitForConnected(500):
            self.is_running = True
            # Jika sudah terbuka, kirim lokasi file ke jendela yang sedang aktif
            if len(argv) > 1:
                file_path = argv[-1]
                socket.write(file_path.encode("utf-8"))
                socket.waitForBytesWritten(500)
            return

        # 2. Jika belum terbuka, buat jalur komunikasi baru
        self.server = QLocalServer()
        self.server.removeServer(self._unique_key)
        self.server.listen(self._unique_key)
        self.server.newConnection.connect(self.handle_message)

    def handle_message(self):
        # Tangkap pesan dari jendela ganda yang mencoba terbuka
        socket = self.server.nextPendingConnection()
        if socket.waitForReadyRead(500):
            file_path = socket.readAll().data().decode("utf-8")
            self.messageReceived.emit(file_path)


if __name__ == "__main__":
    app = SingleApplication(sys.argv, "ProExtractor_App_Key_V1")
    app.setStyle("Fusion")

    # Jika aplikasi sudah berjalan, matikan proses yang baru ini agar tidak dobel
    if app.is_running:
        sys.exit(0)

    # Membaca perintah dari Windows Registry
    args = sys.argv[1:]
    command = "--open"
    file_paths = []

    if args:
        if args[0].startswith("--"):
            command = args[0]
            file_paths = args[1:]
        else:
            file_paths = args

    dest_folder = os.path.dirname(file_paths[0]) if file_paths else ""
    window = None

    # Mengarahkan perintah ke UI yang tepat
    if command == "--open" or not args:
        window = MainWindow()
        if file_paths:
            window.add_files(file_paths)

    elif command == "--extract-to-folder":
        window = MiniWindow(
            file_paths, dest_folder, mode="dialog", create_subfolder=True
        )

    elif command == "--extract-here":
        window = MiniWindow(file_paths, dest_folder, mode="instant")

    elif command == "--extract-here-trash":
        window = MiniWindow(
            file_paths,
            dest_folder,
            mode="instant",
            delete_original=True,
            delete_method="Ke Recycle Bin",
        )

    elif command == "--extract-here-del":
        window = MiniWindow(
            file_paths,
            dest_folder,
            mode="instant",
            delete_original=True,
            delete_method="Permanen",
        )

    else:
        window = MainWindow()

    if window:
        window.show()

        # Fungsi ini bertugas memasukkan file yang diblok ke dalam UI yang sudah tampil
        def receive_new_file(new_file_path):
            new_file_path = os.path.normpath(new_file_path)

            # Jika sedang di mode dialog (Ekstrak ke folder...)
            if isinstance(window, MiniWindow) and window.mode == "dialog":
                existing_items = [
                    window.file_list.item(i).text()
                    for i in range(window.file_list.count())
                ]
                if new_file_path not in existing_items:
                    window.file_list.addItem(new_file_path)

            # Jika sedang di mode aplikasi penuh (Buka dengan Pro Extractor)
            elif isinstance(window, MainWindow):
                window.add_files([new_file_path])

        # Hubungkan sinyal penerima pesan dengan fungsi penambah list di atas
        app.messageReceived.connect(receive_new_file)

    sys.exit(app.exec())
