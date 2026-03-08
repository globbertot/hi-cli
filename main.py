from api.hianime import HiAnime
from api.hianimedownloader import HiAnimeDownloader
from localsystem import LocalSystem
from config import Config
from concurrent.futures import ThreadPoolExecutor, as_completed

import argparse
import sys
from datetime import date


class Main:
    def __init__(self, config, interactive):
        self.version = 0.1
        self.interactive = interactive

        self.config = config
        self.actions = {
            '1': self.doSearchAnime,
            '2': self.doManageLocal,
            '3': self.doGetSchedule,
            '4': self.doExit
        }

        self.api = HiAnime(self.config.get("lang"))
        self.downloader = HiAnimeDownloader(self.config.get("outputVideosLocation"))
        self.local = LocalSystem(self.config.get("outputVideosLocation"))

    def printBanner(self):
        self.api.funcs.clear()
        print(f"hi-cli | {self.version}")

    def chooseFromArr(self, arr, printArr=False, allowBack=True, returnRes=True):
        if printArr:
            for i in range(len(arr)):
                print(f"{i}. {arr[i]}")

        if allowBack:
            print(f"-1. {"Back" if self.interactive else "Exit"}")
        choice = int(input("> "))

        if choice == -1 and allowBack:
            return None

        while choice >= len(arr) or choice < 0:
            print("Outside of range")
            choice = int(input("> "))

        return arr[choice] if returnRes else choice

    def getAnimeToWatch(self, animeToGet=None):
        self.printBanner()
        print(f"-1. {"Back" if self.interactive else "Exit"}")

        print("Search an anime")
        if not animeToGet:
            query = input("> ").strip()
            if query == "-1":
                return None
        else:
            query = animeToGet

        res = self.api.getSearchResults(query)
        self.api.printSearchResults(res)

        if not animeToGet:
            return self.chooseFromArr(res)

        for item in res:
            if item["name"] == animeToGet:
                return item
        raise ValueError(f"{animeToGet} is not inside the search results {res}")

    def getEpisodeToWatch(self, anime, episodeToGet=None, info=None):
        self.printBanner()

        episodes = self.api.getEpisodes(anime["id"])
        episodes.append({"title": "All"})
        if info:
            self.local.printAnimeInfo(info)

        print("Episodes available to be downloaded:")
        self.api.printEpisodes(episodes, False, info["last ep watched"])

        if not episodeToGet:
            choice = self.chooseFromArr(episodes)
            if choice is None:
                return None

            if choice.get("title").lower() == "all":
                return episodes[:len(episodes)-1]
            else:
                return [choice]

        for item in episodes:
            if item["title"] == episodeToGet:
                return item
        raise ValueError("episodeToGet is not inside episodes")

    def getLocalAnime(self):
        print("Installed anime -- Which one do you want to manage")
        localAnime = self.local.getAllAnime()
        self.local.printInfo(localAnime)

        return self.chooseFromArr(localAnime)

    def getLocalEpisodes(self, anime):
        print("Installed episodes -- Which one do you want to manage")
        episodes = self.local.getAllEpisodes(anime)
        self.local.printInfo(episodes)

        return self.chooseFromArr(episodes)

    def doDelete(self, item):
        self.printBanner()

        print(f"You are about to delete '{item["name"]}'")
        confirm = input("Are you sure? [y/n]: ")

        if confirm.lower() == 'y':
            self.local.deleteFile(item["path"])

    def doCheckAnime(self, anime):
        self.printBanner()

        infoValid = self.local.getAnimeInfo(anime)
        if not infoValid:
            input("Anime info seems to be missing, press enter to fix automatically")
            self.doSearchAnime(anime["name"], -1)
            infoValid = self.local.getAnimeInfo(anime)
            self.printBanner()

        self.local.printAnimeInfo(infoValid)
        episode = self.getLocalEpisodes(anime)
        if episode is None:
            return

        self.printBanner()
        print("Action")

        print(f"-1. {"Back" if self.interactive else "Exit"}")
        print("0. Check episode")
        print("1. Play episode")
        print("2. Delete episode")

        c = input("> ").strip()
        if c == '-1':
            return None

        if c == '0':
            self.doCheckEpisode(anime, episode)
        elif c == '1':
            self.doPlayLocalEpisode(anime, episode)
        elif c == '2':
            self.doDelete(episode)

    def doPlayLocalEpisode(self, anime, episode):
        self.printBanner()

        episodeContent = self.local.getEpisodeContent(episode)
        subValid = self.local.isValid(episodeContent["sub"])
        vidValid = self.local.isValid(episodeContent["video"])

        sub = False

        if not vidValid:
            print("Video appears to be missing, would you like to install it?")
            c = input("> ").strip()

            if c.lower() == 'y':
                self.doSearchAnime(anime["name"], episode["name"], False)

        if subValid:
            print("Subtitles found, would you like to play them?")
            c = input("> ").strip()

            if c.lower() == 'y':
                sub = True

        self.local.playAt(anime["name"], episode["name"], sub)

    def doCheckEpisode(self, anime, episode):
        self.printBanner()

        episodeContent = self.local.getEpisodeContent(episode)
        subValid = self.local.isValid(episodeContent["sub"])
        vidValid = self.local.isValid(episodeContent["video"])

        print(f"episode info\nsub: {subValid} | video: {vidValid}")
        if not vidValid:
            print("Video appears to be missing, would you like to install it?")
            c = input("> ").strip()

            if c.lower() == 'y':
                self.doSearchAnime(anime["name"], episode["name"], False)

        if not subValid:
            print("Subtitles appear to be missing, would you like to install them?")
            c = input("> ").strip()

            if c.lower() == 'y':
                self.doSearchAnime(anime["name"], episode["name"], False, True)

        input("All checks done | press enter to continue")

    def mainMenu(self):
        while True:
            self.printBanner()
            print("Please select your choice below")

            print("1. Search for anime to download")
            print("2. Manage installed anime")
            print("3. Get todays schedule")
            print("4. Exit")

            choice = input("> ").strip()
            action = self.actions.get(choice)

            if action:
                action()
            else:
                input("Invalid choice | Press enter to try again")

    def doDownloadEpisode(self, i, anime, episode, sub, subOnly, autoPlay):
        print(f"Starting download for episode {episode["title"]}")
        sources = self.downloader.getSources(episode["id"], sub)
        pickedSource = int(self.config.get("preferredServer"))

        if pickedSource is None or pickedSource == -1:
            print("No preferred server available, please pick manually")
            pickedSource = int(self.chooseFromArr(sources, printArr=True, allowBack=False, returnRes=False))

        downloadRes = self.downloader.start(
            sources[pickedSource],
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

        print(f"Finished episode {episode["title"]}")

        if autoPlay and i == 0:
            print("auto playing the first episode")
            self.local.playAt(anime["name"], episode["title"], sub)

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

    def doSearchAnime(self, animeToGet=None, episodeToGet=None, autoPlay=True, subOnly=False, forceInfo=False):
        self.printBanner()

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
            input("all downloads have finished | press enter to go back to main menu")

    def doManageLocal(self):
        self.printBanner()

        anime = self.getLocalAnime()
        if anime is None:
            return

        self.printBanner()
        print("Action")

        print(f"-1. {"Back" if self.interactive else "Exit"}")
        print("0. Check anime")
        print("1. Update anime info")
        print("2. Delete anime")

        choice = input("> ").strip()
        if choice == '-1':
            return None

        if choice == '0':
            self.doCheckAnime(anime)
        elif choice == '1':
            self.doSearchAnime(anime["name"], -1, forceInfo=True)
            self.printBanner()
            input("Updated anime info | press enter to continue")
        elif choice == '2':
            self.doDelete(anime)

    def doGetSchedule(self):
        self.printBanner()
        t = date.today()
        schedule = self.api.getSchedule(t)

        self.api.printSchedule(schedule)
        input("Press enter to continue")

    def doExit(self):
        print("Bye!")
        sys.exit()


def main():
    cfg = Config()
    parser = argparse.ArgumentParser(
        prog="hi-cli",
        description="A hianime.to cli/tui to watch and manage anime locally from your terminal."
    )

    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument("-s", "--search", action="store_true")
    parser.add_argument("-l", "--local", action="store_true")
    parser.add_argument("-i", "--interactive", action="store_true")

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
    elif args.interactive:
        m = Main(cfg, True)
        m.mainMenu()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
