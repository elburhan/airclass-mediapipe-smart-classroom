"""Pure frame-based gesture stabilization for AirClass."""

from __future__ import annotations

from collections import deque

from airclass.gesture_types import GestureEvent, GestureName


class GestureStabilizer:
    """Suppress short-lived pose changes while preserving discrete gestures."""

    _IMMEDIATE_GESTURES = {
        GestureName.PINCH,
        GestureName.SWIPE_LEFT,
        GestureName.SWIPE_RIGHT,
    }
    _DISCRETE_GESTURES = {
        GestureName.SWIPE_LEFT,
        GestureName.SWIPE_RIGHT,
    }

    def __init__(self, window: int = 3, required: int = 2) -> None:
        if window < 1:
            raise ValueError("Gesture stability window must be at least 1.")
        if required < 1 or required > window:
            raise ValueError(
                "Gesture stability required count must be between 1 and window."
            )

        self._history: deque[GestureName] = deque(maxlen=window)
        self._required = required
        self._stable_event: GestureEvent | None = None

    def stabilize(self, event: GestureEvent) -> GestureEvent:
        """Return the stable gesture corresponding to one raw event."""
        self._history.append(event.name)

        if event.name in self._IMMEDIATE_GESTURES:
            if event.name not in self._DISCRETE_GESTURES:
                self._stable_event = event
            return event

        if self._stable_event is None:
            self._stable_event = GestureEvent(
                GestureName.NONE,
                0.0,
                event.timestamp,
            )

        if event.name is self._stable_event.name:
            self._stable_event = event
            return event

        if self._trailing_count(event.name) >= self._required:
            self._stable_event = event
            return event

        return GestureEvent(
            name=self._stable_event.name,
            confidence=self._stable_event.confidence,
            timestamp=event.timestamp,
            position=self._stable_event.position,
            metadata=dict(self._stable_event.metadata),
        )

    def _trailing_count(self, gesture_name: GestureName) -> int:
        """Count matching gesture names at the end of the history."""
        count = 0
        for name in reversed(self._history):
            if name is not gesture_name:
                break
            count += 1
        return count
