"""Tests for the lightweight AirClass session logger."""

from __future__ import annotations

import csv

from airclass.session_logger import SessionLogger


def _read_csv_rows(path) -> list[list[str]]:
    """Read all rows from a CSV file."""
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.reader(file))


def test_session_logger_creates_csv_file(tmp_path) -> None:
    """Creating a logger should create a timestamped CSV file."""
    logger = SessionLogger(tmp_path)

    assert logger.path.parent == tmp_path
    assert logger.path.exists()

    logger.close()


def test_session_logger_writes_header_row(tmp_path) -> None:
    """The CSV file should begin with the expected header."""
    logger = SessionLogger(tmp_path)
    logger.close()

    rows = _read_csv_rows(logger.path)

    assert rows[0] == [
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


def test_session_logger_writes_event_row(tmp_path) -> None:
    """Logging one event should add one CSV row."""
    logger = SessionLogger(tmp_path)
    logger.log_event(
        timestamp=12.345678,
        gesture="PINCH",
        command="POINTER",
        executed=True,
        message="Pointer active.",
        slide_index=2,
        total_slides=5,
        position=(0.25, 0.75),
    )
    logger.close()

    rows = _read_csv_rows(logger.path)

    assert rows[1] == [
        "12.345678",
        "PINCH",
        "POINTER",
        "True",
        "Pointer active.",
        "2",
        "5",
        "0.250000",
        "0.750000",
    ]


def test_session_logger_writes_empty_position_fields_for_none(tmp_path) -> None:
    """A missing position should leave x/y fields empty."""
    logger = SessionLogger(tmp_path)
    logger.log_event(
        timestamp=1.0,
        gesture="NONE",
        command="NONE",
        executed=False,
        message="No command to execute.",
        slide_index=1,
        total_slides=4,
        position=None,
    )
    logger.close()

    rows = _read_csv_rows(logger.path)

    assert rows[1][-2:] == ["", ""]
