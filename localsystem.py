from pathlib import Path

import subprocess
import mpv

class LocalSystem:
    def __init__(self, baseDir):
        self.baseDir = Path(baseDir).expanduser()

    def getAllAnime(self):
        rtn = []
        for file in self.baseDir.iterdir():  
            if file.is_dir():
                rtn.append({"name": file.name, "path": str(file)})
        return rtn

    def getAllEpisodes(self, anime):
        rtn = []
        for file in (self.baseDir / str(anime["path"])).iterdir():
            if file.is_dir():
                rtn.append({"name": file.name, "path": str(file)})
        return rtn

    def getEpisodeContent(self, episode): 
        inEpisodeDir = (self.baseDir / str(episode["path"]))
        
        videoPath = inEpisodeDir / "output.mp4"
        subPath = inEpisodeDir / "sub.vtt"

        return {"video": videoPath, "sub": subPath}

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
            print(f"{i}. {info[i]['name']}")

    def playAt(self, animeName, episodeName, sub):
        episodePath = self.baseDir / animeName / episodeName
        locations = self.getEpisodeContent({"path": episodePath})

        if not (locations["video"] and locations["video"].exists()):
            raise ValueError(f"File to play does not exist| file: {locations["video"]}")

        useSub = locations["sub"] and locations["sub"].exists() and sub

        player = mpv.MPV(config="yes", input_default_bindings=True, input_vo_keyboard=True, osc=True)
        player.fullscreen = True
        player.loadfile(str(locations["video"]), sub_file=str(locations["sub"]) if useSub else '')
        player.wait_for_playback()
        player.terminate()
