"""Tests for the pure AirClass gesture stabilizer."""

from airclass.gesture_stabilizer import GestureStabilizer
from airclass.gesture_types import GestureEvent, GestureName


def _event(
    name: GestureName,
    timestamp: float,
    position: tuple[float, float] | None = None,
) -> GestureEvent:
    """Build a small gesture event for stabilizer tests."""
    return GestureEvent(name, 1.0, timestamp, position=position)


def test_repeated_same_gesture_becomes_stable() -> None:
    stabilizer = GestureStabilizer(window=3, required=2)

    first = stabilizer.stabilize(_event(GestureName.INDEX_POINT, 0.0))
    second = stabilizer.stabilize(_event(GestureName.INDEX_POINT, 1.0))

    assert first.name is GestureName.NONE
    assert second.name is GestureName.INDEX_POINT


def test_one_frame_flicker_does_not_change_stable_gesture() -> None:
    stabilizer = GestureStabilizer(window=3, required=2)
    stabilizer.stabilize(_event(GestureName.OPEN_PALM, 0.0))
    stabilizer.stabilize(_event(GestureName.OPEN_PALM, 1.0))

    flicker = stabilizer.stabilize(_event(GestureName.INDEX_POINT, 2.0))

    assert flicker.name is GestureName.OPEN_PALM


def test_pinch_passes_through_immediately() -> None:
    stabilizer = GestureStabilizer(window=3, required=2)

    result = stabilizer.stabilize(
        _event(GestureName.PINCH, 0.0, position=(0.4, 0.5))
    )

    assert result.name is GestureName.PINCH
    assert result.position == (0.4, 0.5)


def test_swipes_pass_through_immediately() -> None:
    stabilizer = GestureStabilizer(window=3, required=2)

    right = stabilizer.stabilize(_event(GestureName.SWIPE_RIGHT, 0.0))
    left = stabilizer.stabilize(_event(GestureName.SWIPE_LEFT, 1.0))

    assert right.name is GestureName.SWIPE_RIGHT
    assert left.name is GestureName.SWIPE_LEFT


def test_one_none_frame_does_not_erase_stable_gesture() -> None:
    stabilizer = GestureStabilizer(window=3, required=2)
    stabilizer.stabilize(_event(GestureName.INDEX_POINT, 0.0))
    stabilizer.stabilize(
        _event(GestureName.INDEX_POINT, 1.0, position=(0.3, 0.4))
    )

    missing = stabilizer.stabilize(_event(GestureName.NONE, 2.0))
    confirmed_missing = stabilizer.stabilize(_event(GestureName.NONE, 3.0))

    assert missing.name is GestureName.INDEX_POINT
    assert missing.position == (0.3, 0.4)
    assert confirmed_missing.name is GestureName.NONE
