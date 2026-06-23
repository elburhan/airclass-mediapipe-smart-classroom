"""Lightweight CSV session logging for AirClass."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import csv
from typing import TextIO


@dataclass(frozen=True, slots=True)
class _LogRow:
    """A single session log row."""

    timestamp: float
    gesture: str
    command: str
    executed: bool
    message: str
    slide_index: int
    total_slides: int
    x: float | None
    y: float | None


class SessionLogger:
    """Write concise CSV session logs for an AirClass run."""

    def __init__(self, log_dir: str | Path = "logs") -> None:
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._path = self._unique_path(timestamp)
        self._file: TextIO = self._path.open("w", newline="", encoding="utf-8")
        self._writer = csv.writer(self._file)
        self._writer.writerow(
            [
                "timestamp",
                "gesture",
                "command",
                "executed",
                "message",
                "slide_index",
                "total_slides",
                "x",
                "y",
            ]
        )
        self._file.flush()

    @property
    def path(self) -> Path:
        """Return the path of the active session log file."""
        return self._path

    def _unique_path(self, timestamp: str) -> Path:
        """Return a unique file path for the current session."""
        candidate = self._log_dir / f"airclass_session_{timestamp}.csv"
        suffix = 1
        while candidate.exists():
            candidate = self._log_dir / f"airclass_session_{timestamp}_{suffix}.csv"
            suffix += 1
        return candidate

    def log_event(
        self,
        timestamp: float,
        gesture: str,
        command: str,
        executed: bool,
        message: str,
        slide_index: int,
        total_slides: int,
        position: tuple[float, float] | None,
    ) -> None:
        """Append one event row to the CSV log."""
        row = _LogRow(
            timestamp=timestamp,
            gesture=gesture,
            command=command,
            executed=executed,
            message=message,
            slide_index=slide_index,
            total_slides=total_slides,
            x=position[0] if position is not None else None,
            y=position[1] if position is not None else None,
        )
        self._writer.writerow(
            [
                f"{row.timestamp:.6f}",
                row.gesture,
                row.command,
                str(row.executed),
                row.message,
                str(row.slide_index),
                str(row.total_slides),
                "" if row.x is None else f"{row.x:.6f}",
                "" if row.y is None else f"{row.y:.6f}",
            ]
        )
        self._file.flush()

    def close(self) -> None:
        """Close the underlying CSV file."""
        if not self._file.closed:
            self._file.close()

    def __enter__(self) -> SessionLogger:
        """Enter the context manager."""
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        """Exit the context manager and close the file."""
        self.close()
