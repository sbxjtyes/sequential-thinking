"""In-memory storage for sequential thinking data.

Provides a lightweight storage layer using Python lists. Thoughts persist
for the lifetime of the MCP server process.
"""

from typing import List

from .models import ThoughtData
from .logging_conf import configure_logging

logger = configure_logging("sequential-thinking.storage")


class ThoughtStorage:
    """In-memory storage manager for thought data.

    Stores thoughts in a Python list for the duration of the server process.

    Attributes:
        _thoughts: Internal list of ThoughtData objects.
    """

    def __init__(self) -> None:
        """Initialize empty in-memory storage."""
        self._thoughts: List[ThoughtData] = []
        logger.info("In-memory ThoughtStorage initialized")

    def add_thought(self, thought_data: ThoughtData) -> None:
        """Add a thought to the in-memory store.

        Args:
            thought_data: The thought to store.
        """
        self._thoughts.append(thought_data)
        logger.info(f"Added thought #{thought_data.thought_number} (total: {len(self._thoughts)})")

    def get_all_thoughts(self) -> List[ThoughtData]:
        """Return all stored thoughts, ordered by thought_number.

        Returns:
            List of ThoughtData sorted by thought_number.
        """
        return sorted(self._thoughts, key=lambda t: t.thought_number)

    def clear_history(self) -> None:
        """Clear all thoughts from memory."""
        count = len(self._thoughts)
        self._thoughts.clear()
        logger.info(f"Cleared {count} thoughts from memory")