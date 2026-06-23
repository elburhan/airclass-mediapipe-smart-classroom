"""MediaPipe Tasks hand detection and landmark drawing."""

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from types import TracebackType
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen
import shutil

from airclass.camera import Frame
from airclass.config import HandDetectorConfig

NormalizedLandmark = tuple[float, float, float]
HandConnection = tuple[int, int]

HAND_CONNECTIONS: tuple[HandConnection, ...] = (
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (0, 5),
    (5, 6),
    (6, 7),
    (7, 8),
    (5, 9),
    (9, 10),
    (10, 11),
    (11, 12),
    (9, 13),
    (13, 14),
    (14, 15),
    (15, 16),
    (13, 17),
    (17, 18),
    (18, 19),
    (19, 20),
    (0, 17),
)


class HandDetectorError(RuntimeError):
    """Raised when MediaPipe hand detection cannot be configured or used."""


@dataclass(frozen=True, slots=True)
class HandDetection:
    """A single detected hand and its normalized landmark data."""

    handedness: str
    score: float
    landmarks: tuple[NormalizedLandmark, ...]
    raw_landmarks: tuple[Any, ...]


class HandDetector:
    """Detect and draw hands using MediaPipe Tasks hand landmarker."""

    def __init__(self, config: HandDetectorConfig) -> None:
        self._config = config
        self._model_path = self._resolve_model_path()
        self._landmarker: Any | None = None
        self._closed = False
        self._last_timestamp_ms = -1

    def _resolve_model_path(self) -> Path:
        model_path = Path(self._config.model_path)
        if model_path.exists():
            if model_path.is_file():
                return model_path
            raise HandDetectorError(
                f"Hand landmarker model path exists but is not a file: {model_path}"
            )

        if not self._config.allow_model_download:
            raise HandDetectorError(
                "Hand landmarker model is missing. Place it at "
                f"{model_path} or enable allow_model_download."
            )

        model_path.parent.mkdir(parents=True, exist_ok=True)
        self._download_model(model_path, self._config.model_download_url)
        return model_path

    def _download_model(self, model_path: Path, url: str) -> None:
        download_path = model_path.with_suffix(model_path.suffix + ".download")
        try:
            with urlopen(url) as response, download_path.open("wb") as target:
                shutil.copyfileobj(response, target)
            download_path.replace(model_path)
        except (OSError, URLError) as error:
            if download_path.exists():
                download_path.unlink(missing_ok=True)
            raise HandDetectorError(
                f"Could not download MediaPipe hand landmarker model from {url}."
            ) from error

    def _create_landmarker(self, model_path: Path) -> Any:
        from mediapipe.tasks import python as mp_tasks
        from mediapipe.tasks.python import vision as mp_vision

        base_options = mp_tasks.BaseOptions(model_asset_path=str(model_path))
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=self._config.max_num_hands,
            min_hand_detection_confidence=self._config.min_detection_confidence,
            min_hand_presence_confidence=self._config.min_tracking_confidence,
            min_tracking_confidence=self._config.min_tracking_confidence,
        )
        return mp_vision.HandLandmarker.create_from_options(options)

    def detect(self, frame: Frame) -> list[HandDetection]:
        """Detect hands in a BGR OpenCV frame."""
        if self._closed:
            raise RuntimeError("Hand detector is closed.")

        landmarker = self._ensure_landmarker()

        import cv2
        from mediapipe import Image, ImageFormat

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = Image(image_format=ImageFormat.SRGB, data=rgb_frame)
        timestamp_ms = max(
            int(perf_counter() * 1000),
            self._last_timestamp_ms + 1,
        )
        self._last_timestamp_ms = timestamp_ms
        result = landmarker.detect_for_video(mp_image, timestamp_ms)

        if not result.hand_landmarks:
            return []

        detections: list[HandDetection] = []
        handedness_groups = result.handedness or []

        for index, raw_landmarks in enumerate(result.hand_landmarks):
            handedness = "Unknown"
            score = 0.0
            if index < len(handedness_groups) and handedness_groups[index]:
                category = handedness_groups[index][0]
                handedness = category.category_name or "Unknown"
                score = float(category.score)

            landmarks = tuple(
                (float(landmark.x), float(landmark.y), float(landmark.z))
                for landmark in raw_landmarks
            )
            detections.append(
                HandDetection(
                    handedness=handedness,
                    score=score,
                    landmarks=landmarks,
                    raw_landmarks=tuple(raw_landmarks),
                )
            )

        return detections

    def _ensure_landmarker(self) -> Any:
        """Create the MediaPipe landmarker on demand."""
        if self._landmarker is None:
            self._landmarker = self._create_landmarker(self._model_path)
        return self._landmarker

    def draw_landmarks(
        self,
        frame: Frame,
        detections: list[HandDetection],
    ) -> None:
        """Draw detected hand landmarks and connections onto a frame."""
        import cv2

        height, width = frame.shape[:2]
        connection_color = (255, 180, 0)
        point_color = (0, 255, 0)

        for detection in detections:
            landmarks = detection.raw_landmarks
            for start, end in HAND_CONNECTIONS:
                if start < len(landmarks) and end < len(landmarks):
                    start_point = self._to_pixel(landmarks[start], width, height)
                    end_point = self._to_pixel(landmarks[end], width, height)
                    cv2.line(frame, start_point, end_point, connection_color, 2)

            for landmark in landmarks:
                point = self._to_pixel(landmark, width, height)
                cv2.circle(frame, point, 4, point_color, -1)

    def _to_pixel(self, landmark: Any, width: int, height: int) -> tuple[int, int]:
        return int(landmark.x * width), int(landmark.y * height)

    def close(self) -> None:
        """Release MediaPipe detector resources."""
        if not self._closed:
            if self._landmarker is not None:
                self._landmarker.close()
            self._closed = True

    def __enter__(self) -> "HandDetector":
        """Return the active detector for context manager usage."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Close the detector when leaving a context manager."""
        self.close()
