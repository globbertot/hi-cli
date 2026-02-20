import requests
import os

class Functions:
    def __init__(self):
        pass

    def makeReq(self, uri, headers, params, callback):
        try:
            with requests.get(uri, headers=headers, params=params) as r:
                r.raise_for_status()
                return callback(r)
        except requests.exceptions.RequestException as e:
            print(f"Error while getting request\nUri: {uri}\nException: {e}")
            return None

    def doDownload(self, uri, headers, params, out):
        try:
            with requests.get(uri, headers=headers, params=params, stream=True) as r:
                r.raise_for_status()

                with open(out, "ab") as f:
                    for chunk in r.iter_content(chunk_size=8 * 1024 * 1024): # write per 8mb
                        if chunk:
                            f.write(chunk)
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error downloading file\nUri: {uri}\nException: {e}")
            return None

    def clear(self):
        os.system("cls" if os.name == "nt" else "clear")
