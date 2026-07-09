import re
import time
import requests
import urllib3
from sources import Source, Signal

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

WSCN_LIVES_URL = "https://api.wallstreetcn.com/apiv1/content/lives"
WSCN_CHANNEL = "global-channel"
USER_AGENT = "SignalX/1.0"
KEYWORDS = ["特朗普", "Trump", "川普"]
MAX_AGE_SECONDS = 300  # only push items from the last 5 minutes


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


class WSCNLivesSource(Source):
    source_id = "wscn_lives"

    def fetch(self) -> list[Signal]:
        resp = requests.get(
            WSCN_LIVES_URL,
            params={"channel": WSCN_CHANNEL, "limit": 30},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
            verify=False,
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 20000:
            return []

        now_ts = int(time.time())
        items = data.get("data", {}).get("items", [])
        signals = []

        for item in items:
            # Skip items older than MAX_AGE_SECONDS
            display_time = item.get("display_time", 0)
            if now_ts - display_time > MAX_AGE_SECONDS:
                continue

            item_id = str(item.get("id", ""))
            content_html = item.get("content", "")
            content_text = _strip_html(content_html)

            if not any(kw.lower() in content_text.lower() for kw in KEYWORDS):
                continue

            guid = f"{self.source_id}:{item_id}"
            title = content_text[:120] + ("..." if len(content_text) > 120 else "")
            url = item.get("uri", "")

            signals.append(Signal(
                guid=guid,
                title=title,
                content=content_text,
                url=url,
                source="华尔街见闻快讯",
            ))

        return signals
