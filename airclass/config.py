"""Application configuration for the AirClass foundation."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class CameraConfig:
    """Settings used to initialize and read from the webcam."""

    index: int = 0
    width: int = 640
    height: int = 480
    fps: int = 30
    mirror: bool = True


@dataclass(frozen=True, slots=True)
class HandDetectorConfig:
    """Settings for the MediaPipe Hands detector."""

    max_num_hands: int = 1
    min_detection_confidence: float = 0.4
    min_tracking_confidence: float = 0.4
    model_path: str = "assets/models/hand_landmarker.task"
    allow_model_download: bool = True
    model_download_url: str = "https://storage.googleapis.com/mediapipe-assets/hand_landmarker.task"


@dataclass(frozen=True, slots=True)
class GestureConfig:
    """Thresholds for the rule-based gesture recognizer."""

    pinch_on_threshold: float = 0.04
    pinch_off_threshold: float = 0.06
    swipe_min_displacement: float = 0.11
    swipe_history_size: int = 5
    swipe_cooldown_seconds: float = 0.75
    gesture_stability_window: int = 3
    gesture_stability_required: int = 2
    clear_cooldown_seconds: float = 1.0
    extended_finger_margin: float = 0.025
    folded_finger_margin: float = 0.03
    drawing_min_point_distance: float = 0.01
    drawing_max_jump_distance: float = 0.18
    max_drawing_points: int = 500


@dataclass(frozen=True, slots=True)
class UIConfig:
    """Settings for the OpenCV display window."""

    window_name: str = "AirClass"
    canvas_width: int = 1280
    canvas_height: int = 720
    status_bar_height: int = 150
    preview_width: int = 240
    preview_height: int = 135
    drawing_stroke_width: int = 4
    margin: int = 24
    board_bg_color: tuple[int, int, int] = (245, 247, 250)
    board_border_color: tuple[int, int, int] = (210, 218, 230)
    hud_bg_color: tuple[int, int, int] = (27, 33, 44)
    hud_accent_color: tuple[int, int, int] = (90, 190, 255)
    text_color: tuple[int, int, int] = (30, 38, 48)
    text_subtle_color: tuple[int, int, int] = (110, 120, 135)
    hud_text_color: tuple[int, int, int] = (245, 248, 252)
    help_bg_color: tuple[int, int, int] = (236, 242, 249)
    help_text_color: tuple[int, int, int] = (24, 32, 42)
    label_color: tuple[int, int, int] = (70, 78, 90)
    font_scale_title: float = 1.4
    font_scale_heading: float = 0.9
    font_scale_body: float = 0.66
    start_fullscreen: bool = False


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Top-level AirClass configuration."""

    camera: CameraConfig = field(default_factory=CameraConfig)
    hand_detector: HandDetectorConfig = field(default_factory=HandDetectorConfig)
    gesture: GestureConfig = field(default_factory=GestureConfig)
    ui: UIConfig = field(default_factory=UIConfig)


APP_CONFIG = AppConfig()
