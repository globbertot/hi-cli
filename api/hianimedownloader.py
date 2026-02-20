from .functions import Functions
from .megacloud import MegaCloud

from urllib.parse import urljoin
from pathlib import Path

import subprocess
from lxml import html

class HiAnimeDownloader:
    def __init__(self, savePath):
        self.baseUri = "https://hianime.to"
        self.funcs = Functions()
        self.savePath = Path(savePath).expanduser()

        self.headers = {
            "Referer": "https://megacloud.blog/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "application/vnd.apple.mpegurl,application/x-mpegURL,*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }

    def buildCommand(self, downloadUri, outFile):
        downloadCmd = [
            "ffmpeg",
            "-referer", "https://megacloud.blog/",
            "-protocol_whitelist", "file,tls,tcp,https,http",
            "-extension_picky", "0",
            "-allowed_segment_extensions", "ALL",
            "-i", downloadUri,
            "-c", "copy",
            outFile
        ]

        return downloadCmd

    def getSources(self, episodeId, sub):
        serversUri = f"{self.baseUri}/ajax/v2/episode/servers?episodeId={episodeId}"

        r = self.funcs.makeReq(serversUri, {}, {}, lambda r: r.json())
        if r is None or r.get("html") is None:
            raise ValueError("Couldn't make request to servers")

        htmlStr = r.get("html")
        tree = html.fromstring(htmlStr)

        check = "[@data-type='sub']" if sub else "[@data-type='dub']"
        ids = tree.xpath(f"//div{check}/@data-id")

        return ids

    def getServer(self, sourceId):
        sourceUri = f"{self.baseUri}/ajax/v2/episode/sources?id={sourceId}"

        r = self.funcs.makeReq(sourceUri, {}, {}, lambda r: r.json())
        if r is None or r.get("link") is None:
            raise ValueError("Couldnt get link to server")

        return r.get("link")

    def getMCloudData(self, uri):
        mcloud = MegaCloud(uri)
        data = mcloud.extract()
        if not (data and data.get("sources") and data.get("tracks")):
            return None

        return data

    def downloadVideo(self, mCloudData, anime, episode):
        if not (mCloudData and mCloudData.get("sources")):
            raise ValueError("Could not get megacloud data")

        data = mCloudData.get("sources")
        m3u8IndexUri = data[0].get("file")

        # For now only download 1080p, TODO: support other streams
        downloadUri = urljoin(m3u8IndexUri, "index-f1-v1-a1.m3u8") # HardCoded for testing

        saveDir = self.savePath / str(anime) / str(episode)
        saveDir.mkdir(parents=True, exist_ok=True)

        cmd = self.buildCommand(downloadUri, saveDir / "output.mp4")

        subprocess.run(cmd)
        return True

    def downloadSubtitle(self, mCloudData, anime, episode):
        if not (mCloudData and mCloudData.get("tracks")):
            raise ValueError("Could not get megacloud data")

        data = mCloudData.get("tracks") 
        data = data[0] # Only attempt to download the first subtitle TODO

        fileUri = data.get("file")
        r = self.funcs.makeReq(fileUri, {}, {}, lambda r: r.text)

        saveDir = self.savePath / str(anime) / str(episode)
        saveDir.mkdir(parents=True, exist_ok=True)

        with open(saveDir / "sub.vtt", "w") as f:
            f.write(r)

        return True

    def start(self, episodeID, sub, anime, episode, onlySub=False):
        source = self.getSources(episodeID, sub)
        if len(source) <= 0:
            return (False, f"No sources found, try changing to {'dub' if sub else 'sub'}.")

        serverUri = self.getServer(source[0]) # Right only now picks HD-0 TODO

        mCloud = self.getMCloudData(serverUri)
        if onlySub:
            return (self.downloadSubtitle(mCloud, anime, episode))

        if sub:
            return (self.downloadVideo(mCloud, anime, episode), self.downloadSubtitle(mCloud, anime, episode))
        else:
            return (self.downloadVideo(mCloud, anime, episode))
