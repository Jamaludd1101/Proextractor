import winreg

EXE_PATH = r"D:\Proyek-suka2\ekstraktor\dist\ProExtractor.exe"


def hapus_menu_lama(ext):
    key_path = f"Software\\Classes\\SystemFileAssociations\\{ext}\\shell"
    old_keys = [
        "ProExtractorOpen",
        "ProExtractorHere",
        "ProExtractorFolder",
        "ProExtractor",
    ]

    subkeys = [
        "shell\\cmd1\\command",
        "shell\\cmd1",
        "shell\\cmd2\\command",
        "shell\\cmd2",
        "shell\\cmd3\\command",
        "shell\\cmd3",
        "shell\\cmd4\\command",
        "shell\\cmd4",
        "shell\\cmd5\\command",
        "shell\\cmd5",
        "shell",
        "command",
    ]

    for root_key in [winreg.HKEY_CURRENT_USER, winreg.HKEY_CLASSES_ROOT]:
        for key in old_keys:
            for sub in subkeys:
                try:
                    winreg.DeleteKey(root_key, f"{key_path}\\{key}\\{sub}")
                except OSError:
                    pass
            try:
                winreg.DeleteKey(root_key, f"{key_path}\\{key}")
            except OSError:
                pass


def buat_menu_cascading(ext):
    base_path = f"Software\\Classes\\SystemFileAssociations\\{ext}\\shell\\ProExtractor"
    try:
        k_main = winreg.CreateKey(winreg.HKEY_CURRENT_USER, base_path)
        winreg.SetValueEx(k_main, "MUIVerb", 0, winreg.REG_SZ, "Pro Extractor")
        winreg.SetValueEx(k_main, "Icon", 0, winreg.REG_SZ, EXE_PATH)
        winreg.SetValueEx(k_main, "SubCommands", 0, winreg.REG_SZ, "")
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{base_path}\\shell")

        # Nama menu diperbarui ke "Buka dengan Pro Extractor"
        menus = [
            ("cmd1", "Buka dengan Pro Extractor", f'"{EXE_PATH}" --open "%1"'),
            ("cmd2", "Ekstrak di sini", f'"{EXE_PATH}" --extract-here "%1"'),
            ("cmd3", "Ekstrak ke folder...", f'"{EXE_PATH}" --extract-to-folder "%1"'),
            (
                "cmd4",
                "Ekstrak di sini (Hapus ke Recycle Bin)",
                f'"{EXE_PATH}" --extract-here-trash "%1"',
            ),
            (
                "cmd5",
                "Ekstrak di sini (Hapus Permanen)",
                f'"{EXE_PATH}" --extract-here-del "%1"',
            ),
        ]

        for cmd, name, command in menus:
            k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"{base_path}\\shell\\{cmd}")
            winreg.SetValueEx(k, "MUIVerb", 0, winreg.REG_SZ, name)
            k_cmd = winreg.CreateKey(k, "command")
            winreg.SetValue(k_cmd, "", winreg.REG_SZ, command)

        print(f"[SUKSES] Menu untuk {ext} berhasil diperbarui!")
    except Exception as e:
        print(f"[GAGAL] {ext}: {e}")


if __name__ == "__main__":
    extensions = [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".tgz"]
    for ext in extensions:
        hapus_menu_lama(ext)
        buat_menu_cascading(ext)
