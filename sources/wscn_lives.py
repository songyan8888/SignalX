import re
import requests
import urllib3
from sources import Source, Signal

# Suppress SSL warnings for environments without system certs (e.g. some Windows Python installs)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

WSCN_LIVES_URL = "https://api-one.wallstcn.com/apiv1/content/lives"
WSCN_CHANNELS = [
    "global-channel",
    "us-stock-channel",
    "forex-channel",
    "commodity-channel",
    "hk-stock-channel",
    "a-stock-channel",
]
USER_AGENT = "SignalX/1.0"
KEYWORDS = ["特朗普", "Trump", "川普"]
MIN_SCORE = 3


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


class WSCNLivesSource(Source):
    source_id = "wscn_lives"

    def fetch(self) -> list[Signal]:
        signals: list[Signal] = []
        seen_ids: set[str] = set()

        for channel in WSCN_CHANNELS:
            resp = requests.get(
                WSCN_LIVES_URL,
                params={"channel": channel, "limit": 100},
                headers={"User-Agent": USER_AGENT},
                timeout=10,
                verify=False,
            )
            resp.raise_for_status()
            data = resp.json()

            if data.get("code") != 20000:
                continue

            items = data.get("data", {}).get("items", [])

            for item in items:
                score = item.get("score")
                if isinstance(score, (int, float)) and score < MIN_SCORE:
                    continue

                item_id = str(item.get("id", ""))
                if not item_id or item_id in seen_ids:
                    continue
                seen_ids.add(item_id)

                content_text = item.get("content_text") or _strip_html(item.get("content", ""))
                if not content_text:
                    continue

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
