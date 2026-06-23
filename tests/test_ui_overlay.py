"""Tests for the AirClass UI overlay renderer."""

import numpy as np

from airclass.config import APP_CONFIG
from airclass.ui_overlay import UIOverlay


def test_ui_overlay_render_returns_canvas() -> None:
    """Rendering should return a NumPy image with the configured dimensions."""
    overlay = UIOverlay(APP_CONFIG.ui)
    preview = np.zeros((240, 320, 3), dtype=np.uint8)

    canvas = overlay.render(
        camera_preview_bgr=preview,
        gesture_name="NONE",
        action_name="Landmark Tracking",
        fps=30.0,
        show_help=False,
        slide_title="AirClass",
        slide_subtitle="Touchless Classroom Control System",
        slide_bullets=("One", "Two", "Three"),
        slide_position_text="Slide 1 / 3",
        pointer_position=None,
        drawing_strokes=(),
        status_message=None,
    )

    assert isinstance(canvas, np.ndarray)
    assert canvas.shape == (
        APP_CONFIG.ui.canvas_height,
        APP_CONFIG.ui.canvas_width,
        3,
    )
    assert canvas.dtype == np.uint8


def test_ui_overlay_render_supports_help_state() -> None:
    """Rendering should also work when the help guide is visible."""
    overlay = UIOverlay(APP_CONFIG.ui)
    preview = np.zeros((240, 320, 3), dtype=np.uint8)

    canvas = overlay.render(
        camera_preview_bgr=preview,
        gesture_name="NONE",
        action_name="Landmark Tracking",
        fps=28.5,
        show_help=True,
        slide_title="AirClass",
        slide_subtitle="Touchless Classroom Control System",
        slide_bullets=("One", "Two", "Three"),
        slide_position_text="Slide 1 / 3",
        pointer_position=(0.5, 0.5),
        drawing_strokes=(((0.2, 0.2), (0.4, 0.4)),),
        status_message="Move slides with swipe gestures",
    )

    assert canvas.shape == (
        APP_CONFIG.ui.canvas_height,
        APP_CONFIG.ui.canvas_width,
        3,
    )


def test_ui_overlay_render_supports_board_overlays() -> None:
    """Rendering should accept pointer and drawing overlays."""
    overlay = UIOverlay(APP_CONFIG.ui)
    preview = np.zeros((240, 320, 3), dtype=np.uint8)

    canvas = overlay.render(
        camera_preview_bgr=preview,
        gesture_name="PINCH",
        action_name="POINTER",
        fps=24.0,
        show_help=False,
        slide_title="AirClass",
        slide_subtitle="Touchless Classroom Control System",
        slide_bullets=("One", "Two", "Three"),
        slide_position_text="Slide 1 / 3",
        pointer_position=(0.5, 0.5),
        drawing_strokes=(
            ((0.2, 0.2), (0.4, 0.4)),
            ((0.6, 0.5),),
        ),
        status_message="Pointer active.",
    )

    assert canvas.shape == (
        APP_CONFIG.ui.canvas_height,
        APP_CONFIG.ui.canvas_width,
        3,
    )


def test_ui_overlay_renders_many_drawing_points_without_crashing() -> None:
    """A bounded drawing history should render safely."""
    overlay = UIOverlay(APP_CONFIG.ui)
    preview = np.zeros((240, 320, 3), dtype=np.uint8)
    stroke = tuple(
        (index / 499, 0.5 + 0.2 * ((index % 20) / 20))
        for index in range(500)
    )

    canvas = overlay.render(
        camera_preview_bgr=preview,
        gesture_name="INDEX_POINT",
        action_name="DRAW",
        fps=10.0,
        show_help=False,
        slide_title="AirClass",
        slide_subtitle=None,
        slide_bullets=(),
        slide_position_text="Slide 1 / 1",
        pointer_position=None,
        drawing_strokes=(stroke,),
    )

    assert canvas.shape == (
        APP_CONFIG.ui.canvas_height,
        APP_CONFIG.ui.canvas_width,
        3,
    )


def test_empty_drawing_renders_without_previous_strokes() -> None:
    """CLEAR-like empty stroke state should render without drawing residue."""
    overlay = UIOverlay(APP_CONFIG.ui)
    preview = np.zeros((240, 320, 3), dtype=np.uint8)
    render_kwargs = {
        "camera_preview_bgr": preview,
        "gesture_name": "INDEX_POINT",
        "action_name": "DRAW",
        "fps": 15.0,
        "show_help": False,
        "slide_title": "AirClass",
        "slide_subtitle": None,
        "slide_bullets": (),
        "slide_position_text": "Slide 1 / 1",
        "pointer_position": None,
    }

    drawn = overlay.render(
        **render_kwargs,
        drawing_strokes=(((0.2, 0.2), (0.8, 0.8)),),
    )

    cleared = overlay.render(**render_kwargs, drawing_strokes=())

    assert drawn.shape == cleared.shape
    assert not np.array_equal(drawn, cleared)
