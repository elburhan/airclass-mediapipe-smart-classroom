"""Tests for the AirClass command controller."""

from airclass.command_controller import CommandController
from airclass.gesture_types import CommandName, GestureEvent, GestureName


def _event(name: GestureName) -> GestureEvent:
    """Build a minimal gesture event for mapping tests."""
    return GestureEvent(name=name, confidence=1.0, timestamp=0.0)


def test_swipe_right_maps_to_next_slide() -> None:
    """Swipe right should map to the next slide command."""
    controller = CommandController()
    assert controller.handle_gesture(_event(GestureName.SWIPE_RIGHT)) is CommandName.NEXT_SLIDE


def test_swipe_left_maps_to_previous_slide() -> None:
    """Swipe left should map to the previous slide command."""
    controller = CommandController()
    assert controller.handle_gesture(_event(GestureName.SWIPE_LEFT)) is CommandName.PREVIOUS_SLIDE


def test_pinch_maps_to_pointer() -> None:
    """Pinch should map to the pointer command."""
    controller = CommandController()
    assert controller.handle_gesture(_event(GestureName.PINCH)) is CommandName.POINTER


def test_index_point_maps_to_draw() -> None:
    """Index point should map to the draw command."""
    controller = CommandController()
    assert controller.handle_gesture(_event(GestureName.INDEX_POINT)) is CommandName.DRAW


def test_open_palm_maps_to_clear() -> None:
    """Open palm should map to the clear command."""
    controller = CommandController()
    assert controller.handle_gesture(_event(GestureName.OPEN_PALM)) is CommandName.CLEAR


def test_none_maps_to_none() -> None:
    """None should map to no command."""
    controller = CommandController()
    assert controller.handle_gesture(_event(GestureName.NONE)) is CommandName.NONE
