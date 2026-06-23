"""Tests for the rule-based AirClass gesture recognizer."""

from airclass.config import GestureConfig
from airclass.gesture_recognizer import GestureRecognizer
from airclass.gesture_types import GestureName


def _blank_landmarks() -> list[tuple[float, float, float]]:
    """Create a neutral 21-point hand pose."""
    return [
        (0.50, 0.90, 0.0),  # wrist
        (0.43, 0.78, 0.0),
        (0.40, 0.72, 0.0),
        (0.37, 0.66, 0.0),
        (0.34, 0.64, 0.0),
        (0.48, 0.72, 0.0),
        (0.48, 0.80, 0.0),
        (0.48, 0.84, 0.0),
        (0.48, 0.88, 0.0),
        (0.54, 0.72, 0.0),
        (0.54, 0.80, 0.0),
        (0.54, 0.84, 0.0),
        (0.54, 0.88, 0.0),
        (0.60, 0.72, 0.0),
        (0.60, 0.80, 0.0),
        (0.60, 0.84, 0.0),
        (0.60, 0.88, 0.0),
        (0.66, 0.72, 0.0),
        (0.66, 0.80, 0.0),
        (0.66, 0.84, 0.0),
        (0.66, 0.88, 0.0),
    ]


def _open_palm_landmarks(x_offset: float = 0.0) -> tuple[tuple[float, float, float], ...]:
    """Build a simple open-palm pose."""
    landmarks = _blank_landmarks()
    for index in (8, 12, 16, 20):
        x, _, z = landmarks[index]
        landmarks[index] = (x, 0.42, z)
    landmarks[4] = (0.30, 0.58, 0.0)
    return tuple((x + x_offset, y, z) for x, y, z in landmarks)


def _index_only_landmarks(x_offset: float = 0.0) -> tuple[tuple[float, float, float], ...]:
    """Build a pose with only the index finger extended."""
    landmarks = _blank_landmarks()
    landmarks[8] = (0.48, 0.40, 0.0)
    landmarks[12] = (0.54, 0.88, 0.0)
    landmarks[16] = (0.60, 0.88, 0.0)
    landmarks[20] = (0.66, 0.88, 0.0)
    landmarks[4] = (0.34, 0.68, 0.0)
    return tuple((x + x_offset, y, z) for x, y, z in landmarks)


def _pinch_landmarks() -> tuple[tuple[float, float, float], ...]:
    """Build a pose where thumb and index tips are close together."""
    landmarks = _blank_landmarks()
    landmarks[4] = (0.49, 0.50, 0.0)
    landmarks[8] = (0.50, 0.51, 0.0)
    landmarks[12] = (0.54, 0.86, 0.0)
    landmarks[16] = (0.60, 0.86, 0.0)
    landmarks[20] = (0.66, 0.86, 0.0)
    return tuple(landmarks)


def _make_recognizer() -> GestureRecognizer:
    """Create a recognizer with test-friendly defaults."""
    return GestureRecognizer(
        GestureConfig(
            pinch_on_threshold=0.03,
            pinch_off_threshold=0.05,
            swipe_min_displacement=0.12,
            swipe_history_size=5,
            swipe_cooldown_seconds=1.0,
            extended_finger_margin=0.02,
            folded_finger_margin=0.02,
        )
    )


def test_invalid_or_missing_landmarks_return_none() -> None:
    """Invalid input should produce the NONE gesture."""
    recognizer = _make_recognizer()

    event = recognizer.recognize(None, timestamp=0.0)
    assert event.name is GestureName.NONE

    event = recognizer.recognize(tuple(_blank_landmarks()[:20]), timestamp=1.0)
    assert event.name is GestureName.NONE


def test_open_palm_recognizes_open_palm() -> None:
    """A clearly open hand should map to OPEN_PALM."""
    recognizer = _make_recognizer()

    event = recognizer.recognize(_open_palm_landmarks(), timestamp=0.0)
    assert event.name is GestureName.OPEN_PALM


def test_index_only_hand_recognizes_index_point() -> None:
    """An index-only pose should map to INDEX_POINT."""
    recognizer = _make_recognizer()

    event = recognizer.recognize(_index_only_landmarks(), timestamp=0.0)
    assert event.name is GestureName.INDEX_POINT
    assert event.position == (0.48, 0.40)


def test_index_point_allows_thumb_and_one_other_finger_extended() -> None:
    """Index pointing should tolerate common partial folding in webcam poses."""
    landmarks = list(_index_only_landmarks())
    landmarks[12] = (0.54, 0.40, 0.0)
    landmarks[4] = (0.25, 0.60, 0.0)
    recognizer = _make_recognizer()

    event = recognizer.recognize(tuple(landmarks), timestamp=0.0)

    assert event.name is GestureName.INDEX_POINT


def test_index_point_metadata_describes_finger_states() -> None:
    """Recognized poses should expose useful finger diagnostics."""
    recognizer = _make_recognizer()

    event = recognizer.recognize(_index_only_landmarks(), timestamp=0.0)

    assert event.metadata["index_extended"] is True
    assert event.metadata["folded_non_index_count"] == 3.0
    assert event.metadata["extended_count"] >= 1.0


def test_open_palm_requires_all_four_non_thumb_fingers() -> None:
    """Thumb plus three fingers should not be classified as OPEN_PALM."""
    landmarks = list(_open_palm_landmarks())
    landmarks[20] = (0.66, 0.88, 0.0)
    recognizer = _make_recognizer()

    event = recognizer.recognize(tuple(landmarks), timestamp=0.0)

    assert event.name is not GestureName.OPEN_PALM


def test_close_thumb_index_recognizes_pinch() -> None:
    """A close thumb and index tip should map to PINCH."""
    recognizer = _make_recognizer()

    event = recognizer.recognize(_pinch_landmarks(), timestamp=0.0)
    assert event.name is GestureName.PINCH
    assert event.position == (0.50, 0.51)


def test_sequence_moving_right_recognizes_swipe_right() -> None:
    """A right-moving palm center should trigger SWIPE_RIGHT."""
    recognizer = _make_recognizer()

    positions = (0.20, 0.27, 0.34, 0.42, 0.50)
    event = None
    for index, x_offset in enumerate(positions):
        event = recognizer.recognize(_open_palm_landmarks(x_offset), timestamp=float(index))

    assert event is not None
    assert event.name is GestureName.SWIPE_RIGHT


def test_sequence_moving_left_recognizes_swipe_left() -> None:
    """A left-moving palm center should trigger SWIPE_LEFT."""
    recognizer = _make_recognizer()

    positions = (0.50, 0.43, 0.36, 0.28, 0.20)
    event = None
    for index, x_offset in enumerate(positions):
        event = recognizer.recognize(_open_palm_landmarks(x_offset), timestamp=float(index))

    assert event is not None
    assert event.name is GestureName.SWIPE_LEFT


def test_moving_index_point_does_not_trigger_swipe() -> None:
    """Drawing movement should not accidentally navigate slides."""
    recognizer = _make_recognizer()

    event = None
    for index, x_offset in enumerate((0.20, 0.27, 0.34, 0.42, 0.50)):
        event = recognizer.recognize(
            _index_only_landmarks(x_offset),
            timestamp=float(index),
        )

    assert event is not None
    assert event.name is GestureName.INDEX_POINT


def test_swipe_cooldown_prevents_immediate_repeat() -> None:
    """A swipe should not trigger again immediately during cooldown."""
    recognizer = _make_recognizer()

    first_event = None
    for index, x_offset in enumerate((0.20, 0.27, 0.34, 0.42, 0.50)):
        first_event = recognizer.recognize(_open_palm_landmarks(x_offset), timestamp=float(index))

    assert first_event is not None
    assert first_event.name is GestureName.SWIPE_RIGHT

    repeated = recognizer.recognize(_open_palm_landmarks(0.60), timestamp=0.5)
    assert repeated.name not in {GestureName.SWIPE_LEFT, GestureName.SWIPE_RIGHT}
