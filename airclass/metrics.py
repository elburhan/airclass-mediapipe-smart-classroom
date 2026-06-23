"""Lightweight in-memory runtime metrics for AirClass."""

from __future__ import annotations

from collections import Counter


class RuntimeMetrics:
    """Collect low-overhead measurements from the live application loop."""

    def __init__(self) -> None:
        self.total_frames = 0
        self.frames_with_hand = 0
        self.frames_without_hand = 0
        self.fps_samples: list[float] = []
        self.gesture_counts: Counter[str] = Counter()
        self.command_counts: Counter[str] = Counter()
        self.gesture_transitions: Counter[str] = Counter()
        self.command_transitions: Counter[str] = Counter()
        self.executed_command_counts: Counter[str] = Counter()
        self.rejected_command_counts: Counter[str] = Counter()
        self.cooldown_rejections = 0
        self.drawing_point_count = 0
        self.drawing_strokes_count = 0
        self.drawing_resets = 0
        self.pointer_update_count = 0
        self._previous_gesture: str | None = None
        self._previous_command: str | None = None
        self._previous_drawing_points_count = 0
        self._final_drawing_points = 0

    def record_frame(self, fps: float, has_hand: bool) -> None:
        """Record one processed frame and its hand-detection state."""
        self.total_frames += 1
        self.fps_samples.append(float(fps))
        if has_hand:
            self.frames_with_hand += 1
        else:
            self.frames_without_hand += 1

    def record_gesture(self, gesture_name: str) -> None:
        """Record a recognized gesture and any transition into it."""
        self.gesture_counts[gesture_name] += 1
        self._record_transition(
            self.gesture_transitions,
            self._previous_gesture,
            gesture_name,
        )
        self._previous_gesture = gesture_name

    def record_command(
        self,
        command_name: str,
        executed: bool,
        message: str,
    ) -> None:
        """Record a command attempt, result, transition, and cooldown rejection."""
        self.command_counts[command_name] += 1
        self._record_transition(
            self.command_transitions,
            self._previous_command,
            command_name,
        )
        self._previous_command = command_name

        if executed:
            self.executed_command_counts[command_name] += 1
        else:
            self.rejected_command_counts[command_name] += 1
            if "cooldown" in message.lower():
                self.cooldown_rejections += 1

    def record_visual_state(
        self,
        pointer_active: bool,
        drawing_points_count: int,
        drawing_strokes_count: int = 0,
        drawing_resets: int = 0,
        drawing_points_added_total: int | None = None,
    ) -> None:
        """Record pointer activity and newly added drawing points."""
        if pointer_active:
            self.pointer_update_count += 1

        normalized_count = max(0, int(drawing_points_count))
        if drawing_points_added_total is None:
            if normalized_count > self._previous_drawing_points_count:
                self.drawing_point_count += (
                    normalized_count - self._previous_drawing_points_count
                )
        else:
            self.drawing_point_count = max(
                self.drawing_point_count,
                max(0, int(drawing_points_added_total)),
            )
        self._previous_drawing_points_count = normalized_count
        self._final_drawing_points = normalized_count
        self.drawing_strokes_count = max(
            self.drawing_strokes_count,
            max(0, int(drawing_strokes_count)),
        )
        self.drawing_resets = max(
            self.drawing_resets,
            max(0, int(drawing_resets)),
        )

    def summary(self) -> dict[str, object]:
        """Return a JSON-serializable snapshot of the collected metrics."""
        average_fps = (
            sum(self.fps_samples) / len(self.fps_samples)
            if self.fps_samples
            else 0.0
        )
        hand_detection_rate = (
            self.frames_with_hand / self.total_frames
            if self.total_frames
            else 0.0
        )

        return {
            "total_frames": self.total_frames,
            "frames_with_hand": self.frames_with_hand,
            "frames_without_hand": self.frames_without_hand,
            "average_fps": average_fps,
            "min_fps": min(self.fps_samples, default=0.0),
            "max_fps": max(self.fps_samples, default=0.0),
            "hand_detection_rate": hand_detection_rate,
            "gesture_counts": dict(self.gesture_counts),
            "command_counts": dict(self.command_counts),
            "gesture_transitions": dict(self.gesture_transitions),
            "command_transitions": dict(self.command_transitions),
            "executed_command_counts": dict(self.executed_command_counts),
            "rejected_command_counts": dict(self.rejected_command_counts),
            "cooldown_rejections": self.cooldown_rejections,
            "drawing_point_count": self.drawing_point_count,
            "drawing_points_added": self.drawing_point_count,
            "drawing_strokes_count": self.drawing_strokes_count,
            "drawing_resets": self.drawing_resets,
            "pointer_update_count": self.pointer_update_count,
            "final_drawing_points": self._final_drawing_points,
        }

    @staticmethod
    def _record_transition(
        transitions: Counter[str],
        previous_name: str | None,
        current_name: str,
    ) -> None:
        """Count a transition only when the current state changed."""
        if previous_name is not None and previous_name != current_name:
            transitions[f"{previous_name} -> {current_name}"] += 1
