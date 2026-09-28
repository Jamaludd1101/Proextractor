import json
import os


class ConfigManager:
    def __init__(self, config_file=None):
        if config_file is None:
            # Mengarahkan penyimpanan ke C:\Users\<NamaUser>\AppData\Roaming\ProExtractor
            appdata_dir = os.path.join(
                os.getenv("APPDATA", os.path.expanduser("~")), "ProExtractor"
            )
            os.makedirs(appdata_dir, exist_ok=True)
            self.config_file = os.path.join(appdata_dir, "extractor_config.json")
        else:
            self.config_file = config_file

        self.data = {"history": [], "favorites": []}
        self.load()

    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    isi = json.load(f)
                    if isinstance(isi, dict):
                        self.data["history"] = isi.get("history", [])
                        self.data["favorites"] = isi.get("favorites", [])
            except (json.JSONDecodeError, ValueError):
                self.save()

    def save(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.data, f, indent=4)
        except Exception:
            pass

    def add_history(self, path):
        if path in self.data["history"]:
            self.data["history"].remove(path)
        self.data["history"].insert(0, path)
        self.data["history"] = self.data["history"][:10]
        self.save()

    def toggle_favorite(self, path):
        if path in self.data["favorites"]:
            self.data["favorites"].remove(path)
            res = False
        else:
            self.data["favorites"].append(path)
            res = True
        self.save()
        return res

    def is_favorite(self, path):
        return path in self.data["favorites"]
