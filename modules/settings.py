import json

class Settings:
    def __init__(self):
        self.path = "data/settings.json"
        self.settings = None
        self.load_settings()

    def load_settings(self):
        try:
            with open(self.path, "r") as f:
                self.settings = json.load(f)

        except FileNotFoundError:
            with open(self.path, "w") as f:
                json.dump({"prefix": "!"}, f, indent=4)

            with open(self.path, "r") as f:
                self.settings = json.load(f)
        except json.JSONDecodeError:
            self.settings = {}

    def get(self, key: str, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def save_settings(self):
        with open(self.path, "w") as f:
            json.dump(self.settings, f, indent=4)

