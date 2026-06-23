# AirClass: A MediaPipe-Based Touchless Classroom Control System

## Title Page

**Project Title:** AirClass: A MediaPipe-Based Touchless Classroom Control System  
**Course:** MediaPipe Final Project  
**Team Members:** [Team Member 1], [Team Member 2], [Team Member 3], [Team Member 4]  
**Date:** [Insert Date]

## Abstract

AirClass is a Python-based touchless classroom control system built with OpenCV and MediaPipe. The project uses a webcam to detect hand landmarks in real time and translates simple hand poses and movements into classroom-oriented interactions. Instead of controlling external presentation software or the operating system, AirClass provides a self-contained classroom board interface with internal slide navigation, visual pointer feedback, drawing support, help overlays, and session logging. The final implementation emphasizes modular architecture, offline demo readiness, and testability. The result is a complete and reliable MediaPipe application suitable for demonstration in a classroom environment without requiring internet access during the live run.

## Introduction

During live presentations, instructors and student presenters often need to reach for a keyboard or mouse to advance slides, highlight content, or trigger on-screen actions. That interruption can break eye contact, reduce presentation flow, and make the interaction feel less natural. AirClass addresses this problem by using webcam-based hand gesture control to support touchless classroom interaction.

The system interprets visible hand movements through MediaPipe hand landmark detection and converts them into high-level classroom actions. Rather than relying on external presentation tools, AirClass presents a self-contained classroom board UI that simulates the experience of slide control while remaining safe and predictable for a live demo. This makes the project practical for a final university submission because it demonstrates real-time computer vision, interaction design, and software engineering discipline in one integrated application.

## Objectives

The project was developed to achieve the following objectives:

- real-time hand landmark detection
- gesture recognition
- classroom board UI
- internal slide navigation
- pointer and drawing tools
- offline demo readiness
- testing and logging

## System Functionality

AirClass provides a complete touchless interaction flow designed for classroom presentation use.

- Swipe right advances to the next internal slide.
- Swipe left returns to the previous internal slide.
- Pinch activates a visible pointer on the board surface.
- Index point enables air drawing on the board.
- Open palm clears the drawing overlay.
- A help overlay presents the gesture guide and can be toggled during the demo.
- Session logging records meaningful interaction events for debugging and reporting.
- An offline readiness check verifies that the local MediaPipe model is available before demo day.

The interface is intentionally laptop-only and self-contained. This keeps the behavior understandable in a university demo setting and avoids external software dependencies that could fail under presentation pressure.

## Technical Architecture

AirClass follows a layered pipeline:

**Camera -> HandDetector -> GestureRecognizer -> GestureStabilizer -> CommandController -> CommandGate -> ActionExecutor -> SlideDeck -> UIOverlay**

`SessionLogger` and `RuntimeMetrics` observe the live pipeline to preserve interaction evidence and performance measurements without changing command behavior.

Each layer has a narrow responsibility:

- `config.py`: centralizes application settings in typed dataclasses.
- `camera.py`: wraps `cv2.VideoCapture` for controlled webcam access.
- `hand_detector.py`: integrates MediaPipe HandLandmarker and returns structured hand detections.
- `gesture_types.py`: defines shared enums and gesture event dataclasses.
- `gesture_recognizer.py`: implements rule-based gesture classification from normalized landmarks.
- `gesture_stabilizer.py`: suppresses short-lived pose flicker while keeping pinch and swipe responsive.
- `command_controller.py`: maps gestures to high-level classroom commands.
- `command_gate.py`: converts held discrete gestures into one-shot commands.
- `action_executor.py`: applies commands to internal slide and visual state.
- `slide_deck.py`: stores the simulated slide content and navigation state.
- `ui_overlay.py`: renders the classroom board, HUD, preview, and overlays using OpenCV.
- `session_logger.py`: writes lightweight CSV session logs.
- `metrics.py`: collects FPS, hand-detection, gesture, command, pointer, and drawing measurements.
- `tools/check_offline_demo_ready.py`: validates offline readiness before a live demo.

This separation keeps the application readable and makes each part individually testable.

## Implementation Details

### MediaPipe Hand Landmark Detection

The project uses MediaPipe to detect hands from the webcam feed. The detector produces normalized 21-point landmarks for each hand, along with handedness information and confidence scores. These landmarks form the foundation for all later interaction logic.

### Normalized 21-Point Landmarks

Landmarks are represented in normalized image coordinates, which makes the gesture logic independent of the camera resolution. This is useful because the same logic can be tested with synthetic landmark tuples and then reused in the live application.

### Rule-Based Gesture Recognition

Gesture recognition is intentionally rule-based. The recognizer class evaluates simple geometric conditions such as finger extension, pinch distance, and short-term horizontal movement. This design keeps the behavior deterministic, explainable, and suitable for testing.

### Swipe History and Cooldown

Swipe gestures are recognized using a short history of palm-center positions. The recognizer compares the start and end positions over that window to infer left or right movement. A cooldown prevents one swipe from firing repeatedly across multiple frames.

### Pinch Threshold

Pinch detection is based on the distance between the thumb tip and index fingertip. When the fingers move within a configured threshold, the recognizer emits a pinch gesture event. This event is used for the pointer tool in the board UI.

### Fingertip-Based Pointer and Drawing

For pointer and drawing behavior, the system uses the index fingertip position rather than the palm center. This produces a more intuitive interaction point for the user. The pointer dot follows the fingertip, and drawing points are appended only when the movement exceeds a minimum distance.

### Drawing Jitter Filtering

To reduce visual noise, drawing input is filtered using a minimum distance threshold between successive points. This avoids dense point clusters caused by small frame-to-frame tremors in the hand. Drawing history is also bounded so the application does not accumulate unlimited points during a long session.

### Internal Slide Simulator

AirClass does not control PowerPoint or the operating system. Instead, it uses an internal slide deck with several polished demo slides. Swipe gestures advance or reverse this internal deck, which keeps the demonstration safe and self-contained.

### OpenCV Rendering

The UI overlay is composed entirely with OpenCV drawing functions. The interface includes a large classroom board, slide content, a camera preview thumbnail, a bottom HUD, gesture and action labels, and optional help guidance.

### CSV Session Logging

The session logger writes a compact CSV file for each run. Logs contain timestamped gesture and command events, execution status, slide position, and optional normalized coordinates. This is useful for debugging, evidence collection, and final reporting.

### Runtime Metrics

The runtime metrics collector records frame rate, hand-detection rate, gesture and command counts, transitions, pointer activity, and drawing activity. The metrics analyzer summarizes the latest JSON file after a controlled test session.

## Technology Stack and Environment

AirClass was implemented using the following technology stack:

- Python 3.10+
- OpenCV
- MediaPipe
- NumPy
- Pytest
- a local laptop webcam
- a local MediaPipe model file

The local MediaPipe model file is required for offline demo readiness and is stored at `assets/models/hand_landmarker.task`.

## User Interaction and UX Design

The interface is designed for classroom presentation use. The main board area occupies most of the screen and displays the simulated slide. A bottom HUD contains the live camera preview, gesture and action labels, the current FPS, and control hints. The help overlay can be toggled to show gesture guidance. Fullscreen mode is available for presentation use, and ESC exits the application cleanly.

The UI is intentionally restrained and functional. It is meant to feel like a presentation surface rather than a general-purpose desktop application. That makes the gesture feedback easier to read during a live demo.

## Testing and Verification

The project was verified through multiple layers of testing:

- offline readiness check with `python tools/check_offline_demo_ready.py`
- automated unit tests with `python -m pytest`
- syntax verification with `python -m compileall -q airclass tests tools`
- manual live GUI testing of the camera feed, board UI, pointer, drawing, help overlay, fullscreen toggle, and exit behavior

Current result: **90 tests passed**.

This testing strategy provides confidence that the core logic is stable and that the live demo path remains usable without internet access.

## Deployment / Demo Setup

AirClass is designed for local deployment on a laptop. The recommended setup is:

1. Create and activate a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Ensure the MediaPipe model file exists at `assets/models/hand_landmarker.task`.
4. Run the offline readiness check.
5. Launch the app with `python -m airclass.main`.

After the model is prepared, the demo does not require internet access. A projector is optional because the application can be demonstrated directly from the laptop screen.

## Known Limitations

AirClass is intentionally scoped to a stable final project demonstration. The main limitations are:

- lighting and camera quality affect hand detection quality
- the gesture logic is rule-based rather than trained machine learning
- external PowerPoint or operating system control is intentionally not included
- camera framing affects reliability, especially for gestures near the image edges
- the local MediaPipe model file must be prepared before an offline demo

These constraints were accepted to preserve reliability, explainability, and demo safety.

## Division of Labour

| Team Member | Role |
| --- | --- |
| Team Member 1 | architecture, integration, testing |
| Team Member 2 | MediaPipe detector and gesture recognition |
| Team Member 3 | UI overlay and demo design |
| Team Member 4 | documentation and testing |

Names are intentionally left as placeholders for final submission.

## Conclusion

AirClass satisfies the MediaPipe final project goal by delivering a complete, tested, real-time touchless classroom control system. The application demonstrates webcam-based hand landmark detection, rule-based gesture recognition, internal slide navigation, visual pointer and drawing support, offline readiness, and lightweight session logging in a clean modular architecture. Because the system is self-contained and does not depend on external presentation control, it is well suited for a reliable classroom demonstration and a strong academic submission.
