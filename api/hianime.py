from .functions import Functions
from .hianimedownloader import HiAnimeDownloader

from lxml import html

class HiAnime:
    def __init__(self, lang):
        self.baseUri = "https://hianime.to"
        self.funcs = Functions()
        self.lang = lang or 'jp'

    def getSearchResults(self, query):
        searchUri = f"{self.baseUri}/ajax/search/suggest?keyword={query}"

        r = self.funcs.makeReq(searchUri, {}, {}, lambda r: r.json())
        if not (r and r.get("html")):
            raise ValueError("Cannot get search results")

        htmlStr = r.get("html")
        tree = html.fromstring(htmlStr)

        links = tree.xpath("//div[@class='film-poster']/../@href")
        filmNames = tree.xpath("//h3[@class='film-name']/text()")

        if len(links) != len(filmNames):
            raise ValueError("Links and film names are not same length")

        rtn = []
        for i in range(len(links)):
            id = links[i].rsplit("-", 1)[-1]

            obj = {"name": filmNames[i], "id": id}
            rtn.append(obj)

        return rtn

    def printSearchResults(self, data):
        self.funcs.clear()
        for i in range(len(data)):
            print(f"{i}. {data[i]['name']} {data[i]['id']}")

    def getEpisodes(self, animeID):
        episodesUri = f"{self.baseUri}/ajax/v2/episode/list/{animeID}"

        r = self.funcs.makeReq(episodesUri, {}, {}, lambda r: r.json())
        if not (r and r.get("html") and r.get("totalItems")):
            raise ValueError(f"Cannot get anime episodes info {r}")

        htmlStr = r.get("html")
        expectedEpisodes = int(r.get("totalItems"))
        
        tree = html.fromstring(htmlStr)
        rtn = []

        links = tree.xpath("//a[@data-id]")
        for link in links:
            attr = "title" if self.lang == 'en' else "data-jname"

            title = link.xpath(f".//div[contains(@class, 'ep-name')]/@{attr}")[0]
            id = link.get("data-id")

            obj = {"title": title, "id": id}
            rtn.append(obj)

        if len(rtn) != expectedEpisodes:
            raise ValueError("Episodes length is not the expected length")
        return rtn

    def printEpisodes(self, data):
        self.funcs.clear()
        for i in range(len(data)):
            print(f"{i}. {data[i]['title']}")

