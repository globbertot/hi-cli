import re
from .functions import Functions

CLIENT_KEY_RE = r'([a-zA-Z0-9]{48})|x: "([a-zA-Z0-9]{16})", y: "([a-zA-Z0-9]{16})", z: "([a-zA-Z0-9]{16})"}'
URI_ID_RE = r'([^\/?]+)(?=\?|$)'

class MegaCloud:
    def __init__(self, uri):
        self.baseUri = "https://megacloud.blog"
        self.headers = {
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64; rv:139.0) Gecko/20100101 Firefox/139.0",
            "origin": self.baseUri,
            "referer": self.baseUri + "/",
        }

        self.uri = uri
        self.funcs = Functions()

    def getClientKey(self):
        r = self.funcs.makeReq(self.uri, self.headers, {}, lambda r: r.text)

        if r is None:
            raise ValueError("Cannot retrieve client's key.")

        regex = re.search(CLIENT_KEY_RE, r)
        if not regex:
            raise ValueError("Cannot find client key.")

        return ''.join(filter(None, regex.groups()))

    def getUriId(self):
        regex = re.search(URI_ID_RE, self.uri)

        if not regex:
            raise ValueError(f"Uri {self.uri} does not have an ID")

        return regex.group(1)

    def extract(self):
        srcUri = f"{self.baseUri}/embed-2/v3/e-1/getSources"
        uriId = self.getUriId()
        clientKey = self.getClientKey()

        r = self.funcs.makeReq(srcUri, self.headers, {"id": uriId, "_k": clientKey}, lambda r: r.json())
        
        if r is None:
            raise ValueError("Cannot retrieve sources")

        return r
