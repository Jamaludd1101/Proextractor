import tarfile
import zipfile

import py7zr
import rarfile

rarfile.UNRAR_TOOL = "unrar.exe"


class ArchiveExtractor:
    @staticmethod
    def get_extractor(file_path):
        ext = file_path.lower()
        if ext.endswith(".zip"):
            return ZipHandler(file_path)
        elif ext.endswith(".7z"):
            return SevenZipHandler(file_path)
        elif ext.endswith(".rar"):
            return RarHandler(file_path)
        elif ext.endswith((".tar", ".gz", ".bz2", ".xz", ".tgz")):
            return TarHandler(file_path)
        return None


class BaseHandler:
    def __init__(self, file_path):
        self.file_path = file_path
        self.password = None

    def set_password(self, pwd):
        self.password = pwd


class ZipHandler(BaseHandler):
    def get_metadata(self):
        with zipfile.ZipFile(self.file_path, "r") as z:
            info = z.infolist()
            return {"file_count": len(info), "size": sum(i.file_size for i in info)}

    def test_archive(self):
        with zipfile.ZipFile(self.file_path, "r") as z:
            if z.testzip() is not None:
                raise Exception("File ZIP Rusak")

    def extract_all(self, dest):
        with zipfile.ZipFile(self.file_path, "r") as z:
            if self.password:
                z.setpassword(self.password.encode("utf-8"))
            z.extractall(dest)


class SevenZipHandler(BaseHandler):
    def get_metadata(self):
        with py7zr.SevenZipFile(self.file_path, "r", password=self.password) as z:
            return {
                "file_count": len(z.getnames()),
                "size": z.archiveinfo().uncompressed,
            }

    def test_archive(self):
        with py7zr.SevenZipFile(self.file_path, "r", password=self.password) as z:
            if not z.test():
                raise Exception("File 7Z Rusak")

    def extract_all(self, dest):
        with py7zr.SevenZipFile(self.file_path, "r", password=self.password) as z:
            z.extractall(dest)


class RarHandler(BaseHandler):
    def get_metadata(self):
        with rarfile.RarFile(self.file_path, "r") as r:
            if r.needs_password() and not self.password:
                raise rarfile.NeedFirstVolume()
            return {
                "file_count": len(r.infolist()),
                "size": sum(i.file_size for i in r.infolist()),
            }

    def test_archive(self):
        with rarfile.RarFile(self.file_path, "r") as r:
            r.testrar()

    def extract_all(self, dest):
        with rarfile.RarFile(self.file_path, "r") as r:
            r.extractall(dest, pwd=self.password)


class TarHandler(BaseHandler):
    def get_metadata(self):
        with tarfile.open(self.file_path, "r") as t:
            members = t.getmembers()
            return {"file_count": len(members), "size": sum(m.size for m in members)}

    def test_archive(self):
        with tarfile.open(self.file_path, "r") as t:
            pass

    def extract_all(self, dest):
        with tarfile.open(self.file_path, "r") as t:
            t.extractall(dest)
