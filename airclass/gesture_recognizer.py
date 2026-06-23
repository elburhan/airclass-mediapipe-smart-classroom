"""Pure, testable gesture recognition for AirClass."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from math import hypot
from typing import Deque

from airclass.config import GestureConfig
from airclass.gesture_types import GestureEvent, GestureName

Landmarks = tuple[tuple[float, float, float], ...]


@dataclass(frozen=True, slots=True)
class FingerStates:
    """Binary finger extension state used by the rule-based recognizer."""

    thumb: bool
    index: bool
    middle: bool
    ring: bool
    pinky: bool


class GestureRecognizer:
    """Recognize basic hand gestures from normalized landmarks."""

    def __init__(self, config: GestureConfig) -> None:
        self._config = config
        self._palm_history: Deque[tuple[float, float]] = deque(
            maxlen=config.swipe_history_size
        )
        self._pinch_active = False
        self._last_swipe_timestamp = float("-inf")
        self._synthetic_timestamp = 0.0

    def recognize(
        self,
        landmarks: Landmarks | None,
        timestamp: float | None = None,
    ) -> GestureEvent:
        """Recognize a gesture event from normalized hand landmarks."""
        event_timestamp = self._resolve_timestamp(timestamp)
        if landmarks is None or len(landmarks) != 21:
            return GestureEvent(GestureName.NONE, 0.0, event_timestamp)

        palm_center = self._palm_center(landmarks)
        self._palm_history.append((event_timestamp, palm_center[0]))
        finger_states = self._finger_states(landmarks)
        metadata = self._finger_metadata(finger_states)

        pinch_detected = self._detect_pinch(landmarks)
        if pinch_detected:
            return GestureEvent(
                GestureName.PINCH,
                1.0,
                event_timestamp,
                position=(landmarks[8][0], landmarks[8][1]),
                metadata={**metadata, "distance": pinch_detected},
            )

        swipe_event = self._detect_swipe(
            event_timestamp,
            palm_center,
            metadata,
        )
        if swipe_event is not None:
            return swipe_event

        if (
            finger_states.index
            and finger_states.middle
            and finger_states.ring
            and finger_states.pinky
        ):
            return GestureEvent(
                GestureName.OPEN_PALM,
                0.9,
                event_timestamp,
                position=palm_center,
                metadata=metadata,
            )

        folded_non_index_count = int(metadata["folded_non_index_count"])
        if finger_states.index and folded_non_index_count >= 2:
            return GestureEvent(
                GestureName.INDEX_POINT,
                0.9,
                event_timestamp,
                position=(landmarks[8][0], landmarks[8][1]),
                metadata=metadata,
            )

        return GestureEvent(
            GestureName.NONE,
            0.0,
            event_timestamp,
            position=palm_center,
            metadata=metadata,
        )

    def _resolve_timestamp(self, timestamp: float | None) -> float:
        """Use a supplied timestamp or a monotonic synthetic fallback."""
        if timestamp is None:
            self._synthetic_timestamp += 1.0
            return self._synthetic_timestamp
        self._synthetic_timestamp = timestamp
        return timestamp

    def _detect_pinch(self, landmarks: Landmarks) -> float | None:
        """Detect a pinch using thumb and index tip distance."""
        thumb_tip = landmarks[4]
        index_tip = landmarks[8]
        distance = self._distance(thumb_tip, index_tip)

        if self._pinch_active:
            if distance <= self._config.pinch_off_threshold:
                return distance
            self._pinch_active = False
            return None

        if distance <= self._config.pinch_on_threshold:
            self._pinch_active = True
            return distance

        return None

    def _detect_swipe(
        self,
        timestamp: float,
        palm_center: tuple[float, float],
        metadata: dict[str, float | str | bool],
    ) -> GestureEvent | None:
        """Detect a directional swipe from recent palm-center history."""
        if timestamp - self._last_swipe_timestamp < self._config.swipe_cooldown_seconds:
            return None

        if len(self._palm_history) < self._config.swipe_history_size:
            return None

        extended_non_thumb_count = sum(
            (
                bool(metadata["index_extended"]),
                bool(metadata["middle_extended"]),
                bool(metadata["ring_extended"]),
                bool(metadata["pinky_extended"]),
            )
        )
        if extended_non_thumb_count < 3:
            return None

        _, start_x = self._palm_history[0]
        _, end_x = self._palm_history[-1]
        displacement = end_x - start_x

        if abs(displacement) < self._config.swipe_min_displacement:
            return None

        x_positions = [x for _, x in self._palm_history]
        deltas = [
            current - previous
            for previous, current in zip(x_positions, x_positions[1:])
        ]
        expected_sign = 1 if displacement > 0 else -1
        consistent_steps = sum(
            1
            for delta in deltas
            if delta * expected_sign > 0.005
        )
        required_consistent_steps = max(1, len(deltas) - 1)
        if consistent_steps < required_consistent_steps:
            return None

        direction = GestureName.SWIPE_RIGHT if displacement > 0 else GestureName.SWIPE_LEFT
        self._last_swipe_timestamp = timestamp
        self._palm_history.clear()
        self._palm_history.append((timestamp, palm_center[0]))
        return GestureEvent(
            direction,
            1.0,
            timestamp,
            position=palm_center,
            metadata={
                **metadata,
                "displacement": displacement,
                "consistent_steps": float(consistent_steps),
            },
        )

    def _finger_states(self, landmarks: Landmarks) -> FingerStates:
        """Compute finger extension states from y-axis landmark ordering."""
        margin = self._config.extended_finger_margin

        index = landmarks[8][1] + margin < landmarks[6][1]
        middle = landmarks[12][1] + margin < landmarks[10][1]
        ring = landmarks[16][1] + margin < landmarks[14][1]
        pinky = landmarks[20][1] + margin < landmarks[18][1]

        thumb = self._is_thumb_extended(landmarks)
        return FingerStates(thumb=thumb, index=index, middle=middle, ring=ring, pinky=pinky)

    def _finger_metadata(
        self,
        states: FingerStates,
    ) -> dict[str, float | str | bool]:
        """Return explainable finger-state metadata for diagnostics."""
        extended_count = sum(
            (states.thumb, states.index, states.middle, states.ring, states.pinky)
        )
        folded_non_index_count = sum(
            (not states.middle, not states.ring, not states.pinky)
        )
        return {
            "thumb_extended": states.thumb,
            "index_extended": states.index,
            "middle_extended": states.middle,
            "ring_extended": states.ring,
            "pinky_extended": states.pinky,
            "extended_count": float(extended_count),
            "folded_non_index_count": float(folded_non_index_count),
        }

    def _is_thumb_extended(self, landmarks: Landmarks) -> bool:
        """Use a simple distance heuristic for thumb extension."""
        thumb_tip = landmarks[4]
        thumb_ip = landmarks[3]
        return self._distance(thumb_tip, thumb_ip) > self._config.folded_finger_margin

    def _palm_center(self, landmarks: Landmarks) -> tuple[float, float]:
        """Estimate the palm center from wrist and MCP landmarks."""
        points = (
            landmarks[0],
            landmarks[5],
            landmarks[9],
            landmarks[13],
            landmarks[17],
        )
        x = sum(point[0] for point in points) / len(points)
        y = sum(point[1] for point in points) / len(points)
        return x, y

    def _distance(
        self,
        first: tuple[float, float, float],
        second: tuple[float, float, float],
    ) -> float:
        """Return Euclidean distance between two normalized landmarks."""
        return hypot(first[0] - second[0], first[1] - second[1])
