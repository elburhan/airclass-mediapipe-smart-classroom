# AirClass: A MediaPipe-Based Touchless Classroom Control System

AirClass is a Python, OpenCV, and MediaPipe application for touchless classroom and presentation control using webcam-based hand gestures. It detects hand landmarks in real time, renders a laptop-only classroom board UI, and keeps all demo behavior self-contained inside the app.

## Key Features

- real-time hand landmark detection
- laptop-only classroom board UI
- internal slide simulation
- swipe navigation
- pinch laser pointer
- index-finger air drawing
- open-palm clear
- offline demo readiness
- session logging
- automated tests

## Technology Stack

- Python
- OpenCV
- MediaPipe
- NumPy
- Pytest

## Project Structure

- `airclass/config.py`: shared application configuration dataclasses
- `airclass/camera.py`: webcam capture wrapper around OpenCV
- `airclass/hand_detector.py`: MediaPipe Hand Landmarker integration
- `airclass/gesture_types.py`: shared gesture, command, and event types
- `airclass/gesture_recognizer.py`: pure rule-based gesture recognition
- `airclass/gesture_stabilizer.py`: short-window gesture stabilization
- `airclass/command_controller.py`: maps gestures to classroom commands
- `airclass/command_gate.py`: edge-triggers discrete commands
- `airclass/action_executor.py`: applies commands to internal slide and visual state
- `airclass/slide_deck.py`: internal slide simulator and default deck content
- `airclass/ui_overlay.py`: OpenCV UI composition for the classroom board and HUD
- `airclass/session_logger.py`: lightweight CSV session logging
- `airclass/metrics.py`: runtime metrics collection
- `tools/check_offline_demo_ready.py`: verifies the local model file and offline startup path
- `tools/analyze_session_metrics.py`: analyzes the latest runtime metrics
- `tests/`: automated tests for the project's pure and integration-safe behavior

## Installation

Python 3.10 or newer is required.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

## Offline Model Preparation

AirClass expects the local MediaPipe model file at `assets/models/hand_landmarker.task` before an offline demo. The project can download it when allowed, but demo day should not depend on that.

Verify readiness with:

```powershell
python tools/check_offline_demo_ready.py
```

If the check passes, the project is ready for an offline demo.

## Running the App

```powershell
python -m airclass.main
```

## Controls

- `ESC`: quit
- `H`: toggle help
- `F`: toggle fullscreen

## Gesture Mapping

- Swipe Right -> `NEXT_SLIDE`
- Swipe Left -> `PREVIOUS_SLIDE`
- Pinch -> `POINTER`
- Index Point -> `DRAW`
- Open Palm -> `CLEAR`

## Testing

```powershell
python -m pytest
python -m compileall -q airclass tests tools
```

## Session Logs

AirClass writes lightweight CSV session logs under `logs/`. The folder is ignored by Git so demo runs do not pollute the repository history.

## Runtime Metrics

AirClass prints a runtime metrics summary when the application exits and saves a timestamped metrics JSON file under `logs/`. Inspect the latest session with:

```powershell
python tools/analyze_session_metrics.py
```

Use these measurements to identify FPS, hand-tracking, gesture-transition, cooldown, pointer, and drawing problems before tuning gesture thresholds.

## Performance Tuning

AirClass uses 640x480 camera input by default for smoother real-time performance. Check runtime metrics after each tuning pass, and remember that gesture reliability still depends heavily on lighting and keeping the hand clearly framed.

## Gesture Stability Tuning

AirClass stabilizes continuous gestures over a short frame window to reduce recognition flicker. Swipes remain immediate discrete events, while clear commands are gated to avoid repeatedly clearing the board when an open palm is held. Check runtime metrics after each tuning pass.

## Drawing Smoothness

AirClass keeps drawing lightweight by adding at most one distance-filtered point per `DRAW` frame. Separate strokes prevent accidental connecting lines across pointer or idle modes, and `CLEAR` resets the complete drawing state.

## Known Limitations

- lighting and camera quality affect detection
- gestures are rule-based rather than learned
- no external PowerPoint or operating system control is used by design
- the local MediaPipe model file must be prepared before an offline demo

## Demo Checklist

- confirm `assets/models/hand_landmarker.task` exists
- run `python tools/check_offline_demo_ready.py`
- run `python -m pytest`
- start the app with `python -m airclass.main`
- verify the webcam, HUD, internal slides, pointer, drawing, and clear behavior
- confirm `H`, `F`, and `ESC` work as expected
- check that a session CSV appears under `logs/`
