from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Signal:
    """A signal discovered from a data source."""
    guid: str          # Unique ID: "{source_id}:{item_id}"
    title: str
    content: str
    url: str
    source: str        # Human-readable source name


class Source(ABC):
    """Abstract base class for all signal sources."""

    source_id: str     # Unique source identifier, e.g. "reddit_trump"

    @abstractmethod
    def fetch(self) -> list[Signal]:
        """Fetch new signals from this source. Returns a list of Signal objects."""
        ...
