from pathlib import Path
from videoPlayer import VideoPlayer

import json


class LocalSystem:
    def __init__(self, baseDir):
        self.baseDir = Path(baseDir).expanduser()

    def getAllAnime(self):
        rtn = []
        for file in self.baseDir.iterdir():
            if file.is_dir():
                rtn.append({"name": file.name, "path": str(file)})
        return rtn

    def saveAnimeInfo(self, anime, info):
        saveFile = Path(self.baseDir / str(anime["name"]) / "info.json").expanduser()
        saveFile.parent.mkdir(parents=True, exist_ok=True)

        with open(saveFile, 'w') as f:
            json.dump(info, f)

    def getAnimeInfo(self, anime):
        fileInPath = Path(self.baseDir / str(anime["name"]) / "info.json").expanduser()
        if not fileInPath.is_file():
            return None

        with open(fileInPath, 'r') as f:
            return json.load(f)

    def updateEpisodeSeen(self, anime, episode):
        animeObj = {"name": anime}

        info = self.getAnimeInfo(animeObj)
        if not info:
            raise ValueError("Could not get anime info to save last ep watched")

        info["last ep watched"] = episode
        self.saveAnimeInfo(animeObj, info)

    def printAnimeInfo(self, info):
        print("-- Anime info --")
        for val, key in info.items():
            if (val == 'episodes'):
                continue
            if (val == 'next ep' and isinstance(key, dict)):
                print(f"{val}: {key["date"]} at {key["time"]}")
                continue

            print(f"{val}: {key}")
        print("-- End info --\n\n")

    def getAllEpisodes(self, anime):
        info = self.getAnimeInfo(anime)
        episodes = info["episodes"]

        rtn = []
        path = self.baseDir / str(anime["path"])

        for episode in episodes:
            for file in path.iterdir():
                if file.is_dir() and file.name == episode["title"]:
                    isLastSeen = info["last ep watched"] == file.name
                    rtn.append({"name": file.name, "path": str(file), "lastSeen": isLastSeen})
        return rtn

    def getEpisodeContent(self, episode):
        inEpisodeDir = (self.baseDir / str(episode["path"]))

        videoPath = inEpisodeDir / "output.mp4"
        subPath = inEpisodeDir / "sub.vtt"
        introOutroPath = inEpisodeDir / "introOutro.txt"

        return {"video": videoPath, "sub": subPath,
                "introOutro": introOutroPath}

    def isValid(self, file):
        return file.exists()

    def getPathObj(self, file):
        return Path(file).expanduser()

    def deleteFile(self, content):
        if not isinstance(content, Path):
            content = self.getPathObj(content)

        if content.is_file():
            content.unlink(missing_ok=True)
        else:
            for child in content.iterdir():
                self.deleteFile(child)
            content.rmdir()

    def printInfo(self, info):
        for i in range(len(info)):
            lastSeen = info[i].get("lastSeen")
            lastSeenText = "< last episode watched" if lastSeen else ''

            print(f"{i}. {info[i]['name']} {lastSeenText}")

    def parseIntroOutroFile(self, filePath):
        try:
            with open(filePath, 'r') as f:
                intro = next(f).strip()
                outro = next(f).strip()

                return intro, outro
        except FileNotFoundError:
            print(f"Intro/outro file not found at {filePath}")
            return (None, None)

    def playAt(self, animeName, episodeName, sub, skipIntroOutro):
        episodePath = self.baseDir / animeName / episodeName
        locations = self.getEpisodeContent({"path": episodePath})

        if not (locations["video"] and locations["video"].exists()):
            raise ValueError(f"File to play does not exist| file: {locations["video"]}")

        useSub = locations["sub"] and self.isValid(locations["sub"]) and sub
        intro, outro = self.parseIntroOutroFile(locations["introOutro"])

        self.updateEpisodeSeen(animeName, episodeName)
        player = VideoPlayer(locations)
        player.play(useSub, intro, outro, skipIntroOutro=skipIntroOutro)
