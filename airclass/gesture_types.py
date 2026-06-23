"""Shared gesture and command types for AirClass."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class GestureName(Enum):
    """Gesture labels produced by the recognizer."""

    NONE = auto()
    OPEN_PALM = auto()
    INDEX_POINT = auto()
    PINCH = auto()
    SWIPE_LEFT = auto()
    SWIPE_RIGHT = auto()


class CommandName(Enum):
    """High-level classroom commands mapped from gestures."""

    NONE = auto()
    NEXT_SLIDE = auto()
    PREVIOUS_SLIDE = auto()
    POINTER = auto()
    DRAW = auto()
    CLEAR = auto()


@dataclass(frozen=True, slots=True)
class GestureEvent:
    """A recognized gesture event with optional location metadata."""

    name: GestureName
    confidence: float
    timestamp: float
    position: tuple[float, float] | None = None
    metadata: dict[str, float | str | bool] = field(default_factory=dict)
