"""Safe setup tests for the AirClass hand detector."""

from pathlib import Path

import pytest

from airclass.config import HandDetectorConfig
from airclass.hand_detector import HandDetector, HandDetectorError


def test_hand_detector_imports() -> None:
    """The detector module should import and expose the detector class."""
    assert HandDetector is not None


def test_hand_detector_config_has_model_path() -> None:
    """The detector config should define the preferred local model path."""
    config = HandDetectorConfig()
    assert config.model_path == "assets/models/hand_landmarker.task"


def test_hand_detector_model_path_parent_is_assets_models() -> None:
    """The default model path should resolve under assets/models."""
    config = HandDetectorConfig()
    assert Path(config.model_path).parent == Path("assets/models")


def test_missing_model_raises_when_download_is_disabled(
    tmp_path: Path,
) -> None:
    """Missing local models should fail clearly when downloads are disabled."""
    config = HandDetectorConfig(
        model_path=str(tmp_path / "hand_landmarker.task"),
        allow_model_download=False,
    )

    with pytest.raises(HandDetectorError, match="Hand landmarker model is missing"):
        HandDetector(config)
