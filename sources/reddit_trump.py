import feedparser
from sources import Source, Signal

REDDIT_RSS_URL = "https://www.reddit.com/r/trump/.rss"
USER_AGENT = "SignalX/1.0"


class RedditTrumpSource(Source):
    source_id = "reddit_trump"

    def fetch(self) -> list[Signal]:
        feed = feedparser.parse(
            REDDIT_RSS_URL,
            agent=USER_AGENT,
        )

        signals = []
        for entry in feed.entries:
            guid = f"{self.source_id}:{entry.id}"
            title = entry.get("title", "Untitled")
            # Reddit Atom feed uses 'summary' for the post text
            content = entry.get("summary", "")
            url = entry.get("link", "")

            signals.append(Signal(
                guid=guid,
                title=title,
                content=content,
                url=url,
                source="Reddit r/trump",
            ))

        return signals
