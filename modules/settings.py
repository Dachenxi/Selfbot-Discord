import json


class Settings:
    def __init__(self):
        self.path = "data/settings.json"
        self.default_settings = {
                    "prefix": "!",
                    "server": 950039010733076560,
                    "virtual_fisher": {
                        "bot_id": 574652751745777665,
                        "delay": [60, 600],
                        "sell_command_id": 912432960643416116,
                        "fish_command_id": 912432960643416115,
                        "verify_command_id": 912432961222238220,
                    }
                }
        self.load_settings()


    def load_settings(self):
        try:
            with open(self.path, "r") as f:
                self.settings = json.load(f)

        except FileNotFoundError:
            with open(self.path, "w") as f:
                json.dump(self.default_settings, f, indent=4)

            with open(self.path, "r") as f:
                self.settings = json.load(f)
        except json.JSONDecodeError as e:
            self.settings = {}

    def get(self, key, default=None):
        return self.settings.get(key, default)

    def set(self, key, value):
        self.settings[key] = value
        self.save_settings()

    def save_settings(self):
        with open(self.path, "w") as f:
            json.dump(self.settings, f)
