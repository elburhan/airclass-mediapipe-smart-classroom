"""AirClass classroom demo application."""

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
from time import perf_counter
from typing import Protocol

from airclass.camera import Camera, CameraError
from airclass.action_executor import ActionExecutor
from airclass.command_gate import CommandGate
from airclass.command_controller import CommandController
from airclass.config import APP_CONFIG
from airclass.gesture_recognizer import GestureRecognizer
from airclass.gesture_stabilizer import GestureStabilizer
from airclass.hand_detector import HandDetector, HandDetectorError
from airclass.metrics import RuntimeMetrics
from airclass.slide_deck import create_default_deck
from airclass.session_logger import SessionLogger
from airclass.ui_overlay import UIOverlay


class _ScoredDetection(Protocol):
    """Minimal detection shape used to select the primary hand."""

    score: float
    landmarks: tuple[tuple[float, float, float], ...]


@dataclass(frozen=True, slots=True)
class _SessionLogState:
    """Session log state used to suppress duplicate rows."""

    gesture: str
    command: str
    executed: bool
    message: str
    slide_index: int


def _set_fullscreen(window_name: str, enabled: bool) -> None:
    """Toggle OpenCV fullscreen mode."""
    import cv2 as cv

    value = cv.WINDOW_FULLSCREEN if enabled else cv.WINDOW_NORMAL
    cv.setWindowProperty(window_name, cv.WND_PROP_FULLSCREEN, value)


def run() -> int:
    """Run the classroom demo loop until Escape is pressed."""
    import cv2

    ui_config = APP_CONFIG.ui
    overlay = UIOverlay(ui_config)
    recognizer = GestureRecognizer(APP_CONFIG.gesture)
    stabilizer = GestureStabilizer(
        window=APP_CONFIG.gesture.gesture_stability_window,
        required=APP_CONFIG.gesture.gesture_stability_required,
    )
    command_controller = CommandController()
    command_gate = CommandGate()
    slide_deck = create_default_deck()
    action_executor = ActionExecutor(
        slide_deck,
        drawing_min_point_distance=APP_CONFIG.gesture.drawing_min_point_distance,
        drawing_max_jump_distance=APP_CONFIG.gesture.drawing_max_jump_distance,
        max_drawing_points=APP_CONFIG.gesture.max_drawing_points,
        clear_command_cooldown_seconds=APP_CONFIG.gesture.clear_cooldown_seconds,
    )
    metrics = RuntimeMetrics()
    try:
        session_logger: SessionLogger | None = SessionLogger()
    except OSError as error:
        print(f"Session logging disabled: {error}")
        session_logger = None
    show_help = False
    fullscreen = ui_config.start_fullscreen
    last_logged_state: _SessionLogState | None = None

    try:
        with Camera(APP_CONFIG.camera) as camera, HandDetector(
            APP_CONFIG.hand_detector
        ) as detector:
            cv2.namedWindow(ui_config.window_name, cv2.WINDOW_NORMAL)
            _set_fullscreen(ui_config.window_name, fullscreen)
            if not fullscreen:
                cv2.resizeWindow(
                    ui_config.window_name,
                    ui_config.canvas_width,
                    ui_config.canvas_height,
                )

            last_frame_time = perf_counter()
            while True:
                frame = camera.read()
                detections = detector.detect(frame)
                camera_preview = frame.copy()
                detector.draw_landmarks(camera_preview, detections)
                primary_detection = _select_primary_detection(detections)
                raw_event = recognizer.recognize(
                    primary_detection.landmarks if primary_detection is not None else None,
                    timestamp=perf_counter(),
                )
                stable_event = stabilizer.stabilize(raw_event)
                raw_command = command_controller.handle_gesture(stable_event)
                gated_command = command_gate.gate(raw_command)
                action_result = action_executor.execute(
                    gated_command,
                    position=stable_event.position,
                )

                current_log_state = _SessionLogState(
                    gesture=stable_event.name.name,
                    command=gated_command.name,
                    executed=action_result.executed,
                    message=action_result.message,
                    slide_index=action_result.slide_index,
                )
                if session_logger is not None and _should_log_session_state(
                    current_log_state,
                    last_logged_state,
                ):
                    try:
                        session_logger.log_event(
                            timestamp=stable_event.timestamp,
                            gesture=current_log_state.gesture,
                            command=current_log_state.command,
                            executed=current_log_state.executed,
                            message=current_log_state.message,
                            slide_index=action_result.slide_index,
                            total_slides=action_result.total_slides,
                            position=stable_event.position,
                        )
                        last_logged_state = current_log_state
                    except OSError as error:
                        print(f"Session logging disabled: {error}")
                        session_logger.close()
                        session_logger = None

                now = perf_counter()
                delta = now - last_frame_time
                fps = (1.0 / delta) if delta > 0 else 0.0
                last_frame_time = now
                metrics.record_frame(
                    fps=fps,
                    has_hand=primary_detection is not None,
                )
                metrics.record_gesture(stable_event.name.name)
                metrics.record_command(
                    command_name=gated_command.name,
                    executed=action_result.executed,
                    message=action_result.message,
                )
                metrics.record_visual_state(
                    pointer_active=action_result.state.pointer_position is not None,
                    drawing_points_count=len(action_result.state.drawing_points),
                    drawing_strokes_count=action_result.state.drawing_strokes_created,
                    drawing_resets=action_result.state.drawing_resets,
                    drawing_points_added_total=action_result.state.drawing_points_added,
                )

                slide = slide_deck.current_slide

                composed = overlay.render(
                    camera_preview_bgr=camera_preview,
                    gesture_name=stable_event.name.name,
                    action_name=gated_command.name,
                    fps=fps,
                    show_help=show_help,
                    slide_title=slide.title,
                    slide_subtitle=slide.subtitle,
                    slide_bullets=slide.bullets,
                    slide_position_text=f"Slide {slide_deck.display_index} / {slide_deck.total_slides}",
                    pointer_position=action_result.state.pointer_position,
                    drawing_strokes=action_result.state.drawing_strokes,
                    status_message=action_result.state.status_message,
                )

                cv2.imshow(ui_config.window_name, composed)
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    break
                if key in (ord("h"), ord("H")):
                    show_help = not show_help
                if key in (ord("f"), ord("F")):
                    fullscreen = not fullscreen
                    _set_fullscreen(ui_config.window_name, fullscreen)
                    if not fullscreen:
                        cv2.resizeWindow(
                            ui_config.window_name,
                            ui_config.canvas_width,
                            ui_config.canvas_height,
                        )
    except CameraError as error:
        print(f"Camera error: {error}")
        return 1
    except HandDetectorError as error:
        print(f"Hand detector error: {error}")
        return 1
    finally:
        if session_logger is not None:
            session_logger.close()
        cv2.destroyAllWindows()
        summary = metrics.summary()
        print("\nAirClass Runtime Metrics")
        print(json.dumps(summary, indent=2, sort_keys=True))
        try:
            metrics_path = _save_metrics_summary(summary)
            print(f"Metrics saved to: {metrics_path}")
        except OSError as error:
            print(f"Metrics file could not be saved: {error}")

    return 0


def _save_metrics_summary(
    summary: dict[str, object],
    log_dir: str | Path = "logs",
) -> Path:
    """Save a metrics summary to a unique timestamped JSON file."""
    directory = Path(log_dir)
    directory.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = directory / f"airclass_metrics_{timestamp}.json"
    suffix = 1
    while path.exists():
        path = directory / f"airclass_metrics_{timestamp}_{suffix}.json"
        suffix += 1
    with path.open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2, sort_keys=True)
        file.write("\n")
    return path


def _select_primary_detection(
    detections: list[_ScoredDetection],
) -> _ScoredDetection | None:
    """Pick the highest-confidence hand detection from a detection list."""
    if not detections:
        return None
    return max(detections, key=lambda detection: detection.score)


def _should_log_session_state(
    current_state: _SessionLogState,
    previous_state: _SessionLogState | None,
) -> bool:
    """Return True when a session state is meaningful enough to log."""
    if (
        current_state.command == "NONE"
        and not current_state.executed
        and current_state.message == "No command to execute."
    ):
        return False
    return current_state != previous_state


if __name__ == "__main__":
    raise SystemExit(run())
