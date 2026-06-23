"""Internal command execution simulation for AirClass."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot
from time import perf_counter
from typing import Callable

from airclass.gesture_types import CommandName
from airclass.slide_deck import SlideDeck


@dataclass(frozen=True, slots=True)
class ActionState:
    """Visual action state for the AirClass board."""

    pointer_position: tuple[float, float] | None
    drawing_points: tuple[tuple[float, float], ...]
    drawing_strokes: tuple[tuple[tuple[float, float], ...], ...]
    drawing_points_added: int
    drawing_strokes_created: int
    drawing_resets: int
    status_message: str | None


@dataclass(frozen=True, slots=True)
class ActionResult:
    """The result of an internal command execution attempt."""

    command: CommandName
    executed: bool
    message: str
    slide_index: int
    total_slides: int
    state: ActionState


class ActionExecutor:
    """Execute classroom commands against the internal slide deck only."""

    def __init__(
        self,
        deck: SlideDeck,
        slide_command_cooldown_seconds: float = 0.75,
        drawing_min_point_distance: float = 0.01,
        max_drawing_points: int = 500,
        clock: Callable[[], float] = perf_counter,
        clear_command_cooldown_seconds: float = 0.75,
        drawing_max_jump_distance: float = 0.18,
        drawing_smoothing_alpha: float | None = None,
        drawing_interpolation_step: float | None = None,
    ) -> None:
        self._deck = deck
        self._slide_command_cooldown_seconds = slide_command_cooldown_seconds
        self._clear_command_cooldown_seconds = clear_command_cooldown_seconds
        self._drawing_min_point_distance = drawing_min_point_distance
        self._drawing_max_jump_distance = drawing_max_jump_distance
        self._max_drawing_points = max_drawing_points
        self._clock = clock
        self._last_slide_command_timestamp = float("-inf")
        self._last_clear_command_timestamp = float("-inf")
        self._previous_command = CommandName.NONE
        self._pointer_position: tuple[float, float] | None = None
        self._drawing_strokes: list[list[tuple[float, float]]] = []
        self._drawing_active = False
        self._drawing_strokes_created = 0
        self._drawing_points_added = 0
        self._drawing_resets = 0
        self._status_message: str | None = None

    def execute(
        self,
        command: CommandName,
        position: tuple[float, float] | None = None,
    ) -> ActionResult:
        """Execute a command against the internal slide simulation."""
        current_time = self._clock()
        entered_clear = (
            command is CommandName.CLEAR
            and self._previous_command is not CommandName.CLEAR
        )
        self._previous_command = command
        if command is not CommandName.DRAW:
            self._end_drawing_stroke()

        if command is CommandName.NONE:
            self._pointer_position = None
            self._status_message = None
            return self._result(
                command=command,
                executed=False,
                message="No command to execute.",
            )

        if command in (CommandName.NEXT_SLIDE, CommandName.PREVIOUS_SLIDE):
            if self._is_on_cooldown(current_time):
                self._status_message = "Slide navigation cooldown active."
                return self._result(
                    command=command,
                    executed=False,
                    message="Slide navigation cooldown active.",
                )

            if command is CommandName.NEXT_SLIDE:
                if self._deck.next_slide():
                    self._last_slide_command_timestamp = current_time
                    self._status_message = (
                        f"Moved to slide {self._deck.display_index} of {self._deck.total_slides}."
                    )
                    return self._result(
                        command=command,
                        executed=True,
                        message=self._status_message,
                    )
                self._status_message = (
                    f"Already at the last slide ({self._deck.display_index} / {self._deck.total_slides})."
                )
                return self._result(
                    command=command,
                    executed=False,
                    message=self._status_message,
                )

            if self._deck.previous_slide():
                self._last_slide_command_timestamp = current_time
                self._status_message = (
                    f"Moved to slide {self._deck.display_index} of {self._deck.total_slides}."
                )
                return self._result(
                    command=command,
                    executed=True,
                    message=self._status_message,
                )
            self._status_message = (
                f"Already at the first slide ({self._deck.display_index} / {self._deck.total_slides})."
            )
            return self._result(
                command=command,
                executed=False,
                message=self._status_message,
            )

        label = command.name.replace("_", " ").title()
        if command is CommandName.POINTER:
            if position is None:
                self._pointer_position = None
                self._status_message = "Pointer position unavailable."
                return self._result(
                    command=command,
                    executed=False,
                    message="Pointer position unavailable.",
                )

            self._pointer_position = position
            self._status_message = "Pointer active."
            return self._result(
                command=command,
                executed=True,
                message="Pointer active.",
            )

        if command is CommandName.DRAW:
            if position is None:
                self._end_drawing_stroke()
                self._status_message = "Drawing position unavailable."
                return self._result(
                    command=command,
                    executed=False,
                    message="Drawing position unavailable.",
                )

            self._pointer_position = None
            normalized_position = self._clamp_position(position)
            if not self._drawing_active or self._is_large_drawing_jump(
                normalized_position
            ):
                self._start_drawing_stroke(normalized_position)
            else:
                self._append_drawing_point(normalized_position)
            self._drawing_active = True
            self._trim_drawing_history()
            self._status_message = "Drawing."
            return self._result(
                command=command,
                executed=True,
                message="Drawing.",
            )

        if command is CommandName.CLEAR:
            if (
                not entered_clear
                and current_time - self._last_clear_command_timestamp
                < self._clear_command_cooldown_seconds
            ):
                self._status_message = "Clear command cooldown active."
                return self._result(
                    command=command,
                    executed=False,
                    message=self._status_message,
                )

            self._drawing_strokes = []
            self._drawing_active = False
            self._drawing_resets += 1
            self._pointer_position = None
            self._last_clear_command_timestamp = current_time
            self._status_message = "Drawing cleared."
            return self._result(
                command=command,
                executed=True,
                message="Drawing cleared.",
            )

        self._status_message = f"{label} not implemented yet."
        return self._result(
            command=command,
            executed=False,
            message=self._status_message,
        )

    def _is_on_cooldown(self, current_time: float) -> bool:
        """Return True when slide navigation should be rate-limited."""
        return (
            current_time - self._last_slide_command_timestamp
            < self._slide_command_cooldown_seconds
        )

    def _result(
        self,
        command: CommandName,
        executed: bool,
        message: str,
    ) -> ActionResult:
        """Build an action result from the current deck state."""
        return ActionResult(
            command=command,
            executed=executed,
            message=message,
            slide_index=self._deck.display_index,
            total_slides=self._deck.total_slides,
            state=ActionState(
                pointer_position=self._pointer_position,
                drawing_points=self._flatten_drawing_points(),
                drawing_strokes=tuple(
                    tuple(stroke) for stroke in self._drawing_strokes
                ),
                drawing_points_added=self._drawing_points_added,
                drawing_strokes_created=self._drawing_strokes_created,
                drawing_resets=self._drawing_resets,
                status_message=self._status_message,
            ),
        )

    def _start_drawing_stroke(self, position: tuple[float, float]) -> None:
        """Begin a separate drawing stroke at one point."""
        self._drawing_strokes.append([position])
        self._drawing_points_added += 1
        self._drawing_strokes_created += 1

    def _append_drawing_point(self, position: tuple[float, float]) -> None:
        """Append one sufficiently distant point to the active stroke."""
        if not self._drawing_strokes:
            self._start_drawing_stroke(position)
            return

        previous = self._drawing_strokes[-1][-1]
        if hypot(position[0] - previous[0], position[1] - previous[1]) < (
            self._drawing_min_point_distance
        ):
            return
        self._drawing_strokes[-1].append(position)
        self._drawing_points_added += 1

    def _end_drawing_stroke(self) -> None:
        """End the active stroke without erasing completed drawing."""
        if self._drawing_active:
            self._drawing_active = False

    def _is_large_drawing_jump(
        self,
        position: tuple[float, float],
    ) -> bool:
        """Return True when a point should begin a separate stroke."""
        if not self._drawing_strokes or not self._drawing_strokes[-1]:
            return False
        previous = self._drawing_strokes[-1][-1]
        return hypot(
            position[0] - previous[0],
            position[1] - previous[1],
        ) > self._drawing_max_jump_distance

    @staticmethod
    def _clamp_position(
        position: tuple[float, float],
    ) -> tuple[float, float]:
        """Clamp a normalized drawing position to the board."""
        return (
            min(max(float(position[0]), 0.0), 1.0),
            min(max(float(position[1]), 0.0), 1.0),
        )

    def _flatten_drawing_points(self) -> tuple[tuple[float, float], ...]:
        """Return all drawing points for backward-compatible consumers."""
        return tuple(point for stroke in self._drawing_strokes for point in stroke)

    def _trim_drawing_history(self) -> None:
        """Keep the total drawing history within the configured point limit."""
        excess = len(self._flatten_drawing_points()) - self._max_drawing_points
        while excess > 0 and self._drawing_strokes:
            first_stroke = self._drawing_strokes[0]
            if len(first_stroke) <= excess:
                excess -= len(first_stroke)
                self._drawing_strokes.pop(0)
            else:
                del first_stroke[:excess]
                excess = 0
