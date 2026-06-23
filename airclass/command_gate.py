"""Stateful command triggering rules for AirClass."""

from __future__ import annotations

from airclass.gesture_types import CommandName


class CommandGate:
    """Convert held discrete commands into one-shot edge events."""

    _DISCRETE_COMMANDS = {
        CommandName.NEXT_SLIDE,
        CommandName.PREVIOUS_SLIDE,
        CommandName.CLEAR,
    }

    def __init__(self) -> None:
        self._previous_command = CommandName.NONE

    def gate(self, command: CommandName) -> CommandName:
        """Return a command suitable for frame-by-frame execution."""
        previous_command = self._previous_command
        self._previous_command = command

        if command in self._DISCRETE_COMMANDS and command is previous_command:
            return CommandName.NONE
        return command
