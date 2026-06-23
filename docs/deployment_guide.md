# AirClass Deployment and Running Guide

**Project Title:** AirClass: Touchless Smart Classroom Control System
**Team Name:** Team_San
**Prepared by:** Mohamed Osman Abdi
**Student ID:** 2120256003

---

## 1. Purpose of This Guide

This guide explains how to set up, verify, and run AirClass locally. AirClass is designed as a local Python-based MediaPipe application, so it does not require server deployment, cloud hosting, PowerPoint control, or internet access during the final demonstration after the required dependencies and model file are prepared.

The guide supports the deployment documentation requirement for the application-based MediaPipe course design.

---

## 2. System Requirements

AirClass requires:

* Windows laptop or desktop computer
* Python 3.x
* Laptop webcam or external webcam
* PowerShell or terminal
* Local project folder
* MediaPipe hand landmarker model file
* Python dependencies from `requirements.txt`

Recommended demonstration conditions:

* Good lighting
* Clear camera view
* Hand positioned inside the webcam frame
* Stable laptop position
* Minimal background distraction

---

## 3. Project Folder Structure

The main project structure is:

```text
air_class/
├── airclass/
│   ├── main.py
│   ├── camera.py
│   ├── hand_detector.py
│   ├── gesture_recognizer.py
│   ├── gesture_stabilizer.py
│   ├── command_controller.py
│   ├── command_gate.py
│   ├── action_executor.py
│   ├── slide_deck.py
│   ├── ui_overlay.py
│   ├── metrics.py
│   └── session_logger.py
├── assets/
│   └── models/
│       └── hand_landmarker.task
├── docs/
├── tests/
├── tools/
├── README.md
├── requirements.txt
└── .gitignore
```

The `airclass/` folder contains the main application modules. The `tests/` folder contains automated tests, and the `tools/` folder contains helper scripts for offline readiness and metrics analysis.

---

## 4. Environment Setup

Open PowerShell and go to the project folder:

```powershell
cd C:\Users\Burhan\Desktop\air_class
```

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

---

## 5. MediaPipe Model Preparation

AirClass uses the MediaPipe Hand Landmarker model file:

```text
assets/models/hand_landmarker.task
```

The model must exist before the offline demo readiness check can pass. The model file is required for local hand landmark detection.

The offline readiness script verifies that the model exists and that the detector can initialize correctly.

Run:

```powershell
python tools/check_offline_demo_ready.py
```

Expected result:

```text
Offline readiness: passed
```

---

## 6. Running Automated Tests

Run the automated test suite:

```powershell
python -m pytest
```

Expected final result:

```text
90 passed
```

The test suite checks the major application modules, including gesture recognition, gesture stabilization, command gating, action execution, metrics, logging, and supporting tools.

---

## 7. Running the Compilation Check

Run:

```powershell
python -m compileall -q airclass tests tools
```

If the command finishes without error output, the compilation check has passed.

---

## 8. Running the AirClass Application

Start the application with:

```powershell
python -m airclass.main
```

The application should open the local AirClass classroom interface. The interface includes:

* Classroom board
* Internal slide area
* Camera preview
* Gesture status
* Action status
* FPS/status information
* Help overlay
* Fullscreen option

---

## 9. Application Controls

| Control / Gesture | Function            |
| ----------------- | ------------------- |
| Swipe Right       | Next Slide          |
| Swipe Left        | Previous Slide      |
| Pinch             | Pointer Mode        |
| Index Finger      | Drawing Mode        |
| Open Palm         | Clear Board         |
| `H` Key           | Toggle Help Overlay |
| `F` Key           | Toggle Fullscreen   |
| `ESC` Key         | Quit Application    |

To exit safely, click the application window and press:

```text
ESC
```

---

## 10. Runtime Metrics

After the application exits, AirClass saves runtime metrics under the `logs/` folder. To inspect the latest metrics, run:

```powershell
python tools/analyze_session_metrics.py
```

The metrics analyzer reports:

* Total frames
* Average FPS
* Hand detection rate
* Gesture counts
* Command counts
* Drawing activity
* Pointer updates
* Cooldown rejections
* Possible performance or recognition issues

Runtime metrics were used during development to improve the smoothness and reliability of the application.

---

## 11. Session Logging

AirClass also records session events such as gestures, commands, slide actions, pointer activation, and drawing actions. These logs help verify that the application is responding to user gestures during live operation.

The logs are useful for development and testing, but the full `logs/` folder should not be submitted. Only selected evidence screenshots or representative metrics output should be included in the final document.

---

## 12. Troubleshooting

### Problem: The camera window does not close

Click the AirClass window and press:

```text
ESC
```

If it still does not close, stop the terminal using:

```text
Ctrl + C
```

### Problem: PowerShell cannot activate the virtual environment

Run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Problem: Offline readiness fails

Check that the model file exists at:

```text
assets/models/hand_landmarker.task
```

Then run:

```powershell
python tools/check_offline_demo_ready.py
```

### Problem: Gestures are not recognized smoothly

Improve the demo environment:

* Use good lighting
* Keep the hand inside the camera preview
* Move gestures slowly
* Avoid backlighting
* Keep the hand 40–70 cm from the webcam

---

## 13. Final Verification Commands

Before final demonstration, run the following commands:

```powershell
cd C:\Users\Burhan\Desktop\air_class
.\.venv\Scripts\Activate.ps1
python tools/check_offline_demo_ready.py
python -m pytest
python -m compileall -q airclass tests tools
python -m airclass.main
```

Expected verification results:

```text
Offline readiness: passed
90 tests passed
Compileall: passed
Live application starts successfully
```

---

## 14. Deployment Summary

AirClass is deployed locally as a Python application. It does not require web hosting, database deployment, server configuration, or external classroom hardware. This design is suitable for the course requirement because local demonstration is allowed and does not affect scoring.

The local deployment approach makes AirClass reliable for classroom demonstration because all major functions run from the laptop using the webcam and local MediaPipe model.

---

## 15. Conclusion

This deployment guide confirms that AirClass can be installed, verified, and executed locally. The application uses Python, MediaPipe Hand Landmarker, OpenCV, and a laptop webcam to provide a complete touchless smart classroom control system. The setup process, testing commands, runtime metrics, and troubleshooting steps provide enough information for users or evaluators to run and verify the application successfully.
