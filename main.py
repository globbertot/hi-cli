from api.hianime import HiAnime
from api.hianimedownloader import HiAnimeDownloader
from localsystem import LocalSystem
from config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed

import argparse
import sys
from datetime import date

from gui import GUI


class Main:
    def __init__(self, config, interactive):
        self.version = 0.1
        self.interactive = interactive
        self.gui = GUI(self.version)

        self.config = config

        self.api = HiAnime(self.config.get("lang"))
        self.downloader = HiAnimeDownloader(self.config.get("outputVideosLocation"))
        self.local = LocalSystem(self.config.get("outputVideosLocation"))

    def mainMenu(self):
        while True:
            actions = [
                {
                    "title": 'Search anime',
                    "callback": self.doSearchAnime
                },
                {
                    "title": 'Manage local anime',
                    "callback": self.doManageLocal
                 },
                {
                    "title": 'Check todays schedule',
                    "callback": self.doGetSchedule
                },
                {
                    "title": 'Exit',
                    "callback": self.doExit
                }
            ]

            i = self.gui.printXXMenu(actions=actions, menuName="Main Menu",
                                     hasBack=False)
            action = actions[i].get("callback")

            if action:
                action()

    def doGetSchedule(self):
        self.gui.printBanner()
        t = date.today()
        schedule = self.api.getSchedule(t)

        self.gui.printSchedule(schedule)
        self.gui.pause("Press enter to continue")

    def doExit(self):
        self.gui.print("[i]Bye![/i]")
        sys.exit()

    def doManageLocal(self):
        anime = self.getLocalAnime()
        if anime is None:
            return

        actions = [
            {
                "title": "Check anime",
                "callback": lambda: self.doCheckAnime(anime)
            },
            {
                "title": "Update anime info",
                "callback": lambda: self.doUpdateAnimeInfo(anime)
            },
            {
                "title": "Delete anime",
                "callback": lambda: self.doDelete(anime)
            }
        ]

        i = self.gui.printXXMenu(actions=actions, menuName="Manage local")
        if i is None:
            return

        action = actions[i].get("callback")
        if action:
            action()

    def getLocalAnime(self):
        msg = "-- [b]Installed Anime[/b] --\nWhich one do you want to manage"

        self.gui.print(msg)
        localAnime = self.local.getAllAnime()

        return self.gui.chooseFromArr(arr=localAnime, titleToGet="name")

    def doUpdateAnimeInfo(self, anime):
        self.doSearchAnime(anime["name"], -1, forceInfo=True)
        self.gui.printBanner()
        self.gui.pause("Updated anime info | Press enter to continue")

    def doDelete(self, item):
        msg = f"You are about to delete {item["name"]}"
        confirm = self.gui.printConfirm(msg)

        if confirm:
            self.local.deleteFile(item["path"])
            self.gui.pause("Anime deleted successfully")

    def doCheckAnime(self, anime):
        infoValid = self.local.getAnimeInfo(anime)
        if not infoValid:
            self.gui.pause("Anime info seems to be missing, press enter to fix automatically")
            self.doUpdateAnimeInfo(anime)

            infoValid = self.local.getAnimeInfo(anime)
            self.gui.printBanner()

        self.gui.printAnimeInfo(infoValid)
        episode = self.getLocalEpisodes(anime)
        if episode is None:
            return

        actions = [
            {
                "title": "Check episode for errors",
                "callback": lambda: self.doCheckEpisode(anime, episode)
            },
            {
                "title": "Play episode",
                "callback": lambda: self.doPlayLocalEpisode(anime, episode)
            },
            {
                "title": "Delete episode",
                "callback": lambda: self.doDelete(episode)
            }

        ]

        i = self.gui.printXXMenu(actions=actions, menuName="Checking episode")
        if i is None:
            return None

        action = actions[i].get("callback")
        if action:
            action()

    def getLocalEpisodes(self, anime):
        msg = "[b]Installed episodes[/b] -- \nWhich one do you want to manage"

        self.gui.print(msg)
        episodes = self.local.getAllEpisodes(anime)

        choice = self.gui.chooseFromArr(arr=episodes, titleToGet="name")
        if choice is None:
            return None

        choice["name"] = self.api.funcs.cleanLastSeenEpisode(choice["name"])
        return choice

    def doCheckEpisode(self, anime, episode, pauseExec=True):
        self.gui.printBanner()

        episodeContent = self.local.getEpisodeContent(episode)
        subValid = self.local.isValid(episodeContent["sub"])
        vidValid = self.local.isValid(episodeContent["video"])
        skipPosValid = self.local.isValid(episodeContent["introOutro"])

        if not vidValid:
            msg = "Video appears to be missing, would you like to install it?"
            confirm = self.gui.printConfirm(msg)

            if confirm:
                self.doSearchAnime(anime["name"], episode["name"], False)

        if not subValid:
            msg = "Subtitles appear to be missing, would you like to get them?"
            confirm = self.gui.printConfirm(msg)

            if confirm:
                self.doSearchAnime(anime["name"], episode["name"], False, True)
                subValid = self.local.isValid(episodeContent["sub"])

        if pauseExec:
            self.gui.pause("All checks done | press enter to continue")

        return {"vid": vidValid, "sub": subValid, "skipPos": skipPosValid}

    def doPlayLocalEpisode(self, anime, episode):
        self.gui.printBanner()

        status = self.doCheckEpisode(anime, episode, pauseExec=False)
        sub = False
        skipIntroOutro = False

        if status["sub"]:
            msg = "Subtitles found, would you like to play them?"
            confirm = self.gui.printConfirm(msg)

            if confirm:
                sub = True

        if status["skipPos"]:
            self.gui.print("Found intro and outro positions")
            skipIntroOutro = self.config.get("autoSkipIntros")

        self.local.playAt(anime["name"], episode["name"], sub, skipIntroOutro)

    def getAnimeToWatch(self, animeToGet=None):
        query = ""
        if not animeToGet:
            menuName = "Search an anime to download"
            query = self.gui.printXXMenu(menuName=menuName)
        else:
            query = animeToGet

        res = self.api.getSearchResults(query)
        res.append({"name": "try again", "value": -1})
        if not animeToGet:
            choice = self.gui.chooseFromArr(arr=res, titleToGet="name")
            if choice is None:
                return

            if choice["name"] == "try again":
                return self.getAnimeToWatch(animeToGet)

            return choice
        else:
            for item in res:
                if item["name"] == animeToGet:
                    return item
        raise ValueError(f"{animeToGet} is not inside the search results {res}")

    def getEpisodeToWatch(self, anime, episodeToGet=None, info=None):
        episodes = self.api.getEpisodes(anime["id"], info)
        episodes.append({"title": "All"})
        if info:
            self.gui.printAnimeInfo(info)

        print("Episodes available to be downloaded:")
        if not episodeToGet:
            choice = self.gui.chooseFromArr(arr=episodes, titleToGet="title")
            if choice is None:
                return None

            if choice.get("title").lower() == "all":
                return episodes[:len(episodes)-1]
            else:
                choice["title"] = self.api.funcs.cleanLastSeenEpisode(choice["title"])
                return [choice]

        for item in episodes:
            if item["title"] == episodeToGet:
                return item
        raise ValueError("episodeToGet is not inside episodes")

    def doDownloadEpisode(self, i, anime, episode, sub, subOnly, autoPlay):
        self.gui.print(f"Starting download for episode {episode["title"]}")
        sources = self.downloader.getSources(episode["id"], sub)
        pickedSource = int(self.config.get("preferredServer"))

        if pickedSource is None or pickedSource == -1:
            msg = "No preferred server available, please pick manually"
            self.gui.warning(msg)

            pickedSource = self.gui.chooseFromArr(arr=sources, titleToGet="",
                                                  returnIdx=True)

        downloadRes = self.downloader.start(
            sources[pickedSource] if isinstance(pickedSource, int) else pickedSource,
            sub,
            anime["name"],
            episode["title"],
            subOnly
        )

        if sub and not subOnly:
            if not (downloadRes[0] or downloadRes[1]):
                raise ValueError("Could not download video or subtitle")
        else:
            if subOnly:
                raise ValueError("Could not download subtitle")

            if not downloadRes[0]:
                raise ValueError("Could not download video")

        self.gui.print(f"Finished episode {episode["title"]}")

        if autoPlay and i == 0:
            skipIntroOutro = self.config.get("autoSkipIntros")

            self.gui.print("auto playing the first episode")
            self.local.playAt(anime["name"], episode["title"], sub, skipIntroOutro)

    def doDownloadInfo(self, anime, forceInfo):
        info = self.local.getAnimeInfo(anime)

        if info is None or forceInfo:
            # If there was a last ep watched, make sure we keep track of it
            lastEpWatched = None
            if info is not None:
                lastEpWatched = info["last ep watched"]

            info = self.api.getAnimeInfo(anime)
            if lastEpWatched is not None:
                info["last ep watched"] = lastEpWatched

        self.local.saveAnimeInfo(anime, info)
        return info

    def doSearchAnime(self, animeToGet=None, episodeToGet=None, autoPlay=True,
                      subOnly=False, forceInfo=True):
        self.gui.printBanner()

        anime = self.getAnimeToWatch(animeToGet)
        if anime is None:
            return

        info = self.doDownloadInfo(anime, forceInfo)

        if episodeToGet == -1:
            return

        episodes = self.getEpisodeToWatch(anime, episodeToGet, info)
        if episodes is None:
            return

        sub = self.config.get("lang") == 'jp'
        with ThreadPoolExecutor(max_workers=self.config.get("maxWorkers")) as executor:
            futures = []

            for i, episode in enumerate(episodes):
                futures.append(
                        executor.submit(
                            self.doDownloadEpisode, i, anime, episode,
                            sub, subOnly, autoPlay
                        )
                )

            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    print(f"Download failed {e}")

        if self.interactive:
            self.gui.pause("all downloads have finished | press enter to go back to main menu")


def main():
    cfg = Config()
    parser = argparse.ArgumentParser(
        prog="hi-cli",
        description="A hianime.to cli/tui to watch and manage anime locally from your terminal."
    )

    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument("-s", "--search", action="store_true")
    parser.add_argument("-l", "--local", action="store_true")

    args = parser.parse_args()
    if args.version:
        m = Main(cfg, False)
        print(f"Version: {m.version}")
    elif args.search:
        m = Main(cfg, False)
        m.doSearchAnime()
    elif args.local:
        m = Main(cfg, False)
        m.doManageLocal()
    else:
        m = Main(cfg, True)
        m.mainMenu()


if __name__ == "__main__":
    main()
