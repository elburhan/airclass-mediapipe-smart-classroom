"""Tests for the lightweight AirClass runtime metrics collector."""

from airclass.metrics import RuntimeMetrics


def test_runtime_metrics_starts_empty() -> None:
    metrics = RuntimeMetrics()
    summary = metrics.summary()

    assert summary["total_frames"] == 0
    assert summary["average_fps"] == 0.0
    assert summary["gesture_counts"] == {}
    assert summary["command_counts"] == {}


def test_record_frame_updates_totals() -> None:
    metrics = RuntimeMetrics()

    metrics.record_frame(20.0, has_hand=True)
    metrics.record_frame(10.0, has_hand=False)

    summary = metrics.summary()
    assert summary["total_frames"] == 2
    assert summary["frames_with_hand"] == 1
    assert summary["frames_without_hand"] == 1
    assert summary["average_fps"] == 15.0
    assert summary["min_fps"] == 10.0
    assert summary["max_fps"] == 20.0


def test_hand_detection_rate_is_computed_correctly() -> None:
    metrics = RuntimeMetrics()

    metrics.record_frame(30.0, has_hand=True)
    metrics.record_frame(30.0, has_hand=True)
    metrics.record_frame(30.0, has_hand=False)
    metrics.record_frame(30.0, has_hand=False)

    assert metrics.summary()["hand_detection_rate"] == 0.5


def test_gesture_counts_update_correctly() -> None:
    metrics = RuntimeMetrics()

    metrics.record_gesture("NONE")
    metrics.record_gesture("PINCH")
    metrics.record_gesture("PINCH")

    summary = metrics.summary()
    assert summary["gesture_counts"] == {"NONE": 1, "PINCH": 2}
    assert summary["gesture_transitions"] == {"NONE -> PINCH": 1}


def test_command_counts_and_results_update_correctly() -> None:
    metrics = RuntimeMetrics()

    metrics.record_command("DRAW", executed=True, message="Drawing.")
    metrics.record_command(
        "NEXT_SLIDE",
        executed=False,
        message="Already at the last slide.",
    )

    summary = metrics.summary()
    assert summary["command_counts"] == {"DRAW": 1, "NEXT_SLIDE": 1}
    assert summary["executed_command_counts"] == {"DRAW": 1}
    assert summary["rejected_command_counts"] == {"NEXT_SLIDE": 1}
    assert summary["command_transitions"] == {"DRAW -> NEXT_SLIDE": 1}


def test_cooldown_messages_increment_cooldown_rejections() -> None:
    metrics = RuntimeMetrics()

    metrics.record_command(
        "NEXT_SLIDE",
        executed=False,
        message="Slide navigation cooldown active.",
    )

    assert metrics.summary()["cooldown_rejections"] == 1


def test_visual_state_tracks_pointer_and_drawing_points() -> None:
    metrics = RuntimeMetrics()

    metrics.record_visual_state(
        pointer_active=True,
        drawing_points_count=2,
        drawing_strokes_count=1,
    )
    metrics.record_visual_state(
        pointer_active=False,
        drawing_points_count=3,
        drawing_strokes_count=2,
        drawing_points_added_total=4,
    )
    metrics.record_visual_state(
        pointer_active=False,
        drawing_points_count=0,
        drawing_strokes_count=2,
        drawing_resets=1,
    )

    summary = metrics.summary()
    assert summary["pointer_update_count"] == 1
    assert summary["drawing_point_count"] == 4
    assert summary["drawing_points_added"] == 4
    assert summary["drawing_strokes_count"] == 2
    assert summary["drawing_resets"] == 1
    assert summary["final_drawing_points"] == 0


def test_summary_returns_expected_keys() -> None:
    expected_keys = {
        "total_frames",
        "frames_with_hand",
        "frames_without_hand",
        "average_fps",
        "min_fps",
        "max_fps",
        "hand_detection_rate",
        "gesture_counts",
        "command_counts",
        "gesture_transitions",
        "command_transitions",
        "executed_command_counts",
        "rejected_command_counts",
        "cooldown_rejections",
        "drawing_point_count",
        "drawing_points_added",
        "drawing_strokes_count",
        "drawing_resets",
        "pointer_update_count",
        "final_drawing_points",
    }

    assert expected_keys == set(RuntimeMetrics().summary())
