from .functions import Functions
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

            obj = {"name": filmNames[i], "id": id, "link": links[i]}
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

    def printEpisodes(self, data, clear=True):
        if clear:
            self.funcs.clear()

        for i in range(len(data)):
            print(f"{i}. {data[i]['title']}")

    def getSchedule(self, date):
        # date format: year-month-day

        uri = f"{self.baseUri}/ajax/schedule/list?tzOffset=-120&date={date}"
        r = self.funcs.makeReq(uri, {}, {}, lambda r: r.json())
        if not (r and r.get("html")):
            raise ValueError(f"Could not get schedule {r}")

        tree = html.fromstring(r.get("html"))
        rtn = []
        animeObjects = tree.xpath(".//a[@class='tsl-link']")
        for obj in animeObjects:
            animeH3Name = obj.find(".//h3")
            episodeBtn = obj.find(".//button")

            name = animeH3Name.text if self.lang == 'en' else animeH3Name.get("data-jname")
            time = obj.findtext(".//div[@class='time']")
            episodeName = "".join(episodeBtn.itertext()).strip()

            obj = {"name": name, "time": time, "episode": episodeName}
            rtn.append(obj)
        return rtn

    def printSchedule(self, schedule):
        for i in range(len(schedule)):
            obj = schedule[i]

            print(f"\n\n-------{i} | {obj.get("name")}-------")
            print(f"\tRelease time: {obj.get("time")}")
            print(f"\tEpisode to be released: {obj.get("episode")}")
            print(f"-------{i} | {obj.get("name")}-------")
        print()

    def getAnimeInfo(self, animeObj):
        animeUri = animeObj.get("link")
        fullUri = f"{self.baseUri}{animeUri}"
        info = {}

        r = self.funcs.makeReq(fullUri, {}, {}, lambda r: r.text)
        if not r:
            raise ValueError(f"Cannot make request to get anime info {animeObj.get("name")}\n{r}")

        tree = html.fromstring(r)
        info["name"] = animeObj.get("name")
        info["description"] = tree.xpath(".//div[@class='text']/text()")[0].strip()
        info["episodes"] = self.getEpisodes(animeObj.get("id"))

        # gets the spans with the text expected and returns the next element's text
        info["aired"] = tree.xpath(".//span[.='Aired:']/following::span[@class='name']/text()")[0]
        info["premiered"] = tree.xpath(".//span[.='Premiered:']/following::span[@class='name']/text()")[0]
        info["episode duration"] = tree.xpath(".//span[.='Duration:']/following::span[@class='name']/text()")[0]
        info["status"] = tree.xpath(".//span[.='Status:']/following::span[@class='name']/text()")[0]

        return info
