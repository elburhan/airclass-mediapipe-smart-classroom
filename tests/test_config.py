"""Tests for performance-oriented AirClass defaults."""

from airclass.config import CameraConfig, HandDetectorConfig, UIConfig


def test_camera_defaults_target_laptop_realtime_performance() -> None:
    config = CameraConfig()

    assert (config.width, config.height, config.fps) == (640, 480, 30)
    assert config.mirror is True


def test_hand_detector_defaults_prioritize_one_hand_tracking() -> None:
    config = HandDetectorConfig()

    assert config.max_num_hands == 1
    assert config.min_detection_confidence == 0.4
    assert config.min_tracking_confidence == 0.4


def test_ui_defaults_use_reduced_rendering_dimensions() -> None:
    config = UIConfig()

    assert (config.canvas_width, config.canvas_height) == (1280, 720)
    assert (config.preview_width, config.preview_height) == (240, 135)
    assert config.status_bar_height == 150


def test_gesture_defaults_include_stability_and_swipe_tuning() -> None:
    from airclass.config import GestureConfig

    config = GestureConfig()

    assert config.gesture_stability_window == 3
    assert config.gesture_stability_required == 2
    assert config.clear_cooldown_seconds == 1.0
    assert config.swipe_min_displacement == 0.11
    assert config.swipe_history_size == 5
    assert config.drawing_min_point_distance == 0.01
    assert config.drawing_max_jump_distance == 0.18


def test_ui_defaults_include_drawing_stroke_width() -> None:
    config = UIConfig()

    assert config.drawing_stroke_width == 4
