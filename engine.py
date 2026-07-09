import logging
from datetime import datetime, timezone, timedelta

BJ_TZ = timezone(timedelta(hours=8))  # Asia/Shanghai
from db import is_sent, mark_sent
from pushover import send_pushover
from sources import Source

logger = logging.getLogger("engine")


class SignalEngine:
    """Orchestrates all signal sources: fetch → dedup → push."""

    def __init__(self):
        self._sources: list[Source] = []
        self.last_check: dict[str, datetime] = {}   # source_id → last check time
        self.total_pushed: int = 0

    def register(self, source: Source):
        """Register a signal source."""
        self._sources.append(source)
        self.last_check[source.source_id] = None
        logger.info(f"Registered source: {source.source_id}")

    def run_all(self):
        """Run all registered sources in sequence."""
        for source in self._sources:
            try:
                self._run_source(source)
            except Exception as e:
                logger.error(f"Source {source.source_id} failed: {e}")

    def run_source(self, source_id: str) -> dict:
        """Run a single source by ID. Returns result dict for API response."""
        source = next((s for s in self._sources if s.source_id == source_id), None)
        if source is None:
            return {"error": f"Source '{source_id}' not found"}
        try:
            return self._run_source(source)
        except Exception as e:
            return {"error": str(e)}

    def _run_source(self, source: Source) -> dict:
        """Internal: run one source, dedup, push. Returns stats dict."""
        signals = source.fetch()
        new_count = 0

        for sig in signals:
            if is_sent(sig.guid):
                continue
            new_count += 1
            # Push notification
            push_msg = sig.content[:500] + ("..." if len(sig.content) > 500 else "")
            try:
                send_pushover(
                    message=push_msg,
                    title=f"[{sig.source}] {sig.title[:100]}",
                    url=sig.url,
                )
            except Exception as e:
                logger.error(f"Pushover send failed for {sig.guid}: {e}")
            mark_sent(sig.guid)

        self.last_check[source.source_id] = datetime.now(BJ_TZ)
        self.total_pushed += new_count

        logger.info(
            f"[{source.source_id}] Fetched {len(signals)}, new {new_count}"
        )

        return {
            "source": source.source_id,
            "fetched": len(signals),
            "new_signals": new_count,
            "last_check": self.last_check[source.source_id].isoformat(),
            "total_pushed": self.total_pushed,
        }
