from api.hianime import HiAnime
from api.hianimedownloader import HiAnimeDownloader
from localsystem import LocalSystem
from config import Config
from pathlib import Path

import argparse

class Main:
    def __init__(self, config):
        self.version = 0.1
        self.config = config
        self.actions = {
            '1': self.doSearchAnime,
            '2': self.doManageLocal,
            '3': self.doExit
        }

        self.api = HiAnime(self.config.get("lang"))
        self.downloader = HiAnimeDownloader(self.config.get("outputVideosLocation"))
        self.local = LocalSystem(self.config.get("outputVideosLocation"))

    def printBanner(self):
        self.api.funcs.clear()
        print(f"hi-cli | {self.version}")
        
    def chooseFromArr(self, arr, interactive=True):
        if interactive:
            print("-1. Back")
        choice = int(input("> "))

        if choice == -1:
            return None

        while choice >= len(arr) or choice < 0:
            print("Outside of range")
            choice = int(input("> "))

        return arr[choice]

    def getAnimeToWatch(self, animeToGet=None, interactive=True):
        self.printBanner()
        if interactive:
            print("-1. Back")
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
            return self.chooseFromArr(res, interactive)

        for item in res:
            if item["name"] == animeToGet:
                return item
        raise ValueError("animeToGet is not inside the search results")

    def getEpisodeToWatch(self, anime, episodeToGet=None, interactive=True):
        episodes = self.api.getEpisodes(anime["id"])
        self.api.printEpisodes(episodes)

        if not episodeToGet:
            return self.chooseFromArr(episodes, interactive)

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

        episode = self.getLocalEpisodes(anime)
        if episode is None:
            return

        self.printBanner()
        print("Action")

        print("-1. Back")
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

    def mainMenu(self):
        while True:
            self.printBanner()
            print("Please select your choice below")

            print("1. Search for anime to download")
            print("2. Manage installed anime")
            print("3. Exit")

            choice = input("> ").strip()
            action = self.actions.get(choice)

            if action:
                action()
            else:
                input("Invalid choice | Press enter to try again")

    def doSearchAnime(self, animeToGet=None, episodeToGet=None, autoPlay=True, subOnly=False, interactive=True):
        self.printBanner()

        anime = self.getAnimeToWatch(animeToGet, interactive)
        if anime is None:
            return

        episode = self.getEpisodeToWatch(anime, episodeToGet, interactive)
        if episode is None:
            return

        sub = self.config.get("lang") == 'jp'

        downloadRes = self.downloader.start(
            episode["id"],
            sub,
            anime["name"],
            episode["title"],
            subOnly
        )

        if subOnly:
            return

        if sub:
            if not (downloadRes[0] or downloadRes[1]):
                raise ValueError("Could not download video or subtitle")
        else:
            if not downloadRes[0]:
                raise ValueError("Could not download video")

        if autoPlay:
            self.local.playAt(anime["name"], episode["title"], sub)

    def doManageLocal(self):
        self.printBanner()

        anime = self.getLocalAnime()
        if anime is None:
            return

        self.printBanner()
        print("Action")

        print("-1. Back")
        print("0. Check anime")
        print("1. Delete anime")

        choice = input("> ").strip()
        if choice == '-1':
            return None

        if choice == '0':
            self.doCheckAnime(anime)
        elif choice == '1':
            self.doDelete(anime)

    def doExit(self):
        print("Bye!")
        exit()


def main():
    cfg = Config()
    m = Main(cfg)

    parser = argparse.ArgumentParser(
        prog="hi-cli", 
        description="A hianime.to cli/tui to watch and manage anime locally from your terminal."
    )

    parser.add_argument("-v", "--version", action="store_true")
    parser.add_argument("-s", "--search", action="store_true")
    parser.add_argument("-i", "--interactive", action="store_true")

    args = parser.parse_args()
    if args.version:
        print(m.version)
        return
    elif args.search:
        m.doSearchAnime(interactive=False)
    elif args.interactive:
        m.mainMenu()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
