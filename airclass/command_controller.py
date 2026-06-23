"""Pure gesture-to-command mapping for AirClass."""

from __future__ import annotations

from airclass.gesture_types import CommandName, GestureEvent, GestureName


class CommandController:
    """Map recognized gestures to high-level classroom command names."""

    def handle_gesture(self, event: GestureEvent) -> CommandName:
        """Return the command associated with a gesture event."""
        mapping = {
            GestureName.SWIPE_RIGHT: CommandName.NEXT_SLIDE,
            GestureName.SWIPE_LEFT: CommandName.PREVIOUS_SLIDE,
            GestureName.PINCH: CommandName.POINTER,
            GestureName.INDEX_POINT: CommandName.DRAW,
            GestureName.OPEN_PALM: CommandName.CLEAR,
            GestureName.NONE: CommandName.NONE,
        }
        return mapping.get(event.name, CommandName.NONE)
