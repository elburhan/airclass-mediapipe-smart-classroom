"""Tests for AirClass metrics analysis diagnostics."""

from tools.analyze_session_metrics import _find_problems


def test_clear_cooldown_rejections_get_specific_diagnostic() -> None:
    problems = _find_problems(
        {
            "average_fps": 30.0,
            "hand_detection_rate": 1.0,
            "rejected_command_counts": {"CLEAR": 12},
            "cooldown_rejections": 12,
            "command_counts": {"NEXT_SLIDE": 3, "PREVIOUS_SLIDE": 2},
        }
    )

    assert any("CLEAR is firing too frequently" in problem for problem in problems)


def test_low_swipe_count_suggests_threshold_review() -> None:
    problems = _find_problems(
        {
            "average_fps": 30.0,
            "hand_detection_rate": 1.0,
            "command_counts": {"NEXT_SLIDE": 1, "PREVIOUS_SLIDE": 1},
        }
    )

    assert any("swipe threshold may still be too strict" in problem for problem in problems)


def test_high_drawing_volume_with_low_fps_gets_rendering_warning() -> None:
    problems = _find_problems(
        {
            "average_fps": 7.6,
            "hand_detection_rate": 1.0,
            "drawing_points_added": 1075,
            "command_counts": {"DRAW": 529, "NEXT_SLIDE": 3, "PREVIOUS_SLIDE": 2},
        }
    )

    assert any("drawing rendering may be expensive" in problem for problem in problems)
