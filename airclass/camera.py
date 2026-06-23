"""OpenCV camera lifecycle management."""

from types import TracebackType
from typing import Any

from airclass.config import CameraConfig

Frame = Any


class CameraError(RuntimeError):
    """Raised when the webcam cannot be opened or read."""


class Camera:
    """Wrap an OpenCV ``VideoCapture`` with predictable cleanup."""

    def __init__(self, config: CameraConfig) -> None:
        self._config = config
        self._capture: Any | None = None

    def start(self) -> "Camera":
        """Open and configure the webcam.

        Returns:
            The active camera instance.

        Raises:
            CameraError: If OpenCV cannot open the configured camera.
        """
        import cv2

        if self._capture is not None and self._capture.isOpened():
            return self

        capture = cv2.VideoCapture(self._config.index)
        if not capture.isOpened():
            capture.release()
            raise CameraError(
                f"Could not open camera at index {self._config.index}."
            )

        capture.set(cv2.CAP_PROP_FRAME_WIDTH, self._config.width)
        capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self._config.height)
        capture.set(cv2.CAP_PROP_FPS, self._config.fps)
        self._capture = capture
        return self

    def read(self) -> Frame:
        """Read the next frame, mirroring it when configured.

        Raises:
            CameraError: If the camera is not active or a frame cannot be read.
        """
        if self._capture is None or not self._capture.isOpened():
            raise CameraError("Camera is not started.")

        import cv2

        success, frame = self._capture.read()
        if not success or frame is None:
            raise CameraError("Could not read a frame from the camera.")

        if self._config.mirror:
            frame = cv2.flip(frame, 1)
        return frame

    def stop(self) -> None:
        """Release the webcam if it is open."""
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def __enter__(self) -> "Camera":
        """Start the camera when entering a context manager."""
        return self.start()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Release the camera when leaving a context manager."""
        self.stop()
