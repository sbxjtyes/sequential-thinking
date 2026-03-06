"""In-memory storage for sequential thinking data.

Provides a lightweight storage layer using Python lists. Thoughts persist
for the lifetime of the MCP server process. For cross-session persistence,
use the export_session/import_session tools.
"""

import json
from typing import List
from pathlib import Path
from datetime import datetime

from .models import ThoughtData
from .logging_conf import configure_logging

logger = configure_logging("sequential-thinking.storage")


class ThoughtStorage:
    """In-memory storage manager for thought data.

    Stores thoughts in a Python list for the duration of the server process.
    Provides export/import functionality for explicit persistence to JSON files.

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

    def export_session(self, file_path: str) -> None:
        """Export the current session to a JSON file.

        Args:
            file_path: Absolute path for the output JSON file.

        Raises:
            IOError: If the file cannot be written.
        """
        logger.info(f"Exporting session to {file_path}")
        all_thoughts = self.get_all_thoughts()
        thoughts_as_dicts = [t.to_dict(include_id=True) for t in all_thoughts]

        export_data = {
            "exportedAt": datetime.now().isoformat(),
            "thoughtCount": len(thoughts_as_dicts),
            "thoughts": thoughts_as_dicts,
        }

        p = Path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Exported {len(thoughts_as_dicts)} thoughts to {file_path}")

    def import_session(self, file_path: str) -> None:
        """Import a session from a JSON file, replacing current data.

        Args:
            file_path: Absolute path to the JSON file to import.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a valid file.
            json.JSONDecodeError: If the file contains invalid JSON.
        """
        logger.info(f"Importing session from {file_path}")

        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(f"Import file not found: {file_path}")
        if not p.is_file():
            raise ValueError(f"Import path is not a file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            import_data = json.load(f)

        thoughts_to_import = import_data.get("thoughts", [])

        # Clear existing data before import
        self.clear_history()

        for thought_dict in thoughts_to_import:
            thought_data = ThoughtData.from_dict(thought_dict)
            self._thoughts.append(thought_data)

        logger.info(f"Imported {len(thoughts_to_import)} thoughts from {file_path}")