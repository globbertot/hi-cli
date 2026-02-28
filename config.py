from configparser import ConfigParser
from platformdirs import PlatformDirs
from pathlib import Path

class Config:
    def __init__(self):
        self.dirs = PlatformDirs("hicli", "globbertot")
        self.config = ConfigParser()

        self.settings = {
            "lang": "jp",
            "deleteVidesoAfterWatch": True,
            "autoSkipIntros": False,
            "outputVideosLocation": self.dirs.user_videos_dir,
            "configDir": self.dirs.user_config_dir,
            "preferredServer": 0,
        }

        self.load()

    def save(self):
        savePath = Path(self.settings["configDir"])
        savePath.mkdir(parents=True, exist_ok=True)

        if not self.config.has_section("main"):
            self.config.add_section("main")

        for key, val in self.settings.items():
            self.config.set("main", key, str(val))

        with open(savePath / "config.ini", 'w') as f:
            self.config.write(f)

        return True

    def load(self):
        loadPath = Path(self.settings["configDir"])
        if not loadPath.exists():
            self.save() # save with defaults
            return

        self.config.read(f"{loadPath}/config.ini")
        for key in self.settings:
            if self.config.has_option("main", key):
                val = self.config.get("main", key)

                if val.lower() in ["true", "false"]:
                    val = self.config.getboolean("main", key)

                self.settings[key] = val
        return True

    def get(self, setting):
        return self.settings.get(setting)
