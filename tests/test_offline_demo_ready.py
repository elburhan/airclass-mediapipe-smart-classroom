"""Tests for the AirClass offline demo readiness workflow."""

from pathlib import Path

from airclass.config import APP_CONFIG, HandDetectorConfig
from airclass.hand_detector import HandDetector


def test_offline_demo_model_path_is_assets_models() -> None:
    """The configured local model path should live under assets/models."""
    assert HandDetectorConfig().model_path == "assets/models/hand_landmarker.task"
    assert Path(HandDetectorConfig().model_path).parent == Path("assets/models")


def test_offline_readiness_script_exists() -> None:
    """The offline readiness script should be present in tools/."""
    assert Path("tools/check_offline_demo_ready.py").is_file()


def test_local_model_file_exists() -> None:
    """The hand landmarker model should already be available locally."""
    assert Path("assets/models/hand_landmarker.task").is_file()


def test_hand_detector_initializes_without_download() -> None:
    """The detector should initialize using only the local model file."""
    config = HandDetectorConfig(
        model_path=APP_CONFIG.hand_detector.model_path,
        allow_model_download=False,
    )
    detector = HandDetector(config)
    detector.close()
