"""OpenCV-based AirClass UI composition."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from airclass.config import UIConfig


@dataclass(frozen=True, slots=True)
class _TextBlock:
    """Simple text block description used for layout helpers."""

    text: str
    origin: tuple[int, int]
    scale: float
    color: tuple[int, int, int]
    thickness: int = 2


class UIOverlay:
    """Compose the AirClass classroom board, HUD, and help overlay."""

    def __init__(self, config: UIConfig) -> None:
        self._config = config

    def render(
        self,
        camera_preview_bgr: np.ndarray,
        gesture_name: str,
        action_name: str,
        fps: float,
        show_help: bool,
        slide_title: str,
        slide_subtitle: str | None,
        slide_bullets: tuple[str, ...],
        slide_position_text: str,
        pointer_position: tuple[float, float] | None,
        drawing_strokes: tuple[tuple[tuple[float, float], ...], ...],
        status_message: str | None = None,
    ) -> np.ndarray:
        """Render the composed AirClass UI canvas."""
        import cv2

        canvas = np.full(
            (self._config.canvas_height, self._config.canvas_width, 3),
            self._config.hud_bg_color,
            dtype=np.uint8,
        )
        board_height = self._config.canvas_height - self._config.status_bar_height

        self._draw_board_area(
            canvas,
            board_height,
            show_help,
            slide_title=slide_title,
            slide_subtitle=slide_subtitle,
            slide_bullets=slide_bullets,
            slide_position_text=slide_position_text,
            pointer_position=pointer_position,
            drawing_strokes=drawing_strokes,
            status_message=status_message,
        )
        self._draw_hud(
            canvas,
            camera_preview_bgr,
            gesture_name=gesture_name,
            action_name=action_name,
            fps=fps,
            board_height=board_height,
        )
        return canvas

    def _draw_board_area(
        self,
        canvas: np.ndarray,
        board_height: int,
        show_help: bool,
        slide_title: str,
        slide_subtitle: str | None,
        slide_bullets: tuple[str, ...],
        slide_position_text: str,
        pointer_position: tuple[float, float] | None,
        drawing_strokes: tuple[tuple[tuple[float, float], ...], ...],
        status_message: str | None,
    ) -> None:
        """Draw the main classroom board placeholder area."""
        import cv2

        cfg = self._config
        cv2.rectangle(
            canvas,
            (0, 0),
            (cfg.canvas_width - 1, board_height - 1),
            cfg.board_border_color,
            2,
        )
        canvas[:board_height] = cfg.board_bg_color

        if show_help:
            self._draw_help_guide(canvas, board_height)
        else:
            self._draw_slide_content(
                canvas,
                board_height,
                slide_title=slide_title,
                slide_subtitle=slide_subtitle,
                slide_bullets=slide_bullets,
                slide_position_text=slide_position_text,
                pointer_position=pointer_position,
                drawing_strokes=drawing_strokes,
                status_message=status_message,
            )

    def _draw_slide_content(
        self,
        canvas: np.ndarray,
        board_height: int,
        slide_title: str,
        slide_subtitle: str | None,
        slide_bullets: tuple[str, ...],
        slide_position_text: str,
        pointer_position: tuple[float, float] | None,
        drawing_strokes: tuple[tuple[tuple[float, float], ...], ...],
        status_message: str | None,
    ) -> None:
        """Draw the current simulated slide content."""
        cfg = self._config
        x = cfg.margin
        y = cfg.margin + 18
        self._draw_text(
            canvas,
            _TextBlock(slide_title, (x, y), cfg.font_scale_title, cfg.text_color, 3),
        )
        if slide_subtitle is not None:
            self._draw_text(
                canvas,
                _TextBlock(
                    slide_subtitle,
                    (x, y + 52),
                    cfg.font_scale_heading,
                    cfg.text_subtle_color,
                    2,
                ),
            )

        bullet_y = y + 118
        for index, bullet in enumerate(slide_bullets):
            self._draw_bullet_line(canvas, bullet, (x, bullet_y + index * 44))

        self._draw_visual_overlays(
            canvas,
            board_height,
            pointer_position=pointer_position,
            drawing_strokes=drawing_strokes,
        )
        self._draw_slide_position_badge(canvas, slide_position_text)
        if status_message:
            self._draw_status_message(canvas, status_message, board_height)

    def _draw_help_guide(self, canvas: np.ndarray, board_height: int) -> None:
        """Draw the placeholder gesture guide."""
        import cv2

        cfg = self._config
        panel_x = cfg.margin
        panel_y = cfg.margin
        panel_w = cfg.canvas_width - (cfg.margin * 2)
        panel_h = board_height - (cfg.margin * 2)

        cv2.rectangle(
            canvas,
            (panel_x, panel_y),
            (panel_x + panel_w, panel_y + panel_h),
            cfg.help_bg_color,
            -1,
        )
        cv2.rectangle(
            canvas,
            (panel_x, panel_y),
            (panel_x + panel_w, panel_y + panel_h),
            cfg.board_border_color,
            2,
        )
        self._draw_text(
            canvas,
            _TextBlock(
                "Gesture Guide",
                (panel_x + 24, panel_y + 56),
                cfg.font_scale_title,
                cfg.help_text_color,
                3,
            ),
        )
        self._draw_text(
            canvas,
            _TextBlock(
                "Placeholder gestures for the future interaction layer",
                (panel_x + 24, panel_y + 98),
                cfg.font_scale_body,
                cfg.text_subtle_color,
                2,
            ),
        )

        guide_lines = [
            "Swipe Right  ->  Next Slide",
            "Swipe Left   ->  Previous Slide",
            "Pinch        ->  Laser Pointer",
            "Index Finger ->  Air Drawing",
            "Open Palm    ->  Clear / Pause",
        ]
        start_y = panel_y + 170
        for index, line in enumerate(guide_lines):
            self._draw_text(
                canvas,
                _TextBlock(
                    line,
                    (panel_x + 40, start_y + index * 52),
                    cfg.font_scale_heading,
                    cfg.help_text_color,
                    2,
                ),
            )

    def _draw_slide_position_badge(
        self,
        canvas: np.ndarray,
        slide_position_text: str,
    ) -> None:
        """Draw the slide position text in the upper-right corner."""
        import cv2

        cfg = self._config
        text_size, baseline = cv2.getTextSize(
            slide_position_text,
            cv2.FONT_HERSHEY_SIMPLEX,
            cfg.font_scale_body,
            2,
        )
        padding_x = 16
        padding_y = 12
        box_width = text_size[0] + (padding_x * 2)
        box_height = text_size[1] + baseline + (padding_y * 2)
        box_x = cfg.canvas_width - cfg.margin - box_width
        box_y = cfg.margin

        cv2.rectangle(
            canvas,
            (box_x, box_y),
            (box_x + box_width, box_y + box_height),
            cfg.hud_accent_color,
            -1,
        )
        self._draw_text(
            canvas,
            _TextBlock(
                slide_position_text,
                (box_x + padding_x, box_y + box_height - padding_y - baseline),
                cfg.font_scale_body,
                (255, 255, 255),
                2,
            ),
        )

    def _draw_visual_overlays(
        self,
        canvas: np.ndarray,
        board_height: int,
        pointer_position: tuple[float, float] | None,
        drawing_strokes: tuple[tuple[tuple[float, float], ...], ...],
    ) -> None:
        """Draw the pointer dot and freehand drawing overlay."""
        import cv2

        for stroke in drawing_strokes:
            self._draw_stroke(canvas, stroke, board_height)

        if pointer_position is not None:
            pointer_pixel = self._board_point_to_pixel(pointer_position, board_height)
            cv2.circle(canvas, pointer_pixel, 12, (0, 255, 255), -1, cv2.LINE_AA)
            cv2.circle(canvas, pointer_pixel, 18, (0, 170, 255), 2, cv2.LINE_AA)

    def _draw_stroke(
        self,
        target: np.ndarray,
        stroke: tuple[tuple[float, float], ...],
        board_height: int,
        color: tuple[int, int, int] = (36, 146, 255),
    ) -> None:
        """Draw one anti-aliased stroke onto an image or mask."""
        import cv2

        if not stroke:
            return
        pixel_points = [
            self._board_point_to_pixel(point, board_height) for point in stroke
        ]
        if len(pixel_points) >= 2:
            polyline = np.array(pixel_points, dtype=np.int32).reshape((-1, 1, 2))
            cv2.polylines(
                target,
                [polyline],
                False,
                color,
                self._config.drawing_stroke_width,
                cv2.LINE_AA,
            )
        else:
            cv2.circle(
                target,
                pixel_points[0],
                max(2, self._config.drawing_stroke_width // 2),
                color,
                -1,
                cv2.LINE_AA,
            )

    def _board_point_to_pixel(
        self,
        point: tuple[float, float],
        board_height: int,
    ) -> tuple[int, int]:
        """Convert normalized board coordinates to canvas pixels."""
        cfg = self._config
        x = min(max(point[0], 0.0), 1.0)
        y = min(max(point[1], 0.0), 1.0)
        board_width = cfg.canvas_width - (cfg.margin * 2)
        board_inner_height = board_height - (cfg.margin * 2)
        pixel_x = cfg.margin + int(x * board_width)
        pixel_y = cfg.margin + int(y * board_inner_height)
        return pixel_x, pixel_y

    def _draw_status_message(
        self,
        canvas: np.ndarray,
        status_message: str,
        board_height: int,
    ) -> None:
        """Draw a status banner near the bottom of the board."""
        import cv2

        cfg = self._config
        text_size, baseline = cv2.getTextSize(
            status_message,
            cv2.FONT_HERSHEY_SIMPLEX,
            cfg.font_scale_body,
            2,
        )
        padding_x = 16
        padding_y = 12
        box_width = min(
            text_size[0] + (padding_x * 2),
            cfg.canvas_width - (cfg.margin * 2),
        )
        box_height = text_size[1] + baseline + (padding_y * 2)
        box_x = cfg.margin
        box_y = board_height - box_height - cfg.margin

        cv2.rectangle(
            canvas,
            (box_x, box_y),
            (box_x + box_width, box_y + box_height),
            (232, 236, 242),
            -1,
        )
        cv2.rectangle(
            canvas,
            (box_x, box_y),
            (box_x + box_width, box_y + box_height),
            cfg.board_border_color,
            1,
        )
        self._draw_text(
            canvas,
            _TextBlock(
                status_message,
                (box_x + padding_x, box_y + box_height - padding_y - baseline),
                cfg.font_scale_body,
                cfg.label_color,
                2,
            ),
        )

    def _draw_hud(
        self,
        canvas: np.ndarray,
        camera_preview_bgr: np.ndarray,
        gesture_name: str,
        action_name: str,
        fps: float,
        board_height: int,
    ) -> None:
        """Draw the bottom status bar and preview thumbnail."""
        import cv2

        cfg = self._config
        hud_y = board_height
        hud_h = cfg.status_bar_height

        cv2.rectangle(
            canvas,
            (0, hud_y),
            (cfg.canvas_width - 1, cfg.canvas_height - 1),
            cfg.hud_bg_color,
            -1,
        )
        cv2.line(
            canvas,
            (0, hud_y),
            (cfg.canvas_width - 1, hud_y),
            cfg.hud_accent_color,
            2,
        )

        preview = self._prepare_preview(camera_preview_bgr)
        preview_x = cfg.margin
        preview_y = hud_y + (hud_h - cfg.preview_height) // 2
        canvas[
            preview_y : preview_y + cfg.preview_height,
            preview_x : preview_x + cfg.preview_width,
        ] = preview

        cv2.rectangle(
            canvas,
            (preview_x, preview_y),
            (preview_x + cfg.preview_width, preview_y + cfg.preview_height),
            cfg.hud_accent_color,
            2,
        )

        text_x = preview_x + cfg.preview_width + 32
        base_y = hud_y + 46
        self._draw_text(
            canvas,
            _TextBlock(
                f"Gesture: {gesture_name}",
                (text_x, base_y),
                cfg.font_scale_heading,
                cfg.hud_text_color,
                2,
            ),
        )
        self._draw_text(
            canvas,
            _TextBlock(
                f"Action: {action_name}",
                (text_x, base_y + 40),
                cfg.font_scale_heading,
                cfg.hud_text_color,
                2,
            ),
        )
        self._draw_text(
            canvas,
            _TextBlock(
                f"FPS: {fps:.1f}",
                (text_x, base_y + 80),
                cfg.font_scale_heading,
                cfg.hud_text_color,
                2,
            ),
        )
        self._draw_text(
            canvas,
            _TextBlock(
                "Controls: ESC Quit | H Help | F Fullscreen",
                (text_x, base_y + 122),
                cfg.font_scale_body,
                cfg.hud_text_color,
                2,
            ),
        )

        self._draw_text(
            canvas,
            _TextBlock(
                "AirClass Demo Surface",
                (cfg.canvas_width - 330, hud_y + 44),
                cfg.font_scale_body,
                cfg.hud_text_color,
                2,
            ),
        )

    def _prepare_preview(self, camera_preview_bgr: np.ndarray) -> np.ndarray:
        """Resize the camera preview to the HUD thumbnail dimensions."""
        import cv2

        preview = cv2.resize(
            camera_preview_bgr,
            (self._config.preview_width, self._config.preview_height),
            interpolation=cv2.INTER_AREA,
        )
        return preview

    def _draw_bullet_line(
        self,
        canvas: np.ndarray,
        text: str,
        origin: tuple[int, int],
    ) -> None:
        """Draw a bullet point with an accent marker."""
        import cv2

        cfg = self._config
        bullet_x, bullet_y = origin
        cv2.circle(canvas, (bullet_x + 10, bullet_y - 9), 5, cfg.hud_accent_color, -1)
        self._draw_text(
            canvas,
            _TextBlock(
                text,
                (bullet_x + 28, bullet_y),
                cfg.font_scale_heading,
                cfg.text_color,
                2,
            ),
        )

    def _draw_text(self, canvas: np.ndarray, block: _TextBlock) -> None:
        """Draw a text block using OpenCV."""
        import cv2

        cv2.putText(
            canvas,
            block.text,
            block.origin,
            cv2.FONT_HERSHEY_SIMPLEX,
            block.scale,
            block.color,
            block.thickness,
            cv2.LINE_AA,
        )
